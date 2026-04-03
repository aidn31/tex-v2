# ARCHITECTURE.md — TEX v2

Read this before touching any code. This document is the ground truth for how TEX v2 is built and why.
Every decision here has a reason. If a decision seems wrong, ask before changing it.

---

## WHAT THIS SYSTEM DOES

A coach uploads game film. TEX analyzes it with Gemini 2.5 Pro and generates a master PDF scouting report
with 6 sections: offensive sets, defensive schemes, PnR coverage, individual player pages, game plan,
in-game adjustments + practice plan. The coach downloads the PDF. That is the entire product loop.
Every line of code serves that loop. Nothing else.

---

## HIGH-LEVEL SYSTEM DIAGRAM

```
Browser (Next.js / Vercel)
    │
    ├── Auth → Clerk
    ├── Payments → Stripe
    │
    ├── Direct film upload → Cloudflare R2 (presigned URL — backend never touches the bytes)
    │
    └── API calls → FastAPI (Google Cloud Run)
                        │
                        ├── Validates requests
                        ├── Writes job state to PostgreSQL (Neon)
                        ├── Enqueues tasks → Redis
                        │
                        └── Celery Workers (Google Cloud Run — separate service)
                                │
                                ├── Queue: film_processing
                                │       FFmpeg splits → Gemini File API uploads → analysis per chunk
                                │
                                ├── Queue: report_generation
                                │       6 Gemini prompts → sections saved to DB → PDF assembled
                                │
                                └── Queue: notifications
                                        In-app notification written to DB on completion
```

---

## BOUNDARY DECISIONS

**Frontend lives on Vercel. Backend lives on Google Cloud Run. They communicate only via HTTP.**

The frontend (Next.js) does three things: renders UI, calls FastAPI endpoints, and polls for job status.
It does not run business logic. It does not call Gemini. It does not process video.
All computation — FFmpeg, Gemini, PDF generation — happens inside Cloud Run workers.

This boundary is intentional. Vercel's serverless functions have a 10-second execution timeout on the
free/pro tier. A Gemini analysis of a 2-hour game film takes 15–45 minutes. These two things cannot
coexist. The backend must be long-running, containerized, and independently scalable. Cloud Run with
Celery workers is the correct answer. Next.js on Vercel is the correct answer for the UI layer.

**Why Google Cloud Run instead of AWS or a VPS?**
Gemini is a Google product. The Gemini File API and Cloud Run share Google's internal network.
File transfers from Cloud Run to the Gemini File API are faster and cheaper than cross-cloud.
Cloud Run scales to zero between jobs, which matches TEX's usage pattern — bursts of processing
followed by idle periods. A VPS charges 24/7. Cloud Run charges per invocation.

---

## BACKEND: FastAPI

Entry point for all browser → server communication.

```
tex-v2/backend/
├── main.py                  # FastAPI app, router registration, lifespan events
├── routers/
│   ├── films.py             # POST /films/upload-url, POST /films, GET /films/{id}
│   ├── reports.py           # POST /reports, GET /reports/{id}, GET /reports/{id}/sections
│   ├── teams.py             # CRUD for teams
│   ├── roster.py            # CRUD for roster_players
│   ├── webhooks.py          # Stripe webhook handler
│   └── admin.py             # Training mode endpoints — is_admin gate on every route
├── services/
│   ├── db.py                # get_connection() — fresh psycopg2 connection per call
│   ├── r2.py                # generate_presigned_upload_url(), generate_presigned_read_url()
│   ├── ffmpeg.py            # split_film_into_chunks(), get_duration(), compress_for_upload()
│   ├── pdf.py               # assemble_pdf() — takes all 6 sections, returns bytes
│   ├── clerk.py             # verify_clerk_jwt(), extract_clerk_id()
│   └── ai/                  # AI provider abstraction — see AI PROVIDER ABSTRACTION section
│       ├── base.py          # provider interface
│       ├── gemini.py        # Gemini implementation
│       ├── anthropic.py     # Claude fallback for sections 5-6
│       ├── openai.py        # stub
│       └── router.py        # get_ai_provider() — only import point for rest of codebase
├── tasks/
│   ├── celery_app.py        # Celery app instance, queue definitions, Redis broker config
│   ├── film_processing.py   # process_film task — FFmpeg → Gemini File API → chunk analysis
│   ├── report_generation.py # generate_report task — 6 prompts → PDF → R2
│   └── notifications.py     # notify_coach task — writes notification row to DB
├── models/
│   └── schemas.py           # Pydantic models for all request/response bodies
└── prompts/
    ├── offensive_sets.txt
    ├── defensive_schemes.txt
    ├── pnr_coverage.txt
    ├── player_pages.txt
    ├── game_plan.txt
    └── adjustments_practice.txt
```

FastAPI validates all incoming request bodies with Pydantic. No raw dict access in route handlers.
All authentication is JWT-based via Clerk. Every protected route calls `verify_clerk_jwt()` first.
The service role handles DB writes that bypass RLS (Stripe webhooks, Clerk webhooks).

---

## BACKEND: DATABASE (Neon PostgreSQL)

**Why Neon instead of continuing with Supabase?**
v1 had a recurring Supabase connection timeout bug during long Celery operations. Supabase's connection
pooler (PgBouncer in transaction mode) closes idle connections after ~10 minutes. Celery tasks routinely
run longer than that. Neon uses the same PostgreSQL wire protocol and also offers serverless pooling, but
critically: Neon's pooler behavior with psycopg2 direct connections is more predictable under the
long-running async worker pattern. More importantly, the v2 architecture eliminates the bug structurally —
every DB call opens a fresh connection, does its work, and closes. No persistent connection held across
the life of a task.

**Connection rule: open → execute → close. Never hold a connection across a Celery task boundary.**

```python
# db.py — the entire DB layer. 12 lines.
import psycopg2
import os

def get_connection():
    return psycopg2.connect(
        host=os.environ["NEON_HOST"],
        database=os.environ["NEON_DB"],
        user=os.environ["NEON_USER"],
        password=os.environ["NEON_PASSWORD"],
        sslmode="require"
    )
```

All SQL is raw. No ORM. No SQLAlchemy. No Alembic (use raw migration files).
Reason: the schema is known, stable, and small (10 tables). An ORM adds indirection without benefit here.
Raw SQL is readable, explicit, and debuggable. You can paste any query into Neon's console and run it.

pgvector is enabled on Neon for future player tendency embedding search. No embeddings in v1 of v2.
The extension is installed now so the schema migration is clean later.

---

## BACKEND: CELERY + REDIS

Three queues. A fourth — `section_generation` — is used by individual section workers.
Strict separation. Workers can be scaled independently per queue.

```
film_processing      — heavy, long-running. FFmpeg + Gemini File API. can take 15-45 min.
report_generation    — orchestrator only. fires Celery chords. lightweight.
section_generation   — individual section prompts. 4 run simultaneously per report.
notifications        — fast, lightweight. single DB write. completes in <1 second.
```

**Why separate queues?**
A 2-hour film being processed should not block a coach from receiving a notification about a
completed report. Separate queues mean separate workers. Backpressure in one queue does not
propagate to others.

**Task retry policy:**
`film_processing` and `report_generation` tasks retry up to 3 times with exponential backoff
(30s, 120s, 480s). On third failure, task writes `status: error` and `error_message` to the DB,
then enqueues a notification task to alert the coach.

**Task timeouts — every task has a soft and hard limit:**

Without timeouts, a hung FFmpeg process, a stalled R2 download, or a Gemini API partial outage
holds a worker slot forever. At scale a handful of hung tasks silently consume all worker capacity.
New jobs queue behind them. Coaches see reports stuck on "processing" with no error.

`soft_time_limit` — warning. Task catches `SoftTimeLimitExceeded`, writes error status to DB,
cleans up /tmp, then exits. Graceful death.
`time_limit` — hard kill. Celery kills the process immediately. No cleanup. Last resort.

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    soft_time_limit=3300,   # 55 min — begin cleanup
    time_limit=3600,        # 60 min — hard kill
)
def process_film(self, film_id: str):
    tmp_files = []
    try:
        # ... processing work
    except SoftTimeLimitExceeded:
        update_film_status(film_id, "error", "Processing timed out")
        raise
    finally:
        for path in tmp_files:  # always runs — see /TMP CLEANUP section
            if os.path.exists(path):
                os.remove(path)
