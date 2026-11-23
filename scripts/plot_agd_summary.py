#!/usr/bin/env python3
"""Redraw the restarted-AGD report figures from saved traces. Runs no optimizer."""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
MAGENTA, GREEN, VIOLET, RED = "#e87ba4", "#008300", "#6250d6", "#e34948"
INK, MUTED, GRID = "#1a1a19", "#5f5e58", "#e1e0d9"

# Colour follows the method, not its position: q=0 is always blue, exact q orange.
Q_SWEEP_COLORS = [BLUE, AQUA, YELLOW, ORANGE, VIOLET, RED]
RESTART_STYLE = {
    "none_q0": (BLUE, "-"),
    "exact_q": (ORANGE, "-"),
    "fixed_a": (AQUA, "-"),
    "fixed_b": (YELLOW, "-"),
    "function": (MAGENTA, "--"),
    "gradient": (GREEN, "-"),
}


def panel(axes, directory, case, series, title, floor):
    for label, name, color, style in series:
        with np.load(directory / f"{case}__{name}.npz") as trace:
            axes.semilogy(
                trace["gradients"], trace["f"], color=color, ls=style, lw=1.5, label=label
            )
    axes.set_ylim(bottom=floor)
    axes.set_title(title, fontsize=10, color=INK, loc="left")
    axes.set_xlabel("Gradient evaluations (one per update)", color=MUTED, fontsize=9)
    axes.grid(True, color=GRID, lw=0.6)
    axes.tick_params(colors=MUTED, labelsize=8)
    for spine in axes.spines.values():
        spine.set_color(GRID)
    axes.legend(fontsize=8, frameon=False, labelcolor=INK)


def figure(path, panels, floor):
    fig, axes = plt.subplots(1, len(panels), figsize=(6.2 * len(panels), 4.2), squeeze=False)
    for ax, (directory, case, series, title) in zip(axes[0], panels, strict=True):
        panel(ax, directory, case, series, title, floor)
    axes[0][0].set_ylabel("Current objective gap $f(x_k) - f^*$", color=MUTED, fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150, facecolor="white")
    plt.close(fig)


def sweep(names_and_labels):
    return [
        (label, name, color, "-")
        for (label, name), color in zip(names_and_labels, Q_SWEEP_COLORS, strict=True)
    ]


def restart_series(rows):
    return [(label, name, *RESTART_STYLE[key]) for label, name, key in rows]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replication", required=True, type=Path)
    parser.add_argument("--sensitivity", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    fig1 = sweep(
        [
            ("q = 0", "q=0"),
            ("q = q*/10", "q=qstar_div_10"),
            ("q = q*/3", "q=qstar_div_3"),
            ("q = q* (exact)", "q=qstar"),
            ("q = 3 q*", "q=3_qstar"),
            ("q = 10 q*", "q=10_qstar"),
        ]
    )
    fig3 = restart_series(
        [
            ("No restart, q = 0", "no_restart_q=0", "none_q0"),
            ("No restart, exact q", "optimal_q", "exact_q"),
            ("Fixed restart every 400", "fixed_400", "fixed_a"),
            ("Fixed restart every 700", "fixed_700", "fixed_b"),
            ("Function restart, q = 0", "function_restart", "function"),
            ("Gradient restart, q = 0", "gradient_restart", "gradient"),
        ]
    )
    figure(
        args.output / "replication.png",
        [
            (args.replication, "oc_fig1_q_estimates", fig1, "Estimates of q, no restart (n = 200)"),
            (args.replication, "oc_fig3_restart", fig3, "Fixed and adaptive restart (n = 500)"),
        ],
        floor=1e-30,
    )

    mu_sweep = sweep(
        [
            ("q = 0", "no_restart_q=0"),
            ("q = 0.01 q*", "no_restart_q=0.01_qstar"),
            ("q = 0.1 q*", "no_restart_q=0.1_qstar"),
            ("q = q* (exact)", "no_restart_q=1_qstar"),
            ("q = 10 q*", "no_restart_q=10_qstar"),
            ("q = 100 q*", "no_restart_q=100_qstar"),
        ]
    )
    rules = restart_series(
        [
            ("No restart, q = 0", "no_restart_q=0", "none_q0"),
            ("No restart, exact q", "no_restart_q=1_qstar", "exact_q"),
            ("Fixed restart every 24,313", "fixed_e_sqrt_8_kappa", "fixed_a"),
            ("Function restart, q = 0", "function_restart_q=0", "function"),
            ("Gradient restart, q = 0", "gradient_restart_q=0", "gradient"),
        ]
    )
    for case, name in (("quadratic_paper", "linear"), ("quadratic_log", "log")):
        figure(
            args.output / f"sensitivity_{name}.png",
            [
                (args.sensitivity, case, mu_sweep, f"{name.capitalize()} spectrum: mu estimate"),
                (args.sensitivity, case, rules, f"{name.capitalize()} spectrum: restart rule"),
            ],
            floor=1e-20,
        )


if __name__ == "__main__":
    main()
