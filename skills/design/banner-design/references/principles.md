# Banner principles

The rules every banner follows, merged from four sources and checked against each other.
Where they disagree, the stricter rule wins. Sources at the end.

## Before any pixel

1. **Audience and goal.** One sentence each. "Developers browsing GitHub; get them to install."
   The goal picks the CTA: awareness has none or a URL, launch has "Install", event has "Register".
2. **One idea per banner.** Details go to the next step (README, landing page). If the copy
   needs "and" twice, it is two banners.
3. **Copy before layout.** Write the headline, the proof line and the CTA first, then place them
   (same rule as `../../core/references/taste.md`).

## Copy

| Part | Rule |
|---|---|
| Headline | 6-12 words, benefit first, specific: what, for whom. No "Welcome to", "Introducing". |
| Proof line | One, only if it adds confidence: a number, a time, a differentiator. |
| CTA | One per banner. Starts with a verb (Get, Install, Start, Register). 1-3 words, plus the command or URL if there is no button. The landing page uses the same words. |
| Ads | At most 7 words a line, 3 lines. Text under 20% of the area (Meta penalizes more). |

Proofread every string. A typo on a banner is read by everyone who sees it.

## Hierarchy

Lock the hierarchy in grayscale before adding color or effects. A hierarchy that fails in
grayscale still fails once color is added.

| Element | Weight |
|---|---|
| Headline / brand name | darkest and largest |
| Proof / supporting message | medium |
| CTA | high-contrast shape or strong type |
| Logo | smallest, always in the same place |

The 3-zone reading order: top = logo or value, middle = supporting message and visual,
bottom = CTA. For a horizontal banner the same order runs left to right (see the brand-side
layout in `../SKILL.md`). Put the CTA where the eye ends; in left-to-right reading that is the
bottom-right.

## Safe zones and crops

- Where the platform lays UI over the image (Meta, Instagram, YouTube, stories), critical content
  (headline, CTA, logo) stays in the central 70-80%. Everywhere else (GitHub, web heroes, email)
  it stays 50-100px clear of every edge and outside the platform's crop.
- Three zones: `core` (must always show), `support` (can be trimmed), decorative (can be
  cropped). The first two are the `data-zone` values the bench reads. Know which is which before placing.
- The focal subject is one shape or one picture. A composition where a small detail carries the
  meaning breaks on the first crop.
- Platform overlays: YouTube shows only 1546 × 423 of 2560 × 1440 on every device; Meta and
  Instagram cover the outer 10% with UI. Exact sizes: [sizes-and-styles.md](sizes-and-styles.md).

## Type and color

- At most 2 typefaces. Clean, bold faces for headlines.
- Digital minimums: body 16px, headline 32px. Print: 70pt+ headlines for 3-5 m, and about
  1pt of type per foot of viewing distance.
- Text contrast at least 4.5:1 (3:1 for 24px+ bold). The background never fights the headline,
  least of all at phone size.
- Pick the palette for the feeling (calm blue, urgent red), then check it against the brand.
  Use only the brand's own colors, logo and fonts when they exist; never invent brand assets.

## Imagery

- Use imagery that is sharp and carries the message, or use none. A CSS or SVG shape works better
  than a stock photo that says nothing.
- Generated images carry no text; text is set in the layout so it stays sharp and editable.

## Variants

Deliver a set: the primary, a tight crop for constrained placements, and a text-light version for
small or busy spaces. Keep a master file: prices, dates and offers change.

## QA before publishing

| Test | How | Pass |
|---|---|---|
| Two-second | Shrink to phone-feed width (≈ 400px) and look for two seconds | Brand, the one idea and the CTA read |
| Crop stress | Mask to the safe zone above and to the platform's crop | Nothing in the core zone is cut |
| Compression | Export at the platform's quality (PNG for text-heavy work) and upload once | Text stays crisp |
| Contrast | Measure every text color against what is behind it | ≥ 4.5:1 (≥ 3:1 large bold) |
| Grayscale | Desaturate | Hierarchy unchanged |
| Spelling | Read every string aloud | No errors |

## Print only

300 DPI (150 for large format), CMYK, 3-5 mm bleed on every side. Check the proof on the real
material before the run.

## Sources

- AlphaGraphics, ["From Concept to Catchy: A Guide to Designing Effective Banners and Posters"](https://www.alphagraphics.com/us/arizona/phoenix-camelback/blog/from-concept-to-catchy-a-guide-to-designing-effective-banners-and-posters/):
  audience and goal first, one emotional idea, imagery that stops people, palette by feeling,
  bold headline type, one short CTA, proofread, check print quality.
- Adobe Express, ["Banner design tips"](https://www.adobe.com/express/learn/blog/banner-design-tips): breathing room, core / support / decorative zones,
  grayscale hierarchy, 6-12 word headline, one proof line, CTA where the eye ends, variant set,
  two-second / crop / compression tests, master file and naming.
- nextlevelbuilder/ui-ux-pro-max-skill, [`banner-design/SKILL.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/banner-design/SKILL.md) and
  [`references/banner-sizes-and-styles.md`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/main/.claude/skills/banner-design/references/banner-sizes-and-styles.md): HTML/CSS build at exact size, 2-3 art directions,
  70-80% safe zone, one CTA bottom-right ≥ 44px, ≤ 2 fonts, 16 / 32px minimums, 4.5:1,
  < 20% ad text, print specs, size tables and the 22 styles.
