# Film 02 — Ground Truth (Answer Key)

**Scouted team:** Florida Rebels · **Opponent:** Arizona Unity · **Event:** Nike EYBL Peach Jam 2025
**Prompt 0B output shape:** this document mirrors the synthesis structure so TEX's output
can be graded section-by-section against what's here.

This is the authoritative answer key for grading TEX against film 02. Synthesized FROM
`film_watch_notes.md`, not from raw film. The numbers, names, and tendencies below are the
ground truth; TEX's `chunk_synthesis` output is graded line-by-line against this.

> **Rule 1:** every claim attributes to a jersey number + name.
> **Rule 2:** every count is a number, not a range, unless you explicitly flag uncertainty.
> **Rule 3:** every claim has a confidence tag: `[CONFIRMED]` / `[LIKELY]` / `[SINGLE GAME SIGNAL]`.
>   - `[CONFIRMED]` — observed 3+ times across multiple chunks, or 8+ occurrences total
>   - `[LIKELY]` — observed 2 times, or 4–7 occurrences total
>   - `[SINGLE GAME SIGNAL]` — observed once or only in one chunk. Possible tendency. Not confirmed.
> **Rule 4:** if you don't know, write "insufficient observation" — do not guess.
> **Rule 5 (self-scout note for Film 02):** Rebels staff will be able to validate this
> ground truth against their own knowledge of their players. Error tolerance is lower than
> Film 01. When in doubt on handedness / role / tendency, mark `insufficient observation`
> rather than guess.

---

## SECTION 1 — GAME HEADER

| Field | Value |
|---|---|
| Scouted team | Florida Rebels |
| Opponent | Arizona Unity |
| Final score | FLR `89` — AZ `97` (margin -8, AZ win, close late — within 4 at Q4 1:42) |
| Winner | Arizona Unity |
| Game format | Four 8-min quarters, EYBL 17U (32 min regulation) |
| Total offensive possessions by FLR | `82 logged` (chunk totals: 26 / 26 / 25 / 5). **Chunk 3 intentionally covers only the final 1:42 of Q4** (tape start at `Q4 1:42`), so the 5-possession count is accurate for that window — it is **not** a full Q4 log. Whole-game count is complete as logged; flagged ambiguity on C2 poss 12 (hurt-player stoppage — not counted as a possession). Graded denominator: **82**. |
| Total offensive possessions by opponent | Insufficient observation — AZ possessions were not logged 1-for-1. Only noteworthy defensive events and AZ transition opportunities were tallied. Rough parity with FLR (~80–85) inferable from score/pace but not traceable to the scratchpad. |
| Score progression | 0–0 (start) → FLR 6–14 (Q1 3:28) → FLR 15–17 (Q1 1:08) → FLR 19–19 (end Q1, tie) → FLR 21–28 (Q2 6:19) → FLR 24–32 (end Q2 / end chunk 0, down 8) → FLR 33–48 (halftime, down 15) → FLR 38–58 (Q3 5:05, down 20 — deficit peak) → FLR 47–64 (Q3 2:36, down 17) → FLR 55–66 (Q3 1:51) → FLR 61–75 (end Q3, down 14) → FLR 67–75 (Q4 6:52) → FLR 75–81 (Q4 4:37) → FLR 82–88 (Q4 2:17, down 6) → FLR 86–90 (Q4 1:42, down 4 — peak of comeback) → FLR 88–92 (Q4 0:58) → FLR 89–97 (final) |
| Game shape | **Comeback attempt that fell short.** AZ led wire-to-wire, built a 17-pt lead (47–64 at Q3 2:36); FLR cut to 4 by Q4 1:42 on a transition-heavy run in chunk 2 (8 FT trips, multiple and-1s); settled for contested 3s in the final 1:42 and a `#5` Moton technical foul at `Q4 0:41` (down 4 at the time) sealed the loss. |
| Date of game | 2025 Nike EYBL Peach Jam (exact date not captured in metadata) |
| Event | Nike EYBL Peach Jam 17U 2025 |
| Source film | `1783a716-0ab5-458c-bfad-37bb7f034bc5` |

---

## SECTION 2 — OFFENSE: SET AND ACTION INVENTORY

**Framing note:** The Florida Rebels, like BBE in film 01, **do not run a structured
half-court set offense.** Across 82 logged possessions the overwhelming majority resolve
into one of three modes: (a) transition pushes after any make, miss, or steal, (b)
"4-out 1-in" / "5-out" no-set spacing that defaults to ball-handler iso or a quick
drive-and-kick, and (c) a ball screen for `#3 Daughtry` that is often the only real
action of the possession. Scratchpad language repeatedly describes possessions as **"no
real offense,"** "1 pass then shoot," "bad offense fumbling passes," and "FLR look lost."
The one-time "first real play ran by FLR" note at `Q1 4:04` (a 1-4 DHO) ended in a steal.
Named sets (BLOB box, SLOB box, end-of-game double-stagger) appear but are thin in
structure and rarely produce the designed look. **This is a finding about the Rebels,
not a gap in observation.**

*Counts reconcile scratchpad language per §10a. Sorted by total occurrences descending.*

