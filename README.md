# When Should Momentum Be Reset?

STAT 605 group project by Leonardo Cazares, Kwonsang Jung, Shlok Mishra, and Leo Oh.
The [October 29 proposal](docs/STAT_605_Project.pdf) defines the course scope.

We compare adaptive restart in accelerated gradient descent with randomized and
trajectory-dependent momentum resets in Hamiltonian optimization. The central
question is how spectra and initial modal energies affect efficiency when the
dimension and extreme eigenvalues are held fixed.

**New collaborators: start with the [group handoff and work split](CONTRIBUTING.md).**
It covers setup, the proposed four workstreams, starter inputs, and first tasks.
The [completed-work audit](docs/PROJECT_STATUS.md),
[remaining experiments](docs/EXPERIMENT_PLAN.md), and
[method conventions](docs/METHODS.md) give the scientific detail.

## Run a small example

Use Python 3.13 and Bash (Linux/macOS or a Linux environment on Windows):

```bash
git clone https://github.com/shlokmishra/hmc_optimisation.git
cd hmc_optimisation
bash scripts/setup_env.sh
source scripts/activate_env.sh
python scripts/stat605.py smoke --output tmp/stat605-smoke
python scripts/stat605.py fixed-time-smoke --output tmp/fixed-time-smoke
python -m pytest
ruff check .
ruff format --check .
```

Setup uses Grace modules on Grace and a standard virtual environment elsewhere.
The smoke example runs five existing methods on a tiny synthetic quadratic and
saves a figure, traces, and metadata. It needs no historical results, upstream
checkout, GPU, or Slurm allocation. It is a software demonstration, not a course
experiment or performance result. Output directories must be new.

The fixed-time smoke checks the new periodic RHGD control on the two shared
quadratic inputs (200 gradients each). It resets after every 8 completed updates,
retains the endpoint, and saves reset flags and optional states. This interval is
a software example; benchmark intervals still need to be declared before a
matched comparison. See [the exact convention](docs/METHODS.md#fixed-time-rhgd-control).

Paper-replay tests are skipped if the pinned author checkout is absent. To enable
them, follow [reproduction setup](docs/REPRODUCTION.md), then run
`python -m pytest tests/reproduction`. Large runs belong in a Slurm allocation;
[Grace instructions](docs/grace.md) include environment details.

## Repository map

| Path | Purpose |
| --- | --- |
| `docs/STAT_605_Project.pdf` | Presented course proposal |
| `docs/PROJECT_STATUS.md` | Evidence-backed inventory and limitations |
| `docs/EXPERIMENT_PLAN.md` | Ordered course work and completion criteria |
| `docs/evidence/` | Small, portable copies of historical result summaries |
| `src/rhgd_reproduction/` | Pinned author-cell replay |
| `src/power_reset_spectral_comparison/` | Existing fair-cost quadratic comparison code |
| `src/stat605/` | Course fixed-time RHGD control, RCM variants, and small demonstrations |
| `study/B/src/`, `study/B/configs/` | Unchanged frozen power-reset reference |
| `configs/stat605/` | Course settings, separate from historical settings |
| `configs/stat605/fixtures/` | Exact small historical quadratic and synthetic logistic inputs, with hashes |
| `tests/` | Replay, cost, correctness, and course checks |
| `scripts/` | Setup, smoke example, replay, and sharing tools |

The `B` in old source/configuration names means **power-reset RHGD**. These paths
remain unchanged because historical provenance pins their bytes and locations.
The three selected RCM variants now have an implementation and a qualified
[setup replication](docs/RCM_REPLICATION.md). Their combined comparison with RHGD,
function-restart AGD, and several other proposed reset rules remains future work.

## Share with the group

The shared code is at [shlokmishra/hmc_optimisation](https://github.com/shlokmishra/hmc_optimisation).
Clone it using the commands above. An optional portable source bundle is also available:

```bash
python scripts/package_project.py --output tmp/stat605-collaboration.tar.gz
```

This creates a standalone source bundle with a SHA-256 manifest. It excludes local
environments, private research history, upstream clones, and large raw results.
The cleanup started from a checkout with no Git commits. Use the bundle or this
repository's Git history to share the cleaned project through your group's remote.

Prior experiments predate the course. Label them as inherited evidence in course
deliverables and identify the group's new work. The [cleanup record](docs/CLEANUP.md)
explains what was archived and how to recover it locally.
