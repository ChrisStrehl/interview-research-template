#!/usr/bin/env python3
"""Read the dedicated research inbox over IMAP (Gmail with an app password).

Configuration comes only from environment variables, never from a file in the repo:
  RESEARCH_MAIL_ADDRESS        the account, e.g. someone@gmail.com
  RESEARCH_MAIL_APP_PASSWORD   a Google App Password (2-step verification required)
  RESEARCH_MAIL_IMAP_HOST      default imap.gmail.com
  RESEARCH_MAIL_IMAP_PORT      default 993
Put them in the `env` block of ~/.claude/settings.json.

Commands:
  address [--alias slug]      the address, or the plus-address for one company
  check                       log in and report the message count
  inbox [--limit N] [--alias slug] [--unseen]
  read <uid> [--mark-seen]    body plus extracted codes and links
  wait [--alias slug] [--from s] [--subject s] [--timeout 180] [--interval 10]
"""
import argparse, email, imaplib, json, os, re, sys, time
from email.header import decode_header, make_header
from html import unescape

def die(msg, code=1):
    print(f"mailbox.py: {msg}", file=sys.stderr); sys.exit(code)

def config():
    addr = os.environ.get("RESEARCH_MAIL_ADDRESS")
    pw = os.environ.get("RESEARCH_MAIL_APP_PASSWORD")
    for name, val in (("RESEARCH_MAIL_ADDRESS", addr), ("RESEARCH_MAIL_APP_PASSWORD", pw)):
        if not val or val.startswith("PASTE-"):
            die(f"{name} is not set; add it to the env block of ~/.claude/settings.json")
    return addr, pw, os.environ.get("RESEARCH_MAIL_IMAP_HOST", "imap.gmail.com"), int(os.environ.get("RESEARCH_MAIL_IMAP_PORT", "993"))

def alias_of(addr, slug):
    local, _, domain = addr.partition("@")
    return f"{local}+{slug}@{domain}" if slug else addr

def connect():
    addr, pw, host, port = config()
    try:
        m = imaplib.IMAP4_SSL(host, port, timeout=30)
        m.login(addr, pw)
    except imaplib.IMAP4.error as e:
        die(f"login failed for {addr}: {e}. Gmail needs 2-step verification and an App Password (Google Account > Security > App passwords)")
    except OSError as e:
        die(f"cannot reach {host}:{port}: {e}")
    m.select("INBOX")
    return m, addr

def hdr(msg, name):
    raw = msg.get(name, "")
    try:
        return str(make_header(decode_header(raw)))
    except Exception:
        return raw

def body_text(msg):
    plain, html_part = None, None
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        ctype = part.get_content_type()
        if part.get_content_disposition() == "attachment":
            continue
        try:
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            text = payload.decode(part.get_content_charset() or "utf-8", errors="replace")
        except Exception:
            continue
        if ctype == "text/plain" and plain is None:
            plain = text
        elif ctype == "text/html" and html_part is None:
            html_part = text
    if plain:
        return plain.strip()
    if html_part:
        t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html_part, flags=re.S | re.I)
        t = re.sub(r"<br\s*/?>|</p>|</div>|</tr>", "\n", t, flags=re.I)
        t = re.sub(r"<[^>]+>", " ", t)
        return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n\n", unescape(t))).strip()
    return ""

def fetch(m, uid):
    typ, data = m.uid("fetch", uid, "(RFC822)")
    if typ != "OK" or not data or data[0] is None:
        die(f"no message with uid {uid}")
    return email.message_from_bytes(data[0][1])

def search(m, alias=None, unseen=False, since_uid=None):
    crit = []
    if alias:
        crit += ["TO", f'"{alias}"']
    if unseen:
        crit.append("UNSEEN")
    if since_uid:
        crit.append(f"UID {int(since_uid) + 1}:*")
    typ, data = m.uid("search", None, *(crit or ["ALL"]))
    uids = [u.decode() for u in (data[0].split() if typ == "OK" and data and data[0] else [])]
    if since_uid:
        uids = [u for u in uids if int(u) > int(since_uid)]
    return uids

