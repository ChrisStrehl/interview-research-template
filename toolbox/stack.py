#!/usr/bin/env python3
"""stack.py -- Sniff a website's tech stack without any API key.

Usage:
  python toolbox/stack.py <url> [--json]

Example:
  python toolbox/stack.py https://freecash.com

What it does:
  1. Fetches the page (browser-like User-Agent, follows redirects) and prints
     response headers of interest (server, x-powered-by, via, cf-ray, cookie names).
  2. Scans the HTML and all referenced <script src>/<link href> URLs for known
     vendor signatures, grouped by category (analytics, tag manager, payments,
     feature flags, error tracking, CDN, auth, framework, A/B testing,
     chat/support, marketing automation).

Notes:
  - This is a static, best-effort sniff (no JS execution), so client-side-only
    integrations that inject tags dynamically without leaving a static trace
    may be missed.
"""
import argparse, io, json, re, sys, gzip, zlib, urllib.request, urllib.error

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

HEADERS_OF_INTEREST = ["server", "x-powered-by", "via", "cf-ray", "x-vercel-id", "x-cache", "x-served-by"]

# category -> vendor -> list of regex patterns (matched against html + resource URLs)
VENDORS = {
    "analytics": {
        "Google Analytics / gtag": [r"gtag\(", r"google-analytics\.com", r"googletagmanager\.com/gtag"],
        "Segment": [r"segment\.(com|io)", r"cdn\.segment\.com"],
        "Mixpanel": [r"mixpanel\.com", r"mixpanel\.js"],
        "Amplitude": [r"amplitude\.com", r"cdn\.amplitude\.com"],
        "Hotjar": [r"hotjar\.com", r"static\.hotjar\.com"],
        "FullStory": [r"fullstory\.com", r"fs\.js"],
    },
    "tag manager": {"Google Tag Manager": [r"googletagmanager\.com/gtm\.js", r"googletagmanager\.com/ns\.html"]},
    "payments": {
        "Stripe": [r"js\.stripe\.com", r"stripe\.com/v3"],
        "Braintree": [r"braintreegateway\.com", r"braintree"],
        "PayPal": [r"paypal\.com", r"paypalobjects\.com"],
        "Adyen": [r"adyen\.com", r"checkoutshopper"],
    },
    "feature flags": {
        "LaunchDarkly": [r"launchdarkly\.com", r"ldclient"],
        "Optimizely": [r"optimizely\.com", r"cdn\.optimizely\.com"],
    },
    "error tracking": {
        "Sentry": [r"sentry\.io", r"sentry-cdn\.com", r"\bsentry\b"],
        "Datadog": [r"datadoghq\.com", r"datadog-logs"],
    },
    "auth": {
        "Auth0": [r"auth0\.com"],
        "Firebase": [r"firebaseapp\.com", r"firebase(io)?\.com", r"gstatic\.com/firebasejs"],
    },
    "chat/support": {
        "Intercom": [r"intercom\.io", r"widget\.intercom\.io"],
        "Zendesk": [r"zendesk\.com", r"zdassets\.com"],
    },
    "marketing automation": {
        "HubSpot": [r"hubspot\.com", r"hs-scripts\.com", r"hsforms"],
        "Braze": [r"braze\.com", r"appboycdn\.com"],
        "OneSignal": [r"onesignal\.com", r"cdn\.onesignal\.com"],
        "Iterable": [r"iterable\.com"],
        "Customer.io": [r"customer\.io"],
        "Appsflyer": [r"appsflyer\.com"],
        "Adjust": [r"adjust\.com"],
        "Branch": [r"branch\.io"],
    },
    "cdn": {
        "Cloudflare": [r"cloudflare\.com", r"cf-ray", r"__cf_bm"],
        "Fastly": [r"fastly\.net", r"x-served-by:.*fastly"],
        "Vercel": [r"vercel\.app", r"x-vercel-id", r"\.vercel-insights\.com"],
    },
    "framework": {
        "Next.js": [r"_next/static", r"__NEXT_DATA__", r"x-powered-by:\s*next\.js"],
        "Nuxt": [r"_nuxt/", r"__NUXT__"],
        "React": [r"data-reactroot", r"react-dom", r"__react"],
        "Vue": [r"__vue__", r"data-v-[0-9a-f]{8}", r"vue\.js"],
        "Angular": [r"ng-version", r"angular\.js"],
        "Webflow": [r"webflow\.com", r"webflow\.js", r"data-wf-site"],
        "Shopify": [r"cdn\.shopify\.com", r"shopify\.com", r"Shopify\.theme"],
        "WordPress": [r"wp-content", r"wp-includes", r"/wp-json/"],
    },
    "A/B testing": {"Optimizely (A/B)": [r"optimizely\.com"]},
}


