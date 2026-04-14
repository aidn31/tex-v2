# ROADMAP.md — TEX v2

Live progress tracker. Updated by Claude Code after every completed task.
Tommy also updates manually when needed.
This file is the single source of truth for where the project is right now.

Read CLAUDE.md before this. Read PRD.md for full feature specs.

---

## CURRENT STATE

**Current Phase:** 3 — Report Generation
**Active Task:** 3.17 — Phase 3 eval pass
**Blockers:** Gemini context caching provisioning bug — blocks eval on 3.3 and 3.4
**Last Updated:** April 13, 2026

---

## ACTIVE BLOCKERS

### Gemini Context Caching — Blocks 3.3 and 3.4 eval

Error returned when caching all 4 video chunks (~1.6M tokens):
  400 INVALID_ARGUMENT: Cached content is too large.
  total_token_count=1616899, max_total_token_count=0

Root cause: Google backend provisioning bug. Paid Tier 1 accounts get misclassified
and the context cache quota is hardcoded to 0 despite active billing. 1-2 chunks
cache successfully. 3+ chunks fail.

Confirmed:
- Not a code bug. Code is correct.
- Google Cloud Console shows Paid Tier = Unlimited, Free Tier = 0
- A quota override in IAM → Quotas & Sts is causing the mismatch
- Override removed twice via Console — neither attempt resolved it

Resolution in progress:
- Post live on discuss.ai.google.dev tagging @chunduriv (Google engineer who
  manually resyncs misclassified accounts)
- Tweeted @GoogleDevsInfo with error details and project ID gen-lang-client-0174334843

Fallback (Option C) — ready if no response within 24 hours:
  Skip caching entirely. Pass video URIs directly to each section call.
  Each of the 4 parallel section tasks re-processes the video independently.
  Cost is higher (~4x input tokens for sections 1-4) but no dependency on
  broken Google infrastructure. Re-enabling caching later requires changing
  one argument in the orchestrator — no structural refactor.

