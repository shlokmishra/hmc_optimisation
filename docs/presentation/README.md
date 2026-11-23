# Final STAT 605 study and presentation

The approved protocol is frozen in `configs/stat605/final_protocol.json`.
`final_selected.json` records the actual tuning selection, including all selection
scores and the pilot hash. Full traces stay in ignored `results/stat605/`.
The timed narrative is [SPEAKING_OUTLINE.md](SPEAKING_OUTLINE.md).

The delivered [results](assets/RESULTS.md) cover 132 main paths and 198 robustness
paths. Main runs have no numerical failures; 18 robustness failures occur in the
1.1-times RHGD stress cases. Tuning selects beta=0 for both normalization families.
The committed figures and tables total about four MB:

- [Full comparison](assets/comparison.png), [per-path costs](assets/costs.csv), and [target table](assets/work_to_target.csv).
- [RHGD ablation](assets/rhgd_gradients.png) with a displayed target range; complete traces remain in raw storage and full-comparison plots provide uncropped backups.
- [Initial modal energy](assets/geometry.png) and [eigenvalue distributions](assets/eigenvalue_distributions.png).
- [Controller mechanism](assets/mechanism.png), [robustness](assets/robustness.png), and [replication overview](assets/replication_overview.png).

Each figure also has a same-named PDF. [RAW_ARTIFACTS.json](RAW_ARTIFACTS.json)
identifies the separate hashed 534-trace archive. [COMPUTE.json](COMPUTE.json)
records seven requested CPU-hours versus 0.397 actual allocated CPU-hours and
0.378 measured process CPU-hours; billing SUs are not inferred from those fields.
[ENVIRONMENT.json](ENVIRONMENT.json) documents the shared environment and
objective-count scope, including target-setup matrix products outside benchmark
counters. [SLURM_ACCOUNTING.psv](SLURM_ACCOUNTING.psv) retains the job receipts.

Run commands from the project root after `source scripts/activate_env.sh`.
The following report command is read-only with respect to the raw evidence and
requires a fresh output directory. It verifies every trace hash and independently
recomputes target crossings before exporting PNG/PDF figures and CSV tables:

```bash
PYTHONPATH=src python -m stat605.presentation \
  --main results/stat605/final-20261123/main-0 results/stat605/final-20261123/main-1 \
  --robustness results/stat605/final-20261123/robustness-0 results/stat605/final-20261123/robustness-1 \
  --output tmp/presentation-regenerated \
  --archive results/stat605/final-20261123-regenerated-raw.tar
```

`ASSET_HASHES.json` covers compact exported assets. `provenance.json` identifies
the raw source directories and summary hashes. The separate raw
archive has a `.sha256` receipt. Transfer that archive separately from source Git.
The archive includes main/robustness traces and automatically adds sibling
pilot/tuning directories when present, retaining their hashes for selection
provenance. NPZ traces are already compressed; `.tar` avoids recompressing them.
A `.tar.gz` destination is also supported. No private memory, recovery history, environment or
credentials belong in a source bundle.

The complete study uses four explicit stages; none automatically resubmits.
Slurm commands below **submit jobs and request CPU time**. Verify current account
balance with `myproject` and partition limits with `sinfo -p short` (read-only),
and substitute the verified funded account. Existing output directories are
never overwritten. Submit from the project root. At most two tasks run at once.

```bash
sbatch --account=ACCOUNT --partition=short --time=00:15:00 \
  scripts/stat605_final.slurm pilot --output results/stat605/NEW/pilot
# Only after that pilot completes with a feasible runtime-selected budget:
sbatch --account=ACCOUNT --partition=short --time=00:45:00 \
  scripts/stat605_final.slurm tune --prior results/stat605/NEW/pilot \
  --output results/stat605/NEW/tune
# Only after tuning completes; the driver consumes the saved selection:
sbatch --account=ACCOUNT --partition=short --time=02:00:00 --array=0-1%2 \
  scripts/stat605_final_array.slurm main results/stat605/NEW/tune results/stat605/NEW
# Only after both main tasks complete (or use afterok dependency on their array ID):
sbatch --account=ACCOUNT --partition=short --time=01:00:00 --array=0-1%2 \
  scripts/stat605_final_array.slurm robustness results/stat605/NEW/tune results/stat605/NEW
```

These request seven CPU-hours: .25 pilot + .75 tuning + 4 main + 2 robustness;
one hour remains unrequested contingency within the approved eight-hour ceiling.
Requested ceilings are distinct from actual Slurm CPU accounting. Grace `short`
allows two hours per task; the main four-hour allocation is two one-CPU tasks.
No accuracy-based stopping, success-only summary, or automatic resubmission.

For a bounded integrated software check, use `--smoke` on the driver stages,
fresh directories and both main shards; each path uses only 20 gradients.
Smoke outputs carry `smoke: true` and must never be reported as final experiments.
Existing `scripts/stat605.py spectral` configurations continue to work and accept
optional `method_parameters` per method (`period_steps` or `beta`). The historical
`AR_AGD` adapter stays available for regression checks; it is outside the final 14.

## Controller conventions and accounting

Both new normalized rules use the frozen RHGD map, retained endpoint and zeroed
velocity on reset; finite trial state checks precede resetting. Segment state
clears on events/caps. Endpoint beta=0 is exactly the existing strict-arming power
rule. Discrete kinetic comparison initializes on the first step, arms only after
a positive value, and triggers only on strict decrease of K/t^beta. The cap is
65,536 steps. The endpoint expression is a discrete heuristic, not an exact
energy identity. Tuning selected beta=0 for both families; retain this negative
normalization result and all positive-beta candidates in backup evidence.

RCM's public generator and AGD's public runner remain unchanged. Their new
adapters match finite trajectories in bounded parity tests. RCM pays one initial
gradient, reuses accepted endpoint gradients and pays variable trial/replacement
costs; a trial stopped by the budget retains spent work. Controller objectives
for function-restart AGD are reused by diagnostics. Objectives, reset causes,
rejected trials, cache requests, and unfinished evaluations remain visible.

The final comparison comprises 132 paths: six cases times (12 deterministic paths
plus five CAGD and five randomized RHGD paths). The same five seeds describe
algorithm randomness on fixed problems, not replicated datasets. Robustness has
198 paths on two rescaled cases: supplied-mu factors for the three mu-dependent
methods and step factors for all fourteen methods (including randomized seeds).
The h=1.1 h0 runs are stress tests. Fixed reset physical periods are preserved by
nearest-integer step counts; realized periods are in `robustness.csv`.
