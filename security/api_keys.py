
import hashlib
import secrets

from database.database import get_connection


def generate_api_key():
    """
    Generate a cryptographically secure API key.
    The raw key is returned only once.
    """
    return "fp_test_" + secrets.token_urlsafe(32)


def hash_api_key(api_key):
    return hashlib.sha256(
        api_key.encode("utf-8")
    ).hexdigest()




def create_api_key(merchant_reference):

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

    if merchant[0] != "active":
        connection.close()
        raise ValueError(
            "Merchant must be active to create an API key"
        )

    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_reference TEXT NOT NULL,
            key_hash TEXT UNIQUE NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL
        )
        """
    )

    from datetime import datetime, timezone

    now = datetime.now(timezone.utc).isoformat()

    cursor.execute(
        """
        INSERT INTO api_keys (
            merchant_reference,
            key_hash,
            status,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            merchant_reference,
            api_key_hash,
            "active",
            now,
        ),
    )

    connection.commit()
    connection.close()

    return api_key


def revoke_api_key(
    api_key,
    merchant_reference,
):
    if not api_key:
        raise ValueError("API key required")

    if not merchant_reference:
        raise ValueError(
            "Merchant authorization required"
        )

    api_key_hash = hash_api_key(api_key)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT merchant_reference, status
        FROM api_keys
        WHERE key_hash = ?
        """,
        (api_key_hash,),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        raise ValueError(
            "API key not found or unauthorized"
        )

    if row["merchant_reference"] != merchant_reference:
        connection.close()
        raise ValueError(
            "API key not found or unauthorized"
        )

    if row["status"] != "active":
        connection.close()
        raise ValueError(
            "API key is not active"
        )

    cursor.execute(
        """
        UPDATE api_keys
        SET status = ?
        WHERE key_hash = ?
          AND merchant_reference = ?
        """,
        (
            "revoked",
            api_key_hash,
            merchant_reference,
        ),
    )

    connection.commit()
    connection.close()

    return {
        "success": True,
        "merchant_reference": merchant_reference,
        "status": "revoked",
    }



def revoke_api_key_by_id(
    api_key_id,
    merchant_reference,
):
    """
    Revoke one API key by ID, strictly scoped to its merchant.
    """
    if not merchant_reference:
        raise ValueError("Merchant authorization required")

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            merchant_reference,
            status
        FROM api_keys
        WHERE id = ?
          AND merchant_reference = ?
    """, (
        api_key_id,
        merchant_reference,
    ))

    row = cursor.fetchone()

    if row is None:
        connection.close()
        return False

    if row["status"] != "active":
        connection.close()
        return False

    cursor.execute("""
        UPDATE api_keys
        SET status = 'revoked'
        WHERE id = ?
          AND merchant_reference = ?
          AND status = 'active'
    """, (
        api_key_id,
        merchant_reference,
    ))

    changed = cursor.rowcount == 1

    if changed:
        connection.commit()

    connection.close()

    return changed


def verify_api_key(api_key):
    if not api_key:
        return None

    api_key_hash = hash_api_key(api_key)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            api_keys.merchant_reference,
            api_keys.status AS api_key_status,
            merchants.status AS merchant_status
        FROM api_keys
        INNER JOIN merchants
            ON merchants.merchant_reference =
               api_keys.merchant_reference
        WHERE api_keys.key_hash = ?
        """,
        (api_key_hash,),
    )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    if row["api_key_status"] != "active":
        return None

    if row["merchant_status"] != "active":
        return None

    return row["merchant_reference"]


# FADL_PAY_API_CREDENTIALS_LIST_V1
def list_api_keys(merchant_reference):
    """
    Return non-secret metadata for API credentials belonging ONLY
    to the supplied merchant_reference.

    The raw API key and key_hash are never returned.
    """

    if not merchant_reference:
        return []

    from database.database import get_db_connection

    connection = get_db_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                merchant_reference,
                status,
                created_at
            FROM api_keys
            WHERE merchant_reference = ?
            ORDER BY id DESC
            """,
            (merchant_reference,),
        ).fetchall()

        return [
            {
                "id": row["id"],
                "merchant_reference": row["merchant_reference"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    finally:
        connection.close()