Impact:
- 3.3 and 3.4 are built but cannot be evaled until this resolves
- 3.5, 3.6, and 3.7 through 3.17 are unblocked and buildable now
- Phase 3 eval (3.17) cannot close until 3.3 and 3.4 eval passes

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
3.1  Stripe integration                 ✓ Done          Checkout sessions + webhooks (per-report). See notes below.
3.2  Payment gate middleware            ✓ Done          First report free, else credits. See notes below.
3.3  generate_report orchestrator       Built (eval blocked)  Context cache + Celery chord. Bundled with 3.4. Eval blocked on Gemini billing — see notes below.
3.4  run_section task (sections 1-4)    Built (eval blocked)  Parallel Gemini 2.5 Pro calls. Bundled with 3.3. Eval blocked on Gemini billing.
3.5  run_synthesis_sections callback    ✓ Done          Sections 5-6 sequential via Gemini Flash. See notes below.
3.6  Claude fallback (sections 5-6)     ✓ Done          Auto-triggers on Flash failure. See notes below.
3.7  WeasyPrint PDF assembly            ✓ Done          services/pdf.py + templates/report.css. See notes below.
3.8  PDF upload to R2                   ✓ Done          assemble_and_deliver task + R2 upload. See notes below.
3.9  Chunk cleanup post-report          ✓ Done          Gemini URIs + R2 chunks deleted after PDF upload. See notes below.
3.10 Dead letter task handler           ✓ Done          All 8 tasks write dead letters on final retry.
3.11 Startup recovery function          ✓ Done          recover_stuck_jobs() on worker_ready signal in celery_app.py.
3.12 POST /reports route                ✓ Done          Payment gate + free/credit/stripe paths. See notes below.
3.13 GET /reports/{id} route            ✓ Done          Status + sections progress + presigned PDF URL. Also GET /reports list.
3.14 Frontend — report status page      ✓ Done          /reports/[id] + team page reports tab + api.ts wrappers. Bundled with 3.15.
3.15 Frontend — PDF download            ✓ Done          Bundled into 3.14 — presigned URL download button on report page.
3.16 In-app notifications               ✓ Done          Backend routes + api.ts + dashboard notification display.
3.17 Phase 3 eval pass                  Not started     PDF downloaded, correct content, paid gate works
```

### Task 3.1 — Stripe integration (April 10, 2026)

**Eval: PASSED.** End-to-end test with Stripe CLI forwarding: create-checkout-session returned `checkout_url` + `payment_id`, paid with `4242…`, webhook fired `checkout.session.completed`, payment row in Neon confirmed at `status=complete`, `stripe_payment_intent_id` populated, `amount_cents` matched.

**Decision:** Per-report payment model (Option A), confirmed by Tommy. Credit packs deferred — credits exist only as failure compensation per ARCHITECTURE.md DECISIONS.

**Built:**
- `backend/services/stripe_client.py` — `get_stripe()` lazy-loads `STRIPE_SECRET_KEY` at call time so the app boots without Stripe configured. `verify_webhook()` validates signature against `STRIPE_WEBHOOK_SECRET`.
- `backend/routers/stripe.py` with two endpoints:
  - `POST /stripe/create-checkout-session` — auth-gated. Validates team + films belong to the user, lazy-creates a Stripe Customer on first checkout (writes `users.stripe_customer_id`), pre-inserts a `payments` row with a unique placeholder `stripe_session_id` (`'pending_' || gen_random_uuid()`), creates a Stripe Checkout session in `payment` mode using `STRIPE_REPORT_PRICE_ID`, then updates the row with the real session id, amount, and currency. `tex_payment_id`/`tex_user_id`/`tex_team_id`/`tex_film_ids` are passed in `metadata` AND `payment_intent_data.metadata` so both `checkout.session.completed` and `payment_intent.payment_failed` can find the row.
  - `POST /stripe/webhook` — verifies signature, handles `checkout.session.completed` (sets `status='complete'`, captures `stripe_payment_intent_id`, `amount_cents`, `currency`) and `payment_intent.payment_failed` (sets `status='failed'`). Unhandled event types log + return 200.
- `models/schemas.py` — `CheckoutSessionCreate` and `CheckoutSessionResponse`.
- `main.py` wires the new router at `/stripe`.

**Schema note:** `payments.status` was documented as `'pending' | 'complete' | 'refunded'`. The webhook now also writes `'failed'` on `payment_intent.payment_failed`. Updated the SCHEMA.md comment to match. No DB migration needed — the column has no CHECK constraint.

**Out of scope (deferred to 3.2/3.3):**
- Report row creation in the webhook handler — that happens when `POST /reports` and the payment gate are wired in 3.2.
- `generate_report.delay()` enqueue — task 3.3.
- `STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`/`STRIPE_REPORT_PRICE_ID` were already in `.env.example` from prior scaffolding.

**What Tommy needs to do before testing live:**
1. In Stripe test mode dashboard, create a Product "TEX Scouting Report" with a $49 one-time price. Copy the price id (`price_...`) into `backend/.env` as `STRIPE_REPORT_PRICE_ID`.
2. Set `STRIPE_SECRET_KEY=sk_test_...` and `STRIPE_WEBHOOK_SECRET=whsec_...` in `backend/.env`.
3. Use `stripe listen --forward-to localhost:8001/stripe/webhook` to forward webhooks during local testing — the CLI prints the `whsec_...` to put in `STRIPE_WEBHOOK_SECRET`.

### Task 3.2 — Payment gate middleware (April 10, 2026)

**Eval: PASSED.** End-to-end test via `scripts/test_checkout.sh` → paid with `4242…` test card. Webhook fired `checkout.session.completed`, single DB transaction completed atomically: payment row updated to `status=complete`/`report_id` populated/`stripe_payment_intent_id=pi_3TKsTl…`, reports row created in `status=pending`, report_films join row created, users.reports_used incremented.

**Built:**
- `backend/services/payment_gate.py`:
  - `check_payment_gate(user_id)` → `'free' | 'credit' | 'stripe_required'`. Reads a fresh `users` row every call (never trusts cached JWT data — `reports_used` and `report_credits` mutate from webhook handlers).
  - `consume_entitlement(cur, user_id, path)` — takes a **cursor** (not a connection) so the caller can run it inside its own transaction. Always increments `reports_used`; decrements `report_credits` only on the `credit` path, with a race guard (`WHERE report_credits > 0` + `rowcount` check) that raises `ValueError` if a concurrent request already consumed the last credit.
  - Constants `FREE`, `CREDIT`, `STRIPE_REQUIRED` exported for callers.

- `backend/routers/stripe.py` webhook refactor:
  - `checkout.session.completed` now runs a single DB transaction containing: UPDATE payments → INSERT reports → INSERT report_films (loop over `tex_film_ids` from metadata) → UPDATE payments.report_id → `consume_entitlement(cur, user_id, STRIPE_REQUIRED)`. All-or-nothing — a failure on any step rolls back the whole thing, so we never end up with half-created reports.
  - Added synthetic-event tolerance: if `checkout.session.completed` arrives without `tex_*` metadata (e.g. from `stripe trigger` during dev), log a warning, update the payment row to complete if it exists, and return 200. No report created.
  - Introduced `PLACEHOLDER_PROMPT_VERSION = "v0.0.0-phase3-dev"` constant at the top of the file with a comment noting that task 3.4 (run_section) will replace it with the real prompt loader output.
  - `# TODO(3.3)` marker at the exact site where `generate_report.delay(report_id)` will be added once the orchestrator task exists.

