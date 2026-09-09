


CUSTOM_CSS = """
/* -----------------------------------------------------------
   الصفحة بالكامل
----------------------------------------------------------- */

html,
body,
.gradio-container {
    margin: 0 !important;
    padding: 0 !important;
    min-height: 100vh !important;
}

.gradio-container {
    background:
        radial-gradient(
            circle at 50% 20%,
            #f3f3f3 0%,
            #e8e8e8 38%,
            #dcdcdc 100%
        ) !important;
}


/* -----------------------------------------------------------
   إخفاء المساحات الافتراضية
----------------------------------------------------------- */

.gradio-container > .main {
    padding: 0 !important;
}

.contain {
    max-width: none !important;
}


/* -----------------------------------------------------------
   الحاوية الرئيسية
----------------------------------------------------------- */

.fadl-page {
    min-height: 100vh;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-sizing: border-box;
    padding: 40px 24px;
}


/* -----------------------------------------------------------
   كرت الدفع
----------------------------------------------------------- */

.fadl-card {
    width: min(560px, 100%);
    box-sizing: border-box;

    background:
        linear-gradient(
            145deg,
            #eeeeee 0%,
            #d9d9d9 45%,
            #cfcfcf 100%
        );

    border: 1px solid rgba(255,255,255,0.85);
    border-radius: 28px;

    padding: 34px;

    box-shadow:
        0 30px 70px rgba(0,0,0,0.16),
        0 8px 24px rgba(0,0,0,0.08),
        inset 0 1px 0 rgba(255,255,255,0.9);

    backdrop-filter: blur(10px);
}


/* -----------------------------------------------------------
   رأس الكرت
----------------------------------------------------------- */

.fadl-brand {
    text-align: center;
    margin-bottom: 6px;
}

.fadl-brand h1 {
    margin: 0;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: 0.5px;
    color: #202020;
}

.fadl-brand .pay {
    color: #555555;
}

.fadl-subtitle {
    text-align: center;
    color: #666666;
    font-size: 14px;
    margin-bottom: 28px;
}


/* -----------------------------------------------------------
   العناوين
----------------------------------------------------------- */

.fadl-card label span {
    color: #303030 !important;
    font-weight: 700 !important;
}


/* -----------------------------------------------------------
   الحقول
----------------------------------------------------------- */

.fadl-card input,
.fadl-card textarea,
.fadl-card select {
    background: rgba(255,255,255,0.82) !important;
    border: 1px solid rgba(0,0,0,0.10) !important;
    border-radius: 14px !important;
    color: #222222 !important;
    min-height: 48px !important;
    box-shadow:
        inset 0 1px 2px rgba(0,0,0,0.04) !important;
}

.fadl-card input:focus,
.fadl-card textarea:focus {
    border-color: #777777 !important;
    box-shadow:
        0 0 0 2px rgba(80,80,80,0.12) !important;
}


/* -----------------------------------------------------------
   زر الدفع
----------------------------------------------------------- */

.fadl-pay-btn {
    width: 100% !important;
    min-height: 54px !important;

    margin-top: 12px !important;

    border: none !important;
    border-radius: 16px !important;

    background:
        linear-gradient(
            135deg,
            #242424,
            #414141
        ) !important;

    color: white !important;

    font-size: 17px !important;
    font-weight: 800 !important;

    box-shadow:
        0 12px 24px rgba(0,0,0,0.20) !important;

    transition:
        transform 0.15s ease,
        box-shadow 0.15s ease !important;
}

.fadl-pay-btn:hover {
    transform: translateY(-2px);
    box-shadow:
        0 16px 30px rgba(0,0,0,0.25) !important;
}


/* -----------------------------------------------------------
   الأمان
----------------------------------------------------------- */

.fadl-secure {
    text-align: center;
    margin-top: 20px;
    color: #666666;
    font-size: 12px;
}


/* -----------------------------------------------------------
   الهاتف
----------------------------------------------------------- */

@media (max-width: 700px) {

    .fadl-page {
        align-items: flex-start;
        padding: 22px 14px;
    }

    .fadl-card {
        width: 100%;
        padding: 24px 18px;
        border-radius: 22px;
    }

    .fadl-brand h1 {
        font-size: 27px;
    }

    .fadl-subtitle {
        margin-bottom: 20px;
    }
}

/* FADL PAY — PRESERVED PRODUCTION CSS */

body {
    background: #f5f5f5 !important;
}

.gradio-container {
    max-width: 100% !important;
    padding: 0 !important;
}

#fadl-pay-card {
    width: 390px !important;
    max-width: calc(100vw - 32px) !important;
    margin: 55px auto !important;
    padding: 28px 26px !important;
    background: white !important;
    border-radius: 18px !important;
    box-shadow: 0 4px 20px rgba(0,0,0,0.10) !important;
}

#fadl-pay-card h1,
#fadl-pay-card h3 {
    text-align: center !important;
}

#fadl-pay-card h1 {
    margin-top: 0 !important;
    margin-bottom: 5px !important;
}

#fadl-pay-card h3 {
    margin-top: 0 !important;
    margin-bottom: 12px !important;
}

#fadl-pay-card button {
    width: 100% !important;
    min-height: 46px !important;
    border-radius: 10px !important;
}

@media (max-width: 600px) {
    #fadl-pay-card {
        width: calc(100vw - 24px) !important;
        max-width: none !important;
        margin: 12px auto !important;
        padding: 22px 16px !important;
        border-radius: 16px !important;
    }
}

"""