```

```
Queue                 soft_time_limit   time_limit   reason
─────────────────────────────────────────────────────────────────────
film_processing       55 min            60 min       FFmpeg + 5 chunk uploads
report_generation     25 min            30 min       6 Gemini calls, parallel chord
notifications         25 sec            30 sec       single DB write — 30s means DB is broken
```

The notification timeout being 30 seconds is deliberate. A single DB insert taking that long
signals a broken connection, not a slow task. Surface it immediately.

**Dead letter queue — failed tasks are never silently lost.**

When a task exhausts all retries it writes a full record to the `dead_letter_tasks` table
before dying. No failed job disappears without a trace. Every failure is durable, queryable,
and replayable from the admin UI or a single script call.

Why a DB table instead of a Redis dead letter queue: Redis has no persistence configured.
A Redis dead letter queue loses data on restart. The DB is already the source of truth for
all job state. Failed task context belongs where it is durable and visible.

```sql
CREATE TABLE dead_letter_tasks (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  task_name        text NOT NULL,      -- "process_film" | "generate_report" | "notify_coach"
  task_args        jsonb NOT NULL,     -- full args the task was called with — enables replay
  queue            text NOT NULL,      -- which Celery queue it came from
  error_message    text NOT NULL,      -- the final exception message
  error_traceback  text,               -- full stack trace
  retry_count      integer NOT NULL,   -- how many times it retried before dying
  film_id          uuid,               -- debugging context. null if not film-related.
  report_id        uuid,               -- debugging context. null if not report-related.
  user_id          uuid,               -- which coach was affected
  created_at       timestamptz NOT NULL DEFAULT now(),
  replayed_at      timestamptz,        -- null until manually replayed
  resolved_at      timestamptz         -- null until marked resolved
);
```

Every task's final retry block writes here before dying:

```python
@celery_app.task(bind=True, max_retries=3)
def process_film(self, film_id: str):
    try:
        # ... work
    except Exception as exc:
        if self.request.retries >= self.max_retries:
            write_dead_letter(
                task_name="process_film",
                task_args={"film_id": film_id},
                queue="film_processing",
                error_message=str(exc),
                error_traceback=traceback.format_exc(),
                retry_count=self.request.retries,
                film_id=film_id,
                user_id=get_film_user_id(film_id)
            )
            update_film_status(film_id, "error", str(exc))
            notify_coach_of_failure(film_id)
        raise self.retry(exc=exc)
```

Replay any failed job with its original arguments — one function call, no reconstruction:

```python
def replay_dead_letter_task(dead_letter_id: str):
    task = fetch_dead_letter(dead_letter_id)
    celery_app.send_task(task["task_name"], kwargs=task["task_args"])
    mark_dead_letter_replayed(dead_letter_id)
```

Datadog alert: `tex.dead_letter.written` tagged by `task_name`. Alert fires if more than
3 dead letter events occur in any 1-hour window. That threshold distinguishes a one-off
failure from a systemic issue. One failure is noise. Three in an hour is a pattern.

---

**Task idempotency:**

Every task checks the current job status in the DB before executing. If status is already `complete`,
the task returns immediately. This prevents duplicate processing if a task is accidentally enqueued twice.

```python
# pattern used in every task
def process_film(film_id: str):
    with get_connection() as conn:
        film = fetch_film(conn, film_id)
    if film["status"] == "complete":
        return  # already done, exit cleanly
    # ... rest of processing
```

**Redis:** Used only as Celery broker and result backend. Not used as application cache.
No application state stored in Redis. Redis is ephemeral by default — if Redis restarts
without persistence configured, every queued task that hasn't been picked up vanishes.
Two fixes are required. Both are mandatory.

**Fix 1 — AOF persistence:**
Redis must be configured with `appendonly yes`. Every write to Redis is appended to disk
in real time. On restart, Redis replays the log and recovers its queue state. Tasks queued
but not yet picked up survive the restart. This is one line in redis.conf and is the standard
production configuration for any Redis instance handling work queues.

```
# redis.conf
appendonly yes
appendfsync everysec   # flush to disk every second — balance of durability and performance
```

**Fix 2 — DB-based startup recovery:**
AOF protects against clean restarts. It does not protect against a corrupted Redis instance,
a Redis replacement, or a lost AOF log. The DB is always the source of truth for job state.
Every worker runs a startup recovery function before accepting new tasks:

```python
def recover_stuck_jobs():
    """
    Runs on every worker startup.
    Finds jobs that are active in the DB but have no running task.
    Re-enqueues them. Safe to run multiple times — task idempotency prevents
    duplicate processing.
    """
    with get_connection() as conn:
        # films stuck in processing for more than 2 hours
        # (2x the 60-minute hard timeout — definitely stuck, not just slow)
        stuck_films = conn.execute("""
            SELECT id FROM films
            WHERE status = 'processing'
            AND updated_at < now() - interval '2 hours'
        """).fetchall()

        for film in stuck_films:
            process_film.delay(film["id"])

        # reports stuck in processing for more than 1 hour
        # (2x the 30-minute hard timeout)
        stuck_reports = conn.execute("""
            SELECT id FROM reports
            WHERE status = 'processing'
            AND updated_at < now() - interval '1 hour'
        """).fetchall()

        for report in stuck_reports:
            generate_report.delay(report["id"])
```

The time thresholds are 2x each task's hard timeout — long enough that a slow-but-running
task is never mistakenly re-enqueued, short enough that a genuinely stuck job gets recovered
within hours. Task idempotency (every task checks DB status before executing) prevents
duplicate processing if a task is re-enqueued while the original is still running.

Together AOF + startup recovery mean: Redis data loss from any cause cannot result in
silently lost coach jobs. The worst case is a job gets re-enqueued and runs twice.
Idempotency makes that safe.

---

## FILM PROCESSING PIPELINE

This is the most complex part of the system. Understand this completely.

```
1.  Browser requests presigned upload URL from FastAPI
2.  Browser uploads film directly to Cloudflare R2 (FastAPI never touches the bytes)
3.  Browser POSTs film metadata to FastAPI (r2_key, file_name, file_size, team_id)
4.  FastAPI writes films row with status: uploaded, enqueues process_film task

── TASK: process_film (film_processing queue) ──────────────────────────────────
5.  Worker downloads film from R2 to /tmp, computes SHA-256 hash
6.  Cache check: if film_analysis_cache has a row for this hash + prompt_version,
    jump to step 15 (cache hit — skip all processing)
7.  FFprobe validation: valid container, has video stream, 60s–3hr duration
8.  If file > 1.8GB: FFmpeg compress to H.264 720p
9.  FFmpeg split into 20-25 min chunks (segment_time=1500):
    output: /tmp/{film_id}_chunk_{index:03d}.mp4
10. For each chunk (sequential):
    a. Upload chunk to R2 at chunks/{film_id}/chunk_{index:03d}.mp4
    b. INSERT INTO film_chunks (film_id, chunk_index, r2_chunk_key, gemini_file_state='uploading')
11. Enqueue extract_chunk tasks for ALL chunks simultaneously (parallel group):
    group(extract_chunk.s(film_id, chunk_id, chunk_index) for each chunk).apply_async()
    process_film's work ends here — it does NOT wait for extractions to complete.
12. UPDATE films SET status = 'chunks_uploaded'

── TASK: extract_chunk × N (film_processing queue, parallel) ───────────────────
13. Each extract_chunk worker (one per chunk, running in parallel):
    a. Downloads chunk from R2 to /tmp, uploads to Gemini File API
    b. Polls until gemini_file_state = ACTIVE
    c. Runs Prompt 0A (chunk_extraction) against this chunk's Gemini URI
    d. Saves extraction_output to film_chunks row
    e. If this is the last chunk to complete (atomic advisory lock check):
       enqueue run_chunk_synthesis.delay(film_id)

── TASK: run_chunk_synthesis (film_processing queue) ───────────────────────────
14. Fetches all extraction_outputs from film_chunks for this film
    Runs Prompt 0B (chunk_synthesis, Gemini 2.5 Pro) — text-only, no video
    Writes synthesis_document to film_analysis_cache
    UPDATE films SET status = 'processed'
    If a pending report is cleared for generation (payment confirmed or free/credit path):
    enqueue generate_report.delay(report_id)  ← see AGENTS.md for payment gate logic

15. (Cache hit path) UPDATE films SET status = 'processed'
    Cached synthesis_document and sections used at report generation — no Gemini calls needed.
```

**Why 20-25 minute chunks?**
Gemini 2.5 Pro's video understanding context window is large but not unlimited. A 2-hour game film
uploaded as a single file risks hitting token limits mid-analysis. Chunking also enables parallel
extraction — in v2.0 each chunk runs Prompt 0A (extract_chunk) simultaneously, and Prompt 0B
(run_chunk_synthesis) combines the results into a single synthesis document before report generation.
The infrastructure is chunk-aware from day one.

**Why download to /tmp on the worker instead of streaming?**
FFmpeg requires seekable input. R2 presigned URLs support range requests but FFmpeg's segment muxer
needs to seek backward during splitting. Writing to /tmp is the correct solution. Cloud Run instances
must be configured with 4GB /tmp minimum — default is 512MB which a single 720p compressed film
exceeds. Set this in Cloud Run service configuration for tex-worker-film.

**Every file written to /tmp is tracked and deleted in a finally block regardless of task outcome.**
See /TMP CLEANUP section.

**The film_chunks table (v2 addition to schema):**
```sql
CREATE TABLE film_chunks (
  id                      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  film_id                 uuid NOT NULL REFERENCES films(id),
  chunk_index             integer NOT NULL,          -- 0-indexed order
  duration_seconds        integer NOT NULL,
  r2_chunk_key            text NOT NULL,             -- R2 key for this chunk. kept until report complete.
  gemini_file_uri         text,                      -- files/abc123 — returned by Gemini File API
  gemini_file_state       text NOT NULL DEFAULT 'uploading',
                          -- uploading | active | failed
  gemini_file_expires_at  timestamptz,               -- expireTime from Gemini File API response. 48hr window.
  created_at              timestamptz NOT NULL DEFAULT now(),
  UNIQUE (film_id, chunk_index)
);
```

---

## FILE VALIDATION ON UPLOAD

Three validation layers. Each catches different problems. Together they ensure no bad file
ever reaches a worker, no worker wastes time on an unprocessable file, and every failure
surfaces a clear, actionable error message to the coach — not a cryptic worker crash.

**Layer 1 — Browser (instant, zero server cost):**
Basic checks before the upload starts. First line of defense.

```javascript
const ALLOWED_TYPES = [
  "video/mp4",
  "video/quicktime",    // .MOV
  "video/x-msvideo",   // .AVI
  "video/x-matroska",  // .MKV
  "video/webm"
]
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 * 1024  // 10GB hard ceiling

