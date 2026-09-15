


CUSTOM_CSS = '\n\n/* ==========================================================\n   FADL PAY — ULTRA COMPACT\n   ========================================================== */\n\n\n\n/* إزالة الفراغات الكبيرة التي تضيفها Gradio */\n\n\n/* عناصر الإدخال */\n\n\n/* Labels */\n\n\n/* العناوين */\n\n\n/* النصوص */\n\n\n/* زر الدفع */\n\n\n/* الفوتر */\n\n\n/* منع الفراغات الرأسية الإضافية */\n\n\n/* Mobile */\n@media (max-width: 600px) {\n    .gradio-container {\n        padding: 5px !important;\n    }\n\n    \n\n    \n\n    \n}\n\n\n/* ==========================================================\n   FADL PAY — COMPACT HEIGHT OVERRIDE\n   الشكل فقط — لا وظائف\n   ========================================================== */\n\nbody,\n.gradio-container {\n    min-height: 100vh !important;\n}\n\n/* الكرت */\n\n\n/* تقليل المسافات العامة */\n\n\n/* العناوين */\n\n\n/* النصوص */\n\n\n/* Labels */\n\n\n/* الحقول */\n\n\n/* تقليل المساحة داخل مجموعات Gradio */\n\n\n/* زر الدفع */\n\n\n/* الفوتر */\n\n\n/* الموبايل */\n@media (max-width: 600px) {\n    .gradio-container {\n        padding: 8px !important;\n    }\n\n    \n\n    \n\n    \n}\n\n/* -----------------------------------------------------------\n   الصفحة بالكامل\n----------------------------------------------------------- */\n\nhtml,\nbody,\n.gradio-container {\n    margin: 0 !important;\n    padding: 0 !important;\n    min-height: 100vh !important;\n}\n\n.gradio-container {\n    background:\n        radial-gradient(\n            circle at 50% 20%,\n            #f3f3f3 0%,\n            #e8e8e8 38%,\n            #dcdcdc 100%\n        ) !important;\n}\n\n\n/* -----------------------------------------------------------\n   إخفاء المساحات الافتراضية\n----------------------------------------------------------- */\n\n.gradio-container > .main {\n    padding: 0 !important;\n}\n\n.contain {\n    max-width: none !important;\n}\n\n\n/* -----------------------------------------------------------\n   الحاوية الرئيسية\n----------------------------------------------------------- */\n\n\n\n\n/* -----------------------------------------------------------\n   كرت الدفع\n----------------------------------------------------------- */\n\n\n\n\n/* -----------------------------------------------------------\n   رأس الكرت\n----------------------------------------------------------- */\n\n.fadl-brand {\n    text-align: center;\n    margin-bottom: 6px;\n}\n\n.fadl-brand h1 {\n    margin: 0;\n    font-size: 32px;\n    font-weight: 800;\n    letter-spacing: 0.5px;\n    color: #202020;\n}\n\n.fadl-brand .pay {\n    color: #555555;\n}\n\n.fadl-subtitle {\n    text-align: center;\n    color: #666666;\n    font-size: 14px;\n    margin-bottom: 28px;\n}\n\n\n/* -----------------------------------------------------------\n   العناوين\n----------------------------------------------------------- */\n\n\n\n\n/* -----------------------------------------------------------\n   الحقول\n----------------------------------------------------------- */\n\n\n\n\n\n\n/* -----------------------------------------------------------\n   زر الدفع\n----------------------------------------------------------- */\n\n.fadl-pay-btn {\n    width: 100% !important;\n    min-height: 54px !important;\n\n    margin-top: 12px !important;\n\n    border: none !important;\n    border-radius: 16px !important;\n\n    background:\n        linear-gradient(\n            135deg,\n            #242424,\n            #414141\n        ) !important;\n\n    color: white !important;\n\n    font-size: 17px !important;\n    font-weight: 800 !important;\n\n    box-shadow:\n        0 12px 24px rgba(0,0,0,0.20) !important;\n\n    transition:\n        transform 0.15s ease,\n        box-shadow 0.15s ease !important;\n}\n\n.fadl-pay-btn:hover {\n    transform: translateY(-2px);\n    box-shadow:\n        0 16px 30px rgba(0,0,0,0.25) !important;\n}\n\n\n/* -----------------------------------------------------------\n   الأمان\n----------------------------------------------------------- */\n\n.fadl-secure {\n    text-align: center;\n    margin-top: 20px;\n    color: #666666;\n    font-size: 12px;\n}\n\n\n/* -----------------------------------------------------------\n   الهاتف\n----------------------------------------------------------- */\n\n@media (max-width: 700px) {\n\n    \n\n    \n\n    .fadl-brand h1 {\n        font-size: 27px;\n    }\n\n    .fadl-subtitle {\n        margin-bottom: 20px;\n    }\n}\n\n/* FADL PAY — PRESERVED PRODUCTION CSS */\n\nbody {\n    background: #f5f5f5 !important;\n}\n\n.gradio-container {\n    max-width: 100% !important;\n    padding: 0 !important;\n}\n\n\n\n\n\n\n\n\n\n\n\n@media (max-width: 600px) {\n    \n}\n\n\n\n/* ==========================================================\n   💳 FADL PAY — Gradio Dropdown SVG visual isolation\n   ========================================================== */\n\n/* Gradio 6 renders its own dropdown icon internally.\n   Keep the icon, but prevent accidental inherited text styling. */\n\n/* Do NOT hide SVG globally.\n   Only prevent SVG elements from behaving like text. */\n\n\n\n/* ==========================================================\n   💳 FADL PAY — Hide accidental visible "svg" text only\n   ========================================================== */\n\n\n\n/* ============================================================\n   FADL PAY — FINAL COMPACT CARD OVERRIDE\n   CSS ONLY\n   ============================================================ */\n\nbody,\n.gradio-container {\n    background: #17191c !important;\n}\n\n.gradio-container {\n    width: 100% !important;\n    max-width: 100% !important;\n    min-height: 100vh !important;\n    margin: 0 !important;\n    padding: 28px 16px !important;\n    box-sizing: border-box !important;\n}\n\n/* Compact centered payment card */\n\n\n/* Compact vertical spacing */\n\n\n/* Inputs */\n\n\n/* Labels */\n\n\n/* Button — visual only */\n\n\n/* Focus — visual only */\n\n\n/* Mobile */\n@media (max-width: 600px) {\n\n    .gradio-container {\n        padding: 12px 8px !important;\n    }\n\n    \n\n    \n}\n\n\n/* ==========================================================\n   💳 FADL PAY — WHITE CENTER CARD\n   FIXED SIZE: 520px × 620px\n   ========================================================== */\n\n/* خلفية الصفحة */\nhtml,\nbody,\n#gradio,\n.gradio-container {\n    background: #f2f2f2 !important;\n}\n\n/* الصفحة */\n\n\n/* الكرت الأبيض الوحيد */\n\n\n/* منع الطبقات الرمادية داخل الكرت */\n\n\n/* الحقول */\n\n\n/* زر الدفع */\n\n\n/* الهاتف */\n@media (max-width: 600px) {\n\n    \n\n    \n}\n\n\n/* ============================================================\n   FADL PAY — SINGLE WHITE CARD\n   CSS ONLY\n   ============================================================ */\n\n/* الصفحة ليست كرتًا */\n.fadl-page {\n    width: 100% !important;\n    max-width: 100% !important;\n\n    min-height: 100vh !important;\n\n    margin: 0 !important;\n    padding: 24px 16px !important;\n\n    box-sizing: border-box !important;\n\n    display: flex !important;\n    align-items: center !important;\n    justify-content: center !important;\n\n    background: transparent !important;\n\n    border: 0 !important;\n    box-shadow: none !important;\n}\n\n/* الكرت الوحيد */\n.fadl-card,\n#fadl-pay-card {\n    width: 520px !important;\n    max-width: 100% !important;\n    min-width: 0 !important;\n\n    margin: 0 auto !important;\n    padding: 24px 28px !important;\n\n    box-sizing: border-box !important;\n\n    background: #ffffff !important;\n\n    border: 1px solid #e2e2e2 !important;\n    border-radius: 18px !important;\n\n    box-shadow:\n        0 8px 28px rgba(0,0,0,0.08) !important;\n\n    overflow: visible !important;\n}\n\n/* منع Gradio من توزيع الحقول أفقيًا */\n.fadl-card .gr-row,\n#fadl-pay-card .gr-row {\n    display: block !important;\n    width: 100% !important;\n}\n\n/* كل عنصر يأخذ سطرًا كاملًا */\n.fadl-card .gr-column,\n.fadl-card .form,\n.fadl-card .gr-form,\n.fadl-card .gr-group,\n.fadl-card .block,\n#fadl-pay-card .gr-column,\n#fadl-pay-card .form,\n#fadl-pay-card .gr-form,\n#fadl-pay-card .gr-group,\n#fadl-pay-card .block {\n    width: 100% !important;\n    max-width: 100% !important;\n    box-sizing: border-box !important;\n}\n\n/* تقليل الفراغات */\n.fadl-card .block,\n.fadl-card .form,\n.fadl-card .gr-form,\n.fadl-card .gr-group,\n#fadl-pay-card .block,\n#fadl-pay-card .form,\n#fadl-pay-card .gr-form,\n#fadl-pay-card .gr-group {\n    margin-top: 3px !important;\n    margin-bottom: 3px !important;\n}\n\n/* حقول الإدخال */\n.fadl-card input,\n.fadl-card textarea,\n.fadl-card select,\n#fadl-pay-card input,\n#fadl-pay-card textarea,\n#fadl-pay-card select {\n    width: 100% !important;\n    min-height: 38px !important;\n\n    box-sizing: border-box !important;\n}\n\n/* زر الدفع */\n.fadl-card button,\n#fadl-pay-card button {\n    width: 100% !important;\n    min-height: 42px !important;\n    box-sizing: border-box !important;\n}\n\n/* الهاتف */\n@media (max-width: 600px) {\n\n    .fadl-page {\n        min-height: 100vh !important;\n        padding: 12px 8px !important;\n        align-items: center !important;\n    }\n\n    .fadl-card,\n    #fadl-pay-card {\n        width: 100% !important;\n        max-width: 100% !important;\n\n        padding: 18px 16px !important;\n\n        border-radius: 16px !important;\n    }\n\n    .fadl-card input,\n    .fadl-card textarea,\n    .fadl-card select,\n    #fadl-pay-card input,\n    #fadl-pay-card textarea,\n    #fadl-pay-card select {\n        min-height: 36px !important;\n    }\n}\n\n\n/* ============================================================\n   💳 FADL PAY — ORA STYLE\n   Wide / White / Centered / Vertical\n   ============================================================ */\n\n/* الخلفية */\nbody,\n.gradio-container {\n    background: #f5f5f5 !important;\n}\n\n/* الحاوية الخارجية ليست كرتًا */\n.fadl-page {\n    display: block !important;\n\n    width: 100% !important;\n    max-width: 100% !important;\n\n    min-height: 100vh !important;\n\n    margin: 0 !important;\n    padding: 28px 16px !important;\n\n    box-sizing: border-box !important;\n\n    background: transparent !important;\n\n    border: 0 !important;\n    box-shadow: none !important;\n}\n\n/* الكرت الأبيض الوحيد */\n#fadl-pay-card {\n    display: block !important;\n\n    width: 560px !important;\n    max-width: calc(100vw - 32px) !important;\n    min-width: 0 !important;\n\n    margin: 0 auto !important;\n    padding: 30px 34px !important;\n\n    box-sizing: border-box !important;\n\n    background: #ffffff !important;\n\n    border: 1px solid #e5e5e5 !important;\n    border-radius: 20px !important;\n\n    box-shadow:\n        0 8px 30px rgba(0,0,0,0.08) !important;\n\n    overflow: visible !important;\n}\n\n/* كل محتوى الكرت عمودي */\n#fadl-pay-card > *,\n#fadl-pay-card .gr-column,\n#fadl-pay-card .block,\n#fadl-pay-card .form,\n#fadl-pay-card .gr-form,\n#fadl-pay-card .gr-group {\n    width: 100% !important;\n    max-width: 100% !important;\n    box-sizing: border-box !important;\n}\n\n/* منع أي توزيع أفقي */\n#fadl-pay-card .gr-row {\n    display: block !important;\n    width: 100% !important;\n}\n\n/* الحقول */\n#fadl-pay-card input,\n#fadl-pay-card textarea,\n#fadl-pay-card select {\n    display: block !important;\n\n    width: 100% !important;\n    max-width: 100% !important;\n\n    min-height: 40px !important;\n\n    box-sizing: border-box !important;\n}\n\n/* الزر */\n#fadl-pay-card button {\n    display: block !important;\n\n    width: 100% !important;\n    max-width: 100% !important;\n\n    min-height: 44px !important;\n\n    box-sizing: border-box !important;\n}\n\n/* المسافات */\n#fadl-pay-card .block,\n#fadl-pay-card .form,\n#fadl-pay-card .gr-form,\n#fadl-pay-card .gr-group {\n    margin-top: 4px !important;\n    margin-bottom: 4px !important;\n}\n\n/* الهاتف */\n@media (max-width: 600px) {\n\n    .fadl-page {\n        padding: 12px 8px !important;\n    }\n\n    #fadl-pay-card {\n        width: 100% !important;\n        max-width: 100% !important;\n\n        padding: 20px 16px !important;\n\n        border-radius: 17px !important;\n    }\n\n    #fadl-pay-card input,\n    #fadl-pay-card textarea,\n    #fadl-pay-card select {\n        min-height: 38px !important;\n    }\n}\n\n/* ==========================================================\n   💳 FADL PAY — FINAL SINGLE CARD OVERRIDE\n   ========================================================== */\n\nbody,\n.gradio-container {\n    background: #f5f5f5 !important;\n}\n\n.fadl-page {\n    width: 100% !important;\n    max-width: 100% !important;\n    min-height: 100vh !important;\n    margin: 0 !important;\n    padding: 30px 16px !important;\n\n    display: flex !important;\n    align-items: center !important;\n    justify-content: center !important;\n\n    background: transparent !important;\n    border: 0 !important;\n    box-shadow: none !important;\n}\n\n/* الكرت الحقيقي الوحيد */\n#fadl-pay-card {\n    width: 560px !important;\n    max-width: calc(100vw - 32px) !important;\n    min-width: 0 !important;\n\n    margin: 0 auto !important;\n    padding: 28px 34px !important;\n\n    box-sizing: border-box !important;\n\n    background: #ffffff !important;\n    border: 1px solid #e2e2e2 !important;\n    border-radius: 20px !important;\n\n    box-shadow: 0 10px 30px rgba(0, 0, 0, .08) !important;\n\n    display: flex !important;\n    flex-direction: column !important;\n}\n\n/* المحتوى كله داخل نفس الكرت */\n#fadl-pay-card > *,\n#fadl-pay-card .gradio-row,\n#fadl-pay-card .gradio-column {\n    width: 100% !important;\n    max-width: 100% !important;\n    box-sizing: border-box !important;\n}\n\n/* الحقول */\n#fadl-pay-card input,\n#fadl-pay-card textarea,\n#fadl-pay-card select,\n#fadl-pay-card [role="listbox"] {\n    box-sizing: border-box !important;\n    min-height: 38px !important;\n    height: 38px !important;\n}\n\n/* Labels */\n#fadl-pay-card label {\n    margin-bottom: 5px !important;\n    font-size: 14px !important;\n    line-height: 1.25 !important;\n}\n\n/* تقليل المسافات */\n#fadl-pay-card .block {\n    margin-bottom: 9px !important;\n}\n\n/* زر الدفع */\n#fadl-pay-card button {\n    min-height: 42px !important;\n    height: 42px !important;\n    margin-top: 5px !important;\n    border-radius: 10px !important;\n    font-weight: 600 !important;\n}\n\n/* النتيجة */\n#fadl-pay-card .markdown {\n    margin-top: 10px !important;\n}\n\n/* Auto Currency داخل الكرت */\n#fadl-pay-card .fadl-auto-currency-card,\n#fadl-pay-card .fadl-currency-card {\n    width: 100% !important;\n    box-sizing: border-box !important;\n    margin: 4px 0 9px !important;\n}\n\n/* Mobile */\n@media (max-width: 640px) {\n\n    .fadl-page {\n        min-height: auto !important;\n        padding: 18px 10px !important;\n        align-items: flex-start !important;\n    }\n\n    #fadl-pay-card {\n        width: 100% !important;\n        max-width: 100% !important;\n        padding: 22px 18px !important;\n        border-radius: 16px !important;\n    }\n\n    #fadl-pay-card input,\n    #fadl-pay-card textarea,\n    #fadl-pay-card select,\n    #fadl-pay-card [role="listbox"] {\n        min-height: 36px !important;\n        height: 36px !important;\n    }\n\n    #fadl-pay-card button {\n        min-height: 40px !important;\n        height: 40px !important;\n    }\n}\n\n/* ============================================================\n   FADL PAY — TEXT + SVG VISIBILITY FIX\n   ============================================================ */\n\n/* النصوص داخل كرت الدفع */\n#fadl-pay-card,\n#fadl-pay-card label,\n#fadl-pay-card .label-wrap,\n#fadl-pay-card .wrap,\n#fadl-pay-card .markdown,\n#fadl-pay-card .prose,\n#fadl-pay-card p,\n#fadl-pay-card span {\n    color: #222222 !important;\n}\n\n/* الحقول */\n#fadl-pay-card input,\n#fadl-pay-card textarea,\n#fadl-pay-card select {\n    color: #222222 !important;\n    -webkit-text-fill-color: #222222 !important;\n}\n\n/* Placeholder */\n#fadl-pay-card input::placeholder,\n#fadl-pay-card textarea::placeholder {\n    color: #777777 !important;\n    -webkit-text-fill-color: #777777 !important;\n    opacity: 1 !important;\n}\n\n/* القوائم */\n#fadl-pay-card [role="listbox"],\n#fadl-pay-card [role="combobox"] {\n    color: #222222 !important;\n}\n\n/* SVG الحقيقي يبقى موجودًا كعنصر رسومي،\n   لكن أي SVG تم حقنه كنص لا يظهر */\n#fadl-pay-card svg {\n    color: inherit !important;\n}\n\n/* منع ظهور كلمة svg كنص */\n#fadl-pay-card .svg-text,\n#fadl-pay-card .svg-label {\n    display: none !important;\n}\n\n/* ============================================================\n   FADL PAY — DROPDOWN TEXT VISIBILITY\n   ============================================================ */\n\n/* Dropdown container */\n#fadl-pay-card .gradio-dropdown,\n#fadl-pay-card [data-testid="dropdown"] {\n    color: #222222 !important;\n}\n\n/* Selected value */\n#fadl-pay-card .gradio-dropdown input,\n#fadl-pay-card [role="combobox"] {\n    color: #222222 !important;\n    -webkit-text-fill-color: #222222 !important;\n    font-weight: 600 !important;\n    opacity: 1 !important;\n}\n\n/* Dropdown options */\n#fadl-pay-card [role="option"],\n#fadl-pay-card [role="option"] *,\n#fadl-pay-card .options li,\n#fadl-pay-card .options li * {\n    color: #222222 !important;\n    -webkit-text-fill-color: #222222 !important;\n    font-weight: 500 !important;\n    opacity: 1 !important;\n}\n\n/* Placeholder */\n#fadl-pay-card [role="combobox"]::placeholder {\n    color: #555555 !important;\n    -webkit-text-fill-color: #555555 !important;\n    opacity: 1 !important;\n}\n\n/* Dropdown arrow/icon — keep visible but don\'t turn it into text */\n#fadl-pay-card .wrap svg {\n    opacity: 1 !important;\n}\n\n/* Do NOT allow SVG fallback text to inherit as visible text */\n#fadl-pay-card .wrap > svg {\n    color: #555555 !important;\n}\n\n/* ============================================================\n   FADL PAY — SOFT LIGHT THEME\n   ============================================================ */\n\n/* خلفية مريحة للعين */\nbody,\n.gradio-container {\n    background: #f1f2f4 !important;\n}\n\n/* الكرت نفسه يبقى أبيض ولكن أقل حدة */\n#fadl-pay-card {\n    background: #fafafa !important;\n    border-color: #dddddf !important;\n    box-shadow: 0 10px 28px rgba(0, 0, 0, .07) !important;\n}\n\n/* الحقول */\n#fadl-pay-card input,\n#fadl-pay-card textarea,\n#fadl-pay-card select,\n#fadl-pay-card [role="combobox"] {\n    background: #f5f5f6 !important;\n    border-color: #d6d6d8 !important;\n}\n\n/* النص */\n#fadl-pay-card,\n#fadl-pay-card label,\n#fadl-pay-card span,\n#fadl-pay-card p {\n    color: #252525 !important;\n}\n\n\n\n/* ============================================================\n   FADL PAY — FINAL DROPDOWN + BUTTON VISIBILITY\n   ============================================================ */\n\n/* ---------- Dropdown field ---------- */\n\n#fadl-pay-card .gradio-dropdown,\n#fadl-pay-card [data-testid="dropdown"],\n#fadl-pay-card [role="combobox"] {\n    background: #f3f3f4 !important;\n    color: #1f1f1f !important;\n    opacity: 1 !important;\n    border-color: #c9c9cc !important;\n}\n\n#fadl-pay-card .gradio-dropdown input,\n#fadl-pay-card [role="combobox"] input,\n#fadl-pay-card input[role="combobox"] {\n    background: #f3f3f4 !important;\n    color: #1f1f1f !important;\n    -webkit-text-fill-color: #1f1f1f !important;\n    opacity: 1 !important;\n}\n\n/* ---------- Open options ---------- */\n\n#fadl-pay-card [role="listbox"],\n#fadl-pay-card .options,\n#fadl-pay-card [role="listbox"] ul {\n    background: #ffffff !important;\n    color: #171717 !important;\n    opacity: 1 !important;\n    border: 1px solid #cccccf !important;\n    box-shadow: 0 8px 22px rgba(0,0,0,.14) !important;\n    z-index: 99999 !important;\n}\n\n#fadl-pay-card [role="option"],\n#fadl-pay-card [role="option"] *,\n#fadl-pay-card .options li,\n#fadl-pay-card .options li * {\n    background: #ffffff !important;\n    color: #171717 !important;\n    -webkit-text-fill-color: #171717 !important;\n    opacity: 1 !important;\n    visibility: visible !important;\n    font-weight: 500 !important;\n}\n\n#fadl-pay-card [role="option"]:hover,\n#fadl-pay-card .options li:hover {\n    background: #eeeeef !important;\n    color: #111111 !important;\n}\n\n/* ---------- Pay button ---------- */\n\n#fadl-pay-card button.fadl-pay-btn,\n#fadl-pay-card .fadl-pay-btn,\n#fadl-pay-card button {\n    position: relative !important;\n    z-index: 10000 !important;\n    pointer-events: auto !important;\n    cursor: pointer !important;\n    opacity: 1 !important;\n    visibility: visible !important;\n    color: #ffffff !important;\n    -webkit-text-fill-color: #ffffff !important;\n    background: #303236 !important;\n    border: 1px solid #303236 !important;\n    min-height: 42px !important;\n    height: 42px !important;\n}\n\n#fadl-pay-card button.fadl-pay-btn:hover,\n#fadl-pay-card .fadl-pay-btn:hover {\n    background: #202124 !important;\n}\n\n#fadl-pay-card button.fadl-pay-btn:disabled,\n#fadl-pay-card .fadl-pay-btn:disabled {\n    opacity: .65 !important;\n    pointer-events: auto !important;\n}\n\n/* ---------- Keep card above background layers ---------- */\n\n#fadl-pay-card {\n    position: relative !important;\n    z-index: 10 !important;\n}\n'



