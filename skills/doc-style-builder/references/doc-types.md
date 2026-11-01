# Document types: one skeleton each

Pick the type before writing. Each skeleton fixes the section order and the table columns so two documents
of the same type read the same way. Headings are Thai by default; swap to the English label in brackets
when the reader works in English. Do not mix languages inside one heading level.

Every document opens with the same front matter:

```yaml
---
title: <what this is>
subtitle: <system / version / scope>
author: <team or role, not an internal handle>
date: <dd/mm/yyyy+543 for Thai readers, e.g. 13/10/2569>
---
```

Add a revision-history table (`ประวัติการแก้ไข` / Revision history) right after the front matter for any
document that will be revised: `Version | วันที่ | ผู้เขียน | รายละเอียด`.

---

## 1. Report / change record: รายงาน (Report)

For: work done on a system (deploy, update, migration, incident fix) that someone outside the team must accept.
Reader wants proof it is done and what is still blocked; nothing else.

```
# สรุป (Summary)                3–5 lines: what changed, where, the result, what is still open
# ขั้นตอน (Steps)                numbered walkthrough as the operator runs it on the target, not the tools you used
# ผลการทดสอบ (Results)          one table + evidence images
# ปัญหาที่พบ (Issues)            only if any
# Rollback                      the exact commands to undo, on the target
```

Results table: `รายการ | ผล | หลักฐาน` (Item | Result | Evidence). Result is `ผ่าน` / `ไม่ผ่าน` / `ยังไม่มีหลักฐาน`.
Issues table: `ปัญหา | สาเหตุ | สิ่งที่ต้องทำ | ผู้รับผิดชอบ`; the owner is a role ("IT ของลูกค้า"), never a person's handle.

Rules: no raw logs, no internal paths or config-file labels, at most ~4 screenshots per target, every screenshot
shows the address bar or prompt that proves where it was taken. A check with no evidence stays in the table as
`ยังไม่มีหลักฐาน`; it is not dropped.

## 2. API reference: เอกสาร API Spec (API Specification)

For: integrators calling an endpoint. Ground every field in the real controller/DTO before writing.

Per endpoint, in this order:

```
# API สำหรับ <purpose>                  (API for <purpose>)
<Service Info table>
## รูปแบบข้อมูล Request                 (Request format)
<request table>
ตัวอย่างข้อมูล Request + ```json block
## รูปแบบข้อมูล Response                (Response format)
<response table>
ตัวอย่างข้อมูล Response + ```json block
```

Service Info is a two-column table with all 11 keys in this order, `-` when unknown (never invent a URL):
System Name · Service Name · Service Type · Service Protocol · Service URL Non-Production ·
Service URL Production · HTTP Method · Request Content Type · Request Char Encoding ·
Response Content Type · Response Char Encoding.

Field tables: `ลำดับ | ชื่อข้อมูล | จำเป็น | ชนิดข้อมูล | คำอธิบาย` for requests (`จำเป็น` = `Y`/`N`),
`ลำดับ | ชื่อข้อมูล | ชนิดข้อมูล | คำอธิบาย` for responses. Nested objects are flattened into numbered groups:
the field row names the type (`2 | data | Order[] | …`), then a parent row with only the type name
(`3 | Order | | `), then its fields `3.1`, `3.2`, … The next object continues the counter (`4`, `4.1` …).

On a revision, mark changed rows with `[+]` / `[~]` / `[-]` and add the legend from `theme.md`.

## 3. User guide / quickstart: คู่มือการใช้งาน (User Guide)

For: an end user doing a task in the UI.

```
# ก่อนเริ่ม (Before you start)    what they need: account, role, browser, network
# <task 1>                        numbered steps, one action per step, a screenshot where the screen changes
# <task 2>
# ปัญหาที่พบบ่อย (Troubleshooting)  symptom → cause → fix table
```

A quickstart is the same with one task and no troubleshooting; it should fit on one page.

## 4. FAQ: คำถามที่พบบ่อย (FAQ)

`## <question as the reader would ask it>` followed by a 1–3 sentence answer, then a link or step if needed.
Group under `#` headings by topic once there are more than ~8 questions.

## 5. Architecture / onboarding: ภาพรวมระบบ (System Overview)

For: a developer or operator new to the system.

```
# ภาพรวม (Overview)               one diagram + one paragraph: what talks to what
# ส่วนประกอบ (Components)          table: ส่วนประกอบ | หน้าที่ | เทคโนโลยี | ที่อยู่ (host/port)
# การไหลของข้อมูล (Data flow)      numbered path of one real request, left to right as the diagram reads
# การตั้งค่า (Configuration)       what can change per environment and where it is set
# การเริ่มพัฒนา (Getting started)   clone → run → verify, as copy-paste commands (onboarding only)
```

Use placeholders (`<host>`, `10.x.x.x`) for anything environment-specific when the document leaves the team.

## 6. README

```
# <name>                one-line purpose
## Install              copy-paste commands
## Usage                the two or three commands people actually run
## Configuration        only if there is any
## <Traps / Notes>      what fails silently, measured, with the fix
```

## 7. Changelog: บันทึกการเปลี่ยนแปลง (Changelog)

Newest first, one `## <version> (<date>)` per release, then `### เพิ่ม` (Added) · `### เปลี่ยน` (Changed) ·
`### แก้ไข` (Fixed) · `### นำออก` (Removed). One line per change, written for the reader of the release,
not the commit log.
