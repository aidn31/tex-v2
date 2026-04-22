# TRAINING.md — How to Train TEX

This document is Tommy's working playbook for improving TEX's scouting intelligence over time. It exists because the question "when is TEX ready?" and the question "how do I make TEX better?" are the same question, and both have concrete answers.

Read this after CLAUDE.md, AI_STRATEGY.md, PROMPTS.md, and EVALS.md. This document ties those together into an actionable training loop.

Updated whenever the training method itself changes. Not updated for individual prompt version bumps — those belong in PROMPTS.md.

---

## 1. WHAT "TRAINING TEX" ACTUALLY MEANS

TEX is built on top of Gemini 2.5 Pro and Flash. Tommy does not train foundation models. Google does. When Tommy says "I want to train TEX," the accurate translation is:

> I want to improve the quality of TEX's scouting output, using the levers I actually control, measured against a concrete standard of "good scouting."

There are three levers available, in order of power and near-term priority:

**Lever 1 — Prompt engineering (90% of the work, years 1-2)**
Rewriting the text of TEX's prompts to get better output from the same underlying Gemini model. This is what makes Cursor, Harvey, Perplexity, and every other applied-AI startup differentiate from raw ChatGPT. It is the most powerful, fastest, and cheapest lever Tommy has.

**Lever 2 — Golden set + evaluation (the measuring stick for lever 1)**
A small, curated set of films where Tommy already knows the ground-truth answers. New prompt versions are scored against this set. Changes that improve scores ship. Changes that don't, don't.

**Lever 3 — Fine-tuning (year 2+, only once the data volume justifies it)**
Taking a base Gemini model and continuing its training on TEX-specific scouting data — corrected reports, validated synthesis documents, expert-labeled film breakdowns. This specializes the model for basketball scouting beyond what a prompt alone can achieve. It is not the starting move. It is the payoff after two years of prompt engineering and correction data accumulation.

The levers NOT available to TEX (and why Tommy should ignore them for now):
- **RLHF (Reinforcement Learning from Human Feedback)** — requires owning the model, millions of preference-comparison labels, and an RL infrastructure team. Not applicable to TEX. The vocabulary exists because it is what OpenAI and Anthropic do internally; it is not what applied startups do.
- **Training a model from scratch** — hundreds of millions of dollars minimum. Not relevant.
- **Retrieval-Augmented Generation (RAG) from a basketball knowledge base** — maybe relevant in Phase 3+ of the AI strategy (see AI_STRATEGY.md), when there is a structured coaching knowledge base to retrieve from. Not a lever to start with.

---

## 2. THE MINDSET — YOU ARE AN AI TRAINER

The mental model for Tommy's role in TEX's development:

> TEX is an entry-level basketball analyst who has watched thousands of games in general but has never been taught a specific organization's scouting standards. Tommy is the head of scouting. His job is to teach the analyst what "great scouting" looks like — not by explaining basketball, but by showing examples, correcting mistakes, and updating the written instructions.

This is the same job an AI trainer at Anthropic, OpenAI, or Cursor does: specifying a standard, building the evaluation harness that measures against it, and iterating until the model hits the standard. What differs is scale — Tommy works against one domain (EYBL scouting) and one user archetype (D2/D3 coaches on the sub-Division I circuit) instead of "all coding tasks" or "all customer service." That narrow focus is an advantage. It means Tommy's golden set of 5 films can tell him what a Cursor-scale golden set of 50,000 tasks tells their team.

The instinct to resist: thinking "I'll know it's good when it feels good." That is not training; that is vibes. Everything Tommy touches in TEX's quality loop has to be written down — the ground truth, the evaluation rubric, the prompt version, the score. Otherwise improvements are unrepeatable and regressions are invisible.

---

## 3. THE FEEDBACK LOOP — HOW TEX GETS BETTER

This is the loop Tommy runs every time he wants to improve a piece of TEX. It is never done. It is the job.

