---
name: research
description: Runs the full outside-in research of one company and its product into a workspace under companies/<slug>/: intake of the job ad, transcripts and founder interviews, identity check, parallel gathering by specialist agents, a full product walk that pauses for the user when a gate blocks it, an evidence review, framework canvases, the point of view, and the rendered page. Use whenever the user names a company they are interviewing with, asks to "research", "look into", "prepare for" or "understand" a company or product, or drops a job description or transcript, even if they do not say the word research.
argument-hint: "<company name or URL> [paths or links: job ad, transcripts, podcasts]"
user-invocable: true
---

# /research

One command, one company, one workspace. You orchestrate; the specialists gather; you review, decide
and write the point of view. Read `CLAUDE.md` delegation rules if this session has not yet.

Two things learned the hard way, so they are rules now. **The product walk must reach first value
before anything is synthesised**; a workspace built around an unwalked product is hollow, and the
user would rather wait. **When a specialist is blocked, the run stops and asks**; it never writes
around the gap.

## 0. Session check (once per session)

Run `python toolbox/hn.py --help`, `claude mcp list`, `bdata config`, `python toolbox/mailbox.py check`
and `adb devices` through Bash. Note what is available: toolbox, chrome-devtools, playwright, exa
and firecrawl (connected, not "Needs authentication"), the Bright Data unblocker, the research
inbox, an emulator. If a device is listed, also run `adb shell dumpsys account | grep -c com.google`
to know whether Play is signed in. Tell the user in one line which optional tools are present but
not ready and how to fix each (`/mcp` in Claude Code, `bdata login`, `emulator -avd <name>`, sign
into Play on the device). Do not stop the run for it. If `git remote -v` shows the public template
as origin, tell the user once that company folders are ignored by the template's `.gitignore` and
that a private clone deletes that line to commit research.

## 1. Intake

Parse the arguments: a company name or URL, and any file paths or links. Choose a slug (lowercase,
hyphenated, the brand). Create `companies/<slug>/` with the folders from `companies/README.md` and
copy the given files into `inputs/`. Links to a job board are fetched and saved as a file (Ashby
boards have a public JSON API at `api.ashbyhq.com/posting-api/job-board/<org>`); YouTube links are
transcribed with `python toolbox/youtube.py <id>` into `inputs/`. Ask the user once for anything
they mentioned but did not attach, and for founder interviews or podcasts if they gave none; a
founder talking for an hour is worth more than any search.

Spawn `extractor` on `inputs/`. Read `inputs/brief.md` when it returns.

## 2. Identity and the checkpoint

Establish, with at most five searches of your own: legal entity, brand, primary domain, HQ, founding
year, product surfaces (web app URL, Android package id, iOS app id, B2B side if two-sided), and the
role as posted. Write the identity block into `index.md` (from `templates/index.md`) and
`state.json`.

Confirm it with the user in one short message: the identity block, the surfaces you intend to walk,
and the account plan: the walker signs up itself with the research inbox unless the user says they
have already logged in inside the plugin's Chrome window. Say that consumer sign-ups often carry a
captcha, and that if one appears the run will pause and ask them to solve it in that window. Wait
for the answer.

## 3. Gather, and the walk

Launch in the same turn, each with the identity block, the slug, the role, the account plan, the
path to `inputs/brief.md` and its metered budget (`.claude/rules/tools.md`: default five Firecrawl,
Exa or Bright Data calls, raise it only for a named blocked source the run needs):

| Agent | Fronts | Default model |
|---|---|---|
| `company-analyst` | business, money, people | sonnet |
| `voice-of-customer` | users, culture | sonnet |
| `market-analyst` | market | sonnet |
| `product-walker` | product, screens | sonnet |

Override the model upward for a front when the identity was hard to pin down, the sources are thin,
or the product is technical.

Read each contract as it returns. Three outcomes for the walker:

- **`<report>`**: the walk reached first value. Continue.
- **`<blocked>`**: stop here. Post one message that starts with **Needs you**, states the gate and
  the one action in the walker's `ask` line, and where to do it (the plugin's Chrome window, the
  emulator). Send a push notification with the same line, since the user may not be watching. End
  your turn. The other gatherers keep running. When the user says it is done, resume the same
  walker with a message (it keeps its context) rather than launching a new one. Repeat as often as
  gates appear.
- **Partial, out of turns**: resume it with "continue from <flow>"; do not relaunch.

Do not start step 4 until the walker's `<report>` is in and the three research contracts are back.

## 4. Review

Spawn `reviewer` on the slug. It reads the inputs first, aligns dates before calling contradictions,
adds dates to problems, corrects grades in place, curates `claims-register.md` and writes
`evidence/review-log.md`. Read its contract, then read `claims-register.md` and
`evidence/review-log.md` in full.

## 5. Frameworks

Spawn `strategist` on the slug. It fills `frameworks/` from the reviewed files under the writing
rules and the per-canvas guides, and adds the ranked improvement candidates to
`product/onboarding-teardown.md`: the small, evidenced fixes that answer "what would you try?"
Read its contract.

## 6. The point of view

Yours; do not delegate it. Read `research/*.md` and `product/*.md` in full, once. Write
`point-of-view.md` from the template under `.claude/rules/writing.md`: conclusions with grades and
source numbers, a sources list at the end, the broken-problems table with dates, two or three
bigger bets (the answer to "what would you build here?", each resting on a current problem or a
market fact and naming what would prove it wrong; the small fixes stay in the teardown), and a
questions table where every question shows what it rests on, why this interviewer can answer it,
and that the inputs do not already answer it. Facts stated as facts are [V] in the register.

Then `index.md`: identity, five lines, **Open items** (gaps, history problems, what the next run
should do; this is the only place the research process is described), reading order, one line per
canvas, files, changelog. Create `decisions.md`. Update `state.json`.

## 7. Render and report

Run `python toolbox/render.py companies/<slug>`, check `site/index.html` exists, open it. Report in
at most fifteen lines: where to start, the three findings that matter most, what is still open and
what would close it, and the one next thing. Point to files by path; do not paste them.

## When something fails

A specialist that returns without its files: read its contract, resume it once with a narrower
brief, then proceed with that front marked thin in Open items. A contested identity: stop and ask;
nothing downstream is worth running on the wrong company.
