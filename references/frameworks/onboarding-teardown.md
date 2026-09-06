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
7. **The first experiment**: one change, one metric, one reason, sized to two weeks. The line the
   user can say out loud, and the line most likely to be tested by the interviewer, so it rests on
   an observed drop, not an inferred one.

## Rules

- Observation is [V], opinion is [O], on separate lines.
- The product's own words for screens and features.
- No comparison to competitors here; that is the market front.
- No narration of the research. If a flow was not reached, the run pauses; the teardown is not
  written around a gap.
- Under-promise. "I would test whether the identity check can move after the first payout" beats
  "the onboarding is broken".
- Sources under each section as numbered entries; screenshots referenced by relative path.
