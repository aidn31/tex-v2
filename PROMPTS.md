# PROMPTS.md — TEX v2

All 6 section prompts. Versioned. With changelog.
These are the exact strings loaded from `backend/prompts/*.txt` at report generation time.
Every prompt has a VERSION header. That version is saved to `report_sections.prompt_version`
and `corrections.prompt_version` on every report. Never edit a prompt without incrementing
the version and adding a changelog entry. Cache entries from prior versions are stale — see SCHEMA.md.

Prompts are the highest-leverage asset in the system. One word change can break output quality for
every report until the next correction cycle surfaces it. Change prompts deliberately, version them
always, and run the eval questions in EVALS.md against any changed prompt before deploying.

---

## HOW PROMPTS ARE LOADED

```python
# services/prompts.py
def load_prompt(section_type: str) -> tuple[str, str]:
    path = f"backend/prompts/{section_type}.txt"
    with open(path) as f:
        raw = f.read()
    lines = raw.split("\n")
    version = lines[0].replace("VERSION: ", "").strip()
    prompt_text = raw.split("---\n", 1)[1].strip()
    return prompt_text, version
```

The `---` delimiter separates the version header from the prompt body. Everything below `---` is
sent to Gemini verbatim. No pre-processing except roster injection for sections 1-4 (see below).

---

## CONTEXT STRUCTURE — SECTIONS 1-4

Sections 1-4 receive a Gemini context cache containing:
1. All film chunk URIs (video content — the full game film)
2. The roster string (formatted by `format_roster_for_prompt()`)

The prompt text is sent as the user message against this cached context. The roster is in the
cache, not in the prompt. The prompt does not need to re-describe the roster format — Gemini
reads the cache and the prompt together.

**What Gemini sees for sections 1-4:**
```
[Context cache]:
  [video: chunk_000.mp4]
  [video: chunk_001.mp4]
  ...
  ROSTER:
    #3 Marcus Williams, PG, 6'2", primary_initiator, right-handed
    #10 Jordan Hayes, SF, 6'5", spacer
    ...

[User message]:
  {section_prompt_text}
```

---

## CONTEXT STRUCTURE — SECTIONS 5-6

Sections 5-6 receive no video. They receive sections 1-4 text output as a structured context string.

**What Gemini Flash sees for section 5:**
```
[User message]:
  SCOUTING REPORT CONTEXT — [TEAM NAME]
  Generated from game film analysis. Use this as the complete basis for your output.

  === OFFENSIVE SETS ===
  {section_1_content}

  === DEFENSIVE SCHEMES ===
  {section_2_content}

  === PICK AND ROLL COVERAGE ===
  {section_3_content}

  === INDIVIDUAL PLAYER PROFILES ===
  {section_4_content}

  ---
  {section_5_prompt_text}
```

**What Gemini Flash sees for section 6:**
Same as above, plus section 5 output appended before the section 6 prompt.

---

## PROMPT FILE FORMAT

Every `.txt` file in `backend/prompts/` follows this exact format:

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
[prompt text]
```

The `---` line is the delimiter. It must be on its own line with no leading spaces.
The prompt text begins on the line immediately after `---`.

---

## PROMPT 0 — CHUNK SYNTHESIS

**Files:** `backend/prompts/chunk_extraction.txt` + `backend/prompts/chunk_synthesis.txt`
**Model:** Gemini 2.5 Pro (both stages)
**Input:** Raw video chunks (extraction) → chunk extraction outputs (synthesis)
**Output:** A unified full-game intelligence document consumed by sections 1-4 as context

This is the most important prompt engineering problem in the product. Sections 1-4 are only
as accurate as the foundation they build on. If the synthesis is wrong — miscounted sets,
unreconciled vocabulary, lost half-time adjustments — all 6 sections inherit those errors
and every correction Tommy makes traces back to a synthesis failure, not a section failure.

Prompt 0 is not optional. It is not a performance optimization. It is the mechanism that
turns N partial views of a game into one coherent ground truth.

---

### WHY TWO STAGES

A single synthesis call that receives all raw video simultaneously sounds simpler but
creates a harder problem: asking Gemini to simultaneously perceive, count, reconcile,
and structure a 2-hour game in one pass produces lower accuracy than separating perception
from synthesis. The extraction pass asks Gemini to watch and describe. The synthesis pass
asks it to think. These are different cognitive tasks and perform better when separated.

**Stage 1 — Per-Chunk Extraction (run in parallel, one call per chunk):**
Each chunk gets a structured extraction pass. Output is a machine-parseable observation
log — what was seen, how many times, who did it. No interpretation. No strategy. Pure observation.
These run in parallel alongside each other. 5 chunks = 5 simultaneous Gemini calls.

**Stage 2 — Synthesis (one call, receives all extraction outputs):**
Takes all chunk extraction outputs as text input. No video. Reconciles vocabulary,
aggregates counts, identifies timeline changes, flags contradictions, and produces the
unified full-game intelligence document that sections 1-4 consume.

---

### PIPELINE POSITION

```
Film chunks uploaded to Gemini File API
    │
    ├── Chunk extraction pass (parallel — one per chunk, Gemini 2.5 Pro)
    │   ├── chunk_000: extraction output → saved to DB
    │   ├── chunk_001: extraction output → saved to DB
    │   ├── chunk_002: extraction output → saved to DB
    │   └── chunk_003: extraction output → saved to DB
    │
    └── Synthesis pass (one call, text-in text-out, Gemini 2.5 Pro)
            Input: all chunk extraction outputs + roster
            Output: unified game intelligence document
            Saved to: film_analysis_cache.synthesis_document (new column, Phase 2 addition)
                      and prepended to context cache before sections 1-4 fire
