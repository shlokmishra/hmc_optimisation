"""Reproduce the three selected RCM curves from Section 5.1 on the seed-605 fixture."""

import argparse
import csv
import hashlib
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from stat605.rcm import rcm  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="Fresh output directory")
    out = parser.parse_args().output
    path = ROOT / "configs/stat605/fixtures/rcm_section5_1_seed605.npz"
    with np.load(path, allow_pickle=False) as data:
        a, b, x0, optimum = (data[k] for k in ("eigenvalues", "b", "x0", "x_star"))
        h = float(data["h"])
        np.testing.assert_array_equal(data["v0"], np.zeros_like(x0))

    def gradient(x):
        return a * x + b

    out.mkdir(parents=True, exist_ok=False)
    fig, (ax, events) = plt.subplots(
        2, 1, sharex=True, figsize=(7.2, 5.3), height_ratios=[4, 1], layout="constrained"
    )
    rules = ("kin", "mmd-r", "mmd-dr")
    with (out / "trace.csv").open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            ("rule", "iteration", "gradient_norm", "objective_gap", "restart", "gradient_calls")
        )
        for row, (rule, color) in enumerate(zip(rules, ("#264653", "#c05a12", "#6452a4"))):
            norms, resets = [], []
            for state in rcm(gradient, x0, h, 300, rule):
                error = state.x - optimum
                gap = 0.5 * np.dot(a * error, error)
                norms.append(state.gradient_norm)
                if state.restarted:
                    resets.append(state.iteration)
                writer.writerow(
                    (
                        rule,
                        state.iteration,
                        state.gradient_norm,
                        gap,
                        int(state.restarted),
                        state.gradient_calls,
                    )
                )
            ax.semilogy(range(len(norms)), norms, label="RCM-" + rule, color=color)
            events.scatter(resets, [row] * len(resets), marker="|", color=color, s=70)
            print(
                rule,
                "first resets",
                resets[:6],
                "total",
                len(resets),
                "final norm",
                norms[-1],
                "gap",
                gap,
                "gradient calls",
                state.gradient_calls,
            )
    ax.set_ylabel("Gradient norm")
    ax.legend()
    ax.grid(axis="y", alpha=0.2)
    events.set_yticks(range(3), rules)
    events.set_ylim(2.6, -0.6)
    events.set(xlabel="Iteration", ylabel="Restarts", xlim=(0, 300))
    fig.savefig(out / "rcm_seed605.pdf")
    plt.close(fig)
    print("Fixture SHA-256", hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    main()
