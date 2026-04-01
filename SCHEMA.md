# SCHEMA.md — TEX v2

Complete database schema. Every table, every column, every index, every constraint.
This is the source of truth for Neon PostgreSQL. Migrations are numbered SQL files in `backend/migrations/`.
ARCHITECTURE.md documents why decisions were made. This document documents what to build.
Raw SQL only. No ORM. Read this before writing a single query.

---

## RULES THAT APPLY TO THIS ENTIRE SCHEMA

1. Every table has `id uuid PRIMARY KEY DEFAULT gen_random_uuid()`.
2. Every user-facing table has `user_id uuid NOT NULL REFERENCES users(id)` and an index on it.
3. Every query against a user-facing table must include `WHERE user_id = %s`. Structural, not advisory.
4. `deleted_at timestamptz` is used for soft deletes. Hard deletes only in DECISIONS.md with Tommy approval.
5. `corrections` has no `deleted_at`. It is never soft-deleted or hard-deleted. Permanent.
6. Raw SQL. Parameterized queries. No string interpolation into SQL. Ever.
7. Migrations are applied in order. Never modify a migration that has been applied to production.
   Write a new migration to correct a prior one.
8. pgvector is installed at migration 012. No vector columns exist until Phase 3.

---

## MIGRATION ORDER

```
001_create_users.sql
002_create_teams.sql
003_create_roster_players.sql
004_create_films.sql
005_create_film_chunks.sql
006_create_reports.sql
007_create_report_films.sql
008_create_report_sections.sql
009_create_corrections.sql
010_create_film_analysis_cache.sql
011_create_dead_letter_tasks.sql
012_create_notifications.sql
013_create_payments.sql
014_create_fallback_events.sql
015_install_pgvector.sql
```

Apply with `python scripts/migrate.py`. Script tracks applied migrations in a `schema_migrations` table.
Never apply out of order. Never re-apply a migration. The script is idempotent by design — running it
twice on the same database produces the same result as running it once.

---

## TABLE: users

Created at migration 001. No foreign key dependencies.

```sql
CREATE TABLE users (
  id                  uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  clerk_id            text        NOT NULL UNIQUE,
  email               text        NOT NULL,
  is_admin            boolean     NOT NULL DEFAULT false,
  reports_used        integer     NOT NULL DEFAULT 0,
  report_credits      integer     NOT NULL DEFAULT 0,   -- free credits from technical failures
  stripe_customer_id  text,                             -- null until first payment attempt
  deleted_at          timestamptz,                      -- set on Clerk user.deleted webhook
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_users_clerk_id ON users(clerk_id);
CREATE INDEX idx_users_stripe_customer_id ON users(stripe_customer_id)
  WHERE stripe_customer_id IS NOT NULL;
```

**`reports_used`:** incremented on every report generation (paid or free). Used for the first-report-free
gate: `WHERE reports_used = 0`. Never decremented — even if a report fails.

**`report_credits`:** incremented when a technical failure occurs after payment. Checked before
the Stripe gate — credits skip checkout entirely. Decremented when a credit is consumed.

**`is_admin`:** checked on every admin request via a live DB query. Not cached. Not in the JWT.
A coach whose `is_admin` is set to true can access training mode endpoints. No other difference.

**`deleted_at`:** set when Clerk fires `user.deleted`. A deleted user's rows are never returned
in queries that include `AND deleted_at IS NULL`. Their data is not deleted — just hidden.

---

## TABLE: teams

Created at migration 002. Depends on: `users`.

```sql
CREATE TABLE teams (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid        NOT NULL REFERENCES users(id),
  name             text        NOT NULL,
  level            text        NOT NULL DEFAULT 'unknown',
                               -- 'd1' | 'd2' | 'd3' | 'eybl' | 'aau' | 'high_school' | 'unknown'
  stats_source_url text,       -- Phase 2: link to public stats page for box score ingestion
  deleted_at       timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_teams_user_id ON teams(user_id);
```

