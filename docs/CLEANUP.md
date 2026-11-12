# Course migration: November 12, 2026

The course proposal is now the organizing scope. No numerical source in the
retained RHGD replay, power-reset reference, or fair spectral modules was changed.
No historical optimizer benchmark was rerun, and no Slurm jobs were submitted.
The [validation receipt](CLEANUP_VALIDATION.json) records the checks and their scope.

## Kept in the shared project

- The original course proposal and pinned RHGD paper.
- Replay implementation/configuration/tests and historical reproduction reports.
- Frozen power-reset source/configuration and fair spectral comparison code/tests.
- Small historical parity/result summaries with source paths and hashes.
- Course status, ordered plan, method conventions, collaboration/setup guidance,
  self-contained smoke command, and a source-bundle packager.

## Removed from the active tree

Archived the unrelated DG pilot, A/C candidates, geometry/acquisition/scaling,
GPU and multiproposal branches, their launchers/tests/configs, old advisor reports,
proof drafts, duplicate presentations, handoffs, and chat export. Node/Codex are no
longer part of Python activation. Private history, results and environments are
excluded from Git and source bundles.

Nothing was permanently deleted. The private local recovery directory is
`.archive/stat605-20261112/`. It contains a verified 723-file pre-cleanup source
snapshot, a per-file SHA-256 manifest, the previous root memory, and an exact
move receipt. A/C raw results moved with those archived study directories;
`results/` and `study/B/results/` remain at their original paths. External
checkouts were left untouched. Large historical raw arrays are not copied into
the portable group bundle.

For local recovery, extract `source-before-cleanup.tar.gz` into a **separate empty
directory**, then consult `CLEANUP_RECEIPT.json` for moved raw artifacts. Do not
extract over the course checkout. A full old-study replay needs original raw
results and upstream checkouts as well as the source snapshot. The archive stays
on the same scratch filesystem, so it is a recovery checkpoint, not an offsite
backup.

Git was an unborn `main` branch with no tracked project files before cleanup.
No commits, remote changes, pushes, or publication were performed. Review the
clean source bundle before choosing the group's collaboration remote.
