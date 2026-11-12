"""Frozen-grid comparisons, modal evidence, figures and independent saved-data audit."""

import csv
import json
from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np

from .core import CONFIG, ROOT
from .evidence import check_freeze, load_problem, sha, write_json
from .experiment import planned_paths


def crossings(f, target, successful=True):
    good = np.isfinite(f) & (f <= target)
    first = int(np.flatnonzero(good)[0]) if np.any(good) else None
    bad = np.flatnonzero(~good)
    sustained = int(bad[-1] + 1) if len(bad) else 0
    if sustained >= len(f) or not successful:
        sustained = None
    return {"first": first, "sustained": sustained}


def censored_median(values):
    med = float(np.median([np.inf if v is None else v for v in values]))
    return med if np.isfinite(med) else None


def margin_check(b, comparator, lower_bound, threshold):
    """A censored comparator can only certify a margin using observed work/time."""
    denominator = comparator if comparator is not None else lower_bound
    ratio = b / denominator if b is not None and denominator > 0 else None
    return {
        "ratio_B_over_AR": ratio,
        "ratio_is_upper_bound": comparator is None,
        "bound": threshold,
        "pass": ratio is not None and ratio <= threshold,
    }


def mode_evidence(path, record, outdir):
    A, x0, U, lam = load_problem(record["spectrum"], record["slow_only"])
    with np.load(path) as z:
        x = z["x"]
        v = z["velocity_pre_reset"]
        g = z["endpoint_gradient"]
        f = z["f"]
        elapsed = z["elapsed"]
        power = z["power"]
        age = z["age"]
        event = z["event"].astype(bool)
        reset = z["reset"].astype(bool)
        cap = z["cap"].astype(bool)
        kinetic = z["kinetic"]
        delay = z["delay"]
        minimum = z["segment_min"]
        q = x @ U
        w = v @ U
        ideal_power = lam * q[1:] * w
        actual_power = (g @ U) * w
        loss = 0.5 * lam * q * q
        indices = np.flatnonzero(reset)
        rows = []
        for i in indices:
            mp = ideal_power[i]
            positive = np.flatnonzero(mp > 0)
            top = positive[np.argsort(mp[positive])[-5:][::-1]]
            row = {
                "update": int(i + 1),
                "gradients": int(2 * (i + 1)),
                "reason": "cap" if cap[i] else "power",
                "global_power": float(power[i]),
                "slow_power": float(mp[0]),
                "slow_power_actual": float(actual_power[i, 0]),
                "positive_modes": int(np.count_nonzero(mp > 0)),
                "negative_modes": int(np.count_nonzero(mp < 0)),
                "faster_sum": float(np.sum(mp[1:])),
                "slow_descending": bool(mp[0] < 0),
                "faster_overwhelms_slow": bool(mp[0] < 0 and np.sum(mp[1:]) > -mp[0]),
                "top_positive_modes": [
                    {"index": int(j), "lambda": float(lam[j]), "power": float(mp[j])} for j in top
                ],
                "top_negative_mode": int(np.argmin(mp)),
                "objective_before": float(f[i]),
                "objective_after": float(f[i + 1]),
                "current_objective_increment": float(f[i + 1] - f[i]),
                "next_observed_objective_increment": float(f[i + 2] - f[i + 1])
                if i + 2 < len(f)
                else None,
                "diagnostic_wall_seconds": float(elapsed[i + 1]),
                "segment_min": float(minimum[i]),
                "objective_above_segment_minimum": float(f[i + 1] - minimum[i]),
                "delay": int(delay[i]),
                "age": int(age[i]),
                "kinetic_before_reset": float(kinetic[i]),
                "slow_kinetic_discarded": float(0.5 * w[i, 0] ** 2),
                "ideal_power_residual": float(np.sum(mp) - power[i]),
                "actual_power_residual": float(np.sum(actual_power[i]) - power[i]),
            }
            rows.append(row)
        active = np.flatnonzero(event & (f[:-1] > 1e-10))
        representatives = []
        if len(active):
            representatives = [int(active[0]), int(active[len(active) // 2]), int(active[-1])]
        hit = crossings(f, CONFIG["primary_target"], record["status"] == "budget_complete")[
            "sustained"
        ]
        earlier = np.flatnonzero(
            event & (np.arange(len(event)) + 1 <= (hit if hit is not None else -1))
        )
        if len(earlier):
            representatives.append(int(earlier[-1]))
        representatives = sorted(set(representatives))
        selected = (
            np.unique(
                np.concatenate(
                    [np.arange(max(0, i - 3), min(len(event), i + 4)) for i in representatives]
                )
            )
            if representatives
            else np.array([], int)
        )
        # Modal scalar histories are reconstructed from saved states; selected windows
        # retain every coordinate contribution without duplicating all large raw states.
        np.savez_compressed(
            outdir / f"{record['name']}-modes.npz",
            eigenvalues=lam,
            slow_q=q[:, 0],
            slow_v=w[:, 0],
            slow_loss=loss[:, 0],
            slow_power=ideal_power[:, 0],
            faster_power=np.sum(ideal_power[:, 1:], axis=1),
            global_power=power,
            residual_ideal=np.sum(ideal_power, axis=1) - power,
            residual_actual=np.sum(actual_power, axis=1) - power,
            reset_indices=indices,
            reset_q=q[indices + 1],
            reset_v=w[indices],
            reset_modal_loss=loss[indices + 1],
            reset_modal_power=ideal_power[indices],
            reset_modal_power_actual=actual_power[indices],
            representative_indices=np.array(representatives),
            window_indices=selected,
            window_q=q[selected + 1],
            window_v=w[selected],
            window_loss=loss[selected + 1],
            window_power=ideal_power[selected],
        )
    return {
        "events": rows,
        "event_count": int(np.count_nonzero(event)),
        "cap_count": int(np.count_nonzero(cap)),
        "target_relevant_events": sum(r["objective_before"] > 1e-10 for r in rows),
        "target_relevant_slow_truncations": sum(
            r["objective_before"] > 1e-10 and r["faster_overwhelms_slow"] for r in rows
        ),
        "all_slow_truncations": sum(r["faster_overwhelms_slow"] for r in rows),
        "final_slow_loss": float(loss[-1, 0]),
        "initial_slow_loss": float(loss[0, 0]),
        "slow_targets": {str(t): crossings(loss[:, 0], t) for t in [1e-6, 1e-8, 1e-10]},
        "ages": age[reset].astype(int).tolist(),
        "unfinished_segment_age": int(age[-1]) if not reset[-1] else 0,
        "max_ideal_power_residual": float(np.max(np.abs(np.sum(ideal_power, axis=1) - power))),
        "max_actual_power_residual": float(np.max(np.abs(np.sum(actual_power, axis=1) - power))),
        "representatives_zero_based": representatives,
        "offline_gradient_calls": 0,
        "offline_dense_basis_products": 3,
        "offline_modal_scalar_operations": "loss/power products and reductions",
        "reconstruction": "All full modal histories reconstructable from saved x,v,g,U,lambda without new gradient evaluations",
    }


def analyze(run_dir):
    start = perf_counter()
    run_dir = Path(run_dir).resolve()
    meta = json.loads((run_dir / "metadata.json").read_text())
    if meta["status"] not in ("complete", "completed_with_failures"):
        raise RuntimeError("Run is incomplete; audit failure before performance analysis")
    check_freeze()
    outdir = run_dir / "analysis"
    outdir.mkdir(exist_ok=True)
    figdir = ROOT / CONFIG["paths"]["figures"] / run_dir.name
    figdir.mkdir(parents=True, exist_ok=True)
    targets = [1e-6, 1e-8, 1e-10]
    curves = {}
    rows = []
    summaries = {}
    mechanisms = {}
    for rec in meta["runs"]:
        name = rec["name"]
        with np.load(run_dir / f"{name}.npz") as z:
            curve = {
                key: z[key]
                for key in ("f", "gradients", "literal_gradients", "elapsed", "slow_loss")
            }
            curves[name] = curve
        if rec["method"] == "B":
            mechanisms[name] = mode_evidence(run_dir / f"{name}.npz", rec, outdir)
        if rec["slow_only"]:
            continue
        times = []
        for rep in range(CONFIG["timing_repetitions"]):
            with np.load(run_dir / f"{name}-timing-{rep}.npz") as z:
                times.append(z["elapsed"])
        curves[name]["timings"] = times
        for target in targets:
            hits = crossings(curve["f"], target, rec["status"] == "budget_complete")
            for kind, i in hits.items():
                row = {
                    "name": name,
                    "spectrum": rec["spectrum"],
                    "method": rec["method"],
                    "seed": rec["seed"],
                    "target": target,
                    "kind": kind,
                    "status": rec["status"],
                    "reached": i is not None,
                    "update": i,
                    "gradients": int(curve["gradients"][i]) if i is not None else None,
                    "literal_calls": int(curve["literal_gradients"][i]) if i is not None else None,
                    "wall_repetitions": [
                        float(t[i]) if i is not None and i < len(t) else None for t in times
                    ],
                }
                row["wall_median"] = censored_median(row["wall_repetitions"])
                rows.append(row)
    for spectrum in CONFIG["spectra"]:
        summaries[spectrum] = {}
        for method in CONFIG["methods"]:
            summaries[spectrum][method] = {}
            for target in targets:
                summaries[spectrum][method][str(target)] = {}
                for kind in ("first", "sustained"):
                    r = [
                        r
                        for r in rows
                        if r["spectrum"] == spectrum
                        and r["method"] == method
                        and r["target"] == target
                        and r["kind"] == kind
                    ]
                    summaries[spectrum][method][str(target)][kind] = {
                        "gradients_median": censored_median([a["gradients"] for a in r]),
                        "wall_median": censored_median([a["wall_median"] for a in r]),
                        "literal_calls_median": censored_median([a["literal_calls"] for a in r]),
                        "reached": sum(a["reached"] for a in r),
                        "total": len(r),
                        "individual_gradients": [a["gradients"] for a in r],
                        "individual_wall_medians": [a["wall_median"] for a in r],
                    }
    decision = {}
    for spectrum in CONFIG["spectra"]:
        checks = []
        for target in targets:
            b = summaries[spectrum]["B"][str(target)]["sustained"]
            ar = summaries[spectrum]["AR_AGD"][str(target)]["sustained"]
            bound = 0.8 if target == 1e-8 else 1.25
            for key in ("gradients_median", "wall_median"):
                ar_curve = curves[f"{spectrum}-AR_AGD-det"]
                lower_bound = (
                    float(ar_curve["gradients"][-1])
                    if key == "gradients_median"
                    else float(np.median([t[-1] for t in ar_curve["timings"]]))
                )
                checks.append(
                    {
                        "target": target,
                        "metric": key,
                        **margin_check(b[key], ar[key], lower_bound, bound),
                    }
                )
        decision[spectrum] = {"checks": checks, "pass": all(c["pass"] for c in checks)}
    no_failures = (
        all(r["status"] == "budget_complete" for r in meta["runs"])
        and all(r["status"] == "budget_complete" for r in meta["timing_repetitions"])
        and not meta["errors"]
    )
    passed = no_failures and all(d["pass"] for d in decision.values())
    result = {
        "study_id": CONFIG["study_id"],
        "run": str(run_dir.relative_to(ROOT)),
        "summaries": summaries,
        "decision": decision,
        "no_optimizer_failures": no_failures,
        "general_speed_gate_pass": passed,
        "primary_path_count": len(rows) // 6,
        "diagnostic_controls": 2,
        "mechanisms": mechanisms,
        "conclusion": "general-speed continuation criterion passed"
        if passed
        else "STOP general-speed direction; no change to B",
        "analysis_source_sha256": sha(Path(__file__)),
    }
    write_json(outdir / "summary.json", result)
    with (outdir / "targets.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    write_json(outdir / "target_records.json", rows)
    table = [
        "| Spectrum | Method | Target | First gradients | Sustained gradients | Sustained seconds | Reached |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for spec, methods in summaries.items():
        for method, entries in methods.items():
            for target, e in entries.items():
                r = e["sustained"]
                table.append(
                    f"| {spec} | {method} | {target} | {e['first']['gradients_median']} | {r['gradients_median']} | {r['wall_median']} | {r['reached']}/{r['total']} |"
                )
    (outdir / "comparison.md").write_text("\n".join(table) + "\n")
    plotting_start = perf_counter()
    make_figures(run_dir, meta, curves, mechanisms, outdir, figdir)
    write_json(
        outdir / "analysis_cost.json",
        {
            "total_seconds": perf_counter() - start,
            "plotting_seconds": perf_counter() - plotting_start,
            "additional_gradient_calls": 0,
        },
    )
    print(json.dumps({"general_speed_gate_pass": passed, "decision": decision}, indent=2))


def make_figures(run_dir, meta, curves, mechanisms, outdir, figdir):
    colors = {
        "B": "black",
        "AR_AGD": "purple",
        "AGD": "royalblue",
        "CAGD": "seagreen",
        "RHGD": "darkorange",
    }
    coordinates = {}
    for spectrum in CONFIG["spectra"]:
        fig, axes = plt.subplots(2, 2, figsize=(12, 9))
        for method in CONFIG["methods"]:
            group = [
                r
                for r in meta["runs"]
                if r["spectrum"] == spectrum and r["method"] == method and not r["slow_only"]
            ]
            for r in group:
                c = curves[r["name"]]
                n = len(c["f"])
                ix = np.unique(np.r_[0, np.geomspace(1, n - 1, min(n - 1, 2400)).astype(int)])
                for ax, xx, yy in [
                    (axes[0, 0], c["gradients"], c["f"]),
                    (axes[1, 0], np.arange(n), c["f"]),
                    (axes[1, 1], c["gradients"], c["slow_loss"]),
                ]:
                    ax.plot(
                        xx[ix],
                        np.where(yy[ix] > 0, yy[ix], np.nan),
                        color=colors[method],
                        alpha=0.25 if len(group) > 1 else 0.75,
                        lw=0.8,
                    )
                coordinates[f"{r['name']}-diagnostic"] = np.c_[
                    c["gradients"][ix], c["f"][ix], c["slow_loss"][ix], c["f"][ix] > 0
                ]
                for rep, times in enumerate(c["timings"]):
                    axes[0, 1].plot(
                        times[ix],
                        np.where(c["f"][ix] > 0, c["f"][ix], np.nan),
                        color=colors[method],
                        alpha=0.15,
                        lw=0.8,
                    )
                    coordinates[f"{r['name']}-time-{rep}"] = np.c_[
                        times[ix], c["f"][ix], c["f"][ix] > 0
                    ]
            # Past-only common grids; descriptive pointwise median, not a confidence band.
            for ax, axis_key, loss_key in [
                (axes[0, 0], "gradients", "f"),
                (axes[1, 0], "updates", "f"),
                (axes[1, 1], "gradients", "slow_loss"),
            ]:
                limit = min(
                    (
                        len(curves[r["name"]]["f"]) - 1
                        if axis_key == "updates"
                        else curves[r["name"]]["gradients"][-1]
                    )
                    for r in group
                )
                grid = np.unique(np.r_[0, np.geomspace(1, limit, 1800).astype(int)])
                vals = []
                for r in group:
                    c = curves[r["name"]]
                    xx = np.arange(len(c["f"])) if axis_key == "updates" else c["gradients"]
                    idx = np.searchsorted(xx, grid, side="right") - 1
                    vals.append(c[loss_key][idx])
                median = np.median(vals, axis=0)
                ax.plot(
                    grid,
                    np.where(median > 0, median, np.nan),
                    color=colors[method],
                    label=f"{method} median" if len(group) > 1 else method,
                    lw=1.6,
                )
                coordinates[f"{spectrum}-{method}-{axis_key}-{loss_key}-median"] = np.c_[
                    grid, median, median > 0
                ]
            time_limit = min(float(t[-1]) for r in group for t in curves[r["name"]]["timings"])
            grid = np.geomspace(1e-6, time_limit, 1800)
            vals = []
            for r in group:
                c = curves[r["name"]]
                repvals = []
                for t in c["timings"]:
                    idx = np.searchsorted(t, grid, side="right") - 1
                    # Initial x is available at time zero; do not read a future state.
                    repvals.append(c["f"][np.maximum(idx, 0)])
                vals.append(np.median(repvals, axis=0))
            median = np.median(vals, axis=0)
            axes[0, 1].plot(
                grid, np.where(median > 0, median, np.nan), color=colors[method], lw=1.6
            )
            coordinates[f"{spectrum}-{method}-time-median"] = np.c_[grid, median, median > 0]
        for ax, title, xlabel in [
            (axes[0, 0], "Current objective / distinct gradients", "distinct gradients"),
            (axes[0, 1], "Current objective / optimizer time", "seconds"),
            (axes[1, 0], "Current objective / update count (secondary)", "updates"),
            (axes[1, 1], "Slow-coordinate objective", "distinct gradients"),
        ]:
            initial_key = "slow_loss" if ax is axes[1, 1] else "f"
            initial = curves[f"{spectrum}-B-det"][initial_key][0]
            ax.set(
                xscale="log",
                yscale="log",
                title=title,
                xlabel=xlabel,
                ylim=(1e-12, 2 * initial),
            )
            ax.grid(alpha=0.2)
            ax.axhline(1e-8, color="gray", ls=":", lw=0.8)
        axes[0, 0].legend(fontsize=8)
        fig.suptitle(f"{spectrum}: frozen B vs specified AR_AGD and correctly tuned baselines")
        fig.tight_layout()
        fig.savefig(figdir / f"{spectrum}-performance.png", dpi=160)
        fig.savefig(figdir / f"{spectrum}-performance.pdf")
        plt.close(fig)
        # Full signed loss range for every individual seed.
        fig, ax = plt.subplots(figsize=(9, 5))
        for method in CONFIG["methods"]:
            group = [
                r
                for r in meta["runs"]
                if r["spectrum"] == spectrum and r["method"] == method and not r["slow_only"]
            ]
            for j, r in enumerate(group):
                c = curves[r["name"]]
                ax.plot(
                    c["gradients"],
                    c["f"],
                    color=colors[method],
                    lw=0.6,
                    alpha=0.5,
                    label=method if j == 0 else None,
                )
        ax.set(
            xlabel="distinct gradients",
            ylabel="raw signed objective",
            xscale="symlog",
            title=f"{spectrum}: full work horizon and signed loss",
        )
        ax.set_yscale("symlog", linthresh=1e-12)
        ax.legend()
        fig.tight_layout()
        fig.savefig(figdir / f"{spectrum}-signed.png", dpi=140)
        plt.close(fig)
        b = f"{spectrum}-B-det"
        slow = f"{spectrum}-B-slow-only"
        with np.load(run_dir / f"{b}.npz") as z, np.load(outdir / f"{b}-modes.npz") as mode:
            indices = np.flatnonzero(z["reset"])
            xaxis = z["gradients"][1:]
            fig, axes = plt.subplots(2, 2, figsize=(12, 8))
            for name, label in ((b, "full B"), (slow, "slow-only diagnostic")):
                c = curves[name]
                axes[0, 0].plot(
                    c["gradients"],
                    np.where(c["slow_loss"] > 0, c["slow_loss"], np.nan),
                    label=label,
                )
                coordinates[f"{name}-slow-loss"] = np.c_[c["gradients"], c["slow_loss"]]
            axes[0, 0].set(
                xscale="log",
                yscale="log",
                ylim=(1e-12, None),
                xlabel="distinct gradients",
                ylabel="slow loss",
            )
            axes[0, 0].legend()
            axes[0, 1].scatter(xaxis[indices], z["f"][1:][indices], s=12, label="resets")
            axes[0, 1].set(
                xscale="log",
                yscale="log",
                xlabel="distinct gradients",
                ylabel="objective at B resets",
            )
            axes[1, 0].plot(xaxis[indices], z["age"][indices], ".-")
            axes[1, 0].set(
                xscale="log", xlabel="distinct gradients", ylabel="completed segment length"
            )
            for key, label in (
                ("global_power", "global"),
                ("slow_power", "slow mode"),
                ("faster_power", "other modes"),
            ):
                axes[1, 1].plot(xaxis, mode[key], lw=0.7, label=label)
                coordinates[f"{b}-{key}"] = np.c_[xaxis, mode[key]]
            axes[1, 1].set(xscale="log", xlabel="distinct gradients", ylabel="power")
            axes[1, 1].set_yscale("symlog", linthresh=1e-12)
            axes[1, 1].legend(fontsize=8)
            fig.suptitle(f"{spectrum}: B mechanism; controls do not count as benchmark wins")
            fig.tight_layout()
            fig.savefig(figdir / f"{spectrum}-B-mechanism.png", dpi=160)
            fig.savefig(figdir / f"{spectrum}-B-mechanism.pdf")
            plt.close(fig)
            reps = mode["representative_indices"]
            windows = mode["window_indices"]
            powers = mode["window_power"]
            lam = mode["eigenvalues"]
            fig, axes = plt.subplots(
                1, max(1, len(reps)), figsize=(5 * max(1, len(reps)), 4.5), squeeze=False
            )
            global_window = z["power"][windows]
            for ax, center in zip(axes[0], reps, strict=False):
                take = np.abs(windows - center) <= 3
                matrix = powers[take]
                selected = np.unique(np.r_[0, np.argsort(np.max(np.abs(matrix), axis=0))[-4:]])
                for j in selected:
                    ax.plot(windows[take] + 1, matrix[:, j], ".-", label=f"lambda={lam[j]:.3g}")
                ax.plot(windows[take] + 1, global_window[take], "k--", lw=1, label="global P")
                ax.axvline(center + 1, color="black", ls=":")
                ax.set_title(f"reset at update {center + 1}")
                slow_at_reset = abs(matrix[np.flatnonzero(windows[take] == center)[0], 0])
                linear_scale = max(1e-30, slow_at_reset * 0.1)
                magnitude = max(np.max(np.abs(matrix)), np.max(np.abs(global_window[take])))
                ax.set_yscale("symlog", linthresh=linear_scale)
                high_exp = np.floor(np.log10(magnitude))
                low_exp = min(high_exp, np.ceil(np.log10(linear_scale)) + 1)
                exponents = np.unique(np.rint(np.linspace(low_exp, high_exp, 3)).astype(int))
                ticks = 10.0**exponents
                ax.set_yticks(np.r_[-ticks[::-1], 0, ticks])
                ax.set(
                    ylim=(-1.3 * magnitude, 1.3 * magnitude),
                    xlabel="update",
                    ylabel="modal / global power",
                )
                ax.legend(fontsize=7)
                coordinates[f"{b}-reset-{center + 1}"] = np.c_[windows[take] + 1, matrix]
                coordinates[f"{b}-reset-{center + 1}-global"] = np.c_[
                    windows[take] + 1, global_window[take]
                ]
            fig.tight_layout()
            fig.savefig(figdir / f"{spectrum}-reset-windows.png", dpi=160)
            plt.close(fig)
    np.savez_compressed(figdir / "plot_coordinates.npz", **coordinates)


def audit(run_dir):
    run_dir = Path(run_dir).resolve()
    (run_dir / "analysis").mkdir(exist_ok=True)
    meta = json.loads((run_dir / "metadata.json").read_text())
    check_freeze(check_prior=True)
    assert len(meta["runs"]) == 28 and len(meta["timing_repetitions"]) == 78
    assert {r["name"] for r in meta["runs"]} == {r["name"] for r in planned_paths()}
    assert meta["status"] == "complete" and not meta["errors"]
    for path, value in meta["implementation_sha256"].items():
        if Path(path).name not in ("analysis.py",):
            assert sha(ROOT / path) == value, path
    checks = []
    for rec in meta["runs"]:
        assert rec["status"] == "budget_complete"
        cost = CONFIG["primary_gradients_per_update"][rec["method"]]
        assert rec["numerical_gradients"] == CONFIG["gradient_budget"]
        assert (
            rec["literal_gradient_requests"]
            == rec["updates"] * CONFIG["literal_gradients_per_update"][rec["method"]]
        )
        assert rec["objectives"] == rec["updates"] + 1
        with np.load(run_dir / f"{rec['name']}.npz") as archive:
            z = {key: archive[key] for key in archive.files}
            f = z["f"]
            assert np.all(np.isfinite(f))
            np.testing.assert_array_equal(z["gradients"], np.arange(len(f)) * cost)
            if rec["method"] == "B":
                armed = False
                age = 0
                for i, P in enumerate(z["power"]):
                    age += 1
                    event = armed and P >= 0
                    cap = age >= CONFIG["B_cap"]
                    assert bool(z["event"][i]) == event and bool(z["cap"][i]) == cap
                    assert bool(z["reset"][i]) == bool(event or cap)
                    assert z["age"][i] == age
                    armed = armed or P < 0
                    if event or cap:
                        age, armed = 0, False
                A, x0, U, lam = load_problem(rec["spectrum"], rec["slow_only"])
                # Independent objective, endpoint power and selected recurrence checks.
                for i in np.unique(np.r_[0, np.flatnonzero(z["reset"]), len(f) - 2]):
                    x = z["x"][i]
                    y = (
                        np.zeros_like(x)
                        if i == 0 or z["reset"][i - 1]
                        else z["velocity_pre_reset"][i - 1]
                    )
                    h = np.sqrt(CONFIG["eta"])
                    half = x + h * y
                    xp = half - (h**2) * (A @ half)
                    vp = y - h * (A @ xp)
                    np.testing.assert_array_equal(xp, z["x"][i + 1])
                    np.testing.assert_array_equal(vp, z["velocity_pre_reset"][i])
                    assert float((A @ xp) @ vp) == z["power"][i]
                    assert 0.5 * xp @ A @ xp == f[i + 1]
            if not rec["slow_only"]:
                for rep in range(3):
                    with np.load(run_dir / f"{rec['name']}-timing-{rep}.npz") as t:
                        np.testing.assert_array_equal(f, t["f"])
                        np.testing.assert_array_equal(z["x_final"], t["x_final"])
        checks.append({"name": rec["name"], "passed": True})
    result = {
        "passed": True,
        "paths": checks,
        "checks": [
            "frozen config/protocol/B bytes",
            "all prior artifacts unchanged",
            "matrix hashes/construction validation",
            "all 28 work budgets and literal/objective counts",
            "all 78 full timing path equalities",
            "all B decisions and selected independently reconstructed events",
        ],
        "current_analysis_sha256": sha(Path(__file__)),
    }
    write_json(run_dir / "analysis/audit.json", result)
    print("AUDIT PASSED:", len(checks), "paths")
