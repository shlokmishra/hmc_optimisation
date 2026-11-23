import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from stat605 import agd, agd_experiments
from stat605.agd import CountingOracle, quadratic_oracle, run_agd
from stat605.agd_experiments import crossings, run_config, summarize

ROOT = Path(__file__).resolve().parents[1]


def test_late_failure_retains_first_crossing_but_never_claims_sustained_success():
    calls = 0

    def loss(x):
        nonlocal calls
        calls += 1
        return 0.0 if calls <= 3 else np.nan

    oracle = CountingOracle(loss, lambda x: np.zeros_like(x))
    arrays, meta = run_agd(oracle, np.ones(1), 0.1, 10, restart="function")
    result = summarize(arrays, meta, [1e-8])["targets"]["1e-08"]
    assert meta["status"] == "failure" and meta["updates"] == 2
    assert meta["gradients"] == 3 and meta["objectives"] == 4
    assert meta["charged_unfinished_gradients"] == 1
    assert result["first"]["gradients"] == 0 and result["sustained"] is None
    assert np.isnan(arrays["failed_f"])


def test_nonfinite_initial_objective_is_a_failure_even_without_updates():
    oracle = CountingOracle(lambda x: -np.inf, lambda x: np.zeros_like(x))
    arrays, meta = run_agd(oracle, np.ones(1), 0.1, 0)
    assert meta["status"] == "failure" and meta["gradients"] == 0 and meta["objectives"] == 1
    result = summarize(arrays, meta, [1e-8])["targets"]["1e-08"]
    assert result == {"first": None, "sustained": None}


def test_nonfinite_extrapolation_is_not_returned_as_a_completed_state(monkeypatch):
    monkeypatch.setattr(agd, "momentum", lambda *args: np.inf)
    arrays, meta = run_agd(quadratic_oracle(np.eye(1)), np.ones(1), 0.1, 1)
    assert meta["status"] == "failure" and meta["updates"] == 0
    assert meta["gradients"] == 1 and meta["objectives"] == 2
    assert meta["charged_unfinished_gradients"] == 1
    np.testing.assert_array_equal(arrays["x_final"], [1.0])
    assert np.isfinite(arrays["failed_x"]).all() and not np.isfinite(arrays["failed_y"]).all()


def test_raised_numerical_callback_keeps_paid_work():
    def gradient(x):
        raise FloatingPointError("gradient failed")

    arrays, meta = run_agd(CountingOracle(lambda x: 0.5 * x @ x, gradient), np.ones(1), 0.1, 2)
    assert meta["status"] == "failure" and "gradient failed" in meta["failure"]
    assert meta["gradients"] == meta["charged_unfinished_gradients"] == 1
    assert meta["objectives"] == 1 and len(arrays["f"]) == 1


def test_reusing_an_oracle_reports_each_runs_actual_work_separately():
    oracle = quadratic_oracle(np.eye(1))
    first, a = run_agd(oracle, np.ones(1), 0.1, 5, restart="function")
    second, b = run_agd(oracle, np.ones(1), 0.1, 5, restart="function")
    for meta in (a, b):
        assert meta["gradients"] == 5 and meta["objectives"] == 6
        assert meta["controller_objectives"] == 5 and meta["charged_unfinished_gradients"] == 0
    np.testing.assert_array_equal(first["f"], second["f"])
    assert oracle.gradients == 10 and oracle.objectives == 12


@pytest.mark.parametrize(
    "kwargs",
    [
        {"iterations": -1},
        {"iterations": 1.5},
        {"iterations": True},
        {"eta": 0},
        {"eta": np.inf},
        {"eta": np.nan},
        {"q": np.nan},
    ],
)
def test_invalid_steps_and_nonfinite_parameters_are_rejected_before_work(kwargs):
    args = dict(eta=0.1, iterations=2)
    args.update(kwargs)
    oracle = quadratic_oracle(np.eye(1))
    with pytest.raises(ValueError):
        run_agd(oracle, np.ones(1), **args)
    assert oracle.gradients == oracle.objectives == 0


def test_crossings_do_not_treat_nonfinite_values_as_accuracy():
    assert crossings(np.array([np.inf, -np.inf, np.nan]), 1e-8) == (None, None)


def test_fixture_hash_mismatch_is_rejected_before_loading(monkeypatch, tmp_path):
    monkeypatch.setattr(agd_experiments, "FIXTURES", tmp_path)
    (tmp_path / "altered.npz").write_bytes(b"changed input")
    (tmp_path / "PROVENANCE.json").write_text(
        json.dumps({"fixtures": [{"file": "altered.npz", "sha256": "not-the-actual-hash"}]})
    )
    with pytest.raises(ValueError, match="hash mismatch"):
        agd_experiments.load_problem({"fixture": "altered.npz", "mu": 0.1, "L": 1.0})


def test_cli_preserves_all_commands_and_requires_allocation_for_full_agd(tmp_path):
    script = ROOT / "scripts/stat605.py"
    help_result = subprocess.run(
        [sys.executable, str(script), "--help"], capture_output=True, check=True
    )
    assert b"fixed-time-smoke" in help_result.stdout and b"agd" in help_result.stdout
    env = os.environ.copy()
    env.pop("SLURM_JOB_ID", None)
    config = ROOT / "configs/stat605/agd_sensitivity.json"
    for smoke in (False, True):
        output = tmp_path / str(smoke)
        args = [
            sys.executable,
            str(script),
            "agd",
            "--config",
            str(config),
            "--output",
            str(output),
        ]
        if smoke:
            args.append("--smoke")
        result = subprocess.run(args, env=env, capture_output=True)
        assert result.returncode != 0 and not output.exists()
        assert b"capped" in result.stderr or b"require Slurm" in result.stderr


def test_bounded_config_records_input_provenance_and_controller_costs(tmp_path):
    meta = run_config(ROOT / "configs/stat605/agd_smoke.json", tmp_path / "out", smoke=True)
    assert (
        meta["execution"] == "software_smoke_not_research_evidence" and meta["status"] == "passed"
    )
    assert len(meta["runs"]) == 8 and sum(r["gradients"] for r in meta["runs"]) == 256
    for row in meta["runs"]:
        assert row["objectives"] == 33 and row["input_sha256"]["fixture_file"]
        assert row["controller_objectives"] == (32 if row["restart"] == "function" else 0)


def test_plot_script_refuses_to_overwrite_existing_result_directory(tmp_path):
    out = tmp_path / "existing"
    out.mkdir()
    sentinel = out / "original.png"
    sentinel.write_bytes(b"preserve existing figure")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/plot_agd_summary.py"),
            "--replication",
            str(tmp_path / "no-trace"),
            "--sensitivity",
            str(tmp_path / "no-trace"),
            "--output",
            str(out),
        ],
        capture_output=True,
    )
    assert result.returncode != 0 and sentinel.read_bytes() == b"preserve existing figure"
