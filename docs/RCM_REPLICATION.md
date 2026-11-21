# RCM replication

## Step 2. Quadratic example from Section 5.1

We selected the smooth quadratic experiment in Section~5.1 of
\emph{A Piecewise Conservative Method for Unconstrained Convex Optimization}
by Scagliotti and Colli Franzone (arXiv:2009.11233v4).
Our replication target is the upper-right panel of Figure~2, which compares
restart criteria on a single problem instance. We focus on three variants:
\texttt{RCM-kin}, \texttt{RCM-mmd-r}, and \texttt{RCM-mmd-dr}.
For each variant, we will plot the gradient norm
$\|\nabla f(x_k)\|_2$ against the iteration index $k$ over 300 iterations.

Run command: bash -c 'source scripts/activate_env.sh && python scripts/prepare_rcm_quadratic.py'