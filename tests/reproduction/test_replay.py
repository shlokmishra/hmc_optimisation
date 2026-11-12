"""Check full-cell replay, including author data and shared RNG consumption."""

import ast
import re

import matplotlib.pyplot as plt
import numpy as np
import pytest
from threadpoolctl import threadpool_limits

from rhgd_reproduction.replay import load_sources, numeric_snapshot, prepare, run_case


def test_all_presets_preserve_author_functions():
    manifest, sources = load_sources()
    for case in manifest["cases"].values():
        source = sources[case["cell"]]
        original = [ast.dump(n) for n in ast.parse(source).body if isinstance(n, ast.FunctionDef)]
        for iterations in (None, 12):
            tree, _ = prepare(source, case, iterations)
            actual = [ast.dump(n) for n in tree.body if isinstance(n, ast.FunctionDef)]
            assert actual == original


def test_table_three_settings():
    manifest, sources = load_sources()
    for name in ("fig5-left", "fig5-right"):
        case = manifest["cases"][name]
        tree, _ = prepare(sources[2], case)
        assignments = {
            n.targets[0].id: n.value
            for n in tree.body
            if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)
        }
        smoothness = ast.literal_eval(assignments["lamda_max"])
        assert ast.literal_eval(assignments["eta"]) == 1 / (8 * smoothness)
        assert ast.literal_eval(assignments["h"]) == 1 / (8 * np.sqrt(smoothness))
        nag_call = next(
            n.value
            for n in tree.body
            if isinstance(n, ast.Assign)
            and isinstance(n.value, ast.Call)
            and isinstance(n.value.func, ast.Name)
            and n.value.func.id == "run_nag"
        )
        assert ast.literal_eval(nag_call.args[2]) == 1 / (16 * smoothness)


@pytest.mark.parametrize(
    "case_name",
    [
        "fig1-left",
        "fig1-middle",
        "fig1-right",
        "fig2-left",
        "fig2-right",
        "fig6-left",
        "fig6-right",
    ],
)
def test_full_cell_matches_direct_author_execution(case_name, tmp_path, monkeypatch):
    manifest, sources = load_sources()
    case = manifest["cases"][case_name]
    output = tmp_path / case_name
    metadata = run_case(case_name, output, smoke_iterations=12)
    assert metadata["status"] == "complete"
    assert metadata["mode"] == "smoke_not_paper_result"
    assert metadata["paper_agreement"] == "not_assessed"
    assert len(metadata["figures"]) == 1
    # Independent textual preparation: only display compatibility and short-run settings.
    source = "\n".join(
        line for line in sources[case["cell"]].splitlines() if "set_matplotlib_formats" not in line
    )
    source = re.sub(r"^num_iters\s*=.*$", "num_iters = 12", source, flags=re.MULTILINE)
    if case["cell"] == 1:
        source = re.sub(r"^alphas\s*=.*$", "alphas = [0.01]", source, flags=re.MULTILINE)
    namespace = {}
    monkeypatch.setattr(plt, "show", lambda: None)
    random_state = np.random.get_state()
    try:
        with threadpool_limits(limits=1):
            exec(compile(source, "direct_author_cell", "exec"), namespace)
        expected, _ = numeric_snapshot(namespace)
        with np.load(output / "figure-01-arrays.npz", allow_pickle=False) as actual:
            assert set(actual.files) == set(expected)
            for key in expected:
                np.testing.assert_array_equal(actual[key], expected[key], err_msg=key)
        assert (output / "figure-01.pdf").is_file()
        assert (output / "figure-01-curves.npz").is_file()
    finally:
        np.random.set_state(random_state)
        plt.close("all")
    with pytest.raises(FileExistsError):
        run_case(case_name, output, smoke_iterations=12)


def test_full_run_requires_allocation(tmp_path, monkeypatch):
    monkeypatch.delenv("SLURM_JOB_ID", raising=False)
    with pytest.raises(RuntimeError, match="Slurm"):
        run_case("fig1-left", tmp_path / "not_created")
    assert not (tmp_path / "not_created").exists()


def test_unknown_override_rejected():
    with pytest.raises(ValueError, match="Unapplied"):
        prepare("num_iters = 10", {"assignments": {"typo": 1}})
