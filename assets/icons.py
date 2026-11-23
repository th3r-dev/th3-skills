"""One icon per skill, drawn to match its name: the single source for every icon.svg and hero.

Each icon is line art in a 120 x 120 box, ink on whatever is behind it. `icon(name, x, y, size)`
places it inside a hero; running this file writes skills/<name>/assets/icon.svg with a yellow
tile behind the art, so it reads on GitHub's light and dark themes alike.

Run: uv run assets/icons.py   (stdlib only)
"""
import os

Y, INK = "#FFD60A", "#0A0A0A"
SW = 5  # stroke width in icon units


def _s(w=SW, fill="none"):
    return f'fill="{fill}" stroke="{INK}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'


def _f():
    return f'fill="{INK}"'


ART = {
    # a gamepad: d-pad left, two buttons right
    "game-dev": (
        f'<path d="M34 36H86C100 36 110 48 112 64L114 84C115 94 106 100 98 94L84 80H36L22 94C14 100 5 94 6 84L8 64C10 48 20 36 34 36Z" {_s(fill=Y)}/>'
        f'<path d="M34 50V70M24 60H44" {_s(7)}/>'
        f'<circle cx="80" cy="54" r="6" {_f()}/><circle cx="92" cy="66" r="6" {_f()}/>'),
    # a shipping container on a crane sling
    "containers": (
        f'<path d="M30 34L60 12L90 34" {_s()}/>'
        f'<rect x="10" y="34" width="100" height="58" rx="3" {_s(fill=Y)}/>'
        + "".join(f'<path d="M{x} 44V82" {_s(3.5)}/>' for x in range(24, 100, 12))
        + "".join(f'<rect x="{x}" y="{y}" width="10" height="10" {_f()}/>' for x in (10, 100) for y in (34, 82))
        + f'<path d="M14 104H106" {_s(4)}/>'),
    # a frame on its thirds, one focal point
    "design": (
        f'<rect x="12" y="16" width="96" height="88" rx="4" {_s()}/>'
        + "".join(f'<path d="{d}" {_s(2.5)} opacity=".45"/>' for d in ("M44 16V104", "M76 16V104", "M12 45H108", "M12 75H108"))
        + f'<rect x="66" y="35" width="20" height="20" {_f()}/>'),
    # a server rack: three units, lights and vents
    "devops": (
        "".join(f'<rect x="14" y="{y}" width="92" height="26" rx="3" {_s()}/>'
                f'<path d="M26 {y + 13}H58" {_s(3.5)}/>'
                f'<circle cx="84" cy="{y + 13}" r="4" {_f()}/><circle cx="96" cy="{y + 13}" r="4" {_f()}/>'
                for y in (14, 47, 80))),
    # a code window shipping a tagged release
    "software-engineer": (
        f'<rect x="8" y="14" width="104" height="76" rx="6" {_s()}/>'
        f'<path d="M8 32H112" {_s(4)}/>'
        + "".join(f'<circle cx="{x}" cy="23" r="3.5" {_f()}/>' for x in (20, 32, 44))
        + f'<path d="M40 48L28 61L40 74M80 48L92 61L80 74M66 44L54 78" {_s(5)}/>'
        f'<path d="M58 96H96L110 106L96 116H58Z" {_s(4, fill=Y)}/><circle cx="66" cy="106" r="3.5" {_f()}/>'),
    # a clipboard of ticked checks
    "qa": (
        f'<rect x="20" y="18" width="80" height="94" rx="6" {_s()}/>'
        f'<rect x="42" y="8" width="36" height="18" rx="4" {_f()}/>'
        + "".join(f'<path d="M32 {y}l6 6l11-12" {_s(4.5)}/><path d="M60 {y}H88" {_s(4)}/>' for y in (48, 70, 92))),
    # a styled page with a folded corner
    "documentation": (
        f'<path d="M24 8H78L100 30V112H24Z" {_s()}/>'
        f'<path d="M78 8V30H100" {_s()}/>'
        f'<rect x="36" y="42" width="44" height="10" {_f()}/>'
        f'<path d="M36 66H88M36 80H76M36 94H84" {_s(4)}/>'
        f'<rect x="30" y="74" width="4" height="12" {_f()}/>'),
    # a lab flask: prove the idea
    "poc-spec-driven-builder": (
        f'<path d="M50 12H70M54 12V44L24 100Q21 108 30 108H90Q99 108 96 100L66 44V12" {_s()}/>'
        f'<path d="M38 76H82L93 99Q95 104 89 104H31Q25 104 27 99Z" {_f()}/>'
        f'<circle cx="56" cy="62" r="4" {_f()}/><circle cx="66" cy="54" r="3" {_f()}/>'),
    # a cache: stacked store, the shared prefix on top (agent runs that hit it)
    "agent-kit": (
        f'<path d="M20 28V92Q20 104 60 104Q100 104 100 92V28" {_s()}/>'
        f'<path d="M20 50Q20 62 60 62Q100 62 100 50M20 72Q20 84 60 84Q100 84 100 72" {_s(4)}/>'
        f'<ellipse cx="60" cy="28" rx="40" ry="12" {_f()}/>'),
    # an ID card with a VOID stamp
    "thai-mock-naming": (
        f'<rect x="6" y="24" width="108" height="72" rx="8" {_s()}/>'
        f'<rect x="16" y="38" width="30" height="40" rx="3" {_s(4)}/>'
        f'<circle cx="31" cy="52" r="6" {_f()}/><path d="M21 74Q31 60 41 74Z" {_f()}/>'
        f'<path d="M56 44H100M56 58H88" {_s(4)}/>'
        f'<circle cx="90" cy="78" r="15" {_s(4)} stroke-dasharray="5 5"/>'
        f'<path d="M80 88L100 68" {_s(4)}/>'),
    # a price tag on its string, a baht mark punched through it
    "marketing": (
        f'<path d="M58 14H100V56L56 100Q50 106 44 100L14 70Q8 64 14 58Z" {_s()}/>'
        f'<circle cx="84" cy="30" r="7" {_f()}/>'
        f'<path d="M84 30Q100 4 112 14" {_s(3.5)}/>'
        f'<path d="M44 46V80M44 46H56Q64 46 64 54Q64 62 56 62H44M44 62H58Q66 62 66 71Q66 80 58 80H44M50 40V86" {_s(4)}/>'),
    # a post card: the cover image on top, a title and two lines under it
    "social-media": (
        f'<rect x="14" y="10" width="92" height="100" rx="8" {_s()}/>'
        f'<rect x="24" y="20" width="72" height="42" rx="4" {_f()}/>'
        f'<path d="M30 56L48 38L60 50L68 42L90 56Z" fill="{Y}"/>'
        f'<path d="M24 76H96" {_s(5)}/><path d="M24 90H76" {_s(3.5)}/><path d="M24 100H64" {_s(3.5)}/>'),
    # a dependency tree with the vulnerable leaf traced from the root
    "dependency-vuln-explainer": (
        f'<path d="M60 20L30 60M60 20L90 60M30 60L18 100M90 60L90 100" {_s(3.5)} opacity=".5"/>'
        f'<path d="M60 20L30 60L48 100" {_s(6)}/>'
        + "".join(f'<circle cx="{x}" cy="{y}" r="8" {_s(4, fill=Y)}/>' for x, y in ((60, 20), (30, 60), (90, 60), (18, 100), (90, 100)))
        + f'<circle cx="48" cy="100" r="13" {_f()}/><path d="M48 93V101M48 106V107" stroke="{Y}" stroke-width="4" stroke-linecap="round"/>'),
}


def icon(name, x, y, size, cls=""):
    """The skill's art placed at (x, y), `size` px square, for use inside a hero."""
    c = f' class="{cls}"' if cls else ""
    return f'<g{c} transform="translate({x} {y}) scale({size / 120:.4f})">{ART[name]}</g>'


def icon_svg(name):
    """A standalone icon file: the art on a yellow tile, readable on light and dark pages."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="120" height="120" viewBox="-12 -12 144 144" '
            f'role="img" aria-label="{name} icon"><title>{name}</title>'
            f'<rect x="-12" y="-12" width="144" height="144" rx="28" fill="{Y}"/>{ART[name]}</svg>')


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    have = {d for d in os.listdir(os.path.join(root, "skills")) if os.path.isfile(os.path.join(root, "skills", d, "SKILL.md"))}
    assert have == set(ART), f"skills without an icon: {sorted(have - set(ART))}; icons without a skill: {sorted(set(ART) - have)}"
    for name in sorted(ART):
        d = os.path.join(root, "skills", name, "assets")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "icon.svg"), "w", encoding="utf-8") as fh:
            fh.write(icon_svg(name))
    print(f"{len(ART)} icons written")
