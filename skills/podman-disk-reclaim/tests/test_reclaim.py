import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from reclaim import plan  # noqa: E402

M = "podman-machine-default"


def labels(steps):
    return [label for label, _ in steps]


def test_linux_prunes_only():
    assert labels(plan("Linux", M)) == ["Prune unused images"]


def test_macos_trims_without_compact():
    assert labels(plan("Darwin", M)) == ["Prune unused images", "fstrim inside machine"]


def test_windows_full_pipeline_order():
    assert labels(plan("Windows", M, vhdx="x.vhdx")) == [
        "Prune unused images",
        "fstrim inside machine",
        "Stop machine",
        "wsl --shutdown (stops ALL WSL distros)",
        "Compact vhdx with diskpart",
        "Start machine",
    ]


def test_destructive_prunes_are_opt_in():
    default = labels(plan("Windows", M, vhdx="x.vhdx"))
    assert "Prune stopped containers" not in default
    assert "Prune unused volumes" not in default
    full = labels(plan("Darwin", M, containers=True, volumes=True))
    # containers before volumes, so volumes freed by removed containers get pruned too
    assert full.index("Prune stopped containers") < full.index("Prune unused volumes")


def test_skip_prune_deletes_nothing():
    for system in ("Linux", "Darwin", "Windows"):
        assert not any("Prune" in l for l in labels(plan(system, M, skip_prune=True, vhdx="x")))


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
    print("ok")
