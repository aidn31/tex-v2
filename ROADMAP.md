# ROADMAP.md — TEX v2

Live progress tracker. Updated by Claude Code after every completed task.
Tommy also updates manually when needed.
This file is the single source of truth for where the project is right now.

Read CLAUDE.md before this. Read PRD.md for full feature specs.

---

## CURRENT STATE

**Current Phase:** 2 — Film Pipeline ✓ COMPLETE
**Active Task:** None — Phase 2 complete. Phase 3 ready to begin.
**Blockers:**
- Next.js `headers()` async warning on /dashboard and /upload routes (non-blocking, cosmetic)
**Last Updated:** April 10, 2026

---

## PHASE 0 — CONTEXT ENGINEERING ✓ COMPLETE

Goal: All context documents written and committed before any product code.

```
Task                        Status      Notes
──────────────────────────────────────────────────────────────────
GitHub repo created         ✓ Done      github.com/aidn31/tex-v2
CLAUDE.md                   ✓ Done      Project rules and context
ARCHITECTURE.md             ✓ Done      Full system design
AI_STRATEGY.md              ✓ Done      Intelligence roadmap and moat
SCHEMA.md                   ✓ Done      Complete database schema
PRD.md                      ✓ Done      Product requirements by phase
PROMPTS.md                  ✓ Done      All 6 Gemini section prompts
EVALS.md                    ✓ Done      Eval rubrics per feature and prompt
COSTS.md                    ✓ Done      Per-report cost model and pricing tiers
DECISIONS.md                ✓ Done      17 architectural decisions logged
AGENTS.md                   ✓ Done      All 9 Celery tasks defined
STACK.md                    ✓ Done      Full tech stack with rationale
VISION.md                   ✓ Done      Long-term product vision
FLOWS.md                    ✓ Done      Every screen, state, and user action
MCP.md                      ✓ Done      MCP server configuration
ROADMAP.md                  ✓ Done      This file
```

Phase 0 is complete. Product code begins now.

---

## PHASE 1 — FOUNDATION

Goal: A coach can sign up, create a team, build a roster, and upload a film to R2.
No AI. No report generation. Just the infrastructure working end-to-end.

Eval: Does a film file land in R2 with a correct row in Neon scoped to the right user?

```
Task                                    Status          Notes
──────────────────────────────────────────────────────────────────────────
1.1  Repo structure scaffolded          ✓ Done          backend/ + frontend/ directories
1.2  Docker Compose + local env         ✓ Done          API + worker + Redis
1.3  Neon dev branch created            ✓ Done          dev branch, connection verified
1.4  Database migrations (001–015)      ✓ Done          All 15 tables + pgvector applied to dev
1.5  FastAPI app skeleton               ✓ Done          main.py, routers, db.py, celery queues
1.6  Clerk auth — JWT middleware        ✓ Done          verify_clerk_jwt(), get_current_user()
1.7  Clerk webhook handler              ✓ Done          user.created + user.deleted handled
1.8  Teams CRUD                         ✓ Done          POST/GET/PATCH/DELETE /teams
1.9  Roster management                  ✓ Done          POST/GET/PATCH/DELETE /roster
1.10 Film upload — initiate             ✓ Done          POST /films/upload-initiate
1.11 Film upload — complete             ✓ Done          POST /films/upload-complete
1.12 Film upload — abort                ✓ Done          POST /films/upload-abort
1.13 Frontend — Clerk auth pages        ✓ Done          /sign-in, /sign-up + middleware
1.14 Frontend — Dashboard               ✓ Done          /dashboard — teams + recent films + onboarding
1.15 Frontend — Team page               ✓ Done          /teams/[id] — roster + films + reports tabs
1.16 Frontend — Film upload flow        ✓ Done          /upload?team_id=[id] — 3-step flow
1.17 Frontend — api.ts typed wrappers   ✓ Done          16 endpoints typed, no `any`
1.18 Phase 1 eval pass                  ✓ Done          All 3 checks pass — see notes below
```

### Phase 1 Eval Results

**All checks passed on April 4, 2026:**
1. Create team → row in `teams` table ✓
2. Add roster player → row in `roster_players` table ✓
3. Upload film → file in R2 `tex-films-dev` bucket + row in `films` with `status = 'uploaded'` ✓

**Fixes applied during eval:**
- **Clerk webhook blocker:** ngrok free tier regenerates URLs each session, breaking webhook delivery. Fixed by adding `POST /dev/seed-user` — a dev-only route that creates the user row from the JWT on every sign-in. Production webhook handler stays in place.
- **R2 CORS:** Browser PUT to R2 presigned URL was blocked. Fixed by adding CORS policy on `tex-films-dev` bucket (AllowedOrigins: localhost:3000).
- **Token expiry during upload:** Clerk JWTs expire in ~60 seconds. Large file uploads took longer, causing `filmUploadComplete` to fail with 401. Fixed by fetching a fresh token after the R2 upload completes.
- **Webhook handler hardened:** Added logging with full payload on errors, return 200 for unhandled event types.

