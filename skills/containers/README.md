<p align="center"><img src="assets/hero.svg" width="100%" alt="containers: Podman ate the disk. Get it back. Sub-skill podman: Windows, macOS and Linux, one stdlib script."></p>

# containers

Container runtime toolkit, one skill with sub-skills per runtime.

| Sub-skill | What it does |
|---|---|
| [`podman`](podman/SKILL.md) | Reclaims Podman disk space on Windows, macOS and Linux: prunes unused images, runs `fstrim` in the Podman machine, and on Windows compacts the WSL `ext4.vhdx` so the space returns to the host |

The agent's instructions are in [SKILL.md](SKILL.md).

```
npx skills@latest add th3r-dev/th3-skills --skill containers
```
