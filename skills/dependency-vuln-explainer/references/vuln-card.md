# Vuln card

The card is the unit of knowledge one agent hands to the next and the summary a reviewer reads. Keep the headings in this order so agents can parse it. Leave a field as `unknown` instead of guessing.

```markdown
# <GHSA-id> · <package>@<installed> · <verdict>

| Field | Value |
|---|---|
| Advisory | <GHSA-id> / <CVE-id> · <title> |
| Package | <ecosystem>:<package> |
| Installed | <version(s)> in <manifest/lockfile> |
| Vulnerable range | <range> · first patched <version> |
| Advisory severity | <critical/high/...> · CVSS <score> `<vector>` · EPSS <pct> |
| CWE | <id> <name> |
| Repo / ref | <owner/repo>@<branch> <short-sha> |
| Verdict | <R0/R1/R2/R3/needs validation> |
| App severity | <level or "none"> |

## Path
<root>@<ver> → <parent>@<ver> → <package>@<ver>   (direct|transitive, runtime|dev|optional)

## Preconditions (from the advisory)
- <what the attacker must control for the bug to fire>

## Reachability evidence
- `<command>` → <result>
- `<file:line>` → <what it shows>

## Attacker input
<Where the input the precondition needs comes from in this app, and who can write it. "No such input" is a valid answer.>

## Mechanism (plain language, ≤6 steps)
1. ...

## Neighbourhood
<Same bug class in a package the app does use. State what was checked and the result.>

## Fix options (ranked)
1. **<action>**: files <...>; risk <...>; proof `<command>`
2. ...
Chosen: <option or "awaiting user">

## Open questions
- <fact outside the source> · who can answer it

## Sources
- <advisory URL>
- <release / patch URL>
```

## Rules for agents reading a card

- Re-run the reachability commands before you rely on the verdict if the repo ref has moved.
- A second-opinion agent tries to **refute** the verdict. It reports either "refuted: <evidence>" or "holds: <what was checked>".
- Do not raise the app severity above what the evidence shows, and do not lower the advisory severity in the card's advisory row.
