from z2lgt.periodic_mitigation import (
    exact_single_fault_mitigation,
    write_periodic_mitigation_csv,
)
from z2lgt.periodic_mitigation_plotting import (
    plot_periodic_exact_mitigation,
    read_periodic_mitigation_csv,
)


def test_periodic_mitigation_figure_from_persisted_csv(tmp_path):
    csv_path = write_periodic_mitigation_csv(
        exact_single_fault_mitigation([0.0, 0.5, 1.0, 1.5, 2.0]),
        tmp_path / "mitigation.csv",
    )
    rows = read_periodic_mitigation_csv(csv_path)
    paths = plot_periodic_exact_mitigation(rows, tmp_path / "figures")
    assert [path.suffix for path in paths] == [".pdf", ".png"]
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
