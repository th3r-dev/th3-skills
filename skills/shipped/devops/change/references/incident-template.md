# <YYYYMMDD> — <symptom as the reporter said it>

| | |
|---|---|
| status | investigating · **root cause found** · fixed · monitoring |
| what breaks | the page / endpoint / job, and who sees it |
| endpoint / component | `POST /api/...` → service.method |
| code read | repo · branch · commit |
| data measured on | which database / environment, read-only |
| checked on | date |
| diagram | [`rootcause.html`](rootcause.html) · [`rootcause.png`](rootcause.png) |
| fix | branch / commit / change folder |

![diagram](rootcause.png)

## Summary

What happens, in one paragraph, with the numbers: how long, how many rows, which timeout, what the
user sees. If an earlier version of this report was wrong, keep a **Correction** paragraph saying what
was wrong and what the evidence for the new answer is.

## Why now

The changes that came together (a release that moved a page to a heavier endpoint, data growth, a
default timeout). One numbered item per contributing cause, with the commit or date.

## Evidence

Logs, timings and queries, pasted as they came out. Each block says where it was taken (host, pod,
time UTC).

## Hypotheses ruled out

Each with the evidence that killed it — the next person will think of them too.

## Options

| option | effect | risk | owner decided |
|---|---|---|---|

## Timeline (UTC)

| time | event |
|---|---|
