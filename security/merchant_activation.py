"""
FADL PAY — Merchant Activation Core

Security boundary:
- No HTTP routes.
- No FastAPI dependency.
- Operational token issuance only.
- Token hashes only are persisted.
- Raw setup tokens are returned once to the caller.
- Only pending merchants without an existing password may be activated.
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from datetime import datetime, timezone, timedelta
from typing import Optional

from security.merchant_auth import hash_password


TOKEN_TABLE = "merchant_password_setup_tokens"
DEFAULT_TOKEN_TTL_MINUTES = 15


class MerchantActivationError(Exception):
    """Base activation error."""


class MerchantNotFoundError(MerchantActivationError):
    pass


class MerchantNotEligibleError(MerchantActivationError):
    pass


class InvalidSetupTokenError(MerchantActivationError):
    pass


class ExpiredSetupTokenError(MerchantActivationError):
    pass


class UsedSetupTokenError(MerchantActivationError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_setup_token(raw_token: str) -> str:
    if not raw_token:
        raise ValueError("Setup token is required")

    return hashlib.sha256(
        raw_token.encode("utf-8")
    ).hexdigest()


def ensure_token_table(connection: sqlite3.Connection) -> None:
    """
    Create the activation token table on the supplied connection.

    The caller controls the database connection.
    No global production DB is opened here.
    """
    connection.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {TOKEN_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_reference TEXT NOT NULL,
            token_hash TEXT NOT NULL UNIQUE,
            expires_at TEXT NOT NULL,
            used_at TEXT,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.commit()


def issue_setup_token(
    connection: sqlite3.Connection,
    merchant_reference: str,
    ttl_minutes: int = DEFAULT_TOKEN_TTL_MINUTES,
) -> str:
    """
    Issue a one-time setup token for a pending merchant.

    Security rules:
    - merchant_reference is the only merchant identifier
    - merchant must exist
    - merchant must be pending
    - merchant must not already have a password
    - raw token is never stored
    - only SHA-256(token) is stored
    """

    if not merchant_reference:
        raise ValueError("Merchant reference is required")

    if ttl_minutes <= 0:
        raise ValueError("Token TTL must be positive")

    row = connection.execute(
        """
        SELECT
            merchant_reference,
            status,
            password_hash
        FROM merchants
        WHERE merchant_reference = ?
        LIMIT 1
        """,
        (merchant_reference,),
    ).fetchone()

    if row is None:
        raise MerchantNotFoundError("Merchant not found")

    merchant_ref, status, password_hash = row

    if status != "pending":
        raise MerchantNotEligibleError(
            f"Merchant status '{status}' cannot be activated"
        )

    if password_hash and str(password_hash).strip():
        raise MerchantNotEligibleError(
            "Merchant already has a password"
        )

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_setup_token(raw_token)

    now = utc_now()
    expires_at = now + timedelta(minutes=ttl_minutes)

    connection.execute(
        f"""
        INSERT INTO {TOKEN_TABLE} (
            merchant_reference,
            token_hash,
            expires_at,
            used_at,
            created_at
        )
        VALUES (?, ?, ?, NULL, ?)
        """,
        (
            merchant_ref,
            token_hash,
            expires_at.isoformat(),
            now.isoformat(),
        ),
    )

    connection.commit()

    # Raw token is returned once and is never persisted.
    return raw_token


def consume_setup_token(
    connection: sqlite3.Connection,
    raw_token: str,
    new_password: str,
) -> str:
    """
    Consume a valid setup token and activate the merchant.

    Successful transaction:
        pending + empty password
            ->
        active + Argon2 password hash
            ->
        token marked used
    """

    if not raw_token:
        raise InvalidSetupTokenError("Setup token is required")

    if not new_password or len(new_password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters"
        )

    token_hash = hash_setup_token(raw_token)

    row = connection.execute(
        f"""
        SELECT
            id,
            merchant_reference,
            expires_at,
            used_at
        FROM {TOKEN_TABLE}
        WHERE token_hash = ?
        LIMIT 1
        """,
        (token_hash,),
    ).fetchone()

    if row is None:
        raise InvalidSetupTokenError("Invalid setup token")

    token_id, merchant_ref, expires_at, used_at = row

    if used_at is not None:
        raise UsedSetupTokenError(
            "Setup token already used"
        )

    expires_dt = datetime.fromisoformat(expires_at)

    if utc_now() >= expires_dt:
        raise ExpiredSetupTokenError(
            "Setup token expired"
        )

    merchant = connection.execute(
        """
        SELECT
            status,
            password_hash
        FROM merchants
        WHERE merchant_reference = ?
        LIMIT 1
        """,
        (merchant_ref,),
    ).fetchone()

    if merchant is None:
        raise MerchantNotFoundError("Merchant not found")

    status, existing_hash = merchant

    if status != "pending":
        raise MerchantNotEligibleError(
            f"Merchant status '{status}' cannot complete setup"
        )

    if existing_hash and str(existing_hash).strip():
        raise MerchantNotEligibleError(
            "Merchant already has a password"
        )

    new_hash = hash_password(new_password)
    used_at_now = utc_now().isoformat()

    # Guarded merchant update.
    merchant_update = connection.execute(
        """
        UPDATE merchants
        SET
            password_hash = ?,
            status = 'active'
        WHERE merchant_reference = ?
          AND status = 'pending'
          AND (
              password_hash IS NULL
              OR trim(password_hash) = ''
          )
        """,
        (
            new_hash,
            merchant_ref,
        ),
    )

    if merchant_update.rowcount != 1:
        connection.rollback()
        raise MerchantNotEligibleError(
            "Merchant activation update rejected"
        )

    # Guarded token consumption.
    token_update = connection.execute(
        f"""
        UPDATE {TOKEN_TABLE}
        SET used_at = ?
        WHERE id = ?
          AND used_at IS NULL
        """,
        (
            used_at_now,
            token_id,
        ),
    )

    if token_update.rowcount != 1:
        connection.rollback()
        raise UsedSetupTokenError(
            "Setup token could not be consumed"
        )

    connection.commit()

    return merchant_ref
