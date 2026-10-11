import sqlite3
import gradio as gr
from security.api_keys import create_api_key, list_api_keys

import database.database as db_module
from security.merchant_session import (
    get_session_merchant,
    get_session_role,
)
from security.merchant_rbac import require_permission


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
    role = get_session_role(session_token)
    require_permission(role, "merchant.read")

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

    def create_dashboard_api_key(csrf_token, request: gr.Request):

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

        from security.merchant_session import verify_csrf

        try:
            csrf_valid = bool(csrf_token) and verify_csrf(
                session_token,
                str(csrf_token),
            )
        except Exception:
            csrf_valid = False

        if not csrf_valid:
            return (
                "❌ رمز الحماية CSRF مفقود أو غير صالح؛ أعيدي تحميل صفحة بوابة التاجر.",
                "",
            )

        merchant_reference = get_session_merchant(
            session_token
        )

        if not merchant_reference:
            return (
                "❌ Merchant session is invalid or expired.",
                "",
            )


        try:
            role = get_session_role(session_token)
            require_permission(role, "api_credentials.manage")
        except PermissionError:
            return ("❌ ليس لديك صلاحية إدارة API Credentials.", "")

        # merchant_reference was resolved directly from the server-side session above.

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



    # ==================================================================================================
    # FADL_PAY_UI_RESTORE_V1 — SERVER-SIDE SESSION-BOUND MERCHANT CONTROLS
    # ==================================================================================================

    def load_dashboard_csrf_token(request: gr.Request):
        """Load the CSRF token belonging to this authenticated dashboard session."""
        session_token = getattr(request, "username", None)
        if not session_token:
            return ""
        from security.merchant_session import get_csrf_token
        return get_csrf_token(session_token) or ""

    def _dashboard_identity(request: gr.Request, permission: str):
        session_token = getattr(request, "username", None)

        if not session_token:
            raise PermissionError("Authentication required")

        role = get_session_role(session_token)
        require_permission(role, permission)

        merchant_reference = get_session_merchant(session_token)

        if not merchant_reference:
            raise PermissionError("Merchant session is invalid or expired")

        return session_token, merchant_reference, role

    # ----------------------------------------------------------------------------------------------
    # API Credentials: listing returns only non-secret metadata.
    # ----------------------------------------------------------------------------------------------

    def load_api_keys_ui(request: gr.Request):
        try:
            _, merchant_reference, _ = _dashboard_identity(
                request, "api_credentials.read"
            )

            rows = list_api_keys(merchant_reference)

            safe_rows = [
                {
                    "id": row.get("id"),
                    "status": row.get("status"),
                    "created_at": row.get("created_at"),
                }
                for row in rows
            ]

            return (
                f"✅ تم تحميل بيانات المفاتيح: {len(safe_rows)}",
                safe_rows,
            )

        except PermissionError as exc:
            return (f"❌ {exc}", [])

        except Exception:
            return ("❌ تعذر تحميل مفاتيح API. راجعي سجل الخادم.", [])

    def revoke_api_key_ui(credential_id, csrf_token, request: gr.Request):
        try:
            session_token = getattr(request, "username", None)
            from security.merchant_session import verify_csrf

            if (
                not session_token
                or not csrf_token
                or not verify_csrf(session_token, str(csrf_token))
            ):
                raise PermissionError(
                    "رمز الحماية CSRF مفقود أو غير صالح؛ أعيدي تحميل صفحة بوابة التاجر."
                )

            _, merchant_reference, _ = _dashboard_identity(
                request, "api_credentials.manage"
            )

            if credential_id is None:
                return "⚠️ أدخلي رقم API Credential أولاً."

            numeric_id = float(credential_id)

            if not numeric_id.is_integer() or numeric_id < 1:
                return "⚠️ رقم API Credential غير صالح."

            credential_id = int(numeric_id)

            # Reuse the current backend helper, which checks ownership and active status.
            from backend.merchant_auth_routes import revoke_api_key_by_id

            result = revoke_api_key_by_id(
                credential_id,
                merchant_reference,
            )

            if result.get("status") == "revoked":
                return f"✅ تم إلغاء API Credential رقم {credential_id}."

            return f"⚠️ لم يؤكد الخادم إلغاء المفتاح رقم {credential_id}."

        except PermissionError as exc:
            return f"❌ {exc}"

        except Exception as exc:
            detail = getattr(exc, "detail", None)

            if detail:
                return f"⚠️ {detail}"

            return "❌ تعذر إلغاء المفتاح. راجعي سجل الخادم."

    # ----------------------------------------------------------------------------------------------
    # Webhook endpoints and deliveries: read-only UI.
    # No webhook secret, payload, or signature is returned to the UI.
    # ----------------------------------------------------------------------------------------------

    def load_webhook_endpoints_ui(request: gr.Request):
        connection = None

        try:
            _, merchant_reference, _ = _dashboard_identity(
                request, "webhook.read"
            )

            connection = db_module.get_connection()

            rows = connection.execute(
                """
                SELECT id, webhook_url, status, created_at, updated_at
                FROM webhook_endpoints
                WHERE merchant_reference = ?
                ORDER BY id DESC
                """,
                (merchant_reference,),
            ).fetchall()

            endpoints = []

            for row in rows:
                item = {
                    "id": row["id"],
                    "url": row["webhook_url"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                    "updated_at": row["updated_at"],
                }

                stats = connection.execute(
                    """
                    SELECT
                        COUNT(*) AS total,
                        COALESCE(
                            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END),
                            0
                        ) AS successful,
                        COALESCE(
                            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END),
                            0
                        ) AS failed,
                        MAX(updated_at) AS last_delivery_at
                    FROM webhook_deliveries
                    WHERE webhook_endpoint_id = ?
                    """,
                    (item["id"],),
                ).fetchone()

                item["delivery"] = dict(stats) if stats else {
                    "total": 0,
                    "successful": 0,
                    "failed": 0,
                    "last_delivery_at": None,
                }

                endpoints.append(item)

            return (
                f"✅ عدد Webhook endpoints: {len(endpoints)}",
                endpoints,
            )

        except PermissionError as exc:
            return (f"❌ {exc}", [])

        except Exception:
            return ("❌ تعذر تحميل Webhook endpoints. راجعي سجل الخادم.", [])

        finally:
            if connection is not None:
                connection.close()

    def load_webhook_deliveries_ui(endpoint_id, request: gr.Request):
        connection = None

        try:
            _, merchant_reference, _ = _dashboard_identity(
                request, "webhook.read"
            )

            if endpoint_id is None:
                return ("⚠️ أدخلي رقم Webhook endpoint أولاً.", [])

            numeric_id = float(endpoint_id)

            if not numeric_id.is_integer() or numeric_id < 1:
                return ("⚠️ رقم Webhook endpoint غير صالح.", [])

            endpoint_id = int(numeric_id)
            connection = db_module.get_connection()

            owned_endpoint = connection.execute(
                """
                SELECT id
                FROM webhook_endpoints
                WHERE id = ?
                  AND merchant_reference = ?
                """,
                (endpoint_id, merchant_reference),
            ).fetchone()

            if not owned_endpoint:
                return ("⚠️ Webhook endpoint غير موجود لهذا التاجر.", [])

            rows = connection.execute(
                """
                SELECT
                    id,
                    event_id,
                    transaction_reference,
                    status,
                    attempts,
                    response_status,
                    error_message,
                    created_at,
                    updated_at
                FROM webhook_deliveries
                WHERE webhook_endpoint_id = ?
                ORDER BY id DESC
                LIMIT 100
                """,
                (endpoint_id,),
            ).fetchall()

            deliveries = [dict(row) for row in rows]

            return (
                f"✅ عدد سجلات التسليم المعروضة: {len(deliveries)}",
                deliveries,
            )

        except PermissionError as exc:
            return (f"❌ {exc}", [])

        except Exception:
            return ("❌ تعذر تحميل سجل التسليم. راجعي سجل الخادم.", [])

        finally:
            if connection is not None:
                connection.close()

    # ----------------------------------------------------------------------------------------------
    # Merchant reports: RBAC-protected filters and CSV text export.
    # Report retrieval is read-only; CSV is returned as text for copying.
    # ----------------------------------------------------------------------------------------------

    def _get_dashboard_report(
        request,
        start_date,
        end_date,
        report_status,
        currency,
    ):
        _, merchant_reference, role = _dashboard_identity(
            request, "reports.read"
        )

        from app.reports import get_reports

        return get_reports(
            merchant_reference=merchant_reference,
            role=role,
            start_date=(start_date or None),
            end_date=(end_date or None),
            status=(report_status or None),
            currency=(currency or None),
        )

    def load_reports_ui(start_date, end_date, report_status, currency, request: gr.Request):
        try:
            report = _get_dashboard_report(
                request, start_date, end_date, report_status, currency
            )

            summary = report.get("summary", {})
            total = summary.get("total_transactions", 0)

            return (
                f"✅ تم إنشاء التقرير. عدد المعاملات: {total}",
                report,
            )

        except PermissionError as exc:
            return (f"❌ {exc}", {})

        except Exception:
            return ("❌ تعذر إنشاء التقرير. راجعي سجل الخادم.", {})

    def export_reports_csv_ui(start_date, end_date, report_status, currency, request: gr.Request):
        try:
            report = _get_dashboard_report(
                request, start_date, end_date, report_status, currency
            )

            from app.reports import export_reports_csv

            csv_text = export_reports_csv(report)

            return (
                "✅ ملف CSV النصي جاهز للنسخ والحفظ.",
                csv_text,
            )

        except PermissionError as exc:
            return (f"❌ {exc}", "")

        except Exception:
            return ("❌ تعذر تصدير التقرير. راجعي سجل الخادم.", "")

    portal_html = '<style>\n\n* {\n    box-sizing: border-box;\n}\n\nbody {\n    margin: 0;\n    min-height: 100vh;\n\n    font-family:\n        "Segoe UI",\n        Tahoma,\n        Arial,\n        sans-serif;\n\n    color: #173d30;\n\n    background:\n        radial-gradient(\n            circle at 50% 0%,\n            rgba(212,175,55,.13),\n            transparent 34%\n        ),\n        linear-gradient(\n            180deg,\n            #f7faf8,\n            #edf4f0\n        );\n}\n\n.container {\n    width: min(1100px, 94%);\n    margin: 0 auto;\n    padding: 32px 0 42px;\n}\n\n.header {\n    background:\n        linear-gradient(\n            145deg,\n            #0b5d42,\n            #073b2a\n        );\n\n    color: white;\n\n    border-radius: 26px;\n\n    padding: 30px;\n\n    box-shadow:\n        0 18px 45px rgba(7,59,42,.15);\n\n    margin-bottom: 22px;\n}\n\n.header-top {\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n\n    gap: 20px;\n}\n\n.brand {\n    display: flex;\n    align-items: center;\n    gap: 14px;\n}\n\n.logo {\n    width: 58px;\n    height: 58px;\n\n    display: flex;\n    align-items: center;\n    justify-content: center;\n\n    border-radius: 17px;\n\n    font-size: 28px;\n\n    background:\n        rgba(255,255,255,.10);\n\n    border:\n        1px solid rgba(212,175,55,.42);\n}\n\n.brand-title {\n    font-size: 24px;\n    font-weight: 800;\n}\n\n.brand-subtitle {\n    margin-top: 4px;\n    font-size: 12px;\n    opacity: .72;\n}\n\n.account {\n    text-align: left;\n    font-size: 11px;\n    opacity: .75;\n}\n\n.welcome {\n    margin-top: 24px;\n}\n\n.welcome h1 {\n    margin: 0;\n    font-size: 27px;\n}\n\n.welcome p {\n    margin: 8px 0 0;\n    font-size: 13px;\n    opacity: .75;\n}\n\n.grid {\n    display: grid;\n\n    grid-template-columns:\n        repeat(2, minmax(0, 1fr));\n\n    gap: 17px;\n}\n\n.card {\n    background: white;\n\n    border:\n        1px solid rgba(7,59,42,.09);\n\n    border-radius: 21px;\n\n    padding: 23px;\n\n    box-shadow:\n        0 8px 28px rgba(7,59,42,.07);\n\n    transition:\n        transform .16s ease,\n        box-shadow .16s ease;\n}\n\n.card:hover {\n    transform: translateY(-2px);\n\n    box-shadow:\n        0 13px 35px rgba(7,59,42,.11);\n}\n\n.card-head {\n    display: flex;\n    align-items: center;\n    justify-content: space-between;\n\n    gap: 14px;\n\n    margin-bottom: 15px;\n}\n\n.card-title-wrap {\n    display: flex;\n    align-items: center;\n    gap: 12px;\n}\n\n.icon {\n    width: 46px;\n    height: 46px;\n\n    display: flex;\n    align-items: center;\n    justify-content: center;\n\n    border-radius: 14px;\n\n    background:\n        #edf6f1;\n\n    font-size: 23px;\n}\n\n.card-title {\n    font-size: 17px;\n    font-weight: 800;\n}\n\n.status {\n    padding: 5px 9px;\n\n    border-radius: 999px;\n\n    font-size: 9px;\n    font-weight: 700;\n\n    background: #edf6f1;\n    color: #17663f;\n}\n\n.card-description {\n    margin-bottom: 17px;\n\n    font-size: 11px;\n    line-height: 1.8;\n\n    color: #72847d;\n}\n\n.fields {\n    display: grid;\n    grid-template-columns:\n        repeat(2, minmax(0, 1fr));\n\n    gap: 9px;\n}\n\n.field {\n    min-height: 49px;\n\n    padding: 10px 12px;\n\n    border-radius: 12px;\n\n    background: #f8faf9;\n\n    border:\n        1px solid #e8eeeb;\n}\n\n.field-label {\n    font-size: 9px;\n    color: #8a9a93;\n\n    margin-bottom: 4px;\n}\n\n.field-value {\n    font-size: 11px;\n    font-weight: 700;\n\n    color: #254f40;\n}\n\n.card-button {\n    width: 100%;\n\n    height: 43px;\n\n    margin-top: 15px;\n\n    border: 0;\n    border-radius: 12px;\n\n    background:\n        #e9f4ef;\n\n    color: #0b6042;\n\n    font-size: 11px;\n    font-weight: 800;\n\n    cursor: pointer;\n}\n\n.card-button:hover {\n    background: #dceee6;\n}\n\n.full {\n    grid-column: 1 / -1;\n}\n\n.footer {\n    text-align: center;\n\n    margin-top: 22px;\n\n    font-size: 9px;\n\n    color: #87968f;\n}\n\n@media (max-width: 760px) {\n\n    .grid {\n        grid-template-columns: 1fr;\n    }\n\n    .full {\n        grid-column: auto;\n    }\n\n    .header-top {\n        flex-direction: column;\n        align-items: flex-start;\n    }\n\n    .account {\n        text-align: right;\n    }\n\n    .fields {\n        grid-template-columns: 1fr;\n    }\n\n}\n\n</style>\n<style>\na[role="button"] {\n    cursor: pointer;\n    text-decoration: none !important;\n}\nbutton[disabled][aria-disabled="true"] {\n    opacity: .62 !important;\n    cursor: not-allowed !important;\n}\n#api_credentials, #authentication_info, #webhook_info {\n    scroll-margin-top: 28px;\n}\n</style>\n\n<style>\n/* FADL PAY — HIGH CONTRAST PORTAL CSS V2 */\n/* Text colors and opacity only; layout and behavior are unchanged. */\n\n#fadl_approved_merchant_portal .card-title {\n    color: #173d30 !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .card-description {\n    color: #405b50 !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .field-label {\n    color: #405b50 !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .field-value {\n    color: #163c2e !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .status {\n    color: #14563c !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .card-button,\n#fadl_approved_merchant_portal a.card-button {\n    color: #084b36 !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .header .brand-title,\n#fadl_approved_merchant_portal .header .brand-subtitle,\n#fadl_approved_merchant_portal .header .account,\n#fadl_approved_merchant_portal .header .welcome h1,\n#fadl_approved_merchant_portal .header .welcome p {\n    color: #ffffff !important;\n    opacity: 1 !important;\n}\n\n#fadl_approved_merchant_portal .footer {\n    color: #405b50 !important;\n    opacity: 1 !important;\n}\n</style>\n\n<div id="fadl_approved_merchant_portal">\n\n<div class="container">\n\n    <header class="header">\n\n        <div class="header-top">\n\n            <div class="brand">\n\n                <div class="logo">\n                    💳\n                </div>\n\n                <div>\n                    <div class="brand-title">\n                        FADL PAY\n                    </div>\n\n                    <div class="brand-subtitle">\n                        لوحة التاجر\n                    </div>\n                </div>\n\n            </div>\n\n            <div class="account">\n                الحساب: Merchant\n            </div>\n\n        </div>\n\n        <div class="welcome">\n            <h1>\n                مرحباً بك في لوحة التحكم\n            </h1>\n\n            <p>\n                جميع أدوات حسابك وخدمات FADL PAY في مكان واحد.\n            </p>\n        </div>\n\n    </header>\n\n\n    <main class="grid">\n\n\n        <!-- PAYMENT UI -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        💳\n                    </div>\n\n                    <div class="card-title">\n                        واجهة الدفع\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    نشطة\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إدارة إعدادات واجهة الدفع والخدمات المتاحة للعملاء.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        الدول\n                    </div>\n                    <div class="field-value">\n                        243 دولة\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        العملات\n                    </div>\n                    <div class="field-value">\n                        20 عملة\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="/pay" role="button">\n                فتح واجهة الدفع\n            </a>\n\n        </section>\n\n\n        <!-- FINANCIAL ADMIN -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        💰\n                    </div>\n\n                    <div class="card-title">\n                        الإدارة المالية\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    محمية\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                متابعة المعاملات والأرصدة والتقارير المالية حسب الصلاحية.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        المعاملات\n                    </div>\n                    <div class="field-value">\n                        عرض ومتابعة\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        التقارير\n                    </div>\n                    <div class="field-value">\n                        متاحة حسب الصلاحية\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="/admin/" target="_blank" rel="noopener noreferrer">\n                فتح الإدارة المالية\n            </a>\n\n        </section>\n\n\n        <!-- KEYS -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        🔑\n                    </div>\n\n                    <div class="card-title">\n                        المفاتيح والرموز\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    محمية\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إدارة مفاتيح API والرموز وبيانات الوصول بدون عرض الأسرار مباشرة.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        API Keys\n                    </div>\n                    <div class="field-value">\n                        إدارة المفاتيح\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Tokens\n                    </div>\n                    <div class="field-value">\n                        إدارة الرموز\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="#api_credentials" role="button">\n                فتح المفاتيح والرموز\n            </a>\n\n        </section>\n\n\n        <!-- AUTH -->\n\n        <section class="card">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        🔐\n                    </div>\n\n                    <div class="card-title">\n                        المصادقة والصلاحيات\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    محمية\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إعدادات المصادقة والتحكم في الوصول حسب صلاحية المستخدم.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        Authentication\n                    </div>\n                    <div class="field-value">\n                        مفعّلة\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Permissions\n                    </div>\n                    <div class="field-value">\n                        Role-Based\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="#authentication_info" role="button">\n                إدارة المصادقة\n            </a>\n\n        </section>\n\n\n        <!-- WEBHOOK -->\n\n        <section class="card full">\n\n            <div class="card-head">\n\n                <div class="card-title-wrap">\n\n                    <div class="icon">\n                        🔔\n                    </div>\n\n                    <div class="card-title">\n                        Webhook\n                    </div>\n\n                </div>\n\n                <div class="status">\n                    جاهز للإعداد\n                </div>\n\n            </div>\n\n            <div class="card-description">\n                إدارة Endpoint والأحداث وبيانات التحقق ومتابعة عمليات التسليم.\n            </div>\n\n            <div class="fields">\n\n                <div class="field">\n                    <div class="field-label">\n                        Endpoint\n                    </div>\n                    <div class="field-value">\n                        محفوظ بشكل آمن\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Events\n                    </div>\n                    <div class="field-value">\n                        معاملات الدفع\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Secret\n                    </div>\n                    <div class="field-value">\n                        غير معروض\n                    </div>\n                </div>\n\n                <div class="field">\n                    <div class="field-label">\n                        Delivery\n                    </div>\n                    <div class="field-value">\n                        متابعة الحالة\n                    </div>\n                </div>\n\n            </div>\n\n            <a class="card-button" href="#webhook_info" role="button">\n                إدارة Webhook\n            </a>\n\n        </section>\n\n\n    </main>\n\n\n    <div class="footer">\n        FADL PAY · Merchant Sandbox\n    </div>\n\n</div>\n\n</div>'


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

        gr.Markdown("### 📋 مفاتيح API المسجلة")
        api_keys_status_md = gr.Markdown(value="اضغطي تحديث القائمة لتحميل المفاتيح.")
        api_keys_json = gr.JSON(
            label="API Credentials — بيانات غير سرية فقط",
            value=[],
        )

        with gr.Row():
            api_keys_refresh_btn = gr.Button("🔄 تحديث قائمة API Keys")
            api_key_revoke_id = gr.Number(
                label="رقم المفتاح المراد إلغاؤه",
                precision=0,
            )
            csrf_token_box = gr.Textbox(
                label="CSRF token",
                value="",
                type="password",
                visible=False,
                interactive=False,
            )
            api_key_revoke_btn = gr.Button(
                "🚫 إلغاء المفتاح",
                variant="stop",
            )

        api_key_revoke_status_md = gr.Markdown(value="")

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

        gr.Markdown("### 🔔 Webhook Endpoints")
        webhook_status_md = gr.Markdown(
            value="اضغطي تحديث القائمة لعرض Webhook endpoints الخاصة بحسابك."
        )
        webhook_endpoints_json = gr.JSON(
            label="Webhook Endpoints",
            value=[],
        )
        webhook_refresh_btn = gr.Button("🔄 تحديث Webhook Endpoints")

        with gr.Row():
            webhook_endpoint_id = gr.Number(
                label="رقم Endpoint لعرض سجل التسليم",
                precision=0,
            )
            webhook_deliveries_btn = gr.Button("📜 عرض سجل التسليم")

        webhook_deliveries_status_md = gr.Markdown(value="")
        webhook_deliveries_json = gr.JSON(
            label="Webhook Delivery History — آخر 100 سجل",
            value=[],
        )

        gr.Button(
            "🔁 إعادة محاولة Webhook — قيد الإصلاح",
            interactive=False,
        )
        gr.Markdown(
            "ملاحظة: عرض سجل التسليم متاح، لكن إعادة المحاولة معطّلة مؤقتاً "
            "حتى إصلاح عقد الخادم ومنع إرسال حدث غير صحيح."
        )

        gr.HTML(
            """
            <section id="reports_info" dir="rtl" style="padding:20px 4px 8px">
              <h2>📊 تقارير التاجر</h2>
              <p style="font-size:15px;line-height:1.8">
                التقارير مقيّدة بجلسة التاجر الحالية وصلاحية reports.read.
                التصدير أدناه يعرض CSV كنص قابل للنسخ والحفظ.
              </p>
            </section>
            """
        )

        with gr.Row():
            report_start_date = gr.Textbox(
                label="من تاريخ (YYYY-MM-DD)",
                placeholder="2026-10-01",
            )
            report_end_date = gr.Textbox(
                label="إلى تاريخ (YYYY-MM-DD)",
                placeholder="2026-10-31",
            )

        with gr.Row():
            report_status_filter = gr.Dropdown(
                choices=["", "pending", "paid", "failed", "cancelled"],
                value="",
                label="حالة المعاملة",
            )
            report_currency_filter = gr.Textbox(
                label="العملة (اختياري)",
                placeholder="SDG",
            )

        with gr.Row():
            report_run_btn = gr.Button("📊 إنشاء التقرير", variant="primary")
            report_export_btn = gr.Button("📄 تجهيز CSV")

        report_status_md = gr.Markdown(value="")
        report_json = gr.JSON(label="نتيجة التقرير", value={})
        report_csv_status_md = gr.Markdown(value="")
        report_csv_text = gr.Textbox(
            label="CSV — انسخي النص واحفظيه بامتداد .csv",
            value="",
            lines=10,
            interactive=False,
        )

        create_api_key_btn.click(
            fn=create_dashboard_api_key,
            inputs=[csrf_token_box],
            outputs=[
                api_key_status_md,
                api_key_once,
            ],
        ).then(
            fn=load_api_keys_ui,
            inputs=None,
            outputs=[api_keys_status_md, api_keys_json],
        )

        api_keys_refresh_btn.click(
            fn=load_api_keys_ui,
            inputs=None,
            outputs=[api_keys_status_md, api_keys_json],
        )

        api_key_revoke_btn.click(
            fn=revoke_api_key_ui,
            inputs=[api_key_revoke_id, csrf_token_box],
            outputs=[api_key_revoke_status_md],
        ).then(
            fn=load_api_keys_ui,
            inputs=None,
            outputs=[api_keys_status_md, api_keys_json],
        )

        webhook_refresh_btn.click(
            fn=load_webhook_endpoints_ui,
            inputs=None,
            outputs=[webhook_status_md, webhook_endpoints_json],
        )

        webhook_deliveries_btn.click(
            fn=load_webhook_deliveries_ui,
            inputs=[webhook_endpoint_id],
            outputs=[webhook_deliveries_status_md, webhook_deliveries_json],
        )

        report_run_btn.click(
            fn=load_reports_ui,
            inputs=[
                report_start_date,
                report_end_date,
                report_status_filter,
                report_currency_filter,
            ],
            outputs=[report_status_md, report_json],
        )

        report_export_btn.click(
            fn=export_reports_csv_ui,
            inputs=[
                report_start_date,
                report_end_date,
                report_status_filter,
                report_currency_filter,
            ],
            outputs=[report_csv_status_md, report_csv_text],
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
        ).then(
            fn=load_api_keys_ui,
            inputs=None,
            outputs=[api_keys_status_md, api_keys_json],
        ).then(
            fn=load_webhook_endpoints_ui,
            inputs=None,
            outputs=[webhook_status_md, webhook_endpoints_json],
        ).then(fn=load_dashboard_csrf_token, inputs=None, outputs=[csrf_token_box])
    return demo



