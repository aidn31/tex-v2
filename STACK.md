# STACK.md — TEX v2

Complete tool inventory. Every layer. Every version. Every configuration decision.
Read this before installing anything, writing any configuration, or making any infrastructure decision.
The stack is locked. Deviations require Tommy's explicit approval and a DECISIONS.md entry.

---

## STACK OVERVIEW

```
Layer               Tool                    Version     Role
────────────────────────────────────────────────────────────────────────────────────
Frontend            Next.js                 15.x        App Router. UI and routing.
Styling             Tailwind CSS            3.x         Utility classes. Not used in PDF.
Auth                Clerk                   latest      JWTs, user lifecycle, webhooks.
Payments            Stripe                  latest      Checkout sessions + webhooks.
Frontend Deploy     Vercel                  —           Auto-deploy from main. Preview from branches.
Product Analytics   PostHog                 latest      Frontend event tracking.
─────────────────────────────────────────────
Backend             FastAPI                 0.115.x     HTTP API. Validates, routes, enqueues.
Language            Python                  3.12        Workers and API. Same version everywhere.
Task Queue          Celery                  5.x         4 queues. Chord for parallel sections.
Message Broker      Redis                   7.x         Celery broker + result backend only.
PDF                 WeasyPrint              62.x        Print-optimized PDF from HTML+CSS.
Validation          Pydantic                2.x         All request/response models.
Error Tracking      Sentry                  latest      All unhandled exceptions. film/report/user context.
APM                 Datadog                 latest      Infrastructure metrics. Custom tex.* metrics.
─────────────────────────────────────────────
Database            Neon PostgreSQL          16          Raw SQL. No ORM. Fresh connection per call.
Film Storage        Cloudflare R2           —           Two buckets: films + reports. Presigned URLs only.
Container Registry  GCP Artifact Registry   —           Docker images for all Cloud Run services.
Backend Deploy      Google Cloud Run        —           5 services. See CLOUD RUN section.
Containerization    Docker                  26.x        Same Dockerfile, different CMD per service.
CI/CD               GitHub Actions          —           Build → push → deploy on merge to main.
─────────────────────────────────────────────
AI — Video          Gemini 2.5 Pro          —           Sections 1-4. Video understanding. No substitute.
AI — Text           Gemini 2.5 Flash        —           Sections 5-6. Primary. Text-in, text-out.
AI — Fallback       Claude 3.5 Sonnet       —           Sections 5-6 only. Auto-triggers when Flash fails.
Video Upload        Gemini File API         —           Developer API today. Vertex AI at scale.
─────────────────────────────────────────────
Future (not v1 of v2):
Vector DB           pgvector (Neon)         —           Installed. Not used. Ready for Phase 3+.
Search              Typesense               —           Not yet. Phase 3+.
Orchestration       LlamaIndex              —           Not yet. Knowledge base. Phase 3+.
```

---

## FRONTEND

### Next.js 15 — App Router

App Router only. No Pages Router. No exceptions.
App Router is required for Server Components, which reduces client bundle size and enables
streaming responses — useful when polling report status for 15-45 minutes.

```
Directory structure (enforced):
frontend/app/
  (auth)/          — Clerk login/signup. No auth middleware here.
  dashboard/       — Coach home. Teams + recent reports.
  teams/[id]/      — Team page. Roster, films, reports.
  reports/[id]/    — Report status + PDF download.
  upload/          — Film upload flow.
  admin/           — Training mode. is_admin gate on every route.
```

**Critical Next.js config:**

```js
// next.config.js
module.exports = {
  output: 'standalone',          // required for Docker builds
  experimental: {
    serverActions: { allowedOrigins: ['*'] }
  }
}
```

`output: 'standalone'` generates a self-contained build that does not need `node_modules` at runtime.
Required for Vercel edge builds. Do not remove.

### Tailwind CSS 3

Theme is locked:

```js
// tailwind.config.js
theme: {
  extend: {
    colors: {
      brand: '#F97316',      // orange — primary actions, active states
      background: '#0a0a0a', // near-black — page background
      surface: '#141414',    // dark card/panel background
      border: '#262626',     // subtle borders
    }
  }
}
```

Tailwind is used only in the frontend. **WeasyPrint does not use Tailwind.** The PDF has its own
static stylesheet at `backend/templates/report.css`. Any Tailwind class in a WeasyPrint template
renders as unstyled text — WeasyPrint has no PostCSS pipeline.

### Clerk

Authentication provider. Handles signup, login, session management, and user webhooks.
Clerk issues JWTs. FastAPI verifies them. No session is stored server-side.

