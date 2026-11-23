"""Config-driven restarted-AGD runs: source-style replication and mu sensitivity."""

import hashlib
import json
import platform
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from stat605.agd import quadratic_oracle, run_agd

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "configs/stat605/fixtures"


def crossings(gap, target):
    """First and sustained update index at which gap <= target; None when censored.

    Sustained means the gap stays at or below the target from that index to the
    end of the recorded trace. It says nothing about later updates.
    """
    below = np.asarray(gap) <= target
    if not below.any():
        return None, None
    first = int(np.argmax(below))
    if not below[-1]:
        return first, None
    above = np.flatnonzero(~below)
    return first, int(above[-1] + 1) if len(above) else 0


def generated_quadratic(n, mu, L, spectrum, seed):
    """Seeded A = Q diag(lambda) Q^T with a declared spectrum and Gaussian start."""
    rng = np.random.default_rng(seed)
    if spectrum == "linear":
        eigenvalues = np.linspace(mu, L, n)
    elif spectrum == "log":
        eigenvalues = np.geomspace(mu, L, n)
    else:
        raise ValueError(f"unknown spectrum {spectrum!r}")
    basis, _ = np.linalg.qr(rng.standard_normal((n, n)))
    A = (basis * eigenvalues) @ basis.T
    A = 0.5 * (A + A.T)
    return A, rng.standard_normal(n)


def load_problem(spec):
    """Return A, x0, mu, L for a fixture or a generated quadratic. f* is zero for both."""
    if "fixture" in spec:
        with np.load(FIXTURES / spec["fixture"], allow_pickle=False) as data:
            return data["A"], data["x0"], spec["mu"], spec["L"]
    g = spec["generate"]
    L = g["L"]
    mu = L / g["kappa"]
    A, x0 = generated_quadratic(g["n"], mu, L, g["spectrum"], g["seed"])
    return A, x0, mu, L


def resolve_interval(value, mu, L):
    if value == "e_sqrt_8_kappa":
        # Upper bound on the optimal fixed interval, O'Donoghue and Candes eq. (6).
        return int(round(np.e * np.sqrt(8.0 * L / mu)))
    return value


def _finite(value):
    return float(value) if np.isfinite(value) else None


def summarize(arrays, metadata, targets):
    """Work to each target. Gradients equal updates; objectives are charged per rule."""
    gap = arrays["f"]  # f* = 0 for every quadratic problem handled here.
    per_update = 1 if metadata["restart"] == "function" else 0
    rows = {}
    for target in targets:
        first, sustained = crossings(gap, target)
        rows[f"{target:g}"] = {
            name: None
            if index is None
            else {
                "updates": index,
                "gradients": index,
                "controller_objectives": index * per_update,
                "restarts_so_far": int(arrays["restart"][:index].sum()),
            }
            for name, index in (("first", first), ("sustained", sustained))
        }
    return {
        "targets": rows,
        "final_loss": _finite(gap[-1]),
        "best_loss": _finite(np.min(gap)),
        "restart_updates": (np.flatnonzero(arrays["restart"]) + 1).tolist(),
    }


def run_config(config_path, output):
    """Run every case in a config into a fresh output directory."""
    config_path = Path(config_path)
    config = json.loads(config_path.read_text())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    for case in config["cases"]:
        A, x0, mu, L = load_problem(case["problem"])
        eta = case.get("eta_times_L", 1.0) / L
        figure, axes = plt.subplots(figsize=(8, 4.5))
        try:
            for method in case["methods"]:
                factor = method.get("q_factor")
                q = 0.0 if factor is None else factor * mu / L
                interval = resolve_interval(method.get("interval"), mu, L)
                arrays, metadata = run_agd(
                    quadratic_oracle(A),
                    x0,
                    eta,
                    case["iterations"],
                    q=q,
                    restart=method["restart"],
                    interval=interval,
                )
                stem = f"{case['name']}__{method['label']}"
                np.savez_compressed(output / f"{stem}.npz", **arrays)
                records.append(
                    {
                        "case": case["name"],
                        "label": method["label"],
                        "q_factor": factor,
                        "mu": mu,
                        "L": L,
                        **metadata,
                        **summarize(arrays, metadata, case["targets"]),
                    }
                )
                axes.semilogy(arrays["gradients"], arrays["f"], label=method["label"])
            axes.set(
                xlabel="Gradient evaluations (one per update)",
                ylabel="Current objective gap f(x_k) - f*",
                title=case["name"],
            )
            axes.legend(fontsize=7)
            figure.tight_layout()
            figure.savefig(output / f"{case['name']}.png", dpi=140)
        finally:
            plt.close(figure)
    sources = [Path(__file__), Path(__file__).with_name("agd.py")]
    summary = {
        "purpose": config["purpose"],
        "config": config,
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
        },
        "python": platform.python_version(),
        "numpy": np.__version__,
        "status": "passed" if all(r["status"] == "budget_complete" for r in records) else "failed",
        "runs": records,
    }
    (output / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    return summary
