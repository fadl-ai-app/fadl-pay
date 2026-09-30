import sqlite3
import gradio as gr
from security.api_keys import create_api_key

import database.database as db_module
from security.merchant_session import get_session_merchant


def dashboard_data(merchant_reference):
    """
    Return financial dashboard data for the authenticated merchant only.

    READ-ONLY database queries.
    """

    if not merchant_reference:
        raise PermissionError("Authentication required")

    with db_module.get_connection() as conn:
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

        # ------------------------------------------------------------------
        # Transaction summary
        # ------------------------------------------------------------------

        summary = conn.execute(
            """
            SELECT
                COUNT(*) AS total_transactions,
                COALESCE(SUM(amount), 0) AS total_amount,
                COALESCE(
                    SUM(CASE WHEN status = 'paid' THEN amount ELSE 0 END),
                    0
                ) AS collected_amount,
                COALESCE(
                    SUM(CASE WHEN status = 'pending' THEN amount ELSE 0 END),
                    0
                ) AS pending_amount
            FROM transactions
            WHERE merchant_reference = ?
            """,
            (merchant_reference,),
        ).fetchone()

        # ------------------------------------------------------------------
        # Status breakdown
        # ------------------------------------------------------------------

        status_rows = conn.execute(
            """
            SELECT
                status,
                COUNT(*) AS count,
                COALESCE(SUM(amount), 0) AS amount
            FROM transactions
            WHERE merchant_reference = ?
            GROUP BY status
            ORDER BY status
            """,
            (merchant_reference,),
        ).fetchall()

        status_breakdown = [
            {
                "status": row["status"],
                "count": row["count"],
                "amount": row["amount"],
            }
            for row in status_rows
        ]

        # ------------------------------------------------------------------
        # Currency breakdown
        # ------------------------------------------------------------------

        currency_rows = conn.execute(
            """
            SELECT
                currency,
                COUNT(*) AS count,
                COALESCE(SUM(amount), 0) AS amount
            FROM transactions
            WHERE merchant_reference = ?
            GROUP BY currency
            ORDER BY currency
            """,
            (merchant_reference,),
        ).fetchall()

        currency_breakdown = [
            {
                "currency": row["currency"],
                "count": row["count"],
                "amount": row["amount"],
            }
            for row in currency_rows
        ]

        # ------------------------------------------------------------------
        # Payment method breakdown
        # ------------------------------------------------------------------

        payment_method_rows = conn.execute(
            """
            SELECT
                payment_method,
                COUNT(*) AS count,
                COALESCE(SUM(amount), 0) AS amount
            FROM transactions
            WHERE merchant_reference = ?
            GROUP BY payment_method
            ORDER BY payment_method
            """,
            (merchant_reference,),
        ).fetchall()

        payment_method_breakdown = [
            {
                "payment_method": row["payment_method"],
                "count": row["count"],
                "amount": row["amount"],
            }
            for row in payment_method_rows
        ]

        # ------------------------------------------------------------------
        # Recent transactions
        # ------------------------------------------------------------------

        recent_rows = conn.execute(
            """
            SELECT
                transaction_reference,
                customer_reference,
                amount,
                currency,
                status,
                payment_method,
                created_at
            FROM transactions
            WHERE merchant_reference = ?
            ORDER BY id DESC
            LIMIT 10
            """,
            (merchant_reference,),
        ).fetchall()

        recent_transactions = [
            {
                "transaction_reference": row["transaction_reference"],
                "customer_reference": row["customer_reference"],
                "amount": row["amount"],
                "currency": row["currency"],
                "status": row["status"],
                "payment_method": row["payment_method"],
                "created_at": row["created_at"],
            }
            for row in recent_rows
        ]

        # ------------------------------------------------------------------
        # Ledger count
        # ------------------------------------------------------------------

        ledger = conn.execute(
            """
            SELECT COUNT(*)
            FROM ledger_entries
            WHERE merchant_reference = ?
            """,
            (merchant_reference,),
        ).fetchone()[0]

        # ------------------------------------------------------------------
        # Event count
        # ------------------------------------------------------------------

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

            "transactions": summary["total_transactions"],
            "total_amount": summary["total_amount"],
            "collected_amount": summary["collected_amount"],
            "pending_amount": summary["pending_amount"],

            "ledger": ledger,
            "events": events,

            "status_breakdown": status_breakdown,
            "currency_breakdown": currency_breakdown,
            "payment_method_breakdown": payment_method_breakdown,
            "recent_transactions": recent_transactions,
        }
    
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
    Create the complete merchant dashboard from the
    authenticated server-side merchant session.

    READ-ONLY display layer.
    """

    data = dashboard_data_from_session(session_token)

    return {
        "merchant": data["name"],
        "merchant_reference": data["merchant_reference"],
        "email": data["email"],
        "status": data["status"],

        "transactions": data["transactions"],
        "total_amount": data["total_amount"],
        "collected_amount": data["collected_amount"],
        "pending_amount": data["pending_amount"],

        "ledger": data["ledger"],
        "events": data["events"],

        "status_breakdown": data["status_breakdown"],
        "currency_breakdown": data["currency_breakdown"],
        "payment_method_breakdown": data["payment_method_breakdown"],
        "recent_transactions": data["recent_transactions"],
    }


def _fmt_amount(amount, currency=""):
    """
    Simple display formatter.
    No database access.
    """
    try:
        value = int(amount or 0)
        formatted = f"{value:,}"
    except (TypeError, ValueError):
        formatted = str(amount)

    return f"{formatted} {currency}".strip()


def _status_label(status):
    labels = {
        "paid": "مدفوعة",
        "pending": "معلّقة",
        "refunded": "مستردة",
        "failed": "فاشلة",
        "cancelled": "ملغاة",
    }
    return labels.get(status, status)


def _payment_method_label(method):
    labels = {
        "mobile_money": "محفظة إلكترونية",
        "bank": "تحويل بنكي",
        "card": "بطاقة",
        "test": "اختبار",
    }
    return labels.get(method, method)


def _build_status_markdown(rows):
    if not rows:
        return "لا توجد بيانات."

    lines = [
        "| الحالة | العمليات | القيمة |",
        "|---|---:|---:|",
    ]

    for row in rows:
        status = _status_label(row["status"])
        count = row["count"]
        amount = _fmt_amount(row["amount"])

        lines.append(
            f"| {status} | {count} | {amount} |"
        )

    return "\n".join(lines)


def _build_currency_markdown(rows):
    if not rows:
        return "لا توجد بيانات."

    lines = [
        "| العملة | العمليات | القيمة |",
        "|---|---:|---:|",
    ]

    for row in rows:
        currency = row["currency"]
        count = row["count"]
        amount = _fmt_amount(row["amount"], currency)

        lines.append(
            f"| {currency} | {count} | {amount} |"
        )

    return "\n".join(lines)


def _build_payment_method_markdown(rows):
    if not rows:
        return "لا توجد بيانات."

    lines = [
        "| طريقة الدفع | العمليات | القيمة |",
        "|---|---:|---:|",
    ]

    for row in rows:
        method = _payment_method_label(row["payment_method"])
        count = row["count"]
        amount = _fmt_amount(row["amount"])

        lines.append(
            f"| {method} | {count} | {amount} |"
        )

    return "\n".join(lines)


def _build_recent_transactions_markdown(rows):
    if not rows:
        return "لا توجد عمليات حديثة."

    lines = [
        "| المرجع | مرجع العميل | المبلغ | الحالة | طريقة الدفع | التاريخ |",
        "|---|---|---:|---|---|---|",
    ]

    for row in rows:
        transaction_reference = row["transaction_reference"]
        customer_reference = row["customer_reference"]
        amount = _fmt_amount(row["amount"], row["currency"])
        status = _status_label(row["status"])
        method = _payment_method_label(row["payment_method"])
        created_at = row["created_at"]

        lines.append(
            f"| `{transaction_reference}` | "
            f"`{customer_reference}` | "
            f"{amount} | "
            f"{status} | "
            f"{method} | "
            f"{created_at} |"
        )

    return "\n".join(lines)



def create_dashboard():

    # ----------------------------------------------------------------------------------------------------------
    # Runtime loader
    # ----------------------------------------------------------------------------------------------------------

    def load_dashboard(request: gr.Request):

        session_token = getattr(
            request,
            "username",
            None,
        )

        if not session_token:
            raise PermissionError(
                "Authentication required"
            )

        data = create_dashboard_from_session(
            session_token
        )

        currency = (
            data["currency_breakdown"][0]["currency"]
            if data["currency_breakdown"]
            else ""
        )

        total_amount = _fmt_amount(
            data["total_amount"],
            currency,
        )

        collected_amount = _fmt_amount(
            data["collected_amount"],
            currency,
        )

        pending_amount = _fmt_amount(
            data["pending_amount"],
            currency,
        )

        status_table = _build_status_markdown(
            data["status_breakdown"]
        )

        currency_table = _build_currency_markdown(
            data["currency_breakdown"]
        )

        payment_method_table = _build_payment_method_markdown(
            data["payment_method_breakdown"]
        )

        recent_transactions_table = _build_recent_transactions_markdown(
            data["recent_transactions"]
        )

        return (
            f"""