```

The synthesis document is stored in the film analysis cache alongside sections 1-4.
If the film hash matches an existing cache entry, the synthesis document is retrieved directly —
no re-extraction, no re-synthesis. Same cache invalidation rules apply: stale on prompt version change.

The synthesis document is prepended to the context cache that sections 1-4 receive. Sections 1-4
are still watching the raw video (via the cache URI) — the synthesis document adds structured
prior knowledge so each section prompt does not need to re-derive full-game frequency counts
from scratch. The video is the ground truth. The synthesis document is the structured summary.
Sections 1-4 use both. Neither replaces the other.

---

### STAGE 1 — CHUNK EXTRACTION PROMPT

**File:** `backend/prompts/chunk_extraction.txt`

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are analyzing one segment of a complete basketball game film.
This segment is chunk {chunk_index} of {total_chunks}, covering approximately minutes {start_min} to {end_min}.
The full game roster is provided in context.

Your job is to produce a structured observation log of everything that happens in this segment.
This is a perception task only. Do not interpret, strategize, or draw conclusions.
Document what you see. Use precise counts. Use jersey numbers from the roster.

Output your observations in this exact structure. Use the headers exactly as written.
Every section is required. If nothing was observed for a section, write "None observed in this segment."

=== CHUNK {chunk_index} OBSERVATION LOG ===
Segment: minutes {start_min}–{end_min} (approximately)
Possessions observed: [total offensive possessions for each team in this segment]

--- OFFENSIVE ACTIONS (Team being scouted) ---
For each offensive action observed, document:
  ACTION: [name using standard coaching terminology — e.g., "Horns", "DHO series", "Spain PnR",
           "5-out motion", "Pistol", "Floppy", "Pin-down", "Elevator", "UCLA cut"]
           If you cannot identify the name: describe it structurally — e.g., "two-man action:
           ball handler drives right off screen set by big at elbow"
  COUNT: [exact number of times this action was run in this segment]
  PLAYERS: [jersey numbers and names of initiators and key participants]
  OUTCOME: [success rate in this segment — how many produced good shots, scores, turnovers, stalls]
  NOTES: [anything unusual — counters off the action, situational use, variation observed]

List every distinct action observed more than once.
Single-occurrence actions: list at the end under "SINGLE-OCCURRENCE ACTIONS" with a one-line description.

--- DEFENSIVE SCHEME (Team being scouted, on defense) ---
  BASE DEFENSE: [man-to-man / zone type / press — be specific]
  SCHEME CHANGES: [did they change defenses during this segment? when? what triggered it?]
  BALL SCREEN COVERAGE: [drop / hedge / switch / ICE / blitz — observed in this segment]
  COVERAGE CHANGES: [did ball screen coverage change? on which players or in which situations?]
  TRANSITION DEFENSE: [how do they get back? who is their primary back-defender?]
  NOTABLE MOMENTS: [specific defensive stops or breakdowns worth flagging — jersey numbers]

--- INDIVIDUAL PLAYER OBSERVATIONS ---
For each player who appeared in this segment, document observations:
  #[JERSEY] [NAME]:
    OFFENSE: [what they did — actions, tendencies, shots taken, results]
    DEFENSE: [how they defended — matchup, quality, breakdowns]
    COUNT: [approximately how many possessions they were on the floor]

Only include players with 3+ observable possessions. Skip players with minimal activity.

--- SCORE AND GAME CONTEXT ---
  Score at start of segment: [if determinable from film]
  Score at end of segment: [if determinable from film]
  Game situation notes: [was either team protecting a lead? pressing? fouling intentionally?]
  Tempo notes: [pace of play in this segment vs what you would expect as a baseline]

--- FLAGGED OBSERVATIONS ---
List anything in this segment that seems important but you are uncertain about:
  - Plays or actions you could not confidently identify
  - Player jersey numbers you could not confirm from the roster
  - Game situations that seem unusual or that changed how both teams played
  - Any count you are not confident in (state your uncertainty — e.g., "I counted 4 but may have missed 1")

Be honest about uncertainty. An uncertain count flagged here is more useful than a confident
wrong count that propagates into the synthesis.
=== END CHUNK {chunk_index} LOG ===
```

**Injection note:** `{chunk_index}`, `{total_chunks}`, `{start_min}`, `{end_min}` are
filled programmatically before the prompt is sent. The worker computes start/end minutes
from `film_chunks.chunk_index` and `film_chunks.duration_seconds`.

---

### STAGE 2 — SYNTHESIS PROMPT

**File:** `backend/prompts/chunk_synthesis.txt`

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are synthesizing multiple observation logs from consecutive segments of a basketball game
into a single, unified full-game intelligence document.

You will receive:
1. Observation logs from {total_chunks} consecutive game segments, covering the full game.
2. The complete roster of the team being scouted.

Your job is to resolve inconsistencies, aggregate counts, identify game-long patterns, and
produce a structured full-game intelligence document. This document will be used as the
foundation for a professional scouting report. Errors here propagate into every section
of the report. Accuracy is the only priority.

SYNTHESIS RULES — READ BEFORE PRODUCING OUTPUT:

Rule 1 — AGGREGATE COUNTS EXACTLY.
Count every occurrence of each action across all segments and report the total.
If chunk 1 logged 3 Horns sets, chunk 3 logged 4, and chunk 5 logged 2, the total is 9.
Write 9. Do not re-estimate. Do not approximate. Show your work: "(3 + 4 + 2 = 9 across segments 1, 3, 5)".

Rule 2 — RECONCILE VOCABULARY BEFORE COUNTING.
Different chunk logs may use different names for the same action. Before aggregating,
determine whether two named actions are the same action described differently.
If chunk 1 calls something "DHO series" and chunk 3 calls it "Spain PnR," determine
from the structural description whether they are the same action. If yes, unify under
one name and aggregate. If no, keep them separate and explain why.
State every reconciliation decision explicitly: "Unified 'DHO series' (chunks 1-2) and
'Spain PnR' (chunks 3-4) — same two-man action with guard-to-big handoff at the elbow.
Total: 11 occurrences."

Rule 3 — PRESERVE TIMELINE INFORMATION.
If a team's scheme, coverage, or personnel usage changed during the game, document when
and why. "They played drop coverage for the first 24 minutes, then switched to hard hedge
after their opponent scored 3 consecutive pull-up jumpers" is important scouting data.
Flattening this into "they play a mix of drop and hedge" loses the strategic intelligence.

Rule 4 — HANDLE CONTRADICTIONS EXPLICITLY.
If two chunk logs report conflicting observations about the same action or player, do not
silently choose one. Flag the contradiction, state what each chunk logged, and state your
best resolution with your confidence level.
Example: "Contradiction: chunk 2 logs #3 as right-hand dominant; chunk 4 logs him attacking
left in 3 consecutive possessions. Resolution: right-hand dominant overall (7 right vs 4 left
across all segments) but will attack left in specific situations — likely vs right-hand dominant
on-ball defenders. Confidence: medium."

Rule 5 — SURFACE SINGLE-GAME SIGNALS VS CONFIRMED PATTERNS.
A tendency observed in only one segment may be a genuine tendency or a sample artifact.
Tag observations with confidence:
  [CONFIRMED] — observed in 3+ segments or with high frequency (8+ occurrences)
  [LIKELY]    — observed in 2 segments or 4-7 occurrences
  [SINGLE GAME SIGNAL] — observed once or in only one segment. Possible tendency. Not confirmed.
The scouting report sections will propagate these tags so the coaching staff knows what to trust.

Rule 6 — NEVER INVENT.
If the chunk logs do not contain enough information to answer a question, say so.
"Insufficient data across all segments to determine their late-game offensive preference."
is the correct output. Fabricating a confident answer is worse than acknowledging the gap.

---

OUTPUT FORMAT — produce these exact sections in this exact order:

=== FULL-GAME INTELLIGENCE DOCUMENT ===
Team: [name from roster context]
Total segments analyzed: {total_chunks}
Total possessions logged: [sum from all chunk logs]

--- OFFENSE: SET AND ACTION INVENTORY ---
List every offensive action identified, reconciled, and counted across the full game.
Format each entry as:

  [ACTION NAME] [CONFIDENCE TAG]
  Total occurrences: [exact count] ([breakdown by segment: e.g., "3+4+2 across segments 1,3,5"])
  Primary initiators: [jersey numbers and names]
  Primary screeners/participants: [jersey numbers and names]
  Typical floor position: [where on court it initiates]
  Success rate: [good shots produced / total runs — e.g., "6 of 9 produced a good look"]
  Key counter: [what they run off the primary action when it is taken away, if observed]
  Reconciliation note: [if vocabulary was unified across chunks, state it here]

Order by total occurrences (descending). Their most-used action appears first.

--- OFFENSE: TEMPO AND PACE ---
  Push in transition or set up half-court? [with frequency evidence]
  Average time to half-court action initiation: [fast / moderate / deliberate]
  Pace changes: [did they change tempo situationally? when? evidence from chunk logs]

--- OFFENSE: OUT-OF-BOUNDS SETS ---
  List every BLOB/SLOB set observed. Same format as the action inventory above.
  If none observed: "No out-of-bounds sets with repeating structure observed."

--- OFFENSE: LATE-GAME (final 8 minutes of close games) ---
  Primary isolation player: [jersey number and name, with occurrence count]
  Shot clock offense (under 8 seconds): [what they run and who runs it]
  Scheme changes when protecting lead: [if observed]
  Scheme changes when trailing: [if observed]

--- DEFENSE: BASE SCHEME ---
  Primary defense: [man / zone type / press]
  Percentage of possessions: [approximate — e.g., "man-to-man approximately 70% of possessions"]
  Scheme changes: [full timeline — when did they change and what triggered it]
  Transition defense: [how they get back, who leads it, quality]

--- DEFENSE: BALL SCREEN COVERAGE ---
  Primary coverage: [drop / hedge / switch / ICE / blitz]
  Coverage variations: [does it change by personnel or situation — full detail]
  Coverage timeline: [did it change during the game? when? what triggered it?]
  Execution quality: [where does their coverage break down — be specific]

--- DEFENSE: INDIVIDUAL TENDENCIES ---
For each player with significant defensive responsibilities:
  #[JERSEY] [NAME]:
    Primary assignment: [who or what position they guarded]
    On-ball quality: [specific, with evidence from chunk logs]
    Help activity: [active / passive, with examples]
    Identified weakness: [explicit — what action or situation beats them]
    Confidence: [CONFIRMED / LIKELY / SINGLE GAME SIGNAL]

