"""Shared calibration helpers for target-specific IQM freeze scripts."""

from __future__ import annotations

from .periodic_iqm_audit import physical_operation_qubits


def parse_fixed_layout(value: str, *, expected_size: int = 8) -> tuple[int, ...]:
    """Parse and validate a comma-separated physical layout."""
    try:
        layout = tuple(int(item.strip()) for item in value.split(","))
    except ValueError as exc:
        raise ValueError("fixed layout must contain comma-separated integers") from exc
    if len(layout) != expected_size:
        raise ValueError(f"fixed layout must contain exactly {expected_size} indices")
    if any(index < 0 for index in layout):
        raise ValueError("fixed layout indices must be non-negative")
    if len(set(layout)) != len(layout):
        raise ValueError("fixed layout indices must be distinct")
    return layout


def component_name(backend, index: int) -> str:
    """Return the IQM component name for one backend index."""
    return str(backend.index_to_qubit_name(index))


def instruction_properties(properties) -> dict[str, float | None]:
    """Convert Qiskit instruction properties to JSON-safe scalars."""
    return {
        "duration_seconds": (
            None
            if properties is None or properties.duration is None
            else float(properties.duration)
        ),
        "error": (
            None
            if properties is None or properties.error is None
            else float(properties.error)
        ),
    }


def resolve_target_key(target, operation: str, locus: tuple[int, ...]):
    """Resolve one compiled locus in a calibrated target."""
    operation_data = target[operation]
    if locus in operation_data:
        return locus
    if operation == "cz":
        reverse = tuple(reversed(locus))
        if reverse in operation_data:
            return reverse
    raise RuntimeError(
        f"compiled {operation} locus is absent from the calibrated target: {locus}"
    )


def calibrated_loci(
    backend,
    circuit,
    mapping: list[int],
    operation: str,
    target,
) -> list[dict[str, object]]:
    """Return calibrated properties for every unique compiled locus."""
    records = []
    for locus in sorted(set(physical_operation_qubits(circuit, mapping, operation))):
        key = resolve_target_key(target, operation, locus)
        records.append(
            {
                "component_indices": list(locus),
                "components": [component_name(backend, index) for index in locus],
                "calibration_key_indices": list(key),
                **instruction_properties(target[operation][key]),
            }
        )
    return records


def maximum_error(records: list[dict[str, object]], key: str) -> float | None:
    """Return the largest finite error in one per-circuit locus field."""
    errors = [
        float(item["error"])
        for record in records
        for item in record[key]
        if item["error"] is not None
    ]
    return max(errors) if errors else None


def measurement_classical_bits(circuit) -> list[int]:
    """Return global classical-bit indices written by measurement operations."""
    return [
        circuit.clbits.index(instruction.clbits[0])
        for instruction in circuit.data
        if instruction.operation.name == "measure"
    ]


def has_four_bit_matter_readout(circuit) -> bool:
    """Check that a reduced circuit writes exactly the four matter outputs.

    Physical measurement qubits need not equal the initial matter placement:
    routing can move logical states before readout.  Qiskit preserves the
    logical-to-classical measurement semantics, so the invariant is one write
    to each of the four classical matter bits and no additional measurements.
    """
    bits = measurement_classical_bits(circuit)
    return circuit.num_clbits == 4 and len(bits) == 4 and set(bits) == set(range(4))
