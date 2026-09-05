#!/usr/bin/env python3
"""render.py -- Render one company research workspace into a single self-contained HTML page.

Usage:
  python toolbox/render.py companies/<slug> [--open]

Writes companies/<slug>/site/index.html: one page to screen-share in an interview.
Images are inlined as data URIs, so the file works with no network and no CDN.
Missing files are skipped with a note in the page; only a missing workspace is fatal.

Dependency: markdown (pip install --user markdown). Everything else is stdlib.
"""
import argparse, base64, mimetypes, re, sys, webbrowser
from datetime import date
from html import escape
from pathlib import Path

try:
    import markdown
except ImportError:
    sys.exit("render.py: missing dependency 'markdown' -- run: pip install --user markdown")

MD = markdown.Markdown(extensions=["tables", "fenced_code", "sane_lists"])
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
TAG_RE = re.compile(r"(<[^>]+>)")
GRADE_RE = re.compile(r"\[(V|R|I|U|O)\]")
ASK_RE = re.compile(r"\(ask\)")
IMG_PATH_RE = re.compile(r"(?<![\w/\-.])((?:[\w.\-]+/)+[\w.\-]+\.(?:png|jpe?g|gif|webp))")
SRC_RE = re.compile(r'src="([^"]+)"')
GRADES = {"V": ("Verified", "g-v"), "R": ("Reported", "g-r"), "I": ("Inferred", "g-i"),
          "U": ("Unknown", "g-u"), "O": ("Opinion", "g-o")}
DATE_KEYS = ("researched", "filled", "walked", "written", "curated", "updated")
COLORS = ["#2563eb", "#d97706", "#059669", "#dc2626", "#7c3aed", "#0891b2", "#c026d3", "#65a30d"]
RESEARCH_ORDER = ["business", "money", "people", "users", "culture", "market"]
LEAN_AREAS = [("problem", "Problem"), ("solution", "Solution"), ("uvp", "Unique value proposition"),
              ("advantage", "Unfair advantage"), ("segments", "Customer segments"),
              ("metrics", "Key metrics"), ("channels", "Channels"),
              ("cost", "Cost structure"), ("revenue", "Revenue streams")]
LEAN_KEYS = [("unique value", "uvp"), ("unfair", "advantage"), ("customer segment", "segments"),
             ("key metric", "metrics"), ("channel", "channels"), ("cost", "cost"),
             ("revenue", "revenue"), ("problem", "problem"), ("solution", "solution")]
SWOT_KEYS = ["strengths", "weaknesses", "opportunities", "threats"]
AARRR_KEYS = ["acquisition", "activation", "retention", "revenue", "referral"]
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
    bits = []
    if meta.get("title"):
        bits.append(escape(meta["title"]))
    for key in DATE_KEYS:
        if meta.get(key):
            bits.append("%s %s" % (key, escape(meta[key])))
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
# ------------------------------------------------------------- html transform
def data_uri(path):
    kind = mimetypes.guess_type(path.name)[0] or "image/png"
    return "data:%s;base64,%s" % (kind, base64.b64encode(path.read_bytes()).decode("ascii"))

def resolve(ref, dirs):
    """Find a relative image reference inside the workspace; None if it is not there."""
    ref = ref.replace("\\", "/")
    if ref.startswith(("http:", "https:", "data:", "/")):
        return None
    ref = ref.lstrip("./")
    for base in dirs:
        cand = base / ref
        if cand.is_file():
            return cand
    return None

def img_html(path, cls="shot"):
    return '<img class="%s" loading="lazy" alt="%s" src="%s">' % (cls, escape(path.name), data_uri(path))

def badge(letter):
    label, cls = GRADES[letter]
    return '<span class="badge %s" title="%s">%s</span>' % (cls, label, letter)

def inline_path(ref, dirs):
    target = resolve(ref, dirs)
    return img_html(target, "inline-shot") if target else escape(ref)

def postprocess(text, dirs):
    """Badge the grades and inline the images, skipping anything inside a tag or code."""
    out, depth = [], 0
    for part in TAG_RE.split(text):
        if part.startswith("<"):
            low = part.lower()
            if low.startswith("<img"):
                found = SRC_RE.search(part)
                target = resolve(found.group(1), dirs) if found else None
                part = img_html(target) if target else part
            elif low.startswith(("<pre", "<code")):
                depth += 1
            elif low.startswith(("</pre", "</code")):
                depth = max(0, depth - 1)
            out.append(part)
            continue
        if depth == 0:
            part = GRADE_RE.sub(lambda m: badge(m.group(1)), part)
            part = ASK_RE.sub('<span class="badge g-ask" title="Ask this in the room">ask</span>', part)
            part = IMG_PATH_RE.sub(lambda m: inline_path(m.group(1), dirs), part)
        out.append(part)
    return "".join(out)

