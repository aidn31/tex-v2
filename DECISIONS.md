# DECISIONS.md — TEX v2

Architectural decisions log. Every significant decision made for TEX v2, why it was made,
what alternatives were considered and rejected, and what would cause the decision to be revisited.
Read this before proposing any architectural change. If a decision is documented here, it was
deliberate. Challenge it with evidence, not preference.

New decisions go at the bottom. Never modify a decision already logged — add a SUPERSEDED entry
that references the original and documents what changed and why.

---

## D-001 — Python 3.12 for backend and workers

**Decision:** All backend services (FastAPI API + all Celery workers) run Python 3.12.
Same version everywhere. No mixing.

**Rationale:** Python 3.12 has meaningfully improved error messages over 3.11 — stack traces
are more readable and debugging production failures is faster. Minor performance improvements
in the interpreter are real but not the primary reason. The primary reason is uniformity:
one Python version means one set of dependency constraints, one Dockerfile base image, and no
subtle compatibility bugs between services that share code (the workers import from the same
`services/` directory as the API).

**Alternatives considered:**
- Python 3.11: stable and widely used. Rejected because 3.12 improvements are real and the
  migration cost from 3.11 to 3.12 later is not zero.
- Python 3.13: not yet stable enough at time of decision. Revisit when 3.13 reaches broad
  library support.

**Reversal condition:** A critical dependency that TEX requires does not support 3.12.
In that case, evaluate whether the dependency can be replaced before downgrading Python.

---

## D-002 — FastAPI over Flask / Django

**Decision:** FastAPI is the web framework for the backend API.

**Rationale:** FastAPI provides async request handling, automatic OpenAPI schema generation
from Pydantic models, and native dependency injection — all of which matter for this codebase.
Async handling means the API does not block while waiting on DB calls or enqueuing tasks.
Pydantic integration means request validation is not a separate layer — it is the function
signature. Django's ORM, admin UI, and template system are all things TEX does not use;
Django's overhead is pure cost with no benefit here. Flask is synchronous by default and lacks
Pydantic integration natively.

**Alternatives considered:**
- Django: ruled out. ORM conflicts with the raw SQL requirement. Admin UI is unused.
- Flask: ruled out. Synchronous, no Pydantic integration, more boilerplate for validation.

**Reversal condition:** None anticipated. FastAPI is the correct tool for this workload.

---

## D-003 — Neon PostgreSQL over Supabase

**Decision:** Neon PostgreSQL is the database. Supabase is not used in v2.

**Rationale:** v1 ran on Supabase. Supabase's PgBouncer connection pooler in transaction mode
closed idle connections after ~10 minutes. Celery tasks that held a connection across long
processing windows hit this and failed mid-task with "connection terminated unexpectedly."
The v2 architecture eliminates this structurally — every DB call opens, executes, and closes.
No connection is held across a task boundary. Neon's PostgreSQL wire protocol behavior under
this pattern is predictable and correct. Additionally, v2 does not use Supabase Auth (Clerk
handles auth), Supabase Storage (R2 handles storage), or Supabase Realtime — three of the four
reasons to choose Supabase over raw Postgres. The fourth, the managed Postgres itself, Neon
does equally well with better branching support for schema migrations.

**Alternatives considered:**
- Supabase with structural fix: the connection bug would be fixed by the open/execute/close
  pattern regardless of which managed Postgres is used. Supabase was rejected anyway because
  the RLS policies from v1 reference `auth.uid()` — a Supabase-specific function that does
  not exist in raw Postgres. Porting those policies to Neon requires rewriting them, at which
  point the question is whether RLS is worth maintaining at all (see D-006).
- PlanetScale: MySQL, not Postgres. pgvector requires Postgres. Rejected.
- Self-hosted Postgres on Cloud Run: more operational complexity than Neon with no benefit at
  current scale.

**Reversal condition:** Neon's connection limits become a bottleneck at high concurrent report
volume. At that point, evaluate PgBouncer in front of Neon or migrate to Cloud SQL.

---

## D-004 — Raw SQL, No ORM

**Decision:** All database access uses raw SQL with psycopg2. No ORM. No SQLAlchemy.
No query builder. No Alembic.

**Rationale:** The schema is 15 tables, known in advance, and stable. ORMs pay off when
the schema is large, frequently changing, or when developers unfamiliar with SQL need to
interact with the database. None of these conditions apply to TEX v2. Raw SQL is explicit —
every query is visible, pasteable into Neon's console, and debuggable in isolation. ORM-generated
queries are invisible until something goes wrong, at which point you are debugging the ORM's
behavior as much as the query. Parameterized raw SQL also makes the mandatory `WHERE user_id = %s`
pattern structurally enforced — you cannot forget to add it because it is a function parameter.

