# Script guide

Run from the repository root after `source scripts/activate_env.sh`.

| Script | Purpose |
| --- | --- |
| `setup_env.sh` | Create the Python 3.13 environment on Grace or a local computer |
| `activate_env.sh` | Activate it and set one numerical thread |
| `check_env.py` | Check numerical libraries, environment, and plotting |
| `stat605.py smoke --output …` | Tiny self-contained five-method demonstration |
| `package_project.py --output …` | Package clean group sources with a hash manifest |
| `reproduce_rhgd.py plan` | Validate pinned inputs and list historical panel settings |
| `reproduce_rhgd.py run --case … --smoke --output …` | Short author-cell replay |
| `verify_rhgd_author.py` | Independently check a saved replay against direct author execution |
| `reproduce_rhgd.slurm` | Single-panel Grace job template; supply your current account |

See [reproduction setup](../docs/REPRODUCTION.md) before replaying author cells.
Old study launchers and advisor-figure generators are in the local recovery
archive. They are not course experiment entry points.
