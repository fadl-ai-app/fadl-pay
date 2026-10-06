from backend.merchant_webhook_routes import router as merchant_webhook_router
from starlette.responses import RedirectResponse
from integration_v2.router import router as integration_v2_router
"""
Fadl Pay
Main Application
Payment UI + API
Sandbox / Prototype
"""

import gradio as gr
from fastapi import FastAPI, Cookie, HTTPException, Request

from database.database import initialize_database
from backend.api import app as api_app
from backend.merchant_api_login import router as merchant_api_login_router
from backend.merchant_auth_routes import router as merchant_auth_router
from app.financial_admin_ui import financial_admin_demo
from app.merchant_dashboard import create_dashboard
from security.merchant_session import get_session_merchant, create_session
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

app.include_router(integration_v2_router)


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

def merchant_dashboard_auth_dependency(
    request: Request,
):
    """
    Protect the merchant Dashboard Gradio mount.

    The existing HttpOnly session cookie remains the sole
    authentication source. No new session or authentication
    mechanism is introduced here.
    """
    session_token = request.cookies.get(
        "fadl_merchant_session"
    )

    if not session_token:
        return None

    try:
        merchant_reference = get_session_merchant(session_token)

        if not merchant_reference:
            return None

        return session_token

    except PermissionError:
        return None



# =====================================================================
# MERCHANT DASHBOARD CANONICAL REDIRECT
# /merchant/dashboard -> /merchant/dashboard/
# =====================================================================

@app.get("/merchant/dashboard", include_in_schema=False)
async def merchant_dashboard_redirect():
    return RedirectResponse(url="/merchant/dashboard/")

merchant_dashboard_demo = create_dashboard()

app.include_router(merchant_webhook_router)


# FADL_PAY_FINANCIAL_ADMIN_AUTH_V1
def financial_admin_auth_dependency(
    request: Request,
    fadl_merchant_session: str | None = Cookie(default=None),
):
    """
    Server-side protection boundary for Financial Admin.

    A valid merchant session is required and the authenticated
    merchant role must have financial_admin.read permission.

    This dependency does NOT modify the database.
    """

    if not fadl_merchant_session:
        raise HTTPException(status_code=401, detail="Not authenticated")

    merchant_reference = get_session_merchant(fadl_merchant_session)

    if not merchant_reference:
        raise HTTPException(status_code=401, detail="Invalid or expired session")

    # Resolve role from the existing session/RBAC layer.
    from security.merchant_session import get_session_role
    from security.merchant_rbac import require_permission

    role = get_session_role(fadl_merchant_session)

    try:
        require_permission(role, "financial_admin.read")
    except Exception:
        raise HTTPException(status_code=403, detail="Financial Admin permission required")

    request.state.merchant_reference = merchant_reference
    request.state.merchant_role = role

    return merchant_reference


gr.mount_gradio_app(
    app,
    merchant_dashboard_demo,
    path="/merchant/dashboard",
    auth_dependency=merchant_dashboard_auth_dependency,
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
    auth_dependency=financial_admin_auth_dependency,
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">

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

            padding: 24px;

            font-family:
                "Segoe UI",
                Tahoma,
                Arial,
                sans-serif;

            color: #163c2e;

            background:
                radial-gradient(
                    circle at 50% 0%,
                    rgba(212,175,55,.14),
                    transparent 38%
                ),
                linear-gradient(
                    180deg,
                    #f9fbf8 0%,
                    #eef5f1 100%
                );
        }

        body::before {
            content: "";

            position: fixed;
            inset: 0;

            pointer-events: none;

            opacity: .035;

            background-image:
                linear-gradient(
                    30deg,
                    #b38a24 12%,
                    transparent 12.5%,
                    transparent 87%,
                    #b38a24 87.5%
                ),
                linear-gradient(
                    150deg,
                    #b38a24 12%,
                    transparent 12.5%,
                    transparent 87%,
                    #b38a24 87.5%
                );

            background-size: 52px 90px;
        }

        .page {
            position: relative;
            z-index: 1;

            width: min(470px, 100%);
        }

        .card {
            overflow: hidden;

            border-radius: 26px;

            background: #ffffff;

            border: 1px solid rgba(7,59,42,.10);

            box-shadow:
                0 25px 70px rgba(7,59,42,.12),
                0 4px 16px rgba(0,0,0,.04);
        }

        .top {
            padding: 30px 30px 24px;

            text-align: center;

            color: #ffffff;

            background:
                linear-gradient(
                    145deg,
                    #0b5a40,
                    #073b2a
                );
        }

        .logo {
            width: 62px;
            height: 62px;

            margin: 0 auto 13px;

            display: flex;
            align-items: center;
            justify-content: center;

            border-radius: 18px;

            font-size: 30px;

            background: rgba(255,255,255,.11);

            border: 1px solid
                rgba(212,175,55,.42);

            box-shadow:
                inset 0 1px 0 rgba(255,255,255,.10);
        }

        .name {
            font-size: 27px;
            font-weight: 800;
            letter-spacing: .5px;
        }

        .welcome {
            margin-top: 7px;

            font-size: 15px;
            font-weight: 500;

            opacity: .92;
        }

        .hint {
            margin-top: 7px;

            font-size: 11px;

            opacity: .66;
        }

        .form {
            padding: 30px;
        }

        .field {
            margin-bottom: 17px;
        }

        .label {
            display: block;

            margin-bottom: 8px;

            font-size: 13px;
            font-weight: 700;

            color: #214d3d;
        }

        .input {
            width: 100%;

            height: 52px;

            padding: 0 15px;

            border-radius: 13px;

            border: 1px solid #d7e3dd;

            background: #fbfdfc;

            color: #163c2e;

            font-size: 14px;

            outline: none;

            transition:
                border-color .18s ease,
                box-shadow .18s ease,
                background .18s ease;
        }

        .input:focus {
            background: #ffffff;

            border-color: #0b6a49;

            box-shadow:
                0 0 0 4px rgba(11,106,73,.09);
        }

        .input::placeholder {
            color: #97aaa2;
        }

        .submit {
            width: 100%;

            height: 53px;

            margin-top: 4px;

            border: 0;
            border-radius: 14px;

            background:
                linear-gradient(
                    135deg,
                    #0d704d,
                    #084b36
                );

            color: #ffffff;

            font-size: 15px;
            font-weight: 800;

            cursor: pointer;

            box-shadow:
                0 10px 25px rgba(7,59,42,.16);

            transition:
                transform .16s ease,
                box-shadow .16s ease;
        }

        .submit:hover {
            transform: translateY(-1px);

            box-shadow:
                0 13px 30px rgba(7,59,42,.21);
        }

        .signup {
            margin-top: 20px;

            text-align: center;

            font-size: 12px;

            color: #71847c;
        }

        .signup a {
            color: #0b6042;

            font-weight: 800;

            text-decoration: none;
        }

        .signup a:hover {
            text-decoration: underline;
        }

        .security {
            margin-top: 20px;
            padding-top: 18px;

            border-top: 1px solid #edf1ef;

            text-align: center;

            font-size: 10px;

            color: #81918b;
        }

        .footer {
            margin-top: 16px;

            text-align: center;

            font-size: 9px;

            color: #8a9993;
        }

        @media (max-width: 560px) {
            body {
                padding: 14px;
            }

            .top {
                padding:
                    25px 20px 21px;
            }

            .form {
                padding: 23px 20px 22px;
            }

            .name {
                font-size: 23px;
            }

            .welcome {
                font-size: 14px;
            }

            .input {
                height: 50px;
            }
        }
    </style>