**Alternatives considered:**
- SQLAlchemy Core (not ORM): still adds a query builder abstraction over SQL. Rejected for
  the same reason — the abstraction adds complexity without benefit at this schema size.
- SQLAlchemy ORM: rejected. Conflicts with the fresh-connection-per-call pattern and adds
  the most complexity for the least benefit.
- Tortoise ORM: async-native but the same objection applies.

**Reversal condition:** Schema grows beyond 30 tables with complex join patterns that become
difficult to maintain in raw SQL. At that point, evaluate SQLAlchemy Core (not ORM) for
query building while keeping raw connection management.

---

## D-005 — Cloudflare R2 over AWS S3

**Decision:** Cloudflare R2 is the object storage layer for both buckets (films and reports).

**Rationale:** R2 has no egress fees — data transferred out of R2 to the internet is free.
S3 charges $0.09/GB egress. A 2-hour film compressed to 1.5GB downloaded by a worker from S3
costs $0.135 per download. Workers download films multiple times (original download for
processing, potential re-downloads for re-upload). At volume this is material. R2 eliminates
this cost entirely. R2 uses the S3-compatible API, so the boto3 client works with a single
endpoint URL change. Migration cost to S3 is one environment variable change.

**Alternatives considered:**
- AWS S3: identical feature set, higher egress cost. Rejected solely on cost.
- Google Cloud Storage: would eliminate cross-cloud latency for workers on Cloud Run.
  Rejected because R2's zero-egress advantage outweighs the latency benefit at current
  film sizes, and GCS egress to Cloud Run within the same region is not free.
- Backblaze B2: also zero-egress to Cloudflare network. Fewer features, less mature SDK.
  Rejected in favor of R2's maturity.

**Reversal condition:** Gemini migrates to Vertex AI (see D-011). At that point, workers
upload chunks to GCS instead of Gemini File API. If all workers and storage move to GCP,
GCS becomes the natural choice and R2's egress advantage diminishes relative to GCS-to-CloudRun
zero-cost transfers within GCP. Reassess when Vertex AI migration occurs.

---

## D-006 — No Database-Level RLS

**Decision:** Neon has no Row Level Security policies. Data isolation is enforced entirely
at the application layer via mandatory `WHERE user_id = %s` on every user-facing query.

**Rationale:** TEX v2 has exactly one path to the database: FastAPI. Coaches do not connect
to Neon directly. There is no client SDK, no exposed GraphQL layer, no direct database access
from the browser. FastAPI verifies the Clerk JWT, extracts `user_id`, and enforces scoping
before any query runs. Database-level RLS on this architecture is a second lock on a door
that already has a guard. At scale with fresh connections per call and high poll frequency,
the mandatory `SET LOCAL` session variable that RLS requires adds measurable overhead with
zero security benefit given the architecture.

The one exception: the `corrections` table has a database-level write restriction. Only the
service role key can insert. This is enforced at the Neon level because the corrections table
is the proprietary training dataset and no coach account should ever touch it under any
circumstance — not through a bug, not through a misconfiguration, not through a missing
`WHERE` clause. The asymmetry (no RLS on user tables, hard DB restriction on corrections)
is intentional.

**Alternatives considered:**
- Full RLS on all tables: rejected because `auth.uid()` is a Supabase function that does not
  exist in raw Postgres. Porting the v1 RLS policies requires rewriting them, at which point
  the question is whether they provide any security benefit the application layer doesn't
  already provide. Answer: no, given the single-path architecture.
- Partial RLS (only on most sensitive tables): rejected for consistency. One enforcement
  mechanism is easier to audit than two.

**Reversal condition:** A second database access path is added — a public API, a webhook
that writes directly without going through FastAPI, or a third-party integration with
direct DB access. At that point, RLS becomes necessary.

---

## D-007 — Celery + Redis over alternatives

**Decision:** Celery 5 with Redis as broker and result backend for all async task processing.

**Rationale:** Celery's chord primitive is the correct implementation for the parallel section
generation pattern — fire 4 tasks simultaneously, execute a callback when all 4 complete.
This is not easily replicated with simpler queue systems. Celery also provides per-queue
concurrency controls, soft and hard timeouts, retry with exponential backoff, and task state
tracking — all of which TEX v2 uses. Redis as broker is the standard Celery broker for
production workloads and integrates with the token bucket rate limiter already in the design.

