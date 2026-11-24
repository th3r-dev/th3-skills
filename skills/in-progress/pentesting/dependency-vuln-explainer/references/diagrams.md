# Diagrams for a vulnerability

Draw with the `diagram-design` skill. Its style gate, connector rules and complexity budgets apply unchanged. This file only picks the type and supplies the content.

## Which type

| What you need to show | diagram-design type | Focal (accent) element |
|---|---|---|
| How the exploit runs: injection, template RCE, gadget chain, deserialization, SSRF | **Sequence**, ≤5 lifelines: attacker input → entry point → vulnerable function → internal object → sink | the message that reaches the sink |
| Where the package sits and whether the app reaches it | **Tree** if each node has one parent; **Dependency graph** if several parents pull it in | the vulnerable package node |
| Tainted data spreading: prototype pollution, header injection | **Data flow** | the polluted object or the sink |
| Many alerts at once, triage | **Quadrant**: x = app reachability (R0–R3), y = advisory severity | the top-right items, 2 max |
| Choosing the fix | **Flowchart** (only if the user asks; the ranked list usually suffices) | the chosen option |

The default is two figures in one HTML file: the sequence and the tree.

## Reachability tree conventions

- Root = the app (`name@version` from the manifest).
- Solid edge = the app actually loads it (import found). Dashed edge = installed but never loaded. Label the dashed edge `NO IMPORT` or `NOT CONFIGURED`.
- The vulnerable package node carries the version and the verdict as its sublabel (`10.21.0 · R1`).
- Show at most one sibling: the package the app *does* use for the same job. It answers the reader's next question ("so what renders our templates?").

## Sequence conventions

- Lifeline 1 is the attacker-controlled input itself (`template text`, `request body`), not a person icon.
- Keep each message ≤14 characters (diagram-design label rule). Put the step detail in the `<desc>` and in the card's Mechanism section.
- End at the sink (`Function()`, `child_process`, `fs.readFile`, `eval`). Do not draw anything that happens after code execution.

## Brief to pass to diagram-design

Fill in the angle brackets and pass it as the skill's args or prompt:

```
Two figures in one HTML file, minimal light variant, doc-wide.
Figure 1, sequence "How <GHSA-id> works": lifelines <L1>, <L2>, <L3>, <L4>, <L5>.
Messages in order: <m1>, <m2>, ... Focal: <sink message>.
Figure 2, tree "Does it reach <app>": <app> → <parent> (dashed, NO IMPORT) → <package> (<version> · <verdict>);
<app> → <sibling used instead> (solid). Focal: <package>.
Footer: verdict line, fix option 1, advisory link.
```
