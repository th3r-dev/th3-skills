# Listing reference

## Fastwork service form (seen 2026-11-16)

| Field | Limit / options | What goes in |
|---|---|---|
| Choose media for this service | images, from posts or uploads; the service page gallery shows the **first image as a square (1:1) centre crop** and the others as 4:3 | the hook first (page `"content_ratio": [1, 1]`), then service, process, work samples (spec `"content_ratio": [4, 3]`); upload 1920 x 1080 |
| Service name | one line | what is sold and the main promise, in the buyer's words |
| Describe your service | 2,000 characters | who it is for, where it runs, what every package includes, the steps, what is billed separately, the first step |
| Price + unit | THB; Not specified, Project, Hour, Day, Session | the cheapest project package, unit Project |
| Link to post | an existing post | a post that shows real work (a making-of post works) |
| Add tags to your service | tags | buyer search words, no stack names |

## Fastwork add-package form

| Field | Limit / options | What goes in |
|---|---|---|
| Package name | one line | tier word and what it is: "เริ่มต้น Landing Page หน้าเดียว" |
| Description (optional) | 5,000 characters | included items, where it runs, support, delivery days, revisions, what the client prepares, what is billed separately |
| Price + unit | THB; Not specified, Project, Hour, Day, Session | Project for builds; Session for monthly care, with "1 Session เท่ากับ 1 เดือน" written in the description, since there is no Month |

## listing.md layout

`offer.py check` reads this exact shape:

````markdown
**Service name**

```
<name>
```

**Describe your service** (<n>/2,000)

```
<description>
```

**Price:** `6900` THB, unit **Project**

**Add tags to your service:** <tag>, <tag>

### Package 1

**Package name**

```
<name>
```

**Description** (<n>/5,000)

```
<description>
```

**Price:** `6900` THB, unit **Project**
````

## Rules

- No tech-stack names in any pasted field; the offer's `avoid_terms` lists them and the check
  fails on any match.
- No "·", "+", en or em dashes in pasted fields (`forbidden_symbols` in the offer).
- Every multi-digit number in the pasted text also appears in the offer, so prices, days and
  support periods can't drift from what was calculated.
- External links and contact details stay out of descriptions; marketplaces commonly restrict them
  (Fiverr's package rules do; Fastwork's policy was not checked). Work samples go in media and the
  linked post.
- Support periods and the maintenance hours come out of each package's hour budget; `offer.py price`
  must still pass with them included.
