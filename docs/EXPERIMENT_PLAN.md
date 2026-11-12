# Remaining course work

This is a proposed bounded plan derived from slide 17, not a record of completed
experiments. Owners and compute ceilings should be agreed by the group. No jobs
were submitted during repository cleanup.

## 1. Close the method and replication gaps

- [ ] Choose one representative RCM quadratic example from Scagliotti and Colli
  Franzone. Record the exact source/version, stepsize, initialization, restart
  inequality, and retained endpoint. Implement the paper's method separately
  from RHGD; verify a hand-computed step and the selected source example.
- [ ] Add function-increase restarted AGD alongside the existing gradient-restart
  recurrence. Specify strictness, index ordering, retained point, and state reset.
- [ ] Document the selected restarted-AGD source benchmark and compare it at its
  source settings. Existing implementation tests alone do not replicate a paper.
- [ ] Define fixed-time, kinetic-peak and normalized/mean-dissipation RHGD reset
  variants. Keep RHGD's position/velocity update unchanged. State whether the
  signal is based on actual objective decrease or kinetic energy: the discrete
  map dissipates energy, so these quantities need not agree.
- [ ] For each new controller, test zero initial velocity, no spurious first-step
  reset, equality boundaries, segment-clock reset, cap, and nonfinite failure.

Deliverable: short method specifications, implementations in `src/stat605/`, and
small correctness tests. RCM symplectic Euler and RHGD are different integrators.

## 2. Build one shared benchmark interface

- [ ] Include AGD with known mu, alpha-free AGD, function/gradient restarted AGD,
  CAGD, original RHGD, power-reset RHGD, selected RCM, and the new RHGD controllers.
  GD can serve as a simple reference. Do not infer a common guarantee from a
  shared interface.
- [ ] Make dimension, mu, L, stepsize, seeds and initial modal energy configurable.
  The old spectral runner hard-codes historical settings; do not change its frozen
  global configuration to turn it into a general harness.
- [ ] Record iteration, distinct and literal gradients, objectives, reset counts,
  current loss, signed loss, status, and elapsed optimizer time. Pay for rejected
  work and controller checks. Preserve failures and censored targets.
- [ ] Use the same objective, start, cache policy, and output convention for every
  method. Report both iterations and gradients; RHGD usually needs two gradients
  per update. Keep diagnostics outside the timed boundary or charge them uniformly.
- [ ] Store config, seeds, environment, source hashes, raw traces and summary JSON
  in a new output directory. Separate setup, diagnostics, and optimizer time.

Deliverable: one reproducible configuration-driven CPU benchmark, initially on a
tiny test problem. The current `smoke` command is only an onboarding demonstration.

## 3. Test the spectral hypothesis

- [ ] Start with linear, log-spaced, and one predeclared clustered spectrum, all
  with d=100, mu=5e-5, L=500. Reuse one orthogonal basis for matched comparisons.
- [ ] Compare the retained common-start convention with equal initial modal
  energies. Optionally add a declared slow-heavy start. Equal x coordinates do
  not give equal modal energy: E_i=0.5*lambda_i*z_i(0)^2.
- [ ] First run a short pilot in an allocation to measure cost and detect failures.
  Freeze target(s), budgets, method parameters, starts and seed list before the
  main comparison. Record changes made after this pilot.
- [ ] Use five explicit algorithm seeds initially for randomized methods, and
  repeat starts/problem generation only if the group can afford it. Keep these
  sources of variability separate. Timing repetitions are not statistical seeds.
- [ ] Report current-loss first and sustained targets, reset locations, and modal
  power contributions on a small diagnostic subset. Use above-floor targets and
  mark misses as censored, not omitted.

Deliverable: loss versus gradients, loss versus iterations, work-to-target table,
and a mechanism figure. A change in ranking is a useful result even if no new
controller wins.

## 4. Sensitivity, then optional logistic regression

- [ ] At fixed matrices, compare exact supplied mu with predeclared under/over-
  estimates. Label which methods use mu and which do not; mu-free does not mean
  independent of L, stepsize, spectrum, or caps.
- [ ] On a small subset, compare declared stable stepsizes, for example h factors
  1/2 and 1 times the RHGD paper step. Explain the relation eta=h^2 when matching
  gradient methods. Separate source settings from new sensitivity studies.
- [ ] Only after the quadratic suite is stable, run a small regularized logistic
  comparison using common data/starts and a documented reference minimum.
  Existing logistic results can be reused with their original limitations.

## 5. Produce the group deliverables

- [ ] Final report: question, related methods, exact algorithms, replication,
  design, results including failures, interpretation, limitations, contributions.
- [ ] Final presentation: one clear comparison and one explanation of when a
  reset helps or hurts. Preserve the original proposal as submitted.
- [ ] One-command reproduction of the group's new tables/figures from saved data;
  provide raw-artifact locations and manifests separately from source Git.
- [ ] Confirm course rubric, deadline, report length, and contribution requirements;
  these were not present in the repository audit.
