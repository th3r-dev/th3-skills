# design-flow: guide

How to use this skill to put real screens into Figma, keep them on the file's design system,
and draw each screen's flowchart next to it. The first half is for the person setting it up.
The second half is the runbook an agent follows.

## What it does

| You have | You get in Figma |
|---|---|
| A live web page (public or behind a login) | editable layers in the slot where the screen belongs |
| A local HTML file | the same |
| A screenshot or image | a rebuild over the image from your components, in auto layout |
| A screen with no flow | a flowchart beside it, built by cloning your file's own flow shapes |
| A screen that changed | the new version in place, a large "New version" card, the old version at 50% opacity beside it |

Every imported layer is then bound to your variables and text styles. If a value has no token,
the skill reports it and asks before adding anything.

## Part 1: setup (once per machine)

You need Figma **desktop** (the browser version can't run development plugins), Python 3.10+,
[uv](https://docs.astral.sh/uv/), Google Chrome, Podman or Docker, and Node (only for
`--to layers`, to bundle html-figma once).

### 1. Start the bridge container

The skill talks to Figma through [figma-mcp-bridge](https://github.com/gethopp/figma-mcp-bridge)
(MIT), a Figma plugin plus a local server. It doesn't use Figma's REST API or the official Figma
MCP, so their per-plan call limits don't apply.

```bash
S=<path to this skill>/scripts
python3 $S/bridge.py up --work ~/figma-work --run-script
```

This builds the image on first run and starts a container that:
- listens on `127.0.0.1:1994` for the plugin (loopback only)
- mounts `~/figma-work` at `/work`, where page captures for `import_html_layers` go
- enables `run_script` (Plugin API JavaScript in the open file). Leave out `--run-script` for read-only use.

`python3 $S/bridge.py status` shows it, `logs` shows the last lines, and `down` removes it.

### 2. Register it as an MCP server

```bash
claude mcp add figma-bridge -s user -- python3 $S/bridge.py mcp
```

### 3. Add the plugin to Figma desktop

1. Download `figma-mcp-bridge-v<version>.zip` from the bridge's
   [releases](https://github.com/gethopp/figma-mcp-bridge/releases) and unzip it somewhere
   permanent.
2. Open your design file in Figma desktop.
3. Go to **Plugins › Development › Import plugin from manifest…** and pick `plugin/manifest.json`.
4. Go to **Plugins › Development › Figma MCP Bridge** and keep its small window open while you work.

Check it: `python3 $S/bridge.py call list_files` should print your file. `[]` means the
plugin isn't running in that file.

### 4. (Optional) a signed-in session for capturing an app

```bash
uv run $S/capture.py login --url https://app.example.com/login --state ~/.cache/figma-capture/app.json
```

Chrome opens and you sign in. The session is saved with mode 600 and never printed.

## Part 2: everyday use

Ask the agent in plain words, for example:

- "Analyze this Figma page and list the screens that have no flow"
- "Capture https://app.example.com/reports/daily into the `Role A ▸ Reports ▸ Daily` slot"
- "Replace every *not started* placeholder under App B with the live pages"
- "Add the flow for `Screen 1.1`: check permission, show list or alert"
- "The settings page changed, put the new version in with a version card"

The agent follows the runbook below and tells you what it bound, what it placed, and what
stayed unmatched.

### How the canvas is read

Work reads **top to bottom**. A very wide section label sits at the top of each product area,
with role and menu labels under it and screens under those. New screens go into the x-range of
their section, under their menu. The skill never drops them at the page edge.

### When it stops and asks you

- A color, size, or text style on the page has no matching token.
- The file has no components for something the page uses (buttons, inputs, tables…).
- A version card needs a token or text style that doesn't exist.
- The plugin isn't connected, or the target is a live screen and you didn't say to change it.

## Part 3: runbook for agents

Read `SKILL.md` first. It holds the rules. This is the order of operations.

```
0  bridge.py status → up if needed;  bridge.py call list_files → plugin connected?
   load design-core; run every script from the work folder (paths outside it are refused)
1  inventory: variables, text/paint/effect styles, components (run_script or search_design_system)
   + design-core: each screen's job in one sentence, the product's terms and capitalization
   → anything missing that the task needs: STOP, list it, ask
2  capture
     live page / HTML :  capture.py url|html|jobs --to layers --out <work>/captures [--state FILE]
                         import_html_layers source=captures/<file>.json  (relative to /work)
                         figma_js.py images --page P --root <imported frame> --images captures/<file>.images.json
                           → run_script  (raster images; capture.py splits them out of the layer JSON)
                         figma_js.py autolayout --page P --root <imported frame>  → run_script
     (official MCP only) capture.py ... --to figma --capture <id from generate_figma_design>
     image            :  upload as locked reference → rebuild with components + createAutoLayout
3  figma_js.py tokenize --page P --root <frame> [--prefer-collection C] [--font-map "Fallback=Real"]
                         → run_script; keep the unmatchedColors / unmatchedText it returns
4  figma_js.py place --page P --capture <frame> --target <placeholder or old screen> --name "Role ▸ Menu ▸ Screen"
                         → run_script with allowRemove: true
     placeholder → replaced;  real design → version card + old screen at 0.5 opacity (nothing deleted)
     "blocked" → missing card token/style: ask
5  components: figma_js.py swap --page P --component <set id> --roots <frames> --name-match '^Button$'
                         → run_script with allowRemove: true. One component at a time, screenshot after each.
     match = same layer structure + height + radius + fill token + vector geometry, so icons never get swapped
     for a different icon. Text is carried over; other per-instance art (photos, charts) is not, so leave those
     layers as frames
6  flow (UI → flow → UI): figma_js.py flow-kit once
         → capture EVERY result state (capture.py jobs with steps/selector): dialog open, success shown, page opened,
           back on the list. No state screen = no flow; never end a chain on an `end` text box instead
         → figma_js.py state (overlay or page), each state right after its source in the same row
         → write flow.json from the app source; every anchor's chain ends on a screen in `screens`
         → figma_js.py flow (refuses specs that never reach a screen) → run (allowRemove)
         no room in the section? ask, then figma_js.py make-room. Lettered markers only if the user asks (markers: true)
         → flow_review.py flows/  (a line ending on a marker or never reaching a screen caps at 5)
6b graph: design_graph.py extract/build → dupes (next components), impact (before token edits), gaps
7  one screenshot per row; check every line lands on a picture; score it with design-core's review table;
   fix the top findings, at most three rounds, stop
8  report: placed screens, state screens, flow_review pass count and mean, design-core scores,
   counts bound/styled, unmatched values, anything blocked
```

Without the MCP tools loaded in the session, every bridge tool is reachable from the shell:

```bash
python3 bridge.py call get_document '{}'
python3 bridge.py run code.js --allow-remove        # run_script with the file's code
python3 bridge.py hold &                            # keep a leader session open (stable plugin link)
```

### Rules that are easy to break

- Use `await figma.setCurrentPageAsync(page)` once per script. Assigning `figma.currentPage` fails.
- Colors are 0–1, not 0–255. Fills and strokes are read-only arrays, so build new arrays.
- Load a font before touching text. Captured pages often use a fallback family (`… Fallback`),
  so map it with `--font-map`.
- `capture.py` blocks writes to the target site by default. Keep it that way for production apps.
- Never copy real labels, node IDs, or screenshots from a user's file into anything public.
  Use the mock labels in `references/flow-conventions.md`.

## Files

```
SKILL.md                     rules + workflows (agent entry point)
README.md                    this guide
references/flow-conventions.md   flow kit conventions, read/build snippets, mock labels
scripts/bridge.py            container lifecycle, MCP stdio, call/run/hold
scripts/capture.py           page/HTML → Figma (layers JSON or Figma capture)
scripts/figma_js.py          renders Plugin API scripts: tokenize, place, autolayout, swap, flow-kit, flow, state, make-room, extract
scripts/design_graph.py      design knowledge graph: build, dupes, impact, tour, gaps
scripts/js/*.js              the templates figma_js.py fills
scripts/container/Containerfile   bridge server image
```

Every script has `--self-test`.

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Plugin keeps disconnecting | Figma closes dev plugins when you switch files. Run `bridge.py ensure` (macOS) to relaunch it |
| `list_files` prints `[]` | The plugin isn't running in the file. Start it (Plugins › Development) and keep its window open |
| `could not start figma-bridge … port 1994` | Another bridge (for example `npx` on the host) holds the port. Stop it, then `bridge.py up` |
| `Cannot connect to Podman` | `podman machine start` |
| `run_script` refused | Container started without `--run-script`: `bridge.py up --run-script` |
| Script rejected for `.remove()` | Pass `--allow-remove` (bridge.py run) / `allowRemove: true` |
| Text renders in the wrong font after capture | Map the fallback family: `tokenize --font-map "X Fallback=X"` |
| Official Figma MCP says "tool call limit" | Use the bridge for everything. Only `--to figma` capture needs the official MCP |
| `createPage`: "Starter plan only comes with 3 pages" | Put components in a section on an existing page (for example the one holding your helper components) |
| Styled text loses its style after tokenize | The file has one style per size and weight. A Medium or Bold text can't keep a Regular style, so tokenize reports it. Add weight styles (with the user's yes) |
| Swapped cards all show the same icon | Older `swap` ignored vector geometry. The current one includes it. To repair, detach those instances and put the right icon back from a fresh capture |
| Imported SVG icons are black or empty | html-figma writes broken SVG markup and leaves `currentColor`. `capture.py` repairs both when it saves |
| A text with two sizes in one line stays unstyled | `tokenize` styles each run of a mixed text. Rerun it |
| Captured page shows the login screen | The session expired: run `capture.py login` again |
