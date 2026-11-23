import configparser
import sys
from pathlib import Path
from types import SimpleNamespace as NS

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import jssh  # noqa: E402

INI = """
[ssh]
user = ops
jump_host = 10.0.0.45
password = s3cret
[kube]
context = app-nonprod:app-nonprod
refresh = export PW={password}; refresh {parent}; use {context}
[ssh prod]
user = ops
jump_host = 10.0.1.45
password = prodpw
"""


def cfg():
    c = configparser.ConfigParser(interpolation=None)
    c.read_string(INI)
    return c


def args(**k):
    base = dict(ini="x.ini", profile=None, host=None, kube=False, context=None, sudo=False, forward=None, cmd=[])
    base.update(k)
    return NS(**base)


def test_jump_host_plain():
    argv, pw = jssh.build(args(cmd=["uptime"]), cfg())
    assert argv[-2:] == ["ops@10.0.0.45", "uptime"] and pw == "s3cret"
    assert "-J" not in argv


def test_other_host_via_jump_and_sudo():
    argv, _ = jssh.build(args(host="10.0.0.48", sudo=True, cmd=["ss -tlnp"]), cfg())
    assert argv[argv.index("-J") + 1] == "ops@10.0.0.45" and "ops@10.0.0.48" in argv
    assert argv[-1].startswith("echo s3cret | sudo -S -p '' sh -c 'ss -tlnp'")


def test_kube_refresh_is_prefixed():
    argv, _ = jssh.build(args(kube=True, cmd=["kubectl get ns"]), cfg())
    assert argv[-1] == "export PW=s3cret; refresh app-nonprod; use app-nonprod:app-nonprod; kubectl get ns"


def test_forward_and_profile():
    argv, pw = jssh.build(args(profile="prod", forward="15211:10.0.1.53:1521"), cfg())
    assert pw == "prodpw" and "-N" in argv and "127.0.0.1:15211:10.0.1.53:1521" in argv and argv[-1] == "ops@10.0.1.45"


def test_missing_section():
    with pytest.raises(SystemExit):
        jssh.build(args(profile="nope"), cfg())
