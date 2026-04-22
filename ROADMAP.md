# ROADMAP.md — TEX v2

Live progress tracker. Updated by Claude Code after every completed task.
Tommy also updates manually when needed.
This file is the single source of truth for where the project is right now.

Read CLAUDE.md before this. Read PRD.md for full feature specs.

---

## CURRENT STATE

**Current Phase:** 3 — Report Generation (Phase 4 code also complete), with Phase 2 real completion in flight
**Active Task:** Draft Prompt 0A (`backend/prompts/chunk_extraction.txt`) and Prompt 0B (`backend/prompts/chunk_synthesis.txt`) at `VERSION: v1.0`. All pipeline wiring + schema + fixes are live as of 2026-04-20 evening. Until the prompt files land, `extract_chunk` and `run_chunk_synthesis` fail loudly with `NotImplementedError` pointing at this blocker.
**Blockers:** Prompt text for 0A and 0B is not written. Tommy owns this work (see TRAINING.md). The code path that consumes them is fully wired, the schema migration is applied, and the idempotency retry bug is fixed — the pipeline will start producing real synthesis documents the moment both files exist.
**Last Updated:** April 20, 2026 (evening, post-migration-apply)

**Session log (2026-04-20, evening) — Idempotency fix + AGENTS.md alignment + migration applied to Neon dev:**

Tightened up the mid-day pipeline-wiring commit before Tommy starts writing the prompts. Two code corrections plus one ops action.

*Fix 1 — `extract_chunk` idempotency bug (pre-commit review catch):*
The mid-day scaffolding had a silent-failure mode. Step 4 of `extract_chunk` sets `gemini_file_state='active'` BEFORE Prompt 0A runs at step 5. The idempotency check at the top of the task returned early whenever `state='active'`. So: attempt 1 uploads the Gemini file (setting state='active'), then Prompt 0A raises `NotImplementedError`, then Celery retries. Attempt 2 re-enters the task, sees `state='active'`, and returns silently. No dead letter. No retry exhaustion. No film-error transition. Chunk stuck in `state='active', extraction_status='extracting'` forever.

Fixed in `backend/tasks/film_processing.py`:
- Broadened the SELECT to include `extraction_status` and `gemini_file_uri`.
- Early-return now requires BOTH `gemini_file_state='active'` AND `extraction_status='complete'`.
- New "resume" branch: if the file is already uploaded but extraction is incomplete, reuse the existing `gemini_file_uri` from the DB instead of re-downloading from R2 and re-uploading to Gemini. Saves meaningful time + cost on retries.

Walkthrough of the NotImplementedError stub scenario after the fix (4 total attempts, max_retries=3):
1. Attempt 1 (fresh): `(uploading, r2_key, pending, NULL)` → full path runs → state becomes `(active, extracting, <uri>)` → Prompt 0A raises → `self.retry()`.
2. Attempt 2: `(active, r2_key, extracting, <uri>)` → line 435 check fails (`extraction_status != 'complete'`) → resume branch reuses URI → Prompt 0A raises → `self.retry()`.
3. Attempt 3: same path → raise → `self.retry()`.
4. Attempt 4 (retries=3 >= max_retries=3): same path → generic `except Exception` → UPDATE `gemini_file_state='failed', extraction_status='error'` → `_write_dead_letter(...)` → `_fail_film_from_chunk(...)` transitions film to `error` and enqueues `notify_coach`. MaxRetriesExceededError terminates the task.

Stub is now actually loud.

*Fix 2 — AGENTS.md / code alignment for Prompt 0B model:*
`run_chunk_synthesis` calls `provider.analyze_text()`, which routes to `GEMINI_FLASH_MODEL`. AGENTS.md "TASK: run_chunk_synthesis" step 5 said "Prompt 0B, Gemini 2.5 Pro". Deliberate choice by the mid-day scaffolding (Flash is strong at text-only synthesis and cost is materially lower). Updated AGENTS.md to match the code:
- Step 4 rate bucket: `gemini-2.5-pro` → `gemini-2.5-flash`.
- Step 5 label: "Prompt 0B, Gemini 2.5 Pro" → "Prompt 0B, Gemini 2.5 Flash".
- One sentence added: "Flash is used for Prompt 0B because it is a text-only synthesis over chunk extractions, and Flash's text quality is sufficient. This may be revisited against golden-set grading — see TRAINING.md."

Flash-vs-Pro for 0B is a golden-set decision, not a spec decision. TRAINING.md owns the path forward: when the golden set is live, grade both Flash and Pro outputs against ground truth and flip back to Pro if Flash quality is too thin.

*Ops — Migration 016 applied to Neon dev:*
Ran `ALTER TABLE film_chunks ADD COLUMN extraction_output text, ADD COLUMN extraction_status text NOT NULL DEFAULT 'pending'; CREATE INDEX idx_film_chunks_extraction_status ON film_chunks(film_id, extraction_status);` against Neon dev via `docker compose exec api python` with `services.db.get_connection()` (kept the password out of shell history).

Verification:
- `extraction_output`: text, nullable, no default.
- `extraction_status`: text, NOT NULL, default `'pending'`.
- Index `idx_film_chunks_extraction_status` on `(film_id, extraction_status)` created.
- All 10 existing `film_chunks` rows in dev backfilled to `extraction_status='pending'`.

Migration is irreversible in code — no `DROP COLUMN` written. Safe to roll back by hand if ever needed.

*Git state:*
- Commit `3e6a000` (earlier today, previous session): Option 3 synthesis-only mode + section-cache short-circuit + initial ROADMAP 2026-04-20 entry + TRAINING.md.
- Commit `8a0edca` (mid-day): Prompt 0A + 0B pipeline scaffolding + idempotency fix + AGENTS.md alignment.
- Current commit: ROADMAP updated to reflect the fixes and migration apply.
- Branch: `feature/phase-3`. No merge to main yet.

*What Tommy does next (unchanged, minus step 1 which is now done):*
1. ~~Apply migration 016 to Neon dev.~~ ✓ Done.
2. Draft `backend/prompts/chunk_extraction.txt` (Prompt 0A) at `VERSION: v1.0`.
3. Draft `backend/prompts/chunk_synthesis.txt` (Prompt 0B) at `VERSION: v1.0`.
4. `docker compose up -d --build api worker` to pick up the new code.
5. Re-process a test film. Inspect `film_chunks.extraction_output` + `film_analysis_cache.synthesis_document` for substance.
6. Run a report if synthesis reads like real scouting. Close 3.17 if quality holds.

**Session log (2026-04-20, mid-day) — Pre-processing pipeline wired (steps 1, 4, 5):**

**Session log (2026-04-20, mid-day) — Pre-processing pipeline wired (steps 1, 4, 5):**

Shipped the code scaffolding for the missing Phase 2 work. Prompts themselves are stubbed — both tasks raise `NotImplementedError` with a pointer to this blocker until Tommy drafts the prompt files.

*Migration (step 1):*
- `backend/migrations/016_add_film_chunks_extraction.sql` — adds `extraction_output TEXT` and `extraction_status TEXT NOT NULL DEFAULT 'pending'` to `film_chunks`. Also creates `idx_film_chunks_extraction_status (film_id, extraction_status)` for the atomic last-chunk gate. No CHECK constraint — matches existing `gemini_file_state` style (unconstrained text enum values: `pending` / `extracting` / `complete` / `error`).
- **Not yet applied to Neon dev.** Tommy runs this when ready.

*Provider interface (new method):*
- `services/ai/base.py` — added abstract `analyze_video(uris, prompt, section_type)`. Distinct from `analyze_video_cached` (which uses a context cache sentinel) because Prompt 0A operates on a single chunk at a time with no cross-chunk sharing.
- `services/ai/gemini.py` — implemented on both backends. Dev API path: `Part.from_uri(file_uri=u, mime_type='video/mp4')` + text prompt part → `client.models.generate_content(model=GEMINI_PRO_MODEL, ...)`. Vertex path: `Part.from_uri(u, mime_type='video/mp4')` + text part → `GenerativeModel.generate_content(parts)`. Usage metadata + empty-response guards match the other `analyze_*` methods.
- `services/ai/anthropic.py` — raises `NotImplementedError`. Claude is never used for video.