```
1. DEFINE — what specific capability are we improving? (e.g., "identifying PnR coverages correctly")
2. MEASURE — run current prompts against the golden set. Record scores per capability.
3. HYPOTHESIZE — why did we miss what we missed? Usually: the prompt is under-specified, the synthesis is thin, or the section prompt hallucinates when the synthesis is unclear.
4. CHANGE — update ONE prompt (Prompt 0A, Prompt 0B, or one of the six section prompts). Bump its version. Log the change in PROMPTS.md.
5. RE-MEASURE — run the updated prompt against the same golden set. Compare scores to baseline.
6. DECIDE — if scores improved AND no capability regressed, ship. If anything regressed, revert and re-hypothesize.
7. LOG — write the outcome in PROMPTS.md changelog. If shipped, bump the prompt_version the workers use. If reverted, note why.
```

Two rules that make this loop actually work:

**One variable at a time.** Never change two prompts simultaneously while evaluating. If Prompts 0B and Section 3 change together and scores drop, Tommy can't know which caused it. This is the slowest-sounding rule and it is the single biggest accelerator once Tommy internalizes it.

**The golden set is immutable.** The films, their rosters, and the ground-truth answers do not change when scores are bad. Changing the test is how you cheat yourself into thinking you're improving. If the golden set is no longer the right test (e.g., TEX is now ready for harder cases), Tommy graduates to a NEW golden set — he does not edit the existing one.

---

## 4. THE GOLDEN SET — TEX'S MEASURING STICK

The golden set is the single most important artifact Tommy builds for training. Without it, there is no way to distinguish improvement from random drift.

### What it is

A fixed collection of 5 basketball games Tommy knows deeply, each paired with a "ground truth" document Tommy wrote by hand. The ground truth is what a perfect scouting report for that game would contain — the things a good analyst would notice and a great analyst would also.

### The 5 films (target shape)

Pick films where:
- Tommy has personally watched and coached against the opponent
- Opponent style varies across the 5 films (not all motion offense teams, not all zone teams)
- At least 1 film has a clear, strong defensive identity (so the defensive sections can be graded sharply)
- At least 1 film has a signature offensive set that runs repeatedly (so the offensive sections can be graded sharply)
- At least 1 film features a player Tommy knows the tendencies of to the granular level — left-hand finishing, pull-up tells, off-ball cuts — so player pages can be graded sharply
- At least 1 film has a period of disorganized or unusual action (garbage time, blowout, foul trouble) so TEX's handling of ambiguity can be graded

The 5 films live in R2 alongside every other film. They are flagged internally as "golden set" (add a `is_golden` boolean to the films table during the eval work, or maintain a simple list in this file — whichever is cleaner). They never get deleted.

### The ground-truth document

For each film, Tommy writes a scouting document in the same structure as the final TEX PDF. Six sections. Real content. This is Tommy's version of the perfect report. It is what TEX is trying to converge on.

The ground-truth document serves three purposes:

1. **Direct grading.** For each section in a TEX-generated report, Tommy compares output to ground truth. Are the same plays named? The same tendencies identified? The same defensive coverages listed?
2. **Coverage grading.** Did TEX miss anything that Tommy's ground truth contains? Missed observations are the most important failure mode — TEX can't fix what it didn't see.
3. **Hallucination grading.** Did TEX claim anything that contradicts Tommy's ground truth? Hallucinations are the second most important failure mode — false confidence in wrong facts destroys coach trust.

Three-bucket scoring per section:

- **CAPTURED** — TEX identified the claim, and it matches ground truth
- **MISSED** — the claim is in ground truth but not in TEX's output
- **HALLUCINATED** — TEX asserted a claim that is false per ground truth

Score per section = `CAPTURED / (CAPTURED + MISSED)` accuracy, with `HALLUCINATED = 0` as a hard gate. Any section with hallucinations > 2 per page is failing regardless of accuracy score.

### Building the golden set — recommended sequence

This is the work Tommy does between "Phase 4 close" and "Phase 5 start" (agreed plan, 2026-04-19). Order:

