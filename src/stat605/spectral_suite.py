"""Run and archive the matched STAT 605 quadratic comparison."""

import hashlib
import json
import os
import platform
from importlib.metadata import version
from itertools import product
from pathlib import Path
from time import perf_counter

import numpy as np

from stat605.benchmark import METHODS, run_benchmark
from stat605.problems import FIXTURES, SPECTRA, STARTS, make_problem
from stat605.runtime import single_thread_pools
from stat605.spectral_reporting import plot_modal_energy, write_report

ROOT = Path(__file__).resolve().parents[2]
CONFIGS = ROOT / "configs/stat605"
SOURCES = (
    "scripts/stat605.py",
    "scripts/stat605_spectral_pilot.slurm",
    "scripts/activate_env.sh",
    "src/stat605/problems.py",
    "src/stat605/benchmark.py",
    "src/stat605/runtime.py",
    "src/stat605/spectral_suite.py",
    "src/stat605/spectral_reporting.py",
    "src/power_reset_spectral_comparison/core.py",
    "src/power_reset_spectral_comparison/analysis.py",
    "configs/studies/power_reset_spectral_comparison.json",
    "study/B/src/power_reset.py",
    "requirements.txt",
)


def _digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _save_json(path, data):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _fixture_hashes():
    provenance = FIXTURES / "PROVENANCE.json"
    hashes = {provenance.name: _digest(provenance)}
    for item in json.loads(provenance.read_text())["fixtures"]:
        if item["kind"] == "quadratic":
            name = item["file"]
            hashes[name] = _digest(FIXTURES / name)
            if hashes[name] != item["sha256"]:
                raise ValueError(f"Fixture digest differs from the provenance manifest: {name}")
    return hashes


def _config(path):
    data = path.read_bytes()
    config = json.loads(data)
    if config["purpose"] not in ("local_check", "grace_pilot", "grace_comparison"):
        raise ValueError("Choose local_check, grace_pilot or grace_comparison as the purpose")
    for key, choices in (("spectra", SPECTRA), ("starts", STARTS)):
        selected = config[key]
        if not selected or len(set(selected)) != len(selected) or set(selected) - set(choices):
            raise ValueError(f"Choose distinct {key} from {choices}")
    if not config["seeds"] or set(config["seeds"]) - METHODS.keys():
        raise ValueError(f"Choose methods from {list(METHODS)}")
    for name, seeds in config["seeds"].items():
        if METHODS[name].randomized:
            if not seeds or any(type(s) is not int or s < 0 for s in seeds):
                raise ValueError(f"{name} requires explicit nonnegative integer seeds")
        elif seeds != [None]:
            raise ValueError(f"{name} requires a single deterministic path with a null seed")
        if len(set(seeds)) != len(seeds):
            raise ValueError(f"{name} seeds must be distinct")
    targets = config["targets"]
    if (
        not targets
        or len(set(targets)) != len(targets)
        or any(not np.isfinite(t) or t <= 0 for t in targets)
    ):
        raise ValueError("Specify distinct positive targets")
    for key, minimum in (("gradient_budget", 0), ("power_diagnostic_steps", 0), ("cap", 1)):
        if type(config[key]) is not int or config[key] < minimum:
            raise ValueError(f"{key} must be an integer of at least {minimum}")
    if not np.isfinite(config["eta"]) or config["eta"] <= 0:
        raise ValueError("eta must be positive and finite")
    if any(METHODS[name].uses_mu for name in config["seeds"]):
        mu = config["supplied_mu"]
        if mu is None or not np.isfinite(mu) or mu <= 0:
            raise ValueError("Selected methods require positive finite supplied_mu")
    if config["purpose"] == "local_check":
        paths = (
            len(config["spectra"])
            * len(config["starts"])
            * sum(len(seeds) for seeds in config["seeds"].values())
        )
        if (
            config["problem"]["dimension"] > 100
            or paths > 128
            or paths * config["gradient_budget"] > 20000
        ):
            raise ValueError("local_check is capped at dimension 100, 128 paths and 20000 total G")
    return config, data


