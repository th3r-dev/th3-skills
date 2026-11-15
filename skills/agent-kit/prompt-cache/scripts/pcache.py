#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Byte-stable project context for cache-friendly agent briefs, plus cache stats.

  pcache.py build [root]            fingerprint git-tracked files, re-outline only changed ones
  pcache.py brief "<task>" [--role R] [--root DIR]
  pcache.py stats [session_id] [--logs DIR]
  pcache.py --self-test
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CACHE_DIR = ".pcache"
MAX_BYTES = 1_000_000
MAX_LINES_PER_FILE = 40
TOP_LEVEL = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:pub\s+)?(?:async\s+)?"
    r"(?:function|class|interface|type|enum|struct|trait|impl|fn|func|def|module|const|let)\b"
)
HEADING = re.compile(r"^#{1,3} ")

RULES = """## Rules for this agent
- The project context above is a precomputed outline. Trust it; open a file only when you need its body.
- Do not re-summarise the repo in your reply. Report only what the task asks for.
"""


def outline(path: str, data: bytes) -> list[str]:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return []
    if path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except SyntaxError:
            tree = None
        if tree is not None:
            out = []
            for node in tree.body:
                if isinstance(node, ast.Import):
                    out.append("import " + ", ".join(a.name for a in node.names))
                elif isinstance(node, ast.ImportFrom):
                    out.append(f"from {node.module or '.'} import " + ", ".join(a.name for a in node.names))
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.append(f"def {node.name}({', '.join(a.arg for a in node.args.args)})")
                elif isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    out.append(f"class {node.name}" + (f": {', '.join(methods)}" if methods else ""))
            return out[:MAX_LINES_PER_FILE]
    pattern = HEADING if path.endswith((".md", ".mdx")) else TOP_LEVEL
    lines = [ln.rstrip()[:120] for ln in text.splitlines() if pattern.match(ln)]
    return lines[:MAX_LINES_PER_FILE]


def tracked_files(root: Path) -> list[str]:
    res = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"], cwd=root, capture_output=True, check=True)
    return sorted(p for p in res.stdout.decode().split("\0") if p and not p.startswith(CACHE_DIR + "/"))


def build(root: Path) -> tuple[int, int]:
    cache = root / CACHE_DIR
    index_path = cache / "index.json"
    first_run = not index_path.exists()
    old = json.loads(index_path.read_text()) if not first_run else {}
    new, changed = {}, 0
    for rel in tracked_files(root):
        f = root / rel
        if not f.is_file():
            continue
        data = f.read_bytes()
        sha = hashlib.sha256(data).hexdigest()
        if old.get(rel, {}).get("sha") == sha:
            new[rel] = old[rel]
            continue
        changed += 1
        new[rel] = {"sha": sha, "outline": outline(rel, data) if len(data) <= MAX_BYTES else []}
    cache.mkdir(exist_ok=True)
    index_path.write_text(json.dumps(new, sort_keys=True, indent=1, ensure_ascii=False) + "\n")
    # No timestamps or counts in here: same code must give the same bytes, or the cache prefix breaks.
    parts = ["# Project context (pcache)\n"]
    for rel in sorted(new):
        parts.append(f"\n## {rel}\n")
        parts.extend(f"- {ln}\n" for ln in new[rel]["outline"])
    (cache / "context.md").write_text("".join(parts), encoding="utf-8")
    if first_run:
        print(f"hint: add '{CACHE_DIR}/' to .gitignore", file=sys.stderr)
    return changed, len(new)


def brief(root: Path, task: str, role: str | None) -> str:
    ctx = root / CACHE_DIR / "context.md"
    if not ctx.exists():
        sys.exit(f"no {ctx}; run `pcache.py build` first")
    # Stable parts first, the per-agent task last, so sibling agents share a cached prefix.
    tail = (f"## Role\n{role}\n\n" if role else "") + f"## Task\n{task}\n"
    return ctx.read_text(encoding="utf-8") + "\n" + RULES + "\n" + tail


def usage_of(jsonl: Path) -> dict[str, int]:
    by_id: dict[str, dict] = {}
    for line in jsonl.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        msg = entry.get("message") if isinstance(entry, dict) else None
        if entry.get("type") == "assistant" and isinstance(msg, dict) and msg.get("usage"):
            by_id[msg.get("id") or str(len(by_id))] = msg["usage"]  # streamed chunks repeat an id; keep last
    keys = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
    return {k: sum(int(u.get(k) or 0) for u in by_id.values()) for k in keys}