1. Pick 5 films. Document why each was chosen (1-2 sentences per film, pasted in this file below).
2. For each film, upload the real roster. Full 12-15 players, not 2-player test data.
3. For each film, write the 6-section ground-truth document. Budget: 2-3 hours per film. This is the most expensive part of the work; it is also the most important. Everything downstream is measured against these documents.
4. Run current-version TEX on each golden film. Save the PDF output. This is your baseline.
5. Grade each PDF against its ground truth using the three-bucket scoring above.
6. Record baseline scores in PROMPTS.md or a new `EVAL_SCORES.md`. This is the number TEX has to beat.

After baseline is established, every prompt change gets tested against all 5 films before it ships. That is non-negotiable.

---

## 4.5. THE INTERNAL GRADING UI — HOW TOMMY SCORES AT SPEED

The golden set is only as useful as the speed at which Tommy can score against it. Manual grading in a spreadsheet takes 3-4 hours per film. Across 5 films × dozens of prompt iterations × quarterly golden/blind refresh, that's the bottleneck that quietly kills the eval loop.

The fix is a purpose-built internal grading UI — one of the highest-leverage investments this product makes. Top applied-AI companies (Cursor, Harvey, Perplexity) all build one in their first few months. TEX builds its own.

### What the grading UI does

A web tool that loads a generated report side-by-side with its ground-truth document and walks Tommy through it claim-by-claim.

```
[ Ground-truth claim: "They initiate Horns from the right side ~60% of the time" ]
[ TEX output:         "They initiate Horns exclusively from the right side" ]

[ Captured ]  [ Missed ]  [ Hallucinated ]    (one click)

Correction text (optional): "TEX overstated. Actual is ~60%, not 100%. Flag as frequency error."
```

On save, the tool automatically writes:

1. **One row per claim into the corrections database.** Same schema as production coach corrections (see AI_STRATEGY.md). Every graded run compounds into the labeled dataset from day one.
2. **A scored summary line into `EVAL_SCORES.md`.** Date, `prompt_version`, captured %, missed %, hallucinated %, total claims, freeform notes. One row per film per run.
3. **A timestamped snapshot of the full graded report to disk.** For later reference when comparing prompt versions or diagnosing regressions.

Target: a full golden-film grading session in 20-40 minutes instead of 3-4 hours. That ~6x speedup is the difference between iterating on prompts twice a week and twice a day, which is the difference between shipping a good product and shipping a great one.

### How it gets built

The existing Phase 4 admin corrections UI (`/admin`) is ~60% of what's needed — it already handles the corrections-database write path. The remaining work is a "golden-set grading mode" that:
- Loads a golden-film ground-truth document alongside the generated report (side-by-side view).
- Adds the captured / missed / hallucinated buttons.
- Auto-writes to `EVAL_SCORES.md` in a standardized format.
- Snapshots the graded report to disk.

Estimated effort: 2-3 days of extension work on top of the existing `/admin` UI.

### When to build it

As soon as the golden set has ≥1 film with ground truth written. You do not wait for all 5 ground-truth documents — building the tool alongside ground truth 1 is the right sequence. Tommy grades ground-truth film 1 in the tool while writing ground truth 2. The tool pays for itself before ground truth 3 is written.

See ROADMAP.md → COMMERCIAL READINESS LADDER → Stage 1 for the same requirement documented on the engineering side.

---

## 5. WHEN IS TEX "READY FOR COACHES"? — CONCRETE LAUNCH CRITERIA

"Ready to sell" is not a gut feeling. It is a set of measurable floors that, once cleared, make the product safe to put in front of paying coaches.

The floors below define the quality bar for **Stage 3 (Design Partner Zero)** and **Stage 4 (Design Partner Cohort)** in the ROADMAP.md Commercial Readiness Ladder — the first coaches touch TEX when these criteria are met, not before. Stage 5 (Early Paid Pilot) and Stage 6 (General Launch) add commercial and infrastructure requirements on top of what's listed here; see ROADMAP for those.

The bar for launching to the first 3-5 hand-picked EYBL coaches (agreed plan, 2026-04-19):

### Quality floors (per golden set scoring)

