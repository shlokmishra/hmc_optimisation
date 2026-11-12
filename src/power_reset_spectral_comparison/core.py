"""Uniform-cost adapters. Frozen B functions are imported from byte-pinned source."""

import importlib.util
import json
import sys
from pathlib import Path
from time import perf_counter

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "configs/studies/power_reset_spectral_comparison.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
B_PATH = ROOT / CONFIG["B_source"]
_spec = importlib.util.spec_from_file_location("frozen_power_reset_study_b", B_PATH)
FROZEN_B = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = FROZEN_B
exec(compile(B_PATH.read_bytes(), str(B_PATH), "exec"), FROZEN_B.__dict__)


class Oracle:
    """Same per-update immutable-argument cache for every recurrence."""

    def __init__(self, A, cached=True):
        self.A = A
        self.b = None  # Frozen B's quadratic branch.
        self.cached = cached
        self.numerical = self.literal = self.objectives = self.hits = 0
        self.cache = {}

    def begin(self):
        self.cache.clear()

    def grad(self, x):
        self.literal += 1
        key = id(x)
        if self.cached and key in self.cache:
            saved_x, saved_g = self.cache[key]
            assert saved_x is x
            self.hits += 1
            return saved_g
        g = self.A @ x
        self.numerical += 1
        if self.cached:
            self.cache[key] = (x, g)
        return g

    def loss(self, x):
        self.objectives += 1
        return 0.5 * x @ self.A @ x


def ar_step(oracle, x, u, t, eta):
    """The exact user-specified alpha-free convex recurrence and strict restart."""
    g = oracle.grad(u)
    x_plus = u - eta * g
    t_plus = (1 + np.sqrt(1 + 4 * t * t)) / 2
    power = float(np.dot(g, x_plus - x))
    reset = power > 0
    if reset:
        t_plus = 1.0
        u_plus = x_plus
    else:
        u_plus = x_plus + ((t - 1) / t_plus) * (x_plus - x)
    return x_plus, u_plus, t_plus, reset, power


def steps_for(method, budget, cached=True):
    cost = CONFIG["primary_gradients_per_update" if cached else "literal_gradients_per_update"][
        method
    ]
    return budget // cost


