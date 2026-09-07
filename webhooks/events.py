import json
from datetime import datetime, timezone

from database.database import get_connection


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def create_transaction_event(
    transaction_reference,
    event_type,
    event_data
):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO transaction_events (
            transaction_reference,
            event_type,
            event_data,
            created_at
        )
        VALUES (?, ?, ?, ?)
    """, (
        transaction_reference,
        event_type,
        json.dumps(event_data, ensure_ascii=False),
        utc_now()
    ))

    connection.commit()

    event_id = cursor.lastrowid

    connection.close()

    return event_id


def get_transaction_events(transaction_reference):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            transaction_reference,
            event_type,
            event_data,
            created_at
        FROM transaction_events
        WHERE transaction_reference = ?
        ORDER BY id ASC
    """, (transaction_reference,))

    rows = cursor.fetchall()

    connection.close()

    events = []

    for row in rows:
        events.append({
            "id": row["id"],
            "transaction_reference": row["transaction_reference"],
            "event_type": row["event_type"],
            "event_data": json.loads(row["event_data"]),
            "created_at": row["created_at"]
        })

    return events