**Alternatives considered:**
- Cloud Tasks (GCP): managed, serverless, no Redis dependency. Rejected because Cloud Tasks
  does not have a native chord/group primitive. Implementing parallel section generation with
  a callback requires either polling or a custom fan-out mechanism — more complexity than
  Celery's built-in primitive.
- RQ (Redis Queue): simpler than Celery, Redis-native. Rejected because RQ has no equivalent
  to Celery's chord for parallel fan-out with callback.
- Dramatiq: similar to Celery, cleaner API. Rejected because Celery has a larger ecosystem,
  better documentation, and the chord primitive is more mature.

**Reversal condition:** Cloud Run's maximum request timeout (3600 seconds) and Celery's
operational complexity become a bottleneck at high scale. At that point, evaluate Cloud Tasks
with a custom chord implementation or a managed workflow service (Cloud Workflows).

---

## D-008 — 4 Separate Celery Queues

**Decision:** Four queues: `film_processing`, `report_generation`, `section_generation`,
`notifications`. Each runs on a separate Cloud Run service with independent scaling.

**Rationale:** Backpressure isolation. A 2-hour film being processed takes up to 60 minutes.
If film processing and notifications share a queue, a backlog of film jobs blocks coaches from
receiving notifications about completed reports. Separate queues mean separate worker pools.
Backpressure in one queue does not propagate to others. Independent scaling means section
workers (which need to scale to 10 during report generation peaks) do not consume resources
allocated to film processing workers (which run at concurrency=1 and need 8GB /tmp).

**Reversal condition:** Queue count increases complexity without meaningful isolation benefit.
If TEX's traffic pattern is consistently one queue at 0% and another at 100%, consolidation
may be correct. Monitor queue depths in Datadog before consolidating.

---

## D-009 — Dead Letter Queue in Neon, Not Redis

**Decision:** Failed tasks that exhaust all retries write to the `dead_letter_tasks` table
in Neon. No Redis dead letter queue.

**Rationale:** Redis is configured with AOF persistence but is still fundamentally a cache.
A Redis dead letter queue loses data if Redis is replaced, the AOF is corrupted, or the
instance is provisioned fresh. Neon is durable by design — it is the source of truth for all
application state. A failed task that disappears from a Redis dead letter queue on Redis
restart is a coach job that vanishes without a trace. A failed task in Neon is queryable,
replayable by UUID, and visible in the admin UI without any Redis access. The `task_args`
JSONB column stores the full original arguments, enabling replay with one function call.

**Alternatives considered:**
- Redis dead letter with AOF: rejected because AOF protects against clean restarts, not
  against Redis instance replacement or corruption.
- SQS dead letter queue: adds an AWS dependency to what is otherwise a GCP + Cloudflare stack.
  Rejected.

**Reversal condition:** None. The DB is always the correct location for durable failure state.

---

## D-010 — Film Fingerprint Cache (SHA-256)

**Decision:** Every film is hashed on download (SHA-256 of raw bytes). Before running any
Gemini analysis, the worker checks `film_analysis_cache` for a matching hash + prompt version.
A cache hit skips all LLM calls for sections 1-4.

**Rationale:** Multiple coaches regularly scout the same opponents — especially at EYBL events.
The first coach to upload a given film pays full Gemini cost. Every subsequent coach who uploads
the same film gets an instant result at zero Gemini cost. The cache hit rate compounds with
coach volume — at 500 coaches, popular EYBL programs are effectively analyzed once. The moat
argument: competitors who launch later and pay full API price on every report cannot match TEX's
unit economics at scale without building an equivalent cache, which requires an equivalent
coaching network to populate it.

Cache invalidation is by prompt version — a cache entry is stale when the prompt that generated
it has been superseded. This ensures coaches always receive analysis from the current prompt
quality, not a cached result from an older (potentially worse) prompt.

**Alternatives considered:**
- No caching — pay Gemini on every report: viable at launch with 10 coaches, unviable at 500.
  The decision to build the cache at Phase 0 means the compounding benefit starts from day one.
- Cache by film metadata (filename + size) instead of hash: rejected. Two films with the same
  filename and size can have different content. Hash is the only reliable identity.
- Perceptual hashing (for visually similar but not identical files): rejected. Too complex,
  too many false positives, and the signal is unreliable for game film where slight encoding
  differences are common. SHA-256 of raw bytes is exact and fast.

**Reversal condition:** SHA-256 computation on large files (4-8GB pre-compression) adds
meaningful latency to film processing. At that point, evaluate streaming hash computation
during the R2 download rather than hashing the complete file in memory.

