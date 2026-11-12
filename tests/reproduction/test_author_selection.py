"""The direct verifier's selected panel must equal the original loop's first branch."""

import ast
import importlib.util
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from rhgd_reproduction.replay import load_sources, numeric_snapshot

spec = importlib.util.spec_from_file_location(
    "author_verifier", Path(__file__).resolve().parents[2] / "scripts/verify_rhgd_author.py"
)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


def test_selected_panel_matches_original_first_branch(monkeypatch):
    manifest, sources = load_sources()
    original = "\n".join(
        line for line in sources[1].splitlines() if "set_matplotlib_formats" not in line
    )
    selected, changes = verifier.prepare_direct_source(sources[1], manifest["cases"]["fig1-middle"])
    assert changes == [
        {"kind": "panel_selection", "original_alphas": [0.01, 0.1, 1], "alphas": [0.01]}
    ]

    def functions(source):
        return [ast.dump(n) for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]

    assert functions(original) == functions(selected)

    class FirstPanelComplete(Exception):
        pass

    def stop_at_first_show():
        raise FirstPanelComplete

    snapshots = []
    state = np.random.get_state()
    monkeypatch.setattr(plt, "show", stop_at_first_show)
    try:
        for source in (original, selected):
            source = re.sub(r"^num_iters\s*=.*$", "num_iters = 12", source, flags=re.MULTILINE)
            namespace = {}
            with threadpool_limits(limits=1), pytest.raises(FirstPanelComplete):
                exec(compile(source, "direct_first_panel", "exec"), namespace)
            arrays, scalars = numeric_snapshot(namespace)
            assert scalars["alpha"] == 0.01
            arrays.pop("alphas")  # Selection metadata differs; numerical outputs must not.
            snapshots.append((arrays, scalars))
            plt.close("all")
        assert snapshots[0][1] == snapshots[1][1]
        assert snapshots[0][0].keys() == snapshots[1][0].keys()
        for key in snapshots[0][0]:
            np.testing.assert_array_equal(snapshots[0][0][key], snapshots[1][0][key], strict=True)
    finally:
        np.random.set_state(state)
        plt.close("all")


@pytest.mark.parametrize(
    "case",
    [
        {"cell": 1, "assignments": {"alphas": [0.02]}},
        {"cell": 1, "assignments": {"alphas": [0.01, 0.1]}},
        {"cell": 1, "assignments": {"num_iters": 12}},
        {"cell": 0, "assignments": {"alphas": [0.01]}},
        {"call_arguments": {"run_nag": {"2": 0.1}}},
    ],
)
def test_unsupported_changes_rejected(case):
    with pytest.raises(ValueError):
        verifier.prepare_direct_source("alphas = [0.01, 0.1, 1]", case)


def test_default_source_preserved_except_display():
    _, sources = load_sources()
    source, changes = verifier.prepare_direct_source(sources[0], {"assignments": {}})
    assert source == "\n".join(
        line for line in sources[0].splitlines() if "set_matplotlib_formats" not in line
    )
    assert changes == []


def test_weak_million_override_only_changes_iteration_assignment():
    manifest, sources = load_sources()
    source, changes = verifier.prepare_direct_source(sources[2], manifest["cases"]["fig1-right"])
    original = "\n".join(
        line for line in sources[2].splitlines() if "set_matplotlib_formats" not in line
    )
    assert source == original.replace("num_iters = int(1e4)", "num_iters = 1000000")
    assert changes == [
        {"kind": "user_iteration_override", "original_num_iters": 10000, "num_iters": 1000000}
    ]
    with pytest.raises(ValueError, match="pinned"):
        verifier.prepare_direct_source(source, manifest["cases"]["fig1-right"])
    with pytest.raises(ValueError):
        verifier.prepare_direct_source(sources[2], {"cell": 2, "assignments": {"num_iters": 20000}})
