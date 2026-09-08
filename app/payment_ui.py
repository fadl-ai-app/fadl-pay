from pathlib import Path

import gradio as gr


FADL_PAY_COMPACT_UI_CSS = """
/* ==========================================================
   FADL PAY — Compact Desktop + Responsive Mobile
   ========================================================== */

/* الحاوية الرئيسية */
.fadl-pay-shell {
    width: min(520px, calc(100% - 32px)) !important;
    max-width: 520px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* عنوان الواجهة */
.fadl-pay-header {
    text-align: center !important;
}

/* كرت الدفع */
.fadl-pay-card {
    width: 100% !important;
    max-width: 520px !important;
    margin-left: auto !important;
    margin-right: auto !important;
}

/* الشاشات الصغيرة */
@media (max-width: 700px) {
    .fadl-pay-shell {
        width: calc(100% - 20px) !important;
        max-width: none !important;
    }

    .fadl-pay-card {
        max-width: none !important;
    }
}

/* الشاشات الكبيرة جدًا */
@media (min-width: 1200px) {
    .fadl-pay-shell {
        width: 520px !important;
        max-width: 520px !important;
    }

    .fadl-pay-card {
        max-width: 520px !important;
    }
}
"""



# ============================================================
# 💳 FADL PAY — Payment UI
# ============================================================

COUNTRIES = [
    "Egypt",
    "Saudi Arabia",
    "Sudan",
    "United Arab Emirates",
    "United States",
]

CURRENCIES = [
    "EGP",
    "SAR",
    "SDG",
    "AED",
    "USD",
]

PAYMENT_METHODS = [
    "🏦 بنك",
    "📱 محفظة إلكترونية",
    "💳 بطاقة",
]


def submit_payment(
    country,
    currency,
    amount,
    customer_reference,
    payment_method,
):
    """
    إنشاء عملية دفع من خلال Backend الداخلي.

    لا يتم كشف API Key للمستخدم.
    """

    if not country:
        return "⚠️ الرجاء اختيار الدولة."

    if not currency:
        return "⚠️ الرجاء اختيار العملة."

    if not amount:
        return "⚠️ الرجاء إدخال المبلغ."

    if not payment_method:
        return "⚠️ الرجاء اختيار طريقة الدفع."

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "⚠️ المبلغ يجب أن يكون رقمًا صحيحًا."

    if amount <= 0:
        return "⚠️ المبلغ يجب أن يكون أكبر من صفر."

    # إنشاء المعاملة داخل Backend
    from backend.api import create_transaction

    # merchant_reference داخلي — لا يظهر للمستخدم
    import os

    merchant_reference = os.getenv(
        "FADL_UI_MERCHANT_REFERENCE",
        ""
    ).strip()

    if not merchant_reference:
        return (
            "⚠️ إعداد التاجر غير مكتمل في بيئة التشغيل.\n\n"
            "يرجى ضبط FADL_UI_MERCHANT_REFERENCE في Backend."
        )

    try:
        transaction_reference = create_transaction(
            merchant_reference=merchant_reference,
            amount=amount,
            currency=currency,
            customer_reference=customer_reference or None,
            payment_method=payment_method,
            idempotency_key=None,
        )

        return (
            "🟢 **تم إنشاء عملية الدفع بنجاح**\n\n"
            f"🌍 الدولة: {country}\n"
            f"💱 العملة: {currency}\n"
            f"💰 المبلغ: {amount}\n"
            f"👤 المرجع: {customer_reference or 'غير محدد'}\n"
            f"💳 طريقة الدفع: {payment_method}\n\n"
            f"🔖 **رقم العملية:** `{transaction_reference}`\n\n"
            "🧪 FADL PAY — Sandbox"
        )

    except ValueError as error:
        return f"❌ تعذر إنشاء عملية الدفع: {error}"

    except Exception as error:
        return (
            "❌ حدث خطأ أثناء إنشاء عملية الدفع.\n\n"
            f"التفاصيل: {error}"
        )


with gr.Blocks(
    title="FADL PAY",
    theme=gr.themes.Soft(),
    css_paths=str(Path(__file__).with_name("fadl_pay.css")),
) as demo:

    with gr.Column(elem_classes="fadl-pay-shell"):

        gr.Markdown(
            """
            # 💳 FADL PAY

            ### ادفع بسهولة وأمان

            **FADL PAY — Sandbox**
            """,
            elem_classes="fadl-pay-header",
        )

        with gr.Group(elem_classes="fadl-pay-card"):

            country = gr.Dropdown(
                choices=COUNTRIES,
                label="🌍 الدولة",
                value=None,
                interactive=True,
            )

            # 🔥 العملة أصبحت حقلًا مستقلًا وواضحًا
            currency = gr.Dropdown(
                choices=CURRENCIES,
                label="💱 العملة",
                value=None,
                interactive=True,
            )

            amount = gr.Number(
                label="💰 المبلغ",
                minimum=1,
                precision=0,
                interactive=True,
            )

            customer_reference = gr.Textbox(
                label="👤 رقم / مرجع العميل",
                placeholder="أدخل رقم أو مرجع العميل",
                interactive=True,
            )

            payment_method = gr.Dropdown(
                choices=PAYMENT_METHODS,
                label="💳 طريقة الدفع",
                value=None,
                interactive=True,
            )

            pay_button = gr.Button(
                "💳 ادفع الآن",
                variant="primary",
            )


    result = gr.Markdown()

    pay_button.click(
        submit_payment,
        inputs=[
            country,
            currency,
            amount,
            customer_reference,
            payment_method,
        ],
        outputs=result,
    )

