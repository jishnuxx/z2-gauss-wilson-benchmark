# Circuit and encoding reference

This note records the logical quantum circuits used in the blind-spot benchmark and clarifies which results are exact simulation versus circuit execution.

## 1. Four-qubit static blind-spot circuit

Code path:

```text
src/z2lgt/blindspot_circuits.py
```

Saved artifacts:

```text
circuits/blindspot/qasm/no_error.qasm
circuits/blindspot/qasm/gauge_violating.qasm
circuits/blindspot/qasm/gauge_preserving_string.qasm
circuits/blindspot/qiskit/no_error.qpy
circuits/blindspot/qiskit/gauge_violating.qpy
circuits/blindspot/qiskit/gauge_preserving_string.qpy
```

Logical flow:

```text
Prepare |psi_+>  ->  inject case I/Z0/X0  ->  apply Prep^\dagger  ->  measure q0..q3
```

The preparation circuit is

```text
H(q0) -> CX(q0,q1) -> CX(q1,q2) -> CX(q2,q3) -> H on q0..q3.
```

The error cases are

```text
I   = no error
Z0  = gauge-violating error
X0  = gauge-preserving string/Wilson-sector error
```

Encoding and diagnostics:

```text
q0..q3 = four loop-link qubits
G0 = X0 X1
G1 = X1 X2
G2 = X2 X3
G3 = X3 X0
W  = Z0 Z1 Z2 Z3
```

The joint diagnostic uses a static Clifford decode. In canonical bit order,

```text
c0..c3 = (W, G0, G1, G2) violation bits
G3_violation = c1 xor c2 xor c3.
```

This is why no dynamic circuit is required for the static Emerald blind-spot run.

Resource summary:

```text
Logical Qiskit no-error circuit: 4 qubits, depth 19, 6 CX, 4 measurements
Emerald-compiled static circuits: depth 15-16, 6 CZ
```

## 2. Periodic dynamics and joint-readout circuit

Code paths:

```text
src/z2lgt/periodic_circuits.py
src/z2lgt/periodic_readout.py
```

Saved artifacts:

```text
circuits/periodic/qasm/periodic_Wplus_t0p8_dt0p4.qasm
circuits/periodic/qasm/periodic_Wminus_t0p8_dt0p4.qasm
circuits/periodic/qasm/periodic_joint_Wplus_t0p8_dt0p4.qasm
circuits/periodic/qasm/periodic_joint_Wminus_t0p8_dt0p4.qasm
circuits/periodic/qiskit/periodic_Wplus_t0p8_dt0p4.qpy
circuits/periodic/qiskit/periodic_Wminus_t0p8_dt0p4.qpy
circuits/periodic/qiskit/periodic_joint_Wplus_t0p8_dt0p4.qpy
circuits/periodic/qiskit/periodic_joint_Wminus_t0p8_dt0p4.qpy
```

Logical qubit layout:

```text
q0..q3  = matter sites m0..m3
q4..q7  = gauge links l0..l3
q8..q10 = ancillas for G0,G1,G2
q11     = ancilla for W
```

Target-state preparation:

```text
X(m0), X(m1)
H(l0)
CX(l0,l1), CX(l0,l2), CX(l0,l3)
X(l1), X(l2), X(l3)
```

The `Wminus` comparison circuit applies

```text
Z(l0)
```

before evolution. In this model, `Z(l0)` commutes with every local Gauss check but anticommutes with the conserved Wilson loop.

The dynamics circuit then applies a first-order Trotter product formula with

```text
t = 0.8
dt = 0.4
number of Trotter steps = 2.
```

Joint readout:

```text
c0..c3 = measured matter occupations
c4..c6 = Gauss violation bits g0..g2
c7     = Wilson violation bit
```

The redundant check is inferred as

```text
g3 = m0 xor m1 xor m2 xor m3 xor g0 xor g1 xor g2.
```

Shot-level filters:

```text
Gauss-only accept:    g0 = g1 = g2 = g3 = 0
Gauss+Wilson accept: g0 = g1 = g2 = g3 = 0 and c7 = 0
```

Resource summary:

```text
Logical Qiskit joint-readout circuit: 12 qubits, depth 138, 80 two-qubit operations, 8 measurements
Latest Emerald seed-1 periodic repeat: depth 125, 101 CZ, 8 measurements
Earlier 1000-shot periodic readout run: depth 134, 100 CZ, 8 measurements
```

## 3. Simulation/hardware boundary

The plots do not all come from the same execution mode:

```text
Figure 2: static Qiskit/Aer + Emerald hardware blind-spot circuit
Figure 6: exact diagonalization baseline; no measurement circuit
Figure 7: exact single-fault mitigation model
Figure 8: periodic Qiskit joint-readout circuit compiled and run on IQM Emerald
```

This boundary is important for presentation wording. The simulator shows the problem and the mitigation mechanism; the Emerald runs show that the diagnostic circuits can be compiled and read out on hardware.

## 4. Reproduction commands

Regenerate the static blind-spot circuits and ideal processed CSV:

```bash
python scripts/run_ideal.py --shots 20000
```

Regenerate the periodic Trotter sector circuits:

```bash
python scripts/run_periodic_two_sector_circuits.py
```

Regenerate the periodic joint-readout circuits and ideal shot analysis:

```bash
python scripts/run_periodic_joint_readout.py --shots 20000
```

These commands do not require IQM access.
