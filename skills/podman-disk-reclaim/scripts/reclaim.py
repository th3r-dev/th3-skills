#!/usr/bin/env python3
"""Reclaim disk space from Podman on Windows (WSL), macOS, and Linux.

  1. Prune unused images (optionally stopped containers / unused volumes).
  2. Podman machine only (Windows, macOS): fstrim inside the VM so freed
     blocks are released. macOS VM disks are sparse, so this is enough there.
  3. Windows only: stop the machine, `wsl --shutdown`, compact ext4.vhdx with
     diskpart. WSL's vhdx never shrinks on its own. Needs an Administrator shell.

Linux runs Podman natively, so only step 1 applies.

  python reclaim.py --dry-run
  python reclaim.py                        # prune unused images + reclaim
  python reclaim.py --containers --volumes # also drop stopped containers, unused volumes
  python reclaim.py --skip-prune           # reclaim only, delete nothing
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time

LXSS = r"Software\Microsoft\Windows\CurrentVersion\Lxss"


def vhdx_path(machine):
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, LXSS) as root:
        for i in range(winreg.QueryInfoKey(root)[0]):
            with winreg.OpenKey(root, winreg.EnumKey(root, i)) as dist:
                if winreg.QueryValueEx(dist, "DistributionName")[0] == machine:
                    base = winreg.QueryValueEx(dist, "BasePath")[0].removeprefix("\\\\?\\")
                    return os.path.join(base, "ext4.vhdx")
    sys.exit(f"WSL distro '{machine}' not found. Is this a WSL-backed Podman machine?")


def diskpart_compact(vhdx):
    script = f'select vdisk file="{vhdx}"\nattach vdisk readonly\ncompact vdisk\ndetach vdisk\n'
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
        f.write(script)
    try:
        # WSL can hold the file for a few seconds after --shutdown.
        for _ in range(3):
            if subprocess.run(["diskpart", "/s", f.name]).returncode == 0:
                return
            time.sleep(5)
        sys.exit(f"diskpart could not compact {vhdx}. Close anything using WSL and retry.")
    finally:
        os.unlink(f.name)


def plan(system, machine, containers=False, volumes=False, skip_prune=False,
         skip_compact=False, vhdx=None):
    """Return the steps as (label, argv-list or callable). Pure, so it is testable."""
    steps = []
    if not skip_prune:
        if containers:
            steps.append(("Prune stopped containers", ["podman", "container", "prune", "-f"]))
        steps.append(("Prune unused images", ["podman", "image", "prune", "-a", "-f"]))
        if volumes:
            steps.append(("Prune unused volumes", ["podman", "volume", "prune", "-f"]))
    if skip_compact or system == "Linux":
        return steps
    steps.append(("fstrim inside machine",
                  ["podman", "machine", "ssh", machine, "sudo", "fstrim", "-av"]))
    if system == "Windows":
        steps += [
            ("Stop machine", ["podman", "machine", "stop", machine]),
            ("wsl --shutdown (stops ALL WSL distros)", ["wsl", "--shutdown"]),
            ("Compact vhdx with diskpart", lambda: diskpart_compact(vhdx)),
            ("Start machine", ["podman", "machine", "start", machine]),
        ]
    return steps


def gb(path):
    return round(os.path.getsize(path) / 1024**3, 2)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--machine", default="podman-machine-default")
    p.add_argument("--containers", action="store_true", help="also prune stopped containers")
    p.add_argument("--volumes", action="store_true", help="also prune unused volumes")
    p.add_argument("--skip-prune", action="store_true", help="reclaim only, delete nothing")
    p.add_argument("--skip-compact", action="store_true", help="prune only")
    p.add_argument("--dry-run", action="store_true", help="show sizes and plan, change nothing")
    a = p.parse_args()

    if not shutil.which("podman"):
        sys.exit("podman not found on PATH.")
    system = platform.system()
    uses_machine = system != "Linux"
    vhdx = vhdx_path(a.machine) if system == "Windows" else None
    if system == "Windows" and not a.skip_compact and not a.dry_run:
        import ctypes

        if not ctypes.windll.shell32.IsUserAnAdmin():
            sys.exit("Compaction needs an Administrator shell. Re-run elevated, or pass --skip-compact.")

    steps = plan(system, a.machine, a.containers, a.volumes, a.skip_prune, a.skip_compact, vhdx)
    if uses_machine and steps:
        state = subprocess.run(["podman", "machine", "inspect", "--format", "{{.State}}", a.machine],
                               capture_output=True, text=True).stdout.strip()
        if state != "running":
            steps.insert(0, ("Start machine", ["podman", "machine", "start", a.machine]))

    print(f"OS      : {system}" + (f"  machine: {a.machine}" if uses_machine else ""), flush=True)
    if vhdx:
        before = gb(vhdx)
        print(f"VHDX    : {vhdx} ({before} GB on host)", flush=True)
    subprocess.run(["podman", "system", "df"])

    for label, cmd in steps:
        print(f"==> {label}", flush=True)
        if a.dry_run:
            continue
        if callable(cmd):
            cmd()
        else:
            subprocess.run(cmd, check=True)

    if a.dry_run:
        print("Dry run: nothing changed.")
        return
    subprocess.run(["podman", "system", "df"])
    if vhdx:
        after = gb(vhdx)
        print(f"VHDX on host: {before} GB -> {after} GB (freed {round(before - after, 2)} GB)")


if __name__ == "__main__":
    main()
