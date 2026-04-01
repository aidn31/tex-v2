# EVALS.md — TEX v2

Evaluation framework. How we know TEX is working.
Every feature has an eval question. Every prompt has an eval rubric.
A task is not done until the eval passes. A prompt update is not an improvement until the eval confirms it.
Read PRD.md for feature definitions. Read PROMPTS.md for prompt versions being evaluated.

---

## TWO TYPES OF EVALS

**Infrastructure evals** — binary. Either it works or it doesn't. No partial credit.
A film either lands in R2 with the correct metadata, or it does not. The eval answer is yes or no.
These run once when the feature is built and again any time something changes that could break it.

**Prompt evals** — scored. Output quality is measured against a rubric on a 1-5 scale.
A prompt update that scores lower than the prior version is not an improvement, regardless of
what it was supposed to fix. Evals run on the next 3 reports after any prompt change before
declaring the change an improvement.

---

## INFRASTRUCTURE EVALS

These match the eval questions in PRD.md. Collected here as a single runnable checklist.

```
FEATURE                         EVAL QUESTION                                           PASS CONDITION
────────────────────────────────────────────────────────────────────────────────────────────────────────
Auth                            Can a coach sign up, log in, and see only their data?   users row in Neon, Clerk JWT valid, zero data from other accounts visible
Clerk webhook                   Does user.created write a users row?                    Row exists with correct clerk_id and email within 5 seconds of signup
Teams                           Can a coach create a team and see it on dashboard?      teams row in Neon with correct user_id, renders on /dashboard
Roster                          Can a coach add 10 players and confirm jersey numbers?  10 rows in roster_players, all scoped to correct team_id and user_id
Duplicate jersey                Does adding a duplicate jersey number return 409?        409 returned, no duplicate row created
Film upload (browser → R2)      Does the file land in R2 at the correct key?            Object exists at films/{user_id}/{film_id}/{filename}, films row shows status=uploaded
Film validation L1 (browser)    Does a .pdf file get rejected before upload starts?     Error shown in UI before any network request, R2 untouched
Film validation L2 (FastAPI)    Does a renamed .pdf with .mp4 extension get rejected?   400 returned from POST /films/upload-url, no presigned URL issued
Film validation L3 (FFprobe)    Does a corrupted video file fail at the worker?         films.status=error with validation message, /tmp cleaned, no Gemini calls made
Film under 1 minute             Does a 30-second clip get rejected?                     films.status=error, message references duration
Film over 3 hours               Does a 4-hour file get rejected?                        films.status=error, message references 3-hour limit
Film processing                 Do chunks land in Gemini with correct DB state?         film_chunks rows with non-null gemini_file_uri and gemini_file_expires_at
/tmp cleanup (success)          Is /tmp empty after a successful film processing task?  ls /tmp on worker shows no {film_id}_* files
/tmp cleanup (failure)          Is /tmp empty after a failed film processing task?      ls /tmp on worker shows no {film_id}_* files after intentional failure
URI expiry check                Does an expired URI trigger re-upload from R2?          Set gemini_file_expires_at to past in DB, confirm re-upload runs, new URI saved
Context cache                   Is cache created by orchestrator, deleted after done?   Cache URI present in logs before chord fires, absent after sections complete
Parallel sections               Do sections 1-4 complete faster than sequential?        4 sections complete in ~10 min on 2-hr film vs ~34 min sequential baseline
Section fallback                Does Claude fire when Flash is unavailable?             With Flash endpoint blocked: fallback_events row written, section completes via Claude
Dead letter                     Does a task that exhausts retries write to dead_letter? After 3 forced failures: dead_letter_tasks row with full args, film_id, user_id
PDF export                      Does the PDF contain all 7 sections?                   Cover + 6 sections present, all rostered players in section 4, no blank pages
Payment — free first report     Does first report skip Stripe?                          reports row created without checkout URL returned, report generates
Payment — paid second report    Does second report return a checkout URL?               checkout_url in response, report not created until webhook fires
Payment — credit                Does a credit skip Stripe checkout?                     report_credits > 0: report generates immediately, credits decremented by 1
Failure credit                  Does a failed report apply a credit automatically?      report.status=error → users.report_credits incremented, notification written
Training mode admin gate        Can a non-admin access /admin/* routes?                 403 returned for every /admin route with a non-admin Clerk JWT
Correction save                 Does a correction save with exact ai_claim text?        corrections row matches submitted text exactly, prompt_version matches report
Notification                    Does a coach see a notification when report is ready?   notifications row written, unread count on dashboard increments
Startup recovery                Does recover_stuck_jobs() re-enqueue stuck films?       Film with status=processing and updated_at > 2 hours ago gets re-enqueued on worker boot
Redis AOF                       Does Redis recover queued tasks after a restart?        Queue a task, restart Redis, confirm task is still in queue and executes
```

