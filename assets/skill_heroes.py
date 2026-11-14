"""Build one animated hero per skill: skills/<name>/assets/hero.svg.

Left: the skill's name, its claim, and how to install it. Right: the steps it really runs (from its
SKILL.md); a marker walks down them, each step inverts while it runs and keeps a tick when done,
then the output appears. The still (reduced motion) shows every step ticked and the output.
design-core is not here: it has its own hero (skills/design-core/assets/hero.py).

Run: ~/.venvs/diagram-design/bin/python assets/skill_heroes.py [name ...]   (needs fonttools + brotli)
"""
import importlib.util, os, sys
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
_spec = importlib.util.spec_from_file_location(
    "dc_hero", os.path.join(ROOT, "skills", "design-core", "assets", "hero.py"))
dc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dc)
Doc, embed_fonts, width, Y, INK, INK2, INK3 = dc.Doc, dc.embed_fonts, dc.width, dc.Y, dc.INK, dc.INK2, dc.INK3

W, H = 1280, 640

# copy first. name: (claim, sub, steps [(step, detail)], output)
SKILLS = {
    "poc-spec-driven-builder": (
        ["Proves an idea works,", "tests before code."],
        ["Research, a spec and a full test matrix", "come before any implementation."],
        [("Research", "best practice for the stack"), ("Spec", "an SRS with success criteria"),
         ("Ticket", "issue filed, branch cut"), ("Tests", "a matrix for every requirement"),
         ("Build", "until the tests pass"), ("Ship", "report, push, open the PR")],
        ["a PR that proves it, and what", "a full build would still need"]),
    "design-flow": (
        ["Screens in Figma,", "their flow beside them."],
        ["A developer can build each page", "from one look."],
        [("Inventory", "the file's tokens, styles, components"), ("Capture", "live page to auto-layout layers"),
         ("Tokenize", "every value bound to a variable"), ("States", "each result screen captured"),
         ("Flow", "drawn from the app source"), ("Review", "no crossings, every line lands")],
        ["a screen and its flow per page,", "an implementation checklist"]),
    "prompt-cache-kit": (
        ["Cheaper agent runs,", "same prefix every time."],
        ["Agent briefs share one byte-stable", "outline, so the prompt cache hits."],
        [("Build", "a fingerprinted outline, locally"), ("Brief", "outline first, task last"),
         ("Fan out", "forks, subagents, workflows"), ("Stats", "hit rate per agent, cold ones named")],
        ["one total hit rate,", "and which agents missed"]),
    "thai-mock-naming": (
        ["Thai mock names,", "fake on sight."],
        ["Real Thai text for the code to handle,", "and one grep finds every row."],
        [("Generate", "marker names from approved tokens"), ("Seed", "fixtures, samples, demo users"),
         ("Lint", "real-looking names flagged on edit"), ("Find", "grep the marker, clean up")],
        ["no test row mistaken", "for a real person"]),
    "dependency-vuln-explainer": (
        ["Does this CVE", "actually reach you?"],
        ["How the attack works, and whether", "your code ever calls it."],
        [("Intake", "alert, GHSA, CVE or audit finding"), ("Locate", "the lockfile path that pulls it in"),
         ("Reach", "does your code call the sink?"), ("Fix", "options ranked by effort and risk"),
         ("Explain", "attack and path as diagrams"), ("Card", "a vuln card agents can act on")],
        ["CVSS 10.0, real priority low:", "not reachable from your app"]),
    "devops": (
        ["Infra changes,", "in a fixed order."],
        ["Three sub-skills: change,", "release-scope, network-diagram."],
        [("Triage", "what broke, and its SEV level"), ("Investigate", "read-only first"),
         ("Plan", "steps and rollback, approved"), ("Change", "one step at a time"),
         ("Verify", "the same command as before"), ("Report", "before, steps, after, rollback")],
        ["a change record with", "its SEV level and timeline"]),
    "qa": (
        ["QA evidence that", "holds up in review."],
        ["Four sub-skills for web portals,", "one team format."],
        [("answer-review", "four lenses, one remark per row"), ("export-evidence", "every export clicked, verified"),
         ("excel-import", "validate, submit, check the DB"), ("ticket-report", "the result on the Jira ticket")],
        ["an evidence .xlsx and", "a report on the ticket"]),
    "doc-style-builder": (
        ["Any work product,", "documented one way."],
        ["Seven skeletons, one house theme,", "PDF + DOCX from one Markdown file."],
        [("Gather", "the facts from the work"), ("Ground", "checked against the source"),
         ("Summarize", "into the right skeleton"), ("Confirm", "with the user"),
         ("Build", "Markdown to PDF + DOCX")],
        ["a matching PDF and DOCX,", "changes highlighted"]),
    "pdf-operations": (
        ["PDF work through", "the existing pipeline."],
        ["Merge, split, reorder, rotate and", "overlay with pdf-lib."],
        [("Merge", "many PDFs into one"), ("Split", "one PDF into its pages"),
         ("Reorder", "rotate, delete, duplicate"), ("Overlay", "text and shape stamps")],
        ["one clean PDF,", "no new pipeline written"]),
    "containers": (
        ["Podman ate the disk.", "Get it back."],
        ["Sub-skill podman: Windows, macOS", "and Linux, one stdlib script."],
        [("Measure", "what takes the space, first"), ("Confirm", "before anything is deleted"),
         ("Prune", "unused images"), ("Trim", "fstrim in the Podman machine"),
         ("Compact", "the WSL disk, on Windows")],
        ["the space is back on", "the host, and measured"]),
}


def fit(s, maxw, key, sizes=(72, 64, 56, 50, 44, 40, 36, 32)):
    for z in sizes:
        if width(s, z, key) <= maxw:
            return z
    raise ValueError(f"{s!r} does not fit {maxw}px")


