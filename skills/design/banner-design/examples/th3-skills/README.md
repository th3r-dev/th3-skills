# th3-skills social preview

The repo's GitHub social preview (1280 × 640): the ten skills as four jobs (Design, Build, Test,
Ship), every layout from [layouts.md](../../references/layouts.md) in the three preset styles.

<img src="columns-flat-1280x640.png" width="100%" alt="th3-skills banner, columns layout, flat style: ink brand panel left, four columns Design, Build, Test, Ship with the skills under each, Install bar bottom right">

| | flat | dark | minimal |
|---|---|---|---|
| **columns** | <img src="columns-flat-1280x640.png" alt="columns, flat"> | <img src="columns-dark-1280x640.png" alt="columns, dark"> | <img src="columns-minimal-1280x640.png" alt="columns, minimal"> |
| **rail** | <img src="rail-flat-1280x640.png" alt="rail, flat"> | <img src="rail-dark-1280x640.png" alt="rail, dark"> | <img src="rail-minimal-1280x640.png" alt="rail, minimal"> |
| **stairs** | <img src="stairs-flat-1280x640.png" alt="stairs, flat"> | <img src="stairs-dark-1280x640.png" alt="stairs, dark"> | <img src="stairs-minimal-1280x640.png" alt="stairs, minimal"> |
| **bento** | <img src="bento-flat-1280x640.png" alt="bento, flat"> | <img src="bento-dark-1280x640.png" alt="bento, dark"> | <img src="bento-minimal-1280x640.png" alt="bento, minimal"> |

Everything comes from one spec, [th3-skills.banner.json](th3-skills.banner.json): copy, the skills'
own icons, the variant list.

```
uv run ../../scripts/banner.py th3-skills.banner.json          # 12 SVGs
for f in *-1280x640.svg; do uv run ../../scripts/bench.py $f; done
```

## Bench

All 12 pass. Worst contrast per style: flat 5.54:1, dark 9.05:1, minimal 5.12:1 (the step
numbers and secondary lines); core text 10.0px at a 400px phone card; PNGs 70-74 KB.

How it got there, on the columns-flat original:

1. Failed: the promise at 26px and the CTA at 22px came out at 8px and 7px on a phone card,
   under the 32px headline minimum. Widened the brand side to 32.5%, set both at 32px, moved the
   copyable command to the support zone.
2. Added dark and minimal: tokens only, same grid.
3. Added rail, stairs and bento from the layout research. Stairs' CTA ran out of room indented a
   fourth time, so it became the full-width floor; bento's tiles had dead lower halves, so the
   skill list moved to each tile's foot with one divider height for the grid.

Grayscale and spelling were checked by eye. My pick is columns-flat, because it is the repo's
own system. To use one, upload its `.png` under Settings → Social preview.
