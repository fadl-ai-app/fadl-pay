import json
import urllib.request
import urllib.error
import time
from datetime import datetime, timezone

from webhooks.signature import sign_payload
from webhooks.ssrf import validate_webhook_url


MAX_WEBHOOK_ATTEMPTS = 3
RETRY_DELAYS_SECONDS = [1, 2]


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def build_webhook_payload(
    event_id,
    event_type,
    transaction_reference,
    event_data,
):
    return {
        "id": event_id,
        "event": event_type,
        "transaction_reference": transaction_reference,
        "data": event_data,
        "created_at": utc_now(),
    }


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        req,
        fp,
        code,
        msg,
        headers,
        newurl,
    ):
        raise urllib.error.HTTPError(
            req.full_url,
            code,
            "Webhook redirects are not allowed",
            headers,
            fp,
        )


def send_webhook(
    webhook_url,
    payload,
    webhook_secret,
    timeout=10,
):
    # Re-validate immediately before network delivery.
    # This protects against endpoints becoming unsafe after creation.
    validate_webhook_url(webhook_url)

    body = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":")
    )

    signature = sign_payload(
        body,
        webhook_secret
    )

    request = urllib.request.Request(
        webhook_url,
        data=body.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Fadl-Pay-Webhook/0.1",
            "X-Fadl-Pay-Signature": signature,
        },
        method="POST",
    )

    last_error = None
    last_status_code = None

    for attempt in range(1, MAX_WEBHOOK_ATTEMPTS + 1):

        try:
            opener = urllib.request.build_opener(
                NoRedirectHandler()
            )

            with opener.open(
                request,
                timeout=timeout
            ) as response:

                return {
                    "success": True,
                    "status_code": response.status,
                    "signature": signature,
                    "attempts": attempt,
                }

        except urllib.error.HTTPError as error:
            last_status_code = error.code
            last_error = "HTTP error"

        except Exception as error:
            last_status_code = None
            last_error = str(error)

        if attempt < MAX_WEBHOOK_ATTEMPTS:
            time.sleep(RETRY_DELAYS_SECONDS[attempt - 1])

    return {
        "success": False,
        "status_code": last_status_code,
        "error": last_error,
        "signature": signature,
        "attempts": MAX_WEBHOOK_ATTEMPTS,
    }
