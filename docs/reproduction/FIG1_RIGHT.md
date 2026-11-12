# Figure 1-right: requested million-step run passes exact source parity

On 2026-09-17, job **19772099** completed the weakly convex quadratic experiment
with intended α=0, L=500, one million iterations and five randomized runs.
**All 24 numeric/coordinate arrays match independent direct-author execution
exactly**, including dtype, shape, and matching NaN/Inf positions. Scalar metadata
also matches. Author function bodies remain unchanged.

**Two qualifications matter:** the requested million iterations extend the
notebook's 10,000-step default, and the unchanged author log-band calculation
produces NaN/Inf near zero on this environment. Source parity passed at the
requested settings; this is not a claim of exact historical-figure reproduction.

[Canonical author rendering](../../results/reproduction/fig1-right-19772099/figure-01.png)
retains the entire million-step x range and its distorted automatic y range.
The separately labeled diagnostic below shows signed saved losses without bands;
it changes only the display and does not replace the canonical PNG/PDF.

![Display-only signed-loss diagnostic](../../results/reproduction/fig1-right-19772099/signed_loss_diagnostic.png)

## Numerical outcome and band failure

Every retained raw loss and plotted mean is finite. Near the floor, many losses
are slightly negative; the smallest recorded loss is approximately −7.63×10⁻¹⁵.
Final plotted losses at k=999,999 are:

| Method | Recorded loss |
| --- | ---: |
| GD | −3.135674987102784e−15 |
| AGD | 3.7782737482439685e−16 |
| CAGD, mean of five | −1.5929730338310294e−15 |
| RHGD, mean of five | −5.892911774053604e−16 |

These values are near the numerical floor, not meaningful negative optimality
certificates or evidence for ranking methods there.

**Verified failure mechanism:** the author computes `log10(mean_loss)` without
clipping. Negative means yield NaN in both uncertainty bounds. Validation checks
that the NaN masks coincide exactly with negative means. The delta-method upper
bound also overflows on some positive, near-zero means.

| Randomized method | First negative mean, k | NaN entries in each bound | Additional Inf entries in upper bound |
| --- | ---: | ---: | ---: |
| CAGD | 2,738 | 995,231 | 15 |
| RHGD | 998 | 997,148 | 14 |

This totals **3,984,787 nonfinite entries across the four bound arrays**. Raw
losses/means remain finite. Both executions capture the same warnings:
`invalid value encountered in log10`, `overflow encountered in power`,
`overflow encountered in exp`, and the slow automatic-legend warning.
The unchanged canonical rendering displays approximately y=1 to 10 with tall
band artifacts; it is not a useful view of convergence, but is retained faithfully.

**Working hypothesis:** floating-point matrix construction and cancellation in
`0.5 * x @ A @ x` near the intended nullspace explain the tiny signed residuals.
The precise contribution of construction error versus objective-evaluation error
has not been isolated. A numerical eigenvalue estimate near zero cannot establish
its sign reliably at this scale. No matrix projection, loss clipping, precision
change, or algorithm correction was applied.

**Workaround, display-only and verified:** `signed_loss_diagnostic.*` plots all
saved mean coordinates on a signed logarithmic axis (linear threshold 10⁻¹⁴) and
omits invalid bands. Its source and display settings are retained. This exposes
the near-zero floor; it does not repair the author statistic. Repeating the same
run without changing numerical conditions will not resolve that statistic's
failure. Any corrected statistic or high-precision audit belongs in a separate
study with a new identity.

Visually, the signed diagnostic retains the broad initial decay and near-zero
plateau seen in the paper/notebook. RHGD transients differ, consistent with the
explicit iteration-dependent RNG change. Historical references show a positive
floor near 10⁻¹⁵, whereas this run has signed residuals and invalid bands. These
differences are documented separately from exact source parity, and their full
historical cause remains unverified.

**Measured allocation:** 558 seconds (9m18s), **0.155 allocated CPU-hours**,
node c262, account 132674288899, scheduler `COMPLETED`, exit `0:0`. Sampled batch
peak RSS was 728,284 KiB (about 711 MiB). Replay/capture took 264.99 seconds;
direct-author execution/comparison took 275.73 seconds.

## Settings and fidelity scope

The requested experiment uses dimension 100, intended α=0, L=500, **1,000,000
iterations**, and five randomized runs each for CAGD and RHGD. GD and AGD run once.
All methods use the author's weak-quadratic implementations from cell 2 (zero-based)
of commit `37962b3074a5c9c6248ef062ffa665a2177a1301`.

