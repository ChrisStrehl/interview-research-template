#!/usr/bin/env python3
"""render.py -- Render one company research workspace into a single self-contained HTML page.

Usage:
  python toolbox/render.py companies/<slug> [--open]

Writes companies/<slug>/site/index.html: one page to screen-share in an interview. Images are
inlined as data URIs, so the file works with no network and no CDN. Missing files are skipped
with a note in the page; only a missing workspace is fatal. A "Sources:" line inside a section
or canvas box becomes a small footer; [1]-style markers in the text link into it.

Dependency: markdown (pip install --user markdown). Everything else is stdlib.
"""
import argparse, base64, mimetypes, re, sys, webbrowser
from datetime import date
from html import escape
from io import BytesIO
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("render.py: missing dependency 'markdown' -- run: pip install --user markdown")

try:
    from PIL import Image
except ImportError:
    Image = None

MAX_IMAGE_SIDE = 1400       # longer side, in px; images are never upscaled past their own size
JPEG_QUALITY = 82
SMALL_IMAGE_BYTES = 200 * 1024   # images smaller than this on disk keep their original PNG bytes
FULL_IMAGES = False         # set from --full-images in main(); disables downscaling entirely

MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"(<[^>]+>)")
GRADE_RE = re.compile(r"\[(V|R|I|U|O)\]")
ASK_RE = re.compile(r"\(ask\)")
MARKER_RE = re.compile(r"\[(\d{1,3})\]")
SOURCE_RE = re.compile(r"^\s*(?:[-*]\s+)?(?:\*\*|__|\*|_)?\s*sources?\s*:(?:\*\*|__|\*|_)?\s*(.*)$", re.I)
BARE_URL_RE = re.compile(r'(?<![(<"\w])https?://[^\s<>)"\]]+')
IMG_PATH_RE = re.compile(r"(?<![\w/\-.])((?:[\w.\-]+/)*[\w.\-]+\.(?:png|jpe?g|gif|webp))")
SRC_RE = re.compile(r'src="([^"]+)"')
TAGNAME_RE = re.compile(r"^</?([a-zA-Z][\w-]*)")
LEAD_NUM_RE = re.compile(r"^(\d+)")
TABLE_RE = re.compile(r"<table>.*?</table>", re.S)
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
CELL_RE = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.S)
STRIP_TAGS_RE = re.compile(r"<[^>]+>")
CARD_COLS = 6            # a table with this many columns or more is rendered as cards
CARD_CELL_CHARS = 160    # ...or one whose longest cell is longer than this
GRADES = {"V": ("Verified", "g-v"), "R": ("Reported", "g-r"), "I": ("Inferred", "g-i"),
          "U": ("Unknown", "g-u"), "O": ("Opinion", "g-o")}
DATE_KEYS = ("researched", "filled", "walked", "written", "curated", "updated")
COLORS = ["#2563eb", "#d97706", "#059669", "#dc2626", "#7c3aed", "#0891b2", "#c026d3", "#65a30d"]
RESEARCH_ORDER = ["business", "money", "people", "users", "culture", "market"]
LEAN_AREAS = [("problem", "Problem"), ("solution", "Solution"), ("uvp", "Unique value proposition"),
              ("advantage", "Unfair advantage"), ("segments", "Customer segments"), ("metrics", "Key metrics"),
              ("channels", "Channels"), ("cost", "Cost structure"), ("revenue", "Revenue streams")]
LEAN_KEYS = [("unique value", "uvp"), ("unfair", "advantage"), ("customer segment", "segments"),
             ("key metric", "metrics"), ("channel", "channels"), ("cost", "cost"), ("revenue", "revenue"),
             ("problem", "problem"), ("solution", "solution")]
SWOT_KEYS = ["strengths", "weaknesses", "opportunities", "threats"]
AARRR_KEYS = ["acquisition", "activation", "retention", "revenue", "referral"]
OVERVIEW_ORDER = ["in five lines", "open items", "read in this order", "frameworks"]
OVERVIEW_FOLD = ["files", "changelog"]
BOX = [0]
# ---------------------------------------------------------------- markdown io
def read_md(path):
    """Return (meta, body) with front matter and HTML comments stripped, or None."""
    if not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    meta = {}
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            for line in text[3:end].splitlines():
                if ":" in line:
                    key, val = line.split(":", 1)
                    meta[key.strip()] = val.strip()
            text = text[end + 4:]
    return meta, COMMENT_RE.sub("", text).strip()

def subtitle(meta):
    bits = [escape(meta["title"])] if meta.get("title") else []
    bits += ["%s %s" % (key, escape(meta[key])) for key in DATE_KEYS if meta.get(key)]
    return '<p class="sub">%s</p>' % " &middot; ".join(bits) if bits else ""

def first_h1(body, fallback):
    for line in body.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback

def split_sections(body):
    """Split a body into (lead_text, [(heading, markdown), ...]) on '## ' headings."""
    lead, out, head, buf = [], [], None, []
    for line in body.splitlines():
        if line.startswith("## "):
            if head is None:
                lead = buf
            else:
                out.append((head, "\n".join(buf).strip()))
            head, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if head is None:
        lead = buf
    else:
        out.append((head, "\n".join(buf).strip()))
    return "\n".join(lead).strip(), out

