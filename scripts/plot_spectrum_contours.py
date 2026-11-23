#!/usr/bin/env python3
"""Contour slices of the two quadratic fixtures in eigen-coordinates. Runs no optimizer.

Each panel is the exact restriction of f(x) = x^T A x / 2 to the plane spanned by
the slowest eigenvector v_1 and one other eigenvector v_k, so
f = (lambda_1 y_1^2 + lambda_k y_k^2) / 2 with equal axis scaling.
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

BLUE = "#2a78d6"
INK, MUTED, GRID = "#1a1a19", "#5f5e58", "#e1e0d9"
SEQUENTIAL = LinearSegmentedColormap.from_list("blue", ["#eef4fc", BLUE, "#123a6b"])
CASES = [("Linear spectrum", "quadratic_paper.npz"), ("Log spectrum", "quadratic_log.npz")]
PARTNERS = [2, 10, 30]  # 1-based index k of the eigenvector paired with v_1


def style(axes):
    axes.tick_params(colors=MUTED, labelsize=10)
    for spine in axes.spines.values():
        spine.set_color(GRID)


def spectrum_panel(axes, eigenvalues, title):
    axes.vlines(eigenvalues, 0, 1, color=BLUE, lw=0.8)
    axes.vlines(eigenvalues[[k - 1 for k in [1, *PARTNERS]]], 0, 1, color=INK, lw=1.4)
    axes.set_xscale("log")
    axes.set_xlim(eigenvalues[0] / 3, eigenvalues[-1] * 3)
    axes.set_yticks([])
    axes.set_title(title, fontsize=12, color=INK, loc="left")
    axes.set_xlabel("Eigenvalue (100 ticks; plotted pairs in black)", color=MUTED, fontsize=11)
    style(axes)


def slice_panel(axes, slow, stiff, k):
    grid = np.linspace(-1.0, 1.0, 801)
    y1, yk = np.meshgrid(grid, grid)
    f = 0.5 * (slow * y1**2 + stiff * yk**2)
    # Quadratic level spacing: contour lines are equally spaced along the stiff axis.
    levels = 0.5 * stiff * np.linspace(0.0, 1.0, 9) ** 2
    axes.contourf(y1, yk, f, levels=levels, cmap=SEQUENTIAL, extend="max")
    axes.contour(y1, yk, f, levels=levels[1:], colors="white", linewidths=0.6)
    axes.set_aspect("equal")
    axes.set_xticks([-1, 0, 1])
    axes.set_yticks([-1, 0, 1])
    aspect = np.sqrt(stiff / slow)
    axes.set_title(
        f"$v_1$ vs $v_{{{k}}}$: level sets {aspect:,.0f} : 1"
        if aspect >= 100
        else f"$v_1$ vs $v_{{{k}}}$: level sets {aspect:.3g} : 1",
        fontsize=12,
        color=INK,
        loc="left",
    )
    axes.set_xlabel(f"along $v_1$ ($\\lambda$ = {slow:.3g})", color=MUTED, fontsize=11)
    axes.set_ylabel(f"along $v_{{{k}}}$ ($\\lambda$ = {stiff:.3g})", color=MUTED, fontsize=11)
    style(axes)


def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--fixtures", type=Path, default=root / "configs/stat605/fixtures")
    parser.add_argument("--output", type=Path, default=root / "tmp/spectrum_contours.png")
    args = parser.parse_args()

    fig, axes = plt.subplots(
        len(CASES),
        1 + len(PARTNERS),
        figsize=(15.5, 7.6),
        gridspec_kw={"width_ratios": [1.25, 1, 1, 1]},
    )
    for row, (title, filename) in zip(axes, CASES, strict=True):
        with np.load(args.fixtures / filename) as fixture:
            eigenvalues = np.sort(fixture["eigenvalues"])
        spectrum_panel(row[0], eigenvalues, title)
        for ax, k in zip(row[1:], PARTNERS, strict=True):
            slice_panel(ax, eigenvalues[0], eigenvalues[k - 1], k)
    fig.tight_layout()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.output, dpi=150, facecolor="white")
    plt.close(fig)
    print(args.output)


if __name__ == "__main__":
    main()
