"""Frozen Candidate B and literal-call source-equivalent comparison methods.

Study-owned ports: external author code and canonical results are never changed.
Diagnostic mode adds measured work; minimal mode is the common timing boundary.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
CASES = {
    "exact": "fig1-left-19769000",
    "misspecified": "fig1-middle-19770301",
    "weak": "fig1-right-19772099",
    "logistic": "fig2-left-19768992",
}


@dataclass
class Problem:
    A: np.ndarray
    x0: np.ndarray
    b: np.ndarray | None = None
    alpha: float = 1e-4
    grad_calls: int = 0
    loss_calls: int = 0

    def loss(self, x):
        self.loss_calls += 1
        if self.b is None:
            return 0.5 * x @ self.A @ x
        exp_term = np.exp(-self.b * (self.A @ x))
        return np.mean(np.log(1 + exp_term)) + (self.alpha / 2) * np.linalg.norm(x) ** 2

    def grad(self, x):
        self.grad_calls += 1
        if self.b is None:
            return self.A @ x
        exp_term = np.exp(self.b * (self.A @ x))
        return -(self.A.T @ (self.b / (1 + exp_term))) / len(self.b) + self.alpha * x


def load_problem(case):
    path = ROOT / "results/reproduction" / CASES[case] / "figure-01-arrays.npz"
    with np.load(path) as z:
        p = Problem(z["A"], z["x0"], z["b"] if case == "logistic" else None)
    return p, path


def original_functions(case, p):
    """Unmodified author function ASTs, injected retained data (no data regeneration)."""
    source = ROOT / "results/reproduction" / CASES[case] / "original_cell.py"
    tree = ast.parse(source.read_text())
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
    ns = {
        "np": np,
        "A": p.A,
        "b": p.b,
        "dim": len(p.x0),
        "num_samples": len(p.b) if p.b is not None else 0,
        "lambda_reg": p.alpha,
    }
    exec(compile(tree, str(source), "exec"), ns)
    return ns


def boundary_rng(case, method, seed):
    """Reconstruct original configured-N algorithm boundary, including skipped draws."""
    rng = np.random.default_rng(seed)
    if case == "logistic":
        if method == "RHGD1":
            rng.random(1000)
        elif method == "CAGD":
            rng.random(2000)
    elif method.startswith("RHGD"):
        rng.exponential(scale=1.0, size=1000001)
    return rng


def reset_decision(power, armed, age, cap):
    if not np.isfinite(power):
        raise FloatingPointError("nonfinite power")
    event = armed and power >= 0
    capped = age >= cap
    return bool(event), bool(capped), bool(armed or power < 0)


def rhgd_step(p, x, y, h):
    """Return endpoint, pre-reset velocity, endpoint gradient, updated h, acceptance."""
    x_half = x + h * y
    x_trial = x_half - (h**2) * p.grad(x_half)
    accepted = True
    if p.b is not None:
        trial_loss = p.loss(x_trial)
        half_loss = p.loss(x_half)
        check_norm = np.linalg.norm(p.grad(x_half)) ** 2
        if not np.all(np.isfinite([trial_loss, half_loss, check_norm])):
            raise FloatingPointError("nonfinite logistic acceptance check")
        if trial_loss <= half_loss - (h**2 / 2) * check_norm:
            h = np.sqrt(1.1) * h
            x_new = x_trial
        else:
            h = np.sqrt(0.6) * h
            x_new = x
            accepted = False
    else:
        x_new = x_trial
    g_new = p.grad(x_new)
    v = y - h * g_new
    return x_new, v, g_new, h, accepted


def gradient_cost(case, method):
    if case == "logistic":
        return 2 if method == "AGD" else 3
    return 1 if method == "AGD" else 2


def run(p, case, method, budget, seed=0, cap=65536, diagnostic=False, max_states=20000):
    """No convergence stopping; stop before a complete update exceeds its gradient budget."""
    p.grad_calls = p.loss_calls = 0
    cost = gradient_cost(case, method)
    n = budget // cost
    mu = {"exact": 5e-5, "misspecified": 0.01, "weak": 0.0, "logistic": 1e-4}[case]
    adaptive = p.b is not None
    gamma = 1.0 if adaptive else 0.002
    h = np.sqrt(gamma)
    x = p.x0.copy()
    y = np.zeros_like(x) if method in ("B", "RHGD", "RHGD1", "RHGD2") else x.copy()
    z = x.copy()
    age, armed, t = 0, False, 1.0
    rng = boundary_rng(case, method, seed) if method != "B" else None
    # Reconstruction of the original boundary is setup, not optimizer work.
    rng_state = None if rng is None else rng.bit_generator.state
    start = perf_counter()
    if method == "CAGD":
        # Preserve the configured-N cumulative-sum arithmetic and draw count.
        T = np.cumsum(rng.exponential(scale=1.0, size=max(n + 1, 1001 if adaptive else 1000001)))
    f = np.empty(n + 1)
    elapsed = np.empty(n + 1)
    f[0] = p.loss(x)
    elapsed[0] = perf_counter() - start
    fields = [
        "power",
        "kinetic",
        "h_position",
        "h_velocity",
        "age",
        "event",
        "cap",
        "reset",
        "accepted",
        "segment_min",
        "delay",
        "grad_norm",
        "loss_calls",
    ]
    d = {k: np.full(n, np.nan) for k in fields} if diagnostic else {}
    states, velocities, endpoint_gradients, reset_states = [], [], [], []
    seg_min, min_age = f[0], 0
    segment_start = x.copy()
    completed, failure = 0, None
    for k in range(n):
        old_h = h
        event = capped = reset = False
        accepted = True
        g_new = v = None
        if method in ("B", "RHGD", "RHGD1", "RHGD2"):
            try:
                x_new, v, g_new, h, accepted = rhgd_step(p, x, y, h)
            except FloatingPointError as exc:
                failure = str(exc)
                break
            age += 1
            power = float(np.dot(g_new, v))
            if not np.isfinite(power):
                failure = "nonfinite power"
                break
            if method == "B":
                event, capped, armed = reset_decision(power, armed, age, cap)
                reset = event or capped
            else:
                prob = 17 / (2 * k + 18) if case == "weak" else np.sqrt(mu) * h
                if method == "RHGD2":
                    prob *= 2
                reset = rng.random() < prob
            y_new = np.zeros_like(y) if reset else v
        elif method == "AGD":
            x_old = x.copy()
            trial = y - gamma * p.grad(y)
            if adaptive:
                if p.loss(trial) <= p.loss(y) - (gamma / 2) * np.linalg.norm(p.grad(y)) ** 2:
                    gamma = 1.1 * gamma
                    x_new = trial
                else:
                    gamma = 0.6 * gamma
                    x_new = x_old
                    accepted = False
                kappa = 1 / (gamma * mu)
                theta = (np.sqrt(kappa) - 1) / (np.sqrt(kappa) + 1)
            elif case == "weak":
                x_new = trial
                t_new = (1 + np.sqrt(1 + 4 * t**2)) / 2
                theta = (t - 1) / t_new
                t = t_new
            else:
                x_new = trial
                theta = (1 - np.sqrt(mu * gamma)) / (1 + np.sqrt(mu * gamma))
            y_new = x_new + theta * (x_new - x_old)
        elif method == "CAGD":
            if case == "weak":
                tau = 1 - (T[k] / T[k + 1]) ** 2
                tau_prime = 0
                gamma_prime = T[k] * gamma / 2
            else:
                sqrt_mu_L = np.sqrt(mu * gamma)
                delta_t = T[k + 1] - T[k]
                tau = 0.5 * (1 - np.exp(-2 * sqrt_mu_L * delta_t))
                tau_prime = np.tanh(sqrt_mu_L * delta_t)
                gamma_prime = 1 / np.sqrt(mu / gamma)
            u = x + tau * (z - x)
            trial = u - gamma * p.grad(u)
            x_new = trial
            if adaptive:
                if p.loss(trial) <= p.loss(u) - (gamma / 2) * np.linalg.norm(p.grad(u)) ** 2:
                    gamma = 1.1 * gamma
                else:
                    gamma = 0.6 * gamma
                    x_new = x
                    accepted = False
                tau_prime = np.tanh(np.sqrt(mu * gamma) * delta_t)
                gamma_prime = np.sqrt(gamma) / np.sqrt(mu)
            z = z + tau_prime * (u - z) - gamma_prime * p.grad(u)
            y_new = y
        else:
            raise ValueError(method)
        new_f = p.loss(x_new)
        if not np.isfinite(new_f) or not np.all(np.isfinite(y_new)):
            failure = "nonfinite endpoint"
            break
        f[k + 1] = new_f
        if diagnostic:
            if new_f < seg_min:
                seg_min, min_age = new_f, age
            d["accepted"][k] = accepted
            d["loss_calls"][k] = p.loss_calls
            if g_new is not None:
                vals = [
                    power,
                    0.5 * np.dot(v, v),
                    old_h,
                    h,
                    age,
                    event,
                    capped,
                    reset,
                    accepted,
                    seg_min,
                    age - min_age,
                    np.linalg.norm(g_new),
                    p.loss_calls,
                ]
                for key, val in zip(fields, vals, strict=True):
                    d[key][k] = val
                if method == "B" and k < max_states:
                    states.append(x_new.copy())
                    velocities.append(v.copy())
                    endpoint_gradients.append(g_new.copy())
                if reset:
                    reset_states.append(np.concatenate(([k + 1], segment_start, x_new, v)))
        x, y = x_new, y_new
        completed = k + 1
        if reset:
            age, armed = 0, False
            seg_min, min_age = new_f, 0
            segment_start = x.copy()
        elapsed[k + 1] = perf_counter() - start
    result = {
        "f": f[: completed + 1],
        "elapsed": elapsed[: completed + 1],
        "gradients": np.arange(completed + 1) * cost,
        "x_final": x,
        **{k: a[:completed] for k, a in d.items()},
    }
    if diagnostic and method == "B":
        result.update(
            states=np.asarray(states),
            velocities=np.asarray(velocities),
            endpoint_gradients=np.asarray(endpoint_gradients),
        )
    if diagnostic:
        result["reset_states"] = np.asarray(reset_states)
    meta = {
        "method": method,
        "case": case,
        "seed": seed,
        "budget": budget,
        "completed_updates": completed,
        "gradient_calls": p.grad_calls,
        "objective_calls": p.loss_calls,
        "wall_seconds": perf_counter() - start,
        "rng_boundary": rng_state,
        "failure": failure,
        "status": "failure" if failure else "budget_complete",
    }
    return result, meta