</head>

<body>

    <main class="page">

        <section class="card">

            <div class="top">

                <div class="logo">
                    💳
                </div>

                <div class="name">
                    FADL PAY
                </div>

                <div class="welcome">
                    مرحباً بك
                </div>

                <div class="hint">
                    ادخل إلى حسابك للوصول إلى صفحتك
                </div>

            </div>


            <div class="form">

                <div class="field">

                    <label class="label" for="email">
                        البريد الإلكتروني
                    </label>

                    <input
                        id="email"
                        class="input"
                        type="email"
                        autocomplete="email"
                        placeholder="أدخل بريدك الإلكتروني"
                    >

                </div>


                <div class="field">

                    <label class="label" for="password">
                        كلمة المرور
                    </label>

                    <input
                        id="password"
                        class="input"
                        type="password"
                        autocomplete="current-password"
                        placeholder="أدخل كلمة المرور"
                    >

                </div>


                <button
                    class="submit"
                    type="button"
                    id="enter-page"
                >
                    ادخل للصفحة
                </button>

                <div
                    id="login-status"
                    aria-live="polite"
                    style="
                        margin-top: 12px;
                        min-height: 20px;
                        text-align: center;
                        font-size: 11px;
                    "
                ></div>


                <div class="signup">
                    ليس لديك حساب؟
                    <a href="#" id="create-account">
                        إنشاء حساب
                    </a>
                </div>


                <div class="security">
                    🔐 دخول آمن · الوصول حسب الصلاحية
                </div>

            </div>

        </section>


        <div class="footer">
            FADL PAY · Sandbox
        </div>

    </main>

<script>
document.addEventListener("DOMContentLoaded", function () {

    const button = document.getElementById("enter-page");
    const emailEl = document.getElementById("email");
    const passwordEl = document.getElementById("password");
    const statusEl = document.getElementById("login-status");

    if (!button || !emailEl || !passwordEl) {
        return;
    }

    async function loginFromHome() {

        const email = emailEl.value.trim();
        const password = passwordEl.value;

        if (!email || !password) {
            if (statusEl) {
                statusEl.innerText =
                    "يرجى إدخال البريد الإلكتروني وكلمة المرور.";
                statusEl.style.color = "#a61b1b";
            }
            return;
        }

        button.disabled = true;
        button.style.opacity = "0.75";
        button.innerText = "جاري التحقق...";

        if (statusEl) {
            statusEl.innerText = "";
        }

        try {

            const response = await fetch(
                "/merchant/login",
                {
                    method: "POST",
                    credentials: "include",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                }
            );

            let data = {};

            try {
                data = await response.json();
            } catch (_) {
                data = {};
            }

            if (!response.ok) {

                const detail =
                    typeof data.detail === "string"
                        ? data.detail
                        : "البريد الإلكتروني أو كلمة المرور غير صحيحة.";

                if (statusEl) {
                    statusEl.innerText = detail;
                    statusEl.style.color = "#a61b1b";
                }

                button.disabled = false;
                button.style.opacity = "1";
                button.innerText = "ادخل للصفحة";

                return;
            }

            if (statusEl) {
                statusEl.innerText = "تم تسجيل الدخول بنجاح...";
                statusEl.style.color = "#176b3a";
            }

            window.location.assign(
                "/merchant/dashboard/"
            );

        } catch (error) {

            if (statusEl) {
                statusEl.innerText =
                    "تعذر الاتصال بالخادم. حاول مرة أخرى.";
                statusEl.style.color = "#a61b1b";
            }

            button.disabled = false;
            button.style.opacity = "1";
            button.innerText = "ادخل للصفحة";
        }
    }

    button.addEventListener(
        "click",
        loginFromHome
    );

    passwordEl.addEventListener(
        "keydown",
        function (event) {
            if (event.key === "Enter") {
                loginFromHome();
            }
        }
    );

});
</script>


</body>

</html>
"""

