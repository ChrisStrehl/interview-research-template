---
name: research
description: Runs the full outside-in research of one company and its product into a workspace under companies/<slug>/: intake of the job ad and transcripts, identity check, parallel gathering by specialist agents, an evidence review, framework canvases, the point of view, and the rendered page. Use whenever the user names a company they are interviewing with, asks to "research", "look into", "prepare for" or "understand" a company or product, or drops a job description or transcript, even if they do not say the word research.
argument-hint: "<company name or URL> [paths to job ad, transcripts, notes]"
user-invocable: true
---

# /research

One command, one company, one workspace. You orchestrate; the specialists gather; you review, decide
and write the point of view. Read `CLAUDE.md` delegation rules if this session has not yet.

## 0. Session check (once per session)

Run `python toolbox/hn.py --help`, `claude mcp list`, `bdata config` and `adb devices` through
Bash and note what is available: toolbox, chrome-devtools, playwright, exa and firecrawl (only
when `claude mcp list` shows them connected, not "Needs authentication"), the Bright Data
unblocker (logged in when `bdata config` succeeds), mobile emulator. Tell the user in one line
which optional tools are present but not logged in, and how to log in (`/mcp` in Claude Code,
`bdata login` in a terminal). If the target has an Android app and `adb devices` lists nothing,
say that `emulator -avd <name>` starts the device and that the walk will use store data until it
is running. Do not stop the run for it; the walker can be re-run with `/deepen` later. If
`git remote -v` shows the public template as origin, tell the user once that this clone will contain
their inputs and suggest pointing origin at a private repo or removing it. Do not do it for them.

## 1. Intake

Parse the arguments: a company name or URL, and any file paths. Choose a slug (lowercase, hyphenated,
the brand not the legal name). Create `companies/<slug>/` with the folders from
`companies/README.md` and copy the given files into `inputs/`. Ask the user to paste anything they
mentioned but did not attach; a recruiter transcript is worth more than any search.

If `inputs/` has files, spawn `extractor` on them. Read `inputs/brief.md` when it returns.

## 2. Identity

Establish, with at most five searches of your own: legal entity, brand, primary domain, HQ, founding
year, product surfaces (web app URL, Android package id, iOS app id, B2B side if two-sided), and the
role as posted. Company names collide constantly and German startups trade under brands that differ
from the GmbH. Write the result as the identity block at the top of `index.md` (from
`templates/index.md`) and into `state.json`.

Then confirm it with the user in one short message: the identity block and the surfaces you intend
to walk, plus one question only if it changes the run: whether they have already logged into the
product in the persistent browser profile, or whether the walker should sign up itself with the
research inbox (`python toolbox/mailbox.py check` tells you whether that inbox is configured; say
so). Wait for the answer. This is the only checkpoint in the run.

## 3. Gather (one turn, four agents)

Launch these in the same turn, each with the identity block, the slug, the role, and the path to
`inputs/brief.md`:

| Agent | Fronts | Default model |
|---|---|---|
| `company-analyst` | business, money, people | sonnet |
| `voice-of-customer` | users, culture | sonnet |
| `market-analyst` | market | sonnet |
| `product-walker` | product, screens | sonnet |

Override the model upward for a front when the identity was hard to pin down, the sources are thin,
or the product is technical. Pass the browser and account facts from the checkpoint to the walker.

When the four contracts return, read them, not the files. Note blocked sources and unlocks; they go
into the final report. Do not start reviewing until all four are back.

## 4. Review

Spawn `reviewer` on the slug. It corrects grades in place, resolves or lists contradictions, curates
`claims-register.md` and writes `evidence/review-log.md`. Read its contract, then read
`claims-register.md` and `evidence/review-log.md` in full. These two files plus `inputs/brief.md` are
what you hold in your head for the rest of the run.

## 5. Frameworks

Spawn `strategist` on the slug. It fills `frameworks/` from the reviewed files. Read its contract.

## 6. The point of view

This is yours; do not delegate it. Read `research/*.md` and `product/*.md` now, in full, once. Then
write `point-of-view.md` from `templates/point-of-view.md`, about 500 words, in this order: what the
company is in three sentences; how it is actually doing, with a position; what is working; what is
broken, ranked by confidence and marked evidenced or inferred; where you would focus first and why;
the hypotheses to test in the conversation, each phrased as the question you would ask; the unknowns
that matter. Everything you state as fact must be [V] in the register. Everything [R] or [I] that
matters appears under hypotheses, not under facts.

Then write `index.md`: the identity block, the five-line summary, the reading order, and one line per
file. Create `decisions.md` from the template. Update `state.json` with what ran, when, and the
capabilities used.

## 7. Render and report

Run `python toolbox/render.py companies/<slug>` and check that `site/index.html` exists. Then report
to the user in at most fifteen lines: where to start reading, the three findings that matter most,
the fronts that are thin and why, the sources that were blocked and which optional tool would unblock
them, and the one thing you would do next. Point to files by path; do not paste them.

## When something fails

A specialist that returns without its files: read its contract, re-launch once with a narrower
brief, then proceed with that front marked thin. A blocked browser walk: proceed with store data and
say so. A contested identity: stop and ask; nothing downstream is worth running on the wrong company.
