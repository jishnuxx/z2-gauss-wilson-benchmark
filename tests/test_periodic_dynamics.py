import csv

import numpy as np

from z2lgt.periodic_dynamics import (
    exact_trajectories,
    operator_expectation,
    target_state,
    write_periodic_dynamics_csv,
)
from z2lgt.periodic_model import PeriodicZ2Model


def test_periodic_target_state_is_physical_and_wilson_plus():
    model = PeriodicZ2Model()
    state = target_state(model)
    assert np.isclose(np.vdot(state, state), 1.0)
    assert all(
        np.isclose(operator_expectation(state, check), 1.0)
        for check in model.gauss_checks
    )
    assert np.isclose(operator_expectation(state, model.wilson), 1.0)


def test_wrong_sector_changes_separate_transport_observable():
    rows = exact_trajectories([0.0, 1.0, 1.5, 2.0])
    assert np.isclose(rows[0]["ideal_imbalance"], 1.0)
    assert np.isclose(rows[0]["wrong_sector_imbalance"], 1.0)
    assert rows[2]["absolute_difference"] > 1.0
    assert np.isclose(rows[2]["ideal_imbalance"], 0.461869, atol=1e-6)
    assert np.isclose(rows[2]["wrong_sector_imbalance"], -0.722660, atol=1e-6)


def test_both_trajectories_preserve_gauss_but_have_opposite_wilson_sectors():
    rows = exact_trajectories(np.linspace(0.0, 2.0, 9))
    for row in rows:
        assert np.isclose(row["ideal_min_gauss"], 1.0)
        assert np.isclose(row["wrong_sector_min_gauss"], 1.0)
        assert np.isclose(row["ideal_wilson"], 1.0)
        assert np.isclose(row["wrong_sector_wilson"], -1.0)
        assert row["ideal_norm_error"] < 1e-12
        assert row["wrong_sector_norm_error"] < 1e-12


def test_periodic_dynamics_csv_schema(tmp_path):
    rows = exact_trajectories([0.0, 0.5])
    path = write_periodic_dynamics_csv(rows, tmp_path / "trajectory.csv")
    with path.open(newline="", encoding="utf-8") as handle:
        persisted = list(csv.DictReader(handle))
    assert len(persisted) == 2
    assert list(persisted[0]) == list(rows[0])
    assert persisted[1]["absolute_difference"] != "0.0"
