import csv
import hashlib
import json
import sys
from subprocess import run

import numpy as np
import pytest

from stat605.spectral_suite import CONFIGS, ROOT, spectral_suite


def test_cli_saves_matched_cases_and_rebuilds_table_without_optimization(tmp_path):
    config = json.loads((CONFIGS / "spectral_check.json").read_text())
    config.update(
        spectra=["clustered"],
        starts=["scaled_common", "equal"],
        seeds={"B": [None], "CAGD": [1, 2, 3]},
        gradient_budget=12,
        targets=[1e-10],
    )
    cfg = tmp_path / "my-config.json"
    cfg.write_text(json.dumps(config))
    out = tmp_path / "run"
    cli = [sys.executable, str(ROOT / "scripts/stat605.py")]
    run([*cli, "spectral", "--config", cfg, "--output", out], check=True)
    meta = json.loads((out / "summary.json").read_text())
    assert (out / "config.json").read_bytes() == cfg.read_bytes()
    assert meta["config_sha256"] == hashlib.sha256(cfg.read_bytes()).hexdigest()
    assert meta["status"] == "passed"
    assert len(meta["runs"]) == 8
    assert all(r["numerical_gradients"] == 12 for r in meta["runs"])
    assert [p["initial_loss"] for p in meta["problems"]] == pytest.approx([1, 1])
    hashes = [p["array_sha256"] for p in meta["problems"]]
    assert hashes[0]["A"] == hashes[1]["A"]
    assert hashes[0]["x0"] != hashes[1]["x0"]
    for record in meta["runs"]:
        with np.load(out / record["trace"], allow_pickle=False) as trace:
            assert trace["iteration"][-1] == record["updates"]
            assert trace["objectives"][-1] == record["objectives"]
    with pytest.raises(FileExistsError):
        spectral_suite(out, cfg)
    rebuilt = tmp_path / "rebuilt"
    run([*cli, "spectral-report", "--run", out, "--output", rebuilt], check=True)
    for name in ("targets.csv", "work_to_target.csv"):
        assert (out / name).read_bytes() == (rebuilt / name).read_bytes()
    with (rebuilt / "work_to_target.csv").open() as file:
        groups = list(csv.DictReader(file))
    assert len(groups) == 4
    assert sum(int(row["runs"]) for row in groups) == 8
    for name in ("loss_gradients", "loss_iterations", "modal_energy", "modal_power"):
        assert (rebuilt / f"{name}.png").read_bytes().startswith(b"\x89PNG")


def test_grace_pilot_requires_allocation_before_creating_output(tmp_path, monkeypatch):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    path = tmp_path / "pilot"
    with pytest.raises(ValueError, match="Grace Slurm allocation"):
        spectral_suite(path, CONFIGS / "spectral_pilot.json")
    assert not path.exists()
