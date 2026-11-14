# Explainer video (Bloom)

A one-minute vertical video with Thai narration that a team can watch in chat: what the vulnerability does, whether it reaches us, and the one fix. It is made with [Bloom](https://github.com/daisy-technology/blooms): a `script.md` (narration) and a `scenes.html` (animated picture) become a voiced, captioned MP4.

The video comes **after** the vuln card. It retells the card's verdict, so do steps 1–4 first. A video built before reachability is known will repeat the CVSS score as if it were the app's risk.

## Before you start

- **A Bloom checkout** with `uv sync` done and Playwright's Chromium installed. Find it from `$BLOOM_HOME`, or ask the user where it is. Run Bloom commands from that folder.
- **Read `<bloom>/.claude/skills/bloom-character/SKILL.md`.** It covers the sprite pattern, `steps()` motion, bundling fonts, OmniVoice voices and `peek.py`. This file only adds what a vulnerability video needs on top.
- **A GPU helps.** `uv run bloom remote list`, then `uv run bloom remote check <name>`. If it passes, build with `--voice-on <name>`. Seven lines took 44 s on an RTX 3050 laptop against an estimated 4½ minutes on an M1.

## Keep it anonymous

Alerts usually come from private repos, and videos get forwarded. By default, nothing private goes into the narration, captions, picture or file names:

- leave out: product, repo, org and customer names; file paths, class, table and column names; ticket and alert numbers; private URLs
- say instead: "เซิร์ฟเวอร์ตัวหนึ่งของเรา", "ล็อกตรวจสอบของเรา", "ไลบรารีที่ติดมากับ Express"
- keep: package and framework names, versions, GHSA/CVE ids, CVSS, the advisory's own example values

Put the project **outside any public repo** (for example `~/…/bloom-videos/<pkg>-<ghsa>/`) and build with `--out` into it. Before building, grep the project for every private name you met while tracing (repo, product, files, columns). After building, grep the `.srt` too. Both must come back empty.

## Story: seven scenes, about 55 seconds

Each line is one breath (5–9 s spoken). The picture does the explaining, and the voice says only what the picture can't.

| # | scene | from the card | what the viewer feels |
|---|---|---|---|
| 1 | `hook ~tense` | advisory severity + CVSS | "this is serious". A counter rolls up to the score, siren |
| 2 | `how` | the normal behaviour the bug abuses | "oh, that's how it works". Use an analogy character |
| 3 | `trigger ~tense` | the precondition, in one picture | "that's all it takes?" Show the tiny difference side by side |
| 4 | `surprise ~tense` | the blast radius, as one number | the jolt: quantify it (16.7 million → 4.29 billion addresses, ×256) |
| 5 | `attack` | the mechanism, harmless depiction | "anyone could do this". Show the attacker's input and what the app believes |
| 6 | `us ~calm` | the reachability verdict, with evidence | relief or alarm, honestly. A checklist: ⚠ vulnerable version present · ✓/✗ precondition · ⚠ what it would hit |
| 7 | `fix ~bright +1.5` | fix option 1, plus the safe habit | "easy, do it today". The command typing in a terminal, then the rule |

Scene 6 is where the video earns trust. The hook uses the advisory's score for impact, and scene 6 says what that score means **for us** (R0–R3 in plain words). Never let the video end on the CVSS number.

The safety rules still apply: show the attacker's input and the effect, but no working exploit chain, no real payload, no target.

### Analogies that land

| class | character | picture |
|---|---|---|
| trust / spoofing (proxy headers, auth bypass) | a security guard at a door | a sign that says "I'm from the office", and the guard stamps it |
| injection, template RCE | a cook who follows any note in the order | a note that says "also open the safe" |
| ReDoS | a clerk who must read every form to the end | a form that never ends; the queue grows |
| prototype pollution | someone edits the master copy | every printed copy changes |
| path traversal | a valet given a key labelled `../` | the valet walks into the owner's house |
| SSRF | a mailroom that forwards anything | a letter addressed to the vault inside the building |

Draw the character with `bloom-character` (an original design, small palette, blink and talk loops). Reuse the same sprite in every scene, and give it one reaction where the surprise lands (wide eyes, sweat drop, a shake).

## Narration

- Thai, one speaker, polite particles that match the voice (`ครับ` for a male voice). Male guard: `omnivoice:male, young adult`.
- Every number, version, IP or English identifier goes in `{shown|spoken}`: `{9.1|เก้าจุดหนึ่ง}`, `{2.0.8|สองจุดศูนย์จุดแปด}`, `{/104|ทับหนึ่งร้อยสี่}`, `{X-Forwarded-For|เอ็กซ์ ฟอร์เวิร์ดเด็ด ฟอร์}`. The caption shows the real text and the voice reads the Thai.
- Prefer the precise word. `เชื่อป้าย` (trust the sign) came out as `เชื่อไป` in two takes running. `เชื่อหัวข้อ` (trust the header) is both more accurate and clearer to the ear.

## Picture

Lay out every 1080×1920 scene in three bands, so nothing collides with the captions:

- **content** at y 100–1000: counters, code lines, panels
- **character** at about y 1020–1460
- **caption** at `bottom: 150px` (two lines reach up to about y 1500)

Techniques that worked:

- **Counters and fill-ups** go in `window.bloomSeek(sceneId, t)`, which Bloom calls before every frame. Read the scene length from the section's `--scene-dur` and drive the number from `t / dur`. A 16×16 grid where each cell is one `/8` block makes "every IPv4 address" visible at a glance.
- **Stamps and pop-ins** are timed as fractions of the line: `animation-delay: calc(var(--scene-dur) * .42)`. They stay in sync whichever voice reads it.
- **Sound effects** use `data-sfx` on the element whose first animation is the event: `buzz` for the siren, `whoosh` for a moving request, `thud` for a stamp, `type` for the terminal (with `--n` = number of characters), `chime` for the fix.
- **Code** uses a bundled monospace font (JetBrains Mono, OFL) next to the Thai font (Kanit).

Traps met in the worked example (all caught by previewing):

- `.x:nth-of-type(n)` counts every sibling of the same tag, including the scene's title `div`. One row jumped to the top of the frame. Give rows their own classes.
- A moving card's end position has to clear the box it travels to, or it hides that box's label.
- A stamp laid over a sign hides the sign's text. Put it on the character instead.

Preview twice, mid-scene and at the end, and look at the sheets:

```sh
uv run python .claude/skills/bloom-character/scripts/peek.py <project> --at 3
uv run python .claude/skills/bloom-character/scripts/peek.py <project> --at 5.6
```

## Build and review

```sh
uv run bloom build <project> --voice "omnivoice:male, young adult" --voice-on <remote> --out <project>/out
```

Whisper flags lines it may have misheard, but most flags on a tech video are loanwords it writes in English (`Server`, `Proxy`, `Subnet`). Those are fine. The review page also shortens what it heard. Before retaking anything, transcribe each clip on its own:

```python
from pathlib import Path
from bloom import asr
for w in sorted(Path("<project>/.bloom/voice").glob("omnivoice-*.wav")):
    if "anchor" not in w.name:
        print(asr.transcribe(w))
```

Retake a line (`--retake <scene>`) only when a Thai word is really wrong. If the retake makes the same slip, reword the line instead.

## Hand over

Reply with the MP4 path, its length, and the one-line verdict the video ends on. The video retells the card; it doesn't replace it.

[examples/proxy-addr-GHSA-jqcg-44mw-7w3h-video/](../examples/proxy-addr-GHSA-jqcg-44mw-7w3h-video/) has the worked example: `proxy-addr` IP spoofing (critical, 9.1) on a server that doesn't set `trust proxy`, so it's installed but not reachable today. It has the script and the scenes. Download Kanit and JetBrains Mono into its `fonts/` before building.
