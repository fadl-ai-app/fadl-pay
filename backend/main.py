from starlette.responses import RedirectResponse
"""
Fadl Pay
Main Application
Payment UI + API
Sandbox / Prototype
"""

import gradio as gr
from fastapi import FastAPI, Cookie, HTTPException, Depends

from database.database import initialize_database
from backend.api import app as api_app
from backend.merchant_api_login import router as merchant_api_login_router
from backend.merchant_auth_routes import (
    get_session,
    router as merchant_auth_router,
)
from app.financial_admin_ui import financial_admin_demo
from app.merchant_dashboard import dashboard_data_from_session
from app.merchant_login import (
    demo as merchant_login_demo,
    LOGIN_UI_CSS,
    LOGIN_UI_JS,
)
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

app.include_router(
    merchant_auth_router,
)


# ============================================================
# CUSTOMER CHECKOUT
# /pay + /pay/create
# ============================================================





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
        data = dashboard_data_from_session(
            fadl_merchant_session
        )

        merchant_name = str(data.get("name") or "التاجر")
        merchant_email = str(data.get("email") or "")
        merchant_reference = str(
            data.get("merchant_reference") or ""
        )

        html = f"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>FADL PAY — بوابة التاجر</title>

<style>
* {{
    box-sizing: border-box;
}}

