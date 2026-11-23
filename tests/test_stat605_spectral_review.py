"""Regressions for paid failures, bounded local work and saved evidence."""

import hashlib
import json
import subprocess
import sys

import numpy as np
import pytest

from stat605 import benchmark, spectral_suite
from stat605.benchmark import Method, Step, run_benchmark
from stat605.problems import make_problem
from stat605.spectral_reporting import write_report


@pytest.mark.parametrize("phase", ["prepare", "step", "initial loss", "endpoint loss"])
@pytest.mark.parametrize("error", [FloatingPointError, OverflowError])
def test_numerical_callback_failures_return_paid_work_and_no_sustained_hit(
    phase, error, monkeypatch
):
    problem = make_problem("linear", "equal", source="generated", dimension=2, mu=1, L=2)

    def prepare(oracle, x, settings):
        if phase == "prepare":
            oracle.grad(x)
            raise error("paid setup failure")

        def step(x, k):
            oracle.grad(x)
            if phase == "step":
                raise error("paid update failure")
            return Step(x.copy(), x.copy())

        return step

    loss = benchmark.BenchmarkOracle.loss

    def failing_loss(self, x):
        value = loss(self, x)
        if (phase == "initial loss" and self.objectives == 1) or (
            phase == "endpoint loss" and self.objectives == 2
        ):
            raise error("paid diagnostic failure")
        return value

    monkeypatch.setattr(benchmark.BenchmarkOracle, "loss", failing_loss)
    arrays, record = run_benchmark(
        problem,
        Method("callback", prepare, 1),
        gradient_budget=2,
        eta=0.1,
        supplied_mu=None,
        targets=[2.0],
    )
    assert record["status"] == "failure" and "failure" in record["failure"]
    assert record["updates"] == 0
    assert record["crossings"][0]["sustained"] is None
    expected_gradients = 0 if phase == "initial loss" else 1
    assert (
        record["numerical_gradients"]
        == record["charged_unfinished_gradients"]
        == expected_gradients
    )
    assert record["objectives"] == (2 if phase == "endpoint loss" else 1)
    np.testing.assert_array_equal(arrays["x_final"], problem.x0)
    if phase == "endpoint loss":
        np.testing.assert_array_equal(arrays["failed_x"], problem.x0)
        assert np.isnan(arrays["failed_loss"])


def test_nonfinite_trial_retains_raw_state_and_cost():
    problem = make_problem("linear", "equal", source="generated", dimension=2, mu=1, L=2)
    arrays, record = run_benchmark(
        problem,
        "AGD",
        gradient_budget=2,
        eta=1e250,
        supplied_mu=1.0,
    )
    assert record["status"] == "failure" and record["numerical_gradients"] == 1
    assert not np.isfinite(arrays["failed_loss"])
    assert arrays["failed_x"].shape == problem.x0.shape


@pytest.mark.parametrize("change", ["dimension", "gradients", "paths", "negative budget", "target"])
def test_oversized_or_invalid_local_configuration_stops_before_output(tmp_path, change):
    config = json.loads((spectral_suite.CONFIGS / "spectral_check.json").read_text())
    if change == "dimension":
        config["problem"]["dimension"] = 10000
    elif change == "gradients":
        config["gradient_budget"] = 10**9
    elif change == "paths":
        config["seeds"]["RHGD"] = list(range(1000))
    elif change == "negative budget":
        config["gradient_budget"] = -1
    else:
        config["targets"] = [float("nan")]
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    output = tmp_path / "run"
    with pytest.raises(ValueError):
        spectral_suite.spectral_suite(output, path)
    assert not output.exists()


def test_partial_summary_retains_each_finished_path_and_trace_hash(tmp_path, monkeypatch):
    config = json.loads((spectral_suite.CONFIGS / "spectral_check.json").read_text())
    config.update(
        spectra=["linear"], starts=["equal"], seeds={"AGD": [None], "B": [None]}, gradient_budget=2
    )
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    original = spectral_suite.run_benchmark
    calls = 0

    def interrupted(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("simulate stopped job")
        return original(*args, **kwargs)

    monkeypatch.setattr(spectral_suite, "run_benchmark", interrupted)
    output = tmp_path / "run"
    with pytest.raises(KeyboardInterrupt):
        spectral_suite.spectral_suite(output, path)
    summary = json.loads((output / "summary.json").read_text())
    assert summary["status"] == "incomplete" and len(summary["runs"]) == 1
    record = summary["runs"][0]
    assert record["numerical_gradients"] == 2
    assert (
        record["trace_sha256"]
        == hashlib.sha256((output / record["trace"]).read_bytes()).hexdigest()
    )


def test_reporting_rejects_modified_trace_before_creating_output(tmp_path):
    trace = tmp_path / "trace.npz"
    trace.write_bytes(b"modified saved trace")
    summary = {
        "status": "passed",
        "config": {},
        "runs": [{"trace": trace.name, "trace_sha256": "original digest"}],
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    output = tmp_path / "report"
    with pytest.raises(ValueError, match="Trace digest"):
        write_report(tmp_path, output)
    assert not output.exists()


def test_combined_cli_lists_all_contributed_commands():
    result = subprocess.run(
        [sys.executable, str(spectral_suite.ROOT / "scripts/stat605.py"), "--help"],
        check=True,
        capture_output=True,
        text=True,
    )
    for name in (
        "smoke",
        "fixed-time-smoke",
        "agd",
        "spectral",
        "spectral-design",
        "spectral-report",
    ):
        assert name in result.stdout
