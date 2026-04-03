# AGENTS.md — TEX v2

Complete Celery task definitions. Every task in the system.
Queue assignments, retry policies, timeout values, idempotency rules, and error handling.
Read ARCHITECTURE.md before this. Read SCHEMA.md for the DB tables these tasks write to.
This document is the authoritative reference for everything that runs asynchronously in TEX v2.

---

## OVERVIEW — WHAT RUNS WHERE

TEX v2 has 9 Celery tasks distributed across 4 queues running on 4 Cloud Run worker services.
The FastAPI API enqueues tasks. Workers execute them. Workers never call each other directly —
all coordination happens through Redis (the queue) and Neon (shared state).

```
QUEUE                  WORKER SERVICE          TASKS
──────────────────────────────────────────────────────────────────────────────
film_processing        tex-worker-film         process_film
                                               extract_chunk          (one per chunk, parallel)
report_generation      tex-worker-report       generate_report
                                               run_synthesis_sections (chord callback)
                                               assemble_and_deliver
section_generation     tex-worker-section      run_section            (sections 1-4, parallel)
notifications          tex-worker-notify       notify_coach
```

No task imports from another task file. All cross-task communication goes through:
1. Neon — shared job state (status columns, section content, chunk URIs)
2. Redis — Celery chord coordination (which tasks in a chord are complete)
3. Celery `.delay()` / `.s()` — enqueuing new tasks

---

## GLOBAL TASK RULES

These rules apply to every task without exception.

**Rule 1 — Idempotency.** Every task checks the current job status in Neon before doing any work.
If the status indicates the work is already done, return immediately. Safe to enqueue twice.

```python
# Pattern used in every task — check before acting
def process_film(self, film_id: str):
    with get_connection() as conn:
        film = fetch_film_status(conn, film_id)
    if film["status"] in ("processed", "error"):
        return  # already done or already failed — do not re-process
```

**Rule 2 — /tmp tracking.** Every file written to /tmp is appended to a `tmp_files` list.
The `finally` block deletes every file in that list. No exceptions. No conditional cleanup.

```python
def process_film(self, film_id: str):
    tmp_files = []
    try:
        path = f"/tmp/{film_id}_raw.mp4"
        download_from_r2(path)
        tmp_files.append(path)
        # ... more work
    finally:
        for path in tmp_files:
            if os.path.exists(path):
                os.remove(path)
```

**Rule 3 — Dead letter on final retry.** When `self.request.retries >= self.max_retries`,
write to `dead_letter_tasks` before raising. The write happens even if the raise fails.

**Rule 4 — Sentry context.** Set `film_id`, `report_id`, `user_id` in Sentry scope before
any work. A failure without these identifiers is undebuggable in production.

**Rule 5 — Fresh DB connection per logical operation.** Never hold a connection across a
Gemini call, an FFmpeg call, an R2 download, or any operation that takes more than a few
seconds. Open → execute → close. Every time.

**Rule 6 — No direct provider imports.** All AI calls go through `services/ai/router.py`.
`from services.ai.gemini import GeminiProvider` is never written outside of router.py.

---

## TIMEOUT REFERENCE TABLE

```
TASK                       QUEUE                SOFT LIMIT   HARD LIMIT   RETRIES   BACKOFF
────────────────────────────────────────────────────────────────────────────────────────────
process_film               film_processing      55 min       60 min       3         30s/120s/480s
extract_chunk              film_processing      8 min        10 min       3         30s/60s/120s
generate_report            report_generation    25 min       30 min       3         30s/120s/480s
run_synthesis_sections     report_generation    10 min       12 min       2         60s/180s
assemble_and_deliver       report_generation    10 min       12 min       2         60s/180s
run_section                section_generation   8 min        10 min       3         30s/120s/480s
notify_coach               notifications        25 sec       30 sec       3         5s/10s/20s
```

**Soft limit:** `SoftTimeLimitExceeded` is raised inside the task. The task catches it,
writes error status to DB, cleans up /tmp, and exits gracefully.