--- INDIVIDUAL PLAYER CONSOLIDATED PROFILES ---
For each player with 10+ observed possessions across all segments:
  #[JERSEY] [NAME]:
    Total possessions observed: [sum across all segments]
    Offensive role: [what they do — be specific, with occurrence counts]
    Scoring zones: [where on floor they score, with frequency evidence]
    Dominant hand: [right / left / ambidextrous — with evidence: "attacked right in X of Y drives"]
    Key tendencies: [list, each tagged with confidence level and occurrence count]
    Defensive assignment: [who they guard and how]
    Defensive vulnerability: [what beats them — specific and direct]

--- SYNTHESIS FLAGS ---
List everything the synthesis is uncertain about:
  - Vocabulary reconciliations that were judgment calls
  - Counts where uncertainty was noted in chunk logs
  - Player identifications that were unclear (jersey number could not be confirmed)
  - Contradictions that were resolved but where the resolution is not high confidence
  - Situations that may not be representative of their normal tendencies (e.g., opponent
    adjusted at halftime and this team responded — normal behavior may differ)

This section is not a sign of failure. It is the most important quality signal in the document.
An honest synthesis flag prevents a wrong claim from propagating into the scouting report.
Sections 1-4 will note flagged items with reduced confidence in the final report.

=== END FULL-GAME INTELLIGENCE DOCUMENT ===
```

---

### HOW SECTIONS 1-4 CONSUME THE SYNTHESIS DOCUMENT

The synthesis document is prepended to the Gemini context cache before sections 1-4 fire.
Each section prompt is not modified — sections 1-4 receive the same prompts as documented below.
The synthesis document is visible to Gemini as structured prior knowledge.

**Instruction prepended to every section 1-4 call:**

```
A full-game intelligence document has been pre-computed from all film segments and is provided
below. This document contains reconciled action counts, confirmed player tendencies, and flagged
uncertainties. Use it as your primary reference for counts, frequencies, and player attributions.
You are also watching the complete game film directly. If you observe something in the film that
contradicts the intelligence document, trust the film and note the discrepancy.
Items tagged [SINGLE GAME SIGNAL] in the document should be reported in your section with the
same uncertainty — do not present them as confirmed tendencies.
Items tagged [CONFIRMED] are reliable and can be stated with confidence.

--- FULL-GAME INTELLIGENCE DOCUMENT ---
{synthesis_document}
--- END INTELLIGENCE DOCUMENT ---

{section_prompt}
```

This means: the synthesis document informs sections 1-4 but does not override the video.
Gemini watches the film and has the synthesis as a structured aid. The two inputs check each other.
If the synthesis says 9 Horns sets and Gemini watching the film sees 11, the section output
notes the discrepancy. That discrepancy becomes a correction signal for the extraction prompt.

---

### FAILURE HANDLING

**If a chunk extraction fails:**
Mark that chunk's extraction as failed in `film_chunks.extraction_status`.
The synthesis prompt receives the available extractions and is told which chunk is missing:
"WARNING: Chunk {index} extraction failed. Segment covering minutes {start}–{end} has no
extraction log. Your synthesis should note this gap explicitly."
The synthesis proceeds on available data. The missing segment is flagged in the synthesis document.
Sections 1-4 are notified via the intelligence document header.

**If the synthesis call fails:**
Retry 3 times (same policy as section tasks). On third failure: sections 1-4 run without
the synthesis document, using only the raw video and the instruction:
"Note: full-game synthesis was unavailable. Derive all counts and tendencies directly from the film."
This is a graceful degradation — the report is generated, not blocked.
The failure is logged to `dead_letter_tasks` and surfaces in Datadog as `tex.synthesis.failed`.

**If the synthesis document contains a flag that affects a section:**
Sections 1-4 are responsible for surfacing synthesis flags in their output. The section prompt
instructs Gemini to report flagged items with uncertainty. Tommy sees the flag in the report.
It becomes a correction target: was the flag legitimate uncertainty or a synthesis error?
Both outcomes are valuable training signals.

---

*Last updated: Phase 0 — Context Engineering*
*Prompt 0 versions: chunk_extraction v1.0, chunk_synthesis v1.0*
*This is the highest-priority prompt to iterate on. Accuracy here determines accuracy everywhere.*

---

## SECTION 1 — OFFENSIVE SETS

**File:** `backend/prompts/offensive_sets.txt`
**Model:** Gemini 2.5 Pro
**Input:** Context cache (video + roster)
**Output:** Full offensive scouting section

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are an elite basketball scout analyzing game film for a coaching staff preparing a scouting report.
Your output will be printed and used on a clipboard during a live game. Every word must earn its place.

Analyze the complete game film provided and produce the OFFENSIVE SETS section of the scouting report.
Use the roster provided in context to attribute every action to specific players by jersey number and name.

WHAT TO IDENTIFY AND DOCUMENT:

1. PRIMARY HALF-COURT OFFENSE
   Identify their primary half-court offensive system. Is it motion-based, set-based, or a hybrid?
   If they run named sets: identify the set (Horns, Spain PnR, Floppy, DHO Series, Pistol, Elevator,
   Zipper, Blob/Slob, 5-Out motion, etc.). Name it using standard coaching terminology.
   For each primary set:
   - Which players initiate it (jersey number and name)
   - What triggers the set (signal, floor position, personnel grouping, or game situation)
   - Exactly how it develops — screen actions, cuts, reads in order
   - Primary options (first action) and secondary options (counter off the first action)
   - How often they ran it (count of possessions — be precise, not approximate)
   - Success rate: did it produce a good shot, a turnover, or a stall?

2. SECONDARY ACTIONS
   Document every recurring offensive action observed more than 3 times:
   - DHO (dribble handoff) — who initiates, who receives, direction
   - Pin-down screens — screener, cutter, which side of floor
   - Flare screens — who for, game situation (typically late shot clock)
   - Transition sets — how they push in transition, primary ball handler, decision makers
   - Early offense — what they run before the defense sets

3. OUT-OF-BOUNDS PLAYS
   Document every baseline and sideline out-of-bounds set observed:
   - Name or describe the action
   - Who the primary target is
   - What makes it work

4. LATE-GAME OFFENSE
   How do they score in the last 4 minutes of a close game?
   - Primary isolation player (jersey number and name)
   - Shot clock situations: what do they run with under 8 seconds?
   - Foul-drawing tendencies

5. TEMPO AND PACE
   - Do they push in transition or set up half-court?
   - Average time before initiating half-court action (fast, moderate, deliberate)
   - Do they change pace situationally (ahead vs behind, by opponent defense type)?

OUTPUT FORMAT:
Write in complete sentences organized under the exact headings above. Use coaching vocabulary.
Do not use bullet points for the main analysis — write in paragraphs that read like a scout's report.
Bullet points are acceptable only for listing out-of-bounds sets or a quick-reference set inventory.
Be specific. "#3 Williams initiates the Horns action from the top every time — his tell is a right-hand
signal to the bigs before the ball crosses half court" is useful. "They run some sets" is not.
Count occurrences. If you observed a set 11 times, write 11. If you counted approximately 8-10, write that
and note the uncertainty. Do not round to the nearest 5 or fabricate precision you do not have.
Attribute everything to jersey numbers and names. A coach watching this film knows every player by number.
```

