# Template (what `ticket_report.py draft` renders)

```
Test Result: *PASSED* (green) | *FAILED* (red) | *BLOCKED* (orange) | *NOT TESTED* (grey) — bold + colour
Test Environment: <Dev | UAT | Master | PRD> - Version <actual version>
Platform: <free text: Web (admin app) | Web (customer app) | Mobile app>
Test Date : DD/MM/YYYY HH:MM
Test Data: <username> / <password: dev/uat only>
Actual Result :
<1-2 sentences, opening with the outcome, e.g. "all 4 cases passed …" or "3 cases could not run …">

| Test Case | Actual Result | Expected Result |      (only when there is more than one case)
| 1. <case> | *PASSED* <what happened> | <what should happen> |

### What happened                              (Thai labels with --lang th: สิ่งที่เกิดขึ้น · ควรได้ · ได้จริง · ขั้นตอน · สาเหตุ · ข้อมูลที่ใช้ · รายละเอียดสำหรับทีมพัฒนา · ไฟล์ประกอบ)
**1. <what was tested, in plain words>**  *PASSED*
**Expected** <one sentence>
**Actual** <one sentence, opening with the outcome>
**Steps**
1. <click / enter what>
2. ...
**Cause** <only for cases that did not pass; 1-2 sentences in user terms>
**Test data**
- <name: value>
<image> <one-line caption>
**Details for the dev team**
- <code path · commit · API · table/column · ids>

### Attached files
<report.md, results.json, export files · never cases*.json>
```

# cases.json — one case

```json
{"case": "The tax report for 21/09/2026 shows the full quantity of document DOC-001524",
 "expected": "quantity 1,779,859 L, excise 1,139,109.76",
 "actual": "shows the full 1,779,859 L and 1,139,109.76 (before the fix only 1,084,925 L)",
 "result": "PASSED",
 "steps": ["sign in with the central officer account", "open Reports > Tax report",
           "pick 21/09/2026 to 21/09/2026", "press \"Load data\" and find row DOC-001524"],
 "data": ["document: DOC-001524 · fuel oil", "account: officer.central.01"],
 "evidence": [{"file": "c1-tax-21-09-page.png", "caption": "the report page after Load data"}],
 "tech": ["POST /api/report/taxable/data date_from=date_to=2026-09-21 returns 52 rows",
          "fixed in api commit ad410852f (group by tax point date)"]}
```

Not passed? Add `"why"` in user terms ("the system could not find the product's formula"), never
the code name of the check. A before-the-fix comparison run gets `"baseline": true` (shown, not judged).

# Shapes that come up

| Shape | How |
|---|---|
| N cases, all PASSED | `cases.json` with N entries; header table + one block each |
| baseline + fixed | first entry `baseline: true` (FAILED), second the retest (PASSED); Test Result = PASSED |
| BLOCKED | `result: BLOCKED`, `steps` up to the point it stopped, `why`, `tech` with what the dev team needs |
| mixed | PASSED + FAILED + BLOCKED; Test Result takes the worst (FAILED) |