**Hard limit:** Celery kills the process immediately. No cleanup runs. This is the last resort.
The finally block for /tmp cleanup will not run on a hard kill — this is acceptable because
Cloud Run instance /tmp is ephemeral and will be cleaned when the instance is replaced.

**Why `notify_coach` has a 30-second hard limit:** A single DB insert taking 30 seconds means
the database is broken, not the task. Surface this immediately — do not let a broken notification
task sit in the queue retrying for minutes while the coach waits to see that their report is done.

---

## TASK: process_film

**Queue:** `film_processing`
**Enqueued by:** FastAPI `POST /films` route, after film metadata is written to Neon
**Triggers:** `extract_chunk` tasks (one per chunk, in parallel after split)

```python
@celery_app.task(
    bind=True,
    name="tasks.film_processing.process_film",
    queue="film_processing",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=3300,
    time_limit=3600,
    acks_late=True,
)
def process_film(self, film_id: str):
```

**Full execution sequence:**

```
1.  Set Sentry context: film_id, user_id (fetched from DB)
2.  Fetch film from DB. If status in ('processed', 'error'): return immediately.
3.  UPDATE films SET status = 'processing', updated_at = now()
4.  Download raw film from R2 to /tmp/{film_id}_raw.{ext}
    Track in tmp_files.
5.  Compute SHA-256 hash of raw bytes (streaming — do not load full file into memory).
    UPDATE films SET file_hash = {hash}
6.  Check film_analysis_cache:
      SELECT sections, synthesis_document FROM film_analysis_cache
      WHERE file_hash = {hash} AND prompt_version = {current_version}
    Cache hit → jump to step 14.
    Cache miss → continue.
7.  FFprobe validation:
    - Valid video container
    - Has video stream
    - Duration >= 60 seconds
    - Duration <= 10800 seconds (3 hours)
    On failure: UPDATE films SET status = 'error', error_message = {message}
                Write to dead_letter_tasks.
                Enqueue notify_coach(film_id, type='film_error')
                Return.
8.  If file_size_bytes > 1,800,000,000 (1.8GB):
      FFmpeg compress to H.264 720p → /tmp/{film_id}_compressed.mp4
      Track in tmp_files.
      input_path = compressed path
    Else:
      input_path = raw path
9.  FFmpeg split into 20-25 min segments:
      Output: /tmp/{film_id}_chunk_{index:03d}.mp4
      Track all chunk paths in tmp_files.
      UPDATE films SET chunk_count = {n}, duration_seconds = {duration}
10. For each chunk (sequential — one at a time to avoid overwhelming R2):
    a. Upload chunk to R2 at chunks/{film_id}/chunk_{index:03d}.mp4
    b. INSERT INTO film_chunks (film_id, chunk_index, duration_seconds,
                                r2_chunk_key, gemini_file_state='uploading')
11. Enqueue extract_chunk tasks for all chunks (parallel):
      group(
        extract_chunk.s(film_id, chunk_id, chunk_index)
        for chunk_id, chunk_index in chunk_ids
      ).apply_async()
    Note: extraction runs in parallel but process_film does NOT wait for them.
    Extractions enqueue themselves. process_film's job ends at step 11.
12. UPDATE films SET status = 'chunks_uploaded', gemini_processing_status = 'uploading'
    (Status transitions: uploaded → processing → chunks_uploaded → processed)

14. (Cache hit path)
    UPDATE films SET status = 'processed', file_hash = {hash}
    No Gemini upload needed. Cached sections used at report generation.
    Return.
```

**Error handling:**
```python
except SoftTimeLimitExceeded:
    update_film_status(film_id, "error", "Processing timed out after 55 minutes")
    write_dead_letter(task_name="process_film", ...)
    raise

except Exception as exc:
    if self.request.retries >= self.max_retries:
        update_film_status(film_id, "error", str(exc))
        write_dead_letter(task_name="process_film", ...)
        notify_coach.delay(film_id=film_id, type="film_error")
    raise self.retry(exc=exc, countdown=backoff(self.request.retries))

finally:
    for path in tmp_files:
        if os.path.exists(path):
            os.remove(path)
```

---

## TASK: extract_chunk

