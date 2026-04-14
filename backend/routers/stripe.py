import json
import logging
import os

import stripe as stripe_sdk
from fastapi import APIRouter, Depends, HTTPException, Request

from models.schemas import CheckoutSessionCreate, CheckoutSessionResponse
from services.clerk import get_current_user
from services.db import get_connection
from services.payment_gate import STRIPE_REQUIRED, consume_entitlement
from services.prompts import load_prompt
from services.stripe_client import get_stripe, verify_webhook

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/create-checkout-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    body: CheckoutSessionCreate, user: dict = Depends(get_current_user)
):
    """Create a Stripe Checkout session for a single scouting report.

    Per ARCHITECTURE.md: payment is per-report, not per-credit. The report row
    itself is created later by the webhook handler (Phase 3 task 3.2 wires
    that part). For now this only creates the payment row in 'pending' state
    and the Stripe Checkout session.
    """
    if not body.film_ids:
        raise HTTPException(status_code=400, detail="At least one film_id is required")

    user_id = str(user["id"])
    price_id = os.environ.get("STRIPE_REPORT_PRICE_ID")
    if not price_id:
        raise HTTPException(status_code=500, detail="STRIPE_REPORT_PRICE_ID is not configured")

    base_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")

    # Validate team belongs to the user
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM teams WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
                (body.team_id, user_id),
            )
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Team not found")

            # Validate all films belong to the user and the team
            cur.execute(
                "SELECT id FROM films WHERE id = ANY(%s::uuid[]) AND team_id = %s "
                "AND user_id = %s AND deleted_at IS NULL",
                (body.film_ids, body.team_id, user_id),
            )
            found = {str(r[0]) for r in cur.fetchall()}
            if found != set(body.film_ids):
                raise HTTPException(status_code=404, detail="One or more films not found")
    finally:
        conn.close()

    stripe = get_stripe()

    # Create Stripe customer if the user doesn't have one yet.
    # Customer creation is not strictly required for one-off Checkout in payment
    # mode, but storing the customer_id lets us link future payments to the same
    # Stripe customer record (cleaner Stripe Dashboard, supports later subscription tiers).
    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        try:
            customer = stripe.Customer.create(
                email=user["email"],
                metadata={"tex_user_id": user_id},
            )
        except stripe_sdk.error.StripeError as e:
            logger.exception("Stripe customer create failed", extra={"user_id": user_id})
            raise HTTPException(status_code=502, detail=f"Stripe error: {e.user_message or str(e)}")

        customer_id = customer.id
        conn = get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET stripe_customer_id = %s, updated_at = now() "
                    "WHERE id = %s",
                    (customer_id, user_id),
                )
            conn.commit()
        finally:
            conn.close()

    # Pre-create the payment row so we can put its id in the Checkout metadata.
    # stripe_session_id is NOT NULL UNIQUE, so use a unique placeholder; the
    # webhook handler updates the row to the real session id.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO payments (user_id, stripe_session_id, amount_cents, status) "
                "VALUES (%s, 'pending_' || gen_random_uuid()::text, 0, 'pending') "
                "RETURNING id",
                (user_id,),
            )
            payment_id = str(cur.fetchone()[0])
        conn.commit()
    finally:
        conn.close()

    # Pass tex identifiers in metadata so the webhook can find the row and
    # 3.2/3.3 can build the report. payment_intent_data.metadata is forwarded
    # to the resulting PaymentIntent so payment_intent.payment_failed can find
    # the payment row even before checkout.session.completed fires.
    metadata = {
        "tex_payment_id": payment_id,
        "tex_user_id": user_id,
        "tex_team_id": body.team_id,
        "tex_film_ids": json.dumps(body.film_ids),
    }

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url=f"{base_url}/dashboard?checkout=success",
            cancel_url=f"{base_url}/dashboard?checkout=cancel",
            metadata=metadata,
            payment_intent_data={"metadata": metadata},
        )
    except stripe_sdk.error.StripeError as e:
        logger.exception("Stripe checkout session create failed",
                         extra={"user_id": user_id, "payment_id": payment_id})
        raise HTTPException(status_code=502, detail=f"Stripe error: {e.user_message or str(e)}")

    # Update the payment row with the real session id and amount.
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE payments SET stripe_session_id = %s, amount_cents = %s, "
                "currency = %s, updated_at = now() WHERE id = %s",
                (session.id, session.amount_total or 0,
                 (session.currency or "usd"), payment_id),
            )
        conn.commit()
    finally:
        conn.close()

    return CheckoutSessionResponse(checkout_url=session.url, payment_id=payment_id)


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks. Verifies signature before processing.

    On checkout.session.completed:
      - Update payments row (status='complete', capture payment_intent_id)
      - Create reports row (status='pending')
      - Create report_films join rows for each film in the session metadata
      - Increment users.reports_used via consume_entitlement(path='stripe')
      All in a single DB transaction so partial state is impossible.
    On payment_intent.payment_failed: mark payments row status='failed'.
    """
    body = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = verify_webhook(body, signature)
    except stripe_sdk.error.SignatureVerificationError:
        logger.error("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    except ValueError:
        logger.error("Stripe webhook payload parse failed")
        raise HTTPException(status_code=400, detail="Invalid webhook payload")

    event_type = event["type"]
    data = event["data"]["object"]

    try:
        if event_type == "checkout.session.completed":
            session_id = data["id"]
            payment_intent_id = data.get("payment_intent")
            amount_total = data.get("amount_total") or 0
            currency = data.get("currency") or "usd"
            metadata = data.get("metadata") or {}

            tex_user_id = metadata.get("tex_user_id")
            tex_team_id = metadata.get("tex_team_id")
            tex_film_ids_raw = metadata.get("tex_film_ids")

            if not (tex_user_id and tex_team_id and tex_film_ids_raw):
                # A session completed without our metadata — probably a synthetic
                # `stripe trigger` event. Update the payment row if it exists and
                # return 200 (don't make Stripe retry).
                logger.warning(
                    "Stripe webhook: checkout.session.completed missing tex metadata",
                    extra={"session_id": session_id},
                )
                conn = get_connection()
                try:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE payments SET status = 'complete', "
                            "stripe_payment_intent_id = %s, amount_cents = %s, "
                            "currency = %s, updated_at = now() "
                            "WHERE stripe_session_id = %s",
                            (payment_intent_id, amount_total, currency, session_id),
                        )
                    conn.commit()
                finally:
                    conn.close()
                return {"status": "ok"}

            tex_film_ids = json.loads(tex_film_ids_raw)

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    # 1. Update payment row to complete and capture PI id.
                    cur.execute(
                        "UPDATE payments SET status = 'complete', "
                        "stripe_payment_intent_id = %s, amount_cents = %s, "
                        "currency = %s, updated_at = now() "
                        "WHERE stripe_session_id = %s "
                        "RETURNING id",
                        (payment_intent_id, amount_total, currency, session_id),
                    )
                    payment_row = cur.fetchone()
                    if not payment_row:
                        logger.error(
                            "Stripe webhook: no payment row for session",
                            extra={"session_id": session_id},
                        )
                        conn.rollback()
                        return {"status": "ok"}
                    payment_id = payment_row[0]

                    # 2. Insert reports row.
                    cur.execute(
                        "INSERT INTO reports (user_id, team_id, prompt_version, status) "
                        "VALUES (%s, %s, %s, 'pending') RETURNING id",
                        (tex_user_id, tex_team_id, load_prompt("offensive_sets")[1]),
                    )
                    report_id = str(cur.fetchone()[0])

                    # 3. Insert report_films join rows.
                    for film_id in tex_film_ids:
                        cur.execute(
                            "INSERT INTO report_films (report_id, film_id) VALUES (%s, %s)",
                            (report_id, film_id),
                        )

                    # 4. Link payment row to the report.
                    cur.execute(
                        "UPDATE payments SET report_id = %s, updated_at = now() "
                        "WHERE id = %s",
                        (report_id, payment_id),
                    )

                    # 5. Consume the entitlement — increments users.reports_used.
                    consume_entitlement(cur, tex_user_id, STRIPE_REQUIRED)

                conn.commit()
            finally:
                conn.close()

            # Enqueue the orchestrator. Must happen AFTER the DB transaction
            # commits above — otherwise a worker could pick up the task before
            # the reports row is visible.
            from tasks.report_generation import generate_report
            generate_report.delay(report_id)
            logger.info(
                "Stripe webhook: generate_report enqueued",
                extra={"report_id": report_id, "user_id": tex_user_id},
            )

        elif event_type == "payment_intent.payment_failed":
            payment_intent_id = data["id"]
            metadata = data.get("metadata") or {}
            tex_payment_id = metadata.get("tex_payment_id")

            conn = get_connection()
            try:
                with conn.cursor() as cur:
                    if tex_payment_id:
                        cur.execute(
                            "UPDATE payments SET status = 'failed', "
                            "stripe_payment_intent_id = %s, updated_at = now() "
                            "WHERE id = %s",
                            (payment_intent_id, tex_payment_id),
                        )
                    else:
                        cur.execute(
                            "UPDATE payments SET status = 'failed', updated_at = now() "
                            "WHERE stripe_payment_intent_id = %s",
                            (payment_intent_id,),
                        )
                    if cur.rowcount == 0:
                        logger.error(
                            "Stripe webhook: no payment row for failed PI",
                            extra={"payment_intent_id": payment_intent_id,
                                   "tex_payment_id": tex_payment_id},
                        )
                conn.commit()
            finally:
                conn.close()

        else:
            logger.info("Stripe webhook: unhandled event type",
                        extra={"event_type": event_type})

    except HTTPException:
        raise
    except Exception:
        logger.exception("Stripe webhook handler error",
                         extra={"event_type": event_type})
        raise HTTPException(status_code=500, detail="Internal webhook processing error")

    return {"status": "ok"}
