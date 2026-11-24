# Edge-case names

Names built to break things. Every one still carries a marker, so a failure in production-like data is still obviously a test record.

Use these when you want the fixture to *find bugs*, not just fill a column. The ordinary sets in `name-bank.md` are for demos and screenshots; this set is for QA.

## Length boundaries

| Case | ชื่อ | นามสกุล | What it tests |
|---|---|---|---|
| Minimum | `ก` | `ข` | Min-length validation, single-character rendering, avatar initials |
| Short | `ทด` | `สอบ` | Two-character names, which are legal in Thai |
| Typical | `ทดสอบ` | `นามสมมุติ` | The baseline |
| Long | `ทดสอบความยาวของชื่อที่มากเกินปกติ` | `มิใช่บุคคลจริงนามสกุลยาวมากเกินกำหนด` | Column width, PDF overflow, table truncation, CSS ellipsis |
| Over limit | 300+ characters of `ทดสอบ` repeated | same | Max-length rejection, DB column overflow, 500-error hunting |

Thai has no spaces between words, so a long Thai name is one unbroken token. This breaks word-wrap in ways a long English name does not — a browser can wrap `Supercalifragilistic Expialidocious` at the space, but has nowhere to break `ทดสอบความยาวของชื่อที่มากเกินปกติ` without Thai line-breaking support. That is exactly the bug these rows are for.

## Thai script hazards

| Case | Name | What it tests |
|---|---|---|
| Stacked marks | `ทดสอบ เครื่องหมายซ้อนชั้น` | Vowels above + tone marks on the same base character. Breaks fixed line-height layouts and clips in tight table rows. |
| การันต์ (silent mark) | `ทดสอบกิตติ์ นามสมมุติ` | The `์` terminal mark. Some naive truncation routines cut between the consonant and its mark, producing mojibake. |
| ฤ / ฦ | `ทดสอบฤทธิ์ นามสมมุติ` | Rare characters that fall outside sloppy `[ก-ฮ]` regex ranges. |
| Sara am | `ทดสอบรำ นามสมมุติ` | `ำ` is one character that renders as two glyph parts. Character counts and cursor movement disagree. |
| Leading vowels | `เทดสอบ แนามสมมุติ` | `เ แ โ ใ ไ` are typed and stored *before* their consonant but pronounced after. Breaks naive sorting and phonetic search. |
| No ascenders | `ทดสอบ นามสมมุติ` vs `ทดสอบปิ่น นามสมมุติ์` | Thai line height varies with mark stacking; a row of plain characters and a row of fully-stacked ones should not shift the layout. |

## Structural hazards

| Case | Name | What it tests |
|---|---|---|
| Internal space in surname | `ทดสอบ นามสมมุติ ณ ทดสอบ` | Royal-style `ณ` surnames contain spaces. Any code that splits a full name on whitespace into exactly two fields will corrupt this. |
| Leading / trailing space | `␠ทดสอบ␠` / `␠นามสมมุติ␠` | Trimming on input and on comparison. |
| Double internal space | `ทดสอบ␠␠นามสมมุติ` | Whitespace normalisation. |
| Zero-width space | `ทดสอบ<ZWSP>นามสมมุติ` (`U+200B`) | Thai text often carries ZWSP as a line-break hint. Equality checks and `LIKE` queries fail silently against it. |
| Mixed script | `ทดสอบ Test-นามสมมุติ` | Bidirectional-ish rendering, font fallback, and regex that assumes a single script. |
| Latin-only | `Test Mockname` | The transliterated path, for systems with a separate English-name field. |
| Numerals in name | `ทดสอบ๑๒๓ นามสมมุติ` | Thai digits inside a name field; numeric parsing that assumes Arabic digits. |

## Collation set

Thai sort order is not codepoint order. Leading vowels (`เ แ โ ใ ไ`) sort with the consonant that follows them, not where they are stored. Seed this set and assert the expected order:

```
ทดสอบ กขค
ทดสอบ ขคง
ทดสอบ เกขค      ← sorts as if it began with ก
ทดสอบ คงจ
ทดสอบ แขคง      ← sorts as if it began with ข
ทดสอบ ฤกษ์      ← ฤ sorts after ร, not at the end of the alphabet
ทดสอบ ฮกฮอ
```

Expected Thai collation (ICU `th-TH`) orders by the first *pronounced* consonant, so `เกขค` lands next to `กขค`, not between `แ` and `โ`. A `ORDER BY name` on a database without a Thai collation will get this wrong, and this set is how you prove it.

## Suggested QA fixture

A minimal set that covers most of the above in seven rows:

```
ก ข
ทดสอบ นามสมมุติ
ทดสอบกิตติ์ นามสมมุติ ณ ทดสอบ
ทดสอบฤทธิ์ เครื่องหมายซ้อนชั้น
ทดสอบความยาวของชื่อที่มากเกินปกติ มิใช่บุคคลจริงนามสกุลยาวมากเกินกำหนด
ทดสอบ Test-นามสมมุติ
เทดสอบ แนามสมมุติ
```

Generate it with:

```bash
python3 scripts/gen_names.py --edge-cases --format json
```
