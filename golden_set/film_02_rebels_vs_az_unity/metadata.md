# Film 02 — Florida Rebels vs Arizona Unity

This is the second film in the golden set. Same structural conventions as Film 01.
Treat this document as static reference data — update it only if the facts themselves
are wrong.

---

## Film in Neon (dev)

| Field | Value |
|---|---|
| film_id (UUID) | `1783a716-0ab5-458c-bfad-37bb7f034bc5` |
| file_name | `rebels_vs_az_unity.mp4` |
| team_id (scouted) | `b6710f8b-4b1a-4272-96f2-d5892ab3418e` (Florida Rebels) |
| user_id | `933c00c7-df54-43a4-ae2d-f36502347cce` (Tommy / admin) |
| duration_seconds | `5310` (88:30 wall-clock) |
| chunk_count | `4` (C0-C3) |
| status | `processing → will be 'processed' once all extract_chunk tasks finish` |
| source codecs | H.264 + AAC (confirmed via ffprobe on local raw file) |
| raw file size | 3,436,838,256 bytes (~3.2 GB) |
| compressed size | ~1.4 GB (720p H.264 CRF 28, worker ffmpeg step) |

---

## Game context

| Field | Value |
|---|---|
| Event | **Nike EYBL Peach Jam 2025** |
| Year | **2025** |
| Scouted team | **Florida Rebels** |
| Opponent | **Arizona Unity** |
| Level | AAU 17U — Nike EYBL circuit (Peach Jam is the EYBL championship event) |
| Video source | YouTube (`https://www.youtube.com/watch?v=ScVHvSVgoy8`) |
| Video title | "Brandon McCoy Jr., Paul Osaruyi, & Arizona Unity vs. Florida Rebels \| Nike EYBL Peach Jam 2025" |
| Game clock format | **Four 8-minute quarters** (32 min regulation) — confirmed same format as Film 01 |
| Notable AZ Unity players (from title) | Brandon McCoy Jr., Paul Osaruyi — expect to see heavy usage |

**Who is being scouted:** Florida Rebels. TEX is learning to scout the Rebels *as if
the Rebels were an opponent*. The roster (once seeded) becomes the subject of ground
truth — every action, every player profile, every tendency in `ground_truth.md` refers
to a Florida Rebels player. Arizona Unity players are opponents and are only referenced
indirectly ("#X drove past Arizona's #Y to the rim"). Arizona Unity's own roster is
NOT captured in this ground truth (same discipline as Film 01 with Team Durant).

**Self-scout framing:** This film is effectively a self-scout from the Rebels' own
point of view. The eval value is high because Rebels staff can validate (or poke
holes in) TEX's claims directly — they know their own players cold. Treat any
ground-truth error here as higher-severity than Film 01, because the error-detection
bar for a team that knows itself is unforgiving.

---

## Chunk boundaries (from DB / ffprobe on raw)

Each chunk is analyzed independently by Prompt 0A (extraction). TEX splits on
25-minute wall-clock boundaries (`-segment_time 1500`). Game state column is a
first-pass estimate — fill in `Actual game clock window` at the top of each chunk
section in `film_watch_notes.md` during the watch.

| Chunk | Tape start | Tape end | Duration | Approximate game state (estimate) |
|---|---|---|---|---|
| C0 | 00:00 | 25:00 | 25:00 | Pregame / intros + most of Q1 + possibly start of Q2 |
| C1 | 25:00 | 50:00 | 25:00 | Rest of Q2 + halftime + start of Q3 |
| C2 | 50:00 | 1:15:00 | 25:00 | Rest of Q3 + most of Q4 |
| C3 | 1:15:00 | 1:28:30 | 13:30 | End of Q4 + any OT / post-game wrap |

*Total film = 5,310 seconds = 88:30 wall-clock. Mapping assumes roughly equal
wall-clock time per quarter (~20 min each) with ~5 min halftime. Real mapping
will diverge — e.g. Q4 is typically longer than Q1 due to timeouts/FTs when the
game is close. Update during the watch.*

Record **in-game clock time** in `film_watch_notes.md`, not tape time. Each quarter's
clock counts DOWN from 8:00 to 0:00.

---

## Known players on this roster (as of seed)

Source: Florida Rebels 17U public roster page (screenshot, 2026 class). Position
mapping: `G → PG`, `W → SF`, `F → PF` as seeded defaults (same convention as
`scripts/seed_bbe_roster.py`). Handedness and role default to `right` /
`role_player` and are updated as observations emerge from the film.

| # | Name | Pos (seeded) | Ht | Grad | Handedness | Role |
|---|---|---|---|---|---|---|
| 0 | Donovan Williams Jr. | PG | 6'3" | 2026 | right (default) | role_player (default) |
| 1 | Landyn Colyer | SF | 6'6" | 2026 | right (default) | role_player (default) |
| 3 | Caden Daughtry | PG | 6'1" | 2027 | right (default) | role_player (default) |
| 4 | Samuel Hallas | SF | 6'6" | 2026 | right (default) | role_player (default) |
| 5 | Angelo Moton | SF | 6'6" | 2026 | right (default) | role_player (default) |
| 6 | Mike Broxton Jr | PF | 6'10" | 2026 | right (default) | role_player (default) |
| 8 | Dhani Miller | PG | 6'3" | 2026 | right (default) | role_player (default) |
| 10 | Michael Madueme | PG | 6'5" | 2026 | right (default) | role_player (default) |
| 21 | Tyler Bright | PF | 6'9" | 2026 | right (default) | role_player (default) |
| 22 | Rhiaughn Ferguson | PF | 6'8" | 2026 | right (default) | role_player (default) |
| 23 | Jaxon Richardson | SF | 6'6" | 2026 | right (default) | role_player (default) |

**Position notes to validate during first watch:** #6 Broxton Jr (6'10") and #21
Bright (6'9") are both listed as `F` on the roster sheet but at that height one
or both may actually be playing the 5. Same situation Film 01 had with #31
Pearson (seeded PF, confirmed C from film). Watch for which one operates as the
lone big vs. which one plays as a stretch-four.

---

## Open questions to answer during the first watch

*Same questions as Film 01's template — update / add as the roster becomes clearer.*

- Who is the primary ball-handler / PG of the Rebels? (Often differs from the seeded roster.)
- Which players are left-handed? (Priors: ~10–15% of roster.)
- Who is the primary initiator / secondary handler / spacer / screener / finisher?
- Are any players on this film not on the Rebels roster sheet (call-ups, late additions)?
- What's Rebels' base defense, and does it change during the game?
- Are there any structural half-court sets, or does the team default to no-set iso
  like BBE did? (Relevant comparison point — do not assume one way.)

---

## What to do when you have corrections to this metadata

The DB columns are the source of truth for `film_id`, `team_id`, and `user_id`
once populated. If this document falls out of sync with Neon, the DB wins. Update
this file and commit the diff.

The seeded roster is editable post-hoc through the `/admin` UI or by modifying
`scripts/seed_rebels_roster.py` and re-running. Either is fine for dev; neither
is allowed in production without a migration.

---

*Last updated: Golden set initialization — film_02 scaffold (pre-upload, pre-watch).*
