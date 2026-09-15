# ============================================================
# 💰 FADL PAY — Financial Administration UI
# ============================================================

import gradio as gr

from app.financial_admin import (
    get_financial_summary,
    get_transaction_list,
    search_transactions,
)


def transaction_rows(data):
    return [
        [
            row["transaction_reference"],
            row["merchant_reference"],
            row["customer_reference"],
            row["amount"],
            row["currency"],
            row["payment_method"],
            row["status"],
            row["created_at"],
        ]
        for row in data
    ]


def load_financial_dashboard():
    data = get_financial_summary()
    transactions = get_transaction_list()

    s = data["summary"]

    summary = f"""
## 💰 الإدارة المالية — FADL PAY

| المؤشر | القيمة |
|---|---:|
| 💳 إجمالي المعاملات | {s['total_transactions']} |
| 💰 إجمالي قيمة المعاملات | {s['paid_amount'] + s['pending_amount'] + s['refunded_amount']} |
| 🟢 المحصّل | {s['paid_amount']} |
| 🟡 المعلّق | {s['pending_amount']} |
| 🔵 المرتجع | {s['refunded_amount']} |
| 🔴 الفاشل | {s['failed_amount']} |
| ⚫ الملغي | {s['cancelled_amount']} |
"""

    currency_rows = [
        [
            row["currency"],
            row["transactions"],
            row["gross_amount"],
            row["paid_amount"],
            row["refunded_amount"],
        ]
        for row in data["currencies"]
    ]

    merchant_rows = [
        [
            row["merchant_reference"],
            row["transactions"],
            row["gross_amount"],
            row["paid_amount"],
            row["refunded_amount"],
        ]
        for row in data["merchants"]
    ]

    return (
        summary,
        currency_rows,
        merchant_rows,
        transaction_rows(transactions),
    )


def search_transaction_rows(
    query,
    status,
    payment_method,
    currency,
):
    status = "" if status == "الكل" else status
    payment_method = "" if payment_method == "الكل" else payment_method
    currency = "" if currency == "الكل" else currency
    results = search_transactions(
        query=query,
        status=status,
        payment_method=payment_method,
        currency=currency,
    )

    return transaction_rows(results)


def clear_transaction_search():
    return (
        "",
        "الكل",
        "الكل",
        "الكل",
        transaction_rows(get_transaction_list()),
    )