import gradio as gr


# ============================================================
# FADL PAY — SMALL CENTER PAYMENT CARD
# ============================================================

FADL_PREVIEW_CSS = r"""

/* ============================================================
   FADL PAY — SMALL CENTER PAYMENT CARD
   ============================================================ */

body {
    background: #f5f6f8 !important;
}

/* منطقة Gradio */
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 auto !important;
    padding: 30px 15px !important;
}

/* كرت الدفع */
.fadl-pay-card {
    width: 520px !important;
    max-width: calc(100vw - 30px) !important;
    margin: 35px auto !important;
    padding: 28px !important;

    background: #ffffff !important;

    border: 1px solid #e5e7eb !important;
    border-radius: 22px !important;

    box-shadow:
        0 12px 35px rgba(0,0,0,.08) !important;

    box-sizing: border-box !important;
}

/* بطاقة العملة */
.fadl-auto-currency-card {
    width: 100% !important;
    box-sizing: border-box !important;

    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;

    padding: 13px 16px !important;
    margin: 10px 0 18px !important;

    background: #eeeeee !important;
    border: 1px solid #dddddd !important;
    border-radius: 14px !important;
}

.fadl-currency-title {
    font-size: 14px !important;
    font-weight: 600 !important;
    color: #666666 !important;
}

.fadl-currency-value {
    font-size: 17px !important;
    font-weight: 700 !important;
    color: #222222 !important;
}

/* الهاتف */
@media (max-width: 640px) {

    .gradio-container {
        padding: 10px !important;
    }

    .fadl-pay-card {
        width: 100% !important;
        max-width: 100% !important;

        margin: 10px auto !important;
        padding: 20px !important;

        border-radius: 18px !important;
    }
}

"""




