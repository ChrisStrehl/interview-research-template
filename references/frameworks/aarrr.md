# AARRR: the product as a funnel

Acquisition, Activation, Retention, Revenue, Referral. The vocabulary a product hiring manager
already thinks in. Each stage answers one question about this product; the reader should be able to
walk the funnel from the canvas alone.

| Stage | The question | What belongs | What does not belong |
|---|---|---|---|
| **Acquisition** | How do new users find the product, and which channel carries the weight? | Store presence with installs and rating, paid channels seen (from the ad pixels and the stack), SEO content, referral share if known, the marketing claim users see first | Vendor lists (name the channel, not the pixel), company revenue |
| **Activation** | What is first value, how many steps and inputs does it take, and where do new users drop? | First value defined in the product's own terms; steps, inputs and minutes to reach it from the walk; the one or two drop points with the reason, marked [O]; the welcome incentive if any | Anything not observed in the walk. If the walk has not reached activation, this stage stays empty and the run is not finished |
| **Retention** | What brings a user back, and what pushes them out? | The mechanics that exist (streaks, daily bonuses, notifications, pending rewards), the exit triggers users name in reviews (bans, delays, thresholds) with first seen and still-true dates | Guesses at retention rates. If nothing can be observed, write the mechanics only |
| **Revenue** | Where does money change hands in the product, and what does the user see of it? | For the user: thresholds, fees, payout methods, welcome bonus. For the business: the per-action mechanism in one line, dated | Valuations, competitor deals, funding, anything already in the Lean Canvas revenue box |
| **Referral** | How does the product get users to bring users? | The mechanic and the payout, verbatim from the product; whether users mention it; any evidence of its weight | Speculation about virality |

## Rules

- Bullets are conclusions with grades and source numbers; `Sources:` under each stage.
- Activation gets the most space because it is the stage the user can speak to from experience.
- Every problem named here carries first seen, last seen and still-true-as-of dates.
- Do not repeat what the Lean Canvas already says. If a fact is in Revenue streams there, it is not
  here; here it is the user-facing side of money.
- The open questions section at the end holds one question per stage at most, only where the
  evidence genuinely stops and the answer would change the read.

## Example, Activation

Good:

```
- First value is the first credited offer; the product rewards it with a $10 welcome bonus. [V][1]
- Sign-up is two fields, email and password; verification by email link; first offer wall visible within a minute. [V][2]
- Likely drop: the identity check that appears before the first cash-out, not the sign-up; German reviews name it as the point where people give up. [O][R][3]

Sources: [1] freecash.com/academy/de/support, 6 Sep 2026 · [2] walk, product/onboarding-teardown.md, steps 1 to 6 · [3] App Store DE reviews 2 to 5 Sep 2026, evidence/users/app-store-reviews.md
```

Bad:

```
- The walk reached signup and stopped there: email and password were entered, then a reCAPTCHA image challenge blocked account creation [V] onboarding-teardown.md.
```

That describes the research, not the product.
