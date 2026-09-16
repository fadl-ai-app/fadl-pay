
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


def search_transaction_rows(query):
    results = search_transactions(query)
    return transaction_rows(results)


def clear_transaction_search():
    return transaction_rows(get_transaction_list())



with gr.Blocks(title="FADL PAY — الإدارة المالية") as financial_admin_demo:

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
        inputs=transaction_search,
        outputs=transaction_table,
    )

    transaction_search.submit(
        fn=search_transaction_rows,
        inputs=transaction_search,
        outputs=transaction_table,
    )

    clear_button.click(
        fn=clear_transaction_search,
        outputs=transaction_table,
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
