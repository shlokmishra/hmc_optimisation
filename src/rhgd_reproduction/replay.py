"""Execute full author cells with explicit, recorded experiment-setting changes."""

import ast
import contextlib
import hashlib
import json
import os
import platform
import subprocess
import time
import traceback
import warnings
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from threadpoolctl import threadpool_info, threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "configs/reproduction/rhgd.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_sources(root=ROOT):
    """Reject a changed paper or notebook before executing any author code."""
    manifest = json.loads((root / "configs/reproduction/rhgd.json").read_text())
    for key in ("notebook", "paper"):
        if digest((root / manifest[key]).read_bytes()) != manifest[f"{key}_sha256"]:
            raise ValueError(f"Pinned {key} hash mismatch")
    checkout = root / manifest["notebook"]
    commit = subprocess.check_output(
        ["git", "-C", str(checkout.parent), "rev-parse", "HEAD"], text=True
    ).strip()
    if commit != manifest["commit"]:
        raise ValueError("Pinned upstream commit mismatch")
    notebook = json.loads(checkout.read_text())
    sources = ["".join(c["source"]) for c in notebook["cells"]]
    for entry in manifest["cells"]:
        if digest(sources[entry["index"]].encode()) != entry["sha256"]:
            raise ValueError("Pinned cell hash mismatch")
    return manifest, sources


class Settings(ast.NodeTransformer):
    """Change top-level experiment settings, never any author function body."""

    def __init__(self, assignments, call_arguments):
        self.assignments = assignments
        self.call_arguments = call_arguments
        self.changes = []
        self.seen = set()

    def visit_FunctionDef(self, node):
        return node

    def visit_ImportFrom(self, node):
        if node.module == "IPython.display" and [a.name for a in node.names] == [
            "set_matplotlib_formats"
        ]:
            self.changes.append({"line": node.lineno, "display_only": ast.unparse(node)})
            return None
        return node

    def visit_Expr(self, node):
        if (
            isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id == "set_matplotlib_formats"
        ):
            self.changes.append({"line": node.lineno, "display_only": ast.unparse(node)})
            return None
        return self.generic_visit(node)

    def visit_Assign(self, node):
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if name in self.assignments:
                self.changes.append(
                    {
                        "line": node.lineno,
                        "before": ast.unparse(node),
                        "value": self.assignments[name],
                    }
                )
                node.value = ast.parse(repr(self.assignments[name]), mode="eval").body
                self.seen.add(name)
        return self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in self.call_arguments:
            for index, value in self.call_arguments[node.func.id].items():
                self.changes.append(
                    {
                        "line": node.lineno,
                        "before": ast.unparse(node),
                        "argument": index,
                        "value": value,
                    }
                )
                node.args[int(index)] = ast.parse(repr(value), mode="eval").body
                self.seen.add(f"{node.func.id}:{index}")
        return self.generic_visit(node)


def prepare(source, case, smoke_iterations=None):
    assignments = dict(case.get("assignments", {}))
    if smoke_iterations is not None:
        if not 2 <= smoke_iterations <= 20:
            raise ValueError("Smoke iterations must be between 2 and 20")
        assignments["num_iters"] = smoke_iterations
    transform = Settings(assignments, case.get("call_arguments", {}))
    tree = ast.fix_missing_locations(transform.visit(ast.parse(source)))
    expected = set(assignments) | {
        f"{name}:{index}" for name, args in transform.call_arguments.items() for index in args
    }
    if transform.seen != expected:
        raise ValueError(f"Unapplied settings: {expected - transform.seen}")
    return tree, transform.changes


def numeric_snapshot(namespace):
    arrays, scalars = {}, {}
    for name, value in namespace.items():
        if name.startswith("_"):
            continue
        if isinstance(value, (np.ndarray, list, tuple)):
            try:
                array = np.asarray(value)
                if array.dtype.kind in "biufc" and array.size:
                    arrays[name] = array
            except (ValueError, TypeError):
                pass
        elif isinstance(value, (int, float, np.number)) and np.isfinite(value):
            scalars[name] = value.item() if isinstance(value, np.number) else value
    return arrays, scalars


def run_case(case_name, output, smoke_iterations=None):
    manifest, sources = load_sources()
    case = manifest["cases"][case_name]
    source = sources[case["cell"]]
    tree, changes = prepare(source, case, smoke_iterations)
    if smoke_iterations is None and not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Full figure runs require a Slurm allocation; use --smoke locally")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "original_cell.py").write_text(source)
    (output / "executed_cell.py").write_text(ast.unparse(tree) + "\n")
    (output / "source_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    namespace = {"__name__": "__rhgd_replay__"}
    metadata = {
        "status": "running",
        "case": case_name,
        "mode": "smoke_not_paper_result"
        if smoke_iterations
        else case.get("mode", "paper_parameters"),
        "paper_agreement": "not_assessed",
        "iterations": smoke_iterations or case["iterations"],
        "changes": changes,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "host": platform.node(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "runner_sha256": digest(Path(__file__).read_bytes()),
        "executed_ast_sha256": digest(ast.dump(tree).encode()),
        "figures": [],
    }

    def write_metadata():
        (output / "metadata.json").write_text(
            json.dumps(metadata, indent=2, allow_nan=False) + "\n"
        )

    def capture(*args, **kwargs):
        arrays, scalars = numeric_snapshot(namespace)
        for number in plt.get_fignums():
            fig = plt.figure(number)
            stem = f"figure-{len(metadata['figures']) + 1:02d}"
            curves = {}
            labels = {}
            for ai, ax in enumerate(fig.axes):
                for li, line in enumerate(ax.lines):
                    key = f"axes{ai}_line{li}"
                    curves[f"{key}_x"] = np.asarray(line.get_xdata())
                    curves[f"{key}_y"] = np.asarray(line.get_ydata())
                    labels[key] = line.get_label()
            fig.savefig(output / f"{stem}.png", dpi=150)
            fig.savefig(output / f"{stem}.pdf")
            np.savez_compressed(output / f"{stem}-arrays.npz", **arrays)
            np.savez_compressed(output / f"{stem}-curves.npz", **curves)
            metadata["figures"].append(
                {
                    "stem": stem,
                    "labels": labels,
                    "scalars": scalars,
                    "nonfinite_counts": {
                        k: int(np.count_nonzero(~np.isfinite(v))) for k, v in arrays.items()
                    },
                }
            )
            plt.close(fig)
        write_metadata()

    write_metadata()
    start = time.perf_counter()
    random_state = np.random.get_state()
    old_show = plt.show
    caught = []
    try:
        # The command is a dedicated process; close any preexisting figures before capture.
        plt.close("all")
        plt.show = capture
        with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
            metadata["threadpools"] = threadpool_info()
            warnings.simplefilter("always")
            with (output / "stdout.txt").open("w") as log, contextlib.redirect_stdout(log):
                exec(compile(tree, str(output / "original_cell.py"), "exec"), namespace)
        if namespace["num_iters"] != metadata["iterations"]:
            raise ValueError("Executed iteration count differs from manifest")
        if not metadata["figures"]:
            raise ValueError("Author cell produced no figure")
        metadata["status"] = "complete"
    except BaseException:
        metadata["status"] = "failed"
        (output / "failure.txt").write_text(traceback.format_exc())
        raise
    finally:
        plt.show = old_show
        plt.close("all")
        np.random.set_state(random_state)
        metadata["elapsed_seconds"] = time.perf_counter() - start
        metadata["warnings"] = list(dict.fromkeys(str(w.message) for w in caught))
        write_metadata()
    return metadata
