import json
import time

from webhooks.delivery import (
    build_webhook_payload,
    send_webhook,
)

from webhooks.dispatcher import (
    prepare_webhook_dispatch,
)

from webhooks.endpoint_manager import (
    get_webhook_endpoint,
)

from webhooks.signature import sign_payload

from webhooks.delivery_log import (
    create_delivery_log,
    update_delivery_log,
    get_delivery_log,
    get_delivery_by_event_endpoint,
)


MAX_WEBHOOK_ATTEMPTS = 3

RETRY_DELAYS_SECONDS = [
    1,
    2,
]


def should_retry(attempts, success):
    if success:
        return False

    return attempts < MAX_WEBHOOK_ATTEMPTS


def get_retry_delay(attempts):
    if attempts <= 0:
        return 0

    index = attempts - 1

    if index >= len(RETRY_DELAYS_SECONDS):
        return RETRY_DELAYS_SECONDS[-1]

    return RETRY_DELAYS_SECONDS[index]


def dispatch_webhook(
    merchant_reference,
    event_id,
    event_type,
    transaction_reference,
    event_data,
):
    # -----------------------------------------
    # 1️⃣ اختيار Endpoint
    # -----------------------------------------

    dispatch = prepare_webhook_dispatch(
        merchant_reference=merchant_reference,
        event_id=event_id,
        event_type=event_type,
        transaction_reference=transaction_reference,
        event_data=event_data,
    )

    if not dispatch["ready"]:
        return {
            "success": False,
            "reason": dispatch["reason"],
        }


    # -----------------------------------------
    # 2️⃣ بناء Payload
    # -----------------------------------------

    payload = build_webhook_payload(
        event_id=event_id,
        event_type=event_type,
        transaction_reference=transaction_reference,
        event_data=event_data,
    )

    webhook_url = dispatch["webhook_url"]

    # -----------------------------------------
    # Secure Secret Retrieval
    # -----------------------------------------
    endpoint = get_webhook_endpoint(
        dispatch["endpoint_id"],
        merchant_reference,
    )

    if endpoint is None:
        return {
            "success": False,
            "reason": "Webhook endpoint authorization failed",
        }

    webhook_secret = endpoint["webhook_secret"]


    # -----------------------------------------
    # 3️⃣ إنشاء Signature
    # -----------------------------------------

    payload_body = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":")
    )

    signature = sign_payload(
        payload_body,
        webhook_secret
    )


    # -----------------------------------------
    # 4️⃣ Webhook Idempotency
    # -----------------------------------------

    existing_delivery = (
        get_delivery_by_event_endpoint(
            event_id=event_id,
            webhook_endpoint_id=dispatch["endpoint_id"],
        )
    )

    # Same event + same endpoint already succeeded.
    # Never send it again.
    if (
        existing_delivery is not None
        and existing_delivery["status"] == "success"
    ):

        return {
            "success": True,
            "delivery_id": existing_delivery["id"],
            "attempts": existing_delivery["attempts"],
            "response_status": existing_delivery["response_status"],
            "webhook_url": webhook_url,
            "event_id": event_id,
            "transaction_reference": transaction_reference,
            "idempotent": True,
            "already_delivered": True,
        }


    # -----------------------------------------
    # 5️⃣ إنشاء أو إعادة استخدام Delivery Log
    # -----------------------------------------

    if existing_delivery is not None:

        # Existing failed/pending delivery.
        # Reuse the same Delivery record.
        delivery_id = existing_delivery["id"]
        attempts = existing_delivery["attempts"]

    else:

        # First delivery for this event + endpoint.
        delivery_id = create_delivery_log(
            event_id=event_id,
            transaction_reference=transaction_reference,
            webhook_endpoint_id=dispatch["endpoint_id"],
            webhook_url=webhook_url,
            payload=payload,
            signature=signature,
        )

        attempts = 0


    # -----------------------------------------
    # 6️⃣ Delivery + Retry
    # -----------------------------------------

    final_result = None

    while attempts < MAX_WEBHOOK_ATTEMPTS:

        attempts += 1

        result = send_webhook(
            webhook_url=webhook_url,
            payload=payload,
            webhook_secret=webhook_secret,
        )

        final_result = result

        if result["success"]:

            update_delivery_log(
                delivery_id=delivery_id,
                status="success",
                attempts=attempts,
                response_status=result["status_code"],
                error_message=None,
            )

            break

        update_delivery_log(
            delivery_id=delivery_id,
            status="failed",
            attempts=attempts,
            response_status=result["status_code"],
            error_message=result.get("error"),
        )

        if should_retry(
            attempts,
            result["success"]
        ):

            time.sleep(
                get_retry_delay(attempts)
            )

        else:
            break


    # -----------------------------------------
    # 6️⃣ النتيجة النهائية
    # -----------------------------------------

    final_log = get_delivery_log(
        delivery_id
    )

    return {
        "success": final_log["status"] == "success",
        "delivery_id": delivery_id,
        "attempts": final_log["attempts"],
        "response_status": final_log["response_status"],
        "webhook_url": webhook_url,
        "event_id": event_id,
        "transaction_reference": transaction_reference,
    }
