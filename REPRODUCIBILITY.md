# Reproducibility guide

This repository contains a small, hardware-backed benchmark for observable-aware
gauge certification in a \(\mathbb{Z}_2\) lattice-gauge/QEC setting.

The headline hardware result is already archived in the repository. Reproducing
the figures from the saved data does not require IQM credentials and does not
submit new hardware jobs.

## 1. Environment

Recommended local setup:

```bash
conda create -n QCenv python=3.12
conda activate QCenv
pip install -e ".[test]"
```

If editable install is not used, run scripts from the repository root so that
`scripts/_bootstrap.py` can add `src/` to `PYTHONPATH`.

For headless plotting:

```bash
export MPLCONFIGDIR="$PWD/work/mpl"
export XDG_CACHE_HOME="$PWD/work/cache"
mkdir -p "$MPLCONFIGDIR" "$XDG_CACHE_HOME"
```

## 2. Fast validation

```bash
python -m pytest -q
```

Expected result in the current project state is a passing test suite. The exact
test count can change as the repository evolves.

## 3. Reproduce the static blind-spot result

This reruns the algebra check, ideal simulation, noisy simulation, analysis
using the archived 5000-shot IQM Emerald result, and the main blind-spot plots:

```bash
python scripts/check_algebra.py
python scripts/run_ideal.py --shots 20000
python scripts/run_noisy.py --shots 20000
python scripts/analyze_results.py \
  --iqm results/iqm/static_blindspot_5000/blindspot_minimal.json
python scripts/make_blindspot_plots.py
```

Equivalent Makefile command:

```bash
make PYTHON=python demo
```

If your shell does not resolve the intended Python interpreter, set `PYTHON`
explicitly, for example:

```bash
make PYTHON=/path/to/python demo
```

Main outputs:

```text
results/processed/blindspot_summary.json
results/processed/diagnostic_table.csv
figures/fig02_gauss_vs_string_blindspot.png
figures/fig02_gauss_vs_string_blindspot.pdf
```

The headline IQM Emerald static result is

| Case | \(P_{\rm Gauss}\) | \(\langle W\rangle\) | Interpretation |
|---|---:|---:|---|
| Target circuit | 0.9432 | +0.9224 | Local checks and Wilson sector agree with target. |
| Gauge-violating injected fault | 0.0314 | +0.9352 | Local Gauss checks reject the fault. |
| Gauge-preserving string fault | 0.9390 | -0.9044 | Gauss-only blind spot: local checks pass, Wilson sector is wrong. |

## 4. Reproduce archived IQM readout mitigation

This is an offline mitigation pass using the per-measured-qubit readout errors
already archived in the frozen IQM readiness manifests. It does not submit
hardware jobs.

```bash
python scripts/mitigate_iqm_readout.py
python scripts/make_iqm_mitigation_plot.py
```

Main outputs:

```text
results/processed/iqm_readout_mitigation.json
results/processed/iqm_readout_mitigation.csv
figures/fig09_iqm_readout_mitigation.png
figures/fig09_iqm_readout_mitigation.pdf
```

The static no-error point moves from \(P_{\rm Gauss}=0.9432\) to \(0.9648\);
the string-fault point moves from \(P_{\rm Gauss}=0.9390\) to \(0.9607\), while
its Wilson value remains negative. The periodic 100-CZ readout improves only
modestly, so it should still be described as gate-noise limited.

## 5. Reproduce the periodic exact-dynamics motivation

These commands regenerate the exact-dynamics sector comparison and the
single-fault mitigation model. They are simulator/exact-diagonalization results,
not IQM hardware dynamics results.

```bash
python scripts/run_periodic_ideal.py
python scripts/make_periodic_dynamics_plot.py
python scripts/run_periodic_exact_mitigation.py
python scripts/make_periodic_mitigation_plot.py
```

Main outputs:

```text
results/processed/periodic_dynamics_ideal.csv
results/processed/periodic_exact_mitigation.csv
figures/fig06_periodic_sector_dynamics.png
figures/fig07_periodic_exact_mitigation.png
```

## 6. Reproduce the periodic depth-reduction audit

This audit checks whether the periodic hardware circuit should be shortened
before attempting stronger mitigation. It is offline and does not connect to
IQM.

```bash
python scripts/run_periodic_depth_reduction_audit.py
python scripts/make_periodic_depth_reduction_plot.py
```

Main outputs:

```text
results/processed/periodic_depth_reduction_audit.json
results/processed/periodic_depth_reduction_audit.csv
figures/fig10_periodic_depth_reduction_audit.png
figures/fig10_periodic_depth_reduction_audit.pdf
```

The audit finds that one-Trotter-step circuits are shallower but have zero
target \(O_{\rm LR}\) Wilson-sector separation. The recommended reduced
dynamics readout therefore keeps the two-step \(t=0.8,\ dt=0.4\) physics point
but measures matter only in the dynamics circuit. This reduces source two-qubit
gates from 80 to 67 and source depth from 138 to 127; Gauss/Wilson diagnostics
should be run as separate certification circuits.

## 7. Reproduce the reduced periodic IQM matter-readout result

