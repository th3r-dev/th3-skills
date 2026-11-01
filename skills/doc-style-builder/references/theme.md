# Theme: fonts, sizes, colors

`assets/theme.css` holds the values; this page says what each one is for. Change the CSS, not this table,
and `build_doc.py` carries the change into both the PDF and the DOCX.

## Fonts

| Token | Value | Used for |
|---|---|---|
| `--font-body` | TH Sarabun New → TH SarabunPSK → Sarabun (scaled 75%) → sans-serif | body, tables, captions |
| `--font-heading` | TH Sarabun New → TH SarabunPSK → Sarabun (scaled) | title and headings, bold |
| `--font-code` | Consolas → Courier New → monospace | inline code and code blocks |

TH Sarabun New is free (SIPA / f0nt.com). Install it for exact output. Sarabun (Google Fonts) is the
fallback and is scaled to 75% because 16pt TH Sarabun New reads like 12pt Sarabun. Thai is a complex script in
Word, so the DOCX sets the `cs` font as well as `ascii`/`hAnsi`; without it Thai falls back to the theme font.
The DOCX can name only one font per style, so it takes the first of each stack: put the font your readers
actually have first.

## Type scale (pt)

| Token | Size | Element |
|---|---|---|
| `--size-title` | 26 | document title (front-matter `title`), centered |
| `--size-subtitle` | 18 bold | front-matter `subtitle`, centered |
| `--size-h1` | 20 | `#` section |
| `--size-h2` | 17 | `##` subsection |
| `--size-h3` | 16 | `###` |
| `--size-body` | 16 | body, tables, lists |
| `--size-caption` | 14 italic | figure captions |
| `--size-code` | 10.5 | inline code |
| `--size-code-block` | 8.5 | code blocks (logs and JSON stay on one line more often) |

Line height 1.25. Page A4, margins 18 mm top/bottom and 20 mm left/right.

## Colors

| Token | Hex | Used for |
|---|---|---|
| `--color-text` | `#000000` | all body text and headings |
| `--color-caption` | `#404040` | captions, author/date line, quotes |
| `--color-muted` | `#808080` | "no evidence yet" and other absent values |
| `--color-rule` | `#000000` | table borders |
| `--color-border` | `#BFBFBF` | image and code-block borders |
| `--color-header-bg` | `#E7E6E6` | table header row, key column of key/value tables |
| `--color-code-bg` | `#F5F5F5` | code blocks |
| `--color-pass` | `#1A7F37` | pass / ผ่าน |
| `--color-fail` | `#CC0000` | fail / ไม่ผ่าน |
| `--color-added` | `#C6EFCE` | row added in this revision |
| `--color-edited` | `#FFF2CC` | row edited in this revision |
| `--color-removed` | `#FFC7CE` | row removed in this revision (also struck through) |

The palette is deliberately plain: black text on white, one grey for structure, color only where it
carries meaning (pass/fail, change state). Do not add brand colors to body text or headings.

## Tables

- Every cell bordered, header row shaded `--color-header-bg` and bold, header repeats on each page.
- A row never splits across pages.
- Full text width; column widths follow the dash counts in the Markdown separator line (`|---|------|` gives 1:2).
- Change rows: start the first cell with `[+]`, `[~]` or `[-]`. The builder shades the row and removes the marker.
  When a document uses them, put this legend once near the top:

  ```markdown
  | สถานะ | ความหมาย |
  |---|---|
  | [+] เพิ่มใหม่ | added in this version |
  | [~] แก้ไข | changed in this version |
  | [-] นำออก | removed in this version |
  ```

## Images

Centered, at most 90% of text width in the PDF and text width in the DOCX, 1 px `--color-border` frame,
italic caption below (`![caption](path.png)` makes the caption). Screenshots show the address bar or prompt.

## Dates and file names

- Thai readers: Buddhist-era dates `dd/mm/yyyy+543` (`13/10/2569`). English readers: `13 Oct 2026`.
- Output files: `[<PREFIX>_]<name> - Update <ddmmyyyy>.<ext>`. The date is in the name, so folders group by
  topic, not by day, and a rebuild on the same day overwrites the same file.
