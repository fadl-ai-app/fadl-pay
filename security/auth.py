from fastapi import Header, HTTPException
from security.api_keys import verify_api_key


def authenticate_api_key(authorization: str | None = Header(default=None)):
    """
    التحقق من API Key عبر:
    Authorization: Bearer <API_KEY>
    """

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header"
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid Authorization format"
        )

    api_key = authorization[7:].strip()

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key"
        )

    merchant_reference = verify_api_key(api_key)

    if merchant_reference is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API Key"
        )

    return merchant_reference