def pick(sections, needle):
    for head, text in sections:
        if needle in head.lower():
            return text
    return ""
# ------------------------------------------------------------------- sources
def parse_sources(raw):
    """Split a sources footer into [(number, text), ...]; number is '' when unnumbered."""
    clean = lambda t: " ".join(l.strip().lstrip("-*").strip() for l in t.splitlines()).strip(" ;,")
    parts = MARKER_RE.split(raw)
    if len(parts) == 1:
        return [("", clean(raw))] if clean(raw) else []
    return [(parts[i], clean(parts[i + 1])) for i in range(1, len(parts) - 1, 2) if clean(parts[i + 1])]

def split_sources(md_text):
    """Return (body markdown, footer entries) by pulling 'Sources:' out of each block."""
    chunks, cur = [], []
    for line in md_text.splitlines():
        if line.startswith("#") and cur:
            chunks.append(cur)
            cur = []
        cur.append(line)
    body, entries = [], []
    for chunk in chunks + [cur]:
        cut = next((i for i, line in enumerate(chunk) if SOURCE_RE.match(line)), None)
        body.extend(chunk if cut is None else chunk[:cut])
        if cut is None:
            continue
        raw = SOURCE_RE.match(chunk[cut]).group(1) + "\n" + "\n".join(chunk[cut + 1:])
        entries.extend(parse_sources(raw))
    return "\n".join(body).strip(), entries
# ------------------------------------------------------------- html transform
def downscale(data, mime):
    """Resize+recompress a screenshot for embedding; return (mime, bytes) or None to keep as-is."""
    if Image is None or FULL_IMAGES or not mime.startswith("image/") or len(data) < SMALL_IMAGE_BYTES:
        return None
    try:
        img = Image.open(BytesIO(data))
        img.load()
    except Exception:
        return None
    w, h = img.size
    longer = max(w, h)
    if longer > MAX_IMAGE_SIDE:
        scale = MAX_IMAGE_SIDE / longer
        img = img.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (255, 255, 255))
        flat.paste(rgba, mask=rgba.split()[3])
        img = flat
    elif img.mode != "RGB":
        img = img.convert("RGB")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=JPEG_QUALITY)
    return "image/jpeg", buf.getvalue()

def data_uri(path):
    data = path.read_bytes()
    mime = mimetypes.guess_type(path.name)[0] or "image/png"
    mime, data = downscale(data, mime) or (mime, data)
    return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))

def resolve(ref, dirs):
    """Find a relative image reference inside the workspace; None if it is not there."""
    ref = ref.replace("\\", "/")
    if ref.startswith(("http:", "https:", "data:", "/")):
        return None
    return next((base / ref.lstrip("./") for base in dirs if (base / ref.lstrip("./")).is_file()), None)

def img_html(path, cls="shot", id_attr=None):
    return '<img%s class="%s" loading="lazy" alt="%s" src="%s">' % (
        ' id="%s"' % escape(id_attr) if id_attr else "", cls, escape(path.name), data_uri(path))

def shot_id(path):
    """Stable element id for a gallery screenshot, used by screen-link lightbox lookups."""
    return "shot-%s" % re.sub(r"[^A-Za-z0-9_-]+", "-", path.stem)

def screen_label(stem):
    """'11' from '11-onboarding-bonus-claimed', or the stem itself when there is no leading number."""
    m = LEAD_NUM_RE.match(stem)
    return m.group(1) if m else stem

def screen_link_html(path):
    """A small link that opens the existing lightbox on a screenshot already embedded in the gallery."""
    return ('<a href="#" class="screen-link" data-shot="%s" onclick="return zoomShot(this)">screen %s</a>'
            % (escape(shot_id(path)), escape(screen_label(path.stem))))

def badge(letter):
    return '<span class="badge %s" title="%s">%s</span>' % (GRADES[letter][1], GRADES[letter][0], letter)

def cite(num, bid, srcs):
    """A [1] marker: a superscript link into this box's footer that shows the source on hover,
    or a plain superscript when the box has no footer entry for it."""
    text = srcs.get(num) if srcs else None
    if bid and text is not None:
        return ('<sup class="cite"><a href="#src-%s-%s" title="%s">%s</a></sup>'
                % (bid, num, escape(STRIP_TAGS_RE.sub("", text)), num))
    return '<sup class="cite">%s</sup>' % num

def table_rows(table_html):
    return [CELL_RE.findall(row) for row in ROW_RE.findall(table_html)]

def wants_cards(rows):
    """Wide or wordy tables read better as one card per row than as a table that scrolls sideways."""
    if len(rows) < 2:
        return False
    longest = max((len(STRIP_TAGS_RE.sub("", c)) for r in rows[1:] for c in r), default=0)
    return len(rows[0]) >= CARD_COLS or longest > CARD_CELL_CHARS

def card_html(head, row):
    cells = row + [""] * (len(head) - len(row))
    title, rest = cells[0].strip(), list(zip(head[1:], cells[1:]))
    if re.fullmatch(r"\d+", title) and rest:
        title, rest = "%s &middot; %s" % (title, rest[0][1]), rest[1:]
    body = "".join("<dt>%s</dt><dd>%s</dd>" % (k, v) for k, v in rest if v.strip())
    return '<div class="card"><h4>%s</h4><dl>%s</dl></div>' % (title, body)

