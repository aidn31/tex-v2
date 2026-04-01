# CLAUDE.md — TEX v2

Read this file completely before every session. No exceptions.
Update ROADMAP.md after every completed task. Never lose state between sessions.
This file is the memory. Treat it as ground truth.

---

## WHAT WE ARE BUILDING

**TEX** — AI-powered basketball scouting platform. Named after Tex Winter.

One sentence: a coach uploads game film and TEX generates a master PDF scouting report.
That is the product. Everything we build serves that loop. Nothing else.

**Repo:** `github.com/aidn31/tex-v2` (separate from v1 — clean slate)
**V1 repo:** `github.com/aidn31/tex` (reference only — do not modify)
**Deadline:** Ship to first EYBL coaches as fast as possible.

**Founder:** Tommy. Non-technical. D3 player, D2/EYBL coach. Deep basketball domain expert.

- Communicate all decisions and explanations in plain English
- Use technical language only inside code, file paths, and terminal commands
- Never assume Tommy knows what a technical term means. Define it briefly when introducing one.
- Tommy is the final decision maker on all product and architectural choices

---

## CONTEXT DOCUMENTS — READ ALL OF THESE FIRST

Read every document below before writing a single line of code.
These documents are the source of truth. Code serves them, not the other way around.

```
CLAUDE.md         — this file. project rules and context. read first every session.
ARCHITECTURE.md   — full system design. every architectural decision with reasoning.
AI_STRATEGY.md    — intelligence roadmap. how TEX gets smarter over time. the moat.
SCHEMA.md         — complete database schema. all tables, columns, indexes.
PRD.md            — product requirements. what gets built and in what order.
PROMPTS.md        — all 6 Gemini section prompts with versioning and changelog.
EVALS.md          — how we know each feature is working. eval questions per feature.
COSTS.md          — per-report cost model. pricing tiers. margin targets.
ROADMAP.md        — live progress tracker. current phase, active task, blockers.
DECISIONS.md      — architectural decisions log. what was decided and why.
AGENTS.md         — Celery task definitions. queue assignments. retry policies.
MCP.md            — MCP server configuration and tool usage.
```

If any document conflicts with CLAUDE.md, CLAUDE.md wins.
If any document conflicts with ARCHITECTURE.md, raise it with Tommy before proceeding.

---

## TECH STACK

Locked. Do not deviate. Do not suggest replacements. Do not add tools not on this list.
If a change is genuinely necessary, stop, explain why in plain English, and wait for Tommy.

```
Layer               Tool                    Notes
─────────────────────────────────────────────────────────────────────────
Frontend            Next.js (App Router)    No Pages Router
Styling             Tailwind CSS            Dark theme: #F97316 orange, #0a0a0a bg
Auth                Clerk                   JWT verification in FastAPI
Payments            Stripe                  Checkout sessions + webhooks
Database            Neon (PostgreSQL)       Raw SQL. No ORM. Fresh connection per call.
Film Storage        Cloudflare R2           Two buckets: films + reports
AI — Video          Gemini 2.5 Pro          Sections 1-4. No substitute.
AI — Text           Gemini 2.5 Flash        Sections 5-6. Primary.
AI — Fallback       Claude 3.5 Sonnet       Sections 5-6 only. Flash fails → Claude.
Task Queue          Celery + Redis          4 queues. See AGENTS.md.
Backend             FastAPI (Python 3.12)   Google Cloud Run
Workers             Celery (Python 3.12)    Google Cloud Run (separate services)
PDF                 WeasyPrint              Print-optimized CSS. Not Tailwind.
Search              Typesense               Future. Not v1 of v2.
Vector DB           pgvector (Neon)         Installed. Not used yet.
Orchestration       LangChain / LlamaIndex  Knowledge base. Phase 3+.
Frontend Deploy     Vercel                  Feature branches → preview URLs
Error Tracking      Sentry                  All errors surface and alert
APM                 Datadog                 Infrastructure metrics
Product Analytics   PostHog                 Frontend behavior tracking
```

