import os
import time

import httpx
import jwt
from fastapi import Depends, HTTPException, Request

from services.db import get_connection

# Clerk JWKS endpoint — public keys used to verify JWT signatures
CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"

# Cache JWKS for 1 hour to avoid fetching on every request
_jwks_cache: dict = {"keys": None, "fetched_at": 0}
JWKS_CACHE_TTL = 3600


async def _fetch_jwks() -> dict:
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < JWKS_CACHE_TTL:
        return _jwks_cache["keys"]

    async with httpx.AsyncClient() as client:
        response = await client.get(
            CLERK_JWKS_URL,
            headers={"Authorization": f"Bearer {os.environ['CLERK_SECRET_KEY']}"},
        )
        response.raise_for_status()

    jwks_data = response.json()
    _jwks_cache["keys"] = jwks_data
    _jwks_cache["fetched_at"] = now
    return jwks_data


async def verify_clerk_jwt(token: str) -> dict:
    """Verify a Clerk JWT and return the decoded payload.

    Returns dict with 'sub' (clerk_id), plus any other Clerk claims.
    Raises HTTPException 401 if the token is invalid or expired.
    """
    try:
        jwks_data = await _fetch_jwks()
        public_keys = {}
        for key_data in jwks_data.get("keys", []):
            kid = key_data["kid"]
            public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(key_data)

        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        if kid not in public_keys:
            # Key not found — force refresh JWKS in case keys rotated
            _jwks_cache["keys"] = None
            jwks_data = await _fetch_jwks()
            for key_data in jwks_data.get("keys", []):
                public_keys[key_data["kid"]] = jwt.algorithms.RSAAlgorithm.from_jwk(
                    key_data
                )
            if kid not in public_keys:
                raise HTTPException(status_code=401, detail="Invalid token signing key")

        payload = jwt.decode(
            token,
            key=public_keys[kid],
            algorithms=["RS256"],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
    except httpx.HTTPError:
        raise HTTPException(status_code=503, detail="Auth service unavailable")


async def get_current_user(request: Request) -> dict:
    """FastAPI dependency — extracts and verifies Clerk JWT, returns user row from DB.

    Usage in a route:
        @router.get("/something")
        async def something(user: dict = Depends(get_current_user)):
            user_id = user["id"]
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")

    token = auth_header.split(" ", 1)[1]
    payload = await verify_clerk_jwt(token)
    clerk_id = payload.get("sub")
    if not clerk_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing sub claim")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, clerk_id, email, is_admin, reports_used, report_credits, "
                "stripe_customer_id, deleted_at, created_at "
                "FROM users WHERE clerk_id = %s AND deleted_at IS NULL",
                (clerk_id,),
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="User not found")

    return {
        "id": row[0],
        "clerk_id": row[1],
        "email": row[2],
        "is_admin": row[3],
        "reports_used": row[4],
        "report_credits": row[5],
        "stripe_customer_id": row[6],
        "deleted_at": row[7],
        "created_at": row[8],
    }
