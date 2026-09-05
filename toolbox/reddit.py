#!/usr/bin/env python3
"""reddit.py -- Search Reddit posts (and optionally comments) via the Arctic Shift
archive API (keyless, no Reddit API key needed).

Usage:
  python toolbox/reddit.py <query> --subreddits a,b,c [--limit 25] [--comments] [--json]

Examples:
  python toolbox/reddit.py freecash --subreddits beermoney,passive_income --limit 5 --comments

Notes:
  - Arctic Shift is an archive of Reddit data; it is not real-time (recent posts
    from the last few days may be missing).
  - If you don't know which subreddits are relevant, do a web search first
    (e.g. "site:reddit.com <query>") to find candidates, then pass them here.
Source: https://arctic-shift.photon-reddit.com (see https://github.com/ArthurHeitmann/arctic_shift)
"""
import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE = "https://arctic-shift.photon-reddit.com/api"


def fmt_date(ts):
    try:
        return datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d")
    except Exception:
        return ""


def fetch(url, timeout=25, retries=1):
    req = urllib.request.Request(url, headers={"User-Agent": "toolbox-reddit/1.0"})
    last_err = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            last_err = e
            if e.code in (429, 422, 500, 502, 503, 504) and attempt < retries:
                time.sleep(1.5)
                continue
            raise
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(1.5)
                continue
            raise
    raise last_err


def trim(s, n):
    if not s:
        return ""
    s = s.replace("\n", " ").strip()
    return (s[: n - 1] + "...") if len(s) > n else s


def main():
    ap = argparse.ArgumentParser(description="Search Reddit via Arctic Shift archive API")
    ap.add_argument("query", help="search term (matched against post title / comment body)")
    ap.add_argument("--subreddits", default="", help="comma-separated list of subreddits to search (required)")
    ap.add_argument("--limit", type=int, default=25, help="max results per subreddit (default 25)")
    ap.add_argument("--comments", action="store_true", help="also search matching comments")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    args = ap.parse_args()

    subs = [s.strip() for s in args.subreddits.split(",") if s.strip()]
    if not subs:
        print(
            "Error: no --subreddits given. Arctic Shift requires a subreddit (or author) filter.\n"
            "First find relevant subreddits via a web search (e.g. 'site:reddit.com <query>'),\n"
            "then re-run with --subreddits sub1,sub2,...",
            file=sys.stderr,
        )
        sys.exit(1)

    all_posts = {}
    all_comments = {}
    errors = []

    for sub in subs:
        params = {"subreddit": sub, "title": args.query, "limit": args.limit}
        url = f"{BASE}/posts/search?{urllib.parse.urlencode(params)}"
        try:
            data = fetch(url)
            all_posts[sub] = data.get("data", [])
        except urllib.error.URLError as e:
            errors.append(f"posts/{sub}: {e}")
            all_posts[sub] = []
        except Exception as e:
            errors.append(f"posts/{sub}: {e}")
            all_posts[sub] = []

        if args.comments:
            cparams = {"subreddit": sub, "body": args.query, "limit": args.limit}
            curl = f"{BASE}/comments/search?{urllib.parse.urlencode(cparams)}"
            try:
                cdata = fetch(curl)
                all_comments[sub] = cdata.get("data", [])
            except urllib.error.URLError as e:
                errors.append(f"comments/{sub}: {e}")
                all_comments[sub] = []
            except Exception as e:
                errors.append(f"comments/{sub}: {e}")
                all_comments[sub] = []

    total_posts = sum(len(v) for v in all_posts.values())
    if total_posts == 0 and not any(all_comments.values()):
        if len(errors) == len(subs):
            print(f"Error: could not reach Arctic Shift API for any subreddit: {'; '.join(errors)}", file=sys.stderr)
            sys.exit(1)

    if args.json:
        print(json.dumps({"posts": all_posts, "comments": all_comments, "errors": errors}, indent=2))
        return

    print(f"# Reddit results for \"{args.query}\" in {', '.join(subs)}\n")

    for sub in subs:
        posts = all_posts.get(sub, [])
        print(f"## r/{sub} — posts ({len(posts)})\n")
        if not posts:
            print("_No posts found._\n")
        for p in posts:
            title = p.get("title", "(no title)")
            score = p.get("score", 0)
            ncomments = p.get("num_comments", 0)
            date = fmt_date(p.get("created_utc", ""))
            selftext = trim(p.get("selftext", ""), 500)
            permalink = "https://www.reddit.com" + p.get("permalink", "")
            print(f"- **{title}** — score {score}, {ncomments} comments, {date}")
            if selftext:
                print(f"  - text: {selftext}")
            print(f"  - link: {permalink}")
        print()

        if args.comments:
            comments = all_comments.get(sub, [])
            print(f"## r/{sub} — matching comments ({len(comments)})\n")
            if not comments:
                print("_No comments found._\n")
            for c in comments:
                author = c.get("author", "unknown")
                body = trim(c.get("body", ""), 400)
                date = fmt_date(c.get("created_utc", ""))
                link_id = c.get("link_id", "").replace("t3_", "")
                permalink = c.get("permalink") or f"https://www.reddit.com/comments/{link_id}//{c.get('id','')}/"
                if permalink and not permalink.startswith("http"):
                    permalink = "https://www.reddit.com" + permalink
                print(f"- **{author}** ({date}): {body}\n  - link: {permalink}")
            print()

    if errors:
        print(f"\n_Warnings: {'; '.join(errors)}_")


if __name__ == "__main__":
    main()
