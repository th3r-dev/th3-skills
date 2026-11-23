#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""The board for a lead agent loop: which issue is ready for which role agent, which PR is at which
handoff step. GitHub labels are the state; this script only reads them and writes labels/comments.

  team.py doctor                 # tools each role needs on this machine (config "needs")
  team.py board                  # PRs by status, ready issues, waiting issues with the reason
  team.py next [--limit N] [--role R]   # ready issues as JSON lines {"number","title","role"}
  team.py claim <n> <role>       # agent:<role> + status:in-progress, plus a comment
  team.py release <n> "<why>" [--blocked]
  team.py --selftest

Config (optional) `.claude/team.json` in the repo, defaults below:
  {"roles": [["bug","developer"],["feature","developer"],["design","designer"]],
   "needs": {"developer": ["npm"]}, "workers": ["developer","designer"]}
"roles" is an ordered label -> role list (first match wins). An issue is ready when it is open,
not `blocked`, has no `status:*` label, no open PR closes it, every "Depends on #N" is closed,
a label maps to a role, and that role's tools are on PATH. Order: milestone "M<n>", then number.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

DEFAULT = {
    "roles": [["bug", "developer"], ["feature", "developer"], ["design", "designer"]],
    "needs": {},
    "workers": ["developer", "designer"],
}
PR_FLOW = ("status:needs-playtest", "status:playtesting", "status:needs-review",
           "status:changes-requested", "status:ready-for-owner")
DEP_RE = re.compile(r"depends on\s+((?:#\d+[\s,]*(?:and\s+)?)+)", re.I)
CLOSES_RE = re.compile(r"\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)", re.I)


def load_config(root="."):
    p = os.path.join(root, ".claude", "team.json")
    cfg = dict(DEFAULT)
    if os.path.isfile(p):
        with open(p, encoding="utf-8") as f:
            cfg.update(json.load(f))
    return cfg


# ---------- rules ----------

def names(item):
    return {lab["name"] for lab in item.get("labels", [])}


def role_for(labels, roles):
    for label, role in roles:
        if label in labels:
            return role
    return None


def deps(body):
    out = []
    for m in DEP_RE.finditer(body or ""):
        out += [int(n) for n in re.findall(r"#(\d+)", m.group(1))]
    return sorted(set(out))


def closed_by_prs(prs):
    """issue -> PR. GitHub links only PRs into the default branch, so PR bodies are read too."""
    out = {}
    for pr in prs:
        nums = [ref["number"] for ref in pr.get("closingIssuesReferences") or []]
        nums += [int(n) for n in CLOSES_RE.findall(pr.get("body") or "")]
        out.update({n: pr["number"] for n in nums})
    return out


def wait_reason(issue, open_numbers, have_tool, cfg, in_prs=None):
    """None if ready for a worker, else why it waits."""
    labels = names(issue)
    if in_prs and issue["number"] in in_prs:
        return f"has PR #{in_prs[issue['number']]}"
    if "blocked" in labels:
        return "blocked"
    if any(lab.startswith("status:") for lab in labels):
        return "in progress"
    role = role_for(labels, cfg["roles"])
    if role is None:
        return "no role label"
    open_deps = [d for d in deps(issue.get("body")) if d in open_numbers]
    if open_deps:
        return "waits for " + ", ".join(f"#{d}" for d in open_deps)
    missing = [t for t in cfg["needs"].get(role, []) if not have_tool(t)]
    if missing:
        return f"{role} needs {', '.join(missing)} on this machine"
    return None


def order_key(issue):
    m = re.match(r"M(\d+)", (issue.get("milestone") or {}).get("title") or "")
    return (int(m.group(1)) if m else 99, issue["number"])


def ready(issues, have_tool, cfg, in_prs=None):
    open_numbers = {i["number"] for i in issues}
    return sorted((i for i in issues if wait_reason(i, open_numbers, have_tool, cfg, in_prs) is None),
                  key=order_key)


def pr_stage(pr):
    labels = names(pr)
    for s in PR_FLOW:
        if s in labels:
            return s
    return "blocked" if "blocked" in labels else ("draft (working)" if pr.get("isDraft") else "no status")


# ---------- gh ----------

def gh_json(args):
    r = subprocess.run(["gh", *args], text=True, capture_output=True)
    if r.returncode:
        sys.exit(f"gh {' '.join(args)} failed: {r.stderr.strip()}")
    return json.loads(r.stdout)


def gh(*args):
    print("$ gh " + " ".join(args))
    subprocess.run(["gh", *args], check=True)


def open_issues():
    return gh_json(["issue", "list", "--state", "open", "--limit", "300",
                    "--json", "number,title,labels,body,milestone"])


def open_prs():
    return gh_json(["pr", "list", "--state", "open", "--limit", "100",
                    "--json", "number,title,labels,isDraft,body,closingIssuesReferences"])


def have_tool(t):
    return shutil.which(t) is not None


# ---------- commands ----------

def cmd_doctor(cfg, _):
    bad = 0
    for role, tools in sorted(cfg["needs"].items()):
        for t in tools:
            ok = have_tool(t)
            bad += not ok
            print(f"{'ok  ' if ok else 'NEED'}\t{t}\t{role}")
    ok = subprocess.run(["gh", "auth", "status"], capture_output=True).returncode == 0
    bad += not ok
    print(f"{'ok  ' if ok else 'NEED'}\tgh logged in\tall")
    sys.exit(1 if bad else 0)