**The requested iteration count differs from the pinned notebook:** cell 2 defaults
to 10,000 iterations, and the published Figure 1-right also displays through 10⁴.
The paper panel and saved notebook image both identify L=500. We followed the
user's explicit million-iteration request, recording `num_iters=1000000` and
`mode=user_requested_parameters` in the manifest and run metadata. This is a
million-step extension of the Figure 1-right source, not an untouched-default
10,000-step replay. Exact source parity refers to the explicitly recorded settings.

Stepsizes are unchanged: GD/AGD/CAGD η=0.002=1/L and RHGD h=√0.002=1/√L.
These are the L=500 settings, not the smaller Table 3 steps for L=5,000/50,000.
The weak variants have no positive strong-convexity parameter to misspecify.
The matrix is generated with eigenvalues linearly spaced from zero to 500 and
symmetrized exactly as in the author cell, without projecting away roundoff.

Data generation preserves the legacy seed 42 and draw order, including the weak
matrix generator's internal seed reset. Each replicate uses seed 0–4, runs CAGD
first and RHGD second on the same RNG, and retains the author's pre-update losses
and delta-method statistical bands. CAGD pre-draws N+1 exponential variables.
Consequently changing N changes RHGD's subsequent random stream: the first 10,000
points of the million-step run cannot stand in for the notebook's default RHGD run.

The replay modifies the top-level iteration assignment using its existing AST
adapter. The direct verifier independently replaces exactly the pinned cell-2
assignment as text and rejects unexpected source or unsupported overrides. Both
paths retain every author numerical function body; function AST equality is
checked. Retina-display setup is removed and `plt.show` is intercepted for capture.
The two full executions run in separate processes with one numerical thread.

All **19 reproduction tests** passed, covering unchanged function ASTs, short
numeric parity for all seven cells, supported selections/overrides, fail-closed
source preparation, output protection and Slurm requirements. Ruff lint and
format checks passed. No environment dependencies were changed.

## Artifact interpretation and historical comparison

`figure-01.png` and `figure-01.pdf` retain the **canonical full-range author
rendering**, including the complete million-step arrays. No historical-axis crop
replaces them. `artifact_roles.json` distinguishes canonical output, direct-author
reference and historical reference images. The earlier Figure 1-left and middle
artifact inventories remain byte-for-byte hash-identical, including the left
panel's separately labeled `paper_window.*` diagnostics.

The saved notebook output and published Figure 1-right on page 8 are retained as
references. Both historical references show the original 10,000-step extent and
terminal loss near 10⁻¹⁵. Historical raw arrays and an original environment lock
are unavailable; we have not digitized the references. A visual comparison cannot
establish historical bitwise agreement. The documented iteration/RNG difference
also prevents treating the million-step extension as the default historical run.

## Evidence and accounting

Run directory: `results/reproduction/fig1-right-19772099/`.

- [Canonical PNG](../../results/reproduction/fig1-right-19772099/figure-01.png) and [PDF](../../results/reproduction/fig1-right-19772099/figure-01.pdf).
- [Exact parity report](../../results/reproduction/fig1-right-19772099/author_parity.json), [run metadata](../../results/reproduction/fig1-right-19772099/metadata.json), and [validation](../../results/reproduction/fig1-right-19772099/validation.json).
- [Raw numerical arrays](../../results/reproduction/fig1-right-19772099/figure-01-arrays.npz) and [plotted coordinates](../../results/reproduction/fig1-right-19772099/figure-01-curves.npz), with independent direct-author arrays and reference image.
- [Accounting](../../results/reproduction/fig1-right-19772099/accounting.json), scheduler receipt, logs, dependency pins, preflight tests, source/setting snapshots and artifact hashes.
- [Notebook reference](../../results/reproduction/fig1-right-19772099/author_saved_notebook.png), [published panel](../../results/reproduction/fig1-right-19772099/paper_panel_detail.png), full paper page 8 and [artifact roles](../../results/reproduction/fig1-right-19772099/artifact_roles.json).
- [Submission snapshot](../../results/reproduction/submissions/19772099/) records the exact code, account, prior runtime basis and iteration override.

The bounded allocation requests one CPU, 4 GB and 30 minutes: at most 0.5 allocated
CPU-hours; the scheduler also quoted 0.5 requested SUs. Actual billed SUs were not
independently measured. Wall times include rendering, compression and I/O, and are
not optimizer benchmarking results.

**Scope stop:** Figure 1-right only. Figures 3–7 were not submitted or run.
Four earlier panels have full source parity at their established paper settings;
the fifth source-parity study is this explicitly requested million-step extension.
The default 10,000-step Figure 1-right replay remains separately unverified.