**Frontend integration:**

```ts
// middleware.ts — protects all routes except (auth)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server'

const isPublic = createRouteMatcher(['/sign-in(.*)', '/sign-up(.*)'])

export default clerkMiddleware((auth, req) => {
  if (!isPublic(req)) auth().protect()
})
```

**JWT verification in FastAPI:**

```python
# services/clerk.py
import jwt
import httpx

CLERK_JWKS_URL = "https://api.clerk.com/v1/jwks"

async def verify_clerk_jwt(token: str) -> dict:
    jwks = await fetch_jwks()
    payload = jwt.decode(token, jwks, algorithms=["RS256"])
    return payload   # contains sub (clerk_id), email, etc.
```

**Clerk webhooks (user.created, user.deleted):**
Hit `POST /webhooks/clerk`. Verified with Svix signature before processing.
`user.created` → `INSERT INTO users`. `user.deleted` → `UPDATE users SET deleted_at = now()`.
Never trust a Clerk webhook without verifying the `svix-signature` header.

**Environment variables:**

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY   — frontend
CLERK_SECRET_KEY                    — backend (FastAPI) + frontend (server-side)
CLERK_WEBHOOK_SECRET                — backend Svix verification
```

### Stripe

Payment processing. Checkout sessions only — no custom payment form, no Elements.
Stripe handles PCI compliance. TEX handles business logic.

**What TEX uses:**
- `stripe.checkout.Session.create()` — generates a hosted checkout URL
- `stripe.Webhook.construct_event()` — verifies and parses webhook payloads
- `checkout.session.completed` — the only webhook event TEX acts on at launch

**What TEX does NOT use:**
- Stripe Elements (custom card UI) — adds complexity with no benefit over hosted checkout
- Stripe Billing / subscriptions — subscription tiers are future. pay-per-report at launch.
- Stripe Connect — not a marketplace product

**Stripe Products (create in Stripe Dashboard, not in code):**

```
STARTER:   $49.00 USD one-time     price_id: stored in STRIPE_REPORT_PRICE_ID env var
COACH:     $199.00 USD/month       price_id: stored in STRIPE_COACH_PRICE_ID env var
PROGRAM:   $499.00 USD/month       price_id: stored in STRIPE_PROGRAM_PRICE_ID env var
```

Do not hardcode price IDs. Read from env vars. Price IDs change between test and production.

**Webhook signature verification — mandatory:**

```python
event = stripe.Webhook.construct_event(
    payload=await request.body(),
    sig_header=request.headers["stripe-signature"],
    secret=os.environ["STRIPE_WEBHOOK_SECRET"]
)
# If this raises, return 400 immediately. Never process an unsigned event.
```

### Vercel

Frontend deploy. Automatic on merge to `main`. Preview deploys on every feature branch.
Feature branches → `tex-v2-git-{branch}-{org}.vercel.app`.

**Required Vercel environment variables:**

```
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
NEXT_PUBLIC_API_BASE_URL            # Cloud Run tex-api service URL
NEXT_PUBLIC_POSTHOG_KEY
STRIPE_PUBLISHABLE_KEY
STRIPE_WEBHOOK_SECRET
```

`NEXT_PUBLIC_*` variables are exposed to the browser. Every other variable is server-only.
Never put a secret in a `NEXT_PUBLIC_` variable.

### PostHog

Product analytics. Client-side only. Tracks user behavior, not errors (Sentry handles errors).

**Events to track (complete list at launch):**

```
film_uploaded              { file_size_mb, team_id }
report_generation_started  { film_count, team_id }
report_downloaded          { report_id, generation_time_seconds }
section_error              { section_type, error_reason }
payment_initiated          { tier }
payment_completed          { tier, amount_usd }
```

Initialize once in the root layout. Do not track coach PII — no email, no name.

---

## BACKEND

### FastAPI 0.115

HTTP API layer. No business logic lives here — FastAPI validates, authenticates, and enqueues.
Workers do the work.

**App startup — required lifespan events:**

```python
# main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup: validate all required env vars are present
    validate_env()
    yield
    # shutdown: nothing required — workers close their own connections

