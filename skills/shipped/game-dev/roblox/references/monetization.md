# Monetization: earning Robux every day, fairly

How a Roblox game earns, which levers pay daily, and the rules that keep it fair to a young
audience. The ethics come from [design-lens](../../design-lens/SKILL.md#white-hat--black-hat-audit);
this file is the platform side. Every API name here was read from create.roblox.com on 2026-11-24.
Roblox changes weekly, so read the class page again before writing the code.

## The gate (check every item before it ships)

1. **Never random for Robux.** No paid eggs, crates, spins or mystery boxes. The player sees
   exactly what they get before paying.
2. **Never pressure.** No countdown offers, no "only N left", no pop-ups. The shop opens when the
   player opens it. If a prompt was declined, it doesn't come back in the same session.
3. **Never a board number.** Nothing paid moves a leaderboard, a rank or a competitive stat.
4. **Fair waits only** (below). A wait is tuned for fun before the shop exists, and it is never
   made longer to sell the skip.
5. **A free route to every effect.** Every boost can also be earned in play. Paid cosmetics have
   earnable cousins.
6. **Nobody named.** The game never announces who bought what to the server.

## Fair speed-ups

Selling time is allowed when the time was fair to begin with:

- Set the free pace in playtests **before** any price exists, and write it in config with the
  date. A pace change after launch needs a reason from play data, not from sales.
- The first session is never slowed: no wait in the first 15 minutes can be skipped for Robux.
- A skip shows its price and exactly what it saves ("Finish now: 49 R$, saves 2 h") next to the
  timer. It doesn't appear as an offer anywhere else.
- Skips and boosts never touch board numbers, and boosts have a daily cap per player.
- Show the free path beside the paid one: the timer keeps running, and the reward is the same.

## The levers

| Lever | What it is | Pays | Notes |
|---|---|---|---|
| Game Pass | one-time purchase: a cosmetic pack, a convenience (auto-collect, a bigger bag) | once per player | `MarketplaceService:UserOwnsGamePassAsync` on join; cache the answer; grant in `PromptGamePassPurchaseFinished` on the server |
| Developer Product | repeatable: a boost, a skip, a server event, a cosmetic | every purchase | the daily earner; granted only in `ProcessReceipt` (below) |
| Subscription | a monthly perk (a daily bonus, a cosmetic set) | monthly | read the experience-subscriptions docs for the current API before building |
| Rewarded video ad | the player chooses to watch an ad for a reward | per completed view | eligibility below |
| Server event | a product that starts an event **everyone** in the server enjoys | every purchase | the buyer isn't named; a cooldown per server |
| Creator Rewards | Roblox pays for engaged spenders and new players you bring | daily | no code; design for it (below) |

### ProcessReceipt, the one rule that loses money if wrong

`MarketplaceService.ProcessReceipt` is called on the server for every Developer Product purchase,
and again until it returns `Enum.ProductPurchaseDecision.PurchaseGranted`. So:

- Grant, **save** the player's data with the `PurchaseId`, and only then return `PurchaseGranted`.
- A `PurchaseId` already saved means it was granted before: return `PurchaseGranted` again
  without granting twice.
- If the player left or the save failed, return `NotProcessedYet`. Roblox retries later.
- One callback per server, set once. It handles every product, including ad rewards
  (`receiptInfo.ProductPurchaseChannel == Enum.ProductPurchaseChannel.AdReward`).

### Rewarded video ads

From create.roblox.com/docs/production/promotion/rewarded-video-ads:

- **Eligibility:** a public, unrestricted experience with an approved content questionnaire and
  an average of at least 2,000 unique visitors a month; the publisher is 13+, ID-verified, with
  two-step verification, in good standing. A new game can't use them until it has the visitors,
  so they're a launch-plus-one lever.
- **Flow:** the client checks `AdService:GetAdAvailabilityNowAsync(Enum.AdFormat.RewardedVideo)`
  (one `IsAvailable` covers one play). The server makes the reward with
  `AdService:CreateAdRewardFromDevProductId(id)` and shows it with
  `AdService:ShowRewardedVideoAdAsync(player, reward, placementId?)`. The grant arrives through
  `ProcessReceipt`.
- **Rules:** the reward is a Developer Product that the shop also sells, never Robux and never a
  random item. It must not unbalance the economy. Before each ad, say what the reward is and what
  the player has to do ("Watch an ad for 2× coins for 10 minutes").
- **Where:** where the player is already waiting or choosing: after a session summary, beside a
  timer, as a daily-reward doubler. Never in the middle of play and never required.

### Creator Rewards (replaced Premium Payouts)

Engagement-Based Payouts ended in 2025. Creator Rewards (create.roblox.com/docs/creator-rewards)
pays for two things:

- **Daily Engagement:** 5 Robux per *active spender* who plays 10+ minutes, if yours is one of
  their first three experiences that day. Design for it: a reason to open the game early in the
  day (a daily goal, a fresh event) and a first 10 minutes worth staying for.
- **Audience Expansion:** a 35% share of the first $100 of qualifying purchases by new or returning
  players you bring in through share links. It needs an ID-verified account, and the game must
  average 100+ daily users over 60 days. Design for it: a share link with a reward for both
  friends.

## What earns every day

Robux every day means a reason to come back every day, plus something worth buying again:

| Daily driver | Lever it feeds |
|---|---|
| A daily goal and a login reward (free) | Creator Rewards daily engagement |
| The goal ladder's next tier, visible but not yet reached | skips and boosts (Developer Products) |
| A server event on a timer, or bought by one player for everyone | server events |
| A timer the player is waiting on | rewarded ads, fair skips |
| New tiers or a zone every week | everything above; the update is the reason to return |

## Prices

Restated from the reference repo's pricing notes. These are norms, not rules:

- Floor of 25 R$. Below that the item isn't worth the work.
- Odd prices read cheaper: 49, 99, 199, 499.
- Ladder: 25 to 49 for a single cosmetic or a short boost, 99 to 199 for a standard pass,
  399 to 999 for a large pack. Price a pass by how long it stays useful.
- Bundles show their value honestly ("3 for the price of 2"). A "best value" tag goes on the
  one that is.
- Roblox keeps 30% of passes and products sold in an experience.

## DevEx math

The standard rate is **$0.0038 per earned Robux** (since 2025-09-05; Robux earned before that
date cash out at $0.0035 first). A higher rate applies to qualifying spend by US players aged
18+. Cash-out needs 30,000 earned Robux, age 13+, a verified email and tax forms. The earned
figure is after Roblox's share.

```text
daily Robux earned ≈ daily users × share who buy × average price × 0.7
monthly USD        ≈ daily Robux earned × 30 × 0.0038
```

The share who buy is often quoted at 1 to 5% of daily users. Treat it as **rough** until your own
analytics say otherwise.

## Before launch

- Test every pass and product in Studio (test purchases don't charge), including a failed save
  and a player who leaves mid-purchase.
- `PolicyService:GetPolicyInfoForPlayerAsync` says what a player's region allows (ads, paid
  random items, external links). Check it before showing an ad or a social link.
- Selling models or packages on the Creator Store needs distribution rights on the account.
  Check before planning on it; one game's plan failed on "User is not authorized to distribute
  packages".

Sources: Roblox docs (rewarded video ads, AdService, MarketplaceService, Creator Rewards, DevEx,
the US 18+ rate), read 2026-11-24;
[brockmartin/roblox-game-skill](https://github.com/brockmartin/roblox-game-skill/tree/3f38c3f6cce34d325b7e504bb7f39f41051d4c47)
`references/monetization-systems.md` and `workflows/monetization-audit.md` (no licence, so
restated, not copied). Its Premium Payouts section and its $0.0035 rate are out of date.
