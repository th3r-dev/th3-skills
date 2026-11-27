---
title: Release vX.Y.Z
author: <author>
date: DD/MM/YYYY
---

# Overview

vX.Y.Z is ready for <staging|production>: N user-visible changes. <Items waiting on a merge or only partly shipped, if any.> N questions wait for the BA on the "BA Decision" page.

Production still runs <version>, as shown on the screen on DD/MM/YYYY. Tickets waiting for deploy close once vX.Y.Z is on production.

## In this release

| # | Ticket | What changes for the user | Status |
|-|---|----------|---|
| 1 | KEY-101 | What the user sees differently, plus one fact that makes it concrete (a timing, a number, which report moves) | Waiting for deploy |

## Waiting on a merge or partly shipped

| Ticket | Item | Status | If not handled before deploy |
|--|-----|-----|-----|
| KEY-102 | | PR #NN waiting for merge | |

## Not in this release

| Ticket | Item | Why |
|--|------|------|
| KEY-103 | | PR still a draft / PR targets dev |

## Tell the customer

- Figures that will change after the release, and why
- New rules that reject what used to pass, with how many are affected per user group
- Partly shipped items: never announce them as fixed
- Constraints on the production window, e.g. a low-traffic slot

# BA Decision

Questions only the BA can answer. Each comes from a ticket or a retest result, ordered by what must be answered first.

| # | Question | Options or proposal | Ticket | Needed before |
|-|------|--------|---|---|
| 1 | | The options the ticket or retest states; never invent options | KEY-104 | production / dev starts / go-live |

List only open questions. Anything already answered in meeting notes, a ticket comment or a retest stays out.

# Change details

## 1. KEY-101 <short name> (before and after shots)

| | |
|---|-------|
| Ticket | KEY-101 |
| PR | backend #NN · frontend #NN (PR author) |
| Owner | name from the board / not assigned |
| Status | Waiting for deploy (retest passed on <env> <date>) |
| What changes | one line, matching the real test result |
| Test cases | R01-01 |

| Before | After |
|-----|-----|
| ![before](img/KEY-101-before.png) caption from the test result | ![after](img/KEY-101-after.png) caption from the test result |

## 2. KEY-102 <short name> (after shot only)

| | |
|---|-------|
| Ticket | KEY-102 |
| PR | backend #NN |
| Owner | |
| Status | |
| Original symptom | the symptom as reported in the ticket, with the report date (a new feature uses "Original request") |
| What changes | |
| Test cases | |

| After (<env> <date>) | What it shows |
|-----|-----|
| ![after](img/KEY-102-after.png) | caption from the test result |

## 3. KEY-103 <short name> (no shot)

| | |
|---|-------|
| Ticket | KEY-103 |
| PR | backend #NN |
| Owner | |
| Status | |
| Original symptom | |
| What changes | |
| Test cases | |

Evidence: where it comes from and when, as something a user can see (a file the system produced, a measured timing, a test result). No code file names, unit test counts or code-level detail.

| Check | Before | After |
|----|---|---|
| a real figure or result from the source named above | | |

# <user group being rolled out>

This group's items in this release, and their status.

Items not in this release: where they came from, who owns them, and which rollout ticket they hang off.

| Ticket | Item | Needed before go-live |
|--|----------|---|
| KEY-105 | | yes |

The go-live date, and what must be in a release before it.

# Test plan

| | |
|---|--------|
| Test Environment | Staging - Version vX.Y.Z (check the version on screen before every run) |
| Platform | Web <app name> |
| Test Date | |
| Test Data | account names and roles; no passwords |
| Test documents | documents named in the cases come from <retest env>; if staging lacks one, create one of the same kind and note its number in Actual Result |
| Evidence | a screenshot showing the URL and version for every case |
| Closing a ticket | every case of the ticket passes: move to waiting for deploy; any case fails: move to Fail with the reason and a shot |

## Full cases (tickets in Testing)

| TC | Ticket | Test Case | Expected Result | Actual Result | Status |
|---|----|--------|------|----|----|
| R01-01 | KEY-101 | account, screen and steps in one sentence; if the case compares with the state before deploy, say what to record first | something checkable: a number, a count, the text on screen, or a timing with a reference value | | |

## Re-checks (tickets waiting for deploy)

These tickets already passed a retest. This round checks they still work on staging; a failure moves the ticket back to Fail.

| TC | Ticket | Test Case | Expected Result | Actual Result | Status |
|---|----|--------|------|----|----|
| R01-02 | KEY-102 | | | | |

## Not tested this round

- KEY-103 reason
