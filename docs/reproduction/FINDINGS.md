# RHGD reproduction findings

[Main-paper synthesis](MAIN_PAPER_SYNTHESIS.md) compares all five requested panels
against the paper's claims, with array-derived thresholds, refreshment sensitivity,
and explicit numerical/historical limitations.

As of 2026-09-17, four established paper-setting panels plus the requested
million-step Figure 1-right extension pass exact author-code parity. The latter
is explicitly distinct from the pinned 10,000-step default and preserves invalid
near-zero log bands. [Figure 1-right findings](FIG1_RIGHT.md) record 24 exact array
comparisons, the verified band-failure mechanism, historical differences,
canonical/diagnostic artifacts and 0.155 allocated CPU-hours.

[Figure 1-middle findings](FIG1_MIDDLE.md) record the α̂=0.01 run, exact problem/GD
identity with Figure 1-left, 25 array comparisons and 0.14444 allocated CPU-hours.
[Figure 1-left findings](FIG1_LEFT.md) cover its million-step run, 24 comparisons
and 0.1775 allocated CPU-hours. Work stops after Figure 1-right; Figures 3–7
(ten panels) have not begun. The default 10,000-step right-panel replay remains
separately unverified.

See [Figure 2-left findings](FIG2_LEFT.md) for the 1,000-iteration run, 33 exact array
comparisons, accounting, and terminal differences versus the saved notebook image.

## Figure 2-right: first full panel (2026-09-11)

Figure 2-right (weakly convex adaptive logistic regression) completed at the
notebook's full settings: dimension 100, 500 samples, 200 iterations, five
randomized replicates each for CAGD and RHGD, and deterministic GD/AGD baselines.
The source pin is `37962b3074a5c9c6248ef062ffa665a2177a1301`, cell 4 (zero-based).

**All 26 retained numeric arrays and plotted-coordinate arrays match a separate
direct execution of the author cell exactly, including dtype and shape.**
There were no numerical warnings or nonfinite captured values. This establishes
full-run source parity for this panel on our Grace environment, not for every
panel or for the authors' original computing environment.

## What was compared

The reproduction runner executed the full cell with no numerical setting changes.
The only compatibility change removed the retina-display import/call. The
independent verification executed the original source as text, bypassing the
runner's AST transformer, and removed only those display lines. It retained the
original functions, dataset generation, method order, seeds, and iteration count.
Both runs used the same software environment and one numerical thread.

The comparison covers 18 retained numeric arrays (including data, both 5×200 raw
randomized loss arrays, baseline losses, means, and uncertainty envelopes) plus
eight x/y coordinate arrays for the four plotted lines. Replaying author code
checks execution fidelity; it is not an independent proof of algorithm correctness.

Final plotted values are the pre-update losses at k=199:

| Method | Final plotted loss |
| --- | ---: |
| GD | 1.0531157274853065 × 10⁻³ |
| AGD | 2.566933280856177 × 10⁻¹⁰ |
| CAGD, mean of five | 2.4742788617570973 × 10⁻¹⁰ |
| RHGD, mean of five | 5.948656292744678 × 10⁻¹⁰ |

The weak-logistic cell plots raw loss while its label says f−f★. We preserved this
source convention and do not reinterpret these values as independently measured
optimality gaps.

## Comparison with the published presentation

Visual inspection of the generated panel, the PNG embedded in the authors'
notebook, and Figure 2-right on page 9 of the supplied paper finds consistent
curve shapes, ordering, iteration extent, and terminal scales. GD ends near 10⁻³;
the accelerated curves reach roughly 10⁻¹⁰ to 10⁻⁹. Tick placement and rendering
size differ. We did not digitize the reference curves or obtain their raw arrays,
so **exact published numerical agreement is not established**.

## Allocation and evidence

Job **19734521** completed with exit `0:0` on Grace **c113**, account
`132674288899`. It requested one CPU, 2 GB, and five minutes. Elapsed allocation:
**29 seconds = 0.00806 allocated CPU-hours**, below the 0.08333 CPU-hour ceiling.
The replay including artifact capture took 9.73 seconds; direct verification took
2.31 seconds. These include imports/I/O/rendering effects and are not optimizer
benchmarks. Actual billed SUs were not independently measured. No other panel
jobs were submitted in this step.

Evidence is in [the run directory](../../results/reproduction/fig2-right-19734521/):

- [Exact parity report](../../results/reproduction/fig2-right-19734521/author_parity.json)
- [Run metadata](../../results/reproduction/fig2-right-19734521/metadata.json)
- [Generated panel](../../results/reproduction/fig2-right-19734521/figure-01.png)
- [Scheduler accounting](../../results/reproduction/fig2-right-19734521/accounting.json)
- Original/executed source, raw NPZ arrays, plotted coordinates, PDF, direct-author
  reference arrays, saved notebook PNG, rendered paper page, and artifact hashes.

**Decision:** the first full-panel source replay works. Continue to another problem
family, then measure the cost of dense quadratic runs before scheduling the
million-iteration cases. At this stage fourteen panels still needed full execution; this result
supports proceeding with reproduction, not a general claim about RHGD performance.