body {{
    margin: 0;
    min-height: 100vh;
    font-family: Arial, Tahoma, sans-serif;
    background:
        radial-gradient(circle at top right, #dcfce7 0, transparent 35%),
        linear-gradient(135deg, #f0fdf4, #ffffff 55%, #ecfdf5);
    color: #14532d;
}}

.gateway {{
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 28px 16px;
}}

.card {{
    width: min(720px, 100%);
    background: rgba(255,255,255,.96);
    border: 1px solid #bbf7d0;
    border-radius: 30px;
    padding: 38px 30px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(20,83,45,.14);
}}

.logo {{
    width: 76px;
    height: 76px;
    margin: 0 auto 16px;
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg,#166534,#15803d);
    color: white;
    font-size: 36px;
    box-shadow: 0 10px 25px rgba(21,128,61,.25);
}}

h1 {{
    margin: 0;
    font-size: 34px;
    font-weight: 800;
    color: #14532d;
}}

.subtitle {{
    margin: 10px 0 24px;
    color: #4b6354;
    font-size: 17px;
}}

.merchant {{
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 18px;
    padding: 14px 18px;
    margin-bottom: 24px;
    line-height: 1.9;
}}

.actions {{
    display: grid;
    grid-template-columns: repeat(2,minmax(0,1fr));
    gap: 16px;
}}

.action {{
    min-height: 150px;
    border-radius: 22px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    gap: 10px;
    text-decoration: none;
    font-size: 20px;
    font-weight: 800;
    transition: .18s ease;
}}

.action:hover {{
    transform: translateY(-3px);
    box-shadow: 0 12px 28px rgba(20,83,45,.16);
}}

.pay {{
    background: linear-gradient(135deg,#166534,#15803d);
    color: white;
}}

.admin {{
    background: white;
    color: #166534;
    border: 2px solid #86efac;
}}

.icon {{
    font-size: 36px;
}}

.footer {{
    margin-top: 24px;
    color: #6b806f;
    font-size: 13px;
}}

@media (max-width: 620px) {{
    .actions {{
        grid-template-columns: 1fr;
    }}

    .card {{
        padding: 30px 18px;
    }}

    h1 {{
        font-size: 29px;
    }}
}}
</style>
</head>

<body>
<div class="gateway">
<div class="card">

    <div class="logo">💳</div>

    <h1>FADL PAY</h1>

    <div class="subtitle">
        بوابة التاجر
    </div>

    <div class="merchant">
        <strong>{merchant_name}</strong><br>
        {merchant_email}<br>
        <span>رقم التاجر: {merchant_reference}</span>
    </div>

    <div class="actions">

        <a class="action pay"
           href="/pay?v=7fe68562">
            <span class="icon">💳</span>
            <span>واجهة الدفع</span>
        </a>

        <a class="action admin"
           href="/admin/">
            <span class="icon">📊</span>
            <span>الإدارة المالية</span>
        </a>

    </div>

    <div class="footer">
        اختر الخدمة التي تريد الوصول إليها
    </div>

</div>
</div>
</body>
</html>
"""

        from starlette.responses import HTMLResponse
        return HTMLResponse(content=html)

    except PermissionError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        )

# ============================================================
# MERCHANT LOGIN UI
# /merchant
#
# The existing FastAPI merchant auth endpoints remain under:
# /merchant/login
# /merchant/me
# /merchant/logout
#
# Gradio provides only the browser login interface.
# ============================================================

gr.mount_gradio_app(
    app,
    merchant_login_demo,
    path="/merchant",
    css=LOGIN_UI_CSS,
    js=LOGIN_UI_JS,
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

gr.mount_gradio_app(
    app,
    financial_admin_demo,
    path="/admin",
)

# ============================================================

# ============================================================
# CUSTOMER CHECKOUT
# /pay + /pay/create
#
# Register checkout BEFORE the root payment UI mount so the
# root Gradio UI cannot intercept /pay.
# ============================================================

# =============================================================================
# 🔐 CUSTOMER CHECKOUT AUTH BOUNDARY
# =============================================================================
# All /pay routes require a valid merchant server-side session.
# This dependency is applied at router level so it covers:
#   GET  /pay
#   POST /pay/create
#   POST /pay/sandbox/status
#
# No UI changes.
# No database changes.
# =============================================================================

def require_merchant_session(
    fadl_merchant_session: str | None = Cookie(default=None),
):
    if not fadl_merchant_session:
        raise HTTPException(
            status_code=401,
            detail="Merchant authentication required",
        )

    session = get_session(fadl_merchant_session)

    if session is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired merchant session",
        )

    return session


app.include_router(
    customer_checkout_router,
)


# ================================================================
# 🌿 FADL PAY — MINI ISLAMIC HOME GATEWAY
# ================================================================

from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def fadl_pay_home():
    return HTMLResponse(
        content="""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مرحبًا بك في FADL PAY</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background:
                radial-gradient(circle at top, #f2fff7 0%, #e8f7ee 45%, #dcefe4 100%);
            font-family:
                "Segoe UI",
                Tahoma,
                Arial,
                sans-serif;
            color: #173b2a;
            padding: 24px;
        }

        .card {
            width: min(520px, 100%);
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid rgba(37, 110, 72, 0.14);
            border-radius: 28px;
            padding: 42px 30px;
            text-align: center;
            box-shadow:
                0 20px 60px rgba(27, 83, 53, 0.14);
        }

        .mark {
            width: 76px;
            height: 76px;
            margin: 0 auto 20px;
            border-radius: 22px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #176b45;
            color: white;
            font-size: 34px;
            box-shadow: 0 10px 24px rgba(23, 107, 69, 0.22);
        }

        h1 {
            margin: 0 0 12px;
            font-size: 30px;
            font-weight: 800;
        }

        .subtitle {
            margin: 0 auto 30px;
            color: #52705f;
            font-size: 17px;
            line-height: 1.8;
        }

        .protection {
            margin: 0 0 24px;
            padding: 14px 16px;
            border-radius: 16px;
            background: #f1faf5;
            color: #28583f;
            font-size: 14px;
            line-height: 1.7;
        }

        .button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            min-height: 54px;
            border-radius: 16px;
            background: #176b45;
            color: white;
            text-decoration: none;
            font-size: 17px;
            font-weight: 700;
            transition: transform .15s ease, box-shadow .15s ease;
            box-shadow: 0 10px 22px rgba(23, 107, 69, 0.20);
        }

        .button:hover {
            transform: translateY(-1px);
            box-shadow: 0 14px 28px rgba(23, 107, 69, 0.25);
        }

        .footer {
            margin-top: 24px;
            color: #789080;
            font-size: 12px;
        }
    </style>
</head>

<body>
    <main class="card">
        <div class="mark">🌿</div>

        <h1>مرحبًا بك في FADL PAY</h1>

        <p class="subtitle">
            منصة دفع آمنة وسهلة لإدارة عمليات الدفع والخدمات المالية.
        </p>

        <div class="protection">
            🔐 للوصول إلى خدمات FADL PAY،
            يرجى المرور عبر بوابة الحماية أولًا.
        </div>

        <a class="button" href="/merchant/">
            🔐 الدخول والمتابعة
        </a>

        <div class="footer">
            FADL PAY — دفع بسهولة وأمان
        </div>
    </main>
</body>
</html>
        """,
        status_code=200,
    )
