import sqlite3
import gradio as gr

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


def create_dashboard(session_token=None):

    if not session_token:
        raise PermissionError("Authentication required")

    # --------------------------------------------------------
    # Keep the existing authenticated server-side session flow.
    # No client-provided merchant identity is trusted here.
    # --------------------------------------------------------
    data = create_dashboard_from_session(session_token)

    # --------------------------------------------------------
    # Green merchant gateway
    #
    # This is display/navigation only.
    # No database writes.
    # No auth/session changes.
    # Existing /pay and /admin/ routes are untouched.
    # --------------------------------------------------------

    with gr.Blocks(
        title="FADL PAY — بوابة التاجر",
        css="""
        .fadl-gateway {
            min-height: 72vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 28px 16px;
            direction: rtl;
            font-family: Arial, Tahoma, sans-serif;
        }

        .fadl-card {
            width: min(720px, 100%);
            background: linear-gradient(145deg, #ffffff 0%, #f7fff9 100%);
            border: 1px solid rgba(22, 101, 52, 0.14);
            border-radius: 28px;
            padding: 38px 30px;
            box-shadow: 0 18px 50px rgba(20, 83, 45, 0.12);
            text-align: center;
        }

        .fadl-logo {
            width: 72px;
            height: 72px;
            margin: 0 auto 16px;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #166534, #15803d);
            color: white;
            font-size: 34px;
            box-shadow: 0 10px 24px rgba(21, 128, 61, 0.25);
        }

        .fadl-title {
            color: #14532d;
            font-size: 34px;
            font-weight: 800;
            margin: 0;
        }

        .fadl-subtitle {
            color: #4b6354;
            font-size: 17px;
            margin: 10px 0 26px;
        }

        .fadl-merchant {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 18px;
            padding: 15px 18px;
            margin-bottom: 24px;
            color: #166534;
            line-height: 1.9;
        }

        .fadl-actions {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 16px;
            margin-top: 10px;
        }

        .fadl-action {
            display: flex;
            min-height: 145px;
            align-items: center;
            justify-content: center;
            flex-direction: column;
            gap: 9px;
            padding: 22px 16px;
            border-radius: 22px;
            text-decoration: none !important;
            transition: transform .18s ease, box-shadow .18s ease;
            box-sizing: border-box;
        }

        .fadl-action:hover {
            transform: translateY(-3px);
            box-shadow: 0 12px 28px rgba(20, 83, 45, 0.16);
        }

        .fadl-pay {
            background: linear-gradient(135deg, #166534, #15803d);
            color: white !important;
        }

        .fadl-admin {
            background: white;
            color: #166534 !important;
            border: 2px solid #86efac;
        }

        .fadl-icon {
            font-size: 34px;
        }

        .fadl-action-title {
            font-size: 20px;
            font-weight: 800;
        }

        .fadl-action-desc {
            font-size: 13px;
            opacity: .82;
        }

        .fadl-footer {
            margin-top: 25px;
            color: #718096;
            font-size: 12px;
        }

        @media (max-width: 620px) {
            .fadl-card {
                padding: 30px 18px;
                border-radius: 22px;
            }

            .fadl-title {
                font-size: 29px;
            }

            .fadl-actions {
                grid-template-columns: 1fr;
            }
        }
        """
    ) as demo:

        gr.HTML(
            f"""
            <div class="fadl-gateway">
                <div class="fadl-card">

                    <div class="fadl-logo">💳</div>

                    <h1 class="fadl-title">FADL PAY</h1>

                    <div class="fadl-subtitle">
                        بوابة التاجر
                    </div>

                    <div class="fadl-merchant">
                        <strong>👤 {data["merchant"]}</strong><br>
                        {data["email"]}<br>
                        <span>🟢 الحساب نشط</span>
                    </div>

                    <div class="fadl-actions">

                        <a
                            class="fadl-action fadl-pay"
                            href="/pay?v=7fe68562"
                        >
                            <div class="fadl-icon">💳</div>
                            <div class="fadl-action-title">واجهة الدفع</div>
                            <div class="fadl-action-desc">
                                فتح واجهة الدفع للعملاء
                            </div>
                        </a>

                        <a
                            class="fadl-action fadl-admin"
                            href="/admin/"
                        >
                            <div class="fadl-icon">📊</div>
                            <div class="fadl-action-title">الإدارة المالية</div>
                            <div class="fadl-action-desc">
                                متابعة العمليات والبيانات المالية
                            </div>
                        </a>

                    </div>

                    <div class="fadl-footer">
                        FADL PAY — بوابة التاجر الآمنة
                    </div>

                </div>
            </div>
            """
        )

    return demo
