# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.2"]
# ///
"""Run the GitHub workflow steps for skills locally, the same commands CI runs.

    uv run --script scripts/ci.py              # workflows touched since dev (layout always runs)
    uv run --script scripts/ci.py qa game-dev  # named workflows
    uv run --script scripts/ci.py --all

Exit 1 if any step fails; prints the tail of each failure.
"""
import os
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github/workflows"


def load(name):
    d = yaml.safe_load((WF / f"{name}.yml").read_text())
    on = d.get(True) or d.get("on") or {}  # YAML 1.1 reads the key `on` as True
    paths = (on.get("pull_request") or {}).get("paths", [])
    wd = ROOT / d.get("defaults", {}).get("run", {}).get("working-directory", ".")
    steps = [s for job in d["jobs"].values() for s in job["steps"] if "run" in s]
    return paths, wd, steps


def touched(base="dev"):
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True).stdout.splitlines()
    files = (git("diff", "--name-only", f"{base}...HEAD") + git("diff", "--name-only", "HEAD")
             + git("ls-files", "--others", "--exclude-standard"))
    names = {"layout"}
    for w in WF.glob("*.yml"):
        paths, _, _ = load(w.stem)
        prefixes = [p.split("*")[0] for p in paths]
        if any(f.startswith(pre) for f in files for pre in prefixes if pre):
            names.add(w.stem)
    return sorted(names)


def run(names):
    failed = []
    # CI starts clean: rebuild each skill's .venv, and don't leak this script's own uv environment
    env = {k: v for k, v in os.environ.items() if k not in ("VIRTUAL_ENV", "UV_PROJECT_ENVIRONMENT")}
    env.update(PYTHONDONTWRITEBYTECODE="1", UV_VENV_CLEAR="1")
    for name in names:
        _, wd, steps = load(name)
        for st in steps:
            cwd = ROOT / st["working-directory"] if "working-directory" in st else wd
            r = subprocess.run(["bash", "-ec", st["run"]], cwd=cwd, capture_output=True, text=True, env=env)
            print(f"{'ok  ' if r.returncode == 0 else 'FAIL'} {name:18s} {st.get('name', st['run'][:50])}")
            if r.returncode:
                failed.append(name)
                print((r.stdout + r.stderr)[-1500:])
    return failed


if __name__ == "__main__":
    args = sys.argv[1:]
    names = sorted(w.stem for w in WF.glob("*.yml")) if "--all" in args else (args or touched())
    sys.exit(1 if run(names) else 0)
