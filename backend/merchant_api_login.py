"""
FADL PAY — Merchant API Key Login

WORK-stage authentication bridge:

API Key
    ↓
verify_api_key()
    ↓
merchant_reference
    ↓
MerchantSession
    ↓
HttpOnly Secure Cookie
"""

from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel

from security.merchant_api_session import (
    create_session_from_api_key,
)
from security.merchant_session import (
    SESSION_TTL_SECONDS,
)


router = APIRouter(
    prefix="/merchant",
    tags=["merchant-auth"],
)


SESSION_COOKIE = "fadl_merchant_session"


class MerchantApiKeyLoginRequest(BaseModel):
    api_key: str


@router.post("/api-key-login")
def merchant_api_key_login(
    payload: MerchantApiKeyLoginRequest,
    response: Response,
):
    """
    Authenticate a merchant with an FADL PAY API key.

    The raw API key is validated but is never stored
    in the merchant session or session cookie.
    """

    if not payload.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
        )

    try:
        session = create_session_from_api_key(
            payload.api_key
        )

    except PermissionError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API key",
        )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session.session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_TTL_SECONDS,
        path="/",
    )

    return {
        "authenticated": True,
        "merchant_reference": session.merchant_reference,
        "csrf_token": session.csrf_token,
    }
