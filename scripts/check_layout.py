#!/usr/bin/env python3
"""Check the skills/ bucket layout. Run from the repo root: python3 scripts/check_layout.py [--selftest]

- skills/shipped/<name>/SKILL.md is exactly the plugin.json "skills" list, and each is linked in README.md;
- skills/{in-progress,personal,deprecated}/ never appear in plugin.json or README.md;
- no tracked text file still names a flat skills/<name> path;
- every relative markdown link under skills/ resolves.
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

BUCKETS = ("shipped", "in-progress", "personal", "deprecated")
LINK = re.compile(r"\]\(([^)\s]+)\)")
TEXT = {".md", ".py", ".yml", ".yaml", ".json", ".sh", ".toml", ".mjs", ".js", ""}


def tracked(root):
    out = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True, check=True).stdout
    return [root / f for f in out.split("\n") if f]


def check(root):
    root = Path(root)
    errs = []
    shipped = sorted(p.parent.name for p in (root / "skills/shipped").glob("*/SKILL.md"))
    manifest = json.loads((root / ".claude-plugin/plugin.json").read_text())
    listed = sorted(Path(s).name for s in manifest.get("skills", []))
    if listed != shipped:
        errs.append(f"plugin.json skills {listed} != skills/shipped {shipped}")
    for s in manifest.get("skills", []):
        if not s.startswith("./skills/shipped/"):
            errs.append(f"plugin.json lists a non-shipped path: {s}")
    readme = (root / "README.md").read_text()
    for name in shipped:
        if f"skills/shipped/{name}/" not in readme:
            errs.append(f"README.md has no link to skills/shipped/{name}/")
    for b in BUCKETS[1:]:
        if f"skills/{b}/" in readme:
            errs.append(f"README.md links into skills/{b}/")

    all_skills = {p.parent.name for b in BUCKETS for p in (root / "skills" / b).glob("*/SKILL.md")}
    flat = re.compile(r"(?<![\w.\-/])skills/(" + "|".join(map(re.escape, sorted(all_skills))) + r")(?=/)") if all_skills else None
    for f in tracked(root):
        if f.suffix not in TEXT or not f.is_file():
            continue
        try:
            text = f.read_text()
        except UnicodeDecodeError:
            continue
        rel = f.relative_to(root)
        if flat:
            for m in flat.finditer(text):
                errs.append(f"{rel}: flat path skills/{m.group(1)}/ (missing bucket)")
        if f.suffix == ".md" and rel.parts[0] == "skills" and "template" not in f.name.lower():  # templates link the output's files
            body = re.sub(r"```.*?```|`[^`\n]*`", "", text, flags=re.S)
            for target in LINK.findall(body):
                if re.match(r"[a-z]+:|#|/|<", target):
                    continue
                path = target.split("#")[0].split("?")[0]
                if path and not (f.parent / path).exists():
                    errs.append(f"{rel}: broken link {target}")
    return errs


def selftest():
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        for b, n in (("shipped", "alpha"), ("in-progress", "beta")):
            (r / "skills" / b / n).mkdir(parents=True)
            (r / "skills" / b / n / "SKILL.md").write_text(f"# {n}\n[ok](SKILL.md)\n")
        (r / ".claude-plugin").mkdir()
        (r / ".claude-plugin/plugin.json").write_text(json.dumps({"skills": ["./skills/shipped/alpha"]}))
        (r / "README.md").write_text("[alpha](skills/shipped/alpha/SKILL.md)\n")
        subprocess.run(["git", "init", "-q"], cwd=r, check=True)
        subprocess.run(["git", "add", "-A"], cwd=r, check=True)
        assert check(r) == [], check(r)
        (r / "README.md").write_text("[alpha](skills/shipped/alpha/SKILL.md) [beta](skills/in-progress/beta/SKILL.md) skills/alpha/x\n")
        (r / "skills/shipped/alpha/SKILL.md").write_text("[gone](missing.md) `[code](ignored.md)`\n")
        (r / ".claude-plugin/plugin.json").write_text(json.dumps({"skills": ["./skills/in-progress/beta"]}))
        errs = "\n".join(check(r))
        for want in ("README.md links into skills/in-progress/", "flat path skills/alpha/", "broken link missing.md",
                     "plugin.json skills", "non-shipped path"):
            assert want in errs, (want, errs)
        assert "ignored.md" not in errs
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
        sys.exit(0)
    errors = check(Path.cwd())
    print("\n".join(errors) or "layout ok")
    sys.exit(1 if errors else 0)