# ============================================================
# 🎨 FADL PAY — FINANCIAL ADMIN V3 — CSS V2
# ============================================================
CUSTOM_CSS = r'''
/* ============================================================
   FADL PAY — FINANCIAL ADMIN V3 — CSS V2
   Clean Fintech Admin / RTL / Responsive
   ============================================================ */

/* ---------- Global ---------- */

html,
body {
    margin: 0 !important;
    padding: 0 !important;
    background: #17191c !important;
}

body {
    direction: rtl !important;
}

.gradio-container {
    max-width: 1180px !important;
    margin: 24px auto !important;
    padding: 0 18px 32px !important;
    background: #17191c !important;
}

/* ---------- Main admin card ---------- */

.gradio-container > .main {
    max-width: 1120px !important;
    margin: 0 auto !important;
}

/* ---------- Typography ---------- */

h1 {
    margin: 0 0 8px !important;
    padding: 0 !important;
    text-align: center !important;
    font-size: 30px !important;
    line-height: 1.25 !important;
    font-weight: 800 !important;
    letter-spacing: -0.3px !important;
}

h2 {
    margin: 22px 0 10px !important;
    font-size: 20px !important;
    font-weight: 800 !important;
    line-height: 1.3 !important;
}

h3 {
    margin: 18px 0 9px !important;
    font-size: 17px !important;
    font-weight: 750 !important;
}

/* ---------- Markdown ---------- */

.prose {
    line-height: 1.55 !important;
}

.prose p {
    margin: 5px 0 !important;
}

.prose strong {
    font-weight: 800 !important;
}

/* ---------- Rows ---------- */

.gr-row {
    gap: 10px !important;
    align-items: end !important;
}

/* ---------- Inputs ---------- */

input,
textarea,
select {
    min-height: 40px !important;
    border-radius: 9px !important;
    font-size: 14px !important;
}

/* ---------- Buttons ---------- */

button {
    min-height: 40px !important;
    border-radius: 9px !important;
    font-weight: 750 !important;
    font-size: 14px !important;
}

/* ---------- Search / filter controls ---------- */

.gradio-container .gr-input,
.gradio-container .gr-dropdown {
    border-radius: 9px !important;
}

/* ---------- Tables ---------- */

table {
    width: 100% !important;
    border-collapse: separate !important;
    border-spacing: 0 !important;
    overflow: hidden !important;
    border-radius: 10px !important;
    font-size: 13px !important;
}

th {
    font-weight: 800 !important;
    white-space: nowrap !important;
    padding: 10px 8px !important;
}

td {
    padding: 9px 8px !important;
    white-space: nowrap !important;
}

/* ---------- Dataframe ---------- */

[data-testid="dataframe"] {
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ---------- Accordion / groups ---------- */

.gr-group,
.gr-box {
    border-radius: 11px !important;
}

/* ---------- Clean spacing ---------- */

.gradio-container > div {
    gap: 10px !important;
}

/* ---------- Mobile ---------- */

@media (max-width: 800px) {

    .gradio-container {
        margin: 10px auto !important;
        padding: 0 9px 22px !important;
    }

    h1 {
        font-size: 23px !important;
        margin-bottom: 6px !important;
    }

    h2 {
        font-size: 18px !important;
        margin-top: 17px !important;
    }

    h3 {
        font-size: 16px !important;
    }

    .gr-row {
        gap: 7px !important;
    }

    input,
    textarea,
    select,
    button {
        min-height: 37px !important;
    }

    table {
        font-size: 12px !important;
    }

    th,
    td {
        padding: 8px 6px !important;
    }
}

/* ---------- Small phone ---------- */

@media (max-width: 520px) {

    .gradio-container {
        padding-left: 6px !important;
        padding-right: 6px !important;
    }

    h1 {
        font-size: 21px !important;
    }

    .gr-row {
        flex-wrap: wrap !important;
    }

    table {
        min-width: 760px !important;
    }
}
'''



# ============================================================
# 🎨 FADL PAY — FINANCIAL ADMIN V3 — CSS V2.1
# ============================================================
CUSTOM_CSS_V21 = r'''

/* ============================================================
   FADL PAY — FINANCIAL ADMIN V3 — CSS V2.1
   ============================================================ */

html,
body {
    background: #15171a !important;
}

.gradio-container {
    max-width: 1120px !important;
    margin: 28px auto !important;
    padding: 28px 30px 34px !important;

    background: #292c30 !important;

    border: 1px solid #3b3f44 !important;
    border-radius: 24px !important;

    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.32) !important;

    direction: rtl !important;
}

.gradio-container .gr-group,
.gradio-container .gr-box {
    background: transparent !important;
    border-color: transparent !important;
    box-shadow: none !important;
}

.gradio-container h1 {
    text-align: center !important;
    font-size: 28px !important;
    font-weight: 800 !important;
    margin: 2px 0 6px !important;
}

.gradio-container h2 {
    margin-top: 24px !important;
    margin-bottom: 12px !important;
    padding-bottom: 7px !important;

    border-bottom: 1px solid #42464b !important;

    font-size: 18px !important;
    font-weight: 800 !important;
}

.gradio-container h3 {
    margin-top: 18px !important;
    margin-bottom: 10px !important;
}

.gradio-container .prose {
    color: #e6e8eb !important;
}

.gradio-container .gr-row {
    gap: 10px !important;
    margin-bottom: 10px !important;
    align-items: end !important;
}

.gradio-container input,
.gradio-container textarea,
.gradio-container select {
    background: #202226 !important;
    border: 1px solid #41454b !important;
    border-radius: 10px !important;
    min-height: 40px !important;
}

.gradio-container label {
    font-weight: 700 !important;
}

.gradio-container button {
    min-height: 40px !important;
    border-radius: 10px !important;
    font-weight: 750 !important;
}

.gradio-container table {
    width: 100% !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}

.gradio-container [data-testid="dataframe"] {
    margin-top: 8px !important;
    border-radius: 12px !important;
    overflow-x: auto !important;
}

@media (max-width: 800px) {
    .gradio-container {
        margin: 10px !important;
        padding: 20px 16px 24px !important;
        border-radius: 18px !important;
    }

    .gradio-container h1 {
        font-size: 23px !important;
    }

    .gradio-container h2 {
        font-size: 17px !important;
        margin-top: 20px !important;
    }

    .gradio-container .gr-row {
        gap: 7px !important;
    }
}

@media (max-width: 520px) {
    .gradio-container {
        margin: 6px !important;
        padding: 17px 10px 20px !important;
        border-radius: 16px !important;
    }

    .gradio-container h1 {
        font-size: 21px !important;
    }
}

'''

