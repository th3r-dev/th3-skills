# Taste: how to avoid the generic look

Adapted from [Leonxlnx/taste-skill](https://github.com/Leonxlnx/taste-skill) (MIT). That skill
builds whole marketing sites with its own kit, dealers and a browser gate. This file keeps the
method, not the kit, and runs under design-core's order of authority: the product's own system
still wins over every rule here.

## 1. Classify the work first

Write the kind on the plan's first line. It decides what belongs on the screen.

| Kind | Examples | What leads | Never |
|---|---|---|---|
| Tool | Admin portal, back office, internal dashboard, import screen | The data and the task; dense, quiet, one action per view | Hero images, effects, marketing copy |
| Product app | SaaS app, mobile app screens | The product's real UI and real data shapes | Generic dashboard mock-ups, decorative gradients |
| Tech page | Landing page for software, AI, hardware, a game | The real product at true size (its UI, its device, its world) | A mood picture in place of the product |
| Business page | Service, shop, cafe, clinic, physical product | Photographs of the real thing, place or people; flat colour and type | Shader effects, glows, scroll scenes |

Effects and motion-heavy moments belong only where the subject is technical. Everyone else gets
photographs, type and the product's own colours.

## 2. Copy before layout

1. Write a fact sheet: what it is, who uses it, the one main action, the real material on hand
   (logo, screens, photographs, prices, hours).
2. Write all visible text first, under [writing.md](writing.md). The first heading names the
   thing and who it's for; one hard fact on the first screen; buttons are verb + object.
3. Then plan the layout as screens or sections, one line each: its one idea, its picture, its
   height. If a section has no idea of its own, cut it.

Nothing is invented: no reviews, quotes, customer logos or figures. An assumed value (opening
hours, a price on a mock) is marked as assumed and listed in the hand-off.

## 3. Decide open choices on purpose

When the product leaves a choice open (palette, type pairing, hero layout, card style):

- Name two or three options that fit the kind and the subject, pick one, and write one sentence
  on why it fits. Don't take the first idea that comes to mind; that is where the generic look
  comes from.
- Record the pick in the plan so sibling screens or pages stay consistent, or differ on purpose.
- Violet/lavender accents, glow gradients and a three-card feature row need a product reason.

## 4. Composition rules worth keeping

- One idea per section; on a page, a section is one or two screens tall and the next section's
  heading doesn't peek into the current one.
- Equal left and right content edges; every block on the grid's columns, nothing drifting to one side.
- The real thing shows: the product's own UI with its real data shapes, a different picture in
  each section, the same object leading at most three sections.
- No caption explaining a picture. Credits go in one footer line.
- One system: one button pair, one card style, one radius scale, one link style, two boxes deep at most.
- Motion answers the user (hover, press, focus, a single entrance) and rests under reduced motion.
  No fade-in on every section, no parallax text, no scroll-jacking, no tilt.

## 5. Copy tells to remove

On top of [writing.md](writing.md) and the AI tells in [interface-quality.md](interface-quality.md):

- Stock phrases ("Elevate your…", "Unlock the power of…", "Built for the future").
- Virtue words with nothing behind them ("seamless", "effortless", "world-class").
- A device used as a tic: "Not X, but Y" frames, two-fragment headings ("Fast. Simple."),
  runs of negations, a number pair in every heading. Once is a choice; three times is a tic.
- Leftovers: lorem ipsum, "Sample text", `TODO`, template names.

## 6. Check like a gate

- Give every check an id (`hero-fold`, `tap-size`, `copy-buttons`) so a finding is traceable and
  a re-check confirms the same thing was fixed.
- Look at the real render at 1440, 1024, 768 and 390 wide, and walk 320 for anything past the
  screen. Targets 44 px; nothing overlapping or hidden under a fixed bar.
- Fix, re-check, at most three rounds, then report what is still open (the round limit in
  [workflow.md](workflow.md#5-review)).
- A finding you judge false is waived in writing with its reason, never hidden by gaming the
  check. Waivers go in the report.
- The report starts with the status: pass, or the open findings, then every waiver and every
  assumed fact.
