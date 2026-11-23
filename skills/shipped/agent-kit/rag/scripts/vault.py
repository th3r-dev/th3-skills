#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""A local, Obsidian-compatible knowledge vault with BM25 retrieval, for agent briefs. Stdlib only.

  vault.py init    --vault DIR [--dry-run]
  vault.py migrate --vault DIR --progress FILE [--prompts FILE] [--force] [--dry-run]
  vault.py note    --vault DIR --type decision|session|concept --title T --body B [--dry-run]
  vault.py hot     --vault DIR --body B            # replace wiki/hot.md (what's happening now)
  vault.py index   --vault DIR [--extra GLOB ...]  # wiki/**.md (+ repo docs) -> .vault-meta/bm25.json
  vault.py query   --vault DIR "question" [--top 5] [--json]
  vault.py --selftest

Layout follows claude-obsidian (github.com/AgriciDaniel/claude-obsidian, MIT): inbox/, wiki/{hot,index,
log,overview}.md, wiki/<type>s/, .claude-obsidian.json, derived data in .vault-meta/. Nothing leaves
the machine: chunks get a "title · type" prefix, no LLM. Keep the vault out of git with
.git/info/exclude (local only) when it lives inside a repo.
"""
from __future__ import annotations

import argparse
import datetime
import glob
import hashlib
import json
import math
import os
import re
import sys
import tempfile

DRY = False
TYPES = ("decision", "session", "source", "concept")
WORD = re.compile(r"\w+", re.UNICODE)
# ponytail: \w+ tokens; Thai has no spaces, so a Thai run is one token. Add a Thai word splitter if Thai notes matter.
K1, B = 1.5, 0.75


def today():
    return datetime.date.today().isoformat()


def write(path, text, force=True):
    if os.path.exists(path) and not force:
        print(f"skip {path} (exists)")
        return False
    print(f"write {path}")
    if not DRY:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
    return True


def append(path, text):
    print(f"append {path}")
    if not DRY:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)


def safe_title(text, words=8):
    t = re.sub(r"[`*_\[\]#|/\\:<>\"?]", "", text)
    t = re.sub(r"\s+", " ", t).strip()
    return " ".join(t.split(" ")[:words]).rstrip(".,;") or "untitled"


def frontmatter(**kv):
    lines = ["---"]
    for k, v in kv.items():
        lines.append(f"{k}: [{', '.join(v)}]" if isinstance(v, list) else f"{k}: {v}")
    return "\n".join(lines + ["---", ""])


def read_frontmatter(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}, text
    meta = dict(line.split(":", 1) for line in m.group(1).splitlines() if ":" in line)
    return {k.strip(): v.strip() for k, v in meta.items()}, text[m.end():]


# ---------- init ----------

def cmd_init(a):
    v = a.vault
    write(os.path.join(v, ".claude-obsidian.json"), json.dumps({"version": 1, "mode": "generic"}, indent=2) + "\n", False)
    write(os.path.join(v, ".obsidian", "app.json"), "{}\n", False)
    write(os.path.join(v, "inbox", ".gitkeep"), "", False)
    for t in TYPES:
        write(os.path.join(v, "wiki", f"{t}s", ".gitkeep"), "", False)
    stub = {
        "hot.md": "# Hot\n\nWhat is happening right now. Replaced by the lead each pass (`vault.py hot`).\n",
        "index.md": "# Index\n\n- [[hot]] · [[log]] · [[overview]]\n",
        "log.md": "# Log\n\nOne line per change, newest last.\n",
        "overview.md": "# Overview\n\nWhat this vault is about.\n",
    }
    for name, text in stub.items():
        write(os.path.join(v, "wiki", name), text, False)
    print("keep it out of git (local only): echo '<vault dir>/' >> .git/info/exclude")


# ---------- migrate a single progress file ----------

def sections(text):
    """'## Name' -> body."""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            cur = m.group(1).strip().lower()
            out[cur] = []
        elif cur:
            out[cur].append(line)
    return {k: "\n".join(v).strip() for k, v in out.items()}


def table_rows(body):
    rows = []
    for line in body.splitlines():
        if line.startswith("|") and not re.match(r"^\|[\s:|-]+\|$", line):
            rows.append([c.strip() for c in line.strip().strip("|").split("|")])
    return rows[1:] if rows else []  # drop the header


def prompt_entries(text):
    """'## <stamp>' blocks of a prompt log -> [(stamp, body)]."""
    out = []
    for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", text, re.S | re.M):
        body = m.group(2).strip()
        if body:
            out.append((m.group(1).strip(), body))
    return out


def plan_migration(progress_text, prompts_text, source_name):
    """Pure: returns {relative path: content} plus the log line."""
    sec = sections(progress_text)
    files = {}
    now = sec.get("now", "")
    files["wiki/hot.md"] = frontmatter(type="hot", updated=today(), source=source_name) + f"# Hot\n\n{now}\n"
    nxt = sec.get("next", "")
    files["wiki/index.md"] = ("# Index\n\n- [[hot]] · [[log]] · [[overview]]\n\n## Queue\n\n" + nxt + "\n\n## Decisions\n\n")
    for row in table_rows(sec.get("decisions", "")):
        if len(row) < 2:
            continue
        date, text = row[0], " | ".join(row[1:])
        title = f"{date} {safe_title(text)}"
        files[f"wiki/decisions/{title}.md"] = (frontmatter(type="decision", date=date, source=source_name, tags=["decision"])
                                               + f"# {safe_title(text, 14)}\n\n{text}\n\nBack to [[index]].\n")
        files["wiki/index.md"] += f"- [[{title}]]\n"
    for n, (stamp, body) in enumerate(prompt_entries(prompts_text or ""), 1):
        date = stamp[:10] if re.match(r"\d{4}-\d{2}-\d{2}", stamp) else today()
        title = f"prompt {date} {n:03d}"
        files[f"wiki/sources/{title}.md"] = (frontmatter(type="source", date=date, kind="prompt", stamp=stamp.replace(":", "-"))
                                             + f"# {safe_title(body)}\n\n{body}\n")
    return files


def cmd_migrate(a):
    with open(a.progress, encoding="utf-8") as f:
        progress = f.read()
    prompts = ""
    if a.prompts:
        with open(a.prompts, encoding="utf-8") as f:
            prompts = f.read()
    files = plan_migration(progress, prompts, os.path.basename(a.progress))
    if not os.path.exists(os.path.join(a.vault, ".claude-obsidian.json")):
        cmd_init(a)
    written = 0
    for rel, text in files.items():
        # hot and index are views of the single file: always rewritten; notes are kept unless --force
        force = a.force or rel in ("wiki/hot.md", "wiki/index.md")
        written += bool(write(os.path.join(a.vault, rel), text, force))
    decisions = sum(1 for r in files if r.startswith("wiki/decisions/"))
    sources = sum(1 for r in files if r.startswith("wiki/sources/"))
    append(os.path.join(a.vault, "wiki", "log.md"),
           f"- {today()} migrated {os.path.basename(a.progress)}: {decisions} decisions, {sources} prompts\n")
    print(f"migrated: {decisions} decisions, {sources} prompts, {written} files written")


def cmd_note(a):
    if a.type not in TYPES:
        sys.exit(f"--type must be one of {', '.join(TYPES)}")
    title = f"{today()} {safe_title(a.title)}"
    path = os.path.join(a.vault, "wiki", f"{a.type}s", f"{title}.md")
    write(path, frontmatter(type=a.type, date=today(), tags=[a.type]) + f"# {a.title}\n\n{a.body}\n\nBack to [[index]].\n", False)
    append(os.path.join(a.vault, "wiki", "log.md"), f"- {today()} {a.type}: [[{title}]]\n")
    if a.type == "decision":
        append(os.path.join(a.vault, "wiki", "index.md"), f"- [[{title}]]\n")


def cmd_hot(a):
    write(os.path.join(a.vault, "wiki", "hot.md"), frontmatter(type="hot", updated=today()) + f"# Hot\n\n{a.body}\n")


# ---------- index + query (BM25) ----------

def chunks_of(path, text):
    meta, body = read_frontmatter(text)
    title = os.path.splitext(os.path.basename(path))[0]
    prefix = f"{title} · {meta.get('type', 'doc')}"
    out = []
    for para in re.split(r"\n\s*\n", body):
        para = para.strip()
        if len(para) >= 20 and not re.fullmatch(r"[-|:\s]+", para):
            out.append({"path": path, "prefix": prefix, "text": para})
    return out


def tokens(text):
    return [w.lower() for w in WORD.findall(text)]


def build_index(files, old=None):
    """files: {path: text}. Re-chunks only files whose sha changed."""
    old = old or {"files": {}}
    entries = {}
    for path, text in files.items():
        sha = hashlib.sha256(text.encode()).hexdigest()
        prev = old["files"].get(path)
        entries[path] = prev if prev and prev["sha"] == sha else {"sha": sha, "chunks": chunks_of(path, text)}
    chunks = [c for e in entries.values() for c in e["chunks"]]
    df = {}
    for c in chunks:
        for w in set(tokens(c["prefix"] + " " + c["text"])):
            df[w] = df.get(w, 0) + 1
    lens = [len(tokens(c["prefix"] + " " + c["text"])) for c in chunks]
    return {"files": entries, "df": df, "n": len(chunks), "avgdl": (sum(lens) / len(lens)) if lens else 0.0}


def search(index, query, top=5):
    q = set(tokens(query))
    n, avgdl, df = index["n"], index["avgdl"] or 1.0, index["df"]
    scored = []
    for e in index["files"].values():
        for c in e["chunks"]:
            toks = tokens(c["prefix"] + " " + c["text"])
            tf = {}
            for w in toks:
                if w in q:
                    tf[w] = tf.get(w, 0) + 1
            s = 0.0
            for w, f in tf.items():
                idf = math.log(1 + (n - df[w] + 0.5) / (df[w] + 0.5))
                s += idf * f * (K1 + 1) / (f + K1 * (1 - B + B * len(toks) / avgdl))
            if s > 0:
                scored.append((s, c))
    scored.sort(key=lambda x: (-x[0], x[1]["path"]))
    out, seen = [], set()
    for s, c in scored:  # one passage per page
        if c["path"] not in seen:
            seen.add(c["path"])
            out.append({"path": c["path"], "score": round(s, 3), "text": c["text"]})
        if len(out) == top:
            break
    return out


def meta_path(vault):
    return os.path.join(vault, ".vault-meta", "bm25.json")


def cmd_index(a):
    paths = glob.glob(os.path.join(a.vault, "wiki", "**", "*.md"), recursive=True)
    for g in a.extra or []:
        paths += glob.glob(g, recursive=True)
    files = {}
    for p in sorted(set(paths)):
        with open(p, encoding="utf-8") as f:
            files[os.path.relpath(p, a.vault)] = f.read()
    old = None
    if os.path.exists(meta_path(a.vault)):
        with open(meta_path(a.vault), encoding="utf-8") as f:
            old = json.load(f)
    idx = build_index(files, old)
    write(meta_path(a.vault), json.dumps(idx, ensure_ascii=False, sort_keys=True))
    print(f"indexed {len(files)} files, {idx['n']} chunks")


def cmd_query(a):
    if not os.path.exists(meta_path(a.vault)):
        sys.exit("no index; run `vault.py index` first")
    with open(meta_path(a.vault), encoding="utf-8") as f:
        hits = search(json.load(f), a.question, a.top)
    if a.json:
        print(json.dumps(hits, ensure_ascii=False))
    else:
        for h in hits:
            snippet = re.sub(r"\s+", " ", h["text"])[:200]
            print(f"{h['score']}\t{h['path']}\t{snippet}")


# ---------- self-test ----------

PROGRESS_SAMPLE = """# Work state