`stats_source_url` is null at launch. Phase 2 box score ingestion uses it as the scrape target.
The column exists now so Phase 2 adds data without an `ALTER TABLE`.

`level` drives Phase 2 box score source selection — D1 pulls from ESPN/NCAA, EYBL from Nike portal.
Default `'unknown'` is acceptable at launch — coaches can tag it later.

---

## TABLE: roster_players

Created at migration 003. Depends on: `users`, `teams`.

```sql
CREATE TABLE roster_players (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid        NOT NULL REFERENCES users(id),
  team_id          uuid        NOT NULL REFERENCES teams(id),
  jersey_number    text        NOT NULL,
  full_name        text        NOT NULL,
  position         text,       -- 'PG' | 'SG' | 'SF' | 'PF' | 'C'
  height           text,       -- stored as string: '6''4"' — no conversion logic needed
  dominant_hand    text,       -- 'right' | 'left' | 'ambidextrous'
  role             text,       -- 'primary_initiator' | 'secondary_handler' | 'spacer'
                               -- | 'screener' | 'finisher' | 'role_player'
  notes            text,       -- coach's free text. anything that doesn't fit a field.
  deleted_at       timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (team_id, jersey_number)
);

CREATE INDEX idx_roster_players_user_id ON roster_players(user_id);
CREATE INDEX idx_roster_players_team_id ON roster_players(team_id);
```

`user_id` is denormalized onto this table even though `team_id` already traces to the user.
Reason: the mandatory `WHERE user_id = %s` scoping rule applies to every user-facing table.
Without `user_id` directly on `roster_players`, every roster query requires a join to `teams`
just to enforce the user scoping. The denormalization is intentional and worth the tradeoff.

`UNIQUE (team_id, jersey_number)` prevents a duplicate jersey number on the same team.
The same jersey number can exist on different teams.

Phase 3 will add columns here (`shooting_zones jsonb`, `stat_profile jsonb`, `evaluation_confirmed boolean`).
Those columns are added via a new migration — do not put them here now.

---

## TABLE: films

Created at migration 004. Depends on: `users`, `teams`.

```sql
CREATE TABLE films (
  id                        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                   uuid        NOT NULL REFERENCES users(id),
  team_id                   uuid        NOT NULL REFERENCES teams(id),
  file_name                 text        NOT NULL,
  file_size_bytes           bigint      NOT NULL,
  r2_key                    text        NOT NULL,           -- raw film in R2: films/{user_id}/{film_id}/{filename}
  duration_seconds          integer,                       -- null until FFprobe runs
  file_hash                 text,                          -- SHA-256 of raw bytes. null until worker downloads.
  status                    text        NOT NULL DEFAULT 'uploaded',
                            -- 'uploaded' | 'processing' | 'processed' | 'error'
  gemini_processing_status  text,
                            -- null until chunks are uploading: 'uploading' | 'active' | 'failed'
  chunk_count               integer,                       -- null until FFmpeg splits
  error_message             text,
  deleted_at                timestamptz,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_films_user_id ON films(user_id);
CREATE INDEX idx_films_team_id ON films(team_id);
CREATE INDEX idx_films_status ON films(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_films_file_hash ON films(file_hash) WHERE file_hash IS NOT NULL;
```

`file_hash` is null on insert — the file has not been downloaded to the worker yet.
The worker computes SHA-256 after downloading the raw film to /tmp, then updates this column.
The film fingerprint cache lookup (`film_analysis_cache`) uses this hash.

`status` progression: `uploaded` → `processing` → `processed` → (report triggered) → `complete`
`error` is a terminal state that requires human intervention or retry.

`duration_seconds` and `chunk_count` are null until FFprobe runs on the worker. UI shows
"processing" until these are populated.

`r2_key` stores only the raw film. Chunk keys live in `film_chunks.r2_chunk_key`.
The raw film is never deleted — kept permanently for re-processing and audit.

