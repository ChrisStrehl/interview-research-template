#!/usr/bin/env python3
"""appstore.py -- Look up an app on Apple's App Store (keyless, no API key needed).

Usage:
  python toolbox/appstore.py <search term or numeric app id> [--country de] [--reviews 50] [--json]
  python toolbox/appstore.py <search term or id> --ratings-by-country de,us,gb

Examples:
  python toolbox/appstore.py freecash --country de --reviews 20
  python toolbox/appstore.py 1673567402 --ratings-by-country de,us,gb

Notes:
  - Uses https://itunes.apple.com/search (or /lookup for a numeric id) plus the
    customer-reviews RSS feed. The RSS reviews feed is a legacy, undocumented
    Apple endpoint: for many modern apps it returns zero entries even though the
    app has a large rating count (ratings and written reviews are not the same
    thing, and Apple has largely stopped populating this feed for most apps).
    Treat an empty review list as "not available via RSS", not as "no reviews".
"""
import argparse
import io
import json
import sys
import urllib.parse
import urllib.request
import urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def fetch_json(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": "toolbox-appstore/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def trim(s, n):
    if not s:
        return ""
    s = s.replace("\r", "").strip()
    s_one_line = s.replace("\n", " ")
    return (s_one_line[: n - 1] + "...") if len(s_one_line) > n else s_one_line


def resolve_app(term, country):
    if term.isdigit():
        url = f"https://itunes.apple.com/lookup?{urllib.parse.urlencode({'id': term, 'country': country})}"
    else:
        url = f"https://itunes.apple.com/search?{urllib.parse.urlencode({'term': term, 'country': country, 'entity': 'software', 'limit': 5})}"
    data = fetch_json(url)
    results = data.get("results", [])
    return results


def fetch_reviews(app_id, country, max_reviews):
    reviews = []
    page = 1
    while len(reviews) < max_reviews and page <= 10:
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        try:
            data = fetch_json(url)
        except Exception:
            break
        entries = data.get("feed", {}).get("entry", [])
        if isinstance(entries, dict):
            entries = [entries]
        if not entries:
            break
        # first entry on page 1 can be app metadata (no im:rating) -- skip those
        for e in entries:
            if "im:rating" not in e:
                continue
            reviews.append(e)
        page += 1
    return reviews[:max_reviews]


def main():
    ap = argparse.ArgumentParser(description="Look up an app on Apple's App Store")
    ap.add_argument("term", help="search term or numeric App Store id")
    ap.add_argument("--country", default="us", help="App Store storefront country code (default us)")
    ap.add_argument("--reviews", type=int, default=20, help="max reviews to fetch (default 20)")
    ap.add_argument("--ratings-by-country", help="comma-separated country codes to compare rating/count across storefronts")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    args = ap.parse_args()

    try:
        results = resolve_app(args.term, args.country)
    except urllib.error.URLError as e:
        print(f"Error: could not reach the App Store lookup API: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: unexpected failure querying App Store: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print(f"Error: no App Store app found for '{args.term}' in country '{args.country}'.", file=sys.stderr)
        sys.exit(1)

    app = results[0]
    app_id = app.get("trackId")

    try:
        reviews = fetch_reviews(app_id, args.country, args.reviews) if args.reviews > 0 else []
    except Exception:
        reviews = []

    ratings_by_country = {}
    if args.ratings_by_country:
        for cc in [c.strip() for c in args.ratings_by_country.split(",") if c.strip()]:
            try:
                r = resolve_app(str(app_id), cc)
                if r:
                    ratings_by_country[cc] = {
                        "rating": r[0].get("averageUserRating"),
                        "count": r[0].get("userRatingCount"),
                        "trackName": r[0].get("trackName"),
                    }
                else:
                    ratings_by_country[cc] = None
            except Exception:
                ratings_by_country[cc] = None

    if args.json:
        print(json.dumps({"app": app, "reviews": reviews, "ratings_by_country": ratings_by_country}, indent=2))
        return

    screenshots = app.get("screenshotUrls", []) or []
    print(f"# {app.get('trackName', '(unknown)')}\n")
    print(f"- Seller: {app.get('sellerName', '?')}")
    print(f"- Bundle ID: {app.get('bundleId', '?')}")
    print(f"- Current version: {app.get('version', '?')} (released {app.get('currentVersionReleaseDate', '?')[:10]})")
    print(f"- Price: {app.get('formattedPrice', app.get('price', '?'))}")
    print(f"- Rating: {app.get('averageUserRating', '?')} ({app.get('userRatingCount', 0)} ratings)")
    print(f"- Genres: {', '.join(app.get('genres', []))}")
    print(f"- Screenshots: {len(screenshots)} total")
    for s in screenshots[:5]:
        print(f"  - {s}")
    print(f"- App Store link: {app.get('trackViewUrl', '?')}")
    print()
    print("## Release notes\n")
    print(trim(app.get("releaseNotes", "(none)"), 600))
    print()
    print("## Description\n")
    print(trim(app.get("description", ""), 1000))
    print()

    if ratings_by_country:
        print("## Ratings by country\n")
        print("| Country | Rating | Rating count | Name |")
        print("|---|---|---|---|")
        for cc, info in ratings_by_country.items():
            if info:
                print(f"| {cc} | {info['rating']} | {info['count']} | {info['trackName']} |")
            else:
                print(f"| {cc} | (not found) | | |")
        print()

    print(f"## Reviews ({len(reviews)}, country={args.country})\n")
    if not reviews:
        print("_No reviews available via the RSS reviews feed for this app/country "
              "(this legacy Apple endpoint returns nothing for many modern apps, "
              "even ones with large rating counts)._")
        return
    for r in reviews:
        date = r.get("updated", {}).get("label", "")[:10]
        rating = r.get("im:rating", {}).get("label", "?")
        version = r.get("im:version", {}).get("label", "?")
        title = r.get("title", {}).get("label", "")
        text = trim(r.get("content", {}).get("label", ""), 400)
        print(f"- **{title}** — {rating}/5, v{version}, {date}\n  - {text}")


if __name__ == "__main__":
    main()
