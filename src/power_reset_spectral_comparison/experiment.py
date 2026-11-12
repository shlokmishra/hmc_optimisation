"""Frozen allocations, full-budget timing repetitions and persisted failure accounting."""

import json
import os
import platform
import traceback
from pathlib import Path
from time import perf_counter

import numpy as np
from threadpoolctl import threadpool_info

from .core import CONFIG, ROOT, run
from .evidence import BASE, check_freeze, load_problem, sha, write_json


def planned_paths(controls=True):
    jobs = []
    for spectrum in CONFIG["spectra"]:
        for method, seeds in CONFIG["seeds"].items():
            for seed in seeds:
                jobs.append(
                    {
                        "name": f"{spectrum}-{method}-{seed if seed is not None else 'det'}",
                        "spectrum": spectrum,
                        "method": method,
                        "seed": seed,
                        "slow_only": False,
                    }
                )
        if controls:
            jobs.append(
                {
                    "name": f"{spectrum}-B-slow-only",
                    "spectrum": spectrum,
                    "method": "B",
                    "seed": None,
                    "slow_only": True,
                }
            )
    return jobs


def environment():
    return {
        "host": platform.node(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "cpuinfo": Path("/proc/cpuinfo").read_text().split("\n\n")[0],
        "cpu_model": next(
            line.split(":", 1)[1].strip()
            for line in Path("/proc/cpuinfo").read_text().splitlines()
            if line.startswith("model name")
        ),
        "affinity": sorted(os.sched_getaffinity(0)),
        "threadpools": threadpool_info(),
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
    }


def execute(output, probe=False):
    if not os.environ.get("SLURM_JOB_ID"):
        raise RuntimeError("Performance runs require Slurm")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    start = perf_counter()
    check_freeze()
    validation = json.loads((BASE / "validation.json").read_text())
    if not validation["passed"]:
        raise RuntimeError("Fidelity gate not passed")
    budget = CONFIG["probe_gradient_budget"] if probe else CONFIG["gradient_budget"]
    inputs = {}
    for spectrum in CONFIG["spectra"]:
        for slow in (False, True):
            inputs[spectrum, slow] = load_problem(spectrum, slow)
    for spectrum in CONFIG["spectra"]:
        A, x0, U, lam = inputs[spectrum, False]
        for method, seeds in CONFIG["seeds"].items():
            run(A, x0, method, 100, seed=seeds[0])
    paths = list((ROOT / CONFIG["paths"]["source"]).glob("*.py")) + [
        ROOT / CONFIG["paths"]["runner"]
    ]
    meta = {
        "study_id": CONFIG["study_id"],
        "config": CONFIG,
        "probe": probe,
        "environment": environment(),
        "implementation_sha256": {str(p.relative_to(ROOT)): sha(p) for p in paths},
        "freeze_sha256": sha(BASE / "freeze.json"),
        "validation_sha256": sha(BASE / "validation.json"),
        "status": "running",
        "setup_seconds": perf_counter() - start,
        "serialization_seconds": 0.0,
        "runs": [],
        "timing_repetitions": [],
        "errors": [],
    }
    write_json(output / "metadata.json", meta)
    for job in planned_paths():
        print("diagnostic", job["name"], flush=True)
        A, x0, U, lam = inputs[job["spectrum"], job["slow_only"]]
        try:
            arrays, record = run(
                A, x0, job["method"], budget, job["seed"], detailed=True, basis=U, eigenvalues=lam
            )
        except Exception:
            meta["errors"].append({"job": job, "traceback": traceback.format_exc()})
            record = {"status": "exception", "failure": traceback.format_exc(), **job}
            meta["runs"].append(record)
            write_json(output / "metadata.json", meta)
            continue
        record.update(job)
        t = perf_counter()
        np.savez_compressed(output / f"{job['name']}.npz", **arrays)
        meta["serialization_seconds"] += perf_counter() - t
        meta["runs"].append(record)
        write_json(output / "metadata.json", meta)
    if not probe:
        for rep, shuffle_seed in enumerate(CONFIG["timing_order_seeds"]):
            jobs = planned_paths(controls=False)
            order = np.random.default_rng(shuffle_seed).permutation(len(jobs))
            for idx in order:
                job = jobs[int(idx)]
                A, x0, _, _ = inputs[job["spectrum"], False]
                arrays, record = run(A, x0, job["method"], budget, job["seed"])
                record.update(job, rep=rep)
                # Verification and disk writes are outside measured optimizer time.
                with np.load(output / f"{job['name']}.npz") as detailed:
                    record["path_exact"] = bool(np.array_equal(arrays["f"], detailed["f"]))
                    record["endpoint_exact"] = bool(
                        np.array_equal(arrays["x_final"], detailed["x_final"])
                    )
                if not record["path_exact"] or not record["endpoint_exact"]:
                    meta["errors"].append(
                        {"job": job, "rep": rep, "failure": "timing path mismatch"}
                    )
                t = perf_counter()
                np.savez_compressed(output / f"{job['name']}-timing-{rep}.npz", **arrays)
                meta["serialization_seconds"] += perf_counter() - t
                meta["timing_repetitions"].append(record)
            write_json(output / "metadata.json", meta)
            print("timing repetition complete", rep, flush=True)
    meta["total_wall_seconds"] = perf_counter() - start
    meta["status"] = "complete" if not meta["errors"] else "completed_with_failures"
    write_json(output / "metadata.json", meta)
    print(meta["status"], flush=True)
    return meta
