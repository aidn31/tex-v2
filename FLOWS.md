# FLOWS.md — TEX v2

Every screen a coach sees. Every state a screen can be in. Every action a coach can take.
Read PRD.md before this. Read ARCHITECTURE.md for the frontend route structure.
This document is the source of truth for all frontend UI decisions.

---

## HOW TO READ THIS DOCUMENT

Each flow section covers:
- **Route** — the URL path
- **States** — every possible state the screen can render
- **Actions** — what the coach can do on that screen
- **Empty states** — what the screen shows when there is no data yet
- **Error states** — what the coach sees when something goes wrong

The frontend is a thin client. It renders state and calls the backend. It does not compute anything.

---

## ROUTE MAP

```
/sign-in                    — Clerk login
/sign-up                    — Clerk signup
/dashboard                  — coach home. teams list + recent reports.
/teams                      — all teams (same as dashboard, teams tab)
/teams/[id]                 — single team: roster + films + reports tabs
/upload?team_id=[id]        — film upload flow
/reports/[id]               — report status + PDF download
/admin                      — admin home (is_admin only)
/admin/corrections          — training mode: claim review
/admin/patterns             — pattern analyzer output
/admin/users                — user management
/admin/dead-letters         — dead letter queue review
```

---

## FLOW 1 — AUTH

### Sign Up (`/sign-up`)

Clerk-hosted component. TEX does not build this screen.

**After sign-up:**
- Clerk fires `user.created` webhook → FastAPI inserts row into `users` table
- Coach is redirected to `/dashboard`
- If this is the coach's first time (no teams yet), the dashboard shows the onboarding prompt (see Flow 2)

### Sign In (`/sign-in`)

Clerk-hosted component. TEX does not build this screen.

**After sign-in:**
- Coach is redirected to `/dashboard`

### Auth Gate

Every route except `/sign-in` and `/sign-up` is behind Clerk's auth middleware.
An unauthenticated request to any protected route redirects to `/sign-in`.
This is handled in `middleware.ts` — not in individual page components.

---

## FLOW 2 — ONBOARDING (FIRST-TIME COACH)

**Trigger:** Coach lands on `/dashboard` with zero teams.

**Screen shows:**
- Welcome message: *"TEX analyzes game film and generates a PDF scouting report in 30–50 minutes."*
- Three-step visual guide:
  1. Create a team
  2. Add a roster
  3. Upload film
- CTA button: **"Create Your First Team"** → opens the New Team modal

**Rules:**
- This is a guide, not a gated wizard. The coach can navigate away at any step.
- Once the coach has at least one team, the onboarding prompt is never shown again.
- Do not block the coach from accessing any part of the product during onboarding.

---

## FLOW 3 — DASHBOARD (`/dashboard`)

### States

**State A — Has teams:**
- List of team cards, sorted by most recently updated
- Each card shows: team name, level, number of films, date of last report
- Each card links to `/teams/[id]`
- "New Team" button in top right

**State B — No teams (first visit):**
- Onboarding prompt (see Flow 2)

**State C — Has in-progress reports:**
- A "Processing" banner or card appears above the teams list
- Shows: team name, report status (Processing / Generating), elapsed time
- Polls `GET /reports/[id]` every 5 seconds until status = `complete` or `error`
- When complete: banner becomes a "Download Ready" card with a download button
- When error: banner becomes a "Report Failed" card with a retry option

### Actions
- Create new team → modal (see Flow 4)
- Click team card → `/teams/[id]`
- Download completed report → triggers presigned URL fetch → browser download

---

## FLOW 4 — CREATE TEAM (MODAL)

**Trigger:** "New Team" button on dashboard or teams list.

**Modal fields:**
- Team name (required, text, max 100 chars)
- Competition level (required, dropdown): D1 / D2 / D3 / EYBL / AAU / High School / Unknown

**Actions:**
- Submit → `POST /teams` → on success: modal closes, new team card appears in list
- Cancel → modal closes, no change

**Validation (inline, before submit):**
- Empty team name → "Team name is required"
- Name over 100 chars → "Team name is too long"
- No level selected → "Please select a competition level"

**Error state:**
- API error → "Something went wrong. Try again." inline in modal. Do not close the modal.

---

## FLOW 5 — TEAM PAGE (`/teams/[id]`)

Three tabs: **Roster**, **Films**, **Reports**

### Header (always visible)
- Team name + competition level
- "Edit Team" button → inline name/level edit, save on blur or Enter
- "Delete Team" button → confirmation modal: *"Delete [Team Name]? This cannot be undone."*
  - Soft delete (`deleted_at`). Team disappears from dashboard.

### Tab: Roster

