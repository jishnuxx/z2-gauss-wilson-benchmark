import csv

from z2lgt.periodic_error_sweep import (
    diagnostic_class_counts,
    single_qubit_pauli_error_sweep,
    write_periodic_error_sweep_csv,
)


def _by_error(rows, subsystem, local_index, pauli):
    return next(
        row
        for row in rows
        if row["subsystem"] == subsystem
        and row["local_index"] == local_index
        and row["pauli"] == pauli
    )


def test_all_24_weight_one_pauli_errors_are_classified_once():
    rows = single_qubit_pauli_error_sweep([0.0, 1.0, 2.0])
    assert len(rows) == 24
    assert diagnostic_class_counts(rows) == {
        "gauss_only": 12,
        "wilson_only": 4,
        "gauss_and_wilson": 4,
        "undetected_by_gauss_and_wilson": 4,
    }


def test_representative_error_classes_match_pauli_algebra():
    rows = single_qubit_pauli_error_sweep([0.0, 1.0, 2.0])
    assert _by_error(rows, "matter", 0, "X")["diagnostic_class"] == "gauss_only"
    assert (
        _by_error(rows, "matter", 0, "Z")["diagnostic_class"]
        == "undetected_by_gauss_and_wilson"
    )
    assert _by_error(rows, "link", 0, "X")["diagnostic_class"] == "gauss_only"
    assert _by_error(rows, "link", 0, "Y")["diagnostic_class"] == "gauss_and_wilson"
    assert _by_error(rows, "link", 0, "Z")["diagnostic_class"] == "wilson_only"


def test_t0_invisible_matter_phase_errors_are_harmless_for_this_target():
    rows = single_qubit_pauli_error_sweep([0.0, 0.5, 1.0, 1.5, 2.0])
    invisible = [
        row
        for row in rows
        if row["diagnostic_class"] == "undetected_by_gauss_and_wilson"
    ]
    assert len(invisible) == 4
    assert all(
        row["initial_state_fidelity_after_error"] > 1.0 - 1e-12
        for row in invisible
    )
    assert all(row["max_abs_imbalance_error"] < 1e-12 for row in invisible)


def test_periodic_error_sweep_csv_schema(tmp_path):
    rows = single_qubit_pauli_error_sweep([0.0, 1.0])
    path = write_periodic_error_sweep_csv(rows, tmp_path / "sweep.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        persisted = list(csv.DictReader(handle))
    assert len(persisted) == 24
    assert list(persisted[0]) == list(rows[0])
