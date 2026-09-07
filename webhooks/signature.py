import hashlib
import hmac


def generate_webhook_secret():
    import secrets
    return "whsec_test_" + secrets.token_urlsafe(32)


def sign_payload(payload: str, secret: str) -> str:
    signature = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return "sha256=" + signature


def verify_signature(
    payload: str,
    signature: str,
    secret: str
) -> bool:
    expected_signature = sign_payload(
        payload,
        secret
    )

    return hmac.compare_digest(
        expected_signature,
        signature
    )
