---
name: frameworks
description: How to fill the workspace canvases honestly from outside-in research: Lean Canvas, AARRR funnel, SWOT, strategy canvas, and the onboarding teardown. Loaded into the strategist agent; use directly when the user asks for a canvas, a framework view, a one-pager or "help me understand this company fast".
user-invocable: true
argument-hint: "<slug> [canvas]"
---

# Filling the canvases

A canvas is a compression of the research, not a new source. The test for every box: could the user
defend it in the room with a graded claim behind it? If not, the box says what is missing.

The per-canvas guides are in `references/frameworks/`. Read the one you are filling:

| Canvas | Guide | Template | Feeds from |
|---|---|---|---|
| Lean Canvas | `references/frameworks/lean-canvas.md` | `templates/frameworks/lean-canvas.md` | business, money, users, market, product |
| AARRR funnel | `references/frameworks/aarrr.md` | `templates/frameworks/aarrr.md` | product walk, users, business, market |
| SWOT | `references/frameworks/swot.md` | `templates/frameworks/swot.md` | all research, product, market |
| Strategy canvas | `references/frameworks/strategy-canvas.md` | `templates/frameworks/strategy-canvas.md` | market factor table |
| Onboarding teardown | `references/frameworks/onboarding-teardown.md` | `templates/product/onboarding-teardown.md` | the walk itself |

## Rules that apply to every canvas

- **Cite by file and grade.** Every line ends with `[grade] file.md`. The reader can trace it.
- **Do not upgrade.** A [R] in research stays [R] in the canvas.
- **One screen.** If it does not fit, cut the weakest-evidenced items.
- **Outside-in honesty.** Some boxes cannot be observed from outside (retention, unit economics,
  internal metrics). Fill them with the best inference, mark [I], and name the observable proxy you
  used. Never leave the reader thinking an inferred number is measured.
- **Their words in the sentiment boxes.** A quote with a link beats a summary.
- **Conflicts stay visible.** Two sources disagreeing are shown as two lines with grades.
- **The teardown is opinionated; the others are not.** Only the onboarding teardown and the point of
  view carry [O]. The canvases describe.

## Order of filling

Lean Canvas first, because it forces the business model into nine boxes and exposes which research
fronts are thin. Then AARRR, which is the product seen as a funnel. Then SWOT, which is the bridge
into the conversation: a hiring manager's "what have you done well, where did the team fail, what
should we be doing, what should we not touch" is a SWOT asked out loud. The strategy canvas last, and
only if the market front produced a factor table.
