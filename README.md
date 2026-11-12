# When Should Momentum Be Reset?

STAT 605 group project by Leonardo Cazares, Kwonsang Jung, Shlok Mishra, and Leo Oh.
The [October 29 proposal](docs/STAT_605_Project.pdf) defines the course scope.

We compare adaptive restart in accelerated gradient descent with randomized and
trajectory-dependent momentum resets in Hamiltonian optimization. The central
question is how spectra and initial modal energies affect efficiency when the
dimension and extreme eigenvalues are held fixed.

Start with the [completed-work audit](docs/PROJECT_STATUS.md),
[remaining experiments](docs/EXPERIMENT_PLAN.md), and
[method conventions](docs/METHODS.md). [CONTRIBUTING.md](CONTRIBUTING.md) describes
how the group can divide the work.

## Run a small example

Use Python 3.13. From the project root:

```bash
bash scripts/setup_env.sh
source scripts/activate_env.sh
python scripts/stat605.py smoke --output tmp/stat605-smoke
python -m pytest
ruff check .
ruff format --check .
```

Setup uses Grace modules on Grace and a standard virtual environment elsewhere.
The smoke example runs five existing methods on a tiny synthetic quadratic and
saves a figure, traces, and metadata. It needs no historical results, upstream
checkout, GPU, or Slurm allocation. It is a software demonstration, not a course
experiment or performance result. Output directories must be new.

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
| `src/stat605/` | Course entry points and small demonstrations |
| `study/B/src/`, `study/B/configs/` | Unchanged frozen power-reset reference |
| `configs/stat605/` | Course settings, separate from historical settings |
| `tests/` | Replay, cost, correctness, and course checks |
| `scripts/` | Setup, smoke example, replay, and sharing tools |

The `B` in old source/configuration names means **power-reset RHGD**. These paths
remain unchanged because historical provenance pins their bytes and locations.
RCM and several proposed reset rules still need implementation and validation.

## Share with the group

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
