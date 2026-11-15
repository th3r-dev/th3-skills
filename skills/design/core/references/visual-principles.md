# Visual principles

From Figma's [graphic design principles](https://www.figma.com/resource-library/graphic-design-principles/),
with the check an agent can run in a design file. "Token" means the file's variable or style;
a raw value where a token exists is a finding.

| Principle | What it is | Apply | Check |
|---|---|---|---|
| Alignment | Elements share an edge, center, or baseline | Layout grid; auto layout for text and icon rows | Left edges in a column share one x. No element off-grid by 1–3 px |
| Contrast | Clear difference in color, size, shape, weight or texture draws the eye | Strengthen contrast on key details, without making it jarring | The primary action is the most contrasting control. Text meets WCAG AA (4.5:1, 3:1 for large) |
| Balance | Visual weight spread so the screen feels stable, symmetric or not | Position on grid lines; white space against clutter | No side of the screen carries all the heavy blocks |
| Hierarchy | Order by importance so people know what to see first | Most important at the top; emphasize with color and weight | Squint test: the first, second and third things seen are the intended ones |
| Color | Palette sets emotion and brand | Match the brand; check color-vision deficiencies | Meaning never rests on color alone (add icon or text). Every fill is a color variable |
| White space | Empty space that lets the design breathe | More for minimal, less for dense; consistent padding | Every gap is a spacing token. Space between groups > space within a group |
| Proportion | Relative size and weight of elements | Grid as a baseline; balance heavy with light | Sizes come from the type and spacing scales, not one-off values |
| Repetition | Reused colors, shapes, patterns, fonts | A design system | Repeated structures are instances of one component, not copies |
| Rhythm | Movement from spacing of repeated elements (regular, random, flowing, progressive) | Grid for regular rhythm | List rows, cards and sections repeat at the same interval |
| Movement | A deliberate path for the eye | Z-pattern, F-pattern or layer-cake; key info where the eye lands | The path ends on the primary action, not on decoration |
| Emphasis | The focal point stands out | Color, contrast, white space or size on one element | Exactly one focal point per view. Two primary buttons is a finding |
| Proximity | Related things close, unrelated apart | Group, then separate groups with space | A label sits closer to its own field than to the next one |
| Unity | Everything above working as one composition | Consistent colors, fonts, shapes; grid for spacing | The screen looks like its siblings in the same file |

## Figma practice

- Auto layout everywhere. Spacing and padding bound to spacing variables, radius to radius
  variables, fills to color variables, text to text styles.
- Read a page top-down: section label, role, menu, then screens. Place new work inside its section.
- A duplicated block on two screens is the next component to make.
- Compare with `get_screenshot` after composing, once, then fix and stop.

## Defaults when the product has none

Use these only when the inventory finds nothing. Tell the user they are defaults, and offer to
turn them into tokens.

| Area | Default |
|---|---|
| Spacing | 4 px base: 4, 8, 12, 16, 24, 32, 48, 64. Within a group < between groups < between sections |
| Type scale | Ratio about 1.25. Body 16 px on web, 17 pt on iOS. Nothing under 12 px |
| Line height | Body 1.4–1.6, headings 1.1–1.25 |
| Line length | 45–75 characters for reading text |
| Weights | Two or three: regular, medium or semibold, bold |
| Color | One primary, a neutral ramp, semantic success / warning / error / info, each with a light and dark value |
| Contrast | Text 4.5:1, large text and UI parts (borders, icons, focus rings) 3:1 |
| Radius | Two or three values; nested corners get a smaller radius than their container |
| Targets | 44 × 44 pt on iOS, 48 × 48 dp on Android, at least 24 × 24 px on web |
| Layout | Design the smallest width first, then widen. Columns on a 12-column grid on desktop |

## Common failures

- Two competing focal points (hero image and a bright banner).
- Equal spacing everywhere, so nothing groups.
- A label equidistant between two fields.
- Decorative contrast (gradients, glows) that pulls the eye away from the action.
- One-off colors or sizes that are near a token but not on it.
