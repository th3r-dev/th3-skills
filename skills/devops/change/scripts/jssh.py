#!/usr/bin/env python3
"""ssh into a fleet through a jump host, with the password read from an ini file — never typed on a command line.

    jssh.py 'hostname'                                  # the jump host itself
    jssh.py --host 10.0.0.48 'docker ps'                # another machine, via -J <jump>
    jssh.py --sudo --host 10.0.0.48 'ss -tlnp'          # the whole command under sudo -S
    jssh.py --kube 'kubectl get ns'                     # run the [kube] refresh command first (token refresh)
    jssh.py --forward 15211:10.0.0.53:1521              # ssh -N -L tunnel through the jump host, Ctrl-C to stop
    jssh.py --ini ~/.config/devops/hosts.ini --profile prod 'uptime'

ini (default ~/.config/devops/hosts.ini, chmod 600, outside any repo):

    [ssh]                       ; or [ssh prod] etc. selected with --profile
    user = ops
    jump_host = 10.0.0.45
    password = ...
    ; optional: run before the command when --kube is given; {password} and {context} are filled in
    [kube]
    context = cluster-app-non-production:cluster-app-non-production
    refresh = export VCF_CLI_VSPHERE_PASSWORD={password} KUBECTL_VSPHERE_PASSWORD={password}; vcf context refresh {parent} --insecure-skip-tls-verify >/dev/null 2>&1; vcf context refresh {context} --insecure-skip-tls-verify >/dev/null 2>&1; kubectl config use-context {context} >/dev/null; unset VCF_CLI_VSPHERE_PASSWORD KUBECTL_VSPHERE_PASSWORD

No sshpass: SSH_ASKPASS points back at this file (askpass mode is selected by env JSSH_ASKPASS). The
password lives in this process's environment only; it reaches the remote side only through --sudo
(stdin of sudo -S) and the [kube] refresh command.
"""
from __future__ import annotations

import argparse
import configparser
import os
import shlex
import sys
from pathlib import Path

if os.environ.get("JSSH_ASKPASS"):
    print(os.environ["JSSH_PW"])
    sys.exit(0)

DEFAULT_INI = Path.home() / ".config" / "devops" / "hosts.ini"


def build(a, cfg: configparser.ConfigParser) -> tuple[list[str], str]:
    sec = "ssh" if a.profile is None else f"ssh {a.profile}"
    if sec not in cfg:
        sys.exit(f"[{sec}] not found in {a.ini}")
    s = cfg[sec]
    for k in ("user", "jump_host", "password"):
        if not s.get(k):
            sys.exit(f"[{sec}] needs {k}")
    jump = f"{s['user']}@{s['jump_host']}"
    cmd = " ".join(a.cmd)
    if a.sudo and cmd:
        cmd = f"echo {shlex.quote(s['password'])} | sudo -S -p '' sh -c {shlex.quote(cmd)}"
    if a.kube:
        ksec = "kube" if a.profile is None or f"kube {a.profile}" not in cfg else f"kube {a.profile}"
        if ksec not in cfg or not cfg[ksec].get("refresh"):
            sys.exit(f"--kube needs [{ksec}] with a refresh command in {a.ini}")
        k = cfg[ksec]
        context = a.context or k.get("context", "")
        refresh = k["refresh"].format(password=shlex.quote(k.get("password") or s["password"]),
                                      context=shlex.quote(context), parent=shlex.quote(context.split(":")[0]))
        cmd = f"{refresh}; {cmd or 'kubectl get ns'}"
    argv = ["ssh", "-o", "StrictHostKeyChecking=accept-new", "-o", "ConnectTimeout=10"]
    if a.host and a.host != s["jump_host"]:
        argv += ["-J", jump, f"{s.get('host_user', s['user'])}@{a.host}"]
    else:
        argv.append(jump)
    if a.forward:
        argv[1:1] = ["-N", "-o", "ExitOnForwardFailure=yes", "-L", f"127.0.0.1:{a.forward}"]
    elif cmd:
        argv.append(cmd)
    return argv, s["password"]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ini", type=Path, default=DEFAULT_INI)
    ap.add_argument("--profile", help="use [ssh <profile>] (and [kube <profile>]) instead of [ssh]")
    ap.add_argument("--host", help="target (omit = the jump host)")
    ap.add_argument("--kube", action="store_true", help="run the [kube] refresh command before the command")
    ap.add_argument("--context", help="kube context (default [kube] context)")
    ap.add_argument("--sudo", action="store_true", help="run the command under sudo -S")
    ap.add_argument("--forward", metavar="LPORT:HOST:PORT", help="ssh -N -L through the jump host until Ctrl-C")
    ap.add_argument("cmd", nargs="*", help="command on the target (omit = interactive shell)")
    a = ap.parse_args()
    cfg = configparser.ConfigParser(interpolation=None)
    if not cfg.read(a.ini, encoding="utf-8"):
        sys.exit(f"{a.ini} not found — see the docstring for its layout")
    argv, pw = build(a, cfg)
    askpass = str(Path(__file__).resolve())
    if os.name == "nt":  # Windows OpenSSH runs SSH_ASKPASS with CreateProcess: a .py is not executable (error 193)
        import subprocess
        import tempfile
        shim = Path(tempfile.gettempdir()) / "jssh_askpass.cmd"
        shim.write_text(f'@"{sys.executable}" "{askpass}"\r\n', encoding="utf-8")
        askpass = str(shim)
    env = dict(os.environ, JSSH_ASKPASS="1", JSSH_PW=pw, SSH_ASKPASS=askpass, SSH_ASKPASS_REQUIRE="force")
    if os.name == "nt":  # execvpe on Windows spawns and returns; keep the parent alive for the tunnel
        return subprocess.call(argv, env=env)
    os.execvpe("ssh", argv, env)


if __name__ == "__main__":
    sys.exit(main())
