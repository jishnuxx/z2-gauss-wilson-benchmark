# String-aware diagnostics for Z2 gauge simulation

This repository benchmarks a specific blind spot in QEC-inspired lattice-gauge
diagnostics:

> A state can pass every local Gauss-law check while occupying the wrong
> electric-string/Wilson-loop sector.

The claim is not that this project invented Gauss-law QEC. Local constraint
checks are already useful error-detection primitives. The result here is that
they are necessary but incomplete: a gauge-preserving physical error can be
invisible to every local syndrome while flipping a nonlocal physical label.

## Current reproducibility status

The repository contains a reproducible benchmark package:

- a 5000-shot IQM Emerald static hardware result demonstrating the Gauss-only
  blind spot;
- ideal and noisy Qiskit/Aer reproductions of the same benchmark;
- exact periodic \(\mathbb{Z}_2\) dynamics showing why the missed Wilson sector
  can corrupt a separate matter observable;
- a periodic Emerald readout check showing the Wilson diagnostic can
  be compiled and measured in a deeper circuit;
- tests, frozen QASM/QPY circuit artifacts, processed CSV/JSON outputs, figures,
  and technical documentation.

Headline static Emerald result:

| Case | \(P_{\rm Gauss}\) | \(\langle W\rangle\) | Meaning |
|---|---:|---:|---|
| Target circuit | 0.9432 | +0.9224 | Target local and Wilson sector accepted. |
| Gauge-violating injected fault | 0.0314 | +0.9352 | Gauss checks reject the fault. |
| Gauge-preserving string fault | 0.9390 | -0.9044 | Gauss-only accepts a wrong Wilson sector. |

The supported claim is observable-aware gauge certification, not full quantum
error correction, a decoder, fault tolerance, or large-scale QCD simulation.

## Minimal four-link model

Four data qubits represent the links of a periodic square. The local vertex
checks and Wilson loop are

```text
G0 = X0 X1    G1 = X1 X2    G2 = X2 X3    G3 = X3 X0
W  = Z0 Z1 Z2 Z3
```

`G3 = G0 G1 G2`, so there are three independent local syndromes. The target is
the simultaneous `+1` state of `G0,G1,G2,W`, an equal superposition of all
even-parity computational states.

- `Z0` is gauge violating: it anticommutes with `G0` and `G3`.
- `X0` is gauge preserving: it commutes with all four `G_s`, but anticommutes
  with `W` and flips the Wilson sector.

The matrix-level verification is implemented in
`src/z2lgt/blindspot_model.py`; the full convention and readout map are in
`docs/blindspot_model.md`.

## Environment and tests

Use the existing project environment, or create an equivalent Python
environment:

```bash
conda create -n QCenv python=3.12
conda activate QCenv
pip install -e ".[test]"
export MPLCONFIGDIR="$PWD/work/mpl"
export XDG_CACHE_HOME="$PWD/work/cache"
python -m pytest -q
```

## Reproduce the result

The default demo uses only local Qiskit Aer simulation and deterministic seeds:

```bash
python scripts/check_algebra.py
python scripts/run_ideal.py --shots 20000
python scripts/run_noisy.py --shots 20000
python scripts/analyze_results.py \
  --iqm results/iqm/static_blindspot_5000/blindspot_minimal.json
python scripts/make_blindspot_plots.py
```

The one-command local reproduction path is:

```bash
make PYTHON=/path/to/python reproduce-all
```

This does not submit hardware jobs. It uses the archived IQM JSON/CSV outputs
already in `results/`.

The noisy simulator applies configurable one- and two-qubit depolarizing
channels plus symmetric readout flips. Defaults are `0.001`, `0.01`, and
`0.02`, respectively. This is a transparent stress model, not a calibrated IQM
noise reconstruction.

## Outputs

Raw and processed files are separated:

```text
results/
  ideal/blindspot_minimal.json
  noisy/blindspot_minimal.json
  iqm/static_blindspot_5000/blindspot_minimal.json
  processed/algebra_report.json
  processed/blindspot_ideal.csv
  processed/blindspot_summary.json
  processed/diagnostic_table.csv
figures/
```

Each run record includes backend, shots, circuit label, model metadata, injected
error, expected sectors, raw counts, `P_Gauss`, every `<G_s>`, `<W>`, acceptance
fractions, and binomial standard errors. Exported minimal circuits are saved as
QASM and QPY under `circuits/blindspot/`.

