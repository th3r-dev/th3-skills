import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import release_scope as rs  # noqa: E402

K = rs.Keys(r"PRJ-\d+", r"^\[(PRJ-\d+)\]")


def test_selftest():
    rs.selftest()


def git(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, text=True)


def commit(repo, msg):
    (repo / "f").write_text(msg, encoding="utf-8")
    git(repo, "add", "f")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@x", "commit", "-q", "-m", msg)


def test_scope_on_a_tiny_repo(tmp_path):
    """prod = v1, release = v2 (adds PRJ-2 via a PR merge), dev has PRJ-3 on top of v2."""
    origin = tmp_path / "origin.git"
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True)
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    commit(repo, "PRJ-1 first feature")
    git(repo, "branch", "releases/v1")
    git(repo, "checkout", "-q", "-b", "feat")
    commit(repo, "PRJ-2 second feature")
    git(repo, "checkout", "-q", "main")
    git(repo, "-c", "user.name=t", "-c", "user.email=t@x", "merge", "-q", "--no-ff", "-m", "Merge pull request #7 from x/feat", "feat")
    git(repo, "branch", "releases/v2")
    commit(repo, "PRJ-3 pending work")
    git(repo, "branch", "develop")
    git(repo, "remote", "add", "origin", str(origin))
    git(repo, "push", "-q", "origin", "main", "develop", "releases/v1", "releases/v2")
    res = rs.scope(K, {"app": (repo, None)}, "v2", ["v1"], "origin/develop", "origin/releases/")
    r = res["repos"]["app"]
    assert r["new_keys"] == ["PRJ-2"] and r["lost_keys"] == []
    assert [p["pr"] for p in r["prs"]] == [7] and r["prs"][0]["keys"] == ["PRJ-2"]
    assert [c["key"] for c in r["pending_code"]] == ["PRJ-3"]
    md = rs.render(res, [], [])
    assert "new keys (1): PRJ-2" in md and "lost from prod: 0" in md and "- PRJ-3 · 1 commit(s)" in md


def test_board_rendering_columns():
    rows = [{"board": "tracker", "key": "PRJ-9", "mirror": "", "type": "Story", "status": "In Progress", "summary": "s"}]
    board = rs.board_pending(K, rows, released=set())
    md = rs.render({"to": "v2", "prod": ["v1"], "dev": "d", "repos": {}}, board, ["tracker"])
    assert "| key | tracker key | tracker status | type | summary |" in md and "| PRJ-9 | PRJ-9 | In Progress | Story | s |" in md
