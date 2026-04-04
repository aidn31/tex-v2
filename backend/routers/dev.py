import logging
import os

from fastapi import APIRouter, HTTPException, Request

from services.clerk import verify_clerk_jwt
from services.db import get_connection

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/seed-user")
async def seed_user(request: Request):
    """Dev-only: create a user row from the Clerk JWT.

    Replaces the webhook flow in local development where ngrok URLs
    are unreliable. In production this route returns 404.
    """
    if os.environ.get("ENVIRONMENT") != "development":
        raise HTTPException(status_code=404)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ", 1)[1]
    payload = await verify_clerk_jwt(token)

    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

    # Clerk JWTs may not carry email — fall back to empty string.
    # The webhook handler will fill it in if it ever fires.
    email = payload.get("email", "")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO users (clerk_id, email) VALUES (%s, %s) "
                "ON CONFLICT (clerk_id) DO NOTHING",
                (clerk_id, email),
            )
            conn.commit()
            cur.execute(
                "SELECT id, clerk_id, email, is_admin, reports_used, report_credits, "
                "stripe_customer_id, deleted_at, created_at "
                "FROM users WHERE clerk_id = %s",
                (clerk_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=500, detail="Failed to create or fetch user")

    return {
        "id": row[0],
        "clerk_id": row[1],
        "email": row[2],
        "is_admin": row[3],
        "reports_used": row[4],
        "report_credits": row[5],
        "stripe_customer_id": row[6],
        "deleted_at": str(row[7]) if row[7] else None,
        "created_at": str(row[8]) if row[8] else None,
    }
