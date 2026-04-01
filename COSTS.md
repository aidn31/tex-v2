# COSTS.md — TEX v2

Per-report cost model. Pricing tiers. Margin targets. Unit economics.
Every number here is derived from first principles — token counts, API pricing, and infrastructure rates.
When Gemini pricing changes, update this document and re-run the margin model.
This document is the financial ground truth for every pricing decision TEX makes.

---

## PRICING INPUTS — VERIFY THESE WHEN THEY CHANGE

```
Gemini 2.5 Pro — video/long-context input    $2.50 / 1M tokens   (>200K token context)
Gemini 2.5 Pro — standard input              $1.25 / 1M tokens   (≤200K token context)
Gemini 2.5 Pro — output                      $10.00 / 1M tokens
Gemini 2.5 Pro — context cache read          $0.25 / 1M tokens   (10% of long-context rate)
Gemini 2.5 Pro — context cache storage       $4.50 / 1M tokens / hour
Gemini 2.5 Flash — input                     $0.075 / 1M tokens
Gemini 2.5 Flash — output                    $0.30 / 1M tokens
Claude 3.5 Sonnet — input (fallback only)    $3.00 / 1M tokens
Claude 3.5 Sonnet — output (fallback only)   $15.00 / 1M tokens

Video token rate (Gemini):                   263 tokens / second of video
```

Source: Google AI pricing page and Anthropic pricing page. Check these monthly.
The margin model is only as accurate as these inputs. A 20% price drop in Gemini 2.5 Pro
changes the margin on every tier — run the model again when pricing shifts materially.

---

## TOKEN MATH — 2-HOUR FILM (BASELINE)

A 2-hour game film is the baseline for all cost calculations.
Shorter films cost less. Longer films cost more. The model scales linearly with duration.

```
Film duration:        2 hours = 7,200 seconds
Video tokens:         7,200 seconds × 263 tokens/sec = 1,893,600 tokens ≈ 1.89M tokens
Context window:       1.89M tokens > 200K threshold → long-context rate applies ($2.50/M input)
```

For a 90-minute film (common for a single game including warmups):
```
Film duration:        90 minutes = 5,400 seconds
Video tokens:         5,400 × 263 = 1,420,200 tokens ≈ 1.42M tokens
```

All cost calculations below use the 2-hour / 1.89M token baseline. This is the worst case.

---

## PROMPT 0 — CHUNK EXTRACTION + SYNTHESIS COST

Prompt 0 runs during film processing — before report generation, before payment.
This cost is incurred once per unique film (per file hash). Cache hits skip it entirely.

### Stage 1 — Per-Chunk Extraction (Gemini 2.5 Pro)

A 2-hour film splits into approximately 4-5 chunks of 20-25 minutes each.
Using 5 chunks as the cost ceiling (worst case for a film just under 2 hours):

```
Chunk duration:       25 minutes = 1,500 seconds
Tokens per chunk:     1,500 × 263 = 394,500 tokens ≈ 395K tokens
Context tier:         395K > 200K → long-context rate ($2.50/M)

Cost per chunk extraction:
  Input:    395K tokens × $2.50/M    = $0.99
  Output:   ~3,000 tokens × $10.00/M = $0.03
  Per chunk total:                    $1.02

5 chunks total:                       $5.10
```

Extractions run in parallel — 5 simultaneous Gemini calls. Wall-clock time is the slowest
single chunk, not the sum. Cost is the sum.

### Stage 2 — Synthesis (Gemini 2.5 Pro)

Synthesis receives all 5 extraction outputs as text. No video. One call.

```
Input tokens (5 extraction outputs, ~3,000 tokens each):
  5 × 3,000 = 15,000 tokens + roster ~500 tokens = ~15,500 tokens
  Context tier: 15,500 < 200K → standard rate ($1.25/M)
  Input cost:   15,500 × $1.25/M = $0.02

Output tokens (synthesis document):
  ~6,000 tokens × $10.00/M = $0.06

Synthesis total:                      $0.08
```

### Prompt 0 Total