The demo creates PNG and PDF versions under `figures/` of:

- `fig01_algebraic_blindspot_summary`: result-derived diagnostic table;
- `fig02_gauss_vs_string_blindspot`: the main `P_Gauss` versus `<W>` result;
- `fig03_postselection_gauss_vs_stringaware`: Gauss-only versus joint acceptance;
- `fig04_syndrome_response_matrix`: `P(s_meas | s_true)`;
- `fig05_check_weight_or_depth_scaling`: quality versus identity-layer depth.

## Circuit readout

`src/z2lgt/blindspot_circuits.py` provides two complementary paths:

1. A five-qubit ancilla circuit measures any one `G_s` in the standard
   one-check-at-a-time form.
2. A static four-qubit Clifford decode jointly maps `(W,G0,G1,G2)` to
   computational bits. This enables shot-level Gauss-only and Gauss+string
   postselection and avoids requiring dynamic circuits on hardware.

Direct `W` measurement is computational-basis parity; no hidden basis rotation
is used.

## IQM Emerald hardware runs

The minimal hardware batch is exactly three circuits. The runner defaults to a
provider-free dry run and cannot execute circuits unless a target-specific,
hash-verified manifest has been frozen and interactively approved.

Store the API token in macOS Keychain once, then load the Emerald environment
in each new shell without putting the token in this repository:

```bash
source scripts/activate_iqm_emerald.zsh
```

The provider package is installed with `pip install "iqm-client[qiskit]"`.
Freeze a real Emerald run package using current calibration metrics:

```bash
python scripts/freeze_iqm_blindspot_candidate.py \
  --shots 5000 \
  --outdir results/iqm/emerald_blindspot_candidate_5000
```

This runs the full test suite, transpiles the three circuits, validates the
request without submitting it, records the calibration ID and selected gate
and readout errors, and hashes QASM/QPY artifacts under
`results/iqm/emerald_blindspot_candidate_5000/`. The generated manifest always has
`human_review_approved: false` and `hardware_submitted: false`.

After manually reviewing that manifest, record explicit approval:

```bash
python scripts/approve_iqm_candidate.py
```

The ordinary dry run remains:

```bash
python scripts/run_iqm.py --shots 5000 --batch blindspot-minimal
```

Only after approval, hardware execution requires both the manifest and the explicit
environment gate:

```bash
export Z2LGT_ALLOW_IQM_HARDWARE=YES
python scripts/run_iqm.py --shots 5000 \
  --batch blindspot-minimal --manifest \
  results/iqm/emerald_blindspot_candidate_5000/readiness_manifest.json --submit
```

Missing approval, modified circuit hashes, changed shots, changed target,
missing credentials, or a reused manifest blocks execution. The
runner loads the frozen QPY files and pins the recorded calibration set rather
than retranspiling at execution time. No credentials are written to results
or manifests.

A 5000-shot Emerald run has been completed for the static blind-spot benchmark.
The hardware result is recorded in `docs/iqm_emerald_hardware_result.md`.
The compact technical appendix is `docs/technical_appendix_blindspot_iqm.md`.

## Reproducibility bundle

Create a clean bundle directory and zip archive with:

```bash
python scripts/create_github_bundle.py
```

or

```bash
make PYTHON=/path/to/python bundle
```

The bundle is written under `dist/` and excludes local environments, caches,
temporary working directories, and macOS metadata. It includes the source code,
tests, figures, circuit artifacts, archived hardware JSON/CSV files, and
reproducibility documentation.

## Existing open-chain dynamics workflow

The earlier open-chain Hamiltonian/postselection benchmark remains intact in
`src/z2lgt/model.py` and `scripts/run_all_minimal.py`. It is scientifically
separate from this blind-spot benchmark. Its transport output is an early-time
finite-size diagnostic, not a diffusion coefficient.

## Scope

This is a small diagnostic benchmark, not a full decoder or full QEC protocol.
It does not implement large Hamiltonian dynamics, and it makes no QCD claim.
The supported presentation statement is:

> Local Gauss-law syndrome extraction is a useful QEC-inspired primitive for
> lattice-gauge simulation, but it is incomplete. On a minimal Z2 hardware
> benchmark, gauge-preserving string-sector errors can pass all local checks
> while corrupting a Wilson observable, motivating string-aware diagnostics.

## License

This project is released under the MIT License. See `LICENSE`.
