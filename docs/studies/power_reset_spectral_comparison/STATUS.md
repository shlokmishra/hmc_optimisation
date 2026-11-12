# Status — COMPLETE, 2026-09-23

All requested runs, validation, analysis and reports are complete. The frozen
general-speed continuation rule fails; B is unchanged. The detailed execution
record follows, with the final outcome and verification at the end.

## Pre-run record

Phase 0: protocol and machine configuration frozen before performance runs.
Prior design, B report/theory/configuration, independent synthesis, reproduction
protocol/status and numerical sources read. B and all prior artifacts are read-only.

Live account 132674288899: 18,798.42 SU available; no current user jobs; short
partition available. Initial ceiling: probe 120 CPU-seconds plus main 1,200
CPU-seconds (0.366667 allocated CPU-hours); actual billing will be retained.

Next gates: prepare/hash the two problems; test AR_AGD and uniform caching;
verify frozen B and baseline path equivalence; run the bounded allocation probe;
record a measured estimate here before submitting the main allocation.
No performance results or main submission yet.

## Pre-main gate — 2026-09-23

Preparation and all 26 prefix checks passed. Frozen B matches both direct old-source
execution and its retained paper prefix exactly. Baselines match original functions;
cached/uncached paths and explicit-seed repetitions agree exactly. Analytic AR tests
passed. The preparation manifest protects 912 prior artifact files. Protocol/config
and all individual input arrays have SHA256 records in `freeze.json`.

Bounded probe job **19819630**, node **c672**, Intel Xeon Gold 6248R, one numerical
thread: all 28 probe paths completed, no errors. Measured optimizer time 1.438394 s
(all paths), including 1.351509 s for primary paths; serialization 1.591909 s;
complete probe script 5.810273 s. Extrapolation to 100x work and three timing repeats:
`100*(1.438394 + 3*1.351509) = 549.292184 s` optimizer time (0.152581 CPU h).
Conservatively charging four full diagnostic serialization batches gives
`100*(1.438394 + 3*1.351509 + 4*1.591909) = 1186.055772 s` (0.32946 h).
This overcounts timing serialization because timing records omit large modal-state
histories, but retains a conservative estimate. Main allocation remains the frozen
one CPU / 1200 s ceiling; combined probe/main ceiling remains 0.366667 CPU h.
No target performance summaries from this probe enter the study comparison.
Main submission is authorized by the completed fidelity gate and measured estimate.

Main job **19819633** started on the same node c672, one CPU/thread. No scientific
configuration changed after the freeze. Repository-wide `ruff check .` and
`ruff format --check .` passed (85 files); 34 study/reproduction tests passed,
including hand counters, cache parity, strict restart behavior, censoring, and
checks of the theory's modal closed form. Timing and diagnostic trajectories are
being retained separately; interpretation waits for the full saved-data audit.

## Completed execution and validation

Main job 19819633 completed normally: 28/28 diagnostic/scientific paths and 78/78
minimal timing paths reached the full budget, with no exceptions or numerical
failures. Independent saved-data audit passed: all 912 protected prior files,
frozen protocol/config/B hashes, 28 counters/objective totals, every B arming/reset/
cap decision, independently reconstructed reset endpoints, and all 78 full timing
loss paths/endpoints. See `main-19819633/analysis/audit.json`.

Scheduler allocation was 30 s probe + 609 s main = **639 CPU-seconds = 0.1775
CPU-hours**, below the 0.366667 ceiling. Main measured optimizer time was 156.957 s
for the 28 detailed paths and 356.190 s for timing repetitions; serialization
89.867 s, setup .454 s, total script 606.476 s. `cost.json` and
`scheduler_receipt.txt` retain actual accounting; billed SUs are not independently
measured. Performance interpretation begins only after this audit.

Offline analysis initially stopped before writing a summary: a relative CLI run
path was passed to `Path.relative_to(absolute_ROOT)`, raising `ValueError`. Numerical
runs and the completed audit were unaffected. Fixed only the analysis/audit input
normalization with `Path(...).resolve()`; rerun only saved-data analysis, with no
optimizer rerun and no scientific configuration change. Existing modal files were
intermediate derived output; the complete rerun verifies this infrastructure fix.

## Final outcome — COMPLETE

The continuation gate fails: paper B/AR_AGD sustained-primary work is 10,000/11,832
(15.5% saving, below 20%); log is 43,016/25,188 (70.8% regression). Median times
are .168641/.334968 s and .722348/.711067 s respectively. Log also violates the
secondary work-regression limits. Stop the general-speed direction; B remains
unchanged. The report retains the favorable paper result, substantial RHGD-relative
gains, CAGD caching reversal, and direct modal evidence for slow-mode interference.

The full saved-data audit passed again after final analysis fixes. An independent
reverse-cumulative target audit checks all 156 first/sustained records, all 106
scientific/timing counter records, positive raw losses on all 28 scientific paths,
and document links. Final `ruff check .` and `ruff format --check .` passed
(86 files); the 34 study/reproduction tests passed in 8.19 s. Static performance
and modal figures were visually inspected; modal tick spacing was adjusted only
for readability. The relative-path reporting fix is verified by successful complete
analysis; no numerical reruns were needed. No scientific changes or extra optimizer
comparisons followed the results.

THEORY.md proves segment energy descent and a restricted one-active-curvature
accelerated bound with inactive cap, and records the unsuccessful counterexample
attempt and remaining general multimode gap. REPORT.md is self-contained and ends
with the explicit research verdict. Root MEMORY.md records reusable findings and
supersedes the earlier proposal status. Artifact hashes are retained in the final
manifest; the prior artifacts and B source/config remain unchanged.
