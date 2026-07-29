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

## 4. Reproduce the periodic exact-dynamics motivation

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

## 5. Reproduce the periodic IQM hardware-readout plot

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

## 6. One-command full reproduction

```bash
make PYTHON=/path/to/python reproduce-all
```

This runs tests, the static blind-spot reproduction, periodic exact dynamics,
periodic mitigation, and the periodic IQM hardware-readout plot. It does not
submit hardware jobs.

## 7. Optional IQM hardware execution workflow

Hardware execution is disabled by default and requires all of the following:

1. IQM credentials loaded into the shell;
2. a frozen manifest with hash-verified QPY artifacts;
3. interactive human approval;
4. an explicit environment consent flag;
5. a command using `--submit`.

The archived hardware JSON files are sufficient for reproducing the figures.
Do not rerun hardware jobs just to reproduce the repository.
