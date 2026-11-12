# Working together

Read [the status](docs/PROJECT_STATUS.md) and [plan](docs/EXPERIMENT_PLAN.md) first.
Agree owners before starting; no assignments are implied below.

| Workstream | First concrete deliverable |
| --- | --- |
| RCM and source replication | One source-checked quadratic example and update/restart tests |
| AGD and reset definitions | Function-restart AGD plus precise new RHGD controller specifications |
| Benchmark and diagnostics | Shared cost-accounted interface and controlled spectra/starts |
| Analysis and writing | Figure/table regeneration, evidence ledger, final report/presentation |

Start from Python 3.13 and follow the root README. Every member should be able to
run the smoke example and source-only tests without old raw results or cluster
access. Use a feature branch for a bounded change and a pull request describing
the behavior, mathematical convention, and checks performed. Branch naming is up
to the group.

New algorithms go in `src/stat605/`, configs in `configs/stat605/`, and correctness
tests in `tests/`. Do not alter frozen historical code to make a new method work.
Avoid tuning against the final comparison cases; record pilot decisions and
freeze parameters before reporting main results.

Before proposing a merge:

```bash
source scripts/activate_env.sh
python -m pytest
ruff check .
ruff format --check .
```

Tests that require an absent pinned author checkout skip explicitly. Anyone
changing replay code must install those inputs and run the replay tests too.
Benchmark in an allocation, use a new result directory, and record config/seeds,
environment, source hashes, status, and actual evaluation counts.

Keep large arrays, environments, logs, caches, and upstream clones outside Git.
Share raw artifacts through an agreed group storage location and record hashes
and retrieval instructions. The current private scratch path is not shared storage
or a backup. Small final summaries and figures can be committed under `docs/`.

Prior results predate the course. Identify them as inherited evidence and state
each member's new contribution in the report. Retain failed/censored runs and
unfavorable comparisons; a negative finding is a valid project outcome.