The completed reduced periodic Emerald job is
`019ff54d-9530-76b3-827f-4b9a89999c07`.  It uses the matter-only dynamics
readout selected by the depth audit.

```bash
python scripts/mitigate_iqm_periodic_matter_readout.py
python scripts/make_periodic_matter_hardware_plot.py
```

Main outputs:

```text
results/iqm/periodic_matter_hardware/periodic_matter_readout_5000.json
results/processed/periodic_iqm_matter_readout_5000.csv
results/processed/periodic_iqm_matter_readout_mitigation_5000.json
results/processed/periodic_iqm_matter_readout_mitigation_5000.csv
figures/fig11_periodic_iqm_matter_readout_5000.png
figures/fig11_periodic_iqm_matter_readout_5000.pdf
```

The raw hardware separation is
\(\Delta O_{\rm LR}=0.0470\pm0.0120\), and the readout-mitigated value is
\(\Delta O_{\rm LR}=0.0479\pm0.0120\).  The ideal Trotter separation is
\(0.1489\).  This is a statistically resolved reduced-depth hardware signal,
not a fully corrected dynamics match.

## 8. Reproduce the periodic IQM hardware-readout plot

The periodic Emerald result is a hardware readout check. It is useful
evidence that the Wilson diagnostic can be compiled and measured on Emerald, but
the deeper dynamics circuit remains noisy.

```bash
python scripts/make_periodic_iqm_hardware_plot.py \
  --input results/processed/periodic_iqm_joint_readout_5000_seed1.csv \
  --job-id 019f750b-2c82-7371-a66a-eaf4263c222a \
  --output-stem fig08_periodic_iqm_hardware_readout_5000_seed1 \
  --title "IQM Emerald periodic readout: 5000-shot hardware repeat"
```

Main outputs:

```text
figures/fig08_periodic_iqm_hardware_readout_5000_seed1.png
figures/fig08_periodic_iqm_hardware_readout_5000_seed1.pdf
```

## 9. Reproduce the matched Emerald/Sirius comparison

The final device comparison uses four archived hardware jobs: two independent
5000-shot jobs on Emerald and two on Sirius. Within each device, the calibration
set, physical layout, and compiled resources are fixed. The command below is
entirely offline: it validates the matching metadata, combines the repeats by
inverse-variance weighting, and regenerates the presentation figure.

```bash
make PYTHON=/path/to/python iqm-device-comparison
```

Main outputs:

```text
results/processed/iqm_emerald_sirius_comparison.json
results/processed/iqm_emerald_sirius_comparison.csv
figures/fig15_iqm_emerald_sirius_sector_separation.png
figures/fig15_iqm_emerald_sirius_sector_separation.pdf
```

The archived input job IDs and the precise presentation narrative are recorded
in `docs/hardware_device_comparison.md`. The repeats are same-calibration job
repeats, not different-calibration or different-day repeats.

## 10. One-command full reproduction

```bash
make PYTHON=/path/to/python reproduce-all
```

This runs tests, the static blind-spot reproduction, periodic exact dynamics,
the periodic depth-reduction audit, periodic mitigation, the periodic IQM
hardware-readout plot, the archived IQM readout-mitigation figure, and the
reduced periodic matter-readout hardware figure. It does not submit hardware
jobs.

## 11. Optional IQM hardware submission workflow

Hardware submission is disabled by default and requires all of the following:

1. IQM credentials loaded into the shell;
2. a frozen manifest with hash-verified QPY artifacts;
3. interactive human approval;
4. an explicit environment consent flag;
5. a command using `--submit`.

The archived hardware JSON files are sufficient for reproducing the figures. Do
not rerun hardware execution just to reproduce the repository.

For a stronger static diagnostic, the repository also includes a 19-circuit
response-matrix hardware workflow:

```bash
python scripts/freeze_iqm_blindspot_response_candidate.py --shots 5000
python scripts/approve_iqm_candidate.py \
  results/iqm/emerald_blindspot_response_candidate_5000/readiness_manifest.json
```

After reviewing the manifest and confirming available IQM credits, submit with
`scripts/run_iqm_blindspot_response.py --submit --confirm-candidate <prefix>`.
This calibrates the full four-bit \((W,G_0,G_1,G_2)\) diagnostic response
matrix on hardware.

For a reduced-depth periodic dynamics rerun, freeze and review the two-sector
matter-only candidate:

```bash
python scripts/freeze_iqm_periodic_matter_candidate.py --shots 5000
python scripts/approve_iqm_candidate.py \
  results/iqm/emerald_periodic_matter_candidate_5000/readiness_manifest.json
```

After review, submit with:

```bash
export Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE=YES
python scripts/run_iqm_periodic_matter.py \
  --shots 5000 \
  --manifest results/iqm/emerald_periodic_matter_candidate_5000/readiness_manifest.json \
  --submit \
  --confirm-candidate <first-12-candidate-chars>
```

This produces a shallower hardware \(O_{\rm LR}\) dynamics readout. It should be
paired with the static/response-matrix Gauss-Wilson diagnostics, because the
reduced dynamics circuit intentionally does not measure Gauss and Wilson in the
same shot.