# ============================================================
# 🎨 FADL PAY — FINANCIAL ADMIN V3 — CSS V2.2
# ============================================================
CUSTOM_CSS_V22 = r'''

/* ============================================================
   FADL PAY — FINANCIAL ADMIN V3 — CSS V2.2
   CONTRAST + DROPDOWN VISIBILITY
   ============================================================ */

/* الخلفية */
html,
body {
    background: #121417 !important;
    color: #f3f4f6 !important;
}

/* الكرت الرئيسي */
.gradio-container {
    background: #2b2f34 !important;
    color: #f3f4f6 !important;
}

/* كل النصوص */
.gradio-container,
.gradio-container label,
.gradio-container .prose,
.gradio-container p,
.gradio-container span {
    color: #f1f3f5 !important;
}

/* العناوين */
.gradio-container h1,
.gradio-container h2,
.gradio-container h3 {
    color: #ffffff !important;
}

/* الحقول */
.gradio-container input,
.gradio-container textarea {
    background: #1f2328 !important;
    color: #ffffff !important;

    border: 1px solid #555b63 !important;
}

.gradio-container input::placeholder,
.gradio-container textarea::placeholder {
    color: #aeb4bc !important;
    opacity: 1 !important;
}

/* Dropdown نفسه */
.gradio-container .gr-dropdown,
.gradio-container [data-testid="dropdown"] {
    background: #1f2328 !important;
    color: #ffffff !important;

    border-color: #555b63 !important;
}

/* النص داخل Dropdown */
.gradio-container .gr-dropdown input,
.gradio-container .gr-dropdown input[type="text"] {
    background: #1f2328 !important;
    color: #ffffff !important;
}

/* قائمة الخيارات المنسدلة */
.gradio-container .options,
.gradio-container .dropdown-menu,
.gradio-container [role="listbox"] {
    background: #f1f3f5 !important;
    color: #17191c !important;

    border: 1px solid #8b929b !important;
    border-radius: 10px !important;

    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35) !important;
}

/* كل خيار */
.gradio-container [role="option"],
.gradio-container .options li,
.gradio-container .dropdown-menu li {
    background: #f1f3f5 !important;
    color: #17191c !important;

    font-weight: 650 !important;
}

/* Hover على الخيار */
.gradio-container [role="option"]:hover,
.gradio-container .options li:hover,
.gradio-container .dropdown-menu li:hover {
    background: #d9dde2 !important;
    color: #111317 !important;
}

/* الخيار المحدد */
.gradio-container [role="option"][aria-selected="true"] {
    background: #cbd1d8 !important;
    color: #111317 !important;
}

/* Dataframe */
.gradio-container table {
    color: #f3f4f6 !important;
}

.gradio-container th {
    background: #383d43 !important;
    color: #ffffff !important;
}

.gradio-container td {
    background: #24282d !important;
    color: #e8eaed !important;
    border-color: #444a51 !important;
}

/* الأزرار */
.gradio-container button {
    color: #ffffff !important;
    border-color: #59616b !important;
}

/* لا نخلي العناصر باهتة */
.gradio-container .secondary,
.gradio-container .primary {
    opacity: 1 !important;
}

/* Mobile */
@media (max-width: 800px) {
    .gradio-container {
        color: #f3f4f6 !important;
    }

    .gradio-container input,
    .gradio-container textarea,
    .gradio-container .gr-dropdown {
        color: #ffffff !important;
    }
}

'''

