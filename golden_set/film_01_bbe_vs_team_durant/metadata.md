# Film 01 — Brad Beal Elite vs Team Durant (Peach Jam Quarterfinals 2025)

This is the first film in the golden set. It is the benchmark TEX is graded against for
every prompt change, model change, or pipeline change going forward. Treat this document
as static reference data — update it only if the facts themselves are wrong.

---

## Film in Neon (dev)

| Field | Value |
|---|---|
| film_id (UUID) | `8fbd2dd2-0b98-4a2d-ae03-788312bea32d` |
| file_name | `JJ Andrews,Brad Beal Elite vs Babatunde Oladotun,Team Durant｜Nike EYBL Peach Jam Quarterfinals 2025 [RXyah7MRRa8].mp4` |
| team_id (scouted) | `9585d9cd-e330-425b-97ea-b6628adfcac3` (Brad Beal Elite) |
| user_id | `933c00c7-df54-43a4-ae2d-f36502347cce` (Tommy / admin) |
| duration_seconds | 5480 (~91 min 20 sec) |
| chunk_count | 4 |
| status | `processed` |

---

## Game context

| Field | Value |
|---|---|
| Event | Nike EYBL Peach Jam — Quarterfinals |
| Year | 2025 |
| Scouted team | **Brad Beal Elite** (17U EYBL) |
| Opponent | **Team Durant** (featuring Babatunde Oladotun) |
| Level | EYBL (17U) |
| YouTube source | [RXyah7MRRa8] (archival; film of record is in R2) |
| Game clock format | EYBL 17U: **four 8-minute quarters** (32 min of regulation play) |

**Who is being scouted:** Brad Beal Elite. TEX is learning to scout BBE *as if BBE were an
opponent*. The roster in `roster_players` with `team_id = 9585d9cd-...` is the subject of
ground truth — every action, every player profile, every tendency in `ground_truth.md`
refers to a BBE player. Team Durant players are opponents and are only referenced
indirectly ("#3 drove past Team Durant's #4 to the rim"). Team Durant's own roster is
not captured in this ground truth.

---

## Chunk boundaries (from DB — 4 chunks × ~22m 50s each)

Each chunk is analyzed independently by Prompt 0A (extraction). These are the windows
your scratchpad is organized around.

| Chunk | Tape start | Tape end | Approximate game state |
|---|---|---|---|
| 0 | 0:00 | ~22:50 | Pre-game warmups + Q1 (likely full) + start of Q2 |
| 1 | ~22:50 | ~45:40 | Rest of Q2 + halftime break + start of Q3 |
| 2 | ~45:40 | ~1:08:30 | Rest of Q3 + Q4 (likely most of it) |
| 3 | ~1:08:30 | 1:31:20 | End of Q4 + any OT / post-game wrap |

*The chunk-to-quarter mapping above is a rough estimate. 32 minutes of regulation play
plus ~10 minutes of halftime, ~3 minutes of inter-quarter breaks, warmups, timeouts, and
fouled-out free throws easily inflates a 32-minute game to a 91-minute film. The exact
boundaries get filled in during the first-pass watch — see the `Actual game clock window`
line at the top of each chunk section in `film_watch_notes.md`.*

Record **in-game clock time** in `film_watch_notes.md`, not tape time. A possession at
tape 48:15 is useless — "3:24 left in Q3" is actionable scouting. Each quarter's clock
counts DOWN from 8:00 to 0:00.

---

## Known players on this roster (as of seed)

Source: `scripts/seed_bbe_roster.py`. Handedness and role default to `right` / `role_player`
and are updated as observations emerge from the film.

| # | Name | Pos (seeded) | Ht | Grad | Handedness | Role |
|---|---|---|---|---|---|---|
| 1 | Quentin Coleman | PG | 6'3" | 2026 | right (default) | role_player (default) |
| 2 | Trey Pearson | PG | 6'3" | 2026 | right (default) | role_player (default) |
| 5 | Cam Blivens | PG | 6'2" | 2026 | right (default) | role_player (default) |
| 10 | Ty Edwards | PG | 6'5" | 2026 | right (default) | role_player (default) |
| 22 | Jamison White | PF | 6'9" | 2026 | right (default) | role_player (default) |
| 23 | JJ Andrews | SF | 6'7" | 2026 | right (default) | role_player (default) |
| 31 | Sheek Pearson | PF | 6'11" | 2026 | right (default) | role_player (default) |
| 32 | Jaylan Mitchell | PF | 6'8" | 2027 | right (default) | role_player (default) |
| 33 | Jahadi White | PF | 6'8" | 2026 | right (default) | role_player (default) |

---

## Open questions to answer during the first watch

These are the roster items the printed sheet did not include. Resolve as you watch.

- Which of the four Gs (#1, #2, #5, #10) are pure initiators (PG) vs. off-ball shooters (SG)?
- Is #31 Sheek Pearson (6'11") actually a C, not a PF? Where does he operate on floor?
- Which players are left-handed? (Priors: statistically ~10–15% of roster.)
- Who is the primary initiator / secondary handler / spacer / screener / finisher on this team?
- Are any players on this film not on this roster sheet (call-ups, subs added after roster pub)?
  If yes, they get a new `roster_players` entry after the film is watched.

---

## What to do when you have corrections to this metadata

The DB columns are the source of truth for `film_id`, `team_id`, and `user_id`. If this
document falls out of sync with Neon, the DB wins. Update this file and commit the diff.

The seeded roster is editable post-hoc through the `/admin` UI or by modifying
`scripts/seed_bbe_roster.py` and re-running. Either is fine for dev; neither is allowed
in production without a migration.

---

*Last updated: Golden set initialization — film_01.*