# 🏪 FADL PAY
## لوحة تحكم التاجر

لوحة مالية للقراءة فقط

---

## 👤 بيانات التاجر

**التاجر:** {data["merchant"]}

**Merchant Reference:** `{data["merchant_reference"]}`

**البريد الإلكتروني:** {data["email"]}

**الحالة:** 🟢 {data["status"]}

---

## 📊 الملخص المالي
""",
            f"""
### 💳 العمليات
## {data["transactions"]}
""",
            f"""
### 💰 إجمالي القيمة
## {total_amount}
""",
            f"""
### ✅ المحصل
## {collected_amount}
""",
            f"""
### ⏳ المعلّق
## {pending_amount}
""",
            f"""
## 🔐 السجل التشغيلي

- 📒 **Ledger entries:** {data["ledger"]}
- 🔔 **Transaction events:** {data["events"]}
""",
            "## 📈 توزيع العمليات حسب الحالة",
            status_table,
            "## 💱 توزيع العملات",
            currency_table,
            "## 💳 طرق الدفع",
            payment_method_table,
            "## 🧾 آخر العمليات",
            recent_transactions_table,
        )

    # ------------------------------------------------------------------------------------------------------
    # API Credentials — one-time secret generation
    # ------------------------------------------------------------------------------------------------------

    def create_dashboard_api_key(request: gr.Request):

        session_token = getattr(
            request,
            "username",
            None,
        )

        if not session_token:
            return (
                "❌ Authentication required.",
                "",
            )

        merchant = get_session_merchant(
            session_token
        )

        if not merchant:
            return (
                "❌ Merchant session is invalid or expired.",
                "",
            )

        merchant_reference = merchant.get(
            "merchant_reference"
        )

        if not merchant_reference:
            return (
                "❌ Merchant reference is unavailable.",
                "",
            )

        try:

            raw_api_key = create_api_key(
                merchant_reference
            )

        except Exception as exc:

            return (
                f"❌ API key creation failed: {exc}",
                "",
            )

        return (
            """
