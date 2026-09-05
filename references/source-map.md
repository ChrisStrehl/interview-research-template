# Source map

What each source yields, how to reach it, and where it fails. Access conditions change — if a source
is blocked or paywalled, say so in the dossier rather than working around it silently.

Ordered roughly by how much edge it buys. The first section is the one almost no candidate checks.

Confidence marks carried over from tooling research: **[V]** verified live or from official docs,
**[I]** inferred from secondary sources or not independently confirmed. Keep the mark when you repeat
the claim in a dossier.

---

## How to reach a source

Four routes cover everything in this document. Pick the cheapest one that works, and fall back in
this order:

| Route | What it is | Cost |
|---|---|---|
| **Built-in** | `WebSearch` (search snippets) and `WebFetch` (fetch a page, render to markdown, answer a prompt against it) | Free, always available |
| **Toolbox script** | A keyless script in `toolbox/`, run from the repo root, e.g. `python toolbox/hn.py <query>` | Free, always available |
| **Browser** | `chrome-devtools` MCP — screenshots, accessibility snapshot, network capture, Lighthouse — against a real, persistent Chrome profile | Free, already installed |
| **Optional keyed MCP** | Bright Data or Firecrawl — needs an API key set outside the repo | Free tier, requires signup |

**`WebFetch` is blocked or hostile on specific domains — do not spend a turn retrying these:**
`www.reddit.com`, `old.reddit.com`, and `www.kununu.com` refuse the fetch outright; `glassdoor.com`
returns 403. For all four, use `WebSearch` snippets first (they surface Reddit, Kununu and Glassdoor
result text directly), then the toolbox (Reddit → Arctic Shift) or an optional keyed MCP (Bright Data
for Kununu/Glassdoor/G2 full text) if you need more than the snippet gives you.

Every table below has a **Reach via** column naming the concrete route for that row. Where the route
is itself blocked, the column says so and names the fallback.

---

## 1. German registry and financial filings

The highest-yield, lowest-competition source for any German company. Publication is a legal
obligation, so the data exists whether or not the company wants it public.

### Where

| Source | URL | Yields | Reach via |
|---|---|---|---|
| Unternehmensregister | unternehmensregister.de | Annual accounts (2022 onward), consolidated search | Built-in |
| Bundesanzeiger | bundesanzeiger.de | Annual accounts (historical, pre-2022 especially) | Built-in |
| Handelsregister | handelsregister.de | Registered address, managing directors, capital changes, shareholder list | Built-in — free to view since 2022, but there is no official API and no bulk download [V/I] |
| North Data | northdata.de | Free aggregated view of the above — usually the fastest entry point | Built-in |
| Companyhouse / Firmenwissen | companyhouse.de, firmenwissen.de | Alternative aggregators, partial paywalls | Built-in |

Start with North Data. It aggregates the official registers, renders equity and capital history as a
chart, and is readable without an account. Verify anything load-bearing against the official source.

North Data also has a paid REST API (roughly EUR 500/mo per 1,000 lookups, no MCP) [I] — not worth it
for one-off interview prep. `OffeneRegister.de` publishes a free bulk copy of the Handelsregister
(CC-BY-4.0, ~250MB JSONL or ~740MB SQLite, plus a SQL API) but does not state its freshness — treat any
number from it as possibly stale and verify before quoting [V]. The `deutschland` Python package
(bundesAPI, Apache-2.0) wraps Bundesanzeiger filings programmatically, but it fails to install on
Python 3.13 without a C compiler (the numpy build breaks) — if you need it, create a Python 3.12 venv
first. For a single company's filings, reading Bundesanzeiger or North Data directly through
`WebFetch` or a search snippet is faster than fighting the install.

### What you can actually read

**From the Handelsregister:**
- **Kapitalerhöhungen** (capital increases) with dates — these correspond to funding rounds, and they
  appear in the register whether or not there was ever a press release. A capital increase with no
  corresponding announcement is a real finding.