def run(
    A,
    x0,
    method,
    budget=200000,
    seed=None,
    cached=True,
    detailed=False,
    basis=None,
    eigenvalues=None,
    keep_states=False,
    max_updates=None,
):
    """Full-budget path. No accuracy stopping; failure returns partial charged evidence."""
    if method not in CONFIG["methods"]:
        raise ValueError(method)
    if method in ("CAGD", "RHGD") and seed is None:
        raise ValueError("Randomized methods require an explicit seed")
    oracle = Oracle(A, cached)
    rng = np.random.default_rng(seed) if seed is not None else None
    n = steps_for(method, budget, cached)
    if max_updates is not None:
        n = min(n, max_updates)
    eta, mu = CONFIG["eta"], CONFIG["alpha"]
    h = np.sqrt(eta)
    start = perf_counter()
    x = x0.copy()
    u = x0.copy()
    z = x0.copy()
    y = np.zeros_like(x)
    t = 1.0
    age, armed = 0, False
    if method == "CAGD":
        T = np.cumsum(rng.exponential(scale=1.0, size=n + 1))
    f, elapsed = np.empty(n + 1), np.empty(n + 1)
    f[0] = oracle.loss(x)
    elapsed[0] = perf_counter() - start
    x_trace = np.empty((n + 1, len(x))) if detailed and (method == "B" or keep_states) else None
    if x_trace is not None:
        x_trace[0] = x
    detail = {}
    if detailed:
        detail = {
            k: np.zeros(n)
            for k in (
                "power",
                "kinetic",
                "age",
                "reset",
                "event",
                "cap",
                "segment_min",
                "delay",
                "grad_norm",
            )
        }
        detail["slow_loss"] = np.empty(n + 1)
        detail["slow_loss"][0] = 0.5 * eigenvalues[0] * float(basis[:, 0] @ x) ** 2
        if method == "B":
            detail["velocity_pre_reset"] = np.empty((n, len(x)))
            detail["endpoint_gradient"] = np.empty((n, len(x)))
    minimum, minimum_age = f[0], 0
    completed, failure = 0, None
    reset_dots = 0
    uniforms = 0
    for k in range(n):
        oracle.begin()
        event = capped = reset = False
        P = np.nan
        g = v = None
        if method in ("B", "RHGD"):
            x_plus, v, g, h, _ = FROZEN_B.rhgd_step(oracle, x, y, h)
            age += 1
            if method == "B":
                P = float(np.dot(g, v))
                reset_dots += 1
                if not np.isfinite(P):
                    failure = "nonfinite power"
                    break
                event, capped, armed = FROZEN_B.reset_decision(P, armed, age, CONFIG["B_cap"])
                reset = event or capped
            else:
                reset = rng.random() < np.sqrt(mu) * h
                uniforms += 1
            y_plus = np.zeros_like(y) if reset else v
        elif method == "AR_AGD":
            x_plus, u_plus, t_plus, reset, P = ar_step(oracle, x, u, t, eta)
            reset_dots += 1
            if not np.isfinite(P):
                failure = "nonfinite restart dot"
                break
            u, t = u_plus, t_plus
            y_plus = y
        elif method == "AGD":
            x_old = x.copy()
            x_plus = u - eta * oracle.grad(u)
            theta = (1 - np.sqrt(mu * eta)) / (1 + np.sqrt(mu * eta))
            u = x_plus + theta * (x_plus - x_old)
            y_plus = y
        else:
            sqrt_mu_L = np.sqrt(mu * eta)
            delta_t = T[k + 1] - T[k]
            tau = 0.5 * (1 - np.exp(-2 * sqrt_mu_L * delta_t))
            tau_prime = np.tanh(sqrt_mu_L * delta_t)
            gamma_prime = 1 / np.sqrt(mu / eta)
            q = x + tau * (z - x)
            x_plus = q - eta * oracle.grad(q)
            z = z + tau_prime * (q - z) - gamma_prime * oracle.grad(q)
            y_plus = y
        new_f = oracle.loss(x_plus)
        aux = y_plus if method in ("B", "RHGD") else (z if method == "CAGD" else u)
        if not np.isfinite(new_f) or not np.all(np.isfinite(aux)):
            failure = "nonfinite endpoint or auxiliary state"
            break
        f[k + 1] = new_f
        if detailed:
            if method in ("B", "RHGD"):
                if new_f < minimum:
                    minimum, minimum_age = new_f, age
                if method == "RHGD":
                    P = float(np.dot(g, v))  # Diagnostic only; absent in minimal timing.
                vals = [
                    P,
                    0.5 * np.dot(v, v),
                    age,
                    reset,
                    event,
                    capped,
                    minimum,
                    age - minimum_age,
                    np.linalg.norm(g),
                ]
                for key, val in zip(
                    (
                        "power",
                        "kinetic",
                        "age",
                        "reset",
                        "event",
                        "cap",
                        "segment_min",
                        "delay",
                        "grad_norm",
                    ),
                    vals,
                    strict=True,
                ):
                    detail[key][k] = val
                if method == "B":
                    detail["velocity_pre_reset"][k] = v
                    detail["endpoint_gradient"][k] = g
            elif method == "AR_AGD":
                detail["power"][k], detail["reset"][k] = P, reset
            detail["slow_loss"][k + 1] = 0.5 * eigenvalues[0] * float(basis[:, 0] @ x_plus) ** 2
            if x_trace is not None:
                x_trace[k + 1] = x_plus
        x, y = x_plus, y_plus
        completed = k + 1
        if reset and method in ("B", "RHGD"):
            age, armed = 0, False
            minimum, minimum_age = new_f, 0
        elapsed[k + 1] = perf_counter() - start
    wall = perf_counter() - start
    cost = CONFIG["primary_gradients_per_update" if cached else "literal_gradients_per_update"][
        method
    ]
    arrays = {
        "f": f[: completed + 1],
        "elapsed": elapsed[: completed + 1],
        "gradients": np.arange(completed + 1, dtype=np.int64) * cost,
        "literal_gradients": np.arange(completed + 1, dtype=np.int64)
        * CONFIG["literal_gradients_per_update"][method],
        "x_final": x,
        "aux_final": y if method in ("B", "RHGD") else (z if method == "CAGD" else u),
    }
    if detailed:
        arrays.update(
            {
                key: value[: completed + 1 if key == "slow_loss" else completed]
                for key, value in detail.items()
            }
        )
    if x_trace is not None:
        arrays["x"] = x_trace[: completed + 1]
    metadata = {
        "method": method,
        "seed": seed,
        "cached": cached,
        "budget": budget,
        "updates": completed,
        "numerical_gradients": oracle.numerical,
        "literal_gradient_requests": oracle.literal,
        "cache_hits": oracle.hits,
        "objectives": oracle.objectives,
        "objective_matrix_products": oracle.objectives,
        "objective_dots": oracle.objectives,
        "controller_dots": reset_dots,
        "uniform_draws": uniforms,
        "exponential_draws": n + 1 if method == "CAGD" else 0,
        "scalar_decisions_per_update": {
            "B": "power sign, arming, cap",
            "AR_AGD": "sqrt and strict gradient-displacement sign",
            "AGD": "sqrt-based fixed momentum coefficient",
            "CAGD": "sqrt, exp, tanh and clock difference",
            "RHGD": "sqrt(alpha)*h and Bernoulli draw",
        }[method],
        "diagnostic_slow_dots": completed + 1 if detailed else 0,
        "diagnostic_kinetic_dots": completed if detailed and method in ("B", "RHGD") else 0,
        "diagnostic_gradient_norms": completed if detailed and method in ("B", "RHGD") else 0,
        "diagnostic_power_dots": completed if detailed and method == "RHGD" else 0,
        "wall_seconds": wall,
        "status": "failure" if failure else "budget_complete",
        "failure": failure,
        "charged_unfinished_gradients": oracle.numerical - completed * cost,
    }
    return arrays, metadata
