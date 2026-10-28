# Work report — summarize the steps, so the next person can follow

When this skill does more than read (runs a sandboxed repro, applies a fix, touches a machine or a network path), the work ends with a **report**, not a verbal "done". Same discipline as a DevOps change record: before / steps / after / rollback / outcome, graded by severity, every claim backed by the real command output. Adapted from the OCM-DEVOPS-WORKBENCH `changes/TEMPLATE.md` convention.

A verdict in chat evaporates. A report is what the reviewer reads, what the next agent picks up, and what you diff against when it breaks again.

## When to write one

- **Always** for: running a PoC/repro, applying a fix to a lockfile or code, anything that changes a file or runs target code.
- **Not** for: a pure reachability read that ends in a verdict (the vuln card already is that report).

## Severity (decide before you act, put it at the top)

| SEV | Meaning | Response |
|---|---|---|
| SEV-1 | Confirmed reachable (R3) RCE / auth bypass / data exposure in a running service | now; tell the owner before anything else |
| SEV-2 | Reachable high-impact, or critical advisory reachable behind a precondition | same day |
| SEV-3 | Installed, limited reach (R2), or fix carries breaking-change risk | this week |
| SEV-4 | Installed, not loaded (R1) / informational | normal queue |

App severity here is the skill's reachability verdict, not the advisory's CVSS.

## The report

One file per piece of work, beside the vuln card:

```markdown
# <YYYYMMDD> — <advisory / package> — <what was done>

| | |
|---|---|
| Package / repo | |
| SEV | <1–4> · <why> |
| Verdict | <R0–R3 / needs validation> |
| Requested by | |
| Done by | |
| Status | plan · done · verified · rolled back |

## Why
Two lines. Link the card.

## Before
The commands you ran to capture current state, and their **real output** — not a summary.
Pin the facts the "After" section will be compared against: installed version(s),
`npm ls` / `pip-audit` result, the sandbox image tag, the marker/sentinel used.

​```
<paste actual output>
​```

## Steps actually run
Every command that changed state, in order, with its result — including steps that
were not in the plan. If something unexpected happened, write it in the row, plainly.

| time (UTC) | action | result |
|---|---|---|
| | backup (`cp -p package.json package.json.bak-<date>` / git branch) | |
| | <fix or repro command> | |

## After
Re-run the exact Before commands. Paste the output. If it differs from what you
expected, say where and why. For a fix, the proof command must show the vulnerable
version gone (`npm ls --package-lock-only <pkg>` empty or patched).

## Rollback
The ordered steps that restore the previous state, thought through to the end before
step one. Then the command that proves rollback worked.

## Outcome (blameless)
Systems and steps, not people.
- What went to plan, what didn't.
- Who/what else might be affected, and what you did not check.
- Follow-up prevention work, each with an owner.
```

## Rules carried over from the workbench

- **Evidence, not memory.** Paste real command output; never retype or trim it. The numbers in "Before" are the pass/fail test in "After".
- **Back up before you touch.** A lockfile or config gets a `.bak-<date>` or a git branch first, recorded in the steps table.
- **Reversible first.** Prefer the change you can undo (override, branch) over the one you can't. Write the rollback before the first change, not after it breaks.
- **Shared or production target → ask per time.** A fix to a repo others deploy, or anything run against infrastructure, needs the owner's go-ahead each time. Reading is free; changing is not.
- **Record what you poked.** If verifying meant opening a port, hitting an endpoint, or running target code, log the time — the other side may see it and mistake it for the symptom.
- **If a diagram exists, keep it true.** A new fact that contradicts the explainer diagram means fix the diagram too, not just the prose.

## In chat

Lead with the one-liner (`SEV-4 · R1 · removed @nestjs-modules/mailer, liquidjs gone, verified`), then link the report. The detail lives in the report; chat is the pointer.
