# AI_STRATEGY.md — TEX v2

Read this before making any product decision about data, training, or AI capabilities.
This document is the intelligence roadmap — how TEX gets smarter over time, why it compounds
in value while competitors stay flat, and what gets built in what order and why.
Every decision here has a reason. Nothing in this document is aspirational fluff.

---

## THE CORE THESIS

Most AI products are static. They call a model, return an output, done. The product on day 1,000
is exactly as capable as it was on day 1. They are renting intelligence from Google or OpenAI
and adding no proprietary value on top. Any competitor with the same API key builds the same product.

TEX is different by design. Every time the product is used it gets smarter. Every film analyzed,
every correction Tommy makes, every box score ingested, every game plan a coach approves — all
of it accumulates into a proprietary intelligence layer that no competitor can replicate by
signing up for a Gemini API key.

This is the moat. Not the prompts. Not the PDF. Not the UI. The accumulated dataset of
basketball intelligence that compounds with every session.

---

## TWO DISTINCT AI PROBLEMS

TEX solves two fundamentally different AI problems. Conflating them leads to wrong architectural
decisions. They must be understood and built separately.

**Problem 1 — Perception:**
Watch basketball film and accurately describe what is happening at a strategic level.
Identify plays, schemes, coverages, and tendencies. Attribute them to specific players.
Note frequency, situation, and variation.

This is a pattern recognition problem. The solution is prompt engineering plus a corrections
feedback loop. No model training required today.

**Problem 2 — Strategic Reasoning:**
Given what the opponent does AND what the coach's own players can do, generate a specific,
actionable game plan built for this roster against this opponent.

This is a reasoning problem. The solution is structured input data — opponent tendencies from
film, personnel profiles from roster data, statistical matchups from box scores — combined with
a reasoning model that can find the intersections. The quality of the output is directly
proportional to the quality and richness of the inputs.

Phase 1 solves Problem 1. Phases 2-4 progressively solve Problem 2.
Do not attempt to solve Problem 2 before Problem 1 is working reliably.

---

## THE LIVE TRAINING LOOP

TEX trains while the product is live. There is no pause, no offline training cycle, no version
that coaches cannot use while improvements are being made. Training IS usage.

```
Coach uploads film
    → TEX analyzes with current prompts
    → Report generated and delivered
    → Tommy reviews outputs in training mode
    → Tommy corrects wrong claims at play and tendency level
    → Corrections accumulate in corrections table
    → Pattern analyzer identifies systematic errors
    → Tommy updates relevant prompt
    → New prompt_version deployed immediately
    → Next report is more accurate
    → Repeat indefinitely
```

This loop runs on three timescales simultaneously:

```
Prompt updates:       days.   Tommy corrects → pattern emerges → prompt updated → live immediately.
Knowledge base:       weeks.  Tommy encodes plays and schemes → RAG retrieval improves → live immediately.
Model fine-tuning:    years.  Corrections accumulate → dataset matures → fine-tuned model trained offline
                              → deployed as new provider behind the existing abstraction layer.
```

The product never pauses for any of these. Coaches always have the current best version.

**The grading UI is what makes the loop actually run.** The speed of the prompt-update timescale (days, not weeks) only holds if Tommy can grade a full golden-film evaluation in 20-40 minutes instead of hours. The internal grading UI documented in TRAINING.md §4.5 is the tool that enforces this velocity. Every top applied-AI company ships one in their first few months; TEX does too.

---

## WHAT TEX ACTUALLY KNOWS VS WHAT IT LEARNS

**What Gemini already knows at launch:**
Gemini 2.5 Pro was trained on an enormous corpus that includes coaching literature, basketball
analysis articles, film breakdown content, FIBA and NBA documentation, and coaching forums.
It already knows what a Horns set is. It already knows what drop coverage looks like. It already
knows the counter to a hard hedge. The general basketball knowledge exists in the model.

**What TEX teaches it:**
The gap is not general basketball knowledge. The gap is three things:

1. Tommy's specific taxonomy — the exact vocabulary, naming conventions, and categorization
   framework Tommy uses as a D2/EYBL coach. "ICE coverage" means something specific. "Floppy"
   vs "pin-down" is a distinction that matters. Aligning the model to Tommy's framework is
   what corrections accomplish.

