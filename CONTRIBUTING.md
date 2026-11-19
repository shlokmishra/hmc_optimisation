# Group handoff: start here

Updated November 19, 2026. Shared repository:
[shlokmishra/hmc_optimisation](https://github.com/shlokmishra/hmc_optimisation).
The repository is public, so everyone can clone it. Use a fork and pull request
if direct write access has not yet been arranged.

## 1. Get the code running

Use Python 3.13 and Bash. From a terminal:

```bash
git clone https://github.com/shlokmishra/hmc_optimisation.git
cd hmc_optimisation
bash scripts/setup_env.sh
source scripts/activate_env.sh
python scripts/stat605.py smoke --output tmp/my-first-smoke
python -m pytest
```

The smoke command writes `smoke.png`, five small method traces, and `summary.json`.
It demonstrates working software; it is not a research comparison. Choose a fresh
output directory for each run. Grace uses the project Python modules; local
computers use a standard virtual environment. See [environment details](docs/grace.md).
The non-Grace installation path and other operating systems have not been tested.

A source checkout without the optional author notebook is expected to pass 16
checks and skip 19 replay checks. Those skips are explained by
[reproduction setup](docs/REPRODUCTION.md); they do not prevent course work.
The owner's checkout with pinned upstream inputs has passed all 35 checks.

## 2. What exists now

- RHGD source-parity checks for five settings: strong/weak quadratics and logistic
  regression. The weak million-step experiment extends the notebook default.
- Tested AGD, gradient-restart AGD, CAGD, original RHGD, and power-reset RHGD code.
- Historical fair-cost comparisons on two fixed 100D linear/log spectra.
- Preliminary regularized-logistic power-reset comparisons and logistic replays.
- Portable result summaries, paper/proposal PDFs, setup tools, and starter inputs.

At sustained objective gap 1e-8, power-reset RHGD used 10,000 gradients versus
61,274 for original RHGD on the linear spectrum; on the log spectrum, 43,016
versus 127,424. Randomized RHGD entries are five-seed medians. Restarted AGD used
11,832 and 25,188 respectively: power reset's ranking changes with spectrum.
The old 20% work-and-time gate against restarted AGD failed. Preserve that result.
See the [status audit](docs/PROJECT_STATUS.md) and [saved evidence](docs/evidence/README.md).

These are inherited results from Shlok's earlier work, not new group experiments.
RCM, function-restart AGD, a general course comparison harness, clustered spectra,
and a unified logistic comparison remain to be completed.

## 3. Proposed four workstreams

This follows the proposal-presentation division. Confirm assignments together;
this is a proposed working split, not a record of everyone's agreement.

| Owner | Scope and first task | Deliverable |
| --- | --- | --- |
| **Kwonsang** | Restarted AGD: inspect existing gradient restart, add function restart, and reproduce one selected O'Donoghue/Candes example. | Checked AGD variants, a source-replication comparison, and a short result on restart/mu sensitivity. |
| **Leonardo** | Conservative/RCM methods: choose one Scagliotti/Colli Franzone quadratic example; specify and check its update and kinetic/mean-dissipation restart conventions. | Tested RCM implementation, one replicated example, and a comparison/explanation of its restart criteria. |
| **Shlok** | RHGD and power reset: carry forward verified replays/results, supply RHGD adapters, and add a fixed-time reset control while keeping the RHGD update fixed. | Checked RHGD controls, a mechanism/result figure, and a clear account of the existing power-reset gain and its limits. |
| **Leo** | Spectral geometry and shared comparison: start with the existing methods/fixtures, add clustered spectra and controlled initial modal energies, and assemble common result tables. | Reusable problem/benchmark utilities and spectral/initial-energy comparison figures. |

Each person owns their method/problem checks, one main figure or table, and the
matching final-report subsection. All four contribute to interpretation and the
final presentation. Shlok's completed work counts as the inherited starting point;
a new successful optimizer or general theorem is not a completion requirement.

Suggested separate new files: `src/stat605/agd.py`, `rcm.py`, `rhgd.py`, and
`problems.py`/`benchmark.py`, with corresponding tests. These are proposed work
locations, not implementations already present. Keep frozen historical code intact.
For three streams, combine Shlok and Leo into a joint Hamiltonian/spectral stream.

## 4. Shared problems and independence

Exact compact inputs are committed under `configs/stat605/fixtures/`:

| Fixture | Contents | Use |
| --- | --- | --- |
| `quadratic_paper.npz` | A, x0, basis, eigenvalues; d=100, mu=5e-5, L=500 | Historical linear spectrum |
| `quadratic_log.npz` | Same fields and start, different A; same endpoints | Historical dense log spectrum |
| `logistic_regularized.npz` | Synthetic A (500 by 100), labels b in {-1,+1}, x0 | Logistic loss plus (1e-4/2)*||x||^2 |

`PROVENANCE.json` in that directory records source paths, settings, and file/array
hashes. Load with `numpy.load(path, allow_pickle=False)`; the fixtures contain no
optimizer trajectories. For the quadratic, evaluate `0.5*x @ A @ x` and use the
historical gradient `A @ x`. Matrices retain their original floating-point bytes.
The logistic objective is `mean(logaddexp(0, -b*(A@x))) + (1e-4/2)*dot(x,x)`;
its reference minimum is not supplied and must not be assumed to be zero.

The reusable five-method runner is `src/power_reset_spectral_comparison/core.py`.
`B` means power-reset RHGD. The underlying frozen step/reset source is
`study/B/src/power_reset.py`. The old evidence/experiment tools still expect large
private raw results and are not the new course harness. Use the core recurrence
and small fixtures to start; the full configurable harness remains new work.

At the first group sync, agree common problem inputs, start, method parameters,
gradient budget, and seed, plus output fields: current loss, iteration, actual and
literal gradients, objectives, reset locations, and failure status. Leo can start
with the five existing methods while others independently check their methods on
the shared problems. Keep each method's integrator and source settings explicit.

## 5. Experiment and collaboration plan

1. Everyone clones the repo, runs smoke/tests, and reads their method's source.
2. Method owners validate one small example; Leo prepares the shared interface
   and matched linear/log/clustered fixtures. Agree budgets and freeze settings.
3. Compare the method families on quadratics using the same problems and actual
   gradient counts. Control initial total objective when isolating modal-energy
   effects; retain the historical common-start convention as a separate comparison.
4. Plan one shared regularized-logistic validation after the quadratic suite is
   stable. Each method owner supplies their method. This can be deferred if time
   is insufficient; logistic evidence already exists but the combined comparison
   has not been run. A kinetic/mean-dissipation rule must be validated for the
   actual discrete map, not assumed equivalent across RHGD and RCM.
5. Each person contributes their results and writing; combine into one report
   and presentation. See the [detailed checklist](docs/EXPERIMENT_PLAN.md).

Use a feature branch and a pull request for a bounded change. Before merging:

```bash
source scripts/activate_env.sh
python -m pytest
ruff check .
ruff format --check .
```

Run full benchmarks in a suitable Slurm allocation on Grace with verified current
account/partition, one numerical thread, explicit budgets and a fresh output path.
Record configs, seeds, source hashes, failures, and all paid work. Distinguish
first/sustained targets and current/best loss. Do not mix timing boundaries or
retune the final cases to rescue an unfavorable result.

Large trajectories stay outside Git. Agree a group artifact-storage location
before full runs; it has not yet been set up. The source, compact inputs, and
summaries in Git are sufficient to start implementing and checking methods.