- **No section in any golden-set report contains more than 2 hallucinated claims per page.** Hallucinations are the single fastest way to destroy a coach's trust. This is the hard gate.
- **Per-section CAPTURED / (CAPTURED + MISSED) accuracy ≥ 70% on the top 3 sections for each golden film.** Top 3 = whichever sections are most important for that particular opponent. For a heavily PnR-driven team, PnR Coverage and Defensive Schemes. For a set-based team, Offensive Sets and Player Pages. Tommy's judgment per film.
- **Sections 5 and 6 (Game Plan, Adjustments) never contradict sections 1-4.** They build on 1-4; they do not invent. Measurable by cross-reference during grading.
- **Every rostered player has a player page with content specific to that player.** No duplicate content across players. No "no data available" on a real film.

### Product floors (not AI, but launch-critical)

- Reports generate in ≤ 15 minutes end-to-end from upload to PDF
- No more than 1 failed report per 20 attempts across the 5 golden films
- Training mode (Phase 4) is functional — Tommy can mark corrections on sections and the corrections save to the corrections table
- Payment flow is real — Stripe live keys active, coaches can pay and receive credits

### Launch mindset

Once the quality floors are cleared, TEX ships to 3-5 coaches at $49.99 per report (first report free per account). Tommy commits to a monthly improvement cadence to these coaches — "the product gets better every 4-6 weeks, measurably." That promise is what makes it okay to launch before TEX is perfect. Coaches can see the Anthropic / OpenAI / Cursor pattern; they are used to "v1 is good, v2 is better, v3 is transformative." TEX operates on the same cadence.

What TEX is NOT at launch:
- Not the final product
- Not perfect on all 6 sections for all opponents
- Not a replacement for a good scouting assistant

What TEX IS at launch:
- Faster than a good scouting assistant
- More consistent than an overworked assistant
- Cheaper than the time cost of doing the breakdown yourself
- Improving on a visible cadence, with every coach's corrections feeding into the next version

---

## 6. THE CONTINUOUS IMPROVEMENT CADENCE — "TEX 1.1, 1.2, 2.0"

After launch, TEX gets better on a release rhythm. This is how Tommy builds the "every couple of months, a better TEX" behavior that he wants to mirror Anthropic and OpenAI model releases.

### Monthly release cycle

Every 4-6 weeks, Tommy ships a versioned improvement. The version number encodes what changed:

- **TEX 1.0** — launch to first coaches
- **TEX 1.1** — first patch release. Usually targeting 1-2 specific golden-set weaknesses revealed in the first month of real-coach reports.
- **TEX 1.2** — same, next month. Compound improvement.
- **TEX 2.0** — major release. Usually triggered by a new capability (e.g., "TEX can now identify every ATO", "TEX handles zone offenses as well as man-to-man"). TEX 2.0 only ships when a full golden-set re-evaluation shows ≥ 10 percentage point improvement over TEX 1.x.
- **TEX 3.0** — first fine-tuned model release (year 2+). Biggest jump, typically driven by accumulated correction data.

The external communication to coaches: release notes in plain English. Written by Tommy, not Claude. Something like:

> **TEX 1.3 — April 2027.** This release improves identification of pick-and-roll coverages. TEX is now 40% more accurate at identifying when opponents use "Ice" vs "Drop" coverage, based on grading against 10 games where we know the ground truth. We also fixed an issue where TEX sometimes invented play names — this should be rare now.

Release notes build trust. They give coaches a reason to keep paying.

### What drives each release

Three inputs, in order of weight:

1. **Corrections data (Phase 4 training mode).** Every time Tommy marks a correction on a real coach's report, that correction is labeled with which section, which prompt version, and what the error was. When a pattern accumulates (e.g., "TEX consistently mis-identifies hedge vs drop") that pattern becomes the target for the next prompt update. This is the primary signal and the reason Phase 4 exists.
2. **Coach feedback.** Every report has an optional feedback form. Star rating + freeform. Tommy reads every response. Patterns across coaches — not individual complaints — drive prompt iteration.
3. **Tommy's own observations.** Tommy runs every new golden-set report himself and grades it. Anything the golden set reveals but corrections data doesn't capture, Tommy catches and fixes.

### Versioning rules

