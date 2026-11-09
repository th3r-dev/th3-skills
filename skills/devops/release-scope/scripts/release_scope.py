# /// script
# requires-python = ">=3.10"
# ///
"""What goes up in a release, and what is still pending: one command, facts only.

    S=skills/devops/release-scope/scripts
    uv run $S/release_scope.py --to v1.2.22 --prod v1.2.21,v1.2.21.1 \
        --repo api=../backend-repo=org/backend-repo --repo web=../frontend-repo=org/frontend-repo \
        --key-regex '(?:PRJ|ISS)-\\d+' [--mirror-regex '^\\[(PRJ-\\d+)\\]'] \
        [--board tracker=path/to/issues.json] [--board mirror=path/to/pages.json] [--out DIR]
    uv run $S/release_scope.py --selftest

Per repo (every --repo is a local clone with an `origin`; the optional third part is the GitHub slug for gh):
  1. new in the release   = ticket keys on releases/<to> minus the keys on every --prod branch,
                            each with the PRs that brought it in, plus PRs in the range that carry no key
  2. lost from prod       = keys on --prod that the release no longer has (must be 0)
  3. pending code         = keys on the dev branch that never reached releases/<to>; a key that did reach
                            the release in another repo is flagged "half shipped"
  4. open PRs             = gh pr list --state open (dependabot left out)
  5. board items          = with --board: open non-Epic, non-Bug tickets whose key (or the key a mirror
                            ticket names in its summary) is not in the release

"In the release" means the key appears in a commit subject/body or merged branch name. Boards without
fixVersions give no better link. Work committed under another key reads as pending; check before telling anyone.
--board accepts Jira REST search JSON ({issues:[...]}), the Rovo shape ({issues:{nodes:[...]}}), or a JSON
list of such pages. Writes <out>/scope.md + scope.json and prints the path.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PR_RE = re.compile(r"Merge pull request #(\d+)")
DONE = re.compile(r"done|cancel|closed|resolved", re.I)
ORDER = {"in progress": 0, "testing": 1, "ready for qa": 1, "approved": 1, "blocked": 2,
         "waiting": 3, "to do": 4, "backlog": 5}


class Keys:
    def __init__(self, key_regex: str, mirror_regex: str | None):
        self.key = re.compile(rf"\b({key_regex})\b")
        self.mirror = re.compile(mirror_regex) if mirror_regex else None

    def keys_in(self, text: str) -> set[str]:
        return set(self.key.findall(text))

    def mirror_of(self, summary: str) -> str:
        m = self.mirror.match(summary or "") if self.mirror else None
        return m.group(1) if m else ""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def ref(name: str, prefix: str) -> str:
    """'v1.2.22' -> '<prefix>v1.2.22'; anything with a slash is taken as is."""
    return name if "/" in name else f"{prefix}{name}"


def keys_on(K: Keys, repo: Path, *refs: str) -> set[str]:
    return K.keys_in(git(repo, "log", "--format=%s%n%b", *refs))


def prs_in_range(K: Keys, repo: Path, base: list[str], to: str) -> list[dict]:
    """Every PR merged into `to` since it left the prod branches, with the keys its commits carry."""
    excl = [f"^{b}" for b in base]
    out = []
    for line in git(repo, "log", "--first-parent", "--merges", "--format=%H%x09%cs%x09%s", to, *excl).splitlines():
        sha, day, subj = line.split("\t", 2)
        m = PR_RE.search(subj)
        body = git(repo, "log", "--format=%s%n%b", f"{sha}^1..{sha}")
        out.append({"pr": int(m.group(1)) if m else None, "date": day, "subject": subj,
                    "keys": sorted(K.keys_in(body + "\n" + subj))})
    return out


def pending_code(K: Keys, repo: Path, keys: set[str], dev: str, to: str) -> list[dict]:
    log = git(repo, "log", "--no-merges", "--format=%cs%x09%s", f"{to}..{dev}").splitlines()
    out = []
    for k in sorted(keys):
        hits = [l.split("\t", 1) for l in log if k in K.keys_in(l)]
        if hits:
            out.append({"key": k, "commits": len(hits), "first": hits[-1][0], "last": hits[0][0], "subject": hits[0][1]})
    return out


def open_prs(slug: str | None) -> list[dict]:
    if not slug:
        return []
    try:
        raw = subprocess.run(["gh", "pr", "list", "-R", slug, "--state", "open", "--limit", "100", "--json",
                              "number,title,baseRefName,headRefName,isDraft,updatedAt"],
                             check=True, capture_output=True, text=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        return [{"error": str(e)}]
    return [p for p in json.loads(raw) if not p["headRefName"].startswith("dependabot/")]


def load_board(K: Keys, data, board: str) -> list[dict]:
    """Flatten a Jira export into {board, key, mirror, type, status, summary}."""
    pages = data if isinstance(data, list) else [data]
    rows = []
    for page in pages:
        issues = page.get("issues", [])
        if isinstance(issues, dict):  # Rovo: {issues: {nodes: [...]}}
            issues = issues.get("nodes", [])
        for it in issues:
            it = it.get("issue", it)
            f = it["fields"]
            rows.append({"board": board, "key": it["key"], "mirror": K.mirror_of(f.get("summary") or ""),
                         "type": (f.get("issuetype") or {}).get("name", ""),
                         "status": (f.get("status") or {}).get("name", ""),
                         "summary": f.get("summary") or ""})
    return rows


def rank(status: str) -> int:
    return ORDER.get(status.lower(), 4) if status else 9


def board_pending(K: Keys, rows: list[dict], released: set[str]) -> list[dict]:
    """One row per ticket: a mirror ticket and its source merge on the source key.
    Dropped when any board calls it done, or it is a Bug/Epic, or one of its keys is in the release."""
    merged: dict[str, dict] = {}
    for r in rows:
        k = r["mirror"] or r["key"]
        m = merged.setdefault(k, {"key": k, "keys": {}, "statuses": {}, "type": r["type"],
                                  "summary": (K.mirror.sub("", r["summary"]).strip() if K.mirror else r["summary"])})
        m["statuses"][r["board"]] = r["status"]
        m["keys"][r["board"]] = r["key"]
        if r["type"] in ("Epic", "Bug"):
            m["type"] = r["type"]
    keep = [m for m in merged.values()
            if m["type"] not in ("Epic", "Bug")
            and not any(DONE.search(s) for s in m["statuses"].values())
            and not ({m["key"], *m["keys"].values()} & released)]
    for m in keep:
        m["rank"] = min(rank(s) for s in m["statuses"].values())
    return sorted(keep, key=lambda m: (m["rank"], m["key"]))


def scope(K: Keys, repos: dict[str, tuple[Path, str | None]], to: str, prod: list[str], dev: str, prefix: str) -> dict:
    res = {"to": to, "prod": prod, "dev": dev, "repos": {}}
    for name, (repo, slug) in repos.items():
        git(repo, "fetch", "-q", "origin")
        t, p = ref(to, prefix), [ref(x, prefix) for x in prod]
        k_to, k_prod, k_dev = keys_on(K, repo, t), keys_on(K, repo, *p), keys_on(K, repo, dev)
        res["repos"][name] = {
            "head": git(repo, "log", "-1", "--format=%h %ci %s", t).strip(),
            "new_keys": sorted(k_to - k_prod),
            "lost_keys": sorted(k_prod - k_to),
            "prs": prs_in_range(K, repo, p, t),
            "pending_code": pending_code(K, repo, k_dev - k_to, dev, t),
            "open_prs": open_prs(slug),
            "all_keys": sorted(k_to),
        }
    for name, r in res["repos"].items():  # shipped in one repo, still on dev in another: half a feature
        others = [o for o in res["repos"] if o != name]
        r["half_shipped"] = sorted(c["key"] for c in r["pending_code"]
                                   if any(c["key"] in res["repos"][o]["all_keys"] for o in others))
    return res


def render(res: dict, board: list[dict], boards: list[str]) -> str:
    L = [f"# Release scope: {res['to']} vs prod {' + '.join(res['prod'])}", ""]
    for name, r in res["repos"].items():
        L += [f"## {name}", "", f"head of {res['to']}: `{r['head']}`", "",
              f"new keys ({len(r['new_keys'])}): {' '.join(r['new_keys']) or '-'}",
              f"lost from prod: {' '.join(r['lost_keys']) or '0'}",
              f"**half shipped** (in the release in another repo, still only on dev here): "
              f"{' '.join(r['half_shipped']) or 'none'}", "",
              "| PR | merged | new keys | keys prod already has | subject |", "|---|---|---|---|---|"]
        new = set(r["new_keys"])
        for p in r["prs"]:
            n = [k for k in p["keys"] if k in new]
            o = [k for k in p["keys"] if k not in new]
            L.append(f"| {'#%s' % p['pr'] if p['pr'] else '-'} | {p['date']} | {' '.join(n) or '**none**'} "
                     f"| {' '.join(o)} | {p['subject']} |")
        L += ["", f"pending code: on {res['dev']}, not in {res['to']}", ""]
        L += [f"- {c['key']} · {c['commits']} commit(s) {c['first']}..{c['last']} · {c['subject']}"
              for c in r["pending_code"]] or ["- none"]
        L += ["", "open PRs", ""]
        L += [f"- #{p.get('number')} → {p.get('baseRefName')} · {p.get('headRefName')}"
              f"{' · draft' if p.get('isDraft') else ''} · {str(p.get('updatedAt', ''))[:10]} · {p.get('title', p.get('error'))}"
              for p in r["open_prs"]] or ["- none"]
        L.append("")
    if board:
        active = [b for b in board if b["rank"] <= ORDER["blocked"]]
        cols = " | ".join(f"{b} key | {b} status" for b in boards)
        L += ["## board items with no key in the release", "",
              "In Progress / Testing / Ready for QA / Blocked on any board. Bugs and Epics left out.", "",
              f"| key | {cols} | type | summary |", "|" + "---|" * (3 + 2 * len(boards))]
        for b in active:
            cells = " | ".join(f"{b['keys'].get(x, '-')} | {b['statuses'].get(x) or '-'}" for x in boards)
            L.append(f"| {b['key']} | {cells} | {b['type']} | {b['summary'][:100]} |")
        L += ["", f"plus {len(board) - len(active)} more in Waiting / To Do / Backlog (scope.json `board_pending`)", ""]
    return "\n".join(L)


def selftest() -> None:
    K = Keys(r"(?:PRJ|ISS)-\d+", r"^\[((?:PRJ|ISS)-\d+)\]")
    assert K.keys_in("fix(export): PRJ-261 - x\nMerge pull request #611 from A/hotfix/PRJ-247") == {"PRJ-261", "PRJ-247"}
    assert ref("v1.2.22", "origin/releases/") == "origin/releases/v1.2.22" and ref("origin/develop", "x/") == "origin/develop"
    mirror = {"issues": {"nodes": [
        {"key": "PRJ-227", "fields": {"summary": "[PRJ-5373] report", "issuetype": {"name": "Task"}, "status": {"name": "Testing"}}},
        {"key": "PRJ-219", "fields": {"summary": "[PRJ-5355] ps0508", "issuetype": {"name": "Task"}, "status": {"name": "To Do"}}},
        {"key": "PRJ-246", "fields": {"summary": "[PRJ-5399] nm8", "issuetype": {"name": "Bug"}, "status": {"name": "Waiting"}}}]}}
    got = board_pending(K, load_board(K, mirror, "mirror"), released={"PRJ-5373"})
    assert [g["key"] for g in got] == ["PRJ-5355"], got  # mirrored key counts, bugs are left out
    pair = [{"board": "mirror", "key": "PRJ-184", "mirror": "PRJ-5165", "type": "Task", "status": "Testing", "summary": "[PRJ-5165] dup"},
            {"board": "tracker", "key": "PRJ-5165", "mirror": "", "type": "Story", "status": "Backlog", "summary": "dup"},
            {"board": "tracker", "key": "PRJ-5386", "mirror": "", "type": "Task", "status": "Done", "summary": "x"}]
    got = board_pending(K, pair, released=set())
    assert len(got) == 1 and got[0]["statuses"] == {"mirror": "Testing", "tracker": "Backlog"}, got
    print("selftest ok")


def parse_repo(s: str) -> tuple[str, tuple[Path, str | None]]:
    parts = s.split("=")
    if len(parts) < 2:
        raise argparse.ArgumentTypeError("--repo name=path[=github/slug]")
    return parts[0], (Path(parts[1]).resolve(), parts[2] if len(parts) > 2 else None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--to", help="release to describe, e.g. v1.2.22")
    ap.add_argument("--prod", help="what prod runs, comma-separated, e.g. v1.2.21,v1.2.21.1")
    ap.add_argument("--dev", default="origin/develop")
    ap.add_argument("--release-prefix", default="origin/releases/", help="prepended to --to / --prod names without a slash")
    ap.add_argument("--repo", action="append", type=parse_repo, help="name=path[=github/slug], repeatable")
    ap.add_argument("--key-regex", default=r"[A-Z][A-Z0-9]+-\d+", help="ticket key pattern (no outer group needed)")
    ap.add_argument("--mirror-regex", help="regex with one group: the source key a mirror ticket names in its summary")
    ap.add_argument("--board", action="append", default=[], help="name=issues.json, repeatable")
    ap.add_argument("--out", type=Path, help="default release/<to>/")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()
        return 0
    if not (a.to and a.prod and a.repo):
        ap.error("--to, --prod and at least one --repo are required")
    K = Keys(a.key_regex, a.mirror_regex)
    res = scope(K, dict(a.repo), a.to, a.prod.split(","), a.dev, a.release_prefix)
    released = set().union(*(r["all_keys"] for r in res["repos"].values()))
    boards = [b.split("=", 1)[0] for b in a.board]
    rows = [r for b in a.board for r in load_board(K, json.loads(Path(b.split("=", 1)[1]).read_text(encoding="utf-8")), b.split("=", 1)[0])]
    board = board_pending(K, rows, released)
    res["board_pending"] = board
    out = (a.out.resolve() if a.out else Path("release") / a.to.split("/")[-1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "scope.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "scope.md").write_text(render(res, board, boards), encoding="utf-8")
    print(out / "scope.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
