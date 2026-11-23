"""Symplectic Euler with kinetic or mean-dissipation restart (arXiv:2009.11233v4)."""

from dataclasses import dataclass

import numpy as np


@dataclass
class RCMState:
    iteration: int
    x: np.ndarray
    v: np.ndarray
    gradient_norm: float
    restarted: bool
    segment_steps: int
    gradient_calls: int


def rcm(gradient, x0, h, steps, rule):
    """Yield accepted iterates, including iteration zero. Counts include diagnostics."""
    if rule not in ("kin", "mmd-r", "mmd-dr"):
        raise ValueError("Unknown restart rule")
    if not np.isfinite(h) or h <= 0 or not isinstance(steps, (int, np.integer)) or steps < 0:
        raise ValueError("Expected positive finite h and nonnegative integer steps")

    x = np.array(x0, dtype=np.float64, copy=True)
    if x.ndim != 1 or not x.size or not np.isfinite(x).all():
        raise ValueError("Expected a finite nonempty vector x0")
    calls = 0

    def evaluate(point):
        nonlocal calls
        if not np.isfinite(point).all():
            raise FloatingPointError("Nonfinite RCM position")
        calls += 1
        g = np.array(gradient(point), dtype=np.float64, copy=True)
        if g.shape != x.shape:
            raise ValueError("Gradient shape differs from x0")
        if not np.isfinite(g).all():
            raise FloatingPointError("Nonfinite RCM gradient")
        return g

    v = np.zeros_like(x)
    g = evaluate(x)
    age = 0
    restarted = False
    for iteration in range(steps + 1):
        norm = float(np.linalg.norm(g))
        if not np.isfinite(norm):
            raise FloatingPointError("Nonfinite gradient norm")
        yield RCMState(iteration, x.copy(), v.copy(), norm, bool(restarted), age, calls)
        if iteration == steps:
            return

        with np.errstate(over="raise", invalid="raise"):
            trial_v = v - h * g
            trial_x = x + h * trial_v
            trial_g = None
            restarted = False
            if age:
                speed_squared = trial_v @ trial_v
                if rule == "kin":
                    restarted = speed_squared < v @ v
                elif rule == "mmd-r":
                    restarted = speed_squared / (age + 1) < (v @ v) / age
                else:
                    trial_g = evaluate(trial_x)
                    restarted = speed_squared + 2 * (age + 1) * (trial_g @ trial_v) > 0

            if restarted:
                v = -h * g
                x = x + h * v
                g = evaluate(x)
                age = 1
            else:
                x, v = trial_x, trial_v
                g = evaluate(x) if trial_g is None else trial_g
                age += 1