**Port mappings for local dev:**
- Frontend: `localhost:3000`
- Backend API: `localhost:8001` (remapped from 8000 due to port conflict)
- Redis: `localhost:6380` (remapped from 6379 due to existing local Redis)

---

## PHASE 2 — FILM PIPELINE

Goal: An uploaded film gets processed end-to-end — validated, chunked, uploaded to Gemini, and marked ready for report generation.

Eval: Do chunks upload to Gemini with correct URIs and expiry timestamps in DB?

```
Task                                    Status          Notes
──────────────────────────────────────────────────────────────────────────
2.1  FFprobe validation service         ✓ Done          backend/services/ffprobe.py
2.2  FFmpeg compression + chunking      ✓ Done          backend/services/ffmpeg.py
2.3  Gemini File API integration        ✓ Done          backend/services/gemini_files.py + rate_limit.py
2.4  process_film Celery task           ✓ Done          backend/tasks/film_processing.py
2.5  extract_chunk Celery task          ✓ Done          Same file, Gemini upload + poll + advisory lock
2.6  run_chunk_synthesis placeholder    ✓ Done          Same file, marks status='processed'
2.7  Wire process_film to upload        ✓ Done          POST /films/upload-complete + POST /films/{id}/retry
2.8  URI expiry check service           ✓ Done          backend/services/uri_expiry.py
2.9  Film fingerprint cache             ✓ Done          backend/services/film_cache.py
2.10 Frontend — film status polling     ✓ Done          Polls every 10s, clears on terminal state
2.11 Frontend — processing states       ✓ Done          Badges + error display + retry button
2.12 Phase 2 eval pass                  ✓ Done          Passed April 10, 2026 — see notes below
2.13 Stuck-film bug fix                 ✓ Done          extract_chunk now fails parent film + notifies coach on permanent chunk failure
```

### Phase 2 Eval Results

**Passed on April 10, 2026:**
1. Film uploaded → split into 4 chunks → each chunk uploaded to R2 ✓
2. Each `extract_chunk` task uploaded to Gemini File API and reached `ACTIVE` ✓
3. All 4 `film_chunks` rows show `gemini_file_state = 'active'`, valid `gemini_file_uri`, and `gemini_file_expires_at` ~48 hours from upload ✓
4. `run_chunk_synthesis` fired and marked film as `processed` ✓

**Fixes applied during eval:**
- **`google.generativeai` → `google.genai` migration:** old SDK was deprecated and would have caused runtime failures. Updated `requirements.txt` (`google-generativeai==0.8.*` → `google-genai>=1.0,<2.0`) and rewrote `services/gemini_files.py` to use `genai.Client()`, `client.files.upload(file=..., config={"mime_type": ...})`, `client.files.get(name=...)`, `client.files.delete(name=...)`. State checking simplified — new SDK uses string enum so `file_info.state == "ACTIVE"` works directly.
- **Rate limiter fix:** `upload_to_gemini()` was acquiring slots from the `gemini-2.5-pro` bucket (3/min), which would unnecessarily throttle file uploads and compete with future report generation. Added a separate `gemini-file-api` key (10/min) in `services/rate_limit.py` and switched the upload call to use it.

### Task 2.13 — Stuck-film bug fix (April 10, 2026)

**Problem:** If an `extract_chunk` task permanently failed (after max retries, soft timeout, or unexpected exception), the chunk row was marked `failed` but the parent film stayed in `chunks_uploaded` forever. `run_chunk_synthesis` only fires when all chunks are `active`, so the film never reached a terminal state and the coach saw it stuck "processing" with no error.

**Fix:** Added `_fail_film_from_chunk(film_id, error_message)` helper in `backend/tasks/film_processing.py`. Atomic conditional UPDATE — only marks the film `error` if it's not already in a terminal state (`error` or `processed`), uses `cur.rowcount` to detect whether the transition actually happened, and only fires `notify_coach` on first transition. Race-safe: if multiple chunks fail simultaneously, only the first one notifies.

Wired into all three permanent-failure paths in `extract_chunk`:
- `SoftTimeLimitExceeded` (chunk hit 8-minute hard timeout)
- `GeminiUploadError` after max retries
- Generic `Exception` after max retries

---

## PHASE 3 — REPORT GENERATION

Goal: A coach can trigger a report, all 6 sections generate, and a PDF lands in R2 for download.

Eval: Does the final PDF contain all 7 pages with correct team name and all rostered players?