- Prompt versions live in PROMPTS.md. Each prompt's file header has a version string (`# Version: 1.3`).
- When a prompt changes, the version bumps. The old version is preserved in the changelog at the bottom of PROMPTS.md.
- The `report_sections.prompt_version` column records which prompt version generated each section. Essential for diagnosing regressions — "did TEX get worse at Player Pages between 1.1 and 1.2?" is answerable.
- Major releases (X.0) bump all six section prompts simultaneously after a full golden-set re-evaluation. Minor releases (X.Y) can bump individual prompts.

---

## 7. FINE-TUNING — THE YEAR 2+ PAYOFF

Fine-tuning is what unlocks the "TEX knows basketball better than Gemini does" step change. It is not the first lever. It is the endgame for the training mindset.

### What fine-tuning actually is

"Fine-tuning" means taking a pretrained foundation model (a base Gemini model) and continuing its training on a smaller, specialized dataset — in TEX's case, hundreds or thousands of labeled basketball scouting examples. The weights of the model adjust so that it becomes more accurate on the specialized task. It does not lose its general basketball knowledge; it gets better at the specific work TEX does.

Google supports fine-tuning on Gemini via Vertex AI. The interface is: provide a JSONL file of `(prompt, expected_output)` pairs; Google runs the fine-tuning job; the output is a new model ID that TEX calls exactly like regular Gemini.

### What data TEX would fine-tune on

The accumulated corpus of:
- Golden-set films + ground-truth documents (5-20 films by year 2)
- Corrected report sections from Phase 4 training mode (hundreds by year 2)
- Tommy-validated synthesis documents

Each row in the fine-tune dataset looks something like:
```
input:  [synthesis document + roster + section prompt]
output: [the correct scouting section text, as Tommy would write it]
```

Gemini learns to map "this kind of input" → "this kind of high-quality scouting output" in a way that is structurally closer to what Tommy wants than any prompt engineering alone can achieve.

### When to trigger the first fine-tune

Triggers, in order of importance:

1. **Prompt engineering plateaus.** When 3 months of prompt iteration produce < 2 percentage point improvement on the golden set, the ceiling of prompt engineering has been hit. Fine-tuning is the next lever.
2. **Correction data is sufficient.** Minimum viable fine-tune dataset is ~500 high-quality labeled examples. By the time TEX has run 500+ real reports and Tommy has corrected even a fraction of them, this exists.
3. **Cost economics justify it.** Fine-tuning is expensive to run (low hundreds to low thousands per job) and the resulting fine-tuned model costs more per call than base Gemini. The math only works if TEX has revenue to cover it — which means post-launch, post-subscription, proven unit economics.

Earliest realistic timeline: 9-12 months after launch. Not before.

### What fine-tuning is NOT

- Not a substitute for good prompts. Fine-tuned models built on bad prompts produce bad output faster.
- Not a one-time exercise. Fine-tuning will repeat every 6 months as correction data grows. "TEX 3.0, 3.1, 3.2."
- Not RLHF. Fine-tuning is supervised learning on labeled pairs. RLHF is reinforcement learning on preference pairs. Tommy does fine-tuning; he does not do RLHF.

---

## 8. WHAT TOMMY'S WORK ACTUALLY LOOKS LIKE

Translated out of abstract process language, here is what Tommy actually does as TEX's AI trainer, every day, for the next 2+ years:

**Once, at Phase 2 close / Phase 4 close:**
- Pick 5 golden films
- Write 5 ground-truth scouting documents (10-15 hours of work, the heaviest lift)
- Write Prompts 0A and 0B with Claude Code's help on structure, Tommy's input on content
- Build the internal grading UI — 2-3 day extension of the existing `/admin` corrections UI (see §4.5). Ship it alongside ground-truth film 1, not after all 5 are written. It pays for itself before film 3.
- Establish baseline scores on the golden set

**Weekly, ongoing:**
- Read every report from every real coach
- Mark corrections in training mode when TEX gets something wrong
- Tag patterns — "TEX mis-identified defensive rotations 3 times this week"
- Pick the highest-priority prompt to iterate on next