- **Gesellschafterliste** — the shareholder list. Names the VCs, and shows dilution across rounds.
- **Geschäftsführer** — managing directors, with appointment and removal dates. A removal is a signal.
- Registered address and any changes.

**From the annual accounts (Jahresabschluss):**
- **Eigenkapital** — equity. Typically negative for VC-backed companies, because accumulated losses
  exceed paid-in capital. The size and direction of movement is the useful part.
- **Kapitalrücklage** — capital reserve. This is where VC money lands. A jump between years locates a
  round.
- **Verbindlichkeiten** — liabilities, including any venture debt.
- **Durchschnittliche Zahl der Arbeitnehmer** — average employee count for the year, often disclosed
  even in abbreviated filings. A genuine headcount number, unlike LinkedIn's.

### The limits — state these honestly

- **Size exemptions bite.** Under §267 HGB, small companies (kleine Kapitalgesellschaften) file
  abbreviated accounts: balance sheet and notes, **no profit and loss statement**. So revenue is
  usually *not* available. Micro companies (Kleinstkapitalgesellschaften) may merely deposit rather
  than publish, in which case you get almost nothing. Most sub-50-person startups fall in here.
- **Filings lag 12–18 months.** A filing accessed in 2026 typically covers 2024. It tells you about
  the company two years ago, which still beats nothing but must be dated clearly in the dossier.
- **UG, GmbH & Co. KG, SE and foreign parents** file differently. A German subsidiary of a foreign
  parent may disclose very little.

### Deriving runway — always label as inference

Equity movement year over year approximates annual burn, if no round landed in between. Combine with
known raise date and amount to estimate months of cash remaining. This is rough: it ignores
in-year timing, capitalised costs and any debt facility. Present it as a range with the reasoning
shown, never as a figure. Its value is directional — "probably raising within 6–9 months" changes how
you read everything else about the company.

**Non-German companies:** UK equivalents at Companies House (companieshouse.gov.uk) are comparable
and often better, including full accounts for many small companies; a free API key gives 600
requests/5min [V]. Most other jurisdictions, including the US, disclose nothing for private companies
— say so and fall back to funding databases. SEC EDGAR full-text search (`efts.sec.gov`) is free and
keyless but covers US filers only, and requires a real email address in the User-Agent header or it
403s [V].

---

## 2. Funding, investors and headcount

| Source | Yields | Notes | Reach via |
|---|---|---|---|
| Crunchbase | Rounds, amounts, dates, investors | Free tier is gone; paid only, roughly $49–99/mo entry [I] | Built-in (search snippets only) |
| Dealroom | European coverage, better than Crunchbase for Berlin | Quote-only, no self-serve | Built-in (search snippets) |
| Tracxn, PitchBook | Deeper, heavily paywalled | Use search snippets only | Built-in |
| Sifted | European startup journalism, often has the real story | Partial paywall | Built-in |
| Gründerszene / Business Insider DE | German startup press, layoffs, founder drama | businessinsider.de/gruenderszene | Built-in |
| deutsche-startups.de | German rounds and news | Free | Built-in |
| EU-Startups, Tech.eu | Round announcements | Free | Built-in |
| LinkedIn company page | Headcount, and the 6/12/24-month trend graph | The trend matters more than the number | Browser (chrome-devtools MCP) or Built-in |

On headcount: LinkedIn counts profiles, not employees, and inflates for companies with contractors or
alumni who never updated. Use the *direction and rate of change*, and cross-check against the
Arbeitnehmer figure in the filings where available.

Investor identity is informative. Note who led, and whether they typically follow on.

Crunchbase also has an official remote MCP (`https://mcp.crunchbase.com`, OAuth 2.1) but it requires a
paid plan — not worth setting up for one company [V/I]. Do not chase a Crunchbase key for this
workflow; the search-snippet route gets you the round number and date, which is usually all you need.

---

## 3. Users and customer sentiment

