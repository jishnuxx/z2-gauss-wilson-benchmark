from z2lgt.periodic_dynamics import exact_trajectories, write_periodic_dynamics_csv
from z2lgt.periodic_plotting import (
    plot_periodic_sector_dynamics,
    read_periodic_dynamics_csv,
)


def test_periodic_sector_figure_from_persisted_csv(tmp_path):
    csv_path = write_periodic_dynamics_csv(
        exact_trajectories([0.0, 0.5, 1.0, 1.5, 2.0]),
        tmp_path / "trajectory.csv",
    )
    rows = read_periodic_dynamics_csv(csv_path)
    paths = plot_periodic_sector_dynamics(rows, tmp_path / "figures")
    assert [path.suffix for path in paths] == [".pdf", ".png"]
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
