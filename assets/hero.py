"""Build the th3-skills README hero: hero.svg next to this file.

Left: every skill with the job it does (complete as a still, so reduced motion loses nothing).
Right: a stage that walks the skills one by one and shows each one's input and output,
while a highlight follows it down the index.

Run: ~/.venvs/diagram-design/bin/python assets/hero.py   (needs fonttools + brotli)
Helpers and fonts come from skills/design-core/assets/hero.py.
"""
import importlib.util, os
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location(
    "dc_hero", os.path.join(HERE, "..", "skills", "design-core", "assets", "hero.py"))
dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dc)
Doc, embed_fonts, Y, INK, INK2, INK3 = dc.Doc, dc.embed_fonts, dc.Y, dc.INK, dc.INK2, dc.INK3

W, H = 1280, 720
SLIDE = 2.8

# copy first: (skill, its job, what goes in, what comes out); lifecycle order
SKILLS = [
    ("poc-spec-driven-builder", "proves an idea, tests first",
     ["“Can tickets sync to a sheet?”"], ["spec, test matrix, build,", "a PR with the proof"]),
    ("design-core", "design rules, scored by a critic",
     ["a screen the author", "scored 9.8"], ["critic: 6.1, fix, re-score,", "9.4: passes the 9.2 bar"]),
    ("design-flow", "Figma screens with their flow",
     ["a live page or its HTML"], ["an editable Figma screen,", "its flowchart beside it"]),
    ("prompt-cache-kit", "cheaper agent runs",
     ["agent briefs that differ", "from the first byte"], ["one identical prefix,", "so the prompt cache hits"]),
    ("thai-mock-naming", "mock names that are fake on sight",
     ["a test user who looks", "like a real person"], ["a marker name: fake on sight,", "one grep finds every row"]),
    ("dependency-vuln-explainer", "does this CVE reach you?",
     ["a Dependabot alert,", "CVSS 10.0"], ["traced through the lockfile:", "not reachable, priority low"]),
    ("qa", "QA evidence and reports",
     ["a Q&A sheet, export buttons,", "an Excel import, a ticket"], ["remarks, an evidence .xlsx,", "a test run, a Jira report"]),
    ("devops", "infra changes with a report",
     ["a change on a real server"], ["plan, approved steps, checks,", "before / after / rollback"]),
    ("doc-style-builder", "docs in one house style",
     ["a Markdown file"], ["PDF + DOCX in the house", "theme, changes highlighted"]),
    ("pdf-operations", "merge, split, rotate, stamp",
     ["three separate PDFs"], ["one PDF, pages reordered,", "rotated and stamped"]),
    ("containers", "wins back Podman disk",
     ["a disk full of old images"], ["pruned, trimmed, the WSL", "disk compacted: space back"]),
]
CYCLE = round(SLIDE * len(SKILLS), 3)


