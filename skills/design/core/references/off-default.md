# Off-default: move away from the first, average pick

Adapted from [mankidev/antialgorithm@8706a2d](https://github.com/mankidev/antialgorithm/tree/8706a2d49511954d0d092f732eb5853497ad25fc)
(MIT, © 2026 mankidev). [`../scripts/seed.py`](../scripts/seed.py) is its seed script, unchanged.
Its `rough.py` (hand-made marks on an SVG) and `check.py` (render an SVG at full and icon size,
list clipped, covered, low-contrast or tiny text; needs numpy, Pillow and `rsvg-convert`) are not
bundled: fetch them from the pinned repo when a poster needs them.

Runs under design-core's order of authority. A choice the user, the product's system or the
platform already made is not open, and a request for "the standard version" gets the standard
version. [taste.md](taste.md) §3 says to decide open choices on purpose; this file is how.

## Name the default, then leave it

The first answer that comes to mind is the average of everything already made: familiar, so it
feels right, and the user has seen it a thousand times.

1. Before an open creative choice (a name, a headline, a palette, a layout, a poster, a game idea),
   write one line: **"the default here is X."**
2. Don't use X unless this case truly asks for it.
3. Move away using what only this case has: its project, place, audience, constraints, odd
   details. A good choice could only belong here.
4. Every choice gets a one-sentence reason built on a fact about this project. Strange with no
   reason is as empty as safe.
5. The well-known opposite is the second default: "dark instead of bright", "minimal instead of busy".

## Where the start point comes from

The answer has to differ between users, and "what would be most interesting" lands everyone in
the same place. So start from outside your own taste:

| The request | Start |
|---|---|
| Carries a project, place, person, purpose or constraint | that context |
| Thin, and the work is short (a name, a few lines) | make it from a seed or a stated guess, then ask one question about the case at the end |
| Thin, and the work is long or costly (a full design, a game system) | ask one question first: who it is for, where it lives, what it is about |
| Thin, and the user wants it now | `python3 scripts/seed.py visual`, `text` or `idea`; re-roll one axis once with `--only <axis>` if it fights the subject; tie the seed to the subject with a reason |

A visual seed's verb and scale build the idea behind the piece (who does what). The region shapes
names, habits and the setting; the words stay in the user's language.

## Visual work made to be looked at

For posters, covers, promo images and hero art. **Interfaces keep their grid**: buttons, menus,
panels, HUDs and forms stay aligned and exact; this file picks only their palette, shape language
and words. Pixel art and models owned by another skill take only subject, palette and framing.

- **The AI look is the finish, not the topic**: smooth gradients, soft glow, perfect geometry,
  tiles repeated with no change, clean edges everywhere, even spacing, one default font, the same
  polish on every part. A new subject with this finish still reads as AI.
- **Pick a making method** (from the seed or the subject) and let its marks replace the finish:
  - print and paint: few inks, misregistration, uneven ink, broken edges, paper grain;
  - screens and machines: the pixel or dot grid, scan lines, bloom, banding, the machine's font;
  - camera and science: grain, light fall-off, blur where focus puts it, the instrument's false colours;
  - material and light: seams, joints, thickness, light that bends and reflects like that material.
- Marks stay real and sparse, never a noise filter on a clean image. Clean methods (a glossy
  render, a CAD drawing, a chart) stay clean.
- A hand-drawn wobble on a method not made by hand (an LED board, an x-ray, a render) is a second
  default.
- **Hand-made in code goes into the geometry**: no exactly straight line, repeated marks vary in
  spacing, length and angle, shapes sit slightly off the grid and each other, letters drawn or
  broken rather than a system font in a perfect row, layout placed by eye. Generate the marks with
  a short script, not typed coordinates; keep an SVG under ~200 KB.
- One strong decision leads; the rest serve it. Centred and balanced is a choice, not a start.
- Type is part of the image: cropped, pressed, crowded or turned when that serves the piece.
- Anything with no job (a decorative shape, glow, frame, icon) is the default showing.
- **The working parts stay whole**: what must be read, pressed, recognised or found is never cut
  by an edge, covered or broken by texture. Roughness belongs to the rest.
- Look at it at full size and at icon size. Flat vector at icon size means the method is missing.

## Words

[writing.md](writing.md) and the copy tells in [taste.md](taste.md) §5 already apply. On top:

- A sentence that could be pasted into another project unchanged gets rewritten.
- A concrete detail (a thing someone could see, touch or do there) over a general claim. A count,
  time or date only when the reader needs it to act.
- No reflex shapes: the closing offer to tailor the text, the cheer, the hype question, mirrored
  slogan halves, everything in threes, the line that ties a bow at the end.
- Don't invent facts to sound concrete. Use the project's real details, ask for them, or keep a
  made-up detail clearly made up; flag it only when it could pass as real and do harm (a price, a
  weight, a product claim).
- Keep the user's length and format.

## Ideas, names, options

- Skip the first idea in the field, the most famous mechanic, the name built from the two most
  obvious words. Assume the user already thought of those.
- Options differ in kind, not as variations of one safe idea. The safe one may be there, labelled.
- Give one recommendation with its reason.

## The escape becomes a default

What worked once turns into the new safe pick. Watch for:

- an old, analog or printed look chosen because it reads as "not AI";
- the same small palette, paper, texture or wobbly line from piece to piece;
- invented names from one stock (sea and tide words, old trades, small English towns) instead of
  how the people there name things;
- a cream or off-white ground (take it from the subject: its night, wall, water, screen);
- exact times and numbers used only to look concrete;
- a frame borrowed from another domain (a form, a map, a timetable) laid over the subject;
- a small numbered corner label and a dry joke in the fine print.

If the answer shares its main move with the last off-default answer, it is a default now: change
the kind of move, or say why this case needs it.

## Check before showing

Add these to the review's "Fit to kind, no generic look" row:

| Id | Question | Fail |
|---|---|---|
| `off-default-general` | Could this answer a different project? | too general |
| `off-default-first` | Is this what most people would make first? | move it |
| `off-default-reason` | Is there a one-sentence reason from a fact about this project? | no reason |
