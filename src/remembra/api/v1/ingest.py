"""Ingestion endpoints - import external data sources into memories."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from remembra.auth.middleware import CurrentUser, get_client_ip
from remembra.config import Settings, get_settings
from remembra.core.limiter import limiter
from remembra.ingestion.changelog import ChangelogParser, ChangelogRelease
from remembra.models.memory import StoreRequest
from remembra.security.audit import AuditLogger
from remembra.services.memory import MemoryService

router = APIRouter(prefix="/ingest", tags=["ingestion"])


def get_memory_service(request: Request) -> MemoryService:
    """Dependency to get the memory service from app state."""
    return request.app.state.memory_service


def get_audit_logger(request: Request) -> AuditLogger:
    """Dependency to get the audit logger from app state."""
    return request.app.state.audit_logger


MemoryServiceDep = Annotated[MemoryService, Depends(get_memory_service)]
AuditLoggerDep = Annotated[AuditLogger, Depends(get_audit_logger)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


# ---------------------------------------------------------------------------
# Request/Response Models
# ---------------------------------------------------------------------------


class ChangelogIngestRequest(BaseModel):
    """Request to ingest a changelog."""
    
    content: str | None = Field(
        default=None,
        description="Raw markdown content of the changelog",
    )
    file_path: str | None = Field(
        default=None,
        description="Path to a CHANGELOG.md file (server-side)",
    )
    project_id: str = Field(
        default="default",
        description="Project namespace for stored memories",
    )
    project_name: str | None = Field(
        default=None,
        description="Human-readable project name for context",
    )
    max_releases: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of releases to ingest",
    )
    skip_unreleased: bool = Field(
        default=True,
        description="Skip [Unreleased] section",
    )


class ChangelogIngestResponse(BaseModel):
    """Response from changelog ingestion."""
    
    releases_parsed: int
    memories_stored: int
    memory_ids: list[str]
    errors: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Changelog Ingestion
# ---------------------------------------------------------------------------


@router.post(
    "/changelog",
    response_model=ChangelogIngestResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ingest project history from a CHANGELOG.md",
)
@limiter.limit("10/minute")
async def ingest_changelog(
    request: Request,
    body: ChangelogIngestRequest,
    memory_service: MemoryServiceDep,
    audit_logger: AuditLoggerDep,
    current_user: CurrentUser,
    settings: SettingsDep,
) -> ChangelogIngestResponse:
    """
    Parse a CHANGELOG.md and store each release as a memory.
    
    Supports:
    - Keep a Changelog format (https://keepachangelog.com/)
    - Most markdown changelogs with ## version headers
    
    Each release becomes a memory with version/date metadata,
    making project history searchable and recallable.
    
    **Usage (content):**
    ```json
    {
      "content": "## [1.0.0] - 2024-01-15\\n### Added\\n- Feature X",
      "project_name": "my-project"
    }
    ```
    
    **Usage (file path):**
    ```json
    {
      "file_path": "/path/to/CHANGELOG.md",
      "project_name": "my-project"
    }
    ```
    
    Rate limit: 10 requests/minute.
    """
    if not body.content and not body.file_path:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Either 'content' or 'file_path' must be provided",
        )
    
    parser = ChangelogParser()
    releases: list[ChangelogRelease] = []
    errors: list[str] = []
    
    # Parse changelog
    try:
        if body.file_path:
            releases = parser.parse_file(body.file_path)
        else:
            releases = parser.parse(body.content)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Changelog file not found: {body.file_path}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse changelog: {str(e)}",
        )
    
    if not releases:
        return ChangelogIngestResponse(
            releases_parsed=0,
            memories_stored=0,
            memory_ids=[],
            errors=["No releases found in changelog"],
        )
    
    # Filter releases
    if body.skip_unreleased:
        releases = [r for r in releases if r.version.lower() != "unreleased"]
    
    releases = releases[:body.max_releases]
    
    # Store each release as a memory
    memory_ids: list[str] = []
    project_prefix = f"{body.project_name}: " if body.project_name else ""
    
    for release in releases:
        try:
            # Build content string
            content = release.to_memory_content()
            if body.project_name:
                content = f"Project {body.project_name} - {content}"
            
            # Build metadata
            metadata = release.to_metadata()
            if body.project_name:
                metadata["project_name"] = body.project_name
            
            # Store via memory service
            store_request = StoreRequest(
                user_id=current_user.user_id,
                content=content,
                project_id=body.project_id,
                metadata=metadata,
            )
            
            result = await memory_service.store(
                store_request,
                source="changelog_ingestion",
                trust_score=1.0,  # Changelogs are trusted
            )
            
            if result.id:
                memory_ids.append(result.id)
                
        except Exception as e:
            errors.append(f"Failed to store release {release.version}: {str(e)}")
    
    # Audit log
    await audit_logger.log_memory_store(
        user_id=current_user.user_id,
        memory_id=f"changelog:{len(memory_ids)}_releases",
        api_key_id=current_user.api_key_id,
        ip_address=get_client_ip(request),
        success=len(memory_ids) > 0,
        error="; ".join(errors) if errors else None,
    )
    
    return ChangelogIngestResponse(
        releases_parsed=len(releases),
        memories_stored=len(memory_ids),
        memory_ids=memory_ids,
        errors=errors,
    )