**How to run an infrastructure eval:**
Each eval has a specific action that produces a verifiable state in Neon, R2, or logs.
Run the action, query the expected state, compare. If the state matches, the eval passes.
Do not mark a feature done based on "it seemed to work." Query the database or check the bucket.

---

## PROMPT EVALS

### EVAL PHILOSOPHY

Prompt quality cannot be evaluated by reading the output and deciding it "seems good."
That is not an eval. That is an impression. Impressions are wrong at scale.

Every prompt eval has a rubric with 5 dimensions scored 1-5.
A prompt scores its overall rating as the average across dimensions.
A prompt with an overall score below 3.5 is failing. Fix it before the next report ships on it.
A prompt update that drops any dimension by more than 0.5 is a regression, regardless of other gains.

**Scoring scale:**
```
5 — Exceptional. A senior scout could use this output without edits.
4 — Good. Minor cleanup needed but the substance is correct and complete.
3 — Acceptable. Significant cleanup needed but the foundation is there.
2 — Poor. Major errors or omissions. Would mislead a coaching staff.
1 — Failing. Output is wrong, fabricated, or structurally broken.
```

**Eval cadence:**
- On first deploy of a prompt: run against 3 reports, score all 3, take the average.
- After any prompt update: run against the next 3 reports, compare to prior version average.
- Weekly: review correction data from SCHEMA.md pattern analyzer for the current prompt version.
  High error rates in a category signal a dimension that needs a prompt fix.

---

### PROMPT 0A — CHUNK EXTRACTION EVAL

**File:** `backend/prompts/chunk_extraction.txt`
**Eval question:** Does the extraction log from a single chunk contain accurate, structured observation data that a synthesis prompt can reliably aggregate?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Count accuracy** | Occurrence counts match Tommy's manual recount within ±1 | Counts are off by 2-3 | Counts are fabricated or wildly wrong |
| **Attribution accuracy** | All actions attributed to correct jersey numbers | 1-2 wrong jersey numbers | Multiple wrong attributions or jersey numbers not used |
| **Vocabulary consistency** | Standard coaching terms used correctly | Mix of standard and invented terms | Invented terminology that will block synthesis reconciliation |
| **Uncertainty flagging** | All genuine uncertainties surfaced in FLAGGED section | Some uncertainties surfaced | No flags despite observable ambiguities in the film |
| **Structural compliance** | All required sections present with correct headers | 1-2 sections missing or malformed | Output does not follow the required format |

**Pass threshold:** Average ≥ 3.5 across all 5 dimensions on 3 consecutive chunks.

**Most common failure modes to watch for:**
- Gemini hallucinates jersey numbers that are not in the roster — catch this by cross-referencing every jersey number in the output against the roster in context
- Counts are optimistic (overcounting) because Gemini includes partial or failed actions — the prompt instructs counting only completed set initiations; if overcounting persists, add an explicit definition of what counts as one occurrence
- Uncertainty flags are absent — Gemini prefers confident output; if the FLAGGED section is consistently empty on complex film, add a prompt instruction requiring a minimum of one flag per chunk

---

### PROMPT 0B — CHUNK SYNTHESIS EVAL

