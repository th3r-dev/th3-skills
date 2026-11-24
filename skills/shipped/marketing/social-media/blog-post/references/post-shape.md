# Post shape

## Making-of / how-to

The shape the benchmark case uses. It follows claude-blog's
[how-to template](https://github.com/AgriciDaniel/claude-blog): answer first, then the steps.

| Part | What goes in |
|---|---|
| Title | one of the five options from hooks.md |
| Opening (2 short paragraphs) | what was made, for whom, and the result in one line; then what the post covers |
| Steps (4 to 7, numbered `## 1.`) | one decision per step: what, why, the file or command; real names only; an image right under each heading |
| What broke | the failures and the fix for each, as a short list; the most useful step for a reader |
| The choice | which variant was picked and the measured reason |
| Closing image | the finished work itself, after the last step |
| Close | the "if you want ..." hook, then the CTA link (hooks.md) |

Length: at most 2,000 characters of shown text by default (the `length` check counts what a reader
sees: no markdown marks, image lines, URLs or code). The cover image goes under the title.

Commands go in code blocks; the bench skips code when it checks dashes and numbers.

## Thai

- Load `kien-thai` before drafting. A personal blog uses ผม or ดิฉัน (ask if unknown) and ครับ / ค่ะ
  only at the opening and the sign-off.
- Spaces carry sentence boundaries inside a paragraph; no mid-paragraph periods.
- Technical words stay in English when that is how Thai developers say them (spec, bench, script,
  cluster); Thai words for everything else.
- Pivot with แต่ or a question, not อย่างไรก็ตาม.
- Close forward (an offer, a next step), never a recap.

## English

- Plain sentences, no em dashes, no "not X but Y" staging (the humanizer rules).
- Second person for the reader, first person only for the author's own work.

## After drafting

1. kien-thai audit (Thai) and humanizer pass (both languages).
2. `bench_post.py` with the case; fix every FAIL.
3. Read the post once at phone width; long Thai lines should still break at spaces.
