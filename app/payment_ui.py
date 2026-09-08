
import gradio as gr


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
    if not country:
        return "⚠️ الرجاء اختيار الدولة."

    if not currency:
        return "⚠️ الرجاء اختيار العملة."

    if not amount:
        return "⚠️ الرجاء إدخال المبلغ."

    if not payment_method:
        return "⚠️ الرجاء اختيار طريقة الدفع."

    return (
        "🟢 تم استلام بيانات الدفع بنجاح\n\n"
        f"🌍 الدولة: {country}\n"
        f"💱 العملة: {currency}\n"
        f"💰 المبلغ: {amount}\n"
        f"👤 المرجع: {customer_reference or 'غير محدد'}\n"
        f"💳 طريقة الدفع: {payment_method}\n\n"
        "FADL PAY — Sandbox"
    )


with gr.Blocks(
    title="FADL PAY",
    theme=gr.themes.Soft(),
) as demo:

    gr.Markdown(
        """
        # 💳 FADL PAY

        ### ادفع بسهولة وأمان

        **FADL PAY — Sandbox**
        """
    )

    with gr.Group():

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