---

## THE PRODUCT FLOW

This is the exact sequence TEX executes for every report.
Build nothing outside this flow.

```
1.  Coach signs up / logs in (Clerk)
2.  Coach creates a team (opponent being scouted)
3.  Coach uploads roster — jersey number + player name mapping
4.  Coach uploads game film — file goes directly to Cloudflare R2 via presigned URL
5.  FastAPI writes film record, enqueues process_film task
6.  Worker: validates film (FFprobe), compresses if >1.8GB, splits into 20-25 min chunks
7.  Worker: uploads chunks to Gemini File API, saves URIs + expiry to DB, keeps chunks in R2
8.  Coach triggers report generation (or it auto-triggers after processing)
9.  FastAPI validates payment (first report free, else Stripe checkout)
10. Orchestrator: checks URI expiry, creates context cache, fires Celery chord
11. Sections 1-4 run in parallel (Gemini 2.5 Pro, all reading from shared cache)
12. Chord callback: sections 5-6 run sequentially (Gemini 2.5 Flash)
13. Context cache deleted. Film cache entry written. PDF assembled via WeasyPrint.
14. PDF uploaded to R2. R2 chunks deleted. Gemini file URIs deleted.
15. reports.status = complete. In-app notification fires.
16. Coach downloads PDF via presigned R2 URL.
```

**The master PDF contains — in this order:**
1. Cover page — opponent name, report date, TEX branding
2. Offensive Sets
3. Defensive Schemes
4. Pick and Roll Coverage
5. Individual Player Pages (one full page per rostered player)
6. Game Plan
7. In-Game Adjustments + Practice Plan

---

## FOUR CELERY QUEUES

```
film_processing      — FFmpeg + Gemini File API upload. heavy. 60 min hard timeout.
report_generation    — orchestrator only. fires chords. lightweight. 30 min hard timeout.
section_generation   — individual Gemini section calls. 4 run parallel per report.
notifications        — single DB write. 30 second hard timeout.
```

Every queue has a soft timeout (cleanup warning) and a hard timeout (kill).
See AGENTS.md for full retry policies and timeout values.
Every task checks DB status before executing — idempotency is not optional.
Every failed task writes to dead_letter_tasks table before dying.

---

## DATA ISOLATION

No Neon RLS. Data isolation is enforced at the application layer.
Every query against a user-facing table must include `WHERE user_id = %s`.
This is structural — `user_id` is a required parameter on every DB service function.
It is never optional, never inferred, always passed explicitly from the verified JWT.

The corrections table is the one exception: database-level write restriction enforced
at Neon. Only the service role key can insert. No coach account ever touches it.

See ARCHITECTURE.md — DATA ISOLATION STRATEGY for full reasoning.

---

## AI PROVIDER RULES

Nothing in TEX imports directly from a provider file.
All AI calls go through `services/ai/router.py` — `get_ai_provider()`.

```
AI_VIDEO_PROVIDER = "gemini"    # today
GEMINI_BACKEND = "developer_api"  # today — flip to "vertex" at scale
```

Sections 1-4: Gemini 2.5 Pro only. No fallback. No substitute.
Sections 5-6: Gemini 2.5 Flash primary. Claude 3.5 Sonnet fallback (auto, no manual intervention).
Context cache created ONCE by orchestrator before chord fires. All 4 parallel sections share it.
Every Gemini call acquires a slot from the Redis token bucket before executing.

Context caching is mandatory for sections 1-4 — it is what makes the unit economics work.
Without it, video input cost alone exceeds viable pricing. See ARCHITECTURE.md for the math.

---

## CODING RULES

### Simplicity First

- Write the minimum code that correctly solves the problem
- If a task can be done in 50 lines, do not write 200 lines
- No unnecessary abstractions, no over-engineering, no premature optimization
- Prefer boring, obvious code over clever code
- When in doubt, do less — a smaller correct solution beats a larger uncertain one