# ============================================================
# FADL PAY — AUTO CURRENCY CARD
# ============================================================

FADL_AUTO_CURRENCY_CSS = r"""


/* ============================================================
   FADL PAY — AUTO CURRENCY CARD
   ============================================================ */

.fadl-auto-currency-card {

    width: 100%;
    box-sizing: border-box;

    display: flex;
    align-items: center;
    justify-content: space-between;

    padding: 13px 16px;
    margin: 10px 0 18px;

    background: #eeeeee;

    border: 1px solid #dddddd;
    border-radius: 14px;

    color: #333;

    box-shadow:
        0 3px 10px rgba(0,0,0,.04);
}

.fadl-currency-title {

    font-size: 14px;
    font-weight: 600;

    color: #666;
}

.fadl-currency-value {

    font-size: 17px;
    font-weight: 700;

    color: #222;

    letter-spacing: .5px;
}

/* ------------------------------------------------------------
   Laptop
   ------------------------------------------------------------ */

@media (min-width: 900px) {

    .fadl-pay-card {

        width: 540px !important;
        max-width: 540px !important;

        margin-left: auto !important;
        margin-right: auto !important;
    }
}

/* ------------------------------------------------------------
   Mobile
   ------------------------------------------------------------ */

@media (max-width: 640px) {

    .fadl-pay-card {

        width: calc(100vw - 20px) !important;

        max-width: none !important;

        margin: 10px auto !important;

        padding: 18px !important;
    }

    .fadl-auto-currency-card {

        padding: 12px 14px;
    }
}

"""