**What's deliberately NOT wired:**
- `generate_report.delay()` — task 3.3.
- Free / credit paths are exercised only by `check_payment_gate` unit logic; there's no caller yet because `POST /reports` is an empty stub until task 3.12.
- The placeholder `prompt_version` will look weird in Neon until 3.4 — that's expected.

**Pricing note:** The Stripe Product Tommy created in test mode is priced at $29.99, not the $49 STARTER tier from COSTS.md. That's a Stripe-dashboard-side value — no code change needed to adjust it, just edit the Product's Price in Stripe and the `amount_cents` on future checkout sessions will match. Flagging for the cost model review before launch.

### Tasks 3.3 + 3.4 — generate_report orchestrator + run_section (bundled, April 11, 2026)

**Decision:** Bundled because they're tightly coupled — 3.3 fires a Celery chord that calls 3.4, and splitting meant throwaway stub work on both sides plus real Gemini context cache creation with nothing to consume it. Scope C per session plan. Tommy approved.

**Built:**

*Prompt files (`backend/prompts/`):* All 6 section prompts copied verbatim from PROMPTS.md at version `v1.0`:
- `offensive_sets.txt`, `defensive_schemes.txt`, `pnr_coverage.txt`, `player_pages.txt` (sections 1-4, Gemini 2.5 Pro)
- `game_plan.txt`, `adjustments_practice.txt` (sections 5-6, Gemini 2.5 Flash — loaded but not called until 3.5)

*`services/prompts.py`:* `load_prompt(section_type)` → `(text, version)`. Parses the `VERSION:` header, splits on the `\n---\n` delimiter, returns the prompt body + version string. Verified against all 6 files — chars counts: 3173, 3059, 3781, 2539, 3547, 3284.

