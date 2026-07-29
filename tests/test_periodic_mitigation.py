import csv

import numpy as np

from z2lgt.periodic_mitigation import (
    exact_single_fault_mitigation,
    write_periodic_mitigation_csv,
)


def test_exact_mitigation_starts_from_the_same_error_free_point():
    rows = exact_single_fault_mitigation([0.0, 1.0, 2.0])
    first = rows[0]
    assert first["cumulative_fault_probability"] == 0.0
    assert first["raw_imbalance"] == first["ideal_imbalance"]
    assert first["gauss_only_imbalance"] == first["ideal_imbalance"]
    assert first["gauss_plus_wilson_imbalance"] == first["ideal_imbalance"]


def test_wilson_aware_filter_reduces_but_does_not_remove_all_bias():
    rows = exact_single_fault_mitigation(np.linspace(0.0, 2.0, 17))
    gauss_mae = np.mean([row["gauss_only_abs_error"] for row in rows])
    joint_mae = np.mean([row["gauss_plus_wilson_abs_error"] for row in rows])
    assert joint_mae < gauss_mae
    assert rows[-1]["gauss_plus_wilson_abs_error"] > 1e-6


def test_final_acceptance_matches_analytic_single_fault_weights():
    rows = exact_single_fault_mitigation([0.0, 1.0, 2.0])
    final = rows[-1]
    assert np.isclose(final["cumulative_fault_probability"], 0.2)
    assert np.isclose(final["gauss_only_acceptance"], 0.8 + 0.2 * 8 / 24)
    assert np.isclose(
        final["gauss_plus_wilson_acceptance"],
        0.8 + 0.2 * 4 / 24,
    )


def test_periodic_mitigation_csv_schema(tmp_path):
    rows = exact_single_fault_mitigation([0.0, 1.0])
    path = write_periodic_mitigation_csv(rows, tmp_path / "mitigation.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        persisted = list(csv.DictReader(handle))
    assert len(persisted) == 2
    assert list(persisted[0]) == list(rows[0])
