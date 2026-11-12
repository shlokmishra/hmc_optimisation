# Frozen protocol: power-reset RHGD versus adaptive-restart AGD

Frozen 2026-09-23 before construction validation, probes or main performance runs.
The scientific design and decision rule below must not change after results are
seen. Any additional diagnostic must be labeled **POST-HOC DIAGNOSTIC**. The
machine-readable authority is `configs/studies/power_reset_spectral_comparison.json`.
A freeze receipt hashes this protocol, the configuration, prior B sources/config,
retained data and new prepared arrays before performance runs. Prior studies and
reproduction artifacts remain unchanged.

## Question and scope

Does frozen B retain an efficiency advantage over the specified alpha-free
adaptive-restart AGD under uniform reuse of identical within-update gradients,
and does this advantage survive a change in spectral density at fixed alpha,
L, condition number, dimension, eigenbasis and initial point? This is a new
comparison, not a reproduction or an algorithm repair. No B2, A, C, deadband,
smoothing, rollback, partial/blockwise reset, new tolerance or parameter sweep.

Read inputs: `docs/design/WALNUTS_RHGD_RESEARCH.md`, `study/B/REPORT.md`,
`study/B/THEORY.md`, `study/B/configs/frozen.json`, `docs/studies/SYNTHESIS.md`,
`docs/reproduction/PROTOCOL.md`, `docs/reproduction/STATUS.md`, the retained
Figure 1-left arrays and author cell, and `study/B/src/power_reset.py`.

## Problems and initialization

Both problems have d=100, intended alpha=5e-5, L=500, kappa=1e7; eta=.002,
h=sqrt(eta) using the frozen B arithmetic. Load the exact paper A and x0 from
`results/reproduction/fig1-left-19769000/figure-01-arrays.npz`. Never regenerate,
symmetrize or repair that optimization matrix.

For construction only, compute ascending eigenpairs of (A+A.T)/2. Resolve the
otherwise arbitrary eigenvector signs by making each column's largest-absolute
entry positive. Let this ordered basis be Q. Compute lambdas=geomspace(alpha,L,100)
and A_log=Q@diag(lambdas)@Q.T. Do not subsequently symmetrize A_log. Use the same
x0. Save each array individually (A_paper, A_log, x0, Q, intended lambdas,
computed symmetric-part eigenvalues/eigenvectors, raw nonsymmetric eigenvalues)
and its SHA256, dtype and shape. Report extremal curvatures, symmetry residual,
orthogonality/reconstruction residual, intended versus represented spectrum,
and the signed original slow projection. The original rounded objective and
gradient algebra remain f(x)=.5*x@A@x and g(x)=A@x.

Diagnostics diagonalize each represented matrix's symmetric part. Save both the
ideal lambda_i*q_i*v_i modal power and the actual transformed author-gradient
contribution (U.T@g)_i*(U.T@v)_i, and reconstruction residuals. Tiny representation
asymmetry is reported, not repaired.

Two separate slow-only controls initialize x=(u_min.T@x0)*u_min for the
corresponding matrix. Each runs identical B for the same work budget and is
excluded from benchmark-win and timing counts.

## Exact methods and state conventions

Exactly five optimizers: B, AR_AGD, AGD, CAGD, RHGD. B, AR_AGD, AGD are
deterministic (one scientific path each). CAGD and RHGD each have five seeds:
13 paths per spectrum, 26 primary paths total, plus two slow-only diagnostics.
All start at x0, with zero RHGD velocity, AGD extrapolated point x0 and CAGD
auxiliary position x0. Identity mass, float64, fixed steps throughout.

**B:** import the unchanged prior `rhgd_step` and `reset_decision` functions from
the byte-pinned `study/B/src/power_reset.py`. The adapter preserves its update
arithmetic and state/reset order. P=dot(g_new,v); arm on P<0; once armed reset at
P>=0; cap=65,536 updates regardless of arming. Retain x_new. Reset zeros velocity,
age and arming flag. The source and prior configuration are read-only; the new
budget/logging boundary is an experiment setting, not a trigger change.

**AR_AGD:** initialize x=x0, u=x0, t=1. At each update set

