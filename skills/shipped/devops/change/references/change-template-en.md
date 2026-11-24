# <YYYYMMDD> — <what changes>

| | |
|---|---|
| machine / cluster | |
| severity | SEV-1 whole system down · SEV-2 core feature degraded · SEV-3 workaround exists · SEV-4 minor |
| requested by | |
| executed by | |
| status | plan · executed · verified · rolled back |
| related incident | `incidents/<YYYYMMDD>-<slug>/` |

## Why

Two or three lines; cite the incident evidence if there is one.

## Before

The commands used to look, and their real output — no summarising. Capture evidence before touching
anything (config snapshot, md5, inode, container start time, the numbers the result will be measured
by). These numbers are the pass criterion in "After".

```bash
```

```
```

## Steps actually run

Timeline (UTC of the target machine) of every state-changing command, including steps that were not
in the plan. If something unplanned happened, write it into that row with the reason.

| UTC | what | result |
|---|---|---|
| | back up the config (`cp -p x x.bak-<YYYYMMDD>`) | md5 |
| | | |

```diff
```

## After

Run the same commands as "Before" and paste the output. If it differs from what was expected, say where.

```
```

## Rollback

The full sequence that restores the previous state. Walk it through in your head before step 1 of the change.

1.
2.

Confirm the rollback worked with:

```bash
```

## Remaining impact and lessons

Blameless — about systems and procedures, not people.

- who or what else may be affected, and what has not been checked yet
- what went to plan and what did not
- follow-up prevention work with an owner (technical · process · monitoring · documentation)
