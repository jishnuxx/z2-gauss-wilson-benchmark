# Artifact manifest

This file lists the repository artifacts that support the reproducible
\(\mathbb{Z}_2\) Gauss/Wilson benchmark.

## Headline hardware evidence

| Artifact | Purpose |
|---|---|
| `results/iqm/static_blindspot_5000/blindspot_minimal.json` | 5000-shot IQM Emerald static blind-spot result. |
| `results/iqm/emerald_blindspot_candidate_5000/readiness_manifest.json` | Frozen static hardware manifest with calibration and circuit hashes. |
| `results/processed/blindspot_summary.json` | Combined ideal, noisy, and IQM diagnostic table. |
| `results/processed/diagnostic_table.csv` | CSV version of the diagnostic table. |
| `figures/fig02_gauss_vs_string_blindspot.png` | Main hardware-backed figure: \(P_{\rm Gauss}\) versus \(\langle W\rangle\). |
| `figures/fig02_gauss_vs_string_blindspot.pdf` | Vector/PDF version of the main figure. |
| `results/processed/iqm_readout_mitigation.json` | Offline readout-mitigated IQM hardware analysis from archived manifest errors. |
| `results/processed/iqm_readout_mitigation.csv` | CSV table comparing raw and readout-mitigated IQM diagnostics. |
| `figures/fig09_iqm_readout_mitigation.png` | Raw versus readout-mitigated hardware diagnostics. |
| `figures/fig09_iqm_readout_mitigation.pdf` | Vector/PDF version of the readout-mitigation figure. |

## Static circuit artifacts

| Artifact | Purpose |
|---|---|
| `circuits/blindspot/qasm/*.qasm` | Human-readable QASM exports for the three static benchmark circuits. |
| `circuits/blindspot/qiskit/*.qpy` | Qiskit QPY files used for frozen circuit reproducibility. |
| `src/z2lgt/blindspot_model.py` | Algebraic model: Gauss checks, Wilson observable, target state, injected faults. |
| `src/z2lgt/blindspot_circuits.py` | Qiskit circuits and joint readout/Clifford decode. |
| `src/z2lgt/blindspot_analysis.py` | Shot-count analysis for \(P_{\rm Gauss}\), \(\langle W\rangle\), and acceptances. |
| `src/z2lgt/readout_mitigation.py` | Readout-assignment and response-matrix mitigation utilities. |
| `src/z2lgt/blindspot_response_iqm.py` | Static IQM response-mitigation batch validation helpers. |
| `scripts/freeze_iqm_blindspot_response_candidate.py` | Optional 19-circuit static response-mitigation freeze workflow. |
| `scripts/run_iqm_blindspot_response.py` | Optional protected runner for the static response-mitigation hardware batch. |

## Periodic observable-motivation evidence

| Artifact | Purpose |
|---|---|
| `results/processed/periodic_dynamics_ideal.csv` | Exact dynamics showing wrong Wilson sector changes \(O_{L,R}\). |
| `results/processed/periodic_exact_mitigation.csv` | Exact single-fault mitigation comparison: raw, Gauss-only, Gauss+Wilson. |
| `results/processed/periodic_depth_reduction_audit.json` | Offline scan showing the reduced periodic dynamics-readout option. |
| `results/processed/periodic_depth_reduction_audit.csv` | CSV table for periodic readout modes, depth, gate count, and retained signal. |
| `results/iqm/periodic_matter_hardware/periodic_matter_readout_5000.json` | Completed 5000-shot reduced periodic matter-only Emerald hardware result. |
| `results/processed/periodic_iqm_matter_readout_5000.csv` | Raw processed table for the reduced periodic matter-only hardware result. |
| `results/processed/periodic_iqm_matter_readout_mitigation_5000.json` | Offline readout-mitigated analysis of the reduced periodic matter-only hardware result. |
| `results/processed/periodic_iqm_matter_readout_mitigation_5000.csv` | CSV version of the reduced periodic matter-only mitigation analysis. |
| `figures/fig06_periodic_sector_dynamics.png` | Sector-dependent \(O_{L,R}\) dynamics. |
| `figures/fig07_periodic_exact_mitigation.png` | Simulator/exact mitigation comparison. |
| `figures/fig10_periodic_depth_reduction_audit.png` | Source-depth reduction figure for the periodic hardware rerun plan. |
| `figures/fig11_periodic_iqm_matter_readout_5000.png` | Reduced periodic matter-only IQM hardware result and readout-mitigation figure. |
| `src/z2lgt/periodic_model.py` | Periodic matter-ring model used for the observable-motivation layer. |
| `src/z2lgt/periodic_dynamics.py` | Exact dynamics routines. |
| `src/z2lgt/periodic_mitigation.py` | Exact single-fault mitigation model. |
| `src/z2lgt/periodic_depth_reduction.py` | Offline depth-reduction audit utilities. |
| `src/z2lgt/periodic_matter_iqm_runner.py` | Safety checks for the reduced periodic matter-readout IQM candidate. |
| `scripts/freeze_iqm_periodic_matter_candidate.py` | Optional freeze workflow for the reduced periodic matter-readout run. |
| `scripts/run_iqm_periodic_matter.py` | Optional protected runner for the reduced periodic matter-readout hardware job. |
| `scripts/mitigate_iqm_periodic_matter_readout.py` | Offline readout-mitigation analysis for the reduced periodic matter-readout job. |
| `scripts/make_periodic_matter_hardware_plot.py` | Figure generator for the reduced periodic matter-readout hardware result. |

