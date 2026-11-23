"""Frozen, bounded presentation protocol. Run stages in explicit Slurm jobs."""

import argparse
import json
import os
from dataclasses import replace
from pathlib import Path
from time import perf_counter

import numpy as np

from stat605.benchmark import METHODS, run_benchmark
from stat605.problems import make_problem
from stat605.runtime import single_thread_pools
from stat605.spectral_suite import _digest, _save_json

PROTOCOL_PATH = Path(__file__).resolve().parents[2] / "configs/stat605/final_protocol.json"
PROTOCOL = json.loads(PROTOCOL_PATH.read_text())
METHOD_NAMES = tuple(PROTOCOL["methods"])
SEEDS = tuple(PROTOCOL["algorithm_seeds"])
TARGETS = tuple(PROTOCOL["relative_targets"])
GRIDS = PROTOCOL["grids"]


def cases(training=False):
    for spectrum in ("linear", "log", "clustered"):
        for start in (1605, 2605) if training else ("scaled_common", "equal"):
            p = make_problem(spectrum, "scaled_common" if training else start)
            if training:
                # Retain the common basis/matrix; only the Gaussian start changes.
                x = np.random.default_rng(start).standard_normal(100)
                x *= np.sqrt(1 / (0.5 * x @ p.A @ x))
                p = replace(p, x0=x)
            yield f"{spectrum}-{start}", spectrum, str(start), p


def paths():
    for name in METHOD_NAMES:
        for seed in SEEDS if METHODS[name].randomized else (None,):
            yield name, seed


def parameter(name, value):
    return {"period_steps" if name == "FIXED_RHGD" else "beta": value}


def save_run(
    output,
    manifest,
    case,
    method,
    seed,
    budget,
    parameters=None,
    eta=0.002,
    mu=5e-5,
    label="",
    diagnostics=0,
):
    key, spectrum, start, problem = case
    trace, record = run_benchmark(
        problem,
        method,
        gradient_budget=budget,
        eta=eta,
        supplied_mu=mu,
        seed=seed,
        parameters=parameters,
        targets=tuple(t * (0.5 * problem.x0 @ problem.A @ problem.x0) for t in TARGETS),
        diagnostic_steps=diagnostics,
    )
    filename = f"traces/{key}-{method}-{seed}-{label}.npz"
    np.savez_compressed(output / filename, **trace)
    record.update(
        case=key,
        spectrum=spectrum,
        start=start,
        label=label,
        trace=filename,
        trace_sha256=_digest(output / filename),
        initial_loss=float(trace["loss"][0]),
        final_relative_gap=float(trace["loss"][-1] / trace["loss"][0])
        if np.isfinite(trace["loss"][-1])
        else None,
    )
    manifest["runs"].append(record)
    _save_json(output / "summary.json", manifest)
    return record


def select(candidates, budget=20000):
    """Selection penalties are ONLY used here, never as observed work."""
    scores = []
    for records in candidates:
        work, gaps = [], []
        for run in records:
            hit = run["crossings"][1]["sustained"]
            work.append(
                4 * budget
                if run["status"] == "failure"
                else 2 * budget
                if hit is None
                else hit["gradients"]
            )
            gap = run["final_relative_gap"]
            gaps.append(max(np.finfo(float).tiny, gap) if gap is not None and gap >= 0 else np.inf)
        scores.append((float(np.mean(work)), float(np.mean(np.log(gaps)))))
    return min(range(len(scores)), key=lambda i: (*scores[i], i)), scores


