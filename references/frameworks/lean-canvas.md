# Lean Canvas: what each box is for

One page, nine boxes, the business model as the company appears to run it. A reader who knows
nothing about the company should understand from the canvas alone how it makes money and for whom.
Every bullet is a conclusion. Sources sit under the box.

## The boxes

| Box | The question it answers | What belongs | What does not belong |
|---|---|---|---|
| **Problem** | What pain do the paying customers have, and what pain do the users have? | One line per real problem, from the customer's side. For a two-sided product: the payer's problem and the user's problem, labelled | Product features, the company's marketing headline, complaints about the product (those are weaknesses) |
| **Customer segments** | Who pays, and who uses? | Named segments: "mobile game studios in the top 10 to 30 grossing per market", "consumers who trade time for cash, mostly under 30, DE/US/UK". Add counts only when they belong to that segment and are dated | Total user counts with no segment, vague words like "everyone who plays games" |
| **Unique value proposition** | Why do customers choose this over the alternative? In one sentence per side | The company's own headline if it is honest, or the version users repeat in reviews. Say whether the two match | Feature lists, comparisons to named competitors (market canvas) |
| **Solution** | What does the product do to solve the problems above? | Three to five capabilities in the product's own words: "offer wall with per-milestone cash rewards", "instant cash-out to PayPal, bank and crypto". One line each | How the product is built, screenshots, what was or was not observed |
| **Channels** | How do users and customers arrive? | The actual channels with weight: app stores, paid UA, referral, SEO content, direct sales. State which one dominates and how you know | Vendor names from the tech stack unless they are the channel |
| **Revenue streams** | Who pays, how, and how much stays? | The mechanism in one or two lines: "advertisers pay per user action; 40 to 50% goes to the user as reward, the rest is Almedia's". Then the scale if the company has stated it, dated | Valuations, competitor acquisitions, funding history |
| **Cost structure** | Where does the money go? | The two or three biggest costs, with the company's own figures when available and the date | Estimates without a source, general startup costs |
| **Key metrics** | What numbers does the company itself steer by, and what would a PM here watch? | Published metrics with dates; the analytics events observed; one line on what the north star probably is, marked [I] | Ratings and reviews (users canvas), things we could not observe |
| **Unfair advantage** | What could not be bought or copied in a year? | Only things that pass that test: exclusive supply, data, a brand users trust, distribution deals, regulatory position. Often one line, sometimes empty | "Bootstrapped", "founder-led", "good team", "high rating" (those are strengths, and they can be copied). Never write "none" as content; leave the box empty and say so in Open items |

## Rules for this canvas

- A fact appears in one box only. If it is in Revenue it is not also in Key metrics.
- Bullets are conclusions. "Almedia targets the top 10 to 30 grossing games per market because they
  monetise better [R][1]" is a bullet. "The founder said in a podcast that..." is not.
- Each box ends with `Sources:` and numbered entries: what, date, link or file path.
- Problems the company has fixed, or observations about the research process, do not belong here.
- No box needs to be long. A box with one strong line is better than one with five weak ones.

## Example, Revenue streams

Good:

```
- Advertisers pay Almedia a negotiated budget per user action; 40 to 50% goes back to the user as reward and the rest stays with Almedia. [R][1]
- 2025 revenue about $320M; run rate above $1bn since mid-2026, by the founder's own account. [R][1]
- No public rate card; advertiser deals are sold, not self-serve. [V][2]

Sources: [1] Founder on the Kontor podcast, 23 Jul 2026, 3:04 and 14:16, inputs/founder-podcast-FkD2Kl_oY8g-transcript.md · [2] almedia.co/solutions/advertise-with-freecash, 6 Sep 2026
```

Bad:

```
- According to the founder podcast [R] (podcast [14:16]), roughly 40-50% of the advertiser's budget is returned to users, see research/business.md for details.
- NCSOFT paid ~$205M for 70% of JustPlay [V] market.md, a useful comparable.
```

The first is a report, not a conclusion, and points the reader elsewhere. The second is a market
fact in the wrong box.