## Periodic IQM readout check

| Artifact | Purpose |
|---|---|
| `results/iqm/periodic_hardware/periodic_joint_readout_5000_seed1.json` | 5000-shot periodic Emerald readout result. |
| `results/processed/periodic_iqm_joint_readout_5000_seed1.csv` | Processed periodic hardware readout table. |
| `results/iqm/emerald_periodic_candidate_5000_seed1/readiness_manifest.json` | Frozen periodic hardware manifest. |
| `figures/fig08_periodic_iqm_hardware_readout_5000_seed1.png` | Periodic Emerald readout figure. |

## Matched Emerald/Sirius sector-response benchmark

| Artifact | Purpose |
|---|---|
| `results/iqm/emerald_periodic_matter_hardware/emerald_periodic_matter_scan_5000.json` | Primary archived six-circuit Emerald scan, 5000 shots per circuit. |
| `results/iqm/emerald_periodic_matter_hardware/emerald_periodic_matter_scan_repeat2_5000.json` | Matched Emerald job repeat. |
| `results/iqm/sirius_periodic_matter_hardware/sirius_periodic_matter_scan_5000.json` | Primary archived six-circuit Sirius scan, 5000 shots per circuit. |
| `results/iqm/sirius_periodic_matter_hardware/sirius_periodic_matter_scan_repeat2_5000.json` | Matched Sirius job repeat. |
| `results/iqm/emerald_periodic_matter_scan_candidate_5000/readiness_manifest.json` | Frozen Emerald calibration, layout, circuit resources, and hashes. |
| `results/iqm/emerald_periodic_matter_scan_repeat2_5000/readiness_manifest.json` | Frozen matched-repeat Emerald manifest. |
| `results/iqm/sirius_periodic_matter_scan_candidate_5000/readiness_manifest.json` | Frozen Sirius calibration, layout, circuit resources, and hashes. |
| `results/iqm/sirius_periodic_matter_scan_repeat2_5000/readiness_manifest.json` | Frozen matched-repeat Sirius manifest. |
| `results/processed/iqm_emerald_sirius_comparison.json` | Validated inverse-variance aggregation with job and calibration provenance. |
| `results/processed/iqm_emerald_sirius_comparison.csv` | Presentation-ready combined comparison table. |
| `figures/fig15_iqm_emerald_sirius_sector_separation.png` | Exact, Trotter, Emerald, and Sirius comparison figure. |
| `figures/fig15_iqm_emerald_sirius_sector_separation.pdf` | Vector/PDF version of the final comparison figure. |
| `src/z2lgt/iqm_device_comparison.py` | Validation and matched-repeat aggregation implementation. |
| `scripts/analyze_iqm_device_comparison.py` | Offline comparison CLI. |
| `scripts/make_iqm_device_comparison_plot.py` | Final device-comparison plot generator. |
| `docs/hardware_device_comparison.md` | Presentation narrative, provenance, and claim boundaries. |

## Documentation

| Artifact | Purpose |
|---|---|
| `README.md` | Repository overview and quickstart. |
| `REPRODUCIBILITY.md` | Step-by-step reproduction commands. |
| `LICENSE` | MIT license for the released software and documentation. |
| `BUNDLE_MANIFEST_SHA256.txt` | Generated SHA-256 inventory for the release bundle. |
| `docs/technical_appendix_blindspot_iqm.md` | One-page-style static algebra, readout map, IQM identity, hardware table. |
| `docs/technical_appendix_periodic_iqm.md` | Periodic circuit/readout/IQM appendix. |
| `docs/iqm_emerald_hardware_result.md` | Static IQM Emerald hardware result note. |
| `docs/iqm_readout_and_response_mitigation.md` | Mitigation method, results, limits, and optional response-matrix workflow. |

## Reproducibility boundary

The archived JSON/CSV files reproduce all figures without IQM credentials. New
hardware jobs are optional and require explicit consent through the protected IQM
runner workflow.