---

## D-011 — Gemini Developer API Now, Vertex AI Later

**Decision:** TEX v2 launches on the Gemini Developer API. Migration to Vertex AI happens
when monthly Gemini spend justifies committed use discounts or when operational reasons favor it.

**Rationale:** The Developer API is simpler to set up and iterate on during Phase 0-3. No GCP
project configuration, no service account IAM setup for Vertex, no GCS bucket for file uploads.
The AI provider abstraction layer (router.py) and the GEMINI_BACKEND env var mean this migration
is one configuration change — no code changes to any file outside gemini.py. The operational
complexity of Vertex AI is real; pay it when the pricing benefit justifies it.

Vertex AI triggers:
1. Monthly Gemini spend exceeds the threshold where committed use discounts on Vertex AI
   produce material savings (estimate: >$2,000/month Gemini spend).
2. Gemini File API 48-hour expiry creates operational load that GCS's permanent storage would
   eliminate (the expiry check and re-upload logic becomes a no-op with GCS).

**Alternatives considered:**
- Launch on Vertex AI from day one: rejected. Operational setup complexity and IAM configuration
  slow down Phase 1-3 without any benefit at low volume. The abstraction layer means this
  decision does not need to be made at launch.

**Reversal condition:** Not applicable — this is a migration path, not a binary choice.

---

## D-012 — Prompt 0 Two-Stage Architecture (Extract Then Synthesize)

**Decision:** Film chunk analysis runs in two stages: a parallel per-chunk extraction pass
(Prompt 0A) followed by a single synthesis pass (Prompt 0B). Not a single combined prompt.

**Rationale:** Perception and reasoning are different cognitive tasks. Asking one prompt to
simultaneously watch video, count occurrences, identify players, reconcile vocabulary across
chunks, identify scheme changes, and produce a structured synthesis produces lower accuracy
on all of those tasks than separating them. The extraction pass asks Gemini to watch and log —
a perception task with a structured output format. The synthesis pass asks Gemini to reconcile
and reason across text inputs — a reasoning task with no video. Separation also enables
parallelism: 5 chunk extractions run simultaneously, then one synthesis call processes all 5
outputs. This reduces wall-clock time for Prompt 0 and makes the output of each stage testable
independently.

**Alternatives considered:**
- Single synthesis prompt watching all chunks simultaneously: rejected because it asks the
  model to do too much in one pass. Also, a single call watching a 2-hour film at full
  resolution cannot be structured to produce the granular chunk-by-chunk confidence tagging
  that the two-stage approach produces.
- Extraction only (no synthesis): rejected because 5 separate extraction logs fed directly
  to sections 1-4 would require each section prompt to perform its own reconciliation —
  duplicating the reconciliation work 4 times and producing 4 potentially inconsistent answers
  to the same reconciliation question.

**Reversal condition:** Gemini releases a model with significantly better multi-document
reasoning that makes the two-stage overhead not worth the accuracy improvement. Evaluate by
running the single-stage vs two-stage eval head-to-head on 10 reports.

---

## D-013 — WeasyPrint Over Headless Chrome for PDF Generation

**Decision:** WeasyPrint is the PDF generation library. No headless Chrome, no Playwright,
no Puppeteer.

**Rationale:** Headless Chrome requires installing a full Chromium binary in the Docker
container (~300MB), managing a browser process, and handling browser crashes and timeouts as
a worker failure mode. WeasyPrint is a pure Python library with no browser dependency, a
smaller container footprint, and simpler failure modes — it either renders the HTML or raises
an exception. WeasyPrint implements CSS print rules directly, which means `@page`, `page-break`,
and print-specific layout are handled correctly without browser rendering quirks. The PDF is
a printed document used on a clipboard — it does not need JavaScript execution or dynamic
rendering.

**Alternatives considered:**
- Playwright (headless Chrome): more CSS compatibility. Rejected because the operational
  overhead (browser process, crash handling, larger container) is not justified by the CSS
  compatibility benefit for a static print template.
- wkhtmltopdf: older, fewer dependencies than Chrome. Rejected because development has stalled,
  the print CSS support has known gaps, and WeasyPrint is the more actively maintained alternative.
- ReportLab: generates PDFs programmatically (no HTML). Rejected because the report template
  is HTML with CSS — converting it to ReportLab's canvas API would require a full rewrite
  of the template layer.

**Reversal condition:** The WeasyPrint template requires CSS features that WeasyPrint does not
support (e.g., CSS Grid in complex layouts, or specific print-only features). At that point,
evaluate Playwright with a constrained subset of CSS.