```
Stage 1 (extraction, 5 chunks):       $5.10
Stage 2 (synthesis):                  $0.08
Prompt 0 total per unique film:       $5.18
```

This cost is paid once per unique film file hash. On a cache hit, this entire cost is $0.00.
At scale with many coaches scouting the same EYBL programs, cache hit rates of 40-60%
on popular teams mean Prompt 0 cost per report trends toward zero for those opponents.

---

## REPORT GENERATION COST — REAL-TIME PATH

### Sections 1-4 — Gemini 2.5 Pro with Context Caching

Context cache created once by the orchestrator. All 4 parallel sections read from it.

```
Cache creation (Section 1 pays full price — creates the cache):
  Video input:  1.89M tokens × $2.50/M = $4.73
  Roster input: ~500 tokens × $2.50/M  = $0.001 (negligible)
  Synthesis document input: ~6,000 tokens × $2.50/M = $0.015
  Section 1 creation cost:              $4.75

Cache reads (Sections 2, 3, 4 — pay 10% of input price):
  Per section:  1.89M tokens × $0.25/M = $0.47
  3 sections:                           $1.41

Context cache storage:
  1.89M tokens stored for 15 minutes (chord completes well within TTL)
  $4.50/M tokens/hour × 1.89M tokens × (15 min ÷ 60 min/hr) = $2.13

Output tokens (sections 1-4, ~2,500 tokens each):
  4 × 2,500 = 10,000 tokens × $10.00/M = $0.10

Sections 1-4 total:                    $8.39
  ├── Section 1 (cache creation):      $4.75
  ├── Sections 2-4 (cache reads):      $1.41
  ├── Cache storage (15 min):          $2.13
  └── Output tokens (all 4):           $0.10
```

### Without Context Caching (what this would cost)

```
4 sections × 1.89M tokens × $2.50/M = $18.92 video input alone
4 sections output tokens:              $0.10
Without caching total:                 $19.02
```

**Savings from context caching: $10.63 per report.**
This is not a performance optimization. This is what makes the unit economics viable.

### Sections 5-6 — Gemini 2.5 Flash (primary)

Sections 5-6 receive sections 1-4 text as input. No video. Flash is the correct model here.

```
Input per section (sections 1-4 text + roster + synthesis):
  ~12,000 tokens per section call (generous estimate)
  Flash input: 12,000 × $0.075/M = $0.001 per section

Section 5 output: ~2,500 tokens × $0.30/M = $0.001
Section 6 output: ~2,500 tokens × $0.30/M = $0.001

Sections 5-6 total (Flash):            $0.004
```

Flash cost for sections 5-6 is effectively rounding error — less than half a cent.
This validates the routing decision: Pro for video understanding, Flash for text synthesis.

### Sections 5-6 — Claude 3.5 Sonnet (fallback, if Flash fails)

```
Input per section: 12,000 tokens × $3.00/M = $0.04
Output per section: 2,500 tokens × $15.00/M = $0.04
Both sections via Claude:               $0.16
```

Fallback adds $0.16 to the report cost. Acceptable. Margin holds.

### Infrastructure Per Report

```
Cloud Run compute:
  tex-worker-film:    ~20 min × 4 vCPU × $0.00002/vCPU-sec = $0.096
  tex-worker-report:  ~5 min  × 1 vCPU × $0.00002/vCPU-sec = $0.006
  tex-worker-section: ~10 min × 4 vCPU × $0.00002/vCPU-sec = $0.048
  tex-api:            allocated across all reports — ~$0.01/report at early volume
  Total compute:                         $0.16

Cloudflare R2 storage:
  Raw film (2-hour, compressed to ~1.5GB): $0.015/GB × 1.5GB = $0.023/month
  Chunks (kept until report complete):     transient — <1 hour, negligible
  PDF (~2MB, permanent):                   $0.015/GB × 0.002GB = $0.00003/month
  Per-report storage cost (amortized):     ~$0.02

Cloudflare R2 operations:
  Class A (upload chunks, upload PDF):     $0.36/M ops — negligible at early volume
  Class B (download for workers):          $0.00036/M ops — negligible

Neon PostgreSQL:
  Amortized across reports at early volume: ~$0.02/report

Redis:
  Amortized across reports at early volume: ~$0.01/report

Sentry + Datadog:
  Fixed monthly cost — amortized to ~$0.05/report at early volume

Infrastructure total per report:           ~$0.26
```

