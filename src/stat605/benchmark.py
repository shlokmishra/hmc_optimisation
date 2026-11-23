"""Equal-gradient-budget comparisons of the course quadratic methods."""

from collections.abc import Callable
from dataclasses import dataclass
from time import perf_counter

import numpy as np

from power_reset_spectral_comparison.analysis import crossings
from power_reset_spectral_comparison.core import FROZEN_B, Oracle, ar_step


class BenchmarkOracle(Oracle):
    """Historical per-update gradient cache, plus controller work counters."""

    def __init__(self, matrix):
        super().__init__(matrix, cached=True)
        self.controller_dots = 0
        self.uniform_draws = 0
        self.exponential_draws = 0


@dataclass(frozen=True)
class Settings:
    eta: float
    supplied_mu: float | None
    cap: int
    seed: int | None
    updates: int


@dataclass
class Step:
    """One attempted update. Arrays from earlier steps must remain immutable."""

    x: np.ndarray
    auxiliary: np.ndarray
    reset: bool = False
    accepted: bool = True
    event: bool = False
    capped: bool = False
    power: float | None = None
    gradient: np.ndarray | None = None
    velocity: np.ndarray | None = None


@dataclass(frozen=True)
class Method:
    """Adapter for a fixed-gradient-cost quadratic update.

    prepare(oracle, x0, settings) returns step(x, zero_based_iteration). All
    optimizer gradient and objective evaluations must go through the oracle.
    The cost is the number of uncached gradients per complete update.
    """

    name: str
    prepare: Callable[[BenchmarkOracle, np.ndarray, Settings], Callable[[np.ndarray, int], Step]]
    gradient_cost: int
    uses_mu: bool = False
    randomized: bool = False


def _agd(oracle, x0, settings):
    u = x0.copy()
    q = np.sqrt(settings.supplied_mu * settings.eta)
    theta = (1 - q) / (1 + q)

    def step(x, k):
        nonlocal u
        x_new = u - settings.eta * oracle.grad(u)
        u = x_new + theta * (x_new - x)
        return Step(x_new, u)

    return step


def _restart_agd(oracle, x0, settings):
    u, t = x0.copy(), 1.0

    def step(x, k):
        nonlocal u, t
        oracle.controller_dots += 1
        x_new, u, t, reset, power = ar_step(oracle, x, u, t, settings.eta)
        if not np.isfinite(power):
            raise FloatingPointError("nonfinite restart dot")
        return Step(x_new, u, reset=reset)

    return step


def _cagd(oracle, x0, settings):
    z = x0.copy()
    rng = np.random.default_rng(settings.seed)
    # The retained spectral runner differences a cumulative exponential clock.
    # Direct exponential increments would change its floating-point trajectory.
    times = np.cumsum(rng.exponential(scale=1.0, size=settings.updates + 1))
    oracle.exponential_draws += len(times)
    q = np.sqrt(settings.supplied_mu * settings.eta)
    gamma_prime = 1 / np.sqrt(settings.supplied_mu / settings.eta)

    def step(x, k):
        nonlocal z
        delta = times[k + 1] - times[k]
        tau = 0.5 * (1 - np.exp(-2 * q * delta))
        tau_prime = np.tanh(q * delta)
        u = x + tau * (z - x)
        x_new = u - settings.eta * oracle.grad(u)
        z = z + tau_prime * (u - z) - gamma_prime * oracle.grad(u)
        return Step(x_new, z)

    return step


def _hamiltonian(oracle, x0, settings, power_reset):
    y = np.zeros_like(x0)
    h = np.sqrt(settings.eta)
    age, armed = 0, False
    if not power_reset:
        rng = np.random.default_rng(settings.seed)
        probability = np.sqrt(settings.supplied_mu) * h

    def step(x, k):
        nonlocal y, age, armed
        x_new, velocity, gradient, _, accepted = FROZEN_B.rhgd_step(oracle, x, y, h)
        event = capped = False
        power = None
        if power_reset:
            age += 1
            oracle.controller_dots += 1
            power = float(np.dot(gradient, velocity))
            event, capped, armed = FROZEN_B.reset_decision(power, armed, age, settings.cap)
            reset = event or capped
            if reset:
                age, armed = 0, False
        else:
            reset = rng.random() < probability
            oracle.uniform_draws += 1
        y = np.zeros_like(y) if reset else velocity
        return Step(
            x_new,
            y,
            reset=reset,
            accepted=accepted,
            event=event,
            capped=capped,
            power=power,
            gradient=gradient,
            velocity=velocity,
        )

    return step


