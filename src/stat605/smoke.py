"""Small deterministic onboarding example, never a performance benchmark."""

import hashlib
import json
import platform
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from power_reset_spectral_comparison.core import CONFIG, ROOT, run

from .rhgd import run_fixed_time_quadratic

LABELS = {"B": "Power-reset RHGD", "AR_AGD": "Gradient-restart AGD"}


def smoke(output, config_path=None):
    """Exercise existing recurrences on generated data without any old raw artifacts."""
    config_path = Path(config_path or ROOT / "configs/stat605/smoke.json")
    config = json.loads(config_path.read_text())
    # The reference runner has fixed historical step/mu settings. Do not imply
    # this wrapper is a general configurable benchmark or mutate its globals.
    if config["mu"] != CONFIG["alpha"] or config["L"] != CONFIG["L"]:
        raise ValueError("Smoke mu/L must match the frozen reference runner")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    matrix = np.diag(np.linspace(config["mu"], config["L"], config["dimension"]))
    x0 = np.ones(config["dimension"], dtype=np.float64)
    records = []
    figure, axes = plt.subplots(figsize=(7, 4))
    try:
        for method in config["methods"]:
            seed = config["seed"] if method in ("CAGD", "RHGD") else None
            arrays, record = run(matrix, x0, method, config["gradient_budget"], seed=seed)
            np.savez_compressed(output / f"{method}.npz", **arrays)
            records.append(record)
            axes.semilogy(arrays["gradients"], arrays["f"], label=LABELS.get(method, method))
        axes.set(
            xlabel="Distinct gradient evaluations",
            ylabel="Current objective",
            title="STAT 605 software smoke example — not a benchmark",
        )
        axes.legend(fontsize=8)
        figure.tight_layout()
        figure.savefig(output / "smoke.png", dpi=140)
    finally:
        plt.close(figure)
    sources = [
        Path(__file__),
        ROOT / "src/power_reset_spectral_comparison/core.py",
        ROOT / "study/B/src/power_reset.py",
        ROOT / "configs/studies/power_reset_spectral_comparison.json",
    ]
    metadata = {
        "purpose": "software_smoke_not_research_evidence",
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
    (output / "summary.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    return metadata


def fixed_time_smoke(output, config_path=None):
    """Exercise the fixed-time control on the two shared quadratic fixtures."""
    config_path = Path(config_path or ROOT / "configs/stat605/fixed_time_smoke.json")
    config = json.loads(config_path.read_text())
    if config["purpose"] != "software_smoke_not_research_evidence":
        raise ValueError("This command is a software smoke check")
    if not 0 <= config["gradient_budget"] <= 2000:
        raise ValueError("Smoke checks allow at most 2000 gradients per fixture")
    fixture_root = ROOT / "configs/stat605/fixtures"
    provenance_path = fixture_root / "PROVENANCE.json"
    fixtures = {f["file"]: f for f in json.loads(provenance_path.read_text())["fixtures"]}
    loaded, input_hashes = {}, {}
    for name in config["fixtures"]:
        if fixtures[name]["kind"] != "quadratic":
            raise ValueError("Fixed-time smoke accepts quadratic fixtures only")
        path = fixture_root / name
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != fixtures[name]["sha256"]:
            raise ValueError(f"Fixture hash mismatch: {name}")
        input_hashes[str(path.relative_to(ROOT))] = digest
        with np.load(path, allow_pickle=False) as archive:
            loaded[name] = (archive["A"], archive["x0"])
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = []
    figure, axes = plt.subplots(figsize=(7, 4))
    try:
        for name, (matrix, x0) in loaded.items():
            arrays, record = run_fixed_time_quadratic(
                matrix,
                x0,
                h=np.sqrt(config["eta"]),
                period_steps=config["period_steps"],
                gradient_budget=config["gradient_budget"],
                keep_states=True,
            )
            np.savez_compressed(output / name, **arrays)
            records.append({"fixture": name, **record})
            (line,) = axes.semilogy(arrays["gradients"], arrays["f"], label=Path(name).stem)
            indices = np.flatnonzero(arrays["reset"]) + 1
            axes.plot(
                arrays["gradients"][indices], arrays["f"][indices], "o", color=line.get_color()
            )
        axes.set(
            xlabel="Distinct gradient evaluations (dots mark resets)",
            ylabel="Current objective",
            title="Fixed-time RHGD software smoke — not a benchmark",
        )
        axes.legend(fontsize=8)
        figure.tight_layout()
        figure.savefig(output / "fixed_time_smoke.png", dpi=140)
    finally:
        plt.close(figure)
    sources = [
        Path(__file__),
        ROOT / "src/stat605/rhgd.py",
        ROOT / "src/power_reset_spectral_comparison/core.py",
        ROOT / "study/B/src/power_reset.py",
        ROOT / "configs/studies/power_reset_spectral_comparison.json",
        provenance_path,
    ]
    metadata = {
        "purpose": config["purpose"],
        "config": config,
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "source_sha256": {
            str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources
        },
        "input_sha256": input_hashes,
        "python": platform.python_version(),
        "numpy": np.__version__,
        "status": "passed" if all(r["status"] == "budget_complete" for r in records) else "failed",
        "runs": records,
    }
    (output / "summary.json").write_text(json.dumps(metadata, indent=2, allow_nan=False) + "\n")
    return metadata
