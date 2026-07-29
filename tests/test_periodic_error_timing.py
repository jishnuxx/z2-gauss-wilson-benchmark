import csv

import numpy as np

from z2lgt.periodic_error_timing import (
    timed_single_qubit_error_sweep,
    write_periodic_error_timing_csv,
)


def _matter_z(rows):
    return [
        row
        for row in rows
        if row["subsystem"] == "matter" and row["pauli"] == "Z"
    ]


def test_timing_sweep_covers_all_error_time_pairs():
    rows = timed_single_qubit_error_sweep(
        [0.0, 0.5, 1.0, 1.5, 2.0],
        [0.0, 0.5, 1.0, 1.5],
    )
    assert len(rows) == 24 * 4


def test_matter_z_is_harmless_at_t0_but_harmful_after_superpositions_form():
    rows = timed_single_qubit_error_sweep(
        [0.0, 0.5, 1.0, 1.5, 2.0],
        [0.0, 0.5, 1.0, 1.5],
    )
    t0 = [row for row in _matter_z(rows) if row["injection_time"] == 0.0]
    later = [row for row in _matter_z(rows) if row["injection_time"] > 0.0]
    assert all(row["max_abs_imbalance_error_after_injection"] < 1e-12 for row in t0)
    assert max(row["max_abs_imbalance_error_after_injection"] for row in later) > 0.1
    assert all(
        row["diagnostic_class"] == "undetected_by_gauss_and_wilson"
        for row in later
    )


def test_link_z_remains_a_wilson_only_error_at_all_injection_times():
    rows = timed_single_qubit_error_sweep(
        [0.0, 1.0, 2.0],
        [0.0, 1.0],
    )
    link_z = [
        row
        for row in rows
        if row["subsystem"] == "link" and row["pauli"] == "Z"
    ]
    assert len(link_z) == 8
    assert all(row["diagnostic_class"] == "wilson_only" for row in link_z)


def test_periodic_error_timing_csv_schema(tmp_path):
    rows = timed_single_qubit_error_sweep([0.0, 1.0], [0.0])
    path = write_periodic_error_timing_csv(rows, tmp_path / "timing.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        persisted = list(csv.DictReader(handle))
    assert len(persisted) == 24
    assert list(persisted[0]) == list(rows[0])
