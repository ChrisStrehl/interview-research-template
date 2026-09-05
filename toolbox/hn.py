#!/usr/bin/env python3
"""hn.py -- Search Hacker News (via Algolia HN Search API) for stories and comments.

Usage:
  python toolbox/hn.py <query> [--limit 20] [--since YYYY-MM-DD] [--json]

Examples:
  python toolbox/hn.py freecash --limit 5
  python toolbox/hn.py "stripe" --since 2024-01-01 --limit 10 --json

No API key required. Data source: https://hn.algolia.com/api/v1/search
"""
import argparse
import io
import json
import sys
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "https://hn.algolia.com/api/v1"


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "toolbox-hn/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def trim(s, n):
    if not s:
        return ""
    s = s.replace("\n", " ").strip()
    return (s[: n - 1] + "...") if len(s) > n else s


def strip_html(s):
    if not s:
        return ""
    import re
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&quot;", '"').replace("&#x27;", "'").replace("&amp;", "&").replace("&gt;", ">").replace("&lt;", "<")
    return s


def main():
    ap = argparse.ArgumentParser(description="Search Hacker News via Algolia API")
    ap.add_argument("query", help="search query")
    ap.add_argument("--limit", type=int, default=20, help="max stories to show (default 20)")
    ap.add_argument("--since", help="only include results after this date (YYYY-MM-DD)")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    args = ap.parse_args()

    params = {"query": args.query, "tags": "story"}
    if args.since:
        try:
            dt = datetime.strptime(args.since, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Error: --since must be YYYY-MM-DD, got '{args.since}'", file=sys.stderr)
            sys.exit(1)
        params["numericFilters"] = f"created_at_i>{int(dt.timestamp())}"

    story_url = f"{BASE}/search_by_date?{urllib.parse.urlencode(params)}&hitsPerPage={args.limit}" if args.since else \
        f"{BASE}/search?{urllib.parse.urlencode(params)}&hitsPerPage={args.limit}"

    comment_params = {"query": args.query, "tags": "comment"}
    if args.since:
        comment_params["numericFilters"] = f"created_at_i>{int(dt.timestamp())}"
    comment_url = f"{BASE}/search_by_date?{urllib.parse.urlencode(comment_params)}&hitsPerPage={args.limit}"

    try:
        stories = fetch(story_url)
        comments = fetch(comment_url)
    except urllib.error.URLError as e:
        print(f"Error: could not reach Hacker News (Algolia) API: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: unexpected failure querying Hacker News API: {e}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"stories": stories.get("hits", []), "comments": comments.get("hits", [])}, indent=2))
        return

    shits = stories.get("hits", [])
    chits = comments.get("hits", [])

    print(f"# Hacker News results for \"{args.query}\"\n")
    print(f"## Stories ({len(shits)})\n")
    if not shits:
        print("_No stories found._\n")
    for h in shits:
        title = h.get("title") or h.get("story_title") or "(no title)"
        points = h.get("points", 0)
        ncomments = h.get("num_comments", 0)
        date = h.get("created_at", "")[:10]
        url = h.get("url") or f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        hn_link = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        print(f"- **{title}** — {points} pts, {ncomments} comments, {date}\n  - link: {url}\n  - HN: {hn_link}")
    print()
    print(f"## Top comments ({len(chits)})\n")
    if not chits:
        print("_No comments found._\n")
    for h in chits:
        author = h.get("author", "unknown")
        date = h.get("created_at", "")[:10]
        text = trim(strip_html(h.get("comment_text", "")), 400)
        link = f"https://news.ycombinator.com/item?id={h.get('objectID')}"
        print(f"- **{author}** ({date}): {text}\n  - link: {link}")


if __name__ == "__main__":
    main()
