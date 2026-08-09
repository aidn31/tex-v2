# Drift Report — Plain-English Summary

*Generated 2026-05-19. Source: docs/drift-report-2026-05-19.md*

## TL;DR

- **Cost model is unreliable.** An architectural shift means we cannot answer "what does one report cost?" Pricing and investor conversations are blocked until we recompute.
- **Architecture story is out of date.** The "smart caching" approach described in the doc was replaced. The replacement may be fine, but no doc tells the new story.
- **A whole preprocessing stage is invisible to most docs.** TEX now turns film into a structured intelligence document before sections get written. Live in production, barely documented.
- **UX doc describes a different product than what shipped.** Copy, payment redirects, and the admin corrections page all diverge.
- **The new safety net is undocumented.** Five recent PRs added secret scanning, CI, dependency monitoring, branch protection — none of it appears in the stack doc.

## Per-Doc Findings

### STACK.md
- **Doc vs code:** Doc lists the libraries, services, and local-dev setup. Code has a different AI library, different local ports, a mis-numbered migration list, and lots of new safety infra absent from the doc.
- **Finding type:** Doc catches up to code.
- **Product impact:** New collaborators set up the wrong local environment, don't know what guardrails exist, may re-introduce a deprecated library.

### ARCHITECTURE.md
- **Doc vs code:** Doc says TEX uses Google's caching to feed video to four parallel sections cheaply — called the cornerstone of unit economics. Code bypasses that caching and feeds preprocessed text instead. The doc has a one-paragraph disclaimer; the rest still tells the old story.
- **Finding type:** Code doing something unexpected — needs a decision on whether the shift is permanent.
- **Product impact:** Anyone reasoning about architecture or cost from this doc is reasoning from a model TEX no longer uses.

### FLOWS.md
- **Doc vs code:** Doc describes screens, buttons, and copy line-by-line. Code differs in copy, payment redirect URL, and missing UI (film delete, retry, upload ETA). The admin corrections page uses a manual form, not the documented quick approve/reject UX.
- **Finding type:** Mixed — copy/URL is doc-behind; the admin UX divergence is code-doing-something-unexpected.
- **Product impact:** The corrections page is the engine of TEX's accuracy moat. Higher friction means fewer corrections and slower compounding.

### AGENTS.md
- **Doc vs code:** Doc defines background-job timeouts, retries, and reliability behaviors. Code has the wrong job count, a silently doubled film-processing timeout, and two documented reliability behaviors that were never built (auto-starting a report after preprocessing; graceful degradation when synthesis fails). The crash-monitoring tool is listed but never turned on.
- **Finding type:** Mixed.
- **Product impact:** Safety features that look planned aren't real. If synthesis fails today, the whole report dies — the doc says it should partially recover.

### COSTS.md
- **Doc vs code:** Doc claims ~$14 per report, three pricing tiers, and that caching makes the math work. Code bypasses caching, added a preprocessing stage that isn't modeled, has a second cache layer that can drop cost to near-zero on regeneration (also not modeled), and two of the three pricing tiers exist only as placeholders.
- **Finding type:** Code doing something unexpected.
- **Product impact:** Every margin number is unreliable. The recompute may be favorable or unfavorable — we don't know until someone does the math.

### PROMPTS.md
- **Doc vs code:** The two preprocessing prompts are six revisions ahead of the doc; the doc's mirrored text is the original baseline. The mechanism that decides when cached work gets thrown away is not explained anywhere.
- **Finding type:** Mostly doc-behind, plus one mechanism never documented.
- **Product impact:** A future prompt edit triggers no re-run when one was needed — or an expensive re-run when one wasn't.

### EVALS.md
- **Doc vs code:** Two pass-conditions can't be met (endpoint name changed; a safety-net write was never built). The rubric log and grading files referenced throughout don't exist; the UI that would create them was never built.
- **Finding type:** Mixed.
- **Product impact:** We can't actually verify whether features work, because the rubric points at files that don't exist.

## Decisions Tommy Needs to Make

### Decision 1: Is text-fed sections permanent?
- **The question:** Was switching from video-fed to text-fed sections a permanent choice or a temporary workaround for a Google quota issue?
- **Why it matters:** Every cost number and four canonical doc rewrites hinge on this.
- **What's needed:** Read the git history around the switch — developer comments call out a Google quota problem.
- **Options:**
  - Permanent — simpler, cheaper, but sections never directly re-read film.
  - Temporary — re-test video-fed later, original doc stays valid.
  - Hybrid — video for some sections (e.g., player pages), text for others. Most accurate, most complex.

### Decision 2: Recompute the cost model now or after launch?
- **The question:** Re-do per-report math before going live, or accept margin uncertainty until a paid coach runs reports?
- **Why it matters:** Pricing tiers and investor conversations need a real number.
- **What's needed:** A working session to recompute against the new pipeline.
- **Options:**
  - Recompute now — costs a day, unblocks pricing.
  - Recompute after first paid coach — accept margin fog until then.
  - Partial recompute — preprocessing only, faster but incomplete.

### Decision 3: Implement or drop the fallback safety net?
- **The question:** Should TEX log every time the backup AI model rescues a failed primary call, or admit in the docs that we don't?
- **Why it matters:** Without tracking, we have no idea if rescues happen 1% or 30% of the time.
- **What's needed:** Decide whether v1 needs rescue-frequency visibility.
- **Options:**
  - Implement the writes — small task, real visibility.
  - Remove the claim from docs — accept the blindspot.

### Decision 4: Admin corrections — doc or shipped?
- **The question:** Doc describes a quick per-claim approve/reject UX. The shipped version is a manual form. Which is canonical?
- **Why it matters:** Higher friction here means fewer corrections, slower moat.
- **What's needed:** Decide if the manual form is acceptable as v1 or if the per-claim UX is required before broader rollout.
- **Options:**
  - Update doc to match the shipped form — accept friction.
  - Build the per-claim UX next — higher volume, slower launch.
  - Phased — pilot the form, build the better UX before broader rollout.

### Decision 5: Auto-trigger reports after preprocessing?
- **The question:** Doc says preprocessing should auto-start a pending report. Code requires the coach to click "generate." Should it auto-start?
- **Why it matters:** Coach experience — auto-trigger means uploading film and coming back to a finished report.
- **Options:**
  - Build auto-trigger — better experience, less control.
  - Remove from doc — explicit click stays a coach action.

## Cross-Cutting Threads

- **Text-fed sections** is the single biggest drift source. It affects ARCHITECTURE, AGENTS, COSTS, and PROMPTS. Decision 1 blocks all four.
- **The preprocessing stage** is second. A whole step was added that almost no doc reflects, and the version mechanism gating re-runs is undocumented.
- **The five-PR hygiene audit** is pure doc-catches-up-to-code. No decision needed — but new collaborators won't know what safety nets are running until one trips.