---

## TABLE: film_chunks

Created at migration 005. Depends on: `films`. New in v2 — does not exist in v1.

```sql
CREATE TABLE film_chunks (
  id                     uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  film_id                uuid        NOT NULL REFERENCES films(id),
  chunk_index            integer     NOT NULL,               -- 0-indexed. chunk_000, chunk_001...
  duration_seconds       integer     NOT NULL,
  r2_chunk_key           text        NOT NULL,               -- never null. R2 is the re-upload source.
  gemini_file_uri        text,                               -- null until upload completes: files/abc123
  gemini_file_state      text        NOT NULL DEFAULT 'uploading',
                         -- 'uploading' | 'active' | 'failed'
  gemini_file_expires_at timestamptz,                        -- null until upload completes
  created_at             timestamptz NOT NULL DEFAULT now(),
  UNIQUE (film_id, chunk_index)
);

CREATE INDEX idx_film_chunks_film_id ON film_chunks(film_id);
CREATE INDEX idx_film_chunks_expiry ON film_chunks(gemini_file_expires_at)
  WHERE gemini_file_state = 'active';
```

`r2_chunk_key` is never null. The chunk file must be in R2 before this row is created.
Sequence: FFmpeg splits → chunk uploaded to R2 → row inserted → chunk uploaded to Gemini File API
→ `gemini_file_uri` and `gemini_file_expires_at` populated.

`gemini_file_expires_at` comes from `expireTime` in the Gemini File API response. Gemini
files expire 48 hours after upload. The expiry index accelerates `get_valid_chunk_uris()` —
the query that finds chunks needing re-upload before report generation.

**Expiry check query (used by `get_valid_chunk_uris()`):**

```sql
SELECT id, film_id, r2_chunk_key, gemini_file_uri
FROM film_chunks
WHERE film_id = %s
  AND gemini_file_state = 'active'
  AND gemini_file_expires_at < now() + interval '1 hour';
-- 1-hour buffer: don't use a URI that expires mid-report generation
```

R2 chunk files are deleted only after `reports.status = 'complete'`. Never before.
The deletion happens inside `generate_report` task after the status update.
There is no cleanup path in this table — rows stay until the worker deletes the R2 objects
and then soft-deletes or leaves the rows (they are cheap storage and useful for debugging).

---

## TABLE: reports

Created at migration 006. Depends on: `users`, `teams`.

```sql
CREATE TABLE reports (
  id                      uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                 uuid        NOT NULL REFERENCES users(id),
  team_id                 uuid        NOT NULL REFERENCES teams(id),
  title                   text,                              -- coach-visible name. auto-generated if null.
  status                  text        NOT NULL DEFAULT 'pending',
                          -- 'pending' | 'processing' | 'complete' | 'error' | 'partial'
  pdf_r2_key              text,                              -- null until PDF is uploaded to R2
  prompt_version          text        NOT NULL,              -- version of prompts used. from PROMPTS.md.
  generation_time_seconds integer,                           -- null until complete
  error_message           text,
  completed_at            timestamptz,                       -- null until status = 'complete' or 'partial'
  deleted_at              timestamptz,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_reports_user_id ON reports(user_id);
CREATE INDEX idx_reports_team_id ON reports(team_id);
CREATE INDEX idx_reports_status ON reports(status) WHERE deleted_at IS NULL;
```

`status = 'partial'` means one or more sections errored but the report was generated with
the available sections. The coach receives what TEX could produce, clearly labeled.
`status = 'error'` means no sections completed — no report was generated. Credit is applied.

`prompt_version` is set at report creation from the current version in `prompts/` directory.
It never changes after creation. This is how you know which prompt generated a given report —
critical for the correction feedback loop and cache invalidation.

