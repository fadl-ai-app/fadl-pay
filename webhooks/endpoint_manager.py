from datetime import datetime, timezone
from urllib.parse import urlparse
import sqlite3

from webhooks.signature import generate_webhook_secret
from webhooks.ssrf import validate_webhook_url


DB_PATH = "/content/Fadl_Pay/database/fadl_pay.db"

VALID_STATUSES = {
    "active",
    "disabled",
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_webhook_endpoint(
    merchant_reference,
    webhook_url,
):
    validate_webhook_url(webhook_url)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    # التأكد من وجود التاجر وأنه نشط
    cursor.execute("""
        SELECT
            merchant_reference,
            status
        FROM merchants
        WHERE merchant_reference = ?
    """, (merchant_reference,))

    merchant = cursor.fetchone()

    if merchant is None:
        connection.close()
        raise ValueError("Merchant not found")

    if merchant[1] != "active":
        connection.close()
        raise ValueError(
            "Merchant must be active to create a webhook endpoint"
        )

    webhook_secret = generate_webhook_secret()
    now = utc_now()

    cursor.execute("""
        INSERT INTO webhook_endpoints (
            merchant_reference,
            webhook_url,
            webhook_secret,
            status,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        merchant_reference,
        webhook_url,
        webhook_secret,
        "active",
        now,
        now,
    ))

    endpoint_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "id": endpoint_id,
        "merchant_reference": merchant_reference,
        "webhook_url": webhook_url,
        "webhook_secret": webhook_secret,
        "status": "active",
    }


def get_webhook_endpoint(
    endpoint_id,
    merchant_reference=None,
):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    if merchant_reference is None:
        connection.close()
        raise ValueError(
            "Merchant authorization is required"
        )

    cursor.execute("""
        SELECT *
        FROM webhook_endpoints
        WHERE id = ?
          AND merchant_reference = ?
    """, (
        endpoint_id,
        merchant_reference,
    ))

    row = cursor.fetchone()

    connection.close()

    return dict(row) if row else None


def update_webhook_endpoint_status(
    endpoint_id,
    new_status,
    merchant_reference,
):
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid webhook endpoint status: {new_status}"
        )

    if not merchant_reference:
        raise ValueError(
            "Merchant authorization required"
        )

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE webhook_endpoints
        SET
            status = ?,
            updated_at = ?
        WHERE id = ?
          AND merchant_reference = ?
    """, (
        new_status,
        utc_now(),
        endpoint_id,
        merchant_reference,
    ))

    if cursor.rowcount == 0:
        connection.close()
        raise ValueError(
            "Webhook endpoint not found or unauthorized"
        )

    connection.commit()
    connection.close()

    return {
        "id": endpoint_id,
        "merchant_reference": merchant_reference,
        "status": new_status,
    }


