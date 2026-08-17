# IQM Emerald hardware result: Gauss-only blind spot

Date: 2026-07-19

This note records the 5000-shot IQM Emerald execution of the minimal static
blind-spot benchmark. It is distinct from the periodic dynamics benchmarks
documented elsewhere in the repository.

## Run identity

- Backend family: IQM Resonance
- Quantum computer: `emerald`
- Backend reported qubits: 54
- Native operations: `id`, `delay`, `measure`, `r`, `if_else`, `reset`, `cz`
- Shots per circuit: 5000
- Job ID: `019f7749-5d66-7e71-961d-1ce1de04e5d6`
- Candidate ID: `a2054490d694845a413c9e2d4694d6fa92a9a70d6fa82b296c50c73cebd35401`
- Calibration set ID: `314aeb78-d1ec-418f-b1f2-9ab488ff820e`
- Frozen manifest: `results/iqm/emerald_blindspot_candidate_5000/readiness_manifest.json`
- Hardware result: `results/iqm/static_blindspot_5000/blindspot_minimal.json`

The approved manifest is immutable after execution and is retained for
provenance rather than reuse.

## Circuit resources

All three circuits used the same logical-to-physical mapping:

```text
logical q0, q1, q2, q3 -> physical QB17, QB9, QB10, QB11
```

| Case | Depth | Two-qubit gates | Max CZ error | Max readout error |
|---|---:|---:|---:|---:|
| `no_error` | 15 | 6 | 0.002707 | 0.009600 |
| `gauge_violating` | 15 | 6 | 0.002707 | 0.009600 |
| `gauge_preserving_string` | 16 | 6 | 0.002707 | 0.009600 |

## Hardware result

The estimates are computed from measured syndrome/string bitstrings. Reported
uncertainties are binomial standard errors from 5000 shots; they do not include
calibration drift or model systematics.

| Case | \(P_{\rm Gauss}\) | \(\langle W\rangle\) | Gauss+Wilson acceptance | Dominant count | Interpretation |
|---|---:|---:|---:|---|---|
| `no_error` | 0.9432 ± 0.0033 | +0.9224 ± 0.0055 | 0.9210 ± 0.0038 | `0000`: 4605 | Target sector accepted. |
| `gauge_violating` | 0.0314 ± 0.0025 | +0.9352 ± 0.0050 | 0.0232 ± 0.0021 | `0010`: 4620 | Local Gauss checks reject the fault. |
| `gauge_preserving_string` | 0.9390 ± 0.0034 | -0.9044 ± 0.0060 | 0.0270 ± 0.0023 | `0001`: 4560 | Gauss checks pass, but the Wilson sector is wrong. |

The target and gauge-preserving fault have nearly identical Gauss acceptance,
while the Wilson expectation changes sign:

```text
no_error:                 P_Gauss = 0.9432, <W> = +0.9224
gauge_preserving_string:  P_Gauss = 0.9390, <W> = -0.9044
```

This is the hardware evidence for the central statement

```text
P_Gauss approximately 1 does not imply W = W_target.
```

## Scope

The result demonstrates a static four-qubit diagnostic blind spot. It is not a
decoder, fault-tolerance demonstration, or complete quantum-error-correction
protocol. The periodic exact dynamics, reduced Emerald hardware dynamics, and
matched Emerald/Sirius comparison provide separate evidence about observable
sensitivity and device-level execution.