**Queue:** `film_processing`
**Enqueued by:** `process_film` (one per chunk, dispatched as a group — run in parallel)
**Triggers:** When all chunks complete extraction → synthesis is triggered by a chord callback

```python
@celery_app.task(
    bind=True,
    name="tasks.film_processing.extract_chunk",
    queue="film_processing",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=480,
    time_limit=600,
    acks_late=True,
)
def extract_chunk(self, film_id: str, chunk_id: str, chunk_index: int):
```

**Full execution sequence:**

```
1.  Fetch chunk from DB. If gemini_file_state = 'active' and extraction_output IS NOT NULL:
    return immediately (idempotency).
2.  Upload chunk from R2 to Gemini File API:
    a. Download chunk from R2 to /tmp/{film_id}_chunk_{chunk_index:03d}.mp4
       Track in tmp_files.
    b. Upload to Gemini File API: files.create(path)
    c. Poll until file.state = ACTIVE (max 5 min, poll every 10 sec)
    d. UPDATE film_chunks SET
         gemini_file_uri = {uri},
         gemini_file_state = 'active',
         gemini_file_expires_at = {expireTime}
3.  Acquire Gemini rate limit slot (token bucket via Redis)
4.  Run chunk extraction prompt (Prompt 0A):
    prompt = load_prompt("chunk_extraction")
    prompt = inject_chunk_metadata(prompt, chunk_index, total_chunks,
                                   start_min, end_min)
    provider = get_ai_provider()
    extraction_output = provider.analyze_video(
        uris=[chunk["gemini_file_uri"]],
        prompt=prompt,
        section_type="chunk_extraction"
    )
5.  UPDATE film_chunks SET
      extraction_output = {extraction_output},
      extraction_status = 'complete'
6.  Check if all chunks for this film_id have extraction_status = 'complete':
    SELECT COUNT(*) FROM film_chunks
    WHERE film_id = {film_id} AND extraction_status != 'complete'
    If count = 0: enqueue run_chunk_synthesis.delay(film_id)
    (Only the last chunk to complete triggers synthesis — checked atomically)
```

**Atomic last-chunk detection:**
The "enqueue synthesis when all chunks complete" check must be atomic. Use a Neon advisory
lock or a `SELECT ... FOR UPDATE` on the films row to prevent two chunks completing
simultaneously and both enqueueing synthesis:

```python
with get_connection() as conn:
    with conn.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_xact_lock(%s)", (hash(film_id),))
        locked = cur.fetchone()[0]
        if locked:
            incomplete = cur.execute("""
                SELECT COUNT(*) FROM film_chunks
                WHERE film_id = %s AND extraction_status != 'complete'
            """, (film_id,)).fetchone()[0]
            if incomplete == 0:
                run_chunk_synthesis.delay(film_id)
```

**Error handling on Gemini upload failure:**
If the Gemini File API upload fails after 3 retries, mark the chunk:
`UPDATE film_chunks SET gemini_file_state = 'failed', extraction_status = 'failed'`
Synthesis proceeds with available chunks and notes the missing chunk.

---

## TASK: run_chunk_synthesis

**Queue:** `film_processing`
**Enqueued by:** Last `extract_chunk` task to complete (after all chunks extracted)
**Triggers:** Nothing directly — writes synthesis document, then films.status = 'processed'

```python
@celery_app.task(
    bind=True,
    name="tasks.film_processing.run_chunk_synthesis",
    queue="film_processing",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=720,
    acks_late=True,
)
def run_chunk_synthesis(self, film_id: str):
```

**Full execution sequence:**

