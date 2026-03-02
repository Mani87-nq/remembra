"""API Key management endpoints – /api/v1/keys."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from slowapi import Limiter

from remembra.auth.keys import APIKeyManager
from remembra.auth.middleware import (
    AuthenticatedUser,
    CurrentUser,
    RequireMasterKey,
    get_client_ip,
)
from remembra.cloud.limits import EnforceKeyLimit
from remembra.core.limiter import limiter
from remembra.security.audit import AuditLogger

router = APIRouter(prefix="/keys", tags=["api-keys"])


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class CreateKeyRequest(BaseModel):
    """Request to create a new API key."""
    
    user_id: str = Field(..., description="User ID to create key for")
    name: str | None = Field(None, description="Human-readable name for the key")
    rate_limit_tier: str = Field("standard", description="Rate limit tier: standard or premium")


class CreateKeyResponse(BaseModel):
    """Response after creating an API key."""
    
    id: str = Field(..., description="Key ID (use for revocation)")
    key: str = Field(..., description="Full API key (only shown once!)")
    user_id: str
    name: str | None
    rate_limit_tier: str
    message: str = Field(
        default="Store this key securely. It cannot be retrieved again.",
        description="Important security notice"
    )


class KeyInfo(BaseModel):
    """API key info (without actual key)."""
    
    id: str
    user_id: str
    name: str | None
    created_at: str
    last_used_at: str | None
    active: bool
    rate_limit_tier: str


class ListKeysResponse(BaseModel):
    """Response for listing API keys."""
    
    keys: list[KeyInfo]
    count: int


class RevokeKeyResponse(BaseModel):
    """Response after revoking an API key."""
    
    success: bool
    message: str


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_api_key_manager(request: Request) -> APIKeyManager:
    """Dependency to get the API key manager from app state."""
    return request.app.state.api_key_manager


def get_audit_logger(request: Request) -> AuditLogger:
    """Dependency to get the audit logger from app state."""
    return request.app.state.audit_logger


def get_limiter(request: Request) -> Limiter:
    """Dependency to get the rate limiter from app state."""
    return request.app.state.limiter


APIKeyManagerDep = Annotated[APIKeyManager, Depends(get_api_key_manager)]
AuditLoggerDep = Annotated[AuditLogger, Depends(get_audit_logger)]


# ---------------------------------------------------------------------------
# Create Key (requires master key)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=CreateKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key",
)
async def create_api_key(
    request: Request,
    body: CreateKeyRequest,
    key_manager: APIKeyManagerDep,
    audit_logger: AuditLoggerDep,
    _: RequireMasterKey,  # Require master key for key creation
    _limit: EnforceKeyLimit = None,
) -> CreateKeyResponse:
    """
    Create a new API key for a user.
    
    **Requires master key** (X-API-Key header).
    
    The full key is returned ONLY in this response.
    Store it securely - it cannot be retrieved again.
    
    Rate limit: 5 requests/minute.
    """
    try:
        api_key = await key_manager.create_key(
            user_id=body.user_id,
            name=body.name,
            rate_limit_tier=body.rate_limit_tier,
        )
        
        # Audit log
        await audit_logger.log_key_created(
            user_id=body.user_id,
            key_id=api_key.id,
            ip_address=get_client_ip(request),
        )
        
        return CreateKeyResponse(
            id=api_key.id,
            key=api_key.key,
            user_id=api_key.user_id,
            name=api_key.name,
            rate_limit_tier=api_key.rate_limit_tier,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create API key: {str(e)}",
        )


# ---------------------------------------------------------------------------
# List Keys (authenticated user sees their own keys)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=ListKeysResponse,
    summary="List your API keys",
)
async def list_api_keys(
    request: Request,
    key_manager: APIKeyManagerDep,
    current_user: CurrentUser,
) -> ListKeysResponse:
    """
    List all API keys for the authenticated user.
    
    Note: The actual key values are never shown (only metadata).
    """
    keys = await key_manager.list_keys(current_user.user_id)
    
    return ListKeysResponse(
        keys=[
            KeyInfo(
                id=k.id,
                user_id=k.user_id,
                name=k.name,
                created_at=k.created_at,
                last_used_at=k.last_used_at,
                active=k.active,
                rate_limit_tier=k.rate_limit_tier,
            )
            for k in keys
        ],
        count=len(keys),
    )


# ---------------------------------------------------------------------------
# Revoke Key (user can revoke their own keys)
# ---------------------------------------------------------------------------


@router.delete(
    "/{key_id}",
    response_model=RevokeKeyResponse,
    summary="Revoke an API key",
)
async def revoke_api_key(
    request: Request,
    key_id: str,
    key_manager: APIKeyManagerDep,
    audit_logger: AuditLoggerDep,
    current_user: CurrentUser,
) -> RevokeKeyResponse:
    """
    Revoke (deactivate) an API key.
    
    Users can only revoke their own keys.
    Revoked keys cannot be used for authentication.
    """
    success = await key_manager.revoke_key(key_id, current_user.user_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Key {key_id} not found or already revoked",
        )
    
    # Audit log
    await audit_logger.log_key_revoked(
        user_id=current_user.user_id,
        key_id=key_id,
        ip_address=get_client_ip(request),
        success=True,
    )
    
    return RevokeKeyResponse(
        success=True,
        message=f"API key {key_id} has been revoked",
    )


# ---------------------------------------------------------------------------
# Get Key Info
# ---------------------------------------------------------------------------


@router.get(
    "/{key_id}",
    response_model=KeyInfo,
    summary="Get API key info",
)
async def get_api_key_info(
    key_id: str,
    key_manager: APIKeyManagerDep,
    current_user: CurrentUser,
) -> KeyInfo:
    """
    Get information about a specific API key.
    
    Users can only view their own keys.
    The actual key value is never shown.
    """
    key_info = await key_manager.get_key_info(key_id)
    
    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Key {key_id} not found",
        )
    
    # Security: Ensure user can only see their own keys
    if key_info.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Key {key_id} not found",  # Don't reveal it exists
        )
    
    return KeyInfo(
        id=key_info.id,
        user_id=key_info.user_id,
        name=key_info.name,
        created_at=key_info.created_at,
        last_used_at=key_info.last_used_at,
        active=key_info.active,
        rate_limit_tier=key_info.rate_limit_tier,
    )
