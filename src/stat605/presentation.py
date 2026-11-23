"""Audit saved final-study traces and export compact presentation assets."""

import argparse
import json
import tarfile
from collections import defaultdict
from pathlib import Path
from statistics import median

import matplotlib.pyplot as plt
import numpy as np

from stat605.final_study import METHOD_NAMES, audit, paths
from stat605.final_study import cases as planned_cases
from stat605.spectral_reporting import (
    METHODS,
    _loss_figure,
    _target_tables,
    _write_csv,
    plot_modal_energy,
)
from stat605.spectral_suite import _digest, _save_json


def save(fig, output, name):
    for extension in ("png", "pdf"):
        fig.savefig(output / f"{name}.{extension}", dpi=180, bbox_inches="tight")
    plt.close(fig)


def robustness_figure(robustness_rows, budget, output):
    """Show sensitivity costs on an explicit positive logarithmic range."""
    names = list(METHOD_NAMES)
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), layout="constrained")
    for ax, spectrum in zip(axes, ("linear", "log"), strict=True):
        grouped = defaultdict(list)
        for r in robustness_rows:
            if r["case"].startswith(spectrum):
                grouped[r["method"], r["label"]].append(r)
        for method in names:
            for label, marker in (
                ("mu-0.01", "<"),
                ("mu-1", "o"),
                ("mu-100", ">"),
                ("step-0.5", "s"),
                ("step-1", "+"),
                ("step-1.1", "x"),
            ):
                group = grouped.get((method, label), [])
                if not group:
                    continue
                val = median(
                    np.inf if r["sustained_gradients"] is None else r["sustained_gradients"]
                    for r in group
                )
                ax.scatter(
                    names.index(method),
                    val if np.isfinite(val) else min(budget, 100000) * 1.3,
                    marker=marker,
                    color=METHODS[method][1],
                    label=label if method == "AGD" else None,
                )
                failures = sum(r["status"] == "failure" for r in group)
                if failures:
                    ax.annotate(
                        f"{failures}/{len(group)} fail",
                        (names.index(method), min(budget, 100000) * 1.7),
                        ha="center",
                        fontsize=8,
                    )
        ax.set_ylim(5, min(budget, 100000) * 3)

        ax.set(
            title=spectrum + "; × = 1.1 stress",
            xticks=range(len(names)),
            xticklabels=names,
            yscale="log",
            ylabel="Sustained gradients; censored at top",
        )
        ax.tick_params(axis="x", labelrotation=90)
    axes[0].legend(ncols=2)
    save(fig, output, "robustness")


