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
7. **Improvement candidates**: three to six, ranked by expected effect on the north star, written
   by the strategist after the review so that every one rests on graded evidence and on the KPIs
   section of `frameworks/aarrr.md`. This is the answer to "what would you try or fix?", and the
   test every row must pass is: which KPI goes up, which may go down, and why the trade is worth
   it. A change that adds friction to onboarding is allowed only when the row shows the later KPI
   it raises (lifetime value, first payout completion, reversal rate) and the reasoning for why
   that gain outweighs the activation it costs. A candidate that only removes an annoyance, or only
   adds a safeguard, without a KPI case is not listed. Each row carries the whole chain:
   - *Problem it fixes*: an observed drop from section 4 or a dated review theme, with its grade.
   - *KPI it moves*: the KPI from the AARRR table by name and direction, and the KPI it may hurt.
   - *Reasoning*: the mechanism, not the symptom: why users are lost there, what the product
     assumes, and why the proposed change moves the named KPI. One to three sentences.
   - *Proposed change*: one concrete change to a named screen or rule, in the product's own words.
   - *Cost and risk*: what the change costs in the KPI it may hurt, the fraud, payout or
     compliance exposure it opens, and the measure and comparison that would show the net effect.
   - *Rests on*: the source numbers.
   Good: "KPI: share of accounts reaching a first successful payout within 30 days, up; quiz
   completion, possibly down. Reasoning: the €25 rule is met on the cash-out page after the effort
   is spent, and money the user cannot take out is the highest-volume complaint theme; stating the
   rule where the payout method is chosen sets the expectation before the effort. Change: the
   app's own line, 'unlock withdrawals at 25€', on the earn page above the first offer. Cost and
   risk: some sign-ups stop at the quiz if €25 reads as a wall; measure both rates against the
   four weeks before. Rests on [V][3][7]." Bad: "Improve the cash-out UX", "add gamification", a
   change whose only argument is that users complained, any change to a flow that was not walked,
   a redesign.
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