def _prepare(config_path, output, *, design_only):
    config, data = _config(Path(config_path))
    if not design_only and config["purpose"].startswith("grace_") and not os.getenv("SLURM_JOB_ID"):
        raise ValueError("Run this benchmark inside a verified Grace Slurm allocation.")
    if config["problem"]["dimension"] > 100 and not os.getenv("SLURM_JOB_ID"):
        raise ValueError("Problem designs above dimension 100 require a Grace Slurm allocation.")
    pools = single_thread_pools()
    output.mkdir(parents=True, exist_ok=False)
    (output / "config.json").write_bytes(data)
    setup_start = perf_counter()
    fixture_hashes = _fixture_hashes() if config["problem"]["source"] == "fixture" else {}
    cases = {}
    descriptions = []
    for spectrum, start in product(config["spectra"], config["starts"]):
        case = make_problem(spectrum, start, **config["problem"])
        cases[spectrum, start] = case
        descriptions.append(
            {
                "spectrum": spectrum,
                "start": start,
                "initial_loss": float(0.5 * case.x0 @ case.A @ case.x0),
                "eigenvalues": case.eigenvalues.tolist(),
                "initial_modal_energy": case.modal_energy(case.x0).tolist(),
                "spectral_checks": case.spectral_checks(),
                "array_sha256": {
                    field: hashlib.sha256(getattr(case, field).tobytes()).hexdigest()
                    for field in ("A", "x0", "basis", "eigenvalues")
                },
            }
        )
    setup_seconds = perf_counter() - setup_start
    metadata = {
        "config": config,
        "config_sha256": hashlib.sha256(data).hexdigest(),
        "source_sha256": {name: _digest(ROOT / name) for name in SOURCES},
        "fixture_sha256": fixture_hashes,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "packages": {
                name: version(name) for name in ("numpy", "scipy", "matplotlib", "threadpoolctl")
            },
            "threadpools": pools,
            "slurm": {
                k: os.getenv(k)
                for k in (
                    "SLURM_JOB_ID",
                    "SLURM_JOB_ACCOUNT",
                    "SLURM_JOB_PARTITION",
                    "SLURM_CLUSTER_NAME",
                )
            },
        },
        "problem_setup_seconds": setup_seconds,
        "problems": descriptions,
    }
    return config, cases, metadata


def spectral_design(output, config_path=CONFIGS / "spectral_pilot.json"):
    """Render the input geometry without taking any optimization steps."""
    output = Path(output)
    _, _, metadata = _prepare(config_path, output, design_only=True)
    _save_json(output / "design.json", metadata)
    plot_modal_energy(metadata["problems"], output / "modal_energy.png")
    return metadata


def spectral_suite(output, config_path=CONFIGS / "spectral_check.json"):
    """Run all configured paths to budget, then plot directly from the saved traces."""
    output = Path(output)
    config, cases, metadata = _prepare(config_path, output, design_only=False)
    trace_dir = output / "traces"
    trace_dir.mkdir()
    metadata.update(status="incomplete", runs=[])
    _save_json(output / "summary.json", metadata)
    for (spectrum, start), case in cases.items():
        for method, seeds in config["seeds"].items():
            for seed in seeds:
                arrays, record = run_benchmark(
                    case,
                    method,
                    gradient_budget=config["gradient_budget"],
                    eta=config["eta"],
                    supplied_mu=config["supplied_mu"],
                    cap=config["cap"],
                    seed=seed,
                    targets=config["targets"],
                    diagnostic_steps=config["power_diagnostic_steps"],
                )
                suffix = "deterministic" if seed is None else str(seed)
                trace = trace_dir / f"{spectrum}-{start}-{method}-{suffix}.npz"
                np.savez_compressed(trace, **arrays)
                metadata["runs"].append(
                    dict(
                        record,
                        spectrum=spectrum,
                        start=start,
                        trace=str(trace.relative_to(output)),
                        trace_sha256=_digest(trace),
                    )
                )
                # A stopped job retains every completed path and its charged work.
                _save_json(output / "summary.json", metadata)
    complete = all(run["status"] == "budget_complete" for run in metadata["runs"])
    metadata["status"] = "passed" if complete else "failure"
    _save_json(output / "summary.json", metadata)
    write_report(output)
    return metadata