def report(directories, output, robustness=()):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    runs, sources, manifests = [], [], []
    root = output / "_trace_links"
    root.mkdir()
    for i, directory in enumerate(directories):
        directory = Path(directory).resolve()
        manifest = audit(directory)
        if manifest["status"] != "complete" or manifest["stage"] != "main":
            raise ValueError("Main reports require complete main shards")
        manifests.append(manifest)
        sources.append(
            {"directory": str(directory), "summary_sha256": _digest(directory / "summary.json")}
        )
        (root / str(i)).symlink_to(directory, target_is_directory=True)
        for original in manifest["runs"]:
            run = dict(original)
            run["trace"] = f"{i}/{run['trace']}"
            runs.append(run)
    if (
        len({m.get("tuning_sha256") for m in manifests}) != 1
        or len({m["smoke"] for m in manifests}) != 1
    ):
        raise ValueError("Main shards must share tuning and execution mode")
    for key in ("src/stat605/benchmark.py", "src/stat605/course_methods.py"):
        if len({m["source_sha256"].get(key) for m in manifests}) != 1:
            raise ValueError("Main shards used different numerical implementations")
    keys = [(r["case"], r["method"], r["seed"]) for r in runs]
    expected_keys = {
        (case[0], method, seed) for case in planned_cases() for method, seed in paths()
    }
    if set(keys) != expected_keys or len(keys) != len(expected_keys):
        raise ValueError("Require all 132 distinct matched main paths")
    if len({r["gradient_budget"] for r in runs}) != 1:
        raise ValueError("Main budgets must be uniform")
    for method, field, symbol in (
        ("FIXED_RHGD", "period_steps", "m"),
        ("ENDPOINT_RHGD", "beta", "β"),
        ("KINETIC_RHGD", "beta", "β"),
    ):
        name, color, style = METHODS[method]
        METHODS[method] = (
            name.split(" (")[0] + f" ({symbol}={manifest['parameters'][method][field]})",
            color,
            style,
        )
    rows, groups = _target_tables(runs)
    _write_csv(output / "targets.csv", rows)
    _write_csv(output / "work_to_target.csv", groups)
    costs = [
        {
            k: r[k]
            for k in (
                "case",
                "method",
                "seed",
                "status",
                "failure",
                "gradient_budget",
                "numerical_gradients",
                "literal_gradient_requests",
                "objectives",
                "controller_objectives",
                "diagnostic_objectives",
                "reset_count",
                "rejected_trials",
                "charged_unfinished_gradients",
                "final_relative_gap",
                "optimizer_seconds",
                "diagnostic_seconds",
            )
        }
        for r in runs
    ]
    for row in costs:
        row["target_setup_objectives"] = 3
        row["benchmark_plus_target_setup_objectives"] = row["objectives"] + 3
    _write_csv(output / "costs.csv", costs)
    _save_json(
        output / "provenance.json",
        {
            "raw_sources": sources,
            "paths": len(runs),
            "budget": runs[0]["gradient_budget"],
            "smoke": manifest["smoke"],
            "parameters": manifest["parameters"],
        },
    )
    # Figures are generated from raw saved traces, after hashes/crossings pass.
    scope = (
        "Software check only"
        if manifest["smoke"]
        else "Final matched quadratic study; five algorithm seeds"
    )
    rhgd = [
        r
        for r in runs
        if r["method"] in ("RHGD", "FIXED_RHGD", "B", "ENDPOINT_RHGD", "KINETIC_RHGD")
    ]
    for extension in ("png", "pdf"):
        for axis in ("gradients", "iteration"):
            _loss_figure(
                root, output / f"full_{axis}.{extension}", runs, axis, scope, [1e-4, 1e-6, 1e-8]
            )
            _loss_figure(
                root,
                output / f"rhgd_{axis}.{extension}",
                rhgd,
                axis,
                scope + "; displayed target range",
                [1e-4, 1e-6, 1e-8],
                loss_limits=(1e-10, 2),
            )
        design = json.loads((Path(directories[0]) / "design.json").read_text())
        plot_modal_energy(design["problems"], output / f"geometry.{extension}")
    design = json.loads((Path(directories[0]) / "design.json").read_text())
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    for problem in design["problems"][::2]:
        ax.plot(np.arange(1, 101), problem["eigenvalues"], label=problem["spectrum"])
    ax.set(
        xlabel="Ordered mode",
        ylabel="Eigenvalue",
        yscale="log",
        title="Equal endpoints; different spectral distributions",
    )
    ax.legend()
    save(fig, output, "eigenvalue_distributions")
    tuning_path = Path(directories[0]).parent / "tune"
    if (tuning_path / "summary.json").is_file():
        tuning = audit(tuning_path)
        if _digest(tuning_path / "summary.json") != manifest["tuning_sha256"]:
            raise ValueError("Tuning summary hash differs from main selection")
        tuning_rows = []
        for r in tuning["runs"]:
            hit = r["crossings"][1]["sustained"]
            tuning_rows.append(
                {
                    "case": r["case"],
                    "method": r["method"],
                    "parameter": r["label"],
                    "status": r["status"],
                    "budget": r["gradient_budget"],
                    "observed_sustained_gradients": None if hit is None else hit["gradients"],
                    "final_relative_gap": r["final_relative_gap"],
                    "numerical_gradients": r["numerical_gradients"],
                    "objectives": r["objectives"],
                    "resets": r["reset_count"],
                }
            )
        _write_csv(output / "training_observed.csv", tuning_rows)
        score_rows = [
            {
                "method": method,
                "grid_value": value,
                "mean_penalized_selection_work": score[0],
                "mean_log_final_relative_gap": score[1],
            }
            for method, scores in tuning["selection_scores"].items()
            for value, score in zip(tuning["protocol"]["grids"][method], scores, strict=True)
        ]
        _write_csv(output / "training_selection_scores.csv", score_rows)
    names = list(METHOD_NAMES)
    cases = list(dict.fromkeys(r["case"] for r in runs))
    grid = np.full((len(names), len(cases)), np.nan)
    labels = {}
    for i, method in enumerate(names):
        for j, case in enumerate(cases):
            selected = [r for r in runs if r["method"] == method and r["case"] == case]
            hits = [r["crossings"][1]["sustained"] for r in selected]
            value = median(np.inf if h is None else h["gradients"] for h in hits)
            hit_count = sum(h is not None for h in hits)
            if np.isfinite(value):
                grid[i, j] = np.log10(max(1, value))
            labels[i, j] = f"{value:,.0f}" if np.isfinite(value) else "censored"
            labels[i, j] += f"\n{hit_count}/{len(hits)} hits"
    fig, ax = plt.subplots(figsize=(13, 9), layout="constrained")
    im = ax.imshow(np.ma.masked_invalid(grid), aspect="auto", cmap="viridis")
    ax.set(
        xticks=range(len(cases)),
        xticklabels=cases,
        yticks=range(len(names)),
        yticklabels=[METHODS[n][0] for n in names],
        title="Sustained relative gap ≤ 1e−6: gradients and success counts",
    )
    ax.tick_params(axis="x", labelrotation=0)
    for (i, j), label in labels.items():
        ax.text(
            j,
            i,
            label,
            ha="center",
            va="center",
            fontsize=8,
            color="black"
            if np.isnan(grid[i, j])
            or np.dot(im.cmap(im.norm(grid[i, j]))[:3], [0.2126, 0.7152, 0.0722]) > 0.5
            else "white",
        )
    fig.colorbar(im, ax=ax, label="log10 gradients; gray/blank means censored median")
    save(fig, output, "comparison")
    mechanism = next(
        r
        for r in runs
        if r["method"] == "ENDPOINT_RHGD"
        and r["spectrum"] == "log"
        and r["start"] == "scaled_common"
    )
    with np.load(root / mechanism["trace"], allow_pickle=False) as t:
        steps, modal = t["power_iteration"], t["modal_power"]
        fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True, layout="constrained")
        split = modal.shape[1] // 2
        axes[0].plot(steps, modal[:, :split].sum(1), label="Slow half")
        axes[0].plot(steps, modal[:, split:].sum(1), label="Fast half")
        axes[0].plot(steps, t["global_power"], label="Total", ls=":")
        axes[0].set_ylabel("Modal power")
        axes[0].legend(ncols=3)
        axes[1].plot(steps, t["signal"][steps], color=METHODS["ENDPOINT_RHGD"][1])
        axes[1].axhline(0, color="gray", lw=0.5)
        axes[1].set_ylabel("Endpoint signal")
        axes[2].plot(steps, t["loss"][steps] / t["loss"][0])
        axes[2].set(xlabel="Iteration", ylabel="Relative gap", yscale="log")
        for ax in axes[:2]:
            ax.set_yscale("symlog", linthresh=1e-10)
            lo, hi = ax.get_ylim()
            ticks = ax.get_yticks()
            visible = ticks[(ticks >= lo) & (ticks <= hi)]
            selected = [0.0]
            for side in (visible[visible < -3e-10], visible[visible > 3e-10]):
                if len(side):
                    selected.extend(
                        side[np.linspace(0, len(side) - 1, min(3, len(side)), dtype=int)]
                    )
            ax.set_yticks(sorted(selected))
        for ax in axes:
            for position in steps[t["reset"][steps]]:
                ax.axvline(position, color="gray", alpha=0.2, lw=0.6)
        fig.suptitle("Reset timing combines slow and fast modes on one log-spectrum trajectory")
        save(fig, output, "mechanism")
    robustness_rows = []
    for directory in robustness:
        data = audit(directory)
        if data["status"] != "complete":
            raise ValueError("Robustness shard incomplete")
        for r in data["runs"]:
            hit = r["crossings"][1]["sustained"]
            robustness_rows.append(
                {
                    "case": r["case"],
                    "method": r["method"],
                    "seed": r["seed"],
                    "label": r["label"],
                    "status": r["status"],
                    "failure": r["failure"],
                    "sustained_gradients": None if hit is None else hit["gradients"],
                    "first_gradients": None
                    if r["crossings"][1]["first"] is None
                    else r["crossings"][1]["first"]["gradients"],
                    "numerical_gradients": r["numerical_gradients"],
                    "objectives": r["objectives"],
                    "controller_objectives": r["controller_objectives"],
                    "reset_count": r["reset_count"],
                    "rejected_trials": r["rejected_trials"],
                    "charged_unfinished_gradients": r["charged_unfinished_gradients"],
                    "final_relative_gap": r["final_relative_gap"],
                    "eta": r["settings"]["eta"],
                    "supplied_mu": r["settings"]["supplied_mu"],
                    "period_steps": r["settings"]["parameters"].get("period_steps"),
                    "realized_period": r["settings"]["parameters"].get("period_steps", 0)
                    * np.sqrt(r["settings"]["eta"])
                    if r["method"] == "FIXED_RHGD"
                    else None,
                }
            )
    if robustness_rows:
        robust_keys = [(r["case"], r["method"], r["seed"], r["label"]) for r in robustness_rows]
        if len(robust_keys) != 198 or len(set(robust_keys)) != 198:
            raise ValueError("Require all 198 distinct robustness paths")
        _write_csv(output / "robustness.csv", robustness_rows)
        robustness_figure(robustness_rows, runs[0]["gradient_budget"], output)

    failures = sum(r["status"] == "failure" for r in runs)
    lines = [
        "# Audited final results",
        "",
        f"All {len(runs)} main paths are present; {failures} numerical failures. Uniform budget: {runs[0]['gradient_budget']:,} gradients per path. Primary target: sustained relative gap 1e-6.",
        "",
        f"Frozen controller parameters: `{json.dumps(manifest['parameters'], sort_keys=True)}`.",
        "",
        "Randomized paths use five algorithm seeds on fixed problems. Missing targets remain censored in medians and success denominators. Costs below are observed gradients, never selection penalties.",
        "",
        "| Case | Method | Sustained gradients (median) | Hits / paths | Final relative gap (median) |",
        "| --- | --- | ---: | ---: | ---: |",
    ]
    for case in cases:
        for method in names:
            group = [r for r in runs if r["case"] == case and r["method"] == method]
            hits = [r["crossings"][1]["sustained"] for r in group]
            cost = median(np.inf if h is None else h["gradients"] for h in hits)
            cost_label = f"{cost:,.0f}" if np.isfinite(cost) else "censored"
            final = median(
                np.inf if r["final_relative_gap"] is None else r["final_relative_gap"]
                for r in group
            )
            lines.append(
                f"| {case} | {METHODS[method][0]} | {cost_label} | {sum(h is not None for h in hits)}/{len(hits)} | {final:.3g} |"
            )
    lines += ["", "## Geometry", ""]
    for start in ("scaled_common", "equal"):
        group = [r for r in runs if r["start"] == start]
        lines.append(
            f"- {start}: {sum(r['crossings'][1]['sustained'] is not None for r in group)}/{len(group)} sustained primary-target hits."
        )
    transient = sum(
        r["crossings"][1]["first"] is not None and r["crossings"][1]["sustained"] is None
        for r in runs
    )
    lines += [
        "",
        f"First primary-target crossing without a sustained crossing: {transient}/{len(runs)} paths.",
        "",
        "## Robustness",
        "",
    ]
    if robustness_rows:
        lines.append(
            f"{len(robustness_rows)} paths retained, including {sum(r['status'] == 'failure' for r in robustness_rows)} numerical failures and {sum(r['sustained_gradients'] is None for r in robustness_rows)} censored/failed sustained targets. See robustness.csv for every case, setting and realized fixed-controller physical period. h/h0=1.1 is a stress test."
        )
    else:
        lines.append(
            "Robustness pending; no robustness conclusion is licensed by these main results."
        )
    lines += [
        "",
        "## Interpretation limits",
        "",
        "Training selected beta=0 for both normalization families; positive normalization exponents did not win the predefined training criterion. This is a negative tuning result, not a general impossibility result. Endpoint beta=0 is the existing power controller. Compare discrete kinetic beta=0 separately; discretization can change reset times. Conclusions are conditional on these six geometries, budgets and selected parameters. No general acceleration or novelty claim follows.",
    ]
    (output / "RESULTS.md").write_text("\n".join(lines) + "\n")
    # Representative retained evidence, with qualifications in the speaking outline.
    evidence = [
        (
            Path("docs/evidence/rhgd-logistic-replay.png"),
            "RHGD: author-source replay\nLegend ‘ours’ refers to the authors",
        ),
        (Path("docs/agd_figures/replication.png"), "AGD: new instance"),
        (Path("docs/evidence/rcm/rcm_seed605.png"), "RCM: new seeded instance"),
    ]
    fig, axes = plt.subplot_mosaic(
        [["agd", "agd"], ["rhgd", "rcm"]], figsize=(12, 9), layout="constrained"
    )
    for key, (path, title) in zip(("rhgd", "agd", "rcm"), evidence, strict=True):
        ax = axes[key]
        if path.is_file():
            ax.imshow(plt.imread(path))
        else:
            records = json.loads(Path("docs/evidence/rcm/pilot_summary.json").read_text())
            for offset, spectrum, color in ((-0.18, "linear", "#0072B2"), (0.18, "log", "#D55E00")):
                selected = [r for r in records if r["problem"] == spectrum]
                ax.bar(
                    np.arange(3) + offset,
                    [r["final_gap"] for r in selected],
                    width=0.35,
                    color=color,
                    label=spectrum,
                )
            ax.set(
                yscale="log",
                xticks=range(3),
                xticklabels=["kin", "mmd-r", "mmd-dr"],
                ylabel="Final gap at 300 gradients",
            )
            ax.legend()
            title = "RCM: retained bounded pilot"
        ax.set_title(title)
        if path.is_file():
            ax.axis("off")
    fig.suptitle("Representative replication evidence; source parity differs from paper agreement")
    save(fig, output, "replication_overview")
    # The portable manifest hashes every exported figure/table; raw traces stay out of Git.
    for link in root.iterdir():
        link.unlink()
    root.rmdir()
    _save_json(
        output / "ASSET_HASHES.json", {p.name: _digest(p) for p in output.iterdir() if p.is_file()}
    )
    return groups


def archive(directories, destination):
    destination = Path(destination)
    with tarfile.open(destination, "x:gz" if destination.suffix == ".gz" else "x") as tar:
        for directory in directories:
            directory = Path(directory)
            audit(directory)
            tar.add(directory, arcname=directory.name)
    destination.with_suffix(destination.suffix + ".sha256").write_text(
        _digest(destination) + "  " + destination.name + "\n"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", nargs=2, required=True, type=Path)
    parser.add_argument("--robustness", nargs=2, type=Path, default=())
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    report(args.main, args.output, args.robustness)
    if args.archive:
        evidence = [*args.main, *args.robustness]
        for stage in ("pilot", "tune"):
            directory = args.main[0].parent / stage
            if (directory / "summary.json").is_file():
                evidence.append(directory)
        archive(evidence, args.archive)


if __name__ == "__main__":
    main()