## ✅ تم إنشاء API Credential

**تنبيه أمني:** المفتاح السري يظهر هنا مرة واحدة فقط.
لا يتم حفظه في `localStorage` أو `sessionStorage` بواسطة لوحة التحكم.

احفظه الآن في مكان آمن. بعد مغادرة/إعادة تحميل الصفحة لن تتمكن لوحة التحكم من استرجاع المفتاح السري.
""",
            raw_api_key,
        )

    # ----------------------------------------------------------------------------------------------------------
    # Gradio UI
    # ----------------------------------------------------------------------------------------------------------

    with gr.Blocks(
        title="FADL PAY — لوحة تحكم التاجر"
    ) as demo:

        gr.HTML(
            """
            <style>
            :root {
                --fadl-green-soft: #eef7f1;
                --fadl-green-pale: #f6fbf7;
                --fadl-green-border: #cfe5d6;
                --fadl-green-text: #24543a;
                --fadl-green-accent: #4f8a68;
            }

            body {
                direction: rtl;
            }

            .fadl-dashboard {
                background: var(--fadl-green-pale);
                border: 1px solid var(--fadl-green-border);
                border-radius: 22px;
                padding: 24px;
            }

            .fadl-dashboard h1,
            .fadl-dashboard h2,
            .fadl-dashboard h3 {
                color: var(--fadl-green-text);
            }

            .fadl-dashboard .gr-markdown {
                background: transparent;
            }

            .fadl-dashboard-card {
                background: var(--fadl-green-soft);
                border: 1px solid var(--fadl-green-border);
                border-radius: 16px;
                padding: 16px;
            }
            </style>
            """
        )

        with gr.Column(
            elem_classes=["fadl-dashboard"]
        ):

            title_md = gr.Markdown(
                "## 🔐 جاري تحميل لوحة التاجر..."
            )

            with gr.Row():

                transactions_md = gr.Markdown(
                    "### 💳 العمليات\n## —"
                )

                total_md = gr.Markdown(
                    "### 💰 إجمالي القيمة\n## —"
                )

                collected_md = gr.Markdown(
                    "### ✅ المحصل\n## —"
                )

                pending_md = gr.Markdown(
                    "### ⏳ المعلّق\n## —"
                )

            operational_md = gr.Markdown(
                "## 🔐 السجل التشغيلي\n\nجاري التحميل..."
            )

            status_title_md = gr.Markdown(
                "## 📈 توزيع العمليات حسب الحالة"
            )

            status_md = gr.Markdown(
                "جاري التحميل..."
            )

            currency_title_md = gr.Markdown(
                "## 💱 توزيع العملات"
            )

            currency_md = gr.Markdown(
                "جاري التحميل..."
            )

            payment_title_md = gr.Markdown(
                "## 💳 طرق الدفع"
            )

            payment_md = gr.Markdown(
                "جاري التحميل..."
            )

            recent_title_md = gr.Markdown(
                "## 🧾 آخر العمليات"
            )

            recent_md = gr.Markdown(
                "جاري التحميل..."
            )

        # V2.13-D API CREDENTIALS UI

        gr.Markdown(
            """
## 🔐 API Credentials

إنشاء مفتاح API جديد للتاجر.

> ⚠️ سيتم عرض المفتاح السري مرة واحدة فقط بعد الإنشاء.
> لا يتم تخزينه في المتصفح بواسطة لوحة التحكم.
            """
        )

        create_api_key_btn = gr.Button(
            "🔑 إنشاء API Credential جديد",
            variant="primary",
        )

        api_key_status_md = gr.Markdown(
            "لم يتم إنشاء Credential جديد."
        )

        api_key_once = gr.Textbox(
            label="🔐 المفتاح السري — يظهر مرة واحدة",
            value="",
            interactive=False,
            type="password",
        )

        create_api_key_btn.click(
            fn=create_dashboard_api_key,
            inputs=None,
            outputs=[
                api_key_status_md,
                api_key_once,
            ],
        )

        demo.load(
            fn=load_dashboard,
            inputs=None,
            outputs=[
                title_md,
                transactions_md,
                total_md,
                collected_md,
                pending_md,
                operational_md,
                status_title_md,
                status_md,
                currency_title_md,
                currency_md,
                payment_title_md,
                payment_md,
                recent_title_md,
                recent_md,
            ],
        )

    return demo



