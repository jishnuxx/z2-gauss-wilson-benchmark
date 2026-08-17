# Presentation narrative: matched Emerald versus Sirius benchmark

## The result in one sentence

For the same three physics points and the same 5000 shots per circuit, Emerald
resolves the matter-response difference between the nominal `W=+1` and `W=-1`
preparations at `t=0.8` and `t=1.0`, whereas Sirius returns a separation
consistent with zero.

## What was actually run

At each time `t = 0.6, 0.8, 1.0`, two circuits were run: one prepared in the
nominal `W=+1` sector and one in the nominal `W=-1` sector. Every point used
two Trotter steps, so `dt=t/2`. This is therefore a three-point fixed-depth
sector-response benchmark, not a uniform-time-step trajectory.

Each device was measured in two independent jobs, with 5000 shots per circuit
per job. Within a device, both jobs reused the same calibration set, physical
mapping, and compiled resources. The two job estimates were combined using
inverse-variance weighting.

| device | calibration set | primary job | repeat job |
|---|---|---|---|
| Emerald | `4ce7ac76-bb1c-4106-9b6f-e6999749446a` | `019fffb3-5e4e-7913-b11a-c479eeaf4b2c` | `019fffd6-93d7-73d1-a221-15a57b2a3988` |
| Sirius | `9a9fbebd-5f96-43de-95b0-62e8b2704eda` | `019fff99-c331-7740-9a2d-72fa21fc9ea3` | `01a0000a-b632-7230-ac9d-4aee47297ba1` |

| t | Trotter target | Emerald combined | significance | Sirius combined | significance |
|---:|---:|---:|---:|---:|---:|
| 0.6 | +0.0544 | -0.0034 +/- 0.0079 | 0.43 sigma | +0.0054 +/- 0.0070 | 0.76 sigma |
| 0.8 | +0.1489 | +0.0537 +/- 0.0081 | 6.63 sigma | -0.0005 +/- 0.0070 | 0.07 sigma |
| 1.0 | +0.2982 | +0.1041 +/- 0.0080 | 13.01 sigma | -0.0050 +/- 0.0070 | 0.71 sigma |

At `t=0.8` and `t=1.0`, the Emerald-minus-Sirius contrasts are respectively
5.06 and 10.28 standard deviations. At `t=0.6`, the predicted separation is
small and neither device resolves it.

## Why show the sector difference

The headline observable is

```text
Delta O_LR = O_LR(W=+1) - O_LR(W=-1).
```

If both sector circuits experience a similar additive device bias,

```text
O_plus^HW  = a O_plus^ideal  + b + epsilon_plus,
O_minus^HW = a O_minus^ideal + b + epsilon_minus,
```

then subtraction removes the common offset `b`:

```text
Delta O^HW = a Delta O^ideal + epsilon_plus - epsilon_minus.
```

This is why the difference is more robust than interpreting either raw
observable alone. It is not complete error cancellation: multiplicative signal
attenuation, sector-dependent errors, leakage, and coherent errors remain.

## Why Emerald performs better here

The comparison does not support the simplistic statement that fewer CZ gates
always win. Sirius uses fewer CZ gates, but its circuits are deeper and require
about 80--82 MOVE operations. The archived calibration maxima and resources are:

| device | max depth | CZ | MOVE | max CZ error | max MOVE error | max readout error |
|---|---:|---:|---:|---:|---:|---:|
| Emerald | 114 | 76 | 0 | 0.72% | n/a | 1.17% |
| Sirius | 172 | 59 | 80--82 | 1.96% | 0.95% | 2.17% |

A transparent exposure proxy, not a predicted circuit fidelity, is
`N_CZ e_CZ + N_MOVE e_MOVE`. It is about `0.55` for Emerald and `1.94` for
Sirius, approximately 3.5 times larger on Sirius. The defensible explanation is
therefore greater two-qubit routing exposure on Sirius for this encoded
workload, consistent with the observed loss of sector contrast.

## Suggested 45-second script

“We prepared the same reduced eight-qubit gauge-matter circuits in two nominal
Wilson sectors and measured the matter imbalance. We use their difference as
the signal, because common additive hardware bias cancels to first order. At
the smallest point the ideal separation is too small for either device. At the
two larger points, Emerald resolves the sector response at 6.6 and 13 standard
deviations after combining two independent 5000-shot jobs, while Sirius remains
consistent with zero. This is not explained by CZ count alone: Sirius needs a
deeper routed circuit with roughly 80 MOVE operations and larger calibrated
two-qubit and readout errors. The result demonstrates workload-aware hardware
selection, not full error correction.”

## Claim boundaries for Q&A

- These reduced hardware circuits measure matter only. They prepare nominal
  Wilson sectors but do not directly measure and certify the Wilson or Gauss
  operators on the same hardware shots.
- The two repeats test shot/job stability at one calibration and mapping. They
  are not evidence of calibration-day robustness.
- The joint Gauss-and-Wilson procedure in the simulator is post-selection
  (rejection of invalid shots), not active quantum error correction.
- “Emerald is better for this workload” is supported. “Emerald is universally
  better than Sirius” is not supported.
