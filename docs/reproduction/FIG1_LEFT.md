# Figure 1-left: full author-code parity passed

On 2026-09-16, job **19769000** completed the full strongly convex quadratic
experiment and a separate direct-author execution. **All 24 retained numeric and
plotted-coordinate arrays matched exactly**, including dtype and shape; scalar
metadata also matched. This comprises 16 numeric arrays and eight plotted x/y
arrays. Both randomized loss arrays have five runs of one million iterations.
Author function ASTs and all submission source hashes were verified unchanged.

![Full reproduced panel](../../results/reproduction/fig1-left-19769000/figure-01.png)

## Numerical outcome

No captured numeric arrays contain nonfinite values. Both executions recorded
only the Matplotlib performance warning `Creating legend with loc="best" can be
slow with large amounts of data.` It was retained, not silenced or corrected.
The independently checked extreme matrix eigenvalues were approximately
5.0000000035211874e-5 and 500, consistent with the requested spectrum.

Final plotted losses at k=999,999 (means of five for CAGD and RHGD):

| Method | Loss |
| --- | ---: |
| GD | 8.2461281481005027e-06 |
| AGD | 1.9531600084962648e-275 |
| CAGD | 7.4543658689756728e-271 |
| RHGD (ours) | 5.5980222182521219e-147 |

## Settings and fidelity

The run uses pinned RHGD commit `37962b3074a5c9c6248ef062ffa665a2177a1301`,
notebook cell 0 (zero-based), manifest case `fig1-left`, with **no numerical
parameter overrides** in either full execution:

- Dimension 100; dense QR-generated quadratic matrix with linearly spaced spectrum.
- L=500, κ=10⁷, exact α=L/κ=5×10⁻⁵.
- η=1/L=0.002 for GD/AGD/CAGD; h=√η for RHGD.
- 1,000,000 iterations; five randomized runs for CAGD and RHGD; GD and AGD once.
- Legacy data seed 42; replicate seeds 0–4. Each replicate runs CAGD, then RHGD
  on the same generator. CAGD's N+1 exponential draws and all subsequent random
  draws retain their original ordering.

The established runner removes the retina-display import/call and captures
`plt.show`. Its function ASTs remain unchanged. The separate direct-author
execution bypasses the AST transformer and executes the original source text
with only the same display lines removed. No solver, objective, stopping rule,
random stream, statistic, or numerical implementation was changed or optimized.
Losses are recorded before each update; the last plotted index is k=999,999.
Raw randomized loss arrays are each 5×1,000,000. All full plotted coordinates
and statistical envelopes are retained.

## Historical figure comparison

The full author-style plot extends to 10⁶ iterations and extremely small losses,
as does the PNG saved in the authors' notebook. The published panel on paper
page 8 instead displays a restricted range, with iteration ticks through 10⁵
and a lower loss limit of about 10⁻¹⁴. These are different presentations of the
experiment; matching axis appearance alone would not establish numerical parity.

The additional `paper_window.png` is a **display-only view of saved full-run
arrays**, with x limits [0.55, 180000] and y limits [10⁻¹⁴, 10⁴]. It retains all
points in that interval and performs no optimization rerun, averaging change, or
retuning. Its settings are saved in `paper_window.json`. The original full PNG,
PDF, raw arrays, and coordinates remain intact.

Visual inspection shows broadly consistent convergence shapes and method ordering
against the notebook and paper: the initial transient, GD's slow component near
10⁻⁵, later AGD/CAGD decay, and slower irregular RHGD decay. Tick spacing and
rendering differ. Historical raw curve arrays are unavailable, and the reference
images have not been quantitatively digitized, so **exact historical numerical
agreement is unverified**. Exact same-environment source parity is a separate,
stronger check of our replay path, not proof of the underlying algorithm.

## Runtime probe and scope

A separate 10,000-iteration timing probe ran first within this same allocation.
Its author function bodies were unchanged, but its shortened iteration setting
means it is neither a paper result nor a prefix of the full run. It took 4.19 s;
linear extrapolation for two million-iteration executions was 838.58 s, excluding
full-size artifact saves. This passed the 1,200-second gate within the 1,800-second
allocation. Both subsequent full executions ran in fresh Python processes.

The job requested one CPU and 8 GB to accommodate full million-point arrays and
plots. The 30-minute limit capped allocated CPU time at 0.5 core-hours. Optimizer
speed claims should not use these wall times: they include plotting, compression,
I/O, and validation. Actual billed SUs were not independently measured.

**Scope stop:** Figure 1-left only. Figure 1-middle was not submitted or run.

## Accounting and evidence

Job **19769000** completed with state `COMPLETED`, exit `0:0`, on **c395**, account
`132674288899`. The complete allocation, including the probe and both full
executions, lasted **10m39s = 639 seconds = 0.1775 allocated CPU-hours**.
Replay plus capture took 313.29 s; direct-author execution/comparison took 280.31 s.
Slurm's batch step reports peak RSS of 1,005,152 KiB (about 982 MiB); this is the
scheduler's sampled memory statistic. The 8 GB request was conservative.

[All run artifacts](../../results/reproduction/fig1-left-19769000/) include:

- [Full PNG](../../results/reproduction/fig1-left-19769000/figure-01.png) and [PDF](../../results/reproduction/fig1-left-19769000/figure-01.pdf).
- [Paper-range view](../../results/reproduction/fig1-left-19769000/paper_window.png), [saved notebook reference](../../results/reproduction/fig1-left-19769000/author_saved_notebook.png), and [published panel detail](../../results/reproduction/fig1-left-19769000/paper_panel_detail.png).
- [Parity report](../../results/reproduction/fig1-left-19769000/author_parity.json), [metadata](../../results/reproduction/fig1-left-19769000/metadata.json), and [additional validation](../../results/reproduction/fig1-left-19769000/validation.json).
- [Accounting](../../results/reproduction/fig1-left-19769000/accounting.json), raw scheduler receipt, stdout/stderr, and [cost probe](../../results/reproduction/fig1-left-19769000/cost_probe.json).
- Original/executed source, numerical arrays, plotted coordinates, direct-author
  reference arrays/image, source manifest, dependency pins, submission record,
  published page 8, and artifact hashes. Submission script snapshots are in
  [the submission directory](../../results/reproduction/submissions/19769000/).

**Result:** full Figure 1-left source parity passes. Three of 15 panels now pass
full source parity; twelve remain. Work stops here before Figure 1-middle, as requested.