2. Level-specific patterns — what Horns looks like at the D2 level is different from what it
   looks like at EYBL. Personnel constraints, execution quality, and variation all differ.
   The model learns these distinctions from corrections grounded in real film at real levels.

3. Proprietary strategic intelligence — the knowledge base Tommy builds over time encoding his
   20 years of coaching experience: which plays beat which coverages, which personnel matchups
   are exploitable, which situational rules hold across levels. This knowledge does not exist
   in any public dataset.

---

## PHASE 1 — PERCEPTION
### Timeline: Launch. Target: first 50 coaches.

**What TEX learns to do:**
Watch a single game film and accurately describe what it sees at a strategic level.
Correct play identification, correct defensive scheme labeling, correct PnR coverage naming,
accurate player tendency attribution. The output of sections 1-4 matches what an experienced
scout would write after watching the same film.

**Corrections at this phase: play level only.**

Tommy reviews section outputs and marks specific claims correct or incorrect.
Corrections at this phase are binary and specific:

```
Claim:          "They run Horns as their primary half-court action"
Correction:     FALSE — "This is a DHO series, not Horns. They never set up at both elbows."

Claim:          "#3 is the primary initiator"
Correction:     TRUE

Claim:          "They ran this set 14 times"
Correction:     FALSE — "I counted 9 times. Gemini is overcounting."
```

Tendency corrections are NOT done at this phase. One game of data is insufficient to validate
a tendency claim. "They run this more in the second half" requires multiple games to confirm.
Building corrections on single-game samples produces noisy data that degrades the training set.

**Personnel at this phase: basic.**

```
jersey_number   text        required
full_name       text        required
position        text        "PG" | "SG" | "SF" | "PF" | "C"
height          text        stored as string — "6'4""
dominant_hand   text        "right" | "left" | "ambidextrous"
role            text        "primary_initiator" | "secondary_handler" | "spacer"
                            | "screener" | "finisher" | "role_player"
notes           text        coach's free text — anything that doesn't fit a field
```

This is enough for Gemini to attribute plays and tendencies to named, described players.
It is not enough for statistical matchup analysis. That comes in Phase 2.

**What gets built in Phase 1:**
- Corrections table and training mode UI
- Play-level correction interface — highlight claim, mark correct/incorrect, write correction
- Prompt versioning system — every report section tracks which prompt version generated it
- Weekly correction pattern analyzer — surfaces systematic errors for Tommy to review
- Prompt update workflow — Tommy updates prompt text, new version deploys, tracked in changelog

**What Phase 1 produces:**
A labeled dataset of correct and incorrect AI claims tied to real film at real levels.
The foundation every subsequent phase builds on. Without this dataset Phase 2 is guesswork.

**Eval question for Phase 1:**
Can Tommy read a TEX scouting report section and agree with 80%+ of the claims without
needing to correct them? If yes, Phase 1 perception is working. If no, the corrections loop
is the only path forward — there is no shortcut.

---

## PHASE 2 — CONTEXT
### Timeline: First 50-100 coaches. Trigger: 3+ games analyzed per team.

**What TEX learns to do:**
Understand tendencies across multiple games, not just describe one game accurately.
Synthesize patterns from 3-5 games into a single coherent scouting picture.
Identify which behaviors are consistent (tendencies) vs which are game-specific (noise).

**Corrections at this phase: play level + tendency level.**

With 3+ games per team, Tommy can now meaningfully correct tendency claims:

```
Claim:          "They initiate Horns from the right side 80% of the time"
Correction:     FALSE — "Across 4 games it's closer to 60/40. One game skewed this."

Claim:          "Their PnR blitz comes when their shot blocker is at the nail"
Correction:     TRUE — "Consistent across all 4 games. Reliable tell."

Claim:          "They slow pace in the second half"
Correction:     FALSE — "Only vs zone. Against man they maintain pace all game."
```

Tendency corrections require context that single-game corrections do not.
The corrections table gains a `game_count` field at this phase — how many games was the
tendency observed across. A tendency based on 4 games has different weight than one based on 1.

**Box score ingestion enters at this phase.**

Box scores are public, structured, and available within hours of every game at every level.
TEX does not wait for coaches to upload stats. TEX pulls them automatically.

