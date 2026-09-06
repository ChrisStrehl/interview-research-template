---
paths:
  - "companies/**"
---

# Language rules for everything under companies/

Two kinds of file live here, and they are written differently.

**Deliverables** are what the user reads and shares on a screen: `point-of-view.md`, `index.md`,
`frameworks/*.md`, `product/*.md`, `claims-register.md`. **Evidence** is what they cite:
`research/*.md`, `evidence/**`, `inputs/**`. A deliverable is a set of conclusions with sources
underneath. An evidence file is the material those conclusions rest on.

## Deliverables

- **Conclusions, not reports.** A bullet states what is true and, if it matters, what follows from
  it. It does not say who said it in the sentence; that goes in the sources line. Bad: "According to
  the founder podcast, the company focuses on top games." Good: "Almedia works with the top 10 to 30
  grossing games per market because they monetise better. [1]"
- **One idea per bullet, one sentence where possible, as many bullets as the evidence earns.** If
  a box has two things worth saying, it has two bullets. Never add a bullet to fill space, never
  write "not applicable" or "no advantage observed" as content; leave the box short.
- **A fact appears once**, in the place where it decides something. If the JustPlay acquisition
  matters for the market, it lives in the market canvas, not also in revenue, threats and the point
  of view.
- **Sources go under the box, not in the sentence.** Each bullet ends with its grade and a number,
  `[V][1]`. Each box or section ends with a `Sources:` line listing the numbers: source, date, link
  or file path. The reader can then check any claim in one click without reading around it.
- **Never reference another workspace file inside a sentence.** "See product-map.md" is not a
  conclusion. Put the path in the sources line.
- **Never narrate the research.** "We could not reach", "the walk stopped at", "not observed this
  pass" describe the process, not the company. Gaps go to `index.md` under Open items and to
  `state.json`. If a box has no evidence, it stays empty until it has some.
- **Every problem carries time.** First seen, last seen, and whether it is still true as of the
  newest dated evidence. A problem the company fixed six months ago is history, and the reader has to
  see the difference before they raise it in a room.
- **Plain words.** No "leverage", "landscape", "robust", "delve", "it is worth noting", "notably",
  "crucially", "in today's". No em dashes. No rhetorical questions. No bold inside bullets. Headings
  are the template's; do not add your own.
- **Short beats complete.** If the same thing can be said in fewer words, say it in fewer words.

## Evidence files

- Full sentences, verbatim quotes with links and dates, the grade after every claim, and enough
  context that a deliverable can cite one line from here without the reader needing the rest.
- These files are reference, not reading. Nobody has to read them front to back.

## Both

- English throughout; keep German terms where they are the term and gloss them once.
- Numbers carry a denominator, a storefront or population, and a date.
- Opinion is marked [O] and lives only in `product/onboarding-teardown.md` and `point-of-view.md`.
- No production notes: no "TODO", no "(check this)", no arrows.
