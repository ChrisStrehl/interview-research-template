# Tooling reference

What is available in this environment, what each thing unlocks, how to add the optional pieces, and
how to check what you actually have before a research run. Confidence marks: **[V]** verified live or
from official docs, **[I]** inferred or unverified — carry the mark forward if you repeat the claim.

This is a public template repo. Nothing in here should ever require a key to be committed. Section 4
explains why and where keys actually go.

---

## 1. What works out of the box

No install, no key, no signup. Use these first, always.

| Tool | Unlocks |
|---|---|
| **`WebSearch`** (built-in) | General web search with result snippets — the default discovery tool, and often enough on its own for Reddit, Kununu and Glassdoor, whose full pages `WebFetch` cannot open |
| **`WebFetch`** (built-in) | Fetches a page, renders it to markdown, answers a prompt against it. Blocked on `www.reddit.com`, `old.reddit.com`, `www.kununu.com` (refused); 403s on `glassdoor.com`. Works on essentially everything else — company sites, docs, registries, press |
| **chrome-devtools MCP** (plugin, installed) | Walks a real web product: screenshots, an accessibility-tree snapshot with stable element IDs, and — its standout feature — full network request/response capture, which is the fastest free way to infer a tech stack. Also Lighthouse audits. Launches its own non-headless Chrome with a persistent profile, so a login survives across sessions |
| **playwright MCP** (plugin, installed) | A second browser automation path; stronger auto-waiting on heavy SPAs. Its `--extension` mode attaches to tabs in your *actual*, already-logged-in browser — the clean route through SSO/2FA that chrome-devtools MCP cannot do since Chrome 136 blocks debugging the default profile |
| **exa MCP** (plugin, installed, hosted keyless mode) | Semantic/neural search at `https://mcp.exa.ai/mcp` — finds forum threads, discussions and lookalike companies that keyword search misses. Anonymous hosted use is keyless and rate-limited; set `EXA_API_KEY` for your own key and higher limits |
| **`toolbox/` scripts** | Keyless local scripts run via Bash from the repo root: `hn.py` (Hacker News via Algolia — free, verified working), `reddit.py` (Arctic Shift — the only confirmed free Reddit path), `wayback.py` (Wayback Machine CDX + availability API), `appstore.py` (iTunes lookup + Apple RSS reviews), `playstore.mjs` (Google Play listing/reviews), `youtube.py` (transcripts and comments), `stack.py` (scripted tech-stack read). Prefer these over installing a matching MCP server — they are cheaper in tokens and have no install risk |

Why stop here rather than installing more: a dedicated MCP server exists for several of the above
(Reddit, Wayback, YouTube transcripts), but each either wraps an endpoint the toolbox already calls
directly, or depends on a path that is already broken (public Reddit MCP servers still assume the now
dead `.json` endpoints). Two curl-equivalent calls in a toolbox script beat an extra MCP server's tool
schemas sitting in every prompt for the life of the session.

---

## 2. Optional upgrades

Install only when the built-ins hit a real wall — a blocked page you actually need full text from, or
an Android app you need to click through. Each needs a key from outside this repo (see §4).

### Firecrawl — crawl a whole docs site, changelog or help centre in one shot

```bash
claude mcp add -s user --transport http firecrawl https://mcp.firecrawl.dev/v2/mcp-oauth
claude mcp login firecrawl        # one-time browser OAuth in an interactive terminal, or /mcp inside Claude Code
```
Firecrawl's hosted MCP server with OAuth: no API key is stored anywhere, the credential lives in
Claude Code's own store, and user scope makes it available in every clone of this template. Free
tier: 1,000 credits/month, no card (1 credit per page fetched; `map` costs 1 credit per call) [I].
The tools appear as `mcp__firecrawl__*` (search, scrape, map, crawl, extract). Unlocks: `map` +
`crawl` across an entire site — worth it when you need the full changelog history or every docs
page, not a single fetch `WebFetch` could already do. Alternative if you prefer a key: the
`firecrawl@claude-plugins-official` plugin wraps the `firecrawl` CLI and takes
`firecrawl login --api-key fc-<key>`.

Check in a session with `claude mcp list`: "Needs authentication" means the login has not been done
on this machine yet.

### Bright Data — the unblocker for Kununu, Glassdoor, G2, Crunchbase pages

```bash
claude plugin install brightdata-plugin@claude-plugins-official   # skills only: teaches Claude the CLI, MCP and APIs
npm install -g @brightdata/cli                                     # the tool that actually fetches
bdata login                                                        # one-time browser login; saves the key locally
bdata config                                                       # confirms auth and the auto-created unlocker zone
```
The plugin (v1.8.0, verified 5 Sep 2026) ships no MCP server of its own; it ships 21 skills that
route to the CLI, the hosted MCP server or the REST API. The CLI is the simplest path: after
`bdata login` no token is ever pasted or stored in a repo. Free tier: 5,000 requests/month, no card
[I]. Then, from any agent with Bash:

```bash
bdata scrape https://www.kununu.com/de/<company>/kommentare      # page as markdown, bot walls bypassed
bdata search "<company> glassdoor reviews"                       # Google results as JSON
```

If you prefer the MCP server instead, `claude mcp add --transport http brightdata "https://mcp.brightdata.com/mcp?token=<TOKEN>"`
at user scope, never in the repo. Unlocks: bot-detection and CAPTCHA bypass and structured extractors
for 40+ sites — the only realistic route to full review text on Kununu, Glassdoor and G2, since
`WebFetch` is blocked on all three and none publishes a free API. Check availability in a session
with `bdata config`: a non-zero exit means not logged in.