app = FastAPI(lifespan=lifespan)
```

`validate_env()` checks every env var in `.env.example` is present. Fails loudly at startup.
A missing `GEMINI_API_KEY` discovered at the first report generation, not at startup, is
a production incident. Fail at boot.

**Router registration:**

```python
app.include_router(films.router, prefix="/films", tags=["films"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(teams.router, prefix="/teams", tags=["teams"])
app.include_router(roster.router, prefix="/roster", tags=["roster"])
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
```

All routes are protected by Clerk JWT verification except `/webhooks/*` (protected by provider signatures).
Admin routes additionally check `is_admin` from the DB — not from the JWT, not from a cache.

**CORS:**

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.environ["FRONTEND_URL"]],  # not "*" in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

Do not use `allow_origins=["*"]` in production. Set `FRONTEND_URL` explicitly.

### Python 3.12

3.12 is required. Not 3.11. Not 3.10. The Dockerfile pins this.

```dockerfile
FROM python:3.12-slim
```

Why 3.12: improved error messages (critical for debugging production failures), performance improvements
in the interpreter, and forward compatibility. This is the same version used in both the FastAPI container
and all Celery worker containers. Mixing Python versions across services causes subtle dependency conflicts.

**Required system packages (installed in Dockerfile):**

```dockerfile
RUN apt-get update && apt-get install -y \
    ffmpeg \          # film processing — not pip-installable
    libpango-1.0-0 \  # WeasyPrint PDF rendering
    libpangoft2-1.0-0 \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*
```

`ffmpeg` is the actual binary, not the Python wrapper. FFprobe is included with ffmpeg.
WeasyPrint's system dependencies are `libpango` — missing them causes silent PDF failures
where WeasyPrint runs but produces malformed output. Verify with a test PDF on every fresh build.

**Python dependencies (`requirements.txt`):**

```
fastapi==0.115.*
uvicorn[standard]==0.32.*
celery[redis]==5.4.*
redis==5.2.*
psycopg2-binary==2.9.*
pydantic==2.9.*
google-generativeai==0.8.*      # Gemini Developer API — flip to vertexai at scale
anthropic==0.36.*               # Claude fallback for sections 5-6
stripe==11.*
clerk-backend-api==1.*
svix==1.*                       # Clerk webhook signature verification
weasyprint==62.*
boto3==1.35.*                   # Cloudflare R2 (S3-compatible API)
sentry-sdk[fastapi]==2.*
ddtrace==2.*                    # Datadog APM
python-multipart==0.0.*         # FastAPI form data
python-dotenv==1.*              # local dev only
```

Pin to minor versions (`0.115.*`), not patch. Patch updates are safe to pull automatically.
Minor version bumps require a test run before deploying.

### Celery 5 + Redis 7

Celery is the task queue. Redis is the broker (message bus) and result backend.
Redis stores nothing else — no application state, no session data, no cache.

**Celery app configuration:**

```python
# tasks/celery_app.py
from celery import Celery

celery_app = Celery(
    "tex",
    broker=os.environ["REDIS_URL"],
    backend=os.environ["REDIS_URL"],
    include=[
        "tasks.film_processing",
        "tasks.report_generation",
        "tasks.section_generation",
        "tasks.notifications",
    ]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,       # report_id.status = STARTED in Redis immediately
    task_acks_late=True,           # task acknowledged only after completion, not on pickup
    worker_prefetch_multiplier=1,  # one task per worker slot — prevents starvation
)
```

**`task_acks_late=True` is critical.** Without it, a worker that crashes mid-task has already
acknowledged the task from Redis — the task vanishes. With late ack, a crashed worker causes
the task to return to the queue for retry. Required for the film_processing queue where crashes
during FFmpeg or Gemini upload must re-queue, not silently disappear.

**`worker_prefetch_multiplier=1` is critical.** With the default prefetch of 4, a single slow
film_processing task ties up 4 acknowledgement slots on the worker. Other tasks wait even though
the worker has capacity. Set to 1: each worker takes exactly one task at a time.

**Queue definitions:**

```python
from kombu import Queue

celery_app.conf.task_queues = (
    Queue("film_processing"),
    Queue("report_generation"),
    Queue("section_generation"),
    Queue("notifications"),
)
celery_app.conf.task_default_queue = "notifications"  # fail-safe default
```

The `section_generation` queue is the only queue that runs multiple concurrent tasks on the same worker.
This is by design — during report generation, sections 1-4 run as a chord, all 4 dispatched
to `section_generation` simultaneously. Workers on this queue are configured with `--concurrency=4`.
Film processing workers use `--concurrency=1` — one film per worker, full CPU for FFmpeg.

**Timeout values (replicated here for quick reference — authoritative source is AGENTS.md):**

```
Queue                 soft_time_limit   time_limit   concurrency
────────────────────────────────────────────────────────────────
film_processing       55 min (3300s)    60 min       1
report_generation     25 min (1500s)    30 min       1
section_generation    8 min  (480s)     10 min       4
notifications         25 sec            30 sec       2
```

### Redis 7 — Configuration

Redis is used as Celery broker and result backend only.
It stores task state and enqueued messages. Nothing else lives here.

**Mandatory configuration (`redis.conf`):**

```
appendonly yes              # AOF persistence — tasks queued but not picked up survive restart
appendfsync everysec        # flush to disk every second — durability without sync overhead
maxmemory 512mb             # set a limit — without this Redis will OOM the container
maxmemory-policy allkeys-lru # evict LRU keys when maxmemory reached
```

AOF (Append Only File) persistence is not optional. Redis without AOF loses every queued task
on restart. At tournament weekend when a coach has 10 reports queued, a Redis restart without
AOF means 10 silent job losses. With AOF, Redis replays the log on startup and recovers the queue.

AOF alone does not protect against a corrupted Redis or a replaced instance. The DB-based
startup recovery function in every worker handles that. Both mechanisms are required.

**Connection string format:**

```
REDIS_URL=redis://:password@hostname:6379/0
```

Use database index 0 for Celery. Do not share the Celery database index with any other use.

### WeasyPrint 62

HTML → PDF conversion. Python native. No headless browser, no Puppeteer, no Chrome.

WeasyPrint renders the HTML template at `backend/templates/report.html` using the print
stylesheet at `backend/templates/report.css`. It does not use Tailwind. It does not accept
inline JavaScript. It is a print-optimized CSS renderer.

**Why WeasyPrint instead of Puppeteer/Playwright:**
Puppeteer requires a headless Chrome install inside the Docker container (~300MB), adds a
browser process to manage, and introduces JavaScript execution surface in a worker that
handles sensitive coach data. WeasyPrint is a pure Python library with no browser dependency,
smaller container footprint, and simpler failure modes. It also produces more predictable
PDF pagination since it implements CSS print rules directly.

**Required CSS rules in `report.css`:**

```css
@page {
  size: Letter;
  margin: 0.75in;
}

.page-break {
  page-break-before: always;
}

/* Player pages — one player per printed page */
.player-page {
  page-break-inside: avoid;
}

/* Print-safe font stack — WeasyPrint embeds fonts */
body {
  font-family: 'DejaVu Sans', Arial, sans-serif;
  font-size: 11pt;
  line-height: 1.5;
  color: #000000;    /* black on white — this is a printed document */
}
```

The PDF is printed and used on a clipboard. Black text on white background. High contrast.
No dark theme. No background images. No gradients. Every style decision serves the printed page.

**Invocation pattern:**

```python
# services/pdf.py
from weasyprint import HTML, CSS

def assemble_pdf(sections: dict, team_name: str, report_date: str) -> bytes:
    html_content = render_template("report.html", sections=sections,
                                   team_name=team_name, report_date=report_date)
    css = CSS(filename="backend/templates/report.css")
    pdf_bytes = HTML(string=html_content).write_pdf(stylesheets=[css])
    return pdf_bytes
```

`write_pdf()` returns bytes directly. Write those bytes to /tmp, then upload to R2.
Do not write to disk and read back — keep it in memory unless the file is >50MB (it won't be).

---

## DATABASE — Neon PostgreSQL 16

### Connection Model

```python
# services/db.py — the entire database layer. nothing else.
import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        database=os.environ["NEON_DB"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require",
        connect_timeout=10
    )
```

Open connection → execute → close. Every call. No connection pooling at the application layer.
No SQLAlchemy connection pool. No persistent connection objects. Every function that needs the DB
receives a connection as a parameter or opens one, uses it, and closes it in a `with` block.

```python
# correct pattern — used everywhere
def fetch_film(conn, film_id: str, user_id: str) -> dict:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM films WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
            (film_id, user_id)
        )
        return cur.fetchone()

# how it's called from a task
with get_connection() as conn:
    film = fetch_film(conn, film_id, user_id)
# connection closes when the `with` block exits
```

**Why no connection pool:** Celery workers are long-running processes that spend most of their
time doing FFmpeg or waiting on Gemini. A connection held during that idle time consumes a Neon
connection slot for nothing. Neon's free tier has 5 connection slots. Even paid tiers have limits.
Fresh-per-call is the correct pattern for this workload — bursty DB access interspersed with
long non-DB work.

### SQL Rules

- Raw SQL only. No SQLAlchemy. No Tortoise. No Prisma.
- Parameterized queries only — `%s` placeholders. No string interpolation into SQL. Ever.
- Every query on a user-facing table includes `WHERE user_id = %s`.
- `user_id` always comes from `verify_clerk_jwt()`. Never from the request body.
- Never write a query without explicitly listing the columns returned — no `SELECT *` in production code.

### Migrations

Numbered raw SQL files in `backend/migrations/`. Applied in order by `scripts/migrate.py`.

```
backend/migrations/
  001_create_users.sql
  002_create_teams.sql
  003_create_films.sql
  004_create_film_chunks.sql
  005_create_reports.sql
  006_create_report_sections.sql
  007_create_corrections.sql
  008_create_film_analysis_cache.sql
  009_create_dead_letter_tasks.sql
  010_create_notifications.sql
  011_create_payments.sql
  012_install_pgvector.sql     # pgvector installed now. not used until Phase 3.
```

Apply to Neon dev branch for development. Apply to production only after testing on dev.
Never run migrations against production directly — apply to dev branch, verify, then promote.

Neon supports branch-based migrations (like Git for databases). Create a branch, run the
migration, test it, merge to main. This is the correct workflow for schema changes.

### pgvector

Installed at migration 012. Not queried in v1 of v2.
The `CREATE EXTENSION IF NOT EXISTS vector;` runs now so Phase 3 (player embeddings)
adds columns to existing tables without a new extension migration.

```sql
-- 012_install_pgvector.sql
CREATE EXTENSION IF NOT EXISTS vector;
```

---

## FILE STORAGE — Cloudflare R2

### Two Buckets

```
tex-films-{env}     — raw uploads + FFmpeg chunks. private. no public access.
tex-reports-{env}   — generated PDF reports. private. no public access.
```

`{env}` is `dev` or `prod`. Never share buckets between environments.

### Access Pattern

All access via presigned URLs. The browser never sees R2 credentials.
FastAPI generates presigned URLs. R2 credentials live only in Cloud Run secrets.

```python
# services/r2.py
import boto3  # R2 uses the S3-compatible API

def get_r2_client():
    return boto3.client(
        "s3",
        endpoint_url=f"https://{os.environ['CLOUDFLARE_R2_ACCOUNT_ID']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ["CLOUDFLARE_R2_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["CLOUDFLARE_R2_SECRET_ACCESS_KEY"],
        region_name="auto"
    )

def generate_presigned_upload_url(bucket: str, key: str, expiry_seconds: int = 3600) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_seconds
    )

