# Identity fields

A mock person rarely travels alone. The name is safe once it carries a marker; the fields around it have their own traps, and most of them are worse, because a plausible ID number is not just confusing — it points at a real citizen.

## National ID — เลขประจำตัวประชาชน

Thirteen digits, where the thirteenth is a check digit over the first twelve:

```
check = (11 - (Σ digit[i] × (13 − i)  for i = 0..11) mod 11) mod 10
```

**The rule: deliberately fail the checksum.** A mock ID with a *valid* checksum is a well-formed Thai national ID, and somewhere there is a citizen holding it. A mock ID with an invalid checksum can never belong to anyone, while still being thirteen digits that exercise every length check, input mask, and formatting routine you have.

Ready-made, all with deliberately wrong check digits:

```
0 0000 00000 00 1
0 0000 00000 00 2
0 0000 00000 00 3
9 9999 99999 99 8
9 9999 99999 99 7
```

A leading `0` or `9` adds a second layer of safety: the first digit of a real Thai ID encodes the holder's category and registration route, and `9` is not issued to ordinary individuals in the way `1`–`8` are. Combining an unissued prefix with a broken checksum makes collision effectively impossible.

Generate and verify with the helper in `scripts/gen_names.py`:

```bash
python3 scripts/gen_names.py --count 5 --with-id --format table
```

It emits only IDs that fail the checksum, and the script contains the validator so you can assert that in your own tests.

**Never** take a real ID and change one digit "to be safe" — one-digit edits land on another valid ID about ten percent of the time.

## Juristic person number — เลขทะเบียนนิติบุคคล

Also thirteen digits, same checksum algorithm. Same rule: break the check digit. Use a `0` prefix so the number is visibly not a real registration.

```
0 0000 00000 00 1
0 1055 00000 00 9
```

## Phone numbers

Thailand has no officially reserved test range, so there is no equivalent of the `555-01xx` convention in North America. Use an all-zeros subscriber block, which is not allocated in practice:

```
mobile   08-0000-0001   →  0800000001
mobile   09-0000-0002   →  0900000002
landline 02-000-0001    →  020000001
```

Keep the correct prefix shape (`06`/`08`/`09` for mobile, `02` for Bangkok landline) so number-format validation still fires. Do not generate a realistic-looking subscriber number.

## Email

Use the domains reserved by RFC 2606 and RFC 6761 — these are guaranteed never to be registered by anyone:

```
test.user@example.com
thodsob@example.org
applicant@example.net
anything@test.invalid
```

`example.com`, `example.net`, `example.org`, and the `.test` / `.invalid` / `.localhost` TLDs are reserved. **`example.co.th` is not reserved** — it is a registrable `.co.th` domain and should not be used.

## Addresses

Build from marker tokens, same as names:

```
๙๙/๙๙ หมู่ที่ ๙ ถนนทดสอบ
แขวงนามสมมุติ เขตข้อมูลจำลอง
กรุงเทพมหานคร ๙๙๙๙๙
```

Arabic-digit variant:

```
99/99 หมู่ที่ 9 ถนนทดสอบ
ตำบลนามสมมุติ อำเภอข้อมูลจำลอง
จังหวัดทดสอบ 99999
```

**Postcode:** use `99999`. Thai postcodes encode the province in the first two digits, and real provinces run up to `96` (Narathiwat). Nothing in the `99xxx` range is assigned, so `99999` is structurally a five-digit Thai postcode that can never resolve to a real place.

Note the two address vocabularies — Bangkok uses `แขวง`/`เขต`, the rest of the country uses `ตำบล`/`อำเภอ`/`จังหวัด`. If the system handles both, seed both.

## Bank accounts, tax IDs, and anything else with a checksum

The general principle generalises: **keep the shape, break the check.**

1. Match the real format exactly — length, grouping, prefix ranges — so every validator, mask, and formatter is exercised.
2. Make the value fail its own check digit, or sit in a range that is structurally unissued.
3. Keep it constant across the project so it is greppable alongside the names.

This is the whole discipline in one line: **a mock identifier should pass every format check and fail every authenticity check.**

## What to grep for

Once a project follows this convention, its entire fabricated population is findable:

```sql
SELECT * FROM users          WHERE first_name LIKE 'ทดสอบ%' OR first_name LIKE 'ตัวอย่าง%';
SELECT * FROM companies      WHERE name       LIKE '%ทดสอบ%';
SELECT * FROM users          WHERE national_id LIKE '0%' OR national_id LIKE '9%';
SELECT * FROM users          WHERE email      LIKE '%@example.%';
SELECT * FROM users          WHERE phone      LIKE '0_0000%';
SELECT * FROM addresses      WHERE postcode = '99999';
```

Five queries, complete census, zero false positives. That property is the entire reason to stop using สมชาย ใจดี.
