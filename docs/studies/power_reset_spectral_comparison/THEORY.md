# Theory of frozen quadratic Candidate B

This analysis concerns the unchanged trigger and exact symmetric PSD quadratic
arithmetic. It is separate from the empirical comparison in [REPORT.md](REPORT.md).
The numerical experiments retain their original rounded matrices. No theoretical
assumption here changes their matrices, cap, trigger, or initial conditions.

## 1. Map, power and the unresolved complexity question

Let h=1/sqrt(L), s=lambda/L, a=1-s, and normalize one eigencoordinate by
q=sqrt(lambda)*x, p=y. Before a reset, the frozen RHGD update is

```
[q_plus]   [ a          sqrt(s)*a ] [q]
[p_plus] = [-sqrt(s)*a  1-s*a     ] [p] = M(s)[q,p]^T.
```

The global trigger is sum_i sqrt(lambda_i)*q_i*p_i, evaluated at the new
endpoint. Negative power arms the segment; the first subsequent nonnegative
power zeroes every p_i and retains every q_i. A cap also zeroes momentum.
Each update costs two distinct gradients. The determinant is a and trace is
2a+s^2. Thus the map already damps modes; it is not Hamiltonian leapfrog.

The useful open question is whether total work spent on fast-triggered segments
can be charged to objective reduction, before slow modes contract. A contraction
per completed segment alone does not bound the number or cost of segments.

Power is a proxy, even on a quadratic. From an endpoint (x,y), the next unreset
position displacement is d=h*y-h^2*A*x-h^3*A*y. Its objective difference is
(A*x)^T*d + .5*d^T*A*d. Neither that expression nor the preceding difference is
h times the endpoint power. The old B study already demonstrated disagreements;
this study keeps actual before/after and next observed differences reconstructable
from raw losses, without new counterfactual-gradient probes.

## 2. Proved: energy dissipation and completed-segment objective descent

For 0<=s<=1,

```
I-M(s)^T M(s) =
[ s*(1+s-s^2)      s^(5/2)*(1-s)       ]
[ s^(5/2)*(1-s)    s*(1-s)*(1+s^2)    ].
det(I-M^T M) = s^2*(1-s^2).
```

Both diagonal entries and the determinant are nonnegative. This proves positive
semidefiniteness, including the endpoints. Therefore the total quadratic energy
H=.5*sum_i(q_i^2+p_i^2) cannot increase within an unreset segment. A zero-velocity
reset cannot increase H either. Every segment starts with H=f. Consequently:

**Proposition 1.** For an exact symmetric PSD quadratic and h^2*L<=1, every
completed segment of frozen B satisfies f_end<=f_start, and every intermediate
objective in that segment is <=f_start. This holds for power and cap resets.
The individual update objectives need not be monotone.

This follows from the discrete map, not from the power sign. It supplies an
endpoint-retention safety property but no uniform strict contraction or work
rate. Null directions have no objective contribution. Floating-point gradients
of slightly nonsymmetric stored matrices are outside this exact proposition.
This energy calculation also appears in the completed Candidate C analysis;
it is not claimed as a new consequence of adaptive restart.

## 3. Proved restricted result: one active curvature, cap inactive

Assume all initially nonzero coordinates have the same positive curvature
lambda, zero initial velocity, and 0<s=lambda/L<=1/4. Coordinates outside that
eigenspace are exactly zero. The global trigger then has the scalar power sign.
Let rho=sqrt(a), and define theta in (0,pi/2) and beta>0 by

```
cos(theta) = (2a+s^2)/(2*sqrt(a))
beta = s^2/(2*sqrt(a)*sin(theta)),    phi=atan(beta).
```

Starting from q_0=1, p_0=0, direct diagonalization/Cayley-Hamilton gives

```
r_k = q_k = a^(k/2) * [cos(k*theta)-beta*sin(k*theta)]
p_k = -sqrt(s)*a^((k+1)/2)*sin(k*theta)/sin(theta).
```