def summarize(m, uid):
    typ, data = m.uid("fetch", uid, "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])")
    if typ != "OK" or not data or data[0] is None:
        return None
    msg = email.message_from_bytes(data[0][1])
    flags = data[0][0].decode(errors="replace") if isinstance(data[0][0], bytes) else ""
    return {"uid": uid, "from": hdr(msg, "From"), "to": hdr(msg, "To"), "subject": hdr(msg, "Subject"),
            "date": hdr(msg, "Date"), "seen": "\\Seen" in flags}

def print_message(msg, uid, as_json=False):
    text = body_text(msg)
    codes, seen = [], set()
    for c in re.findall(r"(?<!\d)(\d{4,8})(?!\d)", text):
        if c not in seen:
            seen.add(c); codes.append(c)
    links = list(dict.fromkeys(re.findall(r"https?://[^\s<>\"')\]]+", text)))
    rec = {"uid": uid, "from": hdr(msg, "From"), "to": hdr(msg, "To"), "subject": hdr(msg, "Subject"),
           "date": hdr(msg, "Date"), "body": text, "codes": codes, "links": links}
    if as_json:
        print(json.dumps(rec, indent=2)); return
    for k in ("from", "to", "subject", "date"):
        print(f"**{k.capitalize()}:** {rec[k]}")
    print("\n" + (text[:6000] if text else "(empty body)"))
    print("\n**Codes:** " + (", ".join(codes) if codes else "none"))
    print("**Links:**"); [print(f"- {l}") for l in links[:30]] or print("- none")

def cmd_inbox(a):
    m, _ = connect()
    uids = search(m, a.alias and alias_of(config()[0], a.alias), a.unseen)
    rows = [r for r in (summarize(m, u) for u in reversed(uids[-a.limit:])) if r]
    m.logout()
    if a.json:
        print(json.dumps(rows, indent=2)); return
    if not rows:
        print("Inbox: no messages" + (f" for alias {a.alias}" if a.alias else "")); return
    print("| uid | from | subject | date | seen |\n|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['uid']} | {r['from'][:40]} | {r['subject'][:60]} | {r['date'][:25]} | {'y' if r['seen'] else 'n'} |")

def cmd_wait(a):
    m, addr = connect()
    alias = alias_of(addr, a.alias) if a.alias else None
    baseline = search(m, alias)
    last = max((int(u) for u in baseline), default=0)
    deadline = time.time() + a.timeout
    while time.time() < deadline:
        for uid in search(m, alias, since_uid=last):
            s = summarize(m, uid)
            if not s:
                continue
            if a.sender and a.sender.lower() not in s["from"].lower():
                continue
            if a.subject and a.subject.lower() not in s["subject"].lower():
                continue
            print_message(fetch(m, uid), uid, a.json); m.logout(); return
        print(".", end="", file=sys.stderr, flush=True)
        time.sleep(a.interval)
        m.noop()
    m.logout()
    die(f"no matching message within {a.timeout}s", 2)

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--json", action="store_true")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("address"); s.add_argument("--alias")
    sub.add_parser("check")
    s = sub.add_parser("inbox"); s.add_argument("--limit", type=int, default=20); s.add_argument("--alias"); s.add_argument("--unseen", action="store_true")
    s = sub.add_parser("read"); s.add_argument("uid"); s.add_argument("--mark-seen", action="store_true")
    s = sub.add_parser("wait"); s.add_argument("--alias"); s.add_argument("--from", dest="sender"); s.add_argument("--subject")
    s.add_argument("--timeout", type=int, default=180); s.add_argument("--interval", type=int, default=10)
    a = p.parse_args()
    if a.cmd == "address":
        print(alias_of(config()[0], a.alias))
    elif a.cmd == "check":
        m, addr = connect(); typ, data = m.uid("search", None, "ALL"); m.logout()
        print(f"ok: {addr}, {len(data[0].split()) if data and data[0] else 0} messages in INBOX")
    elif a.cmd == "inbox":
        cmd_inbox(a)
    elif a.cmd == "read":
        m, _ = connect(); msg = fetch(m, a.uid)
        if a.mark_seen:
            m.uid("store", a.uid, "+FLAGS", "(\\Seen)")
        m.logout(); print_message(msg, a.uid, a.json)
    elif a.cmd == "wait":
        cmd_wait(a)

if __name__ == "__main__":
    main()
