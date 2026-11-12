# Working on the STAT 605 project

- The scope is `docs/STAT_605_Project.pdf`. Read `docs/PROJECT_STATUS.md` and
  `docs/EXPERIMENT_PLAN.md` before substantial changes. Consult local `MEMORY.md`
  when history or a previous failure matters; it is not part of the shared bundle.
- Update root `MEMORY.md` after meaningful work with reusable findings, evidence,
  scope, unresolved questions, and retry conditions. Label findings as verified,
  hypotheses, or open questions. Keep transcripts and generated artifacts out.
- Run Python after `source scripts/activate_env.sh`; use `.venv`. Setup is
  `bash scripts/setup_env.sh`. Numerical work uses float64 and one BLAS thread.
- Keep new implementations in `src/stat605/`, settings in `configs/stat605/`,
  and correctness tests in `tests/`. Temporary outputs belong in `tmp/`.
- Preserve frozen RHGD/B numerical source, settings, RNG consumption and raw
  results. New rules are separate named implementations, never silent replay fixes.
- Do not edit acquired upstream code in `external/`. Restore pinned RHGD using
  `docs/REPRODUCTION.md`. The paper manifest is `configs/reproduction/rhgd.json`.
- Historical protocols describe completed studies. The course experiment plan
  supersedes old project priorities; archival stop instructions do not define
  the new course scope. Do not automatically launch expensive experiments.
- Run `ruff check .`, `ruff format --check .`, and relevant tests for Python changes.
  Validate environment changes using `python scripts/check_env.py` and
  `python -m pip check`. Report skipped upstream-dependent tests explicitly.
- Benchmarks require a suitable Slurm allocation on Grace. Verify the current
  account/partition rather than copying historical account numbers. Discover
  modules with `module spider <name>/<version>` and `mla <name>` before changing
  module choices; see the HPRC Python and Grace environment guides.
- Count real gradient/objective evaluations, rejected work and failures. Distinguish
  first and sustained crossings, literal calls and cached evaluations, current
  and best-so-far loss, source parity and paper agreement. Preserve negative results.
  No general acceleration or novelty claim follows from a plot.
- `.archive/` is a private recovery copy. Never include it, chat exports, local
  credentials, raw study results, or `.venv` in group source bundles.
