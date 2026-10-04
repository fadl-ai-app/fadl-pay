from __future__ import annotations

import sqlite3

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database.database import get_connection

from security.merchant_auth import (
    normalize_email,
    verify_password,
    hash_password,
    is_login_blocked,
    record_login_failure,
    clear_login_failures,
)

from security.merchant_session import (
    create_session,
    get_session,
    get_csrf_token,
    revoke_session,
    verify_csrf,
)


router = APIRouter(
    prefix="/merchant",
    tags=["merchant-auth"],
)


SESSION_COOKIE = "fadl_merchant_session"


class MerchantLoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class MerchantLogoutRequest(BaseModel):
    csrf_token: str = Field(min_length=1, max_length=512)


class MerchantChangePasswordRequest(BaseModel):
    current_password: str = Field(
        min_length=1,
        max_length=256,
    )
    new_password: str = Field(
        min_length=8,
        max_length=256,
    )
    csrf_token: str = Field(
        min_length=1,
        max_length=512,
    )



def authenticate_merchant_for_login(
    email: str,
    password: str,
):
    """
    Isolated merchant authentication.

    This function intentionally does NOT import backend.merchant.

    It reads only the merchant authentication fields required for:
        email
        password_hash
        status
        merchant_reference
        name
    """

    normalized_email = normalize_email(email)

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT
                merchant_reference,
                name,
                email,
                status,
                password_hash,
                role
            FROM merchants
            WHERE lower(email) = ?
            LIMIT 1
            """,
            (normalized_email,),
        ).fetchone()

        if row is None:
            return None

        if row["status"] != "active":
            return None

        stored_hash = row["password_hash"]

        if not stored_hash:
            return None

        if not verify_password(password, stored_hash):
            return None

        return {
            "merchant_reference": row["merchant_reference"],
            "name": row["name"],
            "email": row["email"],
            "status": row["status"],
            "role": row["role"] or "owner",
        }

    finally:
        connection.close()


# -------------------------------------------------------------------------
# Login
# -------------------------------------------------------------------------

@router.post("/login")
async def merchant_login(
    payload: MerchantLoginRequest,
    request: Request,
):
    try:
        email = normalize_email(payload.email)

    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    if is_login_blocked(email):
        raise HTTPException(
            status_code=429,
            detail="Too many login attempts",
        )

    merchant = authenticate_merchant_for_login(
        email,
        payload.password,
    )

    if merchant is None:
        record_login_failure(email)

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password",
        )

    clear_login_failures(email)

    session = create_session(
        merchant["merchant_reference"],
        merchant.get("role", "owner"),
    )

    response = JSONResponse(
        {
            "authenticated": True,
            "merchant": {
                "merchant_reference":
                    merchant["merchant_reference"],
                "name":
                    merchant["name"],
                "email":
                    merchant["email"],
            },
            "csrf_token":
                session.csrf_token,
        }
    )

    response.set_cookie(
        key=SESSION_COOKIE,
        value=session.session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=8 * 60 * 60,
        path="/",
    )

    return response


# -------------------------------------------------------------------------
# Change merchant password
# -------------------------------------------------------------------------

@router.post("/password")
async def merchant_change_password(
    payload: MerchantChangePasswordRequest,
    request: Request,
):
    token = request.cookies.get(
        SESSION_COOKIE
    )

    session = get_session(token)

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    if not verify_csrf(
        token,
        payload.csrf_token,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token",
        )

    if (
        not isinstance(payload.current_password, str)
        or not payload.current_password
    ):
        raise HTTPException(
            status_code=400,
            detail="Current password is required",
        )

    if (
        not isinstance(payload.new_password, str)
        or len(payload.new_password) < 8
    ):
        raise HTTPException(
            status_code=400,
            detail="New password must contain at least 8 characters",
        )

    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=400,
            detail="New password must be different from current password",
        )

    merchant_reference = session.merchant_reference

    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT password_hash
            FROM merchants
            WHERE merchant_reference = ?
            LIMIT 1
            """,
            (merchant_reference,),
        ).fetchone()

        if row is None:
            raise HTTPException(
                status_code=404,
                detail="Merchant not found",
            )

        stored_hash = row["password_hash"]

        if not stored_hash:
            raise HTTPException(
                status_code=400,
                detail="Merchant password is not configured",
            )

        if not verify_password(
            payload.current_password,
            stored_hash,
        ):
            raise HTTPException(
                status_code=401,
                detail="Current password is incorrect",
            )

        new_hash = hash_password(
            payload.new_password
        )

        connection.execute(
            """
            UPDATE merchants
            SET password_hash = ?
            WHERE merchant_reference = ?
            """,
            (
                new_hash,
                merchant_reference,
            ),
        )

        connection.commit()

    finally:
        connection.close()

    # Security: invalidate the session used for the password change.
    revoke_session(token)

    response = JSONResponse(
        {
            "success": True,
            "authenticated": False,
            "password_changed": True,
            "reauthentication_required": True,
        }
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
    )

    return response


# -------------------------------------------------------------------------
# Current merchant
# -------------------------------------------------------------------------

@router.get("/me")
async def merchant_me(
    request: Request,
):
    token = request.cookies.get(
        SESSION_COOKIE
    )

    session = get_session(token)

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    return {
        "authenticated": True,
        "merchant_reference":
            session.merchant_reference,
        "csrf_token":
            get_csrf_token(token),
    }


# -------------------------------------------------------------------------
# Logout
# -------------------------------------------------------------------------

@router.post("/logout")
async def merchant_logout(
    payload: MerchantLogoutRequest,
    request: Request,
):
    token = request.cookies.get(
        SESSION_COOKIE
    )

    session = get_session(token)

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    if not verify_csrf(
        token,
        payload.csrf_token,
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid CSRF token",
        )

    revoke_session(token)

    response = JSONResponse(
        {
            "authenticated": False,
            "logged_out": True,
        }
    )

    response.delete_cookie(
        key=SESSION_COOKIE,
        path="/",
    )

    return response