```
Sources by level:
D1:           ESPN, NCAA stats, Sports Reference — updated within hours of game end
D2 / D3:      NCAA stats portal — updated within 24 hours
EYBL / Nike:  Nike EYBL stats portal — event-level updates
Other AAU:    Fragmented. Coach upload fallback for events without public stats.
High School:  MaxPreps primary source. Coverage varies by state. Coach upload fallback.
```

**The box score pipeline:**

```
1. Coach creates a team in TEX, tags the level and links to the public stats source
2. Scheduled job runs nightly — checks for new games for all tracked teams
3. New box score found → parse → update player stat profiles automatically
4. Coach notified: "3 new games of data added for Mokan Elite"
5. Next report generation for this team includes accumulated stat context
```

For levels where public stats are unavailable, TEX provides a structured box score upload.
Coach pastes or uploads after a game. TEX parses it. Same pipeline, different ingestion path.

**What automatic box score ingestion produces:**

After 3-5 games per opponent player, TEX has enough to generate basic contextual profiles:

```
#3 Marcus Williams — 5 games
Points:    18.4 PPG
Assists:   4.2 APG
FG%:       44%
3PT%:      38%
Usage:     high — primary initiator

Cross-referenced with film analysis:
Primary scoring zone: mid-range pull-up right side (from film)
Catch-and-shoot three: right wing primary, left corner secondary (from film)
```

The stat profile and the film profile are separate columns that merge at the game plan prompt.
Neither is sufficient alone. Together they give the reasoning model something to work with.

**What gets built in Phase 2:**
- Box score ingestion pipeline — scheduled job, public source scrapers, coach upload fallback
- Multi-game synthesis prompt — sections 1-4 receive context from all analyzed games, not just one
- Tendency correction interface — same UI as Phase 1 but with game_count context displayed
- Basic opponent player profiles — auto-generated from box scores, linked to film attributions
- Cross-game pattern surfacing — "this tendency appeared in 4 of 5 games" vs "appeared once"

**What Phase 2 produces:**
Opponent profiles grounded in multiple games of film plus public statistics.
The coaching staff gets a scouting report that reflects a season's worth of data, not one game.
The stat profiles accumulated here are the input Phase 3 needs for personnel intelligence.

**Eval question for Phase 2:**
Does a TEX scouting report built from 4 games produce a more accurate and specific game plan
than one built from 1 game? If yes, multi-game synthesis is working. Measure by coach feedback
and correction rate — fewer corrections per report means the model is seeing real patterns.

---

## PHASE 3 — PERSONNEL INTELLIGENCE
### Timeline: After product validation. Trigger: 5+ games per team, 50+ active coaches.

**What TEX learns to do:**
Evaluate players automatically from accumulated film and box score data.
Generate detailed personnel profiles without coach input.
Produce game plans that reason across opponent tendencies AND the coach's own roster strengths.

**This is the phase that answers: "how do I attack based on my personnel vs their personnel."**

**Auto-generated player evaluation:**

After 3-5 games of box scores plus film analysis, TEX generates a structured player evaluation
and presents it to the coach for confirmation or correction:

```
Auto-generated evaluation — #3 Marcus Williams:

Scoring profile:
  Primary action:   pull-up mid-range off DHO (observed 23 times across 5 games)
  Secondary action: catch-and-shoot three, right wing
  Dominant hand:    right — rejects left on 87% of isolation possessions

Efficiency by defensive coverage:
  vs man to man:    48% FG  (34 possessions)
  vs zone:          31% FG  ← significant drop — 17 point efficiency loss
  vs switching:     41% FG

Situational usage:
  4th quarter share:  34% of team possessions ← primary closer
  Down 6+:            iso heavy — 61% of his possessions become isolation
  Up 8+:              off-ball spacer — usage drops to 18%

Identified weakness:
  Zone defense drops his efficiency by 17 FG percentage points.
  In 3 of 5 games, zone triggered visible frustration and increased turnover rate.

TEX recommendation:
  Show zone early. Make him prove he can beat it before committing to man.
```

Coach reviews this evaluation. Approves what's correct. Corrects what's wrong. Adds context
("he was injured in game 3 — ignore those numbers"). Every confirmation and correction is
a data point. The evaluation improves with each review cycle.

