# How to work

The order every design task follows, from a single button to a full flow. Each stage ends with
a check. When a check fails, fix that stage before moving on; a problem carried forward is
harder to find later.

## 1. Understand

- **Who and where.** Who uses this screen, on which device, in what situation (at a desk, on
  the move, under time pressure). This sets density, tone and target size.
- **The kind.** Tool, product app, tech page or business page ([taste.md](taste.md#1-classify-the-work-first)).
  It decides what may lead the screen and whether effects belong at all.
- **The job.** One sentence: "On this screen, a <role> can <do what> so that <outcome>."
  If you can't write it, ask before designing.
- **Behavior from the source.** Take actions, validation, messages and role gates from the
  app's code, the spec, or the user. Never invent business rules.

Check: the one-sentence job is written down, and every open question is asked or answered.

## 2. Inventory

Read before you draw:

- Components, variables (color, spacing, radius), text styles, effect styles.
- The term list and capitalization in the existing screens.
- Sibling screens in the same section: the new screen must look like them.
- Platform: Apple HIG, Material, or web, and the frame sizes the product already uses.
- References for whatever the product leaves open: 9–12 for a new page, 3–5 for a part, with a
  shot list of what to take from each ([reference-first.md](reference-first.md)).

Missing pieces are a list to show the user, not values to invent. Ask before adding tokens or
components. When the product has nothing at all, use the [defaults](visual-principles.md#defaults-when-the-product-has-none)
and say so.

Check: you can name the component, token and text style for every element you plan to place.

## 3. Intent before pixels

Write the plan as text and show it:

- Content order, most important first.
- The one focal point and the primary action.
- The states: default, empty, loading, error, long content (see [interface-quality.md](interface-quality.md)).
- Any flow as `[step] → <decision?> --True--> [step]`.
- The visible text, in the product's words (see [writing.md](writing.md)), written before the layout.
- Every style choice the product leaves open, with its options and one sentence on the pick
  ([taste.md](taste.md#3-decide-open-choices-on-purpose)).

For a new page or a redesign, turn the plan into **three competing static variants** on one
page (desktop and phone) before any app code, and let the user pick
([cook-loop.md](cook-loop.md#2-target-before-code-three-variants)).

Check: the user agrees with the plan, or the request already fixed it. Skip the wait for a
one-element change.

## 4. Build

- Smallest version first: the default state of one screen. Then add the other states.
- Layout before motion: no animation until the static layout holds at every width; then add
  motion from reference recordings ([cook-loop.md](cook-loop.md#4-layout-first-motion-second)).
- Instances of components, never detached copies. Values bound to tokens.
- Auto layout, so the screen survives long text and resizing.
- Clear layer names: `Role ▸ Menu ▸ Screen` for screens, the component's name for parts.
  No `Frame 123`, no `Group 7`.
- Write only where the user pointed you. Experiments go on a duplicated page.

Check: no raw values, no detached instances, no default layer names.

## 5. Review

1. Take one screenshot of the result.
2. Score it with the review table in [SKILL.md](../SKILL.md#how-to-use-it). With references,
   score side by side (reference left, build right) by a fresh-context critic, not by the author;
   apply any calibration offset the user gave ([cook-loop.md](cook-loop.md#6-critics)).
3. Fix the highest-impact findings. A few decisive fixes beat many small nudges.
4. Take one more screenshot and score again. Stop at a pass or after three rounds, and report
   what still fails rather than looping.

Report scores and the remaining findings, never just "done".

## 6. Hand off

For each screen, the developer gets:

- **States**, each one designed, not described.
- **Behavior**: branches, alert texts and their exits, role gates, where each action leads.
- **Tokens and components used**, so nothing has to be measured from pixels.
- **Edge cases**: long text, empty data, slow network, no permission.
- **Gaps**: anything still a placeholder, missing a token, or decided "for now".

## Habits

- Change one thing at a time when fixing, so you know which change helped.
- Keep the user's content, brand and intent. Restyling that wasn't asked for is a finding
  against you, not an improvement.
- Old versions are kept beside the new one, never deleted.
- Real data shapes, not lorem ipsum: realistic names, lengths and numbers. Mock data in
  anything public.
- A rule that blocks the user's request gets raised once, with the reason. If they still want
  it, build what they asked.