def tables_html(html, cards=True):
    """Wrap every table for horizontal scrolling, or turn the wide ones into cards."""
    def repl(m):
        rows = table_rows(m.group(0))
        if cards and wants_cards(rows):
            return '<div class="cards">%s</div>' % "".join(card_html(rows[0], r) for r in rows[1:])
        return '<div class="table-wrap">%s</div>' % m.group(0)
    return TABLE_RE.sub(repl, html)

def inline_path(ref, dirs, in_cell=False):
    """A bare screenshot path found in running text: a gallery screen-link outside tables, an
    inline thumbnail inside a table cell (unchanged behaviour), plain escaped text if unresolved."""
    target = resolve(ref, dirs)
    if not target:
        return escape(ref)
    if target.parent.name == "screens" and target.suffix.lower() == ".png":
        if not in_cell:
            return screen_link_html(target)
        # a thumbnail that borrows its pixels from the gallery copy at load time, so each
        # screenshot is embedded once however often a table refers to it
        return ('<a href="#" class="shot-ref" data-shot="%s" onclick="return zoomShot(this)">'
                '<img class="inline-shot" data-shot="%s" alt="%s"><span>screen %s</span></a>'
                % (escape(shot_id(target)), escape(shot_id(target)), escape(target.name),
                   escape(screen_label(target.stem))))
    return img_html(target, "inline-shot")

def postprocess(text, dirs, bid=None, srcs=None):
    """Badge grades, link citations, inline images; skip anything inside a tag or code."""
    out, depth, cell = [], 0, 0
    for part in TAG_RE.split(text):
        if part.startswith("<"):
            low = part.lower()
            name = TAGNAME_RE.match(part)
            name = name.group(1).lower() if name else ""
            if low.startswith("<img"):
                found = SRC_RE.search(part)
                target = resolve(found.group(1), dirs) if found else None
                part = img_html(target) if target else part
            elif low.startswith(("<pre", "<code")):
                depth += 1
            elif low.startswith(("</pre", "</code")):
                depth = max(0, depth - 1)
            if name in ("td", "th", "dd"):
                cell = cell + 1 if not part.startswith("</") else max(0, cell - 1)
            out.append(part)
            continue
        if depth == 0:
            part = GRADE_RE.sub(lambda m: badge(m.group(1)), part)
            part = MARKER_RE.sub(lambda m: cite(m.group(1), bid, srcs), part)
            part = ASK_RE.sub('<span class="badge g-ask" title="Ask this in the room">ask</span>', part)
            part = IMG_PATH_RE.sub(lambda m: inline_path(m.group(1), dirs, cell > 0), part)
        out.append(part)
    return "".join(out)

def inline_md(text, dirs):
    """One line of markdown to inline HTML, with every link opening in a new tab."""
    MD.reset()
    html = MD.convert(BARE_URL_RE.sub(lambda m: "<%s>" % m.group(0), text)).strip().replace("</p>\n<p>", "<br>")
    html = postprocess(html[3:-4] if html.startswith("<p>") and html.endswith("</p>") else html, dirs)
    return html.replace('<a href="http', '<a target="_blank" rel="noopener" href="http')

def sources_html(entries, bid, dirs):
    """The footer block: one anchored line per numbered source, links opening in a new tab."""
    rows = ['<p%s>%s%s</p>' % (' id="src-%s-%s"' % (bid, num) if num else "",
                               '<span class="n">%s</span>' % escape(num) if num else "",
                               inline_md(text, dirs)) for num, text in entries]
    return ('<details class="srcs"><summary>Sources (%d)</summary><div class="sources">%s</div></details>'
            % (len(rows), "".join(rows)))

def to_html(md_text, dirs, cards=True):
    """Markdown to HTML, with any 'Sources:' block moved to a collapsed footer, citations linked
    and shown on hover, and wide tables turned into cards unless `cards` is False."""
    if not md_text.strip():
        return '<p class="note">Nothing under this heading yet.</p>'
    body, entries = split_sources(md_text)
    cited = bool(entries) or bool(MARKER_RE.search(body))
    BOX[0], bid = BOX[0] + cited, ("b%d" % (BOX[0] + 1) if cited else None)
    MD.reset()
    out = postprocess(tables_html(MD.convert(body), cards), dirs, bid, dict(entries))
    return out + (sources_html(entries, bid, dirs) if entries else "")

def section(sid, title, inner, cls=""):
    return '<section id="%s" class="%s"><h2>%s</h2>%s</section>' % (sid, cls, escape(title), inner)

def missing(path, root):
    shown = path.name if root not in path.parents else path.relative_to(root).as_posix()
    return '<p class="note missing">Not in the workspace: <code>%s</code></p>' % escape(shown)

def strip_h1(body):
    return re.sub(r"^#\s+.*$", "", body, count=1, flags=re.M)