| Source | Best for | Notes | Reach via |
|---|---|---|---|
| G2, Capterra, TrustRadius | B2B SaaS | The highest-yield sentiment source for B2B. Read the "cons" fields. No free programmatic path exists for any of the three [V] | Built-in (snippets); full text needs Optional keyed MCP (Bright Data) |
| Trustpilot | Consumer, marketplaces, fintech | Skews to complaints; weight accordingly. No stated free API tier [V] | Built-in (snippets); Optional keyed MCP for full text |
| App Store / Google Play | Any app | Filter by recency and by German locale separately | Toolbox — see §3b |
| Reddit | Consumer at scale, developer tools | Often empty for small B2B. `WebFetch` is blocked on `www.reddit.com`/`old.reddit.com`; unauthenticated `.json` endpoints are dead, 403 [V] | Built-in (`WebSearch` snippets) for discovery; Toolbox (`toolbox/reddit.py`, Arctic Shift) for full text |
| Hacker News | Developer tools, infra, technical products | Launch threads are gold | Toolbox (`toolbox/hn.py`, HN Algolia — free, keyless, verified working) |
| Product Hunt | Launch-era reception | Read the comment thread, not the upvotes. GraphQL API 401s without a token; free token exists but is non-commercial-licensed only [V] | Built-in (snippets) |
| YouTube | Tutorials, reviews, comparisons | Comment sections carry real complaints | Toolbox (`toolbox/youtube.py`) for transcripts and comments; Built-in for surrounding context |
| LinkedIn search | Live reaction, support escalations | | Browser or Built-in |
| Community forums, Discord, Slack | Developer-tool companies especially | Often public and rarely read by candidates | Built-in |
| Support docs and status page | What breaks, how often | An honest changelog of failure | Built-in |

**X/Twitter is not a usable route in 2026.** No free tier (pay-per-use from roughly $0.005/post read),
and Nitter is dead (C&D letters, Aug 2026). Do not plan a turn around it — see "Absent or dead
sources" below. `WebSearch` still surfaces X content indirectly through other sites that quote it.

Method: read the actual text, not the aggregate score. Extract recurring themes with dates. A
complaint pattern that stops mid-2025 means it was fixed, and that is a different fact from a
complaint pattern that continues.

Always record **volume and recency** alongside any rating. Twelve reviews is anecdote; twelve hundred
is evidence, and the dossier should say which it has.

---

## 3b. App stores and mobile

Store data is free, keyless, and underused — it gives you shipping cadence and a rating trend without
touching the product itself.

| Source | Yields | Reach via |
|---|---|---|
| iTunes Lookup API (`itunes.apple.com/lookup?id=<trackId>&country=de`) | Name, developer, current version, release notes, price, rating count and average, per storefront | Toolbox (`toolbox/appstore.py`) — free, keyless, verified: e.g. Freecash DE returns version 1.260.0, rating 4.62 from 30,752 ratings |
| Apple RSS customer reviews | ~500 most recent reviews per app, each tagged with the version reviewed | Toolbox (`toolbox/appstore.py`) — free, keyless |
| Google Play listing, reviews, "What's new" | Full Play listing text, reviews with sort/pagination | Toolbox (`toolbox/playstore.mjs`, wraps `google-play-scraper`). Note: the maintainer no longer actively maintains it beyond merging PRs — parsers can break when Google changes layout [V] |
| App Store screenshots | Current UI, feature emphasis, localisation | Toolbox (`toolbox/appstore.py`) or Built-in |

**Version history as a shipping-velocity signal.** The release-notes trail from the lookup API is a
genuine changelog: how often the app ships, whether cadence sped up or stalled, and — cross-read
against a funding date — whether a raise visibly changed shipping pace. Treat a long gap with no
release as a signal worth naming, not just an absence of data.

**Ratings by storefront.** Query country by country (`country=de` vs `country=us` vs default) — rating
average, volume and review language all differ by market, and a company can look very different to its
home market than to Berlin. Always state which storefront a number came from.