def generate_presigned_read_url(bucket: str, key: str, expiry_seconds: int = 900) -> str:
    client = get_r2_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=expiry_seconds
    )
```

**Presigned URL expiry:**
- Upload URLs: 3600 seconds (1 hour) — large film files on slow connections can take this long
- Download URLs: 900 seconds (15 minutes) — coach clicks download, short-lived URL is enough
- Chunk re-upload URLs (internal, worker): 300 seconds (5 minutes)

**R2 key naming:**

```
films/{user_id}/{film_id}/{original_filename}          # raw upload. permanent.
chunks/{film_id}/chunk_{index:03d}.mp4                 # FFmpeg chunks. until report = complete.
reports/{user_id}/{report_id}/scouting_report.pdf      # final PDF. permanent.
```

R2 chunks are deleted only after `reports.status = complete`. This is enforced in code —
`delete_r2_chunks()` is called only inside the `generate_report` task after the status update,
never before. R2 is the re-upload source when Gemini file URIs expire.

**Environment variables:**

```
CLOUDFLARE_R2_ACCOUNT_ID
CLOUDFLARE_R2_ACCESS_KEY_ID
CLOUDFLARE_R2_SECRET_ACCESS_KEY
CLOUDFLARE_R2_BUCKET_FILMS          # tex-films-{env}
CLOUDFLARE_R2_BUCKET_REPORTS        # tex-reports-{env}
```

---

## AI PROVIDERS

### Gemini 2.5 Pro — Sections 1-4

Video understanding. Native basketball film analysis. No substitute.

```python
# services/ai/gemini.py
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