**The own-roster reasoning prompt:**

Phase 1 and 2 game plans are opponent-only. Phase 3 game plans reason across both sides.

The game plan prompt receives:

```
OPPONENT PROFILE:
  Primary defense: drop coverage on ball screens
  Weak defender: #41, cannot guard in space, drop is too deep
  Primary offensive action: Horns — primary ball handler is #3 Williams
  Zone tendency: 2nd half when protecting a lead

YOUR ROSTER:
  Point guard: 6'2", right-hand dominant, pull-up shooter — 44% FG 17-22 feet
  Power forward: 6'7", strong screener, runs hard to rim, 68% FG at rim
  Shooting guard: 6'4", catch-and-shoot specialist — 41% 3PT from left corner

STATISTICAL MATCHUPS:
  Your PG vs drop coverage: 44% pull-up FG (opponent allows 51% on pull-ups — above his average)
  Your SF vs zone: 41% 3PT (opponent zone allows 38% from corners — above his average)
```

The model finds the overlaps. Where opponent vulnerability meets your personnel strength.
That intersection is the game plan. Not generic advice. Not "attack their drop." Specifically:
"Run Horns for your point guard every half-court possession. Their drop gives him the pull-up.
He shoots 44% there. They allow 51% on pull-ups. That is your highest-value possession."

**The personnel correction loop:**

Tommy reviews auto-generated player evaluations.
Some he confirms. Some he corrects with context that no stat or film can capture.
"TEX flagged Williams as struggling vs zone but he was sick in those two games.
His zone numbers are artificially low. Adjust." That context gets stored.
TEX learns that box score anomalies require coach context to interpret correctly.

**What gets built in Phase 3:**
- Auto-generated player evaluation system — film + box score synthesis per player
- Evaluation confirmation UI in training mode — approve, reject, or annotate each claim
- Expanded roster profile table — structured fields for shooting tendencies, role, strengths
- Statistical matchup engine — cross-references your roster stats against opponent tendencies
- Reasoning prompt for sections 5-6 — receives both opponent profile AND your roster profile

**What Phase 3 produces:**
Game plans that are specific to the coach's personnel. Recommendations grounded in statistical
evidence, not just film observation. The product becomes genuinely different for every coach
because the output reflects their unique roster, not just the opponent.

**Eval question for Phase 3:**
Does the game plan change meaningfully when the coach's roster changes? If a coach with a
pull-up shooting PG gets a different game plan against the same opponent than a coach with
a drive-and-kick PG, Phase 3 is working. Same opponent. Different roster. Different plan.

---

## PHASE 4 — STRATEGIC INTELLIGENCE
### Timeline: Year 2+. Trigger: 1,000+ corrections, 200+ active coaches, full knowledge base.

**What TEX learns to do:**
Think like an elite coordinator. Generate recommendations based on personnel matchups,
cross-game patterns, situational tendencies, and encoded coaching principles — not just
what was seen in the last 5 games.

**The basketball knowledge base:**

Tommy encodes his 20 years of coaching experience into a structured, searchable knowledge base.
Every play, every scheme, every counter, every personnel principle he has ever taught.
LlamaIndex indexes it. At report generation time, the most relevant pieces are retrieved
and injected into the prompts as context.

```
Knowledge base structure:
  plays/
    horns.md              — full description, personnel requirements, counters
    spain_pnr.md          — setup, execution, defensive counters
    floppy.md
    dhо_series.md
    ... (every named offensive action)

  defenses/
    drop_coverage.md      — how to run it, weaknesses, offensive counters
    hard_hedge.md
    switch_all.md
    ice_coverage.md
    2_3_zone.md
    ... (every defensive scheme)

  principles/
    personnel_matchups.md — undersized guard vs drop → pull-up is available
    situational_rules.md  — team shoots 38% from three → do not play zone
    late_game.md          — rules for last 4 minutes in close games
    transition.md         — when to push, when to set up
```

When TEX generates a game plan for an opponent who plays drop coverage, LlamaIndex retrieves
the `drop_coverage.md` entry. The prompt receives the encoded counter-principles alongside
the live film analysis. The model generates recommendations grounded in real tactical knowledge,
not just model intuition about basketball.