# ------------------------------------------------------------------- canvases
def lean_canvas(doc, dirs, root, path):
    if not doc:
        return missing(path, root)
    meta, body = doc
    _, sections = split_sections(body)
    found = {}
    for head, text in sections:
        area = next((a for n, a in LEAN_KEYS if n in head.lower() and a not in found), None)
        if area:
            found[area] = text
    boxes = ['<div class="canvas-box a-%s"><h3>%s</h3>%s</div>' % (area, escape(label),
             to_html(found.get(area, ""), dirs)) for area, label in LEAN_AREAS]
    return subtitle(meta) + '<div class="lean">%s</div>' % "".join(boxes)

def swot(doc, dirs, root, path):
    if not doc:
        return missing(path, root)
    meta, body = doc
    _, sections = split_sections(body)
    boxes = ['<div class="swot-box s-%s"><h3>%s</h3>%s</div>'
             % (key, key.capitalize(), to_html(pick(sections, key), dirs)) for key in SWOT_KEYS]
    return subtitle(meta) + '<div class="swot">%s</div>' % "".join(boxes)

def aarrr(doc, dirs, root, path):
    if not doc:
        return missing(path, root)
    meta, body = doc
    _, sections = split_sections(body)
    cards = ['<div class="stage"><h3>%s</h3>%s</div>'
             % (key.capitalize(), to_html(pick(sections, key), dirs)) for key in AARRR_KEYS]
    asks = to_html(pick(sections, "open question"), dirs)
    tail = '<div class="asks"><h3>Open questions for the room</h3>%s</div>' % asks
    return subtitle(meta) + '<div class="stages">%s</div>%s' % ("".join(cards), tail)

def parse_factor_table(md_text):
    """Return (factors, companies, scores, evidence) parsed from the first markdown table."""
    rows = []
    for line in md_text.splitlines():
        line = line.strip()
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(c and set(c) <= set("-: ") for c in cells):
                continue
            rows.append(cells)
        elif rows:
            break
    if len(rows) < 2:
        return [], [], [], []
    head = rows[0]
    companies = [c for c in head[1:] if c and "evidence" not in c.lower()]
    ev_col = next((i for i, c in enumerate(head) if "evidence" in c.lower()), None)
    factors, scores, evidence = [], [], []
    score_of = lambda cell: next((int(m) for m in re.findall(r"\d+", cell) if 1 <= int(m) <= 5), None)
    for row in rows[1:]:
        vals = [score_of(cell) for cell in row[1:1 + len(companies)]]
        if row[0] and any(v is not None for v in vals):
            factors.append(row[0])
            scores.append(vals)
            evidence.append(row[ev_col] if ev_col is not None and ev_col < len(row) else "")
    return factors, companies, scores, evidence

def wrap_label(text, width=16, lines=3):
    """Wrap an axis label over at most `lines` rows; the tail folds in, it is never truncated."""
    out = [""]
    for word in text.split():
        if out[-1] and len(out[-1]) + 1 + len(word) > width:
            out.append(word)
        else:
            out[-1] = (out[-1] + " " + word).strip()
    if len(out) > lines:
        out = out[:lines - 1] + [" ".join(out[lines - 1:])]
    return [r for r in out if r] or [text]

def chart_svg(factors, companies, scores, evidence):
    w, h, left, right, top, bottom = 1080, 680, 74, 240, 40, 130
    x1, y1 = w - right, h - bottom
    n = len(factors)
    xs = [left + (x1 - left) * (i / (n - 1)) if n > 1 else (left + x1) / 2 for i in range(n)]
    ypos = lambda v: y1 - (v - 1) / 4 * (y1 - top)
    out = ['<svg class="chart" viewBox="0 0 %d %d" width="%d" height="%d" preserveAspectRatio='
           '"xMidYMid meet" role="img" aria-label="Strategy canvas">' % (w, h, w, h)]
    for score in range(1, 6):
        y = ypos(score)
        out.append('<line class="grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>'
                   '<text class="ax" x="%d" y="%.1f" text-anchor="end">%d</text>'
                   % (left, y, x1, y, left - 14, y + 6, score))
    for i, factor in enumerate(factors):
        spans = "".join('<tspan x="%.1f" dy="%d">%s</tspan>' % (xs[i], 0 if k == 0 else 19, escape(r))
                        for k, r in enumerate(wrap_label(factor)))
        out.append('<text class="ax fx" x="%.1f" y="%d" text-anchor="middle">%s<title>%s</title></text>'
                   % (xs[i], y1 + 30, spans, escape(factor)))
    for j, company in enumerate(companies):
        color = COLORS[j % len(COLORS)]
        pts = [(xs[i], ypos(scores[i][j]), i) for i in range(n) if scores[i][j] is not None]
        if not pts:
            continue
        out.append('<polyline fill="none" stroke="%s" stroke-width="4" stroke-linejoin="round" '
                   'points="%s"/>' % (color, " ".join("%.1f,%.1f" % (p[0], p[1]) for p in pts)))
        for px, py, i in pts:
            tip = "%s: %s\n%s" % (company, scores[i][j], factors[i])
            if evidence and evidence[i]:
                tip += "\n%s" % evidence[i]
            out.append('<circle class="pt" cx="%.1f" cy="%.1f" r="6" fill="%s"><title>%s</title></circle>'
                       % (px, py, color, escape(tip)))
        ly = top + 24 + j * 30
        out.append('<rect x="%d" y="%d" width="16" height="16" rx="3" fill="%s"/>' % (x1 + 34, ly - 13, color))
        out.append('<text class="ax lg" x="%d" y="%d">%s<title>%s</title></text>'
                   % (x1 + 58, ly, escape(company), escape(company)))
    out.append("</svg>")
    return "".join(out)

