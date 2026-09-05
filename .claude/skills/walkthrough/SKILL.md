---
name: walkthrough
description: Method for walking through a product like a new user with the Chrome DevTools browser tools and, when an emulator is attached, the mobile tools: what to open, how to move through screens cheaply, when to screenshot, how to read network calls for the stack, and the account and safety rules. Loaded into the product-walker agent; also usable directly when the user asks to look at a specific flow, screen or app.
user-invocable: true
argument-hint: "<url or app> [flow to walk]"
---

# Walking a product

The aim is a product map and an onboarding teardown that read as if a careful new user wrote them,
with one screenshot per meaningful screen and a stack section from what the browser actually loaded.

## Moving cheaply

Accessibility snapshots are text and scale with the page; screenshots are images and cannot be
clicked. So:

1. `navigate_page` to the URL, `wait_for` the main content.
2. `take_snapshot` once per screen to get element uids.
3. Act by uid: `click`, `fill`, `fill_form`, `press_key`. Do not re-snapshot after every action; only
   after the screen changed.
4. `take_screenshot` for the frames that belong in the teardown, saved to
   `companies/<slug>/product/screens/<NN>-<flow>-<screen>.png` with the tool's file path option.
   Number in walk order. Twenty screenshots is a full walk; forty is too many.
5. When a page is a dense dashboard, screenshot first and snapshot only the region you need to act on.

If the Chrome DevTools tools are unavailable and the Playwright tools are, the same pattern applies
with `browser_navigate`, `browser_snapshot`, `browser_click`, `browser_take_screenshot`.

## The walk

**Marketing site first, five minutes.** Home, pricing, the product tour, the sign-up call to action.
What they promise, what they gate, what they say the product is for. One screenshot of pricing.

**Onboarding to first value.** Sign up only under the account rules below. Count steps, inputs and
decisions asked of you before the product shows value. Note every moment you hesitated, every default
you accepted, every field you did not understand. Time it. Screenshot each step.

**Core flows once each.** The two or three things the product exists to do. Numbered screens, what
each asks and gives. Note where money or the ask appears.

**Settings, help, empty states.** Where the product is unfinished shows here.

**Android**, if `adb devices` lists an emulator: check the app with
`adb shell pm list packages | grep <package>`. If it is missing, open the listing with
`adb shell am start -a android.intent.action.VIEW -d market://details?id=<package>`, tell the user
to press Install, and continue with web until they have. Then launch it, walk onboarding only, then
the one flow most likely to differ from web. Use the mobile screenshot tool for frames and the
accessibility list for taps; `adb exec-out screencap -p > <file>` works as a fallback for frames.
If the app refuses to run on an emulator, say so and stop.

## Reading the stack

After the main flows, call `list_network_requests` and filter to third-party hosts. Record vendors
by category with the evidence string: analytics and tag managers, product analytics, session replay,
error tracking, feature flags, experiments, payments, auth, push and messaging, attribution, CDN and
hosting, the API host and the shape of its calls. Then run `python toolbox/stack.py <url>` from the
repo root and merge. Save the raw list to `evidence/product/network.md`. Grade all of it [V] with the
evidence string; it is first-hand.

Analytics calls also tell you what the company measures. An event named on sign-up completion is a
finding for the teardown.

## Account and safety rules

- Use the browser's persistent profile. If the user said they logged in there, use that session and
  never change account settings, passwords or payment methods.
- Sign up only with a research email the user named in `state.json` or the checkpoint. Never with an
  address you guess. Never with the user's personal email.
- Never enter payment details, never complete a purchase, never redeem, withdraw, post, message or
  delete anything on the user's behalf. Stop at the paywall and screenshot it.
- Stop at captchas, phone verification and identity checks. Report the gate; do not work around it.
- Respect the product. One walk, normal pace, no scripted hammering.
- If the product is a marketplace or has a public-facing side (a profile, a listing), do not create
  anything visible to other users.

## What "good" looks like

A reader who has never opened the product can, from the map, name its surfaces and core flows,
say where value first appears and where the ask sits, and describe how it is built. From the
teardown they can name the three places a new user is most likely to drop, with your reasoning
marked [O], and the first experiment you would run.
