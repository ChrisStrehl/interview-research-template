#!/usr/bin/env python3
"""wayback.py -- List Wayback Machine snapshots for a URL, or fetch one snapshot as text.

Usage:
  python toolbox/wayback.py <url> [--from YYYY] [--to YYYY] [--per-year 2] [--json]
  python toolbox/wayback.py <url> --fetch TIMESTAMP [--json]

Examples:
  python toolbox/wayback.py freecash.com/pricing --from 2023
  python toolbox/wayback.py freecash.com --fetch 20240601110014

Notes:
  - Snapshot listing uses the CDX API; it can occasionally time out or 5xx under
    load. This script retries once with a longer timeout, then falls back to the
    availability API (checked for each January and July in the requested range).
  - --fetch downloads the raw snapshot (id_ modifier) and strips it to plain text,
    capped at 8000 characters.
"""
import argparse
import gzip
import html
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import urllib.error
import zlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def fetch_url(url, timeout=20):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (toolbox-wayback/1.0)", "Accept-Encoding": "gzip"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        elif encoding == "deflate":
            raw = zlib.decompress(raw)
        return raw


def cdx_search(url, frm, to):
    params = {
        "url": url,
        "output": "json",
        "fl": "timestamp,original,statuscode",
        "filter": "statuscode:200",
        "collapse": "timestamp:6",
    }
    if frm:
        params["from"] = frm
    if to:
        params["to"] = to
    cdx_url = f"https://web.archive.org/cdx/search/cdx?{urllib.parse.urlencode(params)}"
    for timeout in (20, 40):
        try:
            data = fetch_url(cdx_url, timeout=timeout)
            rows = json.loads(data.decode("utf-8"))
            if not rows:
                return []
            return rows[1:]  # drop header row
        except (urllib.error.URLError, TimeoutError):
            continue
        except Exception:
            continue
    return None  # signal failure -> caller falls back


def availability_fallback(url, frm, to):
    frm_year = int(frm) if frm else 2015
    to_year = int(to) if to else 2026
    results = []
    for year in range(frm_year, to_year + 1):
        for month in ("01", "07"):
            ts = f"{year}{month}01"
            api_url = f"https://archive.org/wayback/available?{urllib.parse.urlencode({'url': url, 'timestamp': ts})}"
            try:
                data = json.loads(fetch_url(api_url, timeout=15).decode("utf-8"))
                snap = data.get("archived_snapshots", {}).get("closest")
                if snap and snap.get("available"):
                    results.append((snap["timestamp"], url, snap.get("status", "200")))
            except Exception:
                continue
    # de-dup by timestamp
    seen = set()
    out = []
    for ts, u, code in results:
        if ts not in seen:
            seen.add(ts)
            out.append((ts, u, code))
    return out


def html_to_text(raw_bytes):
    try:
        text = raw_bytes.decode("utf-8", errors="replace")
    except Exception:
        text = raw_bytes.decode("latin-1", errors="replace")
    text = re.sub(r"(?is)<script.*?</script>", " ", text)
    text = re.sub(r"(?is)<style.*?</style>", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def group_by_year(rows, per_year):
    by_year = {}
    for ts, orig, code in rows:
        year = ts[:4]
        by_year.setdefault(year, [])
        if len(by_year[year]) < per_year:
            by_year[year].append((ts, orig, code))
    return by_year


def main():
    ap = argparse.ArgumentParser(description="List or fetch Wayback Machine snapshots for a URL")
    ap.add_argument("url", help="URL to look up (with or without scheme)")
    ap.add_argument("--from", dest="frm", help="start year YYYY")
    ap.add_argument("--to", dest="to", help="end year YYYY")
    ap.add_argument("--per-year", type=int, default=2, help="max snapshots to show per year (default 2)")
    ap.add_argument("--fetch", help="fetch a specific snapshot by timestamp and print its text content")
    ap.add_argument("--limit", type=int, default=0, help="max total snapshots to list (0 = no cap beyond per-year)")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    args = ap.parse_args()

    if args.fetch:
        snap_url = f"https://web.archive.org/web/{args.fetch}id_/{args.url}"
        try:
            req = urllib.request.Request(
                snap_url,
                headers={"User-Agent": "Mozilla/5.0 (toolbox-wayback/1.0)", "Accept-Encoding": "gzip"},
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                final_url = resp.geturl()
                encoding = (resp.headers.get("Content-Encoding") or "").lower()
                if encoding == "gzip":
                    raw = gzip.decompress(raw)
                elif encoding == "deflate":
                    raw = zlib.decompress(raw)
        except urllib.error.HTTPError as e:
            print(f"Error: Wayback snapshot fetch failed (HTTP {e.code}) for {snap_url}", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Error: could not reach the Wayback Machine: {e}", file=sys.stderr)
            sys.exit(1)
        text = html_to_text(raw)
        capped = text[:8000]
        if args.json:
            print(json.dumps({"timestamp": args.fetch, "url": args.url, "resolved_url": final_url, "text": capped}, indent=2))
            return
        print(f"# Wayback snapshot: {args.url} @ {args.fetch}\n")
        print(f"Resolved snapshot URL: {final_url}\n")
        print(capped)
        if len(text) > 8000:
            print("\n_[truncated at 8000 characters]_")
        return

    rows = cdx_search(args.url, args.frm, args.to)
    used_fallback = False
    if rows is None:
        rows = availability_fallback(args.url, args.frm, args.to)
        used_fallback = True

    if not rows:
        print(f"No Wayback Machine snapshots found for '{args.url}' in the given range.", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"snapshots": [{"timestamp": t, "original": o, "statuscode": c} for t, o, c in rows], "fallback_used": used_fallback}, indent=2))
        return

    by_year = group_by_year(rows, args.per_year)
    print(f"# Wayback Machine snapshots: {args.url}\n")
    if used_fallback:
        print("_CDX API was unavailable; used the availability API fallback (Jan/Jul samples only)._\n")
    total = 0
    for year in sorted(by_year.keys()):
        print(f"## {year}\n")
        for ts, orig, code in by_year[year]:
            snap_link = f"https://web.archive.org/web/{ts}/{orig}"
            print(f"- {ts} (status {code}) — {snap_link}")
            total += 1
            if args.limit and total >= args.limit:
                break
        print()
        if args.limit and total >= args.limit:
            break


if __name__ == "__main__":
    main()
