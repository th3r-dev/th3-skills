# Interface quality baseline

Distilled from [nexu-io/open-design](https://github.com/nexu-io/open-design/tree/main/skills)
(Apache-2.0): `web-design-guidelines` (a pinned copy of Vercel's Web Interface Guidelines),
`impeccable-design-polish` and `plan-design-review`. The design-side rules come first; the
code-side ones apply when the design is built or reviewed as code.

## States: design every one

| State | What the screen shows |
|---|---|
| Default | Real-looking data at typical length |
| Empty | Next step and its button (see writing.md) |
| Loading | Skeleton or spinner; text ends with "…" ("Loading…", "Saving…") |
| Error | Inline next to the cause, with the fix |
| Long content | Very short, average and very long values: truncation, line clamp or wrap is decided |
| Hover / active / focus | Each more prominent than rest. Focus is always visible |
| Disabled | Only when the reason is visible; a submit button stays enabled until the request starts |
| Destructive | A confirmation or an undo window, never immediate |

## Accessibility

- Text contrast WCAG AA; color is never the only signal.
- Icon-only buttons have a name; decorative icons don't.
- Every form control has a visible label. A placeholder is a hint, not a label.
- Touch targets at least 44 × 44 pt; a checkbox and its label share one hit target.
- Headings form one hierarchy; a skip link exists on web.
- Zoom is never disabled.

## Motion

- Only for feedback or orientation, never decoration.
- Respect reduced motion with a reduced or no-motion variant.
- Animate transform and opacity; motion can be interrupted by input.

## Copy and typography details

- "…" not "...", curly quotes, non-breaking space in "10 MB" and "⌘ K".
- Tabular numerals in number columns.
- Active voice, specific labels ("Save API key", not "Continue"), numerals for counts.
- Dates and numbers formatted per locale, never hard-coded.

## Code-side (when the design is built)

- `<button>` for actions, `<a>` for navigation; no clickable `<div>`.
- Visible `:focus-visible` replacement wherever an outline is removed.
- Inputs: correct `type`, `autocomplete`, `name`; paste never blocked; errors focus the first field.
- Images have width and height; long lists are virtualized.
- URL holds filters, tabs and pagination so the state can be linked.
- Dark theme sets `color-scheme`; full-bleed layouts respect safe areas.

## AI tells: flag and remove

- Purple-blue glow gradients with no product reason.
- A generic row of three feature cards.
- Large rounded cards wrapped around everything.
- Empty marketing adjectives ("seamless", "powerful", "next-level").
- Spacing and type sizes that drift off the scale.
- Effects that don't help anyone understand the screen.

## Review pass

1. Look at the real screen or file first. Don't judge from the prompt.
2. Keep the content, brand and intent; change only what the user asked or what a finding names.
3. A few decisive fixes beat broad cosmetic churn.
4. End with the design in a better working state, not only a list of complaints.
