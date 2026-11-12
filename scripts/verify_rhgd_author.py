#!/usr/bin/env python3
"""Compare replay with direct author code at explicitly recorded settings."""

# ruff: noqa: E402
import argparse
import ast
import hashlib
import json
import os
import re
import sys
import time
import traceback
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from rhgd_reproduction.replay import load_sources, numeric_snapshot


def prepare_direct_source(source, case):
    """Prepare supported settings independently of the replay AST transformer."""
    source = "\n".join(line for line in source.splitlines() if "set_matplotlib_formats" not in line)
    assignments = case.get("assignments", {})
    if case.get("call_arguments"):
        raise ValueError("Direct verification does not support call-argument overrides")
    if not assignments:
        return source, []
    if case.get("cell") == 2 and assignments == {"num_iters": 1000000}:
        pattern = r"^num_iters\s*=\s*int\(1e4\)([^\n]*)$"
        source, count = re.subn(
            pattern, lambda m: "num_iters = 1000000" + m.group(1), source, flags=re.MULTILINE
        )
        if count != 1:
            raise ValueError("Expected the pinned cell-2 iteration assignment")
        return source, [
            {"kind": "user_iteration_override", "original_num_iters": 10000, "num_iters": 1000000}
        ]
    if case.get("cell") != 1 or set(assignments) != {"alphas"}:
        raise ValueError("Only selection of an existing cell-1 alpha panel is supported")
    selection = assignments["alphas"]
    pattern = r"^alphas\s*=\s*(\[[^\n]*?\])"
    matches = list(re.finditer(pattern, source, flags=re.MULTILINE))
    if len(matches) != 1:
        raise ValueError("Expected one top-level author alphas assignment")
    original = ast.literal_eval(matches[0].group(1))
    if not isinstance(selection, list) or len(selection) != 1 or selection[0] not in original:
        raise ValueError("Select exactly one alpha already present in the author cell")
    source = re.sub(pattern, lambda _: f"alphas = {selection!r}", source, flags=re.MULTILINE)
    return source, [{"kind": "panel_selection", "original_alphas": original, "alphas": selection}]


def verify(output):
    output = Path(output)
    metadata = json.loads((output / "metadata.json").read_text())
    manifest, sources = load_sources()
    case = manifest["cases"][metadata["case"]]
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Full author verification requires a Slurm allocation")
    if metadata["status"] != "complete" or metadata["mode"] != case.get("mode", "paper_parameters"):
        raise ValueError("Require a completed full panel")
    source = sources[case["cell"]]
    if (output / "original_cell.py").read_text() != source:
        raise ValueError("Replay source does not match the pinned author cell")
    # Independent textual preparation; no optimizer function body is modified.
    source, selections = prepare_direct_source(source, case)
    dest = output / "direct_author"
    dest.mkdir(exist_ok=False)
    (dest / "executed_cell.py").write_text(source + "\n")
    report = {
        "status": "running",
        "case": metadata["case"],
        "iterations": case["iterations"],
        "author_commit": manifest["commit"],
        "panel_selections": selections,
        "mode": metadata["mode"],
        "comparisons": [],
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "verification_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "scope": "exact equality on this environment; published-figure agreement separate",
    }
    namespace = {}

    def capture():
        arrays, scalars = numeric_snapshot(namespace)
        curves = {}
        fig = plt.gcf()
        for ai, ax in enumerate(fig.axes):
            for li, line in enumerate(ax.lines):
                curves[f"axes{ai}_line{li}_x"] = np.asarray(line.get_xdata())
                curves[f"axes{ai}_line{li}_y"] = np.asarray(line.get_ydata())
        for kind, expected in [("arrays", arrays), ("curves", curves)]:
            np.savez_compressed(dest / f"{kind}.npz", **expected)
            with np.load(output / f"figure-01-{kind}.npz", allow_pickle=False) as actual:
                if set(actual.files) != set(expected):
                    raise AssertionError(f"{kind}: array names differ")
                for name, value in expected.items():
                    np.testing.assert_array_equal(actual[name], value, err_msg=name, strict=True)
                    report["comparisons"].append(
                        {
                            "kind": kind,
                            "name": name,
                            "shape": list(value.shape),
                            "exact_equal": True,
                        }
                    )
        assert scalars["num_iters"] == case["iterations"]
        report["scalars"] = scalars
        fig.savefig(dest / "figure.png", dpi=150)
        plt.close(fig)

    old_show = plt.show
    start = time.perf_counter()
    caught = []
    try:
        plt.show = capture
        with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            exec(compile(source, str(dest / "executed_cell.py"), "exec"), namespace)
        assert report["comparisons"], "No figure comparison occurred"
        report["status"] = "passed"
    except BaseException:
        report["status"] = "failed"
        (dest / "failure.txt").write_text(traceback.format_exc())
        raise
    finally:
        plt.show = old_show
        plt.close("all")
        report["elapsed_seconds"] = time.perf_counter() - start
        report["warnings"] = list(dict.fromkeys(str(w.message) for w in caught))
        (output / "author_parity.json").write_text(json.dumps(report, indent=2) + "\n")
    print(f"Author parity: {report['status']}, {len(report['comparisons'])} arrays/curves")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    verify(parser.parse_args().output)
