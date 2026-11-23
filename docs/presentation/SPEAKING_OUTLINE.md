# When should momentum be reset?

Presentation: November 24, 2026, 2:20 p.m. Budget: 16 minutes plus four minutes
for questions. Speaker assignments are flexible; a suggested split is Shlok
(question, RHGD), Kwonsang (AGD), Leonardo (RCM), Leo (geometry), with results
shared. This is a speaking outline and figure placement guide, not a slide deck.

The main question is whether trajectory-dependent, mu-free reset rules improve
RHGD's measured efficiency and robustness, and under which spectral and initial
energy conditions. The hypothesis concerns conditional rankings; normalization
need not improve performance.

## 0:00–1:00 — When does discarding momentum help?

Title: **Resetting trades useful inertia against oscillation.**
Use proposal slide 16's modal picture. Explain that one global reset acts on all
frequencies, which makes spectral geometry and starting energy plausible causes
of changed rankings. Transition: compare reset rules while retaining the RHGD
numerical step. A favorable curve is neither a rate theorem nor a novelty claim.

## 1:00–2:30 — Three families, several reset clocks

Title: **AGD, randomized acceleration, and conservative restarts.**
Describe GD; known-mu AGD; variable-theta mu-free AGD with no/function/gradient
restart; CAGD; five RHGD rules; RCM kin/mmd-r/mmd-dr. Fourteen final methods.
Explain eta=h². RHGD and symplectic-Euler RCM use different integrators; an RCM
result does not directly validate a new RHGD controller. Historical AR_AGD uses
a different recurrence and remains a regression comparator, outside the final 14.

## 2:30–4:00 — What did we replicate?

Title: **Source parity is stronger than visual resemblance.**
Figure: `assets/replication_overview.png` (exported with the final report) and backup
`../evidence/README.md`, `../AGD_RESTART_SUMMARY.md`, `../RCM_REPLICATION.md`.
Numerical takeaway: five retained RHGD replay cases pass 24, 25, 24, 33, and 26
array comparisons against independent author-code execution. AGD/RCM examples
use declared new instances, so they establish selected qualitative agreement.
The weak RHGD example extends the notebook iteration count. Original published
raw arrays were unavailable; do not describe these as exact published-figure data.

## 4:00–5:30 — A matched design with honest costs

Title: **Same endpoints and condition number; six different energy geometries.**
Figure: `assets/geometry.png`. d=100, mu=5e−5, L=500, condition number 10⁷; retained
common basis; linear/log/clustered spectra; rescaled-common/equal-energy starts
with initial objective about one. Five algorithm seeds each for CAGD and random
RHGD on fixed problems, one path per deterministic method: 132 main paths.
Explain paid gradients, literal cached requests, controller versus diagnostic
objectives, discarded trials, and no target-based stopping. Budget is selected
by pilot runtime, then parameters by separate training cases, before final cases.

## 5:30–7:30 — Two normalization rules are distinct

Title: **Endpoint power and discrete kinetic decrease need not reset together.**
Write P=g(x_k)ᵀv_pre, K=||v_pre||²/2, t=nh. Endpoint rule arms on tP+beta K<0
and resets on a subsequent nonnegative signal. beta=0 reproduces power reset.
Discrete rule compares K/t^beta with the preceding segment value, after a
positive observation; only strict decrease triggers. Both retain the new
position, zero velocity, clear the segment, and cap at 65,536 steps. Finite trial
states are checked before resetting. Equality does not trigger discrete decrease.
Numerical takeaway: scalar f=x²/2, eta=.002, beta=1 first resets at step 27 versus
26. This illustrates different definitions, not optimization superiority.
The endpoint expression is a continuous-dynamics-inspired discrete heuristic;
RHGD's discrete energy balance does not make it an exact identity.

## 7:30–9:30 — Main measured efficiency

Title: **No reset family wins all six geometries.**
Figure: `assets/comparison.png`; backup `full_gradients.png`, `targets.csv`, `costs.csv`.
Numerical takeaway: gradient-restart AGD needs 55 gradients on rescaled linear;
RCM mmd-dr leads equal-energy linear at 7,670; known-mu AGD leads equal-energy
log at 21,593. Normalization tuning chooses beta=0 for both families. Read
`assets/RESULTS.md` and `assets/work_to_target.csv` for the complete audited table.
Discuss sustained relative gap 10⁻⁶ first; 10⁻⁴ and 10⁻⁸ are secondary. Every
method and all five randomized seeds remain in denominators. A censored median
is not an observed cost and not proof of eventual failure. Compare controller
objective costs and reset counts as well as gradients. Do not use tuning
penalties as observed work. State the uniform ceiling and any failed paths.

## 9:30–11:30 — Geometry and starting energy

Title: **Condition number alone does not specify the optimization problem.**
Figure: `assets/geometry.png`, with selected panels of `full_gradients.png`.
Initial anchor: the submitted 2,000-gradient spectral pilot had 36/39 sustained
10⁻⁴ successes for rescaled starts and 0/39 first hits for equal-energy starts.
This was a five-method pilot, not the final fourteen-method comparison, and its
raw traces were unavailable locally. The final 200,000-gradient fourteen-method study has 64/66 sustained 10⁻⁶
hits for rescaled starts and 57/66 for equal-energy starts. The longer study
resolves many earlier censored paths; the pilot misses were not eventual failures. Explain E_i(0)=lambda_i z_i(0)²/2: equal coordinate
amplitudes often put energy in fast modes; equal modal energy exposes slow modes.
A changed ranking supports a conditional mechanism, not a universal theorem.