def strategy_canvas(doc, dirs, root, path):
    if not doc:
        return missing(path, root)
    meta, body = doc
    lead, sections = split_sections(body)
    table_md = pick(sections, "factor table")
    factors, companies, scores, evidence = parse_factor_table(table_md)
    if factors and companies:
        chart = ('<div class="chart-wrap">%s</div>' % chart_svg(factors, companies, scores, evidence)
                 + '<details class="ftable"><summary>Factor table and evidence</summary>%s</details>'
                 % to_html(table_md, dirs, cards=False))
    else:
        chart = ('<p class="note">No numeric factor table found; the file is shown as written.</p>'
                 + to_html(table_md, dirs))
    rest = "".join('<h3>%s</h3>%s' % (escape(head), to_html(text, dirs))
                   for head, text in sections if "factor table" not in head.lower())
    return subtitle(meta) + to_html(lead, dirs) + chart + '<div class="prose cols">%s</div>' % rest
# ------------------------------------------------------------- plain sections
def prose(doc, dirs, root, path, cls="prose"):
    if not doc:
        return missing(path, root)
    meta, body = doc
    return subtitle(meta) + '<div class="%s">%s</div>' % (cls, to_html(strip_h1(body), dirs))

def kv_grid(lead, dirs):
    """Pull the leading identity table out of index.md into a key/value grid."""
    rows, rest = [], []
    for line in lead.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip()[:1] == "|" else None
        if cells is None:
            rest.append(line)
        elif cells[0] and len(cells) > 1 and not all(not c or set(c) <= set("-: ") for c in cells):
            rows.append((cells[0], " ".join(cells[1:]).strip()))
    grid = '<div class="idgrid">%s</div>' % "".join(
        '<div class="k">%s</div><div class="v">%s</div>' % (inline_md(k, dirs), inline_md(v, dirs))
        for k, v in rows) if rows else ""
    return grid, "\n".join(rest).strip()

def overview(doc, dirs, root, path):
    """index.md reordered: identity grid, the ordered headings, Files and Changelog folded away."""
    if not doc:
        return missing(path, root)
    meta, body = doc
    lead, sections = split_sections(strip_h1(body))
    grid, lead_rest = kv_grid(lead, dirs)
    head_html = lambda h, t: '<h3>%s</h3><div class="prose">%s</div>' % (escape(h), to_html(t, dirs))
    out = [subtitle(meta), grid]
    if lead_rest:
        out.append('<div class="prose">%s</div>' % to_html(lead_rest, dirs))
    taken, folded = set(), []
    for needle in OVERVIEW_ORDER:
        hit = next((i for i, (h, _) in enumerate(sections) if needle in h.lower() and i not in taken), None)
        if hit is not None:
            taken.add(hit)
            out.append(head_html(*sections[hit]))
    for i, (head, text) in enumerate(sections):
        if i in taken:
            continue
        if any(key in head.lower() for key in OVERVIEW_FOLD):
            folded.append('<details><summary>%s</summary><div class="prose">%s</div></details>'
                          % (escape(head), to_html(text, dirs)))
        else:
            out.append(head_html(head, text))
    return "".join(out + folded)

def gallery(screens_dir):
    shots = sorted(screens_dir.glob("*.png")) if screens_dir.is_dir() else []
    cells = ['<button class="thumb" type="button" onclick="zoom(this)">%s<span>%s</span></button>'
             % (img_html(shot, "shot", shot_id(shot)), escape(shot.stem)) for shot in shots]
    return ('<div class="strip">%s</div>' % "".join(cells) if shots
            else '<p class="note">No screenshots in <code>product/screens/</code>.</p>')

def raw_material(root, dirs):
    """The six research files, every one collapsed: reference behind the pages above."""
    out = ['<p class="note">Evidence the pages above cite. Reference, not reading.</p>']
    for front in RESEARCH_ORDER:
        path = root / "research" / ("%s.md" % front)
        doc = read_md(path)
        meta, body = doc if doc else ({}, "")
        when = "researched %s" % meta["researched"] if meta.get("researched") else "no date"
        inner = ('<div class="prose">%s</div>' % to_html(strip_h1(body), dirs)) if doc else missing(path, root)
        out.append('<details id="research-%s"><summary>%s <span class="date">%s</span></summary>%s</details>'
                   % (front, escape(meta.get("title") or front.capitalize()),
                      escape(when if doc else "missing"), inner))
    return "".join(out)
