# Reproduction status — September 17, 2026

**Four paper-setting panels and the requested Figure 1-right million-step extension
pass exact source parity. Figures 3–7 (ten panels) have not begun; the default
10,000-step Figure 1-right replay remains separately unverified.**
The first research objective is now the anchor-paper reproduction. The previous
RHGD/DG decision pilot remains historical exploratory evidence.

## Preparation completed

- Pinned and inspected the authors' seven-cell notebook at commit
  `37962b3074a5c9c6248ef062ffa665a2177a1301`; verified notebook and supplied-paper hashes.
- Read the paper's Section 5 and Appendix H experiment specifications and mapped
  all 15 published panels into `configs/reproduction/rhgd.json`.
- Checked Table 3 visually against PDF page 55, including RHGD's `1/(8√L)` step.
- Added a separate full-cell execution path with unchanged author function bodies,
  recorded setting/display patches, raw data and plotted-curve exports, provenance,
  warnings/failure records, and output overwrite protection.
- Added a single-panel, one-CPU Slurm template with a 30-minute limit and an explicit
  case/account selection. No jobs were submitted during this cleanup.
- Reorganized README and agent guidance around reproduction; moved environment
  instructions into `docs/grace.md` and indexed the earlier pilot under `docs/archive/`.
  Original numerical source and result locations were retained for integrity checks.

## Validation

The 11 reproduction checks pass. These cover unchanged function ASTs for all 15
panel presets, Table 3 steps, full-cell numeric equality against direct execution
of all seven author cells with 12 iterations, output capture, overwrite protection,
and rejection of full runs outside Slurm. Equality includes problem arrays and
retained loss/refresh arrays, not just terminal objective values.

The complete test suite also passes: **61 tests**, including the 50 historical
checks. Ruff lint and formatting checks pass. The Slurm template passes `bash -n`.
The test log is `tmp/research-cleanup-tests.log`.

The historical results audit passed for all **870 records**; all nine numerical
source hashes still match the original pre-run provenance. Audit output:
`tmp/research-cleanup-integrity.log`.

A standalone 12-iteration `fig2-right` smoke run completed with one BLAS thread,
no warnings, and no nonfinite captured values. Its saved PNG was visually checked.
Artifacts: `tmp/rhgd-setup-smoke-20260911/` (metadata, original/executed source,
raw arrays, plotted coordinates, PNG and PDF). This remains a smoke result.

These tests establish the short replay path on this environment. They do not
establish the million-iteration behavior or agreement with published figures.

## Full-panel results and remaining work

`fig2-right` completed at full paper settings in job **19734521**: 200 iterations,
five randomized replicates, and exact equality of all 26 retained numeric and
plotted-coordinate arrays against independent execution of the original cell.
The job completed successfully in 29 seconds (0.00806 allocated CPU-hours).
No numerical warnings or nonfinite values were observed.

The saved notebook figure and paper panel are visually consistent with the replay;
exact agreement with original published numerical arrays remains unverified because
those arrays are not supplied. See [findings](FINDINGS.md) for evidence and limits.
`fig2-left` also completed at full settings in job **19768992** on September 16:
1,000 iterations, α=10⁻⁴, five replicates per randomized method, and both RHGD
refresh multipliers. All 33 retained numeric/coordinate arrays matched direct
author execution; no warnings or nonfinite values were captured. Allocation was
29 seconds (0.00806 CPU-hours). Numerical code was unchanged. See the
[Figure 2-left report](FIG2_LEFT.md), including terminal differences versus the
saved notebook image and the limits of visual paper agreement.

`fig1-left` completed in job **19769000**: L=500, κ=10⁷, exact α=5×10⁻⁵,
one million iterations, five randomized runs. All 24 retained numeric/coordinate
arrays and scalar metadata match direct author execution exactly. No nonfinite
values were captured; the retained warning concerns slow automatic legend placement.
The allocation, including a short cost probe and both full executions, used 639 s
(0.1775 allocated CPU-hours). See [Figure 1-left findings](FIG1_LEFT.md).

`fig1-middle` completed in job **19770301**: same quadratic, true α=5×10⁻⁵,
algorithm input α̂=0.01, one million iterations, five randomized runs. All 25
numeric/coordinate arrays and scalar metadata matched direct author execution.
The matrix, initial point, and complete GD trace are identical to Figure 1-left,
and all Figure 1-left artifacts remain hash-identical. No warnings/nonfinite
values were captured. Allocation: 520 s (0.14444 CPU-hours). The narrow direct
verifier extension for selecting one existing alpha branch passed all 18
reproduction tests and lint/format checks. See [findings](FIG1_MIDDLE.md).

`fig1-right` completed in job **19772099** on September 17: intended α=0,
L=500, one million iterations and five randomized runs. All 24 arrays/coordinates
and scalar metadata match direct author execution at the explicitly requested
settings, with unchanged numerical function bodies. This extends the pinned
10,000-step default; metadata records `user_requested_parameters`.

Raw losses remain finite, but tiny negative means cause NaN log bands, with some
upper-band overflows. All nonfinite positions match direct author execution.
The canonical author rendering and separate signed-loss diagnostic are retained.
Cost: 558 seconds, 0.155 allocated CPU-hours, sampled peak RSS about 711 MiB.
All 19 reproduction tests and lint/format checks passed; the Figure 1-left/middle
artifacts remain hash-identical. See [Figure 1-right findings](FIG1_RIGHT.md).

**Current stop:** the [main-paper synthesis](MAIN_PAPER_SYNTHESIS.md) is complete,
using retained arrays only. No new experiments were run. Do not begin Figures 3–7
without further instruction. Historical/default-run agreement remains separate
from the successful million-step source-parity study.

The protocol records issues requiring explicit assessment: shared RNG ordering,
logistic objective-gap plotting conventions, and the weak refresh figure's invalid
thinning bound. These have not been silently corrected in the source replay.

See [the protocol](PROTOCOL.md) for the exact checklist and
[the historical pilot](../archive/decision-pilot.md) for earlier evidence.