**File:** `backend/prompts/chunk_synthesis.txt`
**Eval question:** Does the synthesis document accurately represent the full game with reconciled counts, unified vocabulary, and correctly tagged confidence levels?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Aggregation accuracy** | Total counts match sum of chunk extraction counts exactly | Off by 1-2 across all actions | Counts do not match extractions — synthesis invented numbers |
| **Vocabulary reconciliation** | All reconciliation decisions documented with reasoning | Some reconciliations undocumented | No reconciliation — duplicate entries for the same action |
| **Timeline preservation** | Scheme/coverage changes documented with game context | Changes noted without timing | Timeline collapsed — "they played a mix" type flattening |
| **Contradiction handling** | Every contradiction surfaced and resolved with confidence level | Some contradictions resolved silently | Contradictions silently resolved or ignored |
| **Confidence tagging** | [CONFIRMED]/[LIKELY]/[SINGLE GAME SIGNAL] tags accurate | Tags present but miscalibrated | No confidence tags |

**Pass threshold:** Average ≥ 4.0 across all 5 dimensions. Higher bar than extraction because synthesis errors propagate into all 6 report sections.

**How to verify aggregation accuracy:**
Sum the counts from all chunk extraction outputs manually for the top 3 actions.
Compare to synthesis totals. They must match exactly per Rule 1 in the synthesis prompt.
If they do not match, the synthesis is inventing or dropping counts. This is a critical failure.

**How to verify timeline preservation:**
Watch the last 5 minutes of the film. Identify any scheme change.
Confirm the synthesis document documents it with a timestamp reference.
If a visible scheme change is absent from the synthesis, timeline preservation is failing.

---

### SECTION 1 — OFFENSIVE SETS EVAL

**File:** `backend/prompts/offensive_sets.txt`
**Eval question:** Does a coach reading the Offensive Sets section have an accurate, complete picture of what this opponent runs offensively — with counts, personnel, and game plan implications?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Set identification accuracy** | All primary sets correctly named using coaching vocabulary | 1-2 sets misidentified or wrongly named | Primary set wrong — the section is built on a misidentification |
| **Count accuracy** | Occurrence counts match Tommy's recount within ±1 | Off by 2-3 | Fabricated or no counts provided |
| **Personnel attribution** | Every action attributed to correct jersey numbers from roster | 1-2 misattributions | Jersey numbers absent or wrong throughout |
| **Counter and variation coverage** | Counters off primary actions documented | Counters mentioned but vague | No counters documented |
| **Output usability** | Section reads like a scout's report — complete sentences, coaching vocabulary, no generic advice | Readable but missing specificity | Generic, could apply to any team |

**Pass threshold:** Average ≥ 3.5. Count accuracy and set identification below 3 individually triggers a prompt fix regardless of overall average.

**Tommy's manual check (run on every new prompt version):**
Watch 10 consecutive half-court possessions of the film being evaluated.
Count every occurrence of the primary set TEX identifies.
If Tommy's count differs from TEX's count by more than 2, count accuracy is failing.
This takes 15 minutes and is non-negotiable before declaring a prompt version improved.

---

### SECTION 2 — DEFENSIVE SCHEMES EVAL

**File:** `backend/prompts/defensive_schemes.txt`
**Eval question:** Does a coach reading the Defensive Schemes section know exactly what defense they will face, where the gaps are, and which players are the liabilities?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Scheme identification** | Base defense correctly identified with percentage breakdown | Correctly identified but no percentages | Wrong base defense identified |
| **Scheme change documentation** | All defensive adjustments documented with triggers | Adjustments noted but triggers missing | No scheme changes documented despite visible ones in film |
| **Liability identification** | Weakest defender identified by jersey number with specific vulnerability | Weak defenders noted without specific vulnerability | No defensive liabilities identified |
| **Help principle accuracy** | Help rotation principles described accurately and specifically | Described but vague | Absent or wrong |
| **Actionability** | A coach can draw up 2-3 specific actions to attack this defense after reading | Some attack options implied | No actionable intel — describes defense without identifying how to beat it |

**Pass threshold:** Average ≥ 3.5. Scheme identification below 3 triggers immediate prompt fix.

---

### SECTION 3 — PICK AND ROLL COVERAGE EVAL

**File:** `backend/prompts/pnr_coverage.txt`
**Eval question:** Does a coach reading the PnR section know exactly what coverage they will face in ball screen actions and exactly how to attack it?