```
Task                                    Status          Notes
──────────────────────────────────────────────────────────────────────────
3.1  Stripe integration                 Not started     Checkout sessions + webhooks
3.2  Payment gate middleware            Not started     First report free, else credits
3.3  generate_report orchestrator       Not started     Context cache + Celery chord
3.4  run_section task (sections 1-4)    Not started     Parallel Gemini 2.5 Pro calls
3.5  run_synthesis_sections callback    Not started     Sections 5-6 sequential
3.6  Claude fallback (sections 5-6)     Not started     Auto-triggers on Flash failure
3.7  WeasyPrint PDF assembly            Not started     HTML template + static CSS
3.8  PDF upload to R2                   Not started     reports bucket, presigned download URL
3.9  Chunk cleanup post-report          Not started     R2 chunks + Gemini URIs deleted
3.10 Dead letter task handler           Not started     Write to dead_letter_tasks on final retry
3.11 Startup recovery function          Not started     recover_stuck_jobs() on worker boot
3.12 POST /reports route                Not started     Payment check + enqueue orchestrator
3.13 GET /reports/{id} route            Not started     Status + presigned PDF URL
3.14 Frontend — report status page      Not started     /reports/[id] with section progress
3.15 Frontend — PDF download            Not started     Presigned URL → browser download
3.16 In-app notifications               Not started     notify_coach task + frontend badge
3.17 Phase 3 eval pass                  Not started     PDF downloaded, correct content, paid gate works
```

---

## PHASE 4 — TRAINING MODE

Goal: Tommy can review generated sections, mark claims correct or incorrect, and identify systematic error patterns across prompt versions.

Eval: Does a correction save with exact claim text and correct prompt_version?

```
Task                                    Status          Notes
──────────────────────────────────────────────────────────────────────────
4.1  Admin gate middleware              Not started     is_admin DB check on every /admin route
4.2  GET /admin/corrections route       Not started     Filterable by section, version, date
4.3  POST /admin/corrections route      Not started     Save is_correct + correction_text
4.4  GET /admin/pattern-analysis route  Not started     Error rate by category + Gemini Flash rec
4.5  GET /admin/users route             Not started     All coaches + report counts
4.6  POST /admin/users/{id}/credits     Not started     Manual credit grant
4.7  Prompt versioning loader           Not started     load_prompt() returns text + version
4.8  Cache invalidation on version bump Not started     Stale cache skipped on new version
4.9  Frontend — /admin layout           Not started     Admin nav + is_admin gate
4.10 Frontend — corrections UI          Not started     Claim review with ✓ / ✗ + text input
4.11 Frontend — pattern analyzer UI     Not started     Table + recommendation text
4.12 Phase 4 eval pass                  Not started     Correction saved, pattern table accurate
```

---

## PHASE 5 — LAUNCH

Goal: Production infrastructure hardened. First real EYBL coaches onboarded. TEX generating real reports.

Eval: Can a real coach sign up, upload film, and download a PDF scouting report end-to-end?

```
Task                                    Status          Notes
──────────────────────────────────────────────────────────────────────────
5.1  Sentry live in all environments    Not started     film_id + report_id + user_id on all errors
5.2  Datadog custom metrics live        Not started     All tex.* metrics + alerts configured
5.3  Redis AOF verified in production   Not started     appendonly yes confirmed
5.4  Stripe live mode keys              Not started     Switch from test → live
5.5  CORS locked to production URL      Not started     Not * — Vercel URL only
5.6  Performance targets verified       Not started     See PRD.md §5.4 for targets
5.7  Coach onboarding flow              Not started     Welcome screen + guided first report
5.8  GET /admin/dead-letters route      Not started     List unresolved dead letters
5.9  POST /admin/dead-letters/{id}/replay Not started   Replay failed task
5.10 GET /admin/reports route           Not started     All reports with cost data
5.11 First EYBL coach onboarded        Not started     Real coach, real film, real report
5.12 Phase 5 eval pass                  Not started     End-to-end real coach report
```

---

## DECISION LOG — QUICK REFERENCE

Full decisions with rationale are in DECISIONS.md. This is the index only.

```
D-001  Neon over Supabase
D-002  No Neon RLS — app-layer isolation
D-003  Cloudflare R2 over GCS for film storage
D-004  WeasyPrint over Puppeteer for PDF
D-005  Celery over Cloud Tasks
D-006  Gemini 2.5 Pro for video (sections 1-4)
D-007  Celery chord for parallel section generation
D-008  4 separate Celery queues
D-009  Dead letter queue in Neon, not Redis
D-010  Direct Gemini File API (no Twelve Labs)
D-011  Chunks kept in R2 until report complete
D-012  Context cache per report, not per film
D-013  Polling over WebSockets for job status
D-014  Claude 3.5 Sonnet as Flash fallback only
D-015  Film fingerprint cache keyed on hash + prompt_version
D-016  First report free, credits for subsequent
D-017  Free credit on report failure
```

---

## PERFORMANCE TARGETS (from PRD.md §5.4)

These must be met before launching to real coaches. Not aspirational — required.

```
Film processing (2-hour film):     < 20 minutes
Report generation (2-hour film):   < 50 minutes end-to-end
PDF download:                      < 2 seconds from click to download
Dashboard load:                    < 2 seconds
API error rate:                    < 1% on /films and /reports routes
Dead letter rate:                  < 2% of all tasks
```

---

*Last updated: April 3, 2026 — Phase 0 complete. Phase 1 ready to begin.*