def build(name):
    claim, sub, steps, result = SKILLS[name]
    out = []
    n = len(steps)
    # The left column and the step rows enter once. Only the run loops: it starts after the entrance
    # (delay) and every looping part shares one cycle, so nothing drifts from loop to loop.
    ENTER, LEAD, STEP, HOLD, MOVE = 2.0, 0.4, 1.2, 2.8, 0.25
    cycle = LEAD + n * STEP + HOLD
    end = cycle - 0.4
    d = Doc(cycle, delay=ENTER)

    # left column
    L, COL = 64, 520
    nz = fit(name, COL, "arc-800")
    out.append(d.t(L, 214, name, nz, INK, 800, cls=d.enter(0.1), maxw=COL))
    for i, s in enumerate(claim):
        out.append(d.t(L, 278 + i * 40, s, 32, INK, 800, cls=d.enter(0.3 + i * 0.1), maxw=COL))
    for i, s in enumerate(sub):
        out.append(d.t(L, 378 + i * 30, s, 21, INK2, 500, cls=d.enter(0.6 + i * 0.1), maxw=COL))
    out.append(d.t(L, 600, f"npx skills@latest add th3r-dev/th3-skills --skill {name}", 14, INK3, 500,
                   mono=True, maxw=W - 2 * L))

    # right: the steps
    X0, X1 = 660, 1216
    RX, RW, RH, GAP = X0 + 40, X1 - X0 - 40, 46, 12
    block = n * (RH + GAP) + 10 + 96
    top = round((560 - block) / 2) + 16
    ry = lambda i: top + i * (RH + GAP)
    rail = X0 + 12
    oy = ry(n) + 10

    out.append(f'<path d="M{rail} {ry(0) + RH / 2}V{oy + 48}" stroke="{INK}" stroke-width="2" opacity=".25"/>')
    for i, (step, detail) in enumerate(steps):
        y = ry(i)
        t = LEAD + i * STEP
        cy = y + RH / 2
        row = (f'<rect x="{RX}" y="{y}" width="{RW}" height="{RH}" fill="none" stroke="{INK}" stroke-width="1.5"/>'
               + d.t(RX + 16, cy + 6, step, 16, INK, 800, mono=True)
               + d.t(RX + 182, cy + 6, detail, 16, INK2, 500, maxw=RW - 182 - 44))
        out.append(f'<g class="{d.enter(0.9 + i * 0.08)}">{row}</g>')
        # running: inverted from the moment the marker lands until it leaves
        run = d.window(t, t + STEP, base=0, rise=0, fin=0.12, fout=MOVE)
        out.append(f'<g class="{run}"><rect x="{RX}" y="{y}" width="{RW}" height="{RH}" fill="{INK}"/>'
                   + d.t(RX + 16, cy + 6, step, 16, Y, 800, mono=True)
                   + d.t(RX + 182, cy + 6, detail, 16, Y, 500) + "</g>")
        # done: tick, kept to the end of the cycle
        tick = d.show(t + STEP - MOVE, end, rise=0, fin=0.2)
        out.append(f'<path class="{tick}" d="M{RX + RW - 30} {cy}l6 6l11-12" stroke="{INK}" stroke-width="3" fill="none"/>')
        out.append(f'<circle cx="{rail}" cy="{cy}" r="5" fill="{Y}" stroke="{INK}" stroke-width="2"/>')

    # output
    oc = d.show(LEAD + n * STEP, end)
    out.append(f'<g class="{oc}"><rect x="{RX}" y="{oy}" width="{RW}" height="96" fill="{INK}"/>'
               + d.t(RX + 16, oy + 26, "out", 13, Y, 500, mono=True)
               + "".join(d.t(RX + 16, oy + 56 + k * 24, s, 17, Y, 800, mono=True, maxw=RW - 32)
                         for k, s in enumerate(result)) + "</g>")

    # the marker walking down the rail; its still position is the output
    stops = [ry(i) + RH / 2 for i in range(n)] + [oy + 48]
    final = stops[-1]
    p = d.p
    kf = f"0%{{transform:translateY({stops[0] - final:.0f}px);opacity:0}}"
    kf += f"{p(LEAD)}%{{transform:translateY({stops[0] - final:.0f}px);opacity:1}}"
    for i in range(1, n + 1):
        t = LEAD + i * STEP
        kf += f"{p(t - MOVE)}%{{transform:translateY({stops[i - 1] - final:.0f}px);opacity:1}}"
        kf += f"{p(t)}%{{transform:translateY({stops[i] - final:.0f}px);opacity:1}}"
    kf += f"{p(end)}%{{transform:none;opacity:1}}100%{{transform:none;opacity:0}}"
    walk = d.loop("walk", kf)
    out.append(f'<circle class="{walk}" cx="{rail}" cy="{final}" r="9" fill="{INK}"/>')

    label = (f"{name}: {' '.join(claim)} {' '.join(sub)} Steps: "
             + "; ".join(f"{s}, {dt}" for s, dt in steps) + f". Output: {' '.join(result)}.")
    css = (embed_fonts(d.text)
           + ".a{font-family:A,'Helvetica Neue',Arial,sans-serif}"
           + ".m{font-family:M,ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre}"
           + "".join(d.css)
           + "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
           f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
           f'<style>{css}</style><rect width="{W}" height="{H}" fill="{Y}"/>{"".join(out)}</svg>')
    return svg, cycle


if __name__ == "__main__":
    for name in sys.argv[1:] or SKILLS:
        svg, cycle = build(name)
        d = os.path.join(ROOT, "skills", name, "assets")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "hero.svg"), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"{name}: {len(svg) / 1024:.0f} KB, {cycle:.1f} s loop")
