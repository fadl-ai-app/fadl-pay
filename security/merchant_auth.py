# ============================================================
# 💳 FADL PAY — MERCHANT AUTHENTICATION CORE
# Argon2 Password Hashing
# ============================================================

from __future__ import annotations

import re
import time
import secrets
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError


# ------------------------------------------------------------
# Password hashing
# ------------------------------------------------------------

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """
    Hash a merchant password using Argon2.

    The plaintext password must never be stored.
    """
    if not isinstance(password, str):
        raise ValueError("Password must be a string")

    if len(password) < 8:
        raise ValueError("Password must contain at least 8 characters")

    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a plaintext password against an Argon2 hash.
    """
    if not password or not password_hash:
        return False

    try:
        return bool(
            _password_hasher.verify(password_hash, password)
        )
    except (VerifyMismatchError, VerificationError):
        return False
    except Exception:
        return False


# ------------------------------------------------------------
# Email validation
# ------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def normalize_email(email: str) -> str:
    """
    Normalize merchant email for lookup.
    """
    if not isinstance(email, str):
        raise ValueError("Email must be a string")

    normalized = email.strip().lower()

    if not _EMAIL_RE.match(normalized):
        raise ValueError("Invalid email address")

    return normalized


# ------------------------------------------------------------
# Login attempt limiter
# ------------------------------------------------------------

MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 300
LOGIN_BLOCK_SECONDS = 300


_login_attempts: dict[str, list[float]] = {}
_login_blocks: dict[str, float] = {}


def _cleanup_login_state(now: float) -> None:
    """
    Remove expired login state.
    """
    expired_blocks = [
        key
        for key, blocked_until in _login_blocks.items()
        if blocked_until <= now
    ]

    for key in expired_blocks:
        del _login_blocks[key]

    expired_attempts = []

    for key, timestamps in _login_attempts.items():
        recent = [
            ts
            for ts in timestamps
            if now - ts < LOGIN_WINDOW_SECONDS
        ]

        if recent:
            _login_attempts[key] = recent
        else:
            expired_attempts.append(key)

    for key in expired_attempts:
        del _login_attempts[key]


def is_login_blocked(identifier: str) -> bool:
    """
    Check whether an email/IP identifier is currently blocked.
    """
    now = time.time()
    _cleanup_login_state(now)

    blocked_until = _login_blocks.get(identifier)

    return bool(
        blocked_until is not None
        and blocked_until > now
    )


def record_login_failure(identifier: str) -> None:
    """
    Record a failed login attempt.
    """
    now = time.time()
    _cleanup_login_state(now)

    attempts = _login_attempts.setdefault(identifier, [])

    attempts.append(now)

    if len(attempts) >= MAX_LOGIN_ATTEMPTS:
        _login_blocks[identifier] = (
            now + LOGIN_BLOCK_SECONDS
        )


def clear_login_failures(identifier: str) -> None:
    """
    Clear failed attempts after successful authentication.
    """
    _login_attempts.pop(identifier, None)
    _login_blocks.pop(identifier, None)


# ------------------------------------------------------------
# Secure session token primitive
# ------------------------------------------------------------

def generate_session_token() -> str:
    """
    Generate an opaque cryptographically secure session token.

    Session persistence will be implemented separately.
    """
    return secrets.token_urlsafe(32)