*`services/ai/` — new package:*
- `base.py` — `AIVideoProvider` ABC with `create_context_cache`, `delete_context_cache`, `analyze_video_cached`. Tracks `last_tokens_input` / `last_tokens_output` as instance attrs for cost accounting.
- `gemini.py` — `GeminiProvider` concrete implementation. `create_context_cache` builds a `CreateCachedContentConfig` with video chunk `Part.from_uri(...)` entries, a synthesis text block (or a "not available" placeholder if the film's synthesis failed), and the roster string. TTL defaults to 3600 seconds. `analyze_video_cached` uses `GenerateContentConfig(cached_content=cache_name)` and reads `response.usage_metadata.{prompt_token_count, candidates_token_count}`. Empty outputs raise `RuntimeError` so a silent failure can't land in Neon.
- `router.py` — `get_ai_provider()` — single import point per CLAUDE.md AI PROVIDER RULES. Reads `AI_VIDEO_PROVIDER` env var (default: `gemini`).

*`services/roster_format.py`:* `format_roster_for_prompt(team_id)` fetches the roster from Neon and renders one line per player in the PROMPTS.md context format: `#3 Marcus Williams, PG, 6'2", primary_initiator, right-handed`. Empty rosters return `(no roster data available)`.

*`tasks/section_generation.py` — `run_section`:*
- Queue `section_generation`, soft 480s / hard 600s / 3 retries / 30s backoff (per AGENTS.md timeout table).
- Idempotency check → `UPDATE status='processing'` → `load_prompt` → `acquire_gemini_slot('gemini-2.5-pro')` → `provider.analyze_video_cached` → persist `content`, `model_used='gemini-2.5-pro'`, `prompt_version`, `tokens_input`, `tokens_output`, `generation_time_seconds`.
- On `SoftTimeLimitExceeded`: marks the section errored, writes dead letter, raises.
- On generic exception at final retry: marks errored, writes dead letter, raises. Earlier retries use exponential backoff: `30 * 2^retries`.

*`tasks/report_generation.py` — `generate_report`:*
- Queue `report_generation`, soft 1500s / hard 1800s / 3 retries.
- Full execution per AGENTS.md: idempotency → mark processing → fetch film_ids from `report_films` → verify all films `status='processed'` (if any still processing → `self.retry(countdown=60)`) → `get_valid_chunk_uris` for each film (auto-reuploads expired chunks) → fetch synthesis documents from `film_analysis_cache` → format roster → `acquire_gemini_slot` → `create_context_cache` → save `context_cache_uri` to the reports row → `INSERT ... ON CONFLICT DO UPDATE` for all 6 section rows → fire chord.
- Chord: `chord(group(run_section.s × 4))(run_synthesis_sections.s(report_id, cache_uri))`. The orchestrator returns as soon as the chord is fired — it does not wait.
- Retry exceptions (`celery.exceptions.Retry`) are caught and re-raised unchanged so Celery's retry machinery works normally.

*`tasks/report_generation.py` — `run_synthesis_sections` (STUB):*
- Full version lands in task 3.5 (Gemini 2.5 Flash sections 5-6 with Claude fallback).
- Current stub: marks sections 5-6 as `error` with message `'Deferred to task 3.5 — run_synthesis_sections stub'`, logs chord completion.
- `finally` block always runs: calls `provider.delete_context_cache(cache_uri)` so Gemini cache storage isn't billed after the chord, then clears `reports.context_cache_uri`. Cache deletion is wrapped in try/except — a failure here doesn't error the task (weekly maintenance is the backstop).
- Reports stay in `status='processing'` at the end of 3.3+3.4 — no terminal state transition, no PDF assembly, no notify_coach. Those are tasks 3.6-3.8.

*`routers/stripe.py`:* `TODO(3.3)` replaced with `generate_report.delay(report_id)` — enqueue happens AFTER the DB transaction commits so a worker can't pick up the task before the `reports` row is visible. Import is done at call time inside the webhook handler to avoid circular imports at module load.

**Verified:**
- `python -c "from main import app"` succeeds in api container.
- Celery worker restart picks up all 7 tasks across 4 queues on boot (`film_processing.{process_film,extract_chunk,run_chunk_synthesis}`, `report_generation.{generate_report,run_synthesis_sections}`, `section_generation.run_section`, `notifications.notify_coach`).
- Full import graph smoke test: `get_ai_provider()` → `GeminiProvider` instance, all 6 prompts load at `v1.0`, all task symbols import cleanly.

**Eval attempted April 11, 2026 — BLOCKED on Gemini billing.**

End-to-end flow ran cleanly through the paid-checkout path: Stripe webhook fired, payment row updated, reports + report_films rows created atomically, `generate_report.delay()` enqueued correctly, worker picked up the task, and `generate_report` ran through steps 1-6 (idempotency check, mark processing, fetch films, validate film state, collect chunk URIs, fetch synthesis docs, format roster).

**Failure:** step 7 (`provider.create_context_cache(...)`) returned a Gemini API error:

```
400 INVALID_ARGUMENT. Cached content is too large.
total_token_count=1616933, max_total_token_count=0
```

`max_total_token_count=0` is the smoking gun — the project tied to `GEMINI_API_KEY` has zero allocated cache quota. **Context caching on the Gemini Developer API is a paid feature** — free-tier API keys have it disabled at the project level, not blocked by content size. The cache request itself is well-formed; the project just isn't permitted to create caches at all.

**No code changes required to fix.** Tommy enables billing at https://aistudio.google.com/app/apikey on the project that owns this API key, waits ~5 minutes for quota to propagate, then re-runs the same eval with the same film and flow. The exact same code path will succeed.

**State left behind by the failed eval:**
- `report 739d4766-b95b-41d1-af6c-f862d8586fe2` — status `processing` (became `error` after retries dead-lettered), no `report_sections` rows (error fired before step 9 inserted them — clean state, no orphans).
- `payments` row for the failed eval — `status=complete`, `amount_cents=2999`. Money was taken (test mode) before the orchestrator failed. This is the "technical failure" path described in CLAUDE.md PAYMENT RULES — should trigger `apply_failure_credit` to grant a free credit, but that's task 3.5 / 3.10 (dead letter handler) which isn't built yet. Manual workaround for now: leave the payment row as-is and increment Tommy's `users.report_credits` by 1 if he wants to recover the test charge.
- Dead-lettered task in `dead_letter_tasks` (3 retries exhausted) — the task fixture is in place for replay once billing is enabled.
- **Dollar burn from this eval: $0.** Gemini rejected the cache creation BEFORE any billable token was processed. Stripe took $29.99 in test mode (not real money).

**Why this matters beyond the eval:** the entire COSTS.md margin model depends on context caching working. Without it, sections 1-4 each re-read the full 1.6M video tokens at $2.50/M — blended cost per report jumps from ~$2.69 to ~$18.92 (7x) and Tier 1 STARTER's 71.7% margin goes negative. Context caching is not a performance optimization; it's the load-bearing economic assumption. Confirming it works in production-equivalent conditions BEFORE building 3.5-3.8 was deliberate, and finding this billing blocker now (instead of after 3.5-3.8 were stacked on top) is the right kind of failure.

**Resolution path tomorrow:**
1. Tommy enables billing on the Google AI project at https://aistudio.google.com/app/apikey
2. Wait ~5 minutes
3. Grab a fresh Clerk JWT, re-run `./scripts/test_checkout.sh` with the same TEAM_ID + FILM_ID
4. Pay with `4242…`
5. Watch `docker logs tex-v2-worker-1 -f` for `generate_report: chord fired` followed by 4 × `run_section complete` over 3-8 minutes
6. Verify `report_sections` shows 4 `complete` rows with real content + non-zero tokens, 2 `error` rows with the "Deferred to task 3.5" message
7. Mark 3.3 + 3.4 status as `✓ Done` in this file and update CURRENT STATE

**Pricing visibility:** sections 1-4 will burn real Gemini dollars per the COSTS.md model. A 2-hour film without cache hit is ~$2.69 per report (see COSTS.md § BLENDED COST). Keep test runs minimal while 3.5-3.8 are being built — one full end-to-end test is enough to verify 3.3+3.4 once billing is on.

### Task 3.5 — run_synthesis_sections callback (April 13, 2026)

**Eval: BLOCKED on same Gemini billing blocker as 3.3/3.4.** Code is complete and all imports verified in Docker container. Will eval with 3.3/3.4 once caching resolves (or via Option C fallback).

**Built:**

*`services/ai/base.py`:* Added `analyze_text(context, prompt, section_type)` abstract method to `AIVideoProvider`. Text-only interface for sections 5-6 — no video, no cache. Returns generated text. Updates `last_tokens_input` / `last_tokens_output`.

*`services/ai/gemini.py`:* Added `GEMINI_FLASH_MODEL = "gemini-2.5-flash"` constant and `analyze_text()` implementation. Combines context + prompt with a `---` / `INSTRUCTIONS:` delimiter, calls `generate_content` against Flash, tracks token usage. Empty response raises `RuntimeError`.

*`tasks/report_generation.py` — `run_synthesis_sections` full implementation:*
Replaced the stub with the full AGENTS.md execution sequence:
1. Fetch all 6 section rows → count errored/completed from sections 1-4
2. If all 4 errored → `_handle_all_sections_errored` (mark report error + `_apply_failure_credit` + `notify_coach`)
3. Build synthesis context from completed sections 1-4 content
4. Run section 5 (game_plan) via `_run_text_section` → Gemini Flash + `acquire_gemini_slot("gemini-2.5-flash")`
5. Build section 6 context (sections 1-4 + game_plan if it succeeded)
6. Run section 6 (adjustments_practice) via `_run_text_section`
7. Cache sections 1-4 outputs to `film_analysis_cache`
8. `assemble_and_deliver.delay(report_id)` — `TODO(3.7)` marker, task doesn't exist yet

*Helper functions added:*
- `_build_synthesis_context(section_rows)` — concatenates completed section content with labeled headers
- `_run_text_section(report_id, section_type, context, prompt_version)` — marks processing → loads prompt → rate limit → Flash call → persists result. Returns content on success, `None` on failure. Failure marks section errored but does NOT fail the whole task. `TODO(3.6)` marker where Claude fallback goes.
- `_apply_failure_credit(user_id, report_id)` — increments `users.report_credits` by 1
- `_handle_all_sections_errored(report_id)` — error + credit + notify_coach pipeline
- `_mark_section_error(report_id, section_type, message)` — writes error to report_sections
- `_cache_section_outputs(report_id, section_rows, prompt_version)` — writes sections 1-4 to film_analysis_cache

*Error handling:* `SoftTimeLimitExceeded` → mark report error + dead letter. Generic exception at final retry → mark error + dead letter. Earlier retries use 60s × 3^retries backoff (60s, 180s per AGENTS.md). Celery `Retry` exceptions pass through unchanged.

*Key design decisions:*
- Section 5/6 failures are individual — they mark the section errored but don't fail the task. The report proceeds as partial. `assemble_and_deliver` (3.7) handles partial reports.
- If section 5 fails, section 6 still runs with sections 1-4 context only (no game plan). Degraded but useful.
- Cache deletion stays in `finally` — runs on every exit path per AGENTS.md.

**Verified:**
- All imports pass in Docker (`api` container)
- All 7 Celery tasks registered across 4 queues
- Both section 5-6 prompts load at `v1.0` (3547 and 3284 chars)
- `analyze_text` method available on `GeminiProvider` via `get_ai_provider()`
- Flash rate limit bucket exists at 15 req/min

**What's NOT wired yet:**
- `assemble_and_deliver.delay()` — task 3.8 (now that PDF service exists)

### Task 3.6 — Claude fallback for sections 5-6 (April 13, 2026)

**Eval: BLOCKED on same Gemini billing blocker as 3.3/3.4.** Code is complete, all imports verified. The fallback path can't be tested end-to-end until a real section 5/6 Flash call fails, but the Claude provider's `analyze_text` method is structurally correct and the import/instantiation path is verified.

**Built:**

*`services/ai/anthropic.py` — `ClaudeProvider`:*
New concrete implementation of `AIVideoProvider`. Only `analyze_text` is functional — video methods raise `NotImplementedError` (Claude is never used for sections 1-4). Uses `anthropic==0.36.*` SDK (already in requirements.txt). Model: `claude-3-5-sonnet-20241022`. Max output tokens: 8192. Tracks `last_tokens_input` / `last_tokens_output` from `message.usage`. Same prompt structure as Flash (`context + --- + INSTRUCTIONS: + prompt`). Empty response raises `RuntimeError`. `ANTHROPIC_API_KEY` env var (already in `.env.example`).

*`services/ai/router.py` — `get_fallback_provider()`:*
New function returning `ClaudeProvider()`. Per CLAUDE.md AI PROVIDER RULES, `router.py` is the only file that imports concrete providers — verified by grep.

*`tasks/report_generation.py` — `_run_text_section` refactored:*
Replaced the `TODO(3.6)` marker with a real Flash → Claude fallback. Structure:
1. Mark processing + load prompt (shared by both paths)
2. Try Gemini Flash inside inner try/except
3. If Flash raises → log warning → call `get_fallback_provider().analyze_text()`
4. Persist result using `model_used` set by whichever path succeeded
5. If BOTH fail → outer except marks section errored

`model_used` is `"gemini-2.5-flash"` on the primary path, `"claude-3-5-sonnet"` on fallback — recorded in `report_sections` so Tommy can see exactly which model generated each section.

**Verified:**
- `ClaudeProvider` instantiates, `analyze_text` method exists
- Video methods raise `NotImplementedError` as expected, `delete_context_cache` is a no-op
- Only `router.py` imports concrete providers (grep confirmed)
- All 7 Celery tasks still registered across 4 queues
- `ANTHROPIC_API_KEY` already in `.env.example`

### Task 3.7 — WeasyPrint PDF assembly (April 13, 2026)

**Eval: PASSED.** Generated PDFs with full, partial, and all-error section data. Cover page, content sections, error placeholders, partial banner, page numbers, and footer all render correctly.

**Built:**

*`services/pdf.py`:*
- `assemble_pdf(sections, team_name, report_date, is_partial)` → `bytes`. Takes section dicts from DB, builds HTML, renders via WeasyPrint. Returns raw PDF bytes ready for R2 upload.
- `_build_html()` — assembles full HTML document: cover page, optional partial banner, 6 section divs in master PDF order.
- `_text_to_html()` — lightweight converter for AI-generated section text. Handles: UPPERCASE headings → `<h3>`, `#NUMBER NAME` → player headers, `---` → profile separators, `TRIGGER N:` → trigger headers, `If:/Then:/Tell your team:` → bold-labeled trigger details, `DAY N` → practice plan headers, `- ` → bullet lists, blank lines → paragraph breaks.
- `_build_cover_page()` — dark background, TEX branding in orange, team name, date, footer.
- `SECTION_ORDER` — 6-tuple matching the master PDF structure from CLAUDE.md product flow.

*`templates/report.css`:* Print-optimized CSS (not Tailwind). Letter-size pages, 0.75in margins, `@page` footer with "TEX Scouting Report" + page numbers. Cover page suppresses footer. Orange (#F97316) accent on section titles, player headers, trigger headers. Error sections get red-themed placeholder with light pink background.

*`requirements.txt`:* Pinned `pydyf==0.11.*` — WeasyPrint 62.3 is incompatible with pydyf 0.12.x (missing `transform` method on `Stream`).

**Verified visually:**
- Cover page: TEX brand centered on dark bg, team name, date, footer tagline
- Content sections: headings, paragraphs, bullet lists, justified text
- Player profiles: orange headers with jersey number, profile sub-sections, HR separators
- Trigger blocks: orange headers, indented If/Then/Tell your team labels
- Practice plan: DAY headers with bottom borders, drill bullet lists
- Error sections: red heading, pink background, italic error message
- Partial banner: yellow warning at top of page 2
- Page numbers: bottom-right on every page except cover

### Task 3.8 — PDF upload to R2 + assemble_and_deliver task (April 13, 2026)

**Eval: BLOCKED on same Gemini billing blocker as 3.3/3.4.** Code is complete and all imports verified. 8 Celery tasks now registered. Will eval end-to-end with 3.3/3.4.

**Built:**

*`services/r2.py` — `upload_bytes_to_r2()`:*
New method that uploads raw bytes directly to R2 via boto3 `put_object` — avoids writing PDF to /tmp. Takes `bucket`, `key`, `data` (bytes), and `content_type` (defaults to `application/octet-stream`, set to `application/pdf` for reports).

*`tasks/report_generation.py` — `assemble_and_deliver`:*
New Celery task on `report_generation` queue. Per AGENTS.md execution sequence:
1. Fetch report + idempotency check (skip if already `complete`/`partial`)
2. Fetch team name for cover page
3. Fetch all 6 section rows
4. Count errored sections:
   - 6 errored → full failure → mark error + apply credit + notify coach
   - 1-5 errored → partial report path
   - 0 errored → complete report path
5. Call `assemble_pdf()` with sections, team name, today's date, `is_partial` flag
6. Upload PDF bytes to R2: `reports/{user_id}/{report_id}/scouting_report.pdf`
7. UPDATE reports: `status`, `pdf_r2_key`, `completed_at`, `generation_time_seconds`
8. Enqueue `notify_coach` with appropriate type (`report_complete` or `report_partial`)
9. `TODO(3.9)` marker for chunk cleanup

*`run_synthesis_sections` wired:* Replaced `TODO(3.7)` with `assemble_and_deliver.delay(report_id)`.

**Error handling:** Same pattern as other tasks — `SoftTimeLimitExceeded` + generic exception at final retry → mark report error + dead letter. Backoff: 60s × 3^retries. Celery Retry passthrough.

**Task registration:** 8 tasks now registered (was 7): `assemble_and_deliver` added to `report_generation` queue.

### Task 3.12 — POST /reports route (April 13, 2026)

**Built:**

*`routers/reports.py` — `POST /reports`:*
Auth-gated. Validates team + films belong to user, films are `processed`. Checks payment gate:
- `free` or `credit` → single DB transaction: INSERT report + report_films + consume_entitlement → enqueue `generate_report.delay()` after commit → return `{ report_id, payment_required: false }`
- `stripe_required` → return `{ payment_required: true }` so frontend redirects to Stripe checkout

Validations: films must exist, belong to the correct team, and be in `processed` status. Race guard on credits (409 if exhausted between check and consume).

*`models/schemas.py`:* Added `ReportCreate`, `ReportCreateResponse`, `ReportResponse`.

*`routers/stripe.py`:* Replaced `PLACEHOLDER_PROMPT_VERSION` with `load_prompt("offensive_sets")[1]` — Stripe-created reports now get the real `v1.0` version instead of `v0.0.0-phase3-dev`.

### Task 3.9 — Chunk cleanup post-report (April 13, 2026)

**Built:**

*`services/r2.py` — `delete_from_r2(bucket, key)`:* New method. Best-effort — swallows exceptions so cleanup failures never block delivery.

*`tasks/report_generation.py` — `_cleanup_chunks(report_id)`:*
Called inside `assemble_and_deliver` AFTER the report status is written to DB (per CLAUDE.md hard rule: "Never delete R2 chunks before reports.status = complete"). Fetches all film_chunks for the report's films, then for each chunk:
1. Deletes Gemini file URI via `delete_gemini_file()` (already existed in `services/gemini_files.py`)
2. Updates `film_chunks.gemini_file_state = 'deleted'`
3. Deletes R2 chunk file via `delete_from_r2()`

All best-effort — individual chunk failures are logged but don't block the pipeline.

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

*Last updated: April 13, 2026 — Phase 3 underway. 3.1, 3.2, 3.5-3.16 done. 3.3 and 3.4 built but eval blocked on Gemini provisioning bug. Active task: 3.17 (eval — blocked on Gemini).*
