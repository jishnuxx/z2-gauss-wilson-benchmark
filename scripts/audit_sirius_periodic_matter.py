#!/usr/bin/env python3
"""Transpile the reduced periodic circuits for IQM Sirius.

This script only inspects the backend and transpiles circuits.
It never calls ``backend.run()``, so it consumes no hardware credits.
"""

from __future__ import annotations

import os

import _bootstrap  # noqa: F401  # Adds src/ to Python's import path.

from iqm.qiskit_iqm import IQMProvider
from qiskit import transpile

from z2lgt.periodic_iqm_audit import physical_operation_qubits
from z2lgt.periodic_readout import periodic_matter_readout_circuit


def instruction_properties(
    backend,
    operation: str,
    qubits: tuple[int, ...],
) -> tuple[float | None, float | None]:
    """Return calibration error and duration for one physical operation."""

    operation_data = backend.target[operation]

    if qubits in operation_data:
        properties = operation_data[qubits]
    elif operation == "cz":
        # CZ is symmetric, so try the reverse order.
        reversed_qubits = tuple(reversed(qubits))
        properties = (
            operation_data[reversed_qubits]
            if reversed_qubits in operation_data
            else None
        )
    else:
        properties = None

    if properties is None:
        return None, None

    return properties.error, properties.duration


def main() -> None:
    url = os.environ.get("IQM_SERVER_URL")

    if not url:
        raise SystemExit(
            "IQM_SERVER_URL is missing. "
            "Activate the IQM environment first."
        )

    # We deliberately do not pass the token explicitly.
    # The IQM client reads IQM_TOKEN from the environment.
    provider = IQMProvider(
        url,
        quantum_computer="sirius",
    )

    backend = provider.get_backend(use_metrics=True)

    print("Backend:", backend.name)
    print("Quantum computer: sirius")
    print("Backend qubits:", backend.num_qubits)
    print("Calibration set:", backend.architecture.calibration_set_id)
    print("Native operations:", sorted(backend.operation_names))
    print()

    sector_records = []

    for case, sector in (("Wplus", +1), ("Wminus", -1)):
        source = periodic_matter_readout_circuit(
            time=0.8,
            dt=0.4,
            wilson_sector=sector,
        )

        compiled = transpile(
            source,
            backend=backend,
            optimization_level=3,
            seed_transpiler=7,
        )

        # Logical q0,...,q7 -> initial Sirius physical qubits.
        mapping = [
            int(compiled.layout.initial_layout[source.qubits[index]])
            for index in range(source.num_qubits)
        ]

        operation_counts = {
            str(name): int(count)
            for name, count in compiled.count_ops().items()
        }

        print(f"=== {case}: W={sector:+d} ===")
        print("Logical-to-physical mapping:")

        for logical, physical in enumerate(mapping):
            role = "matter" if logical < 4 else "link"
            print(
                f"  logical q{logical} ({role})"
                f" -> physical QB{physical}"
            )

        print("Depth:", compiled.depth())
        print("Operation counts:", operation_counts)

        for operation in ("cz", "move"):
            if operation not in backend.operation_names:
                continue

            operation_qubits = physical_operation_qubits(
                compiled,
                mapping,
                operation,
            )

            unique_operation_qubits = sorted(set(operation_qubits))
            errors = []

            print(
                f"{operation.upper()} count:",
                operation_counts.get(operation, 0),
            )
            print(f"Unique {operation.upper()} connections:")

            for qubits in unique_operation_qubits:
                error, duration = instruction_properties(
                    backend,
                    operation,
                    tuple(qubits),
                )

                if error is not None:
                    errors.append(float(error))

                print(
                    f"  {tuple(qubits)}:"
                    f" error={error}, duration={duration}"
                )

            if errors:
                print(
                    f"Maximum calibrated {operation.upper()} error:",
                    max(errors),
                )

        measured_qubits = physical_operation_qubits(
            compiled,
            mapping,
            "measure",
        )

        print(
            "Physical qubits measured:",
            [qubits[0] for qubits in measured_qubits],
        )
        print()

        sector_records.append(
            {
                "case": case,
                "mapping": mapping,
                "depth": int(compiled.depth()),
                "operations": operation_counts,
            }
        )

    same_mapping = (
        sector_records[0]["mapping"]
        == sector_records[1]["mapping"]
    )

    print("=== Fair-comparison check ===")
    print("Same mapping for both Wilson sectors:", same_mapping)
    print("backend.run called: false")
    print("Hardware credits consumed: false")


if __name__ == "__main__":
    main()