def to_html(md_text, dirs):
    if not md_text.strip():
        return '<p class="note">Nothing under this heading yet.</p>'
    MD.reset()
    out = MD.convert(md_text)
    out = out.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    return postprocess(out, dirs)

def section(sid, title, inner, cls=""):
    return ('<section id="%s" class="%s">\n<h2>%s</h2>\n%s\n</section>\n'
            % (sid, cls, escape(title), inner))

def missing(path, root):
    try:
        shown = path.relative_to(root).as_posix()
    except ValueError:
        shown = path.name
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
        low = head.lower()
        for needle, area in LEAN_KEYS:
            if needle in low and area not in found:
                found[area] = text
                break
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
    """Return (factors, companies, scores) parsed from the first markdown table."""
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
        return [], [], []
    companies = [c for c in rows[0][1:] if c and "evidence" not in c.lower()]
    factors, scores = [], []
    for row in rows[1:]:
        vals = []
        for cell in row[1:1 + len(companies)]:
            hit = re.search(r"\d+", cell)
            val = int(hit.group()) if hit else None
            vals.append(val if val is not None and 1 <= val <= 5 else None)
        if row[0] and any(v is not None for v in vals):
            factors.append(row[0])
            scores.append(vals)
    return factors, companies, scores

def chart_svg(factors, companies, scores):
    w, h, left, right, top, bottom = 860, 380, 58, 200, 20, 66
    x1, y1 = w - right, h - bottom
    n = len(factors)
    xs = [left + (x1 - left) * (i / (n - 1)) if n > 1 else (left + x1) / 2 for i in range(n)]
    ypos = lambda v: y1 - (v - 1) / 4 * (y1 - top)
    out = ['<svg class="chart" viewBox="0 0 %d %d" role="img" aria-label="Strategy canvas">' % (w, h)]
    for score in range(1, 6):
        y = ypos(score)
        out.append('<line class="grid" x1="%d" y1="%.1f" x2="%d" y2="%.1f"/>' % (left, y, x1, y))
        out.append('<text class="ax" x="%d" y="%.1f" text-anchor="end">%d</text>' % (left - 10, y + 4, score))
    for i, factor in enumerate(factors):
        label = factor if len(factor) <= 16 else factor[:15] + "…"
        out.append('<text class="ax" x="%.1f" y="%d" text-anchor="middle">%s<title>%s</title></text>'
                   % (xs[i], y1 + 22, escape(label), escape(factor)))
    for j, company in enumerate(companies):
        color = COLORS[j % len(COLORS)]
        pts = [(xs[i], ypos(scores[i][j])) for i in range(n) if scores[i][j] is not None]
        if not pts:
            continue
        out.append('<polyline fill="none" stroke="%s" stroke-width="2.5" points="%s"/>'
                   % (color, " ".join("%.1f,%.1f" % p for p in pts)))
        for px, py in pts:
            out.append('<circle cx="%.1f" cy="%.1f" r="3.5" fill="%s"/>' % (px, py, color))
        ly = top + 18 + j * 22
        out.append('<rect x="%d" y="%d" width="12" height="12" rx="2" fill="%s"/>' % (x1 + 26, ly - 10, color))
        out.append('<text class="ax" x="%d" y="%d">%s</text>' % (x1 + 44, ly, escape(company[:22])))
    out.append("</svg>")
    return "".join(out)

def strategy_canvas(doc, dirs, root, path):
    if not doc:
        return missing(path, root)
    meta, body = doc
    lead, sections = split_sections(body)
    table_md = pick(sections, "factor table")
    factors, companies, scores = parse_factor_table(table_md)
    if factors and companies:
        chart = chart_svg(factors, companies, scores)
    else:
        chart = ('<p class="note">No numeric factor table found; the file is shown as written.</p>'
                 + to_html(table_md, dirs))
    rest = "".join('<h3>%s</h3>%s' % (escape(head), to_html(text, dirs))
                   for head, text in sections if "factor table" not in head.lower())
    return subtitle(meta) + to_html(lead, dirs) + chart + '<div class="prose">%s</div>' % rest
# ------------------------------------------------------------- plain sections
def prose(doc, dirs, root, path, cls="prose"):
    if not doc:
        return missing(path, root)
    meta, body = doc
    return subtitle(meta) + '<div class="%s">%s</div>' % (cls, to_html(strip_h1(body), dirs))

