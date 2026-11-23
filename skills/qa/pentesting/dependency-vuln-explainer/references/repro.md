# Sandboxed repro

A repro answers one question: **does the vulnerable code behave as the verdict says in this app's usage pattern?** It is a test, not an attack. The sink is a harmless sentinel. Run it only when the user asks to see a real example, and only in a disposable, network-less container.

This is step 7 of the skill. Use the `poc-spec-driven-builder` process (research → SRS → test matrix → build → verify) but keep the scope tiny and skip its ticket/branch/PR tail unless the user wants a PoC repo.

## What the PoC contains

A minimal harness that reproduces the app's **calling pattern**, not the app:

- The one vulnerable package, pinned to the installed version (from the card's Path row).
- The smallest wrapper that calls it the way the app's parent does (e.g. render a template through the same adapter, parse input through the same function).
- One test that feeds the attacker-controlled input the advisory needs and checks for a **sentinel**: a file like `/tmp/poc/PWNED` or a stdout line `POC-SINK-REACHED`. No real command, no exfiltration, no reverse shell.

## Two spec shapes

**Confirm-reachable (expected R3).** The test asserts the sentinel *appears* when the input flows the way the app allows it. If it appears, the verdict holds and the fix is urgent. SRS purpose: "prove `<pkg>` executes attacker-controlled `<input>` as reached from `<app parent>`."

**Confirm-safe (expected R0/R1/R2).** The test asserts the sentinel *does not* appear, because the app never loads the package / never passes attacker input / pins a patched version. Build the same harness, then show the app's guard (no import, patched range, trusted-only input) blocks it. SRS purpose: "prove `<pkg>` is not reachable in `<app>` because `<guard>`." This is the common, boring, good result.

Either way the test matrix has at least: the trigger case, the patched-version case (bump the pin to the first patched version, same input, sentinel must not appear), and the guard case that reflects the real verdict.

## Container recipe

Lightweight, throwaway, no network. Podman or Docker; the flags are the same. Write the harness in the scratchpad, mount it read-only, let the run write only to a tmpfs.

```sh
# Node example — swap the base image + install step per ecosystem.
POC=/private/tmp/.../scratchpad/poc        # harness dir (host)
cat > "$POC/Dockerfile" <<'EOF'
FROM node:22-slim
RUN useradd -m poc
USER poc
WORKDIR /home/poc/app
COPY --chown=poc package.json poc.test.mjs ./
RUN npm install --omit=dev --ignore-scripts    # pinned vulnerable version, no lifecycle scripts
CMD ["node", "--test"]
EOF

podman build -t vuln-poc "$POC"

podman run --rm \
  --network none \
  --read-only --tmpfs /tmp:size=16m \
  --user poc \
  --cpus 1 --memory 256m --pids-limit 128 \
  --cap-drop ALL --security-opt no-new-privileges \
  --name vuln-poc-run vuln-poc
```

Caps per ecosystem: use `python:3.12-slim` + `pip install --no-deps <pkg>==<ver>`, `golang:1-alpine` + `go test`, etc. Always `--ignore-scripts` / `--no-deps` so installing the package can't run arbitrary setup code. Always `--network none`.

## Reporting the run

Add to the card's Mechanism or Open-questions section, and tell the user in plain words:

- The exact pinned version and the one input shape tested (described, not pasted as a weaponized payload).
- Result: `SINK-REACHED` or `blocked`, and which guard blocked it.
- The patched-version control result (must flip to blocked — this proves the fix works).
- Then destroy the image: `podman rmi vuln-poc`.

If any sandbox flag can't be enforced on the host, do **not** run the PoC. Report the missing control and offer the source-only verdict instead — same rule as the security-audit skill's "if every control cannot be enforced, do not execute target code."