`pdf_r2_key` is null until the PDF is assembled and uploaded. The UI polls on `status` —
when status becomes `complete`, the frontend calls `GET /reports/{id}` which returns a
presigned R2 URL generated from `pdf_r2_key`. The URL is never stored — generated on demand.

---

## TABLE: report_films

Created at migration 007. Depends on: `reports`, `films`. Join table — a report can span multiple films.

```sql
CREATE TABLE report_films (
  report_id  uuid NOT NULL REFERENCES reports(id),
  film_id    uuid NOT NULL REFERENCES films(id),
  created_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (report_id, film_id)
);

CREATE INDEX idx_report_films_film_id ON report_films(film_id);
```

A report references 1-N films. Multi-film reports (Phase 2+) use all listed films to build
the context cache — all chunk URIs from all films are passed to the orchestrator.
At launch, every report references exactly one film. The join table exists from day one
to avoid a schema migration when multi-film reports are needed.

No `user_id` column here — this is a join table, not a user-facing table accessed independently.
Access always happens via `reports.user_id` through a join: `JOIN reports ON reports.id = report_films.report_id WHERE reports.user_id = %s`.

---

## TABLE: report_sections

Created at migration 008. Depends on: `reports`.

```sql
CREATE TABLE report_sections (
  id                       uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id                uuid        NOT NULL REFERENCES reports(id),
  section_type             text        NOT NULL,
                           -- 'offensive_sets' | 'defensive_schemes' | 'pnr_coverage'
                           -- | 'player_pages' | 'game_plan' | 'adjustments_practice'
  status                   text        NOT NULL DEFAULT 'pending',
                           -- 'pending' | 'processing' | 'complete' | 'error'
  content                  text,                              -- generated section text. null until complete.
  model_used               text,                             -- 'gemini-2.5-pro' | 'gemini-2.5-flash' | 'claude-3-5-sonnet'
  prompt_version           text        NOT NULL,
  chunk_count              integer,                          -- number of film chunks analyzed (sections 1-4 only)
  tokens_input             integer,
  tokens_output            integer,
  generation_time_seconds  integer,
  error_message            text,
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  UNIQUE (report_id, section_type)
);

CREATE INDEX idx_report_sections_report_id ON report_sections(report_id);
CREATE INDEX idx_report_sections_status ON report_sections(status);
```

`UNIQUE (report_id, section_type)` enforces one row per section per report. On retry,
`INSERT ... ON CONFLICT (report_id, section_type) DO UPDATE SET status = 'processing'`
rather than creating duplicate rows.

`model_used` records which model actually generated the section. If Flash failed and
Claude was used as fallback, this column reflects `'claude-3-5-sonnet'` — not the
intended primary. This is used in the correction analysis: corrections on Claude-generated
sections have different signal value than corrections on Flash-generated sections.

`tokens_input` and `tokens_output` drive `tex.gemini.tokens_used` in Datadog and the
per-report cost calculation in `tex.report.cost_usd`. Never null on a completed section.

---

## TABLE: corrections

Created at migration 009. Depends on: `reports`, `films`. Never deleted. Never soft-deleted.

