#!/usr/bin/env python3
"""Calibration-informed noisy simulation of the Sirius fixed-depth benchmark."""

from __future__ import annotations

import csv
import math
import os
from pathlib import Path

import _bootstrap  # noqa: F401

from iqm.qiskit_iqm import IQMProvider
from iqm.qiskit_iqm.iqm_transpilation import (
    IQMReplaceGateWithUnitaryPass,
)
from iqm.qiskit_iqm.move_gate import MOVE_GATE_UNITARY
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import (
    NoiseModel,
    ReadoutError,
    depolarizing_error,
)

from z2lgt.periodic_circuits import (
    periodic_two_sector_circuit_comparison,
)
from z2lgt.periodic_readout import (
    analyze_matter_counts,
    periodic_matter_readout_circuit,
)


POINTS = (
    (0.6, 0.3),
    (0.8, 0.4),
    (1.0, 0.5),
)

# Fixed placement previously selected by Sirius transpilation.
INITIAL_LAYOUT = [4, 1, 6, 5, 0, 2, 3, 13]

SHOTS = 5000
OUTPUT = Path(
    "results/processed/"
    "sirius_periodic_matter_noise_scan_5000.csv"
)


def depolarizing_channel(
    average_infidelity: float,
    number_of_qubits: int,
):
    """Convert average gate infidelity into depolarizing strength."""

    dimension = 2**number_of_qubits
    strength = (
        float(average_infidelity)
        * dimension
        / (dimension - 1)
    )
    return depolarizing_error(strength, number_of_qubits)


def create_noise_model(backend) -> NoiseModel:
    """Build a gate/readout model from the current Sirius calibration."""

    noise_model = NoiseModel()
    real_target = backend.get_real_target()

    # Single-qubit PRX/R errors.
    for locus, properties in backend.target["r"].items():
        if properties is None or properties.error is None:
            continue

        noise_model.add_quantum_error(
            depolarizing_channel(properties.error, 1),
            "r",
            list(locus),
        )

    # Physical qubit-resonator CZ errors.
    for locus, properties in real_target["cz"].items():
        if properties is None or properties.error is None:
            continue

        noise_model.add_quantum_error(
            depolarizing_channel(properties.error, 2),
            "cz",
            list(locus),
        )

    # MOVE is replaced by a unitary for Aer. Attach the MOVE error
    # to that unitary on each physical qubit-resonator locus.
    for locus, properties in real_target["move"].items():
        if properties is None or properties.error is None:
            continue

        noise_model.add_quantum_error(
            depolarizing_channel(properties.error, 2),
            "unitary",
            list(locus),
        )

    # The public calibration provides one scalar readout error.
    # Use it as a symmetric assignment-error approximation.
    for locus, properties in backend.target["measure"].items():
        if properties is None or properties.error is None:
            continue

        error = float(properties.error)
        noise_model.add_readout_error(
            ReadoutError(
                [
                    [1.0 - error, error],
                    [error, 1.0 - error],
                ]
            ),
            list(locus),
        )

    return noise_model


def main() -> None:
    backend = IQMProvider(
        os.environ["IQM_SERVER_URL"],
        quantum_computer="sirius",
    ).get_backend(use_metrics=True)

    noise_model = create_noise_model(backend)

    simulator = AerSimulator(
        method="matrix_product_state",
        noise_model=noise_model,
    )

    rows = []

    print("Calibration:", backend.architecture.calibration_set_id)
    print(
        "Fixed initial mapping:",
        [
            backend.index_to_qubit_name(index)
            for index in INITIAL_LAYOUT
        ],
    )

    for point_index, (time, dt) in enumerate(POINTS):
        ideal_rows = periodic_two_sector_circuit_comparison(
            time=time,
            dt=dt,
            include_resources=False,
        )
        ideal_by_sector = {
            int(row["sector"]): row
            for row in ideal_rows
        }

        point_results = {}

        print(f"\nt={time:g}, dt={dt:g}, steps={round(time / dt)}")

        for case, sector in (("Wplus", +1), ("Wminus", -1)):
            source = periodic_matter_readout_circuit(
                time=time,
                dt=dt,
                wilson_sector=sector,
            )

            compiled = transpile(
                source,
                backend=backend,
                initial_layout=INITIAL_LAYOUT,
                optimization_level=3,
                seed_transpiler=7,
            )

            simulation_circuit = IQMReplaceGateWithUnitaryPass(
                "move",
                MOVE_GATE_UNITARY,
            )(compiled)

            counts = simulator.run(
                simulation_circuit,
                shots=SHOTS,
                seed_simulator=(
                    20260814
                    + 10 * point_index
                    + (0 if sector == 1 else 1)
                ),
            ).result().get_counts()

            analysis = analyze_matter_counts(counts)
            reference = ideal_by_sector[sector]
            operations = compiled.count_ops()

            point_results[case] = analysis

            rows.append(
                {
                    "time": time,
                    "dt": dt,
                    "trotter_steps": round(time / dt),
                    "case": case,
                    "wilson_sector": sector,
                    "exact_O_LR": reference["exact_imbalance"],
                    "trotter_O_LR": reference["trotter_imbalance"],
                    "noisy_O_LR": analysis["imbalance"],
                    "noisy_O_LR_se": analysis["imbalance_se"],
                    "shots": SHOTS,
                    "depth": compiled.depth(),
                    "r_count": operations.get("r", 0),
                    "cz_count": operations.get("cz", 0),
                    "move_count": operations.get("move", 0),
                    "calibration_set_id": str(
                        backend.architecture.calibration_set_id
                    ),
                    "noise_model": (
                        "calibration-informed independent "
                        "depolarizing plus symmetric readout"
                    ),
                }
            )

            print(
                f"  {case}: "
                f"Trotter={reference['trotter_imbalance']:.6f}, "
                f"noisy={analysis['imbalance']:.6f} "
                f"+/- {analysis['imbalance_se']:.6f}"
            )

        separation = (
            point_results["Wplus"]["imbalance"]
            - point_results["Wminus"]["imbalance"]
        )
        separation_error = math.sqrt(
            point_results["Wplus"]["imbalance_se"] ** 2
            + point_results["Wminus"]["imbalance_se"] ** 2
        )

        print(
            f"  noisy separation={separation:.6f} "
            f"+/- {separation_error:.6f}"
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    print("\nOutput:", OUTPUT)
    print("backend.run called: false")
    print("Hardware credits consumed: false")


if __name__ == "__main__":
    main()
