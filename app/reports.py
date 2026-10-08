from __future__ import annotations

import csv
import io
from datetime import datetime
from typing import Optional

from database.database import get_connection
from security.merchant_rbac import require_permission


def get_reports(
    merchant_reference: str,
    role: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    currency: Optional[str] = None,
):
    """
    Read-only merchant report.

    No INSERT / UPDATE / DELETE is performed.
    """
    if not merchant_reference:
        raise PermissionError("Authentication required")

    require_permission(role, "reports.read")

    clauses = ["merchant_reference = ?"]
    params = [merchant_reference]

    if start_date:
        clauses.append("created_at >= ?")
        params.append(start_date)

    if end_date:
        clauses.append("created_at <= ?")
        params.append(end_date)

    if status:
        clauses.append("status = ?")
        params.append(status)

    if currency:
        clauses.append("currency = ?")
        params.append(currency)

    where_sql = " AND ".join(clauses)

    conn = get_connection()

    try:
        rows = conn.execute(
            f"""
            SELECT
                transaction_reference,
                merchant_reference,
                amount,
                currency,
                status,
                payment_method,
                created_at,
                updated_at
            FROM transactions
            WHERE {where_sql}
            ORDER BY created_at DESC
            """,
            params,
        ).fetchall()

        data = [dict(row) for row in rows]

        total_count = len(data)
        paid_count = sum(1 for x in data if x["status"] == "paid")
        pending_count = sum(1 for x in data if x["status"] == "pending")
        failed_count = sum(1 for x in data if x["status"] == "failed")

        paid_amount = sum(
            int(x["amount"] or 0)
            for x in data
            if x["status"] == "paid"
        )

        return {
            "merchant_reference": merchant_reference,
            "filters": {
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "currency": currency,
            },
            "summary": {
                "total_transactions": total_count,
                "paid_transactions": paid_count,
                "pending_transactions": pending_count,
                "failed_transactions": failed_count,
                "paid_amount": paid_amount,
            },
            "transactions": data,
        }

    finally:
        conn.close()


def export_reports_csv(report: dict) -> str:
    output = io.StringIO()

    rows = report.get("transactions", [])

    if not rows:
        writer = csv.writer(output)
        writer.writerow([
            "transaction_reference",
            "merchant_reference",
            "amount",
            "currency",
            "status",
            "payment_method",
            "created_at",
            "updated_at",
        ])
        return output.getvalue()

    writer = csv.DictWriter(
        output,
        fieldnames=[
            "transaction_reference",
            "merchant_reference",
            "amount",
            "currency",
            "status",
            "payment_method",
            "created_at",
            "updated_at",
        ],
        extrasaction="ignore",
    )

    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue()