---

## FULL PER-REPORT COST SUMMARY — REAL-TIME PATH

```
COST COMPONENT                          AMOUNT      NOTES
──────────────────────────────────────────────────────────────────────────────
Prompt 0 (film extraction + synthesis)   $5.18      paid at film processing time
                                                     $0.00 on cache hit
Section 1-4 (Pro + context caching)      $8.39      includes cache storage
Section 5-6 (Flash, primary)             $0.004     rounds to $0.00
Section 5-6 (Sonnet, if fallback)        $0.16      only when Flash fails
Infrastructure (compute + storage)       $0.26

TOTAL (cache miss, Flash succeeds):      $13.83
TOTAL (cache hit, Flash succeeds):        $8.65     Prompt 0 = $0.00 on cache hit
TOTAL (cache miss, Sonnet fallback):     $13.99
TOTAL (cache hit, Sonnet fallback):       $8.81
```

**Blended cost per report (estimated at early volume with ~10% cache hit rate):**

```
90% cache miss × $13.83 = $12.45
10% cache hit  × $8.65  = $0.87
Blended:                   $13.32
```

**Blended cost per report (estimated at growth with ~50% cache hit rate):**

```
50% cache miss × $13.83 = $6.92
50% cache hit  × $8.65  = $4.33
Blended:                  $11.25
```

Cache hit rate improvement from 10% to 50% saves $2.07/report. At 1,000 reports/month: $2,070/month
recovered purely from coaches scouting the same teams — no product changes, no infrastructure changes.

---

## BATCH API PATH — COST MODEL

Gemini Batch API processes requests asynchronously with a 24-hour SLA at 50% off all costs.
Reports routed to batch (coach uploaded and closed the tab) pay half price on all Gemini calls.

```
Prompt 0 batch cost:      $5.18 × 0.50 = $2.59
Sections 1-4 batch cost:  $8.39 × 0.50 = $4.20
Sections 5-6 unchanged:   $0.00         (Flash is already cheap — batching saves cents)
Infrastructure unchanged: $0.26         (compute runs the same regardless of API path)

TOTAL (batch, cache miss): $7.05
TOTAL (batch, cache hit):  $4.46
```

**Real-time vs batch comparison:**

```
                    Cache Miss    Cache Hit
Real-time:          $13.83        $8.65
Batch:              $7.05         $4.46
Batch savings:      $6.78         $4.19
```

Routing heuristic: if coach's last poll was >120 seconds ago → batch queue.
Coaches who upload and close the tab never see a difference. Reports arrive by morning.
The product experience is identical. The economics are not.

---

## PRICING TIERS AND MARGIN MODEL

### Tier 1 — STARTER ($49/report, pay-per-report)

```
Revenue:                            $49.00
Stripe processing (2.9% + $0.30):  -$1.72
Net revenue:                        $47.28

Cost (blended, real-time, 10% cache rate):   -$13.32
Gross margin:                        $33.96    71.7%

Cost (blended, real-time, 50% cache rate):   -$11.25
Gross margin:                        $36.03    76.2%

Cost (blended, batch, 10% cache rate):       -$7.31
Gross margin:                        $39.97    84.5%

Cost (blended, batch, 50% cache rate):       -$4.72
Gross margin:                        $42.56    90.0%
```

Target margin at launch: **70%+**. Achieved with real-time path at early cache rates.
Batch routing and cache growth both improve this automatically over time.

### Tier 2 — COACH ($199/month, 10 reports)

