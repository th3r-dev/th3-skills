# Visual review: the score the bench cannot give

`bench_model.py` measures whether a model is game-ready (budget, limits, closed parts, materials,
textures). It cannot say whether the model *looks* right: that is its `manual` `look` row. This
file is how that row gets a number on a fixed scale.

## Rules

- **A fresh reviewer, not the builder.** Whoever built the model has seen every render while
  building and stops seeing its faults. Hand the review to an agent with no part in the build (or
  to a person), and brief it cold: no earlier scores, no expected result.
- **Evidence or it does not count.** Every score names the view (front, side, three-quarter, top)
  and the part it is about.
- **Against the reference board.** Pass the references (`examples/<model>/references.md` and their
  thumbnails), so a 7 means "holds up next to those", not a 7 in a vacuum.
- **Check its claims you can measure.** A reviewer can be wrong about numbers. Re-measure what can
  be measured (part count, positions, poke-through) before acting on it.
- **The same brief every round**, so two scores can be compared.

## Anchors (0–10)

| Score | Means |
|---|---|
| 3 | clearly fails |
| 5 | works, but generic or flawed |
| 7 | good: would ship in an indie game |
| 9 | a reference others would save |

## Criteria

1. Reads as the subject at a glance (silhouette, the parts that identify it)
2. Reads as the theme or role the prompt asked for
3. The stated quality the prompt named (for example "furry"), at this budget
4. Silhouette strength across all four views
5. Proportions and appeal as a character or object
6. Low-poly craft: triangles where they show, nothing hidden, floating or poking through
7. Colour and palette
8. Polygon efficiency for what it achieves, against the references' counts
9. Originality: its own design, not a copy of a reference or a known character

Then an overall score (a judgment, not the average), the three changes that would raise it most
(part, change, triangle cost), and anything that blocks shipping on the target engine.

## Brief template

> You are an independent reviewer of a low-poly 3D game asset. Judge it cold: you have not seen any
> earlier critique, and nobody expects a particular score. Be strict and specific.
> The brief: <the prompt(s) as the user typed them>, read as <one line>. Target engine: <engine>.
> Open every image: <the four renders>. Read the build scripts: <paths>. References (the bar, not
> to copy): <contact sheet, thumbnails>. Measured facts, already verified, do not re-derive:
> <triangles, parts, materials, limits>.
> Score the nine criteria 0–10 on these anchors (3 fails, 5 works but flawed, 7 would ship in an
> indie game, 9 a reference others save), with evidence naming a view and a part. Then the
> overall score, the top three changes with triangle cost, and the blockers.
> Done when you return the 9-row table, the overall score with one sentence why, the top 3
> changes, and the blockers (or "none"). Do not edit any file.

## History: wizard cat

| Round | Model | Overall | What the review found |
|---|---|---|---|
| 1 | 200 triangles, 27 parts | **5** (Fable 5.2) | the cape was lopsided and the body poked through it; fur read as stubby arms (3/10); the clasp sat inside the head; the floating crystal echoed the reference's flames. Both of its measurable claims checked out (cape x −0.62..0.31; 27 parts, not the 22 it was told) |
| 2 | 224 triangles, 27 parts: centred tapered cape, staff with crystal, fur fans and chest ruff, curled tail, ears clear of a gold-rimmed brim | **6** (Fable 5.2) | wizard read up to 7, colour, efficiency and originality 7; still short of 7 overall: the staff crosses the face in side and three-quarter, the brim (r 0.36) is narrower than the head and reads as a party hat, the head icosahedron is not mirror-symmetric so the muzzle patch sits off-centre, about 35 triangles are never seen, 27 parts is heavy. Its measurable claims checked out: the staff intersects `FurCheek_L`; 2 of the head's 12 vertices have an x-mirror partner |
