# Optional historical RHGD replay

The course smoke example does not need external sources. Exact author replay
does. Use Python 3.13 and the project environment, then restore the pinned checkout:

```bash
git clone https://github.com/QiangFu09/RHGD external/RHGD
git -C external/RHGD checkout --detach 37962b3074a5c9c6248ef062ffa665a2177a1301
source scripts/activate_env.sh
python scripts/reproduce_rhgd.py plan
python -m pytest tests/reproduction
python scripts/reproduce_rhgd.py run --case fig2-right --smoke --output tmp/author-smoke
```

The manifest verifies author commit, notebook/cell hashes, and the supplied paper
at the root. A different arXiv revision is not an interchangeable input. The
source bundle retains the supplied PDF; do not modify its bytes.

Full panels require Slurm. Read the [historical protocol](reproduction/PROTOCOL.md)
for parameters, RNG ordering, source display conventions, and known discrepancies.
Its old research priority/stop text describes the previous project; use the
[course plan](EXPERIMENT_PLAN.md) to select representative replications now.

The original arrays remain in this owner's local ignored `results/reproduction/`.
Portable parity receipts are under [evidence](evidence/README.md); a clone does
not contain full arrays. Old spectral `evidence.py`/`experiment.py` tools also
expect those raw data and historical freeze manifests. They are retained reference
code, not the new course benchmark CLI. The course smoke uses only their core
recurrences on generated tiny inputs.
