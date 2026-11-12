# RHGD anchor-paper reproduction protocol

## Objective and scope

Reproduce Figures 1–7 of *Hamiltonian Descent Algorithms for Optimization:
Accelerated Rates via Randomized Integration Time* before investigating extensions.
Use the user-supplied [NeurIPS 2025 paper](../../Hamiltonian%20Descent%20Algorithms%20for%20Optimization.pdf)
as the figure reference and the [authors' repository](https://github.com/QiangFu09/RHGD)
as the implementation reference. The authors' README directs users to replay the
notebook and manually change parameters for Appendix H.

[The manifest](../../configs/reproduction/rhgd.json) pins commit
`37962b3074a5c9c6248ef062ffa665a2177a1301`, the complete notebook hash, each cell hash,
and the supplied PDF hash. The checkout contains no environment lock or separate
raw published numerical arrays. Bitwise agreement with the authors' original
machine cannot be promised. Saved notebook figures are useful secondary references;
nonsequential execution counts mean they are not proof of a fresh sequential run.

Three distinct deliverables are required:

1. **Source replay:** execute each full author cell, preserving function bodies,
   data generation, seed consumption, arithmetic, iteration count, and statistics.
2. **Published-figure agreement:** compare every panel against the supplied PDF,
   recording matched features and unresolved differences. Executing source alone
   does not establish agreement with the paper.
3. **Scientific audit:** assess discrepancies separately. Any corrected algorithm,
   objective evaluation, plot statistic, or Poisson simulator gets a new experiment
   identity; it must not silently replace source replay.

## Figure inventory

Cell indices below are zero-based. All problems have dimension 100. Logistic
problems have 500 observations. Randomized comparison curves use five runs.

| Panel / case | Cell | Setting | Iterations |
| --- | ---: | --- | ---: |
| `fig1-left` | 0 | Strong quadratic, L=500, κ=10⁷, exact α | 1,000,000 |
| `fig1-middle` | 1 | Same problem, supplied α̂=0.01 | 1,000,000 |
| `fig1-right` | 2 | Weak quadratic, L=500; user-requested extension | 1,000,000 |
| `fig2-left` | 3 | Adaptive logistic, α=10⁻⁴, both RHGD refresh multipliers | 1,000 |
| `fig2-right` | 4 | Adaptive logistic, α=0 | 200 |
| `fig3-left` | 0 | Strong quadratic, κ=10³ | 1,000 |
| `fig3-right` | 0 | Strong quadratic, κ=10⁵ | 10,000 |
| `fig4-left` | 1 | Strong quadratic, κ=10⁷, α̂=0.1 | 1,000,000 |
| `fig4-right` | 1 | Strong quadratic, κ=10⁷, α̂=1 | 1,000,000 |
| `fig5-left` | 2 | Weak quadratic, L=5,000, Table 3 steps | 10,000 |
| `fig5-right` | 2 | Weak quadratic, L=50,000, Table 3 steps | 10,000 |
| `fig6-left` | 5 | Strong refresh illustration, κ=10⁷ | 100,000 |
| `fig6-right` | 6 | Weak refresh illustration, L=500 | 1,000 |
| `fig7-left` | 3 | Adaptive logistic, α=10⁻³ | 1,000 |
| `fig7-right` | 3 | Adaptive logistic, α=10⁻⁵ | 1,000 |

Except for the explicit Figure 1-right extension below, counts follow visible
notebook defaults and its κ-dependent iteration rule; compare
published axis ranges during the full reproduction. Appendix experiments change
only the parameters required by the published panels, not a full Cartesian sweep.
The three α̂ values in cell 1 are split into separate panels; its per-value RNG reset
makes this equivalent to those respective branches of the original cell.
The direct-author verifier independently selects one existing `alphas` value by
text replacement and records the selection. It also supports the narrowly specified
cell-2 iteration extension below; other numerical overrides are rejected.
A regression check compares the selected 0.01 panel with the untouched loop's
first branch at short length; optimizer function ASTs must remain identical.

**Figure 1-right setting discrepancy (2026-09-17):** the user explicitly requests
L=500 and one million iterations. The pinned cell uses L=500 and **10,000**
iterations, consistent with the published panel's displayed extent. The manifest
records a top-level `num_iters` override and `mode=user_requested_parameters`.
Both replay and independent direct-author execution use the requested million
iterations, preserving all function bodies, stepsizes and RNG ordering. Exact
parity at these settings must not be called a replay of the untouched 10,000-step
default. CAGD pre-draws N+1 exponentials, so RHGD's million-step prefix is not a
reproduction of the default run. Historical agreement is assessed separately.

Table 2 uses η=1/L and h=1/√L. Table 3 (visually checked on paper page 55) uses, for
L=5,000 and 50,000, GD/CAGD η=1/(8L), AGD η=1/(16L), RHGD h=1/(8√L).
The original weak cell shares one η across methods, so the runner explicitly
patches the AGD call argument as well as top-level settings. The override is
recorded; no optimizer function body changes.

## Fidelity requirements and known discrepancies

- Preserve `np.random.seed(42)`, legacy data-generation draw order, dense QR
  matrices, linearly spaced eigenvalues, and initial normal draws. The weak
  quadratic generator resets the legacy seed internally; the strong one does not.
- Preserve the **shared sequential RNG** within each randomized replicate. Strong
  and weak quadratics run CAGD before RHGD; strong logistic runs RHGD c=2, RHGD c=1,
  then CAGD; weak logistic runs RHGD then CAGD. CAGD pre-draws N+1 exponentials.
  Reducing N changes the later method's randomness: smoke curves cannot stand in
  for prefixes of a full paper run.
- Losses are recorded before each update. Do not add early convergence stopping,
  independent method seed streams, retuning, or oracle-call optimizations.
- Preserve the author's mean and delta-method log-standard-deviation bands.
  These are not bootstrap confidence intervals.
- Strong logistic estimates f★ from the minimum across the compared traces and
  clips randomized shifted losses at 10⁻²⁰. Its first plotted randomized entry is
  overwritten with the unshifted initial loss. Preserve and flag this convention.
  Weak logistic plots raw loss while labeling the axis as f−f★.
- The weak refresh illustration uses thinning with proposal rate 1, although its
  target rate 17/(2t+18h) exceeds 1 near t=0. This is not a valid dominating rate.
  Preserve the source figure, but do not describe it as a verified theoretical
  Poisson reference. Investigate a correction only in the separate audit.
- The paper and notebook have presentation differences (e.g. refresh-event colors).
  Preserve source curves; distinguish plotting differences from numerical ones.
- The only automatic compatibility patch removes the notebook's
  `IPython.display.set_matplotlib_formats` import/call, which controls retina
  display. `plt.show` is intercepted to save artifacts. Function ASTs remain intact.

## Running and preserving evidence

```bash
source scripts/activate_env.sh
python scripts/reproduce_rhgd.py plan
python -m pytest tests/reproduction
python scripts/reproduce_rhgd.py run --case fig2-right --smoke \
    --output tmp/rhgd-smoke-example
```

Use a new output directory for every execution; overwriting is rejected. Each
run stores the original/executed cell, source manifest, settings changes, software
versions, thread-library details, host/job ID, elapsed time, stdout, warnings,
PNG/PDF figures, raw numeric namespace snapshots, and plotted line coordinates.
JSON metadata retains failure status; NPZ arrays retain nonfinite values, with
counts in metadata. Array files load with `np.load(path, allow_pickle=False)`.
The recorded arrays include problem data, raw per-replicate losses, and statistical
bands where the author retains them. This is author-cell data capture, not an
extra per-iteration trajectory logger.

If restoring the ignored upstream checkout on another machine:

```bash
git clone https://github.com/QiangFu09/RHGD external/RHGD
git -C external/RHGD checkout --detach 37962b3074a5c9c6248ef062ffa665a2177a1301
```

Restore the supplied paper separately; `plan` verifies hashes before any replay.
Do not edit the checkout or replace the PDF with a different arXiv version.

## Grace budget and execution order

Start with short validation, then one complete small case (`fig2-right` or
`fig3-left`) to measure runtime and verify artifacts. Estimate expensive panels
from a representative timed allocation before running million-iteration cases.
Dense author code is intentionally retained; do not infer its cost from the old
optimized pilot or from figure-rendering-dominated smoke timings.

`myproject`, `squeue -u "$USER"`, and `sinfo` are read-only allocation/queue/partition
queries. Use them when preparing a submission to confirm account, limits, and
availability; they do not start jobs. Discover changed tools with `module spider`.

The supplied script caps **one panel** at one CPU, 2 GB, 30 minutes: at most
0.5 allocated CPU-hours per submission, not a guaranteed SU tariff or completion
estimate. No account is hard-coded. From the project root, after confirming the
account and choosing one case:

```bash
mkdir -p logs
# Replace YOUR_ACCOUNT with the verified allocation account.
sbatch --account=YOUR_ACCOUNT --export=ALL,RHGD_CASE=fig2-right scripts/reproduce_rhgd.slurm
```

Record actual scheduler accounting after each run. A killed job may leave status
`running`; reconcile this with Slurm state rather than claiming completion. The
runner saves arrays at figure completion, so a timed-out million-iteration panel
may have no numeric artifact. Do not blindly resubmit or increase the limit.
Use a justified longer single allocation if needed after a cost measurement.

Parallelism is a throughput option, not a requirement. The user's suggested eight
jobs is a ceiling to verify against live QOS/account limits, not an established
entitlement. Start with one job; use at most eight only after measuring cost and
setting a total allocation budget. No full sweep is submitted by the cleanup tools.

## Completion criteria

For every panel: complete the specified iteration count and five randomized
replicates (one trajectory for refresh illustrations); retain failures/nonfinite
values; verify data/seeds/parameters; compare all algorithm curves, envelopes,
scales, iteration extent, terminal values, and refresh annotations against the
published panel. Quantitative tolerances must reflect the available reference
(raw arrays if obtained, otherwise documented figure digitization uncertainty).
Do not assert exact numerical agreement from visual similarity alone.

Write `docs/reproduction/FINDINGS.md` only with measured outcomes, linking raw run
IDs, source/environment records, comparison artifacts, discrepancies, and costs.
Mark each panel reproduced, discrepant, or blocked, with evidence. Only then use
the baseline to choose extensions. The historical exploratory pilot is indexed
[separately](../archive/decision-pilot.md).