PRO_MODEL = "gemini-2.5-pro"
FLASH_MODEL = "gemini-2.5-flash"
```

**Developer API vs Vertex AI:**

```
GEMINI_BACKEND = "developer_api"    # today — genai SDK, File API for uploads
GEMINI_BACKEND = "vertex"           # at scale — vertexai SDK, GCS for uploads
```

The `gemini.py` provider handles this switch internally. The rest of the system never sees
the difference. The migration happens when:
1. Monthly Gemini spend exceeds Developer API limits
2. Vertex AI's committed use discounts make it materially cheaper
3. GCS integration for chunk uploads becomes operationally simpler than File API management

At Vertex AI, chunk files go to Google Cloud Storage instead of the File API. The 48-hour
expiry problem disappears — GCS files are permanent until deleted. The expiry check and
re-upload logic in `get_valid_chunk_uris()` becomes a no-op but stays in the codebase
because the abstraction is clean and removing it is not worth the risk.

**Context caching — how it's created:**

```python
# Called by orchestrator before chord fires — ONCE per report
def create_context_cache(self, chunk_uris: list[str], roster_text: str) -> str:
    model = genai.GenerativeModel(PRO_MODEL)
    cache = genai.caching.CachedContent.create(
        model=PRO_MODEL,
        contents=[
            *[genai.upload_file(uri) for uri in chunk_uris],
            roster_text
        ],
        ttl=datetime.timedelta(hours=1)  # enough for 4 parallel sections to complete
    )
    return cache.name   # URI passed to all 4 section tasks