def hit_rate(u: dict[str, int]) -> float:
    total = u["input_tokens"] + u["cache_creation_input_tokens"] + u["cache_read_input_tokens"]
    return u["cache_read_input_tokens"] / total if total else 0.0


def stats(logs: Path, session: str | None) -> list[tuple[str, dict[str, int]]]:
    if session:
        main = logs / f"{session}.jsonl"
    else:
        sessions = sorted(logs.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
        if not sessions:
            sys.exit(f"no sessions in {logs}")
        main = sessions[-1]
    rows = [("main", usage_of(main))]
    for sub in sorted((logs / main.stem / "subagents").glob("*.jsonl")):
        rows.append((sub.stem, usage_of(sub)))
    return rows


def print_stats(rows: list[tuple[str, dict[str, int]]]) -> None:
    print(f"{'agent':<28}{'input':>10}{'cache_wr':>12}{'cache_rd':>12}{'output':>10}{'hit':>7}")
    total = {k: 0 for k in rows[0][1]}
    for name, u in rows:
        for k in total:
            total[k] += u[k]
        flag = "  cold" if hit_rate(u) < 0.5 and name != "main" else ""
        print(f"{name:<28}{u['input_tokens']:>10}{u['cache_creation_input_tokens']:>12}"
              f"{u['cache_read_input_tokens']:>12}{u['output_tokens']:>10}{hit_rate(u):>7.0%}{flag}")
    print(f"{'TOTAL':<28}{total['input_tokens']:>10}{total['cache_creation_input_tokens']:>12}"
          f"{total['cache_read_input_tokens']:>12}{total['output_tokens']:>10}{hit_rate(total):>7.0%}")


def default_logs() -> Path:
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(Path.cwd()))


def self_test() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "a.py").write_text("import os\nclass A:\n    def m(self): pass\ndef f(x, y): pass\n")
        (root / "b.ts").write_text("export function g() {}\n  const inner = 1\n")
        (root / "README.md").write_text("# Title\ntext\n## Sub\n")
        git = ["git", "-c", "user.email=t@t", "-c", "user.name=t"]
        subprocess.run(["git", "init", "-q"], cwd=root, check=True)
        subprocess.run(git + ["add", "."], cwd=root, check=True)
        assert build(root) == (3, 3)
        first = (root / CACHE_DIR / "context.md").read_bytes()
        assert build(root) == (0, 3)
        assert (root / CACHE_DIR / "context.md").read_bytes() == first, "context not byte-stable"
        text = first.decode()
        assert "- class A: m" in text and "- def f(x, y)" in text and "- import os" in text
        assert "export function g" in text and "inner" not in text and "- ## Sub" in text
        (root / "b.ts").write_text("export class G {}\n")
        assert build(root) == (1, 3)
        b1, b2 = brief(root, "task one", None), brief(root, "task two", "reviewer")
        common = len(b1) - len("## Task\ntask one\n")
        assert b2[:common] == b1[:common], "briefs must share their prefix"

        logs = root / "logs"
        (logs / "s1" / "subagents").mkdir(parents=True)
        u = {"input_tokens": 10, "cache_creation_input_tokens": 20, "cache_read_input_tokens": 70, "output_tokens": 5}
        line = json.dumps({"type": "assistant", "message": {"id": "m1", "usage": u}})
        (logs / "s1.jsonl").write_text(line + "\n" + line + "\nnot json\n")
        (logs / "s1" / "subagents" / "agent-x.jsonl").write_text(line.replace("m1", "m2") + "\n")
        rows = stats(logs, "s1")
        assert [r[0] for r in rows] == ["main", "agent-x"]
        assert rows[0][1]["cache_read_input_tokens"] == 70, "duplicate message ids must be deduped"
        assert abs(hit_rate(rows[0][1]) - 0.7) < 1e-9
    print("self-test ok")


def main() -> None:
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("root", nargs="?", default=".")
    br = sub.add_parser("brief")
    br.add_argument("task")
    br.add_argument("--role")
    br.add_argument("--root", default=".")
    st = sub.add_parser("stats")
    st.add_argument("session", nargs="?")
    st.add_argument("--logs", type=Path, default=None)
    args = ap.parse_args()
    if args.cmd == "build":
        changed, total = build(Path(args.root).resolve())
        print(f"changed {changed} / total {total}")
    elif args.cmd == "brief":
        sys.stdout.write(brief(Path(args.root).resolve(), args.task, args.role))
    else:
        print_stats(stats(args.logs or default_logs(), args.session))


if __name__ == "__main__":
    main()
