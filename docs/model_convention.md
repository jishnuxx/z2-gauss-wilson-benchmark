# Model convention

## Layout and boundaries

An open chain has `N` matter qubits and `N-1` gauge-link qubits. Matter uses
indices `0..N-1`; link `l`, between sites `l` and `l+1`, uses index `N+l`.
The two absent boundary links have fixed electric eigenvalue `+1`.

The link qubits use a Hadamard-rotated convention relative to the common
electric-X notation. This makes the electric field and Gauss generators
diagonal in the computational basis, which is required for classifying every
sampled bitstring without auxiliary measurement circuits.

## Hamiltonian

With an irrelevant scalar mass offset omitted,

\[
H=-\frac{m}{2}\sum_i(-1)^i Z_i-g\sum_l Z_l
-\frac{J}{2}\sum_l\left(X_l^{(m)}X_l^{(g)}X_{l+1}^{(m)}
+Y_l^{(m)}X_l^{(g)}Y_{l+1}^{(m)}\right).
\]

Defaults are `m=0.5`, `g=0.35`, and `J=1.0`. The same `PauliTerm` list builds
the dense ED matrix and each Qiskit product-formula step.

## Gauss law

For interior sites,

\[
G_i=Z_{i-1}^{(g)}Z_i^{(m)}Z_i^{(g)},
\]

with the absent boundary factors replaced by `+1`. The selected physical
sector is `G_i=+1` for every site. A canonical bit tuple is ordered
`(q0,q1,...,qN-1)`. Qiskit count keys are reversed on input because Qiskit
prints the highest classical bit first.

The default localized-imbalance state has matter occupations `(1,1,0,...)`;
link bits are solved recursively from `G_i=+1`. Fixed `+1` boundaries imply
even total matter parity.

## Observables

- matter occupation `n_i=(1-Z_i)/2`;
- staggered charge imbalance `N^-1 sum_i (-1)^i n_i`;
- mean link electric field `mean_l Z_l`;
- Gauss-law violation rate;
- right-edge matter occupation as the early-time finite-size transport
  diagnostic.

All are diagonal in the current measurement basis. No diffusion coefficient is
inferred.

