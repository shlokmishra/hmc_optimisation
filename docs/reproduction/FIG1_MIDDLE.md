# Figure 1-middle: full author-code parity passed

On 2026-09-16, job **19770301** completed the misspecified-strong-convexity panel
and a separate direct-author execution. **All 25 retained numeric and plotted
coordinate arrays match exactly**, including dtype and shape; scalar metadata
also matches. This covers 17 numeric arrays and eight plotted x/y arrays.
Each randomized loss array has shape 5×1,000,000. Author numerical function
bodies were unchanged in both full executions.

![Canonical full-range Figure 1-middle](../../results/reproduction/fig1-middle-19770301/figure-01.png)

## Numerical outcome and unchanged problem

There were no captured warnings or nonfinite numeric values. The matrix `A`,
initial point `x0`, and **every entry of the million-step GD trace** are exactly
equal to Figure 1-left. Extreme matrix eigenvalues are approximately
5.0000000035211874e-5 and 500. Thus true α remains 5×10⁻⁵, while the algorithms
receive α̂=0.01. The metadata variable `alpha` denotes the latter loop parameter;
`validation.json` records both quantities explicitly.

Final plotted losses at k=999,999 (means of five for CAGD and RHGD):

| Method | Loss |
| --- | ---: |
| GD | 8.2461281481005027e-06 |
| AGD | 1.7277818431696507e-15 |
| CAGD | 1.7277264169873314e-15 |
| RHGD (ours) | 4.5593399585245947e-25 |

## Settings and branch selection

The selected experiment is manifest case `fig1-middle`, pinned author commit
`37962b3074a5c9c6248ef062ffa665a2177a1301`, notebook cell 1 (zero-based):

- Dimension 100; L=500, κ=10⁷, true α=L/κ=5×10⁻⁵.
- Misspecified algorithm input α̂=0.01 (200 times the true α), passed to AGD,
  CAGD, and RHGD exactly where the author cell uses its loop variable `alpha`.
  GD has no strong-convexity argument. The matrix remains determined by κ and L.
- One million iterations, five randomized runs each for CAGD and RHGD, and
  deterministic GD/AGD once. η=0.002, h=√0.002.
- Data seed 42; replicate seeds 0–4. Each replicate runs CAGD then RHGD on the
  same RNG, preserving CAGD's N+1 exponential draws and subsequent RNG state.

The author cell loops over `alphas = [0.01, 0.1, 1]`. The replay selects `[0.01]`
for this panel. The direct verifier was narrowly extended to make that selection
independently by text replacement, without the runner's AST transformer. It only
allows one alpha already present in cell 1; other numerical overrides remain
unsupported. This is experiment selection, not a change to optimizer semantics.

A regression check executes the original loop through its first `plt.show` and
compares it with the selected branch at short length. Numeric outputs and scalars
agree exactly (only the selection list itself differs). All 18 reproduction tests
passed, as did Ruff lint and formatting checks. Function ASTs remain unchanged.
The two full executions use separate Python processes. The only other source
adaptation removes the retina-display import/call; `plt.show` captures artifacts.

## Rendering and historical comparison

`figure-01.png` and `figure-01.pdf` are the **canonical full-range renderings**,
using the complete saved author curves and their natural notebook plotting range.
They are not cropped to match the paper. `artifact_roles.json` identifies canonical
outputs, direct-author references, and historical references separately.

The saved notebook image for α̂=0.01 and the printed Figure 1-middle on page 8
are retained. The published panel shows losses down to roughly 10⁻¹⁴ and places
the legend at the upper right; the notebook's full-range reference extends lower
and places its legend at the lower left. Rendering size/tick placement also differ.
These presentation differences are separate from source parity.

Visual inspection finds broadly consistent initial transients, the shared slow
component near 10⁻⁵, and subsequent RHGD decay ahead of AGD/CAGD under this
misspecified parameter. This is a qualitative comparison of this panel.

Historical numerical arrays are unavailable and the reference images have not been
quantitatively digitized. Visual consistency is not exact numerical agreement with
the historical figure, nor does source parity prove algorithm correctness or a
general optimization speed advantage.

Figure 1-left was preserved byte-for-byte against its saved artifact hashes,
including the full-range canonical PNG/PDF and the separately labeled display-only
`paper_window.*` diagnostic views. No Figure 1-left rendering was overwritten.

## Allocation and scope

The allocation requests one CPU, 4 GB, and 30 minutes (0.5 allocated CPU-hour ceiling).
The preceding Figure 1-left run provided the runtime and memory estimate, so no
new short timing probe was needed. This job runs only the 0.01 branch and its
independent verification. It does not run the 0.1 or 1 branches or Figure 1-right.
Recorded wall times include rendering, compression, I/O, and verification; they are
not optimizer benchmark timings. Actual billed SUs were not independently measured.

**Scope stop:** report this panel and stop before Figure 1-right.

## Accounting and evidence

Job **19770301** completed with state `COMPLETED`, exit `0:0`, on **c760**, account
`132674288899`, in **8m40s = 520 seconds = 0.14444 allocated CPU-hours**.
Replay/capture took 233.87 s; direct-author execution/comparison took 222.31 s.
Slurm's batch step reports sampled peak RSS of 892,876 KiB (about 872 MiB).

[All run artifacts](../../results/reproduction/fig1-middle-19770301/) include:

- [Canonical full-range PNG](../../results/reproduction/fig1-middle-19770301/figure-01.png) and [PDF](../../results/reproduction/fig1-middle-19770301/figure-01.pdf).
- [Exact parity](../../results/reproduction/fig1-middle-19770301/author_parity.json), [metadata](../../results/reproduction/fig1-middle-19770301/metadata.json), and [additional validation](../../results/reproduction/fig1-middle-19770301/validation.json).
- [Accounting](../../results/reproduction/fig1-middle-19770301/accounting.json), raw scheduler receipt, stdout/stderr, dependency pins, and preflight test log.
- [Saved notebook reference](../../results/reproduction/fig1-middle-19770301/author_saved_notebook.png), [published panel detail](../../results/reproduction/fig1-middle-19770301/paper_panel_detail.png), and full paper page 8.
- Raw NPZ arrays, all plotting coordinates, original/executed cell source,
  independent direct-author arrays/image, source manifest, submission details,
  [artifact roles](../../results/reproduction/fig1-middle-19770301/artifact_roles.json), and hashes.
- [Submission snapshots](../../results/reproduction/submissions/19770301/) include
  the exact verifier and branch-selection regression test used for this run.

**Result:** four of 15 panels now pass full source parity. Eleven remain. Work
stops here; Figure 1-right and the other alpha branches were not submitted or run.
