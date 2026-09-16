from fastapi import Header, HTTPException
from security.api_keys import verify_api_key



# ------------------------------------------------------------
# API Key Rate Limiting — in-memory / process-local
# ------------------------------------------------------------

_API_RATE_MAX_ATTEMPTS = 5
_API_RATE_WINDOW_SECONDS = 300
_API_RATE_BLOCK_SECONDS = 300

_api_rate_state = {}


def _api_rate_key(request, api_key):
    """Build a non-secret rate-limit key."""
    import hashlib

    client = getattr(request, "client", None)
    host = getattr(client, "host", "unknown")

    digest = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    return f"{host}:{digest}"


def _api_rate_blocked(request, api_key):
    """Return True when the API key/client is temporarily blocked."""
    import time

    key = _api_rate_key(request, api_key)
    state = _api_rate_state.get(key)

    if not state:
        return False

    now = time.time()
    blocked_until = state.get("blocked_until", 0)

    if blocked_until <= 0:
        return False

    if now >= blocked_until:
        _api_rate_state.pop(key, None)
        return False

    return True


def _api_rate_record_failure(request, api_key):
    """Record a failed API authentication attempt."""
    import time

    key = _api_rate_key(request, api_key)
    now = time.time()

    state = _api_rate_state.get(key)

    if not state or now - state["first_attempt"] >= _API_RATE_WINDOW_SECONDS:
        state = {
            "first_attempt": now,
            "attempts": 0,
            "blocked_until": 0,
        }

    state["attempts"] += 1

    if state["attempts"] >= _API_RATE_MAX_ATTEMPTS:
        state["blocked_until"] = now + _API_RATE_BLOCK_SECONDS

    _api_rate_state[key] = state


def _api_rate_clear(request, api_key):
    """Clear failed attempts after successful authentication."""
    key = _api_rate_key(request, api_key)
    _api_rate_state.pop(key, None)

def authenticate_api_key(
    request,
    authorization: str | None = Header(default=None),
):
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

    if _api_rate_blocked(request, api_key):
        raise HTTPException(
            status_code=429,
            detail="Too Many Requests",
        )

    merchant_reference = verify_api_key(api_key)

    if merchant_reference is None:
        _api_rate_record_failure(request, api_key)

        raise HTTPException(
            status_code=401,
            detail="Invalid or inactive API Key"
        )

    _api_rate_clear(request, api_key)

    return merchant_reference
