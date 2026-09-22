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

app.include_router(customer_checkout_router)

# ================================================================
# 🌿 FADL PAY — MINI ISLAMIC HOME GATEWAY
# ================================================================

from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def fadl_pay_home():
    return """
<!DOCTYPE html>
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

        html,
        body {
            margin: 0;
            min-height: 100%;
        }

        body {
            min-height: 100vh;

            display: flex;
            align-items: center;
            justify-content: center;

            padding: 18px;

            font-family:
                "Segoe UI",
                Tahoma,
                Arial,
                sans-serif;

            color: #ffffff;

            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(212,175,55,.12),
                    transparent 42%
                ),
                #073b2a;
        }

        /* زخرفة هندسية إسلامية خفيفة */

        body::before {
            content: "";

            position: fixed;
            inset: 0;

            pointer-events: none;

            opacity: .045;

            background-image:
                linear-gradient(
                    30deg,
                    #d4af37 12%,
                    transparent 12.5%,
                    transparent 87%,
                    #d4af37 87.5%
                ),
                linear-gradient(
                    150deg,
                    #d4af37 12%,
                    transparent 12.5%,
                    transparent 87%,
                    #d4af37 87.5%
                );

            background-size: 52px 90px;
        }

        .gateway {
            position: relative;
            z-index: 1;

            width: min(650px, 100%);

            padding: 27px 24px 21px;

            border-radius: 23px;

            border: 1px solid
                rgba(212,175,55,.38);

            background:
                linear-gradient(
                    145deg,
                    rgba(15,82,58,.98),
                    rgba(5,48,34,.98)
                );

            box-shadow:
                0 22px 60px rgba(0,0,0,.28),
                inset 0 1px 0
                    rgba(255,255,255,.08);
        }

        .brand {
            text-align: center;
            margin-bottom: 22px;
        }

        .icon {
            font-size: 28px;
            margin-bottom: 3px;
        }

        .name {
            font-size: 24px;
            font-weight: 800;
            letter-spacing: .4px;
        }

        .subtitle {
            margin-top: 5px;
            font-size: 12px;
            opacity: .72;
        }

        .choices {
            display: grid;

            grid-template-columns:
                repeat(2, minmax(0, 1fr));

            gap: 13px;
        }

        .choice {
            min-height: 108px;

            display: flex;
            flex-direction: column;

            align-items: center;
            justify-content: center;

            text-decoration: none;
            color: #ffffff;

            border-radius: 17px;

            background:
                rgba(255,255,255,.07);

            border:
                1px solid
                rgba(255,255,255,.10);

            transition:
                transform .18s ease,
                background .18s ease,
                border-color .18s ease;
        }

        .choice:hover {
            transform: translateY(-3px);

            background:
                rgba(255,255,255,.115);

            border-color:
                rgba(212,175,55,.65);
        }

        .choice-icon {
            font-size: 29px;
            margin-bottom: 8px;
        }

        .choice-title {
            font-size: 16px;
            font-weight: 700;
        }

        .choice-hint {
            margin-top: 4px;

            font-size: 10px;

            opacity: .58;
        }

        .footer {
            margin-top: 17px;

            text-align: center;

            font-size: 9px;

            opacity: .38;
        }

        @media (max-width: 560px) {

            body {
                padding: 11px;
            }

            .gateway {
                padding: 22px 14px 18px;
                border-radius: 20px;
            }

            .brand {
                margin-bottom: 17px;
            }

            .name {
                font-size: 21px;
            }

            .choices {
                grid-template-columns: 1fr;
                gap: 9px;
            }

            .choice {
                min-height: 82px;
            }

            .choice-icon {
                font-size: 25px;
                margin-bottom: 5px;
            }

        }

    </style>
</head>

<body>

    <main class="gateway">

        <div class="brand">

            <div class="icon">💳</div>

            <div class="name">
                FADL PAY
            </div>

            <div class="subtitle">
                اختر الواجهة للدخول
            </div>

        </div>


        <div class="choices">

            <a
                class="choice"
                href="/pay"
            >
                <div class="choice-icon">
                    💳
                </div>

                <div class="choice-title">
                    واجهة الدفع
                </div>

                <div class="choice-hint">
                    الدفع بسهولة وأمان
                </div>
            </a>


            <a
                class="choice"
                href="/admin/"
            >
                <div class="choice-icon">
                    💰
                </div>

                <div class="choice-title">
                    الإدارة المالية
                </div>

                <div class="choice-hint">
                    إدارة ومتابعة المعاملات
                </div>
            </a>

        </div>


        <div class="footer">
            FADL PAY · Sandbox
        </div>

    </main>

</body>

</html>
"""