```
g = grad(u)
x_plus = u - eta*g
t_plus = (1 + sqrt(1 + 4*t*t))/2
if dot(g, x_plus-x) > 0:
    t_plus = 1
    u_plus = x_plus
else:
    u_plus = x_plus + ((t-1)/t_plus)*(x_plus-x)
x, u, t = x_plus, u_plus, t_plus
```

It has no alpha argument, rollback, deadband, tolerance or line search. It is one
precisely specified comparator related to adaptive-restart literature, not every
possible restart variant. Analytic tests cover initial step, extrapolation,
strict zero boundary, actual positive-trigger reset and retained x_plus.

**AGD/CAGD/RHGD:** project/source-equivalent recurrences from the existing B-study
adapter and author cell. Use true alpha. Preserve arithmetic and state ordering,
changing only duplicate gradient reuse and the explicitly new method-specific
random streams. RHGD reset probability is sqrt(alpha)*h. CAGD uses the author's
cumulative exponential clock, drawing only N+1 values for its new N-update run.
No historical million-draw or shared-stream side effects are timed.

## Gradient, objective and decision accounting

Primary work is actual numerical gradient evaluation with uniform within-update
reuse. Clear the cache before every update. If an unchanged argument array is
queried again in that update, reuse its already calculated gradient; the cache
holds the argument reference to prevent object-ID reuse. No cross-update reuse,
no merging of distinct stage sites that happen to coincide at the numerical
floor. Thus B/RHGD's distinct half-step/endpoint locations cost two, AR_AGD/AGD
one, and CAGD's repeated identical extrapolated argument one. The same oracle
and cache policy applies to all methods. No memoization of nearby points.

Record literal request counts separately: 2/1/1/2/2 per update for
B/AR_AGD/AGD/CAGD/RHGD; actual primary counts are 2/1/1/1/2. Uncached/cached
prefix runs and direct original-function checks must have identical losses,
iterates and final states. B must additionally match its prior recorded paper
prefix and direct frozen implementation on both new input matrices.

Every method evaluates current objective at initialization and after each update
(N+1 objectives). These contain one matrix-vector product and scalar product,
recorded separately from gradients. Count controller dot products (one/update
for B and AR_AGD), stochastic draws, cached hits, objective calls and significant
scalar decision functions. Detailed kinetic/mode/slow-coordinate diagnostics
have separately reported dot products and timing, never free hidden gradients.
No timing-only power calculation for RHGD. Primary timing includes only each
algorithm's actual decision work, common finite checks and common loss/time logs.

## Budget, targets, censoring and failure

Enforce 200,000 actual numerical gradients per path; stop before an update cannot
fit. B/RHGD execute at most 100,000 updates; other methods at most 200,000.
No accuracy stopping. All successful paths share the full observed work horizon.
Primary target: current raw f<=1e-8. Secondary: 1e-6 and 1e-10. Retain first
crossings and the earliest crossing that stays below target through the entire
observed common horizon. This is an offline statistic, not an online stopping
rule. No best-so-far output and no ranking of signed numerical-floor plateaus.

Unreached costs remain censored (infinite for median/decision calculations).
Nonfinite state/objective/power, exception, or scheduler termination is a failure;
retain arrays, charged work and reason. A failed path cannot claim a successful
sustained hit through 200,000 gradients. No paths are dropped, no retries for
performance, no silent cap/budget extensions. Infrastructure validation failures
must be resolved and documented before main interpretation.

## Randomness and timing

CAGD seeds 31001–31005, RHGD seeds 41001–41005, independent `default_rng` streams;
reuse the same listed seed on the two spectra for a controlled comparison. No
random input construction beyond the retained data. Deterministic paths have
no algorithm seed. Shuffle timing order with seeds 51001, 51002, 51003.

First run a bounded probe of all 26 paths plus both controls at 2,000 gradients.
Record its extrapolated full-batch cost and a conservative allowance in STATUS
before main submission. Probe ceiling one CPU/two minutes; main ceiling one
CPU/twenty minutes; total <=.366667 allocated CPU-hours. Account 132674288899,
partition short verified live before freezing; account balance 18798.42 SU.
Ceilings are allocations, not a claimed billing tariff. No automatic resubmission.