FADL_AUTO_CURRENCY_JS = r"""

<script>
(function () {

    const currencyMap = {
        "Egypt": "EGP",
        "مصر": "EGP",

        "Saudi Arabia": "SAR",
        "السعودية": "SAR",

        "Sudan": "SDG",
        "السودان": "SDG",

        "United Arab Emirates": "AED",
        "الإمارات": "AED",

        "United States": "USD",
        "أمريكا": "USD",
        "United States of America": "USD"
    };

    function findCountry() {

        const selects = document.querySelectorAll(
            "select, input"
        );

        for (const el of selects) {

            const value = (
                el.value ||
                el.getAttribute("value") ||
                ""
            ).trim();

            if (currencyMap[value]) {
                return currencyMap[value];
            }
        }

        return null;
    }

    function updateCurrency() {

        const currency = findCountry();

        if (!currency) return;

        let card = document.querySelector(
            ".fadl-auto-currency-card"
        );

        if (!card) {

            card = document.createElement("div");

            card.className =
                "fadl-auto-currency-card";

            const container =
                document.querySelector(
                    "#fadl-pay-card"
                );

            if (container) {
                container.prepend(card);
            }
        }

        card.innerHTML = `
            <div class="fadl-currency-title">
                💱 العملة
            </div>

            <div class="fadl-currency-value">
                ${currency}
            </div>
        `;
    }

    document.addEventListener(
        "change",
        function () {
            setTimeout(updateCurrency, 100);
        }
    );

    setInterval(updateCurrency, 800);

    setTimeout(updateCurrency, 500);

})();
</script>

"""




    
# ============================================================
# FADL PAY — BANK DEMO UI CSS
# ============================================================

