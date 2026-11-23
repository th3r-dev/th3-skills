# Pricing reference

Evidence levels: **platform** (the marketplace's own help pages), **measured** (read from live
pages), **practitioner** (blogs and guides; rules of thumb, often from firms selling something).

## Models

| Model | Fits | Note |
|---|---|---|
| Hourly | unclear scope, ongoing support | safest to start; caps income as you get faster (practitioner) |
| Fixed per project | defined, repeatable work | switch once you can estimate similar jobs; 50% upfront, 50% on delivery is common (practitioner) |
| Value-based | measurable client outcome | highest ceiling; needs proof of results; 10 to 30% of the client's gain is a quoted starting range, unverified (practitioner) |
| Hybrid | fixed build plus ongoing care | fixed packages for the build, a monthly package for maintenance (practitioner) |

Sources: [GetPaidFirst](https://getpaidfirst.ai/blog/hourly-vs-project-based-pricing),
[DEV: The Hourly Trap](https://dev.to/frankdotdev/the-hourly-trap-why-freelance-developers-must-switch-to-value-based-pricing-in-2026-1afa),
[Damongo](https://damongo.com/how-to-price-your-freelance-work-2026-complete-guide/).

## Cost-based floor

Whatever the model, the price must cover the hours at cost. The offer TOON holds:

- **Living costs** (`kind: living`): what the month costs to live, utilities included. Break-even
  covers these.
- **Business costs** (`kind: business`): equipment replacement (price / months of life), software,
  learning, security training. Both break-even and target cover these.
- **Target income:** the income the work must replace (the current salary is a fair default).
- **Working hours:** days per month × hours per day.
- **Platform fee:** listed price = net price / (1 - fee).

Published averages for Thailand found while building the example (2026):

| Item | Average | Source |
|---|---|---|
| Household electricity | 905 THB/month (Bangkok area 1,345) | NSO energy survey 2567, via [The Bangkok Insight](https://www.thebangkokinsight.com/news/business/1618261/) |
| Home fibre internet | 399 to 1,299 THB/month, most plans 415 to 799 | provider plans, [droidsans 2569](https://droidsans.com/compare-promotion-internet-fiber-packages-2026/) |
| Water use (PWA areas) | 23 to 26 m³ per meter per month | Bangkok Bank PWA reports; no baht average found |
| Laptop life | 3 to 5 years | [HP](https://www.hp.com/in-en/shop/tech-takes/post/average-computer-lifespan); straight-line depreciation |
| Mainstream laptop price | 17,000 to 19,000 THB median | buying guides, practitioner |
| Fastwork commission | 17% most cited; 10% promotion Feb to Apr 2568 | [thaiseoboard](https://www.thaiseoboard.com/index.php/topic,404145.0.html), [The Standard](https://thestandard.co/fastwork-commission-discount/); confirm in the seller dashboard |

## Packages and tiers

- **Three tiers** (good, better, best) are the standard; Fiverr allows up to three and recommends at
  least three price points (platform, [Fiverr](https://help.fiverr.com/hc/en-us/articles/360010559138)).
  Fastwork sellers list one to nine (measured).
- **Tier levers** seen on Fastwork: scope (pages, features), delivery days, revisions, support
  period (measured).
- **Anchoring and decoy:** the top tier makes the middle look reasonable; a decoy is an option
  dominated by its neighbour. Keep every tier honest: each one adds real work over the one below, no
  fake tier and no phantom "was" price (practitioner,
  [The Decoy Effect](https://freeacademy.ai/lessons/framing-choice-architecture)).
- **Names say what differs:** simple and descriptive (platform, Fiverr), in the buyer's words.
- **Ongoing package:** maintenance per month keeps income coming after delivery; extra hours at the
  listed target rate.

## When to change the price

- After the first few strong reviews, raise prices (practitioner).
- When real jobs show the hour estimates were off, update `hours` in the offer and rerun
  `offer.py price`.
- When the platform fee changes, update `fee`.