**Cross-game pattern recognition:**

At Phase 4 TEX has analyzed enough games to recognize patterns that no single game reveals.

```
Pattern identified across 8 games of Mokan Elite film:
  Their Horns action succeeds at 71% when Williams drives right off the elbow exchange
  Their Horns action fails at 68% when the weak-side big is denied on the pin-down
  → Reliable counter identified from data, not just one game's observation
```

These patterns get surfaced in the scouting report with confidence scores.
A tendency observed in 1 game gets a different confidence label than one observed in 8.
The coach knows what to trust and what to treat as a small sample.

**The fine-tuning path:**

At 1,000+ labeled corrections, TEX has a proprietary dataset of basketball tactical reasoning:
- What the model said
- What the correct answer was
- The category of error
- The level of play
- The coaching context

This dataset can be used to fine-tune a smaller, faster, cheaper model specifically on
basketball tactical reasoning. That model does not replace Gemini for video understanding —
it replaces Gemini Flash for text-only sections 5 and 6. The fine-tuned model has seen
thousands of examples of correct game plan reasoning. Its output is calibrated to Tommy's
framework in a way that a general-purpose model never will be regardless of prompt engineering.

The fine-tuned model runs as a new provider behind the existing AI provider abstraction layer.
No architecture changes. One new provider file. The rest of the system never changes.

```
Today:
  sections 5-6 → Gemini Flash (general purpose, good at text)

After fine-tuning:
  sections 5-6 → TEX-Coach-1 (fine-tuned on 1,000+ basketball corrections, better and cheaper)
```

This is the point where TEX stops being "Gemini with good prompts" and becomes a model that
thinks like Tommy. This is a 2-3 year horizon. The data collection that enables it starts
on day one.

**Eval question for Phase 4:**
Does TEX's game plan recommendation match what an elite coordinator would recommend, grounded
in the specific personnel and statistical matchups available? Measure by Tommy's correction
rate on game plan sections — if Phase 4 is working, Tommy approves more than he corrects.

---

## THE CORRECTIONS TABLE — FULL LIFECYCLE

Corrections are the most valuable data in the entire system. They are never deleted.
They are the proprietary dataset that makes TEX impossible to replicate.

**Phase 1 corrections:** play-level. binary correct/incorrect on specific claims.
**Phase 2 corrections:** play-level + tendency-level. includes game_count context.
**Phase 3 corrections:** play + tendency + player evaluation confirmation/rejection.
**Phase 4 corrections:** all above + strategic reasoning corrections on game plan logic.

```sql
CREATE TABLE corrections (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  report_id        uuid NOT NULL REFERENCES reports(id),
  film_id          uuid NOT NULL REFERENCES films(id),
  section_type     text NOT NULL,
  phase            integer NOT NULL DEFAULT 1,   -- 1 | 2 | 3 | 4
  ai_claim         text NOT NULL,                -- exact text Gemini produced
  is_correct       boolean NOT NULL,
  correct_claim    text,                         -- Tommy's version. null if is_correct = true.
  category         text NOT NULL,
                   -- "set_identification" | "player_attribution" | "frequency_count"
                   -- | "tendency" | "coverage_type" | "personnel_evaluation"
                   -- | "strategic_reasoning"
  game_count       integer,                      -- how many games was this claim based on
  confidence       text NOT NULL DEFAULT 'high', -- Tommy's confidence: high | medium | low
  prompt_version   text NOT NULL,
  admin_notes      text,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now()
  -- no deleted_at. ever. corrections are permanent.
);
```

**The pattern analyzer:**

Runs weekly (or on-demand). Queries corrections grouped by category and prompt_version.
Surfaces: which categories have the highest error rate, which prompt versions improved things,
which types of claims are systematically wrong. Output is a plain-English report for Tommy.

```
Weekly correction analysis — week of March 31 2026:

Total corrections this week:   47
Correct (approved):            31 (66%)
Incorrect (rejected):          16 (34%)

Error breakdown:
  frequency_count:    9 errors (56% of errors) ← Gemini overcounting set frequency
  set_identification: 4 errors (25%)
  player_attribution: 2 errors (12%)
  tendency:           1 error  (6%)

Recommendation:
  frequency_count is the dominant error category this week.
  Review offensive_sets prompt — add explicit instruction about counting methodology.
  Consider: "Count only possessions where the full set is initiated and completed."
```