```

Cache TTL is 1 hour. Sections 1-4 combined take 8-15 minutes. 1 hour provides headroom
for retries without letting the cache accumulate cost beyond the report window.

**Rate limiting — Redis token bucket (required before every Gemini call):**

```python
# services/ai/gemini.py
RATE_LIMITS = {
    PRO_MODEL:   3,     # requests per minute — update when quota increases
    FLASH_MODEL: 15,    # requests per minute — Flash has higher quota
}

def acquire_gemini_slot(model: str):
    key = f"rate_limit:{model}"
    limit = RATE_LIMITS[model]
    while True:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)
        if count <= limit:
            return
        time.sleep(2 + random.uniform(0, 1))  # jitter prevents thundering herd at scale
```

Every Gemini call acquires a slot before executing. The token bucket is shared across all
workers and all Cloud Run instances via Redis. This prevents 429 errors at the source.

### Gemini 2.5 Flash — Sections 5-6 (Primary)

Text-in, text-out. Sections 5 and 6 receive sections 1-4 output as text context.
They never receive video. Flash is 10x cheaper than Pro and equivalent quality for this task.

Flash is the primary for sections 5-6. If Flash fails or times out, the fallback fires automatically.

### Claude 3.5 Sonnet — Sections 5-6 (Fallback)

Auto-triggers when Flash fails. No manual intervention. No admin action.

```python
# tasks/section_generation.py
def run_text_section(report_id: str, section_type: str, context: str) -> str:
    prompt = load_prompt(section_type)
    try:
        provider = get_ai_provider()          # Gemini Flash
        return provider.analyze_text(context, prompt, section_type)
    except (GeminiUnavailableError, GeminiTimeoutError) as e:
        log_fallback_event(report_id, section_type, "gemini_flash", "claude_sonnet", str(e))
        fallback = get_fallback_provider()    # Claude 3.5 Sonnet
        return fallback.analyze_text(context, prompt, section_type)
```

`get_fallback_provider()` returns the Anthropic provider unconditionally for text sections.
It is not configurable. The fallback relationship is fixed: Flash → Claude.

The Anthropic provider (`services/ai/anthropic.py`) implements only `analyze_text()` at launch.
`analyze_video()`, `upload_video()`, and `delete_video()` raise `NotImplementedError`.

**Environment variables:**

```
GEMINI_API_KEY
ANTHROPIC_API_KEY
AI_VIDEO_PROVIDER       # "gemini" today — change only via DECISIONS.md entry + Tommy approval
GEMINI_BACKEND          # "developer_api" today — flip to "vertex" at scale
```

### AI Provider Abstraction

Nothing in TEX outside of `services/ai/` imports directly from a provider file.
All calls go through `services/ai/router.py`.

```python
# services/ai/router.py — the only import point for the rest of the codebase
def get_ai_provider() -> AIVideoProvider:
    provider = os.environ.get("AI_VIDEO_PROVIDER", "gemini")
    if provider == "gemini":
        from services.ai.gemini import GeminiProvider
        return GeminiProvider()
    elif provider == "anthropic":
        from services.ai.anthropic import AnthropicProvider
        return AnthropicProvider()
    raise ValueError(f"Unknown AI provider: {provider}")

def get_fallback_provider() -> AIVideoProvider:
    from services.ai.anthropic import AnthropicProvider
    return AnthropicProvider()
```

This means: switching AI provider for sections 1-4 = change one env var + update `gemini.py` if needed.
Switching fallback for sections 5-6 = change one line in `get_fallback_provider()`.
Neither change touches the task definitions, the orchestrator, or the pipeline.

---

## INFRASTRUCTURE

### Google Cloud Run — 5 Services

Each service is a separate Docker image built from the same `backend/` directory with different
entry points. One Dockerfile. Different `CMD` per service.

```
Service Name            Queue                  CMD                                          min  max  memory   /tmp
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
tex-api                 —                      uvicorn main:app --host 0.0.0.0 --port 8080  1    10   2Gi      512MB
tex-worker-film         film_processing        celery -A tasks.celery_app worker            0    5    8Gi      8GB
                                               -Q film_processing --concurrency=1
