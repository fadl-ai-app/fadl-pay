
from datetime import datetime, timezone
from uuid import uuid4

from database.database import get_connection


VALID_MERCHANT_STATUSES = {
    "pending",
    "active",
    "suspended",
    "disabled",
}

# Explicit merchant lifecycle policy.
#
# pending   -> active
# active    -> suspended / disabled
# suspended -> active / disabled
# disabled  -> terminal
#
# A merchant cannot jump arbitrarily between states.
ALLOWED_MERCHANT_TRANSITIONS = {
    "pending": {"active"},
    "active": {"suspended", "disabled"},
    "suspended": {"active", "disabled"},
    "disabled": set(),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_merchant(name, email):
    if not name or not email:
        raise ValueError("Merchant name and email are required")

    merchant_reference = "MER-" + uuid4().hex.upper()
    now = utc_now()

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO merchants (
            merchant_reference,
            name,
            email,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            merchant_reference,
            name,
            email,
            "pending",
            now,
        ),
    )

    connection.commit()
    connection.close()

    return merchant_reference


def get_merchant(merchant_reference):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM merchants
        WHERE merchant_reference = ?
        """,
        (merchant_reference,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return dict(row)


def update_merchant_status(merchant_reference, new_status):
    if new_status not in VALID_MERCHANT_STATUSES:
        raise ValueError("Invalid merchant status")

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT status
        FROM merchants
        WHERE merchant_reference = ?
        """,
        (merchant_reference,),
    )

    merchant = cursor.fetchone()

    if merchant is None:
        connection.close()
        raise ValueError("Merchant not found")

    current_status = merchant["status"]

    if current_status == new_status:
        connection.close()
        raise ValueError(
            f"Merchant status is already {new_status}"
        )

    allowed_statuses = ALLOWED_MERCHANT_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        connection.close()
        raise ValueError(
            f"Invalid merchant status transition: "
            f"{current_status} -> {new_status}"
        )

    cursor.execute(
        """
        UPDATE merchants
        SET status = ?
        WHERE merchant_reference = ?
        """,
        (
            new_status,
            merchant_reference,
        ),
    )

    if cursor.rowcount == 0:
        connection.close()
        raise ValueError("Merchant not found")

    connection.commit()
    connection.close()

    return get_merchant(merchant_reference)

# ============================================================
# 💳 MERCHANT PASSWORD AUTH
# ============================================================

from security.merchant_auth import (
    hash_password,
    verify_password,
    normalize_email,
)


def set_merchant_password(
    merchant_reference: str,
    password: str,
) -> bool:
    """
    Set or replace the Argon2 password hash for a merchant.
    """
    if not merchant_reference:
        raise ValueError("Merchant reference is required")

    password_hash = hash_password(password)

    from database.database import get_connection

    connection = get_connection()

    try:
        cursor = connection.execute(
            """
            UPDATE merchants
            SET password_hash = ?
            WHERE merchant_reference = ?
            """,
            (
                password_hash,
                merchant_reference,
            ),
        )

        connection.commit()

        return cursor.rowcount == 1

    finally:
        connection.close()


def authenticate_merchant(
    email: str,
    password: str,
):
    """
    Authenticate an active merchant by email/password.

    Returns merchant data without password_hash.
    Returns None on authentication failure.
    """
    normalized_email = normalize_email(email)

    from database.database import get_connection

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

