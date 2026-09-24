"""
FADL PAY — Merchant Login UI

UI-only layer for merchant authentication.

Security boundary:
- Uses the existing POST /merchant/login endpoint.
- Uses the existing GET /merchant/me contract.
- Uses the existing Secure + HttpOnly session cookie.
- Does not implement authentication logic.
- Does not store passwords.
- Does not store session tokens in browser storage.
- Does not access the database.
- Does not modify merchant authentication routes.
- Does not modify the merchant dashboard.
"""

from __future__ import annotations

import gradio as gr


LOGIN_UI_CSS = r"""
body {
    direction: rtl;
}

.fadl-login-wrap {
    max-width: 520px;
    margin: 0 auto;
    padding: 24px 16px;
}

.fadl-login-card {
    border-radius: 18px;
    padding: 28px;
    border: 1px solid rgba(34, 91, 65, 0.22);
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.08);
}

.fadl-login-title {
    text-align: center;
    margin-bottom: 8px;
}

.fadl-login-subtitle {
    text-align: center;
    opacity: 0.78;
    margin-bottom: 24px;
}

.fadl-login-error {
    color: #a61b1b;
    font-weight: 600;
    min-height: 24px;
}

.fadl-login-success {
    color: #176b3a;
    font-weight: 600;
    min-height: 24px;
}
"""


LOGIN_UI_JS = r"""
async function fadlMerchantRegistration() {
    const nameEl = document.querySelector(
        "#fadl-merchant-register-name textarea, #fadl-merchant-register-name input"
    );

    const emailEl = document.querySelector(
        "#fadl-merchant-register-email textarea, #fadl-merchant-register-email input"
    );

    const passwordEl = document.querySelector(
        "#fadl-merchant-register-password textarea, #fadl-merchant-register-password input"
    );

    const statusEl = document.querySelector(
        "#fadl-register-status"
    );

    const name = nameEl ? nameEl.value.trim() : "";
    const email = emailEl ? emailEl.value.trim() : "";
    const password = passwordEl ? passwordEl.value : "";

    if (!name || !email || !password) {
        if (statusEl) {
            statusEl.innerText =
                "يرجى إدخال الاسم والبريد الإلكتروني وكلمة المرور.";
            statusEl.className = "fadl-login-error";
        }
        return;
    }

    if (password.length < 8) {
        if (statusEl) {
            statusEl.innerText =
                "كلمة المرور يجب أن تحتوي على 8 أحرف على الأقل.";
            statusEl.className = "fadl-login-error";
        }
        return;
    }

    if (statusEl) {
        statusEl.innerText = "جاري إنشاء الحساب...";
        statusEl.className = "";
    }

    try {
        const csrfResponse = await fetch(
            "/merchant/register-csrf",
            {
                method: "GET",
                credentials: "include"
            }
        );

        let csrfData = {};

        try {
            csrfData = await csrfResponse.json();
        } catch (_) {
            csrfData = {};
        }

        if (!csrfResponse.ok || !csrfData.csrf_token) {
            throw new Error("CSRF initialization failed");
        }

        const response = await fetch(
            "/merchant/register",
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRF-Token": csrfData.csrf_token
                },
                body: JSON.stringify({
                    name: name,
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
            if (statusEl) {
                statusEl.innerText =
                    data.detail ||
                    "تعذر إنشاء الحساب. تحقق من البيانات وحاول مرة أخرى.";
                statusEl.className = "fadl-login-error";
            }
            return;
        }

        if (statusEl) {
            statusEl.innerText =
                "تم إنشاء حساب التاجر بنجاح. يمكنك الآن تسجيل الدخول.";
            statusEl.className = "fadl-login-success";
        }

        if (emailEl) {
            emailEl.value = email;
        }

        if (passwordEl) {
            passwordEl.value = "";
        }

        window.scrollTo({
            top: 0,
            behavior: "smooth"
        });

    } catch (error) {
        if (statusEl) {
            statusEl.innerText =
                "تعذر الاتصال بالخادم. حاول مرة أخرى.";
            statusEl.className = "fadl-login-error";
        }
    }
}


async function fadlMerchantLogin() {
    const emailEl = document.querySelector(
        "#fadl-merchant-email textarea, #fadl-merchant-email input"
    );

    const passwordEl = document.querySelector(
        "#fadl-merchant-password textarea, #fadl-merchant-password input"
    );

    const statusEl = document.querySelector(
        "#fadl-login-status"
    );

    const email = emailEl ? emailEl.value.trim() : "";
    const password = passwordEl ? passwordEl.value : "";

    if (!email || !password) {
        if (statusEl) {
            statusEl.innerText = "يرجى إدخال البريد الإلكتروني وكلمة المرور.";
            statusEl.className = "fadl-login-error";
        }
        return;
    }

    if (statusEl) {
        statusEl.innerText = "جاري تسجيل الدخول...";
        statusEl.className = "";
    }

    try {
        const response = await fetch("/merchant/login", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                email: email,
                password: password
            })
        });

        let data = {};

        try {
            data = await response.json();
        } catch (_) {
            data = {};
        }

        if (!response.ok) {
            const detail =
                data.detail ||
                "تعذر تسجيل الدخول. تحقق من البيانات وحاول مرة أخرى.";

            if (statusEl) {
                statusEl.innerText = detail;
                statusEl.className = "fadl-login-error";
            }

            return;
        }

        if (statusEl) {
            statusEl.innerText = "تم تسجيل الدخول بنجاح.";
            statusEl.className = "fadl-login-success";
        }

        /*
         * The authentication endpoint owns the session cookie.
         * We intentionally do not copy the token into JavaScript storage.
         */
        window.location.assign("/merchant/dashboard");

    } catch (error) {
        if (statusEl) {
            statusEl.innerText =
                "تعذر الاتصال بالخادم. حاول مرة أخرى.";
            statusEl.className = "fadl-login-error";
        }
    }
}
"""


