# IQM Emerald hardware result: Gauss-only blind spot

Date: 2026-07-19

This note records the 5000-shot IQM Emerald execution of the minimal blind-spot benchmark. It supersedes the earlier 1000-shot static run as the headline hardware result. It is a hardware result for the static 4-qubit syndrome/string diagnostic, not a hardware result for the periodic dynamics demonstration.

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
- Hardware result JSON: `results/iqm/static_blindspot_5000/blindspot_minimal.json`

The approved manifest is locked after execution. Do not reuse it for another hardware job.

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

The diagnostic estimates are computed from the measured syndrome/string bitstrings. Reported uncertainties are binomial standard errors from 5000 shots only; they do not include calibration drift or model systematics.

| Case | `P_Gauss` | `<W>` | Gauss+Wilson acceptance | Dominant count | Interpretation |
|---|---:|---:|---:|---|---|
| `no_error` | 0.9432 ± 0.0033 | 0.9224 ± 0.0055 | 0.9210 ± 0.0038 | `0000`: 4605 | Target sector is accepted. |
| `gauge_violating` | 0.0314 ± 0.0025 | 0.9352 ± 0.0050 | 0.0232 ± 0.0021 | `0010`: 4620 | Local Gauss checks reject the fault. |
| `gauge_preserving_string` | 0.9390 ± 0.0034 | -0.9044 ± 0.0060 | 0.0270 ± 0.0023 | `0001`: 4560 | Gauss checks pass, but the Wilson sector is wrong. |

## Main conclusion

The real Emerald run demonstrates the intended blind spot:

```text
Gauss-only accepts:
  no_error                 P_Gauss = 0.9432
  gauge_preserving_string  P_Gauss = 0.9390

but the Wilson diagnostic separates them:
  no_error                 <W> = +0.9224
  gauge_preserving_string  <W> = -0.9044
```

Therefore, local Gauss-law checks are necessary but incomplete for this observable-aware certification task. A gauge-preserving string-sector error can look locally physical while occupying the wrong Wilson sector.

Operationally:

- Gauss-only postselection would keep most wrong-sector shots in the `gauge_preserving_string` case.
- Gauss+Wilson postselection rejects the wrong-sector case, with only 0.027 acceptance in this run.
- The hardware result supports the central claim for the minimal static benchmark:

```text
P_Gauss ≈ 1 does not imply W = W_target.
```

## Current scope and caveats

This result is enough for a clean hardware-backed figure of the Gauss/string blind spot. It does not show an IQM hardware improvement of a dynamical scientific observable.

Current status:

- Minimal algebra: complete.
- Ideal and noisy simulator pipeline: complete.
- Periodic exact-dynamics sector sensitivity: complete in ED/simulation.
- IQM Emerald static blind-spot run: complete.
- IQM Emerald periodic readout run: complete as a noisy hardware check.