**Walking the app itself:**
- **Android is fully workable on Windows** via `mobile-mcp` (optional, not installed by default) —
  see `references/tooling.md` for the setup steps. Accessibility-tree driven, screenshots on request.
  Some apps (banking, streaming, some fintech) detect the emulator and refuse to launch — if that
  happens, fall back to store data and reviews rather than burning turns on evasion.
- **iOS has no route on this machine.** iOS automation needs Xcode/`simctl`, which is Mac-only, and a
  cloud device farm (BrowserStack App Live, Appetize.io) is the only realistic alternative — both are
  paid, and Appetize's 2026 pricing could not be confirmed [I]. For interview prep, reconstruct the iOS
  experience from store screenshots, release notes and reviews, or note plainly that it was not walked
  first-hand.

---

## 4. Employees and culture

| Source | Notes | Reach via |
|---|---|---|
| Kununu | kununu.com — far better German coverage than Glassdoor. Start here for German companies. `WebFetch` refuses `www.kununu.com` outright | Built-in (`WebSearch` snippets); Optional keyed MCP (Bright Data) for full review text |
| Glassdoor | Better for international companies; has an interview-experience section. `WebFetch` returns 403 | Built-in (`WebSearch` snippets); Optional keyed MCP (Bright Data) for full review text |
| Blind | US tech heavy, thin for Berlin | Built-in |
| LinkedIn — people tab | Filter by past employees; see where leavers went and how long they stayed | Browser or Built-in |
| LinkedIn posts | Search employees posting about the company; departure posts are candid | Browser or Built-in |
| Indeed reviews | Occasionally has coverage the others lack | Built-in |

Both Kununu and Glassdoor block automated fetching aggressively — this is now confirmed at the
`WebFetch` level, not just an assumption. Search-result snippets frequently carry usable review text
and the aggregate score; that is your default. If you need volume beyond what snippets give you, an
optional keyed MCP (Bright Data, free tier 5,000 requests/mo) is the unblock — see
`references/tooling.md`. If neither gets you enough, say so in the dossier and report what the
snippets support, rather than presenting a thin sample as if it were comprehensive.

Read for **mechanism**: how decisions get made, who has authority, what the meeting load is, whether
remote is real. Anonymous reviews are weak individually and meaningful in aggregate — weight them by
volume and by whether the same specific thing recurs.

---

## 5. Product

| Source | Yields | Reach via |
|---|---|---|
| The product itself | The only first-hand evidence available. Always attempt it | Browser (chrome-devtools MCP) |
| Pricing page | Model, tiers, gating, whether pricing is public at all | Built-in |
| Changelog / release notes / blog | Shipping velocity, and whether it changed | Built-in; Optional keyed MCP (Firecrawl) if you need to crawl a whole changelog/docs site in one shot |
| App Store version history | Release cadence for mobile | Toolbox — see §3b |
| Public GitHub | Commit activity, contributor count, open issues, response times | Built-in |
| Status page + incident history | Reliability, and how they communicate failure | Built-in |
| Docs | Product surface area and depth; often reveals features the marketing site hides | Built-in; Optional keyed MCP (Firecrawl `map`/`crawl`) for a full site |
| Wayback Machine | web.archive.org — how positioning, pricing and messaging changed over time | Toolbox (`toolbox/wayback.py`) |
| BuiltWith / Wappalyzer | Tech stack | See "Walking the product" below — free-forks-plus-network-capture is more reliable than either commercial product now |
| SimilarWeb | Traffic scale and trend; directional only, unreliable at low volume | Built-in (snippets) — the official SimilarWeb MCP needs a Business/Enterprise subscription [V] |

The Wayback comparison is underused: diffing the homepage and pricing page against 12 months ago
shows what the company decided to stop saying.