```
1.  Fetch all film_chunks for film_id with extraction_output.
    Identify any chunks with extraction_status = 'failed' — note them for the synthesis prompt.
2.  Fetch roster for the team associated with this film.
3.  Build synthesis input:
    - All extraction outputs concatenated with chunk headers
    - Roster text
    - List of any failed chunks with their time ranges
4.  Acquire Gemini rate limit slot.
5.  Run synthesis prompt (Prompt 0B, Gemini 2.5 Pro):
    synthesis_document = provider.analyze_text(
        context=all_extractions + roster,
        prompt=load_prompt("chunk_synthesis"),
        section_type="chunk_synthesis"
    )
6.  INSERT INTO film_analysis_cache (file_hash, film_id, sections={}, synthesis_document,
                                      prompt_version)
    ON CONFLICT (file_hash) DO UPDATE SET synthesis_document = EXCLUDED.synthesis_document
    (sections{} is empty at this point — filled after report generation completes)
7.  UPDATE films SET status = 'processed', updated_at = now()
8.  If film has a pending report that is cleared for generation:
      SELECT reports.id FROM reports
      JOIN report_films ON report_films.report_id = reports.id
      LEFT JOIN payments ON payments.report_id = reports.id
      WHERE report_films.film_id = {film_id}
        AND reports.status = 'pending'
        AND (
          payments.id IS NULL             -- free or credit path: no payment row expected
          OR payments.status = 'complete' -- paid path: payment must be confirmed complete
        )
    For each matching report_id: generate_report.delay(report_id)
    (Auto-trigger only if payment is confirmed or no payment is required.
    A report with a payments row in status = 'pending' means the coach abandoned checkout —
    do not generate. The Stripe webhook will trigger generation if they complete payment later.)
```

**Graceful degradation on synthesis failure:**
If synthesis fails after 2 retries, do not block report generation.
Set `films.status = 'processed'` and note in a `synthesis_failed` column.
Sections 1-4 run without the synthesis document, receiving only raw video and roster.
This is worse output quality but not a blocked report.

---

## TASK: generate_report

**Queue:** `report_generation`
**Enqueued by:** FastAPI Stripe webhook handler (after payment confirmed), or `run_chunk_synthesis`
  (auto-trigger if report was pending), or directly by FastAPI (free/credit path)
**Triggers:** Celery chord of 4 `run_section` tasks + `run_synthesis_sections` callback

```python
@celery_app.task(
    bind=True,
    name="tasks.report_generation.generate_report",
    queue="report_generation",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=1500,
    time_limit=1800,
    acks_late=True,
)
def generate_report(self, report_id: str):
```

**Full execution sequence:**

```
1.  Set Sentry context: report_id, user_id
2.  Fetch report. If status in ('complete', 'partial', 'error'): return (idempotency).
3.  UPDATE reports SET status = 'processing'
4.  Fetch film_ids from report_films WHERE report_id = {report_id}
5.  Verify all films have status = 'processed'.
    If any film is still 'processing': raise self.retry(countdown=60)
    (Retry in 60 seconds — film may still be processing)
6.  Call get_valid_chunk_uris(conn, film_id) for each film.
    Re-uploads expired chunks from R2 if any URIs expire within 1 hour.
7.  Fetch synthesis_document from film_analysis_cache for each film.
8.  Fetch roster for the team.
9.  Build context cache input:
    - All valid chunk URIs (across all films)
    - Synthesis document(s)
    - Roster text
10. Acquire Gemini rate limit slot.
11. Create Gemini context cache:
    cache = provider.create_context_cache(chunk_uris, synthesis_text, roster_text, ttl=3600)
    cache_uri = cache.name
    Save cache_uri to reports.context_cache_uri (new column — add to schema migration)
12. INSERT INTO report_sections for all 6 sections with status = 'pending'
    ON CONFLICT (report_id, section_type) DO UPDATE SET status = 'pending'
13. Fire Celery chord:
    chord(
        group(
            run_section.s(report_id, "offensive_sets",    cache_uri, prompt_version),
            run_section.s(report_id, "defensive_schemes", cache_uri, prompt_version),
            run_section.s(report_id, "pnr_coverage",      cache_uri, prompt_version),
            run_section.s(report_id, "player_pages",      cache_uri, prompt_version),
        )
    )(run_synthesis_sections.s(report_id, cache_uri))
14. generate_report returns here. All further work happens in run_section tasks
    and the run_synthesis_sections callback.
```

**Important:** `generate_report` does not wait for the chord to complete. It fires the chord
and returns. The chord callback (`run_synthesis_sections`) handles everything after sections 1-4.

