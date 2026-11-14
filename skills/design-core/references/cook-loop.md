# The cook loop: target, bar, critics

How to iterate until the work holds up next to its references, instead of stopping when it
first renders. Adapted from [Leonxlnx/cook](https://github.com/Leonxlnx/cook) (MIT). Cook itself
is built for 10–40 hour showcase runs; here the same loop is scaled to the job, from one screen
to a full page.

## 1. Intake: every question once, up front

Ask all open questions in one message, each with a default, so the user can reply "defaults":
what to build, references ([reference-first.md](reference-first.md)), the bar, time budget, hard
rules, deliverable, what may be downloaded or published. After that, don't ask; decide, log the
decision, keep going. Exception: anything destructive or outward-facing still needs a yes.

## 2. Target before code: three variants

Before any app code, build a static mockup page with **three competing directions side by side**,
each at desktop and phone width. Same content, different answers to the open choices.

- Cheap to throw away: no state, no data layer, no routing.
- One look shows hierarchy, type and the phone layout across all three.
- Each variant takes from the references, none clones one.

The user picks one (or mixes). Only then build the real thing. In Figma, the three variants
are three frames on a duplicated page.

## 3. The bar, per dimension

Write a number per dimension in the brief: composition, type, color, spacing, detail, motion.

- Aim high and explicit ("99% of the reference's polish", or 9.2/10). A vague "clean and
  professional" has no stop condition.
- **Models rate their own work too high.** When the user says "you're at 60–70%, not 90%", log
  the gap as a calibration offset and subtract it from every later self-score.
- Keep measured numbers (a script produced them) apart from eyeballed ones.

## 4. Layout first, motion second

1. **Static pass.** No animation code. Grid, spacing, type, color, content. Check every width
   (1440, 1024, 768, 390, 320) before moving on.
2. **Motion pass.** From reference recordings: list each effect with its duration, easing and
   trigger, then build them. Take from several, copy none. Reduced motion rests everything.

## 5. Each round

1. **Focus:** open user feedback first, else the weakest dimension on the weakest screen.
2. Fix it in depth: one area exceptional before spreading wide.
3. Render the same views every round (fixed widths and scroll positions).
4. Side-by-side images: reference left, render right.
5. **Score with fresh-context critics** (below). Your own score is logged, never decisive.
6. Log the round. Show the user the images and a three-line note: changed, scores, next focus.
7. If the bar isn't met, start the next round.

Stop when every dimension meets the bar by critic median after calibration, or a cap is hit;
then report what is still below it. Never claim a check that wasn't run: write "not measured".

## 6. Critics

The author can't judge its own work. A critic is a new subagent (or a different model) with
**no history, no code, no brief and not your score**. It gets only the side-by-side images and
the rubric.

- Two critics a round, three for big work; take the median. If they differ by more than 1.0
  on a 10-point scale, add one more.
- A different model as one critic helps (for example Codex or another provider via the user's CLI).
- Without subagents, a fresh session with only the images. Failing that, self-score and mark
  it "self-scored".

```text
You are a strict art director seeing this work for the first time.
Each image: reference left, build right. Score the right side 0–10 against the left on
composition, type, color, spacing, detail. The bar is [9.2].
List the 3 biggest gaps per image: where, what is wrong, what to change.
End with the single weakest area.
```

## 7. Precise feedback

- **Mark it up.** A screenshot with the problem circled beats a sentence.
- **Borrow the build's vocabulary.** When something looks off but can't be named, ask the builder
  to list exactly what it built there: grid, padding scale, alignment, hex values, font size and
  line height. Then give the fix in those terms ("12-column grid, inline padding 48 → 24 px").
- Log the user's exact words and handle them before any critic item.

## 8. Ledger and pacing (long runs)

For anything longer than one sitting, keep run state in a `cook/` folder in the work folder so a
context reset or another agent can continue:

| File | Holds |
|---|---|
| `cook/BRIEF.md` | Target, bar, rules, time, deliverable, permissions |
| `cook/SHOTS.md` | One line per reference: what to take from it |
| `cook/ROUNDS.md` | One entry per round: focus, changes, raw and calibrated scores, decisions, best so far |
| `cook/refs/`, `cook/compare/rNN/` | References; side-by-side images per round |

- Read the clock at each round boundary. Done far before the time budget usually means the bar
  was read too low: look again at full size, at phone width, at the weakest screen.
- Spread usage across the limit window instead of burning it in the first hour.
- If a round lowers a score, fix it or go back to the best round, and log why.
- Commit locally at the end of each round if the project uses git.