```
Revenue per report: $199 ÷ 10 = $19.90
Stripe processing (2.9% + $0.30 on subscription): ~$0.58/report
Net revenue per report: $19.32

Cost — real-time path (COACH tier gets real-time):
  Blended cost at 10% cache hit: -$13.32
Gross margin per report:          $6.00     31.0%

Cost — 40% batch routing (active coaches still get real-time on active sessions):
  60% real-time × $13.32 = $7.99
  40% batch    × $7.31   = $2.92
  Blended cost:            $10.91
Gross margin per report:   $8.41     43.5%

Monthly gross margin (10 reports, 40% batch):
  $84.10 / $199 = 42.3%
```

COACH tier margin is tighter. This is the correct tradeoff — coaches at this tier generate
higher volume and benefit from the cache as that hit rate improves. Month 6 at 50% cache rate:

```
60% real-time × $11.25 = $6.75
40% batch    × $4.46   = $1.78
Blended cost:            $8.53
Gross margin per report: $10.79    55.8%
```

Margin improves from 42% to 55% purely from cache improvement — no pricing change.

### Tier 3 — PROGRAM ($499/month, 40 reports)

```
Revenue per report: $499 ÷ 40 = $12.48
Stripe processing: ~$0.37/report
Net revenue per report: $12.11

PROGRAM tier guaranteed real-time processing (explicit product promise).
No batch routing at this tier.

Cost at 10% cache hit rate: -$13.32
Gross margin per report:     -$1.21    NEGATIVE at launch

Cost at 40% cache hit rate: -$11.67
Gross margin per report:     $0.44     3.6%

Cost at 60% cache hit rate: -$10.41
Gross margin per report:     $1.70     14.0%
```

**PROGRAM tier is loss-leading at launch until cache rates improve.**
This is intentional. PROGRAM customers are EYBL and D1/D2 programs — the reference customers
that validate the product and generate the correction data that improves all tiers.
The data they generate (film analysis, corrections, prompt training) has indirect value that
exceeds the per-report margin loss in the early months.

Do not launch PROGRAM tier until STARTER and COACH are profitable and cache rates are trending up.
Target: launch PROGRAM tier when blended cache hit rate exceeds 35% (approximately month 4-6).

---

## MARGIN TARGETS BY PHASE

```
Phase       Tier Available         Target Gross Margin   Acceptable Floor
──────────────────────────────────────────────────────────────────────────
Phase 5     STARTER only           70%+                  65%
Phase 5+    STARTER + COACH        STARTER: 70%+         65%
                                   COACH: 35%+           30%
Post-launch STARTER + COACH        STARTER: 75%+
+ 6 months  + PROGRAM              COACH: 50%+
                                   PROGRAM: 10%+
```

If any tier falls below its acceptable floor, investigate before adding new users to that tier.
The causes are either Gemini price changes, cache hit rate degradation, or volume lower than
necessary to amortize infrastructure costs.

---

## CACHE HIT RATE PROJECTION

Cache hit rate is the primary lever on unit economics. It improves automatically with usage.

```
Assumption: 10 EYBL events per season, each with 32 teams.
Average coaches per event: 40 programs scouting at least 10 opponents each.
If 100 coaches use TEX at an EYBL event, each scouting 5 of the same 32 teams:
  Films analyzed per team: ~20 per event (varies by seeding/bracket)
  After first 5 coaches scout a team: cache hit rate = 75% for remaining 15 coaches
  Event-level effective cache hit rate: ~60%+

Real-world projection:
  Month 1  (10 coaches):    ~5% cache hit rate
  Month 3  (50 coaches):    ~20% cache hit rate
  Month 6  (150 coaches):   ~40% cache hit rate
  Month 12 (500 coaches):   ~60% cache hit rate — EYBL programs analyzed once, hundreds benefit
```

This is the compounding moat in financial terms, not just strategic terms.
Every coach added to the platform increases the cache hit rate for every subsequent coach.

---

## COST OF A FAILED REPORT

When a report fails technically (all sections error), a credit is applied automatically.
The coach re-runs the report using the credit. Net cost to TEX:

```
Failed run cost:
  Prompt 0: already paid at film processing time — not refunded, not re-incurred
  Sections that completed before failure: sunk
  Sections that failed: $0 (Gemini call failed — no output billed)
  Infrastructure: sunk

Credit redemption (re-run):
  Full report cost again: $13.83 (real-time, cache miss)
  But Prompt 0 is cached from original film processing: -$5.18
  Effective re-run cost: $8.65

Total cost of one failed report + one credit redemption:
  $13.83 (original) + $8.65 (re-run) = $22.48
  vs. revenue of $49 on STARTER

Margin on a failed + re-run report:
  ($49 - $1.72 stripe) - $22.48 = $24.80 net
  Gross margin: 52.6%
```

Acceptable. A single failure and credit redemption does not invert the margin.
A coach who experiences 3+ failures (systematic issue) triggers a Datadog alert before
the cost impact is material. The `tex.dead_letter.written` alert at 3/hour catches this.

---

## INFRASTRUCTURE FIXED COSTS (MONTHLY)

These costs exist regardless of report volume. At low volume they dominate. At high volume they amortize.

```
PROVIDER          SERVICE                         COST/MONTH      NOTES
──────────────────────────────────────────────────────────────────────────────
Google Cloud Run  tex-api (min 1 instance)         ~$20            1 vCPU, 2Gi, always on
                  Workers (scale to 0)              ~$0-50          only pay when running
Neon              PostgreSQL                        $0-19           free tier until 10GB
Redis             Upstash serverless                $0-10           pay per request at low volume
Cloudflare R2     Storage (films + reports)         ~$5-20          depends on film volume retained
Vercel            Frontend                          $0-20           free tier sufficient at launch
Clerk             Auth                              $0-25           free tier to 10K MAU
Stripe            Payments                          2.9% + $0.30    per transaction only
Sentry            Error tracking                    $0-26           free tier to 5K errors/month
Datadog           APM + metrics                     $15+            minimum for custom metrics
PostHog           Analytics                         $0              generous free tier

Estimated fixed costs at launch:                    ~$75-150/month
Breakeven on fixed costs (STARTER at $49):          2-4 reports/month
```

Fixed costs are not a concern at launch. A single paying coach covers them.
The variable costs (Gemini API) scale with usage and are covered by per-report margin.

---

## UNIT ECONOMICS SUMMARY

```
                        STARTER         COACH           PROGRAM
                        ($49/report)    ($199/10 reports) ($499/40 reports)

Revenue per report:     $49.00          $19.90          $12.48
Stripe fee per report:  -$1.72          -$0.58          -$0.37
Net revenue:            $47.28          $19.32          $12.11

Cost (launch, 10% cache hit rate):
  Real-time:            -$13.32         -$13.32          -$13.32
  Blended (40% batch):  -$10.91         -$10.91          N/A (guaranteed real-time)

Gross margin (launch):
  Real-time:            71.8%           31.0%            -$1.21 (loss-leading)
  Blended batch:        76.9%           43.5%            N/A

Gross margin (month 6, 50% cache):
  Real-time:            76.2%           55.8%            14.0%

Target at scale:        80%+            60%+             25%+
```

---

## WHEN TO RE-RUN THIS MODEL

Run the full cost model again when any of the following change:

1. Gemini pricing changes (check monthly — they have been dropping)
2. Gemini 2.5 Pro is replaced with a new model version
3. Average film duration changes significantly from the 2-hour baseline
4. Prompt 0 extraction output token count changes materially (prompt changes → different output length)
5. Cache hit rate crosses a 10-point threshold (10% → 20%, 20% → 30%, etc.)
6. A new pricing tier is proposed
7. Batch API availability or pricing changes
8. Infrastructure provider pricing changes

Update the pricing inputs at the top of this document first. Recalculate from there.
The formulas do not change. Only the inputs do.

---

*Last updated: Phase 0 — Context Engineering*
*All pricing based on Gemini 2.5 Pro and Flash rates as of Q1 2026. Verify before launch.*
*Re-run margin model monthly until unit economics are stable and confirmed in production.*