**Monthly, ongoing:**
- Roll up correction patterns into a prompt update
- Test the updated prompt against all 5 golden films
- Ship if scores improve, revert if not
- Update PROMPTS.md with the changelog
- Write release notes for coaches

**Quarterly, ongoing:**
- Revisit the golden set — does it still represent the hardest cases? Add films if TEX has clearly graduated past the current set.
- Audit trends in coach feedback. What do coaches keep asking for that TEX doesn't do?
- Review cost-per-report. Are prompts getting too long? Is Flash fallback rate acceptable?

**Annually (year 2+):**
- Trigger first fine-tune when prompt engineering plateaus
- Re-evaluate the entire product direction against VISION.md — is TEX still on trajectory to "the Cursor of basketball"?

---

## 9. THINGS TOMMY SHOULD NOT DO

Short list of ways the training loop breaks down — things that feel productive but degrade the system.

- **Don't change prompts based on a single report.** N=1 is not a signal. Wait for a pattern across ≥ 3 reports.
- **Don't tune a prompt to fix a single film.** That is overfitting. If 4 films score well and 1 scores badly, the prompt is probably fine; the 1 film is an edge case to note, not a target to optimize for.
- **Don't edit a ground-truth document to match TEX's output.** Ever. That is cheating yourself. The ground truth is what good scouting looks like; TEX's job is to converge on it.
- **Don't run two prompt changes simultaneously.** Always one variable at a time. Slower feels faster.
- **Don't release without re-evaluating the full golden set.** Every release is regression-tested against all 5 films. Non-negotiable.
- **Don't mistake confident output for correct output.** Gemini is extremely fluent. It will hallucinate in polished, expert-sounding prose. The golden set is what catches this; Tommy's gut alone will not.
- **Don't compare TEX to ChatGPT or Claude at launch.** Those are general models with a massive training budget. TEX is a specialized product with a narrow domain. The correct comparison is "TEX vs. a coach doing a scouting breakdown by hand in 4 hours" — and TEX wins that comparison on day one.

---

## 10. REFERENCES

- `AI_STRATEGY.md` — the long-horizon plan for TEX's intelligence (Phases 1-5 of the AI roadmap). Read for context on where fine-tuning fits in the multi-year arc.
- `PROMPTS.md` — the canonical location of all 6 section prompts + (once written) Prompts 0A and 0B. Every prompt version change is logged here.
- `EVALS.md` — the feature-level eval questions (e.g., "Does the PDF contain all 7 sections with correct formatting?"). Orthogonal to golden-set scoring — EVALS.md asks "does the feature work at all?", golden-set scoring asks "does the output match expert ground truth?"
- `COSTS.md` — unit economics. Read when evaluating whether a longer, higher-quality prompt is worth the extra tokens.
- `DECISIONS.md` — architectural decisions. Fine-tuning will trigger one when its time comes.
- `ROADMAP.md` — the current execution state AND the Commercial Readiness Ladder (Stages 1-8) that tracks TEX from golden-set validation through HS/AAU launch, NCAA expansion, and the long-term professional / AI GM product. This training playbook is the quality engine that feeds Stage 1 and powers every stage thereafter.
- `CLAUDE.md` — the overall project rules. This document is subordinate to it.

---

## APPENDIX — THE 5 GOLDEN FILMS (to be filled in)

Tommy fills this in when the golden set is picked. One row per film.

```
# | Opponent                 | Why chosen                                    | Ground-truth doc path
--|--------------------------|-----------------------------------------------|----------------------
1 | TBD                      | TBD                                           | TBD
2 | TBD                      | TBD                                           | TBD
3 | TBD                      | TBD                                           | TBD
4 | TBD                      | TBD                                           | TBD
5 | TBD                      | TBD                                           | TBD
```

---

*Last updated: April 20, 2026 (evening) — Added §4.5 "The Internal Grading UI" documenting the side-by-side grading tool that takes film scoring from 3-4 hours per film to 20-40 minutes. Linked §5 launch criteria to ROADMAP.md Commercial Readiness Ladder (Stages 3-4). Added grading UI to §8 Tommy's one-time work. Original: April 20, first draft written the night the pre-processing pipeline gap was discovered and the training mindset was committed to.*
