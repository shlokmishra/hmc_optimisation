# Main-paper experimental synthesis

Evidence reviewed: **2026-09-17**. All five requested main-paper panels pass exact
same-environment source parity. Figure 1-right is the explicitly requested
**million-step extension** of a 10,000-step notebook default. This synthesis uses
the retained runs only; no optimizers were rerun and no Figures 3–7 were started.

The main scientific result is conditional: **RHGD is competitive with accelerated
baselines, benefits relative to them under the tested α misspecification, and is
sensitive to refreshment tuning. It is not uniformly the fastest method.** The
weak quadratic also exposes a failure of the author's log-band statistic near
zero that must not be interpreted as optimization divergence.

## Evidence and interpretation

The primary reference is the supplied [paper](../../Hamiltonian%20Descent%20Algorithms%20for%20Optimization.pdf):
Section 5.1 and Figure 1 on pages 8–9; Section 5.2 and Figure 2 on page 9;
Appendix H for data generation, stepsizes and implementation details. The authors'
Section 6 gives a broad favorable summary; the more qualified, panel-specific
Section 5 conclusions are used below. The pinned notebook is commit
`37962b3074a5c9c6248ef062ffa665a2177a1301` in `external/RHGD`.

“Authors' conclusion” below paraphrases the paper. “Observed” describes retained
arrays; “Interpretation” is our bounded inference from that evidence. Exact source
parity verifies our replay against separate direct execution of author code in
our environment, not the algorithm's mathematical correctness or exact historical
numerical agreement. Original published arrays and a complete environment lock
are unavailable. The paper reports Python 3.10.12; our metadata records 3.13.5.
That difference alone does not diagnose any discrepancy.

All problems have dimension 100. Randomized curves average **five algorithm runs
on one fixed generated problem**, not five independent datasets. Data seed is 42;
replicate seeds are 0–4, with the author's shared RNG order preserved. GD and AGD
are deterministic single runs. Saved bands are the author's delta-method
log-standard-deviation construction, not confidence intervals for the mean.