# ----------------------------------------------------------------------- page
def build(root):
    dirs = [root, root / "product", root / "product" / "screens", root / "frameworks"]
    fw, prod = root / "frameworks", root / "product"
    index = read_md(root / "index.md")
    company = first_h1(index[1], root.name) if index else root.name
    blocks, nav = [], []

    def add(sid, label, title, inner, cls=""):
        nav.append((sid, label))
        blocks.append(section(sid, title, inner, cls))

    add("overview", "Overview", "Overview", overview(index, dirs, root, root / "index.md"))
    add("point-of-view", "Point of view", "Point of view",
        prose(read_md(root / "point-of-view.md"), dirs, root, root / "point-of-view.md", "prose pov"),
        "feature")

    canvases = [
        ("strategy-canvas", "Strategy canvas",
         strategy_canvas(read_md(fw / "strategy-canvas.md"), dirs, root, fw / "strategy-canvas.md")),
        ("swot", "SWOT", swot(read_md(fw / "swot.md"), dirs, root, fw / "swot.md")),
        ("lean-canvas", "Lean Canvas",
         lean_canvas(read_md(fw / "lean-canvas.md"), dirs, root, fw / "lean-canvas.md")),
        ("aarrr", "AARRR funnel", aarrr(read_md(fw / "aarrr.md"), dirs, root, fw / "aarrr.md")),
    ]
    nav.append(("canvases", "Canvases"))
    inner = "".join('<div class="sub-section" id="%s"><h3>%s</h3>%s</div>' % (sid, escape(label), html)
                    for sid, label, html in canvases)
    blocks.append(section("canvases", "Canvases", inner, "wide"))
    nav.extend((sid, "— " + label) for sid, label, _ in canvases)

    product = (prose(read_md(prod / "product-map.md"), dirs, root, prod / "product-map.md")
               + "<h3>Screens</h3>" + gallery(prod / "screens")
               + "<h3>Onboarding and activation teardown</h3>"
               + prose(read_md(prod / "onboarding-teardown.md"), dirs, root, prod / "onboarding-teardown.md"))
    add("product", "Product", "Product", product, "wide")
    add("claims", "Claims register", "Claims register",
        prose(read_md(root / "claims-register.md"), dirs, root, root / "claims-register.md"), "wide")
    add("decisions", "Decisions", "Decisions",
        prose(read_md(root / "decisions.md"), dirs, root, root / "decisions.md"), "wide")
    add("raw-material", "Raw material", "Raw material", raw_material(root, dirs))

    links = "".join('<li><a href="#%s">%s</a></li>' % (sid, escape(label)) for sid, label in nav)
    return PAGE % {"title": escape(company), "nav": links, "body": "".join(blocks),
                   "date": date.today().isoformat(), "css": CSS, "js": JS}