def _rhgd(oracle, x0, settings):
    return _hamiltonian(oracle, x0, settings, power_reset=False)


def _power_reset(oracle, x0, settings):
    return _hamiltonian(oracle, x0, settings, power_reset=True)


METHODS = {
    method.name: method
    for method in (
        Method("AGD", _agd, 1, uses_mu=True),
        Method("AR_AGD", _restart_agd, 1),
        Method("CAGD", _cagd, 1, uses_mu=True, randomized=True),
        Method("RHGD", _rhgd, 2, uses_mu=True, randomized=True),
        Method("B", _power_reset, 2),
    )
}
RANDOMIZED_METHODS = frozenset(method.name for method in METHODS.values() if method.randomized)


def _integer(value, minimum=0):
    return isinstance(value, (int, np.integer)) and not isinstance(value, bool) and value >= minimum


def _crossing_records(targets, trace, successful):
    records = []
    for target in targets:
        result = {"target": float(target)}
        for kind, k in crossings(trace["loss"], target, successful).items():
            result[kind] = (
                None if k is None else {"iteration": k, "gradients": int(trace["gradients"][k])}
            )
        records.append(result)
    return records


def run_benchmark(
    problem,
    method,
    *,
    gradient_budget,
    eta,
    supplied_mu,
    cap=65536,
    seed=None,
    targets=(),
    diagnostic_steps=0,
):
    """Run complete updates within the paid-gradient budget and retain failures.

    Accept a built-in name or a Method adapter. The trace starts at iteration 0
    and includes each completed update, including any rejected by its controller.
    The signed quadratic gap is the current objective (the minimizer is zero).
    Metadata also charges any attempted work after the last completed update.
    Optimizer time includes method initialization, RNG, cache clearing, controller
    checks and updates. Endpoint loss, health checks and spectral projections are
    separately timed diagnostics. Trace allocation and bookkeeping are excluded
    from optimizer time. Sustained means through the end of a complete run.
    """
    start = perf_counter()
    if isinstance(method, str):
        if method not in METHODS:
            raise ValueError(f"unknown method {method!r}")
        method = METHODS[method]
    if not _integer(gradient_budget) or not _integer(method.gradient_cost, 1):
        raise ValueError(
            "gradient_budget must be nonnegative and method gradient_cost positive integers"
        )
    if not _integer(diagnostic_steps) or not _integer(cap, 1):
        raise ValueError(
            "diagnostic_steps must be a nonnegative integer and cap a positive integer"
        )
    if not np.isfinite(eta) or eta <= 0:
        raise ValueError("eta must be positive and finite")
    if method.uses_mu and (supplied_mu is None or not np.isfinite(supplied_mu) or supplied_mu <= 0):
        raise ValueError("this method requires positive finite supplied_mu")
    if method.randomized and not _integer(seed):
        raise ValueError("randomized methods require an explicit nonnegative integer seed")
    if not method.randomized and seed is not None:
        raise ValueError("deterministic methods take seed=None")
    targets = tuple(targets)
    if any(not np.isfinite(target) or target <= 0 for target in targets):
        raise ValueError("targets must be positive finite objective gaps")

    oracle = BenchmarkOracle(problem.A)
    x = problem.x0.copy()
    if x.dtype != np.float64 or problem.A.dtype != np.float64:
        raise ValueError("benchmarks require float64 inputs")
    updates = gradient_budget // method.gradient_cost
    settings = Settings(eta, supplied_mu if method.uses_mu else None, cap, seed, updates)
    trace = {
        key: np.zeros(updates + 1, dtype=np.int64)
        for key in ("gradients", "literal_gradients", "objectives")
    }
    for key in ("reset", "accepted", "event", "cap"):
        trace[key] = np.zeros(updates + 1, dtype=bool)
    trace["loss"] = np.empty(updates + 1)
    trace["optimizer_seconds"] = np.empty(updates + 1)
    samples = min(diagnostic_steps, updates) if method.name == "B" else 0
    modal_power = np.empty((samples, len(x)))
    global_power = np.empty(samples)
    completed = attempted = reported_objectives = 0
    failure = None
    setup_seconds = perf_counter() - start

    tick = perf_counter()
    step = method.prepare(oracle, x, settings)
    optimizer_seconds = perf_counter() - tick
    trace["optimizer_seconds"][0] = optimizer_seconds
    tick = perf_counter()
    with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
        trace["loss"][0] = oracle.loss(x)
        reported_objectives += 1
        trace["objectives"][0] = oracle.objectives
        if not np.isfinite(trace["loss"][0]):
            failure = "nonfinite initial objective"
        diagnostic_seconds = perf_counter() - tick
        for k in range(updates):
            if failure is not None:
                break
            attempted += 1
            tick = perf_counter()
            oracle.begin()
            try:
                result = step(x, k)
            except FloatingPointError as exc:
                failure = str(exc)
                break
            finally:
                optimizer_seconds += perf_counter() - tick

            tick = perf_counter()
            loss = oracle.loss(result.x)
            reported_objectives += 1
            if not (np.isfinite(loss) and np.isfinite(result.auxiliary).all()):
                failure = "nonfinite endpoint or auxiliary state"
            if result.velocity is not None and not np.isfinite(result.velocity).all():
                failure = "nonfinite proposed velocity"
            if failure is None and k < samples:
                modal_power[k] = problem.modal_power(result.gradient, result.velocity)
                global_power[k] = result.power
            diagnostic_seconds += perf_counter() - tick
            if failure is not None:
                break
            if oracle.numerical - trace["gradients"][k] != method.gradient_cost:
                raise RuntimeError(
                    f"{method.name} adapter used a different gradient cost than declared"
                )
            completed = k + 1
            x = result.x
            trace["loss"][completed] = loss
            trace["optimizer_seconds"][completed] = optimizer_seconds
            trace["gradients"][completed] = oracle.numerical
            trace["literal_gradients"][completed] = oracle.literal
            trace["objectives"][completed] = oracle.objectives
            trace["reset"][completed] = result.reset
            trace["accepted"][completed] = result.accepted
            trace["event"][completed] = result.event
            trace["cap"][completed] = result.capped

    trace = {name: array[: completed + 1] for name, array in trace.items()}
    trace["iteration"] = np.arange(completed + 1, dtype=np.int64)
    trace["best_loss"] = np.minimum.accumulate(trace["loss"])
    trace["x_final"] = x
    sampled = min(completed, samples)
    trace["power_iteration"] = np.arange(1, sampled + 1, dtype=np.int64)
    trace["modal_power"] = modal_power[:sampled]
    trace["global_power"] = global_power[:sampled]
    record = {
        "method": method.name,
        "seed": seed,
        "settings": {
            "eta": eta,
            "supplied_mu": settings.supplied_mu,
            "h": float(np.sqrt(eta)) if method.name in ("B", "RHGD") else None,
            "cap": cap if method.name == "B" else None,
            "gradients_per_update": method.gradient_cost,
            "cache": "within-update immutable argument identity",
        },
        "gradient_budget": gradient_budget,
        "status": "failure" if failure else "budget_complete",
        "failure": failure,
        "updates": completed,
        "attempted_updates": attempted,
        "rejected_updates": int(np.count_nonzero(~trace["accepted"][1:])),
        "numerical_gradients": oracle.numerical,
        "literal_gradient_requests": oracle.literal,
        "cache_hits": oracle.hits,
        "objectives": oracle.objectives,
        "diagnostic_objectives": reported_objectives,
        "charged_unfinished_gradients": oracle.numerical - int(trace["gradients"][-1]),
        "charged_unfinished_objectives": oracle.objectives - int(trace["objectives"][-1]),
        "controller_dots": oracle.controller_dots,
        "uniform_draws": oracle.uniform_draws,
        "exponential_draws": oracle.exponential_draws,
        "reset_count": int(np.count_nonzero(trace["reset"])),
        "crossings": _crossing_records(targets, trace, failure is None),
        "setup_seconds": setup_seconds,
        "optimizer_seconds": optimizer_seconds,
        "diagnostic_seconds": diagnostic_seconds,
        "wall_seconds": perf_counter() - start,
    }
    return trace, record