# ============================================================
# 🎨 FADL PAY — FINANCIAL ADMIN V3 — CSS V2.3
# ============================================================
CUSTOM_CSS_V23 = r'''

/* ============================================================
   FADL PAY — FINANCIAL ADMIN V3 — CSS V2.3
   PROFESSIONAL FINTECH POLISH
   ============================================================ */

/* ---------- Main visual hierarchy ---------- */

.gradio-container {
    padding-top: 30px !important;
    padding-bottom: 36px !important;
}

/* ---------- Main title ---------- */

.gradio-container h1 {
    font-size: 30px !important;
    line-height: 1.2 !important;
    letter-spacing: -0.4px !important;
    margin-bottom: 10px !important;
}

/* ---------- Section headings ---------- */

.gradio-container h2 {
    font-size: 19px !important;
    line-height: 1.25 !important;
    margin-top: 28px !important;
    margin-bottom: 14px !important;
    padding-bottom: 9px !important;
}

.gradio-container h3 {
    font-size: 16px !important;
    font-weight: 800 !important;
    margin-top: 20px !important;
    margin-bottom: 10px !important;
}

/* ---------- General text ---------- */

.gradio-container p {
    font-size: 14px !important;
    line-height: 1.6 !important;
}

/* ---------- Labels ---------- */

.gradio-container label {
    font-size: 13px !important;
    font-weight: 800 !important;
}

/* ---------- Inputs ---------- */

.gradio-container input,
.gradio-container textarea,
.gradio-container .gr-dropdown {
    min-height: 42px !important;
    font-size: 14px !important;
    border-radius: 10px !important;
}

/* ---------- Search controls ---------- */

.gradio-container .gr-row {
    gap: 11px !important;
    margin-bottom: 11px !important;
}

/* ---------- Buttons ---------- */

.gradio-container button {
    min-height: 42px !important;
    padding-left: 16px !important;
    padding-right: 16px !important;
    font-size: 14px !important;
    border-radius: 10px !important;
}

/* ---------- Data tables ---------- */

.gradio-container table {
    font-size: 13px !important;
}

.gradio-container th {
    font-size: 13px !important;
    font-weight: 850 !important;
    padding: 11px 9px !important;
}

.gradio-container td {
    font-size: 13px !important;
    padding: 10px 9px !important;
}

/* ---------- Dataframe wrapper ---------- */

.gradio-container [data-testid="dataframe"] {
    margin-top: 10px !important;
    border-radius: 13px !important;
}

/* ---------- Better visual spacing ---------- */

.gradio-container .gr-column {
    gap: 8px !important;
}

/* ---------- Keep the dashboard calm ---------- */

.gradio-container hr {
    opacity: 0.22 !important;
}

/* ---------- Mobile ---------- */

@media (max-width: 800px) {

    .gradio-container {
        padding: 20px 14px 26px !important;
    }

    .gradio-container h1 {
        font-size: 24px !important;
    }

    .gradio-container h2 {
        font-size: 18px !important;
        margin-top: 22px !important;
    }

    .gradio-container input,
    .gradio-container textarea,
    .gradio-container .gr-dropdown,
    .gradio-container button {
        min-height: 40px !important;
    }

    .gradio-container th,
    .gradio-container td {
        padding: 9px 7px !important;
    }
}

/* ---------- Small screens ---------- */

@media (max-width: 520px) {

    .gradio-container {
        margin: 5px !important;
        padding: 16px 9px 21px !important;
    }

    .gradio-container h1 {
        font-size: 21px !important;
    }

    .gradio-container h2 {
        font-size: 17px !important;
    }
}

'''