```sql
CREATE TABLE corrections (
  id              uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id       uuid        NOT NULL REFERENCES reports(id),
  film_id         uuid        NOT NULL REFERENCES films(id),
  section_type    text        NOT NULL,
                  -- 'offensive_sets' | 'defensive_schemes' | 'pnr_coverage'
                  -- | 'player_pages' | 'game_plan' | 'adjustments_practice'
  phase           integer     NOT NULL DEFAULT 1,    -- 1 | 2 | 3 | 4 — which AI_STRATEGY phase
  ai_claim        text        NOT NULL,              -- exact text Gemini/Claude produced
  is_correct      boolean     NOT NULL,
  correct_claim   text,                              -- Tommy's correction. null if is_correct = true.
  category        text        NOT NULL,
                  -- 'set_identification' | 'player_attribution' | 'frequency_count'
                  -- | 'tendency' | 'coverage_type' | 'personnel_evaluation'
                  -- | 'strategic_reasoning'
  game_count      integer,                           -- Phase 2+: how many games this claim spans
  confidence      text        NOT NULL DEFAULT 'high',  -- 'high' | 'medium' | 'low'
  prompt_version  text        NOT NULL,              -- which prompt version produced the ai_claim
  admin_notes     text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now()
  -- no deleted_at. corrections are permanent. they are the training dataset.
);

CREATE INDEX idx_corrections_report_id ON corrections(report_id);
CREATE INDEX idx_corrections_film_id ON corrections(film_id);
CREATE INDEX idx_corrections_category ON corrections(category);
CREATE INDEX idx_corrections_prompt_version ON corrections(prompt_version);
CREATE INDEX idx_corrections_section_type ON corrections(section_type);
CREATE INDEX idx_corrections_is_correct ON corrections(is_correct);
```

