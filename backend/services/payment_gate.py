"""Payment gate — decides whether a user can generate a report for free,
using a credit, or must go through Stripe checkout.

Used by:
  - POST /reports (task 3.12) — to decide whether to return a report_id or a
    Stripe checkout URL.
  - routers/stripe.py webhook (task 3.2) — to consume the stripe entitlement
    after checkout.session.completed is received.

Per SCHEMA.md and CLAUDE.md PAYMENT RULES:
  - First report free per account (users.reports_used == 0)
  - Credits (users.report_credits > 0) skip Stripe entirely
  - Otherwise Stripe checkout is required
"""

from services.db import get_connection


FREE = "free"
CREDIT = "credit"
STRIPE_REQUIRED = "stripe_required"


def check_payment_gate(user_id: str) -> str:
    """Return which payment path applies for the given user.

    Reads a fresh user row — never trust a cached value from the JWT flow,
    because reports_used and report_credits change asynchronously from
    webhook handlers.
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT reports_used, report_credits FROM users "
                "WHERE id = %s AND deleted_at IS NULL",
                (user_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise ValueError(f"User not found or deleted: {user_id}")

    reports_used, report_credits = row
    if reports_used == 0:
        return FREE
    if report_credits > 0:
        return CREDIT
    return STRIPE_REQUIRED


def consume_entitlement(cur, user_id: str, path: str) -> None:
    """Update the users row to reflect that an entitlement was consumed.

    Must be called inside the caller's transaction (takes a cursor, not a
    connection) so the update is atomic with whatever else the caller is
    writing — typically the reports row insert.

    - free:   increment reports_used
    - credit: increment reports_used AND decrement report_credits
    - stripe: increment reports_used (the money was already taken by Stripe)

    reports_used is never decremented per SCHEMA.md — even on failure.
    Failure compensation happens via report_credits grants elsewhere.
    """
    if path == FREE:
        cur.execute(
            "UPDATE users SET reports_used = reports_used + 1, updated_at = now() "
            "WHERE id = %s",
            (user_id,),
        )
    elif path == CREDIT:
        # Guard against racing concurrent requests — only consume if credit > 0
        cur.execute(
            "UPDATE users SET reports_used = reports_used + 1, "
            "report_credits = report_credits - 1, updated_at = now() "
            "WHERE id = %s AND report_credits > 0",
            (user_id,),
        )
        if cur.rowcount == 0:
            raise ValueError(
                f"User {user_id} has no credits to consume — race or stale gate check"
            )
    elif path == STRIPE_REQUIRED:
        cur.execute(
            "UPDATE users SET reports_used = reports_used + 1, updated_at = now() "
            "WHERE id = %s",
            (user_id,),
        )
    else:
        raise ValueError(f"Unknown payment path: {path}")