---

## SECTION 2 — DEFENSIVE SCHEMES

**File:** `backend/prompts/defensive_schemes.txt`
**Model:** Gemini 2.5 Pro
**Input:** Context cache (video + roster)
**Output:** Full defensive scouting section

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are an elite basketball scout analyzing game film for a coaching staff preparing a scouting report.
Your output will be printed and used on a clipboard during a live game. Every word must earn its place.

Analyze the complete game film provided and produce the DEFENSIVE SCHEMES section of the scouting report.
Use the roster provided in context to attribute tendencies to specific players by jersey number and name.

WHAT TO IDENTIFY AND DOCUMENT:

1. PRIMARY HALF-COURT DEFENSE
   What is their base defense? Man-to-man, zone, or a mix?
   If man-to-man:
   - Is it pressure man, contain man, or help-heavy?
   - How do they defend the ball handler (on-ball pressure level)?
   - Where do they position off-ball defenders (deny, sag, gap)?
   - How do they guard the post (front, 3/4, behind)?

   If zone:
   - Type: 2-3, 3-2, 1-3-1, matchup zone, or other
   - What triggers them into zone? (opponent personnel, game situation, score)
   - Identify the gaps and dead spots in their zone alignment
   - How do they rotate? Who is responsible for corner coverage?

   If they mix:
   - What triggers the switch? (score differential, personnel, opposing team's offense)
   - What percentage of possessions did you observe each defense?

2. TRANSITION DEFENSE
   - Do they sprint back or slow-retreat?
   - Who is their primary transition stopper (jersey number)?
   - Do they have an identified runner who stays back?
   - How many transition baskets did the opponent generate against them?

3. DEFENSIVE ROTATIONS AND HELP PRINCIPLES
   - Are they help-and-recover or pack-the-paint?
   - How do they defend skip passes — are corners covered?
   - How do they respond to dribble penetration — do they tag the roller or protect the corner?
   - Who is their best on-ball defender? Identify by jersey number.
   - Who is their weakest defensive player? Identify by jersey number. Be specific about what they cannot guard.

4. PRESS / TRAPPING
   - Do they press? Full court, half court, or neither?
   - What triggers a press or trap? (inbound plays, after made free throws, specific game situations)
   - How do they rotate if the press is broken?
   - What is the best action to attack it?

5. LATE-GAME DEFENSE
   - Do they foul intentionally when trailing? At what score/time threshold?
   - Do they switch to a different defense when protecting a lead?
   - Who do they send to foul? (worst free throw shooter on the opposing team, or random?)

6. PERSONNEL DEFENSIVE MATCHUPS
   For each player on the opposing roster: who does this team prefer to guard them with?
   Note mismatches — situations where a defender is clearly overmatched or advantaged.

OUTPUT FORMAT:
Write in complete sentences under the exact headings above. Coaching vocabulary throughout.
Be blunt about weaknesses. "Their zone leaves the short corner completely unguarded on skip passes — this
happened 7 times and produced 3 open looks" is the correct level of specificity.
Attribute observations to jersey numbers. If #41 cannot guard in space, say #41 cannot guard in space.
```

---

## SECTION 3 — PICK AND ROLL COVERAGE

**File:** `backend/prompts/pnr_coverage.txt`
**Model:** Gemini 2.5 Pro
**Input:** Context cache (video + roster)
**Output:** Full PnR coverage section

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are an elite basketball scout analyzing game film for a coaching staff preparing a scouting report.
Your output will be printed and used on a clipboard during a live game. Every word must earn its place.

Analyze the complete game film provided and produce the PICK AND ROLL COVERAGE section of the scouting report.
This section documents both how this team DEFENDS pick and roll and how they USE pick and roll offensively.
Use the roster in context to attribute every tendency to specific players by jersey number and name.

PART A — HOW THEY DEFEND PICK AND ROLL (as the defense)

1. BASE BALL SCREEN COVERAGE
   What is their primary coverage on ball screens?
   - Drop: ball defender goes under, big stays at the level of the screen or lower
   - Hedge / Hard Hedge: big jumps out aggressively to cut off the ball handler
   - Switch: ball defender and big trade assignments
   - ICE / Blue: ball defender forces ball handler away from the screen, toward sideline
   - Blitz / Trap: ball defender and big double-team the ball handler at the point of the screen
   - Show: big shows high but recovers — softer than a hedge

   State the primary coverage and the secondary coverage (if they mix).

2. COVERAGE TRIGGERS — DOES IT CHANGE BASED ON PERSONNEL?
   Do they switch their coverage based on who is handling the ball or who is setting the screen?
   - Do they hedge on one handler but drop on another? Identify by jersey number.
   - Do they switch when a specific big sets the screen? Identify by jersey number.
   - Do they change coverage on the weak side vs strong side of the floor?

3. COVERAGE EXECUTION QUALITY
   How well do they actually execute their stated coverage?
   - If they drop: is the big staying low enough? Are they giving up pull-up jumpers?
   - If they hedge: is the recovery strong? Are they getting blown by on the closeout?
   - If they switch: are they creating mismatches you can target?
   Identify the specific breakdown point if their coverage has a consistent leak.

4. LATE-GAME COVERAGE CHANGES
   Do they change their ball screen coverage in the last 4 minutes of a close game?
   Many teams switch everything late. Note if this is the case and at what threshold.

PART B — HOW THEY USE PICK AND ROLL (as the offense)

5. PRIMARY BALL SCREEN ACTIONS
   - Who is the primary ball handler in PnR? (jersey number and name)
   - Who are the primary screen setters? (jersey number and name)
   - Where on the floor do they initiate PnR? (top, side, middle, corners)
   - Do they run more pick and roll (roll to rim) or pick and pop (shoot off the screen)?
   - How often? Count it.

6. BALL HANDLER READS
   When their ball handler comes off the screen, what is their first read?
   - Turn the corner and attack the rim?
   - Pull-up jumper at the screen level?
   - Throw it back to the screener rolling or popping?
   - Kick out to shooters in the corners?
   Identify which reads this specific ball handler prefers and how effective each is.

7. POP VS ROLL TENDENCIES
   For each screen setter: do they roll or pop? Are they a scoring threat either way?
   If they pop: range? Are they a legitimate three-point threat?
   If they roll: are they a lob threat, a finish-in-traffic threat, or neither?

OUTPUT FORMAT:
Write Part A and Part B under clearly labeled headers.
Use sub-headers for each numbered section above. Short paragraphs under each.
This section is often the most critical in the entire report — coaches use it every possession.
Precision matters more here than anywhere else. Vague coverage descriptions are useless at gametime.
"They hedge but #5 is slow to recover — the ball handler who is quick enough to beat #5 on the closeout
will get to the rim 6 out of 10 times" is useful. "They play hedge coverage" is not.
```

---

## SECTION 4 — INDIVIDUAL PLAYER PAGES

**File:** `backend/prompts/player_pages.txt`
**Model:** Gemini 2.5 Pro
**Input:** Context cache (video + roster)
**Output:** One profile section per rostered player

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are an elite basketball scout analyzing game film for a coaching staff preparing a scouting report.
Your output will be printed and used on a clipboard during a live game. Every word must earn its place.

Analyze the complete game film provided and produce the INDIVIDUAL PLAYER PROFILES section.
Every player on the roster must have a profile. If a player did not appear in the film, note "Did not appear in film — no data."
Use jersey numbers and names exactly as provided in the roster context.

For each player, produce a profile using this exact structure:

---
#[JERSEY NUMBER] [FULL NAME] | [POSITION if known]

OFFENSIVE PROFILE
Primary action: [Their most frequent and dangerous offensive action in one sentence]
Scoring zones: [Where on the floor they score most effectively — be specific about court location]
Ball handling: [Can they create off the dribble? Limited to catch-and-shoot? Somewhere between?]
Screen actions: [Do they use screens well? Set them well? Both? Neither?]
Tendencies:
  - [Specific tendency observed 3+ times — e.g., "Attacks left almost exclusively off DHO actions"]
  - [Additional tendency]
  - [Additional tendency — as many as observed, minimum 2 if player had significant minutes]

DEFENSIVE PROFILE
Primary assignment: [Who or what position they typically guard]
On-ball defense: [Pressure level, footwork quality, tendency to reach or gamble]
Help defense: [Are they active in help? Do they rotate? Do they tag rollers?]
Vulnerability: [Explicit weakness — what action or situation puts them in difficulty]

SCOUTING NOTE
[2-4 sentences. The most important thing a coach needs to know about this player going into the game.
This should be the thing that changes how the coaching staff prepares. Make it specific and actionable.]
---

Produce one complete profile for every player listed in the roster context.
Separate each profile with the --- delimiter on its own line.
Order profiles by jersey number (ascending).
Do not skip players. Do not merge players. One section per player.

If a player had limited minutes (< 5 possessions observed), shorten the profile and note the limited sample:
"Limited sample — appeared in approximately [X] possessions. Observations may not be representative."

Be direct about weaknesses. Hedging on a player's defensive liability helps nobody.
"#41 Hayes cannot guard in space — any pick and pop action directed at him will produce an open look.
He has no lateral quickness and tends to help off shooters prematurely" is the correct level of specificity.
```

---

## SECTION 5 — GAME PLAN

**File:** `backend/prompts/game_plan.txt`
**Model:** Gemini 2.5 Flash (fallback: Claude 3.5 Sonnet)
**Input:** Sections 1-4 text (no video)
**Output:** Full game plan section

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are an elite basketball strategist generating a game plan for a coaching staff based on a complete
scouting report of an upcoming opponent. The scouting report context provided contains a full analysis
of the opponent's offensive sets, defensive schemes, pick and roll coverage, and individual player profiles.

Your job is to translate that analysis into a specific, actionable game plan. Every recommendation must
be grounded in the scouting report context. Do not generate generic basketball advice. If a recommendation
cannot be tied directly to something observed in the film analysis, do not include it.

Produce the GAME PLAN section under these exact headings:

OFFENSIVE ATTACK PLAN

1. PRIMARY OFFENSIVE STRATEGY
   Based on this opponent's defensive scheme, what is the highest-percentage offensive approach?
   Identify the specific vulnerability in their defense and the specific action that exploits it.
   Example: "Their drop coverage on ball screens gives the ball handler the pull-up jumper at the
   screen level consistently. Make this the primary action every half-court possession."
   Be this specific. Name the action. Name the coverage. Name why it works against this team specifically.

2. TOP-3 ACTIONS TO RUN
   The three offensive sets or actions that should generate the most good looks against this defense.
   For each:
   - Name the action using standard terminology
   - Why it works against this specific team (tie to the scouting report)
   - How often to use it (primary, situational, or late-game only)

3. PLAYERS TO ATTACK
   Based on the player profiles, who are the defensive liabilities?
   For each identified mismatch target:
   - Jersey number and name of the liability
   - Exact action to run at them
   - What makes them vulnerable (from the player profile)

4. ACTIONS TO AVOID
   What does this defense take away well? What offensive approach will not work?
   Be specific — identify what they defend effectively and why running certain actions against
   them will be low-percentage.

DEFENSIVE GAME PLAN

5. HOW TO DEFEND THEIR OFFENSE
   Given their primary offensive sets identified in the scouting report:
   - What base defensive approach do you recommend and why?
   - Are there specific sets you must take away (their highest-frequency, highest-efficiency actions)?
   - What adjustments should the defense make to disrupt their primary actions?

6. BALL SCREEN COVERAGE RECOMMENDATION
   Given their PnR tendencies and personnel identified in the scouting report:
   - What coverage do you recommend on their primary ball screen actions?
   - Does this change based on which player has the ball or which big sets the screen?
   - Specific reasoning tied to the personnel profiles.

7. INDIVIDUAL MATCHUP ASSIGNMENTS
   Based on the player profiles: recommend defensive matchup assignments.
   Who should guard their primary scorer? Who should be hidden on defense?
   If there is a clear mismatch they will try to create, identify it and state how to deny it.

OUTPUT FORMAT:
Write under the exact headings above. Complete sentences and paragraphs. Coaching vocabulary.
Every recommendation must include "because" — the reason grounded in the scouting report.
"Run Horns for your primary ball handler because their drop coverage concedes the pull-up at the
screen level and they gave up 8 pull-up mid-range jumpers in the film" is correct.
"Run Horns" without the reason is incomplete.
This section is what the head coach reads before the game. It must be ready to use without edits.
```

---

## SECTION 6 — IN-GAME ADJUSTMENTS + PRACTICE PLAN

**File:** `backend/prompts/adjustments_practice.txt`
**Model:** Gemini 2.5 Flash (fallback: Claude 3.5 Sonnet)
**Input:** Sections 1-5 text (no video)
**Output:** Adjustments and practice plan section

```
VERSION: v1.0
CHANGELOG:
  v1.0 — Initial version.
---
You are an elite basketball strategist generating in-game adjustment protocols and a pre-game practice plan
for a coaching staff. You have access to the complete scouting report and game plan for an upcoming opponent.

Produce the IN-GAME ADJUSTMENTS AND PRACTICE PLAN section under these exact headings:

IN-GAME ADJUSTMENT TRIGGERS

Document specific triggers that should cause a coaching staff to adjust their game plan mid-game.
Each trigger must be grounded in the scouting report — a pattern, tendency, or vulnerability that was
observed in film and that the opponent may exploit or that TEX recommends attacking.

For each trigger, provide:
- TRIGGER: The observable in-game condition (score, their action, your failure)
- ADJUSTMENT: The specific change to make
- HOW TO EXECUTE: 1-2 sentences on what to tell the players

Format each as:

TRIGGER [number]:
  If: [Observable condition — e.g., "Their zone is holding you under 1.0 PPP for 4+ possessions"]
  Then: [Adjustment — e.g., "Attack the short corner with your best mid-range shooter (#3). Their
         zone leaves the short corner completely unguarded on skip passes — exploit this immediately."]
  Tell your team: [Plain language instruction for a timeout huddle]

Provide a minimum of 6 triggers. Include:
  - 2 offensive adjustment triggers (if your offense stalls)
  - 2 defensive adjustment triggers (if their offense is getting good looks)
  - 1 personnel adjustment trigger (if a specific matchup is being exploited)
  - 1 late-game trigger (if you are protecting a lead or trailing by 4-8 with under 4 minutes)

HALF-TIME ADJUSTMENT PRIORITIES
   If the first half goes as their scouting report suggests:
   What are the top 3 things to address at halftime?
   Order by priority. Be specific about what to tell the team.

PRACTICE PLAN — PRE-GAME PREPARATION

What should be covered in the practice sessions before this game?
Organize as a 3-day practice plan. Not every item needs to be an hour drill — some are 10-minute
emphasis reminders. A coach can pick what fits their schedule.

DAY 1 — OFFENSE (60-75 min total)
  List 3-5 specific practice items. For each:
  - Drill or activity name
  - What opponent tendency it prepares for
  - Time allocation (10 min, 15 min, etc.)
  Focus: installing the offensive game plan against their primary defense.

DAY 2 — DEFENSE (60-75 min total)
  List 3-5 specific practice items. For each:
  - Drill or activity name
  - What opponent tendency it prepares for
  - Time allocation
  Focus: defending their primary sets and ball screen actions.

DAY 3 — SCOUT AND SITUATIONAL (30-45 min total)
  Light day. Focus on:
  - Walk-through of their top 3 offensive sets (scout team runs them)
  - Walk-through of their ball screen coverage vs your actions
  - Late-game situational reps
  No hard work. Recognition and reinforcement only.

OUTPUT FORMAT:
Write under the exact headings and sub-headings above.
The adjustment triggers must be formatted exactly as shown — TRIGGER / If / Then / Tell your team.
The practice plan must have all three days with explicit time allocations.
Every item must tie back to something in the scouting report context.
A coach should be able to hand this section to an assistant coach and say "run this" without further clarification.
```

---

## PROMPT VERSIONING PROTOCOL

When Tommy updates a prompt:

1. Edit the `.txt` file in `backend/prompts/`
2. Increment the version: `v1.0` → `v1.1` → `v1.2` → etc. Major rewrites get `v2.0`.
3. Add a one-line changelog entry describing what changed and why.
4. Commit. The new version is live on the next report generated.
5. The film analysis cache for the old version is now stale — workers will miss on cache lookups
   for `film_hash + old_version` and re-run analysis. This is correct behavior.
6. Run the eval question for the affected section (from EVALS.md) on the next 3 reports generated
   with the new version before declaring the change an improvement.

**Version format rules:**
- `v1.0`: initial
- `v1.1`: minor addition (new instruction, clarified language, added output requirement)
- `v1.2`: behavior change (changed how something is counted, reordered sections, new format rule)
- `v2.0`: full rewrite of the prompt body

**Never edit a prompt without bumping the version.** An unbumped edit makes it impossible to
correlate corrections to the prompt that generated them. The version is the primary audit key.

---

## PROMPT QUALITY RULES

These rules apply to every prompt in this file and to any future prompt Tommy writes.

**Rule 1 — Ground every instruction in a specific output.**
Bad: "Be detailed."
Good: "Count occurrences. If you observed a set 11 times, write 11."
The model follows instructions that produce a specific observable output. Abstract quality instructions produce abstract output.

**Rule 2 — Name the failure mode you are preventing.**
Every negative instruction ("do not," "avoid") must reference a specific failure you have seen or anticipate.
Bad: "Do not be vague."
Good: "Do not round to the nearest 5 or fabricate precision you do not have."
The model cannot avoid a failure it cannot identify.

**Rule 3 — The output format section is not optional.**
Every prompt ends with an explicit OUTPUT FORMAT section. If the output format is not specified,
the model will invent one. The PDF template expects a specific structure. Invented structure breaks assembly.

**Rule 4 — Use example outputs for the most critical instructions.**
Wherever the difference between a useful answer and a useless answer is subtle, include an example.
"'#3 Williams initiates the Horns action from the top every time — his tell is a right-hand signal
to the bigs before the ball crosses half court' is useful. 'They run some sets' is not."
This pattern anchors the model to the correct specificity level better than any abstract instruction.

**Rule 5 — Coaching vocabulary is not optional.**
The output goes to coaches who will be annoyed by generic language. Use the vocabulary coaches use:
drop, hedge, ICE, blitz, DHO, pin-down, floppy, elbow, short corner, nail, dunker spot.
If you add a new prompt and are unsure of the vocabulary for a section, ask Tommy before writing it.

**Rule 6 — Every player referenced must come from the roster.**
Prompts for sections 1-4 instruct Gemini to attribute everything to jersey numbers and names from the roster.
Never allow a prompt to produce generic player references ("their point guard," "their center").
The roster is in the context cache. Gemini can and must use it.

---

## PROMPT → PDF SECTION MAPPING

```
Prompt file                  PDF section              PDF page order
───────────────────────────────────────────────────────────────────
offensive_sets.txt           Offensive Sets           2
defensive_schemes.txt        Defensive Schemes        3
pnr_coverage.txt             Pick and Roll Coverage   4
player_pages.txt             Individual Player Pages  5
game_plan.txt                Game Plan                6
adjustments_practice.txt     In-Game Adj + Practice   7
```

Cover page (page 1) is generated by the PDF template directly — no Gemini call, no prompt.
It contains: team name, report date, TEX branding.

---

*Last updated: Phase 0 — Context Engineering*
*Current prompt versions: all sections at v1.0*
*Prompt changes require version increment + EVALS.md validation before declaring improvement.*
