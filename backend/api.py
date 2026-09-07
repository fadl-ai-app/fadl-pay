from fastapi import FastAPI, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional

from security.auth import authenticate_api_key
from payments.transaction_engine import (
    create_transaction,
    get_transaction,
    update_transaction_status,
)


app = FastAPI(
    title="Fadl Pay API",
    description="Independent Payment Gateway - Sandbox",
    version="0.2.0",
)


class TransactionRequest(BaseModel):
    merchant_reference: str = Field(min_length=3, max_length=100)
    amount: int = Field(gt=0)
    currency: str = Field(default="SDG", min_length=3, max_length=3)
    customer_reference: Optional[str] = Field(
        default=None,
        max_length=255,
    )
    payment_method: Optional[str] = Field(
        default=None,
        max_length=50,
    )


@app.get("/")
def root():
    return {
        "name": "Fadl Pay",
        "status": "sandbox",
        "version": "0.2.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": "sandbox",
    }


@app.post("/api/v1/transactions")
def create_payment(
    request: TransactionRequest,
    authenticated_merchant: str = Depends(authenticate_api_key),
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):

    try:
        transaction_reference = create_transaction(
            merchant_reference=authenticated_merchant,
            amount=request.amount,
            currency=request.currency,
            customer_reference=request.customer_reference,
            payment_method=request.payment_method,
            idempotency_key=idempotency_key,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    transaction = get_transaction(
        transaction_reference
    )

    return {
        "success": True,
        "environment": "sandbox",
        "transaction": transaction,
        "idempotent": idempotency_key is not None,
    }


@app.get("/api/v1/transactions/{transaction_reference}")
def read_payment(
    transaction_reference: str,
    authenticated_merchant: str = Depends(authenticate_api_key),
):

    transaction = get_transaction(transaction_reference)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    # 🔒 Merchant ownership check
    if transaction["merchant_reference"] != authenticated_merchant:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    return {
        "success": True,
        "environment": "sandbox",
        "transaction": transaction,
    }


@app.post("/api/v1/sandbox/transactions/{transaction_reference}/status")
def sandbox_update_status(
    transaction_reference: str,
    status: str,
    authenticated_merchant: str = Depends(authenticate_api_key),
):
    """
    Sandbox-only endpoint.
    Simulates a payment result.
    No real money is processed.

    🔒 Protected by API Key.
    🔒 Transaction must belong to authenticated merchant.
    """

    allowed_statuses = {
        "paid",
        "failed",
        "cancelled",
        "refunded",
    }

    if status not in allowed_statuses:
        raise HTTPException(
            status_code=400,
            detail="Invalid sandbox status",
        )

    transaction = get_transaction(transaction_reference)

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    # 🔒 Merchant ownership check
    if transaction["merchant_reference"] != authenticated_merchant:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    try:
        result = update_transaction_status(
            transaction_reference,
            status,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        )

    return {
        "success": True,
        "environment": "sandbox",
        "sandbox": True,
        "result": result,
    }
