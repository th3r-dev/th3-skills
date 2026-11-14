#!/usr/bin/env python3
"""Strict review of rendered flows: score each one 1–10 from the graph it actually drew.

Design → state → graph JSON → this review. A flow passes at 9 or more. Hard gates first (a failed gate caps the
score), then deductions. Re-render anything below 9 with targeted fixes, at most a few rounds.

  flow_review.py DIR [--min 9] [--json out.json] [--allow-markers]   DIR holds <name>.graph.json (+ optional <name>.qa.json)
  flow_review.py --self-test

Hard gates (from strict figure review practice: a wrong or missing arrow is never cosmetic)
  chain ends on a lettered marker ........ score ≤ 5   a flow joins UI to UI: the line lands on the next screen
                                                       (--allow-markers only when the user asked for markers)
  anchor never reaches a screen .......... score ≤ 5   its result state (dialog open, page opened) isn't built
  missing edge or orphan step ............ score ≤ 6   every step must be connected; nothing floats
  forced edge (router fell back) ......... score ≤ 8   drawn, but needs a look
  backward edge (right→left / bottom→top)  score ≤ 8   flows read left to right, top to bottom; returns to a
                                                       screen are allowed
Deductions: −1 per line over an object, −0.5 per label overlap, −0.25 per crossing (−2 at most).
"""
import argparse, json, os, sys
from pathlib import Path


def dead_anchors(graph, allow_markers=False):
    """Anchors whose drawn chain never lands on a screen node. An end step never counts; a marker counts only when
    the user asked for markers (it stands for the screen it points at)."""
    goal = {"screen", "marker"} if allow_markers else {"screen"}
    kind = {n["id"]: n.get("kind") for n in graph.get("nodes") or []}
    nxt = {}
    for e in graph.get("edges") or []:
        if e.get("drawn", True):
            nxt.setdefault(e["from"], []).append(e["to"])
    def reaches(v, seen):
        return kind.get(v) in goal or any(t not in seen and reaches(t, seen | {t}) for t in nxt.get(v, []))
    return [i for i, k in kind.items() if k == "anchor" and not reaches(i, {i})]


def gates(graph, qa, allow_markers=False):
    """Hard gates: (cap, notes). Each failed gate caps the score however clean the drawing is."""
    markers = [n["id"] for n in graph.get("nodes") or [] if n.get("kind") == "marker"]
    dead = dead_anchors(graph, allow_markers)
    cross, other = qa.get("crossings") or 0, qa.get("crossOther") or 0
    checks = [
        (markers and not allow_markers, 5, f"{len(markers)} line(s) end on a lettered marker, not on the screen"),
        (dead, 5, f"never reach a screen: {dead}"),
        (graph.get("missing") or graph.get("orphans"), 6, f"missing {graph.get('missing')} orphans {graph.get('orphans')}"),
        (graph.get("forced"), 8, f"forced {graph.get('forced')}"),
        (graph.get("backward"), 8, f"reads backward {graph.get('backward')}"),
        (graph.get("nested"), 8, f"anchors picked nested elements {graph.get('nested')}"),
        (cross or other, 8, f"{cross} crossing(s), {other} with other flows"),  # a line crossing a line is a fail
    ]
    failed = [(c, note) for hit, c, note in checks if hit]
    return min([10.0] + [c for c, _ in failed]), [note for _, note in failed]


def score(graph, qa=None, allow_markers=False):
    qa = qa or {}
    cap, notes = gates(graph, qa, allow_markers)
    over, lab, inner = qa.get("lineOverObjects") or 0, qa.get("labelOverlaps") or 0, qa.get("headInner") or 0
    s = 10.0 - (over * 1 + lab * 0.5 + min(2.0, inner * 0.5))
    if over: notes.append(f"{over} line(s) over objects")
    if lab: notes.append(f"{lab} label overlap(s)")
    if inner: notes.append(f"{inner} element(s) under a first run")
    return round(max(1.0, min(cap, s)), 2), notes


def inside_work(p, what="path"):
    """CLI paths come from an agent, so this script only reads and writes inside the folder it runs from."""
    root = os.path.realpath(os.getcwd())
    full = os.path.realpath(os.path.join(root, os.path.expanduser(p)))
    if full != root and not full.startswith(root + os.sep):
        raise ValueError(f"{what} {p!r} is outside the working folder {root}; run the script from that folder")
    return full


def self_test():
    ok = {"missing": [], "orphans": [], "forced": [], "backward": [],
          "nodes": [{"id": "a", "kind": "anchor"}, {"id": "n", "kind": "process"}, {"id": "s", "kind": "screen"}],
          "edges": [{"from": "a", "to": "n", "drawn": True}, {"from": "n", "to": "s", "drawn": True}]}
    assert score(ok, {})[0] == 10
    to_marker = {**ok, "nodes": ok["nodes"][:2] + [{"id": "m", "kind": "marker"}], "edges": ok["edges"][:1] + [{"from": "n", "to": "m"}]}
    assert score(to_marker, {})[0] == 5 and score(to_marker, {}, allow_markers=True)[0] == 10
    to_end = {**ok, "nodes": ok["nodes"][:2] + [{"id": "e", "kind": "end"}], "edges": ok["edges"][:1] + [{"from": "n", "to": "e"}]}
    assert score(to_end, {})[0] == 5 and dead_anchors(to_end) == ["a"] and score(to_end, {}, allow_markers=True)[0] == 5
    assert score({**ok, "orphans": ["n1"]}, {})[0] == 6
    assert score({**ok, "forced": ["a→b"]}, {"crossings": 1})[0] == 8
    assert score(ok, {"crossings": 20})[0] == 8 and score(ok, {"crossOther": 1})[0] == 8
    assert score({**ok, "nested": ["a⊂b"]}, {})[0] == 8 and score(ok, {"headInner": 2})[0] == 9
    assert score(ok, {"lineOverObjects": 2, "labelOverlaps": 1})[0] == 7.5
    for bad in ("../outside", "/etc"):
        try:
            inside_work(bad)
        except ValueError:
            continue
        raise AssertionError(f"{bad} accepted")
    print("self-test ok")


def main():
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dir"); ap.add_argument("--min", type=float, default=9); ap.add_argument("--json")
    ap.add_argument("--allow-markers", action="store_true", help="the user asked for on-page connector markers")
    a = ap.parse_args()
    d, rows = Path(inside_work(a.dir, "DIR")), []
    for g in sorted(d.glob("*.graph.json")):
        name = g.name[: -len(".graph.json")]
        qa_p = d / f"{name}.qa.json"
        sc, notes = score(json.loads(g.read_text(encoding="utf-8")) or {},
                          json.loads(qa_p.read_text(encoding="utf-8")) if qa_p.exists() else {}, a.allow_markers)
        rows.append({"flow": name, "score": sc, "pass": sc >= a.min, "notes": notes})
    for r in sorted(rows, key=lambda r: r["score"]):
        print(f"{'PASS' if r['pass'] else 'FAIL'} {r['score']:>5}  {r['flow']}  {'; '.join(r['notes'])[:160]}")
    n = len(rows); ok = sum(r["pass"] for r in rows)
    print(f"\n{ok}/{n} flows pass (≥{a.min}); mean {sum(r['score'] for r in rows) / max(1, n):.2f}")
    if a.json:
        Path(inside_work(a.json, "--json")).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:  # a path outside the working folder: a clear message, not a traceback
        sys.exit(f"error: {exc}")
