# Method conventions

## Existing reusable code

`src/power_reset_spectral_comparison/core.py` contains the tested fair-cost
quadratic runner. It loads `study/B/src/power_reset.py` without changing its
function bodies. `configs/studies/power_reset_spectral_comparison.json` pins its
old settings. Preserve these files as reference implementations.

| Display name | Historical identifier | Information and reset |
| --- | --- | --- |
| AGD | `AGD` | Fixed strongly-convex momentum uses supplied mu and L |
| Gradient-restart AGD | `AR_AGD` | Convex theta recurrence; strict positive gradient/displacement test; resets theta to 1 and extrapolation to retained new x |
| CAGD | `CAGD` | Continuized acceleration; supplied mu and L; exponential clock |
| Original RHGD | `RHGD` | Existing two-gradient map; Bernoulli reset uses supplied mu in the strong-quadratic runner |
| Power-reset RHGD | `B` | Same map; arm after strict negative endpoint power, reset on nonnegative power after arming or at cap 65,536 |

For frozen B, `power = dot(gradient_at_new_x, velocity_before_reset)`. Retain the
new position and zero velocity; there is no rollback to a segment minimum.
Each reset clears segment age and arming. The cap applies even while unarmed.
Nonfinite state or power is a failure, not a trigger. The controller is mu-free;
the whole algorithm still needs a stepsize.

## Integrators must stay distinct

RHGD takes

```text
x_half = x + h*v
x_new  = x_half - h^2*grad(x_half)
v_pre  = v - h*grad(x_new)
```

The proposal's RCM symplectic-Euler update takes

```text
v_new = v - h*grad(x)
x_new = x + h*v_new
```

They differ in gradient locations, cost, and numerical dissipation. The
continuous-flow identity `f(anchor)-f(x)=0.5*||v||^2` must not be assumed exact
for either discrete map. A kinetic-power crossing, objective increase, and
maximum mean dissipation are distinct discrete triggers. New definitions and
tests are required before claiming an implementation matches the RCM source.

The proposal's variable-theta algorithms also differ from fixed strongly-convex
momentum AGD; state which recurrence each experiment uses.

## Measurement conventions

Count actual distinct gradient evaluations and literal calls separately. Reuse
the identical immutable point within an update uniformly across methods. Do not
merge different stage points merely because their values coincide numerically.
Count objectives and controller work separately; retain numerical failures.

A first crossing can be followed by loss increase. A sustained crossing remains
below the target through the observed budget, not forever. Missing targets are
censored. Best-so-far output and current state answer different questions.
Do not turn signed floor losses into invented positive accuracy.

The historical fair study's RNG streams differ intentionally from author-cell
replay. Preserve each study's seed/draw conventions rather than mixing traces.
The [historical protocol](studies/power_reset_spectral_comparison/PROTOCOL.md)
contains its exact boundary; the new course suite needs its own frozen config.

## Fixed-time RHGD control

Implemented November 23, 2026 in `src/stat605/rhgd.py`:

```python
from stat605.rhgd import run_fixed_time_quadratic

arrays, metadata = run_fixed_time_quadratic(
    A, x0, h=h, period_steps=m, gradient_budget=budget, keep_states=True
)
```

This initial implementation is for constant-step quadratics. It calls the same
unchanged frozen `rhgd_step` and the same within-update oracle/cache as the
historical fair comparison. Starting at zero velocity, take exactly m updates,
keep the new position and set velocity to zero, then repeat. The physical reset
interval is T=m*h. Count completed steps with integers to avoid floating-point
threshold drift. The interval m is a required input; there is no inferred/tuned
period, power trigger, random refresh, rollback, or extra cap.

Every attempted update pays two distinct gradients, including m=1 and coincident
zero states. Thus m=1 has the same positions as GD with eta=h^2 but retains the
two-gradient RHGD cost. An odd budget leaves one gradient unused; never split a
step. Do not reset an unfinished final segment solely because the budget ended.
Objectives are counted separately, including initial and failed-trial checks.
Check the pre-reset velocity before deleting it: nonfinite candidates fail, their
work stays charged, and raw failed states/objectives are returned in the arrays.
There is no accuracy-based early stopping; finite signed floor losses are retained.

The returned `f`, `gradients`, `literal_gradients`, `flow_time` and `elapsed`
include the initial point. `reset[i]` and `age[i]` describe completed update i+1;
age is recorded before its reset. Optional `x` and post-reset `velocity` include
the initial state; `velocity_pre_reset` describes completed updates. `x_final`
and `aux_final` contain the final position/velocity. Failure metadata includes
actual spent gradients, charged unfinished work, and the failure reason; failed
attempts are not reported as completed endpoints or resets. State logging is
optional; returned elapsed times include the requested logging/observations and
are not matched historical timing evidence.

Run the capped demonstration from the root after activating the environment:

```bash
python scripts/stat605.py fixed-time-smoke --output tmp/fixed-time-example
```

`configs/stat605/fixed_time_smoke.json` declares m=8, h=sqrt(0.002), and 200
gradients per shared quadratic. It saves traces, reset-marked PNG, source/input
hashes, and JSON metadata. The command caps smoke budgets at 2,000 gradients per
fixture. This is implementation validation, not a choice of a competitive period
or an optimization result. Full comparisons need predeclared periods, matched
budgets and a suitable allocation. Adaptive-step logistic fixed-time scheduling
and the group's general comparison harness remain separate work.