### Assumptions

- State all assumptions explicitly before writing code
- If a requirement is ambiguous, present the interpretations and ask Tommy which is correct
- Never pick silently. Never assume.
- Never assume a file exists, an API call will succeed, or a DB row is present
- Handle all failure cases explicitly

### Error Handling

- Every external API call (Gemini, R2, Neon, Stripe, Clerk) must have explicit error handling
- Never swallow errors with empty catch blocks
- Log errors to Sentry with `film_id`, `report_id`, `user_id` in context — always
- A failure without these identifiers is undebuggable
- Errors surface clearly in the UI — coaches never see silent failures

### /tmp Rules

- Every file written to /tmp is tracked in a list
- Every task has a `finally` block that deletes all tracked /tmp files
- No exceptions — the `finally` block runs on success, failure, and crash
- Use `film_id` prefix on every temp filename to prevent collision between concurrent tasks:
  `/tmp/{film_id}_raw.mp4`, `/tmp/{film_id}_chunk_001.mp4`

### Database Rules

- Open connection → execute → close. Never hold a connection across a task boundary.
- Raw SQL only. No ORM. No SQLAlchemy.
- Every query on a user-facing table includes `WHERE user_id = %s`
- user_id always comes from `verify_clerk_jwt()` — never from the request body
- Never touch the corrections table from application code without the service role key

### File and Folder Structure

```
backend/
├── main.py
├── routers/
│   ├── films.py
│   ├── reports.py
│   ├── teams.py
│   ├── roster.py
│   ├── webhooks.py       # Stripe + Clerk webhooks
│   └── admin.py          # is_admin gate on every route
├── services/
│   ├── db.py             # get_connection() only
│   ├── r2.py
│   ├── ffmpeg.py
│   ├── pdf.py
│   ├── clerk.py
│   └── ai/
│       ├── base.py       # AIVideoProvider interface
│       ├── gemini.py     # Gemini 2.5 Pro + Flash implementation
│       ├── anthropic.py  # Claude fallback for sections 5-6
│       ├── openai.py     # stub
│       └── router.py     # get_ai_provider() — ONLY import point
├── tasks/
│   ├── celery_app.py
│   ├── film_processing.py
│   ├── report_generation.py
│   ├── section_generation.py
│   └── notifications.py
├── models/
│   └── schemas.py        # Pydantic models for all request/response bodies
├── prompts/              # .txt files mirroring PROMPTS.md
│   ├── offensive_sets.txt
│   ├── defensive_schemes.txt
│   ├── pnr_coverage.txt
│   ├── player_pages.txt
│   ├── game_plan.txt
│   └── adjustments_practice.txt
├── templates/
│   └── report.html       # WeasyPrint PDF template
└── migrations/           # numbered raw SQL files
    ├── 001_create_users.sql
    └── ...

frontend/
├── app/
│   ├── (auth)/
│   ├── dashboard/
│   ├── teams/[id]/
│   ├── reports/[id]/
│   ├── upload/
│   └── admin/
├── components/
├── lib/
│   ├── api.ts            # typed fetch wrappers for every FastAPI endpoint
│   └── clerk.ts
└── middleware.ts          # Clerk auth gate
```

### Naming Conventions

```
Python files:           snake_case.py
Python functions:       snake_case
Python classes:         PascalCase
TypeScript files:       kebab-case.ts
React components:       PascalCase.tsx
TypeScript functions:   camelCase
Database tables:        snake_case
Database columns:       snake_case
Environment variables:  SCREAMING_SNAKE_CASE
```

### TypeScript

- Strict mode always on
- No `any` types. Ever. Define it explicitly if you don't know it.
- All props, function arguments, and return types must be typed
- Use Zod for all external data validation (API responses, form inputs, webhook payloads)