function validateFilmUpload(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type))
    return "File type not supported. Please upload MP4, MOV, AVI, MKV, or WebM."
  if (file.size > MAX_FILE_SIZE_BYTES)
    return "File exceeds 10GB limit. Please compress before uploading."
  if (file.size < 1024 * 1024)
    return "File is too small to be a valid game film."
  return null  // valid — proceed with upload
}
```

Browser MIME type checks can be spoofed by a renamed file. Layer 2 catches that.

**Layer 2 — FastAPI before presigned URL is issued:**
No presigned URL is issued until server-side validation passes.
The file never reaches R2 if this layer rejects it.

```python
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
MAX_FILE_SIZE_BYTES  = 10 * 1024 * 1024 * 1024   # 10GB
MAX_DURATION_SECONDS = 60 * 60 * 3                # 3 hours

def validate_upload_request(file_name: str, file_size_bytes: int) -> None:
    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"File extension {ext} not supported.")
    if file_size_bytes > MAX_FILE_SIZE_BYTES:
        raise HTTPException(400, "File exceeds 10GB limit.")
    if file_size_bytes < 1024 * 1024:
        raise HTTPException(400, "File too small to be valid game film.")
```

**Layer 3 — Worker after download (the real gate):**
After the file lands in R2 and the worker downloads it to /tmp, FFprobe runs before
anything else. FFprobe reads the actual container and codec information regardless of
what the filename or MIME type claims. This catches corrupted files, files with no video
stream, and files that are technically valid containers but not game film.

```python
def validate_film_file(local_path: str, film_id: str) -> None:
    result = subprocess.run([
        "ffprobe", "-v", "quiet",
        "-print_format", "json",
        "-show_format", "-show_streams",
        local_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise FilmValidationError("File is corrupted or not a valid video file.")

    probe = json.loads(result.stdout)
    duration = float(probe["format"]["duration"])
    has_video = any(s["codec_type"] == "video" for s in probe["streams"])

    if not has_video:
        raise FilmValidationError("File contains no video stream.")
    if duration < 60:
        raise FilmValidationError("Film is under 1 minute. Not valid game film.")
    if duration > MAX_DURATION_SECONDS:
        raise FilmValidationError("Film exceeds 3-hour limit. Upload individual games only.")
```

**On Layer 3 failure:**
Worker updates `films.status = error` with the validation message. Coach sees a clear error
in the UI. /tmp files cleaned up in the finally block. R2 file deleted. No Gemini calls made.
No cost incurred beyond the R2 storage of the bad file.

**Why 3 hours is the max duration ceiling:**
Real game film at any level — D1 through high school — runs 90-120 minutes including warmups
and halftime. 3 hours covers any single game with generous margin. A file longer than 3 hours
is almost certainly a tournament day recording — multiple games in one file. Reject it clearly:
"Upload individual games, not full tournament recordings." Let the coach trim and re-upload.

**What the validation layers catch:**

```
Problem                              Caught by
──────────────────────────────────────────────────────
Wrong file type (.pptx, .pdf)        Layer 1 + Layer 2
File too large (>10GB)               Layer 1 + Layer 2
File too small (<1MB)                Layer 1 + Layer 2
Renamed file (fake extension)        Layer 3 (FFprobe)
Corrupted video file                 Layer 3 (FFprobe)
Audio-only file                      Layer 3 (FFprobe)
Film under 1 minute                  Layer 3 (FFprobe)
Tournament recording (>3 hours)      Layer 3 (FFprobe)
```

---

## GEMINI FILE EXPIRY GAP AND RECOVERY

Every file uploaded to the Gemini File API is automatically deleted by Google after 48 hours.
The URI stored in `film_chunks.gemini_file_uri` becomes a dead link after that window.

**Why this matters at scale:**
A coach uploads film Thursday night and triggers report generation Sunday morning — 60 hours later.
The queue backs up before a major tournament and jobs wait 50+ hours before a worker picks them up.
A worker crashes after chunk upload and the retry runs 49 hours later. In all three cases, the
stored URI is expired and any Gemini call using it fails. At thousands of coaches these are not
edge cases — they are predictable consequences of growth.

**R2 is the source of truth. Gemini is a temporary processing layer.**
R2 (Cloudflare's file storage) holds the permanent copy of every chunk. Gemini borrows the file,
analyzes it, then forgets it after 48 hours. R2 never forgets. When Gemini loses a chunk, TEX
re-uploads it from R2. This is why chunk files are kept in R2 until report generation is confirmed
complete — not deleted immediately after Gemini upload.

**The fix — expiry-aware chunk retrieval:**

Every report generation task calls `get_valid_chunk_uris()` before running any prompts.
This function checks expiry and re-uploads transparently. The rest of the pipeline never
needs to know a re-upload happened.

```python
def get_valid_chunk_uris(conn, film_id: str) -> list[str]:
    chunks = fetch_chunks(conn, film_id)
    expired = [
        c for c in chunks
        if c["gemini_file_expires_at"] < now() + timedelta(hours=1)
    ]
    # 1-hour buffer: don't use a URI that expires mid-generation
    if expired:
        re_upload_chunks(conn, expired)

    return [c["gemini_file_uri"] for c in fetch_chunks(conn, film_id)]


def re_upload_chunks(conn, expired_chunks: list[dict]):
    for chunk in expired_chunks:
        local_path = download_from_r2(chunk["r2_chunk_key"])
        new_uri, new_expiry = upload_to_gemini_file_api(local_path)

        update_chunk_uri(conn, chunk["id"], new_uri, new_expiry)
        cleanup_local(local_path)
```

**Schema requirements:**
`film_chunks.gemini_file_expires_at` — populated from `expireTime` in Gemini File API response.
`film_chunks.r2_chunk_key` — R2 key for this chunk. Required for re-upload. Never null.

**R2 chunk cleanup rule:**
Chunk files in R2 are deleted only inside the `generate_report` task after `reports.status`
is set to `complete`. Never before. This guarantees R2 always has a valid source for re-upload
for the entire lifetime of the job.

---

## /TMP CLEANUP ON WORKERS

Cloud Run reuses container instances across task invocations. A worker that processes film job A
does not get a fresh container for film job B — it reuses the same instance. Any files left in
/tmp from job A are still there when job B starts. After enough jobs, /tmp fills up. The next
download fails with a disk space error mid-task, with no clear indication of why.

**The fix — track every /tmp file, delete all of them in a finally block:**

```python
def process_film(film_id: str):
    tmp_files = []
    try:
        # download raw film from R2
        raw_path = download_from_r2(film_id)
        tmp_files.append(raw_path)

        # compress if needed
        compressed_path = ffmpeg_compress(raw_path)
        if compressed_path != raw_path:
            tmp_files.append(compressed_path)

        # split into chunks
        chunk_paths = ffmpeg_split(compressed_path)
        tmp_files.extend(chunk_paths)

        # upload chunks to Gemini / GCS
        upload_chunks(chunk_paths, film_id)

    except Exception as e:
        update_film_status(film_id, "error", str(e))
        raise

    finally:
        # always runs — success, failure, or crash
        # never leave files in /tmp between task invocations
        for path in tmp_files:
            if os.path.exists(path):
                os.remove(path)
```

The `finally` block is non-negotiable. It runs whether the task succeeded, failed halfway through,
or hit an unexpected exception. No code path leaves /tmp files behind.

**Cloud Run /tmp configuration:**
Default /tmp on Cloud Run is 512MB. A 2-hour film compressed to H.264 720p is 1-2GB.
The raw film before compression can be 4-8GB. The worker needs headroom for both simultaneously.

```
tex-worker-film service configuration:
  --execution-environment=gen2
  --memory=8Gi
  --cpu=4
  /tmp size: 8GB   ← set via --ephemeral-storage flag in Cloud Run
```

Set this in the Cloud Run deployment configuration. If not set, the first coach who uploads
a 2-hour film will crash the worker with a disk space error that looks unrelated to storage.

**File naming convention in /tmp to avoid collisions:**
Multiple tasks can run on the same worker instance concurrently. Use film_id in every temp filename.

```python
raw_path = f"/tmp/{film_id}_raw.mp4"
compressed_path = f"/tmp/{film_id}_compressed.mp4"
chunk_path = f"/tmp/{film_id}_chunk_{index:03d}.mp4"
```

Without the film_id prefix, two concurrent tasks writing `chunk_001.mp4` overwrite each other.

---

## REPORT GENERATION PIPELINE

```
1. generate_report task receives report_id
2. Fetch report + associated film_ids + roster from DB
3. Call get_valid_chunk_uris() — re-uploads any expired Gemini URIs from R2
4. Create context cache from chunk URIs + roster (orchestrator, before chord fires)
5. Fire Celery chord — sections 1-4 run in PARALLEL:
   Section 1: offensive_sets      — input: cache URI
   Section 2: defensive_schemes   — input: cache URI
   Section 3: pnr_coverage        — input: cache URI
   Section 4: player_pages        — input: cache URI
   Each section saves to report_sections immediately on completion.
6. Chord callback fires when all 4 complete — run_synthesis_sections:
   Section 5: game_plan           — input: sections 1-4 text (no video)
   Section 6: adjustments_practice — input: sections 1-5 text (no video)
7. Delete context cache from Gemini
8. Write sections 1-4 to film_analysis_cache (keyed by film hash)
9. assemble_pdf() → upload PDF to R2 → save pdf_r2_key to reports
10. Delete R2 chunks (report is now confirmed complete)
11. Delete Gemini file URIs
12. Update reports.status = complete
13. Enqueue notify_coach task
```

**Sections 1-4 run in parallel. Sections 5-6 run sequentially after.**
Sections 1-4 are independent — same input, no dependency on each other. The Celery chord
fires all 4 simultaneously. The chord callback triggers sections 5-6 only after all 4 complete.
Section 6 depends on section 5 output, so 5 and 6 are sequential within the callback.

**Context cache is created once by the orchestrator before the chord fires.**
Not by section 1. All 4 parallel sections receive the same cache URI as input. This is
what allows simultaneity — no section waits for another to create shared resources.

**What happens when a multi-film report runs?**
If a coach selects 3 films for one report, the context cache includes chunk URIs from
all 3 films. Gemini receives context for all films in a single cache. The prompt instructs
Gemini to synthesize patterns across games, not summarize each game separately.

**Error recovery at section level:**
If one section fails after 3 retries, it writes `status: error` to report_sections. The
chord callback still fires — Celery chords proceed when all tasks complete regardless of
individual success or failure. The callback checks section statuses and generates the best
possible partial report, clearly indicating which section failed. A 5/6 partial report is
more useful to a coach than a total failure.

---

## GEMINI FILE API INTEGRATION

**Why Gemini File API instead of base64 inline?**
A 20-minute H.264 chunk at 720p is approximately 400-800MB. Inlining that as base64 in a JSON request
body is infeasible. The File API uploads the file once and references it by URI in subsequent requests.
Files persist for 48 hours. TEX deletes them after report generation is confirmed complete.

**File lifecycle:**
```
upload chunk (worker) → poll until state=ACTIVE → create context cache from URIs
→ run 4 parallel section prompts using cache → delete context cache
→ report confirmed complete → delete chunk file URIs → delete R2 chunks
```

**Context cache sits on top of file URIs:**
The Gemini context cache is created from the chunk URIs. It is the cached representation of
the video content that all 4 sections share. The context cache is deleted immediately after
sections 1-4 complete (step 20 in the pipeline). The underlying file URIs are deleted after
the full report is confirmed complete (step 25). R2 chunks are deleted last (step 24).

**Deletion order matters:**
```
1. Context cache deleted (after sections 1-4 complete) — frees Gemini cache storage
2. Gemini file URIs deleted (after full report complete) — frees Gemini file storage
3. R2 chunks deleted (after full report complete) — frees R2 storage
```
Never delete R2 chunks before the report is confirmed complete. R2 is the re-upload source
if a Gemini URI expires or a file needs to be reprocessed.

**Orphaned file cleanup:**
A daily maintenance task calls `files.list` and deletes any Gemini files older than 24 hours
that are not referenced in an active report. This catches files from crashed workers that
died before cleanup ran.

---

## AUTHENTICATION FLOW

Clerk handles auth. FastAPI verifies Clerk JWTs.

```
Browser → Clerk login → Clerk JWT issued
Browser → API call with Authorization: Bearer {jwt}
FastAPI → verify_clerk_jwt(token) → extract clerk_id
FastAPI → SELECT id FROM users WHERE clerk_id = {clerk_id} AND deleted_at IS NULL
FastAPI → use users.id for all DB queries
```

Clerk webhooks (user.created, user.deleted) hit `POST /webhooks/clerk`.
On `user.created`: insert into users. On `user.deleted`: set users.deleted_at.
Webhook handler verifies Svix signature before processing. Never trust unsigned webhooks.

Admin routes additionally check: `SELECT is_admin FROM users WHERE id = {user_id}`.
If `is_admin = false`, return 403 immediately. The is_admin check is in the route handler, not
a middleware, so it is explicit and auditable for each admin endpoint.

---

## STORAGE: CLOUDFLARE R2

Two buckets:
```
tex-films-{env}    — raw uploaded films + processed chunks. private.
tex-reports-{env}  — generated PDF scouting reports. private.
```

All access via presigned URLs. Expiry:
- Upload URLs: 1 hour (sufficient for large film uploads on slow connections)
- Download URLs: 15 minutes (coach clicks download, gets a short-lived URL)

R2 key naming conventions:
```
films/{user_id}/{film_id}/{original_filename}        — raw film. kept permanently.
chunks/{film_id}/chunk_{index:03d}.mp4               — FFmpeg chunks. kept in R2 until report = complete.
reports/{user_id}/{report_id}/scouting_report.pdf    — final PDF
```

Chunk files in R2 are deleted only after `reports.status = complete` is confirmed. They are NOT
deleted after Gemini File API upload. R2 is the source of truth — if a Gemini file URI expires
before report generation runs, the chunk is re-uploaded from R2. See GEMINI FILE EXPIRY section.

---

## PDF GENERATION

Library: WeasyPrint (Python). Input: HTML template + section content. Output: PDF bytes.

```
assemble_pdf(sections: dict[str, str], team_name: str, report_title: str) -> bytes
```

PDF section order (matches v1):
1. Cover page — team name, report date, TEX branding
2. Offensive Sets
3. Defensive Schemes
4. PnR Coverage
5. Individual Player Pages (one page per rostered player)
6. Game Plan
7. In-Game Adjustments + Practice Plan

The HTML template lives at `backend/templates/report.html`. Tailwind CSS is not used here —
WeasyPrint requires static CSS. Use a purpose-built print stylesheet.
Typography: clean, high-contrast, print-optimized. This PDF is printed and used on a clipboard.

---

## FRONTEND: NEXT.JS

The frontend is a thin client. It renders state, collects input, and calls the FastAPI backend.

```
tex-v2/frontend/
├── app/
│   ├── (auth)/              # Clerk login/signup pages
│   ├── dashboard/           # Coach's home: teams, recent reports
│   ├── teams/[id]/          # Team page: roster, films, reports
│   ├── reports/[id]/        # Report status + PDF download
│   ├── upload/              # Film upload flow
│   └── admin/               # Training mode — is_admin gate
├── components/
│   ├── upload/              # Presigned URL upload logic + progress bar
│   ├── report/              # Report status polling + section previews
│   └── ui/                  # Shared primitives: buttons, cards, modals
├── lib/
│   ├── api.ts               # Typed fetch wrappers for every FastAPI endpoint
│   └── clerk.ts             # Auth helpers
└── middleware.ts             # Clerk auth gate on all routes except (auth)
```

**Polling pattern for job status:**
The frontend polls `GET /reports/{id}` every 5 seconds while `status` is `processing`.
When status becomes `complete` or `error`, polling stops. No WebSockets in v2.0.
WebSockets add operational complexity (persistent connections, reconnect logic) that is not
justified when a report takes 15-45 minutes. A coach will check back, not stare at a spinner.

**Film upload (multipart — required for files up to 10GB):**
1. Frontend calls `POST /films/upload-initiate` → gets `{ film_id, upload_id, r2_key, part_urls }`
2. Frontend uploads each 100MB part sequentially via PUT to each presigned part URL, collecting ETags
3. On all parts complete, frontend calls `POST /films/upload-complete` with `{ film_id, upload_id, parts }`
4. Backend completes R2 multipart upload, writes film record, enqueues process_film task
5. On any part failure, frontend calls `POST /films/upload-abort` to prevent orphaned R2 parts
See PRD.md §1.4 for full route specs, part size rationale, and browser upload code.

---

## ENVIRONMENT CONFIGURATION

Two environments: `development` (local Docker Compose) and `production` (Cloud Run + Vercel).

```
# Backend (Cloud Run Secret Manager)
NEON_HOST, NEON_DB, NEON_USER, NEON_PASSWORD
REDIS_URL
GEMINI_API_KEY
CLOUDFLARE_R2_ACCOUNT_ID, CLOUDFLARE_R2_ACCESS_KEY_ID, CLOUDFLARE_R2_SECRET_ACCESS_KEY
CLOUDFLARE_R2_BUCKET_FILMS, CLOUDFLARE_R2_BUCKET_REPORTS
CLERK_SECRET_KEY, CLERK_WEBHOOK_SECRET
STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
SENTRY_DSN
DATADOG_API_KEY

# Frontend (Vercel Environment Variables)
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY
CLERK_SECRET_KEY
NEXT_PUBLIC_API_BASE_URL        # FastAPI Cloud Run URL
NEXT_PUBLIC_POSTHOG_KEY
STRIPE_PUBLISHABLE_KEY
```

No secrets in code. No secrets in Docker images. Cloud Run reads secrets from Secret Manager at boot.

---

## LOCAL DEVELOPMENT

```
# docker-compose.yml spins up:
# - FastAPI (hot reload via uvicorn --reload)
# - Celery worker (all 3 queues, single process for dev)
# - Redis (official image)
# - No local Neon — use Neon dev branch (Neon offers branching like Git)

docker compose up

# Run migrations against Neon dev branch:
python scripts/migrate.py

# Frontend runs separately:
cd frontend && npm run dev
```

All environment variables for local dev live in `backend/.env` (gitignored).
`.env.example` documents every required variable with a description.

---

## OBSERVABILITY

**Sentry:** Every unhandled exception in FastAPI and every failed Celery task reports to Sentry.
Include `film_id`, `report_id`, and `user_id` in Sentry context for every task error.
A film processing failure without these identifiers is undebuggable.

**Datadog:** APM traces on all FastAPI routes. Custom metrics:
- `tex.film.processing_time_seconds` — tagged by film duration
- `tex.report.generation_time_seconds` — tagged by section count
- `tex.gemini.tokens_used` — tagged by section_type and prompt_version
- `tex.report.cost_usd` — computed from token counts, logged per report

**PostHog:** Product analytics in the frontend. Track:
- `film_uploaded` — with file_size_mb property
- `report_generation_started`
- `report_downloaded`
- `section_error` — which section failed and why

These three tools serve distinct purposes. Sentry = errors. Datadog = infrastructure performance.
PostHog = product behavior. Do not conflate them.

---

## DEPLOYMENT

**Backend:**
Cloud Run service: `tex-api` — FastAPI, 1 container, min 1 instance (cold start mitigation), max 10.
Cloud Run service: `tex-worker-film` — Celery film_processing queue, min 0, max 5. 8GB /tmp.
Cloud Run service: `tex-worker-report` — Celery report_generation queue. Orchestrator only — fires chords, does not run prompts. min 0, max 3.
Cloud Run service: `tex-worker-section` — Celery section_generation queue. Runs individual section prompts. min 0, max 10.
Cloud Run service: `tex-worker-notify` — Celery notifications queue, min 0, max 3.

Each Cloud Run service is a separate Docker image built from the same `backend/` directory with
different CMD instructions:
```dockerfile
# tex-api:
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

# tex-worker-film:
CMD ["celery", "-A", "tasks.celery_app", "worker", "-Q", "film_processing", "--concurrency=1"]
```

**Frontend:**
Vercel. Automatic deploys from `main`. Preview deploys from feature branches.
`NEXT_PUBLIC_API_BASE_URL` points to the Cloud Run `tex-api` service URL.

**CI/CD:**
GitHub Actions. On push to `main`: build Docker images, push to Artifact Registry, deploy to Cloud Run.
Tests run before deploy. Deploy blocks on test failure.

---

## WHAT V1 TAUGHT US

**Bug 1 — 2GB file size limit:** The Gemini File API and browser memory both have size limits.
v2 solution: FFmpeg compresses to H.264 720p before chunking if file > 1.8GB. Chunking itself
prevents any single file from exceeding the API limit.

**Bug 2 — Supabase connection timeout:** Supabase's PgBouncer closed idle connections during long
Celery tasks, causing DB calls mid-task to fail with "connection terminated unexpectedly."
v2 solution: structural fix — open connection, execute query, close connection, every time.
No connection held across task boundaries.

**The Twelve Labs removal:** Twelve Labs provided a useful abstraction (semantic video search,
timestamped clip retrieval) but added cost, latency, and a dependency we did not control.
Gemini 2.5 Pro's native video understanding is superior for the TEX use case: we do not need
clip retrieval, we need holistic analysis. Direct video ingestion via the File API is simpler,
cheaper, and more capable for full-game scouting analysis.

---

## SCHEMA CHANGES FROM V1

The v1 schema (10 tables) carries forward with these modifications:

1. `films` table: remove `twelve_labs_task_id`, `twelve_labs_index_id`. Add `gemini_processing_status`.
2. New table: `film_chunks` — tracks FFmpeg chunks and their Gemini File API URIs.
3. `report_sections`: add `chunk_count` — number of chunks analyzed to generate this section.
4. Auth remains Clerk. Payment remains Stripe. Data isolation enforced at application layer — see DATA ISOLATION section. No Neon RLS.
5. `corrections` table: completely redesigned. v1 anchored corrections to `clip_id` from
   Twelve Labs — a timestamped segment identifier. Twelve Labs is gone. There are no clips
   in v2. The v2 corrections table anchors to `report_id` + `section_type` + `ai_claim` —
   the specific sentence or paragraph Gemini produced, tied to the report it came from.
   See AI_STRATEGY.md for the full corrections lifecycle across all four training phases.
   The full v2 schema is in SCHEMA.md.

The full v2 schema is defined in SCHEMA.md. Migrations are numbered SQL files in `backend/migrations/`.

---

## AI PROVIDER ABSTRACTION

The AI landscape changes fast. A better video model can drop next week. A competitor model can
undercut Gemini on price. Gemini can have an outage during tournament weekend. TEX must be able
to swap AI providers without touching anything outside a single folder and one environment variable.

**The rule:** Nothing in TEX ever imports directly from a provider file. Everything imports from
the router. The router reads `AI_VIDEO_PROVIDER` and returns the correct implementation.

```
backend/services/ai/
├── base.py          # the contract — defines what every provider must implement
├── gemini.py        # Gemini 2.5 Pro + 1.5 Flash implementation
├── openai.py        # stub today — real when OpenAI ships competitive video understanding
├── anthropic.py     # stub today — real when Claude gets native video
└── router.py        # reads AI_VIDEO_PROVIDER, returns the right provider
```

**base.py — the interface every provider must satisfy:**

```python
from abc import ABC, abstractmethod

class AIVideoProvider(ABC):

    @abstractmethod
    def upload_video(self, local_path: str) -> str:
        """Upload a video chunk. Return a URI the provider can reference."""
        pass

    @abstractmethod
    def analyze_video(self, uris: list[str], prompt: str, section_type: str) -> str:
        """Run a section prompt against video chunks. Return section text."""
        pass

    @abstractmethod
    def analyze_text(self, context: str, prompt: str, section_type: str) -> str:
        """Run a synthesis prompt against text only. Return section text.
        Used for sections 5-6 which receive no video."""
        pass

    @abstractmethod
    def delete_video(self, uri: str) -> None:
        """Delete uploaded video from provider storage after use."""
        pass

    @abstractmethod
    def check_uri_valid(self, uri: str, expires_at) -> bool:
        """Return False if the URI has expired or will expire within 1 hour."""
        pass
```

**router.py — the only file the rest of TEX imports from:**

```python
import os
from services.ai.base import AIVideoProvider

def get_ai_provider() -> AIVideoProvider:
    provider = os.environ.get("AI_VIDEO_PROVIDER", "gemini")

    if provider == "gemini":
        from services.ai.gemini import GeminiProvider
        return GeminiProvider()
    elif provider == "openai":
        from services.ai.openai import OpenAIProvider
        return OpenAIProvider()
    elif provider == "anthropic":
        from services.ai.anthropic import AnthropicProvider
        return AnthropicProvider()
    else:
        raise ValueError(f"Unknown AI provider: {provider}")
```

**How a section task uses this — provider is never referenced directly:**

```python
# tasks/film_processing.py
from services.ai.router import get_ai_provider

def run_section(report_id: str, section_type: str, roster: list, chunks: list):
    provider = get_ai_provider()
    prompt = load_prompt(section_type)
    uris = [c["uri"] for c in chunks]

    if section_type in ("game_plan", "adjustments_practice"):
        prior_sections = fetch_prior_sections(report_id)
        result = provider.analyze_text(prior_sections, prompt, section_type)
    else:
        result = provider.analyze_video(uris, prompt, section_type)

    save_section(report_id, section_type, result)
```

**Environment variable controls everything:**

```
AI_VIDEO_PROVIDER = "gemini"       # today — Gemini 2.5 Pro for video, Flash for text
AI_VIDEO_PROVIDER = "openai"       # when GPT-5 ships competitive video understanding
AI_VIDEO_PROVIDER = "anthropic"    # when Claude gets native video
```

**Three scenarios this solves:**

1. Better model drops — swap provider, run evals, ship. Zero rewrite.
2. Price competition — route lower tiers to cheaper provider. One router change.
3. Gemini outage — flip to backup provider. Reports keep generating during tournament weekend.

**Note on Vertex AI migration:** The Gemini provider implementation (`gemini.py`) internally
handles the `GEMINI_BACKEND` switch between Developer API and Vertex AI. The rest of TEX
never sees this distinction — it calls `provider.analyze_video()` regardless.

```
AI_VIDEO_PROVIDER = "gemini"  +  GEMINI_BACKEND = "developer_api"   → Gemini File API
AI_VIDEO_PROVIDER = "gemini"  +  GEMINI_BACKEND = "vertex"          → Vertex AI + GCS
```

Two env vars, complete control over the entire AI infrastructure stack.

---

## PIPELINE INTELLIGENCE MAP

Every step in the TEX pipeline, what it uses, and why. A developer should be able to read this
and immediately know where the LLM calls are, which model, and what requires no AI at all.

```
STEP                          TOOL                    LLM?   NOTES
─────────────────────────────────────────────────────────────────────────────
1.  Coach uploads film        Browser → R2            No     Presigned URL. FastAPI never touches bytes.
2.  Film metadata saved       FastAPI → Neon           No     SQL insert. No intelligence involved.
3.  Download film to /tmp     Worker → R2              No     FFmpeg needs seekable local file.
4.  Film hash computed        Worker (SHA-256)         No     Hash computed AFTER download — file must be local.
5.  Cache lookup              Worker → Neon            No     Check film_analysis_cache by hash.
    └─ Cache hit              Return cached sections   No     Skip steps 6-15 entirely. Jump to step 19.
    └─ Cache miss             Continue to step 6       —
6.  Compress if > 1.8GB       FFmpeg (H.264 720p)      No     Pure video processing. No AI.
7.  Split into chunks         FFmpeg (segment muxer)   No     Pure video processing. No AI.
8.  Upload chunks to Gemini   Worker → Gemini File API No     Save URI + expiry to film_chunks. Keep in R2.
9.  Poll until ACTIVE         Worker → Gemini File API No     Waiting for Gemini to process upload.
10. Save chunk URIs to DB     Worker → Neon            No     SQL insert to film_chunks. Includes expiry timestamp.
11. Check chunk URI expiry    Worker → Neon            No     get_valid_chunk_uris(). Re-upload from R2 if expired.
12. Create context cache      Orchestrator → Gemini    No     Cache created ONCE before chord fires. Not by section 1.
─────────────────────────────────────────────────────────────────────────────
13. Section 1 — Offensive Sets     Gemini 2.5 Pro     YES    Input: cache URI (shared video + roster).
14. Section 2 — Defensive Schemes  Gemini 2.5 Pro     YES    Input: cache URI (shared video + roster).
15. Section 3 — PnR Coverage       Gemini 2.5 Pro     YES    Input: cache URI (shared video + roster).
16. Section 4 — Player Pages       Gemini 2.5 Pro     YES    Input: cache URI (shared video + roster).
    └─ Steps 13-16 run in PARALLEL via Celery chord.
    └─ All 4 read from the same cache. Cache created once at step 12.
    └─ Each section saved to report_sections immediately on completion.
─────────────────────────────────────────────────────────────────────────────
17. Section 5 — Game Plan          Gemini 2.5 Flash   YES    Input: sections 1-4 TEXT only. Fallback: Claude 3.5 Sonnet.
18. Section 6 — Adjustments        Gemini 2.5 Flash   YES    Input: sections 1-5 TEXT only. Fallback: Claude 3.5 Sonnet.
    └─ Steps 17-18 run sequentially. Section 6 requires section 5 output.
    └─ Flash used here. Text-in text-out tasks. 2.5 Pro is wasteful and unnecessary.
─────────────────────────────────────────────────────────────────────────────
19. Write film cache entry    Worker → Neon            No     Save sections 1-4 to film_analysis_cache by hash.
20. Delete context cache      Worker → Gemini          No     Cache no longer needed. Frees Gemini storage.
21. Assemble PDF              WeasyPrint               No     HTML template + section text → PDF bytes.
22. Upload PDF to R2          Worker → R2              No     Infrastructure. No intelligence.
23. Save pdf_r2_key to DB     Worker → Neon            No     SQL update on reports table.
24. Delete R2 chunks          Worker → R2              No     Only now — report is confirmed complete.
25. Delete Gemini file URIs   Worker → Gemini File API No     Cleanup. files.delete per chunk URI.
26. Write notification        Worker → Neon            No     SQL insert to notifications table.
27. Coach downloads PDF       Browser → R2             No     Presigned read URL. 15 min expiry.
─────────────────────────────────────────────────────────────────────────────
```

**Summary:**
- 27 steps total in the pipeline.
- 6 steps touch an LLM (steps 13-18).
- 21 steps involve zero AI — infrastructure, SQL, FFmpeg, file I/O.
- Gemini 2.5 Pro called exactly 4 times per report (sections 1-4), all parallel.
- Gemini 2.5 Flash called exactly 2 times per report (sections 5-6), sequential.
- Context cache created once at step 12 by orchestrator — shared across all 4 parallel sections.
- A cache hit eliminates steps 6-18 entirely — jumps from step 5 to step 19.
- R2 chunks kept until step 24 — never deleted before report is confirmed complete.

**This map is the cost model.** Every dollar TEX spends on AI is in steps 13-18.
Everything else is infrastructure cost — storage, compute, egress. Know the difference.

---

## AI FALLBACK STRATEGY

**Sections 1-4: no fallback exists.**
These sections require native video understanding at a strategic basketball level. As of today,
Gemini 2.5 Pro is the only model capable of this task. If Gemini is unavailable, sections 1-4
wait and retry. The retry policy (3 attempts, exponential backoff: 30s, 120s, 480s) handles
transient failures. A sustained Gemini outage means sections 1-4 are down — this is a Google
infrastructure event, not a TEX failure. The provider abstraction layer means when a second
model becomes genuinely capable of sports film analysis, it plugs in as a real fallback.

**Sections 5-6: Claude 3.5 Sonnet is the fallback for Gemini 2.5 Flash.**
Sections 5 (game plan) and 6 (adjustments + practice plan) are text-in, text-out tasks.
They receive sections 1-4 output as context and produce long-form coaching documents.
Claude 3.5 Sonnet is excellent at this category of task and is a legitimate alternative
to Gemini 2.5 Flash when Flash is unavailable or returns an error.

**Fallback trigger — automatic, no manual intervention:**

```python
def run_text_section(report_id: str, section_type: str, context: str) -> str:
    prompt = load_prompt(section_type)

    try:
        provider = get_ai_provider()   # Gemini Flash (primary)
        return provider.analyze_text(context, prompt, section_type)

    except (GeminiUnavailableError, GeminiTimeoutError) as e:
        log_fallback_event(report_id, section_type, "gemini_flash", "claude_sonnet", str(e))

        fallback = get_fallback_provider()   # Claude 3.5 Sonnet
        return fallback.analyze_text(context, prompt, section_type)
```

`get_fallback_provider()` always returns the Anthropic Claude provider for text sections.
The fallback is hardcoded for sections 5-6 — it is not configurable via env var because
the fallback relationship is specific: Flash fails → Claude steps in. Nothing else.

**What gets logged on a fallback:**
Every fallback event writes to a `fallback_events` table:
`report_id, section_type, primary_provider, fallback_provider, error_reason, timestamp`
This surfaces in Datadog as a metric — `tex.fallback.triggered` tagged by section_type.
A spike in fallback events signals a Gemini Flash degradation before coaches notice anything.

**The Anthropic provider stub already exists** in `backend/services/ai/anthropic.py`.
For launch it implements only `analyze_text()` — the one method sections 5-6 need.
`analyze_video()`, `upload_video()`, and `delete_video()` raise `NotImplementedError`
until Claude has native video understanding and TEX adds full support.

```
Summary:
Section 1 — Offensive Sets        Gemini 2.5 Pro    fallback: none
Section 2 — Defensive Schemes     Gemini 2.5 Pro    fallback: none
Section 3 — PnR Coverage          Gemini 2.5 Pro    fallback: none
Section 4 — Player Pages          Gemini 2.5 Pro    fallback: none
Section 5 — Game Plan             Gemini Flash      fallback: Claude 3.5 Sonnet
Section 6 — Adjustments           Gemini Flash      fallback: Claude 3.5 Sonnet
```

---



**Decision: application-layer enforcement. No database-level RLS on Neon.**

v1 used Supabase, which has a built-in auth system that injects `auth.uid()` into every database
session automatically. Neon is raw PostgreSQL. There is no `auth.uid()`. Every RLS policy in v1
SCHEMA.md references this function and breaks the moment the database is Neon.

The correct v2 answer is not to port those policies to Neon. It is to recognize that they were
solving a problem TEX v2 does not have.

**Why TEX does not need database-level RLS:**
Every single database call in TEX routes through FastAPI. There is no other path to the database.
Coaches do not connect to Neon directly. There is no client SDK hitting Neon. There is no exposed
GraphQL endpoint. The browser talks to FastAPI. FastAPI talks to Neon. Full stop. FastAPI is the
security boundary. It verifies the Clerk JWT, extracts the user ID, and has the verified user object
before any query runs. Database-level RLS would be a second lock on a door that is already locked,
bolted, and has a guard standing in front of it — at the cost of an additional SET command on every
connection at scale.

At thousands of coaches with concurrent uploads, fresh connection per query, and high poll frequency,
adding a mandatory session variable set before every query adds measurable overhead for zero security
benefit given the architecture.

**What replaces RLS:**

Rule 1 — mandatory user_id scoping. Every query against a user-facing table must include
`WHERE user_id = %s` or a join that traces back to it. This is enforced structurally:

```python
# db.py — user_id is a required parameter. structurally impossible to omit.
def fetch_films(conn, user_id: str) -> list[dict]:
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM films WHERE user_id = %s AND deleted_at IS NULL",
        (user_id,)
    )
    return cur.fetchall()

# Every service function follows this exact pattern.
# user_id comes from verify_clerk_jwt() in the route handler.
# It is never optional. It is never inferred. It is always passed explicitly.
```

Rule 2 — the corrections table is the one exception that gets a hard database constraint.
The corrections table is the proprietary moat. No coach account should ever read or write it
under any circumstance. This table gets a database-level write restriction: only the service role
key (held only by backend workers) can insert. This is enforced at the Neon level, not in code,
because it protects the single most valuable asset in the product.

Rule 3 — all admin routes check `is_admin` on every request. Not cached. Not inferred from JWT.
`SELECT is_admin FROM users WHERE id = %s` runs on every admin endpoint call.

---

## PARALLEL SECTION GENERATION

**Decision: sections 1-4 run in parallel via Celery chord. Sections 5-6 run sequentially after.**

Sections 1-4 (offensive_sets, defensive_schemes, pnr_coverage, player_pages) are completely
independent. They receive identical input: roster + film chunk URIs. None depends on the others.
Running them sequentially produces the same output as running them in parallel — just 4x slower.

Sequential timing on a 2-hour film: ~34 minutes before sections 5-6 can begin.
Parallel timing on a 2-hour film: ~10 minutes before sections 5-6 can begin.

At thousands of coaches this is not just a UX decision. Sequential processing means workers are
running at 25% utilization — one section runs, three slots sit idle. Parallel processing means
full worker utilization and 4x throughput on the same infrastructure spend.

**Implementation — Celery chord:**

`generate_report` becomes a pure orchestrator. It does not run prompts. It sets up the chord and fires it.

```python
from celery import chord, group

def generate_report(report_id: str):
    report, roster, chunks = fetch_report_context(report_id)

    chord(
        group(
            run_section.s(report_id, "offensive_sets", roster, chunks),
            run_section.s(report_id, "defensive_schemes", roster, chunks),
            run_section.s(report_id, "pnr_coverage", roster, chunks),
            run_section.s(report_id, "player_pages", roster, chunks),
        )
    )(
        run_synthesis_sections.s(report_id)  # fires when all 4 complete
    )
```

`run_synthesis_sections` receives sections 1-4 text and runs sections 5 and 6 sequentially —
section 6 (adjustments + practice plan) receives section 5 (game plan) output as context, so
they cannot be parallelized.

Celery chords use Redis to track completion state. The Redis infrastructure is already in the
architecture. No new infrastructure required.

**Worker split that enables this at scale:**

```
tex-worker-section   → runs individual section prompts on section_generation queue. scale 0-10 instances.
tex-worker-report    → orchestrator only on report_generation queue. fires chords. 3 instances sufficient.
```

At peak load with 20 concurrent reports, 80 section tasks distribute across 10 worker instances.
The orchestrator is lightweight and never the bottleneck.

**Partial failure behavior:**
If one section fails after 3 retries, it writes `status: error` to report_sections. The chord
callback still fires — Celery chords proceed when all tasks complete regardless of individual
task success or failure. The callback checks section statuses and generates the best possible
partial report, clearly indicating which section failed. A 5/6 partial report is more useful
to a coach than a total failure.

---

## MODEL ROUTING, RATE LIMITS, AND FILM CACHING

### Model Routing — Use the Right Model for Each Task

Not every section needs Gemini 2.5 Pro. Using the most expensive model for every task is the
same mistake as using a Ferrari to go to the grocery store.

```
Sections 1-4  →  Gemini 2.5 Pro      video understanding. no substitute exists.
Sections 5-6  →  Gemini 2.5 Flash    text-in, text-out synthesis. 10x cheaper. same quality.
```

Sections 5 and 6 receive text from sections 1-4. They never see video. They are long-form
reasoning and writing tasks. Flash handles this perfectly and at a fraction of the cost.
This routing decision alone cuts Gemini 2.5 Pro consumption by roughly 40% per report.

### Rate Limit Handling — Redis Token Bucket

All Gemini API calls across all workers across all Cloud Run instances are coordinated through
a shared token bucket in Redis. Before any Gemini call, the worker acquires a slot. If the
bucket is empty, the worker waits with jitter and retries. This prevents 429 errors at the
source rather than catching them after the fact.

```python
def acquire_gemini_slot(model: str):
    key = f"rate_limit:{model}"
    limit = RATE_LIMITS[model]  # separate limits per model tier

    while True:
        current = redis.incr(key)
        if current == 1:
            redis.expire(key, 60)   # bucket resets every 60 seconds
        if current <= limit:
            return                  # slot acquired, proceed with API call
        time.sleep(2 + random.uniform(0, 1))  # jitter prevents thundering herd
```

`RATE_LIMITS` is configured per model and updated when Google grants quota increases.
Every Gemini call in every worker calls `acquire_gemini_slot` before executing. No exceptions.

### Context Caching — Mandatory, Not Optional

Context caching is not a performance optimization for TEX. It is what makes the unit economics work.

Video is billed at 263 tokens per second. A 2-hour film = 1.89 million tokens. That exceeds
Gemini 2.5 Pro's 200K threshold, meaning every call is billed at the long-context rate of
$2.50/M input tokens. Without caching, sections 1-4 each pay full price for the same video
input — 4 × $4.73 = $18.92 in video input alone per report before output or infrastructure.

With context caching, section 1 pays full price and creates the cache. Sections 2, 3, and 4
read from that cache at 10% of the input price ($0.25/M vs $2.50/M).

```
Without caching:   4 sections × $4.73 video input = $18.92
With caching:      $4.73 + (3 × $0.47) = $6.14 video input
Savings:           $12.78 per report on input tokens alone
```

Cache storage costs $4.50/M tokens/hour. For a 15-minute report generation window,
storage cost on 1.89M tokens = $2.13. Net saving is still ~$10.65 per report.

**Implementation rule:** The context cache is created by the `generate_report` orchestrator
before the chord fires. The cache URI is passed to all 4 sections as a parameter. No section
creates the cache — only the orchestrator does. This is what allows all 4 sections to run
simultaneously while sharing the same cached video input.

```python
# report_generation.py — cache creation and reuse pattern
def generate_report(report_id: str):
    chunks = get_valid_chunk_uris(conn, film_id)

    # orchestrator creates the cache BEFORE firing the chord
    # all 4 sections receive the cache_uri — none of them create it
    cache = provider.create_context_cache(chunks, roster)
    cache_uri = cache.name

    chord(
        group(
            run_section.s(report_id, "offensive_sets", cache_uri),
            run_section.s(report_id, "defensive_schemes", cache_uri),
            run_section.s(report_id, "pnr_coverage", cache_uri),
            run_section.s(report_id, "player_pages", cache_uri),
        )
    )(run_synthesis_sections.s(report_id))

    # cache is deleted after all 4 sections complete — see cleanup task
```

### Batch API Routing — Financial Justification

The Batch API routing decision (route non-urgent jobs to batch, real-time for active coaches)
is not just a rate-limit strategy. It is a margin decision.

Batch API is 50% off all Gemini costs. For a $9-10 real-time report:

```
Real-time report cost:    ~$9.25
Batch report cost:        ~$5.01
Margin difference:        ~$4.24 per report
```

At 1,000 reports/month with 60% routed to batch:
600 batch × $4.24 savings = $2,544/month in recovered margin.

The routing heuristic already defined in this document (poll gap > 120 seconds → batch)
captures the majority of overnight uploads without any coach-facing change. Coaches who
upload and close the tab never know they got a batch job. Coaches actively watching the
progress indicator get real-time. The product experience is identical. The economics are not.



Gemini's Batch API processes requests asynchronously with a 24-hour SLA at 50% lower cost.
A coach who uploads film at 11pm does not need the report in 12 minutes. They need it by morning.

```python
def route_report_job(report_id: str, user_last_poll: datetime):
    seconds_since_poll = (now() - user_last_poll).seconds
    if seconds_since_poll < 120:        # coach is actively waiting
        queue = "report_generation_realtime"
    else:                                # coach closed the tab
        queue = "report_generation_batch"
```

At scale, the majority of reports are submitted and abandoned — coaches upload and come back.
Routing these to the Batch API halves their cost with no perceived quality difference.

### Film Fingerprint Cache — The Moat Multiplier

Every film uploaded to TEX is hashed on arrival (SHA-256 of the raw bytes). Before running
any Gemini analysis, the worker checks: has this exact film been analyzed before?

```python
def check_film_cache(conn, file_hash: str) -> dict | None:
    cur = conn.execute(
        "SELECT id, sections FROM film_analysis_cache WHERE file_hash = %s",
        (file_hash,)
    )
    return cur.fetchone()
```

If the film is in the cache, return the cached section outputs instantly. No Gemini call.
No worker time. No cost. Immediate result.

If not in the cache, run analysis normally and write the result to the cache.

**Why this is a compounding moat:**

Multiple coaches regularly scout the same opponents — especially at major EYBL events where
every program is watching the same top-ranked teams. The more coaches use TEX, the higher
the cache hit rate, the lower the marginal cost per report, the wider the margin advantage
over any competitor paying full API price on every report.

At 10 coaches: cache hit rate ~5%. Marginal benefit minimal.
At 1,000 coaches: cache hit rate ~40-60% for popular programs. Cost per report drops significantly.
At 10,000 coaches: popular EYBL programs analyzed once. Hundreds of coaches get instant results.

This is the same compounding dynamic that makes Google Search cheaper per query as it grows —
the cache is the business model advantage, not just a technical optimization.

**New table required:**

```sql
CREATE TABLE film_analysis_cache (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  file_hash    text UNIQUE NOT NULL,     -- SHA-256 of raw film bytes
  film_id      uuid REFERENCES films(id),-- first film that generated this cache entry
  sections     jsonb NOT NULL,           -- all 4 section outputs keyed by section_type
  prompt_version text NOT NULL,          -- invalidate cache when prompts are updated
  created_at   timestamptz NOT NULL DEFAULT now()
  -- no deleted_at. cache entries are invalidated by prompt_version, not deleted.
);

CREATE INDEX idx_film_cache_hash ON film_analysis_cache(file_hash);
CREATE INDEX idx_film_cache_prompt_version ON film_analysis_cache(prompt_version);
```

Cache invalidation rule: when PROMPTS.md is updated and prompt_version increments, the cache
for the old version is stale. Workers skip cache entries where `prompt_version != current_version`.
Old entries are purged by a weekly maintenance task. This ensures coaches always get analysis
from the current prompt quality, not a cached result from an inferior older prompt.

---

## PAYMENT FLOW

**Decision 1 — When the gate triggers: before generation starts.**
Coach clicks "Generate Report" → Stripe checkout → payment confirmed → job enters queue.
Reason: TEX incurs real cost the moment a Gemini call runs. A coach who pays and gets a
failed report gets an automatic credit (see below). A coach who generates without paying
is a cost with no revenue. Gate before generation.

**Decision 2 — First report free: per account.**
One free report ever, regardless of teams or films uploaded. Not per team.
Per-team free reports are easily gamed — coach creates 10 teams, gets 10 free reports.
Per-account is clean, enforceable via `users.reports_used = 0` check in the route handler.

**Decision 3 — Technical failure after payment: automatic credit.**
Two distinct failure types require different handling:

*Technical failure* — Gemini outage, worker crash, PDF generation error. Coach paid, got
nothing. TEX's fault, unambiguously. Response: automatic free regeneration credit applied
to the coach's account immediately by the report status webhook. No Tommy involvement.
No Stripe refund (days of friction). One credit. Instant. Automatic.

*Quality disagreement* — Coach received the report, disagrees with the analysis. Not a
refund scenario at launch. Every quality complaint is a training signal. A refund gives
the coach no reason to explain what was wrong. An in-app feedback form tied to the
report_id gives TEX a correction. Tommy reviews and decides case-by-case whether to comp
the report. No automated refund policy for quality issues.

**Payment gate implementation:**

```python
# routers/reports.py
@router.post("/reports")
async def create_report(request: ReportCreateRequest, user = Depends(verify_clerk_jwt)):

    # first report free check
    if user["reports_used"] == 0:
        report_id = create_report_record(conn, user["id"], request)
        increment_reports_used(conn, user["id"])
        generate_report.delay(report_id)
        return {"report_id": report_id, "status": "processing", "charged": False}

    # paid path — create Stripe checkout session
    checkout = stripe.checkout.Session.create(
        customer=user["stripe_customer_id"],
        line_items=[{"price": STRIPE_REPORT_PRICE_ID, "quantity": 1}],
        mode="payment",
        success_url=f"{BASE_URL}/reports/{{CHECKOUT_SESSION_ID}}/processing",
        cancel_url=f"{BASE_URL}/dashboard",
        metadata={"user_id": user["id"], "report_request": json.dumps(request.dict())}
    )
    return {"checkout_url": checkout.url}
```

**Stripe webhook handler:**

```python
# routers/webhooks.py
@router.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    # always verify signature before processing
    event = stripe.Webhook.construct_event(
        await request.body(),
        request.headers["stripe-signature"],
        STRIPE_WEBHOOK_SECRET
    )

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session["metadata"]["user_id"]
        report_request = json.loads(session["metadata"]["report_request"])

        report_id = create_report_record(conn, user_id, report_request)
        increment_reports_used(conn, user_id)
        record_payment(conn, user_id, report_id, session)
        generate_report.delay(report_id)
```

**Technical failure credit:**

```python
# triggered when report_sections error count = total sections after all retries
def apply_failure_credit(user_id: str, report_id: str):
    conn.execute("""
        UPDATE users SET report_credits = report_credits + 1
        WHERE id = %s
    """, (user_id,))

    write_notification(conn, user_id, report_id,
        type="report_failed_credit_applied",
        message="Your report could not be completed. We've added a free report to your account."
    )
```

Credit is checked before the Stripe gate — if `user.report_credits > 0`, decrement the
credit and skip Stripe checkout entirely. No coach ever sees a payment screen for a
report they already paid for that failed.

**In-app quality feedback:**

Every completed report shows a feedback button. Coach clicks it, sees a structured form:
- Which section is wrong? (dropdown — offensive sets, defensive schemes, etc.)
- What did TEX get wrong? (free text)
- Severity: minor issue / major issue / report is unusable

Submits to `report_feedback` table. Tommy reviews in training mode. Every submission
is a potential correction. Tommy decides individually whether to comp the report.
No automated quality refunds at launch.

**Pricing tiers (documented here, implemented in Stripe Products):**

```
STARTER — Pay per report
  $49/report
  First report free per account
  No commitment
  Target: AAU/EYBL coaches, occasional scouts
  TEX margin: ~80% real-time, higher with batch routing

COACH — $199/month
  10 reports/month ($19.90 effective per report)
  Up to 5 unused reports roll over
  Target: active college scouts, high school programs
  TEX margin: ~50-60% (batch routing improves this significantly)

PROGRAM — $499/month
  40 reports/month ($12.50 effective per report)
  Priority queue — real-time processing guaranteed
  Target: D1/D2 programs, serious EYBL programs
  TEX margin: ~50% at batch pricing for off-peak volume
```

Pricing reflects a 70-80% gross margin target. Human scouts charge $200-500/report.
Synergy subscriptions cost $2,000-5,000/year for college programs. TEX at $49/report
is a fraction of either alternative while delivering a report in 30-50 minutes vs
4-48 hours. Price holds until a direct competitor exists that does what TEX does.

---

## CORRECTIONS TABLE — V1 VS V2

**The v1 anchor is broken.**
v1 corrections were anchored to `clip_id` — a Twelve Labs segment identifier pointing to a
specific timestamped moment in the film. "At 2:34-2:52, the AI labeled this as Horns."
Tommy watched that clip, approved or rejected the label, and the correction saved with
that clip identifier as the anchor.

Twelve Labs is gone. There are no clips. There are no timestamps. There are no segment
identifiers. Every `clip_id` value in v1 corrections is meaningless in v2.

**The v2 anchor: report + section + claim.**
Gemini in v2 produces narrative analysis, not timestamped labels. It does not say
"at 2:34 this is a Horns set." It says "they ran Horns 14 times throughout the game,
initiated from the top with #3 as the ball handler." The correction must live at the
granularity of the claim — the specific sentence or paragraph — not a video timestamp.

**Why claim-level, not section-level:**
Section-level corrections ("section 1 was wrong") are too coarse. They tell you a section
had errors but not which type, not which claim, not why. Claim-level corrections tell you
exactly what Gemini got wrong — "it called a DHO series a Horns set" or "it overcounted
set frequency by 20%." At 500+ corrections, category patterns in claim-level data drive
specific prompt improvements. Section-level data drives nothing.

**What changed in the schema:**

```
REMOVED:
  clip_id          — Twelve Labs segment identifier. meaningless in v2.

ADDED:
  report_id        — replaces clip_id as the primary anchor
  ai_claim         — the specific sentence or paragraph Gemini produced
  correct_claim    — Tommy's corrected version. null if is_correct = true.
  category         — finer grain than section_type:
                     "set_identification" | "player_attribution" | "frequency_count"
                     | "tendency" | "coverage_type" | "personnel_evaluation"
                     | "strategic_reasoning"
  game_count       — how many games was this claim based on (Phase 2+)
  phase            — which training phase produced this correction (1 | 2 | 3 | 4)

KEPT:
  film_id          — still anchors to the source film
  section_type     — still identifies which of the 6 sections this came from
  is_correct       — still binary: approved or rejected
  confidence       — Tommy's confidence in his correction: high | medium | low
  prompt_version   — which prompt version produced the ai_claim
  admin_notes      — Tommy's optional context
```

**The training mode UI changes accordingly:**
v1: Tommy watches a video clip, approves or rejects a label.
v2: Tommy reads a generated section, highlights a specific claim, marks it correct or
incorrect, optionally writes the correction. Every decision saves immediately.
This is a better training loop than v1 — Tommy is correcting the exact text that went
into the report, grounded in real language a coach reads, not a raw label on an isolated clip.

**Full corrections schema and lifecycle is documented in AI_STRATEGY.md.**
SCHEMA.md contains the complete SQL. Corrections are never deleted. Ever.

---

## INVARIANTS — NEVER VIOLATE THESE

1. **No long-lived DB connections in workers.** Open, execute, close. Every time.
2. **No business logic in the frontend.** Next.js renders and calls the API. That is all.
3. **No direct R2 credential exposure to the browser.** Presigned URLs only.
4. **Sections 5-6 (game_plan, adjustments_practice) never receive raw video.** They receive sections 1-4 text.
5. **Gemini File API files are deleted after report generation.** No accumulation.
6. **Every Celery task checks DB status before executing.** Idempotency is not optional.
7. **The corrections table is never deleted from.** Corrections are the moat. Permanent records.
8. **Every query against a user-facing table must include `WHERE user_id = {verified_user_id}`.** No exceptions. See DATA ISOLATION section.
9. **No ORM.** Raw SQL. Every query is explicit and visible.
10. **is_admin is checked on every admin request**, not cached, not inferred from the JWT.
