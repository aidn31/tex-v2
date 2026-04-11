import os

import stripe


def get_stripe() -> "stripe":
    """Return the stripe module configured with the secret key.

    Reads STRIPE_SECRET_KEY at call time (not import time) so the app
    boots in environments where Stripe is not yet configured.
    """
    secret = os.environ.get("STRIPE_SECRET_KEY")
    if not secret:
        raise RuntimeError("STRIPE_SECRET_KEY is not set")
    stripe.api_key = secret
    return stripe


def verify_webhook(payload: bytes, signature: str) -> dict:
    """Verify a Stripe webhook signature and return the parsed event.

    Raises stripe.error.SignatureVerificationError if the signature is invalid.
    """
    secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if not secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET is not set")
    return stripe.Webhook.construct_event(payload, signature, secret)
