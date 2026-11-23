# Review and playtest

A review scores **Studio captures**, never the code or the brief alone (game-dev: a check is a run,
not a parse). Use design-core's table ([SKILL.md, "When reviewing"](../../../design/core/SKILL.md))
and add three Roblox rows. Each row is 0-10 with what a 10 would be; a pass is 8 or more on every row.

| Row | A 10 looks like |
|---|---|
| Mobile fit | every string fits at 844×390; nothing that matters in the bottom corners; frequent buttons in the right thumb's reach; tap targets never below their floor |
| First action | a new player acts within 10-30 s; the first screen is play, not menus; no popup in the first five minutes |
| Trust boundary | every purchase or reward goes through the server; the client shows `loading` until it answers; a forged request changes nothing |

Score with fresh eyes: in Claude Code a subagent given only the captures and the brief; in another
agent a new session or a second model. The author's own score never decides.

## Playtest checklist

Run in Studio (Play), then the Device Emulator at phone, tablet and desktop. Capture each with the
Studio MCP server's screenshot tool, or by hand.

- [ ] Every state in the brief shows, at every device size: default, empty, loading, error, locked
      (and a shop's affordable, unaffordable, owned).
- [ ] No text overflow or clipping; numbers at their largest expected value (e.g. 9,999,999 gold).
- [ ] Bottom-left and bottom-right corners clear on the phone; the top bar not covered.
- [ ] Buttons answer: hover, press, disabled, loading; a sound and a tween on the action.
- [ ] Close X top right, greyed disabled, lock with its unlock condition, red price when short.
- [ ] Colours from tokens only; text on plates passes 4.5:1.
- [ ] The output log has no errors or warnings from the UI scripts.
- [ ] A purchase with too little currency is refused by the server even when the client is bypassed.

## UX review output

When reviewing a game's existing UI, report, most severe first (after AshExplained/roblox-skills, MIT):

- **First-action time**: seconds from spawn to the first meaningful action.
- **Friction before play**: menus, popups, reading.
- **Mobile risks**: overflow, reach, covered corners, precision drags.
- **Missing progression signals**: the objective, the currency, the next reward not visible in the loop.
- **Social visibility gaps**: what friends are doing, not shown.
- **Interruptions from monetization**: offers during the core action or the first session.
- **Fixes ranked by retention impact**, each as `surface:location — issue → fix` (design-core's
  finding format).

## Hand-off

Per surface: the brief's states and what the captures showed, the tokens used, the remotes the UI
calls and what the server checks, and the gaps (NOT ASSESSED items with the command to run them).
