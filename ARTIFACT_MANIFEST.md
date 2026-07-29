# Artifact manifest

This file lists the repository artifacts that support reproducing the benchmark.

## Headline hardware evidence

| Artifact | Purpose |
|---|---|
| `results/iqm/static_blindspot_5000/blindspot_minimal.json` | 5000-shot IQM Emerald static blind-spot result. |
| `results/iqm/emerald_blindspot_candidate_5000/readiness_manifest.json` | Frozen static hardware-run manifest with calibration and circuit hashes. |
| `results/processed/blindspot_summary.json` | Combined ideal, noisy, and IQM diagnostic table. |
| `results/processed/diagnostic_table.csv` | CSV version of the diagnostic table. |
| `figures/fig02_gauss_vs_string_blindspot.png` | Main hardware-backed figure: \(P_{\rm Gauss}\) versus \(\langle W\rangle\). |
| `figures/fig02_gauss_vs_string_blindspot.pdf` | Vector/PDF version of the main figure. |

## Static circuit artifacts

| Artifact | Purpose |
|---|---|
| `circuits/blindspot/qasm/*.qasm` | Human-readable QASM exports for the three static benchmark circuits. |
| `circuits/blindspot/qiskit/*.qpy` | Qiskit QPY files used for frozen circuit reproducibility. |
| `src/z2lgt/blindspot_model.py` | Algebraic model: Gauss checks, Wilson observable, target state, injected faults. |
| `src/z2lgt/blindspot_circuits.py` | Qiskit circuits and joint readout/Clifford decode. |
| `src/z2lgt/blindspot_analysis.py` | Shot-count analysis for \(P_{\rm Gauss}\), \(\langle W\rangle\), and acceptances. |

## Periodic observable-motivation evidence

| Artifact | Purpose |
|---|---|
| `results/processed/periodic_dynamics_ideal.csv` | Exact dynamics showing wrong Wilson sector changes \(O_{L,R}\). |
| `results/processed/periodic_exact_mitigation.csv` | Exact single-fault mitigation comparison: raw, Gauss-only, Gauss+Wilson. |
| `figures/fig06_periodic_sector_dynamics.png` | Sector-dependent \(O_{L,R}\) dynamics. |
| `figures/fig07_periodic_exact_mitigation.png` | Simulator/exact mitigation comparison. |
| `src/z2lgt/periodic_model.py` | Periodic matter-ring model used for the observable-motivation layer. |
| `src/z2lgt/periodic_dynamics.py` | Exact dynamics routines. |
| `src/z2lgt/periodic_mitigation.py` | Exact single-fault mitigation model. |

## Periodic IQM hardware readout check

| Artifact | Purpose |
|---|---|
| `results/iqm/periodic_hardware/periodic_joint_readout_5000_seed1.json` | 5000-shot periodic Emerald readout result. |
| `results/processed/periodic_iqm_joint_readout_5000_seed1.csv` | Processed periodic hardware readout table. |
| `results/iqm/emerald_periodic_candidate_5000_seed1/readiness_manifest.json` | Frozen periodic hardware-run manifest. |
| `figures/fig08_periodic_iqm_hardware_readout_5000_seed1.png` | Periodic Emerald readout figure. |

## Documentation

| Artifact | Purpose |
|---|---|
| `README.md` | Repository overview and quickstart. |
| `REPRODUCIBILITY.md` | Step-by-step reproduction commands. |
| `docs/technical_appendix_blindspot_iqm.md` | One-page-style static algebra, readout map, IQM identity, hardware table. |
| `docs/technical_appendix_periodic_iqm.md` | Periodic circuit/readout/IQM appendix. |

## Reproducibility boundary

The archived JSON/CSV files reproduce all figures without IQM credentials. New
hardware jobs are optional and require explicit consent through the protected IQM
runner workflow.