### Action A: Transition / push

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `14 opportunities / 12 scores / ~25 pts` (breakdown per end-of-chunk tallies: C0: `6 / 4 (9 pts)`, C1: `3 / 3 (6 pts)`, C2: `5 / 5 (10 pts)`, C3: `0 / 0`).
  - Representative possessions: C0-4 (`Q1 7:01` #1 steal → miss layup), C0-15 (`Q1 1:40` #3 transition 3pt make), C0-16 (`Q1 1:10` #0 outlet to #5 layup), C0-17 (`Q1 0:57` #3 length-of-court finish), C0-21 (`Q2 7:08` #0 tough layup after make), C1-8 (`Q2 2:04` #4 drive into 3 defenders miss), C1-24 (`Q3 4:04` #5 push + OREB put-back), C1-25 (`Q3 3:36` #3 length-of-court pass → #8 dunk), C2-2 (`Q3 2:17` halfcourt steal → #3 finish), C2-11 (`Q4 7:33` #3 steal → #0 layup), C2-14/15/18 (`Q4 7:02 / 6:38 / 5:17` chained transition FT / and-1 / and-1), C2-22 (`Q4 3:20` full-court inbound pass finish), C2-23/24 (`Q4 2:52 / 2:17` back-to-back transition scores).
- **Primary initiator(s):** `#3 Daughtry` (primary — pushes length-of-court, aggressive outlet-taker); `#0 Williams Jr.` (secondary — pushes after makes, advance-passer); `#10 Madueme` (tertiary — coast-to-coast finisher, see C2-24 `Q4 2:17`); `#5 Moton` (finisher / trailer).
- **Primary screener(s):** None. Transition is ahead-of-the-defense, no screen setup.
- **Typical floor position:** Start = DREB, steal, **or after an AZ make (`Q2 7:08` explicit — "pushed ball fast up court after AZ scored")**. End = rim attack or early 3 (C0-15 `Q1 1:40`). Advance pass to streaking wing is the most common transition arc.
- **Success rate:** `12 of 14 produced points` (`~86%` transition conversion rate — elite). Additional FT trips drawn on contested transition drives (C2-14 `Q4 7:02`, C2-15 `Q4 6:38` and-1, C2-18 `Q4 5:17` and-1). This is `FLR's most efficient mode by a wide margin` and the mechanism for their Q3–Q4 comeback.
- **Key counter:** Stopping FLR's transition requires either (a) slowing the initial outlet (getting two defenders back on every shot), or (b) forcing turnovers in the backcourt before FLR can push. **AZ's transition D got worse as the comeback built** (scratchpad C2 `Q4 ~5:17 → 2:17`) — multiple coast-to-coast scores against unset defense.
- **Reconciliation note:** Unified "transition," "push," "pushed ball," "advance pass," "push after make," "push after miss," "steal and score," "coast-to-coast" under one action per §10a. No sub-splits.
- **Situational use:** Primary scoring mode after ANY defensive event (make, miss, steal). Explicitly noted: "FLR like to push pace after makes and misses" (C0) and "FLR best in transition" (C2 poss 18). `Zero transition opportunities in chunk 3` (final 1:42) — FLR was forced into half-court because AZ was protecting the lead and FLR was chasing stops.

### Action B: Iso / no-set ("4-out 1-in" / "5-out" / "1-4")

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~46` (breakdown: C0: `~14`, C1: `~16`, C2: `~9`, C3: `~2`). This is the default mode whenever FLR is in the half-court and NOT in transition. The exact count is the set of possessions labeled `4 out 1 in`, `5 out`, `1-4`, `3 out 2 in`, or explicitly described as "no action ran" / "just moved ball around wing" / "nothing ran."
  - Representative possessions: C0-3 (`Q1 7:14` #3 length-of-court + PU miss, zero passes), C0-6 (`Q1 5:42` DHO TO, "poor offense"), C0-13 (`Q1 2:24` #0 contested PU off ball screen, zero passes), C1-3 (`Q2 4:30` lazy DHO pass stolen), C1-6 (`Q2 2:48` post feed + backdown jumper, 1 pass), C1-13/14/15 (`Q3 7:45 / 7:24 / 7:15` three consecutive TOs out of half-court), C1-20 (`Q3 5:27` `#3 dribbled 14 sec of shot clock` → contested 3 miss), C2-16 (`Q4 6:04` "one pass to wing who settles for deep contested 3"), C2-20 (`Q4 4:21` "zero half court offense FLR has. Just 1 maybe 2 passes and shoot"), C3-5 (`Q4 0:12` #3 crossover PU 3 — game-ending possession).
- **Primary initiator(s):** `#3 Daughtry` (primary — ~60% of iso / no-set initiations); `#0 Williams Jr.` (secondary); `#10 Madueme` (rotation initiator when #3 is off-ball); `#4 Hallas` occasional post-up iso.
- **Primary screener(s):** None in the iso variant. When a screen IS offered, it's typically `#22 Ferguson` or `#8 Miller` on the ball screen for `#3` — but the screen frequently doesn't connect or the ball-handler doesn't use it ("weak pnr," "ball screen weak").
- **Typical floor position:** 4-out 1-in (`#22` at elbow / short corner) or pure 5-out. Ball-handler on top or wing, 1–2 perimeter passes at most, then a drive or pull-up.
- **Success rate:** `Mixed — leans negative.` Explicit scratchpad tally: multiple possessions end in TO (C1-13/14/15 three straight), contested misses (C0-12 `Q1 3:09` airball, C1-20 `Q3 5:27` forced 3, C2-16 `Q4 6:04` deep 3 miss), or PU jumpers that miss. Productive iso possessions do exist (C1-10 `Q2 1:12` #3 ball-screen layup; C2-1 `Q3 2:28` #3 layup; C2-21 `Q4 3:52` #3 tough 3 make) but are driven almost entirely by #3's individual shot creation, not by structure. **Probably `<40%` scored; `[LIKELY]` at that directional rate.**
- **Key counter (if taken away):** Not observable — FLR defaulted to this mode whenever they weren't in transition, regardless of AZ's coverage. The real "counter" to iso is the scratchpad's own observation: "Slow them down and force them to run half-court offense — they can't execute it."
- **Reconciliation note:** Per §10a, unified "4 out 1 in," "5 out," "1-4," "1-4 flat," "3 out 2 in," and possessions tagged "none" (action column) under this category. These are spacing descriptors, not named sets. Keeping them as a single category is the honest representation because FLR treats all five as interchangeable half-court defaults.
- **Situational use:** Whenever FLR can't push. Increases whenever AZ scored and got matched up before FLR could advance the ball. Dominant mode in chunks 0–1 (falling behind and pressing the game), still present in chunk 2 alongside transition pushes, and the only mode available in chunk 3 once AZ was in clock-protect posture.

### Action C: High PnR with `#3 Daughtry` + `#22` or `#8`

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~9 used` (breakdown: C0: `2` [C0-5 Q1 6:27 #22 screens for #3, C0-13 Q1 2:24 #22 screens for #0], C1: `4` [C1-7 Q2 2:24 DHO + drive, C1-10 Q2 1:12, C1-11 Q2 0:35, C1-20 Q3 5:27, C1-22 Q3 4:47 — note: overlaps with drive-and-kick], C2: `2` [C2-1 Q3 2:28 #8 screens for #3, C2-4 Q3 1:25 #8 screens for #3], C3: `0`). Additional offered-but-unused or "weak pnr" instances exist but are hard to separate from generic iso.
  - Representative possessions: C0-5 (`Q1 6:27` #22 screens for #3 drive middle), C1-10 (`Q2 1:12` #3 used ball screen → layup make), C1-22 (`Q3 4:47` #3 used PnR + kick-out → 3pt make), C2-1 (`Q3 2:28` #3 + #8 PnR → layup make).
- **Primary initiator(s):** `#3 Daughtry` (~85% of PnR used); `#0 Williams Jr.` (C0-13 `Q1 2:24`).
- **Primary screener(s):** `#22 Ferguson` (primary — C0, C1); `#8 Miller` (secondary — C2 both PnRs logged).
- **Typical floor position:** Screen set above the arc or on the right wing. Ball-handler uses the screen to drive to the basket (often middle) or kicks to an open shooter. Roll-man finishes are rare — `#22` rolled but was rarely targeted cleanly.
- **Success rate:** `~5 of 9 used produced a score or FT` (C1-10 layup, C1-22 kick-out 3pt make, C2-1 layup, C2-4 FT trip, C0-5 tough pass — recovered but missed). `4 of 9 produced a negative outcome` (C0-13 contested miss, C1-11 forced TO, C1-20 14-sec dribble → contested miss). Roughly `~55% produced something` — better than the pure-iso rate, which is why PnR is #3's preferred initiation mode when a screen is available.
- **Key counter:** `drop coverage by the screen defender allows #3 to get to the rim` (see §7). Switching works when the switched defender can stay with #3 — fails when #3 is matched on a bigger defender (C1-10 Q2 1:12, C2-4 Q3 1:25).
- **Reconciliation note:** Per §10a, unified "ball screen," "pnr," "high pnr," "pick n pop," and "used ball screen" across chunks into this one action. The "weak pnr" / "ball screen set very weak" instances (C0-5, C0-13 note "held ball") are counted in the `used` column only if the ball-handler actually went off the screen; if the screen was offered but declined, it's counted under Action B iso.
- **Situational use:** FLR's clearest half-court offensive weapon other than transition. Clusters in the second half (C1 + C2) as `#3` leaned into it for the comeback run. **Not observed in chunk 3** — the late-game clock / set posture dropped PnR off the board entirely.

### Action D: Dribble handoff (DHO) — right-wing or left-wing entry

- **Confidence:** `[LIKELY]`
- **Total occurrences:** `~6` (breakdown: C0: `~3`, C1: `~2`, C2: `0`, C3: `0`).
  - C0-2 (`Q1 7:32` 4-out 1-in DHO right wing → #1 drove right + FT 2/2), C0-6 (`Q1 5:42` DHO right wing → TO on contested pass), C0-10 (`Q1 4:04` 1-4 DHO `#3/#10` — "first real play ran by FLR" → TO on steal), C1-3 (`Q2 4:30` DHO left side → lazy pass stolen), C1-7 (`Q2 2:24` DHO left side `#3/#4` + ball screen → charge called), C1-16 (`Q3 6:52` "some DHO quick ball movement" → foul on floor).
- **Primary initiator(s):** `#3 Daughtry` (typically the secondary handler in the DHO — receives the ball on the action). Executed by various wings.
- **Primary screener(s):** The DHO handler is effectively the screener — `#4 Hallas` and `#22 Ferguson` both ran DHOs handing to `#3` or `#0`.
- **Typical floor position:** Right or left wing, above the foul line extended. One or two passes to set up the DHO; drive off the hand-off to the rim or mid-range pull-up.
- **Success rate:** `~2 of 6 produced points` (C0-2 FT 2/2 by #1; C1-16 drew foul on floor). `3 of 6 ended in a TO or charge` (C0-6, C0-10, C1-3, C1-7). **Execution is poor — the DHO is where FLR's half-court sloppiness shows up most.**
- **Key counter:** TD doesn't need one — FLR breaks down on their own DHOs (lazy passes, held ball, ball-handler holding the DHO rather than attacking off it).
- **Reconciliation note:** DHO possessions that also contain a ball screen (C1-7) are counted HERE (primary action is the DHO) rather than under Action C.
- **Situational use:** Appears in chunks 0–1 only. Falls out of the offensive inventory by chunk 2 as FLR commits fully to push + iso. No DHOs in the comeback or late-game windows.

### Action E: Press-break (reactive)

- **Confidence:** `[LIKELY]`
- **Total occurrences:** `~4 observed` (breakdown: C0: `0`, C1: `~3` [C1-1 Q2 5:10 broke press with pass to halfcourt, C1-15 Q3 7:15 #0 bad bounce pass → TO, C1-19 Q3 6:03 `#10 got it dribbled rest of court to basket`], C2: `~1` [C2-5 Q3 1:00 `FLR breaks press #0 3/5 length court`], C3: `0`).
  - Representative possessions: C1-1 `Q2 5:10` (broke press, found open man → 2pt make), C1-15 `Q3 7:15` (bounce pass at #22's ankles → TO), C1-19 `Q3 6:03` (#10 dribbled through pressure → score), C2-5 `Q3 1:00` (#0 drove length for FT 1/2).
- **Primary initiator(s):** `#0 Williams Jr.` (primary press-breaker — inbounder + initial ball-advancer); `#10 Madueme` (secondary — dribbles through pressure); `#3 Daughtry` (receives from press-break and attacks).
- **Primary screener(s):** None — freelance two-guard ball advancement.
- **Typical floor position:** AZ applies man-to-man full-court press; FLR inbounds to `#0` or finds an open man at half-court, then drives or passes to `#3` or `#10` to attack.
- **Success rate:** `2 of 4 cleared pressure into a score / FT` (C1-1, C1-19, C2-5 drew foul). `1 of 4 was a TO` (C1-15 bad bounce pass).
- **Key counter:** FLR is vulnerable to pressure on inbounder (`#0`). Scratchpad: "FLR ball handler got trapped at halfcourt made a pass nearly stolen" multiple times.
- **Reconciliation note:** None — "press-break" was consistent language.
- **Situational use:** Only deployed when AZ pressed. AZ pressed intermittently in Q2–Q3; scratchpad notes `AZ man-to-man press` multiple times. Clusters in chunk 1's Q3 sequence (`Q3 7:15 → 5:01`).

### Action F: Vs zone — perimeter ball-swing

- **Confidence:** `[SINGLE GAME SIGNAL]` (2 possessions only, one in a single offense slot)
- **Total occurrences:** `2` (C0: `1`, C2: `1`)
  - C0-24 (`Q2 6:04`) — AZ in 2-1-2 zone. FLR "moved ball around well no dribbles" → ball-swing to `#10` right corner for 3pt **make**.
  - C2-10 (`Q4 7:54`) — AZ in 2-3 zone. FLR "3 out 2 in against 2-3 zone" → `#3` drove for tough PU **make**.
- **Primary initiator(s):** `#3 Daughtry` (C2-10); `#10 Madueme` received the C0-24 kick-out.
- **Primary screener(s):** None observed.
- **Typical floor position:** 2-1-2 or 3-out 2-in vs. zone. Perimeter ball movement with minimal dribble, find a gap or kick to a corner shooter.
- **Success rate:** `2 of 2 scored` — both possessions converted. Sample too small to generalize, but the pattern (perimeter passing rather than dribble-attack) is consistent.
- **Key counter:** None observed. AZ played zone only briefly in chunks 0 + 2.
- **Reconciliation note:** Unified "2-1-2 offense vs 2-1-2 zone" and "3 out 2 in against 2-3 zone" under this anti-zone category. Both share the same principle (pass-first, collapse-and-kick).
- **Situational use:** Only when AZ plays zone. Very small sample — AZ was almost exclusively man-to-man against FLR. If later films show FLR facing more zone, the action inventory should be re-evaluated.

### Single-occurrence actions / variants

*Not part of the repeating inventory, but observed. Tagging so TEX is neither penalized nor rewarded for catching them individually.*

- `C0-24 Q2 6:04` — 2-1-2 offense vs. 2-1-2 zone → corner 3 (counted in Action F; listed for completeness).
- `C1-25 Q3 3:36` — Length-of-court transition pass by `#3` → `#8 Miller` dunk. Exceptional individual play, not a repeating structure.
- `C2-22 Q4 3:20` — Full-court inbound pass (camera didn't show the set) → finish. Likely a BLOB get-ball-out-of-bounds action rather than a designed play.
- `C2-25 Q4 1:54` — 3-out 2-in "high-low" look: `#10` posted up at elbow, `#5` posted on block, `#4` drove from wing and finished. Only observed "post-involvement" action; likely not a repeating set.
- `C3-1 Q4 1:22` — End-of-game ATO: "3-out 2-in, double-staggered screens for #0 and #3" (see §4). The only designed ATO observed in the film.

**Reminder on what's NOT here:** No Horns sets. No Spain PnR. No Flare screens. No Elevator. No Iverson cut. No named traditional set offense observed. TEX outputs that produce any of those terms from this film are hallucinating — see §10f watch-item #1.

---

## SECTION 3 — OFFENSE: TEMPO AND PACE

- **Primary tempo:** `fast with iso fallback` — aggressive push on every make, miss, or steal; defaults to no-set iso / 5-out when forced to set up half-court. `[CONFIRMED]`
  - **Frequency evidence:** `14 transition opportunities whole-game` (C0: 6, C1: 3, C2: 5, C3: 0). `12 transition scores` (C0: 4, C1: 3, C2: 5, C3: 0). Transition conversion rate `~86%` — the single most efficient mode by a wide margin. Transition accounted for approximately `~25 of 89` total points (`~28%` of FLR's offense from `~17% of their possessions`).
  - Typical transition triggers: DREB + outlet to `#0` or `#3` (`Q1 1:40`, `Q1 1:10`, `Q3 3:36`, `Q4 7:02`), steal on halfcourt trap (`C2-2 Q3 2:17`, `C2-11 Q4 7:33`, `C2-23 Q4 2:52`), **explicit push after AZ makes** (`Q2 7:08` — "pushed ball fast up court after AZ scored").
- **Average time to half-court action initiation:** `fast to moderate` (FLR typically shoots within `0–1 passes` in the half-court, typically 4–8 seconds after crossing half-court). Scratchpad explicitly: "FLR half-court offense is low-pass-count: many possessions are 0–1 passes before a drive or shot" (C0 Other observations); "Zero half court offense FLR has. Just 1 maybe 2 passes and shoot" (C2-20 notes).
- **Pace changes (situational):**
  - **Chunk 2 pace accelerates materially vs chunks 0–1** — FLR's comeback run is built on push tempo. 5 of the 12 whole-game transition scores come from C2 alone; the chunk's other observations note "AZ's transition D got worse as FLR pushed." `[CONFIRMED]`
  - **#3 Daughtry over-dribble in late-clock situations** — `Q3 5:27` (#3 dribbles 14 seconds of 24-second clock → contested 3 miss) is the explicit counter-example. FLR does NOT have a clock-kill PG the way BBE had `#2 Pearson`. `[SINGLE GAME SIGNAL]` as a weakness.
  - **Desperation tempo in chunk 3 (final 1:42)** — FLR pushed hard but shot selection decayed (contested 3s at `Q4 1:22` #0, `Q4 0:12` #3). This is chasing-points behavior with the game on the line, not FLR's base tempo. `[CONFIRMED within this game]` but not a durable tendency.
- **Confidence on tempo claims:** `[CONFIRMED]` overall. Push-first with iso-fallback is supported across all 4 chunks. Transition conversion rate is `[LIKELY]` at the exact `86%` figure given the 14-opportunity sample.

---

## SECTION 4 — OFFENSE: OUT-OF-BOUNDS SETS

*BLOB = baseline out-of-bounds. SLOB = sideline out-of-bounds.*
*FLR's OOB "structure" is thin — they run box-formation looks that consistently devolve
into "no real action ran, players pop, then go into half-court offense." Explicit across
chunks 0, 1, and 2. That said, there IS one end-of-game ATO with designed structure
(double-stagger for `#0` and `#3`) that deserves its own entry.*

### BLOB #1: Box formation (weak / no-real-action)

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~4` (C0: 1 [`Q1 2:16`], C1: 1 [`Q3 5:09`], C2: 1 [`Q4 7:11`], C3: 0 observed as BLOB)
  - `Q1 2:16` — box formation, "opposite block screen opposite elbow and block screen elbow. Ran it slow and set horrible screens. Couldn't get ball in until someone popped. Then went into offense." Outcome: `pass that reset their offense` (no shot).
  - `Q3 5:09` — box, `#1` caught in corner after "coming off screen from opposite elbow or catch and drive" → drove to basket, drew foul → `FT 2/2`.
  - `Q4 7:11` — box formation, `#3` made a "lazy pass out of BLOB for steal" → TO.
- **Primary target (who's supposed to score):** `#1 Colyer` (C1 `Q3 5:09` — primary target cutting out of screen); `#3 Daughtry` (C2 `Q4 7:11` — primary inbound pass receiver).
- **Screeners:** "Opposite block + opposite elbow" — typically `#22 Ferguson` and `#4 Hallas` / `#5 Moton` rotating, not fixed assignments.
- **Structural description:** Ball under own basket. Box alignment with two players on blocks, two on elbows, one inbounder. Players on blocks pop up to elbows using screens from the original elbow players; ball enters to whoever comes open. Scratchpad explicitly: "Ran it slow and set horrible screens."
- **Success rate:** `1 of 3 produced points` (`Q3 5:09` FT trip by #1). `2 of 3 were unproductive or TOs` (`Q1 2:16` reset with no shot; `Q4 7:11` TO on lazy pass).
- **Key counter (if taken away):** Not needed — FLR breaks themselves down on most BLOBs. AZ defended them largely by fighting through the weak screens (same team-level weak screen-setting pattern noted in §10a).
- **Reconciliation note:** Unified all box-formation BLOBs under this entry. The pattern is consistent across chunks: box + screens + cut out of screen. Screens rarely connect cleanly.
- **Situational use:** Used whenever FLR needs to inbound from under their own basket. `3 observed BLOBs whole-game`, no BLOBs in the final 1:42 (chunk 3). Execution is poor — **this is an attackable BLOB structure for opposing coaches**.
- **Defensive tell (for scouting consumer):** **Screens don't make contact.** Identical pattern to BBE in film 01 — be physical at the cut, fight through the "screen," and the action collapses. Confirmed 3 times in the scratchpad across 3 chunks.

### SLOB #1: Box formation (weak / pop-out)

- **Confidence:** `[LIKELY]`
- **Total occurrences:** `~2–3` (C0: 1 [`Q2 7:35` possession 20 — "out of SLOB", 3-out 2-post alignment], C1: 2 [`Q2` #9 + `Q2 6:42` — both box formation SLOBs with missed 2pt/3pt outcomes])
  - C0-20 (`Q2 7:35`) — 3-out 2-post; camera didn't show set setup. Inbounder cut through baseline after inbound. Outcome: `3pt miss`.
  - C1-special (`Q2 ~`) — "box formation, #3 got ball and forced a bad pass. No real action out of SLOB. Just popped out for ball." Outcome: `missed 3pt`.
  - C1-special (`Q2 6:42`) — "box formation, no real action, players pop open they pass then get into halfcourt." Outcome: `missed 2pt`.
- **Primary target:** `#3 Daughtry` (pops out for entry pass); `#10 Madueme` (corner shooter in 3-out 2-post variant).
- **Screeners:** Not clearly structured — "no real action, just pop out for ball."
- **Structural description:** Box alignment on the sideline, inbounder between the box. Players pop out to get the ball rather than using screens to create separation. Once the ball is in, FLR immediately transitions into their default half-court offense (Action B iso).
- **Success rate:** `0 of 3 produced a shot on the SLOB action itself`. Two missed contested shots off the initial entry pass, one set up a regular half-court possession. **No observed SLOB score.**
- **Key counter:** None observed.
- **Reconciliation note:** SLOB and SLOB-special-situations rows were consolidated; the box-formation pattern is consistent enough to name it one structure.
- **Situational use:** Observed only in chunks 0–1 (Q2 and early Q3). No SLOB drawn up in chunk 2's comeback run or chunk 3's end-of-game sequence.
- **Defensive tell:** Same as BLOB #1 — weak screen-setting. Deny the pop-out and FLR has no backup action.

### ATO #1: 3-out 2-in, double-staggered screens for `#0` and `#3`

- **Confidence:** `[SINGLE GAME SIGNAL]` (1 observed end-of-game ATO, but structurally distinct enough from BLOB/SLOB to warrant its own entry)
- **Total occurrences:** `1` (`Q4 1:22`)
- **Primary target:** `#0 Williams Jr.` and `#3 Daughtry` (designed as a dual-option — either #0 or #3 comes off the stagger for a shot).
- **Screeners:** `#5 Moton` and `#10 Madueme` (the double-stagger pair).
- **Structural description:** FLR down 4 with 1:22 left. 3-out 2-in alignment. `#5` + `#10` set a double-staggered screen; `#0` and `#3` run off the stagger with the primary read going to whoever pops clean. Inbounder is `#4 Hallas`.
- **Success rate:** `0 of 1` — `#0` elected to keep the ball rather than use the designed stagger, dribbled into space, and settled for a contested 3 → **miss**. The designed action was NOT executed; the possession defaulted to iso. Scouting insight: **even FLR's one designed late-game set produced an off-script iso 3.**
- **Key counter:** Not needed — the ball-handler opted out of the set on his own. This is an execution / decision-making failure, not a coverage failure.
- **Reconciliation note:** Kept as a distinct ATO entry despite only one observation because the structural setup (3-out 2-in + double-stagger) is qualitatively different from the BLOB and SLOB box looks.
- **Situational use:** End-of-game down 4. Explicit single observation. Whether this is FLR's repeating clutch-time ATO or a one-off is `[NOT DETERMINABLE]` from this film alone.
- **Defensive tell:** Cover both primary options (#0, #3) aggressively on the stagger — because if either gets a clean look, they're the ones who can hit a late 3. But the bigger scouting note is that **FLR defaulted to iso off the set**, so preparing for the iso is probably more useful than preparing for the action itself.

### Single-occurrence OOB actions

*Logged but not part of a repeating structure:*

- `C1 Q3 5:09` — Same as BLOB #1 (listed there).
- `C2 Q4 3:20` poss #22 — full-court inbound pass after AZ make, pass caught and finished. Likely a BLOB get-it-in get-out execution, not a designed play. Camera didn't show setup.

*Noting: FLR ran essentially NO ATO sets with repeating structure — the one ATO with designed structure (`Q4 1:22` double-stagger) appeared only once and was executed off-script. Single-occurrence; not a base structure.*

---

## SECTION 5 — OFFENSE: LATE-GAME (final 8 minutes of close games)

- **Close late?** `YES` — FLR was within 6 from `Q4 2:17` onward, within 4 at `Q4 1:42`, within 4 at `Q4 0:58` (88–92). The final 1:42 IS a close-game late window. `[CONFIRMED]`
- **This is the single most important section for film 02 grading** — unlike Film 01 (blowout), Film 02 has a close-late scenario and TEX's late-game execution claims are directly testable here.

### What Rebels actually ran in the final 2:00 (close-game execution)

- **Primary mode: iso / 5-out + isolated ATO + desperation pushes.** Six possessions in the final 1:42 (scratchpad C3). Explicit scratchpad pattern: "hunting 3s and pushing hard, but shot selection decayed."
- **Possession breakdown for the final 1:42** (5 FLR offensive possessions, 1 defensive stop):
  - `Q4 1:22` (Poss 1) — **ATO double-stagger** for `#0` and `#3` → `#0` kept ball, settled for contested 3 → **miss**. Designed set NOT executed.
  - `Q4 1:07` (Poss 2) — 5-out, **OREB** → `#5 Moton` mid-range pull-up → **make**. Score: 88–92. 2nd-chance points on a scramble, not a designed look.
  - `Q4 1:00` (Defense) — `#3 Daughtry` full-court ball pressure → drew **offensive foul** on AZ ball-handler. Big stop, `[SINGLE GAME SIGNAL]` as an intentional end-of-game defensive strategy (see §8).
  - `Q4 0:58` (Poss 3) — 5-out, `#5` desperate drive + multiple OREB tip-back attempts → **all miss**. Scratchpad: "Played desperate this possession rather than slow it down to get a good shot to cut lead to 2." Clear decision-making failure.
  - `Q4 0:41` (Moment) — `#5 Moton` **TECHNICAL FOUL** while down 4. AZ cashed free throws + retained possession. **Scouting-critical moment.**
  - `Q4 0:16` (Poss 4) — `#3` drew shooting foul on OREB scramble → **FT 1-of-2 (by #3)**. Could not convert both ends when every point mattered.
  - `Q4 0:12` (Poss 5) — 5-out iso, `#3` crossover pull-up 3 → **miss**. Game ends 89–97.
- **Primary ball-handler in clutch / clock-kill:** `#3 Daughtry` — primary handler on all 5 FLR possessions as initiator or shot-taker. `[CONFIRMED]` for the final-1:42 window.
- **Primary scorer / foul-drawer when a bucket is needed:** `#3 Daughtry` (drew the FT trip at `Q4 0:16`; also drew AZ's offensive foul at `Q4 1:00`); `#5 Moton` (hit the mid-range at `Q4 1:07`).
- **Primary rebounder / outlet:** Scrambled — `#3` and others were crashing the glass. `3 OREBs in the final 1:42` but converted only `1 2nd-chance point` (the `#5` mid-range). FLR is an active-but-inefficient OREB team late.

### What IS observable about actual late-game execution

- **Shot clock offense (under 8 seconds):** **Insufficient observation** of a structured FLR late-clock action. The pattern of 1–2 passes + contested jumper holds in the final-1:42 window (`Q4 0:12` is essentially a 5-out iso pull-up). No observable rescue-valve action (no late-clock DHO + drive, no baseline runner, no shooter-sprint set). `[CONFIRMED]` absence of late-clock structure.
- **Scheme changes when trailing (end of game):** `YES` — `#3` applied full-court pressure at `Q4 1:00` drawing the offensive foul. One explicit observation. `[SINGLE GAME SIGNAL]` — not established as a repeating full-court-press-to-force-the-turnover posture, but flagged for TEX.
- **Scheme changes when protecting lead:** **NOT OBSERVED** — FLR was never leading after the opening minutes. `[NOT OBSERVED]`.
- **Decision-making under pressure:** **Poor.** Settled for contested 3s twice in 5 possessions (`Q4 1:22` #0, `Q4 0:12` #3). Forced desperate drives (`Q4 0:58` #5). Committed a costly technical (`Q4 0:41` #5). Missed a critical FT second-of-two (`Q4 0:16` #3). **Team composure and shot selection in close-late is a graded weakness.** `[CONFIRMED within this game]` — the comeback collapsed on execution, not coverage.
- **Confidence on late-game tendencies:** `[CONFIRMED]` that FLR's close-late offensive mode is iso + push + contested shots. `[CONFIRMED]` that team composure (tech, missed FT) was a deciding factor. `[SINGLE GAME SIGNAL]` on `#3` full-court-press-late as a scheme. Any TEX output that describes FLR as "executing a structured end-game offense" from film 02 is overstating — the evidence says otherwise.

---

## SECTION 6 — DEFENSE: BASE SCHEME

- **Primary defense:** `man-to-man` with occasional press packages (2-2-1 in Q1, man-to-man full-court press in Q2–Q3) and occasional half-court traps (Q4). `[CONFIRMED]`
- **Percentage of possessions (approximate):** Man-to-man half-court `~80%` / 2-2-1 or man press `~15%` / half-court trap `~5%`. No sustained zone observed (single 2-2-1 half-court fall-back at `Q1 4:47` which scratchpad notes they didn't look settled in).
- **Scheme changes — timeline:**
  - **Q1 8:00 → Q1 4:48 (pure man-to-man).** Active on-ball pressure, some trapping (`Q1 7:23` `#1` left his man to trap ball-handler). Generated `2 steals + 1 deflection` from aggressive help + on-ball pressure. Specific failure: `Q1 5:58` `#22 Ferguson` horrible close-out (bit on pump fake → dunk allowed).
  - **Q1 4:47 (first 2-2-1 press appearance).** 2-2-1 full-court press falling back into 2-2-1 half-court look. Scratchpad: "AZ handled press well. Got in gaps kicked out. FLR #10 bad close out which led to drive and a pass for a dunk for AZ #7." Press execution shaky — `FLR #22` had another "horrible close out" at `Q1 1:10`.
  - **Q1 4:48 → Q2 end (pure man-to-man).** Reverted to man-to-man; generated deflections (`Q2 8:00` — "cause a few deflections OOB AZ ball") but lost transition defense twice (`Q2 6:39`, `Q2 6:19`) after their own bad shots.
  - **Q3 5:01 (man-to-man press deployment).** Man-to-man full-court press — `good hedge and recover, good contest airball 3pt` at `Q3 5:01`. `#3` + `#22` hedge-recover sequence is the clearest positive defensive possession in the chunk.
  - **Q3 4:29 (transition defense breakdown).** `AZ quickly inbounds ball and #7 goes coast to coast and beats FLR down court for lay up. Horrible defense.` `[CONFIRMED]` transition D is weak after FLR makes.
  - **Q4 (half-court trap packages added).** `Q4 7:35` + `Q4 2:52` — `man-to-man trapped ball handler at halfcourt led to steal to basket` (both possessions generated steals + transition scores for FLR). `[LIKELY]` that Q4 half-court traps are a late-game change-of-pace tactic. `#3 Daughtry` full-court pressure at `Q4 1:00` drew offensive foul.
- **Pressure level:**
  - In man (Q1–Q4): `pressure` — aggressive ball pressure across the game. Multiple possessions tagged "solid man to man," "cause a few deflections." Weaknesses are close-outs (bites on pump fakes) and transition transitions (see below), not effort.
  - In press (Q1 + Q3): `pressure` — but execution is inconsistent. `Q3 5:01` clean hedge-recover; `Q3 3:50` collapse ("double ball handler at half court which leads to AZ swinging ball FLR unable to rotate").
- **Off-ball positioning:**
  - `deny / gap` — mixed. `#1 Colyer` left his man to trap ball-handler (`Q1 7:23` — help over-rotation). `#8 Miller` ran hard back on transition (`Q2 6:39`, `Q2 6:19`) but was awareness-weak on matchups.
  - Weakness: **close-outs team-wide.** Scratchpad chunk 1 Other observations: "FLR bad close out team. Does not move ball. Like to push ball." Individual examples: `#22 Ferguson` at `Q1 5:58` pump fake bite → dunk, `Q1 1:10` horrible close out, `#5 Moton` lazy close out on 3 at `Q3 1:17`.
- **Post defense:** **Insufficient observation.** AZ's post game wasn't a consistent feature of their offense; no FLR post-front / behind-post / 3-quarter patterns systematically documented. `[NOT OBSERVED]`.
- **Transition defense:**
  - **Sprint back or retreat?:** `Mixed — weak after own FLR makes.` Explicit: `Q2 6:39` "#8 ran hard back. But no idea where their men were." `Q3 4:29` "AZ quickly inbounds ball and #7 goes coast to coast." `Q3 2:11` "FLR does not get back on defense and let an easy layup after scoring back to back." **Pattern: FLR transition defense is weakest after their own makes.** `[CONFIRMED]`
  - **Primary back-defender (who trails the break):** Insufficient observation — scratchpad doesn't systematically identify a consistent trailer. `#8 Miller` flagged as trailing at `Q2 6:19` but beaten. `[NOT OBSERVED]` at player level.
  - **Transition baskets allowed:** `~11 whole-game` (C0: 6 scored, C1: 5 scored, C2: 0, C3: not tracked). Q1 and Q2 bleed is the standout weakness. C2 tally is the bright spot — AZ's transition dried up because FLR was in push mode and AZ was protecting lead.
- **Confidence:** `[CONFIRMED]` primary defense is man-to-man with pressure packages. `[CONFIRMED]` close-outs are a team-level weakness (pump-fake bites + lazy close-outs). `[CONFIRMED]` transition defense weak after FLR makes. `[LIKELY]` press packages generate some steals but execute inconsistently. `[NOT OBSERVED]` post defense and specific trailer.

---

## SECTION 7 — DEFENSE: BALL SCREEN COVERAGE

- **Primary coverage:** `split drop / switch` — with `hedge` as the most successful secondary. `[LIKELY]` (primary coverage identification is not clean — drop and switch are used roughly equally).
- **Frequency (of 10 logged PnR defensive possessions across chunks 0–1):**
  - `drop` — **4 of 10** (`~40%`): C0 `Q1 7:42`, C0 `Q1 5:00`, C1 `Q2 5:21`, C1 `Q2 1:37`. Outcomes: `1 stop / 3 scores` (`~25% stop rate`).
  - `switch` — **4 of 10** (`~40%`): C0 `Q1 6:42`, C0 `Q1 6:01`, C0 `Q1 0:22`, C1 `Q2 3:56`. Outcomes: `1 stop (contested jumper), 1 "play continued" (no clean outcome), 2 scores` (`~25% stop rate, 50% neutral`).
  - `hedge` — **2 of 10** (`~20%`): C0 `Q2 7:23`, C1 `Q3 4:53`. Outcomes: `2 stops / 0 scores` (`100% stop rate on 2 possessions`).
  - No `drop-coverage-only`, `ICE`, `blitz`, or `show` coverages observed.
- **Coverage timeline (did it change during game?):**
  - **Q1:** Mixed within man — 2 drops, 3 switches, 0 hedges (before the Q2 7:23 hedge). Coverage-by-coverage rotation seems reactive to the on-floor personnel more than a scheme choice.
  - **Q2:** Drop (2x) + switch (1x) + hedge (1x). Three of four Q2 PnRs ended in AZ scores. **This is the chunk where FLR's PnR defense was worst.**
  - **Q3:** One hedge logged (`Q3 4:53`, stop). No other PnR coverages logged in chunk 1 Q3 or in chunk 2. **PnR defense drops off the observation board entirely from chunk 2 onward** — unclear whether AZ stopped running PnR or whether FLR's Q4 half-court trap took PnR off the table.
  - **Q4:** `NO PnR DEFENSE LOGGED` — `[NOT OBSERVED]`.
- **Coverage by personnel:**
  - **`#22 Ferguson`** is the screen defender in `~6 of 10` logged PnR possessions (C0 `Q1 6:42` switch, C0 `Q1 5:00` drop, C1 `Q2 5:21` drop, C1 `Q2 3:56` switch, C1 `Q3 4:53` hedge — plus the "horrible close out" team-level tendency he owns at `Q1 5:58`). **He is the primary PnR screen defender when on the floor, and the primary target for attackers — see §10f watch-item #3.**
  - **`#1 Colyer`** was screen defender twice (C0 `Q1 7:42` drop — `stop`, C0 `Q1 6:01` switch — `play continued`). Best performance of any screen defender in the sample.
  - **`#10 Madueme`** was screen defender once (C0 `Q1 0:22` switch — `held for contested jumper`, `stop`).
  - **`#8 Miller`** was screen defender once (C0 `Q2 7:23` hedge — `stop`). One of the clean positive coverages.
  - **`#3 Daughtry`** was screen defender once (C1 `Q2 1:37` drop → `2pt make` — "both players followed the ball handler and left roller wide open").
  - Ball defender was usually `#3 Daughtry` (5 of 10) or `#4 Hallas` (3 of 10). One possession had `#0 Williams Jr.` as ball defender (3 of 10 — note overlapping counts because rotating).
- **Execution quality (where does it break down?):**
  - **Drops — #22 Ferguson gets blown by.** C0 `Q1 5:00` drop → `#22 Ferguson` in drop, AZ ball-handler blew by for layup make. C1 `Q2 5:21` drop → `#3` fought through, `#22` stayed with roll-man but nobody guarded the popping screener → AZ scored. **`#22` in drop coverage is an exploitable matchup.** `[CONFIRMED]`
  - **Switches — #22 Ferguson bites on jumpers and loses positioning.** C0 `Q1 6:42` switch → `#22 bit hard on a hessi jumper thinking it was a jump shot; #7 AZ drove baseline for dunk.` C1 `Q2 3:56` switch → `#22 over-aggressive, screener slipped screen, score allowed.` **`#22` on switches has a pump-fake / hesitation bite tendency.** `[CONFIRMED]` — same pattern as his close-out defense more broadly.
  - **Hedges — clean when executed.** Both hedges logged were stops. C0 `Q2 7:23` `#8 Miller` hedge + recover (`#0` recovered to his man) — "Good coverage here." C1 `Q3 4:53` `#22 Ferguson` hedge → missed 3pt. **Hedge execution is actually FLR's cleanest PnR coverage.** But sample is only 2 possessions.
  - **PnR communication is poor.** Explicit at C1 `Q2 1:37` drop — "both players followed the ball handler and left roller wide open which led to extra passes to open man and open jumper. NO Communication on pnr." Team-level issue, not player-specific.
- **Confidence:** `[LIKELY]` on split drop/switch being the primary coverages. `[CONFIRMED]` that `#22 Ferguson` is the exploitable screen defender across both drop and switch variants. `[LIKELY]` that hedge is the most successful coverage when used (2-of-2 stops). `[SINGLE GAME SIGNAL]` on FLR showing no ICE, no blitz, no drop-as-sole-coverage — opposing bigs who hit pick-and-pop 3s would meaningfully test this sample.

---

## SECTION 8 — DEFENSE: INDIVIDUAL DEFENSIVE TENDENCIES

*One block per FLR player with significant defensive minutes. 8 players appeared on tape;
3 seeded players (#6, #21, #23) did not appear. Defensive snap counts are not precisely
tracked, but the rotation minutes from film_watch_notes.md give rough denominators.*

### #0 — Donovan Williams Jr.

- **Primary defensive assignment:** TD's off-guards / wings in man; perimeter press participant when FLR extends.
- **On-ball quality:** `[LIKELY]` **above average.** `Q1 6:17` knocked ball loose for a steal on transition D (paired with `#1`). Active in help rotations.
- **Help activity:** `active`. Multiple help-side steals or deflections contributed to FLR's turnovers-forced count (C0: 2 forced, C1: 1 forced, C2: 2 forced — `#0` involved in several).
- **Identified weakness:** No specific individual breakdown called out in the scratchpad defensive sections. Sample is smaller than `#22`'s — `[NOT OBSERVED]` for specific defensive liabilities.
- **Confidence:** `[LIKELY]` above-average defense based on 2–3 positive observations; not enough for `[CONFIRMED]`.

### #1 — Landyn Colyer

- **Primary defensive assignment:** Wing in man; help-side rotations.
- **On-ball quality:** `[LIKELY]` **active-to-above-average.** Two specific positive observations: `Q1 7:01` stole ball at half-court on a bad lob pass ("long arms, good awareness"), `Q1 6:17` knocked ball loose for a steal.
- **Help activity:** `active`. `Q1 7:23` left his man to trap ball-handler at half-court — led to AZ having wide-open shot (miss). Mixed outcome: good aggression, sometimes leaves his man exposed.
- **Identified weakness:** Over-help on traps (`Q1 7:23`) creates 4-on-3 help situations. `[SINGLE GAME SIGNAL]` — 1 observation, not enough to establish a pattern.
- **Confidence:** `[LIKELY]` active defender with good hands; `[SINGLE GAME SIGNAL]` on over-help tendency.

### #3 — Caden Daughtry

- **Primary defensive assignment:** AZ's primary ball-handler in man; top of any FLR press; initiator of half-court traps in chunk 2 / chunk 3.
- **On-ball quality:** `[CONFIRMED]` **strong.** Drew offensive foul on full-court pressure at `Q4 1:00` (critical end-of-game defensive play). Active on-ball pressure across chunks; generated steals paired with `#0` and `#1` in transition D.
- **Help activity:** `active`. Involved in multiple half-court trap steals (`Q4 7:35`, `Q4 2:52`). Initiated full-court pressure late in games.
- **Identified weakness:** Nothing specific in the scratchpad.
- **Confidence:** `[CONFIRMED]` strong on-ball defense. `[LIKELY]` he's the player who initiates FLR's late-game defensive changes (half-court trap, full-court press).

### #4 — Samuel Hallas

- **Primary defensive assignment:** Wing / forward in man. Ball-pressure specialist in chunk 2 (`Q4 6:26`).
- **On-ball quality:** `[SINGLE GAME SIGNAL]` positive. `Q4 6:26` "man to man very good ball pressure by #4 on the ball. Almost a steal but called a foul. Great defense." One clean positive observation.
- **Help activity:** Involved in multiple defensive sequences (`Q3 3:50`, `Q2 3:23`) but not individually featured.
- **Identified weakness:** `Q1 7:23` — was part of the help-over-rotation that left AZ wide open for a 3 (though scratchpad credits `#1` as the trigger). Not a clean weakness attribution.
- **Confidence:** `[SINGLE GAME SIGNAL]` on ball pressure; otherwise `[NOT OBSERVED]`.

### #5 — Angelo Moton

- **Primary defensive assignment:** Wing in man.
- **On-ball quality:** **Insufficient observation** on individual on-ball matchups.
- **Help activity:** Participated in standard rotations.
- **Identified weakness:** **`Q3 1:17` weak / lazy close-out on a 3pt shot after a screen switch.** Scratchpad: "FLR play lost his man back turned AZ player open #5 weak lazy close out 3pt made." Single observation, but tagged because close-outs are a team-level weakness.
- **Non-defensive weakness tied to defense:** **Technical foul at `Q4 0:41`** while down 4 (82–88 context). Gave AZ free points and possession in a close-late scenario. **Scouting-critical** — see §5 and §10f watch-item #6. `[SINGLE GAME SIGNAL]` on composure weakness, but the consequence was outsized.
- **Confidence:** `[SINGLE GAME SIGNAL]` on lazy close-out; `[SINGLE GAME SIGNAL]` on composure. Both individually low-confidence but together paint a pattern worth tagging.

### #8 — Dhani Miller

- **Primary defensive assignment:** Rotation guard. 2-2-1 press participant in Q1.
- **On-ball quality:** `[SINGLE GAME SIGNAL]` positive (PnR specifically). `Q2 7:23` hedge-and-recover → stop. Clean hedge execution.
- **Help activity:** `active` effort, `weak awareness`. Scratchpad explicit: `Q2 6:39` "#8 ran hard back. But no idea where their men were. #8 got beat on a skip pass and did not close out hard to stop jump shot. 3pt made by AZ. FLR needs more effort and awareness." `Q2 6:19` "FLR gets beat on 2 on 1 with #8 trailing from behind." **Effort-without-awareness is the clearest pattern.** `[LIKELY]`.
- **Identified weakness:** Poor close-out decision-making in transition. 2 independent observations. `[LIKELY]`.
- **Confidence:** `[SINGLE GAME SIGNAL]` on clean hedge; `[LIKELY]` on transition awareness weakness.

### #10 — Michael Madueme

- **Primary defensive assignment:** Rotation guard. Bottom of 2-2-1 press in Q1.
- **On-ball quality:** `[LIKELY]` **average with one positive on-ball stop.** `Q1 0:22` switch coverage → held AZ for contested jumper (clean switch defense).
- **Help activity:** Participated in press + transition rotations.
- **Identified weakness:** **Bit on pump fake** at `Q3 2:47` → fouled shooter + and-1. Scratchpad: "FLR bites on a lot of pump fakes. Don't stay on their feet." `#10` is the specific named example of the team-level pump-fake weakness. `[SINGLE GAME SIGNAL]` on `#10` individually; `[CONFIRMED]` as a team-level weakness.
- **Also: bad close-out on 2-2-1 press** at `Q1 4:47` → drive + dunk for AZ. `[SINGLE GAME SIGNAL]`.
- **Confidence:** `[LIKELY]` average on-ball; `[CONFIRMED]` as one participant in the team-level pump-fake-bite pattern.

### #22 — Rhiaughn Ferguson

- **Primary defensive assignment:** **Primary PnR screen defender.** Rim-protector when FLR is in man. Wing rotations when off-ball.
- **On-ball quality (PnR specifically):** `[CONFIRMED]` **liability — the single most exploitable individual defensive matchup on the Rebels.**
  - `Q1 5:00` drop → AZ blew by for layup make.
  - `Q1 5:58` close-out bit on pump fake → dunk allowed. **Team-level pump-fake weakness, individually owned by `#22`.**
  - `Q1 6:42` switch → bit on hesitation jumper → AZ baseline dunk.
  - `Q1 1:10` "horrible close out" on 2-2-1 press → AZ missed layup (saved by AZ error, not `#22`'s defense).
  - `Q2 3:56` switch → over-aggressive, screener slipped → AZ scored.
  - `Q2 5:21` drop → stayed with roller but nobody guarded the popping screener → AZ scored.
  - **One positive counterexample:** `Q3 4:53` hedge → missed 3pt. Clean coverage.
- **Net:** `1 clearly positive PnR-defense action` vs. `6+ clearly negative` across `2 chunks`. **This is the most direct `#22` finding in the film.**
- **Help activity:** `passive / inconsistent` on close-outs. Close-outs are ALWAYS an issue — both in PnR pick-and-pop and in generic off-ball help.
- **Identified weaknesses (multiple):**
  - **Pump-fake bites** — loses positioning on the very first pump fake. Multiple observations.
  - **Drop-coverage rim protection is soft** — gets blown by instead of walling up at the rim.
  - **Switches are exploited by ball-handlers** — can't contain smaller, quicker attackers on the perimeter.
  - **Close-out distance is poor** — bad footwork on closeouts, late + short.
- **Confidence:** `[CONFIRMED]` PnR liability. `[CONFIRMED]` exploitable on pump-fake / hesitation moves. `[CONFIRMED]` team-level close-out weakness is most frequently associated with him.

### Players with no observable defensive signal

- **`#6 Mike Broxton Jr` (seeded PF, 6'10"):** `DID NOT APPEAR on film.` `[NOT EVALUATED]`.
- **`#21 Tyler Bright` (seeded PF, 6'9"):** `DID NOT APPEAR on film.` `[NOT EVALUATED]`.
- **`#23 Jaxon Richardson` (seeded SF, 6'6"):** `DID NOT APPEAR on film.` `[NOT EVALUATED]`.

### Summary — team-level defensive tendencies

- **Attack `#22 Ferguson` on PnR (drop, switch, or pop).** Single most actionable defensive scouting tip. `[CONFIRMED]`
- **FLR bites on pump fakes team-wide.** `#22` is the worst offender but `#10` also observed. `[CONFIRMED]`
- **FLR close-outs are poor team-wide.** Late, short, and off-balance. Spot-up shooters get clean looks. `[CONFIRMED]`
- **Transition defense is weak after FLR makes.** `AZ quickly inbounds → coast-to-coast` pattern observed 3+ times. FLR does not reliably get back. `[CONFIRMED]`
- **Press packages generate steals but leak on scramble.** The 2-2-1 / man-press in Q1 and the half-court trap in Q4 produce turnovers but also yield clean shots when AZ breaks pressure. `[LIKELY]`
- **`#3 Daughtry` is the defensive identity on the ball.** Best on-ball defender, primary trap-initiator, drew the critical offensive foul in the final minute. `[CONFIRMED]`

---

## SECTION 9 — INDIVIDUAL PLAYER CONSOLIDATED PROFILES

*One block per Rebels player with meaningful offensive possessions. 8 players appeared;
3 did not. Possession counts are approximate.*

### #0 — Donovan Williams Jr. (seeded PG, 6'3", 2026)

- **Total possessions observed:** `~25–30` (breakdown by chunk: `~10 / ~5 / ~10 / ~3`). Rotational backcourt minutes across all chunks; subbed for `#5` at halftime; heavy minutes in the chunk 2 comeback.
- **Confirmed position from film:** `PG / combo guard` — secondary ball-handler, not the primary initiator. Similar role-distortion vs. seeded position as BBE film 01 (#1 Coleman was seeded PG but #2 was the real PG).
- **Confirmed dominant hand from film:** `RIGHT` — `[LIKELY]` based on `Q1 2:24` explicit scratchpad note ("#0 right handed"). One direct observation.
  - **Evidence:** `Q1 2:24` "right handed" explicit annotation on a pull-up attempt. No contradictory observation.
- **Confirmed role:** `secondary_handler / transition_creator`
- **Offensive role (specific):** Secondary ball-handler behind `#3`. Primary press-breaker (inbounder + initial advance-passer on press-break possessions). Transition creator — several advance-passes to `#3`, `#5`, `#10` for finishes. Drives to rim in chunk 2 comeback run. Not a designed 3-point threat.
- **Scoring zones with frequency:**
  - Rim: `~3 of ~4` — `Q2 7:08` tough layup make, `Q4 7:33` transition layup make (from `#3` pass), `Q4 5:17` tough layup and-1. `Q1 7:57` missed layup.
  - Paint (non-rim): `0 observed`.
  - Mid-range: `0 of ~2` — `Q1 2:24` PU miss (note: occasionally described as a PU jumper off ball screen).
  - 3pt: `0 of ~2` — `Q4 1:22` ATO contested 3 miss (off-script from the double-stagger); `Q3 0:14` (C2-8) corner 3 miss. **No 3pt makes observed.**
  - FT attempts: `~3 trips` (`Q2 5:29` FT 1/2, `Q3 1:00` FT 1/2, `Q4 7:02` FT 2/2 — note: `Q4 7:02` is attributable to `#3` in the scratchpad, so `#0`'s FT count is `2 trips`). Scratchpad is not always clean on FT-shooter attribution.
- **Shot chart location summary:** Low-volume but rim-focused. Attacks off drives and transition pushes. Does not shoot 3s reliably.
- **Key tendencies (each tagged with confidence + count):**
  - RIGHT-handed `[LIKELY]` (1 explicit observation).
  - Pushes after makes `[CONFIRMED]` (multiple — `Q1 1:10`, `Q2 7:08`, `Q2 7:35` push sequence).
  - Inbounder + primary press-breaker `[CONFIRMED]` (`Q2 5:10`, `Q3 7:15`, `Q3 1:00`, `Q4` various).
  - Off-script in ATO sets — keeps the ball rather than using screens `[SINGLE GAME SIGNAL]` (`Q4 1:22` kept it, settled for contested 3 instead of using the double-stagger).
  - Strong rim finisher in traffic `[LIKELY]` (`Q2 7:08` "tough lay up," `Q4 5:17` tough layup + and-1).
- **Defensive assignment:** AZ's off-guards / wings. Pressed + help-side rotated.
- **Defensive vulnerability:** Not specifically observed.
- **Free throw shooting observed:** `~2 trips` (split attribution with other possessions). Makes not separated.
- **Turnovers:** `~2` attributable (`Q3 7:15` bad bounce pass → TO; `Q3 0:32` "head down no passes" → TO leading to alley-oop).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 1:10` — push after make, advance pass to `#5` for layup.
  - `C1 · Q2 5:10` — broke press, advance to `#10` who found him for PU make.
  - `C2 · Q3 2:00` — drive-and-kick to `#3` for 3pt + and-1 (4-pt play for team).
  - `C2 · Q4 7:33` — transition layup make from `#3` pass, cut lead to 10.
  - `C2 · Q4 5:17` — tough layup + and-1 in transition.
  - `C3 · Q4 1:22` — ATO double-stagger → kept ball, settled for contested 3 miss (off-script execution).

### #1 — Landyn Colyer (seeded SF, 6'6", 2026)

- **Total possessions observed:** `~10–12` (breakdown: `~3 / ~5 / ~3 / ~1`). Rotational wing minutes; subbed in `Q2 4:38` for `#10`, back out `Q3 5:05` for `#5`, back in `Q3 1:20`.
- **Confirmed position from film:** `SF` / wing.
- **Confirmed dominant hand from film:** `RIGHT` — `[LIKELY]` based on `Q1 7:32` scratchpad ("#1 right handed").
  - **Evidence:** `Q1 7:32` explicit on a drive to the basket.
- **Confirmed role:** `role_player / wing_driver`
- **Offensive role (specific):** Rotation wing. Drives right off DHO or BLOB entries; occasional corner spot-up. Not a primary scorer. Two clean drawn-foul / FT trips logged (`Q1 7:32`, `Q3 5:09`), both on right-hand drives.
- **Scoring zones with frequency:**
  - Rim: `0 of ~2` — `Q1 7:01` missed contested layup after steal; `Q1 5:42` stripped on contested pass (counted as TO).
  - Paint (non-rim): `0 observed`.
  - Mid-range: `0 of 1` — `Q1 6:27` missed mid-range PU jumper ("no rim was hit — long").
  - 3pt: `0 of 1` — `Q3 0:14` (C2-8) corner 3 miss (possession continued via OREB; see reconciliation in §10c).
  - FT attempts: `2 trips` (`Q1 7:32` FT 2/2, `Q3 5:09` BLOB FT 2/2).
- **Shot chart location summary:** Low-volume. Drives right drawing fouls. Corner 3s when off the ball. No reliable go-to scoring move.
- **Key tendencies (each tagged with confidence + count):**
  - RIGHT-handed `[LIKELY]` (1 explicit).
  - Drives right off DHO or off-ball screen `[LIKELY]` (`Q1 7:32`, `Q3 5:09`).
  - **Active defensive hands** → steals (`Q1 7:01` half-court steal, `Q1 6:17` knocked ball loose). `[LIKELY]`.
  - Over-helps on traps → leaves his man open `[SINGLE GAME SIGNAL]` (`Q1 7:23`).
- **Defensive assignment:** Wing in man.
- **Defensive vulnerability:** Not specifically observed.
- **Free throw shooting observed:** `2 trips` (both 2/2 logged). `4 FT made / 4 attempted` — small sample.
- **Turnovers:** `~1` attributable (`Q1 5:42` DHO contested pass stripped — shared attribution with passer).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 7:32` — drive right, drew foul, FT 2/2.
  - `C0 · Q1 7:01` — half-court steal in transition D.
  - `C1 · Q3 5:09` — BLOB cross-screen cut → drove to basket → FT 2/2.

### #3 — Caden Daughtry (seeded PG, 6'1", **2027**) — **the primary scorer and initiator**

- **Total possessions observed:** `~40+` (breakdown: `~12 / ~12 / ~13 / ~4`). **Played the highest minutes in the rotation — near-wire-to-wire. Most impactful player on the film.**
- **Confirmed position from film:** `PG` — **primary ball-handler confirmed.** Note: `#3` is seeded as a 2027 grad while the rest of the rotation is 2026. **Playing up a year is common for a star PG** — treat this as context, not a grading error.
- **Confirmed dominant hand from film:** `RIGHT` — `[LIKELY]` based on `Q1 1:40` explicit scratchpad note ("#3 right handed").
  - **Evidence:** `Q1 1:40` explicit on a transition 3pt make.
- **Confirmed role:** `primary_initiator / primary_scorer`
- **Offensive role (specific):** De-facto point guard AND lead scorer. Initiates nearly every half-court possession. Primary PnR ball-handler. Can pull up, drive, or make tough shots off the dribble. Primary transition creator — pushes length-of-court and advance-passes. **Primary clutch operator in the chunk 3 final 1:42.** Playmaker as well — scratchpad calls him out explicitly as "playmaker/scorer" (C2 poss 21) and "playmaker" (C2 poss 1).
- **Scoring zones with frequency:**
  - Rim: `~5 of ~8` — `Q1 0:57` transition finish, `Q3 2:28` PnR layup make, `Q3 2:17` halfcourt steal → rim make, `Q4 6:38` transition and-1 (assist credit depending on encoding), `Q1 7:14` PU miss in paint (encode as "paint jumper" but noted in rim column), `Q3 6:20` forced shot → blocked (at-rim attempt), `Q3 5:48` (C0-25) blocked in transition at rim.
  - Paint (non-rim): `~1` — `C2-10 Q4 7:54` tough PU make vs. 2-3 zone.
  - Mid-range: `0 of ~2` — `Q1 7:14` PU miss, `Q3 4:17` (C1-23) PU miss ("another possession with very little passes").
  - 3pt: `~3 of ~6` — makes: `Q1 1:40` transition 3pt (right-handed annotation), `Q3 4:47` (C1-22) PnR + kick-out 3pt make, `Q4 3:52` (C2-21) tough 3pt make; misses: `Q2 1:55` deep 3 with 1 sec shot clock, `Q3 5:27` (C1-20) 14-sec dribble → contested 3, `Q4 0:12` (C3-5) crossover pull-up 3 final possession.
  - FT attempts: `~4 trips` — `Q3 1:25` FT 1/2, `Q3 0:49` FT 2/2, `Q4 7:02` FT 2/2, `Q4 0:16` FT 1/2.
- **Shot chart location summary:** Multi-level scorer. Can pull up from 3, drive-and-finish (both rim and tough paint jumpers), and make tough contested shots off the dribble. Good transition 3pt shooter off the catch or in early offense. **Has `[CONFIRMED]` 3-point shooting ability** — "#3 can shoot" (scratchpad C1-22).
- **Key tendencies (each tagged with confidence + count):**
  - RIGHT-handed `[LIKELY]` (1 explicit).
  - **Primary initiator on virtually every half-court possession** `[CONFIRMED]` (~31+ initiator credits across chunks).
  - Pushes length-of-court in transition `[CONFIRMED]` (multiple — `Q1 0:57`, `Q3 3:36`, `Q4 7:33`, `Q4 6:38`).
  - **Playmaker — looks for teammates on drives** `[CONFIRMED]` (C0-5 `Q1 6:27` middle drive + tough corner pass, C1-25 `Q3 3:36` length-of-court pass to `#8` for dunk, C2-15 `Q4 6:38` advance to `#4` and-1, explicit scratchpad calls "#3 good play maker").
  - **Can shoot pull-up 3s** `[LIKELY]` (`Q1 1:40` transition 3 make, `Q4 3:52` tough 3 make, `Q4 0:12` pull-up 3 miss).
  - **Over-dribbles on slow-clock possessions** `[SINGLE GAME SIGNAL]` (`Q3 5:27` 14 seconds of 24 → contested 3).
  - **Primary clutch / full-court pressure player** `[CONFIRMED]` (`Q4 1:00` offensive foul drawn on pressure, `Q4 1:22` and `Q4 0:12` final-2:00 shot attempts).
- **Defensive assignment:** AZ's primary ball-handler. Top of all press + trap packages.
- **Defensive vulnerability:** Not observed. Strongest on-ball defender in the rotation.
- **Free throw shooting observed:** `~4 trips, ~5 makes of ~8 attempts` (`~63% FT%` small sample). Missed the second of a 1-of-2 trip at `Q4 0:16` when the game was within 4.
- **Turnovers:** `~3` (`C1-11 Q2 0:35` high PnR forced bad pass → TO, `C2-13 Q4 7:11` lazy BLOB pass → TO, `C2-17 Q4 5:33` over-dribble → TO).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 0:57` — length-of-court transition finish.
  - `C0 · Q1 1:40` — transition 3pt make (right-handed annotation).
  - `C1 · Q3 4:47` — PnR + drive-and-kick + 3pt make off return pass.
  - `C1 · Q3 3:36` — length-of-court transition pass to `#8` for dunk.
  - `C2 · Q3 2:28` — PnR layup make starting the comeback run.
  - `C2 · Q4 3:52` — tough pull-up 3pt make in the comeback.
  - `C3 · Q4 1:00` — full-court pressure drew offensive foul (critical stop).
  - `C3 · Q4 0:16` — FT 1/2 (missed the second when 2 points mattered).
  - `C3 · Q4 0:12` — final-possession crossover pull-up 3 miss.

### #4 — Samuel Hallas (seeded SF, 6'6", 2026)

- **Total possessions observed:** `~20` (breakdown: `~5 / ~10 / ~4 / ~1`). Rotational wing / forward; inbounder + post-player; subbed for `#5` at `Q2 6:11`; back out at `Q3 2:36` for `#0`.
- **Confirmed position from film:** `SF / stretch-4` — operates as a stretch wing with post-up option. More interior-oriented than `#1` or `#5`.
- **Confirmed dominant hand from film:** **Insufficient observation** — no explicit handedness note in the scratchpad. `[NOT OBSERVED]`.
- **Confirmed role:** `role_player / wing_scorer / spot-up_shooter`
- **Offensive role (specific):** Wing / secondary post player. Hits pick-and-pop 3 (`Q2 0:15` end-of-Q2). Backdoor cutter on sets (`Q1 5:16`). Posts up occasionally. Inbounder on multiple BLOB sets.
- **Scoring zones with frequency:**
  - Rim: `~2 of ~4` — `Q1 5:16` backdoor cut + finish, `Q4 6:38` transition and-1 catch-and-finish (from `#3` pass). Misses: `Q1 4:58` drew foul on drive (no make), `Q2 2:04` drove into 3 defenders → forced miss.
  - Paint (non-rim): `1 of 2` — `Q2 4:11` post-feed 2pt make, `Q2 2:48` missed backdown jumper.
  - Mid-range: `0 of 0`.
  - 3pt: `1 of 1` — `Q2 0:15` pick-n-pop 3pt make (end-of-Q2).
  - FT attempts: `~2 trips` (`Q1 4:58` drew foul, makes not logged; additional FT trips tied to the `C2` and-1 chain).
- **Shot chart location summary:** Rim + post + corner / pick-n-pop 3. Multi-zone but low volume at each. Not a lead scorer.
- **Key tendencies (each tagged with confidence + count):**
  - Backdoor cut vs. ball pressure `[SINGLE GAME SIGNAL]` (`Q1 5:16`).
  - Pick-n-pop 3pt shooter `[SINGLE GAME SIGNAL]` (`Q2 0:15`).
  - Posts up in half-court and isolation sets `[LIKELY]` (`Q2 4:11`, `Q2 2:48`, `Q3 3:03`).
  - Forces shots in traffic `[LIKELY]` (`Q2 2:04` drove into 3 defenders).
  - **Strong ball pressure defender** `[SINGLE GAME SIGNAL]` (`Q4 6:26` clean pressure, nearly a steal → foul called).
- **Defensive assignment:** Wing / forward matchups in man.
- **Defensive vulnerability:** Not individually called out.
- **Free throw shooting observed:** `~2 trips`; makes not separated.
- **Turnovers:** `~2` (`Q2 2:24` charge called on drive, `Q1 5:42` DHO contested pass — shared-blame with `#1`).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 5:16` — backdoor cut, `#3` feed → layup make.
  - `C0 · Q1 4:58` — drive + drew foul (no make).
  - `C1 · Q2 0:15` — pick-n-pop 3pt make to end Q2.
  - `C2 · Q4 6:26` — ball pressure nearly stole it (foul called instead).
  - `C2 · Q4 6:38` — caught `#3` transition pass + finish (and-1).

### #5 — Angelo Moton (seeded SF, 6'6", 2026)

- **Total possessions observed:** `~15–20` (breakdown: `~5 / ~5 / ~7 / ~3`). Rotational wing; subbed for `#4` at `Q1 2:16`; in / out across chunks; on the floor for the end-of-game stretch.
- **Confirmed position from film:** `SF` / wing.
- **Confirmed dominant hand from film:** `RIGHT` — `[LIKELY]` based on `Q1 2:12` scratchpad ("#5 right hand").
  - **Evidence:** `Q1 2:12` explicit annotation on a pull-up jumper.
- **Confirmed role:** `role_player / transition_finisher`
- **Offensive role (specific):** Rotation wing. Transition finisher (`Q1 1:10` outlet-to-layup from `#0`; `Q1 0:13` end-of-Q1 blocked layup off `#3` assist attempt). Post-up option. Occasional pull-up shooter. Role expanded in the end-of-game sequence.
- **Scoring zones with frequency:**
  - Rim: `~1 of ~3` — `Q1 1:10` transition layup make. Misses: `Q1 2:12` PU miss + tipped-in by `#0` (encoded as `#0` tip-in make, not `#5` rim make), `Q1 0:13` end-of-Q1 layup blocked by AZ.
  - Paint (non-rim): `1 of 1` — `Q4 1:07` (C3-2) OREB → mid-range pull-up → make. Game-critical bucket cutting it to 88–90.
  - Mid-range: `0 of ~1` — `Q1 2:12` PU miss.
  - 3pt: `0 of 0` — no 3pt attempts clearly logged for `#5`.
  - FT attempts: `0 observed` cleanly attributable.
- **Shot chart location summary:** Rim / paint / mid-range, but low-volume. Does NOT shoot 3s in this film. Wing role is more about running the floor and spotting up than creating.
- **Key tendencies (each tagged with confidence + count):**
  - RIGHT-handed `[LIKELY]` (1 explicit).
  - Transition finisher as the trailer / wing receiver `[LIKELY]` (`Q1 1:10`).
  - **Technical foul at `Q4 0:41` down 4 — critical composure failure** `[SINGLE GAME SIGNAL]` but outsized consequence. Ties to §5 and §10f watch-item #6.
  - Desperate drives when team is chasing `[SINGLE GAME SIGNAL]` (`Q4 0:58` — "Played desperate this possession rather than slow it down").
- **Defensive assignment:** Wing in man.
- **Defensive vulnerability:** **Weak close-out at `Q3 1:17`** → AZ 3pt make (see §8).
- **Free throw shooting observed:** No clean FT trips logged for `#5`.
- **Turnovers:** `0` cleanly attributable.
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 1:10` — transition layup make from `#0` outlet.
  - `C2 · Q4 1:07` — OREB → mid-range make (88–90 comeback bucket).
  - `C2 · Q4 0:58` — desperate drive + OREB tips → misses (`82–92` → `88–92` sequence).
  - `C2 · Q4 0:41` — **technical foul (down 4)** — game-critical negative moment.

### #8 — Dhani Miller (seeded PG, 6'3", 2026)

- **Total possessions observed:** `~10` (breakdown: `~2 / ~3 / ~4 / ~1`). Rotational guard; subbed in `Q1 0:42` for `#22`; out `Q2 5:26` for `#22`; back for stretches.
- **Confirmed position from film:** `PG / combo guard`.
- **Confirmed dominant hand from film:** **Insufficient observation.** `[NOT OBSERVED]`.
- **Confirmed role:** `role_player / transition_finisher / screener`
- **Offensive role (specific):** Rotation handler. Sets ball screens for `#3` in `chunk 2` PnRs. Transition finisher (`Q3 3:36` dunk from `#3`'s length-of-court pass). Low individual-shot volume.
- **Scoring zones with frequency:**
  - Rim: `1 of 1` — `Q3 3:36` transition dunk off `#3`'s length pass.
  - Paint (non-rim): `0 of 0`.
  - Mid-range: `0 of 0`.
  - 3pt: `0 of 0`.
  - FT attempts: `0 observed`.
- **Shot chart location summary:** Basically no individual shot volume. Contributes as a screen-setter and transition dunker.
- **Key tendencies (each tagged with confidence + count):**
  - Sets screens in the C2 PnR action with `#3` `[LIKELY]` (C2-1 `Q3 2:28`, C2-4 `Q3 1:25`).
  - Transition finisher when fed `[SINGLE GAME SIGNAL]` (`Q3 3:36`).
  - **Clean PnR hedge execution defensively** `[SINGLE GAME SIGNAL]` (`Q2 7:23`).
- **Defensive assignment:** Rotation guard.
- **Defensive vulnerability:** Not specifically observed on-ball; team-level awareness noted at `Q2 6:39` (effort-without-awareness).
- **Free throw shooting observed:** `0 of 0`.
- **Turnovers:** `0` cleanly attributable.
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q2 7:23` — hedge + recover PnR defense (stop).
  - `C1 · Q3 3:36` — transition dunk off `#3` pass.
  - `C2 · Q3 2:28` — set screen for `#3` PnR → `#3` layup (kickstarted comeback).

### #10 — Michael Madueme (seeded PG, 6'5", 2026)

- **Total possessions observed:** `~15–20` (breakdown: `~4 / ~6 / ~8 / ~2`). Rotational guard; multiple subs in/out; heavy minutes in C2 comeback.
- **Confirmed position from film:** `PG / combo guard` — 6'5" is tall for a PG, plays combo backcourt with `#3` or `#0`.
- **Confirmed dominant hand from film:** **Insufficient observation.** `[NOT OBSERVED]`.
- **Confirmed role:** `secondary_initiator / transition_scorer`
- **Offensive role (specific):** Secondary initiator / ball-handler. Coast-to-coast transition scorer (`Q2 6:25`, `Q4 2:17`). Posts up at the elbow (`Q4 1:54`, 3-out 2-in high-low). Hit a kick-out 3 vs. zone (`Q2 6:04`).
- **Scoring zones with frequency:**
  - Rim: `~3 of ~5` — `Q3 6:03` push-through-pressure finish, `Q3 4:04` OREB put-back after `#22` miss, `Q4 2:17` coast-to-coast layup. Misses: `Q2 6:25` blocked drive, `Q2 4:51` blocked layup.
  - Paint (non-rim): `0 of ~1` — `Q4 1:54` 3-out 2-in elbow post-up (pass-out, not shot).
  - Mid-range: `0 of 0`.
  - 3pt: `1 of 1` — `Q2 6:04` right-corner 3 vs. 2-1-2 zone.
  - FT attempts: `~1 trip` (implied via drives that drew fouls — no clean attribution).
- **Shot chart location summary:** Rim-focused in transition; occasional corner 3 vs. zone. Can post up at 6'5" when needed but rarely does.
- **Key tendencies (each tagged with confidence + count):**
  - Coast-to-coast transition finisher `[LIKELY]` (`Q2 6:25` force, `Q4 2:17` clean — 2 observations).
  - Corner 3 vs. zone `[SINGLE GAME SIGNAL]` (`Q2 6:04`).
  - Posts up at 6'5" when matched smaller `[SINGLE GAME SIGNAL]` (`Q4 1:54`).
  - Forces shots in traffic `[LIKELY]` (`Q2 6:25` "drove ball on two defenders and got blocked. No passes").
- **Defensive assignment:** Rotation guard. Bottom of 2-2-1 press (Q1).
- **Defensive vulnerability:** Pump-fake bite `[SINGLE GAME SIGNAL]` (`Q3 2:47`). Bad 2-2-1 press close-out → dunk allowed `[SINGLE GAME SIGNAL]` (`Q1 4:47`).
- **Free throw shooting observed:** Not clearly separated.
- **Turnovers:** `~0–1`.
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 3:37` — DHO jumper make.
  - `C0 · Q2 6:04` — right-corner 3pt make vs. 2-1-2 zone.
  - `C1 · Q3 6:03` — drove through pressure → layup make.
  - `C2 · Q4 2:17` — coast-to-coast layup in comeback.
  - `C2 · Q4 1:54` — 3-out 2-in elbow post-up → `#4` finish (pass-out play).

### #22 — Rhiaughn Ferguson (seeded PF, 6'8", 2026)

- **Total possessions observed:** `~20–25` (breakdown: `~10 / ~10 / ~2 / ~2`). Heavy minutes in chunks 0–1; subbed out for `#8` at `Q3 3:53`; back in sparingly in C2/C3.
- **Confirmed position from film:** `PF / C` — functionally the lone big in most FLR lineups. Sets ball screens, posts up occasionally, crashes offensive boards. Size/role consistent with seeded PF but operating closer to a C than a stretch-4.
- **Confirmed dominant hand from film:** **Insufficient observation.** `[NOT OBSERVED]`.
- **Confirmed role:** `screener / offensive_rebounder / finisher`
- **Offensive role (specific):** Primary screener in FLR's PnR action with `#3`. Offensive rebounder — multiple OREB attempts / putback fouls drawn. Does NOT shoot 3s. Post-up attempts are rare.
- **Scoring zones with frequency:**
  - Rim: `~0 of ~2` — OREB put-back attempts (`Q1 2:24` drew foul off OREB, `Q3 4:04` missed layup → `#10` put-back). No clean rim makes attributed.
  - Paint (non-rim): `0 of 0`.
  - Mid-range: `0 of 0`.
  - 3pt: `0 of 0`.
  - FT attempts: `~1 trip` (`Q1 2:24` drew foul on OREB attempt).
- **Shot chart location summary:** No on-ball scoring attempts at any level. Contributes as screener + offensive rebounder + putback threat.
- **Key tendencies (each tagged with confidence + count):**
  - Primary screener in FLR PnR `[CONFIRMED]` (`Q1 6:27`, `Q1 2:24`, `Q2 1:12`, `Q2 0:35`, `Q3 5:27`, `Q3 4:47` — 6+ observations across chunks 0–1).
  - Crashes offensive glass `[LIKELY]` (`Q1 2:24` OREB battle drew foul, OREB attempts in other possessions).
  - **Weak screen-setting** `[LIKELY]` — screens frequently described as "weak" or "ball screen set very weak" (`C0-11 Q1 3:37`, `Q1 6:01` "switch a screen that was set very weak").
  - **Rolls hard but is rarely targeted** `[LIKELY]` — multiple PnRs where the ball-handler kept it rather than using `#22` as the roll-man.
- **Defensive assignment:** **Primary PnR screen defender** (see §8). Rim protection.
- **Defensive vulnerability:** **Comprehensive PnR defense liability — see §8.** Pump-fake bites, poor close-outs, drop coverage gets blown by, over-aggressive on switches.
- **Free throw shooting observed:** `~1 trip` (`Q1 2:24`), makes not logged.
- **Turnovers:** `0` directly attributable.
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 5:58` — horrible close-out, pump-fake bite → dunk allowed (exploitable tendency).
  - `C0 · Q1 2:24` — OREB battle → drew foul.
  - `C1 · Q2 3:56` — switch over-aggression → score allowed.
  - `C1 · Q3 4:04` — OREB attempt → `#10` put-back.
  - `C1 · Q3 4:53` — clean hedge → missed 3pt (positive counter-example).

### #6 — Mike Broxton Jr (seeded PF, 6'10", 2026)

- **DID NOT APPEAR on film.** No possessions observed in any chunk. Either a DNP or garbage-time minutes below the observation threshold. Status: `not_evaluated`.

### #21 — Tyler Bright (seeded PF, 6'9", 2026)

- **DID NOT APPEAR on film.** No possessions observed in any chunk. Status: `not_evaluated`.

### #23 — Jaxon Richardson (seeded SF, 6'6", 2026)

- **DID NOT APPEAR on film.** No possessions observed in any chunk. Status: `not_evaluated`.

### Unknown players (seen on film but not on seeded roster)

*No unrostered Rebels jerseys observed. All 8 Rebels players who appeared (#0, #1, #3, #4, #5, #8, #10, #22) are on the seeded roster. Three seeded players (#6, #21, #23) did not appear on film — notable because both big men (6'9" and 6'10") are among the DNPs, and the sole big in the rotation was 6'8" `#22`.*

| # | Short description | Suggested name (if known) | Possessions observed |
|---|---|---|---|
|   | *(none)*  |   |   |

---

## SECTION 10 — SYNTHESIS FLAGS

*This is the most important section for building a valid eval set. Every judgment call
you made goes here. Every uncertainty. Every vocabulary reconciliation. Every
contradiction you resolved.*

### 10a — Vocabulary reconciliations you made

- **"Transition" / "push" / "pushed ball" / "advance pass" / "push after make" / "push after miss" / "steal and score" / "coast-to-coast"** — all unified in §2 Action A under "Transition / push." Explicit team-level tendency was to push on any defensive event (make, miss, steal). Total count reconciles the 14-opportunity / 12-score tally from end-of-chunk summaries.
- **"4 out 1 in" / "5 out" / "1-4" / "1-4 flat" / "3 out 2 in"** — spacing descriptors, NOT named sets. Unified in §2 Action B under "Iso / no-set." This is a deliberate vocabulary choice because "having no set offense" IS a finding about FLR — same as BBE in film 01. Flag if TEX's output calls these "5-out motion" (which implies structure) rather than "no-set iso" (which is what actually happened).
- **"Ball screen" / "PnR" / "high PnR" / "pick n pop" / "used ball screen" / "weak pnr"** — unified in §2 Action C under "High PnR with #3 + #22 (or #8)." The "weak pnr" / "ball screen set very weak" subset is counted in `used` if the ball-handler actually came off the screen; otherwise it rolls into Action B iso.
- **"DHO on right wing" / "DHO on left side" / "some DHO quick ball movement"** — unified in §2 Action D under "Dribble handoff." All observed DHOs share structural logic (wing entry + drive off the hand-off).
- **"Press break" / "broke press" / "got pressed into half court set"** — unified in §2 Action E under "Press-break (reactive)."
- **"2-1-2 offense vs 2-1-2 zone" / "3 out 2 in against 2-3 zone"** — unified in §2 Action F under "Vs zone — perimeter ball-swing" despite being different zone shapes. The offensive principle (pass-first collapse-and-kick) is identical across both.
- **"Box formation" (BLOB) / "box" (SLOB) / "opposite block screen opposite elbow"** — unified in §4 BLOB #1 and SLOB #1 under "Box formation (weak)."
- **"Man to man" / "man to man press" / "man to man trap" / "2-2-1 press" / "2-2-1 halfcourt"** — in §6, distinguished as separate scheme windows within a "man-to-man base with pressure packages" framework. Did NOT collapse the 2-2-1 press + man-to-man press into one scheme because the shapes differ.
- **"No 2 on roster — likely typo for #5"** — C1 poss #21 (`Q3 5:09`) and #22 (`Q3 4:47`) list `#2` in personnel. Resolved as `#5` based on the `Q3 5:05` substitution (`#5 in for #1`). Confidence `[LIKELY]` on this interpretation.
- **"Primary handler" vs "primary PG"** — `#0 Williams Jr.` seeded as PG. `#3 Daughtry` is the clear primary initiator on film. Resolution: **`#3` is the de-facto primary handler; `#0` is secondary.** Same resolution pattern as BBE film 01 (#2 Pearson over #1 Coleman).

### 10b — Counts you are not confident on

- **Chunk 3 possession count (5)** — **This is the critical flag.** The 5-possession chunk 3 count covers ONLY the final 1:42 of Q4 (tape start at `Q4 1:42`). It is NOT incomplete — it is intentionally narrow. Whole-game total of 82 is accurate as logged. Per-possession rate claims for chunk 3 alone are reliable for the 1:42 window only.
- **AZ possessions total** — not tracked 1-for-1. Only noteworthy defensive events were tallied. Any claim about AZ's offensive tendencies is `[NOT OBSERVED]` at the possession level.
- **Rebels team fouls** — not tracked from scoreboard at all across 4 chunks. Scratchpad explicitly flagged: "Rebels team fouls / foul trouble not tracked live."
- **FT makes per player** — tracked at chunk summary level, NOT per-player cleanly. Whole-game FT trip count `12`, whole-game FT makes `15` of `20` attempts (`75% FT%`). Per-player FT splits are `[LIKELY]` at best.
- **Rebels OREB totals per chunk** — C2 logged `0 OREBs` (oddly low given the and-1 chains), C3 logged `3 OREBs` in just 5 possessions. Pattern suggests C2's OREB tally may be under-counted by a few; C3's is tightly accurate. Whole-game total `5 OREBs` is `[LIKELY]`.
- **C1 "transition scores" (3 scores 6 pts)** — the 3 transition possession rows (C1-8, C1-24, C1-25) had outcomes `miss layup`, `OREB put-back`, `dunk`. The arithmetic (3 scores 6 pts = 3 two-pointers) doesn't quite match: C1-8 was a miss, C1-24 was an OREB put-back (counts 2 pts), C1-25 was a dunk (2 pts). That's `2 scores / 4 pts` from the transition opportunities themselves, with the OREB put-back adding a 2nd-chance point. The scratchpad summary `3 scores 6 pts` is slightly over-counted. `[LIKELY]` on the directional claim (transition is productive) but `[SINGLE GAME SIGNAL]` on the exact count.
- **AZ transition scores allowed in C2 = 0** — this is internally consistent with the chunk notes (AZ's transition D got worse as FLR pushed, implying AZ wasn't pushing either). `[LIKELY]`.
- **AZ 2nd-chance points** — `C0: not filled` (flagged unknown), `C1: 1 score (3pt) 2` (confusing notation), `C2: 1 score / 2 pts`, `C3: not tracked`. Total ~2–5 points. Directional claim (FLR gives up some 2nd-chance points but not many) is `[LIKELY]`; exact count is not.

### 10c — Jersey numbers you could not confirm

- **C1 poss #21 (`Q3 5:09`) and #22 (`Q3 4:47`)** list `#2` in personnel — no `#2` on the Rebels seeded roster. Resolved as `#5` based on the `Q3 5:05` sub (`#5 in for #1`). Flag retained in case the correction is wrong and a later film establishes otherwise.
- **C2 poss #1 and #2 originally had duplicate `#10` in personnel** — resolved to `#0` during the audit pass (see §10d).
- **C2 poss #5 (`Q3 1:00`)** personnel `#3,#10,#5,#1,#10` has `#10` listed twice; 5th player unknown. Ground truth uses 4-player list with 1 unknown.
- **C2 defensive row at `Q3 2:11`** — originally had clock `Q2 2:11`, corrected to `Q3 2:11` during audit (see §10d). Personnel `#10` duplicate resolved to `#0`.
- **C3 row personnel inconsistency** — `#` prefix missing on second jersey (`#3,10,#5,#4,#0`). Typo, not substantive.
- **C3 defensive row at `Q4 1:00`** — personnel `#2,#10,#4,#5,#0` contains `#2` — same no-`#2`-on-roster issue. Likely typo for `#3` based on the action ("`#3` pressured ball full court drew offensive foul"). Unresolved as a typo; content is clear.
- **C1 poss #8 (`Q2 2:04`)** — only 4 jerseys listed (`#4, #22, #1, #5`). 5th player unknown.
- **C1 poss #15 (`Q3 7:15`)** — only 4 jerseys listed.
- **C3 Rebels possession `#` column** — all 5 rows have blank `#` column (identified by clock only). Not a jersey issue, but an indexing flag.
- **Handedness of #4, #8, #10, #22** — not explicitly established in the scratchpad. Ground truth §9 shows "insufficient observation" for all four rather than guess. Only `#0`, `#1`, `#3`, `#5` have confirmed-from-film right-handedness.

### 10d — Contradictions resolved (and how)

- **Chunk 0 transition summary** — initial scratchpad summary listed AZ transition scores at `6` and Rebels transition scores inconsistently. During audit pass: FLR transition scores unified as `4 scores 9 pts` with explicit possession attribution (`#15` 3pt, `#16/#17/#21` 2pt). AZ transition scores allowed `6` kept as the scratchpad tally. Internal consistency ensured.
- **C2 possession #1-#2 (`Q3 2:28 / Q3 2:17`) personnel duplicates** — `#3,#8,#10,#5,#10` had `#10` listed twice. Resolved as `#0` for the second `#10` based on the surrounding possessions (poss #3 lists `#0` explicitly, and `#0` was subbed in at `Q3 2:36`).
- **C1 defensive observation clock typo** — `Q2 2:11` corrected to `Q3 2:11` during audit. Chunk 1 ended at `Q3 2:36`, so a `Q2 2:11` timestamp was impossible inside chunk 2's window. Likely typo.
- **C2 possession #3 (`Q3 2:00`) "3pt make and1 1/1 from FT"** — unusual encoding (and-1 on a made 3 is a 4-pt play). Re-encoded as `3pt make + 1-of-1 FT` for counting clarity. 4 points total, attributable to `#3`.
- **C2 possession #4 FT trip** — scratchpad initially showed `FT 0/1`; corrected during audit to `FT 1-of-2 (by #3)` to match Chunk 2 total FT makes (9 of 12 = sum of individual trips).
- **C3 possession #2 outcome encoding** — re-encoded as `OREB → 2pt make` to reflect the actual sequence (OREB first, then `#5` mid-range).
- **Chunk 1 poss #10 Initiator / Screener** — audit fixed `Initiator #22` to `Initiator #3` with `Screener #22`. The scratchpad note was clear (`#3 brought up ball... used ball screen`) — initiator should be the ball-handler.

### 10e — Situations that may not be representative

- **`#3 Daughtry` is a 2027 grad (playing up a year)** — his outsized usage + playmaker-scorer role is what a team would expect from an age-up star PG. Any stat-comparison to same-age 2026 peers should note the class mismatch. Handedness, role, tendency claims are `[CONFIRMED within this game]` but his usage rate may be inflated vs. what it will look like when `#6` and `#21` (both big men, 2026) return to the rotation.
- **Three seeded bigs (#6, #21, #23) did not appear on tape.** Actual rotation is 8 players, not 11. **`#6 Broxton Jr` (6'10") and `#21 Bright` (6'9") are both listed as PFs but could be true 5s** — their absence means FLR played `#22 Ferguson` (6'8") as the sole big for nearly the entire game. This compressed the frontcourt and may not represent FLR's full offensive inventory. Any ground-truth claim about FLR's actual "best-case" post offense is absent because the bigs weren't on the floor.
- **FLR was trailing the entire game.** The offensive profile (more push, more iso, more contested shots) may reflect a chasing-points posture that doesn't generalize to games where FLR leads. Conservatively, transition-heavy tendency should hold (it's their identity), but the "1–2 pass, shoot" half-court pattern may tighten up when the game isn't forcing desperation.
- **AZ Unity had `#7 Brandin McCoy Jr` who was NOT on the published AZ roster.** Off-roster star players can distort a game. `#7 McCoy Jr` was called out in the YouTube title as a featured player — expect him to have taken more shots than a typical AZ rotation piece, which may have forced FLR into more possessions of on-ball pressure than they'd normally run.
- **AZ played almost exclusively man-to-man; only 2 small samples of zone.** FLR's anti-zone action inventory (§2 Action F) is 2 possessions total. If future films show FLR facing zone, the §2 framing may need to be revisited.
- **Chunk 2 comeback context (down 17 → down 4)** — the chunk's extreme foul-drawing volume (8 FT trips / 12 attempts / 9 makes, multiple and-1s) and transition conversion rate are partially the product of AZ's lead-protection posture (less aggressive defense, not running their own offense). These Chunk 2 numbers should NOT be used as FLR's base-rate offensive efficiency.
- **`#5 Moton` technical foul at `Q4 0:41`** is a composure / emotional event, not a repeating tactical tendency. `[SINGLE GAME SIGNAL]` but outsized consequence — any TEX output calling `#5` "a composure risk" from one observation is over-claiming; calling the tech foul out specifically as a game-altering moment is fair.

### 10f — Things you want TEX to get right (watch-items for grading)

1. **FLR has no structured half-court set offense.** Primary scoring is transition + iso + PnR with `#3`. Any TEX output that describes FLR as running named sets ("Horns motion," "Spain PnR," "flex continuity," "flare screens," "motion offense") is hallucinating. The one real designed structure in the half-court is the BLOB box (and even that is weak). The one ATO observed (`Q4 1:22` double-stagger) was executed off-script.
2. **`#3 Caden Daughtry` is the primary initiator AND primary scorer.** Not `#0 Williams Jr.` (seeded PG), not any other rostered player. `#3` is a 2027 grad playing up a year — confirm on scouting reports and do not confuse his outsized usage with a roster error.
3. **`#22 Rhiaughn Ferguson` is a PnR defense liability.** Pump-fake bites, soft drop, over-aggressive on switches, poor close-outs. 6+ independent negative PnR-defense observations across chunks 0–1 vs. 1 clean hedge. **This is the single most actionable defensive scouting tip for opposing coaches.** Same structural finding as BBE film 01's `#31 Pearson`.
4. **FLR bites on pump fakes team-wide.** `#22` and `#10` both observed. This is a team-level close-out discipline weakness, not a player-specific one. TEX must identify this as a team tendency, not a `#22`-only finding.
5. **FLR transition defense breaks down after their own makes.** "AZ quickly inbounds → coast-to-coast" observed 3+ times across chunks. `[CONFIRMED]` pattern. TEX should flag this as an exploitable defensive gap.
6. **`#5 Moton` took a technical foul at `Q4 0:41` while down 4 — it sealed the loss.** This is a game-altering moment and a composure watch-item for future films. TEX should attribute the tech to `#5` specifically and tie it to the final margin.
7. **FLR's late-game execution fails the same way twice.** Settled for contested 3 by `#0` at `Q4 1:22` off a double-stagger ATO (executed off-script), then settled for a pull-up 3 by `#3` at `Q4 0:12`. **TEX should call out "FLR hunts 3s late instead of driving / getting to the line."**
8. **Three rostered bigs (#6, #21, #23) DID NOT APPEAR on film.** Actual rotation is 8 players. TEX should mark these players as `not_evaluated` rather than invent observations. **Both 6'9"+ bigs are among the DNPs**, which means FLR played small all game with `#22` (6'8") as the lone true big.
9. **All four observed-handedness players are RIGHT-handed** (`#0`, `#1`, `#3`, `#5`). Unlike BBE film 01 (3 lefties), no lefties observed on FLR. `#4`, `#8`, `#10`, `#22` have `[NOT OBSERVED]` handedness. TEX should mark unobserved hands accordingly — guessing right for everyone is not the same as observing it.
10. **Game was close late (within 4 at `Q4 1:42`), NOT a blowout.** Unlike BBE film 01, the close-game late-execution section (§5) is testable on this film. Any TEX output that treats FLR's final-1:42 as "blowout protection" or "garbage time" is mis-framing — these possessions are high-signal for close-game tendencies.

---

## SECTION 11 — HOW THIS DOCUMENT GETS GRADED

When TEX runs against this film, grading will walk through each numbered section:

| Section | Graded how |
|---|---|
| 2 — Action inventory | Each action TEX identifies is compared to this list. `captured / missed / hallucinated`. |
| 3 — Tempo | Does TEX's claim match yours within tolerance (e.g. 50% vs 60% = match)? |
| 4 — OOB sets | Each OOB TEX identifies compared to yours. |
| 6 — Base scheme | Does TEX identify the right primary defense? Timeline changes? |
| 7 — Ball screen coverage | Primary coverage correct? Timeline changes captured? |
| 8 — Individual defensive tendencies | Each claim compared to yours. |
| 9 — Player profiles | Each player's handedness, role, tendencies compared to yours. |
| 10 — Synthesis flags | Did TEX flag the same uncertainties? Is TEX over-confident where you were uncertain? |

The per-section scores roll up to a `captured / missed / hallucinated` table for film 02
and get written to `EVAL_SCORES.md`. Section 11 is documentation only — nothing to fill in.

---

*All blanks above have been filled in (or explicitly marked "insufficient observation").
This document is ready. Commit it. Then run TEX against film 02 and the grading UI will
diff TEX's output against this file.*

*Film 02 is step 2 of 5. Films 03–05 repeat this process. At 5 films complete, golden
set initialization is done and Stage 1 of the commercial ladder (per ROADMAP.md) is gated.*
