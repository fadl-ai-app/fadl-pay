from dataclasses import dataclass
from datetime import datetime, timedelta
import hmac
import secrets


SESSION_TTL_SECONDS = 8 * 60 * 60


@dataclass
class MerchantSession:
    session_token: str
    merchant_reference: str
    csrf_token: str
    created_at: datetime
    expires_at: datetime


_sessions = {}


def _cleanup_expired_sessions():
    now = datetime.utcnow()

    expired = [
        token
        for token, session in _sessions.items()
        if session.expires_at <= now
    ]

    for token in expired:
        _sessions.pop(token, None)


def create_session(merchant_reference):
    if not merchant_reference:
        raise ValueError("merchant_reference is required")

    _cleanup_expired_sessions()

    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)

    now = datetime.utcnow()
    expires_at = now + timedelta(
        seconds=SESSION_TTL_SECONDS
    )

    session = MerchantSession(
        session_token=session_token,
        merchant_reference=merchant_reference,
        csrf_token=csrf_token,
        created_at=now,
        expires_at=expires_at,
    )

    _sessions[session_token] = session

    return session


def get_session(session_token):
    _cleanup_expired_sessions()

    if isinstance(session_token, MerchantSession):
        session_token = session_token.session_token

    if not session_token:
        return None

    return _sessions.get(session_token)


def get_session_merchant(session_token):
    session = get_session(session_token)

    if session is None:
        return None

    return session.merchant_reference


def get_csrf_token(session_token):
    session = get_session(session_token)

    if session is None:
        return None

    return session.csrf_token


def verify_csrf(session_token, csrf_token):
    session = get_session(session_token)

    if session is None:
        return False

    if not csrf_token:
        return False

    return hmac.compare_digest(
        session.csrf_token,
        csrf_token,
    )


def revoke_session(session_token):
    if isinstance(session_token, MerchantSession):
        session_token = session_token.session_token

    if not session_token:
        return False

    return (
        _sessions.pop(session_token, None)
        is not None
    )


def active_session_count():
    _cleanup_expired_sessions()
    return len(_sessions)