FADL_BANK_UI_CSS = r"""


/* ==========================================================
   FADL PAY — BANK DEMO RESPONSIVE UI
   ========================================================== */

body,
.gradio-container {
    margin: 0 !important;
    padding: 0 !important;
}

.gradio-container {
    min-height: 100vh !important;
}

/* المحتوى الرئيسي */
.fadl-pay-shell,
.fadl-pay-container,
.fadl-pay-card {
    box-sizing: border-box !important;
}

/* البطاقة الرئيسية */
.fadl-pay-card {
    width: min(560px, calc(100vw - 32px)) !important;
    max-width: 560px !important;
    margin: 32px auto !important;
    padding: 28px !important;

    border-radius: 22px !important;

    box-shadow:
        0 18px 45px rgba(0,0,0,.10),
        0 3px 12px rgba(0,0,0,.06) !important;

    background: rgba(255,255,255,.98) !important;
}

/* العنوان */
.fadl-pay-card h1,
.fadl-pay-card h2 {
    text-align: center !important;
}

/* الحقول */
.fadl-pay-card input,
.fadl-pay-card textarea,
.fadl-pay-card select {
    border-radius: 12px !important;
}

/* ==========================================================
   💱 Currency Card
   ========================================================== */

.fadl-currency-card {
    width: 100% !important;
    box-sizing: border-box !important;

    padding: 14px 16px !important;
    margin: 8px 0 18px 0 !important;

    border-radius: 14px !important;

    background: #eeeeee !important;
    border: 1px solid #dddddd !important;

    color: #333333 !important;

    display: flex !important;
    align-items: center !important;
    justify-content: space-between !important;

    font-size: 15px !important;
}

.fadl-currency-card .currency-label {
    font-weight: 600 !important;
    color: #666 !important;
}

.fadl-currency-card .currency-value {
    font-weight: 700 !important;
    color: #222 !important;
}

/* زر الدفع */
.fadl-pay-card button {
    border-radius: 13px !important;
    min-height: 48px !important;
}

/* ==========================================================
   📱 Mobile
   ========================================================== */

@media (max-width: 640px) {

    .fadl-pay-card {
        width: calc(100vw - 20px) !important;
        max-width: none !important;

        margin: 10px auto !important;
        padding: 18px !important;

        border-radius: 18px !important;
        box-shadow: 0 8px 25px rgba(0,0,0,.08) !important;
    }

    .fadl-currency-card {
        margin-top: 6px !important;
    }
}

/* ==========================================================
   💻 Large Screens
   ========================================================== */

@media (min-width: 1200px) {

    .fadl-pay-card {
        width: 540px !important;
        max-width: 540px !important;
        margin-left: auto !important;
        margin-right: auto !important;
    }
}

"""




