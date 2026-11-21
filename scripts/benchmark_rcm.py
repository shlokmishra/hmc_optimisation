"""Run RCM on the course's shared quadratic fixtures with a hard gradient budget."""

import argparse
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from stat605.rcm import rcm  # noqa: E402


class BudgetReached(Exception):
    pass


def run_case(matrix, start, h, rule, budget, trace, problem):
    calls = objectives = resets = 0
    last = None
    status = "budget_reached"
    reason = ""

    def gradient(x):
        nonlocal calls
        if calls == budget:
            raise BudgetReached
        calls += 1
        return matrix @ x

    try:
        for state in rcm(gradient, start, h, budget, rule):
            objectives += 1
            loss = 0.5 * (state.x @ (matrix @ state.x))
            if not np.isfinite(loss):
                raise FloatingPointError("Nonfinite objective")
            resets += int(state.restarted)
            last = (state.iteration, state.gradient_calls, float(loss))
            trace.writerow(
                (
                    problem,
                    rule,
                    state.iteration,
                    state.gradient_calls,
                    calls,
                    objectives,
                    loss,
                    state.gradient_norm,
                    int(state.restarted),
                )
            )
            if calls == budget:
                break
    except BudgetReached:
        pass  # The final call may have gone to a rejected trial point.
    except FloatingPointError as error:
        status, reason = "failed", str(error)
    return dict(
        problem=problem,
        rule=rule,
        status=status,
        reason=reason,
        gradient_budget=budget,
        gradients_spent=calls,
        objectives=objectives,
        last_iteration=last[0] if last else None,
        gradients_at_last_iterate=last[1] if last else None,
        final_gap=last[2] if last else None,
        restarts=resets,
        h=h,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gradient-budget", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.gradient_budget < 1:
        parser.error("gradient budget must be positive")
    args.output.mkdir(parents=True, exist_ok=False)
    fixtures = ROOT / "configs/stat605/fixtures"
    provenance = json.loads((fixtures / "PROVENANCE.json").read_text())
    metadata = {entry["file"]: entry for entry in provenance["fixtures"]}
    summary = []
    with (args.output / "trace.csv").open("w", newline="") as handle:
        trace = csv.writer(handle)
        trace.writerow(
            (
                "problem",
                "rule",
                "iteration",
                "actual_gradients",
                "literal_gradient_calls",
                "objective_calls",
                "current_loss",
                "gradient_norm",
                "restart",
            )
        )
        for problem, name in (("linear", "quadratic_paper.npz"), ("log", "quadratic_log.npz")):
            path = fixtures / name
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != metadata[name]["sha256"]:
                raise ValueError(f"Fixture hash mismatch: {name}")
            with np.load(path, allow_pickle=False) as data:
                matrix, start = data["A"], data["x0"]
            h = 1 / np.sqrt(metadata[name]["settings"]["L"])
            for rule in ("kin", "mmd-r", "mmd-dr"):
                row = run_case(matrix, start, h, rule, args.gradient_budget, trace, problem)
                row.update(
                    fixture=name,
                    fixture_sha256=digest,
                    rcm_sha256=hashlib.sha256(
                        (ROOT / "src/stat605/rcm.py").read_bytes()
                    ).hexdigest(),
                )
                summary.append(row)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    for row in summary:
        print(row["problem"], row["rule"], row["status"], row["final_gap"])


if __name__ == "__main__":
    main()
