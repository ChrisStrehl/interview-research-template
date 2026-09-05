#!/usr/bin/env node
/**
 * playstore.mjs -- Look up an app on Google Play via the google-play-scraper
 * npm package (keyless, no API key needed).
 *
 * Usage:
 *   node toolbox/playstore.mjs <package.id> [--lang en] [--country de] [--reviews 50] [--json]
 *
 * Example:
 *   node toolbox/playstore.mjs com.freecash.app2 --reviews 20
 *
 * Setup: run `npm install` inside toolbox/ once (installs google-play-scraper).
 *
 * Notes:
 *   - google-play-scraper scrapes the public Play Store web pages; it can break
 *     whenever Google changes page layout/markup, and may be rate-limited if
 *     you hit it too fast.
 */
import process from "node:process";

function printHelp() {
  console.log(`playstore.mjs -- Google Play app lookup (keyless)

Usage:
  node toolbox/playstore.mjs <package.id> [--lang en] [--country de] [--reviews 50] [--json]

Example:
  node toolbox/playstore.mjs com.freecash.app2 --reviews 20
`);
}

function parseArgs(argv) {
  const args = { lang: "en", country: "de", reviews: 50, json: false, help: false, packageId: null };
  const rest = [];
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === "--help" || a === "-h") args.help = true;
    else if (a === "--json") args.json = true;
    else if (a === "--lang") args.lang = argv[++i];
    else if (a === "--country") args.country = argv[++i];
    else if (a === "--reviews") args.reviews = parseInt(argv[++i], 10);
    else if (a === "--limit") args.reviews = parseInt(argv[++i], 10);
    else rest.push(a);
  }
  args.packageId = rest[0] || null;
  return args;
}

function trim(s, n) {
  if (!s) return "";
  const oneLine = String(s).replace(/\r/g, "").replace(/\n/g, " ").trim();
  return oneLine.length > n ? oneLine.slice(0, n - 1) + "..." : oneLine;
}

function fmtDate(ms) {
  if (!ms) return "?";
  try {
    return new Date(ms).toISOString().slice(0, 10);
  } catch {
    return "?";
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help || !args.packageId) {
    printHelp();
    process.exit(args.help ? 0 : 1);
  }

  let gplay;
  try {
    gplay = (await import("google-play-scraper")).default;
  } catch (e) {
    console.error(
      "Error: google-play-scraper is not installed. Run `npm install` inside toolbox/ first."
    );
    process.exit(1);
  }

  let app;
  try {
    app = await gplay.app({ appId: args.packageId, lang: args.lang, country: args.country });
  } catch (e) {
    console.error(`Error: could not find or reach Google Play for package '${args.packageId}': ${e.message}`);
    process.exit(1);
  }

  let reviews = [];
  if (args.reviews > 0) {
    try {
      const r = await gplay.reviews({
        appId: args.packageId,
        lang: args.lang,
        country: args.country,
        sort: gplay.sort.NEWEST,
        num: args.reviews,
      });
      reviews = (r.data || []).slice(0, args.reviews);
    } catch (e) {
      console.error(`Warning: could not fetch reviews: ${e.message}`);
    }
  }

  if (args.json) {
    console.log(JSON.stringify({ app, reviews }, null, 2));
    return;
  }

  const screenshots = app.screenshots || [];
  console.log(`# ${app.title}\n`);
  console.log(`- Developer: ${app.developer}`);
  console.log(`- Installs: ${app.installs}`);
  console.log(`- Score: ${app.score} (${app.ratings} ratings)`);
  console.log(`- Current version: ${app.version || "?"}`);
  console.log(`- Updated: ${fmtDate(app.updated)}`);
  console.log(`- Screenshots: ${screenshots.length} total`);
  console.log(`- Play Store link: ${app.url}`);
  console.log();
  console.log("## What's new\n");
  console.log(trim(app.recentChanges || "(none)", 600));
  console.log();
  console.log("## Description\n");
  console.log(trim(app.description || "", 1000));
  console.log();
  console.log(`## Reviews (${reviews.length}, sorted newest)\n`);
  if (!reviews.length) {
    console.log("_No reviews returned._");
  } else {
    for (const r of reviews) {
      const date = r.date ? String(r.date).slice(0, 10) : "?";
      console.log(`- **${r.score}/5** v${r.version || "?"} (${date}): ${trim(r.text, 400)}`);
    }
  }
}

main().catch((e) => {
  console.error(`Error: unexpected failure: ${e.message}`);
  process.exit(1);
});
