# Figure 2-left: full author-code parity passed

On 2026-09-16, job **19768992** reproduced the strongly convex adaptive logistic
panel at full notebook settings and passed a separate direct author-cell replay.
**All 33 retained numeric and plotted-coordinate arrays agree exactly**, including
dtype and shape. Scalar metadata also agrees. No numerical implementation or
instrumentation code was changed for this run.

![Reproduced Figure 2-left](../../results/reproduction/fig2-left-19768992/figure-01.png)

## Settings and fidelity

- Source: commit `37962b3074a5c9c6248ef062ffa665a2177a1301`, notebook cell 3
  (zero-based), manifest case `fig2-left` with no numerical overrides.
- Dimension 100, 500 observations, α=10⁻⁴, 1,000 iterations, initial η=h=1.
- Legacy data seed 42; randomized replicate seeds 0–4. Within each replicate the
  same generator runs RHGD c=2, RHGD c=1, then CAGD, in the author's order.
- Five replicates for each randomized method; deterministic GD and AGD once.
  Raw randomized loss arrays each have shape 5×1,000.
- Existing display-only removal of `set_matplotlib_formats` and capture of
  `plt.show` were retained. Author function ASTs and submission source hashes
  were checked unchanged. The independent verifier bypassed the AST transformer.
- The 33 comparisons comprise 23 retained numeric arrays and 10 plotted x/y
  coordinate arrays. Both executions used the same environment and one BLAS thread.

## Results and limits

There were no captured warnings or nonfinite numeric values. The author estimates
f★ from the minimum across compared traces; here it was **0.020236446186274216**.
Randomized shifted losses retain the author's 10⁻²⁰ clipping and first-entry
overwrite convention. These are not independently certified optimality gaps.

Final plotted values (pre-update losses at k=999, using the author's reference):

| Method | Final plotted value |
| --- | ---: |
| GD | 2.42861286636753e-16 |
| AGD | 2.498001805406602e-16 |
| CAGD mean | 2.4980018054066023e-17 |
| RHGD c=2 mean | 7.563394355258879e-17 |
| RHGD c=1 mean | 4.85722573273506e-17 |

Visual inspection shows broadly consistent convergence shapes against the saved
notebook PNG and Figure 2-left on paper page 9. However, the saved notebook's
terminal plateaus and ordering differ near 10⁻¹⁶; rendering sizes/ticks also differ.
The paper panel does not show the full terminal range. Exact source parity on this
environment is verified; exact numerical reproduction of the historical figure is
**not established**. Original numerical reference arrays are unavailable.

Floating-point/library differences and cancellation in trace-derived gaps are
plausible explanations for the terminal discrepancy, **not a verified diagnosis**.
The original environment and fresh-run history of the saved notebook outputs are
unknown. No algorithm or plotting correction was applied to force agreement.

## Accounting and artifacts

The job completed with exit `0:0` on **c575**, account `132674288899`, partition
`short`. Request: one CPU, 2 GB, five minutes. Elapsed allocation: **29 seconds**,
or **0.00806 allocated CPU-hours**, below the 0.08333 CPU-hour ceiling. Actual billed
SUs were not independently measured. Replay/capture took 11.72 seconds and direct
verification 4.27 seconds; these include I/O/rendering and are not optimizer timings.

The [run directory](../../results/reproduction/fig2-left-19768992/) contains:

- [PNG](../../results/reproduction/fig2-left-19768992/figure-01.png) and [PDF](../../results/reproduction/fig2-left-19768992/figure-01.pdf).
- [Parity report](../../results/reproduction/fig2-left-19768992/author_parity.json), [metadata](../../results/reproduction/fig2-left-19768992/metadata.json), and [additional validation](../../results/reproduction/fig2-left-19768992/validation.json).
- [Accounting](../../results/reproduction/fig2-left-19768992/accounting.json), raw scheduler receipt, and stdout/stderr.
- Original/executed cell source, raw NPZ arrays, plotted coordinates, direct-author
  arrays/image, source manifest, dependency pins, saved notebook PNG, paper page,
  submission details, and artifact hashes.

Both Figure 2 panels now pass full source parity. Thirteen other panels remain
pending; this run does not resolve dense-quadratic costs or validate new methods.
