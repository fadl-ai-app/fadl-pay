
# ============================================================
# 💰 FADL PAY — Financial Administration
# ============================================================

import sqlite3
from pathlib import Path

DB_PATH = (
    Path("/content/drive/MyDrive/FADL_PAY_SAVED")
    / "FADL_PAY_NEW_UI_SAFE_2026-09-08_06-02-50"
    / "WORKING_DATABASE"
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