### Environment Variables

- Never hardcode API keys, secrets, or URLs
- Backend secrets: Cloud Run Secret Manager
- Frontend variables: Vercel environment variables
- Local dev: `backend/.env` (gitignored)
- Every required env variable documented in `.env.example`
- App fails loudly on startup if a required env variable is missing — not silently at runtime

### Git Workflow

- All work on feature branches — never directly on `main`
- Branch naming: `feature/short-description` (e.g., `feature/film-upload`)
- Commit messages: short and precise — what changed and why in one line
- Tommy reviews all PRs before merge. Never auto-merge.
- Never push to main directly. Hard limit.

---

## DECISION PROTOCOL

### When you hit a decision point:

1. Stop
2. Describe the decision in plain English
3. Present 2-3 options with tradeoffs. No jargon.
4. State which option you recommend and why
5. Wait for Tommy to decide
6. Do not proceed until Tommy confirms

### When you are confused or uncertain:

1. Stop immediately
2. State exactly what you are confused about
3. Ask the specific question needed to resolve it
4. Do not guess and proceed
5. Do not hide confusion by building something plausible-sounding

### When something breaks:

1. Stop. Do not spiral through 10 silent fixes.
2. Write a plain English summary: what you were trying to do, what went wrong, what the error says
3. Present 2-3 options to fix it with tradeoffs
4. Wait for Tommy to choose the path forward

---

## AFTER EVERY COMPLETED TASK

Execute this sequence every time. No skipping steps.

```
1. VERIFY    — confirm the feature works as intended
2. SUMMARIZE — tell Tommy in plain English: what was built, why it was built that way
3. TEST      — tell Tommy exactly what to click or do to verify it himself
4. UPDATE    — mark task complete in ROADMAP.md, update active task and blockers
5. STOP      — wait for Tommy to tell you what to do next. Do not auto-advance.
```

---

## EVAL QUESTIONS — HOW WE KNOW EACH FEATURE WORKS

Every feature has a single answerable eval question. A task is not done until the eval passes.

```
Feature                     Eval Question
──────────────────────────────────────────────────────────────────────────
Auth                        Can a coach sign up, log in, and see only their own data?
Film upload                 Does the file land in R2 with correct metadata in Neon?
Film validation             Does an invalid file (wrong type, <1min, >3hrs) get rejected cleanly?
Film processing             Do chunks upload to Gemini with correct URIs and expiry timestamps in DB?
/tmp cleanup                Is /tmp empty after every task — success or failure?
URI expiry check            Does a report re-upload expired chunks from R2 before running prompts?
Context cache               Is the cache created by the orchestrator and deleted after sections complete?
Parallel sections           Do sections 1-4 complete faster than sequential would allow?
Section fallback            Does Claude 3.5 Sonnet fire automatically when Flash is unavailable?
Dead letter                 Does a task that exhausts retries write to dead_letter_tasks?
PDF export                  Does the PDF contain all 7 sections with correct formatting?
Payment gate                Does the free report decrement correctly? Does Stripe checkout trigger?
Failure credit              Does a failed report automatically credit the coach's account?
Training mode               Does each correction save to Neon with the full v2 schema?
Admin gate                  Can a non-admin user access any admin route? (Answer must be no.)
Notifications               Does the coach see the notification when the report is ready?
```

If you cannot answer the eval question affirmatively, the task is not done.

---

## PAYMENT RULES

- First report is free per account (`users.reports_used == 0`)
- Check `user.report_credits` before Stripe — credits skip checkout entirely
- Payment gate fires before report generation starts — not after
- Technical failure → automatic credit applied to account, no Stripe refund
- Quality disagreement → in-app feedback form, Tommy decides case-by-case
- Stripe webhook signature must be verified before processing any event
- Never trust payment status from the client — always verify via webhook

---

## SECURITY RULES — HARD LIMITS