def create_merchant_login_demo():
    """
    Build the merchant login UI.

    This is presentation only.
    Authentication remains exclusively in backend/merchant_auth_routes.py.
    """

    with gr.Blocks(
        title="FADL PAY — دخول التاجر",
    ) as demo:

        gr.HTML(
            """
            <div class="fadl-login-wrap">
                <div class="fadl-login-card">

                    <div class="fadl-login-title">
                        <h1>🏪 FADL PAY</h1>
                    </div>

                    <div class="fadl-login-subtitle">
                        دخول التاجر
                    </div>

                </div>
            </div>
            """
        )

        with gr.Column(elem_classes=["fadl-login-wrap"]):

            gr.Markdown(
                """
                ## 🔐 تسجيل دخول التاجر

                أدخل البريد الإلكتروني وكلمة المرور للوصول إلى لوحة التاجر.
                """
            )

            email = gr.Textbox(
                label="البريد الإلكتروني",
                placeholder="merchant@example.com",
                elem_id="fadl-merchant-email",
                type="email",
            )

            password = gr.Textbox(
                label="كلمة المرور",
                placeholder="••••••••",
                elem_id="fadl-merchant-password",
                type="password",
            )

            gr.HTML(
                """
                <div
                    id="fadl-login-status"
                    class="fadl-login-error"
                    aria-live="polite"
                ></div>
                """
            )

            login_button = gr.Button(
                "تسجيل الدخول",
                variant="primary",
            )

            gr.Markdown(
                """
                ---
                ## 🆕 إنشاء حساب تاجر

                أنشئ حسابًا جديدًا للوصول إلى خدمات FADL PAY.
                """
            )

            register_name = gr.Textbox(
                label="اسم التاجر",
                placeholder="اسم المتجر أو الشركة",
                elem_id="fadl-merchant-register-name",
            )

            register_email = gr.Textbox(
                label="البريد الإلكتروني",
                placeholder="merchant@example.com",
                elem_id="fadl-merchant-register-email",
                type="email",
            )

            register_password = gr.Textbox(
                label="كلمة المرور",
                placeholder="8 أحرف على الأقل",
                elem_id="fadl-merchant-register-password",
                type="password",
            )

            gr.HTML(
                """
                <div
                    id="fadl-register-status"
                    class="fadl-login-error"
                    aria-live="polite"
                ></div>
                """
            )

            register_button = gr.Button(
                "إنشاء حساب التاجر",
                variant="secondary",
            )

            register_button.click(
                fn=None,
                inputs=[
                    register_name,
                    register_email,
                    register_password,
                ],
                outputs=[],
                js="fadlMerchantRegistration",
            )

            login_button.click(
                fn=None,
                inputs=[email, password],
                outputs=[],
                js="fadlMerchantLogin",
            )

    return demo


demo = create_merchant_login_demo()


__all__ = [
    "create_merchant_login_demo",
    "demo",
]
