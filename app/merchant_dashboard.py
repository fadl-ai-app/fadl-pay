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


    portal_html = '<style>\n\n* {\n    box-sizing: border-box;\n}\n\nbody {\n    margin: 0;\n    min-height: 100vh;\n\n    font-family:\n        "Segoe UI",\n        Tahoma,\n        Arial,\n        sans-serif;\n\n    color: #173d30;\n\n    background:\n        radial-gradient(\n            circle at 50% 0%,\n            rgba(212,175,55,.13),\n            transparent 34%\n        ),\n        linear-gradient(\n            180deg,\n            #f7faf8,\n            #edf4f0\n        );\n}\n\n.container {\n    width: min(1100px, 94%);\n    margin: 0 auto;\n    padding: 32px 0 42px;\n}\n\n.header {\n    background:\n        linear-gradient(\n            145deg,\n            #0b5d42,\n            #073b2a\n        );\n\n    color: white;\n\n    border-radius: 26px;\n\n    padding: 30px;\n\n    box-shadow:\n        0 18px 45px rgba(7,59,42,.15);\n\n    margin-bottom: 22px;\n}\n\n.header-top {\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n\n    gap: 20px;\n}\n\n.brand {\n    display: flex;\n    align-items: center;\n    gap: 14px;\n}\n\n.logo {\n    width: 58px;\n    height: 58px;\n\n    display: flex;\n    align-items: center;\n    justify-content: center;\n\n    border-radius: 17px;\n\n    font-size: 28px;\n\n    background:\n        rgba(255,255,255,.10);\n\n    border:\n        1px solid rgba(212,175,55,.42);\n}\n\n.brand-title {\n    font-size: 24px;\n    font-weight: 800;\n}\n\n.brand-subtitle {\n    margin-top: 4px;\n    font-size: 12px;\n    opacity: .72;\n}\n\n.account {\n    text-align: left;\n    font-size: 11px;\n    opacity: .75;\n}\n\n.welcome {\n    margin-top: 24px;\n}\n\n.welcome h1 {\n    margin: 0;\n    font-size: 27px;\n}\n\n.welcome p {\n    margin: 8px 0 0;\n    font-size: 13px;\n    opacity: .75;\n}\n\n.grid {\n    display: grid;\n\n    grid-template-columns:\n        repeat(2, minmax(0, 1fr));\n\n    gap: 17px;\n}\n\n.card {\n    background: white;\n\n    border:\n        1px solid rgba(7,59,42,.09);\n\n    border-radius: 21px;\n\n    padding: 23px;\n\n    box-shadow:\n        0 8px 28px rgba(7,59,42,.07);\n\n    transition:\n        transform .16s ease,\n        box-shadow .16s ease;\n}\n\n.card:hover {\n    transform: translateY(-2px);\n\n    box-shadow:\n        0 13px 35px rgba(7,59,42,.11);\n}\n\n.card-head {\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n\n    gap: 14px;\n\n    margin-bottom: 15px;\n}\n\n.card-title-wrap {\n    display: flex;\n    align-items: center;\n    gap: 12px;\n}\n\n.icon {\n    width: 46px;\n    height: 46px;\n\n    display: flex;\n    align-items: center;\n    justify-content: center;\n\n    border-radius: 14px;\n\n    background:\n        #edf6f1;\n\n    font-size: 23px;\n}\n\n.card-title {\n    font-size: 17px;\n    font-weight: 800;\n}\n\n.status {\n    padding: 5px 9px;\n\n    border-radius: 999px;\n\n    font-size: 9px;\n    font-weight: 700;\n\n    background: #edf6f1;\n    color: #17663f;\n}\n\n.card-description {\n    margin-bottom: 17px;\n\n    font-size: 11px;\n    line-height: 1.8;\n\n    color: #72847d;\n}\n\n.fields {\n    display: grid;\n    grid-template-columns:\n        repeat(2, minmax(0, 1fr));\n\n    gap: 9px;\n}\n\n.field {\n    min-height: 49px;\n\n    padding: 10px 12px;\n\n    border-radius: 12px;\n\n    background: #f8faf9;\n\n    border:\n        1px solid #e8eeeb;\n}\n\n.field-label {\n    font-size: 9px;\n    color: #8a9a93;\n\n    margin-bottom: 4px;\n}\n\n.field-value {\n    font-size: 11px;\n    font-weight: 700;\n\n    color: #254f40;\n}\n\n.card-button {\n    width: 100%;\n\n    height: 43px;\n\n    margin-top: 15px;\n\n    border: 0;\n    border-radius: 12px;\n\n    background:\n        #e9f4ef;\n\n    color: #0b6042;\n\n    font-size: 11px;\n    font-weight: 800;\n\n    cursor: pointer;\n}\n\n.card-button:hover {\n    background: #dceee6;\n}\n\n.full {\n    grid-column: 1 / -1;\n}\n\n.footer {\n    text-align: center;\n\n    margin-top: 22px;\n\n    font-size: 9px;\n\n    color: #87968f;\n}\n\n@media (max-width: 760px) {\n\n    .grid {\n        grid-template-columns: 1fr;\n    }\n\n    .full {\n        grid-column: auto;\n    }\n\n    .header-top {\n        flex-direction: column;\n        align-items: flex-start;\n    }\n\n    .account {\n        text-align: right;\n    }\n\n    .fields {\n        grid-template-columns: 1fr;\n    }\n\n}\n\n</style>\n<style>\na[role="button"] {\n    cursor: pointer;\n    text-decoration: none !important;\n}\nbutton[disabled][aria-disabled="true"] {\n    opacity: .62 !important;\n    cursor: not-allowed !important;\n}\n#api_credentials, #authentication_info, #webhook_info {\n    scroll-margin-top: 28px;\n}\n</style>\n<div id="fadl_approved_merchant_portal">\n\n<div class="container">\n\n    <header class="header">\n\n        <div class="header-top">\n\n            <div class="brand">\n\n                <div class="logo">\n                    💳\n                </div>\n\n                <div>\n                    <div class="brand-title">\n                        FADL PAY\n                    </div>\n\n                    <div class="brand-subtitle">\n                        لوحة التاجر\n                    </div>\n                </div>\n\n            </div>\n\n            <div class="account">\n                الحساب: Merchant\n            </div>\n\n        </div>\n\n        <div class="welcome">\n            <h1>\n                مرحباً بك في لوحة التحكم\n            </h1>\n\n            <p>\n                جميع أدوات حسابك وخدمات FADL PAY في مكان واحد.\n            </p>\n        </div>\n\n    </header>\n\n\n    <main class="grid">\n\n\n        <!-- PAYMENT UI -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        💳\n                    </div>\n\n                    <div class="card-title">\n                        واجهة الدفع\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    نشطة\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إدارة إعدادات واجهة الدفع والخدمات المتاحة للعملاء.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        الدول\n                    </div>\n                    <div class="field-value">\n                        243 دولة\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        العملات\n                    </div>\n                    <div class="field-value">\n                        20 عملة\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="/pay" role="button">\n                فتح واجهة الدفع\n            </a>\n\n        </section>\n\n\n        <!-- FINANCIAL ADMIN -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        💰\n                    </div>\n\n                    <div class="card-title">\n                        الإدارة المالية\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    محمية\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                متابعة المعاملات والأرصدة والتقارير المالية حسب الصلاحية.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        المعاملات\n                    </div>\n                    <div class="field-value">\n                        عرض ومتابعة\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        التقارير\n                    </div>\n                    <div class="field-value">\n                        متاحة حسب الصلاحية\n                    </div>\n                </div>\n\n            </div>\n\n            <button class="card-button" type="button" disabled aria-disabled="true" title="تتطلب صلاحية Admin مستقلة">\n                فتح الإدارة المالية\n            </button>\n\n        </section>\n\n\n        <!-- KEYS -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        🔑\n                    </div>\n\n                    <div class="card-title">\n                        المفاتيح والرموز\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    محمية\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إدارة مفاتيح API والرموز وبيانات الوصول بدون عرض الأسرار مباشرة.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        API Keys\n                    </div>\n                    <div class="field-value">\n                        إدارة المفاتيح\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Tokens\n                    </div>\n                    <div class="field-value">\n                        إدارة الرموز\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="#api_credentials" role="button">\n                فتح المفاتيح والرموز\n            </a>\n\n        </section>\n\n\n        <!-- AUTH -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        🔐\n                    </div>\n\n                    <div class="card-title">\n                        المصادقة والصلاحيات\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    محمية\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إعدادات المصادقة والتحكم في الوصول حسب صلاحية المستخدم.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        Authentication\n                    </div>\n                    <div class="field-value">\n                        مفعّلة\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Permissions\n                    </div>\n                    <div class="field-value">\n                        Role-Based\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="#authentication_info" role="button">\n                إدارة المصادقة\n            </a>\n\n        </section>\n\n\n        <!-- WEBHOOK -->\n\n        <section class="card full">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        🔔\n                    </div>\n\n                    <div class="card-title">\n                        Webhook\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    جاهز للإعداد\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إدارة Endpoint والأحداث وبيانات التحقق ومتابعة عمليات التسليم.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        Endpoint\n                    </div>\n                    <div class="field-value">\n                        محفوظ بشكل آمن\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Events\n                    </div>\n                    <div class="field-value">\n                        معاملات الدفع\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Secret\n                    </div>\n                    <div class="field-value">\n                        غير معروض\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Delivery\n                    </div>\n                    <div class="field-value">\n                        متابعة الحالة\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="#webhook_info" role="button">\n                إدارة Webhook\n            </a>\n\n        </section>\n\n\n    </main>\n\n\n    <div class="footer">\n        FADL PAY · Merchant Sandbox\n    </div>\n\n</div>\n\n</div>'


    with gr.Blocks(title="FADL PAY — لوحة التاجر") as demo:

        # Approved complete design, embedded into the real dashboard.
        gr.HTML(portal_html)

        gr.HTML(
            """
            <section id="merchant_account_data" dir="rtl"
                     style="padding:20px 4px 8px">
              <h2>👤 بيانات حساب التاجر</h2>
              <p style="font-size:16px;line-height:1.8">
                هذه البيانات محمّلة من مصادر لوحة التاجر الحقيقية بعد
                التحقق من جلسة الدخول.
              </p>
            </section>
            """
        )

        title_md = gr.Markdown(value="⏳ جاري تحميل بيانات التاجر...")

        with gr.Row():
            transactions_md = gr.Markdown(
                value="### 💳 العمليات\n## —"
            )
            total_md = gr.Markdown(
                value="### 💰 إجمالي القيمة\n## —"
            )
            collected_md = gr.Markdown(
                value="### ✅ المحصل\n## —"
            )
            pending_md = gr.Markdown(
                value="### ⏳ المعلّق\n## —"
            )

        operational_md = gr.Markdown(
            value="## 🔐 السجل التشغيلي\n\nجاري التحميل..."
        )

        status_title_md = gr.Markdown(
            value="## 📈 توزيع العمليات حسب الحالة"
        )
        status_md = gr.Markdown(value="جاري التحميل...")

        currency_title_md = gr.Markdown(
            value="## 💱 توزيع العملات"
        )
        currency_md = gr.Markdown(value="جاري التحميل...")

        payment_title_md = gr.Markdown(
            value="## 💳 طرق الدفع"
        )
        payment_md = gr.Markdown(value="جاري التحميل...")

        recent_title_md = gr.Markdown(
            value="## 🧾 آخر العمليات"
        )
        recent_md = gr.Markdown(value="جاري التحميل...")

        gr.HTML(
            """
            <section id="api_credentials" dir="rtl"
                     style="padding:20px 4px 8px">
              <h2>🔑 إدارة API Credentials</h2>
              <p style="font-size:16px;line-height:1.8">
                إنشاء مفتاح مرتبط بجلسة التاجر الحالية.
                المفتاح السري يظهر مرة واحدة فقط؛ احفظيه في مكان آمن.
              </p>
            </section>
            """
        )

        create_api_key_btn = gr.Button(
            "🔑 إنشاء API Credential",
            variant="primary",
        )

        api_key_status_md = gr.Markdown(value="")

        api_key_once = gr.Textbox(
            label="المفتاح السري — يظهر مرة واحدة فقط",
            value="",
            type="text",
            interactive=False,
        )

        gr.HTML(
            """
            <section id="authentication_info" dir="rtl"
                     style="padding:20px 4px 8px">
              <h2>🔐 المصادقة والصلاحيات</h2>
              <p style="font-size:16px;line-height:1.8">
                لوحة التاجر محمية بجلسة Merchant Session.
                لا يُسمح بفتحها دون جلسة صالحة.
              </p>
            </section>
            """
        )

        gr.HTML(
            """
            <section id="webhook_info" dir="rtl"
                     style="padding:20px 4px 8px">
              <h2>🔔 Webhook</h2>
              <p style="font-size:16px;line-height:1.8">
                طبقة Webhook موجودة في الخلفية. لا تعرض هذه اللوحة
                أزرار إدارة غير مرتبطة بواجهة فعلية.
              </p>
            </section>
            """
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