**Tech-stack caveat:** Wappalyzer went fully commercial in Aug 2023 — the GPL repo was deleted and the
npm package deprecated [V]. Free community forks exist (`enthec/webappanalyzer`,
`tunetheweb/wappalyzer`, `dochne/wappalyzer`) but treat their coverage as weaker than the original.
BuiltWith has an official MCP but it is paid. The cheapest reliable method is described below.

**Traffic caveat:** if SimilarWeb is out of reach, the Chrome UX Report API (free, Google Cloud key,
150 queries/min) and Cloudflare Radar (free Cloudflare account, bearer token) are credible free
proxies for real-user performance and relative popularity [V]. Tranco gives a stable free popularity
baseline with no signup at all [V].

### Walking the product

The product itself is first-hand evidence nothing else replaces. Use the **chrome-devtools MCP**
(already installed) for this:

- `take_screenshot` and `take_snapshot` (an accessibility-tree read with stable element IDs) let you
  navigate and click through the actual UI.
- `list_network_requests` and `get_network_request` are the network capture — this is the strongest
  free route to real tech-stack evidence. Reading the request waterfall surfaces the analytics vendor,
  payment processor, feature-flag service and monitoring tool directly — e.g. calls to
  `/api/v2/graphql`, Segment, Stripe Elements, LaunchDarkly, Datadog RUM. It beats BuiltWith and
  Wappalyzer for a live product because it reads what the page actually loads, not a fingerprint
  database.
- `performance_start_trace` / `lighthouse_audit` if performance itself is part of the read.

**Logged-in sessions.** Since Chrome 136, Chrome refuses `--remote-debugging-port` on your default,
everyday profile — attaching to "the Chrome you already have open" does not work [V]. Use a
**dedicated debug profile** instead: launch Chrome once with a separate `--user-data-dir`, log in by
hand, and the chrome-devtools MCP plugin can then attach to it (`--browser-url` to an existing Chrome
at `http://127.0.0.1:9222`, or `--userDataDir` to manage its own persistent profile). Logins persist
across sessions this way, without touching your real browser profile. Other useful plugin flags:
`--isolated` (throwaway profile), `--slim` (fewer tool schemas, cheaper turns when you only need
drive-and-screenshot), `--headless`. If a product is SSO-gated and the debug-profile route is
awkward, the **playwright** plugin's `--extension` mode attaches to tabs in your real, already-logged-in
browser instead — the cleaner path through SSO/2FA specifically.

**Token cost.** An accessibility snapshot is text and scales with DOM size — expensive on a dense
dashboard. Snapshot once per screen to get element IDs, act by ID, and screenshot only the frames you
actually want to keep for the teardown.

For a scripted, repeatable pass at stack evidence rather than manual network-tab reading, use
`toolbox/stack.py`.

---

## 6. People

| Source | Yields | Reach via |
|---|---|---|
| LinkedIn profiles | Backgrounds, tenure, trajectory, what they post about | Browser or Built-in |
| Founder/exec podcasts and talks | The richest source on what leadership actually cares about | Built-in |
| Company blog and engineering blog | Named authors, and the problems they chose to write about | Built-in |
| Conference talks, YouTube | As above | Toolbox (`toolbox/youtube.py`) for transcripts; Built-in for discovery |
| Personal sites, Substack, X | Unfiltered opinion | Built-in for sites/Substack; X is not reachable — see "Absent or dead sources" |
| Handelsregister | Who legally runs the entity, and when that changed | Built-in — see §1 |
| Crunchbase people section | Prior companies and exits | Built-in (snippets only — see §2) |

What a founder repeats publicly is what they are proud of and what they are worried about. This is
free, high-signal, and nearly nobody reads it before an interview.

---

## 7. Market and competitors

| Source | Yields | Reach via |
|---|---|---|
| G2 / Capterra category pages | The competitor set as buyers actually see it | Built-in (snippets — see §3 on the block) |
| The company's own comparison pages | Who they think the enemy is | Built-in |
| Competitors' comparison pages | How the market attacks them | Built-in |
| Analyst and category coverage | Market direction, consolidation | Built-in |
| Search: "<company> vs" | Real buyer comparisons and forum threads | Built-in |
| Trade press for the vertical | Regulation, structural pressure | Built-in |