```
Never do these without explicit permission from Tommy:
  - Delete or truncate any Neon table, row, or column
  - Push code directly to main
  - Change any tool in the tech stack
  - Modify Stripe products, prices, or webhook configuration
  - Add any package not already in the project
  - Change environment variables in Vercel or Cloud Run production
  - Run any destructive script against the production database

Never do these ever:
  - Write any query without WHERE user_id = %s on user-facing tables
  - Expose Cloudflare R2 credentials to the browser (presigned URLs only)
  - Skip Stripe webhook signature verification
  - Skip Svix signature verification on Clerk webhooks
  - Check is_admin only at login — check it on every admin request
  - Hold a DB connection across a Celery task boundary
  - Import directly from services/ai/gemini.py — always go through router.py
  - Delete R2 chunks before reports.status = complete
  - Use `any` type in TypeScript
  - Write a catch block that swallows errors silently
  - Hardcode any API key, secret, or environment-specific value
  - Build features not in PRD.md or explicitly requested by Tommy
  - Add abstractions or utilities "for future use" — build for now
  - Rewrite working code outside the scope of the current task
  - Auto-merge any branch to main
```

---

## WHAT V1 TAUGHT US

These are real bugs that happened. Do not repeat them.

**Supabase connection timeout:**
Supabase's PgBouncer closed idle connections during long Celery tasks. DB calls mid-task
failed with "connection terminated unexpectedly."
V2 fix: open connection → execute → close. Every time. No connection held across task boundaries.

**2GB file size limit:**
Large film files hit the Gemini File API size limit and browser memory limits.
V2 fix: FFmpeg compresses to H.264 720p if file > 1.8GB before chunking.

**Twelve Labs removal:**
Twelve Labs added cost, latency, and a dependency we did not control. The clip-based
corrections table was anchored to Twelve Labs segment IDs — meaningless without the service.
V2 fix: direct Gemini video ingestion via File API. Corrections anchored to report + section + claim.

---

## DO NOT — HARD RULES

These are non-negotiable. Violating any of these breaks trust and can break production.

- Never build a workaround without explaining why the real solution wasn't used
- Never suggest changing the product direction or pivoting features
- Never make architectural decisions silently — always surface and ask
- Never assume Tommy approved something that was not explicitly confirmed
- Never ignore an error or warning and proceed anyway
- Never install a library to solve a problem that can be solved with 10 lines of code
- Never touch files outside the scope of the current task
- Never delete or modify comments you do not fully understand

---

## CURRENT PROJECT STATE

> Claude Code updates this section at the end of every session.
> Tommy also updates manually when needed.

**Current Phase:** 0 — Context Engineering
**Active Task:** Writing all 12 context documents before any product code
**Completed:**
- GitHub repo created at `github.com/aidn31/tex-v2`
- ARCHITECTURE.md — complete
- AI_STRATEGY.md — complete
- CLAUDE.md — complete (this file)

**Remaining context docs:**
- STACK.md
- SCHEMA.md
- PRD.md
- PROMPTS.md
- EVALS.md
- COSTS.md
- ROADMAP.md
- DECISIONS.md
- AGENTS.md
- MCP.md

**Blockers:** None
**Last Updated:** March 31, 2026

---

## PHASE OVERVIEW

```
Phase   Label                   Goal
──────────────────────────────────────────────────────────────────────────
0       Context Engineering     All 12 context docs written. Zero product code before this.
1       Foundation              Auth, dashboard, roster, film upload to R2, Neon wired
2       Film Pipeline           FFmpeg chunking, Gemini File API, chunk management
3       Report Generation       Parallel chord, 6 sections, PDF output end-to-end
4       Training Mode           Admin toggle, claim-level corrections, pattern analyzer
5       Payments + Launch       Stripe live, Sentry on, first EYBL coaches onboarded
```

Zero product code before Phase 0 is complete. This is the rule.
The context documents are not overhead — they are what makes the build fast and correct.