---

## TASK: run_section

**Queue:** `section_generation`
**Enqueued by:** `generate_report` (as part of a Celery chord group — 4 dispatched simultaneously)
**Triggers:** Nothing — saves to `report_sections`, chord callback fires after all 4 complete

```python
@celery_app.task(
    bind=True,
    name="tasks.section_generation.run_section",
    queue="section_generation",
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=480,
    time_limit=600,
    acks_late=True,
)
def run_section(self, report_id: str, section_type: str,
                cache_uri: str, prompt_version: str):
```

**Full execution sequence:**

```
1.  Set Sentry context: report_id, section_type
2.  Fetch section row. If status = 'complete': return (idempotency).
3.  UPDATE report_sections SET status = 'processing' WHERE report_id = {id}
    AND section_type = {type}
4.  Load prompt: prompt_text, version = load_prompt(section_type)
5.  Acquire Gemini rate limit slot (model = "gemini-2.5-pro")
6.  start_time = time.monotonic()
7.  provider = get_ai_provider()
    content = provider.analyze_video_cached(
        cache_uri=cache_uri,
        prompt=prompt_text,
        section_type=section_type
    )
8.  elapsed = int(time.monotonic() - start_time)
9.  UPDATE report_sections SET
      status = 'complete',
      content = {content},
      model_used = 'gemini-2.5-pro',
      prompt_version = {version},
      tokens_input = {provider.last_tokens_input},
      tokens_output = {provider.last_tokens_output},
      generation_time_seconds = {elapsed},
      updated_at = now()
```

**Error handling:**
On final retry failure, write `status = 'error'` to `report_sections` and `dead_letter_tasks`.
The chord callback fires regardless — Celery chords fire when all tasks complete (success or failure).
`run_synthesis_sections` checks section statuses and handles partial results.

**Chord behavior on failure:**
Celery chord callbacks fire when all tasks in the group reach a terminal state — complete or failed.
A failed `run_section` task does not block the chord callback. The callback checks all section
statuses and proceeds with whatever completed successfully.

---

## TASK: run_synthesis_sections

**Queue:** `report_generation`
**Enqueued by:** Celery chord callback — fires automatically when all 4 `run_section` tasks complete
**Triggers:** `assemble_and_deliver`

```python
@celery_app.task(
    bind=True,
    name="tasks.report_generation.run_synthesis_sections",
    queue="report_generation",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=720,
    acks_late=True,
)
def run_synthesis_sections(self, chord_results: list, report_id: str, cache_uri: str):
```

**Full execution sequence:**

```
try:
1.  Set Sentry context: report_id
2.  Fetch all 6 section rows for this report.
3.  Count errored sections from sections 1-4.
    If all 4 sections errored: skip to step 9 (no context for synthesis)
4.  Build synthesis context from completed sections 1-4:
    context = build_synthesis_context(sections_1_4)
    Includes any [CONFIRMED]/[LIKELY]/[SINGLE GAME SIGNAL] tags from synthesis document.
5.  Run section 5 — Game Plan (Gemini Flash, fallback Claude):
    game_plan_content = run_text_section(report_id, "game_plan", context)
    Saves to report_sections on completion.
6.  Build section 6 context (sections 1-4 + section 5):
    context_with_game_plan = context + f"\n\nGAME PLAN:\n{game_plan_content}"
7.  Run section 6 — Adjustments + Practice Plan (Gemini Flash, fallback Claude):
    run_text_section(report_id, "adjustments_practice", context_with_game_plan)
    Saves to report_sections on completion.
8.  Write film_analysis_cache sections 1-4:
    UPDATE film_analysis_cache SET sections = {sections_1_4_content}
    WHERE file_hash = {film.file_hash} AND prompt_version = {current_version}
    Enqueue: assemble_and_deliver.delay(report_id)
    Return.
9.  (All sections 1-4 errored path)
    Update reports.status = 'error'
    apply_failure_credit(user_id, report_id)
    Enqueue: notify_coach.delay(report_id=report_id, type='report_failed_credit_applied')
    Return.

finally:
10. Delete Gemini context cache — runs on every exit path: success, partial, full failure, or exception.
    if cache_uri:
        try:
            provider.delete_context_cache(cache_uri)
        except Exception:
            log.warning(f"Cache deletion failed for {cache_uri} — will be caught by weekly maintenance")
        UPDATE reports SET context_cache_uri = NULL WHERE id = {report_id}
```

