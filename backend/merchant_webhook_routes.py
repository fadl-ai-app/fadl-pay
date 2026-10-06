from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from security.merchant_session import (
    get_session_merchant,
    get_session_role,
    verify_csrf,
)
from security.rbac import require_permission

from webhooks.endpoint_manager import (
    create_webhook_endpoint,
    get_webhook_endpoint,
    update_webhook_endpoint_status,
)
from webhooks.dispatcher import get_merchant_webhook_endpoint


router = APIRouter(
    prefix="/merchant",
    tags=["merchant-webhook"],
)

SESSION_COOKIE = "fadl_merchant_session"


class WebhookCreateRequest(BaseModel):
    url: str = Field(min_length=1, max_length=2048)


class WebhookStatusRequest(BaseModel):
    status: str


def _authenticated_merchant(request: Request):
    session_token = request.cookies.get(SESSION_COOKIE)

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    merchant = get_session_merchant(session_token)

    if not merchant:
        raise HTTPException(
            status_code=401,
            detail="Merchant session is invalid or expired",
        )

    return session_token, merchant


def _authorized(request: Request, permission: str):
    session_token, merchant = _authenticated_merchant(request)

    role = get_session_role(session_token)

    require_permission(role, permission)

    return session_token, merchant


@router.get("/webhook")
async def get_merchant_webhook(request: Request):
    """
    Read-only webhook endpoint information.

    Secret is NEVER returned.
    """
    _, merchant = _authorized(request, "webhook.read")

    endpoint = get_merchant_webhook_endpoint(merchant)

    if not endpoint:
        return {
            "configured": False,
            "endpoint": None,
        }

    return {
        "configured": True,
        "endpoint": {
            "id": endpoint.get("id"),
            "merchant_reference": endpoint.get("merchant_reference"),
            "url": endpoint.get("url"),
            "status": endpoint.get("status"),
            "created_at": endpoint.get("created_at"),
            "updated_at": endpoint.get("updated_at"),
        },
    }


@router.post("/webhook")
async def create_merchant_webhook(
    request: Request,
    payload: WebhookCreateRequest,
):
    """
    Create a webhook endpoint.

    The secret is returned once.
    """
    session_token, merchant = _authorized(
        request,
        "webhook.manage",
    )

    verify_csrf(request)

    merchant_reference = merchant.get("merchant_reference")

    if not merchant_reference:
        raise HTTPException(
            status_code=400,
            detail="Merchant reference is unavailable",
        )

    endpoint = create_webhook_endpoint(
        merchant_reference=merchant_reference,
        url=payload.url,
    )

    return {
        "success": True,
        "endpoint": {
            "id": endpoint.get("id"),
            "url": endpoint.get("url"),
            "status": endpoint.get("status"),
            "created_at": endpoint.get("created_at"),
        },
        "secret": endpoint.get("secret"),
        "warning": (
            "The webhook secret is shown once only. "
            "Store it securely."
        ),
    }


@router.post("/webhook/{endpoint_id}/status")
async def update_merchant_webhook_status(
    endpoint_id: int,
    request: Request,
    payload: WebhookStatusRequest,
):
    """
    Update webhook endpoint status for the authenticated merchant only.
    """
    _, merchant = _authorized(
        request,
        "webhook.manage",
    )

    verify_csrf(request)

    merchant_reference = merchant.get("merchant_reference")

    if not merchant_reference:
        raise HTTPException(
            status_code=400,
            detail="Merchant reference is unavailable",
        )

    allowed = {"active", "inactive", "disabled"}

    if payload.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail="Invalid webhook status",
        )

    endpoint = get_webhook_endpoint(
        endpoint_id=endpoint_id,
        merchant_reference=merchant_reference,
    )

    if not endpoint:
        raise HTTPException(
            status_code=404,
            detail="Webhook endpoint not found",
        )

    updated = update_webhook_endpoint_status(
        endpoint_id=endpoint_id,
        merchant_reference=merchant_reference,
        status=payload.status,
    )

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Webhook endpoint not found",
        )

    return {
        "success": True,
        "endpoint_id": endpoint_id,
        "status": payload.status,
    }
