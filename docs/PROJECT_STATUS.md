# STAT 605: completed work and gaps

Audited November 12, 2026 against the 17-slide October 29 proposal and retained
source/configuration/result files. No historical benchmark was rerun in this
audit. Prior experiments were individual research completed before the course;
the group should distinguish reuse from its new contributions.

## What we already have

| Proposal commitment | Existing evidence | Status for the course |
| --- | --- | --- |
| Representative RHGD quadratic replication | Figure 1 exact and misspecified strong-convexity cases; weak quadratic extension | Substantially done, with the caveats below |
| Selected RCM replication | Proposal reviews the paper, but no RCM experiment implementation was found in the project source inventory | Still to do |
| Restarted AGD | Tested gradient-restart, alpha-free accelerated recurrence in `core.ar_step` | Implemented; function-increase restart and selected source replication remain |
| Fair AGD/CAGD/RHGD comparison | Two 100D fixed quadratics, equal distinct-gradient budgets and three timing repetitions | Done for this limited historical suite |
| Vary spectra at fixed dimension and endpoints | Linear and logarithmic spectra with d=100, mu=5e-5, L=500 | Partial: clustered spectra and controlled modal energies remain |
| Test mu misspecification | Figure 1 exact mu versus supplied 0.01 on the same matrix | One overestimate done; controlled broader sensitivity remains |
| Stepsize sensitivity | Paper settings and historical variants exist | No unified course sensitivity experiment completed |
| Adaptive RHGD resets with unchanged state update | Frozen power-reset RHGD, strict arming and zero-velocity reset | One useful rule implemented and evaluated |
| Fixed-time, kinetic-energy, normalized/mean-dissipation resets | Discussed in proposal/history | Need precise discrete definitions, implementation, tests, and comparison |
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

| Spectrum | Power-reset RHGD | Gradient-restart AGD | AGD | CAGD median |
| --- | ---: | ---: | ---: | ---: |
| Paper linear | 10,000 | 11,832 | 16,750 | 16,747 |
| Dense logarithmic | 43,016 | 25,188 | 23,771 | 24,376 |

Values are gradient evaluations. The full [saved summary](evidence/spectral-summary.json)
also contains timing and other targets. Power-reset RHGD failed the predeclared
20% work-and-time improvement gate against restarted AGD on both spectra.
It improves the original RHGD in selected settings but is not a general winner.
These two matrices support the proposal's motivation for testing spectra; they
do not isolate every effect of initial modal energies or establish a rate theorem.

## What is intentionally outside the course core

The early implicit/discrete-gradient pilot, A/C reset candidates, geometry and
subspace acquisition, GPU audits, multiproposal/global-search studies, advisor
handoffs, and restricted two-mode proof are archived locally. Those branches
contain useful negative evidence, but implementing them is not required by the
proposal. Do not treat the old theory as a general guarantee for a new rule.

The smallest next task is **source-check and reproduce one RCM quadratic example**,
with a hand-computed symplectic-Euler step and an explicit restart convention.
This closes the largest missing method family before building a broad benchmark.
See the [ordered plan](EXPERIMENT_PLAN.md).
