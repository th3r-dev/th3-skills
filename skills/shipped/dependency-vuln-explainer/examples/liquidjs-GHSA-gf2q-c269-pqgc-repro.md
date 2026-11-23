# Live sandbox repro — GHSA-gf2q-c269-pqgc

Step 7 of the skill, run for real against the benchmark advisory. A confirm-reachable PoC built around the vulnerable package, run in a throwaway `--network none` container, with a **benign sink**: a marker file we planted, read back through the vulnerability. No OS command, no network, no sensitive file. The runnable harness lives in the session scratchpad only — per the skill rule, a working exploit chain is not committed to a repo; the public advisory carries the full gadget.

## What the PoC does

1. Feeds a crafted **template** to LiquidJS (the attacker-controlled input the advisory needs).
2. `1|valueOf` returns the engine's own internal render context (the CWE-94 root cause).
3. Through the documented gadget, the template reaches the engine's file loader and makes it **open a path the template chose** — not the app.
4. The sink is benign: it reads back a marker file we planted containing `Hello World, Exploit work!!!`. The same run is repeated on the patched version as a control.

## Steps actually run

### 1. Build the container image

The Dockerfile installs only the vulnerable package, runs as non-root, and plants a benign marker file as the exfil target.

```dockerfile
FROM node:22-slim
RUN useradd -m poc
USER poc
WORKDIR /home/poc/app
COPY --chown=poc package.json poc.mjs ./
ARG V=10.21.0
RUN npm install --omit=dev --ignore-scripts liquidjs@${V}
RUN echo 'Hello World, Exploit work!!!' > /home/poc/app/marker.txt
CMD ["node", "poc.mjs"]
```

`package.json` is minimal (`{"name":"liquidjs-poc","private":true,"type":"module"}`).

Build for each version:

```sh
podman build --build-arg V=10.21.0 -t vuln-poc-10.21.0 "$POC"
podman build --build-arg V=10.26.0 -t vuln-poc-10.26.0 "$POC"
```

### 2. The harness (`poc.mjs`)

Three checks, each independent. The template expressions come from the public advisory's documented gadget chain — described here at mechanism level, not as copy-paste payload:

| Check | What it does | Pass = vulnerable |
|-------|-------------|-------------------|
| **A — root cause** | Renders `{{ 1 \| valueOf }}` and inspects the return. On a vulnerable build the filter hands back the engine's live render context object (`r.liquid…`). On a patched build it returns a harmless primitive. | Output contains `liquid` |
| **B — file sink** | Walks from the leaked context to the engine's `parseFile` method and asks it to open a path that does not exist (`NO_SUCH_FILE`). If the engine tries, it throws `ENOENT` — proof the template controlled which file the engine opened. | `ENOENT` thrown |
| **C — exfil** | Same as B, but points at the planted `marker.txt`. If the engine opens it, the template reads back the bytes `Hello World, Exploit work!!!`. | Marker bytes returned |

The harness prints a tagged line for each check and a final `SINK-REACHED` or `blocked` verdict.

### 3. Run in sandbox

Both versions run with identical lockdown flags:

```sh
podman run --rm \
  --network none \
  --read-only --tmpfs /tmp:size=16m \
  --user poc \
  --cpus 1 --memory 256m --pids-limit 128 \
  --cap-drop ALL --security-opt no-new-privileges \
  --name vuln-poc-run vuln-poc-10.21.0
```

(Repeat with `vuln-poc-10.26.0` for the patched control.)

### 4. Output

**Vulnerable — liquidjs 10.21.0:**

```
[poc] liquidjs version: 10.21.0
[poc] A root cause   1|valueOf exposes engine internals: YES
[poc] B file sink    engine opened attacker-named path: YES (ENOENT from engine loader)
[poc] C exfil        engine read the template-chosen file (no error); its bytes:
[poc] >>> Hello World, Exploit work!!!
[poc] SINK-REACHED on 10.21.0
```

**Patched — liquidjs 10.26.0:**

```
[poc] liquidjs version: 10.26.0
[poc] A root cause   1|valueOf exposes engine internals: NO (neutralized)
[poc] B file sink    engine opened attacker-named path: no
[poc] C exfil        blocked on 10.26.0 — vulnerability not reachable
```

### 5. Cleanup

```sh
podman rmi vuln-poc-10.21.0 vuln-poc-10.26.0
```

## Reading the result

- **A** — on 10.21.0, `1|valueOf` hands template code the live engine object (`r.liquid…`). On 10.26.0 it returns nothing useful. That single difference is the fix.
- **B** — the honest, engine-sourced proof: on 10.21.0 the engine threw `ENOENT` trying to open the template-named path `/home/poc/app/NO_SUCH_FILE`. The app never asked for that file — the **template** did. On 10.26.0 no open is attempted.
- **C** — pointed at a file that exists (our planted marker), the vulnerable engine opens and reads it; the bytes `Hello World, Exploit work!!!` come back. Benign target by choice; a real attacker names a secret instead, or pivots the same gadget to the `Function` constructor for full RCE (that final hop is in the advisory, not reproduced here).

## What it changes for the verdict

Nothing — and that is the point. The bug is **real and critical in isolation** (confirmed firing on 10.21.0), yet Honey-Pot is still **R1: not loaded**, because the app never calls LiquidJS at all (see the [card](liquidjs-GHSA-gf2q-c269-pqgc.md)). The repro proves the package is dangerous; the reachability trace proves this app is one `import` away from exposure, not currently exposed. Fix stays recommended, priority stays low.

## Fix verification (the command that proves it after applying option 1 or 3)

```sh
npm ls --package-lock-only liquidjs     # option 1 → empty ; option 3 → 10.26.0
```
