from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from payments.transaction_engine import create_transaction, get_transaction

router = APIRouter()

COUNTRY_CURRENCY = {"SD": "SDG", "EG": "EGP", "SA": "SAR", "AE": "AED", "US": "USD"}
CURRENCY_DATA = {"AED": {"name": "UAE Dirham", "symbol": "د.إ", "decimal_places": 2}, "EGP": {"name": "Egyptian Pound", "symbol": "ج.م", "decimal_places": 2}, "SAR": {"name": "Saudi Riyal", "symbol": "﷼", "decimal_places": 2}, "SDG": {"name": "Sudanese Pound", "symbol": "ج.س", "decimal_places": 2}, "USD": {"name": "United States Dollar", "symbol": "$", "decimal_places": 2}}




@router.post("/pay/create")
async def create_customer_payment(request: Request):

    data = await request.json()

    country = data.get("country")
    currency = data.get("currency")
    amount = data.get("amount")
    customer_reference = data.get("customer_reference")
    payment_method = data.get("payment_method")

    if country not in COUNTRY_CURRENCY:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="الدولة غير مدعومة"
        )

    expected_currency = COUNTRY_CURRENCY[country]

    if currency != expected_currency:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="العملة لا تطابق الدولة"
        )

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="المبلغ غير صحيح"
        )

    if amount <= 0:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="المبلغ يجب أن يكون أكبر من صفر"
        )

    if payment_method not in {
        "bank",
        "mobile_money",
        "card",
    }:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="طريقة الدفع غير مدعومة"
        )

    # --------------------------------------------------------
    # Sandbox merchant
    # --------------------------------------------------------

    MERCHANT_REFERENCE = "MER-007FFD589DE34A66A9ACB5063DD61F51"

    transaction_reference = create_transaction(
        merchant_reference=MERCHANT_REFERENCE,
        amount=amount,
        currency=currency,
        customer_reference=customer_reference,
        payment_method=payment_method,
        idempotency_key=None,
    )

    transaction = get_transaction(
        transaction_reference,
        merchant_reference=MERCHANT_REFERENCE,
    )

    return {
        "success": True,
        "environment": "sandbox",
        "transaction": transaction,
    }


