# golden_set/

This folder is the source of truth for TEX evaluation. Every film in here is part of the
**5-film golden set** — a fixed benchmark TEX is graded against on every prompt change,
model change, or pipeline change. Nothing in this folder ever changes silently. If the
content here is wrong, every eval score downstream is wrong.

See `TRAINING.md` §3 (Building the Golden Set) and `ROADMAP.md` Commercial Readiness Ladder
Stage 1 for why this exists and what "Stage 1 passing" looks like.

---

## What lives in each film folder

Each film gets its own subfolder named `film_NN_<scouted_team>_vs_<opponent>/`. Inside:

| File | Purpose | When you fill it |
|---|---|---|
| `metadata.md` | DB film_id, scouted team, opponent, game context, chunk boundaries | Once, before watching |
| `film_watch_notes.md` | Live chronological scratchpad while watching film | While watching (1-pass, timestamped) |
| `ground_truth.md` | Polished answer key. Mirrors Prompt 0B synthesis output. | After watching, synthesized from scratch notes |

**The scratchpad is the raw observation; the ground truth is the consolidated answer.**
Grading compares TEX's output against `ground_truth.md`. The scratchpad is not graded against
— it's just how you build the answer without losing observations between minutes 3 and 90.

---

## Workflow for a single film (target: 6–8 hours of Tommy time per film)

1. **Fill `metadata.md`** (5 min). Film UUID, date, opponent, scouted team, chunk boundaries.
2. **First pass — watch and log** (~2.5× the film length, so ~4 hours for a 90-min film).
   Open `film_watch_notes.md` beside the video. Pause freely. Rewind as needed.
3. **Second pass — synthesize** (~1–2 hours). Open `ground_truth.md`. Copy counts and
   observations from `film_watch_notes.md` into the structured headers. Aggregate totals.
   Mark confidence tags ([CONFIRMED] / [LIKELY] / [SINGLE GAME SIGNAL]).
4. **Commit** to git. These files are versioned. If you update ground truth later
   (corrected observation, better vocabulary), the git diff is the audit trail.

---

## Film naming convention

`film_NN_<scouted_team>_vs_<opponent>` — e.g. `film_01_bbe_vs_team_durant`.
Lowercase. Underscores. `NN` is the golden-set index (01-05 for the fixed set).
Pick memorable short-codes: `bbe` (Brad Beal Elite), `td` (Team Durant), etc.

---

## What makes a ground truth document "done"

Per TRAINING.md:
- Every section of the Prompt 0B output structure is filled in (or explicitly marked "none observed").
- Every action count has a number, not a range — unless uncertainty is noted.
- Every player with 10+ possessions has a consolidated profile.
- Every action is attributed to jersey numbers + names from the roster.
- Every judgment call you made (vocabulary reconciliation, contradiction resolution)
  is documented in the "Synthesis flags" section.

If any of these are blank, the document is not ready to grade TEX against yet.

---

## Do NOT put inside this folder

- Raw video files (too big; films live in Cloudflare R2 and are referenced by UUID)
- Eval scores (those go in `EVAL_SCORES.md` at the repo root, auto-written by the grading UI)
- Player-specific data that belongs in the DB (rosters live in `roster_players`, not here)

---

*Last updated: Phase 3 — Report Generation.*
*This folder is the evaluation ground truth. Treat it like a production database.*