This is the highest-stakes section in the report. PnR actions represent 30-50% of possessions
at every level above high school. A wrong coverage identification sends a coaching staff into a
game with a fundamentally broken game plan.

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Coverage identification** | Primary coverage correctly named (drop/hedge/switch/ICE/blitz) | Correct coverage but wrong secondary | Wrong primary coverage — coaching staff will prepare the wrong counters |
| **Personnel-based variation** | Coverage changes by matchup documented with jersey numbers | Variations noted without personnel specificity | No variations documented despite visible ones |
| **Execution quality assessment** | Specific breakdown point identified with evidence | Breakdown noted without specificity | "They execute well" or "they have trouble sometimes" — no specificity |
| **Offensive PnR tendencies** | Ball handler reads, screener pop/roll preference documented with counts | Present but incomplete | Absent |
| **Defensive and offensive coverage present** | Both Part A and Part B complete | One part significantly shorter than the other | Only one part present |

**Pass threshold:** Average ≥ 4.0. Coverage identification below 3 is a critical failure — triggers immediate prompt fix and manual review of any reports generated with that prompt version.

**Tommy's manual check:**
Watch 10 ball screen possessions. Identify the coverage on each.
The modal coverage is the "primary coverage." If TEX identifies a different primary coverage, this is a critical failure.

---

### SECTION 4 — INDIVIDUAL PLAYER PAGES EVAL

**File:** `backend/prompts/player_pages.txt`
**Eval question:** Does each player profile give a coaching staff an accurate, actionable picture of that player — offensive tendencies, defensive liabilities, and the one thing they must know going into the game?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Completeness** | Every rostered player has a profile | 1-2 players missing | Multiple players missing |
| **Offensive profile accuracy** | Scoring zones, dominant hand, primary actions correct | 1-2 errors | Primary action wrong — would send defense to the wrong spot |
| **Defensive liability specificity** | Explicit vulnerability with evidence ("he gives up the corner 3 on skip passes — 4 times in film") | Liability noted without evidence | "He is a below-average defender" — no specific vulnerability |
| **Scouting note quality** | The note changes how the staff prepares — specific, actionable, tied to the film | Generic positive or negative assessment | Absent or content-free ("he is a key player") |
| **Jersey number accuracy** | All profiles correctly attributed to the right player | 1 misattribution | Multiple misattributions — profiles swapped between players |

**Pass threshold:** Average ≥ 3.5. Jersey number accuracy below 4 triggers immediate fix — a misattributed profile actively misleads the coaching staff.

**How to check jersey number accuracy:**
Pick 3 players at random from the report. Watch 5 possessions per player in the film.
Confirm the scouting note matches what you see on film for that jersey number.

---

### SECTION 5 — GAME PLAN EVAL

**File:** `backend/prompts/game_plan.txt`
**Eval question:** Does a head coach reading the Game Plan section have a specific, film-grounded offensive and defensive approach ready to install — with every recommendation tied to a "because"?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Grounding in scouting report** | Every recommendation cites specific evidence from sections 1-4 | Most recommendations cited | Recommendations that could apply to any team — not grounded in this opponent |
| **Offensive specificity** | Top-3 actions named with specific reasoning for this defense | Actions named but reasoning generic | "Run your best plays" type content |
| **Attack-the-liability clarity** | Specific player targets identified with the exact action to run at them | Targets identified without specific action | No player-specific attack plan |
| **Defensive recommendation quality** | Coverage recommendation with specific reasoning tied to their PnR personnel | Coverage recommended without reasoning | Generic defensive advice |
| **Avoid list accuracy** | "Actions to avoid" match what this defense actually takes away | Partially accurate | Absent or recommends avoiding things this defense does not actually stop |

**Pass threshold:** Average ≥ 3.5. Grounding score below 3 means the game plan is not using the scouting report — it is generating generic basketball content. This is a critical failure.

**Tommy's check:**
Read the offensive attack plan. For each recommendation, ask: "Would this be in a game plan against any good defense, or is it specific to what we know about this team?"
If 2+ recommendations would apply to any opponent, the grounding score is 2 or below.

---

### SECTION 6 — IN-GAME ADJUSTMENTS + PRACTICE PLAN EVAL

**File:** `backend/prompts/adjustments_practice.txt`
**Eval question:** Can a coaching staff hand the Adjustments section to an assistant coach and say "run this" without further clarification?

**Rubric:**