## Now

- **Task:** build the gate (issue #4).

## Next

| Step | Issue | Feature |
|---|---|---|
| 1 | #2 | Core loop |

## Decisions

| Date | Decision |
|---|---|
| 2026-11-16 | Dungeon Key costs 14,000 gold, never Robux |
| 2026-11-16 | Packages are owned by a Roblox Group |
"""
PROMPTS_SAMPLE = "# Prompt log\n\n## 2026-11-16T18:01:55+07:00\n\nmake pets\n\n## 2026-11-16 (backfill 2)\n\nadd a dungeon\n"


def selftest():
    global DRY
    files = plan_migration(PROGRESS_SAMPLE, PROMPTS_SAMPLE, "progress.md")
    dec = sorted(p for p in files if p.startswith("wiki/decisions/"))
    assert len(dec) == 2, dec
    assert "build the gate" in files["wiki/hot.md"]
    assert "[[2026-11-16 Dungeon Key costs 14,000 gold, never Robux]]" in files["wiki/index.md"]
    assert sum(p.startswith("wiki/sources/") for p in files) == 2
    assert "type: decision" in files[dec[0]] and "[[index]]" in files[dec[0]]
    assert safe_title("a/b: `c` | d") == "ab c d"
    idx = build_index({"wiki/decisions/key.md": files[dec[0]], "wiki/decisions/group.md": files[dec[1]],
                       "wiki/x.md": "# X\n\nPets hatch from eggs bought with gold and shards only.\n"})
    assert search(idx, "how much does the dungeon key cost")[0]["path"] == "wiki/decisions/key.md"
    assert search(idx, "who owns roblox packages")[0]["path"] == "wiki/decisions/group.md"
    assert search(idx, "zzzz") == []
    again = build_index({"wiki/x.md": "# X\n\nPets hatch from eggs bought with gold and shards only.\n"}, idx)
    assert again["files"]["wiki/x.md"] is idx["files"]["wiki/x.md"], "unchanged file must not be re-chunked"
    with tempfile.TemporaryDirectory() as tmp:
        prog, pr = os.path.join(tmp, "progress.md"), os.path.join(tmp, "prompts.md")
        open(prog, "w").write(PROGRESS_SAMPLE)
        open(pr, "w").write(PROMPTS_SAMPLE)
        v = os.path.join(tmp, "vault")
        ns = argparse.Namespace(vault=v, progress=prog, prompts=pr, force=False)
        DRY = False
        cmd_migrate(ns)
        n1 = len(glob.glob(os.path.join(v, "wiki", "**", "*.md"), recursive=True))
        cmd_migrate(ns)  # idempotent: same files, notes not duplicated
        n2 = len(glob.glob(os.path.join(v, "wiki", "**", "*.md"), recursive=True))
        assert n1 == n2 == 4 + 2 + 2, (n1, n2)
        assert os.path.exists(os.path.join(v, ".claude-obsidian.json"))
    print("selftest ok")


def main():
    global DRY
    if "--selftest" in sys.argv:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("init", "migrate", "note", "hot", "index", "query"):
        p = sub.add_parser(name)
        p.add_argument("--vault", required=True)
        if name == "migrate":
            p.add_argument("--progress", required=True)
            p.add_argument("--prompts")
            p.add_argument("--force", action="store_true")
        elif name == "note":
            p.add_argument("--type", required=True)
            p.add_argument("--title", required=True)
            p.add_argument("--body", required=True)
        elif name == "hot":
            p.add_argument("--body", required=True)
        elif name == "index":
            p.add_argument("--extra", nargs="*")
        elif name == "query":
            p.add_argument("question")
            p.add_argument("--top", type=int, default=5)
            p.add_argument("--json", action="store_true")
    a = ap.parse_args()
    DRY = a.dry_run
    {"init": cmd_init, "migrate": cmd_migrate, "note": cmd_note, "hot": cmd_hot,
     "index": cmd_index, "query": cmd_query}[a.cmd](a)


if __name__ == "__main__":
    main()