**Context cache deletion is in `finally` — not inline:**
The cache deletion (step 10) runs in a `finally` block, not in the main execution sequence.
This guarantees it fires on every exit path: normal completion, partial failure, full failure,
unhandled exception, and retry. Placing it inline (as step 5 previously) meant any exception
before that step left the cache alive indefinitely, bleeding Gemini storage costs.

The inner `try/except` on the delete call is intentional — a failed deletion should never
block report delivery or error the task. It logs a warning and moves on. The weekly maintenance
task (`files.list` + delete anything older than 24 hours not referenced by an active report)
is the backstop for any caches that slip through after all retries are exhausted.

**`run_text_section` with Flash → Claude fallback:**

```python
def run_text_section(report_id: str, section_type: str, context: str) -> str:
    prompt_text, version = load_prompt(section_type)
    try:
        acquire_gemini_slot("gemini-2.5-flash")
        provider = get_ai_provider()
        content = provider.analyze_text(context, prompt_text, section_type)
        save_section(report_id, section_type, content,
                     model_used="gemini-2.5-flash", prompt_version=version)
        return content
    except Exception as e:
        log_fallback_event(report_id, section_type, "gemini_flash", "claude_sonnet", str(e))
        fallback = get_fallback_provider()
        content = fallback.analyze_text(context, prompt_text, section_type)
        save_section(report_id, section_type, content,
                     model_used="claude-3-5-sonnet", prompt_version=version)
        return content
```

---

## TASK: assemble_and_deliver

**Queue:** `report_generation`
**Enqueued by:** `run_synthesis_sections` (after sections 5-6 complete)
**Triggers:** `notify_coach`

```python
@celery_app.task(
    bind=True,
    name="tasks.report_generation.assemble_and_deliver",
    queue="report_generation",
    max_retries=2,
    default_retry_delay=60,
    soft_time_limit=600,
    time_limit=720,
    acks_late=True,
)
def assemble_and_deliver(self, report_id: str):
```

**Full execution sequence:**

```
1.  Set Sentry context: report_id, user_id
2.  Fetch report. If status in ('complete', 'partial'): return (idempotency).
3.  Fetch all 6 sections from report_sections.
4.  Count errored sections:
      error_count = len([s for s in sections if s['status'] == 'error'])
    If error_count == 6: → full failure path (step 10)
    If 1 <= error_count <= 5: → partial report path
    If error_count == 0: → complete report path
5.  Assemble PDF:
    pdf_bytes = assemble_pdf(
        sections=sections,          # errored sections get placeholder page
        team_name=team.name,
        report_date=today(),
        is_partial=(error_count > 0)
    )
    Report status will be 'partial' if any section errored.
6.  Upload PDF to R2:
    key = f"reports/{user_id}/{report_id}/scouting_report.pdf"
    upload_to_r2(bucket=BUCKET_REPORTS, key=key, data=pdf_bytes)
7.  UPDATE reports SET
      status = 'complete' or 'partial',
      pdf_r2_key = {key},
      completed_at = now(),
      generation_time_seconds = {elapsed since reports.created_at}
8.  Delete Gemini file URIs (chunk files — no longer needed):
    For each chunk in film_chunks WHERE film_id in {report film_ids}:
      provider.delete_video(chunk.gemini_file_uri)
      UPDATE film_chunks SET gemini_file_state = 'deleted'
9.  Delete R2 chunk files:
    For each chunk: delete_from_r2(bucket=BUCKET_FILMS, key=chunk.r2_chunk_key)
    ONLY after reports.status is confirmed written. Never before.
10. (Full failure path — error_count == 6)
    UPDATE reports SET status = 'error'
    apply_failure_credit(user_id, report_id)
    Enqueue: notify_coach.delay(report_id=report_id, type='report_failed_credit_applied')
    Return.
11. Enqueue: notify_coach.delay(report_id=report_id,
             type='report_complete' if error_count == 0 else 'report_partial')
```