| Dimension | Score 5 | Score 3 | Score 1 |
|---|---|---|---|
| **Trigger specificity** | TRIGGER/If/Then format followed, conditions are observable in-game | Format followed but conditions are vague | Format not followed or conditions are not observable during a game |
| **Adjustment actionability** | "Tell your team" instruction is usable in a 60-second timeout | Actionable but too long for a timeout | Abstract — coaching staff cannot implement this mid-game |
| **Practice plan specificity** | Each drill tied to a specific opponent tendency with time allocation | Drills listed without opponent tie or time allocation | Generic drills that could appear in any practice plan |
| **Coverage of failure modes** | Offensive, defensive, personnel, and late-game triggers all present | 3 of 4 covered | 1-2 covered |
| **Halftime priorities quality** | 3 specific priorities that a staff could implement in a 10-minute halftime | Present but generic | Absent or too many (more than 3 — not prioritized) |

**Pass threshold:** Average ≥ 3.5.

---

## FULL-PIPELINE EVAL

Run this after every complete system change (new prompt version, infrastructure change, Gemini model update).
This is the end-to-end test. Everything else is a unit test.

**Test input:** A real game film that Tommy has personally scouted. He knows what the team runs.
**Test output:** A complete TEX scouting report PDF.
**Evaluator:** Tommy.

**Questions Tommy answers after reading the full report:**

```
1. Did TEX correctly identify the opponent's primary offensive set?                   Y / N
2. Did TEX correctly identify the opponent's base defensive scheme?                   Y / N
3. Did TEX correctly identify the primary ball screen coverage?                       Y / N
4. Are the occurrence counts within ±2 of your manual counts for the top 3 actions?  Y / N
5. Did TEX correctly identify the weakest defensive player?                           Y / N
6. Would you use this game plan as a starting point for your actual game prep?        Y / N
7. Did any section contain information that would actively mislead your staff?        Y / N
8. How many claims did you need to correct in training mode after reading?            [count]
9. How long did it take to read the full report and feel prepared?                    [minutes]
10. Would you pay $49 for this report?                                                Y / N
```

**Pass conditions:**
- Questions 1-5: at least 4 of 5 yes
- Question 6: yes
- Question 7: no (any yes here is a P0 issue regardless of other scores)
- Question 8: fewer than 10 corrections needed
- Question 9: under 20 minutes to feel prepared
- Question 10: yes

If the full-pipeline eval does not pass, the system is not ready for real coaches regardless of
what individual prompt evals show. Unit tests passing does not mean the product works.

---

## EVAL TRACKING

Tommy records eval scores after each run in a simple log. Format:

```
DATE        PROMPT          VERSION   REPORTS_EVALUATED   DIM1  DIM2  DIM3  DIM4  DIM5  AVG   PASS
2026-04-01  offensive_sets  v1.0      3                   3.7   4.0   3.3   3.0   4.0   3.6   Y
2026-04-08  offensive_sets  v1.1      3                   4.0   4.0   3.7   3.3   4.3   3.9   Y   +0.3 improvement
2026-04-08  pnr_coverage    v1.0      3                   2.7   3.3   3.0   3.7   4.0   3.3   N   coverage_id failing
```

This log lives in `backend/evals/eval_log.csv`. Claude Code updates it after every eval run.
Tommy can override any score with a note — his domain expertise overrides automated assessment.

---

## WHAT MAKES AN EVAL QUESTION GOOD

An eval question is good if:
1. It has a binary or numeric answer — not "did it seem good?"
2. The answer can be verified without asking the model to evaluate itself
3. A failing answer points to a specific fix

An eval question is bad if:
1. It is answered by reading the output and deciding it is "high quality"
2. It can be passed by a hallucinated but plausible-sounding output
3. Passing it does not mean the feature actually works for a coach

The eval question "Does the report look professional?" is bad. It fails all three criteria.
The eval question "Does the primary ball screen coverage match what Tommy observes in 10 manual possessions?" is good. It is verifiable, human-grounded, and failure points to a specific prompt fix.

---

*Last updated: Phase 0 — Context Engineering*
*Eval framework version: v1.0*
*All prompt evals require Tommy as the domain evaluator. Automated scoring is a supplement, not a replacement.*
