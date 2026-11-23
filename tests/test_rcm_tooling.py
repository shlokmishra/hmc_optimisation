import csv
import importlib.util
import io
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("rcm_benchmark", ROOT / "scripts/benchmark_rcm.py")
benchmark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(benchmark)


def test_budget_pays_for_discarded_trial_without_exposing_an_unfinished_restart():
    trace = io.StringIO()
    row = benchmark.run_case(np.eye(1), np.ones(1), 0.5, "mmd-dr", 4, csv.writer(trace), "hand")
    # At step 3 the rejected trial spends gradient 4; the fallback would require
    # gradient 5. Preserve the last fully observed iterate (step 2), paying all 4.
    assert row["status"] == "budget_reached" and row["gradients_spent"] == 4
    assert row["last_iteration"] == 2 and row["gradients_at_last_iterate"] == 3
    assert row["final_gap"] == 0.5 * (5 / 16) ** 2
    assert row["objectives"] == 3 and row["restarts"] == 0
    assert len(trace.getvalue().splitlines()) == 3


def test_benchmark_retains_failure_status_and_spent_gradient():
    row = benchmark.run_case(
        np.array([[np.inf]]), np.ones(1), 0.5, "kin", 4, csv.writer(io.StringIO()), "bad"
    )
    assert row["status"] == "failed" and "Nonfinite" in row["reason"]
    assert row["gradients_spent"] == 1 and row["last_iteration"] is None
    assert row["final_gap"] is None


def test_fixture_regeneration_matches_saved_arrays_and_refuses_overwrite(tmp_path):
    script = ROOT / "scripts/prepare_rcm_quadratic.py"
    out = tmp_path / "fixture.npz"
    subprocess.run(
        [sys.executable, str(script), "--output", str(out)], check=True, capture_output=True
    )
    original = ROOT / "configs/stat605/fixtures/rcm_section5_1_seed605.npz"
    with np.load(out, allow_pickle=False) as actual, np.load(original, allow_pickle=False) as saved:
        assert set(actual.files) == set(saved.files)
        for key in saved.files:
            if saved[key].dtype.kind == "f":
                # Original and guarded generators agree bitwise on Grace. The
                # submitted input differs by <=2 ULP under this runtime; require
                # close regeneration, while keeping its exact committed bytes.
                np.testing.assert_array_max_ulp(actual[key], saved[key], maxulp=4)
            else:
                np.testing.assert_array_equal(actual[key], saved[key])
    before = out.read_bytes()
    retry = subprocess.run([sys.executable, str(script), "--output", str(out)], capture_output=True)
    assert retry.returncode != 0 and b"Refusing to overwrite" in retry.stderr
    assert out.read_bytes() == before


def test_full_benchmark_requires_allocation_and_smoke_has_a_ceiling(tmp_path, monkeypatch):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    script = ROOT / "scripts/benchmark_rcm.py"
    for flags in ([], ["--smoke"]):
        output = tmp_path / ("smoke" if flags else "full")
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                "--gradient-budget",
                "301",
                "--output",
                str(output),
                *flags,
            ],
            capture_output=True,
        )
        assert result.returncode != 0 and not output.exists()
        assert b"Slurm" in result.stderr or b"capped" in result.stderr
