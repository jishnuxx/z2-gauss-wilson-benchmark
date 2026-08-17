# IQM hardware mitigation plan

This note separates two mitigation levels for the IQM Emerald hardware data.

## 1. Archived readout-assignment mitigation

The frozen IQM readiness manifests archive a readout error estimate for each
measured physical qubit.  The offline mitigation script treats each classical
bit as an independent symmetric assignment channel,

\[
M_i =
\begin{pmatrix}
1-p_i & p_i\\
p_i & 1-p_i
\end{pmatrix},
\qquad
\vec p_{\rm meas}
=
\left(\bigotimes_i M_i\right)\vec p_{\rm true}.
\]

The corrected distribution is obtained by linear inversion,

\[
\vec p_{\rm corr}
=
\left(\bigotimes_i M_i\right)^{-1}\vec p_{\rm meas},
\]

followed by a small nonnegative projection if finite-shot noise creates tiny
negative quasi-probabilities.

Reproduce it without IQM credentials:

```bash
conda run -n QCenv make iqm-mitigate-offline PYTHON=/path/to/python
```

Main outputs:

- `results/processed/iqm_readout_mitigation.json`
- `results/processed/iqm_readout_mitigation.csv`
- `figures/fig09_iqm_readout_mitigation.png`
- `figures/fig09_iqm_readout_mitigation.pdf`

For the archived 5000-shot static blind-spot result, the readout-mitigated
numbers are:

| case | raw \(P_{\rm Gauss}\) | mitigated \(P_{\rm Gauss}\) | raw \(\langle W\rangle\) | mitigated \(\langle W\rangle\) |
|---|---:|---:|---:|---:|
| no error | 0.9432 | 0.9648 | +0.9224 | +0.9313 |
| gauge violating | 0.0314 | 0.0228 | +0.9352 | +0.9444 |
| gauge-preserving string | 0.9390 | 0.9607 | -0.9044 | -0.9133 |

For the periodic 100-CZ hardware readout, the same readout-only correction is
modest:

| case | raw \(P_{\rm Gauss}\) | mitigated \(P_{\rm Gauss}\) | raw \(\langle W\rangle\) | mitigated \(\langle W\rangle\) |
|---|---:|---:|---:|---:|
| Wplus | 0.2838 | 0.3005 | +0.3684 | +0.3720 |
| Wminus | 0.2920 | 0.3095 | -0.4196 | -0.4237 |

That is expected: readout mitigation cannot remove accumulated coherent or
incoherent gate error from the long periodic circuit.

## 2. Stronger static response-matrix mitigation

The stronger static path is to run a hardware response calibration in the
actual diagnostic syndrome basis. The
batch contains:

- 3 data circuits: no error, gauge-violating fault, gauge-preserving string
  fault;
- 16 calibration circuits with known true syndrome
  \((W,G_0,G_1,G_2)\in\{0,1\}^4\).

The calibration estimates

\[
M_{\alpha\beta}
=
P(\hbox{measured syndrome } \alpha
\mid
\hbox{true syndrome } \beta),
\]

and the mitigated syndrome distribution is

\[
\vec p_{\rm corr}=M^{-1}\vec p_{\rm meas}.
\]

This is stronger than using scalar readout errors because it calibrates the
full four-bit diagnostic response.  It is still not a full logical decoder or a
claim of fault-tolerant quantum error correction.

Optional hardware workflow:

```bash
# Requires IQM_SERVER_URL, IQM_TOKEN, and IQM_QUANTUM_COMPUTER.
conda activate QCenv
make iqm-response-freeze PYTHON=/path/to/python
make iqm-response-approve PYTHON=/path/to/python

# Then submit only after checking the manifest and candidate prefix.
export Z2LGT_ALLOW_IQM_HARDWARE=YES
/path/to/python scripts/run_iqm_blindspot_response.py \
  --shots 5000 \
  --manifest results/iqm/emerald_blindspot_response_candidate_5000/readiness_manifest.json \
  --submit \
  --confirm-candidate <first-12-candidate-chars>
```

If completed, the runner writes:

- `results/iqm/static_blindspot_response_mitigated/blindspot_response_mitigated.json`
- `results/processed/static_iqm_response_mitigation.csv`

## Presentation-safe wording

Use this wording:

> The archived Emerald result has now been processed with explicit
> readout-assignment mitigation from the frozen calibration metadata.  This
> moves the static hardware points closer to the ideal syndrome pattern while
> preserving the main conclusion: Gauss-only checks miss the string-sector
> error. The repository also includes a 19-circuit response-matrix batch that
> can be run on Emerald to
> calibrate and invert the full \((W,G_0,G_1,G_2)\) diagnostic response.

Avoid saying that the periodic dynamics hardware result is fully mitigated; the
archived periodic circuit remains gate-noise limited.

## 3. Depth reduction before periodic mitigation

For the periodic hardware-dynamics claim, circuit depth must be reduced before
strong mitigation claims are credible. The repository therefore includes an
offline source-depth audit:

```bash
conda run -n QCenv make periodic-depth-reduction PYTHON=/path/to/python
```

The key result is:

| readout design at \(t=0.8,\ dt=0.4\) | source qubits | source two-qubit gates | source depth | same \( |\Delta O_{\rm LR}| \)? |
|---|---:|---:|---:|---|
| joint matter+Gauss+Wilson | 12 | 80 | 138 | yes |
| matter+Wilson | 9 | 71 | 137 | yes |
| matter only | 8 | 67 | 127 | yes |

One-step Trotter candidates reduce gates further but give exactly zero target
\(O_{\rm LR}\) separation in this Trotter observable, so they are not useful for
the dynamics claim.

The recommended periodic rerun strategy is therefore:

1. run the reduced two-step matter-only dynamics circuit for the hardware
   \(O_{\rm LR}\) comparison;
2. run Gauss/Wilson diagnostic circuits separately to certify the sector;
3. apply readout/response mitigation after the reduced-depth data exist.

Presentation-safe wording:

> We first asked whether mitigation was the right fix for the long periodic
> circuit. The audit shows that a one-step circuit is too shallow to generate
> the target \(O_{\rm LR}\) sector separation. The practical reduction is to
> keep the two-step physics point but split dynamics readout from certification:
> the matter-only dynamics circuit keeps the same ideal \(O_{\rm LR}\) signal
> with 16% fewer source two-qubit gates than the original joint-readout circuit.

The protected reduced hardware workflow is:

```bash
python scripts/freeze_iqm_periodic_matter_candidate.py --shots 5000
python scripts/approve_iqm_candidate.py \
  results/iqm/emerald_periodic_matter_candidate_5000/readiness_manifest.json
export Z2LGT_ALLOW_PERIODIC_IQM_HARDWARE=YES
python scripts/run_iqm_periodic_matter.py \
  --shots 5000 \
  --manifest results/iqm/emerald_periodic_matter_candidate_5000/readiness_manifest.json \
  --submit \
  --confirm-candidate <first-12-candidate-chars>
```

The reduced periodic matter run has now been completed on Emerald:

| quantity | value |
|---|---:|
| IQM job | `019ff54d-9530-76b3-827f-4b9a89999c07` |
| native CZ count | 69 |
| native depth | 115 |
| previous joint-readout native CZ count | 101 |
| previous joint-readout native depth | 125 |
| raw \(\Delta O_{\rm LR}\) | \(0.0470 \pm 0.0120\) |
| readout-mitigated \(\Delta O_{\rm LR}\) | \(0.0479 \pm 0.0120\) |
| ideal Trotter \(\Delta O_{\rm LR}\) | \(0.1489\) |

Reproduce the offline analysis and figure with:

```bash
python scripts/mitigate_iqm_periodic_matter_readout.py
python scripts/make_periodic_matter_hardware_plot.py
```

Presentation-safe wording:

> The reduced periodic hardware circuit resolves the Wilson-sector-dependent
> matter response at about four standard deviations while using 31.7% fewer
> native CZ gates than the previous joint-readout circuit. Readout mitigation is
> small, so the remaining gap to the ideal Trotter value is gate-noise limited;
> this is reduced-depth hardware feasibility evidence, not a fully corrected
> dynamics trajectory.