def fetch(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
        encoding = (resp.headers.get("Content-Encoding") or "").lower()
        if encoding == "gzip":
            raw = gzip.decompress(raw)
        elif encoding == "deflate":
            raw = zlib.decompress(raw)
        set_cookies = resp.headers.get_all("Set-Cookie") or []
        return raw, dict(resp.headers), resp.geturl(), set_cookies


def extract_resource_urls(html):
    urls = []
    for m in re.finditer(r'<script[^>]+src=["\']([^"\']+)["\']', html, re.I):
        urls.append(m.group(1))
    for m in re.finditer(r'<link[^>]+href=["\']([^"\']+)["\']', html, re.I):
        urls.append(m.group(1))
    return urls


def main():
    ap = argparse.ArgumentParser(description="Sniff a website's tech stack (keyless, static analysis)")
    ap.add_argument("url", help="URL to analyze")
    ap.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    args = ap.parse_args()

    url = args.url
    if not re.match(r"^https?://", url):
        url = "https://" + url

    try:
        raw, headers, final_url, set_cookies = fetch(url)
    except urllib.error.HTTPError as e:
        print(f"Error: {url} returned HTTP {e.code}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: could not reach {url}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: unexpected failure fetching {url}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        html = raw.decode("utf-8", errors="replace")
    except Exception:
        html = raw.decode("latin-1", errors="replace")

    resource_urls = extract_resource_urls(html)
    haystack = html + "\n" + "\n".join(resource_urls)
    haystack_lower = haystack.lower()

    # headers of interest (case-insensitive lookup)
    lower_headers = {k.lower(): v for k, v in headers.items()}
    interesting = {h: lower_headers[h] for h in HEADERS_OF_INTEREST if h in lower_headers}
    cookie_names = []
    for v in set_cookies:
        name = v.split("=", 1)[0].strip()
        if name and name not in cookie_names:
            cookie_names.append(name)

    findings = []
    for category, vendors in VENDORS.items():
        for vendor, patterns in vendors.items():
            for pat in patterns:
                m = re.search(pat, haystack_lower, re.I)
                if m:
                    snippet = haystack[max(0, m.start() - 20): m.start() + 60].replace("\n", " ").strip()
                    findings.append((category, vendor, snippet))
                    break  # one match per vendor is enough

    if args.json:
        print(json.dumps({
            "url": url,
            "final_url": final_url,
            "headers_of_interest": interesting,
            "cookie_names": cookie_names,
            "findings": [{"category": c, "vendor": v, "evidence": e} for c, v, e in findings],
        }, indent=2))
        return

    print(f"# Tech stack sniff: {url}\n")
    if final_url != url:
        print(f"_Redirected to: {final_url}_\n")

    print("## Response headers of interest\n")
    if interesting:
        for k, v in interesting.items():
            print(f"- **{k}**: {v}")
    else:
        print("_None of the tracked headers were present._")
    print(f"- **cookie names set**: {', '.join(cookie_names) if cookie_names else '(none observed)'}")
    print()

    print("## Detected vendors\n")
    if not findings:
        print("_No known vendor signatures detected in the static HTML/resource URLs._")
    else:
        print("| Category | Vendor | Evidence |")
        print("|---|---|---|")
        for category, vendor, snippet in findings:
            snippet = snippet.replace("|", "\\|")
            print(f"| {category} | {vendor} | `{snippet}` |")


if __name__ == "__main__":
    main()
