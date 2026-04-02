# VISION.md — TEX Long-Term Product Vision

This document is the north star. It does not change what gets built in v2.
It exists so that every decision made in v2 points in the right direction.
Read this before making any product decision about scope, features, or roadmap.

---

## WHAT TEX IS IN ONE SENTENCE

TEX is the Cursor of Basketball — the smartest AI in the sport, and the platform
that every serious coach at the high school, AAU/EYBL, college, and professional
level eventually cannot operate without.

---

## THE LONG-TERM VISION

TEX is not a scouting tool. It is not a PDF generator.

It is a complete basketball intelligence platform that replaces the need for
Synergy Sports, Hudl, and FastModel — not immediately, not in v2, but eventually.
Coaches who reach full adoption have no reason to pay for any of those three separately.

The product gets smarter with every game uploaded. Every film analyzed, every correction
Tommy makes, every game plan a coach approves — all of it compounds into a proprietary
intelligence layer that no competitor can replicate by signing up for an API key.

---

## THE PRODUCT MODEL

TEX is one product with multiple modes. Not separate apps. Not separate logins.
One platform, one interface — the coach opens TEX and works in whatever mode
fits what they need that day.

This is the same model as how AI assistants have different modes within one product.
TEX will operate the same way — the coach chooses their mode, TEX routes them
into the right tools for that session.

---

## THE MODES — IN ORDER OF PRIORITY

```
Priority   Mode                  What It Does
──────────────────────────────────────────────────────────────────────────────
1          Opponent Scouting     Upload opponent film. TEX analyzes it and generates
                                 a full scouting report. This is the core loop. Ships first.

2          Game Plan Builder     Take what the scouting found and build a specific,
                                 actionable game plan for that matchup.

3          Practice Planning     Take what the film showed and generate a practice plan
                                 to address it — specifically tailored to what your team
                                 needs to work on before the next game.

4          Self Scout            Analyze your own team's film and tendencies.
                                 Understand what opponents see when they scout you.
                                 Comes after opponent scouting is fully adopted.

5          Individual Dev        Player-specific breakdowns for trainers and players
                                 who want to improve their game with film.
                                 Phase 1: weaknesses and tendencies. Phase 2: drill plans.
                                 Comes after coaches are locked in.

6          Chat / Q&A            Ask TEX anything about an opponent you already scouted
                                 or your own team. Persistent basketball intelligence
                                 that lives in the product between sessions.
```

Modes 1-3 are the coach's core workflow. TEX ships Mode 1 first, then adds modes
as the platform matures. No mode gets built before the one ahead of it is solid.

---

## THE TARGET USER

High-level basketball coaches and programs. In order of initial focus:

- EYBL and AAU circuits
- High school programs
- Lower-level college (D3, D2, smaller D1)
- Upper-level college and professional over time

TEX is built for coaches who take the game seriously. It is not for recreational
or youth coaches who just need something simple. The product earns its price by
delivering professional-grade intelligence to coaches who previously couldn't
afford a full-time analytics staff.

---

## HOW TEX EVOLVES — THREE STAGES

**Stage 1 — TEX Does The Work (v2, now)**
Coach uploads film. TEX generates a complete report. Coach reviews and downloads the PDF.
TEX does the heavy lifting. Coach approves. The PDF is the output.

**Stage 2 — TEX Is Always Open (next)**
The PDF becomes an interactive experience. Coach opens TEX multiple times per week —
not just when they have new film. They ask questions about opponents they already scouted,
refine their game plan, build practice plans, review their own team's tendencies.
TEX becomes a daily tool, not a once-per-opponent transaction.
The PDF becomes the printable export of a living document, not the product itself.

**Stage 3 — TEX Knows Your System (maturity)**
Coach brings their own system and philosophy into TEX. TEX generates a full plan
AND adapts it to how that specific coach coaches — their offensive sets, their
defensive principles, their personnel. TEX knows your roster, knows your system,
knows your opponent, and builds something custom at the intersection of all three.
The product is meaningfully different for every coach who uses it.

---

## THE COACH-TEX RELATIONSHIP

TEX does not assist the coach. TEX does the work and the coach reviews it.

In v2: TEX generates the full game plan. Coach reviews and approves.
At maturity: TEX generates the full plan AND coaches can inject their own
system, adjustments, and philosophy. TEX adapts to the coach — not the other way around.

TEX does not have a personality. Coaches want accuracy, not an AI companion.
The product earns trust through precision and depth of basketball knowledge,
not through tone or character.

---

## THE TRAINING LOOP — TOMMY'S ROLE

Every game uploaded is not just a transaction. It is a training asset.

TEX gets smarter through two mechanisms:
1. Tommy's corrections — labeled data that refines how TEX reads film
2. Cross-game patterns — tendencies that emerge across hundreds of uploaded games

Tommy's labeling load gets lighter over time as the model becomes more accurate
on familiar patterns. But Tommy never fully steps away. New schemes emerge.
The game evolves. When TEX encounters something genuinely new, Tommy corrects it.

Tommy is not the labeler forever — he is the basketball expert who keeps TEX
calibrated to the game as it evolves. No one else can do that job.

---

## THE BUSINESS MODEL

Tiered subscription. Modeled after how Cursor prices — pay more, unlock more capability.

- Base tier: Opponent Scouting
- Higher tiers: Game Plan Builder, Practice Planning, and future modes as they ship

The pricing model gates capability, not volume. A coach on the base tier can
run as many scouting reports as they need. Moving up unlocks new modes.

---

## WHAT THIS MEANS FOR V2

Nothing in v2 changes because of this document. The current build is correct.

What this document does is ensure that every v2 decision is made with the full
picture in mind. The database schema should be able to support multiple report types.
The architecture should not assume the PDF is the only output format forever.
The AI strategy should treat every uploaded game as a long-term training asset,
not a one-time transaction.

V2 ships the scouting loop. Everything else is built on top of it.
Build v2 right and every mode after it is additive, not a rebuild.

---

## THE ONE-PARAGRAPH INVESTOR NARRATIVE

TEX is the Cursor of Basketball. It is the first AI platform built specifically
for how coaches actually work — not a chatbot, not a tagging tool, not a PDF
generator, but a complete intelligence system that gets smarter with every game
uploaded and every correction made. The product starts with opponent scouting
and ships to EYBL and high school coaches first, then expands into game planning,
practice planning, self-scouting, and individual player development. The business
model is tiered subscription — base tier for scouting, higher tiers for the full
platform. The moat is the corrections dataset, the cross-game pattern library,
and the coaching intelligence that compounds with every session. A competitor
with the same API key cannot replicate twelve months of labeled basketball data.
That data is the product. The scouting report is just where it starts.

---

*Last updated: April 2, 2026 — documented from founder session with Tommy.*
