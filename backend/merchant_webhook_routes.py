from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from security.merchant_session import (
    get_session_merchant,
    get_session_role,
    verify_csrf,
)
from security.merchant_rbac import require_permission

from webhooks.endpoint_manager import (
    create_webhook_endpoint,
    get_webhook_endpoint,
    update_webhook_endpoint_status,
)
from webhooks.dispatcher import get_merchant_webhook_endpoint
from webhooks.delivery_log import (
    get_delivery_by_event_endpoint,
)


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


@router.get("/webhook/endpoints")
async def list_merchant_webhook_endpoints(
    request: Request,
):
    """
    Return webhook endpoints owned by the authenticated merchant.

    Secrets are NEVER returned.
    """
    _authorized(request, "webhook.read")

    session_token = request.cookies.get(SESSION_COOKIE)
    merchant_reference = get_session_merchant(session_token)

    if not merchant_reference:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired merchant session",
        )

    conn = None
    try:
        from database.database import get_connection

        conn = get_connection()

        rows = conn.execute(
            """
            SELECT
                id,
                merchant_reference,
                webhook_url,
                status,
                created_at,
                updated_at
            FROM webhook_endpoints
            WHERE merchant_reference = ?
            ORDER BY id DESC
            """,
            (merchant_reference,),
        ).fetchall()

        endpoints = []

        for row in rows:
            item = dict(row)

            deliveries = conn.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END)
                        AS successful,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END)
                        AS failed,
                    MAX(updated_at) AS last_delivery_at
                FROM webhook_deliveries
                WHERE webhook_endpoint_id = ?
                """,
                (item["id"],),
            ).fetchone()

            item["delivery"] = dict(deliveries) if deliveries else {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "last_delivery_at": None,
            }

            endpoints.append(item)

        return {
            "success": True,
            "merchant_reference": merchant_reference,
            "endpoints": endpoints,
        }

    finally:
        if conn is not None:
            conn.close()


@router.get("/webhook/{endpoint_id}/deliveries")
async def list_webhook_deliveries(
    endpoint_id: int,
    request: Request,
):
    """
    Return delivery history for an endpoint owned by the merchant.
    """
    _authorized(request, "webhook.read")

    session_token = request.cookies.get(SESSION_COOKIE)
    merchant_reference = get_session_merchant(session_token)

    if not merchant_reference:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired merchant session",
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

    from database.database import get_connection

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                id,
                event_id,
                transaction_reference,
                status,
                attempts,
                response_status,
                error_message,
                created_at,
                updated_at
            FROM webhook_deliveries
            WHERE webhook_endpoint_id = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (endpoint_id,),
        ).fetchall()

        return {
            "success": True,
            "endpoint_id": endpoint_id,
            "deliveries": [dict(row) for row in rows],
        }

    finally:
        conn.close()


@router.post("/webhook/{endpoint_id}/retry")
async def retry_webhook_delivery(
    endpoint_id: int,
    request: Request,
):
    """
    Retry the latest failed delivery for an authenticated merchant endpoint.

    The existing webhook service performs its own retry policy.
    """
    _authorized(request, "webhook.manage")
    verify_csrf(request)

    session_token = request.cookies.get(SESSION_COOKIE)
    merchant_reference = get_session_merchant(session_token)

    if not merchant_reference:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired merchant session",
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

    from database.database import get_connection

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT
                transaction_reference
            FROM webhook_deliveries
            WHERE webhook_endpoint_id = ?
              AND status = 'failed'
            ORDER BY id DESC
            LIMIT 1
            """,
            (endpoint_id,),
        ).fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="No failed webhook delivery available for retry",
        )

    from webhooks.service import dispatch_webhook

    result = dispatch_webhook(
        merchant_reference=merchant_reference,
        transaction_reference=row["transaction_reference"],
    )

    return {
        "success": bool(result.get("success")),
        "endpoint_id": endpoint_id,
        "transaction_reference": row["transaction_reference"],
        "delivery": result,
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
