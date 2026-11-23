"""Course RHGD controls using the unchanged frozen position/velocity step."""

import operator
from time import perf_counter

import numpy as np

from power_reset_spectral_comparison.core import FROZEN_B, Oracle


def _integer(value, name, minimum):
    if isinstance(value, (bool, np.bool_)):
        raise ValueError(f"{name} must be an integer >= {minimum}")
    value = operator.index(value)
    if value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def run_fixed_time_quadratic(A, x0, *, h, period_steps, gradient_budget, keep_states=False):
    """Reset velocity after every period_steps full, constant-h RHGD updates.

    The physical reset interval is period_steps*h. The integer clock avoids
    floating-point threshold drift. Retain each new position, including an uphill
    endpoint; no power trigger, random draws, rollback, or additional cap applies.
    Start with zero velocity and preserve velocity in an unfinished final segment.

    Each attempted update pays for the half-step and endpoint gradients, even if
    their values coincide. Stop before an update would exceed gradient_budget;
    objectives are charged separately. Nonfinite trials fail and retain their
    spent work and raw failed state. There is no accuracy-based early stopping.

    f/gradients/flow_time include the initial point. reset/age refer to completed
    updates (index i means update i+1); age is measured before a scheduled reset.
    Optional x/velocity include the initial state; velocity is AFTER resetting.
    Callers select a suitable constant h; this function does not estimate L or
    symmetrize A. Full benchmarks require a suitable allocation.
    """
    period_steps = _integer(period_steps, "period_steps", 1)
    gradient_budget = _integer(gradient_budget, "gradient_budget", 0)
    if isinstance(h, (bool, np.bool_)) or np.ndim(h) != 0:
        raise ValueError("h must be a finite positive scalar")
    h = np.float64(h)
    with np.errstate(over="ignore", invalid="ignore"):
        period_time = float(period_steps * h)
    if not np.isfinite(h) or h <= 0 or not np.isfinite(period_time):
        raise ValueError("h and period_steps*h must be finite and positive")
    A, x0 = np.asarray(A, dtype=np.float64), np.asarray(x0, dtype=np.float64)
    if x0.ndim != 1 or x0.size == 0 or A.shape != (x0.size, x0.size):
        raise ValueError("A must be square and match the nonempty vector x0")
    if not np.all(np.isfinite(A)) or not np.all(np.isfinite(x0)):
        raise ValueError("A and x0 must be finite")

    oracle = Oracle(A)
    n = gradient_budget // 2
    x, velocity = x0.copy(), np.zeros_like(x0)
    f, elapsed = np.empty(n + 1), np.empty(n + 1)
    resets, ages = np.zeros(n, dtype=bool), np.empty(n, dtype=np.int64)
    positions = np.empty((n + 1, x.size)) if keep_states else None
    velocities = np.empty_like(positions) if keep_states else None
    pre_reset_velocities = np.empty((n, x.size)) if keep_states else None
    if keep_states:
        positions[0], velocities[0] = x, velocity
    start = perf_counter()
    with np.errstate(over="ignore", invalid="ignore"):
        f[0] = oracle.loss(x)
    elapsed[0] = perf_counter() - start
    completed = attempted = age = 0
    failure = None if np.isfinite(f[0]) else "nonfinite_initial_objective"
    failed_arrays = {}
    for k in range(n):
        if failure:
            break
        oracle.begin()
        attempted += 1
        with np.errstate(over="ignore", invalid="ignore"):
            x_new, v_pre, _, _, _ = FROZEN_B.rhgd_step(oracle, x, velocity, h)
            new_f = oracle.loss(x_new)
        # Check the pre-reset state too: deleting velocity cannot hide a failure.
        if not (np.isfinite(new_f) and np.all(np.isfinite(x_new)) and np.all(np.isfinite(v_pre))):
            failure = "nonfinite_endpoint_or_velocity_or_objective"
            failed_arrays = {
                "failed_x": x_new.copy(),
                "failed_velocity_pre_reset": v_pre.copy(),
                "failed_f": np.asarray(new_f),
            }
            break
        age += 1
        reset = age == period_steps
        x, velocity = x_new, np.zeros_like(v_pre) if reset else v_pre
        f[k + 1], resets[k], ages[k] = new_f, reset, age
        if keep_states:
            positions[k + 1], velocities[k + 1] = x, velocity
            pre_reset_velocities[k] = v_pre
        if reset:
            age = 0
        completed = k + 1
        elapsed[k + 1] = perf_counter() - start
    wall = perf_counter() - start
    gradients = 2 * np.arange(completed + 1, dtype=np.int64)
    arrays = {
        "f": f[: completed + 1],
        "elapsed": elapsed[: completed + 1],
        "gradients": gradients,
        "literal_gradients": gradients.copy(),
        "flow_time": h * np.arange(completed + 1),
        "reset": resets[:completed],
        "age": ages[:completed],
        "x_final": x,
        "aux_final": velocity,
        **failed_arrays,
    }
    if keep_states:
        arrays.update(
            x=positions[: completed + 1],
            velocity=velocities[: completed + 1],
            velocity_pre_reset=pre_reset_velocities[:completed],
        )
    metadata = {
        "method": "FIXED_TIME_RHGD",
        "h": float(h),
        "period_steps": period_steps,
        "period_time": period_time,
        "budget": gradient_budget,
        "updates": completed,
        "attempted_updates": attempted,
        "resets": int(np.count_nonzero(resets[:completed])),
        "final_segment_age": age,
        "numerical_gradients": oracle.numerical,
        "literal_gradient_requests": oracle.literal,
        "cache_hits": oracle.hits,
        "objectives": oracle.objectives,
        "objective_matrix_products": oracle.objectives,
        "objective_dots": oracle.objectives,
        "controller_dots": 0,
        "uniform_draws": 0,
        "exponential_draws": 0,
        "charged_unfinished_gradients": oracle.numerical - 2 * completed,
        "unused_gradient_budget": gradient_budget - oracle.numerical,
        "wall_seconds": wall,
        "timing_scope": "includes observations and requested state logging",
        "status": "failure" if failure else "budget_complete",
        "failure": failure,
    }
    return arrays, metadata
