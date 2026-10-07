import sqlite3

from webhooks.endpoint_manager import get_webhook_endpoint


from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = str(PROJECT_ROOT / "database" / "fadl_pay.db")



# Maximum number of webhook delivery attempts.
MAX_ATTEMPTS = 5

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


# ================================================================================================
# FADL PAY — WEBHOOK DELIVERY ENGINE V1
# ================================================================================================

import json
import urllib.request
from datetime import datetime, timezone

from webhooks.signature import sign_payload


MAX_WEBHOOK_ATTEMPTS = 5


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _get_dispatch_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def create_webhook_delivery(
    merchant_reference,
    event_id,
    transaction_reference,
    payload,
):
    endpoint = get_merchant_webhook_endpoint(
        merchant_reference
    )

    if endpoint is None:
        return {
            "created": False,
            "reason": "No active webhook endpoint",
        }

    if isinstance(payload, dict):
        payload_text = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    else:
        payload_text = str(payload)

    signature = sign_payload(
        payload_text,
        endpoint["webhook_secret"],
    )

    now = _utc_now()

    connection = _get_dispatch_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO webhook_deliveries (
            event_id,
            transaction_reference,
            webhook_url,
            payload,
            signature,
            status,
            attempts,
            response_status,
            error_message,
            created_at,
            updated_at,
            webhook_endpoint_id
        )
        VALUES (?, ?, ?, ?, ?, 'pending', 0, NULL, NULL, ?, ?, ?)
    """, (
        event_id,
        transaction_reference,
        endpoint["webhook_url"],
        payload_text,
        signature,
        now,
        now,
        endpoint["id"],
    ))

    delivery_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return {
        "created": True,
        "delivery_id": delivery_id,
        "endpoint_id": endpoint["id"],
        "webhook_url": endpoint["webhook_url"],
        "status": "pending",
        "attempts": 0,
        "signature": signature,
    }


def get_webhook_delivery(
    delivery_id,
    merchant_reference,
):
    connection = _get_dispatch_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            d.*,
            e.merchant_reference
        FROM webhook_deliveries d
        JOIN webhook_endpoints e
          ON e.id = d.webhook_endpoint_id
        WHERE d.id = ?
          AND e.merchant_reference = ?
    """, (
        delivery_id,
        merchant_reference,
    ))

    row = cursor.fetchone()

    connection.close()

    return dict(row) if row else None


def list_webhook_deliveries(
    merchant_reference,
    limit=50,
):
    limit = max(1, min(int(limit), 200))

    connection = _get_dispatch_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            d.id,
            d.event_id,
            d.transaction_reference,
            d.webhook_url,
            d.status,
            d.attempts,
            d.response_status,
            d.error_message,
            d.created_at,
            d.updated_at,
            d.webhook_endpoint_id
        FROM webhook_deliveries d
        JOIN webhook_endpoints e
          ON e.id = d.webhook_endpoint_id
        WHERE e.merchant_reference = ?
        ORDER BY d.id DESC
        LIMIT ?
    """, (
        merchant_reference,
        limit,
    ))

    rows = [dict(row) for row in cursor.fetchall()]

    connection.close()

    return rows


def _update_delivery_result(
    delivery_id,
    merchant_reference,
    status,
    attempts,
    response_status=None,
    error_message=None,
):
    connection = _get_dispatch_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE webhook_deliveries
        SET
            status = ?,
            attempts = ?,
            response_status = ?,
            error_message = ?,
            updated_at = ?
        WHERE id = ?
          AND webhook_endpoint_id IN (
              SELECT id
              FROM webhook_endpoints
              WHERE merchant_reference = ?
          )
    """, (
        status,
        attempts,
        response_status,
        error_message,
        _utc_now(),
        delivery_id,
        merchant_reference,
    ))

    changed = cursor.rowcount == 1

    if changed:
        connection.commit()

    connection.close()

    return changed


def dispatch_webhook_delivery(
    delivery_id,
    merchant_reference,
    timeout=10,
):
    delivery = get_webhook_delivery(
        delivery_id,
        merchant_reference,
    )

    if delivery is None:
        return {
            "success": False,
            "reason": "Webhook delivery not found",
        }

    if delivery["status"] == "delivered":
        return {
            "success": True,
            "delivery_id": delivery_id,
            "status": "delivered",
            "attempts": delivery["attempts"],
            "response_status": delivery["response_status"],
        }

    if int(delivery["attempts"]) >= MAX_WEBHOOK_ATTEMPTS:
        return {
            "success": False,
            "delivery_id": delivery_id,
            "status": "failed",
            "attempts": delivery["attempts"],
            "reason": "Maximum webhook attempts reached",
        }

    attempt_number = int(delivery["attempts"]) + 1

    request = urllib.request.Request(
        delivery["webhook_url"],
        data=delivery["payload"].encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "X-FADL-PAY-Signature": delivery["signature"],
            "X-FADL-PAY-Delivery-ID": str(delivery_id),
            "X-FADL-PAY-Event-ID": str(delivery["event_id"]),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(
            request,
            timeout=timeout,
        ) as response:
            response_status = int(response.status)

        if 200 <= response_status < 300:
            _update_delivery_result(
                delivery_id,
                merchant_reference,
                "delivered",
                attempt_number,
                response_status,
                None,
            )

            return {
                "success": True,
                "delivery_id": delivery_id,
                "status": "delivered",
                "attempts": attempt_number,
                "response_status": response_status,
            }

        next_status = (
            "failed"
            if attempt_number >= MAX_WEBHOOK_ATTEMPTS
            else "retry_pending"
        )

        _update_delivery_result(
            delivery_id,
            merchant_reference,
            next_status,
            attempt_number,
            response_status,
            f"Webhook returned HTTP {response_status}",
        )

        return {
            "success": False,
            "delivery_id": delivery_id,
            "status": next_status,
            "attempts": attempt_number,
            "response_status": response_status,
        }

    except Exception as exc:
        next_status = (
            "failed"
            if attempt_number >= MAX_WEBHOOK_ATTEMPTS
            else "retry_pending"
        )

        _update_delivery_result(
            delivery_id,
            merchant_reference,
            next_status,
            attempt_number,
            None,
            str(exc)[:1000],
        )

        return {
            "success": False,
            "delivery_id": delivery_id,
            "status": next_status,
            "attempts": attempt_number,
            "error": str(exc)[:1000],
        }


def retry_webhook_delivery(
    delivery_id,
    merchant_reference,
    timeout=10,
):
    delivery = get_webhook_delivery(
        delivery_id,
        merchant_reference,
    )

    if delivery is None:
        return {
            "success": False,
            "reason": "Webhook delivery not found",
        }

    if delivery["status"] == "delivered":
        return {
            "success": False,
            "reason": "Webhook delivery already delivered",
        }

    if int(delivery["attempts"]) >= MAX_WEBHOOK_ATTEMPTS:
        return {
            "success": False,
            "reason": "Maximum webhook attempts reached",
        }

    return dispatch_webhook_delivery(
        delivery_id,
        merchant_reference,
        timeout,
    )

