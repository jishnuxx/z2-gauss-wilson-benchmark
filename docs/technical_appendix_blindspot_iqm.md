# Technical appendix: minimal IQM blind-spot benchmark

This appendix records the exact algebra, circuit readout map, and IQM run identity for the four-qubit \(\mathbb{Z}_2\) Gauss/Wilson blind-spot benchmark.

## A. Algebra

Data qubits \(q_0,q_1,q_2,q_3\) are ordered around a periodic four-link loop. The local Gauss generators are

```text
G0 = X0 X1
G1 = X1 X2
G2 = X2 X3
G3 = X3 X0
```

with one redundancy,

```text
G0 G1 G2 G3 = I.
```

The Wilson/string observable is

```text
W = Z0 Z1 Z2 Z3.
```

All \(G_s\) commute with \(W\), because each local \(X_sX_{s+1}\) check overlaps the \(Z_0Z_1Z_2Z_3\) loop on two qubits.

The target state is the simultaneous \(+1\) eigenstate of \(G_0,G_1,G_2,G_3,W\):

```text
|psi_+> = (1/sqrt(8)) sum_{x: parity(x) even} |x>.
```

The two diagnostic faults are

```text
E_gv     = Z0
E_string = X0
```

Their algebraic roles are

| Operator | Relation to Gauss checks | Relation to \(W\) | Consequence |
|---|---|---|---|
| \(Z_0\) | Anticommutes with \(G_0,G_3\) | Commutes with \(W\) | Gauge-violating fault; locally detected. |
| \(X_0\) | Commutes with all \(G_s\) | Anticommutes with \(W\) | Gauge-preserving string-sector fault; invisible to Gauss-only checks. |

Thus the benchmark tests

```text
P_Gauss ≈ 1  does not imply  W = W_target.
```

## B. Circuit and readout map

The joint diagnostic circuit prepares the target state, injects one of the three cases, applies the inverse preparation Clifford, and measures all four data qubits. No dynamic circuits are required.

The inverse Clifford maps the stabilizer/string violations to measured data bits in canonical order:

```text
(q0, q1, q2, q3) = (W, G0, G1, G2) violation bits.
```

The redundant Gauss violation is inferred as

```text
G3_violation = q1 xor q2 xor q3.
```

Qiskit count keys are printed as `c3 c2 c1 c0`; the analysis reverses that display order before interpreting the canonical bits.

Shot-level acceptance rules:

```text
Gauss-only accept:    q1 = q2 = q3 = 0
Gauss+Wilson accept: q0 = q1 = q2 = q3 = 0
```

The three submitted circuit cases were

```text
no_error
gauge_violating
gauge_preserving_string
```

## C. IQM Emerald run identity

The headline hardware result uses the frozen, reviewed 5000-shot candidate under
`results/iqm/emerald_blindspot_candidate_5000/readiness_manifest.json`.

| Field | Value |
|---|---|
| Quantum computer | IQM Emerald |
| Backend-reported qubits | 54 |
| Native operations | `id`, `delay`, `measure`, `r`, `if_else`, `reset`, `cz` |
| Shots per circuit | 5000 |
| Job ID | `019f7749-5d66-7e71-961d-1ce1de04e5d6` |
| Candidate ID | `a2054490d694845a413c9e2d4694d6fa92a9a70d6fa82b296c50c73cebd35401` |
| Calibration set ID | `314aeb78-d1ec-418f-b1f2-9ab488ff820e` |
| Result JSON | `results/iqm/static_blindspot_5000/blindspot_minimal.json` |

All three circuits used the same logical-to-physical mapping:

```text
q0,q1,q2,q3 -> QB17,QB9,QB10,QB11
```

Circuit resources:

| Case | Depth | Two-qubit gates | Max recorded CZ error | Max recorded readout error |
|---|---:|---:|---:|---:|
| `no_error` | 15 | 6 | 0.002707 | 0.009600 |
| `gauge_violating` | 15 | 6 | 0.002707 | 0.009600 |
| `gauge_preserving_string` | 16 | 6 | 0.002707 | 0.009600 |

## D. Hardware table

Uncertainties are binomial standard errors from 5000 shots. They do not include device drift or systematic calibration uncertainty.

| Case | \(P_{\rm Gauss}\) | \(\langle W\rangle\) | Gauss-only accepted shots | Gauss+Wilson accepted shots | Gauss+Wilson acceptance |
|---|---:|---:|---:|---:|---:|
| `no_error` | 0.9432 ± 0.0033 | +0.9224 ± 0.0055 | 4716 | 4605 | 0.9210 ± 0.0038 |
| `gauge_violating` | 0.0314 ± 0.0025 | +0.9352 ± 0.0050 | 157 | 116 | 0.0232 ± 0.0021 |
| `gauge_preserving_string` | 0.9390 ± 0.0034 | -0.9044 ± 0.0060 | 4695 | 135 | 0.0270 ± 0.0023 |

The target and the gauge-preserving string error have the same local Gauss acceptance within statistical uncertainty, but opposite Wilson sign. This is the hardware-demonstrated blind spot.

## E. Scope

This appendix supports the static four-qubit IQM result only. The periodic dynamics and \(O_{L,R}\) observable results are exact/simulator evidence, not yet IQM hardware dynamics.