---

## D-014 — Clerk Over Auth.js / Custom Auth

**Decision:** Clerk handles all authentication. FastAPI verifies Clerk JWTs. No custom auth.

**Rationale:** Auth is not a competitive differentiator for TEX. Clerk handles signup, login,
session management, MFA, email verification, and user webhooks correctly. Building equivalent
functionality with Auth.js or custom JWT issuance is weeks of work that produces no user-facing
benefit. Clerk's webhook system (user.created, user.deleted) maps directly to the DB writes
TEX needs. The JWT verification in FastAPI is standard RS256 public key verification — no
Clerk SDK required in the backend.

**Reversal condition:** Clerk's pricing becomes prohibitive at scale (>10K MAU), or a feature
TEX needs (e.g., organization-level auth for team accounts) is not supported by Clerk.

---

## D-015 — Context Cache TTL of 1 Hour

**Decision:** The Gemini context cache created before the chord fires has a TTL of 1 hour.

**Rationale:** Sections 1-4 combined take 8-15 minutes in the parallel chord. 1 hour provides
4x headroom for retries, slow Gemini responses, and queue delays without letting the cache
accumulate unnecessary storage cost. Cache storage costs $4.50/M tokens/hour. For a 1.89M
token cache, every additional hour costs $2.13. A 1-hour TTL that covers a 15-minute window
means the cache is deleted by Google 45 minutes after it is no longer needed in the worst case.
The orchestrator also explicitly deletes the cache after sections complete — the TTL is a
safety net, not the primary cleanup mechanism.

**Alternatives considered:**
- 30-minute TTL: too tight. A section that fails and retries three times with 480-second
  backoff (8 minutes per retry) could consume 24 minutes of the TTL before sections 1-4
  complete. If retry timing pushes past 30 minutes, the cache expires mid-generation.
- 2-hour TTL: unnecessary. 1 hour already provides 4x headroom. Doubling it doubles the
  worst-case storage cost overage with no benefit.

**Reversal condition:** Section 1-4 generation times consistently exceed 45 minutes due to
Gemini latency increases or significantly longer films. Extend TTL at that point.

---

## D-016 — First Report Free Per Account, Not Per Team

**Decision:** The first-report-free gate checks `users.reports_used == 0`. One free report
per account. Not one free report per team.

**Rationale:** Per-team free reports are trivially gamed — a coach creates 10 teams and
gets 10 free reports. Per-account is clean, single-query enforceable, and cannot be gamed
without creating multiple Clerk accounts (which Clerk tracks by email and device fingerprint).
The free report is a product demo, not a permanent discount structure. One free report is
sufficient to demonstrate value. The marginal cost of the free report ($13.83 at cache miss)
is justified by the LTV of a converting coach.

**Reversal condition:** Conversion rate data shows that one free report is insufficient to
demonstrate value and coaches need two before converting. At that point, evaluate raising the
gate to `reports_used < 2`.

---

## D-017 — Technical Failure Credit, Not Stripe Refund

**Decision:** When a report fails due to a technical error after payment, the coach receives
an automatic credit (`users.report_credits + 1`), not a Stripe refund.

**Rationale:** A Stripe refund takes 5-10 business days. A credit is instant. The coach
needs to get their report — the path of least friction is a credit that lets them regenerate
immediately. A refund requires the coach to go back through checkout, which creates friction
and a negative moment in the product experience. Credits also keep the revenue in the system —
the coach will use the credit on their next report. The only coaches who prefer a refund over
a credit are coaches who have decided to stop using TEX — in which case the relationship is
already lost and the refund is the correct resolution handled case-by-case by Tommy.

**Reversal condition:** Credit usage rate falls below 50% — coaches are receiving credits
but not using them, meaning credits are not valued. At that point, add an option to request
a Stripe refund instead of using the credit.

---

## DECISION PROTOCOL FOR FUTURE DECISIONS

When a new architectural decision is needed:

1. Stop. Do not implement until the decision is documented here.
2. State the decision being made in one sentence.
3. Write the rationale — why this option over others.
4. List alternatives considered and why they were rejected.
5. State the reversal condition — what evidence would cause this decision to be revisited.
6. Get Tommy's explicit approval.
7. Add the entry to this file with the next D-NNN number.
8. Then implement.

A decision made without a DECISIONS.md entry is an undocumented decision.
Undocumented decisions get reversed accidentally when context is lost between sessions.

---

*Last updated: April 1, 2026 — Phase 0, context engineering*
*17 decisions logged. All decisions current as of this date.*
