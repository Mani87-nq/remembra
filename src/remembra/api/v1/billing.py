"""Billing endpoints – /api/v1/billing.

Supports both Stripe and Paddle based on REMEMBRA_BILLING_PROVIDER config.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from remembra.auth.middleware import CurrentUser
from remembra.config import Settings, get_settings
from remembra.core.limiter import limiter

router = APIRouter(prefix="/billing", tags=["billing"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class PlanInfo(BaseModel):
    """Plan information."""
    id: str
    name: str
    price_monthly: int = Field(description="Price in cents")
    price_yearly: int | None = Field(None, description="Yearly price in cents")
    features: list[str]
    limits: dict[str, Any]


class PlansResponse(BaseModel):
    """Available plans."""
    plans: list[PlanInfo]
    provider: str = Field(description="Billing provider: 'stripe' or 'paddle'")


class CheckoutRequest(BaseModel):
    """Checkout request."""
    plan: str = Field(description="Plan ID: 'pro' or 'team'")
    billing_cycle: str = Field(default="monthly", description="'monthly' or 'yearly'")


class CheckoutResponse(BaseModel):
    """Checkout response."""
    checkout_url: str | None = Field(None, description="Redirect URL for hosted checkout")
    client_token: str | None = Field(None, description="Client token for overlay checkout (Paddle)")
    transaction_id: str | None = Field(None, description="Transaction ID for overlay checkout (Paddle)")
    provider: str


class PortalResponse(BaseModel):
    """Customer portal response."""
    portal_url: str


# ---------------------------------------------------------------------------
# Billing Provider Detection
# ---------------------------------------------------------------------------


def get_billing_provider(settings: Settings) -> str:
    """Determine which billing provider to use."""
    provider = getattr(settings, 'billing_provider', None)
    if provider:
        return provider.lower()
    
    # Auto-detect based on configured keys
    if getattr(settings, 'paddle_api_key', None):
        return 'paddle'
    if getattr(settings, 'stripe_secret_key', None):
        return 'stripe'
    
    return 'none'


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/plans",
    response_model=PlansResponse,
    summary="Get available plans",
)
@limiter.limit("60/minute")
async def get_plans(
    request: Request,
    settings: SettingsDep,
) -> PlansResponse:
    """Get available subscription plans.
    
    Returns plan details including pricing and features.
    Does not require authentication.
    """
    provider = get_billing_provider(settings)
    
    if provider == 'paddle':
        from remembra.cloud.plans_paddle import PLANS, PlanTier
        
        plans = []
        for tier in [PlanTier.PRO, PlanTier.TEAM]:
            plan = PLANS[tier]
            plans.append(PlanInfo(
                id=tier.value,
                name=plan.name,
                price_monthly=plan.price_monthly,
                price_yearly=plan.price_yearly,
                features=plan.features,
                limits={
                    "max_memories": plan.max_memories,
                    "max_stores_per_month": plan.max_stores_per_month,
                    "max_recalls_per_month": plan.max_recalls_per_month,
                    "max_api_keys": plan.max_api_keys,
                    "max_users": plan.max_users,
                },
            ))
        
        return PlansResponse(plans=plans, provider="paddle")
    
    elif provider == 'stripe':
        from remembra.cloud.plans import PLANS, PlanTier
        
        plans = []
        for tier in [PlanTier.PRO, PlanTier.ENTERPRISE]:
            plan = PLANS[tier]
            plans.append(PlanInfo(
                id=tier.value,
                name=plan.name,
                price_monthly=plan.price_monthly,
                price_yearly=getattr(plan, 'price_yearly', None),
                features=getattr(plan, 'features', []),
                limits={
                    "max_memories": plan.max_memories,
                    "max_stores_per_month": plan.max_stores_per_month,
                    "max_recalls_per_month": plan.max_recalls_per_month,
                    "max_api_keys": plan.max_api_keys,
                    "max_users": plan.max_users,
                },
            ))
        
        return PlansResponse(plans=plans, provider="stripe")
    
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing is not configured on this instance.",
        )


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Create checkout session",
)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    body: Annotated[CheckoutRequest, Body(...)],
    current_user: CurrentUser,
    settings: SettingsDep,
) -> CheckoutResponse:
    """Create a checkout session for plan upgrade.
    
    For Paddle: Returns client token for overlay checkout.
    For Stripe: Returns redirect URL for hosted checkout.
    """
    provider = get_billing_provider(settings)
    
    if provider == 'paddle':
        from remembra.cloud.billing_paddle import PaddleBillingManager
        from remembra.cloud.paddle_config import get_paddle_config
        from remembra.cloud.plans_paddle import PlanTier
        
        config = get_paddle_config()
        billing = PaddleBillingManager(
            api_key=config.api_key,
            webhook_secret=config.webhook_secret or "",
            sandbox=config.sandbox,
        )
        
        try:
            plan_tier = PlanTier(body.plan.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid plan: {body.plan}. Choose 'pro' or 'team'.",
            )
        
        result = await billing.create_checkout_session(
            customer_id=None,  # Will be created
            plan=plan_tier,
            user_id=current_user.user_id,
            email=current_user.email,
        )
        
        return CheckoutResponse(
            checkout_url=result.get("checkout_url"),
            client_token=result.get("client_token"),
            transaction_id=result.get("transaction_id"),
            provider="paddle",
        )
    
    elif provider == 'stripe':
        # Delegate to existing cloud checkout
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/api/v1/cloud/checkout"},
            detail="Use /api/v1/cloud/checkout for Stripe billing.",
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing is not configured on this instance.",
        )


@router.post(
    "/portal",
    response_model=PortalResponse,
    summary="Get customer portal URL",
)
@limiter.limit("10/minute")
async def get_portal(
    request: Request,
    current_user: CurrentUser,
    settings: SettingsDep,
) -> PortalResponse:
    """Get URL to customer billing portal.
    
    Users can manage subscriptions, update payment methods, view invoices.
    """
    provider = get_billing_provider(settings)
    
    if provider == 'paddle':
        from remembra.cloud.billing_paddle import PaddleBillingManager
        from remembra.cloud.paddle_config import get_paddle_config
        
        config = get_paddle_config()
        billing = PaddleBillingManager(
            api_key=config.api_key,
            webhook_secret=config.webhook_secret or "",
            sandbox=config.sandbox,
        )
        
        # Get customer ID from user profile
        # For now, return the Paddle customer portal URL
        url = await billing.create_portal_session(
            customer_id=current_user.user_id,  # We'd need to look this up
        )
        
        return PortalResponse(portal_url=url)
    
    elif provider == 'stripe':
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/api/v1/cloud/portal"},
            detail="Use /api/v1/cloud/portal for Stripe billing.",
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Billing is not configured on this instance.",
        )


@router.post(
    "/webhook/paddle",
    summary="Paddle webhook handler",
    include_in_schema=False,
)
async def paddle_webhook(request: Request) -> dict[str, str]:
    """Process Paddle webhook events.
    
    Handles subscription lifecycle events.
    Validates via Paddle webhook signature.
    """
    settings = get_settings()
    
    provider = get_billing_provider(settings)
    if provider != 'paddle':
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Paddle billing is not configured.",
        )
    
    from remembra.cloud.billing_paddle import PaddleBillingManager
    from remembra.cloud.paddle_config import get_paddle_config
    
    config = get_paddle_config()
    billing = PaddleBillingManager(
        api_key=config.api_key,
        webhook_secret=config.webhook_secret or "",
        sandbox=config.sandbox,
    )
    
    # Get raw body and signature
    payload = await request.body()
    signature = request.headers.get("paddle-signature", "")
    
    try:
        event = billing.verify_webhook(payload.decode(), signature)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook signature: {e}",
        )
    
    # Process the event
    result = await billing.handle_webhook_event(event)
    
    # TODO: Apply result to metering system (similar to Stripe webhook)
    
    return {"status": "ok", "action": result.action if result else "ignored"}