tex-worker-report       report_generation      celery -A tasks.celery_app worker            0    3    2Gi      512MB
                                               -Q report_generation --concurrency=1
tex-worker-section      section_generation     celery -A tasks.celery_app worker            0    10   2Gi      512MB
                                               -Q section_generation --concurrency=4
tex-worker-notify       notifications          celery -A tasks.celery_app worker            0    3    512Mi    512MB
                                               -Q notifications --concurrency=2
```

**tex-worker-film requires explicit configuration:**

```bash
# Cloud Run deploy command for tex-worker-film
gcloud run deploy tex-worker-film \
  --image gcr.io/tex-prod/tex-worker-film:latest \
  --execution-environment gen2 \
  --memory 8Gi \
  --cpu 4 \
  --ephemeral-storage 8Gi \    # /tmp size — default 512MB is insufficient for film files
  --min-instances 0 \
  --max-instances 5 \
  --no-allow-unauthenticated
```

`--execution-environment gen2` is required for `--ephemeral-storage` to work. gen1 does not
support custom ephemeral storage sizes. Without gen2, the flag is silently ignored and /tmp
defaults to 512MB — a 2-hour film compressed to 720p alone exceeds this.

**tex-api min-instances = 1:**
The API has min-instances set to 1 to avoid cold starts on every request. A coach who clicks
"Generate Report" should not wait 5 seconds for a Cloud Run instance to warm up.
Worker services scale to zero — a cold start on a worker is invisible (task is already queued).

### Docker

Single `Dockerfile` at `backend/Dockerfile`. Different `CMD` per Cloud Run service.

```dockerfile
FROM python:3.12-slim

# system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# CMD is NOT set here — specified per Cloud Run service
# tex-api:           CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
# tex-worker-film:   CMD ["celery", "-A", "tasks.celery_app", "worker", "-Q", "film_processing", "--concurrency=1"]
# etc.
```

**Build and push to Artifact Registry:**

```bash
# GitHub Actions runs this on merge to main
docker build -t us-central1-docker.pkg.dev/tex-prod/tex/backend:${{ github.sha }} ./backend
docker push us-central1-docker.pkg.dev/tex-prod/tex/backend:${{ github.sha }}
```

Tag images by commit SHA. Never use `latest` as the only tag — you lose the ability to roll back.

### GitHub Actions — CI/CD

Trigger: push to `main`. Sequence: test → build → push → deploy.

```yaml
# .github/workflows/deploy.yml
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - name: Authenticate to GCP
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Build and push Docker image
        run: |
          docker build -t $IMAGE_TAG ./backend
          docker push $IMAGE_TAG

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy tex-api --image $IMAGE_TAG ...
          gcloud run deploy tex-worker-film --image $IMAGE_TAG ...
          gcloud run deploy tex-worker-report --image $IMAGE_TAG ...
          gcloud run deploy tex-worker-section --image $IMAGE_TAG ...
          gcloud run deploy tex-worker-notify --image $IMAGE_TAG ...
```

Deploy blocks on test failure. Never deploy untested code. Feature branches are not auto-deployed —
only merges to `main` trigger production deploy. Tommy reviews all PRs before merge.

### Secrets Management

**Backend secrets:** Google Cloud Secret Manager. Cloud Run reads secrets as environment variables at boot.
**Frontend secrets:** Vercel environment variables (encrypted at rest).
**Local dev:** `backend/.env` (gitignored). `.env.example` documents every required variable.

No secret ever lives in a Docker image, a GitHub Actions log, or a committed file.
If a secret is accidentally committed: rotate it immediately, then clean the history.

---

## OBSERVABILITY

### Sentry

Every unhandled exception in FastAPI and every failed Celery task reports to Sentry.
Context required on every error: `film_id`, `report_id`, `user_id`. Without these three
identifiers, debugging a production failure is a guessing game.

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

sentry_sdk.init(
    dsn=os.environ["SENTRY_DSN"],
    integrations=[FastApiIntegration(), CeleryIntegration()],
    traces_sample_rate=0.1,   # 10% of requests get performance traces
    environment=os.environ.get("ENVIRONMENT", "development")
)

# In every task, set context before any work:
with sentry_sdk.push_scope() as scope:
    scope.set_tag("film_id", film_id)
    scope.set_tag("report_id", report_id)
    scope.set_tag("user_id", user_id)
```

