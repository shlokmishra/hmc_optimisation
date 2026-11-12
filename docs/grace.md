# Environment setup

## Grace

The retained runtime is Python 3.13.5 with GCCcore/14.3.0. Before changing modules,
check prerequisites using `module spider Python/3.13.5`, `mla Python`, and
`module spider GCCcore/14.3.0`. See HPRC's
[Python guide](https://hprc.tamu.edu/kb/Software/Python/) and
[Grace environment guide](https://hprc.tamu.edu/kb/User-Guides/Grace/Computing_Environment/).

From the checkout root:

```bash
bash scripts/setup_env.sh
source scripts/activate_env.sh
python scripts/check_env.py
python -m pip check
```

Setup creates `.venv` and installs `requirements.txt`, the retained resolved
versions. It refuses to silently replace a virtual environment with a different
base Python. Activation loads the Grace Python toolchain and sets one thread for
numerical libraries. Node, Codex, shell aliases, and other projects are not needed.

Full performance runs belong in a suitable Slurm allocation. Inspect current
accounts and partitions with `myproject`, `sinfo`, and `squeue -u "$USER"` before
submitting. The old reproduction job template requires an explicit account;
historical account numbers do not establish current availability. No automatic
submission or full course experiment sweep is configured.

## Local computer

Install Python 3.13, then use the same setup and activation commands. Off Grace,
setup uses `python3.13` (or `python3` if it is version 3.13), and activation skips
cluster modules. The tested local entry points use Bash, for example macOS/Linux
or a Linux environment on Windows. Bundle portability is checked on Grace;
the non-Grace installation path and other operating systems were not tested.

Do not copy `.venv` between machines. The retained dependency pins are the
historical environment; package availability and compilation on each teammate's
machine must be checked during onboarding. Avoid changing pins to resolve a local
issue without recording and validating the new environment separately.

## Validation

```bash
source scripts/activate_env.sh
python scripts/check_env.py
python -m pip check
python -m pytest
ruff check .
ruff format --check .
```

The environment check runs a small float64 solve, a known quadratic optimizer,
imports, one-thread checks, and plot rendering; it writes `tmp/environment.json`.
For notebooks, select `.venv/bin/python` and use `%matplotlib inline` if wanted.
Large datasets, package caches, logs, and results stay out of Git.
