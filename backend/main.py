"""
Fadl Pay
Core Backend
Sandbox / Prototype
"""

from fastapi import FastAPI

app = FastAPI(
    title="Fadl Pay API",
    description="Payment Gateway Infrastructure - Sandbox",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "Fadl Pay",
        "status": "sandbox",
        "version": "0.1.0",
        "message": "Fadl Pay API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": "sandbox"
    }

from backend.api import app as api_app

# Customer Checkout Integration
from app.customer_checkout import router as customer_checkout_router

# Public customer payment page
# Must be registered before the root API mount.
app.include_router(customer_checkout_router)


# Merchant Dashboard Integration

# Existing API remains mounted at /
app.mount("/", api_app)
