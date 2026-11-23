"""Generate the quadratic comparison tables and figures from saved run evidence."""

import csv
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import EngFormatter, LogLocator

SPECTRA = {"linear": "Linear spacing", "log": "Log spacing", "clustered": "Two clusters"}
STARTS = {
    "common": "Common start",
    "scaled_common": "Rescaled common",
    "equal": "Equal modal energy",
}
METHODS = {
    "AGD": ("AGD", "#0072B2", "-"),
    "AR_AGD": ("Historical restart AGD", "#7852A3", "--"),
    "CAGD": ("CAGD", "#008367", "-"),
    "RHGD": ("RHGD", "#D55E00", "-"),
    "B": ("Power-reset RHGD", "#252525", "--"),
}
METHODS.update(
    {
        "GD": ("GD", "#999999", ":"),
        "FREE_AGD": ("Mu-free AGD", "#56B4E9", "--"),
        "FUNCTION_AGD": ("Function-restart AGD", "#CC79A7", "-"),
        "GRADIENT_AGD": ("Gradient-restart AGD", "#7852A3", "--"),
        "FIXED_RHGD": ("Fixed-time RHGD", "#E69F00", ":"),
        "ENDPOINT_RHGD": ("Endpoint normalized RHGD", "#A65628", "-"),
        "KINETIC_RHGD": ("Kinetic normalized RHGD", "#F781BF", "--"),
        "RCM_kin": ("RCM kin", "#1B9E77", "-"),
        "RCM_mmd-r": ("RCM mmd-r", "#7570B3", "--"),
        "RCM_mmd-dr": ("RCM mmd-dr", "#66A61E", ":"),
    }
)
PURPOSES = {
    "local_check": "Local software check",
    "grace_pilot": "Grace pilot",
    "grace_comparison": "Grace comparison",
}
CROSSINGS = ("first", "sustained")


def _target_tables(runs):
    """Each miss ranks after every observed hit. Failures remain in the denominator."""
    rows = []
    groups = defaultdict(list)
    for run in runs:
        for crossing in run["crossings"]:
            row = {k: run[k] for k in ("spectrum", "start", "method", "seed", "status", "failure")}
            row.update(
                target=crossing["target"],
                total_gradients=run["numerical_gradients"],
                total_literal_gradients=run["literal_gradient_requests"],
                total_objectives=run["objectives"],
                updates=run["updates"],
                resets=run["reset_count"],
            )
            miss = "failed" if run["status"] == "failure" else "budget_censored"
            for kind in CROSSINGS:
                hit = crossing[kind]
                row[f"{kind}_status"] = "hit" if hit is not None else miss
                for field in ("iteration", "gradients"):
                    row[f"{kind}_{field}"] = hit[field] if hit is not None else None
            rows.append(row)
            groups[tuple(row[k] for k in ("spectrum", "start", "method", "target"))].append(row)

    summaries = []
    for key, group in groups.items():
        summary = dict(zip(("spectrum", "start", "method", "target"), key, strict=True))
        summary.update(runs=len(group), failures=sum(r["status"] == "failure" for r in group))
        for kind in CROSSINGS:
            states = [r[f"{kind}_status"] for r in group]
            summary[f"{kind}_hits"] = states.count("hit")
            summary[f"{kind}_budget_censored"] = states.count("budget_censored")
            summary[f"{kind}_failed_before_hit"] = states.count("failed")
            for field in ("iteration", "gradients"):
                values = [r[f"{kind}_{field}"] for r in group]
                middle = median(np.inf if value is None else value for value in values)
                summary[f"{kind}_median_{field}"] = middle if np.isfinite(middle) else None
        summaries.append(summary)
    return rows, summaries