# ============================================================
# 💳 FADL PAY — Payment UI
# ============================================================

COUNTRIES = [
    "Egypt",
    "Saudi Arabia",
    "Sudan",
    "United Arab Emirates",
    "United States",
]

CURRENCIES = [
    "EGP",
    "SAR",
    "SDG",
    "AED",
    "USD",
]

PAYMENT_METHODS = [
    "🏦 بنك",
    "📱 محفظة إلكترونية",
    "💳 بطاقة",
]


def submit_payment(
    country,
    currency,
    amount,
    customer_reference,
    payment_method,
):
    """
    إنشاء عملية دفع من خلال Backend الداخلي.

    لا يتم كشف API Key للمستخدم.
    """

    if not country:
        return "⚠️ الرجاء اختيار الدولة."

    if not currency:
        return "⚠️ الرجاء اختيار العملة."

    if not amount:
        return "⚠️ الرجاء إدخال المبلغ."

    if not payment_method:
        return "⚠️ الرجاء اختيار طريقة الدفع."

    try:
        amount = int(amount)
    except (TypeError, ValueError):
        return "⚠️ المبلغ يجب أن يكون رقمًا صحيحًا."

    if amount <= 0:
        return "⚠️ المبلغ يجب أن يكون أكبر من صفر."

    # إنشاء المعاملة داخل Backend
    from backend.api import create_transaction

    # merchant_reference داخلي — لا يظهر للمستخدم
    import os

    merchant_reference = os.getenv(
        "FADL_UI_MERCHANT_REFERENCE",
        ""
    ).strip()

    if not merchant_reference:
        return (
            "⚠️ إعداد التاجر غير مكتمل في بيئة التشغيل.\n\n"
            "يرجى ضبط FADL_UI_MERCHANT_REFERENCE في Backend."
        )

    try:
        transaction_reference = create_transaction(
            merchant_reference=merchant_reference,
            amount=amount,
            currency=currency,
            customer_reference=customer_reference or None,
            payment_method=payment_method,
            idempotency_key=None,
        )

        return (
            "🟢 **تم إنشاء عملية الدفع بنجاح**\n\n"
            f"🌍 الدولة: {country}\n"
            f"💱 العملة: {currency}\n"
            f"💰 المبلغ: {amount}\n"
            f"👤 المرجع: {customer_reference or 'غير محدد'}\n"
            f"💳 طريقة الدفع: {payment_method}\n\n"
            f"🔖 **رقم العملية:** `{transaction_reference}`\n\n"
            "🧪 FADL PAY — Sandbox"
        )

    except ValueError as error:
        return f"❌ تعذر إنشاء عملية الدفع: {error}"

    except Exception as error:
        return (
            "❌ حدث خطأ أثناء إنشاء عملية الدفع.\n\n"
            f"التفاصيل: {error}"
        )


