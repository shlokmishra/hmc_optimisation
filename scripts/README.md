# Script guide

Run from the repository root after `source scripts/activate_env.sh`.

| Script | Purpose |
| --- | --- |
| `setup_env.sh` | Create the Python 3.13 environment on Grace or a local computer |
| `activate_env.sh` | Activate it and set one numerical thread |
| `check_env.py` | Check numerical libraries, environment, and plotting |
| `stat605.py smoke --output …` | Tiny self-contained five-method demonstration |
| `stat605.py fixed-time-smoke --output …` | Periodic RHGD check on both shared quadratic inputs |
| `stat605.py agd --smoke --config configs/stat605/agd_smoke.json --output …` | Bounded AGD check; full configured runs require Slurm |
| `stat605.py spectral --output …` | Bounded five-method matched spectral software check |
| `stat605.py spectral-design --output …` | Plot controlled starting energies without optimizer updates |
| `stat605.py spectral-report --run … --output …` | Rebuild tables/figures from saved traces into a fresh directory |
| `stat605_spectral_pilot.slurm` | Bounded quadratic pilot; supply a verified current account/partition |
| `package_project.py --output …` | Package clean group sources with a hash manifest |
| `reproduce_rhgd.py plan` | Validate pinned inputs and list historical panel settings |
| `reproduce_rhgd.py run --case … --smoke --output …` | Short author-cell replay |
| `verify_rhgd_author.py` | Independently check a saved replay against direct author execution |
| `reproduce_rhgd.slurm` | Single-panel Grace job template; supply your current account |

See [reproduction setup](../docs/REPRODUCTION.md) before replaying author cells.
Old study launchers and advisor-figure generators are in the local recovery
archive. They are not course experiment entry points.