**State A — Has players:**
- Table with columns: #, Name, Position, Height, Role, Actions
- Each row is editable inline on click
- Delete icon per row → confirmation: *"Remove #[jersey] [name]?"*
- "Add Player" button → inline empty row appended to table bottom

**State B — No players:**
- Empty state: *"No players yet. Add your roster so TEX can attribute plays to specific players."*
- "Add First Player" button

**Add/Edit player fields:**
- Jersey # (required, text — allows "00", "0", "33A")
- Full name (required, text, max 60 chars)
- Position (optional, dropdown): PG / SG / SF / PF / C
- Height (optional, text, e.g. "6'4"")
- Dominant hand (optional, dropdown): Right / Left / Ambidextrous
- Role (optional, dropdown): Primary Initiator / Secondary Handler / Spacer / Screener / Finisher / Role Player
- Notes (optional, text)

**Validation:**
- Duplicate jersey number on same team → "Jersey #[X] is already on this roster"
- Empty name → "Player name is required"

### Tab: Films

**State A — Has films:**
- List of film cards: file name, upload date, duration, status badge, actions
- Status badges: `Uploading` / `Processing` / `Ready` / `Error`
- "Upload Film" button top right

**State B — No films:**
- Empty state: *"No film uploaded yet."*
- "Upload Film" button → navigates to `/upload?team_id=[id]`

**Film card actions:**
- If status = `Ready`: "Generate Report" button (or "Report Generating" if one is already running)
- If status = `Error`: "Retry Processing" button
- Delete film → confirmation modal. Soft delete.

### Tab: Reports

**State A — Has reports:**
- List of report cards: date generated, status badge, section count, actions
- Status badges: `Generating` / `Complete` / `Error`
- Complete reports show: "Download PDF" button

**State B — No reports:**
- Empty state: *"No reports yet. Upload a film and generate your first scouting report."*

---

## FLOW 6 — FILM UPLOAD (`/upload?team_id=[id]`)

### Step 1 — Select File

**Screen shows:**
- Drag-and-drop zone: *"Drop your film here, or click to browse"*
- Accepted formats noted below: MP4, MOV, MKV, AVI
- Max file size noted: 10GB

**Client-side validation (before any API call):**
- Wrong file type → *"Only video files are accepted (MP4, MOV, MKV, AVI)"*
- File under 1 minute → *"Film must be at least 1 minute long"* (checked after server validation)
- File over 10GB → *"File is too large. Maximum size is 10GB"*

### Step 2 — Uploading

**Screen shows:**
- File name + size
- Progress bar — updates as each 100MB part completes
- Percentage complete (e.g. "47%")
- Estimated time remaining (calculated from upload speed)
- "Cancel Upload" button

**Part failure:**
- Retry the failed part up to 3 times silently (no UI change)
- If 3 retries fail: show error state (see below) and call `POST /films/upload-abort`

**Upload complete:**
- Call `POST /films/upload-complete`
- Transition to Step 3

### Step 3 — Processing

**Screen shows:**
- *"Film uploaded. TEX is processing your film — this takes 10–20 minutes."*
- Spinner or progress indicator
- "Go to Dashboard" link (coach does not need to stay on this page)
- Status polling: `GET /films/[id]` every 10 seconds

**When processing completes:**
- Status changes to `ready`
- Screen shows: *"Film is ready."* + "Generate Report" button

**When processing errors:**
- Screen shows error state (see below)

### Error States

| Error | Message shown |
|---|---|
| Upload part failure | *"Upload failed. Check your connection and try again."* + Retry button |
| File validation failure (server) | *"TEX couldn't process this file: [reason]. Try re-exporting the film."* |
| Film too short (<1 min) | *"Film must be at least 1 minute long."* |
| Film too long (>3 hrs) | *"Film must be under 3 hours."* |
| Processing worker failure | *"Something went wrong processing your film. Try again or contact support."* + Retry button |

---

## FLOW 7 — GENERATE REPORT

**Trigger:** Coach clicks "Generate Report" on the Films tab or film upload completion screen.

### First Report (Free)

- No payment prompt
- `POST /reports` called immediately
- Coach sees report status screen (Flow 8)

### Subsequent Reports (Paid)

- Payment modal appears: *"This report costs 1 credit ($X)."*
- If coach has credits: "Use 1 Credit" button → `POST /reports` → report status screen
- If coach has no credits: "Buy Credits" button → Stripe Checkout session → on return, report auto-triggers

**Stripe redirect flow:**
1. `POST /payments/checkout` → returns Stripe Checkout URL
2. Browser navigates to Stripe
3. On success: Stripe redirects to `/reports/[id]?payment=success`
4. On cancel: Stripe redirects to `/teams/[id]` — no report created

---

## FLOW 8 — REPORT STATUS (`/reports/[id]`)

### States

**State A — Generating:**
- Status: *"Generating your scouting report…"*
- Section progress tracker (updates as each section completes):
  ```
  ✓ Offensive Sets          [complete]
  ✓ Defensive Schemes       [complete]
  ⟳ Pick and Roll Coverage  [running]
  ○ Player Pages            [queued]
  ○ Game Plan               [queued]
  ○ In-Game Adjustments     [queued]
  ```
- Estimated time remaining: *"~12 minutes remaining"*
- Polls `GET /reports/[id]` every 5 seconds
- Coach does not need to stay on this page. In-app notification fires on completion.

**State B — Complete:**
- *"Your scouting report is ready."*
- "Download PDF" button — calls `GET /reports/[id]/download` → presigned R2 URL → browser download
- Report metadata: team name, date generated, film used
- Section summary (optional preview of section titles)

**State C — Error:**
- *"Report generation failed."*
- Error reason if available (e.g. *"Gemini file URI expired — film will be re-processed automatically"*)
- "Try Again" button → re-triggers report generation
- "Contact Support" link

### Polling Rules
- Poll every 5 seconds while status = `processing` or `generating`
- Stop polling when status = `complete` or `error`
- If coach navigates away, polling stops. Notification fires when report is done.
- Do not use WebSockets. Polling is sufficient given 15–50 minute report times.

---

## FLOW 9 — IN-APP NOTIFICATIONS

**Trigger events that produce notifications:**
- Film processing complete → *"[Team Name] film is ready. Generate your report."*
- Report complete → *"[Team Name] scouting report is ready. Download your PDF."*
- Report failed → *"[Team Name] report failed. Tap to retry."*

**Display:**
- Notification badge on dashboard nav icon
- Notification dropdown listing unread items
- Clicking a notification navigates to the relevant screen and marks it read

**Implementation note:** Notifications are written to the `notifications` table by the `notify_coach` Celery task. Frontend fetches `GET /notifications?unread=true` on dashboard load and after each polling cycle.

---

## FLOW 10 — ADMIN (`/admin`) — IS_ADMIN ONLY

**Access gate:** Every admin route checks `is_admin` via live DB query on every request. A non-admin user who navigates to `/admin` sees a 403 page: *"Access denied."*

### Admin Home (`/admin`)
- Links to: Corrections, Pattern Analyzer, Users, Dead Letters
- Summary stats: total reports today, active jobs, dead letter count

### Training Mode — Corrections (`/admin/corrections`)

**Screen shows:**
- List of recent report sections flagged for review
- Each item: team name, section type, claim text, current status (unreviewed / correct / incorrect)
- Filter by: section type, prompt version, date range

**Correction flow:**
- Click a claim → expands to show full claim text
- Two buttons: ✓ Correct / ✗ Incorrect
- If Incorrect: text field appears → coach writes the correction → Submit
- Submitting writes to `corrections` table with `is_correct`, `correction_text`, `prompt_version`

### Pattern Analyzer (`/admin/patterns`)

**Screen shows:**
- Filter controls: prompt version, date range (default: last 7 days)
- Table: Category / Error Count / Total / Error Rate %
- Recommendation text (generated by Gemini Flash, may be absent if call failed)
- "Refresh" button

### User Management (`/admin/users`)

- Table: email, report count, last active, credits remaining
- "Add Credits" button per row → number input → `POST /admin/users/[id]/credits`

### Dead Letters (`/admin/dead-letters`)

- Table: task name, film_id, report_id, error message, retry count, created_at
- "Replay" button per row → `POST /admin/dead-letters/[id]/replay`
- "Dismiss" button per row (marks resolved without replaying)

---

## GLOBAL UI RULES

**Colors (from CLAUDE.md tech stack):**
- Background: `#0a0a0a`
- Accent: `#F97316` (orange)
- Dark theme throughout. No light mode.

**Loading states:**
- Every API call that takes >300ms shows a loading indicator on the triggering element (spinner on button, skeleton on list)
- Never show a blank screen while data loads

**Error handling:**
- Every API error surfaces a message to the coach. No silent failures.
- Errors appear inline near the action that caused them, not in a global toast that disappears
- If a full-page error occurs (e.g. team not found), show a simple error page with a "Go to Dashboard" link

**Responsive:**
- Responsive web. No mobile app.
- Target: functional on tablet (coaches use iPads on the sideline)
- Minimum supported width: 768px

**Polling:**
- Only two screens actively poll: Dashboard (for in-progress reports) and `/reports/[id]`
- All other screens are static — they load data once and do not refresh automatically

---

*Last updated: Phase 0 — Context Engineering*
*Add FLOWS.md to the context documents list in CLAUDE.md before next session.*