def run(stage, output, prior=None, shard=0, smoke=False):
    if not smoke and not os.getenv("SLURM_JOB_ID"):
        raise ValueError("Final experiments require a verified Slurm allocation")
    single_thread_pools()
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output / "traces").mkdir()
    manifest = {
        "stage": stage,
        "status": "incomplete",
        "runs": [],
        "smoke": smoke,
        "job_id": os.getenv("SLURM_JOB_ID"),
        "protocol": PROTOCOL,
        "protocol_sha256": _digest(PROTOCOL_PATH),
        "input_sha256": {
            str(p): _digest(p) for p in sorted(Path("configs/stat605/fixtures").glob("*.npz"))
        },
        "source_sha256": {str(p): _digest(p) for p in sorted(Path("src/stat605").glob("*.py"))},
    }
    _save_json(output / "summary.json", manifest)
    _save_json(
        output / "design.json",
        {
            "problems": [
                dict(
                    spectrum=spectrum,
                    start=start,
                    eigenvalues=p.eigenvalues.tolist(),
                    initial_modal_energy=p.modal_energy(p.x0).tolist(),
                )
                for _, spectrum, start, p in cases(stage == "tune")
            ]
        },
    )
    tick = perf_counter()
    if stage == "pilot":
        for case in cases():
            for method, seed in paths():
                save_run(output, manifest, case, method, seed, 20 if smoke else 1000)
        elapsed = perf_counter() - tick
        # Full pipeline wall time includes compression, diagnostics and manifest writes.
        prediction = {
            str(b): elapsed * b / (20 if smoke else 1000) for b in (200000, 100000, 50000, 20000)
        }
        selected = next(
            (int(b) for b, seconds in prediction.items() if 2 * seconds <= 4 * 3600), None
        )
        manifest.update(runtime_predictions_seconds=prediction, selected_budget=selected)
    elif stage == "tune":
        pilot = json.loads((Path(prior) / "summary.json").read_text())
        if pilot["status"] != "complete" or pilot["selected_budget"] is None:
            raise ValueError("A completed feasible pilot is required; retain pilot otherwise")
        tuned, scores = {}, {}
        for method, grid in GRIDS.items():
            candidates = []
            for value in grid:
                records = [
                    save_run(
                        output,
                        manifest,
                        case,
                        method,
                        None,
                        20 if smoke else 20000,
                        parameter(method, value),
                        label=str(value),
                    )
                    for case in cases(training=True)
                ]
                candidates.append(records)
            index, scores[method] = select(candidates, 20 if smoke else 20000)
            tuned[method] = parameter(method, grid[index])
        manifest.update(
            parameters=tuned,
            selection_scores=scores,
            main_budget=pilot["selected_budget"],
            pilot_sha256=_digest(Path(prior) / "summary.json"),
        )
    else:
        tuning = json.loads((Path(prior) / "summary.json").read_text())
        if tuning["status"] != "complete":
            raise ValueError("Completed frozen tuning is required")
        manifest.update(
            tuning_sha256=_digest(Path(prior) / "summary.json"),
            parameters=tuning["parameters"],
            main_budget=tuning["main_budget"],
        )
        budget = 20 if smoke else tuning["main_budget"]
        if stage == "main":
            for i, case in enumerate(cases()):
                if i % 2 != shard:
                    continue
                for method, seed in paths():
                    save_run(
                        output,
                        manifest,
                        case,
                        method,
                        seed,
                        budget,
                        tuning["parameters"].get(method),
                        diagnostics=min(budget // 2, 12000),
                    )
        elif stage == "robustness":
            for case in cases():
                if case[2] != "scaled_common" or case[1] != ("linear", "log")[shard]:
                    continue
                for method, seed in paths():
                    for factor in (0.01, 1, 100) if METHODS[method].uses_mu else ():
                        save_run(
                            output,
                            manifest,
                            case,
                            method,
                            seed,
                            min(budget, 100000),
                            tuning["parameters"].get(method),
                            mu=5e-5 * factor,
                            label=f"mu-{factor}",
                        )
                    for factor in (0.5, 1, 1.1):
                        pars = dict(tuning["parameters"].get(method, {}))
                        if method == "FIXED_RHGD":
                            pars["period_steps"] = max(
                                1, int(np.floor(pars["period_steps"] / factor + 0.5))
                            )
                        save_run(
                            output,
                            manifest,
                            case,
                            method,
                            seed,
                            min(budget, 100000),
                            pars,
                            eta=0.002 * factor**2,
                            label=f"step-{factor}",
                        )
        else:
            raise ValueError(stage)
    manifest.update(status="complete", wall_seconds=perf_counter() - tick)
    _save_json(output / "summary.json", manifest)
    return manifest


def audit(directory):
    """Independently derive crossings from every hashed trace."""
    directory = Path(directory)
    manifest = json.loads((directory / "summary.json").read_text())
    for run in manifest["runs"]:
        path = directory / run["trace"]
        if _digest(path) != run["trace_sha256"]:
            raise ValueError(f"Trace hash mismatch: {path}")
        with np.load(path, allow_pickle=False) as trace:
            recomputed = []
            for saved in run["crossings"]:
                target = saved["target"]
                inside = np.isfinite(trace["loss"]) & (trace["loss"] <= target)
                indices = np.flatnonzero(inside)
                first = int(indices[0]) if indices.size else None
                outside = np.flatnonzero(~inside)
                sustained = int(outside[-1] + 1) if outside.size else 0
                if sustained >= len(inside) or run["status"] == "failure":
                    sustained = None
                recomputed.append(
                    {
                        "target": target,
                        **{
                            kind: None
                            if index is None
                            else {"iteration": index, "gradients": int(trace["gradients"][index])}
                            for kind, index in (("first", first), ("sustained", sustained))
                        },
                    }
                )
            if recomputed != run["crossings"]:
                raise ValueError(f"Crossing mismatch: {path}")
            if run["numerical_gradients"] > run["gradient_budget"]:
                raise ValueError("Gradient ceiling violated")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("pilot", "tune", "main", "robustness", "audit"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--prior", type=Path)
    parser.add_argument("--shard", type=int, choices=(0, 1), default=0)
    parser.add_argument("--smoke", action="store_true")
    args = parser.parse_args()
    if args.stage == "audit":
        result = audit(args.output)
    else:
        result = run(args.stage, args.output, args.prior, args.shard, args.smoke)
    print(
        json.dumps(
            {k: v for k, v in result.items() if k not in ("runs", "source_sha256")}, indent=2
        )
    )


if __name__ == "__main__":
    main()
