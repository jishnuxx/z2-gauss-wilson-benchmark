# Four-link blind-spot model

## Geometry and Pauli convention

Data qubits `q0,q1,q2,q3` are Z2 links ordered around a periodic square. At
vertex `s`, the local Gauss generator is the product of electric `X` operators
on the two incident links:

\[
G_s=X_sX_{(s+1)\bmod 4}.
\]

The closed-loop observable is

\[
W=Z_0Z_1Z_2Z_3.
\]

Every `G_s` commutes with `W` because their supports overlap on two links. The
closed graph has one redundancy, `G0 G1 G2 G3 = I`.

## State and errors

The target state is

\[
|\psi_+\rangle=\frac{1}{\sqrt 8}
\sum_{x:\,|x|\;\mathrm{even}}|x\rangle,
\]

which has `G_s=+1` for all vertices and `W=+1`.

The gauge-violating error `Z0` anticommutes with `G0` and `G3`. The
gauge-preserving string error `X0` commutes with every `G_s` but anticommutes
with `W`. Therefore `X0|psi_+>` remains in the selected local gauge sector and
has `W=-1`.

This four-link construction is deliberately an algebraic minimum. Its `W` is a
contractible single-plaquette Wilson loop, and `X0` is a local electric operator
that changes that loop eigenvalue; it is not yet a noncontractible logical
string on a torus. The demonstrated statement is therefore the observable-aware
blind spot (`Gauss pass` does not certify this Wilson observable), not a claim of
topological protection or code distance.

## Readout convention

The preparation Clifford is a four-qubit GHZ chain followed by Hadamards on all
data qubits. Applying its inverse before measurement maps stabilizer violations
to data bits in canonical order

```text
(q0, q1, q2, q3) = (W, G0, G1, G2) violation bits.
```

Qiskit prints count keys as `c3 c2 c1 c0`; analysis reverses that display order.
`G3` violation is inferred as `q1 xor q2 xor q3`. A shot passes Gauss selection
when `q1=q2=q3=0`; it passes string-aware selection when all four bits are zero.

The direct Wilson circuit measures all data qubits without a basis rotation and
uses bit parity. The ancilla-based Gauss circuit prepares ancilla `|+>`, applies
ancilla-to-data CNOTs over the check support, returns the ancilla to the Z basis,
and measures it.