## 11:30–13:30 — Why does reset timing change?

Title: **A global signal mixes slow and fast modes.**
Figure: `assets/mechanism.png`; `assets/rhgd_gradients.png` and
`assets/rhgd_iteration.png` in backup. The selected endpoint beta=0 equals power
reset; this figure diagnoses the selected controller rather than positive-beta gains.
Follow one log-spectrum endpoint-normalized trajectory: slow/fast modal power,
controller signal, and gap share an iteration axis; vertical lines mark resets.
Discuss only visible, reproducible signal timing. Mode cancellation can delay a
power crossing, and normalization can move it. The figure diagnoses one path;
it cannot establish the cause of every aggregate ranking. Randomized ablations
show individual seeded paths, not uncertainty over independent datasets.

## 13:30–14:30 — Robustness and uncertainty

Title: **Mu-free does not mean stepsize-free.**
Figure: `assets/robustness.png`; backup `robustness.csv`, first/sustained target columns.
Supplied-mu factors .01, 1, 100 only for methods that use mu. h factors .5, 1,
1.1 for all methods on rescaled linear/log problems; 1.1 is a stress test.
All 198 sensitivity paths are retained. Eighteen numerical failures occur, all
in the 1.1× RHGD stress cases (nine paths per spectrum across the five RHGD rules).
There are no numerical failures at baseline or half stepsize, or in supplied-mu
checks. This separates failure of a tested stepsize from a mu-free reset rule.
Normalization parameters stay frozen. Fixed period is rounded to integer steps
at changed h and the realized physical period is recorded. Retain numerical
failures, misses, and discarded/unfinished work. State any deferred checks.

## 14:30–16:00 — What can we conclude?

Title: **Reset timing matters conditionally; normalization is an empirical choice.**
Use the audited main finding, one geometry observation, and one robustness
qualification from `assets/RESULTS.md`. Historical anchor: power-reset RHGD reduced
sustained 10⁻⁸ work from 61,274 to 10,000 gradients on the retained linear case,
and from 127,424 to 43,016 on the log case; it did not beat historical restarted
AGD on both spectra or pass the predeclared work-and-time improvement gate.
These historical absolute-gap comparisons use original starts and budgets;
do not mix them with the new relative-gap table. If normalization loses, say so.
Limits: fixed quadratics/basis, six geometries, finite budgets, five algorithm
seeds, parameters selected from small declared grids. Logistic is deferred.
Close with the actual answer to the research question and invite questions.

## 16:00–20:00 — Backup answers

- **Gradient fairness:** enforce the budget at each actual matrix-gradient call.
  RCM pays its initial gradient, carries accepted endpoint gradients forward,
  and pays both trial and replacement gradients when required. RHGD pays two
  per complete step; CAGD's identical within-update request is cached. Literal
  requests, cache hits, initialization, unfinished work, and rejected trials
  are reported separately.
- **Objectives and timing:** function-restart AGD's objective is controller work
  and is reused for its diagnostic trace. Other endpoint objectives are
  diagnostics. Gradient cost alone omits controller objective cost. Optimizer
  and diagnostic timing are separate; no universal wall-time claim follows.
- **Tuning fairness:** each of 12 candidates receives 20,000 gradients on all
  six training cases (three matrices, two Gaussian starts, seeds 1605/2605).
  No equal-energy final start is used for tuning. Choose one parameter per
  family using mean sustained 10⁻⁶ work, predefined miss/failure penalties,
  final-gap tie break, then grid order. Report all candidates and their costs.
- **Censoring:** first crossing can be transient; sustained means remaining
  under target through the completed finite run. Failed paths have no sustained
  hit. On rescaled linear, RCM kin first crosses at 178 gradients but its
  finite-horizon sustained crossing is at 200,000, the last saved endpoint.
  This does not guarantee the next step stays below target. Missing paths cannot
  disappear from a denominator. A median including
  censored paths may itself be censored. No success-only medians are used.
- **Mu-free:** adaptive reset rules avoid supplied mu but still use L through
  eta/h, a finite segment cap and a tested spectrum. This is not parameter-free.
- **Integrator distinction:** RCM uses symplectic Euler and may discard a trial
  before taking a restart step from the previous point. RHGD's frozen map is
  different and retains its new endpoint when its controller zeros velocity.
- **Continuous versus discrete:** continuous kinetic dissipation motivates the
  endpoint signal; discrete RHGD does not obey the identical energy identity.
- **Reproduction scope:** exact source-array parity is separate from agreement
  with a printed paper figure; generated seeded examples disclose that limit.

## Rehearsal and freeze

Before 7 a.m., verify `ASSET_HASHES.json`, raw archive hash, matching path counts,
figure labels, uniform budgets, and `RESULTS.md`; freeze those exported files.
One run of the report command regenerates assets from saved data (see README).
Rehearse at 14:30 once, then 16:00; keep the comparison and mechanism explanations
intact if transitions run long. Allocate four minutes to questions. No slide-deck
construction is part of this task.