def build():
    d = Doc(CYCLE)
    out = []
    L = 64

    # left: title and the index
    out.extend([
        d.t(L, 112, "th3-skills", 72, INK, 800, maxw=560),
        d.t(L, 156, "Claude Code skills. Each one does a whole job.", 22, INK2, 500, maxw=560),
    ])

    NX, JX, RIGHT = L + 20, L + 270, 628
    row = lambda i: 222 + i * 40
    for i, (name, job, _, _) in enumerate(SKILLS):
        y = row(i)
        out.extend([
            f'<rect x="{L}" y="{y - 11}" width="8" height="8" fill="{INK}"/>',
            d.t(NX, y, name, 15, INK, 800, mono=True, maxw=JX - NX - 14),
            d.t(JX, y, job, 16, INK2, 500, maxw=RIGHT - JX),
        ])
        # the highlight that follows the stage
        hl = d.window(i * SLIDE, (i + 1) * SLIDE, base=1 if i == 0 else 0, rise=0)
        out.append(f'<g class="{hl}"><rect x="{L - 10}" y="{y - 25}" width="{RIGHT - L + 20}" height="36" fill="{INK}"/>'
                   + d.t(NX, y, name, 15, Y, 800, mono=True) + d.t(JX, y, job, 16, Y, 500) + "</g>")

    out.append(d.t(L, 686, "/plugin install th3-skills --marketplace th3r-dev/th3-skills", 14, INK3, 500, mono=True,
                   maxw=RIGHT - L))

    # right: the stage
    X0, X1 = 700, 1216
    SW = X1 - X0
    top = row(0) - 25
    out.append(f'<rect x="{X0}" y="{top}" width="{SW}" height="{row(10) + 11 - top}" fill="none" stroke="{INK}" stroke-width="2"/>')
    PX = X0 + 28
    for i, (name, job, src, res) in enumerate(SKILLS):
        t0 = i * SLIDE
        base = 1 if i == 0 else 0
        part = lambda dt: d.window(t0 + dt, t0 + SLIDE, base=base)
        g = []
        g.append(f'<g class="{part(0)}">' + d.t(PX, top + 64, name, 30, INK, 800, maxw=SW - 56) + "</g>")
        # in
        iy = top + 104
        box = f'<rect x="{PX}" y="{iy}" width="{SW - 56}" height="96" fill="none" stroke="{INK}" stroke-width="1.5"/>'
        txt = d.t(PX + 16, iy + 26, "in", 13, INK3, 500, mono=True)
        txt += "".join(d.t(PX + 16, iy + 56 + k * 24, s, 17, INK, 800, mono=True, maxw=SW - 88) for k, s in enumerate(src))
        g.append(f'<g class="{part(0.1)}">{box}{txt}</g>')
        # arrow
        ax, ay1, ay2 = X0 + SW / 2, iy + 110, iy + 150
        g.append(f'<g class="{part(0.5)}"><path d="M{ax} {ay1}V{ay2 - 2}M{ax - 7} {ay2 - 9}L{ax} {ay2}L{ax + 7} {ay2 - 9}" '
                 f'stroke="{INK}" stroke-width="2.5" fill="none"/></g>')
        # out
        oy = iy + 164
        box = f'<rect x="{PX}" y="{oy}" width="{SW - 56}" height="96" fill="{INK}"/>'
        txt = d.t(PX + 16, oy + 26, "out", 13, Y, 500, mono=True)
        txt += "".join(d.t(PX + 16, oy + 56 + k * 24, s, 17, Y, 800, mono=True, maxw=SW - 88) for k, s in enumerate(res))
        g.append(f'<g class="{part(0.8)}">{box}{txt}</g>')
        out.extend(g)

    # progress ticks under the stage, one per skill
    py = row(10) + 11 - 24
    tw = (SW - 56 - 10 * 6) / 11
    for i in range(len(SKILLS)):
        x = PX + i * (tw + 6)
        out.append(f'<rect x="{x:.1f}" y="{py}" width="{tw:.1f}" height="4" fill="{INK}" opacity=".2"/>')
        on = d.window(i * SLIDE, (i + 1) * SLIDE, base=1 if i == 0 else 0, rise=0)
        out.append(f'<rect class="{on}" x="{x:.1f}" y="{py}" width="{tw:.1f}" height="4" fill="{INK}"/>')

    label = ("th3-skills: Claude Code skills, each doing a whole job. "
             + " ".join(f"{n}: {j}. In: {' '.join(s)}. Out: {' '.join(r)}." for n, j, s, r in SKILLS))
    css = (embed_fonts(d.text)
           + ".a{font-family:A,'Helvetica Neue',Arial,sans-serif}"
           + ".m{font-family:M,ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}"
           + "".join(d.css)
           + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
            f'<style>{css}</style><rect width="{W}" height="{H}" fill="{Y}"/>{"".join(out)}</svg>')


if __name__ == "__main__":
    svg = build()
    path = os.path.join(HERE, "hero.svg")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"{path}: {len(svg) / 1024:.0f} KB, {CYCLE:.1f} s loop")
