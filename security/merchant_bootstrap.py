"""
FADL PAY — Merchant Operational Bootstrap

Security boundary:
- Local / operational use only.
- No FastAPI dependency.
- No public HTTP route.
- Does not modify main.py.
- Issues one-time activation tokens only.
- Raw setup tokens are returned once to the operator.
"""

from __future__ import annotations

import sqlite3

from security.merchant_activation import (
    DEFAULT_TOKEN_TTL_MINUTES,
    issue_setup_token,
)


def issue_merchant_setup_token(
    connection: sqlite3.Connection,
    merchant_reference: str,
    ttl_minutes: int = DEFAULT_TOKEN_TTL_MINUTES,
) -> str:
    """
    Issue a one-time setup token for a pending merchant.

    This function is intentionally operational-only.

    The caller controls the database connection.
    The raw token is returned once and must not be persisted
    or logged by this module.
    """

    return issue_setup_token(
        connection=connection,
        merchant_reference=merchant_reference,
        ttl_minutes=ttl_minutes,
    )


__all__ = [
    "issue_merchant_setup_token",
]
