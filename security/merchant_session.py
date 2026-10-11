import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta


SESSION_TTL_SECONDS = 8 * 60 * 60


@dataclass
class MerchantSession:
    session_token: str
    merchant_reference: str
    role: str
    csrf_token: str
    created_at: datetime
    expires_at: datetime


_schema_ready = False


def _get_connection():
    # Use the application's configured database connector.
    from database.database import get_connection
    return get_connection()


def _token_hash(session_token):
    return hashlib.sha256(str(session_token).encode("utf-8")).hexdigest()


def _iso(value):
    return value.isoformat(timespec="microseconds")


def _ensure_session_table(connection):
    global _schema_ready

    if _schema_ready:
        return

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS merchant_sessions (
            session_token_hash TEXT PRIMARY KEY NOT NULL,
            merchant_reference TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'owner',
            csrf_token TEXT NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_merchant_sessions_expires_at
        ON merchant_sessions (expires_at)
        """
    )
    connection.commit()
    _schema_ready = True


def _delete_expired(connection, now_text=None):
    if now_text is None:
        now_text = _iso(datetime.utcnow())

    connection.execute(
        "DELETE FROM merchant_sessions WHERE expires_at <= ?",
        (now_text,),
    )


def _cleanup_expired_sessions():
    connection = _get_connection()
    try:
        _ensure_session_table(connection)
        _delete_expired(connection)
        connection.commit()
    finally:
        connection.close()


def create_session(merchant_reference, role="owner"):
    if not merchant_reference:
        raise ValueError("merchant_reference is required")

    session_token = secrets.token_urlsafe(32)
    csrf_token = secrets.token_urlsafe(32)

    now = datetime.utcnow()
    expires_at = now + timedelta(seconds=SESSION_TTL_SECONDS)

    session = MerchantSession(
        session_token=session_token,
        merchant_reference=merchant_reference,
        role=role or "owner",
        csrf_token=csrf_token,
        created_at=now,
        expires_at=expires_at,
    )

    connection = _get_connection()
    try:
        _ensure_session_table(connection)
        _delete_expired(connection, _iso(now))

        connection.execute(
            """
            INSERT INTO merchant_sessions (
                session_token_hash,
                merchant_reference,
                role,
                csrf_token,
                created_at,
                expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                _token_hash(session_token),
                session.merchant_reference,
                session.role,
                session.csrf_token,
                _iso(session.created_at),
                _iso(session.expires_at),
            ),
        )
        connection.commit()
    finally:
        connection.close()

    return session


def get_session(session_token):
    if isinstance(session_token, MerchantSession):
        session_token = session_token.session_token

    if not isinstance(session_token, str) or not session_token:
        return None

    connection = _get_connection()
    try:
        _ensure_session_table(connection)

        row = connection.execute(
            """
            SELECT
                merchant_reference,
                role,
                csrf_token,
                created_at,
                expires_at
            FROM merchant_sessions
            WHERE session_token_hash = ?
              AND expires_at > ?
            """,
            (
                _token_hash(session_token),
                _iso(datetime.utcnow()),
            ),
        ).fetchone()

        if row is None:
            return None

        return MerchantSession(
            session_token=session_token,
            merchant_reference=row["merchant_reference"],
            role=row["role"],
            csrf_token=row["csrf_token"],
            created_at=datetime.fromisoformat(row["created_at"]),
            expires_at=datetime.fromisoformat(row["expires_at"]),
        )
    finally:
        connection.close()


def get_session_merchant(session_token):
    session = get_session(session_token)
    return session.merchant_reference if session else None


def get_session_role(session_token):
    session = get_session(session_token)
    return session.role if session else None


def get_csrf_token(session_token):
    session = get_session(session_token)
    return session.csrf_token if session else None


def verify_csrf(session_token, csrf_token):
    session = get_session(session_token)

    if session is None or not csrf_token:
        return False

    return hmac.compare_digest(
        session.csrf_token.encode("utf-8"),
        str(csrf_token).encode("utf-8"),
    )


def revoke_session(session_token):
    if isinstance(session_token, MerchantSession):
        session_token = session_token.session_token

    if not isinstance(session_token, str) or not session_token:
        return False

    connection = _get_connection()
    try:
        _ensure_session_table(connection)
        cursor = connection.execute(
            "DELETE FROM merchant_sessions WHERE session_token_hash = ?",
            (_token_hash(session_token),),
        )
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()


def active_session_count():
    connection = _get_connection()
    try:
        _ensure_session_table(connection)
        _delete_expired(connection)
        connection.commit()

        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM merchant_sessions
            WHERE expires_at > ?
            """,
            (_iso(datetime.utcnow()),),
        ).fetchone()

        return int(row["total"])
    finally:
        connection.close()
