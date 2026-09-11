
from datetime import datetime, timezone
from uuid import uuid4
import json
import hashlib

from database.database import get_connection


VALID_STATUSES = {
    "pending",
    "paid",
    "failed",
    "cancelled",
    "refunded",
}

ALLOWED_TRANSITIONS = {
    "pending": {"paid", "failed", "cancelled"},
    "paid": {"refunded"},
    "failed": set(),
    "cancelled": set(),
    "refunded": set(),
}


def utc_now():
    return datetime.now(timezone.utc).isoformat()



def build_request_hash(
    amount,
    currency,
    customer_reference,
    payment_method,
):
    request_data = (
        f"{amount}|"
        f"{currency}|"
        f"{customer_reference}|"
        f"{payment_method}"
    )

    return hashlib.sha256(
        request_data.encode("utf-8")
    ).hexdigest()


def create_transaction(
    merchant_reference,
    amount,
    currency="SDG",
    customer_reference=None,
    payment_method=None,
    idempotency_key=None,
):
    if amount <= 0:
        raise ValueError("Amount must be greater than zero")

    # Idempotency Key validation
    if idempotency_key is not None:
        if not isinstance(idempotency_key, str):
            raise ValueError(
                "Idempotency key must be a string"
            )

        idempotency_key = idempotency_key.strip()

        if not idempotency_key:
            raise ValueError(
                "Idempotency key cannot be empty"
            )

        if len(idempotency_key) > 255:
            raise ValueError(
                "Idempotency key is too long"
            )

    request_hash = build_request_hash(
        amount=amount,
        currency=currency,
        customer_reference=customer_reference,
        payment_method=payment_method,
    )

    connection = get_connection()
    cursor = connection.cursor()

    try:
        # --------------------------------------------------
        # Verify merchant
        # --------------------------------------------------

        cursor.execute(
            """
            SELECT merchant_reference, status
            FROM merchants
            WHERE merchant_reference = ?
            """,
            (merchant_reference,),
        )

        merchant = cursor.fetchone()

        if merchant is None:
            raise ValueError("Merchant not found")

        if merchant["status"] != "active":
            raise ValueError(
                f"Merchant is not active: {merchant['status']}"
            )

        # --------------------------------------------------
        # Idempotency lookup
        # --------------------------------------------------

        if idempotency_key is not None:

            cursor.execute(
                """
                SELECT
                    transaction_reference,
                    request_hash
                FROM idempotency_keys
                WHERE merchant_reference = ?
                  AND idempotency_key = ?
                """,
                (
                    merchant_reference,
                    idempotency_key,
                ),
            )

            existing = cursor.fetchone()

            if existing is not None:

                if existing["request_hash"] != request_hash:
                    raise ValueError(
                        "Idempotency key already used "
                        "with different request data"
                    )

                # Same request → return original transaction
                connection.commit()

                return existing["transaction_reference"]

        # --------------------------------------------------
        # Create new transaction
        # --------------------------------------------------

        transaction_reference = (
            "FP-" + uuid4().hex.upper()
        )

        now = utc_now()

        cursor.execute(
            """
            INSERT INTO transactions (
                transaction_reference,
                merchant_reference,
                customer_reference,
                amount,
                currency,
                status,
                payment_method,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                transaction_reference,
                merchant_reference,
                customer_reference,
                amount,
                currency,
                "pending",
                payment_method,
                now,
                now,
            ),
        )

        cursor.execute(
            """
            INSERT INTO transaction_events (
                transaction_reference,
                event_type,
                event_data,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                transaction_reference,
                "transaction.created",
                json.dumps({
                    "status": "pending",
                    "amount": amount,
                    "currency": currency,
                    "merchant_reference":
                        merchant_reference,
                }),
                now,
            ),
        )

        # --------------------------------------------------
        # Store Idempotency Key
        # --------------------------------------------------

        if idempotency_key is not None:

            cursor.execute(
                """
                INSERT INTO idempotency_keys (
                    merchant_reference,
                    idempotency_key,
                    transaction_reference,
                    request_hash,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    merchant_reference,
                    idempotency_key,
                    transaction_reference,
                    request_hash,
                    now,
                ),
            )

        connection.commit()

        return transaction_reference

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_transaction(transaction_reference, merchant_reference=None):
    """
    Retrieve a transaction.

    If merchant_reference is provided, the transaction must
    belong to that merchant.
    """
    if not transaction_reference:
        return None

    connection = get_connection()
    cursor = connection.cursor()

    if merchant_reference is None:
        cursor.execute(
            """
            SELECT
                id,
                transaction_reference,
                merchant_reference,
                customer_reference,
                amount,
                currency,
                status,
                payment_method,
                created_at,
                updated_at
            FROM transactions
            WHERE transaction_reference = ?
            """,
            (transaction_reference,),
        )
    else:
        cursor.execute(
            """
            SELECT
                id,
                transaction_reference,
                merchant_reference,
                customer_reference,
                amount,
                currency,
                status,
                payment_method,
                created_at,
                updated_at
            FROM transactions
            WHERE transaction_reference = ?
              AND merchant_reference = ?
            """,
            (transaction_reference, merchant_reference),
        )

    row = cursor.fetchone()
    connection.close()

    if row is None:
        return None

    return dict(row)


def _post_ledger_entry(
    connection,
    transaction_reference,
    merchant_reference,
    entry_type,
    amount,
    currency,
    description=None,
):
    """
    Create exactly one ledger entry for a transaction + entry type.
    """

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id
        FROM ledger_entries
        WHERE transaction_reference = ?
          AND entry_type = ?
        ORDER BY id
        LIMIT 1
        """,
        (
            transaction_reference,
            entry_type,
        ),
    )

    existing = cursor.fetchone()

    if existing is not None:
        return existing["id"]

    cursor.execute(
        """
        INSERT INTO ledger_entries (
            transaction_reference,
            merchant_reference,
            entry_type,
            amount,
            currency,
            description,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            transaction_reference,
            merchant_reference,
            entry_type,
            amount,
            currency,
            description,
            utc_now(),
        ),
    )

    return cursor.lastrowid

def update_transaction_status(transaction_reference, new_status):
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"Invalid transaction status: {new_status}"
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT merchant_reference, status, amount, currency
        FROM transactions
        WHERE transaction_reference = ?
        """,
        (transaction_reference,),
    )

    row = cursor.fetchone()

    if row is None:
        connection.close()
        raise ValueError("Transaction not found")

    merchant_reference = row["merchant_reference"]
    old_status = row["status"]
    amount = row["amount"]
    currency = row["currency"]

    allowed_next_statuses = ALLOWED_TRANSITIONS.get(old_status, set())

    if new_status not in allowed_next_statuses:
        connection.close()
        raise ValueError(
            f"Invalid status transition: {old_status} -> {new_status}"
        )

    now = utc_now()

    event_data = {
        "old_status": old_status,
        "new_status": new_status,
    }

    cursor.execute(
        """
        UPDATE transactions
        SET status = ?, updated_at = ?
        WHERE transaction_reference = ?
        """,
        (
            new_status,
            now,
            transaction_reference,
        ),
    )

    cursor.execute(
        """
        INSERT INTO transaction_events (
            transaction_reference,
            event_type,
            event_data,
            created_at
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            transaction_reference,
            "transaction.status_changed",
            json.dumps(event_data),
            now,
        ),
    )

    event_id = cursor.lastrowid

    ledger_entry_id = None

    if new_status == "paid":
        ledger_entry_id = _post_ledger_entry(
            connection=connection,
            transaction_reference=transaction_reference,
            merchant_reference=merchant_reference,
            entry_type="CREDIT",
            amount=amount,
            currency=currency,
            description="Payment credited",
        )

    elif new_status == "refunded":
        ledger_entry_id = _post_ledger_entry(
            connection=connection,
            transaction_reference=transaction_reference,
            merchant_reference=merchant_reference,
            entry_type="DEBIT_REFUND",
            amount=amount,
            currency=currency,
            description="Payment refunded",
        )

    connection.commit()
    connection.close()

    # -----------------------------------------
    # Webhook Dispatch
    # -----------------------------------------

    webhook_result = None

    try:
        from webhooks.service import dispatch_webhook

        webhook_result = dispatch_webhook(
            merchant_reference=merchant_reference,
            event_id=event_id,
            event_type="transaction.status_changed",
            transaction_reference=transaction_reference,
            event_data=event_data,
        )

    except Exception as error:
        webhook_result = {
            "success": False,
            "reason": "Webhook dispatch error",
            "error": str(error),
        }

    return {
        "transaction_reference": transaction_reference,
        "old_status": old_status,
        "new_status": new_status,
        "event_id": event_id,
        "ledger_entry_id": ledger_entry_id,
        "webhook": webhook_result,
    }