The formulas reproduce k=0,1 and the second-order recurrence with trace
2a+s^2 and determinant a, proving them for every integer k. Scaling the initial
amplitude scales both coordinates, so does not change the power sign.

Here r_1=a>0 and p_1<0, so arming occurs on the first update. The first armed
nonnegative power is at

    K = ceil((pi/2-phi)/theta).

Indeed p_k<0 until k*theta reaches pi, while q first becomes nonpositive at K;
K>=2 and K*theta<pi on this parameter range. Equality q_K=0 is included because
the trigger is nonnegative after arming. The operational cap must be >=K.

The phase overshoot at K is in [0,theta). Using

```
sin(theta)^2 = s*a-s^4/(4*a)
(1+beta^2)*sin(theta)^2 = s*a
```

gives the retained-endpoint contraction

    r_K^2 <= a^K*(1+beta^2)*sin(theta)^2 <= s*(1-s) <= 3/16.

Also sin(theta)^2>=s/2 on 0<s<=1/4, hence theta>=sqrt(s/2), and

    K <= pi/sqrt(2s)+1.

After a reset the state again has zero velocity and the same active curvature,
so the same bound applies to every subsequent nonzero segment. If a coordinate
lands exactly at zero, the objective is already solved and no next event is needed.

**Proposition 2.** Under these assumptions, with the cap inactive, at most

    2*(pi/sqrt(2s)+1)*ceil(log(f_0/epsilon)/log(16/3))

gradient evaluations suffice to obtain a completed-segment objective <=epsilon
(for 0<epsilon<f_0). Proposition 1 makes this a sustained bound for every
subsequent iterate. Since lambda>=alpha, the bound is
O(sqrt(kappa)*log(f_0/epsilon)). It applies to one active eigenspace, even if the
ambient spectrum has other unused eigenvalues. It does NOT cover a general
multimode initialization or the actual floating-point slow-only control forever.
The fixed finite cap prevents taking an unrestricted kappa->infinity limit of
this cap-inactive statement; one must retain K<=65536 or explicitly study an
uncapped/scaling-cap mathematical model separately.

## 4. Exact multimode segment recursion and the missing amortization

For segment j starting with zero velocity, write E_{i,j}=.5*lambda_i*x_{i,j}^2.
For modes in the oscillatory range use r_i(k), p_i(k) above; for other modes use
M(s_i)^k directly. The first armed global crossing determines K_j via

    P_j(k) = 2*sum_i E_{i,j}*sqrt(lambda_i)*r_i(k)*p_i(k).

At the completed reset,

    E_{i,j+1} = E_{i,j}*r_i(K_j)^2,
    cost_j = 2*K_j.

This is an exact nonlinear recurrence for the modal weights because the shared
K_j depends on every weight. Proposition 1 applies mode by mode and bounds each
r_i(K_j)^2<=1, but supplies no adequate lower bound on progress per unit work.

For fixed K and s->0, induction in the original recurrence gives

    r_s(K) = 1 - s*K*(K+1)/2 + O_K(s^2),
    -log(r_s(K)^2) = s*K*(K+1) + O_K(s^2).

Thus repeated short segments can give only O(s*K) logarithmic slow contraction
per update. Recovering an accelerated rate would require an amortized inequality,
for example bounding the total short-segment work by O(sqrt(kappa)) times a
logarithmic initial/final potential ratio. Proving uniform long segments is too
strong: observed and admissible global sign cancellation already allows short
ones. Useful candidate potentials would have to track both residual fast-mode
energy and slow-mode contraction, and handle sign cancellation at the crossing.
No such general inequality is proved here.

## 5. Counterexamples attempted; what they establish and fail to establish

