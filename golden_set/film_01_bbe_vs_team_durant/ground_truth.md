# Film 01 — Ground Truth (Answer Key)

**Scouted team:** Brad Beal Elite · **Opponent:** Team Durant · **Event:** Peach Jam QF 2025
**Prompt 0B output shape:** this document mirrors the synthesis structure so TEX's output
can be graded section-by-section against what's here.

This is the authoritative answer key for grading TEX against film 01. You fill it in
**after** watching the film and after `film_watch_notes.md` is complete. It is synthesized
FROM your scratchpad, not from raw film. The numbers, names, and tendencies below are the
ground truth; TEX's `chunk_synthesis` output is graded line-by-line against this.

> **Rule 1:** every claim attributes to a jersey number + name.
> **Rule 2:** every count is a number, not a range, unless you explicitly flag uncertainty.
> **Rule 3:** every claim has a confidence tag: `[CONFIRMED]` / `[LIKELY]` / `[SINGLE GAME SIGNAL]`.
>   - `[CONFIRMED]` — observed 3+ times across multiple chunks, or 8+ occurrences total
>   - `[LIKELY]` — observed 2 times, or 4–7 occurrences total
>   - `[SINGLE GAME SIGNAL]` — observed once or only in one chunk. Possible tendency. Not confirmed.
> **Rule 4:** if you don't know, write "insufficient observation" — do not guess.

---

## SECTION 1 — GAME HEADER

| Field | Value |
|---|---|
| Scouted team | Brad Beal Elite |
| Opponent | Team Durant |
| Final score | BBE `91` — TD `59` (margin +32, BBE win, not close) |
| Winner | Brad Beal Elite |
| Game format | Four 8-min quarters, EYBL 17U (32 min regulation) |
| Total offensive possessions by BBE | `57 logged` (chunk totals: 10 / 15 / 17 / 15) — **estimated ~60–62 actual** (chunk 0 flagged incomplete ~14–17 actual; chunk 2 missing 1 BLOB possession at Q3 3:22 → flagged as poss ~10.5). Use 57 as graded denominator; flag estimate ±5. |
| Total offensive possessions by opponent | Insufficient observation — TD possessions were not logged 1-for-1; only noteworthy defensive events were tracked. Rough parity with BBE (~58–62) inferable from score/pace but not traceable to the scratchpad. |
| Score progression | 0–0 (start) → BBE 11–4 (Q1 ~3:30) → BBE 21–14 (end Q1, inferred from chunk 1 start) → BBE 32–20 (Q2 4:14) → BBE 46–28 (halftime) → BBE 57–38 (Q3 2:49) → BBE 69–44 (end Q3) → BBE 78–53 (Q4 4:29) → BBE 87–57 (Q4 1:56) → BBE 91–59 (final) |
| Game shape | BBE led wire-to-wire. Briefly pressured early Q1 by TD transition scoring (3 transition dunks / layups in a row), then BBE switched to 1-2-2 press → 1-2-2 half-court zone starting Q2 5:39 and pulled away in Q3. Effectively decided by ~Q4 2:00 (TD "gave up" per scratchpad). |
| Date of game | 2025 Nike EYBL Peach Jam — Quarterfinals (exact date not captured in metadata) |
| Event | Nike EYBL Peach Jam 17U — Quarterfinals 2025 |
| Source film | `8fbd2dd2-0b98-4a2d-ae03-788312bea32d` |

---

## SECTION 2 — OFFENSE: SET AND ACTION INVENTORY

**Framing note:** BBE does not run a structured half-court set offense. Across 57 logged possessions, the overwhelming majority resolve into (a) transition pushes after defensive events, (b) 1-on-1 iso drives (especially by `#23 Andrews` left and `#2 Pearson` lefty), or (c) generic High PnR between `#2` and `#31` that is often declined. Designed half-court set plays are essentially absent from the inventory — possessions repeatedly log as "no set," "no action ran," "stagnant 5-out," or "4-out with ball-handler iso." **This is a finding about BBE, not a gap in observation.** The counts below reflect what actually happened on the floor; many possessions fall into the iso / no-set / transition bucket rather than a named set.

*Counts reconcile scratchpad language per §10a. Sorted by total occurrences descending. Totals are `[LIKELY]` at the exact count, `[CONFIRMED]` directionally — chunk 0 is incomplete (see §10b).*

