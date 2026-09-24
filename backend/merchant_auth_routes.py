from __future__ import annotations

import sqlite3
import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from database.database import get_connection

from security.merchant_auth import (
    normalize_email,
    hash_password,
    verify_password,
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


class MerchantRegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=256)


class MerchantLogoutRequest(BaseModel):
    csrf_token: str = Field(min_length=1, max_length=512)


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
                password_hash
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
        }

    finally:
        connection.close()



# -------------------------------------------------------------------------
# Registration CSRF
# -------------------------------------------------------------------------

REGISTRATION_CSRF_COOKIE = "fadl_merchant_registration_csrf"


def _registration_csrf_value(request: Request) -> str | None:
    return request.cookies.get(REGISTRATION_CSRF_COOKIE)


def _registration_csrf_hash(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


@router.get("/register-csrf")
async def merchant_registration_csrf():
    token = secrets.token_urlsafe(32)

    response = JSONResponse(
        {
            "csrf_token": token,
        }
    )

    response.set_cookie(
        key=REGISTRATION_CSRF_COOKIE,
        value=_registration_csrf_hash(token),
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=10 * 60,
        path="/merchant",
    )

    return response


# -------------------------------------------------------------------------
# Registration
# -------------------------------------------------------------------------

@router.post("/register")
async def merchant_register(
    payload: MerchantRegisterRequest,
    request: Request,
):
    csrf_token = request.headers.get("X-CSRF-Token", "").strip()
    stored_csrf_hash = _registration_csrf_value(request)

    if (
        not csrf_token
        or not stored_csrf_hash
        or not secrets.compare_digest(
            _registration_csrf_hash(csrf_token),
            stored_csrf_hash,
        )
    ):
        raise HTTPException(
            status_code=403,
            detail="Invalid registration CSRF token",
        )

    try:
        email = normalize_email(payload.email)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid email address",
        )

    name = payload.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Merchant name is required",
        )

    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    created_at = datetime.now(timezone.utc).isoformat()

    connection = get_connection()

    try:
        existing = connection.execute(
            """
            SELECT merchant_reference
            FROM merchants
            WHERE lower(email) = ?
            LIMIT 1
            """,
            (email,),
        ).fetchone()

        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="A merchant account with this email already exists",
            )

        merchant_reference = None

        for _ in range(10):
            candidate = (
                "MER-"
                + secrets.token_hex(16).upper()
            )

            collision = connection.execute(
                """
                SELECT 1
                FROM merchants
                WHERE merchant_reference = ?
                LIMIT 1
                """,
                (candidate,),
            ).fetchone()

            if collision is None:
                merchant_reference = candidate
                break

        if merchant_reference is None:
            raise HTTPException(
                status_code=503,
                detail="Unable to generate a unique merchant reference",
            )

        try:
            connection.execute(
                """
                INSERT INTO merchants (
                    merchant_reference,
                    name,
                    email,
                    password_hash,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, 'active', ?)
                """,
                (
                    merchant_reference,
                    name,
                    email,
                    password_hash,
                    created_at,
                ),
            )

            connection.commit()

        except sqlite3.IntegrityError:
            connection.rollback()

            raise HTTPException(
                status_code=409,
                detail="A merchant account with this email already exists",
            )

    finally:
        connection.close()

    response = JSONResponse(
        {
            "registered": True,
            "merchant": {
                "merchant_reference": merchant_reference,
                "name": name,
                "email": email,
                "status": "active",
            },
        },
        status_code=201,
    )

    response.delete_cookie(
        key=REGISTRATION_CSRF_COOKIE,
        path="/merchant",
    )

    return response


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
        merchant["merchant_reference"]
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
