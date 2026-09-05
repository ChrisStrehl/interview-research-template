---
name: deepen
description: Extends or refreshes an existing company workspace after the first /research run: add a new input such as a transcript from the next interview round, re-run one front, walk one more flow, add a canvas, record a settled decision, or check what has gone stale. Use whenever the user comes back to a company already under companies/, says "add this", "update", "go deeper on", "re-run", "we decided", or pastes new material about a company that already has a workspace.
argument-hint: "<slug> [what to add or refresh]"
user-invocable: true
---

# /deepen

The workspace grows between interview rounds. Each round adds inputs (a transcript, names, the
hiring manager's own framing of the problem), which change what matters. Re-running everything is
wasteful; re-running nothing leaves the point of view stale.

Read `companies/<slug>/state.json` and `index.md` first. Then do the one thing asked, or offer this
menu in one short message if the user did not say:

1. **Add material.** Copy the file to `inputs/`, spawn `extractor` to refresh `inputs/brief.md`,
   then decide which fronts the new facts touch. A hiring-manager transcript usually touches people,
   culture and the point of view; a pricing change touches business and the Lean Canvas.
2. **Re-run a front.** Spawn the matching agent with the identity block and a narrower brief that
   names what was thin last time (from `evidence/review-log.md`). Then spawn `reviewer` on the
   changed files only, and `strategist` to refresh the canvases that feed from that front.
3. **Walk a flow.** Spawn `product-walker` with the one flow or screen to look at. Append to the
   product map; do not rewrite it.
4. **Add a canvas.** Spawn `strategist` for one canvas. If the canvas needs research that does not
   exist yet (the strategy canvas needs the factor table), run that front first.
5. **Record a decision.** Append to `decisions.md`: the decision, the date, the reasoning, the
   prepared follow-up. Settled decisions are not re-argued.
6. **Stale check.** Anything researched more than thirty days ago, or before a new funding or store
   event, is listed with the front and date. Offer to refresh.

After any change: rewrite the affected part of `point-of-view.md` yourself, update `index.md`,
append to the changelog in `index.md` with the date and what changed, update `state.json`, and run
`python toolbox/render.py companies/<slug>`. Report in at most eight lines.

The trajectory between rounds is itself information. Keep the changelog honest: what the second
transcript changed about the read is exactly the kind of thing worth knowing before the third call.
