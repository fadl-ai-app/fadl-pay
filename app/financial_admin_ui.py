
# ============================================================
# 💰 FADL PAY — Financial Administration UI
# ============================================================

import gradio as gr

from app.financial_admin import get_financial_summary


def load_financial_dashboard():
    data = get_financial_summary()
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

    return summary, currency_rows, merchant_rows


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

    refresh.click(
        fn=load_financial_dashboard,
        outputs=[
            summary,
            currency_table,
            merchant_table,
        ],
    )

    financial_admin_demo.load(
        fn=load_financial_dashboard,
        outputs=[
            summary,
            currency_table,
            merchant_table,
        ],
    )