with gr.Blocks(css=CUSTOM_CSS + CUSTOM_CSS_V21 + CUSTOM_CSS_V22 + CUSTOM_CSS_V23, title="FADL PAY — الإدارة المالية") as financial_admin_demo:

    gr.Markdown("# 💰 FADL PAY — الإدارة المالية")

    refresh = gr.Button("🔄 تحديث البيانات", variant="primary")

    summary = gr.Markdown()

    gr.Markdown("### 💱 الملخص حسب العملة")

    currency_table = gr.Dataframe(
        headers=[
            "العملة",
            "المعاملات",
            "الإجمالي",
            "المحصّل",
            "المرتجع",
        ],
        datatype=[
            "str",
            "number",
            "number",
            "number",
            "number",
        ],
        interactive=False,
    )

    gr.Markdown("### 🏪 الملخص حسب التاجر")

    merchant_table = gr.Dataframe(
        headers=[
            "مرجع التاجر",
            "المعاملات",
            "الإجمالي",
            "المحصّل",
            "المرتجع",
        ],
        datatype=[
            "str",
            "number",
            "number",
            "number",
            "number",
        ],
        interactive=False,
    )

    gr.Markdown("### 📋 سجل المعاملات")

    with gr.Row():
        transaction_search = gr.Textbox(
            label="🔎 البحث",
            placeholder="مرجع المعاملة أو التاجر أو العميل",
            scale=4,
        )

        status_filter = gr.Dropdown(
            choices=[
                "الكل",
                "pending",
                "paid",
                "failed",
                "cancelled",
                "refunded",
            ],
            value="الكل",
            label="📌 الحالة",
            scale=2,
        )

        payment_method_filter = gr.Dropdown(
            choices=[
                "الكل",
                "bank",
                "mobile_wallet",
                "card",
            ],
            value="الكل",
            label="💳 طريقة الدفع",
            scale=2,
        )

        currency_filter = gr.Dropdown(
            choices=[
                "الكل",
                "SDG",
                "USD",
                "EUR",
            ],
            value="الكل",
            label="💱 العملة",
            scale=2,
        )

    with gr.Row():
        search_button = gr.Button(
            "بحث",
            variant="primary",
            scale=1,
        )

        clear_button = gr.Button(
            "مسح",
            scale=1,
        )

    transaction_table = gr.Dataframe(
        headers=[
            "مرجع المعاملة",
            "مرجع التاجر",
            "مرجع العميل",
            "المبلغ",
            "العملة",
            "طريقة الدفع",
            "الحالة",
            "تاريخ الإنشاء",
        ],
        datatype=[
            "str",
            "str",
            "str",
            "number",
            "str",
            "str",
            "str",
            "str",
        ],
        interactive=False,
    )

    refresh.click(
        fn=load_financial_dashboard,
        outputs=[
            summary,
            currency_table,
            merchant_table,
            transaction_table,
        ],
    )

    search_button.click(
        fn=search_transaction_rows,
        inputs=[
            transaction_search,
            status_filter,
            payment_method_filter,
            currency_filter,
        ],
        outputs=transaction_table,
    )

    transaction_search.submit(
        fn=search_transaction_rows,
        inputs=[
            transaction_search,
            status_filter,
            payment_method_filter,
            currency_filter,
        ],
        outputs=transaction_table,
    )

    clear_button.click(
        fn=clear_transaction_search,
        outputs=[
            transaction_search,
            status_filter,
            payment_method_filter,
            currency_filter,
            transaction_table,
        ],
    )

    financial_admin_demo.load(
        fn=load_financial_dashboard,
        outputs=[
            summary,
            currency_table,
            merchant_table,
            transaction_table,
        ],
    )
