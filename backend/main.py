from starlette.responses import RedirectResponse
"""
Fadl Pay
Main Application
Payment UI + API
Sandbox / Prototype
"""

import gradio as gr
from fastapi import FastAPI, Cookie, HTTPException

from database.database import initialize_database
from backend.api import app as api_app
from backend.merchant_api_login import router as merchant_api_login_router
from app.payment_ui import demo
from app.financial_admin_ui import financial_admin_demo
from app.merchant_dashboard import dashboard_data_from_session
from app.customer_checkout import router as customer_checkout_router


initialize_database()


app = FastAPI(
    title="Fadl Pay",
    description="Payment Gateway + Payment UI - Sandbox",
    version="0.2.0",
)


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": "sandbox",
    }


# ============================================================
# API ROUTES
# نحافظ على المسارات الأصلية:
# /api/v1/transactions
# /api/v1/transactions/{transaction_reference}
# /api/v1/sandbox/transactions/{transaction_reference}/status
# ============================================================

for route in api_app.routes:
    route_path = getattr(route, "path", "")

    if route_path.startswith("/api/v1/"):
        app.router.routes.append(route)


# ============================================================
# MERCHANT API KEY LOGIN
# API Key → Merchant Session
# ============================================================

app.include_router(
    merchant_api_login_router,
)


# ============================================================
# CUSTOMER CHECKOUT
# /pay + /pay/create
# ============================================================

app.include_router(customer_checkout_router)




# ============================================================
# MERCHANT DASHBOARD ROUTE
# API Key → Merchant Session → Dashboard
# ============================================================

@app.get("/merchant/dashboard")
def merchant_dashboard(
    fadl_merchant_session: str | None = Cookie(default=None),
):
    if not fadl_merchant_session:
        raise HTTPException(
            status_code=401,
            detail="Merchant authentication required",
        )

    try:
        return dashboard_data_from_session(
            fadl_merchant_session
        )

    except PermissionError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )

# ============================================================
# Redirect /admin → /admin/
@app.get("/admin", include_in_schema=False)
async def admin_redirect():
    return RedirectResponse(url="/admin/")


# ============================================================
# FINANCIAL ADMIN
# الإدارة المالية
# يجب أن يسبق root حتى لا تلتقط واجهة الدفع مسار /admin
# ============================================================

app = gr.mount_gradio_app(
    app,
    financial_admin_demo,
    path="/admin",
)

# ============================================================
# PAYMENT UI
# الصفحة الرئيسية /
# ============================================================

app = gr.mount_gradio_app(
    app,
    demo,
    path="/",
)