| Panel | Retained job | Iterations | Exact numeric/coordinate comparisons | Detailed evidence |
| --- | --- | ---: | ---: | --- |
| Figure 1-left | 19769000 | 1,000,000 | 24 passed | [Report](FIG1_LEFT.md), [parity](../../results/reproduction/fig1-left-19769000/author_parity.json) |
| Figure 1-middle | 19770301 | 1,000,000 | 25 passed | [Report](FIG1_MIDDLE.md), [parity](../../results/reproduction/fig1-middle-19770301/author_parity.json) |
| Figure 1-right extension | 19772099 | 1,000,000 | 24 passed, including NaN/Inf positions | [Report](FIG1_RIGHT.md), [parity](../../results/reproduction/fig1-right-19772099/author_parity.json) |
| Figure 2-left | 19768992 | 1,000 | 33 passed | [Report](FIG2_LEFT.md), [parity](../../results/reproduction/fig2-left-19768992/author_parity.json) |
| Figure 2-right | 19734521 | 200 | 26 passed | [Report](FINDINGS.md#figure-2-right-first-full-panel-2026-09-11), [parity](../../results/reproduction/fig2-right-19734521/author_parity.json) |

For a reproducible comparison above the numerical floor, tables below use the
**first recorded index k after which the plotted curve stays at or below a stated
threshold through the end of the retained run**. This is stricter than a first
oscillatory dip. Indexing starts at zero and losses precede updates. “Not reached”
means not reached sustainably within the run. These are descriptive iteration
comparisons, not fitted convergence rates, statistical significance tests, or
runtime/oracle-cost comparisons. For randomized methods the threshold applies
to the mean curve, not to every replicate.

The [machine-readable array summary](../../results/reproduction/main-paper-synthesis-20260917/array_summary.json)
contains thresholds, sampled values, terminal values, replicate diagnostics and
input hashes. Its [measurement source](../../results/reproduction/main-paper-synthesis-20260917/measurement_source.py)
only reads saved NPZ/JSON artifacts. Original run directories were not modified.

## Figure 1-left — exact strong-convexity information

**Setting and question.** Minimize f(x)=½xᵀAx for a dense quadratic with L=500,
κ=10⁷ and true, supplied α=L/κ=5×10⁻⁵. The spectrum is linearly spaced between α
and L. All methods use the selected author steps: η=1/L=0.002 for GD/AGD/CAGD,
h=1/√L for RHGD. One million iterations test whether RHGD competes with GD and
established acceleration when the strong-convexity parameter is known exactly.

**Authors' conclusion.** Section 5.1 says all accelerated methods outperform GD;
RHGD is slower than AGD/CAGD with exact parameter knowledge, while competitive
during early iterations.

**Observed in our arrays.** The long-run ordering supports that qualified claim.

| Method | Sustained loss ≤10⁻⁸: k | Sustained loss ≤10⁻¹²: k | Final recorded loss |
| --- | ---: | ---: | ---: |
| GD | Not reached | Not reached | 8.24613×10⁻⁶ |
| AGD | 16,750 | 33,216 | 1.95316×10⁻²⁷⁵ |
| CAGD | 16,675 | 33,024 | 7.45437×10⁻²⁷¹ |
| RHGD | 33,378 | 74,902 | 5.59802×10⁻¹⁴⁷ |

All captured numerical arrays are finite. The extremely small final values are
outputs of this quadratic/source implementation, not accuracy certificates for
general optimization problems. Thresholds well before those values show that
RHGD substantially improves on GD but loses to AGD/CAGD here.

**Parity and historical caveat.** All 24 arrays match direct author execution;
no numerical setting overrides were needed. The paper clips the displayed range
near loss 10⁻¹⁴ and roughly 10⁵ iterations, whereas the canonical notebook-style
plot retains the full million-step range. The separately labeled `paper_window.*`
view is display-only. Historical shapes/order are broadly consistent; exact
historical arrays remain unavailable.

**Interpretation for RHGD.** Acceleration relative to GD is a demonstrated
strength on this ill-conditioned problem. Superiority over optimally informed
AGD/CAGD is not: this panel supplies explicit counterevidence to a universal
“RHGD is fastest” reading of the paper's broader closing summary.

## Figure 1-middle — overestimated α

**Setting and question.** Keep the same quadratic, L=500 and true α=5×10⁻⁵, but
supply **α̂=0.01**, an overestimate by a factor of 200, wherever AGD/CAGD/RHGD
require strong-convexity information. Keep the same stepsizes and million-step
count. The matrix, initial point and complete GD trace are verified identical to
Figure 1-left. This isolates sensitivity to incorrect algorithmic information
rather than changing the objective's true curvature.

**Authors' conclusion.** Section 5.1 reports substantial AGD/CAGD degradation
under overestimated α, with RHGD remaining stable and outperforming them later.

**Observed in our arrays.** The ranking reverses at late-stage targets:

| Method | Sustained loss ≤10⁻⁸: k | Sustained loss ≤10⁻¹²: k | Final recorded loss |
| --- | ---: | ---: | ---: |
| GD | Not reached | Not reached | 8.24613×10⁻⁶ |
| AGD | 307,596 | 717,150 | 1.72778×10⁻¹⁵ |
| CAGD | 307,592 | 717,146 | 1.72773×10⁻¹⁵ |
| RHGD | 158,364 | 368,160 | 4.55934×10⁻²⁵ |

All retained arrays remain finite. RHGD reaches the 10⁻⁸ threshold about twice
as early as AGD/CAGD, but it also slows relative to its exact-α run: 158,364 versus
33,378 iterations. AGD/CAGD slow by about 18 times at this target; RHGD by about
4.7 times. Thus **relative robustness does not mean insensitivity**.

The source uses refresh probability h√α̂ instead of h√α for RHGD: approximately
0.004472 versus 0.000316 per iteration. This verified parameter change increases
the refresh probability by √200. It identifies what changed in the code; the
experiment does not separately identify a causal mechanism for the resulting
relative advantage.

**Parity and historical caveat.** All 25 arrays match direct execution after
selecting the existing α̂=0.01 branch from the author's loop. Function bodies are
unchanged. The historical panel uses a narrower vertical range and different
legend placement; qualitative late-stage ordering agrees, but exact historical
numerical agreement is unverified.

**Interpretation for RHGD.** This is the strongest main-paper evidence for a
practical advantage under uncertain α: less degradation and faster late-stage
convergence on the same problem. It covers one overestimate, one spectrum and
five randomized runs. It does not establish robustness to underestimation, all
misspecification magnitudes, or other problem families; Figures 3–7 were not run.

## Figure 1-right — weak quadratic and million-step extension

**Setting and question.** Use a dense quadratic with intended α=0, L=500,
linearly spaced eigenvalues from zero to 500 and the author's symmetrization.
Use the weak-convexity algorithm variants with η=0.002 and h=√0.002. RHGD's
refreshment rate γₖ=17/[2(k+9)h] gives refresh probability 17/(2k+18).
The question is whether decaying refreshment provides useful acceleration without
a positive strong-convexity constant.

**Authors' conclusion.** Section 5.1 describes RHGD as fastest in this panel and
better than AGD/CAGD throughout the iterations. That is the authors' claim about
their displayed experiment, not an established pointwise ordering for our extension.

**Observed in our arrays.** At all four checked sustained targets (10⁻⁶ through
10⁻¹²), RHGD reaches the target first. Two representative targets are:

| Method | Sustained recorded loss ≤10⁻⁸: k | Sustained recorded loss ≤10⁻¹²: k |
| --- | ---: | ---: |
| GD | 840 | 1,294 |
| AGD | 559 | 1,244 |
| CAGD | 822 | 2,136 |
| RHGD | 380 | 753 |

The observed advantage is target-dependent and does not imply pointwise dominance.
CAGD's oscillatory tail even reaches the stricter sustained target later than GD.
All methods subsequently reach tiny signed losses near zero; terminal means are
approximately −3.14×10⁻¹⁵ (GD), 3.78×10⁻¹⁶ (AGD), −1.59×10⁻¹⁵ (CAGD) and
−5.89×10⁻¹⁶ (RHGD). Such floor values cannot rank optimization accuracy.

**Verified numerical/statistical issue.** Raw losses and means stay finite, but
negative means invalidate the author's unguarded `log10(mean_loss)`. The stored
NaN masks agree exactly with the negative-mean masks. CAGD and RHGD respectively
have 995,231 and 997,148 NaNs in each bound; upper bounds additionally contain
15 and 14 infinities. The first negative mean occurs at k=2,738 and k=998,
respectively—already within the first 10,000 steps of this extension. The issue
must not be described as arising only after the published iteration range.

The resulting canonical log plot is distorted. Its original PNG/PDF are retained;
[signed_loss_diagnostic.png](../../results/reproduction/fig1-right-19772099/signed_loss_diagnostic.png)
is a separate, full-range display of saved signed means without invalid bands.
No matrix projection, loss clipping or numerical correction was made. Roundoff
in matrix construction and objective evaluation is a **working hypothesis** for
the signed residuals; the contributions have not been isolated. The log-band
failure mechanism is verified, while that deeper diagnosis remains provisional.

**Parity and historical caveat.** All 24 arrays, including matching NaN/Inf
positions, pass direct-author parity at **the requested million iterations**.
The notebook default and historical panel extend to 10,000. Increasing N changes
RHGD's RNG stream because CAGD first consumes N+1 exponential draws on their
shared generator. Our million-step prefix is therefore not a default-run replay.
The historical figures show a positive floor near 10⁻¹⁵; our extension has signed
residuals and invalid bands. Source parity does not settle that historical difference.

**Interpretation for RHGD.** The recorded pre-floor convergence supports a useful
weak-quadratic advantage at the checked targets. The million-step extension adds
fidelity and numerical-diagnostic evidence, not one million steps of meaningful
accuracy improvement. The broken bands are a limitation of the reported statistic,
not evidence that raw optimizer trajectories diverged or a reason to silently
repair the author implementation.

## Figure 2-left — adaptive logistic regression and refreshment sensitivity

**Setting and question.** Minimize the synthetic logistic loss plus
(α/2)‖x‖², with 500 observations, dimension 100 and α=10⁻⁴. Run 1,000 iterations
using author adaptive steps, initially η=h=1. Compare RHGD rates γ=c√α for
**c=1 and c=2**, five runs each, with adaptive GD/AGD/CAGD. The source's actual
refresh probability is c√α times the adaptively updated h. This tests performance
on a nonquadratic problem without a known L, and sensitivity to refreshment rate.

**Authors' conclusion.** Section 5.2 says c=2 gives faster, more stable convergence
than the theorem-motivated c=1; both beat GD at late iterations and are comparable
to AGD/CAGD.

**Observed in our arrays.** Later-stage targets support the advantage of c=2:

| Method | Sustained plotted gap ≤10⁻⁶: k | Sustained plotted gap ≤10⁻¹⁰: k |
| --- | ---: | ---: |
| GD | 234 | 461 |
| AGD | 166 | 301 |
| CAGD | 164 | 233 |
| RHGD c=2 | 158 | 263 |
| RHGD c=1 | 210 | 368 |

At k=100, c=2 has mean shifted loss 9.72×10⁻⁴ and sample standard deviation
1.49×10⁻³, versus 1.16×10⁻² and 1.95×10⁻² for c=1. At k=200, those quantities
are 9.42×10⁻⁸ and 2.09×10⁻⁷ versus 1.37×10⁻⁶ and 2.49×10⁻⁶. However, at k=50,
c=2's mean and standard deviation are **larger** (0.503 and 0.676 versus 0.397
and 0.543). These sampled checks support improved later absolute performance and
dispersion, not uniformly better stability at every iteration or in relative terms.
Sample deviations here use ddof=1 and are descriptive; they are not the author's
band formula or a significance test.

