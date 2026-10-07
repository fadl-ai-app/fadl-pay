from fastapi import APIRouter, HTTPException, Request

from database.database import get_connection
from security.merchant_rbac import require_permission
from security.merchant_session import (
    get_session_merchant,
    get_session_role,
)


router = APIRouter(
    prefix="/merchant",
    tags=["merchant-reports"],
)

SESSION_COOKIE = "fadl_merchant_session"


def _authorized_merchant(request: Request):
    session_token = request.cookies.get(SESSION_COOKIE)

    if not session_token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    merchant = get_session_merchant(session_token)

    if not merchant:
        raise HTTPException(
            status_code=401,
            detail="Merchant session is invalid or expired",
        )

    role = get_session_role(session_token)

    require_permission(
        role,
        "reports.read",
    )

    merchant_reference = merchant.get(
        "merchant_reference"
    )

    if not merchant_reference:
        raise HTTPException(
            status_code=400,
            detail="Merchant reference is unavailable",
        )

    return merchant_reference


@router.get("/reports")
async def get_merchant_reports(request: Request):
    merchant_reference = _authorized_merchant(request)

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) AS transaction_count,
            COALESCE(SUM(amount), 0) AS total_amount
        FROM transactions
        WHERE merchant_reference = ?
    """, (merchant_reference,))

    summary = dict(cursor.fetchone())

    cursor.execute("""
        SELECT
            status,
            COUNT(*) AS count,
            COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE merchant_reference = ?
        GROUP BY status
        ORDER BY status
    """, (merchant_reference,))

    by_status = [
        dict(row)
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT
            currency,
            COUNT(*) AS count,
            COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE merchant_reference = ?
        GROUP BY currency
        ORDER BY currency
    """, (merchant_reference,))

    by_currency = [
        dict(row)
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT
            payment_method,
            COUNT(*) AS count,
            COALESCE(SUM(amount), 0) AS amount
        FROM transactions
        WHERE merchant_reference = ?
        GROUP BY payment_method
        ORDER BY payment_method
    """, (merchant_reference,))

    by_payment_method = [
        dict(row)
        for row in cursor.fetchall()
    ]

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM ledger_entries
        WHERE merchant_reference = ?
    """, (merchant_reference,))

    ledger_count = int(
        cursor.fetchone()["count"]
    )

    cursor.execute("""
        SELECT COUNT(*) AS count
        FROM transaction_events e
        JOIN transactions t
          ON t.transaction_reference =
             e.transaction_reference
        WHERE t.merchant_reference = ?
    """, (merchant_reference,))

    event_count = int(
        cursor.fetchone()["count"]
    )

    cursor.execute("""
        SELECT
            transaction_reference,
            amount,
            currency,
            status,
            payment_method,
            created_at,
            updated_at
        FROM transactions
        WHERE merchant_reference = ?
        ORDER BY id DESC
        LIMIT 50
    """, (merchant_reference,))

    recent_transactions = [
        dict(row)
        for row in cursor.fetchall()
    ]

    connection.close()

    return {
        "merchant_reference": merchant_reference,
        "summary": summary,
        "by_status": by_status,
        "by_currency": by_currency,
        "by_payment_method": by_payment_method,
        "ledger_count": ledger_count,
        "event_count": event_count,
        "recent_transactions": recent_transactions,
    }