CSS = """
:root{--bg:#fbfbfa;--fg:#1c1c1e;--mut:#5f6368;--line:#dcdcd8;--card:#fff;--accent:#1d4ed8;--shade:#f2f2ef}
@media(prefers-color-scheme:dark){:root{--bg:#15161a;--fg:#e9e9ec;--mut:#a0a3ad;--line:#2f313a;--card:#1d1f25;--accent:#7aa2ff;--shade:#22242b}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);overflow-x:hidden;font:16px/1.55 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
h1,h2,h3,h4{line-height:1.25;font-weight:650} h1{font-size:1.6rem;margin:0} h2{font-size:1.35rem;margin:0 0 .4rem} h3{font-size:1.02rem;margin:1.4rem 0 .4rem} a{color:var(--accent)}
.top{position:sticky;top:0;z-index:9;background:var(--card);border-bottom:1px solid var(--line);padding:.7rem 1.2rem;display:flex;gap:1rem;align-items:baseline;flex-wrap:wrap} .top .sub{margin:0}
.shell{display:grid;grid-template-columns:200px minmax(0,1fr);gap:2rem;max-width:1480px;margin:0 auto;padding:1.2rem} main{min-width:0} nav ul{list-style:none;margin:0;padding:0}
nav{position:sticky;top:3.4rem;align-self:start;max-height:calc(100vh - 4rem);overflow:auto} nav a{display:block;padding:.24rem .5rem;border-radius:5px;text-decoration:none;color:var(--mut);font-size:.88rem} nav a:hover{background:var(--shade);color:var(--fg)}
section{margin:0 0 2.6rem;padding-top:.6rem;border-top:1px solid var(--line)} section:first-of-type{border-top:0}
.prose>p,.prose>ul,.prose>ol,.prose>blockquote,.prose>h3,.prose>h4{max-width:74ch} .prose>ul,.prose>ol{padding-left:1.4rem}
.feature .prose{font-size:1.06rem} .feature .prose>p,.feature .prose>ul,.feature .prose>ol{max-width:78ch} .feature h3{margin-top:1.6rem;color:var(--accent)} .cols{max-width:none;column-count:2;column-gap:2.4rem} .cols h3{margin-top:0;break-after:avoid} .cols>*{break-inside:avoid}
.sub{margin:.1rem 0 1rem;color:var(--mut);font-size:.8rem} .note{color:var(--mut);font-size:.86rem;font-style:italic} .missing{border-left:3px solid var(--line);padding-left:.6rem}
.table-wrap{overflow-x:auto;max-width:100%;margin:.8rem 0;border:1px solid var(--line);border-radius:8px} table{border-collapse:collapse;font-size:.88rem;min-width:100%} th,td{border-bottom:1px solid var(--line);padding:.4rem .6rem;text-align:left;vertical-align:top;overflow-wrap:anywhere} th{background:var(--shade);white-space:nowrap}
.cards{display:grid;gap:.6rem;margin:.8rem 0;grid-template-columns:repeat(auto-fit,minmax(min(100%,560px),1fr))} .card{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.65rem .85rem;font-size:.9rem;min-width:0}
.card h4{margin:0 0 .45rem;font-size:.95rem;font-weight:600;line-height:1.35} .card dl{display:grid;grid-template-columns:minmax(6.5rem,10rem) minmax(0,1fr);gap:.22rem 1rem;margin:0} .card dt{color:var(--mut);font-size:.8rem;font-weight:600;padding-top:.1rem} .card dd{margin:0;overflow-wrap:anywhere}
code{background:var(--shade);padding:.1em .3em;border-radius:4px;font-size:.88em;overflow-wrap:anywhere} img{max-width:100%;height:auto} blockquote{margin:.8rem 0;padding-left:.8rem;border-left:3px solid var(--line);color:var(--mut)}
.badge{display:inline-block;min-width:1.15em;padding:0 .32em;margin:0 .12em;border-radius:4px;font-size:.72em;font-weight:700;line-height:1.5;text-align:center;color:#fff;vertical-align:.08em} .g-v{background:#15803d}.g-r{background:#b45309}.g-i{background:#1d4ed8}.g-u{background:#6b7280}.g-o{background:#7c3aed}.g-ask{background:#0f766e;padding:0 .4em}
sup.cite{font-size:.68em;line-height:0;font-weight:600;margin-left:.05em} sup.cite a{text-decoration:none} sup.cite+sup.cite::before{content:",";margin-right:.08em}
details.srcs{border:0;border-top:1px solid var(--line);border-radius:0;background:none;margin:.7rem 0 0;padding:0} details.srcs summary{font-size:.66rem;font-weight:600;text-transform:uppercase;letter-spacing:.06em;color:var(--mut);padding:.35rem 0}
.sources{color:var(--mut);font-size:.76rem;line-height:1.4;padding-bottom:.3rem;overflow-wrap:anywhere} .sources p{margin:.16rem 0} .sources .n{font-weight:700;margin-right:.35rem}
.idgrid{display:grid;grid-template-columns:minmax(8rem,14%) minmax(0,1fr);gap:0 1.1rem;margin:.4rem 0 1.4rem;max-width:96ch} .idgrid .k{font-weight:650;font-size:.82rem;color:var(--mut)} .idgrid .k,.idgrid .v{padding:.4rem 0;border-top:1px solid var(--line)} .idgrid .v{font-size:.9rem}
.lean{display:grid;gap:.6rem;grid-template-columns:repeat(3,minmax(0,1fr));grid-template-areas:"problem solution uvp" "problem metrics uvp" "advantage channels segments" "cost cost revenue"}
.a-problem{grid-area:problem}.a-solution{grid-area:solution}.a-uvp{grid-area:uvp}.a-advantage{grid-area:advantage}.a-segments{grid-area:segments}.a-metrics{grid-area:metrics}.a-channels{grid-area:channels}.a-cost{grid-area:cost}.a-revenue{grid-area:revenue}
.canvas-box,.swot-box,.stage,.asks{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.6rem .7rem;font-size:.86rem;min-width:0;overflow-wrap:anywhere} .canvas-box,.swot-box{line-height:1.38}
.canvas-box h3,.swot-box h3,.stage h3{margin:0 0 .3rem;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.canvas-box ul,.swot-box ul,.stage ul{padding-left:1.1rem;margin:.25rem 0} .canvas-box li,.swot-box li{margin:.18rem 0} .canvas-box p,.swot-box p,.stage p{margin:.3rem 0}
.swot{display:grid;gap:.6rem;grid-template-columns:repeat(2,minmax(0,1fr))} .s-strengths{border-top:3px solid #15803d}.s-weaknesses{border-top:3px solid #b91c1c}.s-opportunities{border-top:3px solid #1d4ed8}.s-threats{border-top:3px solid #b45309}
.stages{display:flex;gap:.6rem;flex-wrap:wrap} .stages .stage{flex:1 1 300px} .asks{margin-top:.8rem} .strip{display:flex;gap:.6rem;overflow-x:auto;padding:.4rem 0}
.chart-wrap{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:.6rem .4rem;margin:.8rem 0 1rem} .chart{width:100%;height:auto;min-height:560px;display:block} .chart .grid{stroke:var(--line)}
.chart .ax{fill:var(--mut);font-size:14px;font-family:inherit} .chart .fx{fill:var(--fg);font-size:13px} .chart .lg{font-size:15px;fill:var(--fg)} .chart .pt{cursor:pointer} .chart .pt:hover{r:9}
details.ftable{font-size:.9rem} details.ftable summary{font-weight:500;color:var(--mut)}
.thumb{flex:0 0 auto;width:160px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.35rem;cursor:zoom-in;font:inherit;color:var(--mut)}
.thumb img{display:block;width:100%;height:96px;object-fit:cover;border-radius:4px;background:var(--shade)}
.thumb span{display:block;font-size:.72rem;margin-top:.25rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap} .inline-shot{max-height:110px;border:1px solid var(--line);border-radius:4px;vertical-align:middle}
.screen-link{font-size:.85em;white-space:nowrap;text-decoration:underline dotted}
.shot-ref{display:inline-block;text-decoration:none;font-size:.75em;color:var(--mut);margin:.1rem .3rem .1rem 0;vertical-align:top} .shot-ref img{display:block;max-height:110px;max-width:160px;object-fit:cover;object-position:top} .shot-ref span{display:block}
#lightbox{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:50;cursor:zoom-out} #lightbox.on{display:flex} #lightbox img{max-width:92vw;max-height:92vh}
details{border:1px solid var(--line);border-radius:8px;background:var(--card);margin:.5rem 0;padding:.2rem .8rem} summary{cursor:pointer;font-weight:650;padding:.5rem 0} summary .date{font-weight:400;color:var(--mut);font-size:.8rem;margin-left:.4rem}
.sub-section{margin-bottom:2rem} .sub-section>h3{font-size:1.1rem;margin:1.2rem 0 .6rem;padding-bottom:.2rem;border-bottom:1px solid var(--line)}
footer{border-top:1px solid var(--line);padding:1rem 1.2rem;color:var(--mut);font-size:.82rem;text-align:center} .sources a{color:var(--accent)}
@media(max-width:900px){
 .shell{grid-template-columns:minmax(0,1fr);gap:.8rem;padding:.8rem}
 nav{position:sticky;top:2.9rem;max-height:none;background:var(--bg);border-bottom:1px solid var(--line);padding:.3rem 0;z-index:8}
 nav ul{display:flex;gap:.3rem;overflow-x:auto} nav a{white-space:nowrap}
 .cols{column-count:1} .chart{min-height:0} .idgrid{grid-template-columns:minmax(0,1fr);gap:0} .idgrid .v{border-top:0;padding-top:0} .card dl{grid-template-columns:minmax(0,1fr)} .card dt{padding-top:.3rem}
 .lean{grid-template-columns:minmax(0,1fr);grid-template-areas:"problem" "solution" "uvp" "advantage" "segments" "metrics" "channels" "cost" "revenue"}
 .swot{grid-template-columns:minmax(0,1fr)}}
@media print{
 nav,#lightbox{display:none} .top{position:static} .shell{display:block;max-width:none;padding:0}
 details>*{display:block!important} details{border-color:#999} .cols{column-count:1}
 details.srcs summary{display:none} details,section,.canvas-box,.swot-box,.stage,.card{break-inside:avoid} body{background:#fff;color:#000;font-size:11pt}}
"""

