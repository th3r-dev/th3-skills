---
name: game-dev-idea-grill
description: >-
  Turn a game idea into a first game that can ship: grill the idea one question at a time, check
  what already works on the platform and how players use it, put the original idea on top of a
  proven loop as one twist, cap the scope (few systems, a long ladder of goals and tiers), and set
  dated milestones for development, alpha, beta and launch. Use WHENEVER the work starts from an
  idea, or the idea is growing: "game idea", "I want to make a game about", "first game", "game
  scope", "too big", "too many features", "what's popular on Roblox", "what games make Robux",
  "is this idea good", "market research", "milestones", "roadmap", "release date", "alpha",
  "beta", "ไอเดียเกม", "ขอบเขตเกม", "เกมแรก", "แผนงานเกม", "วันปล่อยเกม". Runs before design-lens
  and the game brief.
---

# Idea grill: from idea to a first game that ships

A first game fails for one of two reasons: nobody wants the loop, or the loop never gets finished
because ten systems were started at once. This step guards against both before any code. It
runs in four parts, in order, and ends with a scope the person signs off and dates they chose.

Write everything into `design/idea-grill.md`. The person's own words go in quotes, unedited.

## 1. Grill (one question at a time)

Ask, wait for the answer, then ask the next one. Don't send a form. Push back on every answer that
adds a system ("and also pets, and a town"): write it under **Later** and move on.

1. Who plays, and what do they come for? Name them by what they want, not by age.
2. What is the one verb? Mine, climb, hatch, build, dodge. If there are two, pick the one the
   player does every few seconds.
3. What are the 30 seconds? Do, get, spend, do better.
4. What is a 10-minute session, and where does it end with the player wanting one more go?
5. Why come back tomorrow?
6. What is the one twist, the thing no game in the market check below does?
7. If you had to cut half, what goes first?

Done when every answer fits in two lines and the verb, the 30 seconds and the twist agree.

## 2. Market check: what exists, then how players use it

Look before inventing. Pick 3 to 5 live games in the genre. On Roblox, start from the Charts and
Discover pages and the game pages themselves; tracker sites help with trends. For each, play
it or watch someone play it, then fill one row:

| Game | Core loop (one line) | First minute | What it sells, at what price | How players use it (what they repeat, show off, wait for) | What players complain about |
|---|---|---|---|---|---|

- Complaints come from the game's own comments, its group wall, the DevForum and videos. They are
  the gap the twist can fill.
- Revenue and visit figures from third-party sites conflict with each other; mark them **rough**
  and never plan on them.
- Copy the grammar, not the game. The loop, the genre and the price points are free to use; another
  game's name, characters, art, music and levels never are.

## 3. Fit: a proven frame plus one twist

The original idea sits on top of a loop players already know, as **one** twist. A new player
should recognise the game in five seconds and find the twist in five minutes.

Write it as one line: "*\<proven frame from the table\>*, but *\<the twist\>*." If it takes two
twists to say, cut one and put it in Later.

## 4. Scope budget: few systems, a long ladder

"Compact and simple" means few **systems**. It doesn't mean little to do. Content (tiers, zones,
items) is rows in a config file, cheap to add and cheap to balance. Every system is code, tests
and UI. So keep the systems few and the ladder long:

| Budget for the first game | Cap |
|---|---|
| Core loops | 1 |
| Currencies | 1 soft currency (a second only if the loop can't work without it) |
| Progression ladders | 1, with **many tiers**: 10 to 30 rows of tools, zones or ranks, each one visibly better |
| Maps | 1, split into zones the ladder unlocks |
| Screens | 5 at most: HUD, shop, settings, reward pop, one more |
| Monetization at launch | 1 to 2 Game Passes, 1 to 2 Developer Products (see [monetization](../roblox/references/monetization.md)) |
| Not in the first game | trading, towns or plots, pets, rebirth, a second map, clans, story mode |

### The goal ladder

Players stay for the next goal they can see. Give them three at once:

| Span | Example | What the HUD shows |
|---|---|---|
| Seconds | the next pickup, the next hit | the counter moving, a pop on each one |
| A session | the next tier or zone | progress as X / Y toward it |
| Days | the top tier, the last zone, a title | the ladder with the next rows silhouetted and marked "?" |

A silhouetted tier makes the player curious about what it is. That pull is free and fair, as
long as every tier can be earned in play. Where the ladder gets long, the later tiers are where
a paid speed-up makes sense, under the fair-wait rules in the monetization reference. The first
session is never slowed down.

## 5. Milestones with dates

The person sets the dates; ask for the launch date or the hours per week, then plan backwards.
Without an answer, use the durations below for a solo first game, marked "default".

| Milestone | Default length | Exit: done when |
|---|---|---|
| Prototype | 1 week | the core loop runs with grey boxes and the person played it for 10 minutes |
| Vertical slice | 2 weeks | the first zone plays from join to the first tier up, with real UI; feel checked |
| Alpha (playable) | 2 to 3 weeks | every v1 system is in; friends or a small test group play a private server; the owner's playtest finds no blocker |
| Beta (fun) | 2 weeks | an open test; players come back the next day and play a full session; numbers compared with the benchmarks in Roblox's Creator Analytics |
| Launch (earning) | 1 week | test purchases work end to end; the shop, a pass and a product are live; the thumbnail and icon are done |
| Live | weekly | one update a week: new tiers, a zone or an event, chosen from what the data and comments show |

Each milestone gets a date, the issues in it, and its exit line. A milestone that misses its date
loses scope, not the date: move rows to Later.

## Output

`design/idea-grill.md` with these parts: the grill answers, the market table, the one-line fit,
the scope budget split into **In v1** and **Later**, the goal ladder, and the dated milestones.
The game brief (`design/game-brief.md`, step 3 of [the flow](../SKILL.md#the-flow)) then takes
them over.

**Done when** the person says "scope locked" and every milestone has a date.

## Why the caps

A game built with this skill started from a ten-point vision: a climbable mountain, a town,
pets, rebirth, cloud mini-games, events, taming, mutations, boards and a shop. It passed a
thousand issues and pull requests before its first slice was fun, and the owner's first full playtest found
eighteen defects in one sitting. The loop was good. It was buried under systems that had all
started at once.

Sources: [brockmartin/roblox-game-skill](https://github.com/brockmartin/roblox-game-skill/tree/3f38c3f6cce34d325b7e504bb7f39f41051d4c47)
(`workflows/new-game.md` scope step, `references/game-design-roblox.md` loops and genre notes;
no licence, so restated, not copied).