**Why so many indexes:** The weekly pattern analyzer queries this table along every dimension.
`GROUP BY category WHERE prompt_version = X` — needs category + prompt_version.
`WHERE section_type = 'offensive_sets' AND is_correct = false` — needs both.
The table grows slowly (corrections require Tommy's manual review) but is read frequently.
The indexes pay for themselves immediately.

**No `user_id` on this table.** Corrections are never returned to a coach — they are internal
training data accessed only by admin routes. Every admin route is gated by `is_admin = true`.
The admin context provides implicit data scoping — Tommy sees everything. No coach sees anything.

**`ai_claim` is the exact text.** Not a summary. Not a paraphrase. The exact sentence or
paragraph that Gemini produced. This is the anchor for the training loop — corrections
grounded in the model's exact output, not a re-interpretation of it.

**`correct_claim` is null when `is_correct = true`.** A confirmation saves the claim as-is.
A rejection requires Tommy to write the correct version. The `UPDATE` trigger on `is_correct`
should enforce this at the application layer (not the DB — application-layer validation via Pydantic).

---

## TABLE: film_analysis_cache

Created at migration 010. Depends on: `films`. New in v2 — does not exist in v1.

```sql
CREATE TABLE film_analysis_cache (
  id             uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  file_hash      text        NOT NULL UNIQUE,        -- SHA-256 of raw film bytes
  film_id        uuid        REFERENCES films(id),   -- first film that generated this entry
  sections       jsonb       NOT NULL,               -- all 4 section outputs: {"offensive_sets": "...", ...}
  prompt_version text        NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now()
  -- no deleted_at. cache entries are never soft-deleted.
  -- invalidation is by prompt_version, not deletion.
  -- stale entries (old prompt_version) are purged by weekly maintenance task.
);

CREATE UNIQUE INDEX idx_film_cache_hash ON film_analysis_cache(file_hash);
CREATE INDEX idx_film_cache_prompt_version ON film_analysis_cache(prompt_version);
```

**Cache hit query:**

```sql
SELECT sections
FROM film_analysis_cache
WHERE file_hash = %s
  AND prompt_version = %s;
-- if row exists: return sections, skip all Gemini calls
-- if row absent: run full pipeline, write result here
```

**Cache write (after sections 1-4 complete):**

```sql
INSERT INTO film_analysis_cache (file_hash, film_id, sections, prompt_version)
VALUES (%s, %s, %s, %s)
ON CONFLICT (file_hash) DO NOTHING;
-- ON CONFLICT DO NOTHING: if two workers race on the same film, the second write is a no-op.
```

`sections` JSONB structure:
```json
{
  "offensive_sets": "full section text...",
  "defensive_schemes": "full section text...",
  "pnr_coverage": "full section text...",
  "player_pages": "full section text..."
}
```

Only sections 1-4 are cached. Sections 5-6 are synthesized from sections 1-4 output and
cannot be meaningfully reused — the game plan and adjustments depend on which coach is
asking and potentially which roster is being used (Phase 3+). Caching 1-4 eliminates
90% of the video token cost. Sections 5-6 are text-only and cheap by comparison.

**Cache invalidation:** When `prompt_version` increments, existing cache entries for the
old version are stale. Workers skip entries where `prompt_version != current_version`.
A weekly maintenance task deletes entries older than 30 days with stale prompt versions.
Never delete a cache entry that matches the current prompt version.

---

## TABLE: dead_letter_tasks

Created at migration 011. No foreign key constraints — orphan-safe by design.

```sql
CREATE TABLE dead_letter_tasks (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  task_name        text        NOT NULL,    -- 'process_film' | 'generate_report' | 'run_section' | 'notify_coach'
  task_args        jsonb       NOT NULL,    -- full args the task was called with. enables replay.
  queue            text        NOT NULL,    -- which Celery queue
  error_message    text        NOT NULL,
  error_traceback  text,
  retry_count      integer     NOT NULL,
  film_id          uuid,                    -- null if not film-related
  report_id        uuid,                    -- null if not report-related
  user_id          uuid,
  created_at       timestamptz NOT NULL DEFAULT now(),
  replayed_at      timestamptz,             -- null until manually replayed
  resolved_at      timestamptz              -- null until marked resolved
);

CREATE INDEX idx_dead_letter_created_at ON dead_letter_tasks(created_at DESC);
CREATE INDEX idx_dead_letter_task_name ON dead_letter_tasks(task_name);
CREATE INDEX idx_dead_letter_user_id ON dead_letter_tasks(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_dead_letter_unresolved ON dead_letter_tasks(created_at)
  WHERE resolved_at IS NULL;
```

No FK constraints on `film_id`, `report_id`, `user_id` — intentional.
A dead letter task records the context of a failure for debugging and replay.
If the film or report row was itself corrupted and doesn't exist, the dead letter record
still needs to persist. FK constraints would prevent writing the dead letter in that scenario —
exactly the scenario where you most need the record.

`task_args` JSONB stores the full arguments that can be passed directly to `celery_app.send_task()`
for replay. Example: `{"film_id": "uuid-here"}` for a `process_film` task.

**Replay query:**

```sql
SELECT id, task_name, task_args FROM dead_letter_tasks
WHERE resolved_at IS NULL
ORDER BY created_at DESC;
```

---

## TABLE: notifications

Created at migration 012. Depends on: `users`, `reports`.

```sql
CREATE TABLE notifications (
  id         uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id    uuid        NOT NULL REFERENCES users(id),
  report_id  uuid        REFERENCES reports(id),      -- null for non-report notifications
  type       text        NOT NULL,
             -- 'report_complete' | 'report_failed' | 'report_partial'
             -- | 'report_failed_credit_applied'
  message    text        NOT NULL,
  read_at    timestamptz,                              -- null until coach reads it
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_unread ON notifications(user_id, created_at DESC)
  WHERE read_at IS NULL;
```

`type = 'report_failed_credit_applied'` is the notification coaches see when a technical
failure occurred and a credit was applied to their account. Message text:
"Your report could not be completed. We've added a free report to your account."

The unread partial index (`WHERE read_at IS NULL`) accelerates the dashboard badge count
query — fetching unread notification counts is called on every dashboard load.

---

## TABLE: payments

Created at migration 013. Depends on: `users`, `reports`.

```sql
CREATE TABLE payments (
  id                        uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id                   uuid        NOT NULL REFERENCES users(id),
  report_id                 uuid        REFERENCES reports(id),    -- null until report is created
  stripe_session_id         text        NOT NULL UNIQUE,
  stripe_payment_intent_id  text,                                  -- populated after checkout.session.completed
  amount_cents              integer     NOT NULL,
  currency                  text        NOT NULL DEFAULT 'usd',
  status                    text        NOT NULL DEFAULT 'pending',
                            -- 'pending' | 'complete' | 'refunded'
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_payments_stripe_session_id ON payments(stripe_session_id);
```

`report_id` is null when the payment row is created (before the Stripe checkout is completed).
The Stripe webhook handler updates `report_id` and `status = 'complete'` when the session completes,
then creates the report record and enqueues generation.

**Payment flow sequence:**
1. Coach clicks "Generate Report" → `POST /reports` → payment row inserted with `status = 'pending'`, `report_id = null`
2. Coach redirected to Stripe checkout
3. Stripe fires `checkout.session.completed` webhook
4. Webhook handler: creates report record, updates payment `report_id` + `status = 'complete'`, enqueues task

If the webhook never fires (coach abandons checkout), the payment row stays `pending` indefinitely.
These are harmless — no report is generated, no credit consumed.

---

## TABLE: fallback_events

Created at migration 014. Depends on: `reports`.

```sql
CREATE TABLE fallback_events (
  id               uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id        uuid        NOT NULL REFERENCES reports(id),
  section_type     text        NOT NULL,
  primary_provider text        NOT NULL,     -- 'gemini_flash'
  fallback_provider text       NOT NULL,     -- 'claude_sonnet'
  error_reason     text        NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_fallback_events_report_id ON fallback_events(report_id);
CREATE INDEX idx_fallback_events_created_at ON fallback_events(created_at DESC);
```

Every fallback event writes here before calling Claude. Used for:
1. Datadog metric `tex.fallback.triggered` — spike signals Flash degradation
2. Admin dashboard: how often is the fallback being used? Is Flash reliability acceptable?
3. Audit trail: which sections in a given report used Claude vs Flash?

The Datadog alert on this table: 5+ fallback events in any 1-hour window = Flash may be degraded.
Investigate before coaches notice quality difference between Flash and Sonnet output.

---

## TABLE: schema_migrations

Created by `scripts/migrate.py` before any other migrations run. Tracks applied migrations.

```sql
CREATE TABLE IF NOT EXISTS schema_migrations (
  filename   text        PRIMARY KEY,
  applied_at timestamptz NOT NULL DEFAULT now()
);
```

`scripts/migrate.py` reads all `.sql` files from `backend/migrations/`, checks which are already
in `schema_migrations`, and applies the unapplied ones in filename order. Never re-applies.

---

## PGVECTOR

```sql
-- 015_install_pgvector.sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Extension is installed. No vector columns exist yet. Phase 3 adds:
- `roster_players.tendency_embedding vector(1536)` — player tendency vector for similarity search
- `film_analysis_cache.embedding vector(1536)` — film-level embedding for cross-film pattern retrieval

Do not add these columns until Phase 3. The extension install is the only Phase 0 action.

---

## QUERY PATTERNS

Reference patterns for the most common DB operations. Every service function follows these shapes.

**Fetch user by Clerk ID (auth flow — called on every request):**

```sql
SELECT id, is_admin, reports_used, report_credits, stripe_customer_id, deleted_at
FROM users
WHERE clerk_id = %s AND deleted_at IS NULL;
```

**Fetch films for a user (dashboard):**

```sql
SELECT id, team_id, file_name, file_size_bytes, duration_seconds, status, created_at
FROM films
WHERE user_id = %s AND deleted_at IS NULL
ORDER BY created_at DESC
LIMIT 20;
```

**Fetch report with sections (report status page):**

```sql
-- report
SELECT id, team_id, status, pdf_r2_key, prompt_version, error_message, completed_at, created_at
FROM reports
WHERE id = %s AND user_id = %s AND deleted_at IS NULL;

-- sections (separate query — not a join)
SELECT section_type, status, content, model_used, error_message
FROM report_sections
WHERE report_id = %s
ORDER BY section_type;
```

**Film fingerprint cache lookup (called before every report generation):**

```sql
SELECT sections
FROM film_analysis_cache
WHERE file_hash = %s AND prompt_version = %s;
```

**Expired chunks that need re-upload:**

```sql
SELECT id, film_id, r2_chunk_key, chunk_index
FROM film_chunks
WHERE film_id = %s
  AND gemini_file_state = 'active'
  AND gemini_file_expires_at < now() + interval '1 hour';
```

**Unread notification count (dashboard badge):**

```sql
SELECT COUNT(*) FROM notifications
WHERE user_id = %s AND read_at IS NULL;
```

**Pattern analyzer — error rate by category (weekly):**

```sql
SELECT
  category,
  COUNT(*) FILTER (WHERE is_correct = false) AS error_count,
  COUNT(*) AS total_count,
  ROUND(100.0 * COUNT(*) FILTER (WHERE is_correct = false) / COUNT(*), 1) AS error_rate
FROM corrections
WHERE prompt_version = %s
GROUP BY category
ORDER BY error_count DESC;
```

**Stuck job recovery (startup recovery function — runs on every worker boot):**

```sql
-- films stuck in 'processing' for longer than 2x the hard timeout
SELECT id FROM films
WHERE status = 'processing'
  AND updated_at < now() - interval '2 hours'
  AND deleted_at IS NULL;

-- reports stuck in 'processing' for longer than 2x the hard timeout
SELECT id FROM reports
WHERE status = 'processing'
  AND updated_at < now() - interval '1 hour'
  AND deleted_at IS NULL;
```

---

## DATA TYPES — DECISIONS AND RATIONALE

**`uuid` for all primary keys:** Avoids sequential ID enumeration — a coach cannot guess
another coach's film_id by incrementing an integer. Also safe for distributed generation.
`gen_random_uuid()` uses the PostgreSQL built-in — no extension required on Neon PG 16.

**`text` for string fields, not `varchar(n)`:** PostgreSQL stores both identically.
`varchar(n)` adds a length constraint that has caused real migration pain when a film file
name exceeds the limit. Use `text` with application-layer validation via Pydantic.

**`timestamptz` for all timestamps:** Always UTC. Always timezone-aware. A coach in
Tampa and a coach in LA uploading films at the same wall-clock time must not have ambiguous
`created_at` values. `timestamptz` stores UTC, displays in local timezone if requested.
Never use `timestamp` (without timezone) for any column in this schema.

**`jsonb` for structured blobs (`sections`, `task_args`):** `jsonb` is indexed, queryable,
and efficient. `json` is stored as text and re-parsed on every access. Use `jsonb` everywhere.
The `sections` column in `film_analysis_cache` and `task_args` in `dead_letter_tasks` are
blobs that we occasionally need to query into — `jsonb` makes that possible without a schema change.

**`integer` for `tokens_input`, `tokens_output`:** Max value ~2.1B. Gemini 2.5 Pro has a
2M token context window. `integer` is sufficient. Use `bigint` only where values can realistically
exceed 2.1B — `file_size_bytes` on `films` is `bigint` because a 10GB file is 10,737,418,240 bytes.

---

## WHAT DOES NOT EXIST IN THIS SCHEMA

These are absent intentionally. Do not add them without a DECISIONS.md entry.

**No `sessions` table:** Clerk manages sessions. No server-side session store.
**No `api_keys` table:** Not building a public API in v1 of v2.
**No `audit_log` table:** Sentry + Datadog covers audit needs at launch.
**No `team_stats` table:** Phase 2 — box score ingestion. Not yet.
**No `player_evaluations` table:** Phase 3 — personnel intelligence. Not yet.
**No `knowledge_base` table:** Phase 3 — RAG. Not yet. LlamaIndex manages this externally.
**No RLS policies:** Application-layer enforcement via mandatory `user_id` scoping. See ARCHITECTURE.md.

---

*Last updated: Phase 0 — Context Engineering*
*Schema version: v2.0.0*
*All migrations must be applied in order. Never modify a migration applied to production.*
