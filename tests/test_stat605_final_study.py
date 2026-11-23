"""Protocol selection and independent audit checks without expensive benchmarks."""

import json

import numpy as np
import pytest

from stat605.final_study import METHOD_NAMES, audit, cases, paths, select
from stat605.spectral_suite import _digest


def record(hit=None, failure=False, gap=1):
    return {
        "status": "failure" if failure else "budget_complete",
        "crossings": [{}, {"sustained": None if hit is None else {"gradients": hit}}],
        "final_relative_gap": gap,
    }


def test_selection_penalties_and_ties():
    index, scores = select([[record(failure=True)], [record()], [record(hit=20000)]])
    assert index == 2
    assert [s[0] for s in scores] == [80000, 40000, 20000]
    assert select([[record(gap=0.2)], [record(gap=0.1)]])[0] == 1
    assert select([[record()], [record()]])[0] == 0


def test_design_and_denominators():
    assert len(METHOD_NAMES) == 14 and len(list(paths())) == 22
    train, final = list(cases(True)), list(cases())
    assert len(train) == len(final) == 6
    assert {c[2] for c in train} == {"1605", "2605"}
    assert {c[2] for c in final} == {"scaled_common", "equal"}
    for _, _, _, p in train + final:
        assert p.A.dtype == p.x0.dtype == np.float64
        assert 0.5 * p.x0 @ p.A @ p.x0 == pytest.approx(1)
    # Starts change without changing the retained matrices or basis.
    np.testing.assert_array_equal(train[0][3].A, final[0][3].A)
    np.testing.assert_array_equal(train[0][3].basis, final[0][3].basis)


def test_independent_audit_rejects_crossing_and_hash_changes(tmp_path):
    trace = tmp_path / "trace.npz"
    np.savez(trace, loss=[1.0, 0.01, 0.2, 0.001], gradients=[0, 2, 4, 6])
    crossing = {
        "target": 0.1,
        "first": {"iteration": 1, "gradients": 2},
        "sustained": {"iteration": 3, "gradients": 6},
    }
    summary = {
        "runs": [
            {
                "trace": trace.name,
                "trace_sha256": _digest(trace),
                "crossings": [crossing],
                "status": "budget_complete",
                "numerical_gradients": 6,
                "gradient_budget": 6,
            }
        ]
    }
    path = tmp_path / "summary.json"
    path.write_text(json.dumps(summary))
    audit(tmp_path)
    crossing["sustained"]["gradients"] = 2
    path.write_text(json.dumps(summary))
    with pytest.raises(ValueError, match="Crossing mismatch"):
        audit(tmp_path)
    trace.write_bytes(b"changed")
    with pytest.raises(ValueError, match="hash mismatch"):
        audit(tmp_path)
