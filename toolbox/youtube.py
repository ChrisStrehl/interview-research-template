#!/usr/bin/env python3
"""youtube.py -- Fetch a YouTube video transcript, or search YouTube (keyless).

Usage:
  python toolbox/youtube.py <video url or id> [--lang en,de] [--json]
  python toolbox/youtube.py --search "<query>" [--limit 10] [--json]

Examples:
  python toolbox/youtube.py --search "freecash app review" --limit 5
  python toolbox/youtube.py UNoaM7Pcpyw

Notes:
  - Tries youtube-transcript-api first; falls back to `yt_dlp --write-auto-subs`
    (VTT -> text) if that fails (blocked / disabled / no captions).
  - --search uses yt-dlp ytsearch:<query> (full extraction, so it can report a
    real upload date) -- allow a couple seconds per result.
"""
import argparse, io, json, os, re, subprocess, sys, tempfile, urllib.parse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def extract_video_id(s):
    s = s.strip()
    if re.fullmatch(r"[A-Za-z0-9_-]{11}", s):
        return s
    parsed = urllib.parse.urlparse(s)
    if "youtu.be" in parsed.netloc:
        return parsed.path.strip("/").split("/")[0]
    qs = urllib.parse.parse_qs(parsed.query)
    if "v" in qs:
        return qs["v"][0]
    m = re.search(r"/(?:embed|shorts)/([A-Za-z0-9_-]{11})", parsed.path)
    return m.group(1) if m else None


def fmt_ts(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return f"{h:d}:{m:02d}:{s:02d}" if h else f"{m:d}:{s:02d}"


def group_paragraphs(snippets, window=60):
    paragraphs, cur_start, cur_words = [], None, []
    for sn in snippets:
        start = sn["start"]
        text = sn["text"].replace("\n", " ").strip()
        if not text:
            continue
        if cur_start is None:
            cur_start = start
        if start - cur_start >= window and cur_words:
            paragraphs.append((cur_start, " ".join(cur_words)))
            cur_start, cur_words = start, []
        cur_words.append(text)
    if cur_words:
        paragraphs.append((cur_start, " ".join(cur_words)))
    return paragraphs


def try_transcript_api(video_id, langs):
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        return YouTubeTranscriptApi().fetch(video_id, languages=langs).to_raw_data()
    except Exception:
        return None


def vtt_to_snippets(vtt_text):
    snippets, seen = [], set()
    time_re = re.compile(r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})")
    to_sec = lambda ts: (lambda h, m, s: int(h) * 3600 + int(m) * 60 + float(s))(*ts.split(":"))
    for block in re.split(r"\n\n+", vtt_text.strip()):
        lines = block.splitlines()
        for i, line in enumerate(lines):
            m = time_re.search(line)
            if not m:
                continue
            text = " ".join(re.sub(r"<[^>]+>", "", t) for t in lines[i + 1:]).strip()
            text = re.sub(r"\s+", " ", text)
            if text and text not in seen:
                seen.add(text)
                snippets.append({"start": to_sec(m.group(1)), "text": text})
            break
    return snippets


def try_yt_dlp_fallback(video_id, langs):
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [sys.executable, "-m", "yt_dlp", "--skip-download", "--write-auto-subs", "--write-subs",
               "--sub-lang", ",".join(langs), "--sub-format", "vtt", "-o", os.path.join(tmpdir, "%(id)s"),
               f"https://www.youtube.com/watch?v={video_id}"]
        try:
            subprocess.run(cmd, capture_output=True, timeout=60, text=True)
        except Exception:
            return None
        vtt_files = sorted(f for f in os.listdir(tmpdir) if f.endswith(".vtt"))
        if not vtt_files:
            return None
        with open(os.path.join(tmpdir, vtt_files[0]), "r", encoding="utf-8", errors="replace") as f:
            return vtt_to_snippets(f.read())


def do_search(query, limit):
    cmd = [sys.executable, "-m", "yt_dlp", f"ytsearch{limit}:{query}", "--dump-json", "--skip-download", "-q"]
    try:
        proc = subprocess.run(cmd, capture_output=True, timeout=120, text=True, encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"Error: could not run yt-dlp search: {e}", file=sys.stderr)
        sys.exit(1)
    if proc.returncode != 0 and not proc.stdout.strip():
        print(f"Error: yt-dlp search failed: {proc.stderr.strip()[:300]}", file=sys.stderr)
        sys.exit(1)
    results = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            results.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return results


def main():
    ap = argparse.ArgumentParser(description="Fetch a YouTube transcript or search YouTube (keyless)")
    ap.add_argument("video", nargs="?", help="video URL or 11-char video id")
    ap.add_argument("--search", help="search query instead of fetching a transcript")
    ap.add_argument("--limit", type=int, default=10, help="max search results (default 10)")
    ap.add_argument("--lang", default="en", help="comma-separated language preference, e.g. en,de (default en)")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    args = ap.parse_args()

    if args.search:
        results = do_search(args.search, args.limit)
        if not results:
            print(f"Error: no YouTube results found for '{args.search}'.", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(results, indent=2))
            return
        print(f"# YouTube search: \"{args.search}\"\n")
        for d in results:
            title = d.get("title", "(no title)")
            channel = d.get("channel") or d.get("uploader", "?")
            date = d.get("upload_date", "")
            date = f"{date[:4]}-{date[4:6]}-{date[6:8]}" if len(date) == 8 else "unknown"
            dur = d.get("duration_string") or d.get("duration", "?")
            url = d.get("webpage_url") or f"https://www.youtube.com/watch?v={d.get('id')}"
            print(f"- **{title}** — {channel}, {date}, {dur}\n  - {url}")
        return

    if not args.video:
        print("Error: provide a video URL/id, or use --search \"<query>\".", file=sys.stderr)
        sys.exit(1)

    video_id = extract_video_id(args.video)
    if not video_id:
        print(f"Error: could not parse a video id from '{args.video}'.", file=sys.stderr)
        sys.exit(1)

    langs = [l.strip() for l in args.lang.split(",") if l.strip()]
    snippets = try_transcript_api(video_id, langs)
    source = "youtube-transcript-api"
    if snippets is None:
        snippets = try_yt_dlp_fallback(video_id, langs)
        source = "yt-dlp auto-subs (fallback)"

    if not snippets:
        print(f"Error: no transcript available for video '{video_id}' (tried youtube-transcript-api "
              f"and yt-dlp auto-subs; captions may be disabled or the video unavailable).", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps({"video_id": video_id, "source": source, "snippets": snippets}, indent=2))
        return

    print(f"# Transcript: {video_id}\n")
    print(f"_Source: {source}_\n")
    for start, text in group_paragraphs(snippets, window=60):
        print(f"**[{fmt_ts(start)}]** {text}\n")


if __name__ == "__main__":
    main()
