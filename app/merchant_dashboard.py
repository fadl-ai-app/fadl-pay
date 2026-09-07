
import sqlite3
import gradio as gr

DB_PATH = "/content/FADL_PAY_RESTORE/database/fadl_pay.db"


def dashboard_data():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    merchant = cur.execute(
        "SELECT merchant_reference FROM merchants LIMIT 1"
    ).fetchone()

    transactions = cur.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

    ledger = cur.execute(
        "SELECT COUNT(*) FROM ledger_entries"
    ).fetchone()[0]

    events = cur.execute(
        "SELECT COUNT(*) FROM transaction_events"
    ).fetchone()[0]

    conn.close()

    name = merchant[0] if merchant else "غير متوفر"

    return f"""
# 🏪 لوحة التاجر — FADL PAY

## 👤 التاجر
{name}

🟢 حالة الحساب: نشط

---

## 💳 المبيعات
**عدد العمليات:** {transactions}

---

## 💰 المالية
**الحركات المالية:** {ledger}

---

## 🔔 الإشعارات
**الأحداث:** {events}

---

✅ النظام يعمل بشكل طبيعي
"""


def create_dashboard():

    with gr.Blocks() as demo:

        gr.Markdown(
            "# 🏪 FADL PAY\n## لوحة تحكم التاجر"
        )

        info = gr.Markdown(
            dashboard_data()
        )

        refresh = gr.Button(
            "🔄 تحديث البيانات"
        )

        refresh.click(
            dashboard_data,
            outputs=info
        )

    return demo
