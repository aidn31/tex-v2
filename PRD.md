# PRD.md — TEX v2

Product requirements. What gets built, in what order, and what done means for each feature.
Read ARCHITECTURE.md before this. Read SCHEMA.md before writing any route or query.
Every feature here maps to a phase. Zero product code ships before Phase 0 (context docs) is complete.
A feature is not done until its eval question in EVALS.md passes. Not before.

---

## THE PRODUCT IN ONE SENTENCE

A coach uploads game film. TEX analyzes it with Gemini 2.5 Pro and generates a master PDF scouting report. The coach downloads the PDF. That is the entire loop. Every feature serves that loop.

---

## WHAT DOES NOT GET BUILT

These are explicitly out of scope. Not for v1 of v2. Not unless Tommy says otherwise.

- Real-time video annotation or clip tagging
- Live game tracking or in-game use
- Mobile app (responsive web is sufficient at launch)
- Public API for third-party integrations
- Multi-user accounts (one coach per account — no team seats)
- Custom branding or white-labeling
- Integrations with Synergy, Hudl, or Catapult
- Box score scrapers or automated stat ingestion from ESPN, MaxPreps, Nike EYBL portal, or any external site — coaches enter stats manually until Phase 3 defines this explicitly
- Social features, sharing, or comments
- Automated game scheduling or calendar sync (beyond the Google Calendar proof-of-concept — that's AIDN)
- Any feature not described in this document

If Tommy asks for something not listed here, it goes in DECISIONS.md first, then here, then gets built. Never the other way.

---

## PHASE OVERVIEW

```
Phase   Label                   Goal                                          Ships When
──────────────────────────────────────────────────────────────────────────────────────────────
0       Context Engineering     All 12 context docs written and committed     All docs complete
1       Foundation              Auth, teams, roster, film upload, DB wired    First film in R2
2       Film Pipeline           FFmpeg, Gemini File API, chunk management     First processed film
3       Report Generation       Parallel chord, 6 sections, PDF, payments     First paid report
4       Training Mode           Admin UI, corrections, pattern analyzer        50th correction
5       Launch                  Sentry live, Stripe live, first EYBL coaches  First real coach
```

---

## PHASE 1 — FOUNDATION

Goal: a coach can sign up, create a team, build a roster, and upload a film to R2. No AI. No report. Just the infrastructure working end-to-end.

### 1.1 Authentication

**What it does:** Coach signs up or logs in with Clerk. Session is verified on every API call. Coach sees only their own data.

**Routes:**
- Frontend: `/sign-in`, `/sign-up` — Clerk-hosted components
- FastAPI: `POST /webhooks/clerk` — handles `user.created`, `user.deleted`
- All other FastAPI routes require `Authorization: Bearer {clerk_jwt}` header

**Clerk webhook handler (`POST /webhooks/clerk`):**

```
user.created  → INSERT INTO users (clerk_id, email)
user.deleted  → UPDATE users SET deleted_at = now() WHERE clerk_id = {event.data.id}
```

Verify `svix-signature` header before processing. Return 400 on invalid signature.

**JWT verification middleware (applied to all protected routes):**

```python
async def get_current_user(authorization: str = Header(...)) -> dict:
    token = authorization.replace("Bearer ", "")
    payload = await verify_clerk_jwt(token)
    user = fetch_user_by_clerk_id(conn, payload["sub"])
    if not user or user["deleted_at"]:
        raise HTTPException(401, "Unauthorized")
    return user
```

`user` dict is passed to every route handler as a dependency. Never trust user_id from the request body.

**Eval:** Can a coach sign up, log in, and confirm their `users` row was created in Neon?

---

### 1.2 Teams

**What it does:** Coach creates a team (the opponent being scouted). Teams belong to the coach. Coach can create multiple teams.

**Routes:**
- `POST /teams` — create team. Body: `{ name, level }`.
- `GET /teams` — list all teams for the authenticated coach.
- `GET /teams/{id}` — fetch single team with roster and films.
- `PATCH /teams/{id}` — update name or level.
- `DELETE /teams/{id}` — soft delete (`deleted_at = now()`).

**Validation:**
- `name`: required, 1-100 characters
- `level`: must be one of `d1 | d2 | d3 | eybl | aau | high_school | unknown`

**UI (`/teams`):**
- List of teams with name, level, film count, last report date
- "New Team" button → modal with name + level fields
- Each team card links to `/teams/{id}`

**UI (`/teams/{id}`):**
- Team name + level
- Roster tab (Phase 1.3)
- Films tab (Phase 1.5)
- Reports tab (Phase 3.1)

**Eval:** Can a coach create a team, see it on the dashboard, and confirm the row in Neon scoped to their `user_id`?

---

### 1.3 Roster Management

**What it does:** Coach adds players to a team by jersey number and name. Players are passed to Gemini at report generation time for attribution.

**Routes:**
- `POST /roster` — add player. Body: `{ team_id, jersey_number, full_name, position, height, dominant_hand, role, notes }`.
- `GET /roster?team_id={id}` — list all players for a team.
- `PATCH /roster/{id}` — update player fields.
- `DELETE /roster/{id}` — soft delete.

**Validation:**
- `jersey_number`: required, text (allows "00", "0", "33A")
- `full_name`: required, 1-60 characters
- `position`: optional. `PG | SG | SF | PF | C` if provided
- `dominant_hand`: optional. `right | left | ambidextrous` if provided
- `role`: optional. `primary_initiator | secondary_handler | spacer | screener | finisher | role_player` if provided
- Duplicate `(team_id, jersey_number)` rejected with 409

**UI (`/teams/{id}` — Roster tab):**
- Table: jersey #, name, position, height, role
- "Add Player" button → inline form row or modal
- Edit inline on click
- Delete with confirmation

**Roster export for Gemini context (used by report generation):**

```python
def format_roster_for_prompt(players: list[dict]) -> str:
    lines = ["ROSTER:"]
    for p in sorted(players, key=lambda x: x["jersey_number"]):
        line = f"  #{p['jersey_number']} {p['full_name']}"
        if p.get("position"):    line += f", {p['position']}"
        if p.get("height"):      line += f", {p['height']}"
        if p.get("role"):        line += f", role: {p['role']}"
        if p.get("dominant_hand"): line += f", {p['dominant_hand']}-handed"
        if p.get("notes"):       line += f". Notes: {p['notes']}"
        lines.append(line)
    return "\n".join(lines)
```

This formatted string is injected into the Gemini context cache alongside video URIs.

**Eval:** Can a coach add 10 players to a team with jersey numbers and names, see them listed, and confirm they are scoped to the correct `user_id` and `team_id` in Neon?

---

### 1.4 Film Upload (Browser → R2)

**What it does:** Coach selects a film file. Browser validates it. FastAPI initiates a multipart
upload and issues presigned URLs for each part. Browser uploads parts directly to R2. FastAPI
completes the multipart upload and writes the film record.

**Why multipart upload is required:**
R2 has a hard 5GB limit on single-PUT operations. Game film files range from 1.8GB to 10GB.
A single PUT for any file above 5GB fails unconditionally. Files between 1.8GB and 5GB are at
high risk of browser memory exhaustion or network timeout on slow connections. Multipart upload
splits the file into 100MB parts — each part is a small, resumable PUT that the browser can
handle without loading the full file into memory.

**Part size:** 100MB per part. A 10GB file produces 100 parts — well within R2's 10,000 part
maximum. R2 requires a minimum part size of 5MB (except the last part). 100MB gives ample
headroom and balances upload parallelism against browser memory usage.

**Routes:**
- `POST /films/upload-initiate` — initiate multipart upload. Body: `{ team_id, file_name, file_size_bytes }`.
  Returns: `{ film_id, r2_key, upload_id, part_urls: [{part_number, presigned_url}] }`.
  FastAPI generates presigned URLs for all parts upfront and returns them in one response.
- `POST /films/upload-complete` — complete multipart upload after all parts finish.
  Body: `{ film_id, upload_id, parts: [{part_number, etag}] }`.
  FastAPI calls R2 CompleteMultipartUpload and writes the film record to Neon.
- `POST /films/upload-abort` — abort a multipart upload on failure.
  Body: `{ film_id, upload_id }`. FastAPI calls R2 AbortMultipartUpload. Prevents orphaned
  partial uploads accumulating in R2 storage.
- `GET /films/{id}` — fetch film status.
- `GET /films?team_id={id}` — list films for a team.

**Layer 1 — Browser validation (before upload starts):**

```typescript
const ALLOWED_TYPES = ["video/mp4", "video/quicktime", "video/x-msvideo",
                        "video/x-matroska", "video/webm"]
const MAX_SIZE = 10 * 1024 * 1024 * 1024   // 10GB
const MIN_SIZE = 1024 * 1024               // 1MB

function validateFilm(file: File): string | null {
  if (!ALLOWED_TYPES.includes(file.type))
    return "Unsupported file type. Upload MP4, MOV, AVI, MKV, or WebM."
  if (file.size > MAX_SIZE) return "File exceeds 10GB limit."
  if (file.size < MIN_SIZE) return "File too small to be valid game film."
  return null
}
```

**Layer 2 — FastAPI validation (before multipart upload is initiated):**

```python
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
PART_SIZE_BYTES = 100 * 1024 * 1024   # 100MB per part

def validate_upload_request(file_name: str, file_size_bytes: int) -> None:
    ext = Path(file_name).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Extension {ext} not supported.")
    if file_size_bytes > 10 * 1024 ** 3:
        raise HTTPException(400, "File exceeds 10GB limit.")
    if file_size_bytes < 1024 ** 2:
        raise HTTPException(400, "File too small.")

def compute_parts(file_size_bytes: int) -> list[dict]:
    """Returns list of {part_number, offset, size} for each 100MB part."""
    parts = []
    offset = 0
    part_number = 1
    while offset < file_size_bytes:
        size = min(PART_SIZE_BYTES, file_size_bytes - offset)
        parts.append({"part_number": part_number, "offset": offset, "size": size})
        offset += size
        part_number += 1
    return parts
```

**Browser multipart upload with progress:**

```typescript
const PART_SIZE = 100 * 1024 * 1024  // 100MB

async function uploadFilmMultipart(
  file: File,
  partUrls: { part_number: number; presigned_url: string }[],
  onProgress: (pct: number) => void
): Promise<{ part_number: number; etag: string }[]> {
  const completedParts: { part_number: number; etag: string }[] = []
  let bytesUploaded = 0

  for (const { part_number, presigned_url } of partUrls) {
    const offset = (part_number - 1) * PART_SIZE
    const chunk = file.slice(offset, offset + PART_SIZE)

    const response = await fetch(presigned_url, {
      method: "PUT",
      body: chunk,
      headers: { "Content-Type": file.type },
    })

    if (!response.ok) throw new Error(`Part ${part_number} upload failed: ${response.statusText}`)

    const etag = response.headers.get("ETag")
    if (!etag) throw new Error(`Part ${part_number} missing ETag in response`)

    completedParts.push({ part_number, etag })
    bytesUploaded += chunk.size
    onProgress(Math.round((bytesUploaded / file.size) * 100))
  }

  return completedParts
}
```

Parts are uploaded sequentially. Parallel part uploads are faster but exhaust browser memory
on large files. Sequential upload with a 100MB part size is reliable across all connection types.

**UI (`/upload`):**
- Team selector dropdown
- File drop zone with file type + size guidance
- Progress bar during upload (updates per part — smooth on large files)
- On completion: "Film uploaded. Processing will begin shortly."
- Redirect to `/teams/{id}` after confirmation
- On upload failure: call `POST /films/upload-abort` before showing error to prevent orphaned R2 parts

**R2 key format:**

```
films/{user_id}/{film_id}/{original_filename}
```

`film_id` is generated by FastAPI at `POST /films/upload-initiate` and returned to the browser
with the part URLs. The browser includes `film_id` in the `POST /films/upload-complete` call.

**Eval:** Does a film file land in R2 at the correct key with a `films` row in Neon showing `status = 'uploaded'`? Does a 6GB file upload successfully without error?

---

### 1.5 Dashboard

**What it does:** The coach's home page. Shows teams, recent films, and report status at a glance.

**UI (`/dashboard`):**
- Welcome header with coach name (from Clerk)
- Notification badge with unread count
- Teams grid: each card shows team name, level, film count, last report date, "View Team" link
- Recent activity: last 5 films uploaded with status
- "New Team" shortcut button

**Routes used:**
- `GET /teams` — all teams
- `GET /films?limit=5` — recent films
- `GET /notifications?unread=true` — unread count for badge

**No pagination at Phase 1.** Coaches at launch have <10 teams and <50 films. Add pagination in Phase 5 if needed.

**Eval:** Does the dashboard load within 2 seconds and show accurate team and film counts for the authenticated coach only?

---

## PHASE 2 — FILM PIPELINE

Goal: an uploaded film gets processed end-to-end — validated, compressed if needed, split into chunks, uploaded to the Gemini File API, and marked ready for report generation.

### 2.1 Film Processing Worker

**What it does:** Downloads film from R2, validates with FFprobe, compresses if >1.8GB, splits into 20-25 minute chunks, uploads each chunk to the Gemini File API, saves URIs to `film_chunks`.

**Celery task:** `process_film(film_id: str)` on queue `film_processing`.

**Task sequence:**

```
1.  Check films.status in DB. If 'processed' or 'error', return immediately (idempotency).
2.  Update films.status = 'processing'.
3.  Download raw film from R2 to /tmp/{film_id}_raw.{ext}. Track in tmp_files list.
4.  Compute SHA-256 of raw bytes. UPDATE films SET file_hash = {hash}.
5.  Check film_analysis_cache by hash + current prompt_version.
    Cache hit → skip to step 14 (film is already analyzed — skip all processing).
    Cache miss → continue.
6.  Run FFprobe validation (Layer 3):
    - File is a valid video container
    - Has a video stream
    - Duration >= 60 seconds
    - Duration <= 10800 seconds (3 hours)
    On failure: UPDATE films SET status = 'error', error_message = {validation_message}. Cleanup. Return.
7.  If file_size_bytes > 1.8GB: FFmpeg compress to H.264 720p.
    Output: /tmp/{film_id}_compressed.mp4. Track in tmp_files.
8.  FFmpeg split into 20-25 min chunks (segment_time=1500):
    Output: /tmp/{film_id}_chunk_{index:03d}.mp4. Track all in tmp_files.
9.  UPDATE films SET duration_seconds = {duration}, chunk_count = {count}.
10. For each chunk:
    a. Upload chunk to R2 at chunks/{film_id}/chunk_{index:03d}.mp4.
    b. INSERT INTO film_chunks (film_id, chunk_index, duration_seconds, r2_chunk_key,
       gemini_file_state='uploading').
    c. Upload chunk to Gemini File API.
    d. Poll until gemini_file_state = ACTIVE (max 5 min per chunk).
    e. UPDATE film_chunks SET gemini_file_uri = {uri}, gemini_file_state = 'active',
       gemini_file_expires_at = {expiry}.
11. UPDATE films SET status = 'processed', gemini_processing_status = 'active'.
12. Enqueue generate_report if auto-trigger is enabled (Phase 3 decision — hold for now).
14. (Cache hit path) UPDATE films SET status = 'processed'.
    No Gemini upload needed — cached sections will be used at report generation.
finally:
    Delete all files in tmp_files list. No exceptions.
```

**FFprobe validation call:**

```python
def validate_film_file(local_path: str) -> dict:
    result = subprocess.run([
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", local_path
    ], capture_output=True, text=True, timeout=60)

    if result.returncode != 0:
        raise FilmValidationError("File is corrupted or not a valid video.")

    probe = json.loads(result.stdout)
    duration = float(probe["format"]["duration"])
    has_video = any(s["codec_type"] == "video" for s in probe["streams"])

    if not has_video:   raise FilmValidationError("No video stream found.")
    if duration < 60:   raise FilmValidationError("Film is under 1 minute.")
    if duration > 10800: raise FilmValidationError("Film exceeds 3-hour limit. Upload individual games.")

    return {"duration": duration, "streams": probe["streams"]}
```

**FFmpeg compression (if >1.8GB):**

```python
def compress_film(input_path: str, output_path: str) -> None:
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-vcodec", "libx264", "-crf", "28",
        "-vf", "scale=-2:720",
        "-acodec", "aac", "-b:a", "128k",
        "-y", output_path
    ], check=True, timeout=3600)
```

**FFmpeg chunk split:**

```python
def split_film(input_path: str, output_pattern: str) -> list[str]:
    subprocess.run([
        "ffmpeg", "-i", input_path,
        "-c", "copy",
        "-f", "segment",
        "-segment_time", "1500",    # 25 minutes
        "-reset_timestamps", "1",
        output_pattern              # /tmp/{film_id}_chunk_%03d.mp4
    ], check=True, timeout=3600)
    return sorted(glob.glob(output_pattern.replace("%03d", "*")))
```

**Retry policy:** 3 retries, backoff 30s / 120s / 480s. On final failure: write to `dead_letter_tasks`, update `films.status = 'error'`, notify coach.

**Eval:** After uploading a valid 2-hour film, does `films.status = 'processed'` and does `film_chunks` contain the correct number of rows with non-null `gemini_file_uri` and `gemini_file_expires_at`?

---

### 2.2 Film Status Polling (Frontend)

**What it does:** Coach sees real-time film processing status without refreshing.

**UI (`/teams/{id}` — Films tab):**
- Film card shows status badge: Uploaded / Processing / Ready / Error
- While status is 'processing': badge pulses, no user action available
- While status is 'error': error message shown, "Re-upload" button visible
- While status is 'processed': "Generate Report" button appears

**Polling:** `GET /films/{id}` every 5 seconds while `status = 'processing'`. Stop polling when status changes. No WebSockets.

**Eval:** Does the film status badge update from "Processing" to "Ready" in the UI without a page refresh after the worker completes?

---

### 2.3 Chunk URI Expiry Management

**What it does:** Before report generation, checks if any Gemini file URIs are expired (or expire within 1 hour) and re-uploads those chunks from R2.

**Called by:** `generate_report` orchestrator, before the chord fires. Never called by section tasks.

```python
def get_valid_chunk_uris(conn, film_id: str) -> list[str]:
    expired = fetch_expired_chunks(conn, film_id)   # chunks expiring within 1 hour
    if expired:
        re_upload_chunks(conn, expired)              # download from R2, re-upload to Gemini
    chunks = fetch_all_chunks(conn, film_id)
    return [c["gemini_file_uri"] for c in chunks]
```

**Eval:** If a film's chunk URIs are manually set to an expiry 30 minutes in the past in the DB, does `get_valid_chunk_uris()` re-upload them from R2 and return fresh URIs?

---

## PHASE 3 — REPORT GENERATION

Goal: a coach can pay, trigger a report, and receive a fully assembled PDF scouting report with all 6 sections.

### 3.1 Payment Gate

**What it does:** First report is free. Subsequent reports require Stripe checkout. Credits skip checkout. Payment is confirmed before report generation starts.

**Route: `POST /reports`**

```python
@router.post("/reports")
async def create_report(request: ReportCreateRequest, user = Depends(get_current_user)):
    conn = get_connection()

    # Check for available credit first
    if user["report_credits"] > 0:
        decrement_report_credits(conn, user["id"])
        report_id = create_report_record(conn, user["id"], request)
        increment_reports_used(conn, user["id"])
        generate_report.delay(report_id)
        return {"report_id": report_id, "status": "processing", "charged": False}

    # First-report-free check
    if user["reports_used"] == 0:
        report_id = create_report_record(conn, user["id"], request)
        increment_reports_used(conn, user["id"])
        generate_report.delay(report_id)
        return {"report_id": report_id, "status": "processing", "charged": False}

    # Paid path — create Stripe checkout session
    checkout = stripe.checkout.Session.create(
        customer=user["stripe_customer_id"],
        line_items=[{"price": os.environ["STRIPE_REPORT_PRICE_ID"], "quantity": 1}],
        mode="payment",
        success_url=f"{os.environ['BASE_URL']}/reports/{{CHECKOUT_SESSION_ID}}/processing",
        cancel_url=f"{os.environ['BASE_URL']}/dashboard",
        metadata={
            "user_id": str(user["id"]),
            "film_ids": json.dumps([str(f) for f in request.film_ids]),
            "team_id": str(request.team_id)
        }
    )
    # Insert pending payment record
    create_payment_record(conn, user["id"], checkout.id, 4900)
    return {"checkout_url": checkout.url}
```

**Stripe webhook handler (`POST /webhooks/stripe`):**

```python
if event["type"] == "checkout.session.completed":
    session = event["data"]["object"]
    user_id = session["metadata"]["user_id"]
    film_ids = json.loads(session["metadata"]["film_ids"])
    team_id = session["metadata"]["team_id"]

    report_id = create_report_record(conn, user_id, team_id, film_ids)
    increment_reports_used(conn, user_id)
    update_payment_record(conn, session["id"], report_id, "complete",
                          session["payment_intent"])
    generate_report.delay(report_id)
```

**Eval:** Does the free first report generate without a Stripe redirect? Does the second report trigger Stripe checkout? Does a credit skip Stripe and generate immediately?

---

### 3.2 Report Generation Orchestrator

**What it does:** Validates film readiness, checks URI expiry, creates Gemini context cache, fires a Celery chord for sections 1-4, then sections 5-6 run in the chord callback.

**Celery task:** `generate_report(report_id: str)` on queue `report_generation`.

**Task sequence:**

```
1.  Fetch report from DB. Check status — if 'complete', return (idempotency).
2.  UPDATE reports SET status = 'processing'.
3.  Fetch associated film_ids from report_films.
4.  Verify all films have status = 'processed'. If any are not ready, retry in 60s.
5.  Call get_valid_chunk_uris() for each film — re-upload expired chunks from R2.
6.  Acquire Gemini rate limit slot.
7.  Build roster text string via format_roster_for_prompt().
8.  Create Gemini context cache from all chunk URIs + roster text.
    Save cache_uri. This is passed to all 4 section tasks.
9.  INSERT report_sections rows for all 6 sections with status = 'pending'.
10. Fire Celery chord:
    group(
        run_section.s(report_id, "offensive_sets", cache_uri),
        run_section.s(report_id, "defensive_schemes", cache_uri),
        run_section.s(report_id, "pnr_coverage", cache_uri),
        run_section.s(report_id, "player_pages", cache_uri),
    ) | run_synthesis_sections.s(report_id)
```

The orchestrator does not run any prompts. It sets up and fires. That's all.

**Eval:** After `generate_report` fires, do 4 `run_section` tasks appear simultaneously in the `section_generation` queue?

---

### 3.3 Parallel Section Generation (Sections 1-4)

**What it does:** Each section task calls Gemini 2.5 Pro with the shared context cache URI and the section-specific prompt. Saves result to `report_sections`.

**Celery task:** `run_section(report_id: str, section_type: str, cache_uri: str)` on queue `section_generation`.

```python
def run_section(report_id: str, section_type: str, cache_uri: str):
    with get_connection() as conn:
        section = fetch_section(conn, report_id, section_type)
        if section["status"] == "complete":
            return                          # idempotency — already done

        update_section_status(conn, report_id, section_type, "processing")

    prompt = load_prompt(section_type)      # reads from backend/prompts/{section_type}.txt
    provider = get_ai_provider()            # always GeminiProvider via router

    acquire_gemini_slot("gemini-2.5-pro")  # rate limit check before call

    start = time.time()
    content = provider.analyze_video_cached(cache_uri, prompt, section_type)
    elapsed = int(time.time() - start)

    with get_connection() as conn:
        update_section_complete(conn, report_id, section_type,
                                content=content,
                                model_used="gemini-2.5-pro",
                                generation_time_seconds=elapsed,
                                tokens_input=provider.last_tokens_input,
                                tokens_output=provider.last_tokens_output)
```

**Retry policy:** 3 retries, backoff 30s / 120s / 480s. On final failure: `report_sections.status = 'error'`. The chord callback fires regardless — see 3.5 for partial report handling.

**Eval:** Do sections 1-4 complete faster than if they ran sequentially? Measure: all 4 complete in ~10 minutes on a 2-hour film vs ~34 minutes sequential.

---

### 3.4 Synthesis Sections (5-6)

**What it does:** Chord callback runs after all 4 parallel sections complete. Sections 5 and 6 run sequentially. They receive sections 1-4 text as context — no video.

**Celery task:** `run_synthesis_sections(chord_results: list, report_id: str)` on queue `report_generation`.

```python
def run_synthesis_sections(chord_results, report_id: str):
    with get_connection() as conn:
        sections_1_4 = fetch_completed_sections(conn, report_id,
            ["offensive_sets", "defensive_schemes", "pnr_coverage", "player_pages"])

    # Build text context for sections 5-6
    context = build_synthesis_context(sections_1_4)   # formatted text summary

    # Section 5 — Game Plan
    game_plan = run_text_section(report_id, "game_plan", context)

    # Section 6 — Adjustments + Practice Plan (receives section 5 output too)
    context_with_game_plan = context + f"\n\nGAME PLAN:\n{game_plan}"
    run_text_section(report_id, "adjustments_practice", context_with_game_plan)

    # All sections complete — proceed to PDF assembly
    assemble_and_deliver_report.delay(report_id)
```

**`run_text_section` with fallback:**

```python
def run_text_section(report_id: str, section_type: str, context: str) -> str:
    prompt = load_prompt(section_type)
    try:
        provider = get_ai_provider()     # Gemini Flash
        acquire_gemini_slot("gemini-2.5-flash")
        return provider.analyze_text(context, prompt, section_type)
    except (GeminiUnavailableError, GeminiTimeoutError, Exception) as e:
        log_fallback_event(conn, report_id, section_type,
                           "gemini_flash", "claude_sonnet", str(e))
        fallback = get_fallback_provider()    # Claude 3.5 Sonnet
        return fallback.analyze_text(context, prompt, section_type)
```

**Eval:** Does section 6 include content derived from section 5? Do sections 5-6 start only after all 4 parallel sections are in `report_sections` with `status = 'complete'` or `'error'`?

---

### 3.5 PDF Assembly and Delivery

**What it does:** After all 6 sections complete (or error), assembles the PDF, uploads it to R2, updates report status, deletes Gemini resources, and enqueues a notification.

**Celery task:** `assemble_and_deliver_report(report_id: str)` on queue `report_generation`.

```
1.  Fetch all 6 sections from report_sections.
2.  Count errored sections.
    0 errors    → status will be 'complete'
    1-5 errors  → status will be 'partial' (PDF generated with available sections)
    6 errors    → status will be 'error' (no PDF generated, credit applied)
3.  If status = 'error':
    - apply_failure_credit(user_id, report_id)
    - UPDATE reports SET status = 'error'
    - Enqueue notification: 'report_failed_credit_applied'
    - Return.
4.  Assemble PDF from available sections via WeasyPrint.
    Missing section gets a placeholder page: "This section could not be generated."
5.  Upload PDF bytes to R2 at reports/{user_id}/{report_id}/scouting_report.pdf.
6.  UPDATE reports SET status = {complete|partial}, pdf_r2_key = {key}, completed_at = now().
7.  Delete Gemini context cache (if not already deleted).
8.  Write film_analysis_cache entry (sections 1-4 keyed by file_hash + prompt_version).
9.  Delete Gemini file URIs for all chunks.
10. DELETE R2 chunk files (chunks/{film_id}/chunk_*.mp4).
    Only now — report is confirmed complete.
11. Enqueue notify_coach task.
```

**PDF section order (enforced in `report.html` template):**

```
1. Cover page — team name, report date, TEX logo
2. Offensive Sets
3. Defensive Schemes
4. Pick and Roll Coverage
5. Individual Player Pages (one full page per rostered player, alphabetical by jersey number)
6. Game Plan
7. In-Game Adjustments + Practice Plan
```

**Failure credit logic:**

```python
def apply_failure_credit(conn, user_id: str, report_id: str):
    conn.execute(
        "UPDATE users SET report_credits = report_credits + 1 WHERE id = %s",
        (user_id,)
    )
    write_notification(conn, user_id, report_id,
        type="report_failed_credit_applied",
        message="Your report could not be completed. A free report credit has been added to your account."
    )
```

**Eval:** Does the final PDF contain all 7 pages (cover + 6 sections) with correct team name and all rostered players appearing in section 4? Is the PDF downloadable via a presigned R2 URL?

---

### 3.6 Report Status and Download (Frontend)

**What it does:** Coach sees report generation progress in real time and downloads the PDF when ready.

**Route:** `GET /reports/{id}` — returns status, error_message, and (if complete) generates a presigned R2 URL for PDF download.

```python
@router.get("/reports/{report_id}")
async def get_report(report_id: str, user = Depends(get_current_user)):
    report = fetch_report(conn, report_id, user["id"])   # always scoped to user
    if not report:
        raise HTTPException(404)

    response = {
        "id": report["id"],
        "status": report["status"],
        "error_message": report["error_message"],
        "sections": fetch_section_statuses(conn, report_id),
        "pdf_url": None
    }

    if report["status"] in ("complete", "partial") and report["pdf_r2_key"]:
        response["pdf_url"] = generate_presigned_read_url(
            os.environ["CLOUDFLARE_R2_BUCKET_REPORTS"],
            report["pdf_r2_key"],
            expiry_seconds=900
        )
    return response
```

**UI (`/reports/{id}`):**
- Report title and team name
- Section progress: 6 rows, each showing Pending / Generating / Complete / Error
- Sections 1-4 show as generating simultaneously
- Sections 5-6 show as pending until sections 1-4 complete
- When complete: "Download PDF" button → opens presigned URL in new tab
- When partial: "Download PDF" button + banner "One or more sections could not be generated."
- When error: "Report failed. A free credit has been added to your account." with "Generate New Report" button

**Polling:** `GET /reports/{id}` every 5 seconds while status is 'processing'. Stop on 'complete', 'partial', or 'error'.

**Eval:** Does the PDF download link work? Does it expire after 15 minutes? Does a second click after expiry correctly fail (403 from R2)?

---

## PHASE 4 — TRAINING MODE

Goal: Tommy can review generated sections, mark claims correct or incorrect, write corrections, and identify systematic error patterns. Every correction is saved permanently and used to improve prompts.

### 4.1 Admin Gate

**What it does:** All `/admin/*` routes require `is_admin = true`. Checked on every request via a live DB query. Not cached. Not from JWT.

```python
async def require_admin(user = Depends(get_current_user)) -> dict:
    with get_connection() as conn:
        is_admin = fetch_is_admin(conn, user["id"])
    if not is_admin:
        raise HTTPException(403, "Admin access required")
    return user
```

All admin routes use `Depends(require_admin)` instead of `Depends(get_current_user)`.

**Eval:** Can a non-admin authenticated user access any `/admin/*` route? Answer must be no — 403 returned.

---

### 4.2 Training Mode UI

**What it does:** Tommy views a generated report section, highlights a specific claim, marks it correct or incorrect, optionally writes the correction, and submits.

**Routes:**
- `GET /admin/reports` — list all reports with correction counts
- `GET /admin/reports/{id}/sections` — fetch all 6 sections with correction counts per section
- `POST /admin/corrections` — save a correction
- `GET /admin/corrections` — list all corrections with filters
- `GET /admin/pattern-analysis` — weekly error rate breakdown by category

**`POST /admin/corrections` body:**

```json
{
  "report_id": "uuid",
  "film_id": "uuid",
  "section_type": "offensive_sets",
  "ai_claim": "They ran Horns as their primary half-court action 14 times.",
  "is_correct": false,
  "correct_claim": "This is a DHO series, not Horns. I counted 9 occurrences, not 14.",
  "category": "set_identification",
  "confidence": "high",
  "admin_notes": null
}
```

**Pydantic validation on correction submission:**
- `ai_claim`: required, non-empty
- `is_correct`: required, boolean
- `correct_claim`: required if `is_correct = false`, null if `is_correct = true`
- `category`: must be one of the 7 defined values

**UI (`/admin/reports/{id}`):**
- Section selector tabs across top
- Section content rendered as readable text
- Text is selectable — click to highlight a sentence or paragraph
- Highlighted text populates the `ai_claim` field
- Correct / Incorrect toggle
- If Incorrect: text area for `correct_claim`, category dropdown, confidence selector
- Submit button — saves immediately, highlights correction in green (correct) or red (incorrect)
- Correction count badge on each section tab

**Eval:** Can Tommy highlight a claim in an offensive_sets section, mark it incorrect, write a correction, and verify the row in the `corrections` table contains the exact claim text with `is_correct = false`?

---

### 4.3 Pattern Analyzer

**What it does:** Weekly report surfacing which error categories are most common, which prompt versions improved or degraded accuracy, and recommendations for prompt updates.

**Route:** `GET /admin/pattern-analysis?prompt_version={v}&days={n}`

**Query:**

```sql
SELECT
  category,
  COUNT(*) FILTER (WHERE is_correct = false) AS error_count,
  COUNT(*)                                    AS total_count,
  ROUND(
    100.0 * COUNT(*) FILTER (WHERE is_correct = false) / NULLIF(COUNT(*), 0),
    1
  )                                           AS error_rate_pct
FROM corrections
WHERE created_at >= now() - (interval '1 day' * %s)
  AND prompt_version = %s
GROUP BY category
ORDER BY error_count DESC;
```

**Output format (JSON → rendered as table in UI):**

```json
{
  "period_days": 7,
  "prompt_version": "v1.2",
  "total_corrections": 47,
  "error_rate_overall": 34.0,
  "breakdown": [
    { "category": "frequency_count",    "errors": 9, "total": 16, "error_rate": 56.3 },
    { "category": "set_identification", "errors": 4, "total": 15, "error_rate": 26.7 },
    { "category": "player_attribution", "errors": 2, "total": 10, "error_rate": 20.0 },
    { "category": "tendency",           "errors": 1, "total": 6,  "error_rate": 16.7 }
  ],
  "recommendation": "frequency_count has the highest error rate this period. Review offensive_sets and defensive_schemes prompts — add explicit counting methodology instruction."
}
```

`recommendation` is generated by a lightweight LLM call (Gemini Flash) that reads the breakdown
and produces a plain English suggestion. The call is cheap, fast, and optional — if it fails,
the table renders without the recommendation field.

**Eval:** Does the pattern analyzer return a breakdown sorted by error_count? Does the breakdown change correctly when filtered by a different `prompt_version`?

---

### 4.4 Prompt Versioning

**What it does:** Every prompt has a version. When Tommy updates a prompt, the version increments. New reports use the new version. The film analysis cache is invalidated for the old version.

**Prompt files:** `backend/prompts/*.txt`. Each file starts with a version header:

```
VERSION: v1.3
CHANGELOG:
  v1.3 — Added explicit counting instruction: "Count only possessions where the full set initiates and completes."
  v1.2 — Added roster context injection point.
  v1.1 — Initial version.
---
[prompt text begins here]
```

**Version loading:**

```python
def load_prompt(section_type: str) -> tuple[str, str]:
    path = f"backend/prompts/{section_type}.txt"
    with open(path) as f:
        content = f.read()
    version_line = content.split("\n")[0]
    version = version_line.replace("VERSION: ", "").strip()
    prompt_text = content.split("---\n", 1)[1]
    return prompt_text, version
```

Both `prompt_text` and `version` are returned. `version` is saved to `report_sections.prompt_version` and `corrections.prompt_version`.

**Cache invalidation on version change:** The film analysis cache key includes `prompt_version`. A cache entry with `prompt_version = 'v1.2'` is skipped when the current version is `'v1.3'`. Stale entries are purged by the weekly maintenance task.

**Eval:** After incrementing a prompt version, does the next generated report use the new version? Does the cache miss correctly (old cached result not returned for the new version)?

---

## PHASE 5 — LAUNCH

Goal: production infrastructure is hardened, first real coaches are onboarded, and TEX is generating real reports for EYBL programs.

### 5.1 Production Hardening

**Sentry:** All environments. Verify `film_id`, `report_id`, `user_id` appear in every error context.
**Datadog:** Custom metrics live. `tex.dead_letter.written` alert configured at threshold of 3/hour.
**Redis AOF:** Verify `appendonly yes` is set in production Redis config. Test by simulating a restart.
**Startup recovery:** Verify `recover_stuck_jobs()` runs on every worker boot by checking logs.
**Stripe live mode:** Switch from test keys to live keys. Verify webhook endpoint is registered in Stripe Dashboard.
**CORS:** `allow_origins` set to production Vercel URL only. Not `*`.

### 5.2 Admin Tooling

- `GET /admin/users` — list all coaches with report counts and last activity
- `POST /admin/users/{id}/credits` — manually add credits to a coach account
- `GET /admin/dead-letters` — list unresolved dead letter tasks
- `POST /admin/dead-letters/{id}/replay` — replay a dead letter task
- `GET /admin/reports` — all reports with generation times and costs
- `DELETE /admin/films/{id}` — hard delete a film from R2 + DB (Tommy-only, destructive action)

**All admin routes require is_admin check via live DB query. No exceptions.**

### 5.3 Coach Onboarding Flow

First experience for a new coach:

```
1. Sign up with Clerk
2. Welcome screen: "TEX analyzes game film and generates a PDF scouting report in 30-50 minutes."
3. "Create your first team" prompt → team name + level form
4. "Add your roster" prompt → guided roster entry with jersey number and name
5. "Upload your first film" prompt → drag-and-drop upload flow
6. Film processes in background
7. Coach sees "Film Ready" notification
8. "Generate Your Free Report" CTA button appears
9. Report generates
10. Coach downloads PDF
```

Every step after step 1 is optional — coaches can skip to film upload if they understand the product.
The onboarding flow is a UI guide, not a gated wizard. Coach can navigate away at any step.

### 5.4 Performance Targets

These are not aspirational. If these are not met, the product is not ready to launch.

```
Film processing (2-hour film):     < 20 minutes for chunk upload to complete
Report generation (2-hour film):   < 50 minutes end-to-end (sections 1-4 parallel ~10min + sections 5-6 ~5min + PDF ~2min)
PDF download:                      < 2 seconds from click to download starting
Dashboard load:                    < 2 seconds
API error rate:                    < 1% on /films and /reports routes
Dead letter rate:                  < 2% of all tasks
```

If any target is not met in pre-launch testing, identify the bottleneck before onboarding real coaches. Do not ship a slow product to EYBL coaches who have scouting deadlines.

---

## FEATURE STATUS TRACKER

```
Feature                                  Phase   Status
──────────────────────────────────────────────────────────────
Auth (Clerk + Neon sync)                 1       Not started
Teams CRUD                               1       Not started
Roster management                        1       Not started
Film upload (browser → R2)               1       Not started
Dashboard                                1       Not started
Film processing worker (FFmpeg + Gemini) 2       Not started
Film status polling (frontend)           2       Not started
Chunk URI expiry management              2       Not started
Payment gate (Stripe)                    3       Not started
Report orchestrator (chord)              3       Not started
Parallel sections 1-4                    3       Not started
Synthesis sections 5-6 + fallback        3       Not started
PDF assembly + delivery                  3       Not started
Report status + download (frontend)      3       Not started
Admin gate                               4       Not started
Training mode UI (corrections)           4       Not started
Pattern analyzer                         4       Not started
Prompt versioning                        4       Not started
Production hardening (Sentry + DLQ)      5       Not started
Admin tooling                            5       Not started
Coach onboarding flow                    5       Not started
```

---

*Last updated: Phase 0 — Context Engineering*
*Zero product code ships before all 12 context documents are committed.*