*extract_chunk wiring (step 4):*
- After Gemini file reaches ACTIVE, the same UPDATE that sets `gemini_file_state='active'` now also sets `extraction_status='extracting'`.
- New block immediately after: `_load_preprocess_prompt('chunk_extraction')` → `acquire_gemini_slot('gemini-2.5-pro')` → `provider.analyze_video(uris=[uri], ...)` → UPDATE `extraction_output` + `extraction_status='complete'`. Logs char count + token usage.
- Atomic last-chunk gate now reads `extraction_status != 'complete'` instead of `gemini_file_state != 'active'`. Closes a race where chunk A could fire synthesis before chunk B finished Prompt 0A.
- All three retry-exhaustion paths (SoftTimeLimit / GeminiUploadError / generic) now also set `extraction_status='error'` when they mark `gemini_file_state='failed'`.

*run_chunk_synthesis (step 5):*
- Full body replaced. Pulls `extraction_output` rows ordered by `chunk_index`, verifies every chunk is `extraction_status='complete'` (bails early with error if not), concatenates with `=== CHUNK N OF M ===` headers, appends roster via `format_roster_for_prompt`.
- `_load_preprocess_prompt('chunk_synthesis')` → `acquire_gemini_slot('gemini-2.5-flash')` → `provider.analyze_text(context, prompt, 'chunk_synthesis')`.
- Result written via UPSERT on `film_analysis_cache.file_hash` — preserves any existing `sections` JSONB (from prior report completions), only overwrites `synthesis_document` / `film_id` / `prompt_version`. Inserts with empty `{}` sections on first write.
- Film marked `processed` at the end. No auto-trigger for pending reports — that wasn't in the prior code and isn't being added.

*Stub helper:*
- `_load_preprocess_prompt(section_type)` in `tasks/film_processing.py` wraps `load_prompt()` and converts the natural `FileNotFoundError` into `NotImplementedError` with a message pointing at ROADMAP ACTIVE BLOCKERS. Existing retry + dead letter machinery in both tasks surfaces the error through 3 retries → dead letter row → film marked `error` → coach notified. No silent failure modes.

*Verified:*
- `python3 -m py_compile` on `tasks/film_processing.py`, `services/ai/base.py`, `services/ai/gemini.py`, `services/ai/anthropic.py` — clean.
- `GeminiProvider()` and `ClaudeProvider()` both instantiate, confirming every abstract method on the ABC now has a concrete implementation.
- `load_prompt('chunk_extraction')` and `load_prompt('chunk_synthesis')` both raise `FileNotFoundError` with the expected paths — the stub wrapper will catch this and re-raise `NotImplementedError`.