JS = """
var box=document.getElementById('lightbox');
function zoom(el){box.querySelector('img').src=el.querySelector('img').src;box.classList.add('on');}
function zoomShot(el){var img=document.getElementById(el.getAttribute('data-shot'));if(img){box.querySelector('img').src=img.src;box.classList.add('on');}return false;}
box.addEventListener('click',function(){box.classList.remove('on');});
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('sup.cite a');if(!a){return;}var t=document.getElementById(a.getAttribute('href').slice(1));var d=t&&t.closest('details');if(d){d.open=true;}});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){box.classList.remove('on');}});
document.querySelectorAll('img.inline-shot[data-shot]').forEach(function(t){var g=document.getElementById(t.getAttribute('data-shot'));if(g){t.src=g.src;}else{t.remove();}});
window.addEventListener('beforeprint',function(){document.querySelectorAll('details').forEach(function(d){d.open=true;});});
"""

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%(title)s &mdash; research walkthrough</title>
<style>%(css)s</style></head>
<body>
<header class="top"><h1>%(title)s</h1><p class="sub">Research walkthrough &middot; rendered %(date)s</p></header>
<div class="shell">
<nav><ul>%(nav)s</ul></nav>
<main>
%(body)s
</main>
</div>
<div id="lightbox"><img alt="screenshot"></div>
<footer>Rendered %(date)s from Markdown; the Markdown is the source of truth.</footer>
<script>%(js)s</script>
</body></html>
"""

def main():
    ap = argparse.ArgumentParser(description="Render a company workspace to one self-contained HTML page.")
    ap.add_argument("workspace", help="path to companies/<slug>")
    ap.add_argument("--open", action="store_true", dest="open_it", help="open the page in the browser")
    ap.add_argument("--full-images", action="store_true", dest="full_images",
                     help="embed screenshots at full size/PNG instead of downscaling to JPEG")
    args = ap.parse_args()
    global FULL_IMAGES
    FULL_IMAGES = args.full_images
    if Image is None and not FULL_IMAGES:
        print("render.py: Pillow not found, embedding full-size images -- pip install --user pillow",
              file=sys.stderr)
    root = Path(args.workspace).expanduser().resolve()
    if not root.is_dir():
        sys.exit("render.py: no such workspace folder: %s" % root)
    out = root / "site" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(root), encoding="utf-8")
    print("wrote %s (%.0f KB)" % (out, out.stat().st_size / 1024))
    if args.open_it:
        webbrowser.open(out.as_uri())

if __name__ == "__main__":
    main()
