# RCM implementation and quadratic setup replication

Leonardo Cazares contributed `kin`, `mmd-r`, and `mmd-dr`, their small correctness
checks, a seed-605 example figure, and a 300-gradient pilot on the shared fixtures.

## Source and exact conventions

Reference: Scagliotti and Colli Franzone,
[A Piecewise Conservative Method for Unconstrained Convex Optimization, arXiv v4](https://arxiv.org/pdf/2009.11233v4).
The numerical core is `src/stat605/rcm.py`. It uses symplectic Euler, Eq. (35).
`mmd-r` follows Eq. (39)/Algorithm 1; `mmd-dr` follows Eq. (40)/Algorithm 2 **as
printed**, including its integer segment clock and no additional factor of h in
the trigger. This should not be silently replaced by another continuous-time
interpretation. Kinetic restart compares the two consecutive squared speeds.

On a trigger, discard the tentative step and take a zero-momentum gradient step
from the previous accepted position. The resulting stored velocity is -h*g at
that position, and the new segment age is 1. This differs from the project's
power-reset RHGD, which retains its tentative endpoint and zeros velocity.
The three included variants do not implement RCM-grad or establish its theorem.

Gradient counts include the initial diagnostic gradient, endpoint gradients
cached for the next step, and discarded trial gradients for `mmd-dr`. Pilot
summaries distinguish total gradients spent from the count at the last returned
iterate. If the budget expires during a rejected trial, that paid work is retained
and the last complete observation remains the output.

## Section 5.1 example

The committed input is `configs/stat605/fixtures/rcm_section5_1_seed605.npz`:
dimension 1,000, eigenvalues sampled uniformly on [0.03,15], independent standard
normal b, x0=0, v0=0, and h=1/sqrt(max sampled eigenvalue). It represents
f(x)=0.5*x^T*A*x+b^T*x in the eigenbasis of A. The fixture includes the exact
quadratic minimizer, objective minimum, and seed. Seed 605, the particular matrix
representation and x0 are this project's choices; original published numerical
arrays were not supplied. This is a replication of the problem setup and three
selected method curves, not exact agreement with the paper's original Figure 2.
The paper's RCM-grad curve and averaged 50-problem experiment are not reproduced.

From the root, activate the environment and use a fresh output directory:

```bash
source scripts/activate_env.sh
python scripts/reproduce_rcm.py --output tmp/rcm-replication
```

This small diagonal example writes 300-iteration gradient-norm traces and reset
locations to `trace.csv` and `rcm_seed605.pdf`. It prints final counts and the
fixture hash. The historical figure is `docs/evidence/rcm/rcm_seed605.pdf`.
To regenerate an input for inspection without overwriting the committed fixture:

```bash
python scripts/prepare_rcm_quadratic.py --output tmp/rcm-input-check.npz
```

The committed input is authoritative. On the reviewed Grace runtime, regeneration
matches b, initial states, h and f_star exactly, while eigenvalues differ by at
most one ULP and x_star by at most two ULP (units in the last place). Both the
original submitted generator and the safeguarded generator produce exactly the
same arrays on this runtime. A shared seed alone is not a cross-environment
bitwise guarantee; do not overwrite the submitted input or change its hashes to
hide such a difference.

## Shared-fixture pilot and remaining work

`docs/evidence/rcm/pilot_summary.json` contains six saved 300-gradient results
(two shared quadratics, three rules). Every record pins its numerical core and
input hashes. It is a small pilot, not evidence of convergence or a matched
performance win. It contains no timing or replicated uncertainty assessment;
no historical wall-time comparison with RHGD follows.

A capped software check is available without a benchmark allocation:

```bash
python scripts/benchmark_rcm.py --smoke --gradient-budget 30 --output tmp/rcm-smoke
```

The smoke ceiling is 300 gradients per case. Larger/full benchmark runs require
an active Slurm allocation, matched cost conventions, declared budgets and new
output directories. The full group comparison and logistic validation remain
future work. Failures remain failures even if the last saved objective is small.
