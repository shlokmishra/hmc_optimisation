# Reproduced results

Start with the plot below and the [findings report](FINDINGS.md).
For scientific interpretation across all five requested main-paper panels, read
the [main-paper synthesis](MAIN_PAPER_SYNTHESIS.md).
**Five studies pass exact source parity:** four established paper-setting panels
and the requested million-step Figure 1-right extension. Its notebook default is
10,000 iterations; default-run historical agreement remains unverified. Figures
3–7 have not begun. Smoke checks are not paper results.

## Figure 1-right: weak quadratic, requested million-step extension

L=500, intended α=0, five randomized runs; all 24 retained numeric/coordinate
arrays match direct execution at the explicitly overridden iteration count.
The author log bands contain NaN/Inf near zero. Preserve the distorted canonical
rendering and use the separately labeled signed diagnostic to inspect convergence.

[Findings and evidence](FIG1_RIGHT.md) ·
[Canonical PNG](../../results/reproduction/fig1-right-19772099/figure-01.png) ·
[Canonical PDF](../../results/reproduction/fig1-right-19772099/figure-01.pdf) ·
[Signed-loss diagnostic](../../results/reproduction/fig1-right-19772099/signed_loss_diagnostic.png).

## Figure 1-middle: misspecified strong-convexity parameter

![Canonical full-range Figure 1-middle](../../results/reproduction/fig1-middle-19770301/figure-01.png)

Same quadratic as Figure 1-left, true α=5×10⁻⁵, but α̂=0.01 is supplied to the
algorithms. One million iterations and five randomized runs; all 25 retained
numeric/coordinate arrays match direct author execution exactly.
[Findings and evidence](FIG1_MIDDLE.md) ·
[Canonical PDF](../../results/reproduction/fig1-middle-19770301/figure-01.pdf).

## Figure 1-left: strongly convex quadratic

![Paper-range view of the full run](../../results/reproduction/fig1-left-19769000/paper_window.png)

L=500, κ=10⁷, exact α=5×10⁻⁵, one million iterations, five randomized runs. All
24 retained numeric/coordinate arrays match direct author execution exactly.
The image above only changes the display range of saved full-run data.
[Findings and evidence](FIG1_LEFT.md) ·
[Original full-range PNG](../../results/reproduction/fig1-left-19769000/figure-01.png) ·
[PDF](../../results/reproduction/fig1-left-19769000/figure-01.pdf).

## Figure 2-left: strongly convex adaptive logistic regression

![Full reproduced left panel](../../results/reproduction/fig2-left-19768992/figure-01.png)

1,000 iterations, α=10⁻⁴, five replicates per randomized method, both RHGD refresh
rates. All 33 retained numeric/coordinate arrays match direct author execution.
See [settings, comparison caveats, and evidence](FIG2_LEFT.md).
[PDF](../../results/reproduction/fig2-left-19768992/figure-01.pdf) ·
[Raw artifacts](../../results/reproduction/fig2-left-19768992/).

## Figure 2-right: adaptive logistic regression

![Full reproduced panel](../../results/reproduction/fig2-right-19734521/figure-01.png)

200 iterations, five randomized replicates, 100 dimensions, 500 observations.
All 26 retained numeric and plotted-coordinate arrays matched direct execution
of the authors' code exactly on the same environment. Job 19734521 completed
in 29 seconds, using 0.00806 allocated CPU-hours.

| What to inspect | File |
| --- | --- |
| Main conclusion and limitations | [Findings](FINDINGS.md) |
| Full-size plot | [PNG](../../results/reproduction/fig2-right-19734521/figure-01.png) · [PDF](../../results/reproduction/fig2-right-19734521/figure-01.pdf) |
| Authors' saved notebook plot | [Reference PNG](../../results/reproduction/fig2-right-19734521/author_saved_notebook.png) |
| Published Figure 2 | [Paper page 9](../../results/reproduction/fig2-right-19734521/paper_page9.png) |
| Exact array comparison | [Parity report](../../results/reproduction/fig2-right-19734521/author_parity.json) |
| Raw data, losses, and statistical bands | [NPZ arrays](../../results/reproduction/fig2-right-19734521/figure-01-arrays.npz) |
| Plotted line coordinates | [NPZ curves](../../results/reproduction/fig2-right-19734521/figure-01-curves.npz) |
| Settings, versions, and warnings | [Metadata](../../results/reproduction/fig2-right-19734521/metadata.json) |
| Job cost | [Accounting](../../results/reproduction/fig2-right-19734521/accounting.json) |

The reference figures look consistent with the replay. Exact agreement with the
authors' original numerical arrays is unverified: those arrays are not provided.
See the findings for the raw-loss versus optimality-gap labeling caveat.

## Continue the research

- [Status](STATUS.md): what has run and what remains.
- [Protocol](PROTOCOL.md): figure settings, fidelity requirements, and budget procedure.
- [Script guide](../../scripts/README.md): commands for subsequent runs.
- [Earlier exploratory pilot](../archive/decision-pilot.md): a separate study,
  preserved for reference; it is not evidence of paper reproduction.
