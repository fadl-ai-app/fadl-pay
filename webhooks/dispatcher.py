import sqlite3

from webhooks.endpoint_manager import get_webhook_endpoint


DB_PATH = "/content/Fadl_Pay/database/fadl_pay.db"


def get_merchant_webhook_endpoint(
    merchant_reference,
):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM webhook_endpoints
        WHERE merchant_reference = ?
          AND status = 'active'
        ORDER BY id DESC
        LIMIT 1
    """, (merchant_reference,))

    row = cursor.fetchone()

    connection.close()

    return dict(row) if row else None


def prepare_webhook_dispatch(
    merchant_reference,
    event_id,
    event_type,
    transaction_reference,
    event_data,
):
    endpoint = get_merchant_webhook_endpoint(
        merchant_reference
    )

    if endpoint is None:
        return {
            "ready": False,
            "reason": "No active webhook endpoint",
        }

    return {
        "ready": True,
        "endpoint_id": endpoint["id"],
        "merchant_reference": merchant_reference,
        "webhook_url": endpoint["webhook_url"],
        "event_id": event_id,
        "event_type": event_type,
        "transaction_reference": transaction_reference,
        "event_data": event_data,
    }