@router.get("/pay", response_class=HTMLResponse)
def customer_checkout():

    html = """<!DOCTYPE html>
<html lang="ar" dir="rtl">

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>FADL PAY</title>

<style>

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    background: #f5f7fa;
    font-family: Arial, Tahoma, sans-serif;
    color: #17202a;
}

.container {
    width: min(460px, calc(100% - 30px));
    margin: 45px auto;
}

.card {
    background: white;
    border-radius: 18px;
    padding: 28px;
    box-shadow: 0 8px 30px rgba(0,0,0,.08);
}

.logo {
    text-align: center;
    font-size: 30px;
    font-weight: bold;
}

.subtitle {
    text-align: center;
    color: #687078;
    margin: 8px 0 28px;
}

label {
    display: block;
    margin: 15px 0 7px;
    font-weight: bold;
}

input,
select {
    width: 100%;
    padding: 13px;
    border: 1px solid #d7dce1;
    border-radius: 10px;
    font-size: 16px;
    background: white;
}

.currency-box {
    background: #f1f3f5;
}

button {
    width: 100%;
    margin-top: 24px;
    padding: 15px;
    border: 0;
    border-radius: 11px;
    background: #111827;
    color: white;
    font-size: 17px;
    font-weight: bold;
    cursor: pointer;
}

.result {
    margin-top: 18px;
    padding: 14px;
    border-radius: 10px;
    display: none;
    text-align: center;
}

.note {
    margin-top: 20px;
    text-align: center;
    color: #7a828a;
    font-size: 13px;
}

</style>

</head>

<body>

<div class="container">

<div class="card">

<div class="logo">
💳 FADL PAY
</div>

<div class="subtitle">
ادفع بسهولة وأمان
</div>

<label>
🌍 الدولة
</label>

<select id="country"
        onchange="updateCurrency()">

<option value="">
اختر الدولة
</option>

<option value="EG">Egypt</option>
<option value="SA">Saudi Arabia</option>
<option value="SD">Sudan</option>
<option value="AE">United Arab Emirates</option>
<option value="US">United States</option>

</select>

<label>
💱 العملة
</label>

<input
    id="currency"
    class="currency-box"
    type="text"
    readonly
    placeholder="تُحدد تلقائيًا"
/>

<label>
💰 المبلغ
</label>

<input
    id="amount"
    type="number"
    min="1"
    step="1"
    placeholder="أدخل المبلغ"
/>

<label>
👤 رقم / مرجع العميل
</label>

<input
    id="customer_reference"
    type="text"
    maxlength="255"
    placeholder="اختياري"
/>

<label>
💳 طريقة الدفع
</label>

<select id="payment_method">

<option value="">
اختر طريقة الدفع
</option>

<option value="bank">
🏦 بنك
</option>

<option value="mobile_money">
📱 محفظة إلكترونية
</option>

<option value="card">
💳 بطاقة
</option>

</select>

<button onclick="startPayment()">
💳 ادفع الآن
</button>

<div id="result"
     class="result">
</div>

<div class="note">
FADL PAY — Sandbox
</div>

</div>

</div>

<script>const COUNTRY_CURRENCY = {
    "SD": "SDG",
    "EG": "EGP",
    "SA": "SAR",
    "AE": "AED",
    "US": "USD"
};

const CURRENCY_DATA = {
    "AED": {"name": "UAE Dirham", "symbol": "د.إ"},
    "EGP": {"name": "Egyptian Pound", "symbol": "ج.م"},
    "SAR": {"name": "Saudi Riyal", "symbol": "﷼"},
    "SDG": {"name": "Sudanese Pound", "symbol": "ج.س"},
    "USD": {"name": "United States Dollar", "symbol": "$"}
};

function updateCurrency() {
    const countryInput =
        document.getElementById("country");

    const currencyInput =
        document.getElementById("currency");

    if (!countryInput || !currencyInput) {
        return;
    }

    const currencyCode =
        COUNTRY_CURRENCY[countryInput.value];

const info =
        CURRENCY_DATA[currencyCode];

    if (info) {
        currencyInput.value =
            currencyCode + " — " +
            info.name + " " +
            info.symbol;
    } else {
        currencyInput.value =
            currencyCode;
    }
}



async function startPayment() {

    const country =
        document.getElementById("country").value;

    const currency =
        document.getElementById("currency").value;

    const amount =
        document.getElementById("amount").value;

    const customerReference =
        document.getElementById("customer_reference").value.trim();

    const paymentMethod =
        document.getElementById("payment_method").value;


    if (!country) {
        showResult("❌ اختر الدولة أولاً", false);
        return;
    }

    if (!currency) {
        showResult("❌ لم يتم تحديد العملة", false);
        return;
    }

    if (!amount || Number(amount) <= 0) {
        showResult("❌ أدخل مبلغًا صحيحًا", false);
        return;
    }

    if (!paymentMethod) {
        showResult("❌ اختر طريقة الدفع", false);
        return;
    }

    showResult("⏳ جارٍ إنشاء عملية الدفع في Sandbox...", true);

    try {

        const response = await fetch("/pay/create", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                country: country,
                currency: currency,
                amount: Number(amount),
                customer_reference: customerReference || null,
                payment_method: paymentMethod
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showResult(
                "❌ " + (data.detail || "تعذر إنشاء العملية"),
                false
            );
            return;
        }

        if (data.success && data.transaction) {

            const transaction =
                data.transaction;

            showResult(
                "🟢 تم إنشاء العملية بنجاح\n\n" +
                "رقم العملية: " +
                transaction.transaction_reference +
                "\nالحالة: " +
                transaction.status +
                "\nالمبلغ: " +
                transaction.amount +
                " " +
                transaction.currency,
                true
            );

        } else {

            showResult(
                "❌ تعذر إنشاء العملية",
                false
            );
        }

    } catch (error) {

        showResult(
            "❌ حدث خطأ في الاتصال بالسيرفر",
            false
        );

        console.error(error);
    }
}


function showResult(message, success) {

    const result =
        document.getElementById("result");

    result.style.display = "block";

    result.style.background =
        success ? "#eaf8ef" : "#fdecec";

    result.style.color =
        success ? "#176b36" : "#a12626";

    result.innerText = message;
}


document.addEventListener("DOMContentLoaded", function () {
    const countryInput = document.getElementById("country");

    if (countryInput) {
        countryInput.addEventListener("change", updateCurrency);
        updateCurrency();
    }
});
</script>

</body>

</html>"""

    return HTMLResponse(content=html)
