"""
Fadl Pay
Main Application
Payment UI + API
Sandbox / Prototype
"""

import gradio as gr
from fastapi import FastAPI
from backend.merchant_auth_routes import router as merchant_auth_router

from database.database import initialize_database
from backend.api import app as api_app
from app.payment_ui import demo
from app.financial_admin_ui import financial_admin_demo


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
# FINANCIAL ADMIN
# يجب تركيبه قبل الصفحة الرئيسية /
# ============================================================

app = gr.mount_gradio_app(
    app,
    financial_admin_demo,
    path="/admin/",
)


# ============================================================
# PAYMENT UI
# الصفحة الرئيسية /
# ============================================================

# ============================================================
# MERCHANT AUTHENTICATION
# Must be mounted before Gradio replaces the app reference.
# ============================================================
app.include_router(merchant_auth_router)

app = gr.mount_gradio_app(
    app,
    demo,
    path="/",
)

# ============================================================
# FINAL ADMIN ROUTE ORDER
# الإدارة يجب أن تسبق Root Gradio
# ============================================================

_admin_mount = None
_root_mount = None

for _route in app.router.routes:

    _route_path = getattr(_route, "path", None)

    if _route_path == "/admin":
        _admin_mount = _route

    elif _route_path == "":
        _root_mount = _route

if _admin_mount is None:
    raise RuntimeError("❌ Admin Gradio mount not found")

if _root_mount is None:
    raise RuntimeError("❌ Root Gradio mount not found")

_admin_index = app.router.routes.index(_admin_mount)
_root_index = app.router.routes.index(_root_mount)

if _admin_index > _root_index:

    app.router.routes.remove(_admin_mount)
    app.router.routes.remove(_root_mount)

    app.router.routes.append(_admin_mount)
    app.router.routes.append(_root_mount)

