"""
Fadl Pay
Core Backend
Sandbox / Prototype
"""

from fastapi import FastAPI

from database.database import initialize_database
from backend.api import app as api_app


# ------------------------------------------------------------
# Database initialization
# ------------------------------------------------------------

initialize_database()


# ------------------------------------------------------------
# Main application
# ------------------------------------------------------------

app = FastAPI(
    title="Fadl Pay API",
    description="Payment Gateway Infrastructure - Sandbox",
    version="0.2.0",
)


@app.get("/")
def root():
    return {
        "name": "Fadl Pay",
        "status": "sandbox",
        "version": "0.2.0",
        "message": "Fadl Pay API is running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": "sandbox",
    }


# API routes
app.mount("/", api_app)
