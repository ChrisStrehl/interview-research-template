# Onboarding and activation teardown

The one document a hiring manager remembers, because it is about the part of the product every
candidate could have used and almost none did. It is written only after the walk has reached first
value. A teardown of a sign-up form is not a teardown.

## What it must contain

1. **First value, in one sentence**, in the product's own terms, and the moment it appeared in the
   walk.
2. **The path as a table**: step, screen, what it asks, what it gives, inputs, decisions, time,
   screenshot. Then the totals: steps, inputs, decisions, minutes to first value.
3. **What it assumes about the user**: intent, device, patience, prior knowledge. Each is a
   hypothesis the company made; name it in one line.
4. **Where a new user drops**: the two or three steps most likely to lose people, each with the
   reason marked [O], the review theme that supports it marked [R] with dates, and the signal that
   would confirm it. Drops are about real users; a bot check that blocks automation is not a drop
   point unless reviews say humans fail it too.
5. **What it measures**: analytics events seen in the network capture, especially around sign-up
   completion and first value.
6. **What is good**: specific and fair. A teardown that finds only faults is not credible.
7. **Improvement candidates**: three to six, ranked by expected effect over effort, written by the
   strategist after the review so that every one rests on graded evidence. This is the answer to
   "what would you try or fix?" Each row carries the whole chain:
   - *Problem it fixes*: an observed drop from section 4 or a dated review theme, with its grade.
   - *Reasoning*: why users are lost there and what the product currently assumes. One or two
     sentences, the mechanism, not the symptom.
   - *Proposed change*: one concrete change to a named screen or rule, in the product's own words.
   - *Measure*: the metric that moves if the reasoning is right, with the comparison it needs.
   - *Rests on*: the source numbers, and a risk in the same cell when there is one: what the change
     could break (fraud exposure, payout cost, a compliance rule).
   Good: "Show the €25 first-withdrawal rule on the earn page before the first offer, as the app's
   cash-out modal already does; measure the share of accounts that reach €25 within 14 days and
   the volume of 'where is my money' support contacts. Risk: fewer sign-ups finish the quiz if the
   threshold reads as a wall. Rests on [V][3][7]." Bad: "Improve the cash-out UX", "add
   gamification", any change to a flow that was not walked, a redesign.
8. **The first experiment**: candidate 1 sized to two weeks, one change, one metric, one reason.
   The line the user can say out loud, and the line most likely to be tested by the interviewer,
   so it rests on an observed drop, not an inferred one.

## Rules

- Observation is [V], opinion is [O], on separate lines.
- The product's own words for screens and features.
- No comparison to competitors here; that is the market front.
- No narration of the research. If a flow was not reached, the run pauses; the teardown is not
  written around a gap.
- Under-promise. "I would test whether the identity check can move after the first payout" beats
  "the onboarding is broken".
- Sources under each section as numbered entries; screenshots referenced by relative path.
