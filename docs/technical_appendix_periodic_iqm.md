# Technical appendix: periodic IQM sector-dynamics run

This appendix records the exact algebra, readout map, IQM job identity, and hardware table for the periodic four-site \(\mathbb{Z}_2\) matter-gauge benchmark.

## A. Algebra and target observable

Data qubits are ordered as matter \(m_0,m_1,m_2,m_3\) on \(q_0..q_3\), followed by periodic links \(\ell_0,\ell_1,\ell_2,\ell_3\) on \(q_4..q_7\). The local Gauss checks are

```text
G0 = Z_m0 Z_l3 Z_l0
G1 = Z_m1 Z_l0 Z_l1
G2 = Z_m2 Z_l1 Z_l2
G3 = Z_m3 Z_l2 Z_l3
```

The conserved Wilson-sector operator is

```text
W = X_l0 X_l1 X_l2 X_l3.
```

The Hamiltonian used for the dynamics is

```text
H = -(m/2) sum_s (-1)^s Z_ms
    -(kappa/2) sum_l [X_ml X_ll X_m(l+1) + Y_ml X_ll Y_m(l+1)].
```

The electric-link term is omitted, so \([H,G_s]=0\) for all \(s\), and \([H,W]=0\). The target sector is \(W=+1\). The wrong-sector comparator is prepared by applying \(Z_{\ell 0}\), which preserves all Gauss checks but flips \(W\to -1\).

The scientific observable is the left-right matter imbalance

```text
O_LR = (n0 + n1 - n2 - n3) / 2.
```

For the reviewed \(t=0.8, dt=0.4\) two-step Trotter point, ideal statevector simulation gives \(O_{LR}^{W+}=0.189405\), \(O_{LR}^{W-}=0.040536\), and sector separation \(0.148869\). Minimum Trotter-vs-exact state fidelity over the two sectors is \(0.912084\).

## B. Circuit and readout map

The joint readout circuit uses 12 qubits: 8 data qubits plus ancillas \(q_8,q_9,q_{10}\) for \(G_0,G_1,G_2\), and \(q_{11}\) for \(W\). Classical bits are interpreted as

```text
c0..c3 = matter occupations m0..m3
c4..c6 = Gauss violation bits g0..g2
c7     = Wilson violation bit w
```

The redundant check is inferred in analysis:

```text
g3 = m0 xor m1 xor m2 xor m3 xor g0 xor g1 xor g2.
```

Shot-level rules:

```text
Gauss-only accept:    g0 = g1 = g2 = g3 = 0
Gauss+Wilson accept: g0 = g1 = g2 = g3 = 0 and w = 0
```

Here \(w=0\) means the target \(W=+1\) sector. Qiskit count keys are stored as `c7..c0`; the analysis reverses them before interpreting canonical bits.

## C. IQM Emerald job identity

| Field | Value |
|---|---|
| Quantum computer | IQM Emerald |
| Backend-reported qubits | 53 |
| Native operations | `id`, `delay`, `measure`, `r`, `if_else`, `reset`, `cz` |
| Job ID | `019f74ca-1c78-7983-8a8f-97974909067e` |
| Candidate ID | `2c46432e3de316ae56722c47014d427e172bca15c6a1676a617408e99fee5d54` |
| Calibration set ID | `548516b7-6a1b-41b7-95cb-8e9992f0095c` |
| Shots per circuit | 1000 |
| Submitted UTC | `2026-07-18T10:33:50.479475+00:00` |
| Completed UTC | `2026-07-18T10:33:58.322652+00:00` |
| Result JSON | `results/iqm/periodic_hardware/periodic_joint_readout.json` |
| Processed CSV | `results/processed/periodic_iqm_joint_readout.csv` |

Both sectors used the same frozen logical-to-physical mapping:

```text
q0..q11 -> QB24,QB15,QB16,QB33,QB17,QB9,QB18,QB25,QB23,QB8,QB26,QB10
```

Circuit resources for both `Wplus` and `Wminus`:

| Depth | CZ gates | Measurements | Max recorded CZ error | Max recorded readout error |
|---:|---:|---:|---:|---:|
| 134 | 100 | 8 | 0.011695 | 0.019350 |

## D. Hardware table

Uncertainties shown for \(P_{\rm Gauss}\) and \(O_{LR}\) are shot-noise standard errors from 1000 shots. They do not include calibration drift or systematic error.

| Case | Target sector | \(P_{\rm Gauss}\) | \(\langle W\rangle\) | \(O_{LR}\) raw | Gauss-only \(O_{LR}\) | Gauss+Wilson \(O_{LR}\) | Gauss+Wilson accept |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Wplus` | \(+1\) | 0.360 ± 0.015 | +0.334 | +0.1600 ± 0.0187 | +0.1944 | +0.1950 | 0.282 |
| `Wminus` | \(-1\) | 0.321 ± 0.015 | -0.360 | +0.1045 ± 0.0187 | +0.0997 | +0.2923 | 0.065 |

Measured Wilson contrast is \(0.694\). The raw hardware imbalance separation is \(0.0555\), smaller than the ideal Trotter separation \(0.1489\). Therefore this run is useful as an Emerald execution record showing opposite measured Wilson signs in the two sectors, but it should not be described as the strongest quantitative mitigation evidence.

## E. 5000-shot repeat and calibration check

Under the later Emerald calibration, the initial mapping placed Gauss ancilla
\(q_9\) on physical qubit QB3, whose recorded readout error was 0.0598, so that
mapping was rejected during pre-execution calibration screening.

We then scanned transpiler seeds using IQM request validation only. The accepted repeat used seed 1:

| Field | Value |
|---|---|
| Job ID | `019f750b-2c82-7371-a66a-eaf4263c222a` |
| Candidate ID | `69a8f20eae2478515d80c55a5f58424fe92ad2091a9bbb9d4819b88bc0495228` |
| Calibration set ID | `314aeb78-d1ec-418f-b1f2-9ab488ff820e` |
| Shots per circuit | 5000 |
| Transpiler seed | 1 |
| Logical-to-physical map | `q0..q11 -> QB24,QB16,QB25,QB33,QB9,QB8,QB10,QB17,QB32,QB7,QB18,QB26` |
| Depth | 125 |
| Native CZ gates | 101 |
| Max recorded CZ error | 0.006846584936122446 |
| Max recorded readout error | 0.013700000000000045 |
| Result JSON | `results/iqm/periodic_hardware/periodic_joint_readout_5000_seed1.json` |
| Processed CSV | `results/processed/periodic_iqm_joint_readout_5000_seed1.csv` |

The 5000-shot hardware table is

| Case | Target sector | \(P_{\rm Gauss}\) | \(\langle W\rangle\) | \(O_{LR}\) raw | Gauss-only \(O_{LR}\) | Gauss+Wilson \(O_{LR}\) | Gauss+Wilson accept |
|---|---:|---:|---:|---:|---:|---:|---:|
| `Wplus` | \(+1\) | 0.2838 ± 0.0064 | +0.3684 | +0.0969 ± 0.0081 | +0.1445 | +0.1661 | 0.2288 |
| `Wminus` | \(-1\) | 0.2920 ± 0.0064 | -0.4196 | +0.0533 ± 0.0082 | +0.0610 | -0.0071 | 0.0564 |

Measured Wilson contrast is 0.788. The raw hardware imbalance separation is 0.0436 with combined standard error approximately 0.0115, i.e. about 3.8 standard deviations. The interpretation remains conservative: Emerald resolves the Wilson diagnostic in the long periodic circuit, while the quantitative mitigation curve remains simulator-backed because the 101-CZ dynamics circuit is noisy.
