import logging
import os

from fastapi import APIRouter, HTTPException, Request
from svix.webhooks import Webhook, WebhookVerificationError

from services.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/clerk")
async def clerk_webhook(request: Request):
    """Handle Clerk user lifecycle webhooks.

    Verifies Svix signature before processing.
    user.created → INSERT INTO users.
    user.deleted → UPDATE users SET deleted_at = now().
    Unhandled event types return 200 (Clerk retries on non-2xx).
    """
    body = await request.body()
    headers = {
        "svix-id": request.headers.get("svix-id", ""),
        "svix-timestamp": request.headers.get("svix-timestamp", ""),
        "svix-signature": request.headers.get("svix-signature", ""),
    }

    try:
        wh = Webhook(os.environ["CLERK_WEBHOOK_SECRET"])
        payload = wh.verify(body, headers)
    except WebhookVerificationError:
        logger.error("Clerk webhook signature verification failed", extra={"body": body.decode(errors="replace")})
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = payload.get("type")
    data = payload.get("data", {})

    try:
        if event_type == "user.created":
            clerk_id = data.get("id")
            email = (
                next(
                    (
                        e["email_address"]
                        for e in data.get("email_addresses", [])
                        if e.get("id") == data.get("primary_email_address_id")
                    ),
                    None,
                )
                or data.get("email_addresses", [{}])[0].get("email_address", "")
            )

            if not clerk_id or not email:
                logger.error("Clerk user.created missing clerk_id or email", extra={"payload": payload})
                raise HTTPException(status_code=400, detail="Missing clerk_id or email")

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO users (clerk_id, email) VALUES (%s, %s) "
                        "ON CONFLICT (clerk_id) DO NOTHING",
                        (clerk_id, email),
                    )
                conn.commit()
            finally:
                conn.close()

        elif event_type == "user.deleted":
            clerk_id = data.get("id")
            if not clerk_id:
                logger.error("Clerk user.deleted missing clerk_id", extra={"payload": payload})
                raise HTTPException(status_code=400, detail="Missing clerk_id")

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE users SET deleted_at = now(), updated_at = now() "
                        "WHERE clerk_id = %s AND deleted_at IS NULL",
                        (clerk_id,),
                    )
                conn.commit()
            finally:
                conn.close()

    except HTTPException:
        raise
    except Exception:
        logger.exception("Clerk webhook handler error", extra={"event_type": event_type, "payload": payload})
        raise HTTPException(status_code=500, detail="Internal webhook processing error")

    # Return 200 for all event types (including ones we don't handle)
    # so Clerk does not retry them.
    return {"status": "ok"}
