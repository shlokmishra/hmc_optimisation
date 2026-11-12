# Frozen objective-power RHGD: controlled spectral comparison

**The frozen general-speed continuation rule fails.** B has a modest gradient
advantage and a substantial measured-time advantage on the paper spectrum, but
uses 70.8% more gradients than the alpha-free comparator on the dense log spectrum.
Keep B unchanged and stop the general-speed direction; multimode theory remains open.

New study, 2026-09-23. Scientific authority: [PROTOCOL.md](PROTOCOL.md),
[frozen configuration](../../../configs/studies/power_reset_spectral_comparison.json).
The completed A/B/C studies and original reproduction are retained unchanged.
All performance numbers below come from this new comparison.

## Research question and motivation

Does frozen Candidate B retain a useful efficiency advantage over the specified
alpha-free adaptive-restart accelerated-gradient method after fair gradient
reuse, on both the retained paper spectrum and a dense logarithmic spectrum
with the same dimension, alpha, L, eigenbasis construction and initial point?

The [independent synthesis](../SYNTHESIS.md) found that geometric Candidate A
resets too late, Candidate C had no meaningful pre-floor refinement need on the
tested quadratics, and B improved the original RHGD baseline. It also identified
two unresolved confounders: literal baseline implementations repeat gradients,
and a dense-spectrum B diagnostic showed slow-mode interruptions without a fair
optimizer comparison on that spectrum. Those observations motivated this study;
they are not counted as new performance evidence. No A or C paths, B2, repairs,
parameter sweeps, or additional optimizers were introduced.

## Methods and exact state conventions

**B is unchanged.** Its fixed quadratic step is

```
x_half = x + h*y
x_plus = x_half - h**2*grad(x_half)
v = y - h*grad(x_plus)
P = dot(grad(x_plus), v)  # reuse the endpoint gradient already evaluated
```

Observe P<0 to arm the current segment. Once armed, reset at P>=0; also retain
the existing operational cap of 65,536 updates. A reset keeps x_plus, sets y=0,
and clears age/arming. Otherwise keep v. There is no rollback, deadband,
smoothing, extra line search, partial reset or Bernoulli fallback. The actual
step and decision functions are imported from the unchanged
[prior B source](../../../study/B/src/power_reset.py), whose SHA256 is
`12690622465189339b0203bce4d71fe8fa4c69b0778fd16f9dc735f4e914889c`.
The prior B configuration hash is
`317c74277fc4bbc62d5360341a9deb9a50c7378f038b1cd1845432c96b0d0606`.
B's reset controller uses no supplied alpha; L still sets h=1/sqrt(L).

**AR_AGD**, the precise alpha-free comparator, starts x=u=x0, t=1, eta=1/L:

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