import gradio as gr


# ============================================================
# FADL PAY — SMALL CENTER PAYMENT CARD
# ============================================================

FADL_PREVIEW_CSS = r"""

/* ============================================================
   FADL PAY — SMALL CENTER PAYMENT CARD
   ============================================================ */

body {
    background: #f5f6f8 !important;
}

/* منطقة Gradio */
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 30px 15px !important;
}

/* كرت الدفع */
.fadl-pay-card {
    width: 520px !important;
    max-width: calc(100vw - 30px) !important;
    margin: 35px auto !important;
    padding: 28px !important;

    background: #ffffff !important;

    border: 1px solid #e5e7eb !important;
    border-radius: 22px !important;

    box-shadow:
        0 12px 35px rgba(0,0,0,.08) !important;

    box-sizing: border-box !important;
}

/* بطاقة العملة */
.fadl-auto-currency-card {
    width: 100% !important;
    box-sizing: border-box !important;

    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;

    padding: 13px 16px !important;
    margin: 10px 0 18px !important;

    background: #eeeeee !important;
    border: 1px solid #dddddd !important;
    border-radius: 14px !important;
}

.fadl-currency-title {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #666666 !important;
}

.fadl-currency-value {
    font-size: 17px !important;
    font-weight: 700 !important;
    color: #222222 !important;
}

/* الهاتف */
@media (max-width: 640px) {

    .gradio-container {
        padding: 10px !important;
    }

    .fadl-pay-card {
        width: 100% !important;
        max-width: 100% !important;

        margin: 10px auto !important;
        padding: 20px !important;

        border-radius: 18px !important;
    }
}

"""




# ============================================================
# FADL PAY — AUTO CURRENCY CARD
# ============================================================

FADL_AUTO_CURRENCY_CSS = r"""


/* ============================================================
   FADL PAY — AUTO CURRENCY CARD
   ============================================================ */

.fadl-auto-currency-card {

    width: 100%;
    box-sizing: border-box;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 13px 16px;
    margin: 10px 0 18px;

    background: #eeeeee;

    border: 1px solid #dddddd;
    border-radius: 14px;

    color: #333;

    box-shadow:
        0 3px 10px rgba(0,0,0,.04);
}

.fadl-currency-title {

    font-size: 14px;
    font-weight: 600;

    color: #666;
}

.fadl-currency-value {

    font-size: 17px;
    font-weight: 700;

    color: #222;

    letter-spacing: .5px;
}

/* ------------------------------------------------------------
   Laptop
   ------------------------------------------------------------ */

@media (min-width: 900px) {

    .fadl-pay-card {

        width: 540px !important;
        max-width: 540px !important;

        margin-left: auto !important;
        margin-right: auto !important;
    }
}

/* ------------------------------------------------------------
   Mobile
   ------------------------------------------------------------ */

@media (max-width: 640px) {

    .fadl-pay-card {

        width: calc(100vw - 20px) !important;

        max-width: none !important;

        margin: 10px auto !important;

        padding: 18px !important;
    }

    .fadl-auto-currency-card {

        padding: 12px 14px;
    }
}

"""

