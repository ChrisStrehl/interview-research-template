---
name: render
description: Rebuilds the shareable HTML page for a company workspace from its Markdown files and opens it. Use when the user asks to see, open, present, share or screen-share the workspace, or after any change to research, product or framework files that the user wants to look at in a browser.
argument-hint: "<slug>"
user-invocable: true
allowed-tools: Bash, Read, Glob
---

# /render

```
python toolbox/render.py companies/<slug>
```

The script reads `index.md`, `point-of-view.md`, `claims-register.md`, `frameworks/*.md`,
`product/*.md` and `research/*.md`, and writes one self-contained `site/index.html` with the
screenshots embedded, so the file can be opened from anywhere and shared on a screen without a
server. Canvases are laid out as grids; everything else is rendered as sections with a left-hand
navigation.

After it runs, confirm the file exists and its size, then open it with `start companies/<slug>/site/index.html`
through PowerShell on Windows (or the platform's equivalent) and tell the user the path. If the
script fails, show the error and fix the Markdown that broke it rather than the script, unless the
script is at fault.

The page is a view, never a source. Edit the Markdown, then re-render.