Tommy reads this, updates the prompt, increments the version. Done in 20 minutes.
Next week's reports are more accurate. The loop runs again.

---

## THE DATA MOAT — WHY THIS COMPOUNDS

A competitor who launches today with the same Gemini API key and the same tech stack has:
- The same general model capability
- No corrections dataset
- No knowledge base
- No player profiles
- No cross-game patterns
- No prompt refinements grounded in real film at real levels

TEX after 12 months of operation has:
- 5,000+ labeled corrections calibrated to Tommy's framework
- A knowledge base encoding 20+ years of coaching intelligence
- Player profiles built from thousands of box scores
- Prompt versions refined by real failure patterns
- Cross-game patterns from hundreds of games at every level

The competitor cannot buy this. They cannot scrape it. They cannot replicate it.
The only way to build it is to operate the product for 12 months with a world-class coach
doing training mode corrections. That is the moat.

**The compounding curve:**

```
Month 1:    Raw Gemini output + basic prompts. Good but generic.
Month 3:    100+ corrections. Prompts refined. Accuracy noticeably better.
Month 6:    500+ corrections. Cross-game patterns emerging. Game plans getting specific.
Month 12:   1,000+ corrections. Knowledge base mature. Personnel intelligence live.
            Product is measurably better than any competitor who launched the same day.
Year 2:     Fine-tuning dataset ready. TEX-Coach-1 model trained. Sections 5-6 outperform
            any general-purpose model on basketball tactical reasoning.
Year 3:     Coaching network effects. Every coach using TEX contributes film data.
            The model has seen more basketball at more levels than any scouting service
            in existence. This is the Second Spectrum / Synergy competitive position.
```

**How this curve maps to the business stages:**

The compounding curve above describes the *intelligence trajectory*. The *commercial trajectory* that runs alongside it is documented in ROADMAP.md → COMMERCIAL READINESS LADDER. The two curves are tightly coupled — the corrections dataset that powers the intelligence curve is generated primarily during ladder Stages 4-7.

```
Intelligence curve       Business stages (ROADMAP ladder)
─────────────────────────────────────────────────────────────────────────
Month 1-3                Stages 3-4 — Design partner zero + cohort. First ~100 corrections.
Month 3-6                Stage 5 — Early paid pilot. First 500 corrections. Retention data.
Month 6-12               Stage 6 — HS/AAU general launch. 1,000+ corrections. Moat visible.
Year 2                   Stage 7 — NCAA expansion. 10,000+ corrections. First fine-tuned model.
Year 3-5                 Stage 8 — Professional / AI GM. 100,000+ corrections. Full platform.
```

Without the ladder, the intelligence curve has no customers feeding it data. Without the intelligence curve, the ladder has no defensible product to sell. The two must advance together; a gap in either collapses the moat.

---

## INVESTOR NARRATIVE — ONE PARAGRAPH

TEX is not an AI product that calls Gemini and wraps it in a PDF. TEX is a basketball
intelligence system that compounds with every game analyzed, every correction made, and
every coach onboarded. The product gets measurably more accurate every week through a live
training loop that runs continuously while coaches use it. The corrections dataset, the
knowledge base, and the cross-game pattern library are proprietary assets that accumulate
value over time and cannot be replicated by a competitor regardless of their API access.
The founding team has the domain expertise to label the data correctly — a non-negotiable
requirement for building a defensible AI system in a specialized domain. TEX is not building
a better scouting report. It is building the data infrastructure that makes every future
version of the scouting report better than the last.

---

## WHAT DOES NOT CHANGE ACROSS PHASES

Regardless of phase, three things remain constant:

1. **The corrections table is never deleted from.** Every label is permanent.
   It is the training data. Treat it accordingly.

2. **Prompt versions are always tracked.** Every report section records which prompt
   version generated it. You can always measure whether a prompt change improved things.

3. **The provider abstraction layer means model changes are config changes.**
   When a better model ships — for video, for text, or as a fine-tuned TEX model —
   it slots in behind the existing interface. The pipeline never changes.
   The intelligence behind it improves continuously.
