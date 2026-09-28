"""
FADL PAY — Integration V2 Runtime Core

Authorization order:

    Integration
        ↓
    Credential
        ↓
    Integration status / expiry
        ↓
    Merchant authorization
        ↓
    Scope
        ↓
    Existing application boundary

Credential storage:
    SHA-256 digest in integration_credentials.credential_hash

Raw credential secrets are never persisted.

This module is intentionally isolated from:
    - Payment UI
    - Financial Admin
    - Merchant Login
    - Transaction Engine
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import sqlite3
from typing import Optional


APPROVED_SCOPES = frozenset(
    {
        "transactions:create",
        "transactions:read",
        "sandbox:status",
    }
)

ACTIVE_STATUS = "active"


class IntegrationV2Error(Exception):
    """Base Integration V2 authorization error."""


class IntegrationNotFound(IntegrationV2Error):
    pass


class IntegrationDisabled(IntegrationV2Error):
    pass


class IntegrationExpired(IntegrationV2Error):
    pass


class CredentialRejected(IntegrationV2Error):
    pass


class CredentialExpired(IntegrationV2Error):
    pass


class MerchantAuthorizationRejected(IntegrationV2Error):
    pass


class MerchantAuthorizationExpired(IntegrationV2Error):
    pass


class ScopeRejected(IntegrationV2Error):
    pass


@dataclass(frozen=True)
class IntegrationContext:
    integration_pk: int
    integration_id: str
    credential_id: str
    merchant_reference: str
    scope: str


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None

    text = value.strip()

    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)

    return parsed.astimezone(timezone.utc)


def _expired(value: Optional[str]) -> bool:
    parsed = _parse_timestamp(value)
    return parsed is not None and parsed <= _utc_now()


def hash_integration_credential(secret: str) -> str:
    """
    Return the SHA-256 hexadecimal digest of an Integration V2 secret.

    The raw secret must never be persisted by this module.
    """
    if not isinstance(secret, str) or not secret:
        raise ValueError("Credential secret must be a non-empty string.")

    return hashlib.sha256(
        secret.encode("utf-8")
    ).hexdigest()


def verify_integration_credential(
    supplied_secret: str,
    stored_hash: str,
) -> bool:
    """
    Verify a supplied Integration V2 secret against its stored
    SHA-256 digest using constant-time comparison.
    """
    if not isinstance(supplied_secret, str):
        return False

    if not isinstance(stored_hash, str):
        return False

    calculated = hash_integration_credential(
        supplied_secret
    )

    return hmac.compare_digest(
        calculated,
        stored_hash,
    )


def _get_integration(
    conn: sqlite3.Connection,
    integration_id: str,
):
    row = conn.execute(
        """
        SELECT
            id,
            integration_id,
            status,
            expires_at
        FROM integrations
        WHERE integration_id = ?
        """,
        (integration_id,),
    ).fetchone()

    if row is None:
        raise IntegrationNotFound("Integration not found.")

    return row


def _get_credential(
    conn: sqlite3.Connection,
    integration_pk: int,
    credential_id: str,
):
    row = conn.execute(
        """
        SELECT
            credential_id,
            credential_hash,
            status,
            expires_at,
            revoked_at
        FROM integration_credentials
        WHERE integration_id = ?
          AND credential_id = ?
        """,
        (integration_pk, credential_id),
    ).fetchone()

    if row is None:
        raise CredentialRejected("Credential not found.")

    return row


def _get_authorization(
    conn: sqlite3.Connection,
    integration_pk: int,
    merchant_reference: str,
):
    row = conn.execute(
        """
        SELECT
            id,
            status,
            expires_at,
            revoked_at
        FROM integration_merchant_authorizations
        WHERE integration_id = ?
          AND merchant_reference = ?
          AND status = 'active'
        ORDER BY id DESC
        LIMIT 1
        """,
        (integration_pk, merchant_reference),
    ).fetchone()

    if row is None:
        raise MerchantAuthorizationRejected(
            "Active merchant authorization not found."
        )

    return row


def _require_scope(
    conn: sqlite3.Connection,
    authorization_id: int,
    scope: str,
):
    if scope not in APPROVED_SCOPES:
        raise ScopeRejected("Unknown or unsupported scope.")

    exists = conn.execute(
        """
        SELECT 1
        FROM integration_scopes
        WHERE integration_merchant_authorization_id = ?
          AND scope = ?
        LIMIT 1
        """,
        (authorization_id, scope),
    ).fetchone()

    if exists is None:
        raise ScopeRejected("Required scope is not granted.")


def authorize(
    conn: sqlite3.Connection,
    *,
    integration_id: str,
    credential_id: str,
    credential_secret: str,
    merchant_reference: str,
    scope: str,
) -> IntegrationContext:
    """
    Perform the complete Integration V2 authorization boundary.

    This function is READ-ONLY.

    It:
        1. verifies Integration
        2. verifies credential
        3. verifies Integration status/expiry
        4. verifies merchant authorization
        5. verifies scope

    It does NOT:
        - create transactions
        - modify transactions
        - write the database
        - call the Transaction Engine
        - alter existing authentication
    """

    integration = _get_integration(
        conn,
        integration_id,
    )

    integration_pk = integration[0]
    stored_integration_id = integration[1]
    integration_status = integration[2]
    integration_expires_at = integration[3]

    if integration_status != ACTIVE_STATUS:
        raise IntegrationDisabled(
            "Integration is not active."
        )

    if _expired(integration_expires_at):
        raise IntegrationExpired(
            "Integration has expired."
        )

    credential = _get_credential(
        conn,
        integration_pk,
        credential_id,
    )

    stored_credential_id = credential[0]
    stored_hash = credential[1]
    credential_status = credential[2]
    credential_expires_at = credential[3]
    revoked_at = credential[4]

    if credential_status != ACTIVE_STATUS:
        raise CredentialRejected(
            "Credential is not active."
        )

    if revoked_at:
        raise CredentialRejected(
            "Credential has been revoked."
        )

    if _expired(credential_expires_at):
        raise CredentialExpired(
            "Credential has expired."
        )

    if not verify_integration_credential(
        credential_secret,
        stored_hash,
    ):
        raise CredentialRejected(
            "Credential verification failed."
        )

    authorization = _get_authorization(
        conn,
        integration_pk,
        merchant_reference,
    )

    authorization_id = authorization[0]
    authorization_status = authorization[1]
    authorization_expires_at = authorization[2]
    authorization_revoked_at = authorization[3]

    if authorization_status != ACTIVE_STATUS:
        raise MerchantAuthorizationRejected(
            "Merchant authorization is not active."
        )

    if authorization_revoked_at:
        raise MerchantAuthorizationRejected(
            "Merchant authorization has been revoked."
        )

    if _expired(authorization_expires_at):
        raise MerchantAuthorizationExpired(
            "Merchant authorization has expired."
        )

    _require_scope(
        conn,
        authorization_id,
        scope,
    )

    return IntegrationContext(
        integration_pk=integration_pk,
        integration_id=stored_integration_id,
        credential_id=stored_credential_id,
        merchant_reference=merchant_reference,
        scope=scope,
    )
