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
