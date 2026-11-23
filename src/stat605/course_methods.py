"""Separate course controllers; no edits to frozen RHGD or contributed APIs."""

from functools import partial

import numpy as np

from power_reset_spectral_comparison.core import FROZEN_B
from stat605.agd import momentum, next_theta


class NormalizedReset:
    """Segment-local normalized signals, with strict arming and decrease rules."""

    def __init__(self, family, beta, cap):
        if family not in ("endpoint", "kinetic") or not np.isfinite(beta) or beta < 0:
            raise ValueError("invalid normalization family or beta")
        self.family, self.beta, self.cap = family, beta, cap
        self.age, self.armed, self.previous = 0, False, None

    def observe(self, power, kinetic, h):
        if not np.isfinite([power, kinetic]).all():
            raise FloatingPointError("nonfinite normalization statistic")
        self.age += 1
        if self.family == "endpoint":
            # beta=0 follows the frozen sign test exactly, without t*P underflow.
            signal = power if self.beta == 0 else self.age * h * power + self.beta * kinetic
            event = self.armed and signal >= 0
            self.armed |= signal < 0
        else:
            signal = kinetic / (self.age * h) ** self.beta
            event = self.armed and self.previous is not None and signal < self.previous
            self.armed |= signal > 0
            self.previous = signal
        if not np.isfinite(signal):
            raise FloatingPointError("nonfinite normalized signal")
        capped, age = self.age >= self.cap, self.age
        if event or capped:
            self.age, self.armed, self.previous = 0, False, None
        return bool(event), bool(capped), float(signal), age


def _gd(oracle, x0, settings):
    from stat605.benchmark import Step

    def step(x, k):
        y = x - settings.eta * oracle.grad(x)
        return Step(y, y)

    return step


def _agd(oracle, x0, settings, rule):
    from stat605.benchmark import Step

    y, theta = x0.copy(), 1.0
    previous = oracle.controller_loss(x0) if rule == "function" else None
    if rule == "function":
        oracle.initial_loss = previous

    def step(x, k):
        nonlocal y, theta, previous
        g = oracle.grad(y)
        new = y - settings.eta * g
        loss = oracle.controller_loss(new) if rule == "function" else None
        if rule == "function":
            fire = loss > previous
            previous = loss
        elif rule == "gradient":
            statistic = float(g @ (new - x))
            if not np.isfinite(statistic):
                raise FloatingPointError("nonfinite gradient restart statistic")
            oracle.controller_dots += 1
            fire = statistic > 0
        else:
            fire = False
        oracle.controller_operations += 1
        if fire:
            theta, y = 1.0, new.copy()
        else:
            nxt = next_theta(theta, 0.0)
            y = new + momentum(theta, nxt) * (new - x)
            theta = nxt
        return Step(new, y, reset=bool(fire), event=bool(fire), loss=loss)

    return step


def _rhgd(oracle, x0, settings, family):
    from stat605.benchmark import Step

    v = np.zeros_like(x0)
    h = np.sqrt(settings.eta)
    age = 0
    period = settings.parameters.get("period_steps", 64)
    if type(period) is not int or period < 1:
        raise ValueError("period_steps must be a positive integer")
    controller = (
        NormalizedReset(family, settings.parameters.get("beta", 0.0), settings.cap)
        if family != "fixed"
        else None
    )

    def step(x, k):
        nonlocal v, age
        new, pre, g, _, accepted = FROZEN_B.rhgd_step(oracle, x, v, h)
        # A reset must never mask a nonfinite trial.
        if not all(np.isfinite(a).all() for a in (new, pre, g)):
            return Step(new, pre, gradient=g, velocity=pre)
        power = float(g @ pre)
        oracle.controller_dots += 1
        oracle.controller_operations += 1
        if family == "fixed":
            age += 1
            event, capped, signal, observed_age = age >= period, False, float(age), age
            if event:
                age = 0
        else:
            kinetic = float(0.5 * (pre @ pre))
            oracle.controller_dots += 1
            event, capped, signal, observed_age = controller.observe(power, kinetic, h)
        reset = event or capped
        v = np.zeros_like(pre) if reset else pre
        return Step(
            new,
            v,
            reset=reset,
            event=event,
            capped=capped,
            accepted=accepted,
            power=power,
            gradient=g,
            velocity=pre,
            signal=signal,
            age=observed_age,
        )

    return step


def _rcm(oracle, x0, settings, rule):
    from stat605.benchmark import Step

    v = np.zeros_like(x0)
    g = oracle.grad(x0)
    age = 0
    h = np.sqrt(settings.eta)

    def evaluate(x):
        if not np.isfinite(x).all():
            raise FloatingPointError("nonfinite RCM trial position")
        gradient = oracle.grad(x)
        if not np.isfinite(gradient).all():
            raise FloatingPointError("nonfinite RCM gradient")
        return gradient

    def step(x, k):
        nonlocal v, g, age
        pre = v - h * g
        new = x + h * pre
        trial_g, fire = None, False
        if age:
            speed = float(pre @ pre)
            oracle.controller_dots += 2
            if rule == "kin":
                fire = speed < v @ v
            elif rule == "mmd-r":
                fire = speed / (age + 1) < (v @ v) / age
            else:
                trial_g = evaluate(new)
                signal = speed + 2 * (age + 1) * (trial_g @ pre)
                if not np.isfinite(signal):
                    raise FloatingPointError("nonfinite RCM restart statistic")
                fire = signal > 0
            if not np.isfinite(speed):
                raise FloatingPointError("nonfinite RCM speed")
        oracle.controller_operations += 1
        if fire:
            oracle.rejected_trials += 1
            pre = -h * g
            new = x + h * pre
            trial_g = evaluate(new)
            next_age = 1
        else:
            trial_g = evaluate(new) if trial_g is None else trial_g
            next_age = age + 1
        v, g, age = pre, trial_g, next_age
        return Step(new, v, reset=bool(fire), event=bool(fire), age=age)

    return step


def register_methods(methods):
    from stat605.benchmark import Method

    methods.update(
        {
            m.name: m
            for m in (
                Method("GD", _gd, 1),
                Method("FREE_AGD", partial(_agd, rule="none"), 1),
                Method("FUNCTION_AGD", partial(_agd, rule="function"), 1),
                Method("GRADIENT_AGD", partial(_agd, rule="gradient"), 1),
                Method("FIXED_RHGD", partial(_rhgd, family="fixed"), 2),
                Method("ENDPOINT_RHGD", partial(_rhgd, family="endpoint"), 2),
                Method("KINETIC_RHGD", partial(_rhgd, family="kinetic"), 2),
                *(
                    Method("RCM_" + rule, partial(_rcm, rule=rule), 1, variable_cost=True)
                    for rule in ("kin", "mmd-r", "mmd-dr")
                ),
            )
        }
    )
