# Toolbox

Keyless research scripts for pre-interview company/product research. Every script:
prints Markdown to stdout by default (`--json` for raw JSON), takes `--limit N` where
applicable, has `--help`, and fails with a one-line message (no traceback) if a source
is unreachable. Run everything from the repo root.

## Setup

```
python -m pip install --user -r toolbox/requirements.txt
cd toolbox && npm install && cd ..
```

## Scripts

| Script | What it yields | Example command |
|---|---|---|
| `hn.py` | Hacker News stories + top comments matching a query (Algolia HN Search) | `python toolbox/hn.py freecash --limit 5` |
| `reddit.py` | Reddit posts (and optionally comments) matching a query, per subreddit (Arctic Shift archive) | `python toolbox/reddit.py freecash --subreddits beermoney,passive_income --limit 5 --comments` |
| `wayback.py` | Wayback Machine snapshot timeline for a URL, or the plain-text content of one snapshot | `python toolbox/wayback.py freecash.com --from 2023` / `python toolbox/wayback.py freecash.com --fetch 20240601110014` |
| `appstore.py` | Apple App Store listing (metadata, screenshots, ratings by country) + RSS reviews | `python toolbox/appstore.py freecash --country de --reviews 20` |
| `playstore.mjs` | Google Play listing + reviews (newest first) via `google-play-scraper` | `node toolbox/playstore.mjs com.freecash.app2 --reviews 20` |
| `youtube.py` | Video transcript (timestamped paragraphs), or `--search "<query>"` to list videos | `python toolbox/youtube.py --search "freecash app review" --limit 5` |
| `stack.py` | Tech-stack sniff of a site: response headers of interest + vendor table by category | `python toolbox/stack.py https://freecash.com` |
| `render.py` | Renders a `companies/<slug>` workspace into one self-contained HTML page (maintained separately) | `python toolbox/render.py companies/<slug>` |

## Known limits

- **Arctic Shift (`reddit.py`)** is an archive of Reddit, not a live feed — very
  recent posts/comments (last few days) may be missing, and it occasionally
  returns a transient 422/5xx (the script retries once).
- **App Store RSS reviews (`appstore.py`)** is a legacy, undocumented Apple
  endpoint. It caps out around the ~500 most recent reviews, and for many
  modern apps (even ones with large rating counts) it returns zero entries —
  ratings and written reviews are not the same data. Treat an empty review
  list as "unavailable," not "no reviews exist." Ratings/counts from
  `/lookup` and `/search` are reliable regardless.
- **`google-play-scraper` (`playstore.mjs`)** scrapes Play Store web pages; it
  breaks whenever Google changes page markup, and can be rate-limited if
  called too rapidly in a loop.
- **Wayback CDX (`wayback.py`)** can time out or 504 under load. The script
  retries once with a longer timeout, then falls back to the availability API
  (`archive.org/wayback/available`), sampled at January/July of the requested
  range only.
- **`youtube.py`** transcripts depend on `youtube-transcript-api`, which can be
  IP-blocked by YouTube in some environments; the script falls back to
  `yt-dlp --write-auto-subs` (VTT) automatically. `--search` uses full (not
  flat) yt-dlp extraction so it can report a real upload date, which costs
  roughly 1-2 seconds per result.
- **`stack.py`** is a static sniff (no JS execution/headless browser), so
  vendors injected only via runtime JavaScript with no static trace in the
  HTML or referenced resource URLs will be missed.
- **Algolia HN Search (`hn.py`)** tokenizes/fuzzy-matches queries (not exact
  substring), so a query like `freecash` can also surface unrelated "free
  cash" stories — this is Algolia's normal behavior, not a bug.