### Datadog

Infrastructure metrics and APM. Custom `tex.*` metrics are the cost and performance dashboard.

**Custom metrics (complete list):**

```
tex.film.processing_time_seconds     tagged: film_duration_minutes
tex.report.generation_time_seconds   tagged: section_count, parallel
tex.gemini.tokens_used               tagged: section_type, model, prompt_version
tex.report.cost_usd                  computed from token counts, logged per report
tex.dead_letter.written              tagged: task_name — alert at 3+ per hour
tex.fallback.triggered               tagged: section_type — spike = Flash degradation
tex.cache.hit                        tagged: cache_type (film_fingerprint | context)
tex.cache.miss                       tagged: cache_type
```

`tex.dead_letter.written` alert threshold: 3 events in any 1-hour window.
`tex.fallback.triggered` alert threshold: 5 events in any 1-hour window (Flash may be degraded).

---

## LOCAL DEVELOPMENT

```yaml
# docker-compose.yml
version: '3.9'
services:
  api:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload
    ports: ["8000:8000"]
    env_file: ./backend/.env
    volumes: ["./backend:/app"]  # hot reload

  worker:
    build: ./backend
    command: celery -A tasks.celery_app worker -Q film_processing,report_generation,section_generation,notifications --concurrency=2 --loglevel=info
    env_file: ./backend/.env
    volumes: ["./backend:/app"]
    depends_on: [redis]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    command: redis-server --appendonly yes  # AOF enabled in dev too
```

**Frontend runs outside Docker in local dev:**

```bash
cd frontend && npm run dev    # runs on localhost:3000
```

`NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in frontend `.env.local`.

**No local Neon.** Use Neon's dev branch feature.
Neon dev branches are isolated from production and reset independently.
Create a dev branch in the Neon dashboard. Use its connection string in `backend/.env`.
Never use the production Neon connection string in local dev.

---

## ENVIRONMENT VARIABLE REFERENCE

Complete list. Every variable required at boot. App fails loudly if any are missing.

```
# Neon PostgreSQL
NEON_HOST
NEON_DB
NEON_USER
NEON_PASSWORD

# Redis
REDIS_URL                           # redis://:password@host:6379/0

# AI Providers
GEMINI_API_KEY
ANTHROPIC_API_KEY
AI_VIDEO_PROVIDER                   # "gemini"
GEMINI_BACKEND                      # "developer_api"

# Cloudflare R2
CLOUDFLARE_R2_ACCOUNT_ID
CLOUDFLARE_R2_ACCESS_KEY_ID
CLOUDFLARE_R2_SECRET_ACCESS_KEY
CLOUDFLARE_R2_BUCKET_FILMS
CLOUDFLARE_R2_BUCKET_REPORTS

# Auth
CLERK_SECRET_KEY
CLERK_WEBHOOK_SECRET

# Payments
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_REPORT_PRICE_ID
STRIPE_COACH_PRICE_ID
STRIPE_PROGRAM_PRICE_ID

# Frontend (Vercel)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
NEXT_PUBLIC_API_BASE_URL
NEXT_PUBLIC_POSTHOG_KEY
STRIPE_PUBLISHABLE_KEY

# Observability
SENTRY_DSN
DATADOG_API_KEY

# App
ENVIRONMENT                         # "development" | "production"
FRONTEND_URL                        # used in CORS + Stripe return URLs
BASE_URL                            # same as FRONTEND_URL — used in Stripe metadata
```

---

## WHAT IS NOT IN THE STACK YET

Do not build, install, or configure any of the following until the relevant phase is ready.
Installing a tool before you need it creates maintenance burden with no benefit.

```
Typesense        — full-text search. Phase 3. Not needed before player profile search.
LlamaIndex       — RAG orchestration. Phase 3. Not needed before knowledge base ingestion.
LangChain        — same as LlamaIndex. Phase 3.
pgvector queries — vector DB. Phase 3. Extension is installed. No queries until embeddings exist.
Fine-tuning      — Phase 4. Not needed before 1,000+ labeled corrections exist.
WebSockets       — not needed. Polling every 5 seconds is sufficient for 15-45 minute jobs.
GraphQL          — not needed. REST over FastAPI is the correct level of complexity here.
Kubernetes       — not needed. Cloud Run with Celery handles the workload pattern.
```

---

*Last updated: Phase 0 — Context Engineering*
*All decisions in this document are locked pending explicit Tommy approval for changes.*
