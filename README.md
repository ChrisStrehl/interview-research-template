# interview-research-template

A Claude Code workspace that researches a company and its product from the outside, deeply enough
that you can talk with the hiring manager as a peer: how the business works, what users say, how the
product is built and where it loses people, and where you would focus first.

Built by a product manager for product-manager interviews. Works for any company with a public
product.

## Why

Every candidate reads the website and the last funding announcement. That work is worth nothing,
because everyone in the loop has it. The interviews that go well feel like consultations: you walk in
already holding their problem, you can say what is working and what is not, and you ask the questions
that show you have done the job before you have it. That needs hours of research per company, and
the research has to be honest, because you will say it out loud to the people it is about.

This repo does the hours. You do the conversation.

## What you get

After one command, `companies/<slug>/` holds:

- **A point of view.** About 600 words: what the company is, how it is doing, what is working, what is
  broken with dates, where you would focus, two or three bigger bets with the KPI each one moves and
  what would prove it wrong, and the questions to ask in the room.
- **Canvases.** Lean Canvas, AARRR funnel with the KPIs the product is assumed to run on, SWOT, and a
  strategy canvas when the market front produced a factor table. One screen each, every line ending
  in a grade and a source number.
- **A product walk.** A product map with one screenshot per screen on web and Android, a stack section
  from what the browser actually loaded, and an onboarding and activation teardown with ranked
  improvement candidates, each naming the KPI it moves, the KPI it may hurt and the net case, and
  the first experiment you would run.
- **Seven research fronts.** Business, money, people, users, culture, market and product, each with
  fixed headings, sources and dates.
- **A claims register.** The fifteen or so claims your point of view leans on, each graded, with what
  would verify it and whether it is safe to say.
- **A rendered page.** One self-contained HTML file for screen-sharing.

Raw material lives in `evidence/`, which you do not read. It is there for depth and citations.

## How it works

The main chat is the PM, defined in `CLAUDE.md`. It delegates gathering to specialist agents in
`.claude/agents/`, each on the cheapest model that does the job well, and keeps review, synthesis
and the point of view on the strongest model. Agents hand off by file and return a short contract,
so the chat stays small.

| Agent | Does | Default model |
|---|---|---|
| `extractor` | Turns job ads and transcripts into a short brief | Haiku |
| `company-analyst` | Business model, money, people and org | Sonnet |
| `voice-of-customer` | Users and employees in their own words | Sonnet |
| `market-analyst` | Competitor set, positioning, category pressure | Sonnet |
| `product-walker` | Walks the product in a real browser and on Android | Sonnet |
| `reviewer` | Audits every claim, curates the register | Opus |
| `strategist` | Fills the canvases from reviewed research | Opus |

Every claim carries a grade: **[V]** verified, **[R]** reported by one source, **[I]** inferred with
the working shown, **[U]** unknown, **[O]** opinion. Anything you would state as fact in the room
must be [V]. Everything else becomes a question. The rules are in `.claude/rules/evidence.md`.

## Quick start

1. Use this template on GitHub, clone it, and point origin at a private repo or remove it. Your
   transcripts will live in this clone.
2. Open the folder in Claude Code. The Chrome DevTools, Playwright and Exa plugins are enabled by
   the project settings; install them once if prompted. Run `npm install` inside `toolbox/` and
   `pip install --user -r toolbox/requirements.txt`.
3. Drop the job ad and any transcripts anywhere, then:

```
/research Acme https://acme.com ./downloads/acme-jd.pdf ./downloads/recruiter-call.txt
```

The PM confirms the company identity with you once, then runs everything and reports where to
start reading. Later rounds: `/deepen acme` to add a transcript, re-run a front, or walk another
flow. `/render acme` rebuilds the page.

Optional upgrades that remove specific walls (Firecrawl for whole-site crawls, Bright Data for
review sites that block fetches, an Android emulator for native apps) are in `references/tooling.md`,
with where the keys go so they never enter the repo.

## Layout

```
CLAUDE.md              the PM persona and the delegation rules
.claude/agents/        the specialists
.claude/skills/        /research, /deepen, /render, plus the walkthrough and frameworks methods
.claude/rules/         evidence grading and writing rules, loaded for companies/**
templates/             output skeletons with fixed headings
references/            source map, tooling, how to fill each canvas honestly
toolbox/               keyless scripts: HN, Reddit, Wayback, app stores, YouTube, stack, render
companies/             one folder per company (empty in the template)
```

## Credits

The orchestration shape borrows from André Albuquerque's
[claude-config](https://github.com/AndreAlbuquerque/claude-config): output contracts, handoff by
file, tool budgets per agent. The "start from zero, build the workspace up" character comes from
[product-workspace-template](https://github.com/ChrisStrehl/product-workspace-template). The reason
to do any of this comes from Jacob Warwick's approach to interviews: reveal little, collect much,
and do the job before you have it.
