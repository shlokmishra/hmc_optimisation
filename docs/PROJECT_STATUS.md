# STAT 605: completed work and gaps

Audited November 12, 2026 against the 17-slide October 29 proposal and retained
source/configuration/result files. No historical benchmark was rerun in this
audit. Prior experiments were individual research completed before the course;
the group should distinguish reuse from its new contributions.

**Collaborator handoff updated November 19, 2026:** source is on
[GitHub](https://github.com/shlokmishra/hmc_optimisation). The
[group guide](../CONTRIBUTING.md) gives the proposed named workstreams and first
tasks. Compact exact inputs for both historical quadratic problems and the
synthetic regularized-logistic problem are now included in
`configs/stat605/fixtures/`, with source paths and hashes. They are problem inputs,
not historical trajectories. No new research benchmark was run for this handoff.

**Implementation update, November 23:** the constant-step quadratic fixed-time
RHGD control is implemented in `src/stat605/rhgd.py`, with a required integer reset
period, unchanged frozen numerical map, and explicit evaluation/failure counts.
The CLI provides a capped two-fixture smoke demonstration. A matched performance
comparison and the choice of benchmark periods remain to be done.

**RCM contribution reviewed, November 23:** Leonardo's `kin`, `mmd-r`, and
`mmd-dr` implementations, seeded Section 5.1 setup example, figure, and six-case
300-gradient pilot are integrated. The printed paper algorithms and restart
conventions were checked; the numerical core and submitted artifacts are retained.
This is a new seeded instance and three selected curves, not exact agreement with
the original published figure. See [the replication note](RCM_REPLICATION.md).

**AGD contribution reviewed, November 23:** Kwonsang's variable-theta scheme,
function/gradient/fixed restart modes, source-style example figures, and reported
mu-sensitivity study are integrated. The recurrence and restart definitions were
checked against the primary paper. Failure reporting, finite-state checks, input
provenance and allocation guards were strengthened without changing finite
trajectories in 24 bounded parity cases. The submitted laptop figures/tables are
carried forward; the full 100,000-update sweep was not rerun for this review.
See [the AGD summary](AGD_RESTART_SUMMARY.md). Integration with the common benchmark remains open.

**Spectral contribution reviewed, November 23:** Leo's configurable quadratic
harness, clustered spectra, controlled modal energies, saved-data reporting and
submitted 100D Grace pilot are integrated. It currently includes the five
historical methods, not the newly contributed AGD/RCM/fixed-time variants.
The submitted tables count 117 paths at 2,000 gradients each: 36/39 rescaled-common
paths sustain 1e-4, while 0/39 equal-energy paths reach it. These are bounded pilot
results, with eventual rankings on censored cases unresolved. Raw Grace traces
are not in this checkout; their shared location and manifest remain a handoff task.
See [the report and review scope](spectral/REPORT.md).

## What we already have

| Proposal commitment | Existing evidence | Status for the course |
| --- | --- | --- |
| Representative RHGD quadratic replication | Figure 1 exact and misspecified strong-convexity cases; weak quadratic extension | Substantially done, with the caveats below |
| Selected RCM replication | Three variants, correctness/budget checks, seed-605 Section 5.1 setup example and small shared-fixture pilot | Implemented for selected variants; full common comparison remains |
| Restarted AGD | Historical `core.ar_step` plus reviewed variable-theta function/gradient/fixed restart, source-style figures and reported sensitivity | Implemented; new variants need shared-harness adapters and a final common study |
| Fair AGD/CAGD/RHGD comparison | Two 100D fixed quadratics, equal distinct-gradient budgets and three timing repetitions | Done for this limited historical suite |
| Vary spectra at fixed dimension and endpoints | Linear, logarithmic and clustered spectra; common and controlled-energy starts; five-method 100D pilot | Implemented and piloted; broader method-family comparison remains |
| Test mu misspecification | Figure 1 exact mu versus supplied 0.01 on the same matrix | One overestimate done; controlled broader sensitivity remains |
| Stepsize sensitivity | Paper settings and historical variants exist | No unified course sensitivity experiment completed |
| Adaptive RHGD resets with unchanged state update | Frozen power-reset RHGD, strict arming and zero-velocity reset | One useful rule implemented and evaluated |
| Fixed-time RHGD reset control | Constant-step quadratic implementation, reset-boundary/parity/cost tests, capped smoke command | Implemented; matched performance comparison not run |
| Additional kinetic-energy/mean-dissipation RHGD resets | Discussed in proposal/history; selected RCM rules are separate methods | Not implemented for RHGD; defer before expanding scope if time is short |
| Logistic extension | Original RHGD logistic replays and earlier power-reset comparison | Reusable preliminary evidence; not a completed course-wide comparison |
| Final group report and presentation | Proposal PDF only | Still to do |

## RHGD reproduction that is actually complete

| Setting | Saved run | Iterations | Exact numeric/coordinate array comparisons |
| --- | --- | ---: | ---: |
| Figure 1-left, exact mu | 19769000 | 1,000,000 | 24 |
| Figure 1-middle, supplied mu=0.01 | 19770301 | 1,000,000 | 25 |
| Figure 1-right, weak extension | 19772099 | 1,000,000 | 24 |
| Figure 2-left, regularized logistic | 19768992 | 1,000 | 33 |
| Figure 2-right, unregularized logistic | 19734521 | 200 | 26 |

The [portable parity receipts](evidence/README.md) copy the original saved checks.
Agreement is against separate direct execution of the authors' code in the same
environment, not against unavailable historical published arrays. Figure 1-right
extends the notebook's 10,000-step default at the original user's request; it is
not an untouched default replay. Figures 3–7 were not run and need not all be
completed for the course's representative-replication scope.

Randomized curves use five algorithm seeds on one generated problem, not five
independent datasets. Weak-quadratic log-band NaNs near zero reflect signed
roundoff and the source statistic; they are not evidence of divergent iterates.
The original logistic gap/reference conventions also need qualification.

## The most useful existing result

The fair spectral study counted distinct evaluations uniformly, including cached
CAGD duplicates. At a sustained objective-gap target of 1e-8:

| Spectrum | Original RHGD median | Power-reset RHGD | Gradient-restart AGD | AGD | CAGD median |
| --- | ---: | ---: | ---: | ---: | ---: |
| Paper linear | 61,274 | 10,000 | 11,832 | 16,750 | 16,747 |
| Dense logarithmic | 127,424 | 43,016 | 25,188 | 23,771 | 24,376 |

Values are gradient evaluations. The full [saved summary](evidence/spectral-summary.json)
also contains timing and other targets. Power-reset RHGD failed the predeclared
20% work-and-time improvement gate against restarted AGD on both spectra.
Power reset substantially reduces gradient work relative to original RHGD on
these two fixed problems. Its advantage over restarted AGD depends on the spectrum;
it is not a general winner.
These two matrices support the proposal's motivation for testing spectra; they
do not isolate every effect of initial modal energies or establish a rate theorem.

## What is intentionally outside the course core

The early implicit/discrete-gradient pilot, A/C reset candidates, geometry and
subspace acquisition, GPU audits, multiproposal/global-search studies, advisor
handoffs, and restricted two-mode proof are archived locally. Those branches
contain useful negative evidence, but implementing them is not required by the
proposal. Do not treat the old theory as a general guarantee for a new rule.

All four streams now have source contributions. Next integrate the newly
contributed method variants into the shared harness, including variable rejected
work for RCM, freeze a bounded comparison, share its raw artifacts, and assemble
the report/slides. See the [ordered plan](EXPERIMENT_PLAN.md).