Here x is the accepted endpoint, u the next gradient/extrapolation point, and t
the convex acceleration clock. A restart retains the new endpoint and resets
both extrapolation and clock. A zero dot product does not restart. There is no
alpha, rollback, tolerance, deadband or line search. The gradient/displacement
restart motivation is established in
[O'Donoghue and Candes, section 3.2](https://arxiv.org/html/1204.3982v1#S3.SS2).
B uses a different endpoint gradient/velocity proxy in RHGD's dissipative map;
the general idea of removing harmful momentum is not novel. This one specified
comparator does not represent every adaptive-restart method.

**AGD, CAGD and RHGD** use the project/author recurrences with true alpha=5e-5.
Their numerical state ordering is unchanged apart from identical-gradient reuse.
RHGD has Bernoulli reset probability sqrt(alpha)*h. AGD has fixed momentum
(1-sqrt(alpha/L))/(1+sqrt(alpha/L)). CAGD retains its exponential-clock update.
This is a new independent-stream comparison, not historical shared-RNG replay.

Per spectrum there is one B, one AR_AGD and one AGD trajectory, five CAGD seeds
31001–31005, and five RHGD seeds 41001–41005: **13 primary paths per spectrum,
26 total**. Each randomized path uses its own `numpy.default_rng` and the same
listed seed on both spectra. Two additional B slow-only paths diagnose mechanism
and never count as benchmark wins. Every path starts at the prescribed x0 with
zero momentum/appropriate initial auxiliary positions.

## Matrices, initialization and provenance

Both problems have d=100, intended L=500, alpha=5e-5 and kappa=1e7. The paper
A/x0 are loaded directly from
`results/reproduction/fig1-left-19769000/figure-01-arrays.npz`; archive SHA256:
`36e998439575f55287c92b9758e8cb88a0cb87fe51af70fcadb6762529c9137d`.
They were not regenerated or symmetrized for optimization.

For construction only, Q is the ascending orthogonal eigenbasis of the paper
matrix's symmetric part, with each column's largest-absolute entry made positive.
The new matrix is exactly the saved float64 expression
`Q @ diag(geomspace(5e-5,500,100)) @ Q.T`, with the same x0. There is no subsequent
symmetrization. The intended log spectrum, independently computed spectra,
Q, both diagnostic eigenbases, A_log and x0 are saved individually with hashes.
This is a new controlled problem, not a correction to the published example.

| Quantity | Paper | Dense log |
|---|---:|---:|
| Computed smallest symmetric-part eigenvalue | 5.0000000027188764e-5 | 5.0000000008373106e-5 |
| Computed largest eigenvalue | 499.99999999999983 | 500.0000000000003 |
| Computed condition number | 9999999.994562244 | 9999999.998325385 |
| Next eigenvalue after the smallest | 5.05055455 | 5.88405976e-5 |
| Original signed slow projection | 0.6347233019328173 | 0.6347233027715493 |
| Initial slow-coordinate objective | 1.007184175588928e-5 | 1.0071841778717248e-5 |
| Initial full objective | 11362.682269790992 | 1594.041124014992 |
| Maximum entrywise asymmetry | 2.84e-14 | 7.11e-15 |

Thus spectral density and initial distribution of energy across curvatures change,
while x0, intended extrema and the construction basis are held fixed. Total initial
objective is deliberately not normalized: doing so would violate the same-x0 design.
The almost identical slow projections make the full-versus-slow-only comparison
interpretable. Each slow-only control uses `(u_min.T@x0)*u_min` for its own matrix.

Raw C-order byte SHA256 values (file/container hashes are additionally retained):

| Array | SHA256 |
|---|---|
| Paper A | `38e47e1ea02d937f3103abbbc4adfa6f3e25c6d91eddf0025100e926a7bcf56c` |
| A_log | `aabf1ff12f9068825e45e7cf6cc7e4bc2ba0f470d89f2e23c8e516ca12a27bf0` |
| x0 | `22467333cce9ae74da2aa3d048e6921cad04043b1d1d5b3097c76623328d7333` |
| Q | `d034138b5d40730e8b9e62fa71ec8c2ffbe0298a1191f876ae54dbb50167e648` |
| Computed log spectrum | `af278988507cb213d9fffe4efaea2e9b580249cb1ea5af752bb3af88f24f165e` |

The [freeze receipt](../../../results/studies/power_reset_spectral_comparison/freeze.json)
contains full residuals and every saved-array hash. Diagnostics use each represented
matrix's symmetric eigensystem and also reconstruct power from the actual transformed
gradient, so the tiny asymmetry is neither silently repaired nor ignored.

## Gradient accounting, observations and targets

The primary work unit is a numerical gradient evaluation. An unchanged argument
array may reuse its gradient within an update; the same oracle/cache policy serves
all five methods. The cache is cleared before every update. Distinct stage arguments
are always charged separately, including B's half-step and endpoint. Coincidence
at a numerical floor does not merge stages. Direct original-path and cache parity
checks verify that this policy preserves the numerical trajectories.

| Method | Distinct gradients/update | Literal requests/update | Controller dots/update |
|---|---:|---:|---:|
| B | 2 | 2 | 1 |
| AR_AGD | 1 | 1 | 1 |
| AGD | 1 | 1 | 0 |
| CAGD | 1 | 2 | 0 |
| RHGD | 2 | 2 | 0 |

Every method records current objective at initialization and after each update,
so N updates have N+1 objective evaluations, each with one matrix product and
one scalar product. These are counted separately from gradients. CAGD has N+1
exponential draws and per-update exponential/tanh clock work; RHGD has N uniforms.
Reset dots, scalar decisions, cache hits, and diagnostic dot/norm counts are saved.
Offline modal transformations use saved gradients and add zero gradient calls.

All paths run to **200,000 distinct gradients**, without accuracy stopping:
100,000 B/RHGD updates or 200,000 AGD/AR_AGD/CAGD updates. The analytic intended
minimum is f*=0. Primary target is current f<=1e-8; secondary targets are 1e-6 and
1e-10. First hit and sustained hit are both retained. Sustained means the earliest
hit after the last violation through the common 200,000-gradient horizon; it is
an offline statistic, not a usable online stopping certificate. Best-so-far loss
never supplies the output or ranking. Raw signed losses are retained; plots mask
nonpositive values only for log display and also supply full signed views.
Unreached paths are censored, optimizer failures remain failures, and neither is
discarded when computing descriptive summaries.

## Timing and frozen decision rule

Main job **19819633** and bounded probe **19819630** use the same node **c672**,
one numerical thread, and the same logging boundary across methods. Warmup and
input loading precede timing. The minimal timed path includes state/log allocation,
actual decision work, common finite checks, and each current objective/time
observation. CAGD's N+1 random-clock draws are included; RNG-object setup is outside.
Detailed modal/kinetic logging is collected separately. Serialization, plotting,
and offline analysis are outside optimizer time. Full-budget repetitions match
the scientific path; the target timestamp is read from each repetition.

Three serial timing repetitions of all 26 primary configurations use shuffled
orders with seeds 51001, 51002, 51003. Deterministic timing reports the median of
three repetitions. Randomized timing reports each seed's three-repeat median,
then the descriptive median across five seeds. Work summaries similarly use the
five individual seeds, not a pooled/mean loss crossing. Five algorithm seeds do
not justify a confidence interval. No historical timing is used in this report.

Before the full batch, the 2,000-gradient-per-path probe projected 549.3 seconds
of optimizer work and a conservative total of 1186.1 seconds including saving
results. The frozen main ceiling was 1200 seconds on one CPU, with a combined
probe/main allocation ceiling of 0.366667 CPU-hours; see [STATUS.md](STATUS.md).

The frozen continuation gate requires B to use at most 80% of AR_AGD's distinct
gradients **and** median time at sustained 1e-8 on **both** spectra, with no
optimizer failure and no >25% regression in either metric at either secondary
target. These are practical study thresholds, not scientific constants. Failure
of this gate stops the general-speed direction; it does not authorize changing B.

## Fidelity and validation outcome

All 26 cached/uncached prefixes match exactly, including intermediate states;
the author AGD/CAGD/RHGD paths match their adapters with independent method seeds.
B matches the unchanged implementation on both matrices and its retained paper
prefix. Analytic AR tests verify state order, zero versus positive trigger,
endpoint retention and absence of an alpha argument. Hand-counted short runs,
deterministic repeats and randomized seeded repeats pass.

The independent full-run audit passed for all 28 paths and all 78 timing paths:
full loss/endpoint equality, actual/literal/objective counters, every one of the
400,000 B arming/reset decisions across the four B paths, and independently
reconstructed reset endpoints/powers/objectives. All 912 protected prior files
are byte-unchanged. Protocol and configuration hashes still match the pre-run
freeze. Repository-wide lint/format checks passed, as did 34 study/reproduction
tests, including checks of the theoretical scalar formula.

One offline reporting error was fixed: relative CLI paths were normalized before
forming a root-relative output label. It occurred before a performance summary
was written and required no optimizer rerun. The cause, fix and successful retry
are retained in STATUS.md. Plot readability changes affect derived displays only.
No scientific configuration or numerical implementation changed after main runs.

## Main results: sustained current objective 1e-8

Randomized entries are descriptive medians across the five recorded seeds.
First and sustained medians are computed independently per path; no mean-curve
crossing is used. Time is the three-repeat median, then the five-seed median where
applicable. Every target in the tables was reached by every primary path.

| Spectrum | Method | First gradients | Sustained gradients | Sustained seconds |
|---|---|---:|---:|---:|
| paper | B | 10,000 | 10,000 | 0.168641 |
| paper | AR_AGD | 11,832 | 11,832 | 0.334968 |
| paper | AGD | 16,750 | 16,750 | 0.412655 |
| paper | CAGD | 16,747 | 16,747 | 0.518874 |
| paper | RHGD | 18,306 | 61,274 | 0.948523 |
| log | B | 43,016 | 43,016 | 0.722348 |
| log | AR_AGD | 25,188 | 25,188 | 0.711067 |
| log | AGD | 22,669 | 23,771 | 0.585235 |
| log | CAGD | 23,443 | 24,376 | 0.753798 |
| log | RHGD | 86,790 | 127,424 | 1.978735 |

**Paper:** B beats this AR_AGD at the primary target by **15.48% in gradients**
and **49.65% in measured time**. The work reduction misses the frozen 20% threshold.
B also beats correctly tuned AGD, cached CAGD and original RHGD at this target.
This is a real favorable result for the retained spectrum, but is insufficient
for the predeclared general-speed continuation rule.

**Dense log:** B uses **70.78% more gradients** than AR_AGD and **1.59% more median
time**. The timing difference is small relative to the observed repetition spread;
it supports approximate time parity, not a robust timing separation. B also needs
more gradients than correctly tuned AGD and cached CAGD. It still improves substantially
on original RHGD: 43,016 versus median 127,424 gradients, and .722 versus 1.979 s.
AGD is both cheaper in gradients and faster than B. B's small primary-time advantage
over CAGD (.722 versus .754 s) does not accompany a gradient-work advantage.

Iteration counts alone are misleading here: dense B takes 21,508 updates versus
25,188 for AR_AGD, but B's two-gradient update costs 43,016 gradients. Measured
wall time includes different per-update arithmetic and the prescribed common
objective/time observation, so it need not scale exactly with gradient count.
These timings characterize this single-thread Python/NumPy study implementation,
not every optimized implementation or objective-evaluation cost model.

Individual sustained-primary gradient costs, in ascending listed algorithm-seed order:

| Spectrum | Method | Five gradient counts | Five per-seed median seconds |
|---|---|---|---|
| paper | CAGD | 16783, 16646, 16755, 16731, 16747 | 0.5190, 0.5158, 0.5181, 0.5189, 0.5192 |
| paper | RHGD | 62258, 32506, 23944, 99952, 61274 | 0.9704, 0.5036, 0.3718, 1.5550, 0.9485 |
| log | CAGD | 24143, 24879, 24376, 24240, 24413 | 0.7439, 0.7699, 0.7538, 0.7515, 0.7540 |
| log | RHGD | 116492, 148604, 127424, 136686, 100470 | 1.8048, 2.3197, 1.9787, 2.1178, 1.5649 |

The three B/AR_AGD primary timing repetitions, in recorded repetition order, are:
paper B [.168641, .170667, .161594] s and AR_AGD [.335115, .334968, .307190] s;
log B [.722348, .726403, .658698] s and AR_AGD [.715939, .711067, .698459] s.
No confidence intervals are inferred from these repetitions or five algorithm seeds.

## Target dependence and first versus sustained crossings

| Spectrum | Method | Sustained gradients at 1e-6 | Seconds at 1e-6 | Sustained gradients at 1e-10 | Seconds at 1e-10 |
|---|---|---:|---:|---:|---:|
| paper | B | 8,172 | 0.137931 | 10,180 | 0.171663 |
| paper | AR_AGD | 8,811 | 0.249448 | 12,234 | 0.346312 |
| paper | AGD | 7,492 | 0.184306 | 25,142 | 0.619127 |
| paper | CAGD | 7,522 | 0.234270 | 25,140 | 0.777264 |
| paper | RHGD | 23,140 | 0.359359 | 66,402 | 1.027564 |
| log | B | 26,928 | 0.452296 | 59,394 | 0.999015 |
| log | AR_AGD | 17,244 | 0.486854 | 35,760 | 1.008467 |
| log | AGD | 16,771 | 0.413026 | 30,132 | 0.741723 |
| log | CAGD | 17,619 | 0.547013 | 31,266 | 0.967258 |
| log | RHGD | 77,950 | 1.213224 | 154,524 | 2.412378 |

At 1e-6, correctly tuned AGD/CAGD need fewer paper-spectrum gradients than B;
B's superiority over those methods is target-dependent even on the retained case.
Against AR_AGD, B's work ratios at [1e-6,1e-8,1e-10] are
**[.9275,.8452,.8321] on paper** and **[1.5616,1.7078,1.6609] on log**.
Its corresponding time ratios are [.5529,.5035,.4957] and [.9290,1.0159,.9906].
The log case therefore also violates the allowed 25% secondary-target work
regression at both secondary targets.

B and AR_AGD have identical first/sustained costs at all three requested targets
on both problems. This does not mean their full objective traces are monotone.
Original RHGD illustrates why sustained cost matters: on paper its median primary
first crossing is 18,306 gradients, but sustained crossing is 61,274. On log the
corresponding costs are 86,790 and 127,424. Tuned AGD/CAGD also have excursions on
log: AGD's primary costs are 22,669 first versus 23,771 sustained; CAGD's medians
are 23,443 versus 24,376. Every individual first/sustained work count and timing,
including secondary targets, is retained in `analysis/targets.csv` and
`analysis/target_records.json`, with the complete aggregate table in
`analysis/comparison.md`.

## What uniform caching changed

CAGD's two literal requests refer to one identical extrapolated argument. Caching
halves its numerical gradient work at every fixed iterate without changing any
iterate or loss. AGD already uses one gradient point; B/RHGD retain two distinct
sites; AR_AGD uses one. This is verified reuse, not a changed optimizer.

At the log primary target, literal-source counting would charge CAGD median
**48,752** calls, making B's **43,016** look 11.77% cheaper. Uniform reuse charges
CAGD **24,376**, making B **76.47% more expensive**. That ranking reversal is
material. On paper, CAGD changes from 33,494 literal calls to 16,747 actual gradients;
B remains cheaper at the primary target. CAGD's paper 1e-6 actual cost is 7,522,
which is lower than B's 8,172 despite its 15,044 literal requests.

Caching does not change the B-versus-AR_AGD gradient ordering, because neither
has duplicate gradient requests. The general-speed failure is therefore not
solely a caching artifact: it also arises against the alpha-free comparator and
under the spectrum change. All reported wall times already use the uniform cache;
no historical or uncached runtime is mixed into that comparison.

## Slow-mode and modal-power mechanism

| Diagnostic | Paper full B | Log full B |
|---|---:|---:|
| Power resets over 100,000 updates | 33 | 53 |
| Cap resets | 0 | 0 |
| All resets with negative slow power overwhelmed by other modes | 13 | 52 |
| Resets with preceding objective >1e-10 | 13 | 25 |
| Of those, faster modes overwhelm descending slow mode | 13/13 | 25/25 |
| Of those, delay from sampled segment minimum is 0 updates | 11 | 21 |
| Of those, delay is 1 update | 2 | 4 |
| Above-threshold segment lengths: min / median / max | 3 / 8 / 19 | 4 / 521 / 4915 |
| Slow-coordinate sustained 1e-8, full B, gradients | 10,000 | 41,396 |
| Same slow-coordinate target, slow-only B control, gradients | 9,736 | 9,736 |
| Full/control slow-target work ratio | 1.0271 | 4.2518 |

The pre-event objective filter >1e-10 was frozen as an accuracy-relevant subset;
it is not an estimated numerical floor. All events remain in the raw data and
summary. Overall reset frequency is 33/100,000 and 53/100,000 updates respectively.
The paper's 13 early interruptions finish by update 132, followed by repeated
4,968-update segments. The dense path repeatedly loses slow momentum well into
the target range: 20 interruptions precede the primary-target crossing. Its full
completed segment lengths range from 4 to 5,242 updates; the cap is inactive.
The extra work is not caused by the operational cap.

The slow-only controls isolate the coupling through the global trigger: the same
initial slow amplitude, curvature and stepping reach slow loss 1e-8 at update
4,868. Full paper B reaches it at update 5,000; full log B needs update 20,698.
Thus multimode resets materially truncate useful slow progress in this finite
comparison. This does not prove a general asymptotic complexity violation.

Representative dense resets selected by the frozen first/middle/last/pre-primary
rule show a moving set of responsible curvatures:

| Update | Segment age | Global P | Slow-mode power | Largest positive contributor lambda | Positive / negative modes | Total kinetic energy discarded |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 4 | 1.6632e2 | -1.8017e-10 | 260.7004 | 11 / 89 | 3.3666e2 |
| 2,621 | 1,025 | 5.1946e-7 | -4.0957e-8 | .1457527 | 39 / 61 | 1.8664e-3 |
| 16,748 | 2,493 | 7.4505e-12 | -1.4228e-9 | .000488505 | 48 / 52 | 3.6044e-7 |
| 27,850 | 676 | 3.4981e-15 | -1.2592e-14 | .005616620 | 44 / 56 | 5.7018e-11 |

At update 16,748, the reset discards slow kinetic energy 1.0120e-7 while slow
power remains negative. Its largest positive contributor is about 9.77 times
the minimum curvature. At other stages much faster/intermediate modes dominate;
the issue is a spectrum of competing oscillations, not necessarily the largest
lambda=500 mode. A majority of coordinates can have negative power while a few
larger positive contributions determine the global sign.

The actual transformed-gradient powers sum to the implemented P up to roundoff.
At the update-16,748 example their reconstruction residual is 1.58e-25; the ideal
lambda*x_i*y_i residual is 6.25e-19, versus P=7.45e-12. The observed sign conflict
in the accuracy range is not explained by those reconstruction residuals. Full
x, pre-reset y, endpoint gradient, eigenbasis and eigenvalues permit every mode's
coordinate/loss/power history to be reconstructed. Saved reset rows include the
five largest positive contributors, counts, slow power, total and slow kinetic
energy, current/next observed objective increments, minima and delays.

**The power proxy is not an objective-increase test.** At dense update 4, P>0
while the current objective increment is -58.7834. At update 16,748, P>0 while
that increment is -2.7197e-13. At update 2,621 the current increment is positive,
5.9188e-9, and B keeps that endpoint. The segment minimum is the minimum among
actually observed states from the last reset through the current endpoint;
all observed minimum-to-trigger delays are at most one update. The next saved
increment is the actual post-reset continuation, not an unreset counterfactual.
No extra counterfactual gradient probes were added.

The paper slow-only control has 20 resets. The dense slow-only control eventually
has 35, including 29 slow interruptions, but its first such interruption is at
update 18,188 with preceding objective about 1.95e-26. The nominal slow eigenspace
is not perfectly invariant under repeated rounded dense operations. This late
behavior is consistent with small other-mode components becoming relevant after
the original slow component contracts; it does not affect any requested target.
No very-small-loss ranking or exact-arithmetic conclusion is drawn from it.

## Figures and retained trajectories

Thin randomized curves show individual seeds; thicker curves show pointwise
**descriptive medians**, using past-only observations on common grids. Time panels
also retain all three timing repetitions per seed. No confidence bands are used.
The table statistics are per-path sustained hits, not crossings of these median
curves. The lower-left update-count panel is secondary; the lower-right panel
shows slow-coordinate loss in gradient units.

![Paper performance](../../../tmp/power_reset_spectral_comparison/main-19819633/paper-performance.png)

![Dense log performance](../../../tmp/power_reset_spectral_comparison/main-19819633/log-performance.png)

The mechanism panels show full/control slow loss, reset events, completed segment
lengths and signed global/slow/other-mode powers over work. The control curves
are mechanism evidence only.

![Paper B mechanism](../../../tmp/power_reset_spectral_comparison/main-19819633/paper-B-mechanism.png)

![Dense B mechanism](../../../tmp/power_reset_spectral_comparison/main-19819633/log-B-mechanism.png)

Every representative window is consecutive +/-3 updates around a predeclared
reset. These display the slow mode, four largest absolute modal contributors in
that window, and actual global power. Axis linear regions are display choices,
not trigger tolerances.

![Paper modal windows](../../../tmp/power_reset_spectral_comparison/main-19819633/paper-reset-windows.png)

![Dense modal windows](../../../tmp/power_reset_spectral_comparison/main-19819633/log-reset-windows.png)

Full signed-range [paper](../../../tmp/power_reset_spectral_comparison/main-19819633/paper-signed.png)
and [log](../../../tmp/power_reset_spectral_comparison/main-19819633/log-signed.png)
figures, PDF performance/mechanism figures and `plot_coordinates.npz` accompany
these images. Plot coordinate records include individual seeds, repetitions,
descriptive medians and positive-value masks; the full-resolution arrays remain
the numerical authority.

## Failures, censoring and scope

There were **zero optimizer failures**, **zero censored requested targets**, and
**zero dropped trajectories**. All 26 primary paths reached all three targets
within the common full work horizon. All raw scientific losses were strictly
positive; no claim depends on a signed numerical-floor excursion. Both slow-only
controls were retained but excluded from benchmark summaries and timing wins.
The offline path-label error described above was an infrastructure failure,
repaired and rerun from unchanged saved data; it is not an optimizer failure.

The new study tests correctly tuned baselines on two fixed, strongly convex,
100-dimensional quadratics. It does not newly test weak convexity, misspecified
alpha, nonquadratic objectives, other dimensions, rotations or initial states.
It establishes a spectrum-dependent finite-problem comparison, not a population
claim over problems. B and the specified AR_AGD remove supplied alpha from reset
control; this does not remove condition number from their possible complexity.

## Theoretical findings and unresolved counterexample

[THEORY.md](THEORY.md) separates exact derivations from observations. For a
symmetric PSD quadratic with s=lambda/L in [0,1], the normalized RHGD matrix M
satisfies I-M^T*M positive semidefinite. Zero-reset segments therefore retain an
endpoint objective no larger than their starting objective, despite possible
individual objective increases. That safety property does not establish a work rate.

A restricted result is proved for one active curvature with 0<s<=1/4 and inactive
cap: the first armed sign crossing takes at most pi/sqrt(2s)+1 updates, and retained
objective contracts by at least a factor bound s*(1-s)<=3/16 per completed segment.
This gives O(sqrt(kappa)*log(f_0/epsilon)) gradient work for that stated class.
It does not cover a general multimode initialization or an unrestricted fixed-cap
kappa limit.

The exact modal-weight recursion is E_i,next=E_i*r_i(K)^2, with the common stopping
length K determined by the weighted modal-power sum. A local two-mode example
proves that a fast mode can force a four-update reset while the slow mode descends.
For short fixed K, slow contraction is only 1-s*K*(K+1)+O_K(s^2) in objective,
so repeated interruptions can be costly. However, no general bound on their total
work is proved. An attempted persistent single-fast-mode construction requires
accounting for growing initial energy or a logarithmic transient and does not
supply a complexity counterexample. A normalized dense-spectral, cap-inactive
family violating an accelerated bound remains open. The finite 4.25x slow-mode
penalty here is not such an asymptotic counterexample.

## Decision, supported claims and exact next step

The frozen general-speed gate **fails on both spectra**: paper fails the 20%
gradient-saving condition; log fails both primary conditions and the secondary
work-regression conditions. B has a useful paper-spectrum advantage over this
AR_AGD, and improves original RHGD on both tested spectra. It is **spectrum-dependent**,
and the general-speed claim is unsupported by this controlled comparison.

Stop the general-speed direction. Do not change B, retune the cap, add a deadband,
smooth power, roll back, split modes, or run a rescue sweep. None was done here.
The narrower theoretical direction remains worthwhile because interference is
measurable and the exact segment recursion exposes the missing argument. The
specific optional next task is mathematical: prove an amortized work bound over
an explicitly stated spectral/amplitude class, or construct a normalized dense
family with a proved fast-triggered schedule and inactive cap that violates it.
That is a separate research question, with no new optimizer design implied.

## Reproducibility, cost and artifact map

CPU: Intel Xeon Gold 6248R at 3.00 GHz; node c672; Python 3.13.5, NumPy 2.5.3,
OpenBLAS 0.3.34.106.0 (SkylakeX/pthreads), one numerical thread. Full platform,
CPU affinity and library paths are in the main `metadata.json`. Main numerical
work is 5,600,000 gradients for 26 primary plus two controls, and 15,600,000 for
78 timing repetitions; the main has 16,200,106 objective evaluations. Validation,
warmup and the bounded probe are separate from those totals.

Actual probe/main allocation: 639 CPU-seconds, **0.1775 CPU-hours**, below the
.366667 ceiling. Scheduler process CPU usage totals 603.606 s. Main optimizer
seconds are 156.957 detailed and 356.190 minimal timing; serialization 89.867,
setup .454, complete main script 606.476. Offline hashing, validation, analysis
and plotting are outside optimizer time; analysis time is recorded separately.
Billed account SUs were not independently measured.

Important paths, relative to the repository root:

- `docs/studies/power_reset_spectral_comparison/{PROTOCOL,STATUS,THEORY,REPORT}.md`.
- `configs/studies/power_reset_spectral_comparison.json`.
- `src/power_reset_spectral_comparison/{core,evidence,experiment,analysis}.py`.
- `tests/studies/test_power_reset_spectral_comparison.py`.
- `scripts/run_power_reset_spectral_comparison.py` and the two
  `scripts/power_reset_spectral_{probe,main}.slurm` allocation scripts.
- `results/studies/power_reset_spectral_comparison/data/`: individual frozen arrays.
- That results parent's `freeze.json`, `prior_artifacts.json`, `validation.json`,
  `verification_commands.json`, `cost.json`, `scheduler_receipt.txt`, and final
  `artifact_manifest.json` supply provenance, checks and cost accounting.
- `results/studies/power_reset_spectral_comparison/probe-19819630/`: bounded probe.
- `results/studies/power_reset_spectral_comparison/main-19819633/`: metadata and all
  per-path NPZ arrays; `*-timing-{0,1,2}.npz` are minimal full-budget repetitions.
- Main `analysis/`: `audit.json`, `summary.json`, `target_records.json`,
  `targets.csv`, `comparison.md`, `*-modes.npz`, and `analysis_cost.json`.
- `tmp/power_reset_spectral_comparison/main-19819633/`: inspected figures, PDFs
  and `plot_coordinates.npz`. Temporary figures stay outside the numerical source.

Regeneration from retained numerical data:

```bash
source scripts/activate_env.sh
python scripts/run_power_reset_spectral_comparison.py audit --run results/studies/power_reset_spectral_comparison/main-19819633
python scripts/run_power_reset_spectral_comparison.py analyze --run results/studies/power_reset_spectral_comparison/main-19819633
python -m pytest tests/studies/test_power_reset_spectral_comparison.py tests/reproduction -q
ruff check .
ruff format --check .
```

`analyze` rewrites derived analysis/figures only. Numerical reproduction uses
`sbatch scripts/power_reset_spectral_probe.slurm` and, after its recorded estimate,
`sbatch scripts/power_reset_spectral_main.slurm`; each new job uses a unique output
path and refuses overwrite. The existing data freeze should be reused, not
regenerated. `prepare` intentionally refuses to overwrite the frozen preparation.
This study performed no additional optimizer comparisons or post-hoc trigger variants.

## Research verdict

- **Did B beat alpha-free adaptive-restart AGD on paper?** Yes: 15.5% fewer
  gradients and 49.7% less measured time at sustained 1e-8; below the required
  20% gradient-saving margin.
- **Did B beat it on dense log?** No: 70.8% more gradients and approximately equal
  measured time (1.6% higher median).
- **Did fair caching change the conclusion?** It reverses the dense CAGD gradient
  ranking and narrows paper CAGD differences. B-versus-AR_AGD is unchanged by
  caching; that comparison independently rejects the general-speed criterion.
- **Did multimode interference materially hurt B?** Yes: 25/25 accuracy-relevant
  dense resets truncate descending slow momentum; the matched slow-target work
  penalty is 4.25x, versus 1.027x on paper. Caps are inactive.
- **Generally faster, spectrum-dependent, or unsupported?** Spectrum-dependent;
  a general-speed claim is unsupported.
- **Is theory worthwhile if the speed claim fails?** Yes: a restricted scalar
  accelerated bound is available, while the multimode amortization/counterexample
  problem remains unresolved.
- **Proceed, redesign, or stop?** Stop the general-speed direction. Keep B frozen.
  A separately scoped theoretical analysis may proceed; no redesign is warranted
  by this study's authorization or decision rule.
