
# ============================================================
# 💰 FADL PAY — Financial Administration
# ============================================================

import sqlite3
from pathlib import Path

DB_PATH = (
    Path(__file__).resolve().parent.parent
    / "database"
    / "fadl_pay.db"
)


def get_financial_summary():
    """
    قراءة مالية فقط.
    لا تقوم هذه الوحدة بتعديل قاعدة البيانات.
    """

    connection = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True
    )
    connection.row_factory = sqlite3.Row

    summary = connection.execute("""
        SELECT
            COUNT(*) AS total_transactions,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'paid' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS paid_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'pending' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS pending_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'refunded' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS refunded_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'failed' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS failed_amount,

            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'cancelled' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS cancelled_amount

        FROM transactions
    """).fetchone()

    currencies = connection.execute("""
        SELECT
            currency,
            COUNT(*) AS transactions,
            COALESCE(SUM(amount), 0) AS gross_amount,
            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'paid' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS paid_amount,
            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'refunded' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS refunded_amount
        FROM transactions
        GROUP BY currency
        ORDER BY currency
    """).fetchall()

    merchants = connection.execute("""
        SELECT
            merchant_reference,
            COUNT(*) AS transactions,
            COALESCE(SUM(amount), 0) AS gross_amount,
            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'paid' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS paid_amount,
            COALESCE(
                SUM(
                    CASE
                        WHEN status = 'refunded' THEN amount
                        ELSE 0
                    END
                ), 0
            ) AS refunded_amount
        FROM transactions
        GROUP BY merchant_reference
        ORDER BY gross_amount DESC
    """).fetchall()

    connection.close()

    return {
        "summary": dict(summary),
        "currencies": [dict(row) for row in currencies],
        "merchants": [dict(row) for row in merchants],
    }


def search_transactions(
    query="",
    status="",
    payment_method="",
    currency="",
    limit=100,
):
    """
    البحث والفلترة في سجل المعاملات فقط.
    لا تقوم هذه الوحدة بتعديل قاعدة البيانات.
    """

    connection = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True
    )
    connection.row_factory = sqlite3.Row

    query = str(query or "").strip()
    status = str(status or "").strip()
    payment_method = str(payment_method or "").strip()
    currency = str(currency or "").strip()

    conditions = []
    parameters = []

    if query:
        conditions.append("""
            (
                transaction_reference LIKE ?
                OR merchant_reference LIKE ?
                OR customer_reference LIKE ?
            )
        """)
        like_query = f"%{query}%"
        parameters.extend([
            like_query,
            like_query,
            like_query,
        ])

    if status:
        conditions.append("status = ?")
        parameters.append(status)

    if payment_method:
        conditions.append("payment_method = ?")
        parameters.append(payment_method)

    if currency:
        conditions.append("currency = ?")
        parameters.append(currency)

    where_clause = ""

    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT
            transaction_reference,
            merchant_reference,
            customer_reference,
            amount,
            currency,
            payment_method,
            status,
            created_at
        FROM transactions
        {where_clause}
        ORDER BY created_at DESC
        LIMIT ?
    """

    parameters.append(int(limit))

    rows = connection.execute(
        sql,
        parameters,
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]

def get_transaction_list(limit=100):
    """
    قراءة سجل المعاملات فقط.
    لا تقوم هذه الوحدة بتعديل قاعدة البيانات.
    """

    connection = sqlite3.connect(
        f"file:{DB_PATH}?mode=ro",
        uri=True
    )
    connection.row_factory = sqlite3.Row

    rows = connection.execute("""
        SELECT
            transaction_reference,
            merchant_reference,
            customer_reference,
            amount,
            currency,
            payment_method,
            status,
            created_at
        FROM transactions
        ORDER BY created_at DESC
        LIMIT ?
    """, (int(limit),)).fetchall()

    connection.close()

    return [dict(row) for row in rows]