**Local mechanism with two active modes, established algebraically.** Take
s_fast=1/4. If L must be the sharp largest eigenvalue, include an additional
zero-amplitude coordinate of curvature L; it stays exactly zero. From
zero velocity, successive fast positions are approximately
.7500, .421875, .0966796875, -.16534423828125; at update 4 its velocity is still
negative, so its power is positive. For sufficiently small s_slow, the slow
position remains positive and its velocity negative through all four updates.
A sufficiently large but finite fast amplitude makes the fourth global power
nonnegative while the earlier fast and slow powers are negative. B therefore
resets at update 4 while the slow mode is descending, with the cap inactive.
This proves the possibility of an early harmful interruption; it does not prove
persistent asymptotic inefficiency.

**Repeated dominance by one fast mode, attempted and insufficient.** Choosing a
very large initial fast amplitude can prolong a fast-dominated transient. But its
reset contraction r_fast(K)^2 is strictly below one at such crossings. For fixed
curvatures, maintaining N similar interruptions requires an initial fast/slow
energy ratio growing exponentially in N in this simple construction. As the slow
curvature decreases, its negative-power threshold also decreases: schematically
the required ratio is proportional to s_slow times rho_fast^(-N), with fixed
short K and rho_fast<1 denoting the fast energy contraction. Thus bounded initial
energies can permit a logarithmic-in-kappa transient, which alone is too short
to contradict an accelerated bound. Making N much larger forces the initial
energy logarithm to grow too. Counting the transient while hiding that initial
energy fails to contradict O(sqrt(kappa)*log(f_0/epsilon)). No negative complexity
theorem follows from this attempt; the schematic estimate is not a theorem about
an arbitrary sequence of varying segment lengths.

**Dense cascade, open.** A ladder of intermediate curvatures may pass control of
the trigger from one band to another as faster modes dissipate. The empirical
matched-spectrum experiment tests whether this materially matters at kappa=1e7.
For a rigorous negative result one still needs a family with stated dimension,
spectral density and normalized initial energies, a proved reset schedule (not
an assumed one), inactive cap, and a divergent ratio of work to
sqrt(kappa)*log(f_0/epsilon). The present work does not construct that family.
Increasing the number of modes or inflating initial objective without accounting
for it is not a counterexample. A fixed finite experiment cannot decide this
asymptotic question.

**Fixed-cap obstruction, known and outside the requested counterexample.** For
sufficiently small s and fixed cap M, short-segment expansion gives only O(s*M^2)
contraction per capped segment. This can obstruct uniform acceleration as kappa
grows, but uses an active cap and therefore does not answer the cap-inactive
multimode question. It is not used to explain the empirical result.

## 6. Relationship to adaptive-restart accelerated gradients

The gradient/displacement restart criterion is already described by
[O'Donoghue and Candes, section 3.2](https://arxiv.org/html/1204.3982v1#S3.SS2).
The comparator in this study uses grad(u)^T*(x_plus-x)>0 with the specified convex
acceleration recurrence. B uses grad(x_plus)^T*y_plus>=0 after strict-negative
arming in a different, dissipative RHGD map. Both aim to remove unhelpful momentum;
that concept is not novel here. Existing adaptive-restart intuition or results do
not automatically transfer to B's map, two-gradient work, or multimode trigger.
This single comparator does not represent all possible adaptive-restart methods.

## 7. Claims ledger and next theoretical step

- **Proved above:** modal map, energy inequality, segment endpoint descent;
  restricted one-active-curvature accelerated work bound with inactive cap;
  exact modal-weight recursion; fixed-K slow expansion; existence of a fast-caused
  early reset while the slow coordinate descends.
- **Empirical only:** finite-problem competitive costs and reset contributions,
  reported separately. These do not prove or disprove an asymptotic rate.
- **Open:** a spectrum/amplitude class admitting a multimode amortized work bound;
  a normalized dense-spectral cap-inactive counterexample; finite-precision sign
  sensitivity and general nonquadratic guarantees.

If theory continues, work directly on the modal-weight recursion and either prove
an amortized potential decrease under explicit spectral/amplitude assumptions or
construct a normalized family violating it. No trigger modification is part of
that next step, and no general-speed claim should be rescued by these restricted
propositions.
