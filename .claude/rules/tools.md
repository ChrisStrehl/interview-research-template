# Tool cost rules

These apply to every agent in this repo, the orchestrator included. Some tools are free to call as
often as needed. Others burn credits from a monthly quota that has run out mid-research before.
Running out mid-run costs more than any single page was worth.

## Free: use first, use freely

- The `toolbox/` scripts (`hn.py`, `reddit.py`, `wayback.py`, `appstore.py`, `playstore.mjs`,
  `youtube.py`, `stack.py`, `mailbox.py`).
- The built-in `WebSearch` and `WebFetch`.
- The chrome-devtools, playwright and mobile MCPs (they drive a local browser or device).

## Metered: last resort, one reason per call

- **Firecrawl** (`mcp__firecrawl__*`): every scrape, search, map, crawl, agent and extract call
  spends credits.
- **Exa** (`mcp__plugin_exa_*`): rate-limited and, with a key set, metered.
- **Bright Data** (`bdata scrape`, `bdata search`, the Bright Data MCP): every request counts
  against a monthly quota.

A metered call is allowed only when all of the following hold:

1. The free route was tried and failed on this exact target: `WebFetch` refused or returned a
   403, an empty shell or a bot wall, and `WebSearch` snippets do not carry the text you need.
2. The page or result decides a claim that will carry weight in the workspace. Full review text on
   Kununu, a registry filing, a pricing page that will not render. Not a page you are curious about.
3. You can write the reason in one line. If you cannot, it is not needed.

What is never allowed without the user or the orchestrator asking for it in the brief:

- Firecrawl `search` or Exa search as a substitute for `WebSearch`. Search with the free tool; reach
  for the metered one only when the free one found nothing on a query that matters.
- Firecrawl `crawl`, `agent`, `extract`, `interact` or `monitor`. These spend many credits per call.
- Firecrawl `map` more than once per company, and only when the site is large enough that its
  changelog, docs or careers pages cannot be found with two searches.
- Any metered call for a page `WebFetch` already rendered readably, or for a page that is only
  going into `evidence/` without deciding a claim.

Budget: at most five metered calls per agent run unless the brief you were given names a higher
number. Count them. When the budget is spent, stop using metered tools, grade the remaining claims
[R] or [U], and say so in your contract. Report the count on the `metered:` line of the output
contract with the tool and the reason for each call. Zero is the expected value on most runs.

When a source would only open through a metered tool and the budget does not allow it, record the
wall in the research file as `references/tooling.md` §2 describes, so the next run can decide.
