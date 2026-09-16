"""
FADL PAY — Merchant API Key Session Adapter

WORK-stage adapter:
API Key -> verify_api_key -> merchant_reference -> session

The raw API key is never stored in the merchant session.
"""

from security.api_keys import verify_api_key
from security.merchant_session import create_session


def create_session_from_api_key(api_key):
    """
    Validate an FADL PAY API key and create a merchant session.

    Returns:
        MerchantSession

    Raises:
        PermissionError
    """

    if not api_key:
        raise PermissionError("Invalid API key")

    merchant_reference = verify_api_key(api_key)

    if merchant_reference is None:
        raise PermissionError("Invalid API key")

    return create_session(merchant_reference)
