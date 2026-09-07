from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

COUNTRY_CURRENCY = {"SD": "SDG", "EG": "EGP", "SA": "SAR", "AE": "AED", "US": "USD"}
CURRENCY_DATA = {"AED": {"name": "UAE Dirham", "symbol": "د.إ", "decimal_places": 2}, "EGP": {"name": "Egyptian Pound", "symbol": "ج.م", "decimal_places": 2}, "SAR": {"name": "Saudi Riyal", "symbol": "﷼", "decimal_places": 2}, "SDG": {"name": "Sudanese Pound", "symbol": "ج.س", "decimal_places": 2}, "USD": {"name": "United States Dollar", "symbol": "$", "decimal_places": 2}}


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

<script>

const COUNTRY_CURRENCY = {"SD": "SDG", "EG": "EGP", "SA": "SAR", "AE": "AED", "US": "USD"};

const CURRENCY_DATA = {"AED": {"name": "UAE Dirham", "symbol": "د.إ", "decimal_places": 2}, "EGP": {"name": "Egyptian Pound", "symbol": "ج.م", "decimal_places": 2}, "SAR": {"name": "Saudi Riyal", "symbol": "﷼", "decimal_places": 2}, "SDG": {"name": "Sudanese Pound", "symbol": "ج.س", "decimal_places": 2}, "USD": {"name": "United States Dollar", "symbol": "$", "decimal_places": 2}};


function updateCurrency() {

    const country =
        document.getElementById("country").value;

    const currencyInput =
        document.getElementById("currency");

    const currencyCode =
        COUNTRY_CURRENCY[country];

    if (!currencyCode) {
        currencyInput.value = "";
        return;
    }

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


function startPayment() {

    const country =
        document.getElementById("country").value;

    const currency =
        document.getElementById("currency").value;

    const amount =
        document.getElementById("amount").value;

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

    showResult(
        "🟢 البيانات صحيحة — الواجهة جاهزة.",
        true
    );
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

</script>

</body>

</html>"""

    return HTMLResponse(content=html)