def gallery(screens_dir):
    shots = sorted(screens_dir.glob("*.png")) if screens_dir.is_dir() else []
    if not shots:
        return '<p class="note">No screenshots in <code>product/screens/</code>.</p>'
    cells = ['<button class="thumb" type="button" onclick="zoom(this)">%s<span>%s</span></button>'
             % (img_html(shot), escape(shot.stem)) for shot in shots]
    return '<div class="strip">%s</div>' % "".join(cells)

def research(root, dirs):
    out = []
    for i, front in enumerate(RESEARCH_ORDER):
        path = root / "research" / ("%s.md" % front)
        doc = read_md(path)
        open_attr = " open" if i == 0 else ""
        if not doc:
            out.append('<details%s id="research-%s"><summary>%s <span class="date">missing</span>'
                       '</summary>%s</details>'
                       % (open_attr, front, front.capitalize(), missing(path, root)))
            continue
        meta, body = doc
        when = meta.get("researched", "")
        out.append('<details%s id="research-%s"><summary>%s <span class="date">%s</span></summary>'
                   '<div class="prose">%s</div></details>'
                   % (open_attr, front, escape(meta.get("title") or front.capitalize()),
                      escape("researched %s" % when if when else "no date"), to_html(strip_h1(body), dirs)))
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

    add("overview", "Overview", "Overview", prose(index, dirs, root, root / "index.md"))
    add("point-of-view", "Point of view", "Point of view",
        prose(read_md(root / "point-of-view.md"), dirs, root, root / "point-of-view.md", "prose pov"),
        "feature")

    canvases = [
        ("lean-canvas", "Lean Canvas",
         lean_canvas(read_md(fw / "lean-canvas.md"), dirs, root, fw / "lean-canvas.md")),
        ("swot", "SWOT", swot(read_md(fw / "swot.md"), dirs, root, fw / "swot.md")),
        ("aarrr", "AARRR funnel", aarrr(read_md(fw / "aarrr.md"), dirs, root, fw / "aarrr.md")),
        ("strategy-canvas", "Strategy canvas",
         strategy_canvas(read_md(fw / "strategy-canvas.md"), dirs, root, fw / "strategy-canvas.md")),
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
    add("research", "Research", "Research", research(root, dirs))
    add("claims", "Claims register", "Claims register",
        prose(read_md(root / "claims-register.md"), dirs, root, root / "claims-register.md"), "wide")
    add("decisions", "Decisions", "Decisions",
        prose(read_md(root / "decisions.md"), dirs, root, root / "decisions.md"), "wide")

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
.shell{display:grid;grid-template-columns:216px minmax(0,1fr);gap:2rem;max-width:1240px;margin:0 auto;padding:1.2rem} main{min-width:0}
nav{position:sticky;top:3.4rem;align-self:start;max-height:calc(100vh - 4rem);overflow:auto} nav ul{list-style:none;margin:0;padding:0}
nav a{display:block;padding:.24rem .5rem;border-radius:5px;text-decoration:none;color:var(--mut);font-size:.88rem} nav a:hover{background:var(--shade);color:var(--fg)}
section{margin:0 0 2.6rem;padding-top:.6rem;border-top:1px solid var(--line)} section:first-of-type{border-top:0}
.prose{max-width:70ch} .feature .prose{max-width:74ch;font-size:1.06rem} .feature h3{margin-top:1.6rem;color:var(--accent)}
.sub{margin:.1rem 0 1rem;color:var(--mut);font-size:.8rem} .note{color:var(--mut);font-size:.86rem;font-style:italic} .missing{border-left:3px solid var(--line);padding-left:.6rem}
.table-wrap{overflow-x:auto;max-width:100%;margin:.8rem 0;border:1px solid var(--line);border-radius:8px} table{border-collapse:collapse;font-size:.88rem;min-width:100%} th,td{border-bottom:1px solid var(--line);padding:.4rem .6rem;text-align:left;vertical-align:top} th{background:var(--shade);white-space:nowrap}
code{background:var(--shade);padding:.1em .3em;border-radius:4px;font-size:.88em} img{max-width:100%;height:auto} blockquote{margin:.8rem 0;padding-left:.8rem;border-left:3px solid var(--line);color:var(--mut)}
.badge{display:inline-block;min-width:1.15em;padding:0 .32em;margin:0 .12em;border-radius:4px;font-size:.72em;font-weight:700;line-height:1.5;text-align:center;color:#fff;vertical-align:.08em}
.g-v{background:#15803d}.g-r{background:#b45309}.g-i{background:#1d4ed8}.g-u{background:#6b7280}.g-o{background:#7c3aed}.g-ask{background:#0f766e;padding:0 .4em}
.lean{display:grid;gap:.6rem;grid-template-columns:repeat(5,minmax(0,1fr));grid-template-areas:"problem solution uvp advantage segments" "problem metrics uvp channels segments" "cost cost cost revenue revenue"}
.a-problem{grid-area:problem}.a-solution{grid-area:solution}.a-uvp{grid-area:uvp}.a-advantage{grid-area:advantage}.a-segments{grid-area:segments}
.a-metrics{grid-area:metrics}.a-channels{grid-area:channels}.a-cost{grid-area:cost}.a-revenue{grid-area:revenue}
.canvas-box,.swot-box,.stage,.asks{background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.6rem .7rem;font-size:.86rem;overflow:hidden}
.canvas-box h3,.swot-box h3,.stage h3{margin:0 0 .3rem;font-size:.78rem;text-transform:uppercase;letter-spacing:.04em;color:var(--mut)}
.canvas-box ul,.swot-box ul,.stage ul{padding-left:1.1rem;margin:.3rem 0} .canvas-box p,.swot-box p,.stage p{margin:.3rem 0}
.swot{display:grid;gap:.6rem;grid-template-columns:repeat(2,minmax(0,1fr))} .s-strengths{border-top:3px solid #15803d}.s-weaknesses{border-top:3px solid #b91c1c}.s-opportunities{border-top:3px solid #1d4ed8}.s-threats{border-top:3px solid #b45309}
.stages{display:flex;gap:.6rem;flex-wrap:wrap} .stages .stage{flex:1 1 175px} .asks{margin-top:.8rem}
.chart{width:100%;height:auto;max-width:900px;display:block;margin:.6rem 0} .chart .grid{stroke:var(--line)} .chart .ax{fill:var(--mut);font-size:11px;font-family:inherit}
.strip{display:flex;gap:.6rem;overflow-x:auto;padding:.4rem 0}
.thumb{flex:0 0 auto;width:160px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:.35rem;cursor:zoom-in;font:inherit;color:var(--mut)}
.thumb img{display:block;width:100%;height:96px;object-fit:cover;border-radius:4px;background:var(--shade)}
.thumb span{display:block;font-size:.72rem;margin-top:.25rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.inline-shot{max-height:110px;border:1px solid var(--line);border-radius:4px;vertical-align:middle}
#lightbox{position:fixed;inset:0;background:rgba(0,0,0,.85);display:none;align-items:center;justify-content:center;z-index:50;cursor:zoom-out}
#lightbox.on{display:flex} #lightbox img{max-width:92vw;max-height:92vh}
details{border:1px solid var(--line);border-radius:8px;background:var(--card);margin:.5rem 0;padding:.2rem .8rem}
summary{cursor:pointer;font-weight:650;padding:.5rem 0} summary .date{font-weight:400;color:var(--mut);font-size:.8rem;margin-left:.4rem}
.sub-section{margin-bottom:2rem} .sub-section>h3{font-size:1.1rem;margin:1.2rem 0 .6rem;padding-bottom:.2rem;border-bottom:1px solid var(--line)}
footer{border-top:1px solid var(--line);padding:1rem 1.2rem;color:var(--mut);font-size:.82rem;text-align:center}
@media(max-width:900px){
 .shell{grid-template-columns:minmax(0,1fr);gap:.8rem;padding:.8rem}
 nav{position:sticky;top:2.9rem;max-height:none;background:var(--bg);border-bottom:1px solid var(--line);padding:.3rem 0;z-index:8}
 nav ul{display:flex;gap:.3rem;overflow-x:auto} nav a{white-space:nowrap}
 .lean{grid-template-columns:minmax(0,1fr);grid-template-areas:"problem" "solution" "uvp" "advantage" "segments" "metrics" "channels" "cost" "revenue"}
 .swot{grid-template-columns:minmax(0,1fr)}}
@media print{
 nav,#lightbox{display:none} .top{position:static} .shell{display:block;max-width:none;padding:0}
 details>*{display:block!important} details{border-color:#999}
 details,section,.canvas-box,.swot-box,.stage{break-inside:avoid} body{background:#fff;color:#000;font-size:11pt}}
"""

JS = """
var box=document.getElementById('lightbox');
function zoom(el){box.querySelector('img').src=el.querySelector('img').src;box.classList.add('on');}
box.addEventListener('click',function(){box.classList.remove('on');});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){box.classList.remove('on');}});
window.addEventListener('beforeprint',function(){
 document.querySelectorAll('details').forEach(function(d){d.open=true;});});
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
    args = ap.parse_args()
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