CAGD reaches 10⁻¹⁰ before either RHGD rate; c=2 beats AGD there, whereas c=1
trails it. Both beat GD. The two RHGD configurations consume successive segments
of a shared RNG, rather than identical random draws in a paired comparison.
Five trajectories do not establish an optimal rate or a universal causal law that
more refreshment is always better.

**Parity and historical caveat.** All 33 arrays pass exact direct-author parity;
no warnings/nonfinite values were captured. The plotted “gap” subtracts the
minimum across all compared traces, f★≈0.020236446186274216, rather than a
separately certified optimum. Randomized shifted losses are clipped at 10⁻²⁰;
the first randomized plotted value is overwritten with the unshifted initial
loss. Terminal plotted values are near 10⁻¹⁷–10⁻¹⁶ and their ordering differs
from the saved notebook. In particular, c=1 ends below c=2 despite slower
pre-floor convergence. That terminal ordering is not a sound basis for selecting
the refreshment rate. Broad historical shapes agree; exact historical parity and
the cause of floor differences remain unresolved. Floating-point/library effects
and cancellation are hypotheses, not verified explanations.

**Interpretation for RHGD.** Adaptive RHGD is competitive beyond quadratics,
but refreshment is a consequential tuning choice. This evidence favors c=2 over
c=1 for late convergence on this dataset, while showing remaining variability
and target-dependent competition with AGD/CAGD. The theorem's suggested rate need
not be the empirically best choice in this implementation and setting.