### How to report hitting a wall this would remove

When a research run needs full text from a blocked source (Kununu, Glassdoor, G2, a whole docs site)
and only Bright Data or Firecrawl would get it, do not silently under-report or fabricate volume.
State it plainly in the relevant `research/` note or `evidence/` file: *"Full review text on Kununu is
blocked ([V], `WebFetch` refused); only search-snippet text was available. Bright Data (not installed)
would unblock this."* That sentence is cheap, keeps the claims register honest, and tells the next
person exactly what to install if the source turns out to matter.

---

## 3. Android emulator setup (Windows)

Android is fully workable on Windows; iOS is not (needs Xcode/`simctl`, Mac-only — use store data
instead, per `references/source-map.md` §3b).

Verified on Windows 11, 5 Sep 2026 [V]:

1. Install Android Studio and let its first-run wizard finish. On a current install the wizard
   already downloads a **Google Play** system image and creates a Pixel virtual device (here:
   `Pixel_10_Pro`, image `android-37.1 google_apis_playstore`). Check with
   `ls %LOCALAPPDATA%\Android\Sdk\system-images` and `ls %USERPROFILE%\.android\avd`. If no device
   exists, create one in Android Studio's Device Manager and pick an image whose tag says
   "Google Play"; plain AOSP images cannot install apps from the store.
2. Put the SDK on the user PATH once, in PowerShell:
   ```powershell
   $sdk="$env:LOCALAPPDATA\Android\Sdk"
   [Environment]::SetEnvironmentVariable("Path", [Environment]::GetEnvironmentVariable("Path","User") + ";$sdk\platform-tools;$sdk\emulator", "User")
   [Environment]::SetEnvironmentVariable("ANDROID_HOME", $sdk, "User")
   ```
   New terminals see it; a running Claude Code session may need a restart.
3. Register mobile-mcp at user scope:
   ```bash
   claude mcp add -s user mobile-mcp -- npx -y @mobilenext/mobile-mcp@latest
   ```
   Free, MIT, drives the device over ADB with accessibility snapshots and screenshots [V].
4. **Before a research run, start the device**: `emulator -avd Pixel_10_Pro` (or from Android
   Studio's Device Manager). Boot takes about 75 seconds on this machine; `adb devices` then lists
   `emulator-5554 device`. Never start the same AVD twice; the second launch fails and leaves an
   `offline` entry, which `adb kill-server && adb start-server` clears.
5. **Sign in to Google once on the emulator** (Play Store → Sign in). Without an account the store
   cannot install anything. Use a Google account you are comfortable using for research. Then
   install the target app from the Play Store; the walker checks with
   `adb shell pm list packages | grep <package>` and, if missing, opens the listing with
   `adb shell am start -a android.intent.action.VIEW -d market://details?id=<package>` and asks you
   to press Install.
6. Screenshots from the shell work without the MCP: `adb exec-out screencap -p > file.png` [V].

**Known limitation:** several consumer apps — banking, streaming, some fintech — detect that they are
running on an emulator and refuse to launch [V]. If that happens, stop: fall back to store listing,
version history and reviews (`references/source-map.md` §3b) rather than trying to evade detection.

**Optional complement — Maestro.** YAML-defined flows, no instrumentation, good for a repeatable
scripted walkthrough with frame capture. On Windows it officially wants WSL2 [V]. Not a replacement
for mobile-mcp — use it when you want the same walkthrough re-runnable rather than driven live.

---

## 4. Where keys go, and why

This repo is a **public template**. Anyone can clone it. A key committed to `.claude/settings.json` in
the repo is a key leaked to everyone who ever clones it — including future you, on a machine you don't
trust, or a stranger who forks the template.

Keys belong in one of two places, never in a repo-tracked file:

- `~/.claude/settings.json` (your user-level Claude Code settings, outside any repo), under an `env`
  block, or
- a Windows user environment variable (`$env:FIRECRAWL_API_KEY`, `$env:API_TOKEN`, etc.), set once and
  inherited by every shell.

The repo's own `.gitignore` already excludes `.claude/settings.local.json`, `*.env` and `.env*` as a
second line of defence — but the working assumption should be that nothing keyed ever gets *written*
into a tracked file in the first place, not that the ignore file will catch it.

---

## 5. Capability check

Run this at the start of a research session to find out what is actually available before planning
which routes to use. None of these commands need a key to run — they report presence/absence, not
data.

```bash
claude plugin list            # confirms chrome-devtools-mcp, playwright, exa, and any optional plugins installed
claude mcp list                # confirms configured MCP servers and whether they're connected
python toolbox/hn.py --help    # confirms the toolbox scripts are runnable from this checkout
adb devices                    # confirms an Android emulator or device is available (empty output = none)
```

Record the result in that company's `state.json` under a `capabilities` key, so later steps in the
same research run — or a re-run days later — know what was available without re-probing. Shape it
like the rest of `state.json`: what has run, when, and (implicitly) what to re-check if it's gone
stale. A reasonable shape:

```json
{
  "capabilities": {
    "checked_at": "2026-09-05T10:00:00Z",
    "chrome_devtools_mcp": true,
    "playwright_mcp": true,
    "exa_mcp": true,
    "firecrawl": false,
    "brightdata": false,
    "toolbox": true,
    "android_emulator": false
  }
}
```

If a capability is `false` and the research plan would have used it, that is exactly the wall
described in §2 — name it in the relevant note rather than quietly skipping the source.
