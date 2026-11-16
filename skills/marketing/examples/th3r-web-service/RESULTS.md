# Worked case: a web service on Fastwork

A developer's first Fastwork service: websites and systems, sold in four packages.

| File | What it is |
|---|---|
| [offer.toon](offer.toon) | costs with sources, fee, hours, the four packages, the measured market, the listing rules |
| [listing.md](listing.md) | the listing in Fastwork's field layout, ready to paste |
| [media.banner.json](media.banner.json) | the three listing images in one spec |
| `service-blueprint`, `process-paper`, `showcase-blueprint` `-1920x1080.png` | the images |

## Market (measured 2026-11-16)

40 services from fastwork.co/web-development, 36 with packages. Cheapest package: median 3,225 THB,
75% at or under 7,975. Three-package sellers: medians 4,500 / 14,000 / 20,000. Delivery median 14
days; 2 or 3 revisions most common. 11 of 36 start at 6,900 or more.

## Price

The income and living-cost figures in the offer are round examples; the real case used the seller's
own numbers, which stay private. Package prices are the ones published.

```
$ python3 ../../scripts/offer.py price offer.toon
hours/month 176  fee 17%
break-even 118.7 THB/h net, list at >= 143.0
target     186.9 THB/h net, list at 225.2

เริ่มต้น Landing Page หน้าเดียว             6,900 Project  net    5,727  est  24.0 h  pays  30.6 h at target,  48.2 h before a loss  ok
แนะนำ เว็บธุรกิจและหลังบ้านแก้เองได้       14,900 Project  net   12,367  est  56.0 h  pays  66.2 h at target, 104.2 h before a loss  ok
ระบบ Web App สมาชิกและ Dashboard           26,900 Project  net   22,327  est 100.0 h  pays 119.5 h at target, 188.1 h before a loss  ok
ดูแลรายเดือน เว็บไซต์และระบบ                1,990 Session  net    1,652  est   7.0 h  pays   8.8 h at target,  13.9 h before a loss  ok
```

## Check

`offer.py check offer.toon listing.md`: 8/8 pass (field lengths, units, packages match the offer,
no "·", "+" or dashes, no stack names, every number in the offer). All three images pass `bench.py`.

## What changed on the way

1. The first packages named the stack; the user asked for where it runs and the support instead.
   The check now fails on any stack term.
2. "·" and "+" in package names became a space and "และ" at the user's request; the check fails on
   either.
3. Fastwork's units have no Month, so maintenance is a Session, defined as one month in its
   description.
4. The first service image showed stack names; it was redrawn in buyer words with Thai fonts, and
   banner.py gained role-based fonts for every layout and the `showcase` template.
5. The showcase caption first carried an instruction for the author; it is now a line for buyers.
6. The process image first used the service image's style and a list, so the two looked alike; it
   became the stairs layout on paper, light where the service image is dark.
7. Fastwork's service card showed a 4:3 centre crop and cut off the brand side. The spec now sets
   `content_ratio` [4, 3], and `bench.py --safe-ratio 4:3` checks the crop.
8. The first image was a detailed diagram; a buyer scrolling search needs a hook. The new `hook`
   layout leads the gallery: promise, checklist, price, real work in a browser frame.
9. The listing file in the user's notes folder was overwritten with an old copy by an open editor;
   it was regenerated and checked again.
