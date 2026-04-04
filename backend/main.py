import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import admin, films, reports, roster, teams, webhooks

# Infrastructure vars required at boot — app won't start without these.
# Service-specific vars (Gemini, Stripe, Sentry, Datadog) are validated
# when those services are actually called, not at startup.
REQUIRED_ENV_VARS = [
    "NEON_HOST",
    "NEON_DB",
    "NEON_USER",
    "NEON_PASSWORD",
    "REDIS_URL",
    "CLOUDFLARE_R2_ACCOUNT_ID",
    "CLOUDFLARE_R2_ACCESS_KEY_ID",
    "CLOUDFLARE_R2_SECRET_ACCESS_KEY",
    "CLOUDFLARE_R2_BUCKET_FILMS",
    "CLOUDFLARE_R2_BUCKET_REPORTS",
    "CLERK_SECRET_KEY",
    "CLERK_WEBHOOK_SECRET",
    "ENVIRONMENT",
    "FRONTEND_URL",
]


def validate_env():
    missing = [var for var in REQUIRED_ENV_VARS if not os.environ.get(var)]
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_env()
    yield


app = FastAPI(title="TEX API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ.get("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(films.router, prefix="/films", tags=["films"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(teams.router, prefix="/teams", tags=["teams"])
app.include_router(roster.router, prefix="/roster", tags=["roster"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/health")
async def health():
    return {"status": "ok"}