Main run: warm each method/import first; 26 detailed full paths plus two detailed
controls, then three serial shuffled minimal-logging repetitions of every primary
path, each through the full same work horizon. Record CPU model, affinity, node,
Python/NumPy/BLAS versions and one numerical thread. Timing begins before state
and minimal-log allocation and CAGD's own N+1 draws, after data loading/warmup/RNG
object creation. It ends after final common loss/time observation. Setup,
serialization, offline modal analysis and plotting have distinct time fields.
No cross-study historical runtime comparison. Every minimal path must match its
scientific diagnostic path exactly. Report individual repetitions and medians,
not confidence intervals from five seeds. Failed timing runs stay failures.

## Required diagnostics and presentations

For all primary paths save raw f, actual/literal gradient counts, objective count,
elapsed time, final state, diagnostic slow-coordinate loss and update index.
For every B run save all full x, pre-reset v and available g_new; P, kinetic energy,
age, event/cap/reset flags, segment minima, before/after losses and reset states.
After timing, reconstruct eigencoordinates/modal loss and power with costs separate.
At each reset save signed global/slow power, positive/negative mode counts, largest
positive and negative contributors and their curvatures, faster-mode sum, and
whether the slow mode is still downhill. Report all events and the accuracy subset
with pre-update f>1e-10; this filter is not a numerical-floor estimator.

Per spectrum show current loss versus distinct gradients, optimizer seconds and
updates; slow loss versus gradients; B event times, segment lengths and global
power; modal contributions in +/-3-update windows around frozen representative
events (first/middle/last above-threshold event and event immediately preceding
sustained primary crossing). Compare full and slow-only B. Show every randomized
seed plus a clearly labeled pointwise median on a common grid using past-only
observations. Preserve raw signed/symlog views and positive-value masks. Tables
retain individual and aggregate first/sustained target costs and censoring.

## Falsifiable decision rule and separate theory

A general-speed direction passes only if B costs <=80% of AR_AGD's distinct
work AND <=80% of its median wall time at sustained 1e-8 on BOTH spectra, has no
optimizer failure, and has no >25% regression in either work or median time at
1e-6 or 1e-10 on either spectrum. Apply comparisons to finite full-horizon costs;
if comparator is censored and B finite, require the lower bound on comparator
cost to certify the margin. These are pragmatic criteria, not universal constants.
If the rule fails, stop the general-speed claim. Do not tune or repair B.

Theory is separate: derive the exact quadratic modal map and segment contractions;
attempt restricted-class accelerated work bounds and a cap-inactive dense-spectral
counterexample. Distinguish proved statements, conditional propositions, failed
attempts and open gaps. A finite empirical slowdown alone is not an asymptotic
counterexample. No optimizer parameter search is authorized as part of theory.

## Output paths and reproduction entry points

- Protocol/status/theory/report: `docs/studies/power_reset_spectral_comparison/`.
- Config: `configs/studies/power_reset_spectral_comparison.json`.
- Implementation: `src/power_reset_spectral_comparison/`.
- Tests: `tests/studies/test_power_reset_spectral_comparison.py`.
- Runner: `scripts/run_power_reset_spectral_comparison.py`.
- Frozen data/manifests: `results/studies/power_reset_spectral_comparison/data/`
  and `freeze.json`, `prior_artifacts.json` in its parent.
- Validation: `results/studies/power_reset_spectral_comparison/validation.json`.
- Probe and main: `results/studies/power_reset_spectral_comparison/probe-JOBID/`
  and `main-JOBID/`, each rejecting overwrite; Slurm logs in the parent.
- Derived tables, per-path NPZ, summary/audit and costs: main run directory and
  `analysis/` beneath it. Machine JSON, CSV and Markdown tables are retained.
- Figures/coordinates: `tmp/power_reset_spectral_comparison/main-JOBID/`.
- Scheduler/SU receipts and artifact hashes: results parent.

Activate with `source scripts/activate_env.sh`; runner subcommands are `prepare`,
`validate`, `probe`, `run`, `analyze`, `audit`. Only `probe`/`run` execute
performance work and require Slurm. Final report records exact job IDs and commands.
