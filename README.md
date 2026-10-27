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

## Related

- [kien-thai (เขียนไทย)](https://github.com/chakrit/kien-thai) by chakrit — a skill for writing Thai that Thai readers find easy to read. Pairs with `thai-mock-naming`: that skill handles the Thai prose in free-text fields, this one handles the identity fields.

## License

MIT — see [LICENSE](LICENSE).
