import json

import numpy as np
import pytest

from stat605.smoke import smoke


def test_smoke_is_self_contained_reproducible_and_cost_bounded(tmp_path):
    first = smoke(tmp_path / "first")
    second = smoke(tmp_path / "second")
    assert first["purpose"] == "software_smoke_not_research_evidence"
    assert first["status"] == second["status"] == "passed"
    for record in first["runs"]:
        assert record["numerical_gradients"] == 200
        assert record["updates"] == (100 if record["method"] in ("B", "RHGD") else 200)
        name = record["method"] + ".npz"
        with np.load(tmp_path / "first" / name) as a, np.load(tmp_path / "second" / name) as b:
            np.testing.assert_array_equal(a["f"], b["f"])
            assert np.all(np.isfinite(a["f"]))
    saved = json.loads((tmp_path / "first/summary.json").read_text())
    assert saved["source_sha256"] == first["source_sha256"]
    with pytest.raises(FileExistsError):
        smoke(tmp_path / "first")
