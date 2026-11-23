import csv
import json

import matplotlib.pyplot as plt
import numpy as np
import pytest

from stat605 import spectral_reporting
from stat605.spectral_reporting import _drawing_indices, write_report


def test_reports_retain_seeds_budget_censoring_and_failed_work(tmp_path):
    runs = []
    for seed, status, first, sustained, charged in [
        (1, "budget_complete", 1, 2, 2),
        (2, "budget_complete", 2, 2, 2),
        (3, "failure", 1, None, 2),
        (4, "budget_complete", None, None, 2),
        (5, "failure", None, None, 1),
    ]:
        filename = f"seed-{seed}.npz"
        n = charged + 1 if status == "budget_complete" else charged
        np.savez(
            tmp_path / filename,
            loss=np.array([1.0, 0.2, 0.1])[:n],
            gradients=np.arange(n),
            iteration=np.arange(n),
        )

        def hit(index):
            return None if index is None else {"iteration": index, "gradients": index}

        runs.append(
            {
                "spectrum": "linear",
                "start": "common",
                "method": "CAGD",
                "seed": seed,
                "status": status,
                "failure": "nonfinite" if status == "failure" else None,
                "updates": n - 1,
                "numerical_gradients": charged,
                "literal_gradient_requests": charged * 2,
                "objectives": n,
                "reset_count": 0,
                "trace": filename,
                "crossings": [{"target": 0.25, "first": hit(first), "sustained": hit(sustained)}],
            }
        )
    summary = {
        "status": "failure",
        "config": {"targets": [0.25], "purpose": "local_check"},
        "problems": [
            {
                "spectrum": "linear",
                "start": "common",
                "eigenvalues": [1, 10],
                "initial_modal_energy": [0, 1],
            }
        ],
        "runs": runs,
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    output = tmp_path / "rebuilt"
    write_report(tmp_path, output)
    with (output / "work_to_target.csv").open() as stream:
        (group,) = csv.DictReader(stream)
    assert group["runs"] == "5"
    assert group["failures"] == "2"
    assert group["first_median_gradients"] == "2"
    assert group["sustained_median_gradients"] == ""
    assert group["sustained_hits"] == "2"
    assert group["sustained_failed_before_hit"] == "2"
    assert group["sustained_budget_censored"] == "1"
    with (output / "targets.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    assert rows[2]["first_status"] == "hit"
    assert rows[2]["sustained_status"] == "failed"
    assert rows[2]["updates"] == "1" and rows[2]["total_gradients"] == "2"
    assert rows[3]["first_status"] == "budget_censored"
    for fig in ("loss_gradients", "loss_iterations", "modal_energy"):
        assert (output / f"{fig}.png").read_bytes().startswith(b"\x89PNG")
    assert not (output / "modal_power.png").exists()
    with pytest.raises(FileExistsError):
        write_report(tmp_path, output)


def test_incomplete_suite_does_not_generate_partial_group_statistics(tmp_path):
    (tmp_path / "summary.json").write_text(json.dumps({"status": "incomplete"}))
    with pytest.raises(ValueError, match="finished suite"):
        write_report(tmp_path)
    assert not (tmp_path / "work_to_target.csv").exists()


def test_rendering_extrema_and_endpoints_survive_reduction():
    loss = np.ones(20000)
    loss[6534] = 10
    loss[18002] = -1
    kept = _drawing_indices(loss)
    assert {0, 6534, 18002, len(loss) - 1} <= set(kept)
    assert np.all(np.diff(kept) > 0)


def test_work_axes_include_initial_state_and_share_loss_ranges_by_start(tmp_path, monkeypatch):
    runs = []
    for start, losses in [("common", [10000.0, 2.0, -1e-9]), ("equal", [1.0, 0.2, 0.1])]:
        filename = start + ".npz"
        np.savez(tmp_path / filename, gradients=[0, 10, 2000], loss=losses)
        for spectrum in ("linear", "log"):
            runs.append(
                dict(
                    start=start,
                    spectrum=spectrum,
                    method="AGD",
                    seed=None,
                    status="budget_complete",
                    trace=filename,
                )
            )

    def check_figure(fig, output):
        try:
            common, other_common, equal, other_equal = fig.axes
            assert common.get_shared_y_axes().joined(common, other_common)
            assert equal.get_shared_y_axes().joined(equal, other_equal)
            assert not common.get_shared_y_axes().joined(common, equal)
            assert common.get_yscale() == "symlog"
            assert equal.get_yscale() == "log"
            assert common.get_ylim()[0] < 0
            for ax in fig.axes:
                assert ax.get_xscale() == "symlog"
                assert ax.get_xlim() == (0, 2000)
                assert {0, 10, 100, 2000} <= set(ax.get_xticks())
        finally:
            plt.close(fig)

    monkeypatch.setattr(spectral_reporting, "_save_figure", check_figure)
    spectral_reporting._loss_figure(
        tmp_path, tmp_path / "figure.png", runs, "gradients", "Grace pilot", [1e-4]
    )
