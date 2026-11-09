# th3-skills

Skills for Claude Code, installable via [`npx skills`](https://dev.to/baltz/sharing-skills-with-npx-2nbc).

## Install as a Claude Code plugin (all skills)

```
/plugin install th3-skills --marketplace th3r-dev/th3-skills
```

## Install a skill

```
npx skills@latest add th3r-dev/th3-skills --skill poc-spec-driven-builder
```

## Skills

- [`poc-spec-driven-builder`](skills/poc-spec-driven-builder/SKILL.md) — builds a proof of concept end-to-end: research → SRS → test matrix → implementation → verification, run autonomously without pausing for clarification.
- [`thai-mock-naming`](skills/thai-mock-naming/README.md) — Thai mock names that are unmistakably fake, greppable in a database, and still exercise real Thai text handling. Replaces สมชาย ใจดี / สมหญิง พอใจ with marker names like ทดสอบ นามสมมุติ. Ships a generator and a linter.
- [`doc-style-builder`](skills/doc-style-builder/SKILL.md) — documents any work product (API, deploy, system, release) in one house style: seven document skeletons, a TH Sarabun theme with change highlighting, and Markdown → PDF + DOCX in one command.
- [`pdf-operations`](skills/pdf-operations/SKILL.md) — PDF manipulation with `pdf-lib`: merging multiple PDFs into one, splitting a PDF into pages, extracting/reordering pages, rotating pages, and drawing overlays. Migrated from `pdf-kit-skills`.

- [`podman-disk-reclaim`](skills/podman-disk-reclaim/SKILL.md) — reclaims Podman disk space on Windows, macOS and Linux: prunes unused images, runs `fstrim` in the Podman machine, and on Windows compacts the WSL `ext4.vhdx` so the space actually returns to the host. One stdlib-only Python script, `--dry-run` first.

- [`prompt-cache-kit`](skills/prompt-cache-kit/SKILL.md) — makes dynamic agents cheaper by keeping prompt prefixes byte-identical so the prompt cache hits. A uv-run script builds a fingerprinted project outline locally, writes agent briefs that put that outline first and the task last, and reports per-agent cache hit rate from the local session logs.

- [`dependency-vuln-explainer`](skills/dependency-vuln-explainer/SKILL.md) — explains a vulnerable dependency (Dependabot alert, GHSA/CVE, `npm audit`) so a person can see how the attack works and whether it reaches their app. Traces the lockfile path, rates real reachability instead of repeating the CVSS score, ranks fix options, draws the exploit and dependency path with `diagram-design`, and leaves a vuln card other agents can act on. Optional sandboxed repro via `poc-spec-driven-builder` in a network-less container. Optional anonymized one-minute explainer video with Bloom (Thai narration, pixel character, captions). Benchmarked on a real liquidjs RCE alert (CVSS 10.0 → low real priority).

- [`design-core`](skills/design-core/SKILL.md) — the design principles the other design skills share: composition (Figma's graphic design principles), interface writing (Apple HIG Writing), and an interface quality baseline drawn from [open-design](https://github.com/nexu-io/open-design) (states, accessibility, motion, AI tells), a staged working order from brief to handoff, a taste pass adapted from [taste-skill](https://github.com/Leonxlnx/taste-skill) (classify the kind, copy before layout, deliberate choices, gate-style checks), defaults for products with no design system, and a 0–10 review table. It defers to the product's own design system.

- [`design-flow`](skills/design-flow/README.md) — puts real screens into Figma with their flowchart beside them. It captures live pages or HTML as editable auto-layout layers, binds every value to the file's variables and text styles (and asks before adding missing ones), fills placeholder slots or versions changed screens on the canvas, and builds flows from the file's own flow kit. Runs through a containerized [figma-mcp-bridge](https://github.com/gethopp/figma-mcp-bridge), so Figma's API and MCP call limits don't apply. Python tools, guide in its README.

- [`qa`](skills/qa/SKILL.md) — QA toolkit for web portals, one skill with four sub-skills and their scripts: `answer-review` (review a meeting Q&A sheet through business · program · data · operation lenses and write one Remark per row), `export-evidence` (walk every CSV / Excel / PDF export button on a signed-in Chrome, verify the files, build the .xlsx evidence report), `excel-import` (design, preflight, run and verify a test set for an Excel-template import, with a pluggable adapter for the importer) and `ticket-report` (post a QA / retest result on a Jira ticket in the team format with screenshots inline). Generalised from a Thai-government integration project.

- [`devops`](skills/devops/SKILL.md) — DevOps toolkit, one skill with three sub-skills and their scripts: `change` (infra work on real machines in a fixed order — triage, read-only investigation, evidence, approved plan, stepwise change, same-command verification, blameless review — closed with a before / steps / after / rollback report; `jssh.py` jump-host ssh from an ini, `snapshot_haproxy.sh` for the config a container is *really* running), `release-scope` (what ships in the next release vs what prod runs, by ticket keys across every repo plus the issue boards, written as the PM list and checked against the customer message) and `network-diagram` (one draw.io file with a board per version → clean one-page PDF; rebuild a drawio from a final PDF; benchmark text / layout / pixels). Generalised from a Thai-government integration project.

## Related

- [kien-thai (เขียนไทย)](https://github.com/chakrit/kien-thai) by chakrit — a skill for writing Thai that Thai readers find easy to read. Pairs with `thai-mock-naming`: that skill handles the Thai prose in free-text fields, this one handles the identity fields.

## License

MIT — see [LICENSE](LICENSE).