def _write_csv(path, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _grid(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)


def _label_bottom(axes, text):
    """Axes-level labels reserve their own space above the shared legend."""
    bottom = [ax for ax in axes[-1] if ax.get_visible()]
    if len(bottom) % 2:
        bottom[len(bottom) // 2].set_xlabel(text)
    else:
        for ax in bottom:
            ax.set_xlabel(text)


def _save_figure(fig, output):
    try:
        fig.savefig(output, dpi=145, bbox_inches="tight")
    finally:
        plt.close(fig)


def plot_modal_energy(problems, output, *, title="Initial energy across eigenvalues"):
    """Plot absolute per-mode starting energies on the common eigenvalue scale."""
    spectra = list(dict.fromkeys(p["spectrum"] for p in problems))
    fig, axes = plt.subplots(
        1,
        len(spectra),
        figsize=(4 * len(spectra), 3.9),
        squeeze=False,
        sharey=True,
        layout="constrained",
    )
    styles = {
        "common": ("#0072B2", "o"),
        "scaled_common": ("#D55E00", "+"),
        "equal": ("#222222", "_"),
    }
    nonpositive = False
    max_energy = 0.0
    legend = {}
    for ax, spectrum in zip(axes[0], spectra, strict=True):
        for item in (p for p in problems if p["spectrum"] == spectrum):
            energy = np.asarray(item["initial_modal_energy"])
            start = item["start"]
            label = STARTS.get(start, start)
            color, marker = styles.get(start, ("#008367", "x"))
            # An open circle leaves an overlapping rescaled point visible.
            handle = ax.scatter(
                item["eigenvalues"],
                energy,
                s=22,
                marker=marker,
                facecolors="none" if marker == "o" else color,
                edgecolors=color if marker == "o" else None,
                linewidths=1.15,
                alpha=0.85,
            )
            legend[label] = handle
            nonpositive |= bool(np.any(energy <= 0))
            max_energy = max(max_energy, float(np.max(energy)))
        ax.set(xscale="log", title=SPECTRA.get(spectrum, spectrum))
        _grid(ax)
    if nonpositive:
        axes[0, 0].set_yscale("symlog", linthresh=max(1e-16, max_energy * 1e-12))
    else:
        axes[0, 0].set_yscale("log")
    fig.suptitle(title)
    _label_bottom(axes, "Eigenvalue")
    fig.supylabel("Initial potential energy per mode")
    fig.legend(
        legend.values(), legend.keys(), loc="outside lower center", ncols=len(legend), frameon=False
    )
    _save_figure(fig, output)


def _drawing_indices(loss, bins=800):
    """Keep endpoint and within-bin extrema in chronological order on long plots."""
    if loss.size <= 2 * bins:
        return np.arange(loss.size)
    edges = np.linspace(0, loss.size, bins + 1, dtype=int)
    indices = [0, loss.size - 1]
    for lo, hi in zip(edges[:-1], edges[1:], strict=True):
        segment = loss[lo:hi]
        indices.extend((lo + np.argmin(segment), lo + np.argmax(segment)))
    return np.unique(indices)


def _loss_figure(run_dir, output, runs, axis, scope, targets, loss_limits=None):
    spectra = list(dict.fromkeys(r["spectrum"] for r in runs))
    starts = list(dict.fromkeys(r["start"] for r in runs))
    by_work = axis == "gradients"
    size = (
        (3.2 * len(spectra) + 0.3, 1.95 * len(starts) + 1.4)
        if by_work
        else (4.0 * len(spectra) + 0.3, 2.45 * len(starts) + 1.6)
    )
    fig, axes = plt.subplots(
        len(starts),
        len(spectra),
        figsize=size,
        sharex=True,
        sharey="row" if by_work else True,
        squeeze=False,
        layout="constrained",
    )
    legend = {}
    nonpositive_rows = np.zeros(len(starts), dtype=bool)
    max_x = 0
    for run in runs:
        row = starts.index(run["start"])
        ax = axes[row, spectra.index(run["spectrum"])]
        method = run["method"]
        name, color, style = METHODS.get(method, (method, "C7", "-."))
        with np.load(run_dir / run["trace"], allow_pickle=False) as trace:
            x, y = trace[axis], trace["loss"]
        max_x = max(max_x, x.max(initial=0))
        finite = np.isfinite(y)
        x, y = x[finite], y[finite]
        legend[name] = Line2D([], [], color=color, ls=style)
        if not y.size:
            continue
        selected = _drawing_indices(y)
        ax.plot(
            x[selected],
            y[selected],
            color=color,
            ls=style,
            lw=1.3,
            alpha=0.55 if run["seed"] is not None else 0.95,
            marker="." if len(y) == 1 else None,
        )
        nonpositive_rows[row] |= np.any(y <= 0)
        if run["status"] == "failure":
            ax.plot(x[-1], y[-1], "x", color=color)
            legend["Last finite state of failed run"] = Line2D(
                [], [], color="0.3", marker="x", ls="none"
            )
    scale_groups = nonpositive_rows if by_work else [nonpositive_rows.any()]
    for ax, nonpositive in zip(axes[:, 0], scale_groups, strict=False):
        if nonpositive:
            ax.set_yscale("symlog", linthresh=max(np.finfo(float).tiny, min(targets) * 0.01))
        else:
            ax.set_yscale("log")
            if by_work:
                ax.yaxis.set_major_locator(LogLocator(numticks=6))
    if loss_limits is not None:
        for panel in axes.flat:
            panel.set_ylim(*loss_limits)
    xlabel = "Paid gradient evaluations" if by_work else "Completed iterations"
    if by_work and max_x >= 100:
        # Show the initial iterate and early paid work alongside the entire budget.
        ax = axes[0, 0]
        ax.set_xscale("symlog", linthresh=10, linscale=0.55)
        ax.set_xlim(0, max_x)
        ax.xaxis.get_major_locator().set_params(numticks=6)
        ticks = ax.get_xticks()
        ticks = ticks[(ticks >= 0) & (ticks < max_x / 3)]
        ax.set_xticks([*ticks, max_x])
        ax.xaxis.set_major_formatter(EngFormatter(sep=""))
        xlabel += " (linear to 10, then log)"
    for j, spectrum in enumerate(spectra):
        axes[0, j].set_title(SPECTRA.get(spectrum, spectrum))
    for i, start in enumerate(starts):
        axes[i, 0].set_ylabel(STARTS.get(start, start))
    for ax in axes.flat:
        _grid(ax)
    fig.suptitle(
        f"Current objective gap by {'paid gradients' if by_work else 'completed iterations'}\n"
        f"{scope} · {'Shared loss scale within each row' if by_work else 'One trajectory per run'}",
        fontsize=14,
    )
    _label_bottom(axes, xlabel)
    fig.supylabel("Current objective gap")
    fig.legend(
        legend.values(),
        legend.keys(),
        loc="outside lower center",
        ncols=min(3 if len(spectra) == 1 else 5, len(legend)),
        frameon=False,
    )
    _save_figure(fig, output)


def _power_figure(run_dir, output, runs, scope):
    records = []
    starts = list(dict.fromkeys(r["start"] for r in runs))
    for run in sorted(runs, key=lambda r: starts.index(r["start"])):
        if run["method"] != "B":
            continue
        with np.load(run_dir / run["trace"], allow_pickle=False) as trace:
            if "power_iteration" not in trace or not trace["power_iteration"].size:
                continue
            steps, power = trace["power_iteration"], trace["modal_power"]
            split = (power.shape[1] + 1) // 2
            records.append(
                (
                    run,
                    steps,
                    power[:, :split].sum(axis=1),
                    power[:, split:].sum(axis=1),
                    trace["global_power"],
                    trace["reset"][steps],
                )
            )
    if not records:
        return
    cols = len({r[0]["spectrum"] for r in records})
    rows = (len(records) + cols - 1) // cols
    fig, axes = plt.subplots(
        rows,
        cols,
        figsize=(4.0 * cols + 0.3, 2.55 * rows + 1.25),
        squeeze=False,
        layout="constrained",
    )
    for ax, (run, steps, slower, faster, total, resets) in zip(axes.flat, records, strict=False):
        ax.axhline(0, color="0.75", lw=0.75)
        ax.plot(steps, slower, color="#0072B2", label="Slow half of modes")
        ax.plot(steps, faster, color="#D55E00", ls="--", label="Fast half of modes")
        ax.plot(steps, total, color="#222222", lw=1.1, ls=":", label="Total")
        ax.scatter(
            steps[resets],
            np.full(np.count_nonzero(resets), 0.97),
            transform=ax.get_xaxis_transform(),
            marker="v",
            color="black",
            s=19,
            label="Reset",
        )
        ax.set_title(
            f"{SPECTRA.get(run['spectrum'], run['spectrum'])} · {STARTS.get(run['start'], run['start'])}"
        )
        peak = float(np.max(np.abs([slower, faster, total])))
        if peak > 0:
            threshold = max(np.finfo(float).tiny, peak * 1e-4)
            ax.set_yscale("symlog", linthresh=threshold)
            low, high = ax.get_ylim()
            # Place at most three decade ticks per sign, outside the linear region.
            ticks = ax.get_yticks()
            ticks = ticks[(low <= ticks) & (ticks <= high)]
            spaced = [0.0]
            for side in (ticks[ticks < -3 * threshold], ticks[ticks > 3 * threshold]):
                if len(side):
                    indices = np.linspace(0, len(side) - 1, min(len(side), 3), dtype=int)
                    spaced.extend(side[indices])
            ax.set_yticks(sorted(spaced))
        _grid(ax)
    for ax in list(axes.flat)[len(records) :]:
        ax.set_visible(False)
    fig.suptitle(
        f"Modal power along power-reset RHGD trajectories\n{scope}",
        fontsize=14,
    )
    _label_bottom(axes, "Iteration")
    fig.supylabel("Gradient–velocity product")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(
        handles, labels, loc="outside lower center", ncols=2 if cols == 1 else 4, frameon=False
    )
    _save_figure(fig, output)


def write_report(run_dir, output=None):
    """Rebuild the figures and target tables using saved summaries and traces only."""
    run_dir = Path(run_dir)
    output = Path(output) if output is not None else run_dir
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    if summary["status"] not in {"passed", "failure"}:
        raise ValueError("Reporting requires a finished suite so every planned run is counted")
    config, runs = summary["config"], summary["runs"]
    for run in runs:
        expected = run.get("trace_sha256")
        if expected is not None:
            actual = hashlib.sha256((run_dir / run["trace"]).read_bytes()).hexdigest()
            if actual != expected:
                raise ValueError(f"Trace digest differs from the saved run: {run['trace']}")
    scope = PURPOSES.get(config["purpose"], config["purpose"])
    if output.resolve() != run_dir.resolve():
        output.mkdir(parents=True, exist_ok=False)
    rows, groups = _target_tables(runs)
    _write_csv(output / "targets.csv", rows)
    _write_csv(output / "work_to_target.csv", groups)
    for axis in ("gradients", "iteration"):
        filename = "loss_gradients.png" if axis == "gradients" else "loss_iterations.png"
        _loss_figure(run_dir, output / filename, runs, axis, scope, config["targets"])
    plot_modal_energy(
        summary["problems"],
        output / "modal_energy.png",
        title=f"Initial energy across eigenvalues\n{scope}",
    )
    _power_figure(run_dir, output / "modal_power.png", runs, scope)
