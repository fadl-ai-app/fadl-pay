import sqlite3
import gradio as gr

import database.database as db_module
from security.merchant_session import get_session_merchant


def dashboard_data(merchant_reference):
    """
    Return dashboard data for the authenticated merchant only.
    """

    if not merchant_reference:
        raise PermissionError("Authentication required")

    conn = sqlite3.connect(db_module.DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        merchant = conn.execute(
            """
            SELECT merchant_reference, name, email, status
            FROM merchants
            WHERE merchant_reference = ?
            LIMIT 1
            """,
            (merchant_reference,),
        ).fetchone()

        if not merchant:
            raise ValueError("Merchant not found")

        transactions = conn.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE merchant_reference = ?
            """,
            (merchant_reference,),
        ).fetchone()[0]

        ledger = conn.execute(
            """
            SELECT COUNT(*)
            FROM ledger_entries
            WHERE merchant_reference = ?
            """,
            (merchant_reference,),
        ).fetchone()[0]

        events = conn.execute(
            """
            SELECT COUNT(*)
            FROM transaction_events
            WHERE json_extract(event_data, '$.merchant_reference') = ?
            """,
            (merchant_reference,),
        ).fetchone()[0]

        return {
            "merchant_reference": merchant["merchant_reference"],
            "name": merchant["name"],
            "email": merchant["email"],
            "status": merchant["status"],
            "transactions": transactions,
            "ledger": ledger,
            "events": events,
        }

    finally:
        conn.close()


def dashboard_data_from_session(session_token):
    """
    Resolve merchant identity exclusively from the
    server-side authenticated session.
    """

    if not session_token:
        raise PermissionError("Authentication required")

    merchant_reference = get_session_merchant(session_token)

    if not merchant_reference:
        raise PermissionError("Invalid or expired session")

    return dashboard_data(merchant_reference)


def create_dashboard_from_session(session_token):
    """
    Create dashboard data using only the authenticated
    server-side merchant session.
    """

    data = dashboard_data_from_session(session_token)

    return {
        "merchant": data["name"],
        "merchant_reference": data["merchant_reference"],
        "email": data["email"],
        "status": data["status"],
        "transactions": data["transactions"],
        "ledger": data["ledger"],
        "events": data["events"],
    }


def create_dashboard(session_token=None):

    if not session_token:
        raise PermissionError("Authentication required")

    data = create_dashboard_from_session(session_token)

    with gr.Blocks() as demo:

        gr.Markdown(
            "# 🏪 FADL PAY\n## لوحة تحكم التاجر"
        )

        info = gr.Markdown(
            f"""
### 👤 التاجر
**{data["merchant"]}**

### 🆔 Merchant Reference
`{data["merchant_reference"]}`

### ✉️ البريد
{data["email"]}

### 🟢 الحالة
{data["status"]}

---

### 💳 المبيعات
**عدد العمليات:** {data["transactions"]}

### 💰 المالية
**الحركات المالية:** {data["ledger"]}

### 🔔 الإشعارات
**الأحداث:** {data["events"]}
"""
        )

    return demo
