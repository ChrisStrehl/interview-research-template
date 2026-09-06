---
paths:
  - "companies/**"
  - "templates/**"
---

# Evidence rules

These apply to every file under `companies/`. They exist because the user repeats this material out
loud, to the people it is about.

## Grades

Every factual claim carries one grade, written inline in square brackets after the claim, followed by
its source and access date.

| Grade | Meaning | Example |
|---|---|---|
| **[V]** Verified | A primary source (the company's own page, a registry filing, the product itself, the store listing) or two independent secondary sources that agree | `Pricing is $35/user/month annual [V] (qase.io/pricing, 4 Aug 2026)` |
| **[R]** Reported | One secondary source: press, an aggregator, a recruiter, a review site, a single post | `~64 employees [R] (one aggregator, Jun 2026)` |
| **[I]** Inferred | Our reasoning from graded facts. Show the working | `Near breakeven [I]: ~50 people on ~$7.5M ARR is ~$150k per head` |
| **[U]** Unknown | Looked for, not found. Say where you looked | `Revenue: [U], searched Latka, Crunchbase snippets, filings (small-company exemption)` |
| **[O]** Opinion | Your own assessment of quality, craft, or fit | `Onboarding is well paced but the paywall arrives before value [O]` |

Rules that follow from the grades:

- **The company's own dated statement is the primary source about its own numbers.** A founder
  saying "we did $320M in 2025" in July 2026 is [R] and it is the best available figure. A third-party
  profile from October 2025 saying "over €100 million" describes 2024, not a contradiction. Align the
  dates before calling anything a contradiction; two figures at two times are a trend.
- **Marketing screenshots are not product evidence.** A screenshot on the company's B2B site showing
  the app is the company's account of its product, never [V] for how the product works. Product
  claims come from the walk or stay [U].

- **Aggregators are Reported, always.** theorg.com, Latka, Tracxn snippets, LinkedIn headcount, Kununu
  aggregates, Crunchbase snippets. They are frequently stale or wrong. Two aggregators that copy each
  other are still one source.
- **Recruiter and job-ad claims are Reported** until checked against something they did not write.
- **A number needs a denominator and a date.** "4.6 stars" is not a finding; "4.6 from 30,752 ratings
  on the German storefront, 5 Sep 2026" is.
- **Absence is a finding.** Record what you searched and did not find. Silently omitting a front you
  could not research is worse than a short honest section.
- **Never fill a gap with a plausible guess.** Leave the [U].
- **Inference is shown, not asserted.** Runway, burn, growth rates, headcount trends and "why they
  are hiring" are always [I] with the arithmetic visible.

## The claims register

`companies/<slug>/claims-register.md` lists the ten to twenty claims that carry the most weight in
the point of view. For each: the claim, its grade, its source, what would verify it, and whether it
is safe to say in the room. Anything the user would state as fact must be [V] here. Anything [R] or
[I] that matters becomes a hypothesis to test in the conversation, phrased as a question.

## Promotion

Raw material goes to `evidence/<front>/`. Only what fits the template headings gets promoted to
`research/<front>.md`. When promoting, keep the grade and the source; drop everything else. Quotes
from users, employees and founders are kept verbatim with a link, because their wording is evidence
and a paraphrase is not.

## Recency

Every file states when it was researched. Data and metrics carry an "as of" date distinct from the
file date. A changelog that stopped, a review pattern that ended, a pricing page that changed are all
findings, so keep the dates attached to the facts.

**Every problem carries three dates**: first seen, last seen, and the "still true as of" date of the
newest dated evidence that shows it. A problem is *current* only if the last evidence is within
thirty days of the research date; otherwise it is *history* and is labelled so. The user will raise
current problems in a room; raising a fixed one costs the interview. Praise follows the same rule.

When a problem is current, say what would show it had been fixed (a release note, a policy change,
a drop in complaint volume) so the next run can check.
