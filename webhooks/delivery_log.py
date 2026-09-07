from datetime import datetime, timezone
import json
import sqlite3

DB_PATH = "/content/Fadl_Pay/database/fadl_pay.db"


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_delivery_log(
    event_id,
    transaction_reference,
    webhook_endpoint_id,
    webhook_url,
    payload,
    signature,
):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        now = utc_now()

        cursor.execute("""
            INSERT INTO webhook_deliveries (
                event_id,
                webhook_endpoint_id,
                transaction_reference,
                webhook_url,
                payload,
                signature,
                status,
                attempts,
                response_status,
                error_message,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id,
            webhook_endpoint_id,
            transaction_reference,
            webhook_url,
            json.dumps(payload, ensure_ascii=False),
            signature,
            "pending",
            0,
            None,
            None,
            now,
            now,
        ))

        delivery_id = cursor.lastrowid

        connection.commit()

        return delivery_id

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def update_delivery_log(
    delivery_id,
    status,
    attempts,
    response_status=None,
    error_message=None,
):
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    try:
        cursor.execute("""
            UPDATE webhook_deliveries
            SET
                status = ?,
                attempts = ?,
                response_status = ?,
                error_message = ?,
                updated_at = ?
            WHERE id = ?
        """, (
            status,
            attempts,
            response_status,
            error_message,
            utc_now(),
            delivery_id,
        ))

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_delivery_log(delivery_id):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM webhook_deliveries
        WHERE id = ?
    """, (delivery_id,))

    row = cursor.fetchone()
    connection.close()

    return dict(row) if row else None


def get_delivery_by_event_endpoint(
    event_id,
    webhook_endpoint_id,
):
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            event_id,
            webhook_endpoint_id,
            transaction_reference,
            webhook_url,
            payload,
            signature,
            status,
            attempts,
            response_status,
            error_message,
            created_at,
            updated_at
        FROM webhook_deliveries
        WHERE event_id = ?
          AND webhook_endpoint_id = ?
        ORDER BY id ASC
        LIMIT 1
    """, (
        event_id,
        webhook_endpoint_id,
    ))

    row = cursor.fetchone()

    connection.close()

    if row is None:
        return None

    return dict(row)
