
from pathlib import Path
import sqlite3

from fastapi import APIRouter, Header, HTTPException, Depends
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from typing import Optional

from integration_v2.runtime_core import authorize


integration_bearer = HTTPBearer(auto_error=False)

router = APIRouter(
    prefix="/api/v1/integrations",
    tags=["integration-v2"],
)


class IntegrationTransactionRequest(BaseModel):
    amount: int
    currency: str = "SDG"
    customer_reference: Optional[str] = None
    payment_method: Optional[str] = None


def _database_path():
    from database.database import DB_PATH
    return str(DB_PATH)


def _require_transport_headers(
    authorization: Optional[str],
    integration_id: Optional[str],
    credential_id: Optional[str],
    merchant_reference: Optional[str],
):
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Integration authentication required",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid integration authentication scheme",
        )

    credential_secret = authorization[7:].strip()

    if not credential_secret:
        raise HTTPException(
            status_code=401,
            detail="Integration authentication required",
        )

    if not integration_id:
        raise HTTPException(
            status_code=400,
            detail="X-Integration-ID is required",
        )

    if not credential_id:
        raise HTTPException(
            status_code=400,
            detail="X-Credential-ID is required",
        )

    if not merchant_reference:
        raise HTTPException(
            status_code=400,
            detail="X-Merchant-Reference is required",
        )

    return (
        integration_id,
        credential_id,
        merchant_reference,
        credential_secret,
    )


def _authorize_request(
    *,
    integration_id: str,
    credential_id: str,
    merchant_reference: str,
    credential_secret: str,
    scope: str,
):
    conn = sqlite3.connect(
        f"file:{_database_path()}?mode=ro",
        uri=True,
    )

    try:
        return authorize(
            conn,
            integration_id=integration_id,
            credential_id=credential_id,
            credential_secret=credential_secret,
            merchant_reference=merchant_reference,
            scope=scope,
        )
    except Exception:
        raise HTTPException(
            status_code=403,
            detail="Integration authorization denied",
        )
    finally:
        conn.close()


def _engine_error(exc):
    # Do not expose internal exception details or credential material.
    raise HTTPException(
        status_code=400,
        detail="Transaction operation rejected",
    ) from exc


@router.post("/transactions", dependencies=[Depends(integration_bearer)])
def create_integration_transaction(
    request: IntegrationTransactionRequest,
    authorization: Optional[str] = Header(default=None),
    integration_id: Optional[str] = Header(
        default=None,
        alias="X-Integration-ID",
    ),
    credential_id: Optional[str] = Header(
        default=None,
        alias="X-Credential-ID",
    ),
    merchant_reference: Optional[str] = Header(
        default=None,
        alias="X-Merchant-Reference",
    ),
    idempotency_key: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    (
        integration_id,
        credential_id,
        merchant_reference,
        credential_secret,
    ) = _require_transport_headers(
        authorization,
        integration_id,
        credential_id,
        merchant_reference,
    )

    context = _authorize_request(
        integration_id=integration_id,
        credential_id=credential_id,
        merchant_reference=merchant_reference,
        credential_secret=credential_secret,
        scope="transactions:create",
    )

    from payments.transaction_engine import create_transaction, get_transaction

    try:
        transaction_reference = create_transaction(
            merchant_reference=context.merchant_reference,
            amount=request.amount,
            currency=request.currency,
            customer_reference=request.customer_reference,
            payment_method=request.payment_method,
            idempotency_key=idempotency_key,
        )

        transaction = get_transaction(
            transaction_reference,
            merchant_reference=context.merchant_reference,
        )

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found",
            )

        return {
            "success": True,
            "environment": "sandbox",
            "transaction": transaction,
            "idempotent": idempotency_key is not None,
        }

    except HTTPException:
        raise
    except Exception as exc:
        _engine_error(exc)


@router.get("/transactions/{transaction_reference}", dependencies=[Depends(integration_bearer)])
def read_integration_transaction(
    transaction_reference: str,
    authorization: Optional[str] = Header(default=None),
    integration_id: Optional[str] = Header(
        default=None,
        alias="X-Integration-ID",
    ),
    credential_id: Optional[str] = Header(
        default=None,
        alias="X-Credential-ID",
    ),
    merchant_reference: Optional[str] = Header(
        default=None,
        alias="X-Merchant-Reference",
    ),
):
    (
        integration_id,
        credential_id,
        merchant_reference,
        credential_secret,
    ) = _require_transport_headers(
        authorization,
        integration_id,
        credential_id,
        merchant_reference,
    )

    context = _authorize_request(
        integration_id=integration_id,
        credential_id=credential_id,
        merchant_reference=merchant_reference,
        credential_secret=credential_secret,
        scope="transactions:read",
    )

    from payments.transaction_engine import get_transaction

    try:
        transaction = get_transaction(
            transaction_reference,
            merchant_reference=context.merchant_reference,
        )

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found",
            )

        return {
            "success": True,
            "transaction": transaction,
        }

    except HTTPException:
        raise
    except Exception as exc:
        _engine_error(exc)


@router.post(
    "/transactions/{transaction_reference}/sandbox/status",
    dependencies=[Depends(integration_bearer)],
)
def update_integration_sandbox_status(
    transaction_reference: str,
    status: str,
    authorization: Optional[str] = Header(default=None),
    integration_id: Optional[str] = Header(
        default=None,
        alias="X-Integration-ID",
    ),
    credential_id: Optional[str] = Header(
        default=None,
        alias="X-Credential-ID",
    ),
    merchant_reference: Optional[str] = Header(
        default=None,
        alias="X-Merchant-Reference",
    ),
):
    (
        integration_id,
        credential_id,
        merchant_reference,
        credential_secret,
    ) = _require_transport_headers(
        authorization,
        integration_id,
        credential_id,
        merchant_reference,
    )

    context = _authorize_request(
        integration_id=integration_id,
        credential_id=credential_id,
        merchant_reference=merchant_reference,
        credential_secret=credential_secret,
        scope="sandbox:status",
    )

    from payments.transaction_engine import (
        get_transaction,
        update_transaction_status,
    )

    try:
        # Explicit merchant ownership check before mutation.
        transaction = get_transaction(
            transaction_reference,
            merchant_reference=context.merchant_reference,
        )

        if transaction is None:
            raise HTTPException(
                status_code=404,
                detail="Transaction not found",
            )

        result = update_transaction_status(
            transaction_reference,
            status,
        )

        return {
            "success": True,
            "transaction": result,
        }

    except HTTPException:
        raise
    except Exception as exc:
        _engine_error(exc)
