"""Accelerated gradient descent with restart, after O'Donoghue and Candes (2015).

This is a separate course implementation. The frozen historical recurrence
``power_reset_spectral_comparison.core.ar_step`` is not modified or replayed here.

Scheme (their Algorithm 1), from x_0, y_0 = x_0, theta_0 = 1 and q in [0, 1]:

    x_k       = y_{k-1} - eta * grad f(y_{k-1})
    theta_k   solves theta_k^2 = (1 - theta_k) * theta_{k-1}^2 + q * theta_k
    beta_k    = theta_{k-1} * (1 - theta_{k-1}) / (theta_{k-1}^2 + theta_k)
    y_k       = x_k + beta_k * (x_k - x_{k-1})

q = 0 is the mu-free scheme, q = mu / L the strongly convex one, q = 1 plain
gradient descent.

Restart rules, each checked once per update after x_k is formed:

    "function"  f(x_k) > f(x_{k-1})
    "gradient"  grad f(y_{k-1})^T (x_k - x_{k-1}) > 0
    "fixed"     every ``interval`` updates since the start or the last restart
    "none"      never

Conventions this implementation fixes (the paper gives no pseudocode for the
adaptive rules, so these are our declared reading of its fixed-restart scheme):

* Both inequalities are strict; equality does not restart.
* The new endpoint x_k is retained, also when f(x_k) > f(x_{k-1}). The function
  rule is therefore not a monotone safeguard.
* A restart sets y_k = x_k and theta_k = 1. Then beta_{k+1} = 0, so the update
  after a restart is a plain gradient step from x_k.
* Cost: one gradient per update for every rule. The function rule also needs
  f(x_k) at every update, which is charged as a controller objective. The
  gradient rule needs one extra dot product and no objective. This runner
  evaluates f(x_k) for every rule to record the trace; for the other rules that
  evaluation is a diagnostic and is reported separately.
"""

from time import perf_counter

import numpy as np

RESTARTS = ("none", "fixed", "function", "gradient")


class CountingOracle:
    """Counts every real objective and gradient evaluation. Nothing is cached."""

    def __init__(self, objective, gradient):
        self._objective = objective
        self._gradient = gradient
        self.gradients = 0
        self.objectives = 0

    def grad(self, x):
        self.gradients += 1
        return self._gradient(x)

    def loss(self, x):
        self.objectives += 1
        return float(self._objective(x))


def quadratic_oracle(A):
    """f(x) = 0.5 * x^T A x with gradient A x, as in the shared quadratic fixtures."""
    return CountingOracle(lambda x: 0.5 * x @ A @ x, lambda x: A @ x)


def logistic_oracle(A, b, reg):
    """mean(logaddexp(0, -b * (A x))) + (reg / 2) * ||x||^2 with labels b in {-1, +1}."""

    def objective(x):
        return np.mean(np.logaddexp(0.0, -b * (A @ x))) + 0.5 * reg * (x @ x)

    def gradient(x):
        margin = b * (A @ x)
        # sigmoid(-margin) written through logaddexp so large margins do not overflow.
        weight = np.exp(-np.logaddexp(0.0, margin))
        return -(A.T @ (b * weight)) / len(b) + reg * x

    return CountingOracle(objective, gradient)


def next_theta(theta, q):
    """Positive root of t^2 + (theta^2 - q) * t - theta^2 = 0."""
    c = theta * theta - q
    return 0.5 * (-c + np.sqrt(c * c + 4.0 * theta * theta))


def momentum(theta, theta_next):
    return theta * (1.0 - theta) / (theta * theta + theta_next)


def run_agd(
    oracle,
    x0,
    eta,
    iterations,
    q=0.0,
    restart="none",
    interval=None,
    keep_states=False,
):
    """Run a fixed number of updates. No accuracy stopping.

    A nonfinite endpoint, objective or restart statistic stops the run with
    status "failure"; the partial trace and all work already paid are returned.
    """
    if restart not in RESTARTS:
        raise ValueError(f"restart must be one of {RESTARTS}, got {restart!r}")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"q must lie in [0, 1], got {q}")
    if eta <= 0:
        raise ValueError(f"eta must be positive, got {eta}")
    if restart == "fixed":
        if interval is None or int(interval) != interval or interval < 1:
            raise ValueError("fixed restart needs a positive integer interval")
        interval = int(interval)
    elif interval is not None:
        raise ValueError("interval is only used by the fixed restart rule")

    n = int(iterations)
    start = perf_counter()
    x = np.array(x0, dtype=np.float64)
    y = x.copy()
    theta = 1.0
    age = 0
    f = np.empty(n + 1)
    f[0] = oracle.loss(x)
    fired = np.zeros(n, dtype=bool)
    statistic = np.full(n, np.nan)
    states = None
    if keep_states:
        states = {"x": np.empty((n + 1, len(x))), "y": np.empty((n + 1, len(x)))}
        states["x"][0] = x
        states["y"][0] = y
    completed, failure = 0, None
    controller_dots = 0

    for k in range(n):
        g = oracle.grad(y)
        x_new = y - eta * g
        f_new = oracle.loss(x_new)
        age += 1
        if restart == "gradient":
            stat = float(g @ (x_new - x))
            controller_dots += 1
            fire = stat > 0.0
        elif restart == "function":
            stat = f_new - f[k]
            fire = f_new > f[k]
        elif restart == "fixed":
            stat = float(age)
            fire = age == interval
        else:
            stat = 0.0
            fire = False
        if not (np.isfinite(f_new) and np.isfinite(stat) and np.all(np.isfinite(x_new))):
            failure = "nonfinite endpoint, objective or restart statistic"
            break
        if fire:
            theta = 1.0
            y = x_new.copy()
            age = 0
        else:
            theta_new = next_theta(theta, q)
            y = x_new + momentum(theta, theta_new) * (x_new - x)
            theta = theta_new
        x = x_new
        f[k + 1] = f_new
        fired[k] = fire
        statistic[k] = stat
        if states is not None:
            states["x"][k + 1] = x
            states["y"][k + 1] = y
        completed = k + 1
    wall = perf_counter() - start

    arrays = {
        "f": f[: completed + 1],
        "gradients": np.arange(completed + 1, dtype=np.int64),
        "restart": fired[:completed],
        "statistic": statistic[:completed],
        "x_final": x,
        "y_final": y,
    }
    if states is not None:
        arrays["x"] = states["x"][: completed + 1]
        arrays["y"] = states["y"][: completed + 1]
    function_rule = restart == "function"
    metadata = {
        "restart": restart,
        "interval": interval,
        "q": float(q),
        "eta": float(eta),
        "iterations_requested": n,
        "updates": completed,
        "gradients": oracle.gradients,
        "objectives": oracle.objectives,
        # f(x_k) per attempted update is controller work only for the function rule.
        "controller_objectives": oracle.objectives - 1 if function_rule else 0,
        "diagnostic_objectives": 1 if function_rule else oracle.objectives,
        "controller_dots": controller_dots,
        "restarts": int(fired[:completed].sum()),
        "charged_unfinished_gradients": oracle.gradients - completed,
        "wall_seconds": wall,
        "wall_note": "includes the per-update objective evaluation for every rule",
        "status": "failure" if failure else "budget_complete",
        "failure": failure,
    }
    return arrays, metadata
