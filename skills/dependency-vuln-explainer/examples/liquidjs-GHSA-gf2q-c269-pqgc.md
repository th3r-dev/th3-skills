# GHSA-gf2q-c269-pqgc · liquidjs@10.21.0 · R1 installed, not loaded

Worked example: a liquidjs Dependabot alert on a NestJS API, anonymized here as **Honey-Pot**. Shows how a **critical (CVSS 10.0)** advisory becomes a **low** real-app priority once reachability is traced — and why it still gets fixed. The app identity, source paths and DB names below are generic stand-ins; the technique is what transfers.

| Field | Value |
|---|---|
| Advisory | GHSA-gf2q-c269-pqgc / CVE-2026-45618 · LiquidJS is vulnerable to Remote Code Execution |
| Package | npm:liquidjs |
| Installed | 10.21.0 in `package-lock.json` |
| Vulnerable range | `< 10.26.0` · first patched **10.26.0** |
| Advisory severity | critical · CVSS 10.0 `AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H` · EPSS ~0.8% |
| CWE | CWE-94 Improper Control of Generation of Code |
| Repo / ref | Honey-Pot (NestJS API, anonymized) |
| Verdict | **R1 installed, not loaded** |
| App severity | **low** — fix anyway |

## Path
```
honey-pot@0.0.1
  └─ @nestjs-modules/mailer@2.0.2   (direct, runtime)
       └─ liquidjs@10.21.0          (transitive, optional peer of the mailer)
```
`liquidjs` is an **optional peer** of `@nestjs-modules/mailer` — the mailer supports Liquid, Handlebars, EJS, Pug and MJML as template engines and installs them all, but loads only the one the app configures.

## Preconditions (from the advisory)
- The attacker must control **template text** that LiquidJS parses/renders. A crafted template reaches `valueOf` → the `this` scope, climbs through the parser's internals to the `Function` constructor, and runs arbitrary code. Data passed *into* a trusted template is not enough; the template source itself must be attacker-controlled.

## Reachability evidence
- `npm ls --package-lock-only liquidjs` → `@nestjs-modules/mailer@2.0.2 └── liquidjs@10.21.0`. Installed, one copy, in range.
- `grep -rnE "nestjs-modules/mailer|liquidjs|LiquidAdapter|MailerModule" --include='*.ts' src` → **no match.** The mailer module is never imported; no `MailerModule.forRoot`, no Liquid adapter configured.
- The mail service → mail is sent straight through `@sendgrid/mail` (`sgMail.send`). The app does not use `@nestjs-modules/mailer` at all.
- The dependency is dead weight pulled in by a mailer package the app chose not to wire up. The vulnerable code is never on a code path.

## Attacker input
None. There is no request field, DB column or file whose contents become a LiquidJS template, because LiquidJS is never invoked.

## Mechanism (plain language)
1. The app renders a Liquid template whose **text** comes from an untrusted source.
2. A LiquidJS filter expression reaches the engine's internal render context instead of a plain value.
3. From that context the template walks to the JavaScript `Function` constructor.
4. `Function` lets the template build and run code → RCE.

Full PoC is in the advisory: https://github.com/harttle/liquidjs/security/advisories/GHSA-gf2q-c269-pqgc — not reproduced here.

## Neighbourhood
The app renders email/document HTML with **Handlebars** (`Handlebars.compile(template.html)` in several services), and the template text comes from an email-template DB table. Checked:
- Handlebars installed version is **4.7.8** — above the known Handlebars RCE/prototype-pollution advisories. Not vulnerable.
- That template column is written only by a seed script (`INSERT`), not by any request handler. So even the Handlebars path has no attacker-controlled template source today. Worth a note to the team: if an admin "edit email template" screen is ever added, that becomes attacker-controlled template text and the same bug class would apply to whichever engine renders it.

## Fix options (ranked)
1. **Remove the mailer** — `npm remove @nestjs-modules/mailer`. The app uses SendGrid directly, so this drops liquidjs, ejs, pug, mjml and more. Files: `package.json`, lockfile. Risk: none if nothing imports the mailer (confirmed by grep). Proof: `npm ls --package-lock-only liquidjs` → empty. **Recommended.**
2. **Upgrade the mailer** to a release whose peer range requires liquidjs ≥ 10.26.0 (check `@nestjs-modules/mailer` releases). Keeps the dep; only worth it if the app plans to use the mailer.
3. **Force the patched version** — add `"overrides": { "liquidjs": "^10.26.0" }` to `package.json`, then `npm install`. Smallest change that closes the alert while keeping the mailer. Risk: low (patch release, same major). Proof: `npm ls --package-lock-only liquidjs` → `10.26.0`.

Chosen: awaiting user. Default recommendation is option 1.

## Open questions
- Does any roadmap item add a user- or admin-editable email/document template? If yes, revisit the Handlebars path (neighbourhood note) before it ships.

## Sources
- https://github.com/harttle/liquidjs/security/advisories/GHSA-gf2q-c269-pqgc
- https://github.com/harttle/liquidjs/releases/tag/v10.26.0
