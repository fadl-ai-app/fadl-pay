from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from fastapi import Request
from payments.transaction_engine import create_transaction, get_transaction, update_transaction_status

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


@router.post("/pay/sandbox/status")
async def customer_sandbox_status(request: Request):
    """
    Sandbox-only Customer Checkout completion endpoint.

    This endpoint is intentionally separate from the public
    API-key-protected sandbox endpoint in backend/api.py.

    It is used only by the Customer Checkout Sandbox controls.
    No real money is processed.
    """

    data = await request.json()

    transaction_reference = data.get("transaction_reference")
    new_status = data.get("status")

    allowed_statuses = {
        "paid",
        "failed",
        "cancelled",
    }

    if not transaction_reference:
        raise HTTPException(
            status_code=400,
            detail="رقم العملية مطلوب",
        )

    if new_status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="حالة Sandbox غير مدعومة",
        )

    MERCHANT_REFERENCE = "MER-007FFD589DE34A66A9ACB5063DD61F51"

    transaction = get_transaction(
        transaction_reference,
        merchant_reference=MERCHANT_REFERENCE,
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="العملية غير موجودة",
        )

    try:
        result = update_transaction_status(
            transaction_reference,
            new_status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    return {
        "success": True,
        "environment": "sandbox",
        "transaction": result,
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

<script>

function updateCurrency() {

    const countryInput =
        document.getElementById("country");

    const currencyInput =
        document.getElementById("currency");

    if (!countryInput || !currencyInput) {
        return;
    }

    const country =
        countryInput.value;

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



async function startPayment() {

    const country =
        document.getElementById("country").value;

    const currency =
        COUNTRY_CURRENCY[country];

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

    const paymentEnabled =
        BACKEND_ENABLED_COUNTRIES[country] === currency &&
        SUPPORTED_PAYMENT_CURRENCIES.has(currency);

    if (!paymentEnabled) {
        showResult(
            "❌ الدولة أو العملة غير مدعومة للدفع حاليًا",
            false
        );
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
                "🟢 تم إنشاء العملية بنجاح\\n\\n" +
                "رقم العملية: " +
                transaction.transaction_reference +
                "\\nالحالة: " +
                transaction.status +
                "\\nالمبلغ: " +
                transaction.amount +
                " " +
                transaction.currency,
                true
            );

            showSandboxControls(transaction);

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


function showSandboxControls(transaction) {

    const result = document.getElementById("result");

    if (!result) {
        return;
    }

    const oldControls =
        document.getElementById("sandbox-controls");

    if (oldControls) {
        oldControls.remove();
    }

    const controls =
        document.createElement("div");

    controls.id = "sandbox-controls";

    controls.style.marginTop = "16px";
    controls.style.padding = "14px";
    controls.style.border = "1px solid #ddd";
    controls.style.borderRadius = "12px";
    controls.style.background = "#fafafa";

    controls.innerHTML = `
        <div style="
            font-weight:700;
            margin-bottom:10px;
            text-align:center;
        ">
            🧪 نتيجة الدفع — Sandbox
        </div>

        <div style="
            display:flex;
            gap:8px;
            flex-wrap:wrap;
            justify-content:center;
        ">
            <button
                type="button"
                onclick="completeSandboxPayment(
                    '${transaction.transaction_reference}',
                    'paid'
                )"
                style="
                    padding:9px 14px;
                    border:0;
                    border-radius:8px;
                    cursor:pointer;
                "
            >
                🟢 نجاح الدفع
            </button>

            <button
                type="button"
                onclick="completeSandboxPayment(
                    '${transaction.transaction_reference}',
                    'failed'
                )"
                style="
                    padding:9px 14px;
                    border:0;
                    border-radius:8px;
                    cursor:pointer;
                "
            >
                🔴 فشل الدفع
            </button>

            <button
                type="button"
                onclick="completeSandboxPayment(
                    '${transaction.transaction_reference}',
                    'cancelled'
                )"
                style="
                    padding:9px 14px;
                    border:0;
                    border-radius:8px;
                    cursor:pointer;
                "
            >
                ⚫ إلغاء الدفع
            </button>
        </div>
    `;

    result.parentNode.insertBefore(
        controls,
        result.nextSibling
    );
}


async function completeSandboxPayment(
    transactionReference,
    status
) {

    showResult(
        "⏳ جارٍ تحديث نتيجة الدفع في Sandbox...",
        true
    );

    try {

        const response = await fetch(
            "/pay/sandbox/status",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    transaction_reference:
                        transactionReference,
                    status: status
                })
            }
        );

        const data = await response.json();

        if (!response.ok) {

            showResult(
                "❌ " +
                (
                    data.detail ||
                    "تعذر تحديث حالة العملية"
                ),
                false
            );

            return;
        }

        if (
            data.success &&
            data.transaction
        ) {

            const result =
                data.transaction;

            let icon = "🟢";

            if (result.new_status === "failed") {
                icon = "🔴";
            } else if (
                result.new_status === "cancelled"
            ) {
                icon = "⚫";
            }

            showResult(
                icon +
                " نتيجة الدفع: " +
                result.new_status +
                "\\n\\n" +
                "رقم العملية: " +
                result.transaction_reference,
                result.new_status === "paid"
            );

            const controls =
                document.getElementById(
                    "sandbox-controls"
                );

            if (controls) {
                controls.remove();
            }

        } else {

            showResult(
                "❌ تعذر تحديث حالة العملية",
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


const COUNTRY_CURRENCY = {
    "AD": "EUR",
    "AE": "AED",
    "AF": "AFN",
    "AG": "XCD",
    "AL": "ALL",
    "AM": "AMD",
    "AO": "AOA",
    "AQ": null,
    "AR": "ARS",
    "AS": "USD",
    "AT": "EUR",
    "AU": "AUD",
    "AW": "AWG",
    "AX": "EUR",
    "AZ": "AZN",
    "BA": "BAM",
    "BB": "BBD",
    "BD": "BDT",
    "BE": "EUR",
    "BF": "XOF",
    "BG": "BGN",
    "BH": "BHD",
    "BI": "BIF",
    "BJ": "XOF",
    "BL": "EUR",
    "BM": "BMD",
    "BN": "BND",
    "BO": "BOB",
    "BQ": "USD",
    "BR": "BRL",
    "BS": "BSD",
    "BT": "INR",
    "BV": "NOK",
    "BW": "BWP",
    "BY": "BYN",
    "BZ": "BZD",
    "CA": "CAD",
    "CC": "AUD",
    "CD": "CDF",
    "CF": "XAF",
    "CG": "XAF",
    "CH": "CHF",
    "CI": "XOF",
    "CK": "NZD",
    "CL": "CLP",
    "CM": "XAF",
    "CN": "CNY",
    "CO": "COP",
    "CR": "CRC",
    "CU": "CUP",
    "CV": "CVE",
    "CW": "XCG",
    "CX": "AUD",
    "CY": "EUR",
    "CZ": "CZK",
    "DE": "EUR",
    "DJ": "DJF",
    "DK": "DKK",
    "DM": "XCD",
    "DO": "DOP",
    "DZ": "DZD",
    "EC": "USD",
    "EE": "EUR",
    "EG": "EGP",
    "EH": "MAD",
    "ER": "ERN",
    "ES": "EUR",
    "ET": "ETB",
    "FI": "EUR",
    "FJ": "FJD",
    "FK": "FKP",
    "FM": "USD",
    "FO": "DKK",
    "FR": "EUR",
    "GA": "XAF",
    "GB": "GBP",
    "GD": "XCD",
    "GE": "GEL",
    "GF": "EUR",
    "GG": "GBP",
    "GH": "GHS",
    "GI": "GIP",
    "GL": "DKK",
    "GM": "GMD",
    "GN": "GNF",
    "GP": "EUR",
    "GQ": "XAF",
    "GR": "EUR",
    "GT": "GTQ",
    "GU": "USD",
    "GW": "XOF",
    "GY": "GYD",
    "HK": "HKD",
    "HN": "HNL",
    "HR": "EUR",
    "HT": "HTG",
    "HU": "HUF",
    "ID": "IDR",
    "IE": "EUR",
    "IL": "ILS",
    "IM": "GBP",
    "IN": "INR",
    "IO": "USD",
    "IQ": "IQD",
    "IR": "IRR",
    "IS": "ISK",
    "IT": "EUR",
    "JE": "GBP",
    "JM": "JMD",
    "JO": "JOD",
    "JP": "JPY",
    "KE": "KES",
    "KG": "KGS",
    "KH": "KHR",
    "KI": "AUD",
    "KM": "KMF",
    "KN": "XCD",
    "KP": "KPW",
    "KR": "KRW",
    "KW": "KWD",
    "KY": "KYD",
    "KZ": "KZT",
    "LA": "LAK",
    "LB": "LBP",
    "LC": "XCD",
    "LI": "CHF",
    "LK": "LKR",
    "LR": "LRD",
    "LS": "ZAR",
    "LT": "EUR",
    "LU": "EUR",
    "LV": "EUR",
    "LY": "LYD",
    "MA": "MAD",
    "MC": "EUR",
    "MD": "MDL",
    "ME": "EUR",
    "MF": "EUR",
    "MG": "MGA",
    "MH": "USD",
    "MK": "MKD",
    "ML": "XOF",
    "MM": "MMK",
    "MN": "MNT",
    "MO": "MOP",
    "MP": "USD",
    "MQ": "EUR",
    "MR": "MRU",
    "MS": "XCD",
    "MT": "EUR",
    "MU": "MUR",
    "MV": "MVR",
    "MW": "MWK",
    "MX": "MXN",
    "MY": "MYR",
    "MZ": "MZN",
    "NA": "ZAR",
    "NE": "XOF",
    "NF": "AUD",
    "NG": "NGN",
    "NI": "NIO",
    "NL": "EUR",
    "NO": "NOK",
    "NP": "NPR",
    "NR": "AUD",
    "NU": "NZD",
    "NZ": "NZD",
    "OM": "OMR",
    "PA": "PAB",
    "PE": "PEN",
    "PF": "XPF",
    "PG": "PGK",
    "PH": "PHP",
    "PK": "PKR",
    "PL": "PLN",
    "PM": "EUR",
    "PR": "USD",
    "PS": "ILS",
    "PT": "EUR",
    "PW": "USD",
    "PY": "PYG",
    "QA": "QAR",
    "RE": "EUR",
    "RO": "RON",
    "RS": "RSD",
    "RU": "RUB",
    "RW": "RWF",
    "SA": "SAR",
    "SB": "SBD",
    "SC": "SCR",
    "SD": "SDG",
    "SE": "SEK",
    "SG": "SGD",
    "SH": "SHP",
    "SI": "EUR",
    "SK": "EUR",
    "SL": "SLE",
    "SM": "EUR",
    "SN": "XOF",
    "SO": "SOS",
    "SR": "SRD",
    "SS": "SSP",
    "ST": "STN",
    "SV": "USD",
    "SX": "XCG",
    "SY": "SYP",
    "SZ": "SZL",
    "TC": "USD",
    "TD": "XAF",
    "TF": "EUR",
    "TG": "XOF",
    "TH": "THB",
    "TJ": "TJS",
    "TK": "NZD",
    "TL": "USD",
    "TM": "TMT",
    "TN": "TND",
    "TO": "TOP",
    "TR": "TRY",
    "TT": "TTD",
    "TV": "AUD",
    "TW": "TWD",
    "TZ": "TZS",
    "UA": "UAH",
    "UG": "UGX",
    "UM": "USD",
    "US": "USD",
    "UY": "UYU",
    "UZ": "UZS",
    "VA": "EUR",
    "VC": "XCD",
    "VE": "VES",
    "VI": "USD",
    "VN": "VND",
    "VU": "VUV",
    "WF": "XPF",
    "WS": "WST",
    "XK": "EUR",
    "YE": "YER",
    "YT": "EUR",
    "ZA": "ZAR",
    "ZM": "ZMW",
    "ZW": "USD"
};


const SUPPORTED_PAYMENT_CURRENCIES = new Set([
    "AED",
    "AUD",
    "BHD",
    "CAD",
    "EGP",
    "EUR",
    "GBP",
    "IDR",
    "INR",
    "KWD",
    "MYR",
    "NGN",
    "OMR",
    "PKR",
    "QAR",
    "SAR",
    "SDG",
    "TRY",
    "USD",
    "ZAR"
]);


const BACKEND_ENABLED_COUNTRIES = {
  "AD": "EUR",
  "AE": "AED",
  "AS": "USD",
  "AT": "EUR",
  "AU": "AUD",
  "AX": "EUR",
  "BE": "EUR",
  "BH": "BHD",
  "BL": "EUR",
  "BQ": "USD",
  "BT": "INR",
  "CA": "CAD",
  "CC": "AUD",
  "CX": "AUD",
  "CY": "EUR",
  "DE": "EUR",
  "EC": "USD",
  "EE": "EUR",
  "EG": "EGP",
  "ES": "EUR",
  "FI": "EUR",
  "FM": "USD",
  "FR": "EUR",
  "GB": "GBP",
  "GF": "EUR",
  "GG": "GBP",
  "GP": "EUR",
  "GR": "EUR",
  "GU": "USD",
  "HR": "EUR",
  "ID": "IDR",
  "IE": "EUR",
  "IM": "GBP",
  "IN": "INR",
  "IO": "USD",
  "IT": "EUR",
  "JE": "GBP",
  "KI": "AUD",
  "KW": "KWD",
  "LS": "ZAR",
  "LT": "EUR",
  "LU": "EUR",
  "LV": "EUR",
  "MC": "EUR",
  "ME": "EUR",
  "MF": "EUR",
  "MH": "USD",
  "MP": "USD",
  "MQ": "EUR",
  "MT": "EUR",
  "MY": "MYR",
  "NA": "ZAR",
  "NF": "AUD",
  "NG": "NGN",
  "NL": "EUR",
  "NR": "AUD",
  "OM": "OMR",
  "PK": "PKR",
  "PM": "EUR",
  "PR": "USD",
  "PT": "EUR",
  "PW": "USD",
  "QA": "QAR",
  "RE": "EUR",
  "SA": "SAR",
  "SD": "SDG",
  "SI": "EUR",
  "SK": "EUR",
  "SM": "EUR",
  "SV": "USD",
  "TC": "USD",
  "TF": "EUR",
  "TL": "USD",
  "TR": "TRY",
  "TV": "AUD",
  "UM": "USD",
  "US": "USD",
  "VA": "EUR",
  "VI": "USD",
  "XK": "EUR",
  "YT": "EUR",
  "ZA": "ZAR",
  "ZW": "USD",
};


const CURRENCY_DATA = {
    "AED": {"name": "UAE Dirham", "symbol": "د.إ"},
    "AUD": {"name": "Australian Dollar", "symbol": "A$"},
    "BHD": {"name": "Bahraini Dinar", "symbol": "د.ب"},
    "CAD": {"name": "Canadian Dollar", "symbol": "C$"},
    "EGP": {"name": "Egyptian Pound", "symbol": "ج.م"},
    "EUR": {"name": "Euro", "symbol": "€"},
    "GBP": {"name": "British Pound", "symbol": "£"},
    "IDR": {"name": "Indonesian Rupiah", "symbol": "Rp"},
    "INR": {"name": "Indian Rupee", "symbol": "₹"},
    "KWD": {"name": "Kuwaiti Dinar", "symbol": "د.ك"},
    "MYR": {"name": "Malaysian Ringgit", "symbol": "RM"},
    "NGN": {"name": "Nigerian Naira", "symbol": "₦"},
    "OMR": {"name": "Omani Rial", "symbol": "ر.ع."},
    "PKR": {"name": "Pakistani Rupee", "symbol": "₨"},
    "QAR": {"name": "Qatari Riyal", "symbol": "ر.ق"},
    "SAR": {"name": "Saudi Riyal", "symbol": "﷼"},
    "SDG": {"name": "Sudanese Pound", "symbol": "ج.س"},
    "TRY": {"name": "Turkish Lira", "symbol": "₺"},
    "USD": {"name": "United States Dollar", "symbol": "$"},
    "ZAR": {"name": "South African Rand", "symbol": "R"}
};


function updateCurrency() {
    const countryInput = document.getElementById("country");
    const currencyInput = document.getElementById("currency");

    if (!countryInput || !currencyInput) {
        return;
    }

    const country = countryInput.value;
    const currencyCode = COUNTRY_CURRENCY[country];

    if (!currencyCode) {
        currencyInput.value = "";
        return;
    }

    const info = CURRENCY_DATA[currencyCode];

    currencyInput.value = info
        ? currencyCode + " — " + info.name + " " + info.symbol
        : currencyCode;
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