*Deliberately NOT touched:*
- Prompt text for 0A and 0B (Tommy's work; see TRAINING.md §2).
- Empty-input guardrails on section prompts 2/3/5/6 (flagged in the earlier-AM log; still lower priority than 0A/0B).
- Brad Beal Elite roster (still 2 players; Tommy to populate before eval).
- Migration is NOT applied to Neon dev yet — awaiting Tommy.

*What Tommy needs to do next:*
1. Apply migration 016 to the Neon dev branch.
2. Draft `backend/prompts/chunk_extraction.txt` (Prompt 0A) at `VERSION: v1.0`. Per TRAINING.md, this prompt teaches Gemini to watch one 20-25 min chunk and output per-possession scouting notes (plays, coverages, tendencies, jersey numbers).
3. Draft `backend/prompts/chunk_synthesis.txt` (Prompt 0B) at `VERSION: v1.0`. Reads all chunk extractions + roster, outputs one consolidated scouting breakdown.
4. Re-upload and process a single test film. Inspect `film_chunks.extraction_output` (should be substantive per-chunk notes) and `film_analysis_cache.synthesis_document` (should be a consolidated breakdown, thousands of characters). Iterate on the prompts if thin.
5. Once synthesis output reads like real scouting, re-run a report end-to-end. If the section PDFs reflect the synthesis content accurately (no hallucinated possession counts), close 3.17.



**Session log (2026-04-20, early AM) — Option 3 eval exposed the missing pre-processing pipeline:**

Ran Option 3 (synthesis-only mode) end-to-end on real film data. Pipeline architecturally succeeded — full report generated in 3 min on a multi-film report including a 2-hour game — but content was heavily hallucinated. Diagnosis traced back through the stack to the upstream pre-processing step, which turns out to have never been implemented.

*What ran successfully:*
- `synthesis-only mode: bypassing video cache (chunk_count=5, text_chars=127)` logged at the start of `generate_report`. Option 3 path is live.
- No `1048576` token-limit errors from Gemini. Long-film blocker is gone.
- 4 parallel `run_section` tasks completed (Gemini 2.5 Pro). 2 synthesis sections completed (Flash).
- `assemble_and_deliver` produced an 18-page PDF and wrote it to R2.
- `notify_coach` fired the in-app notification. Dashboard shows "Complete" with 6/6 sections.
- Stripe CLI webhook delivery worked once `stripe listen --forward-to localhost:8001/stripe/webhook` was restarted.

*What the PDF actually contained:*
- Section 1 (Offensive Sets) — correctly opened with `"NOTE: Game film synthesis failed. No film was available for analysis. This report serves as a structural template..."`, then hallucinated specifics anyway.
- Section 4 (Player Pages) — correctly output `"No data available — film synthesis failed"` for every field on both rostered players.
- Sections 2, 3 (Defensive Schemes, PnR Coverage) — generated confident, plausible-sounding content with specific possession counts (`"[11] possessions"`, `"14 fast-break points"`) and named tendencies. **All fabricated.** No film content backed any of it. The section prompts had no empty-input guardrails.
- Sections 5, 6 (Game Plan, Adjustments) — referenced the fabricated content from sections 2-3 and built on it. Also fabricated.

*Database inspection (queries run against Neon via `docker compose exec -T api python`):*
- Report `970e57dd` was linked to 4 films (2 of which were duplicate `trimmed_15min.mp4` uploads, plus 2 real full games).
- `film_analysis_cache` had **no row** for any of the 4 films. Zero synthesis documents have ever been written, for any film.
- `film_chunks` schema columns: `id, film_id, chunk_index, duration_seconds, r2_chunk_key, gemini_file_uri, gemini_file_state, gemini_file_expires_at, created_at`. **No `extraction_output` or `extraction_status` column exists.**
- Brad Beal Elite roster: **2 players** (`#1 Quentin Colman`, `#2 Trey Pearson`). Test data, not a real roster.

*Code inspection (`backend/tasks/film_processing.py`):*
- `extract_chunk` task: downloads chunk from R2, uploads to Gemini File API, polls to ACTIVE, saves URI + expiry. Then checks if all chunks are ACTIVE and enqueues `run_chunk_synthesis`. **No `analyze_video` call. No Prompt 0A execution. No extraction output generated.** The docstring makes no mention of Prompt 0A either.
- `run_chunk_synthesis` task: docstring verbatim — `"Phase 2 placeholder: verify all chunks are active, mark film as processed. Phase 3 replaces this with actual Gemini synthesis (Prompt 0B)."` Body is ~20 lines that count active chunks and flip `films.status`. **No Gemini call. No synthesis.** Completes in <1 second regardless of film length.
- `backend/prompts/` listing: `offensive_sets.txt, defensive_schemes.txt, pnr_coverage.txt, player_pages.txt, game_plan.txt, adjustments_practice.txt`. **No `chunk_extraction.txt`. No `chunk_synthesis.txt`.** Prompts 0A and 0B were never drafted.

*Consequence:*
- The `text_context` that gets passed to sections 1-4 today is effectively `"FULL-GAME SYNTHESIS DOCUMENT: (not available — synthesis failed for this film)\nROSTER:\n#1 Quentin Colman\n#2 Trey Pearson"` — 127 characters. `text_chars=127` in the log matches exactly.
- With Option 3 routing sections 1-4 to synthesis-only, sections 1-4 now depend entirely on a document that is never produced. The pipeline ships a PDF, but the content is made up.
- The architectural decision to go synthesis-only is still correct — but it assumed Phase 2 was complete. It wasn't.

*What this reclassifies:*
- **Task 2.6 (`run_chunk_synthesis placeholder`)** was marked `✓ Done` on April 10 under Phase 2 eval. The eval verified the task completes and flips the film status — it did not verify that any synthesis document was actually produced. The "placeholder" in the task name was accurate; "Done" was not. Status corrected in the Phase 2 table below.
- **Task 3.17 eval** cannot close until 0A and 0B are built and a report ships with real content from real synthesis. Pipeline works ≠ eval passes. Eval is about output quality, not flow.

*Next-session work (real Phase 2 completion):*
1. Add `extraction_output` (text) and `extraction_status` (enum: `pending`/`complete`/`error`) columns to `film_chunks` via a new numbered migration. Apply to dev branch.
2. Write `backend/prompts/chunk_extraction.txt` (Prompt 0A). Instructions: Gemini watches a 20-25 min chunk, outputs structured per-possession scouting notes — every play called, every defensive coverage, every notable tendency, with player jersey numbers tied to roster entries. Include chunk metadata (chunk_index, total_chunks, start_min, end_min) in the prompt header so Gemini knows where in the game it is. This is THE core perception prompt for TEX.
3. Write `backend/prompts/chunk_synthesis.txt` (Prompt 0B). Instructions: Gemini reads all chunk extractions together (concatenated with headers) + the roster, outputs a single consolidated scouting breakdown keyed to the 6 downstream sections' needs.
4. Wire Prompt 0A into `extract_chunk`: after Gemini file is ACTIVE, `acquire_gemini_slot("gemini-2.5-pro")`, call `provider.analyze_video(uris=[chunk.gemini_file_uri], prompt=prompt_0a, section_type="chunk_extraction")`, save output to `film_chunks.extraction_output`, set `extraction_status = 'complete'`. Atomic last-chunk detection gates `run_chunk_synthesis.delay`.
5. Replace `run_chunk_synthesis` body with the real synthesis call. Pull all `extraction_output` rows for the film, concatenate with chunk headers, append roster, call `provider.analyze_text(context, prompt_0b, "chunk_synthesis")`, write result into `film_analysis_cache.synthesis_document` (UPSERT on `file_hash`), then resume the existing auto-trigger logic for pending reports.
6. Re-process one existing film end-to-end after 0A and 0B ship. Inspect the `film_analysis_cache.synthesis_document` manually — it should be thousands of characters, not empty, and readable as an actual scouting breakdown. If not, iterate on Prompts 0A / 0B before running any report.
7. Re-run one report after synthesis is non-empty. Sections should pull real content. If quality is strong, close 3.17.

*Ancillary (not blockers, but flagged):*
- The Brad Beal Elite test team roster has only 2 players. Report quality testing requires a real 12-15 player roster — Tommy to populate before eval.
- Celery queue bindings still show `exchange=notifications(direct) key=notifications` for all 4 queues in worker boot output. Functionally OK (tasks route by queue name), but hygiene issue to correct during Phase 5.
- Section prompts 2, 3, 5, 6 need empty-input guardrails similar to sections 1 and 4. When building 0A/0B, extend these prompts to refuse with an explicit error instead of hallucinating if `text_context` is thin. Lower priority than 0A/0B themselves — once synthesis produces real content, the hallucination risk falls dramatically.
- ~4 duplicate/error report rows in Tommy's dev dashboard from tonight's testing. Cosmetic. Purge during Phase 5 launch prep.

**Session log (2026-04-19, later) — Synthesis-only mode (Option 3):**

Earlier today the no-cache fallback was wired in, which unblocked caching but still sent the full video token count on every section call — which hit Gemini's hard 1,048,576 input-token ceiling for any film over ~50 minutes. The leftover 2h film from Tommy's eval raised `400 INVALID_ARGUMENT: The input token count exceeds the maximum number of tokens allowed 1048576` on the first `run_section` attempt.

Option 3 resolves this structurally: sections 1-4 no longer touch the video at all. They run against the full-game synthesis document (already produced by `run_chunk_synthesis` during film processing and stored in `film_analysis_cache.synthesis_document`) plus the roster text. The synthesis document is designed exactly for this — it is the textual model of the entire game that sections 1-4 were meant to reason over. Handing it to Gemini directly skips the video re-read entirely.

*Change landed (`backend/services/ai/gemini.py`, single file):*
- Module docstring + NO_CACHE_PREFIX comment updated to reflect synthesis-only mode.
- `_create_context_cache_dev` + `_create_context_cache_vertex`: removed the `client.caches.create` / `CachedContent.create` call entirely. Both now build the text_context (synthesis + roster), log `"synthesis-only mode: bypassing video cache (chunk_count=N, text_chars=M)"` at INFO, and return a sentinel carrying ONLY `text_context`. No `chunk_uris` in the payload.
- `_analyze_video_cached_dev` + `_analyze_video_cached_vertex` (sentinel branch): removed all `Part.from_uri` video construction. Parts = `[Part.from_text(text_context), Part.from_text(prompt)]`. Raise `RuntimeError` if `text_context` is empty (synthesis should never be empty in production). Non-sentinel real-cache branches retained but marked unreachable for future re-enablement.
- `delete_context_cache` unchanged — it already early-returns on empty or sentinel URI.
- Signatures of `create_context_cache` are identical — callers in `generate_report` do not change. `ttl_seconds` / `display_name` retained but unused.

*Verified:*
- `python -m py_compile` on `gemini.py` — clean.
- Worker restart — all 8 tasks registered across 4 queues, no tracebacks on boot.
- Inline smoke test: `create_context_cache` returns the sentinel with `text_context` present and `chunk_uris` absent, no network call made.

*Out of scope / explicitly NOT touched:*
- Model choice — still Gemini 2.5 Pro for sections 1-4.
- Rate limit bucket key — still `gemini-2.5-pro`.
- Orchestration in `generate_report` / `run_section` — unchanged.
- Flash fallback for sections 5-6 — unchanged.
- Database schema / prompts — unchanged.

*Cost / quality note:*
Per-report cost drops significantly — input is now ~20-40K tokens (synthesis doc + roster + prompt) per section instead of ~1.5M. Expected blended cost per report is a small fraction of a dollar. The quality risk: sections 1-4 now depend entirely on the synthesis document being rich and accurate, which in turn depends on `run_chunk_synthesis` (Prompt 0B) doing its job. Anything the synthesis omits is invisible to sections 1-4. If eval output is thin, the fix is in the synthesis prompt, not in the section prompts.

*What Tommy needs to test (in order):*
1. `docker compose up -d --build worker`.
2. Upload a full game film (2+ hours).
3. Tail worker logs: expect `"synthesis-only mode: bypassing video cache (chunk_count=N, text_chars=M)"` before sections start.
4. Confirm all 4 parallel sections complete WITHOUT the `1048576 token` error.
5. Sections 5-6 run sequentially via Flash.
6. PDF assembled and uploaded to R2. In-app notification fires.
7. Download the PDF. Check: sections have real content (not generic filler), actual team name on cover, actual rostered player names on player pages, specific play calls / defensive schemes referenced (not abstract descriptions).

If PDF quality is OK, mark 3.17 `✓ Done`. If sections look thin or generic, the synthesis document probably needs richer extraction — open a follow-up to tune Prompt 0B.

**Session log (2026-04-19) — No-cache fallback + section-cache short-circuit:**

Bundled two changes in one session to unblock 3.17 without waiting on Google to fix context caching.

*Change 1 — No-cache fallback on Developer API path (`backend/services/ai/gemini.py`):*
- Renamed `VERTEX_NO_CACHE_PREFIX` → `NO_CACHE_PREFIX` (string value `"vertex:no-cache:"` unchanged so any in-flight sentinels stay valid). Shared by both backends now.
- Wrapped `client.caches.create(...)` in `_create_context_cache_dev` with try/except. On failure (e.g. `max_total_token_count=0`), logs a warning matching the Vertex shape, encodes `{chunk_uris, text_context}` into the sentinel string, and returns it — mirrors the Vertex path exactly.
- Added sentinel-detection branch at the top of `_analyze_video_cached_dev`: parses the JSON, rebuilds `types.Part.from_uri(...)` video parts + a text context part + the prompt part, wraps them in `types.Content(role="user", parts=...)`, and calls `client.models.generate_content(...)` without `cached_content`. Usage-metadata extraction stays shared with the cached path.

Net effect: when Google's Developer API caching is broken, the section call carries the video URIs directly each time. Costs more per report (~$19 vs ~$3 — sections 1-4 each re-read the full video tokens), but removes the caching dependency entirely.

*Change 2 — Section-cache short-circuit (`backend/tasks/report_generation.py`):*
- New top-level helper `_try_section_cache_hit(report_id, film_rows, prompt_version)` — returns the cached sections dict on hit, `None` on miss. Only fires for single-film reports with a `file_hash`, and only when `film_analysis_cache.sections` contains all 4 parallel section types with non-empty string content.
- New branch inserted between step 6 (roster) and step 7 (create_context_cache): on cache hit, upserts sections 1-4 as `status='complete'` with cached content + `model_used='cached'`, upserts sections 5-6 as `status='pending'`, and enqueues `run_synthesis_sections.delay(None, report_id=..., cache_uri="")` directly. No chord fired. Empty `cache_uri` is safe — `run_synthesis_sections` finally block guards deletion with `if cache_uri:`.

Net effect: regenerating the same single film at the same `prompt_version` costs ~$0.02 instead of ~$19. Makes dev/test on every downstream task affordable.

*Verification done:*
- `docker compose build api worker` clean (cached layers, no errors).
- `docker compose up -d api worker redis` — worker boots with all 8 tasks registered across 4 queues, no stack traces.
- `from main import app` + explicit imports of `generate_report`, `run_synthesis_sections`, `assemble_and_deliver`, `_try_section_cache_hit`, `GeminiProvider`, `NO_CACHE_PREFIX` — all succeed.

*What Tommy needs to test (in order):*
1. `docker compose up -d --build worker`
2. Generate a real report end-to-end through the UI.
3. Tail worker logs: expect the "Developer API context caching FAILED" warning from `_create_context_cache_dev`, then 4 × `run_section` complete over 3-8 minutes, then 2 × synthesis sections over 1-2 minutes, then `assemble_and_deliver` producing a PDF.
4. Confirm the PDF lands in R2 and the in-app notification fires.
5. Immediately trigger a SECOND report for the same film at the same prompt_version. Worker logs should show "generate_report: section cache HIT — skipping Gemini chord". Sections 1-4 rows should appear with `model_used='cached'` in seconds. Only sections 5-6 call Gemini. Total time < 2 minutes.

If both runs pass, mark 3.17 `✓ Done`.

**Session log (2026-04-15) — Vertex AI migration:**
- GCP project `tex-v2` created, billing linked, Vertex AI API + Cloud Storage API enabled.
- GCS bucket `tex-film-chunks-prod` created in `us-central1`.
- Service account `tex-backend@tex-v2.iam.gserviceaccount.com` with `roles/storage.objectAdmin` on bucket + `roles/aiplatform.user` at project. Vertex AI Service Agent (`service-1063428634162@gcp-sa-aiplatform.iam.gserviceaccount.com`) granted `roles/storage.objectViewer` on bucket.
- D-011 executed early via Option A. See **DECISIONS.md D-018**. `GEMINI_BACKEND` env var controls which path runs — no code changes to switch.

**Session log (2026-04-16) — Task 3.17 eval attempts:**

Attempt 1 — Vertex AI path (`GEMINI_BACKEND=vertex`):
- ✅ Film upload → R2 → chunking → GCS upload at `gs://tex-film-chunks-prod/chunks/{film_id}/` confirmed.
- ✅ Stripe test-mode payment (`4242…`) → webhook → `generate_report` dispatched.
- ✅ Vertex `CachedContent.create` succeeded (cache created in 14s).
- ❌ Vertex inference (`model.generate_content` against cache) failed: `429 RESOURCE_EXHAUSTED`. Root cause: brand-new GCP project has default token-per-minute quota far below what a single 15-min video section prompt requires (~80K+ input tokens). The deprecated `vertexai.generative_models` SDK obscured this as `503 Socket closed`.
- **Fix needed:** request Vertex AI Gemini quota increase (input tokens/min for gemini-2.5-pro and flash to ≥2M). Not yet done.

Attempt 2 — Developer API path (`GEMINI_BACKEND=developer_api`):
- Switched back to Developer API via env var flip. No code changes needed — abstraction layer worked as designed.
- ❌ Initial chunk uploads failed: `API key not valid`. Root cause: `.env` had a stale duplicate `GEMINI_API_KEY` from earlier sessions. Fixed by Tommy.
- ❌ Second attempt: `429 RESOURCE_EXHAUSTED — prepayment credits depleted`. Root cause: AI Studio billing account had zero credits. Fixed by Tommy adding credits.
- ✅ Third attempt: API key valid, all 4 chunks uploaded to Gemini File API, all ACTIVE with valid URIs.
- ✅ Stripe payment, webhook delivery, `generate_report` dispatched.
- ❌ Orchestrator hit Neon `SSL SYSCALL error: EOF detected` during expired-chunk re-uploads for an OLD film (`8fbd2dd2-...`). Connection held too long across Gemini File API polling. Fixed by marking old film's expired chunks as `deleted`.
- ❌ Cache creation hit `gs://` URI from Vertex-era chunk (`d9e03696-...`) still marked `active` in DB. Developer API can't read GCS URIs. Fixed by marking that chunk as `deleted`.
- ❌ **FINAL BLOCKER:** `client.caches.create` returned `400 INVALID_ARGUMENT: Cached content is too large. total_token_count=1566488, max_total_token_count=0`. This is the **same Google AI Studio caching quota bug** from before D-018. Still unresolved on Google's side.

**What passed during the eval (confirmed working):**
- ✅ Film upload → R2 presigned URL → frontend progress bar → `POST /films/upload-complete`
- ✅ `process_film` → FFprobe validation → compression skip (under 1.8GB) → chunking
- ✅ `extract_chunk` → Gemini File API upload → poll until ACTIVE → URI + expiry saved to DB
- ✅ Stripe Checkout (test mode) → webhook signature verified → payment row created
- ✅ Payment gate: free report consumed on first attempt, Stripe checkout triggered on second
- ✅ `generate_report` orchestrator: film lookup, chunk URI gathering, expiry check, context cache creation call
- ✅ Vertex/Developer API abstraction layer: `GEMINI_BACKEND` env var switches paths with zero code changes
- ✅ No-cache sentinel (Vertex path): correctly encodes chunk URIs in the sentinel string, survives Celery prefork process boundary
- ✅ Docker Compose stack: API, worker (4 queues, 8 tasks), Redis, frontend all healthy

**What has NOT been tested (blocked):**
- ❌ Context cache creation succeeding (quota = 0 on both backends)
- ❌ Sections 1-4 parallel chord completing
- ❌ Sections 5-6 sequential completing
- ❌ PDF assembly via WeasyPrint
- ❌ PDF upload to R2 + presigned download URL
- ❌ In-app notification on report completion

**Proposed fix — no-cache fallback in gemini.py:**
Add a Developer API fallback identical to Vertex's sentinel path: when `client.caches.create` fails, encode chunk URIs into a sentinel string, and `analyze_video_cached` detects it and passes video parts directly per section call. Cost is ~4x input tokens for sections 1-4 (each section re-reads the video) but removes ALL dependency on the broken caching quota. This is a change only inside `gemini.py`.

**Build status:**
- Phase 3: tasks 3.1-3.16 all built. 3.17 eval blocked on caching quota — needs no-cache fallback.
- Phase 4: tasks 4.1-4.11 all built. 4.12 eval needs real report data — unblocks once 3.17 passes.
- Phase 5: not started — requires Phase 3 + 4 evals to pass first.

---

## ACTIVE BLOCKERS

### Prompt 0A + 0B Text Not Yet Written

**Originally discovered:** 2026-04-20 (early AM), during Option 3 end-to-end eval.
**Scope reduced:** 2026-04-20 (evening), after pipeline wiring + schema migration landed. Code side is now complete.

**What's left:**
- `backend/prompts/chunk_extraction.txt` — Prompt 0A at `VERSION: v1.0`. Does not exist.
- `backend/prompts/chunk_synthesis.txt` — Prompt 0B at `VERSION: v1.0`. Does not exist.

**What is already done (shipped in commits `3e6a000` and `8a0edca`, plus migration apply):**
- Schema migration 016 applied to Neon dev — `film_chunks.extraction_output` + `extraction_status` + index.
- `services/ai/base.py` — `analyze_video(uris, prompt, section_type)` abstract method added.
- `services/ai/gemini.py` — `analyze_video` implemented on both Developer API and Vertex backends.
- `services/ai/anthropic.py` — video methods explicitly raise `NotImplementedError` (Claude is text-only).
- `tasks/film_processing.py::extract_chunk` — runs Prompt 0A against each chunk, saves to `extraction_output`, flips `extraction_status='complete'`. Idempotency check hardened to prevent silent retry short-circuit.
- `tasks/film_processing.py::run_chunk_synthesis` — rewritten. Concatenates per-chunk extractions, appends roster, runs Prompt 0B via Gemini Flash, UPSERTs `film_analysis_cache.synthesis_document`.
- `_load_preprocess_prompt` stub helper — translates `FileNotFoundError` into `NotImplementedError` with a clear pointer back to this blocker. Dead letter + film-error transition + coach notification all fire correctly on retry exhaustion.
- `AGENTS.md` updated — Prompt 0B is documented as Flash (matches code).

**Why this still matters:**
Option 3 (synthesis-only mode, shipped 2026-04-19) routes sections 1-4 to read the synthesis document instead of the video. Without Prompts 0A and 0B, that document is still empty and sections still hallucinate. Task 3.17 cannot close until both prompt files exist and produce substantive synthesis.

**Resolution:**
1. Write Prompt 0A — Gemini watches one 20-25 min chunk, outputs structured per-possession scouting notes (plays, coverages, tendencies, jersey numbers). Include chunk metadata (index / total / start_min / end_min) in the prompt header.
2. Write Prompt 0B — Gemini reads all chunk extractions + roster, outputs one consolidated scouting breakdown keyed to the 6 downstream sections' needs.
3. Rebuild worker: `docker compose up -d --build api worker` to pick up the wired pipeline.
4. Re-process one test film. Inspect `film_chunks.extraction_output` (should be thousands of chars per chunk) and `film_analysis_cache.synthesis_document` (should be a rich consolidated breakdown). Iterate on the prompts if thin.
5. Re-run a report. If content reflects the synthesis accurately, close 3.17.

This is prompt-engineering work Tommy owns — see `TRAINING.md` sections 4 and 7 for method.

---

## RESOLVED BLOCKERS

### Gemini Context Caching Quota = 0 — RESOLVED via synthesis-only mode (2026-04-19)

**Original problem (reported 2026-04-13):** Google Developer API returned `400 INVALID_ARGUMENT: Cached content is too large. total_token_count=1616899, max_total_token_count=0` when caching video chunks. Root cause: Google-side provisioning bug that hardcoded `max_total_token_count` to 0 despite active billing. 1-2 chunks worked; 3+ chunks failed.

**Attempted resolution (2026-04-15):** D-011 Vertex AI migration via Option A. Vertex `CachedContent.create` succeeded, but inference against the cache hit `429 RESOURCE_EXHAUSTED` (Dynamic Shared Quota).

**Final resolution (2026-04-19):** Option 3 — remove video from sections 1-4 entirely. Sections now read the synthesis document + roster as text only. Gemini context caching is no longer on the critical path for any backend. See Session log 2026-04-19 (later) in CURRENT STATE.

Caveat: resolution created the exposed dependency on Prompts 0A + 0B (see ACTIVE BLOCKERS above). The caching issue itself is no longer a code-level blocker.

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
2.6  run_chunk_synthesis                ⚠ Wired, awaits prompt  Prompt 0B call path fully wired 2026-04-20 mid-day. _load_preprocess_prompt raises NotImplementedError until backend/prompts/chunk_synthesis.txt exists. Will run end-to-end and UPSERT film_analysis_cache.synthesis_document the moment the prompt file lands.
2.6a chunk_extraction (Prompt 0A)        ⚠ Wired, awaits prompt  Migration 016 adds extraction_output + extraction_status. extract_chunk now runs Prompt 0A after Gemini file reaches ACTIVE and persists per-chunk output. Atomic last-chunk gate switched to extraction_status='complete'. Same NotImplementedError stub until backend/prompts/chunk_extraction.txt exists.
2.7  Wire process_film to upload        ✓ Done          POST /films/upload-complete + POST /films/{id}/retry
2.8  URI expiry check service           ✓ Done          backend/services/uri_expiry.py
2.9  Film fingerprint cache             ✓ Done          backend/services/film_cache.py
2.10 Frontend — film status polling     ✓ Done          Polls every 10s, clears on terminal state
2.11 Frontend — processing states       ✓ Done          Badges + error display + retry button
2.12 Phase 2 eval pass                  ✓ Done          Passed April 10, 2026 — see notes below
2.13 Stuck-film bug fix                 ✓ Done          extract_chunk now fails parent film + notifies coach on permanent chunk failure
```

### Phase 2 Eval Results

**Passed on April 10, 2026 (but see 2026-04-20 correction below):**
1. Film uploaded → split into 4 chunks → each chunk uploaded to R2 ✓
2. Each `extract_chunk` task uploaded to Gemini File API and reached `ACTIVE` ✓
3. All 4 `film_chunks` rows show `gemini_file_state = 'active'`, valid `gemini_file_uri`, and `gemini_file_expires_at` ~48 hours from upload ✓
4. `run_chunk_synthesis` fired and marked film as `processed` ✓

**2026-04-20 correction — Phase 2 eval missed the actual product work:**
The eval above only verified *file flow* (R2 → Gemini File API → ACTIVE state → film status = 'processed'). It did not verify any *AI output* was produced. The core pre-processing work — Prompt 0A (chunk extraction) and Prompt 0B (chunk synthesis) — was stubbed with a placeholder, and the placeholder was what the eval tested. All four checks above remain true in the current code, but no synthesis document has ever been generated. See ACTIVE BLOCKERS for full detail. Phase 2 is NOT actually complete — items 2.6 and 2.6a are the remaining work.

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
3.3  generate_report orchestrator       Built (ready for eval)  Orchestrator runs cleanly through chunk validation + cache creation. No-cache fallback on Developer API path (2026-04-19) bypasses the broken caching quota — cache failure now encodes URIs into a sentinel instead of raising. Also added section-cache short-circuit for cheap regeneration.
3.4  run_section task (sections 1-4)    Built (ready for eval)  No-cache sentinel path unblocks execution on Developer API — video URIs are passed directly to each section call when caching is unavailable. Pending Tommy's end-to-end eval.
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
3.17 Phase 3 eval pass                  In progress (code ready — awaiting Tommy's end-to-end eval)  Synthesis-only mode shipped — sections 1-4 no longer re-read video; caching bypass no longer a blocker. Earlier today the no-cache fallback hit Gemini's 1,048,576 input-token cap on long films; Option 3 removes video from the section call path entirely. See session log in CURRENT STATE for verification steps.
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
4.1  Admin gate middleware              ✓ Done          require_admin dependency in clerk.py. 403 if not admin.
4.2  GET /admin/corrections route       ✓ Done          Filterable by section, version, category, correctness.
4.3  POST /admin/corrections route      ✓ Done          Full validation, saves to corrections table.
4.4  GET /admin/pattern-analysis route  ✓ Done          Error rate by category + section + prompt version.
4.5  GET /admin/users route             ✓ Done          All coaches + report counts.
4.6  POST /admin/users/{id}/credits     ✓ Done          Manual credit grant with balance return.
4.7  Prompt versioning loader           ✓ Done          Built in Phase 3 (3.3) — load_prompt() returns text + version.
4.8  Cache invalidation on version bump ✓ Done          Built in Phase 3 (3.3) — orchestrator queries WHERE prompt_version.
4.9  Frontend — /admin layout           ✓ Done          Admin layout with nav + is_admin gate check.
4.10 Frontend — corrections UI          ✓ Done          /admin — list, filter, create corrections. Correct/incorrect + text.
4.11 Frontend — pattern analyzer UI     ✓ Done          /admin/patterns — error rate tables by category + section. /admin/users — user list + credit grant.
4.12 Phase 4 eval pass                  Not started     Correction saved, pattern table accurate. Needs test data.
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

## COMMERCIAL READINESS LADDER

The engineering phases above (1-5) make TEX *technically ready*. This ladder makes TEX *commercially ready* and scales it from the first paying coach all the way to professional front offices and NBA GM tooling.

Do not skip stages. Every stage exposes failure modes the prior stage could not. A company that jumps from Stage 1 directly to Stage 6 ships a product that fails in ways the team cannot even see.

Read this alongside VISION.md. VISION is the *why* (Cursor of Basketball, platform replacing Synergy/Hudl/FastModel, AI GM endgame). This ladder is the *what* and *when*. Every engineering phase above maps to at least one stage below.

### The Ladder At A Glance

```
Stage   Goal                                                      Typical window
───────────────────────────────────────────────────────────────────────────────────
1       Golden Set Passes                                         In progress
2       Blind Set Validation                                      Wk +1-2 after Stage 1
3       Design Partner Zero (1 real coach)                        Wk +2-4 after Stage 2
4       Design Partner Cohort (3-5 coaches)                       Mo +1-3
5       Early Paid Pilot (5-10 coaches)                           Mo +3-6
6       General Launch — HS / AAU tier (50-500 coaches)           Mo +6-18
7       NCAA Expansion (college programs, institutional sales)    Yr 2-3
8       Professional / AI GM (NBA, WNBA, G-League, international) Yr 3-5+
```

---

### Stage 1 — Golden Set Passes

**Goal:** Prove TEX produces high-quality, accurate reports on a fixed set of hand-graded films.

**Who:** Internal only. Tommy runs this.

**Definition of done:**
- 5 golden films, each with a hand-written ground-truth scouting document per TRAINING.md §2.
- Prompts 0A + 0B + sections 1-6 execute end-to-end on every golden film.
- Output scored on every claim (captured / missed / hallucinated) per TRAINING.md rubric.
- `EVAL_SCORES.md` tracks every scored run with date + `prompt_version`.
- Bar: ≥85% captured, <5% hallucinated, held across ≥3 consecutive prompt iterations (proves stability, not luck).

**Internal tooling to build alongside Stage 1 (highest-leverage investment Tommy can make):**
Build a minimal internal grading UI — a web tool that loads a generated report side-by-side with its ground-truth document and lets Tommy walk through it claim-by-claim. One-click buttons for captured / missed / hallucinated. A paste-correction field for each marked claim. On save, it auto-writes:
- One row per claim into the corrections database (so every graded run compounds into labeled data from day one).
- A scored summary line into `EVAL_SCORES.md` (date, `prompt_version`, captured %, missed %, hallucinated %, total claims, notes).
- A timestamped snapshot of the full graded report to disk for later reference.

The existing Phase 4 admin corrections UI (`/admin`) is ~60% of what's needed but is tuned for post-report review, not side-by-side golden-set grading. Extending it for golden-set grading mode is ~2-3 days of work and pays itself back in a week. Without this tool, grading a single golden film takes 3-4 hours in a spreadsheet. With it, 20-40 minutes. Across 5 films × dozens of iterations, that difference is the entire eval velocity of the company.

**Does NOT prove:** Generalization to unseen films. Coach demand. Willingness to pay.

**Gate to Stage 2:** Golden scores hit bar on 3 consecutive iterations.

**Current state:** In progress. Blocked on Prompts 0A / 0B (see ACTIVE BLOCKERS). Internal grading UI is a parallel workstream Tommy can ship any time — does not depend on 0A/0B being written first.

---

### Stage 2 — Blind Set Validation

**Goal:** Prove TEX's scores hold on films it was never tuned against. Catches overfitting to the golden set.

**Who:** Internal. Tommy (+ optional second grader for calibration).

**Definition of done:**
- 3-5 additional films selected from a *different* source than the golden set (different tournament, different season, different style of play).
- Hand-graded ground truth for each, same rubric as Stage 1.
- TEX runs on each → scored blind.
- Scores within 5 percentage points of Stage 1 golden-set scores.

**What counts as failure:** Golden 87% captured, blind 72%. That's overfit. Widen the golden set, re-tune prompts, retry.

**Gate to Stage 3:** Blind scores hold within 5pp of golden.

**Typical window:** 1-2 weekends after Stage 1 passes. Infrastructure + rubric already exist — grading is faster the second time.

---

### Stage 3 — Design Partner Zero

**Goal:** One real coach uses TEX on one film of their own choosing, for a real opponent they're actually scouting, and tells Tommy what they think.

**Who:** One coach Tommy already trusts. EYBL preferred (target market). Free.

**Definition of done:**
- Coach uploads film through the actual product UI.
- Report generates within PRD.md §5.4 SLA (<50 min for 2-hour film).
- Coach reads the PDF, uses it for the actual game, and gives structured feedback:
  - What was useful?
  - What was wrong?
  - What was missing?
  - Would you have paid $X for this?
  - What would make you use this every week?

**Why this stage is the most important gate in the company:** Golden scores tell you if TEX is *technically good*. This stage tells you if TEX is *commercially valuable*. Those are different things. Plenty of products are technically good and commercially useless.

**What you're actually testing:**
- Does TEX solve a real problem or a theoretical one?
- Will the coach upload a film they genuinely care about? (Revealed preference.)
- Does the report save the coach time or add a checkbox to their process?
- Is the output good enough to survive contact with a real scouting workflow?

**Likely findings (prepare for all):**
- "Amazing but it missed X, Y, Z." → Prompt 0B work.
- "Fine I guess." → Red flag. Talk to 2-3 more coaches before building further.
- "Couldn't figure out upload." → Wrapper / onboarding gap.
- "I'd rather have this as a video overlay, not a PDF." → Format rethink.
- "When can I pay?" → Green light to Stage 4.

**Gate to Stage 4:** Coach says some version of "when can I pay" without being prompted.

**Typical window:** 2-3 weeks after Stage 2.

---

### Stage 4 — Design Partner Cohort

**Goal:** 3-5 coaches use TEX on real films through a full scouting cycle (2-3 weeks). Expose every gap Stage 3 missed.

**Who:** Tommy's extended basketball network. Free or heavily discounted. These are the first names on the wall.

**Definition of done:**
- 3-5 coaches onboarded through the actual product flow.
- Each runs ≥3 reports across the cohort window.
- Every coach gives structured weekly feedback (standing call or async form).
- TEX ships ≥2 substantive product improvements in response to cohort feedback.
- ≥2 coaches explicitly say they would pay to continue.
- Corrections database starts capturing real labels from Tommy grading cohort reports.

**What gets exposed here (that earlier stages couldn't):**
- Reliability under repeated use — does the pipeline crash on the 7th film?
- Multi-film reports (coach wants to scout the same team across 3 games).
- Roster edge cases (transfers mid-season, injuries, jersey changes).
- Film-quality variance (some EYBL film is cellphone-quality).
- Delivery expectations — email, push, dashboard row?
- Support load — what happens when a coach finds a mistake at 11pm before a game?

**Engineering work that emerges:**
- Phase 4 Training Mode gets its first real workout (Tommy corrects cohort reports daily).
- Phase 5 hardening items surface organically (Sentry, alerting, error recovery, retry policy tuning).
- First product-level quality investments (reliability dashboards, SLA monitoring).

**Gate to Stage 5:** ≥2 coaches offer to pay unprompted. Cohort retention through the full 2-3 weeks (nobody drops out mid-cohort).

**Typical window:** 1-2 months.

---

### Stage 5 — Early Paid Pilot

**Goal:** 5-10 coaches paying real money. First revenue. First churn. First pricing test.

**Who:** Cohort + cohort referrals. Below sticker price is fine — you're testing commitment and elasticity, not ARR.

**Definition of done:**
- Stripe live mode. Real cards.
- Published pricing — even if it changes. Base tier (Opponent Scouting) priced per VISION.md tiered model.
- 5-10 coaches on recurring subscriptions, not one-off reports.
- 30-day + 60-day retention data recorded.
- First churn event. Tommy understands why they left.
- Support process documented (ticket destination, response SLA, bug-to-fix path).
- Basic legal shipped: ToS, Privacy Policy, DPA template.
- Minors-protection review: HS and AAU film contains minors. State-by-state review of COPPA (under 13), FERPA (school-affiliated), and state name/likeness laws.

**What "commercial viability" means at this stage:**
- Gross margin per coach per month ≥70% (COSTS.md model holds).
- Month-over-month retention ≥70%.
- ≥1 coach renews without Tommy asking.
- NPS or qualitative equivalent ≥40.

**Team work that emerges:**
- First-hire decision: second engineer, or basketball-ops lead? Usually whichever is the tightest bottleneck — typically product/eng.
- First capital decision: bootstrap longer or raise angel round?

**Gate to Stage 6:** Retention >70% at 60 days. ≥1 coach refers another coach unprompted. Unit economics provably positive.

**Typical window:** 2-3 months.

---

### Stage 6 — General Launch (HS / AAU Tier)

**Goal:** TEX is a real business serving the HS and EYBL/AAU market. Open signup. Self-serve onboarding. Paid growth.

**Who:** Any coach who finds the site. HS + AAU is the beachhead per VISION.md.

**Definition of done:**
- Public marketing site with real social proof (coach testimonials, sample reports, video demos).
- Self-serve signup + onboarding (no Tommy calls for every new user).
- 50-500 paying coaches (range dependent on pricing + sales motion).
- Scalable support (ticket system, knowledge base, no more Tommy DMs).
- Reliability SLAs published and met (uptime, turnaround, accuracy targets per PRD.md §5.4).
- Compliance baseline:
  - SOC 2 Type I in progress or complete (required by larger programs).
  - GDPR-ready data handling for international AAU use.
  - Film retention + deletion policy (coach can delete film; deletion persists through all caches).
  - Explicit minors-protection policy (data handling, parental-consent posture where relevant).
- First hires in place: second engineer, part-time basketball ops, part-time customer success.

**Product work required:**
- **Reliability at scale.** 100 concurrent film uploads. 500 concurrent inferences. No single point of failure in Celery / Redis / Neon / R2.
- **Self-serve onboarding.** Guided first-report flow. No human needed.
- **Billing.** Stripe subscriptions, proration, refunds, failed-card handling, invoicing for programs needing POs.
- **Team admin.** Head coach + assistants + video coordinator roles + permissions.
- **Integration path 1 — film source ingestion.** Coaches already use Hudl, Krossover, or Synergy as their film library. TEX needs to pull from at least one via API or standardized export. Without this, upload friction kills conversion.
- **Integration path 2 — delivery upgrade.** Web-native interactive report with shareable links, not just PDF. Alerts on completion. Mobile-readable.

**Moat investments that compound:**
- **Corrections database.** Every Tommy correction = labeled data. Target ≥1,000 labeled examples by end of Stage 6. This is the dataset that enables Stage 7 fine-tuning.
- **Pattern library.** Cross-game tendencies surfaced as coaches scout the same opponents repeatedly. Build infrastructure now; value compounds in year 2.
- **Basketball knowledge base.** Structured ontology of offensive sets, defensive schemes, coverage types, player archetypes. Starts as a spreadsheet, becomes a graph DB, eventually the RAG backbone for Chat/Q&A mode (VISION.md Mode 6).

**Capital required:**
- Bootstrap or angel through Stage 5.
- Stage 6 launch usually needs a seed round ($2-5M) to fund compliance, hiring, infrastructure.
- Raise on Stage 5 traction data, not promises.

**Gate to Stage 7:** ≥$500K ARR. ≥70% retention at 6 months. Organic growth signal (referrals outpace paid acquisition). At least one program-level (not individual-coach) buyer inquires.

**Typical window:** 6-12 months.

---

### Stage 7 — NCAA Expansion

**Goal:** Sell into college programs, not individual coaches. Institutional sales motion, larger contracts, multi-year commitments.

**Why this is a different business from Stage 6:**
- Buyer is the athletic department or head coach, not an individual.
- Sales cycle: 3-12 months (budget cycles, compliance review, demo gauntlets).
- Contracts: annual or multi-year, not monthly SaaS.
- Pricing: per-program, not per-seat. $10K-$50K+ annual contracts.
- Expected capabilities broader: recruiting, transfer portal, self-scout, practice planning, NIL-adjacent analysis.

**Product expansions required:**
- **Self Scout mode** (VISION.md Mode 4). Programs want to know what opponents see when they scout them.
- **Game Plan Builder** (VISION.md Mode 2). Already in v2 vision — college programs *require* it.
- **Practice Planning** (VISION.md Mode 3). Tied to film findings and game plan.
- **Transfer portal analysis.** Evaluate incoming transfer film against program's system. Novel product.
- **Recruiting pipeline.** HS / EYBL film evaluation for roster construction. TEX is uniquely positioned because Stage 6 is already capturing HS/AAU film.
- **Multi-user permissions.** Head coach + assistants + video coordinator + analyst with distinct access.
- **System-fit modeling.** Does this player's tendencies fit your system? VISION.md Stage 3 (TEX Knows Your System) pays off here.

**Compliance additions:**
- SOC 2 Type II (required by most athletic department IT).
- FERPA compliance (student-athletes are students; data is FERPA-protected).
- NCAA compliance review: TEX outputs cannot violate recruiting rules, contact rules, or evaluation-period restrictions.

**Team additions:**
- Enterprise AE (experience selling into NCAA or pro sports).
- Full-time customer success lead dedicated to programs (different motion than coach-by-coach).
- Basketball domain expert at near-senior level (former D1 assistant or analyst).

**Capital:** Series A ($10-25M). Raise on Stage 6 ARR + NCAA pipeline signal.

**Moat investment: proprietary fine-tuned model.** With ≥10,000 labeled corrections from Stages 4-6, fine-tune a basketball-specific model on top of whichever frontier video model is best in year 2. The result is genuinely non-replicable — a competitor with the same API key cannot match it without 10,000 of their own labeled examples (takes years to generate).

**Gate to Stage 8:** ≥10 college programs under contract. ≥$3M ARR. Basketball intelligence layer (corrections DB + pattern library + fine-tuned model) demonstrably outperforms off-the-shelf frontier models on TEX's golden set.

**Typical window:** 12-24 months from Stage 6.

---

### Stage 8 — Professional / AI GM Tier

**Goal:** TEX sells into NBA, WNBA, G-League, and international professional front offices. The product evolves from scouting into a full AI GM capability.

**What "AI GM" means concretely:**
- **Opponent scouting.** Professional-depth version of Stages 1-7 product.
- **Draft analysis.** NCAA + international film → pro projection. Player archetype matching. Historical analog modeling.
- **Free agent evaluation.** Fit modeling against team's current roster and system. Contract value projection against market.
- **Trade analysis.** Simulate roster outcomes for proposed trades. Cap impact. Fit score. Depth chart projection.
- **Salary cap optimization.** Multi-year roster construction with cap constraints.
- **G-League pipeline.** Two-way contract value. Call-up readiness. Development trajectory.
- **International scouting.** EuroLeague, EuroCup, CBA, NBL, BAL film. Novel market.
- **Player development.** Individual improvement tracking across seasons.
- **Load / risk modeling.** Biomechanics and usage risk via partnerships (Second Spectrum, Sportradar, league data feeds). Stay *out* of medical data itself.

**Data requirements (all net-new vs. Stage 7):**
- Contract + salary cap data (Spotrac, RealGM, Basketball Insiders, or direct league deal).
- Historical player trajectory database (back to ~1996 for NBA; shorter for international).
- Biomechanical / tracking data (Second Spectrum for NBA, Synergy for college + pro feeds).
- Combine + pre-draft testing data (for draft product).
- League schedule + travel data (for rest/fatigue modeling).

**Integrations required (all net-new):**
- Each pro team runs custom analytics stacks. Selling in means meeting them where they are — Tableau, Databricks, Snowflake, or custom internal tools. TEX is a source-of-truth they pipe *into* their stack, not a replacement.
- Synergy Sports, Second Spectrum, Hudl SportVU, Sportradar.
- League data feeds (NBA Advanced Stats, FIBA, EuroLeague).

**Compliance additions:**
- Pro league data licensing (NBA has strict rules on derivative analytics products).
- Per-team NDA/DPA standards (each franchise has its own).
- SOC 2 Type II + ISO 27001 for European clients.
- Multi-region data residency (EU data in EU, per GDPR).

**Team additions:**
- VP Engineering (the Stage 8 stack isn't a founder-ships-it product).
- Head of Basketball (former GM, AGM, or Director of Analytics from NBA/top college).
- VP Sales (enterprise SaaS + sports tech background).
- Legal / compliance (dedicated).
- 15-30 total headcount typical at Stage 8 maturity.

**Capital:** Series B ($25-75M). Raise on Series A traction + strategic interest signal (league partnerships, franchise inquiries).

**The product at maturity (VISION.md Stage 3 fully realized):**
A team's entire basketball operation lives in TEX. GM and coaching staff open TEX every day. It knows their system, their roster, their cap situation, their draft board, their opponents, their development plans. It is not assisting — it is the shared source of truth for all basketball decisions, and every decision flows through it.

**The moat at maturity:**
- Corrections DB: 6-7 figures of labeled basketball examples.
- Proprietary fine-tuned models specific to basketball video + structured basketball reasoning.
- Proprietary pattern library covering every team, coach, and player in organized basketball.
- Integration depth with film providers, data vendors, league feeds that takes years to replicate.
- Customer lock-in through system integration — ripping TEX out of a franchise's workflow is a 6-month project, not a cancellation.

**Typical window:** 24-36 months from Stage 7. Total company age at Stage 8 maturity: 5-7 years from today.

---

## WHAT A TOP APPLIED-AI COMPANY DOES AT EVERY STAGE

These disciplines apply across every stage. Top companies do not bolt them on later — they run them from Stage 1.

### 1. Eval-Driven Development (every stage)

Every prompt change, model change, or pipeline change is graded against the golden set before it merges. Regressions in captured / hallucinated scores block the merge. This single habit separates companies that ship reliable AI from companies that ship plausible AI.

- `EVAL_SCORES.md` is source of truth. Every run logged.
- Golden set grows every quarter (add 2-3 films).
- Blind set refreshed every quarter (churn the films so tuning can't overfit).
- Rubric stays stable (captured / missed / hallucinated). Never change the rubric to make scores look better.
- **Internal grading UI is non-negotiable.** Built in Stage 1 (see above), extended every stage. A grader that takes 20-40 min per film beats a spreadsheet that takes 3-4 hours by ~6x. That multiplier is the difference between iterating on prompts twice a week and twice a day, which is the difference between shipping a good product and shipping a great one. Companies that cheap out on eval tooling ship AI that plateaus early.

### 2. Corrections Database As Flywheel (Stage 4+)

Every correction from Tommy or a user is labeled data. This is the core moat.

- Structured capture: section, claim text, correctness verdict, correction text, category, `prompt_version`.
- Targets: 100 corrections by end of Stage 4, 1,000 by end of Stage 6, 10,000 by end of Stage 7.
- Used three ways: (a) prompt refinement signals, (b) fine-tuning dataset, (c) regression test set.

### 3. Fine-Tuning (Stage 7+)

At ≥10,000 labeled examples, fine-tuning starts to measurably outperform prompt engineering on the frontier base model.

- Fine-tune on top of the strongest available base model at that time. Do not lock into one vendor.
- Ship the fine-tuned model only if it beats the prompt-engineered frontier model on the golden + blind sets.
- Retrain quarterly as the corrections DB grows.
- Keep the prompt-engineered frontier path as a fallback (per CLAUDE.md AI PROVIDER RULES).

### 4. Moat Infrastructure (every stage)

The corrections DB is the core moat but not the only one. Build moat infrastructure early so it compounds.

- **Pattern library.** Cross-game tendencies surfaced as structured data (opponent X runs horns 34% of 3rd-quarter possessions). Grows every game uploaded.
- **Basketball knowledge base.** Structured ontology of sets, schemes, coverages, archetypes. Starts small, becomes the RAG backbone.
- **Proprietary film archive (where licensing permits).** The longer TEX runs, the deeper the archive. Gated by what licenses allow.

### 5. Distribution Advantages (Stage 4+)

- **Founder-led sales through Stage 6.** Tommy sells every early deal. Not delegatable.
- **Network effects.** Every coach on TEX scouts other coaches' teams. Word spreads in narrow basketball circles fast. Design for it.
- **Referral infrastructure.** Track attribution. Build explicit referral incentives by Stage 5.
- **Enterprise motion emerges at Stage 7.** First AE hires only when founder-led sales can no longer keep up.

### 6. Integrations (Stage 6+)

Every integration creates switching cost. Build the top 3 per market.

- HS/AAU (Stage 6): Hudl, Krossover, Synergy (coach-level access).
- NCAA (Stage 7): Synergy, XOS Digital, Sportscode / Hudl Assist.
- Pro (Stage 8): Synergy, Second Spectrum, Sportradar, SportVU, league feeds.

### 7. Compliance (staged, but think about it from Stage 1)

- Stage 5: ToS, Privacy Policy, DPA template, state-by-state minors review.
- Stage 6: SOC 2 Type I, GDPR readiness, film deletion policy.
- Stage 7: SOC 2 Type II, FERPA, NCAA compliance review.
- Stage 8: ISO 27001, multi-region data residency, league data licensing, per-team DPA.

### 8. Hiring Sequence (opinionated baseline)

- Stage 5: Second engineer (product/infra).
- Stage 6: Third engineer, part-time basketball ops, part-time customer success.
- Stage 7: Enterprise AE, full-time CS lead, full-time basketball expert.
- Stage 8: VP Eng, Head of Basketball, VP Sales, legal/compliance. Scale to 15-30 total.

### 9. Capital Strategy

- Stages 1-4: Bootstrap. Do not raise until Stage 3+ validation.
- Stage 5: Optional angel round ($250K-$1M) on Stage 4 cohort data. Not required.
- Stage 6: Seed round ($2-5M) on Stage 5 revenue + retention data.
- Stage 7: Series A ($10-25M) on Stage 6 ARR + NCAA pipeline.
- Stage 8: Series B ($25-75M) on Stage 7 traction + strategic interest.

Never raise on promises. Always raise on data.

---

## KEY RISKS TO STAGE-6-AND-BEYOND

Failure modes that derail companies at TEX's trajectory. Flagged here so decisions stay calibrated.

### Risk 1 — Overfitting the golden set
Symptom: Scores climb on golden but stall on blind. Mitigation: Stage 2 discipline + quarterly golden/blind refresh.

### Risk 2 — Wrapper drift
Symptom: Eng time goes to UI polish, billing, dashboards, admin tools — everything except AI quality. Mitigation: Every sprint allocates ≥60% of eng time to AI quality, ≤40% to wrapper. Enforced at planning.

### Risk 3 — Premature scaling
Symptom: Raising seed / A before Stage 5 retention is real. Burning capital on marketing before PMF. Mitigation: Do not raise until gates are met. Do not hire ahead of revenue.

### Risk 4 — Losing the corrections moat
Two separate failure modes that both drain the data flywheel:

*4a — Tommy is the grading bottleneck.* Grading reports in a spreadsheet is too slow. A new prompt version ships, grading queue grows, Tommy falls behind, eval loop stalls, prompt iteration slows to weekly instead of daily. Mitigation: **Ship the internal grading UI in Stage 1** (see Stage 1 definition of done). Target: <40 min per golden-film grading session. Every grading action auto-writes to `EVAL_SCORES.md` + corrections DB — no manual double-entry.

*4b — Users skip corrections in production.* Coaches in Stages 5-8 never submit corrections, so the only labeled data is what Tommy grades internally. Mitigation: Invest in Phase 4 Training Mode UX hard. Correction submission must take <30s for a coach. Instrument submission rates as a first-class product metric. Consider small incentives (credit toward next report, prioritized support) for coaches who correct regularly.

### Risk 5 — Vendor lock-in
Symptom: Architecture assumes Gemini is the only video model forever. Mitigation: CLAUDE.md AI PROVIDER RULES already enforce single-import abstraction. Keep this religiously. When a better model appears, flip the env var.

### Risk 6 — NCAA / pro compliance surprise
Symptom: Shipping a feature that violates NCAA recruiting rules or NBA data-licensing terms. Mitigation: Stage 7 entry triggers a full compliance review. Consumer SaaS rules do not map to institutional sports.

### Risk 7 — Founder burnout
Symptom: Tommy is grading bottleneck, sales bottleneck, product bottleneck, and hiring manager simultaneously. Mitigation: First hire at Stage 5 relieves the tightest bottleneck. Usually second engineer. Second hire relieves the next.

### Risk 8 — Distribution dries up
Symptom: Organic referrals slow after Stage 6. Paid acquisition expensive in narrow vertical markets. Mitigation: Stage 7's NCAA motion is the planned expansion. Do not over-invest in paid HS/AAU acquisition if NCAA is reachable.

### Risk 9 — Data moat erosion from model commoditization
Symptom: Frontier models close the gap on basketball reasoning without training on TEX's corrections. Mitigation: Corrections DB must stay proprietary. Pattern library + basketball knowledge base + fine-tuned model + integration depth + customer workflow integration together form the moat — no single layer is enough.

### Risk 10 — Minors data incident
Symptom: HS/AAU film contains minors; a data breach or misuse incident creates existential legal + reputational risk. Mitigation: Minors-protection policy shipped at Stage 5. State-by-state review. Hard deletion + no-training guarantees for film containing minors. Incident response plan rehearsed annually.

---

## HOW THIS LADDER RELATES TO THE ENGINEERING PHASES

- **Phases 1-3 (above):** Build the product that passes Stage 1.
- **Phase 4 (Training Mode):** The corrections DB that fuels Stages 4-8.
- **Phase 5 (Launch):** The hardening required to enter Stage 5 with real paying users.
- **Ladder Stages 1-4:** Happen in parallel with Phase 5 engineering work.
- **Ladder Stages 5-8:** Each unlocks new engineering phases (scale, compliance, multi-tenant, integrations, fine-tuning, enterprise APIs, etc.) — treated as future roadmap, tracked here as they crystallize.

When new engineering phases are added (Phase 6+), they map explicitly to the ladder stage that drove them. This keeps engineering accountable to commercial trajectory and keeps commercial strategy accountable to what is actually shippable.

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

*Last updated: April 20, 2026 (evening) — Commercial Readiness Ladder added. Covers Stages 1-8 from current golden-set work through HS/AAU general launch, NCAA expansion, and the long-term AI GM product for NBA / WNBA / G-League / international front offices. Documents per-stage definition of done, gates, capital strategy, hiring sequence, compliance requirements, and key risks. Maps every stage back to the engineering phases above. Prior engineering update: April 20 mid-day (pipeline wiring + idempotency fix + migration 016 apply).*