**PDF assembly with errored sections:**
`assemble_pdf()` accepts sections regardless of status. An errored section renders as:

```html
<div class="section section-error">
  <h2>[Section Name]</h2>
  <p class="error-notice">
    This section could not be generated. Please contact support or regenerate the report.
  </p>
</div>
```

A partial report is still a usable document. 5 of 6 sections is more useful to a coach
than a complete failure with no PDF.

---

## TASK: notify_coach

**Queue:** `notifications`
**Enqueued by:** `assemble_and_deliver`, `run_synthesis_sections` (on full failure),
                  `process_film` (on film validation failure)
**Triggers:** Nothing — terminal task

```python
@celery_app.task(
    bind=True,
    name="tasks.notifications.notify_coach",
    queue="notifications",
    max_retries=3,
    default_retry_delay=5,
    soft_time_limit=25,
    time_limit=30,
    acks_late=True,
)
def notify_coach(self, report_id: str = None, film_id: str = None,
                 type: str = "report_complete"):
```

**Notification types and messages:**

```python
NOTIFICATION_MESSAGES = {
    "report_complete": "Your scouting report is ready. Download it now.",
    "report_partial":  "Your report is ready with {n} of 6 sections complete. "
                       "One or more sections could not be generated.",
    "report_failed_credit_applied": "Your report could not be completed. "
                                    "A free report credit has been added to your account.",
    "film_error":      "Your film could not be processed: {error_message}. "
                       "Please re-upload or contact support.",
}
```

**Execution sequence:**

```
1.  Fetch user_id from report or film (whichever is provided).
2.  Build message from NOTIFICATION_MESSAGES[type].
3.  INSERT INTO notifications (user_id, report_id, type, message)
4.  Return. Nothing else. One DB write. That is the entire task.
```

If this task fails after 3 retries, the coach simply does not receive a notification.
The report is still in Neon — the coach can refresh their dashboard and see it.
A notification failure never blocks a report delivery.

---

## STARTUP RECOVERY FUNCTION

Runs on every worker boot, before the worker accepts any tasks.
Registered as a Celery `worker_ready` signal handler.

```python
from celery.signals import worker_ready

@worker_ready.connect
def on_worker_ready(sender, **kwargs):
    recover_stuck_jobs()

def recover_stuck_jobs():
    """
    Finds jobs stuck in 'processing' longer than 2x their expected hard timeout.
    Re-enqueues them. Safe to call multiple times — task idempotency prevents duplicate work.

    Thresholds:
      films:   2 hours  (2x the 60-min film_processing hard limit)
      reports: 1 hour   (2x the 30-min report_generation hard limit)
    """
    with get_connection() as conn:
        stuck_films = conn.execute("""
            SELECT id FROM films
            WHERE status = 'processing'
              AND updated_at < now() - interval '2 hours'
              AND deleted_at IS NULL
        """).fetchall()

        for row in stuck_films:
            process_film.delay(row["id"])
            log.info(f"Startup recovery: re-enqueued stuck film {row['id']}")

        stuck_reports = conn.execute("""
            SELECT id FROM reports
            WHERE status = 'processing'
              AND updated_at < now() - interval '1 hour'
              AND deleted_at IS NULL
        """).fetchall()

        for row in stuck_reports:
            generate_report.delay(row["id"])
            log.info(f"Startup recovery: re-enqueued stuck report {row['id']}")
```

This function is safe to run on every worker boot including rolling deploys where old and
new worker versions run simultaneously. Task idempotency (check status before acting) ensures
a re-enqueued task that is actually still running simply exits immediately when it checks status.

---

## DEAD LETTER WRITER

Every task's final retry block calls this before raising:

```python
def write_dead_letter(
    task_name: str,
    task_args: dict,
    queue: str,
    error_message: str,
    error_traceback: str,
    retry_count: int,
    film_id: str = None,
    report_id: str = None,
    user_id: str = None,
):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO dead_letter_tasks
              (task_name, task_args, queue, error_message, error_traceback,
               retry_count, film_id, report_id, user_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (task_name, json.dumps(task_args), queue, error_message,
              error_traceback, retry_count, film_id, report_id, user_id))
        conn.commit()
```

No FK constraints on the dead_letter_tasks table — write succeeds even if the referenced
film or report row is corrupted or missing. See D-009.

---

## TASK INTERACTION MAP

```
FastAPI POST /films
    └── process_film (film_processing)
            └── extract_chunk × N (film_processing, parallel)
                    └── [last chunk completes] run_chunk_synthesis (film_processing)
                            └── [auto-trigger if report pending] generate_report (report_generation)

FastAPI POST /reports (free/credit path)
    └── generate_report (report_generation)

Stripe webhook checkout.session.completed
    └── generate_report (report_generation)
            └── chord: [run_section × 4] (section_generation, parallel)
                    └── [chord callback] run_synthesis_sections (report_generation)
                            └── assemble_and_deliver (report_generation)
                                    └── notify_coach (notifications)
```

Every path eventually terminates at `notify_coach`. That is the only terminal task.
Every other task either enqueues another task or fires a chord. No task loops back to itself
(idempotency prevents this even if a task is accidentally enqueued twice).

---

## RATE LIMIT TOKEN BUCKET

Shared across all workers and all Cloud Run instances via Redis.
Every Gemini call acquires a slot before executing. No exceptions.

```python
# services/rate_limit.py
import redis
import time
import random

RATE_LIMITS = {
    "gemini-2.5-pro":   3,    # requests per 60 seconds — update when quota increases
    "gemini-2.5-flash": 15,   # requests per 60 seconds
}

def acquire_gemini_slot(model: str, redis_client):
    key = f"rate_limit:{model}"
    limit = RATE_LIMITS[model]
    while True:
        count = redis_client.incr(key)
        if count == 1:
            redis_client.expire(key, 60)   # reset bucket every 60 seconds
        if count <= limit:
            return                          # slot acquired
        time.sleep(2 + random.uniform(0, 1))  # jitter — prevents thundering herd
```

`RATE_LIMITS` values are starting points based on default Gemini API quotas.
Request quota increases from Google as volume warrants. Update `RATE_LIMITS` dict when granted.
The token bucket automatically handles the new limit — no other code changes needed.

---

## CELERY WORKER STARTUP COMMAND REFERENCE

```bash
# tex-worker-film — film processing + chunk extraction + synthesis
celery -A tasks.celery_app worker \
  -Q film_processing \
  --concurrency=1 \
  --loglevel=info \
  --hostname=worker-film@%h

# tex-worker-report — orchestration only, no prompts
celery -A tasks.celery_app worker \
  -Q report_generation \
  --concurrency=1 \
  --loglevel=info \
  --hostname=worker-report@%h

# tex-worker-section — section prompts, runs 4 concurrent tasks
celery -A tasks.celery_app worker \
  -Q section_generation \
  --concurrency=4 \
  --loglevel=info \
  --hostname=worker-section@%h

# tex-worker-notify — notifications
celery -A tasks.celery_app worker \
  -Q notifications \
  --concurrency=2 \
  --loglevel=info \
  --hostname=worker-notify@%h
```

`--concurrency=1` on film and report workers is intentional. Film workers run FFmpeg which
is CPU-bound and uses all available cores natively. Running 2 concurrent film tasks on one
worker would starve both. Report workers are orchestrators — they fire chords and return.
Concurrency=1 is sufficient because they spend almost no time executing.

`--concurrency=4` on section workers matches the chord size. 4 concurrent tasks per worker
means one worker can handle a full chord (all 4 sections) without waiting for a slot.
At 10 worker instances, 40 concurrent section tasks can run simultaneously — 10 full reports
generating sections in parallel.

---

*Last updated: April 1, 2026 — Phase 0, context engineering*
*9 tasks defined. 4 queues. All retry policies, timeouts, and interaction maps complete.*