---

## 8. Comp reference

| Source | Notes | Reach via |
|---|---|---|
| levels.fyi | Thin for Berlin startups, useful for scale-ups | Built-in |
| Kununu Gehalt | German-specific, self-reported, wide ranges | Built-in (snippets — same `WebFetch` block as §4) |
| Glassdoor salaries | Similar caveats | Built-in (snippets — same `WebFetch` block as §4) |
| StepStone / Gehalt.de reports | Broad German market bands | Built-in |
| The job ad itself | EU pay-transparency practice means more ads now publish ranges | Built-in |
| Berlin startup salary surveys | Published periodically by VCs and job boards; check the year | Built-in |

All of it is self-reported and noisy. Report ranges with the source and sample size, never a single
number, and never present a band as authoritative.

---

## Absent or dead sources

Do not spend turns on these. Each was checked; each is either gone or was never free.

- **X/Twitter.** No free tier in 2026 — pay-per-use from roughly $0.005/post read. Nitter is dead
  (C&D letters, Aug 2026). The `cdn.syndication.twimg.com/tweet-result` endpoint still hydrates a
  single *known* tweet ID but has no search or timeline function. Treat X as unavailable; rely on
  `WebSearch` surfacing X content indirectly through sites that quote it.
- **Proxycurl, or any LinkedIn scraping — do not.** Proxycurl is dead: LinkedIn sued in Jan 2025 and it
  shut down 4 Jul 2025. Scraping LinkedIn directly is the exact mechanism that killed it. Use the
  Bundesanzeiger Arbeitnehmer figure (§1) and job-posting counts (below) as the legitimate free proxies
  for headcount instead.
- **Reddit's `.json` endpoints.** Dead, 403 — confirmed on both `www.` and `old.reddit.com`, with and
  without a browser user agent. Use `WebSearch` snippets plus `toolbox/reddit.py` (Arctic Shift)
  instead.
- **PullPush.io.** Returns 429, with a response body that explicitly refuses free scraping for agents.
  Do not use it.
- **Crunchbase's free tier.** Gone. It is paid-only now, roughly $49–99/mo at entry. Use search
  snippets against Crunchbase's own pages, or lean on Dealroom, Sifted, and deutsche-startups.de, which
  remain free or partially free.
- **Product Hunt's GraphQL API without a token.** 401s. A free developer token exists but is licensed
  non-commercial-only, and no verified MCP server exists for it — treat Product Hunt as a
  read-the-page-and-comments source, not an API source.
- **Fictitious or 404 packages some aggregator sites promote as if they worked:**
  `opencorporates/opencorporates-mcp`, `@similarweb/mcp-server` on npm, and `adzuna-mcp` on PyPI do not
  exist. Do not plan around any of them; if you see them recommended elsewhere, verify before trusting.

---

## Search technique

- Search in **German and English separately** for German companies. The results differ substantially.
- Use `site:` operators for Reddit, HN, LinkedIn and forums rather than hoping general search surfaces
  them — but confirm with the toolbox script for Reddit and HN once you have a lead, since `WebFetch`
  cannot open the Reddit result directly.
- Search the **legal entity name** as well as the brand — filings, court records and press use the
  former.
- Search for the **negative case** explicitly: `<company> layoffs`, `<company> Kritik`,
  `<company> problems`, `<company> alternative`, `<company> leaving`. Positive coverage finds itself;
  negative coverage has to be looked for.
- Search **former employees** by name once identified — departure posts are candid in a way reviews
  are not.
- Job-posting counts (Arbeitsagentur Jobsuche, careers pages on Greenhouse/Lever/Personio) are a free
  hiring-velocity proxy worth checking alongside headcount — track the count over time rather than
  reading it once.