def cmd_board(cfg, _):
    prs = open_prs()
    print("## Pull requests")
    for pr in sorted(prs, key=lambda p: p["number"]):
        agent = ",".join(sorted(lab[6:] for lab in names(pr) if lab.startswith("agent:"))) or "-"
        print(f"#{pr['number']}\t{pr_stage(pr)}\t{agent}\t{pr['title']}")
    issues, in_prs = open_issues(), closed_by_prs(prs)
    open_numbers = {i["number"] for i in issues}
    print("\n## Ready issues (next first)")
    for i in ready(issues, have_tool, cfg, in_prs):
        print(f"#{i['number']}\t{role_for(names(i), cfg['roles'])}\t{i['title']}")
    print("\n## Waiting issues")
    waits = {}
    for i in sorted(issues, key=order_key):
        why = wait_reason(i, open_numbers, have_tool, cfg, in_prs)
        if why:
            waits.setdefault(why, []).append(f"#{i['number']}")
    for why, nums in waits.items():
        print(f"{why}:\t{' '.join(nums)}")


def cmd_next(cfg, a):
    roles = a.role or cfg["workers"]
    for i in [i for i in ready(open_issues(), have_tool, cfg, closed_by_prs(open_prs()))
              if role_for(names(i), cfg["roles"]) in roles][: a.limit]:
        print(json.dumps({"number": i["number"], "title": i["title"], "role": role_for(names(i), cfg["roles"])}))


def cmd_claim(cfg, a):
    gh("issue", "edit", str(a.number), "--add-label", f"agent:{a.role},status:in-progress")
    gh("issue", "comment", str(a.number), "--body", f"Claimed by the **{a.role}** agent (lead loop).")


def cmd_release(cfg, a):
    labels = [lab for lab in names(gh_json(["issue", "view", str(a.number), "--json", "labels"]))
              if lab.startswith(("agent:", "status:"))]
    if labels:
        gh("issue", "edit", str(a.number), "--remove-label", ",".join(labels))
    if a.blocked:
        gh("issue", "edit", str(a.number), "--add-label", "blocked")
    gh("issue", "comment", str(a.number), "--body", f"Released by the lead loop: {a.why}")


def selftest():
    cfg = {**DEFAULT, "roles": [["asset", "modeler"], ["feature", "developer"], ["design", "designer"]],
           "needs": {"developer": ["lune"]}}

    def issue(n, labels, body="", ms=None):
        return {"number": n, "title": f"i{n}", "labels": [{"name": x} for x in labels], "body": body,
                "milestone": {"title": ms} if ms else None}

    def all_tools(_):
        return True

    assert role_for({"asset", "feature"}, cfg["roles"]) == "modeler"
    assert role_for({"ui"}, cfg["roles"]) is None
    assert deps("depends on #3, #5 and #7\nnot #9") == [3, 5, 7]
    assert deps(None) == []
    assert closed_by_prs([{"number": 19, "body": "Closes #18, fixes #7"},
                          {"number": 20, "closingIssuesReferences": [{"number": 4}]}]) == {18: 19, 7: 19, 4: 20}
    nums = {2, 3}
    assert wait_reason(issue(3, ["feature"], "Depends on #2"), nums, all_tools, cfg) == "waits for #2"
    assert wait_reason(issue(3, ["feature"], "Depends on #1"), nums, all_tools, cfg) is None
    assert wait_reason(issue(2, ["feature", "blocked"]), nums, all_tools, cfg) == "blocked"
    assert wait_reason(issue(2, ["feature", "status:in-progress"]), nums, all_tools, cfg) == "in progress"
    assert wait_reason(issue(2, ["feature"]), nums, lambda t: False, cfg) == "developer needs lune on this machine"
    assert wait_reason(issue(2, ["feature"]), nums, all_tools, cfg, {2: 9}) == "has PR #9"
    order = [issue(30, ["asset"], ms="M4 Art"), issue(5, ["feature"], ms="M2"), issue(9, ["design"]),
             issue(2, ["feature"], ms="M1"), issue(3, ["feature"], "Depends on #2", ms="M1")]
    assert [i["number"] for i in ready(order, all_tools, cfg)] == [2, 5, 30, 9]
    pr = {"labels": [{"name": "status:needs-review"}], "isDraft": True}
    assert pr_stage(pr) == "status:needs-review"
    assert pr_stage({"labels": [], "isDraft": True}) == "draft (working)"
    print("selftest ok")


def main(argv=None):
    if argv is None and "--selftest" in sys.argv:
        return selftest()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".", help="repo root holding .claude/team.json")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor")
    sub.add_parser("board")
    p = sub.add_parser("next")
    p.add_argument("--limit", type=int, default=2)
    p.add_argument("--role", action="append")
    p = sub.add_parser("claim")
    p.add_argument("number", type=int)
    p.add_argument("role")
    p = sub.add_parser("release")
    p.add_argument("number", type=int)
    p.add_argument("why")
    p.add_argument("--blocked", action="store_true")
    a = ap.parse_args(argv)
    cfg = load_config(a.root)
    {"doctor": cmd_doctor, "board": cmd_board, "next": cmd_next, "claim": cmd_claim,
     "release": cmd_release}[a.cmd](cfg, a)


if __name__ == "__main__":
    main()