## Figure 2-right — weakly convex adaptive logistic regression

**Setting and question.** Remove regularization (α=0) from the synthetic logistic
problem with 500 observations and 100 features. Run 200 iterations, initial
η=h=1 and author adaptive updates, with five randomized replicates. RHGD uses
the decaying refresh probability 17/(2k+18). The question is whether its
weak-convexity behavior remains competitive with adaptive accelerated baselines
on a nonquadratic objective.

**Authors' conclusion.** Section 5.2 reports accelerated methods outperforming GD,
with RHGD comparable to AGD/CAGD, rather than claiming a clear RHGD win here.

**Observed in our arrays.** All retained values are finite and no warnings were
captured. The raw terminal losses at k=199 are:

| Method | Sustained raw loss ≤10⁻⁸: k | Final recorded raw loss |
| --- | ---: | ---: |
| GD | Not reached | 1.05312×10⁻³ |
| AGD | 163 | 2.56693×10⁻¹⁰ |
| CAGD | 164 | 2.47428×10⁻¹⁰ |
| RHGD | 172 | 5.94866×10⁻¹⁰ |

RHGD joins the accelerated methods far below GD, but AGD/CAGD reach this target
sooner and have smaller terminal loss. This supports comparable performance, not
RHGD superiority on this panel. The clean raw-loss behavior also shows that the
weak quadratic's invalid-band issue is not observed in every α=0 experiment.

**Parity and historical caveat.** All 26 arrays pass direct-author parity with
no numerical overrides. Historical shapes, ordering, extent and terminal scales
are visually consistent, but no original numerical arrays were supplied or
digitized. The source plots **raw logistic loss**, despite an f−f★ axis label;
these values are not independently certified optimality gaps. This convention
differs from Figure 2-left's trace-referenced shifted values.

**Interpretation for RHGD.** Decaying refreshment plus adaptive steps gives a
competitive weak-logistic method in this test. The observed cost is a modest
iteration disadvantage relative to AGD/CAGD at the reported target. Neither a
wall-clock speed advantage nor a general weak-convexity advantage follows.

## What the five panels establish for the project's direction

1. **Execution fidelity is established for the five requested settings.** Author
   numerical semantics were retained and independent direct execution matched.
   The right-quadratic iteration override and its invalid bands remain explicit.
2. **The strongest relative advantage is conditional.** RHGD is more tolerant of
   the tested α overestimate than AGD/CAGD, and reaches checked weak-quadratic
   targets sooner. Exact-α quadratics favor AGD/CAGD; weak logistic shows parity
   in broad performance rather than dominance.
3. **Refreshment deserves scientific attention.** Figure 2-left demonstrates
   consequential sensitivity to c=1 versus c=2, but does not identify an optimal
   schedule, a general stability mechanism, or an automatic tuning rule.
4. **Numerical reporting needs an explicit boundary.** Negative quadratic losses
   and invalid log bands, trace-derived/clipped logistic gaps, and raw-loss axis
   labels limit what can be inferred near zero. Any corrected statistic or
   higher-precision diagnosis must remain a separate study from these reproductions.
5. **Generalization remains open.** Five algorithm seeds on fixed synthetic
   problems do not establish dataset robustness, a universal convergence ordering,
   wall-clock efficiency, or gradient/oracle efficiency. Existing allocation times
   include replay, validation, plotting and I/O; they are not algorithm benchmarks.

The evidence supports framing RHGD as an alternative worth studying for parameter
uncertainty and refreshment design, while retaining strong AGD/CAGD baselines.
It does not yet justify promoting RHGD as generally faster. Broader α sensitivity,
refreshment mechanisms, and precise numerical-floor causes remain open questions,
not findings inferred from unrun appendix panels.

**Stop:** synthesis complete. No Figures 3–7 were submitted or run in this work.