FADL_AUTO_CURRENCY_JS = r"""

<script>
(function () {

    const currencyMap = {
        "Egypt": "EGP",
        "مصر": "EGP",

        "Saudi Arabia": "SAR",
        "السعودية": "SAR",

        "Sudan": "SDG",
        "السودان": "SDG",

        "United Arab Emirates": "AED",
        "الإمارات": "AED",

        "United States": "USD",
        "أمريكا": "USD",
        "United States of America": "USD"
    };

    function findCountry() {

        const selects = document.querySelectorAll(
            "select, input"
        );

        for (const el of selects) {

            const value = (
                el.value ||
                el.getAttribute("value") ||
                ""
            ).trim();

            if (currencyMap[value]) {
                return currencyMap[value];
            }
        }

        return null;
    }

    function updateCurrency() {

        const currency = findCountry();

        if (!currency) return;

        let card = document.querySelector(
            ".fadl-auto-currency-card"
        );

        if (!card) {

            card = document.createElement("div");

            card.className =
                "fadl-auto-currency-card";

            const container =
                document.querySelector(
                    ".fadl-pay-card"
                ) ||
                document.querySelector(
                    ".gradio-container"
                );

            if (container) {
                container.prepend(card);
            }
        }

        card.innerHTML = `
            <div class="fadl-currency-title">
                💱 العملة
            </div>

            <div class="fadl-currency-value">
                ${currency}
            </div>
        `;
    }

    document.addEventListener(
        "change",
        function () {
            setTimeout(updateCurrency, 100);
        }
    );

    setInterval(updateCurrency, 800);

    setTimeout(updateCurrency, 500);

})();
</script>

"""




    
# ============================================================
# FADL PAY — BANK DEMO UI CSS
# ============================================================

FADL_BANK_UI_CSS = r"""


/* ==========================================================
   FADL PAY — BANK DEMO RESPONSIVE UI
   ========================================================== */

body,
.gradio-container {
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-container {
    min-height: 100vh !important;
}

/* المحتوى الرئيسي */
.fadl-pay-shell,
.fadl-pay-container,
.fadl-pay-card {
    box-sizing: border-box !important;
}

/* البطاقة الرئيسية */
.fadl-pay-card {
    width: min(560px, calc(100vw - 32px)) !important;
    max-width: 560px !important;
    margin: 32px auto !important;
    padding: 28px !important;

    border-radius: 22px !important;

    box-shadow:
        0 18px 45px rgba(0,0,0,.10),
        0 3px 12px rgba(0,0,0,.06) !important;

    background: rgba(255,255,255,.98) !important;
}

/* العنوان */
.fadl-pay-card h1,
.fadl-pay-card h2 {
    text-align: center !important;
}

/* الحقول */
.fadl-pay-card input,
.fadl-pay-card textarea,
.fadl-pay-card select {
    border-radius: 12px !important;
}

/* ==========================================================
   💱 Currency Card
   ========================================================== */

.fadl-currency-card {
    width: 100% !important;
    box-sizing: border-box !important;

    padding: 14px 16px !important;
    margin: 8px 0 18px 0 !important;

    border-radius: 14px !important;

    background: #eeeeee !important;
    border: 1px solid #dddddd !important;

    color: #333333 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;

    font-size: 15px !important;
}

.fadl-currency-card .currency-label {
    font-weight: 600 !important;
    color: #666 !important;
}

.fadl-currency-card .currency-value {
    font-weight: 700 !important;
    color: #222 !important;
}

/* زر الدفع */
.fadl-pay-card button {
    border-radius: 13px !important;
    min-height: 48px !important;
}

/* ==========================================================
   📱 Mobile
   ========================================================== */

@media (max-width: 640px) {

    .fadl-pay-card {
        width: calc(100vw - 20px) !important;
        max-width: none !important;

        margin: 10px auto !important;
        padding: 18px !important;

        border-radius: 18px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,.08) !important;
    }

    .fadl-currency-card {
        margin-top: 6px !important;
    }
}

/* ==========================================================
   💻 Large Screens
   ========================================================== */

@media (min-width: 1200px) {

    .fadl-pay-card {
        width: 540px !important;
        max-width: 540px !important;
        margin-left: auto !important;
        margin-right: auto !important;
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
    css=CUSTOM_CSS,
    title="FADL PAY",
    theme=gr.themes.Soft(),
) as demo:

    with gr.Column(elem_classes="fadl-page"):

        with gr.Column(
            elem_classes="fadl-card",
            elem_id="fadl-pay-card",
        ):

            gr.HTML(
                """
                <div class="fadl-brand">
                    <h1>💳 FADL <span class="pay">PAY</span></h1>
                </div>
                <div class="fadl-subtitle">
                    ادفع بسهولة وأمان
                </div>
                """
            )

            country = gr.Dropdown(
                choices=COUNTRIES,
                value=None,
                label="🌍 الدولة",
                interactive=True,
            )

            currency = gr.Dropdown(
                choices=CURRENCIES,
                value=None,
                label="💱 العملة",
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
                value=None,
                label="💳 طريقة الدفع",
                interactive=True,
            )

            pay_button = gr.Button(
                "💳 ادفع الآن",
                variant="primary",
                elem_classes="fadl-pay-btn",
            )

            result = gr.Markdown()

            gr.HTML(
                """
                <div class="fadl-secure">
                    🔒 دفع آمن • FADL PAY
                </div>
                """
            )

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

