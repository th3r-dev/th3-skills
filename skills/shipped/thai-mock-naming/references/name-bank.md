# Name bank

Approved tokens, ready-made sets, and the blocklist. Everything here follows the one rule: **the given-name slot carries a test marker.**

## Given-name markers (ชื่อ)

| Token | Reading | Note |
|---|---|---|
| ทดสอบ | test | House default. Not used as a Thai personal name. |
| ตัวอย่าง | example, sample | Second default, for a distinct person. |
| ทดลอง | trial, experiment | Good for pilot/experimental records. |
| สมมุติ | hypothetical, supposed | Also spelled สมมติ — pick one spelling per project. |
| นำร่อง | pilot | For pilot-phase fixtures. |
| ชั่วคราว | temporary | For records that are meant to be deleted. |
| สาธิต | demonstration | For demo and training environments. |

All seven are gender-neutral. Add `ชาย` / `หญิง` / `เล็ก` as a suffix when you need the title logic exercised: `ทดสอบชาย`, `ทดสอบหญิง`, `ทดสอบเล็ก`.

## Surname markers (นามสกุล)

| Token | Reading |
|---|---|
| นามสมมุติ | pseudonym |
| ข้อมูลจำลอง | simulated data |
| นามทดสอบ | test name |
| มิใช่บุคคลจริง | not a real person |
| ตัวอย่างสกุล | example surname |
| ระบบทดสอบ | test system |

`มิใช่บุคคลจริง` is the strongest signal and the longest — useful precisely because it also stress-tests column width.

## Role tokens (surname slot, role-bearing tier)

| Token | Role |
|---|---|
| ผู้ยื่นคำขอ | applicant / submitter |
| ผู้อนุมัติ | approver |
| ผู้ตรวจสอบ | reviewer / auditor |
| ผู้ดูแลระบบ | system administrator |
| เจ้าหน้าที่รัฐ | government officer |
| ผู้ประกอบการ | business operator |
| ผู้รับมอบอำนาจ | authorised representative |
| ผู้ใช้ทั่วไป | ordinary user |

## Ready-made sets

### Minimum pair

```
ทดสอบ นามสมมุติ
ตัวอย่าง ข้อมูลจำลอง
```

### Title / gender matrix

```
นาย       ทดสอบชาย    นามสมมุติ
นาง       ตัวอย่างหญิง  ข้อมูลจำลอง
นางสาว    ทดสอบหญิง   นามสมมุติ
เด็กชาย    ทดสอบเล็ก    นามสมมุติ
เด็กหญิง   ตัวอย่างเล็ก  ข้อมูลจำลอง
```

### Approval-workflow cast

```
ทดสอบ ผู้ยื่นคำขอ
ทดสอบ ผู้ตรวจสอบ
ทดสอบ ผู้อนุมัติ
ทดสอบ ผู้ดูแลระบบ
```

Four actors, one marker, instantly readable in a screenshot of an audit trail.

### Bulk seed (indexed)

Arabic digits:

```
ทดสอบ นามสมมุติ001
ทดสอบ นามสมมุติ002
ทดสอบ นามสมมุติ003
```

Thai digits, when the system must survive them:

```
ทดสอบ นามสมมุติ๐๐๑
ทดสอบ นามสมมุติ๐๐๒
ทดสอบ นามสมมุติ๐๐๓
```

Keep the padding width fixed. `นามสมมุติ9` sorts after `นามสมมุติ10` as a string; `นามสมมุติ009` does not.

### Juristic persons

```
บริษัท ทดสอบระบบ จำกัด
บริษัท ตัวอย่างข้อมูล จำกัด (มหาชน)
ห้างหุ้นส่วนจำกัด นามสมมุติการค้า
ห้างหุ้นส่วนสามัญ ทดสอบพาณิชย์
ร้านทดสอบค้าปลีก
บริษัท สาธิตอุตสาหกรรม จำกัด
```

## Blocklist — never use as mock data

### Given names

`สมชาย` · `สมหญิง` · `สมศรี` · `สมปอง` · `สมพงษ์` · `สมบัติ` · `สมคิด` · `มานะ` · `มานี` · `ปิติ` · `ชูใจ` · `วีระ` · `สุดา` · `สมหมาย` · `ประเสริฐ` · `จำลอง` · `สมบูรณ์` · `อนันต์`

### Surnames

`ใจดี` · `พอใจ` · `ทองดี` · `ศรีสุข` · `สุขใจ` · `รักเรียน` · `ดีงาม` · `แสงทอง` · `รุ่งเรือง` · `สว่างวงศ์` · `บุญมี` · `มีสุข` · `ศรีเมือง` · `ทองคำ`

These are all real, common Thai names. `มานะ มานี ปิติ ชูใจ` are the characters from the Thai ป.1 primary reader — widely recognised, which tempts people into treating them as safe. They are not: they are ordinary Thai given names, and real people have them.

### The trap worth repeating

`จำลอง` means "simulated", which makes it feel like a marker. It is also a real Thai given name. Use it only inside a compound — `ข้อมูลจำลอง` — never alone in the given-name slot.

## Project convention block

Copy this into the project README or `CONTRIBUTING.md` so the convention survives contributor turnover:

```markdown
## Mock data naming

All fabricated people in this repo use the given name `ทดสอบ`.
All fabricated companies use `บริษัท ทดสอบ... จำกัด`.

This makes test records greppable:

    SELECT * FROM users WHERE first_name LIKE 'ทดสอบ%';

Do not use plausible real Thai names (สมชาย ใจดี, มานี, etc.) anywhere
in fixtures, seeds, docs, or screenshots. CI runs
`scripts/check_mock_names.py` and will fail the build.
```