with gr.Blocks(
    css=CUSTOM_CSS,
    title="FADL PAY",
    theme=gr.themes.Soft(),
) as demo:

    with gr.Column(elem_classes="fadl-page"):

        with gr.Column(
            elem_classes="fadl-card",
            elem_id="fadl-pay-card",
        ):

            gr.HTML(
                """
                <div class="fadl-brand">
                    <h1>💳 FADL <span class="pay">PAY</span></h1>
                </div>
                <div class="fadl-subtitle">
                    ادفع بسهولة وأمان
                </div>
                """
            )

            country = gr.Dropdown(
                choices=COUNTRIES,
                value=None,
                label="🌍 الدولة",
                interactive=True,
            )

            currency = gr.Dropdown(
                choices=CURRENCIES,
                value=None,
                label="💱 العملة",
                interactive=True,
            )

            amount = gr.Number(
                label="💰 المبلغ",
                minimum=1,
                precision=0,
                interactive=True,
            )

            customer_reference = gr.Textbox(
                label="👤 مرجع العميل",
                placeholder="أدخل رقم أو مرجع العميل",
                interactive=True,
            )

            payment_method = gr.Dropdown(
                choices=PAYMENT_METHODS,
                value=None,
                label="💳 طريقة الدفع",
                interactive=True,
            )
            pay_button = gr.Button(
                "💳 ادفع الآن",
                variant="primary",
                elem_classes="fadl-pay-btn",
            )

            result = gr.Markdown()

            gr.HTML(
                """
                <div class="fadl-secure">
                    🔒 دفع آمن • FADL PAY
                </div>

                <div class="fadl-admin-link">
                    <a href="/admin/" target="_self">
                        🔐 الإدارة المالية
                    </a>
                </div>
                """
            )

            pay_button.click(
                submit_payment,
                inputs=[
                    country,
                    currency,
                    amount,
                    customer_reference,
                    payment_method,
                ],
                outputs=result,
            )