### Action A: Iso / 5-out no-set (half-court 1-on-1)

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~18` (breakdown: chunk 0: `~3`, chunk 1: `~3`, chunk 2: `~6`, chunk 3: `~6`)
  - Representative possessions (subset, not exhaustive — full count is ~18): C0-6 (`Q1 3:30` #23 1-on-5 left iso), C0-9 (`Q1 1:43` #2 stagnant drive), C1-14 (`Q2 1:18` #22 post iso), C2-2 (`Q3 7:26` #23 SLOB iso), C2-7 (`Q3 4:52` #2 lefty drive), C2-11 (`Q3 2:48` #23 and-1), C2-17 (`Q3 0:12` #23 end-of-Q iso), C3-8 (`Q4 4:46` #22 iso 3), C3-11 (`Q4 2:55` #23 spin move), C3-13 (`Q4 1:47` #23 foul-draw), C3-15 (`Q4 0:46` clock-kill iso).
- **Primary initiator(s):** `#23 Andrews` (primary, always drives left — see §10f watch-item #3), `#2 Pearson` (secondary, lefty drives). `#22 White` occasionally iso'd on mismatches (C1 Q2 1:18, C3 Q4 4:46).
- **Primary screener(s):** None. When a screen is offered (typically by `#31`), the ball-handler frequently declines it (`C0-4` Q1 5:43 declined; `C3-9` Q4 4:21 declined → TO).
- **Typical floor position:** Initiated from either wing (#23 left side preferred, #2 left side preferred despite being lefty). 5-out or 4-out spacing with #31 at elbow or short corner.
- **Success rate:** `Mixed.` #23 iso = `~5 of 7 produced a good look` (rim finish, and-1, or drawn FT); #2 iso = `~3 of 4 produced a good look`; #22 iso = `0 of 2 produced a good look` (forced contested 3 C3-8, stripped on post-up C1-14). Overall iso possessions that scored OR drew fouls: `~10 of 18`.
- **Key counter (if taken away):** Offensive-rebound crashing. When iso shot misses, #22 / #23 / #31 / #1 crash boards for put-back attempts (3+ OREB → score sequences observed in C1 and C3).
- **Reconciliation note:** Per §10a, unified "no set," "no action ran," "stagnant 5-out," and "4-out with ball-handler iso" under this category. This is the dominant half-court mode, and keeping it as its own Action entry (rather than distributing to set-based categories that don't exist) is the honest representation.
- **Situational use:** Increases in frequency as the game progresses — fewer than half of Q1 possessions are pure iso, but the majority of Q3 and Q4 possessions default to this mode. Partially a function of garbage-time loose play (see §10e).

### Action B: Transition / push

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~16 opportunities / 7 scores` (breakdown: chunk 0: `2 opps / 1 score`, chunk 1: `4 / 1`, chunk 2: `4 / 2`, chunk 3: `3 / 3`). See §3 for full trigger/outcome breakdown.
  - Representative possessions: C0-5 (`Q1 4:06` push off missed TD FT), C0-10 (`Q1 1:13` 4-on-2 dunk), C1-10 (`Q2 2:57` push → kick-out 3), C2-13/14/16 (`Q3 1:38 / 1:17 / 0:49` chained pushes off DREBs), C3-5/12/14 (`Q4 5:56 / 2:20 / 1:12` transition scores).
- **Primary initiator(s):** `#2 Pearson` (length-of-court passing and tempo-setting); `#23 Andrews` (aggressive push after DREB or steal); `#10 Edwards` (secondary playmaker in transition — great transition pass C3 `Q4 2:20`).
- **Primary screener(s):** None. Transition is ahead-of-the-defense, no screen setup.
- **Typical floor position:** Start = DREB, steal, or missed TD FT. End = rim attack (typically #5, #23, #1, or #31 receiving outlet).
- **Success rate:** `~7 of 16 produced points`; additional trips drew fouls / FTs (C1-9, C1-11, C2-12, C2-13, C3-3 OREB → foul). Ballpark conversion rate `~44% scored, ~65% produced points or FTs`.
- **Key counter:** TD full-court press (ran in Q2 and portions of Q3–Q4) — forces BBE into press-break mode rather than pure push, which loops into Action D below.
- **Reconciliation note:** Unified "transition push," "push the ball," "outlet to ___ for layup," "steal → fast break" under one action.
- **Situational use:** Primary scoring mode after any defensive event. Increases in Q2 due to 1-2-2 press producing more steals + DREBs. High-efficiency mode relative to BBE's half-court offense.

### Action C: High PnR with #2 + #31 (or declined variant)

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~12 offered / ~8 used / ~4 declined-or-weak` (breakdown: chunk 0: `2 offered / 1 used (Q1 7:23) / 1 declined (Q1 5:43)`, chunk 1: `~6 offered / ~4 used / ~2 declined-or-weak (Q2 1:51 weak, Q2 0:31 unused)`, chunk 2: `~3 offered / ~3 used`, chunk 3: `~1 offered / 0 used / 1 declined (Q4 4:21)`).
  - Representative possessions: C0-2 (`Q1 7:23` quick PnR → #31 fumble TO), C0-4 (`Q1 5:43` declined → #2 pull-up 3 make), C1-5 (`Q2 5:25` PnR → tip-in OREB chain), C1-6 (`Q2 4:45` PnR → foul drawn), C1-12 (`Q2 1:51` weak PnR → TO), C2-5 (`Q3 5:47` motion → PnR miss), C2-8 (`Q3 4:27` PnR → kick-out miss), C2-10 (`Q3 3:38` double PnR #23+#31), C3-9 (`Q4 4:21` declined PnR → TO).
- **Primary initiator(s):** `#2 Pearson` (~70% of PnRs); `#1 Coleman` (C1-5, C1-6 with #31 and #10 screens respectively).
- **Primary screener(s):** `#31 Pearson` (primary — all but 2 of the PnRs); `#10 Edwards` set the screen in C1-6; `#23 Andrews` set the screen in C1-12 (without contact) and C2-10 (paired with #31).
- **Typical floor position:** Screen set above the arc, top-of-key or slightly to the strong side. Ball-handler drives off the screen and either pulls up, kicks, or drives to finish. #31 rolls hard when actually used.
- **Success rate:** `~4 of 7 used produced a good look` (score, FT, or clear paint touch). Declined / unused PnRs are tracked separately — `~3 declined` → typically turns into Action A (iso) on the same possession.
- **Key counter (if taken away):** Declined PnR → iso by #2 or #1. Actually observed (see C3-9 declined PnR → TO).
- **Reconciliation note:** Per §10a, unified "ball screen," "on-ball screen," "High PnR," "PnR" across all scratchpad language into this one action. The C1-12 "weak PnR" (no contact) and C3-9 "declined PnR" are counted in the `offered` column but not the `used` column.
- **Situational use:** BBE's primary half-court action, but used less than you'd expect — the ball-handler frequently just ignores it. Cleared off the board entirely in Q4 once BBE committed to zone and TD stopped running halfcourt sets (no BBE half-court PnR D to log in chunk 3).

### Action D: Press-break (two-guard back-and-forth with #2 + #23)

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `~8` (breakdown: chunk 0: `0`, chunk 1: `~1`, chunk 2: `4`, chunk 3: `4`).
  - C2: poss 1 (`Q3 7:42`), poss 3 (`Q3 6:56`), poss 6 (`Q3 5:18`), poss 15 (`Q3 1:08`).
  - C3: poss 2 (`Q4 6:58`), poss 3 (`Q4 6:33`), poss 4 (`Q4 6:12`), poss 7 (`Q4 5:01`).
- **Primary initiator(s):** `#2 Pearson` (primary handler, calm-under-pressure, long-distance passing). `#23 Andrews` (secondary handler, aggressor — will muscle through and attack).
- **Primary screener(s):** None — BBE's press-break is freelance two-guard handling, **not a designed set.** Explicitly noted in scratchpad chunks 2–3 ("no set besides giving it to #2 or #23 and figuring it out"). Occasional lone screen offer (C2-3 `Q3 6:56` #23 "set a ball screen" — really just popped out for the pass, no contact).
- **Typical floor position:** TD applies full-court or 3/4-court pressure. #2 and #23 handle the ball across the backcourt, typically with passes back-and-forth until one of them clears the pressure and attacks.
- **Success rate:** `~5 of 8 cleared pressure into a scoring / FT opportunity`; `3 of 8 resulted in TOs or failed possessions` (C2-15 `Q3 1:08` #5 bad pass → lost ball; C3-4 `Q4 6:12` #2 bad pass out of double team; C3-7 `Q4 5:01` off-ball foul halted play).
- **Key counter:** If you eliminate #2 from the ball (double-team him in the backcourt), BBE struggles. C3-4 `Q4 6:12` is the explicit example — double-team on inbound → #2 bad pass → TO.
- **Reconciliation note:** None — "press-break" was consistent language across scratchpad chunks.
- **Situational use:** Only deployed when TD pressed. TD's pressure increased late in each quarter / after BBE scores, so press-breaks cluster late in quarters. Ball-handler hierarchy (#2 primary, #23 secondary) is consistent.

### Action E: Vs zone — ball-swing + DHO or baseline runner

- **Confidence:** `[LIKELY]` (only 3 cleanly observed half-court vs-zone possessions; TD played mostly man-to-man so sample is small)
- **Total occurrences:** `3` (all in chunk 1 + 3)
  - C1-7 (`Q2 ~3:50`) — `#1` drives into 2-3 zone to collapse top, kicks to `#5` for open right-wing 3 (miss) → OREB.
  - C1-8 (`Q2 3:49`) — `#10` runs baseline behind the 2-3 zone for open paint look (miss) → OREB → `#31` put-back score.
  - C3-1 (`Q4 7:45`) — Ball-swing vs. zone, DHO right wing `#1` to `#22`, `#22` makes 3.
  - C3-10 (`Q4 3:52`) — 4-out 1-in vs. zone, DHO `#23`/`#2`, lob to `#31` post-up for and-1.
- **Primary initiator(s):** `#2 Pearson`, `#1 Coleman`, `#23 Andrews` — rotating depending on lineup.
- **Primary screener(s):** None in the traditional sense. DHO is the primary screening action; baseline runner is a movement action not a screen.
- **Typical floor position:** 4-out 1-in or 4-out with #31 at short corner / post. Ball-handler on wing, DHO to receiver, receiver either shoots or attacks gap.
- **Success rate:** `2 of 4 produced a good look that scored` (C3-1 #22 3pt make, C3-10 #31 and-1). The 2 C1 possessions missed the initial shot but extended via OREB.
- **Key counter:** None observed — TD played zone rarely against BBE, so counter-adjustments didn't come up.
- **Reconciliation note:** Unified "swing ball + DHO vs. zone," "baseline runner vs. zone," "4-out 1-in vs. zone → DHO → post lob" under one anti-zone action category. Structurally they share the same logic (collapse the zone, exploit the gap), just at different spots.
- **Situational use:** Only when TD plays zone. Small sample. If film 02 shows TD or another opponent playing zone, expect to see this action more often.

### Single-occurrence actions / variants (one-line each, listed for completeness)

*Not part of the repeating inventory, but observed. Tagging so TEX is neither penalized nor rewarded for catching them individually.*

- `C0-1 Q1 7:54` — Set play: pass + off-ball screens into skip-to-wing drive for `#23` FT trip. Structured opener, didn't repeat.
- `C0-3 Q1 6:58` — Flex screen → pin-down → skip → drive-and-kick 3 for `#2`. Complex, didn't repeat.
- `C0-7 Q1 ~3:15` — Box set (2 on elbows, 2 on blocks) — passed to `#22` at elbow, stolen. Didn't repeat.
- `C0-8 Q1 ~2:50` — **ATO**: Double on-ball screens + wing DHO. The only ATO with any structural design in the game. Didn't repeat.
- `C1-1 Q2 7:57` — Flex + motion → backdoor read by `#31` to `#1`. Didn't repeat (though some structural overlap with BLOB #1 in §4).
- `C1-4 Q2 6:02` — Stagger ball screens for `#2` — `#23` screens for `#31` who sets a ball screen for `#2`. Variant of Action C; didn't repeat exactly.
- `C2-10 Q3 3:38` — Double PnR (R + L screens) for `#2` from `#23` + `#31`. Variant of Action C; didn't repeat.

**Reminder on what's NOT here:** No Horns sets. No Spain PnR. No Flare screens. No Elevator. No Iverson cut. No named traditional set offense. TEX outputs that produce any of those terms from this film are hallucinating — see §10f watch-item #1.

---

## SECTION 3 — OFFENSE: TEMPO AND PACE

- **Primary tempo:** `mixed` — aggressive push on any rebound / steal / made TD FT; stagnant 5-out / iso in half-court when forced to set up. `[CONFIRMED]`
  - **Frequency evidence:** 13 transition opportunities logged across chunks (C0: 2, C1: 4, C2: 4, C3: 3), converting 7 transition scores (C0: 1, C1: 1, C2: 2, C3: 3). Note chunk 0 possessions are incomplete (10 logged of ~14–17 actual), so true transition rate is modestly understated. Transition offense outscored any single half-court "set" in every chunk.
  - Typical transition triggers: DREB + outlet to #2 or #23 (`Q3 1:38`, `Q3 1:17`, `Q3 0:49`, `Q4 1:12`), steal on 1-2-2 press (`Q2 5:39`, `Q2 7:17`), missed TD FT (`Q1 4:06`).
- **Average time to half-court action initiation:** `moderate` (6–12s) in half-court — most possessions involve a perimeter pass or two before either a declined PnR offer from #31 or a direct iso drive by #2 / #23. Rarely deliberate (>12s) except clock-kill situations.
- **Pace changes (situational):**
  - **#2 Pearson deliberately slows the game to close out quarters / kill clock** — confirmed at `Q2 0:31` (end of Q2), `Q4 1:47` (late-game clock management), `Q4 0:46` (end-of-game clock kill). `[CONFIRMED]`
  - **Q2 pace accelerates vs Q1** — BBE's switch to 1-2-2 press at `Q2 5:39` creates more steals + OREB second-chance possessions, adding ~2–3 extra possessions per game minute. `[LIKELY]`
  - **Q3–Q4 pace loosens once up 20+** — questionable shot selection and forced passes when game is decided (`Q4 5:56`, `Q4 5:33`, `Q4 4:46`). Tag these possessions as "garbage-time loose play" rather than base tempo. `[CONFIRMED]`
- **Confidence on tempo claims:** `[CONFIRMED]` overall. The "mixed tempo with transition emphasis after defensive events" finding is well-supported across all 4 chunks; the exact transition ratio is `[LIKELY]` due to chunk 0 under-logging.

---

## SECTION 4 — OFFENSE: OUT-OF-BOUNDS SETS

*BLOB = baseline out-of-bounds. SLOB = sideline out-of-bounds.*
*BBE's OOB "structure" is thin — they run motion/cross-screen looks that consistently devolve into "players move to spots rather than actually screen" (explicit team-level tendency confirmed in chunks 0, 1, 2). That said, there ARE two repeating structural patterns worth calling out, plus one single-occurrence box set.*

### BLOB #1: Cross-screen for guard cutter + post seal attempt by #31

- **Confidence:** `[CONFIRMED]`
- **Total occurrences:** `5` (breakdown: chunk 0: 0, chunk 1: 4, chunk 2: 1, chunk 3: 0)
  - `Q2 7:45` — post-seal score
  - `Q2 7:10` — cross-screen to corner 3
  - `Q2 1:45` — staggered cross-screen, bail-out 3 miss, rescued by OREB
  - `Q2 1:11` — cross-screen + lob-setup fake, rescued by OREB
  - `Q3 3:22` — box-set cut to L-corner for easy layup (variant)
- **Primary target (who's supposed to score):** `#1 Coleman` or `#23 Andrews` (guard cutting across baseline); `#31 Pearson` as secondary target sealing under basket.
- **Screeners:** `#22 White`, `#23 Andrews`, `#31 Pearson` — rotating, not fixed assignments.
- **Structural description:** Ball under own basket. Two players on blocks, one at elbow, one inbounder. Guard target (#1 or #23) uses a cross-screen (typically from #22 or #23/#1) to cut baseline-to-opposite-corner or baseline-to-opposite-wing. Simultaneously #31 tries to seal inside for a high-low feed. If first and second options are covered, bail-out pass to top-of-key (often #5) for a late-shot-clock jumper.
- **Success rate:** `5 of 5 possessions produced points`, but only `3 of 5 scored on the initial designed action` (Q2 7:45 #31 dunk, Q2 7:10 #1 corner 3, Q3 3:22 #23 layup). The other 2 relied on offensive-rebound put-backs (Q2 1:45 #22 put-back, Q2 1:11 #22 put-back) after the designed action failed. **Direct-action efficacy is moderate; overall possession conversion is inflated by BBE's board-crashing.**
- **Key counter (if taken away):** Bail-out pass to #5 at top / half-court for a forced jumper — this is their escape valve when the initial cross-screen is covered (`Q2 1:45`).
- **Reconciliation note:** Unified the "cross-screen / cutter-across-baseline" action across 5 chunks-1-and-2 BLOBs under one entry — all share the same structural skeleton (cutter uses screen to cross to opposite side; #31 seals). The Q3 3:22 "box set" is slightly distinct (no real screens, players switch spots + #23 cuts to block) and is listed here as a variant rather than separately; coach-draw-the-play description holds.
- **Situational use:** Primarily late-Q2 / end-of-half; one late-Q3 occurrence. No BLOBs drawn up in Q4 — chunk 3 end-of-game notes explicitly say "no BLOB / SLOB / ATO plays drawn up late."
- **Defensive tell (for scouting report consumer):** Be physical at the cut — BBE screeners rarely make real contact, so a defender who fights through the "screen" disrupts this action cleanly. Noted 3 separate times in the scratchpad as "easy to defend: be physical, push them through."

### BLOB #2: Direct feed / post-up to #31

- **Confidence:** `[SINGLE GAME SIGNAL]` (1 occurrence in notes)
- **Total occurrences:** `1` (`Q3 4:13`)
- **Primary target:** `#31 Pearson` (post-up on block)
- **Screeners:** None — 3 players across baseline, no real screening action.
- **Structural description:** Inbounder throws a post-entry pass to #31 on the block. #31 attempts to catch and attack immediately from the post. No setup action. Relies entirely on whether #31 can establish deep position.
- **Success rate:** `0 of 1 on initial action` — #31 caught off-balance, forced a bad shot, missed. OREB by #23 extended possession; outcome of extended play unclear (flagged in notes).
- **Reconciliation note:** Kept separate from BLOB #1 despite both involving #31 — structurally the action is different (direct feed vs. seal-as-counter-to-cross-screen). Re-evaluate after film 02 if this shows up again.
- **Situational use:** Single observation mid-Q3. Not a base BLOB.
- **Defensive tell:** #31 is easily moved off his post spot (confirmed independently in chunk 1 notes + chunk 2 post-feed observation) — deny the catch and he can't score from the post.

### SLOB #1: Double-stagger screen for #1 pop / #23 flash

- **Confidence:** `[LIKELY]` (2 SLOB observations + explicit scratchpad claim "they run this set on almost every SLOB"; actual logged repetitions = 1 structured + 1 degenerate)
- **Total occurrences:** `2 logged` — `Q3 7:29` (structured — setup only, no shot on the SLOB itself), `Q3 7:10` (degenerate — quick inbound to #23 for an airball 3, no actual action ran).
- **Primary target:** `#1 Coleman` (primary — comes off the double screen to pop / flash); `#23 Andrews` (secondary / flash option).
- **Screeners:** `#31 Pearson` + `#23 Andrews` (double stagger).
- **Structural description:** Box-set baseline alignment, inbounder on the sideline. #1 starts on a block, cuts off a stagger of #31 then #23, **looks like he's going far L for a catch-and-shoot, then stops and pops out short**; #23 flashes L off the same action. Often the shot never comes — it's a setup action into their half-court offense, not a direct scoring play.
- **Success rate:** `0 of 2 produced a shot on the SLOB action itself`. One setup led to generic half-court offense; the other (degenerate) produced a low-quality #23 airball 3.
- **Key counter:** None observed — TD didn't actively take this away because it rarely produced a shot directly.
- **Reconciliation note:** The scratchpad's explicit "they run this set on almost every SLOB" outpaces the literal count (1 clean observation). Tagging `[LIKELY]` instead of `[CONFIRMED]` because the counted occurrences only marginally support the stronger claim. If film 02 or film 03 shows the same alignment, upgrade to `[CONFIRMED]`.
- **Situational use:** Observed in chunk 2 only (Q3). No SLOBs in the scratchpad for Q1 or Q4.
- **Defensive tell:** Same as BLOB #1 — the stagger screens rarely make contact; physical fight-through disrupts the action.

### Single-occurrence OOB actions

*Logged but not part of a repeating structure:*

- `Q2 4:39` — SLOB, BBE, simple inbound to #5 at half-court with no play ran. Pure get-in-bounds execution.
- `Q1 5:17` — BLOB by TD (not BBE offensive possession); logged for defensive context (BBE #23 poke-away forced SCV).

*Noting: BBE ran NO ATO sets with repeating structure — the one ATO logged (`Q1 ~2:50`, poss 8) was a double-on-ball-screen DHO action that only appeared once and was described as "lazy screens, #2/#31 switching instead of screening." Single-occurrence; not a base structure.*

---

## SECTION 5 — OFFENSE: LATE-GAME (final 8 minutes of close games)

- **Close late?** `NO` — BBE won 91–59 (+32), led wire-to-wire. Lead was 25+ from Q3 2:49 onward; game was effectively decided by ~Q4 2:00 per scratchpad ("TD had given up at this point").
- **Late-game tendencies — GAME NOT CLOSE.** Under a normal "final 8 minutes of close games" read, this section would be marked `insufficient observation`. However, per our grading discipline and because chunk 3 has a dedicated "End-of-game execution" subsection, what BBE DID run in the final 2:00 is captured here for contrast — with the explicit caveat that **these are not close-game tendencies; they are blowout-protection / clock-kill behaviors and should be tagged as such in TEX's output.**

### What BBE actually ran in the final 2:00 (blowout protection, NOT close-game execution)

- **Primary mode: transition pushes + 5-out iso / 1-on-1 ball + clock-kill.** No half-court sets drawn up. Explicit scratchpad quote: "No BLOB / SLOB / ATO plays drawn up late — BBE trusts the zone and transition to close the game."
- **Possession breakdown for the final 2:00** (3 possessions total):
  - `Q4 1:47` — 5-out iso / clock management. #2 slows the game, swings to #23 who drives left and draws a foul → FT trip.
  - `Q4 1:12` — Transition. #31 DREB → long outlet to #2 streaking down court wide open → dunk. Pure transition, no offense run. TD had disengaged.
  - `Q4 0:46` — 5-out clock-kill. #2 dribbles out the shot clock, eventually takes a forced shot → miss. No play call.
- **Primary ball-handler in clutch / clock-kill:** `#2 Pearson` — operated every end-of-game possession as the primary (confirmed earlier in Q2 0:31 end-of-quarter too).
- **Primary scorer / foul-drawer when a bucket is needed:** `#23 Andrews` — drives left, initiates contact, gets the call (`Q4 1:47`).
- **Primary rebounder / outlet:** `#31 Pearson` — DREB → outlet pass to streaking guard (`Q4 1:12`).

### What IS observable about actual late-game execution (game not close, so take with appropriate caution)

- **Shot clock offense (under 8 seconds):** Insufficient observation at normal end-of-close-game state. Related data point: `Q2 1:45` BLOB had an 8-second bail-out situation that resolved into #5 forcing a 3 → OREB → put-back. **This bail-out (guard at top / half-court takes a contested 3) is BBE's only observed late-clock pattern, and it's not specific to end-of-game.** Confidence: `[SINGLE GAME SIGNAL]`.
- **Scheme changes when protecting lead:** `YES, defensively.` BBE introduced the 1-2-2 press → 1-2-2 half-court zone at `Q2 5:39` (up 21–14) and **rode it to the final buzzer without reverting to man-to-man, even as TD started figuring it out in late Q3 and early Q4.** This is a protecting-lead scheme posture. `[CONFIRMED]`
- **Scheme changes when trailing:** Insufficient observation — BBE was never trailing after the opening minutes. `[NOT OBSERVED]`
- **Confidence on late-game tendencies:** The *blowout* late-game mode is `[CONFIRMED]` (transition + iso + clock-kill, no plays drawn up). The *close-game* late-game mode is `[NOT OBSERVED]` and should be flagged in the grading rubric — any TEX output that makes confident close-game-late claims from film 01 is hallucinating, because the game doesn't support them.

---

## SECTION 6 — DEFENSE: BASE SCHEME

- **Primary defense:** `mixed` — BBE ran two distinct base schemes across the game: **pure man-to-man for all of Q1**, then **1-2-2 full-court press → 1-2-2 half-court zone** starting `Q2 5:39` and running as the base through the final buzzer. The two schemes are unified in §10a as a single scheme family ("1-2-2 press-to-zone") because personnel and shape extend continuously from full-court to half-court. `[CONFIRMED]`
- **Percentage of possessions (approximate):** Man-to-man `~30%` / 1-2-2 press-to-zone `~70%`. Skewed heavily toward zone in the second half — Q3 and Q4 were essentially 100% zone (no return to man even when TD started exploiting gaps).
- **Scheme changes — timeline:**
  - **Q1 8:00 → Q2 5:39 (pure man-to-man).** Good overall ball pressure, verbal communication (C0 `Q1 2:29` #2 visibly calling out back screen). Specific failures: `Q1 5:26` #31 over-hedge on unused screen; `Q1 4:17` #31 poor pick-n-pop close-out → foul; `Q1 3:56` + `Q1 3:39` transition give-ups (3 straight TD transition scores before BBE timeout at `Q1 3:30`).
  - **Q2 5:39 (first 1-2-2 appearance).** 1-2-2 full-court press with #10 at top, #1 top-right, #5 top-left, #23 bot-left, #31 bot-right → swings to half-court 1-2-2 zone. First deployment produced a steal by #1 → transition score.
  - **Q2 5:39 → Q2 end (mixed / lineup-dependent).** BBE oscillated between 1-2-2 and man based on who was on the floor. Explicit observation at `Q2 2:37`: "Switched back to man-to-man when #2 re-entered the game." And `Q2 2:26`: "Back to 1-2-2 press on next defensive possession with #2 in game, then fell back into man." Flag per §10e — this Q2 oscillation is not a durable pattern; it's a transition window, not a settled scheme.
  - **Q3 7:44 → Q4 0:00 (pure 1-2-2 press-to-zone).** Base scheme for the entire second half. No return to man-to-man at any point in Q3 or Q4, even as TD began finding the middle of the zone (`Q3 1:33`, `Q3 0:37`, `Q4 4:44`) and even after going up 25+. BBE "trusts the zone enough to ride it to the final buzzer" per scratchpad.
- **Pressure level:**
  - In man (Q1): `pressure` — good on-ball pressure, 3/4-court pickup at times (C0 `Q1 2:29` #1 picked up 3/4-court).
  - In 1-2-2 press (Q2–Q4): `pressure` — active ball pressure at the top of the press, forcing passes; bottom 2 defenders tended to play loose / soft or get out of position.
- **Off-ball positioning:**
  - In man: `deny / gap` — mixed; #23 actively denied post at `Q1 5:17` (poked ball away → TD SCV); help-side rotations were generally active (#1 help-side steal at `Q1 2:09`, #23 weak-side steal at `Q1 2:09`).
  - In zone: zone spacing — bottom 2 defenders cover the blocks and bump to corners; top defender pressures ball; middle is the known exposure (see §10f watch-item #6).
- **Post defense:** **Insufficient observation.** TD's post game wasn't a feature of their offense in the logged possessions — no BBE post-front / 3-quarter / behind-post patterns consistently documented. Tag as `[NOT OBSERVED]` for TEX grading.
- **Transition defense:**
  - **Sprint back or retreat?:** **Weak in Q1 — explicit problem.** 3 TD transition scores allowed in Q1 (`Q1 7:10`, `Q1 3:56`, `Q1 3:39`), each converted. Scratchpad notes "no BBE players on the opposite side of the court while TD had 3 (players attacking)." Improved once BBE switched to zone — fewer transition chances allowed because the press slowed TD's outlets.
  - **Primary back-defender (who trails the break):** Insufficient observation — scratchpad doesn't systematically identify which BBE player consistently trails the break. `[NOT OBSERVED]` at the player level.
  - **Transition baskets allowed:** `~6 total whole-game` (C0: 3, C1: 1 zone breakdown at `Q2 4:14` #31 missed assignment, C2: 1 dunk in middle of zone `Q3 3:01`, C3: 1 baseline drive `Q4 4:44`). C0 transition-D collapse is the standout game-level weakness that triggered the scheme switch.
- **Confidence:** `[CONFIRMED]` for the two-scheme framing and the timeline breakpoints. `[CONFIRMED]` for "zone is the base for Q3–Q4." `[LIKELY]` for exact snap-share percentages (derived from quarter-level observations, not counted per possession). `[NOT OBSERVED]` for post defense and named back-defender.

---

## SECTION 7 — DEFENSE: BALL SCREEN COVERAGE

- **Primary coverage:** `switch` — with `hedge` as the secondary coverage. `[CONFIRMED]`
- **Frequency (of 9 logged PnR defensive possessions across chunks 0–2):**
  - `switch` — **6 of 9** (`~67%`): C0 `Q1 4:17`, C0 `Q1 1:24`, C1 `Q2 7:00`, C1 `Q2 0:58`, C1 `Q2 0:48`, C2 `Q3 4:37`.
  - `hedge` — **2 of 9** (`~22%`): C0 `Q1 5:26`, C0 `Q1 2:09`. Both with `#31` as screen defender.
  - `no coverage / weak` — **1 of 9** (`~11%`): C2 `Q3 7:03` — no switch/help/hedge; ball defender #2 got around the screen anyway, but TD drove to a foul.
  - No `drop`, `ICE`, `blitz`, or `show` coverages observed across any chunk.
- **Coverage timeline (did it change during game?):**
  - **Q1:** Mixed within man — hedge (#31 as screen defender) and switch both deployed. 2 hedges + 2 switches + some unlabeled ball-screen defense.
  - **Q2:** Pure switch on every logged PnR (3 of 3 in chunk 1). This shift coincides with BBE's growing commitment to zone — switches are compatible with the transition into 1-2-2 principles.
  - **Q3:** Switch + one no-coverage breakdown (2 logged).
  - **Q4:** **No PnR defense logged — zone took PnR off the table entirely.** TD couldn't run traditional ball screens against the 1-2-2 half-court zone, so the coverage inventory for Q4 is `not applicable`. Explicit note in scratchpad chunk 3.
- **Coverage by personnel:**
  - **#31 Pearson** is the screen defender in `~7 of 9` logged PnR possessions. He is the primary PnR screen defender when on the floor, and the primary target for attackers — see §10f watch-item #4.
  - **#23 Andrews** was screen defender once (C0 `Q1 4:17` switch → got caught on the screen → foul drawn on BBE).
  - Ball defender was usually `#2` (6 of 9) or `#1` (2 of 9). One possession had `#23` as ball defender (C1 `Q2 0:58`).
  - **No observable "when X is in, we drop; when Y is in, we switch" lineup pattern** — switches were the default when any personnel were on the floor. This departs from typical scouting reports that tie coverage to screen-defender size.
- **Execution quality (where does it break down?):**
  - **Switches attacked on the perimeter:** When TD exploits a switch and drives / splits past `#31`, BBE gives up good looks. Confirmed at C1 `Q2 7:00` (ball-handler drove past #31 → help over-rotated by #10 → open 3 and make), C1 `Q2 0:48` (drive past #31 guarding ball, ball knocked loose by help but #31 was beat), C2 `Q3 4:37` (#31 got split for easy drive and lob). **#31 on switches to the perimeter is THE exploitable coverage matchup.**
  - **Hedges that over-extend:** `#31` over-hedges on screens even when not needed. C0 `Q1 5:26` is the explicit example — screen was never actually used, `#31` over-hedged anyway, allowing a pass back to the popping screener. One high-quality hedge: C0 `Q1 2:09` (`#31` great hedge → `#23` weak-side steal → BBE transition layup), so the hedge isn't systematically bad — just inconsistent.
  - **Pick-n-pop close-outs:** Separate from pure PnR but related. C0 `Q1 4:17` — TD ran pick-n-pop, `#31` forced to close out on the popping wing after `#23` got screened, got blown by → foul. Documented as a distinct close-out weakness (see §8).
  - **Overall breakdown rate:** `~5 of 9 logged PnR possessions` resulted in a BBE-negative outcome (score allowed, foul, or driving paint touch). Roughly 50/50 execution — not catastrophic, but with clearly repeatable exploitable spots at the #31 screen-defender position.
- **Confidence:** `[CONFIRMED]` for primary coverage being switch, for #31 being the exploitable target, and for the hedge-as-secondary pattern. `[LIKELY]` for the exact percentages given the small PnR sample (9 possessions) and the fact that PnR defense drops off the board entirely in Q4. `[SINGLE GAME SIGNAL]` on the fact that BBE shows NO drop coverage across the whole film — opposing bigs who are strong pop / pick-and-pop shooters would meaningfully test this sample size.

---

## SECTION 8 — DEFENSE: INDIVIDUAL DEFENSIVE TENDENCIES

*One block per BBE player with significant defensive minutes. Most players appeared in all 4 chunks; defensive snap counts are not precisely tracked but the rotation-minute pattern in film_watch_notes.md gives rough denominators.*

### #2 — Trey Pearson

- **Primary defensive assignment:** TD's primary ball-handler / PG when BBE is in man; top of the 1-2-2 press when BBE is in zone. Rotates into the "point" role of the press on most possessions.
- **On-ball quality:** `[CONFIRMED]` **strong.** Recovered cleanly off hedges (`Q1 2:09`), stripped TD possessions (`Q2 7:17` steal → transition assist; `Q1 2:29` steal → transition layup), fought through down-screens to generate steals. Generally keeps ball-handler in front.
- **Help activity:** `active`. Vocal — visibly called out screens for teammates (`Q1 2:29` audible back-screen call for `#22`). Helps off-ball in man; pressures the entry pass at the top of the 1-2-2 press.
- **Identified weakness:** None observed on defense. His on-ball defense does not break down in any logged possession.
- **Confidence:** `[CONFIRMED]` strong overall. Defensive IQ + communication is arguably his most under-valued skill.

### #23 — JJ Andrews

- **Primary defensive assignment:** Wing in man; bottom-corner or wing of the 1-2-2 zone. Occasionally posts up smaller defenders defensively.
- **On-ball quality:** `[LIKELY]` **average, with high activity.** Got caught on screens twice (`Q1 4:17` picked by TD #12 on pick-n-pop action). But active hands and disruption — poked ball free on BLOB post (`Q1 5:17` → TD SCV), weak-side steal (`Q1 2:09` → BBE transition layup).
- **Help activity:** `active`. Weak-side / help-side steals logged (`Q1 2:09`). Crashes the defensive glass.
- **Identified weakness:** Gets caught on well-set off-ball screens (`Q1 4:17`). Not a consistent man-defender on wing pick-and-pop actions. Only 1–2 observations — `[SINGLE GAME SIGNAL]` on this specific weakness; may not replicate.
- **Confidence:** `[CONFIRMED]` for activity / help side; `[LIKELY]` for average man-defense quality.

### #31 — Sheek Pearson

- **Primary defensive assignment:** **Primary PnR screen defender.** Rim-protector when BBE is in man. Bottom of the 1-2-2 zone when in press (bot-left or bot-right). Post defender on TD's posts.
- **On-ball quality (PnR specifically):** `[CONFIRMED]` **liability.** Five independent negative PnR-defense possessions: `Q1 5:26` over-hedge on unused screen; `Q1 4:17` poor pick-n-pop close-out; `Q3 7:03` no help on screen; `Q3 4:37` split on switch; `Q2 0:48` + `Q2 0:58` + `Q2 7:00` all show him getting beat on perimeter switches. **One positive counterexample:** `Q1 2:09` great hedge → steal on the pass. Net: 1 clearly positive PnR action vs. 5+ clearly negative.
- **Help activity:** `passive` on closeouts specifically — closes out late and short, allows TD bigs to step into shots or drives. Missed zone assignment at `Q2 4:14` (left TD cutter wide open under basket → easy layup) — **positional discipline in the zone is a separate issue from PnR defense.**
- **Identified weaknesses (multiple):**
  - **Perimeter switches** — gets attacked repeatedly on switches to the wing or top of the key. Cannot guard opposing guards 1-on-1. Opposing team should seek switches onto `#31`.
  - **Pick-n-pop close-outs** — blown by at `Q1 4:17`, caused foul.
  - **Over-hedging unnecessarily** — creates 4-on-3 help situations that BBE can't cover.
  - **Zone discipline** — left a cutter open under the basket at `Q2 4:14` (top-of-zone confusion).
- **Confidence:** `[CONFIRMED]` PnR liability. `[CONFIRMED]` exploitable on perimeter switches. `[LIKELY]` inconsistent hedge quality (sometimes great, mostly bad).

### #1 — Quentin Coleman

- **Primary defensive assignment:** Helper / rotation guard in man. Top or top-wing in the 1-2-2 press. Picks up 3/4-court on select possessions.
- **On-ball quality:** `[LIKELY]` **above average.** Picked up 3/4-court at `Q1 2:29` and turned his man twice. Active ball pressure.
- **Help activity:** `active`. Help-side steal at `Q2 5:39` (read pass into paint during 1-2-2 press initial deployment → steal). Help-side tag on back-screen sequence (`Q1 2:29` tagged the screen recipient to slow him down).
- **Identified weakness:** None specifically called out in the scratchpad defensive sections. Sample is smaller than #2's — `[NOT OBSERVED]` for specific defensive breakdowns attributable to #1.
- **Confidence:** `[LIKELY]` for above-average defense based on 2–3 positive signals; not enough to promote to `[CONFIRMED]`.

### #22 — Jamison White

- **Primary defensive assignment:** Wing / forward matchups in man. Bottom corners / wings of the 1-2-2 zone. Guards TD's forwards.
- **On-ball quality:** `[LIKELY]` **average.** Limited specific on-ball observations. Avoided a back screen cleanly at `Q1 2:29` (aided by #2's verbal comm, but #22 did the physical avoidance).
- **Help activity:** `active` on the glass — contests shots and crashes defensive boards. On rotations, one specific failure logged: `Q1 ~3:15` failed to seal his defender on an elbow catch → TD steal (this was ostensibly an offensive breakdown but included in defensive context since the defender's positioning contributed).
- **Identified weakness:** **Brief exit at `Q1 7:40`** after face contact on #23's drive — not a skill weakness but a note on durability / availability. Returned to play.
- **Confidence:** `[LIKELY]` average overall; too few on-ball possessions explicitly logged to say more.

### #5 — Cam Blivens

- **Primary defensive assignment:** Rotation guard. Right-side wing of the 1-2-2 press (most possessions). Man-to-man assignments rotated.
- **On-ball quality:** **Insufficient observation.** Scratchpad defensive sections don't break out #5's individual matchups with specific counts.
- **Help activity:** Participated in 1-2-2 press rotations. No specific help-side events attributed to him.
- **Identified weakness:** Not observable from the scratchpad. Will be visible in a press-break / zone-breakdown film cut, but not separately logged here.
- **Confidence:** `[NOT OBSERVED]` at the individual-defender level. Flag for future films.

### #10 — Ty Edwards

- **Primary defensive assignment:** Rotation guard. Top or top-side wing of the 1-2-2 press. Man-to-man on TD wings when in man.
- **On-ball quality:** **Insufficient observation** — no specific on-ball matchups logged.
- **Help activity:** Participated in press rotations from `Q2 7:45` onward. **One specific negative observation:** `Q2 7:00` he "over-helped" when `#31` had the ball screen covered → TD kicked out to an open 3 for a make. Over-helping is a definable tendency worth flagging, though based on 1 observation it's `[SINGLE GAME SIGNAL]`.
- **Identified weakness:** Over-helping on already-contained actions. Single observation only.
- **Confidence:** `[SINGLE GAME SIGNAL]` over-help; otherwise `[NOT OBSERVED]`.

### Summary — team-level defensive tendencies

- **Attack #31 on PnR / switches.** This is the single most actionable defensive scouting tip derivable from film 01. `[CONFIRMED]`
- **Attack the middle of the 1-2-2 zone (high-post / free-throw line).** TD failed to consistently exploit it but the opportunity was there 4+ times. `[CONFIRMED]`
- **BBE close-outs are generally poor team-wide** — specifically in zone. Multiple scratchpad observations across Q3 and Q4 ("bad close-outs"). `[CONFIRMED]`
- **BBE transition defense is weak in man, better in zone** — Q1 bleeding transition scores was the proximate reason for the scheme switch. `[CONFIRMED]`

---

## SECTION 9 — INDIVIDUAL PLAYER CONSOLIDATED PROFILES

*Fill in one block per BBE player with 10+ observed offensive possessions. This is the
foundation for the "Player Pages" section of the final report (Section 4 of the report).*

### #1 — Quentin Coleman (seeded PG, 6'3", 2026)

- **Total possessions observed:** `~40` (breakdown by chunk: ~10 / ~10 / ~12 / ~8). Appeared in a majority of lineups but subbed out in late Q4 for #10/#2.
- **Confirmed position from film:** `SG / secondary PG` — **not the primary PG** despite seeded position. Update roster position flag in §10a.
- **Confirmed dominant hand from film:** **Insufficient observation** — hand dominance not clearly established in scratchpad across 4 chunks. `[NOT OBSERVED]` — flag for rewatch or future films.
- **Confirmed role:** `secondary_handler`
- **Offensive role (specific):** Secondary ball-handler; participates in press-break rotations but #2 leads most presses; occasional shooter on set plays (BLOB cross-screen cuts); transition passer.
- **Scoring zones with frequency:**
  - Rim: `0 of 0` — no rim attempts logged. (`Q1 1:13` transition play was a pass to #31 for the dunk, attributed as an assist not a shot.)
  - Paint (non-rim): `0 of 0` observed attempts.
  - Mid-range: `0 of 0` observed.
  - 3pt: `1 of 1` RIGHT corner (`Q2 7:10` BLOB cross-screen → catch and shoot make). **Only 3pt attempt logged.**
  - FT attempts: None explicitly logged for #1.
- **Shot chart location summary:** Extremely low-volume shooter — 1 field goal attempt logged all game (the BLOB 3). Not a scoring-first player. Primary contribution is ball-advancement + transition passing.
- **Key tendencies (each tagged with confidence + count):**
  - Hits spot-up 3s off BLOB cross-screens `[SINGLE GAME SIGNAL]` (1 of 1).
  - Occasional shaky decisions under pressure `[LIKELY]` (`Q1 ~2:50` ATO pressured hard, struggled getting ball upcourt; `Q2 7:17` passed up a wide-open layup in transition to #10 → nearly stolen; `Q3 1:08` dropped a pass that should have been caught).
  - Crashes offensive boards `[LIKELY]` (`Q3 7:42` OREB → jumpball).
  - Great transition passer `[SINGLE GAME SIGNAL]` (`Q1 1:13` perfect pass to #31 for dunk).
- **Defensive assignment:** Help-side / rotation guard in man; top or wing of 1-2-2 press. Specific help-side steal at `Q2 5:39`.
- **Defensive vulnerability:** Not observed. Too few on-ball matchups explicitly logged.
- **Free throw shooting observed:** `0 of 0` (no FT trips attributed).
- **Turnovers:** `0` directly attributable (the `Q3 1:08` dropped pass was #5's bad throw, not #1's TO; the `Q2 7:17` near-steal ended OOB with TD touching last per scratchpad).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 1:13` — transition pass to #31 for dunk.
  - `C0 · Q1 6:58` — initiated flex + pin-down set → kick-out 3 for #2.
  - `C1 · Q2 7:10` — BLOB catch-and-shoot 3 make (right corner).
  - `C1 · Q2 5:39` — help-side steal on 1-2-2 press deployment.
  - `C2 · Q3 7:42` — OREB on missed #22 3 leading to jumpball.

### #2 — Trey Pearson (seeded PG, 6'3", 2026) — **the real PG**

- **Total possessions observed:** `~50` (breakdown by chunk: ~10 / ~13 / ~15 / ~12). Played the highest minutes in the rotation — rarely off the floor, and scheme oscillation in Q2 was explicitly tied to his sub pattern.
- **Confirmed position from film:** `PG` — **primary ball-handler confirmed.**
- **Confirmed dominant hand from film:** `LEFT` — `[CONFIRMED]` across all 4 chunks.
  - **Evidence:** Lefty pull-up 3 (`Q1 6:58` make, left top of key), lefty pull-up 3 (`Q1 5:43` right-side PU, ball in left hand), lefty contested layup in traffic (`Q3 4:52`), lefty drives (multiple iso possessions).
- **Confirmed role:** `primary_initiator`
- **Offensive role (specific):** De-facto point guard. Initiates most half-court possessions. Primary press-breaker. Floor leader — slows game deliberately to manage clock at end of quarters. Clutch operator on every clock-kill possession. Scoring threat from 3 and off drives.
- **Scoring zones with frequency:**
  - Rim: `~3 of ~4` — `Q1 1:43` layup (`make`), `Q3 4:52` tough contested lefty layup (`make`), `Q4 1:12` transition dunk (`make`), `Q4 0:46` clock-kill attempt (`miss`).
  - Paint (non-rim): `0 observed`.
  - Mid-range: `0 of 1` — `Q3 5:47` PU miss (mid-range pull-up).
  - 3pt: `2 of ~4` — `Q1 6:58` LEFT top-of-key (make), `Q1 5:43` RIGHT-side PU (make), other attempts missed (e.g. `Q3 0:12` end-of-Q3 miss off #23 kick-out).
  - FT attempts: `~2+ trips` (`Q3 2:12` foul drawn; more likely during press-break).
- **Shot chart location summary:** Multi-level scorer. Can pull up from 3, drive-and-finish with his left hand, and make tough contested shots through contact. Not a primary catch-and-shoot player; most makes come off his own creation.
- **Key tendencies (each tagged with confidence + count):**
  - LEFT-handed shooter / finisher `[CONFIRMED]` (multiple observations all 4 chunks).
  - **Prefers starting on the LEFT side of the floor despite being lefty** `[CONFIRMED]` (`Q1 1:43`, `Q2 7:57` — explicit; see §10d).
  - **Slows the game to kill clock** `[CONFIRMED]` (`Q2 0:31`, `Q4 1:47`, `Q4 0:46` — 3 separate end-of-period occurrences).
  - Calm under pressure `[CONFIRMED]` (clean press-break handling `Q3 6:56`, `Q3 1:08`, `Q4 6:58`).
  - Vocal defensive leader — visibly calls out screens `[CONFIRMED]` (`Q1 2:29` back-screen call-out for #22).
  - Occasional lazy chest passes lead to TOs `[LIKELY]` (`Q1 ~3:15` poss 7 elbow-pass steal → TD layup; `Q4 6:12` bad pass out of double-team → TO).
  - Will decline offered PnR screens to go iso `[LIKELY]` (`Q1 1:43`, `Q3 5:47`, `Q4 4:21`).
- **Defensive assignment:** Primary on-ball defender for TD's PG in man. Top / "point" of the 1-2-2 press in zone.
- **Defensive vulnerability:** Not observed. On-ball defense does not break down in any logged possession.
- **Free throw shooting observed:** **Insufficient observation** — scratchpad doesn't break out FT makes per player; one specific FT trip logged (`Q3 2:12` foul drawn, makes not counted).
- **Turnovers:** `~3` attributable (`Q1 ~3:15` elbow-pass steal; `Q3 1:08` note — actually #5 bad pass; `Q4 6:12` bad pass out of double team; `Q4 4:21` declined-PnR TO). **~3 cleanly on #2 (Q1 ~3:15, Q4 6:12, Q4 4:21).**
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 6:58` — LEFT top-of-key 3 make off drive-and-kick.
  - `C0 · Q1 5:43` — RIGHT-side pull-up 3 make.
  - `C0 · Q1 2:29` — audible back-screen call-out for #22 + subsequent steal → transition layup.
  - `C1 · Q2 7:17` — full-court steal → transition creation.
  - `C1 · Q2 2:57` — pushed ball, found #23 trailer, #23 to #5 open corner 3 (make).
  - `C2 · Q3 4:52` — tough 1-on-1 contested lefty layup.
  - `C3 · Q4 1:12` — wide-open transition dunk off #31 outlet.
  - `C3 · Q4 6:58` — calm length-of-court pass breaking press.

### #5 — Cam Blivens (seeded PG, 6'2", 2026)

- **Total possessions observed:** `~25` (breakdown: ~5 / ~6 / ~6 / ~8). Rotational minutes, with increased usage in Q4.
- **Confirmed position from film:** `SG` / combo guard.
- **Confirmed dominant hand from film:** `LEFT` — `[LIKELY]` based on `Q4 6:58` scratchpad note ("#5 is lefty too"). Fewer explicit handedness observations than #2 / #23 / #10.
- **Confirmed role:** `role_player` / transition finisher.
- **Offensive role (specific):** Rotation guard — subs for #2 or #22. Transition finisher; receives full-court outlet passes. Occasional catch-and-shoot corner threat. Helps handle the ball against press.
- **Scoring zones with frequency:**
  - Rim: `1 of 2` — `Q4 5:56` and-1 layup (make + foul); `Q4 6:58` open transition layup (miss after open look — at-rim attempt, mis-bucketed in earlier pass).
  - Paint (non-rim): `0 of 0`.
  - Mid-range: `0 of 0`.
  - 3pt: `1 of 2` — `Q2 2:57` LEFT corner make off transition kick-out; `Q2 1:45` forced contested 3 on BLOB bail-out (miss → rescued by OREB).
  - FT attempts: `Q2 2:35` trip (makes not logged).
- **Shot chart location summary:** Low volume. Spot-up left-corner 3, rim finishes off cuts and transition.
- **Key tendencies (each tagged with confidence + count):**
  - Receives full-court passes in transition `[LIKELY]` (`Q4 5:56`, `Q4 6:58`).
  - Wild / low-efficiency passes when pressured `[LIKELY]` (`Q3 1:08` bad full-court throw → TO — though attribution is mixed since #1 "should have caught it"; `Q4 5:56` "one-arm football pass" before cutting).
  - Cuts hard to basket after making outlet passes `[SINGLE GAME SIGNAL]` (`Q4 5:56`).
- **Defensive assignment:** 1-2-2 press right-side wing; man-to-man rotations when in.
- **Defensive vulnerability:** **Insufficient observation** at individual-matchup level.
- **Free throw shooting observed:** At least 1 trip (`Q2 2:35`), makes not separated.
- **Turnovers:** `~1` (`Q3 1:08` bad press-break pass — arguably should have been caught by #1; attribution fuzzy).
- **Notable plays (timestamps for the grading UI):**
  - `C1 · Q2 2:57` — left-corner 3 make off #23 kick-out.
  - `C1 · Q2 2:35` — FT trip from transition layup.
  - `C3 · Q4 5:56` — and-1 layup.

### #10 — Ty Edwards (seeded PG, 6'5", 2026)

- **Total possessions observed:** `~25` (breakdown: `0 / ~8 / ~10 / ~7`). **Did not appear in chunk 0** — subbed in at `Q2 7:45` for #22 and played heavy rotation minutes thereafter.
- **Confirmed position from film:** `SG / Wing`.
- **Confirmed dominant hand from film:** `LEFT` — `[CONFIRMED]` (`Q2 6:42` explicit lefty drive + floater; reconfirmed across later chunks).
- **Confirmed role:** `secondary_scorer` / `playmaker`.
- **Offensive role (specific):** Sleeper scorer and secondary playmaker. Hits tough shots, uses body well on drives, makes the right transition pass. Called out in scratchpad as "don't sleep on him."
- **Scoring zones with frequency:**
  - Rim: `1 of 1` + OREB — `Q2 6:42` left drive → floater miss → own OREB → finish.
  - Paint (non-rim): `0 of 1` — `Q2 3:49` baseline runner open look behind zone (miss).
  - Mid-range: `0 of 0`.
  - 3pt: `1 of 2` — `Q3 5:18` LEFT corner make off press-break; `Q3 4:27` LEFT corner miss on open look off PnR kick.
  - FT attempts: `0 observed`.
- **Shot chart location summary:** Drives with body control, uses floater off left-hand penetration, spots up in left corner from 3. Willing shooter with a tough-shot-maker streak.
- **Key tendencies (each tagged with confidence + count):**
  - LEFT-handed `[CONFIRMED]`.
  - Drives left, uses body to create space, floater off drive `[LIKELY]` (`Q2 6:42`).
  - Made transition / drive-and-kick pass for teammate layup `[SINGLE GAME SIGNAL]` (`Q4 2:20`).
  - Questionable decision at `Q2 7:17` (passed-up alley-oop attempt nearly OOB) `[SINGLE GAME SIGNAL]`.
- **Defensive assignment:** Top or top-wing of 1-2-2 press; wing assignments in man.
- **Defensive vulnerability:** **Over-helped** on a contained PnR screen at `Q2 7:00`, leaving the open 3 shooter → TD make. `[SINGLE GAME SIGNAL]` on over-help.
- **Free throw shooting observed:** `0 of 0`.
- **Turnovers:** `0 cleanly attributable`.
- **Notable plays (timestamps for the grading UI):**
  - `C1 · Q2 6:42` — lefty drive, floater miss, own OREB, finish.
  - `C1 · Q2 3:49` — open baseline runner miss behind zone.
  - `C2 · Q3 5:18` — left-corner 3 make off press-break.
  - `C3 · Q4 2:20` — great transition pass for teammate's easy layup.

### #22 — Jamison White (seeded PF, 6'9", 2026)

- **Total possessions observed:** `~30` (breakdown: ~8 / ~5 / ~8 / ~9). Exited briefly at `Q1 7:40` after face contact; returned `Q1 4:24`. Subbed for #10 at `Q2 7:45`; back in rotation later.
- **Confirmed position from film:** `PF` / `stretch-4`.
- **Confirmed dominant hand from film:** **Insufficient observation** — not clearly established across chunks. `[NOT OBSERVED]`.
- **Confirmed role:** `spacer / stretch-forward / offensive-rebounder`.
- **Offensive role (specific):** Stretch-four. Elbow or wing spacing in half-court. 3-point shooter on ball-swing vs. zone. Aggressive offensive rebounder — multiple put-back scores. Flex / cross-screen setter on BLOB sets.
- **Scoring zones with frequency:**
  - Rim: `~3 of 3` — put-back scores at `Q2 3:49`, `Q2 1:45`, `Q3 1:17` (all OREB conversions).
  - Paint (non-rim): `0 of 0` — no live FGA logged in this zone. (`Q1 ~3:15` elbow catch and `Q2 1:18` post-up were stripped before any shot attempt; classified as turnovers, not FGA — see TOs row.)
  - Mid-range: `0 of 0`.
  - 3pt: `1 of 2` — `Q4 7:45` RIGHT wing make off ball-swing vs. zone; `Q4 4:46` between-legs contested 3 miss (forced / blowout loose play).
  - FT attempts: `Q4 6:33` trip drawn from OREB (makes not logged).
- **Shot chart location summary:** Spot-up right-wing 3 off zone ball-swing. Rim finishes almost exclusively via put-backs (not via post-ups). Does NOT have a reliable back-to-basket game (`Q2 1:18` can't back down a smaller guard; stripped).
- **Key tendencies (each tagged with confidence + count):**
  - Aggressive offensive rebounder → put-backs `[CONFIRMED]` (`Q2 3:49`, `Q2 1:45`, `Q3 1:17`, `Q4 6:33` drew foul — 4+ independent observations).
  - Shoots right-wing 3 off zone ball-swing `[LIKELY]` (1 make + exposure pattern).
  - Weak back-to-basket post game `[LIKELY]` (`Q2 1:18` stripped when posting smaller defender).
  - Occasional forced / questionable shot selection `[LIKELY]` (`Q4 4:46` between-legs contested 3).
- **Defensive assignment:** Wing / forward in man; bottom corners / wings of 1-2-2 zone.
- **Defensive vulnerability:** Failed to seal on elbow catch at `Q1 ~3:15` → TD steal (contributed to a TO). Brief injury-related exit at `Q1 7:40`.
- **Free throw shooting observed:** At least 1 trip (`Q4 6:33`), makes not separated.
- **Turnovers:** `~2` involvements (`Q1 ~3:15` elbow catch stolen on an entry pass from #2 — shared-blame, also counted under #2's TO total; `Q2 1:18` stripped on post-up attempt — clean on #22).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 2:29` — clean avoidance of back screen (good defensive IQ).
  - `C1 · Q2 3:49` — OREB put-back.
  - `C1 · Q2 1:45` — OREB put-back off #5's forced 3.
  - `C2 · Q3 1:17` — put-back off blocked transition layup.
  - `C3 · Q4 7:45` — right-wing 3 make vs. zone.
  - `C3 · Q4 6:33` — OREB → drew foul.

### #23 — JJ Andrews (seeded SF, 6'7", 2026) — **the film's named player, primary scorer**

- **Total possessions observed:** `~55` (breakdown: ~10 / ~15 / ~17 / ~13). Played nearly wire-to-wire.
- **Confirmed position from film:** `SF` / `3`.
- **Confirmed dominant hand from film:** `LEFT` — `[CONFIRMED]` across all 4 chunks (`Q1 7:54`, `Q3 2:48`, `Q3 0:49`, `Q4 2:55`, `Q4 6:33`).
- **Confirmed role:** `primary_scorer` / `slasher`.
- **Offensive role (specific):** Primary slasher and scorer. Attacks the rim, draws lots of fouls, runs the floor in transition. Physical, high-motor, aggressor personality. Often takes late-clock / end-of-period iso possessions. Sets flex / cross-screens on BLOB sets (secondary role).
- **Scoring zones with frequency:**
  - Rim: `~5 of ~8` — `Q3 2:48` and-1, `Q3 0:49` full-court lefty finish in traffic, `Q3 3:22` BLOB layup, `Q4 2:55` spin-move finish, `Q1 7:54` drive → drew foul (no make, just contact), `Q3 7:26` blocked at rim after SLOB iso (at-rim attempt, mis-bucketed in earlier pass).
  - Paint (non-rim): `0 of 0`.
  - Mid-range: `0 of 0`.
  - 3pt: `0 of 2` — `Q1 ~2:50` miss (ATO kick-out), `Q3 7:10` airball (SLOB quick-release).
  - FT attempts: **High volume.** 5 clean trips logged: `Q1 7:54`, `Q2 0:31`, `Q3 6:56`, `Q3 2:48` (and-1), `Q4 1:47`. (Earlier draft double-counted `Q4 1:47`; deduped here.)
- **Shot chart location summary:** Exclusively a rim-attacker — everything at the basket or drawing fouls on the way there. 3-pt shot is a **non-threat** (0-for-2 including an airball). Does not take mid-range. `Force him to shoot 3s, don't let him drive.`
- **Key tendencies (each tagged with confidence + count):**
  - **Almost exclusively drives LEFT** `[CONFIRMED]` — `Q1 7:54`, `Q1 ~3:30`, `Q3 2:48`, `Q3 0:12`, `Q4 2:55`, `Q4 6:33` (6+ independent observations). **Primary scouting tip: force him right.** (See §10f watch-item #3.)
  - Draws fouls on drives through contact `[CONFIRMED]` (5+ FT trips).
  - Pushes ball after DREB `[CONFIRMED]` (`Q3 1:38`, `Q3 1:17`, `Q3 0:49`).
  - Forces contested / bad shots when aggressive `[CONFIRMED]` (`Q1 ~3:30` 1-on-5 iso, `Q4 6:33` full-court lefty drive into traffic, `Q3 7:10` airball 3).
  - Takes BLOB / SLOB / last-shot possessions `[CONFIRMED]` (`Q3 7:10`, `Q3 3:22`, `Q3 0:12`).
  - Cannot reliably hit 3s `[CONFIRMED]` (0-for-2 including an airball).
- **Defensive assignment:** Wing in man; bottom corner / wing of 1-2-2 zone.
- **Defensive vulnerability:** Got caught on screen at `Q1 4:17` forcing BBE into a bad switch sequence. Primary defensive strength is activity/help, not on-ball containment.
- **Free throw shooting observed:** 5 clean trips (see Scoring zones row); whole-game FT makes included in chunk-summary totals (~10 attempts across his trips, makes not per-player separated).
- **Turnovers:** `~0 cleanly attributable` in possession logs.
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 7:54` — lefty drive, drew foul, 2-of-2 FT.
  - `C0 · Q1 5:17` — poked ball away from TD post on BLOB → TD SCV.
  - `C0 · Q1 2:09` — weak-side steal → transition layup.
  - `C2 · Q3 2:48` — and-1 on lefty drive.
  - `C2 · Q3 0:49` — full-court transition, lefty finish in traffic.
  - `C2 · Q3 3:22` — BLOB easy layup (cut to block).
  - `C3 · Q4 2:55` — spin move right, finish left.
  - `C3 · Q4 1:47` — clutch lefty drive, drew foul in clock-management situation.

### #31 — Sheek Pearson (seeded PF, 6'11", 2026) — **likely plays C**

- **Total possessions observed:** `~45` (breakdown: ~10 / ~12 / ~12 / ~11). Subbed briefly `Q2 2:28` out, back `Q2 1:11`; sub at `Q3 2:07` out, back by chunk 3.
- **Confirmed position from film:** `C` — functionally the center despite PF on seed; plays as the lone big in nearly all observed lineups. Update roster.
- **Confirmed dominant hand from film:** **Insufficient observation** — hand not clearly established on drives or finishes. `[NOT OBSERVED]`.
- **Confirmed role:** `screener / finisher / rim-runner`.
- **Offensive role (specific):** Primary screener in virtually all BBE PnR actions (paired with #2). Roll-man / rim-runner on PnR finishes. Lob / dunker-spot threat. Sets seals on BLOB sets. Occasional elbow spacing. Does NOT shoot from outside or beyond the paint.
- **Scoring zones with frequency:**
  - Rim: `~5 of ~7` — Makes: `Q1 1:13` transition dunk, `Q2 6:42` roll dunk, `Q3 4:13` BLOB dunk (after fumble), `Q4 5:33` tip-in, `Q4 3:52` and-1 lob finish on post-up vs. zone. Misses: 2 missed tip / put-back attempts (rebound chains, scratchpad-flagged).
  - Paint (non-rim): `0 of 1` — `Q3 4:13` BLOB post-up off-balance miss (separate from the recovered BLOB dunk on the same possession). No other paint FGA.
  - Mid-range: `0 of 0`.
  - 3pt: `0 of 0` — does not shoot from deep.
  - FT attempts: `Q2 2:35` trip inferred; others tied to and-1 conversions.
- **Shot chart location summary:** Rim only. Dunker, lob-catcher, put-back finisher. Zero mid-range or perimeter shot attempts. If defender doesn't help on the roll, he finishes at the rim.
- **Key tendencies (each tagged with confidence + count):**
  - On-ball screens for #2 is the bread-and-butter action `[CONFIRMED]` (all 4 chunks).
  - Screens are often offered but declined by ball-handler `[LIKELY]` (`Q1-4`, `Q1-9`, `Q4-9` declined).
  - Crashes offensive glass and rolls hard `[CONFIRMED]` (multiple OREB → score sequences).
  - Occasional fumbled catches in the paint `[LIKELY]` (`Q1 7:23` fumble → TO; `Q3 4:13` fumbled but recovered for dunk).
  - **Easily moved off post spot** `[CONFIRMED]` — cannot maintain post position against pressure; forces bad shots when fed (`Q2 1:18` note on teammate #22; `Q3 4:13` own post-up misfire).
- **Defensive assignment:** Primary PnR screen defender. Rim-protector. Bottom of 1-2-2 press (usually bot-left or bot-right).
- **Defensive vulnerability:** **Comprehensive PnR defense liability — see §8.** Over-hedges, poor pick-n-pop close-outs, split on switches, perimeter defense is exploitable. Missed zone assignment at `Q2 4:14` (left cutter wide open under basket). See §10f watch-item #4.
- **Free throw shooting observed:** Not separately logged.
- **Turnovers:** `~1` (`Q1 7:23` fumbled pass on quick PnR).
- **Notable plays (timestamps for the grading UI):**
  - `C0 · Q1 1:13` — transition dunk off #1 pass.
  - `C0 · Q1 2:09` — great hedge → #23 steal → BBE transition layup.
  - `C1 · Q2 6:42` — roll dunk on high PnR.
  - `C2 · Q3 4:13` — BLOB dunk after fumbled catch.
  - `C2 · Q3 3:52` — and-1 lob finish posting vs. zone.
  - `C3 · Q4 1:12` — DREB + outlet pass for #2 transition dunk.
  - `C0 · Q1 5:26` — over-hedge on unused screen (exploitable tendency).
  - `C1 · Q2 4:14` — missed zone assignment → TD layup under basket.

### #32 — Jaylan Mitchell (seeded PF, 6'8", 2027)

- **DID NOT APPEAR on film.** No possessions observed in any chunk. Either a DNP or garbage-time minutes below the observation threshold. Status: `not_evaluated`.

### #33 — Jahadi White (seeded PF, 6'8", 2026)

- **DID NOT APPEAR on film.** No possessions observed in any chunk. Either a DNP or garbage-time minutes below the observation threshold. Status: `not_evaluated`.

### Unknown players (seen on film but not on seeded roster)

*No unrostered jerseys observed. All 7 BBE players who appeared (#1, #2, #5, #10, #22, #23, #31) are on the seeded roster. Two seeded players (#32, #33) did not appear on film.*

| # | Short description | Suggested name (if known) | Possessions observed |
|---|---|---|---|
|   | *(none)*  |   |   |

---

## SECTION 10 — SYNTHESIS FLAGS

*This is the most important section for building a valid eval set. Every judgment call
you made goes here. Every uncertainty. Every vocabulary reconciliation. Every
contradiction you resolved. Listing them here is what makes the ground truth honest.*

### 10a — Vocabulary reconciliations you made

- **"Ball screen" / "on-ball screen" / "High PnR" / "PnR"** were used interchangeably across chunks in the scratchpad. All BBE two-man actions where a big (almost always #31) sets a screen above the arc for a guard (almost always #2) are unified under **"High PnR with #2 + #31"** in §2 inventory. Total count per §2 aggregates all four phrasings. This is a low-risk unification — the structural action is identical across chunks.
- **"Weak screen" / "didn't make contact" / "offered but unused" / "lazy screen" / "switched instead of screened"** were all used to describe the same underlying team-level tendency. Unified in §2 / §9 under **"weak screen-setting (team-level)"** with count of 6+ observations across chunks 0–2. Calling this `[CONFIRMED]` team tendency, not an individual quirk.
- **"1-2-2 press → 1-2-2 halfcourt zone"** — the full-court press shape and the half-court zone shape share personnel and structure (top defender, two wing defenders, two bottom defenders). Scratchpad treats them as one continuous scheme that extends the zone concept full-court. Unified in §6 as a single scheme ("1-2-2 press-to-zone") rather than two separate schemes. Revisit if film 02 shows BBE running the half-court 1-2-2 WITHOUT the press (or vice versa) — may need to split.
- **"No set," "no action ran," "5-out," "4-out," "iso drive"** — all used to describe possessions where BBE didn't execute a designed half-court action and instead defaulted to spacing + 1-on-1. Unified in §2 as **"iso / 5-out no-set"** category. This is a deliberate vocabulary choice because "having no set offense" IS a finding about BBE — not a gap in the observation. Flag if TEX's output calls these "5-out motion" (which implies structure) rather than "no-set iso" (which is what actually happened).
- **"Secondary handler" vs "primary PG"** — chunk 0 initially treated #1 as the PG based on the seeded roster (PG position). By chunks 1–3, #2 was clearly established as the primary initiator / press-breaker / clutch operator. Resolution: **#2 is the de-facto PG; #1 is a secondary / rotation handler.** This contradicts the seeded roster's position label, which is fine — roster positions are estimates and the film is the source of truth.

### 10b — Counts you are not confident on

- **Chunk 0 possession count** — only 10 BBE possessions logged, but scratchpad flags actual count as `~14–17`. True chunk-0 possession count is under-logged by `~4–7`. Impact: any chunk-0-specific ratio (TOs per possession, OREBs per possession) is unreliable for chunk 0. Whole-game denominators (sum of 4 chunks) are off by `~4–7` but directionally correct. Treat all whole-game BBE possession-rate claims as `[LIKELY]` not `[CONFIRMED]`.
- **Chunk 2 possession count** — 17 logged, but scratchpad flags one missing possession at `Q3 3:22` (box-set BLOB with #23 layup, captured in special-situations table but not in main possession table). True chunk-2 count is `~18`. Minor — adjust whole-game total from 57 logged to `~58–62 actual`.
- **BBE FT makes per possession** — only tracked at chunk-summary level, not per-possession. Per-chunk FT trips/attempts/makes (C0: 1/4/3, C1: 3 trips / ~6 / ~5, C2: 6/12/10, C3: 4/6/5) are best-guess team totals. Whole-game FT trip count `~14`, whole-game FT makes `~23`. Both are `[LIKELY]`, not `[CONFIRMED]`.
- **BBE offensive rebounds total** — C0: 1, C1: ~6, C2: ~4, C3: 2 = `~13` whole-game. C1 and C2 counts are fuzzy (scratchpad uses `~` prefix). Directional claim ("BBE is a strong offensive rebounding team") is `[CONFIRMED]` by qualitative observations across all chunks; exact count is `[LIKELY]`.
- **BBE 2nd-chance points** — C0 not tracked, C1 ~8, C2 0 clean OREB→makes (though extended possessions scored), C3 ~2. Total is `~10 2nd-chance points`, highly imprecise. Directional claim (OREBs are a scoring weapon) is `[CONFIRMED]`; exact count is not.
- **TD possessions / TD FT count / TD shooting splits** — not tracked 1-for-1. Anything about TD's offensive tendencies in this ground truth is `[NOT OBSERVED]`. TEX should not produce TD-side claims from this film.
- **BBE team fouls** — captured only at C3 (3 team fouls noted). Whole-game team foul count not reconstructable.

### 10c — Jersey numbers you could not confirm

- **TD jersey numbers are mostly unidentified.** Scratchpad captured #2 (TD PG), #4 (wing, got pop-3 look Q1 4:17), #7 (screener/cutter on Q1 Horns + Q2 7:17 BLOB), #12 (big screener on Q1 5:26 + 4:17). Everyone else on TD is logged as "TD player." Any individual TD opponent profile is out of scope for this ground truth — rely on the TD roster for identification if TEX produces TD-side claims.
- **Chunk 0 poss 8 and poss 9** — originally logged as "#5 initiator" in the scratchpad but later corrected to "#2 initiator" based on narrative cues (the full-name "Pearson" was mentioned, and #2 is the PG). Scratchpad now shows `*Personnel note: original log listed #5; corrected to #2 based on narrative.*` — resolved, but flagged in case the correction is wrong and a later film establishes the opposite.
- **Chunk 1 substitution at Q2 3:22** — scratchpad notes "#2 subbed in for #? *(unclear which player came out — flag for rewatch)*." Impact: minor, doesn't affect any ground-truth claim; flagged for completeness.
- **Chunk 2 poss 9 outcome** — #23 iso on left side after OREB, but final result (make / miss / TO) not cleanly logged in the scratchpad. Treating as `[unknown outcome]` for grading purposes.
- **Chunk 2 poss 12 shooter** — "layup off #10 pass" but the shooter's jersey not cleanly logged. Likely #2 or #23 based on lineup context; not attributed in §9 player profiles.
- **Handedness of #1 Coleman and #31 Pearson** — scratchpad says "unclear across all 4 chunks" for both. §9 player profile entries will say "hand dominance: unobserved" rather than guess.

### 10d — Contradictions resolved (and how)

- **#31 Pearson PnR defense: occasionally great (Q1 2:09 hedge → steal) vs. systematically a liability (Q1 5:26 over-hedge, Q1 4:17 blown close-out, Q3 7:03 no help, Q3 4:37 split on switch, Q2 0:48 + 0:58 beaten on perimeter).** Resolution: **inconsistent but with a clear net-negative tilt — mark as a liability with one caveat.** 1 positive observation vs. 5 negative observations. Confidence: `[CONFIRMED]` liability, `[LIKELY]` occasionally capable of a well-timed hedge.
- **BBE base defense is "man-to-man" (chunk 0) vs. "1-2-2 zone" (chunks 1–3).** Resolution per user guidance: **base scheme is "split" / mixed with a timeline.** Q1 was pure man-to-man. First 1-2-2 appearance Q2 5:39. Q2 oscillated between 1-2-2 and man depending on lineup (notably, when #2 was out, BBE stayed in zone; when #2 came in, they sometimes reverted to man — `Q2 2:37` / `Q2 2:26`). Q3 and Q4 were firmly 1-2-2 press → 1-2-2 half-court zone as the base. **Both schemes are real; the team played materially more zone than man by snap count in Q2–Q4.** Confidence: `[CONFIRMED]` for the timeline; §6 will capture this as a split/mixed with per-quarter breakdown.
- **"BBE is a good offensive rebounding team" vs. "BBE is a sloppy, undisciplined offense."** Resolution: **both are true and they're linked.** BBE's half-court sets are stagnant / lazy / often don't produce a quality initial shot, but the team compensates by crashing the offensive glass with #22, #23, #31, #1 all willing to dive for boards. This is the mechanism by which a mediocre half-court offense still scores 91 points. Confidence: `[CONFIRMED]`.
- **#2 Pearson is left-handed but prefers starting on the LEFT side.** Unusual for a lefty (most lefties prefer starting right so their dominant hand is toward the middle). Resolution: **real tendency, confirmed across multiple possessions (Q1 1:43, Q2 7:57 observed).** Not a contradiction but a quirk worth flagging for the scouting consumer.
- **Chunk 2 poss 15 personnel listed #2 + #5 on floor simultaneously** — possible, but scratchpad notes suggest #5 was just subbed in at Q3 2:07. Resolution: both on floor for the Q3 2:07 → Q3 0:49 window is plausible (#2 + #5 are both guards, can share backcourt). No contradiction resolved — listing as-is.

### 10e — Situations that may not be representative

- **Blowout loose play after ~Q3 3:00.** Once BBE was up 20+, shot selection and decision-making deteriorated (Q4 5:56 wild full-court pass, Q4 5:33 forced drive, Q4 4:46 between-legs → contested 3, Q4 6:33 hero-ball push). Tag these possessions as "up-big loose play" rather than base half-court offense. Any TEX output that treats chunks 2–3 iso rates as the base rate will over-count iso frequency — the real base rate is closer to chunks 0–1.
- **TD disengaged by ~Q4 1:12 per scratchpad.** The final 3 possessions of the game (Q4 1:47, 1:12, 0:46) are clock-management possessions against a team that had given up — they should not be used to infer BBE's clutch execution, 2-way pressure, or late-clock offense. Flagged in §5.
- **Q2 TD full-court press.** TD pressed BBE heavily in Q2 and again in Q3–Q4, creating extra transition opportunities and flipping the possession pace. Scratchpad explicitly notes "TD ran full-court press in Q2 — forced BBE to adapt." The BBE transition scoring rate and the press-break action inventory are both driven by TD's pressure choices, not by BBE's intrinsic style. If film 02's opponent does NOT press, BBE's possession profile may look very different.
- **First 1-2-2 appearance was lineup-dependent.** Chunk 1 scratchpad flags that BBE ran zone when #2 was out and reverted to man when he came back in during Q2. Q3 onward the zone became base regardless of lineup. The Q2 "scheme depends on who's on the floor" window should not be confused with BBE's settled base defense — the settled base (Q3–Q4) is 1-2-2 press-to-zone. Any claim about "BBE plays zone when X lineup is on the floor" as a general tendency is overclaiming from a single-quarter pattern.
- **#23 Andrews LEFT-hand drive tendency could be matchup-specific.** Confirmed across all 4 chunks against Team Durant, but this is one opponent. The scouting tip "force him right" is durable if it replicates in films 02–05. For film 01 alone, tag as `[CONFIRMED within this game]`, understanding that hand dominance typically generalizes but drive-direction preference might partially reflect TD's defensive tendencies.

### 10f — Things you want TEX to get right (watch-items for grading)

1. **BBE has no repeating half-court set-play inventory.** Their "offense" is High PnR with #2/#31 (often declined), iso drives by #23 (always left) and #2 (lefty), transition pushes, and offensive-rebound second chances. Any TEX output that describes BBE as running "Horns motion" or "5-out motion offense" or identifies a named set they "run" in half-court is hallucinating. The one real repeating structure is the BLOB cross-screen (§4).
2. **BBE's base defense CHANGED DURING the game.** Q1 pure man-to-man. `Q2 5:39` first 1-2-2 appearance. Q3–Q4 firmly 1-2-2 press → 1-2-2 half-court zone as the base. TEX must identify the timeline change, not just pick one scheme and call it "base."
3. **#23 Andrews is LEFT-handed and almost exclusively drives LEFT.** Confirmed across all 4 chunks. Primary scouting tip for opposing coaches is "force him right." TEX missing this handedness/direction tendency is a graded miss.
4. **#31 Pearson is a PnR defense liability** — over-hedges, poor close-outs on pick-and-pop, gets beaten on switches to the perimeter. 5+ independent negative observations across chunks 0–2. TEX must identify this as an attackable matchup.
5. **#2 Pearson is the real PG** (not #1 Coleman, despite the seeded roster). Left-handed, best ball-handler, primary press-breaker, vocal floor leader, handles every clutch/clock-kill possession. TEX must attribute initiator / press-break / clock-management duties to #2.
6. **Middle of the 1-2-2 zone is WIDE OPEN.** Repeatedly noted across Q3 and Q4 (Q3 2:07, Q3 1:33, Q3 0:37, Q4 5:44, Q4 4:44) — TD didn't consistently exploit it, but the weakness is real. Any opposing team that can get the ball to the high post / free-throw line vs. BBE's zone will collapse it. TEX must flag this exploitable gap.
7. **BBE's half-court screen-setting is a team-level weakness.** 6+ independent observations of weak / non-contact / declined screens across chunks 0–2. This is a pattern, not player-specific. TEX must call this out as a team tendency.
8. **Offensive rebounding is BBE's compensating weapon.** ~13 OREBs whole-game, multiple 2nd-chance scoring sequences, explicit "they extend possessions with effort" pattern. TEX must identify OREB crashing as a strategic priority, not a byproduct.
9. **Three LEFT-handed guards** (#2 Pearson, #5 Blivens, #10 Edwards) plus one LEFT-handed wing (#23 Andrews). Unusually high lefty concentration. TEX must correctly label handedness per player in §9; getting 2-of-4 right is partial credit, missing the pattern entirely is a graded miss.
10. **Game shape was a wire-to-wire blowout; late-game tendencies are not observable for close games.** Any TEX output that produces confident close-game-late claims from film 01 is hallucinating and should be graded as such. §5 must be tagged "insufficient observation" for close-late, with blowout-protection observations tagged separately.

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

The per-section scores roll up to a `captured / missed / hallucinated` table for film 01
and get written to `EVAL_SCORES.md`. Section 11 is documentation only — nothing to fill in.

---

*When every blank above is filled in (or explicitly marked "insufficient observation"),
this document is ready. Commit it. Then run TEX against film 01 and the grading UI will
diff TEX's output against this file.*

*Film 01 is step 1 of 5. Films 02–05 repeat this process. At 5 films complete, golden
set initialization is done and Stage 1 of the commercial ladder (per ROADMAP.md) is gated.*
