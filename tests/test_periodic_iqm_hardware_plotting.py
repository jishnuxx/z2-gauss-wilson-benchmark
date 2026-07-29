import csv

from z2lgt.periodic_iqm_hardware_plotting import (
    plot_periodic_iqm_hardware_readout,
    read_periodic_iqm_hardware_csv,
)


def test_periodic_iqm_hardware_figure_from_persisted_csv(tmp_path):
    csv_path = tmp_path / "periodic_iqm.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "case",
                "wilson_sector",
                "shots",
                "P_Gauss",
                "P_Gauss_se",
                "wilson_expectation",
                "wilson_target_probability",
                "imbalance",
                "imbalance_se",
                "gauss_only_imbalance",
                "gauss_plus_wilson_imbalance",
                "gauss_only_acceptance",
                "gauss_plus_wilson_acceptance",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "case": "Wplus",
                "wilson_sector": 1,
                "shots": 1000,
                "P_Gauss": 0.36,
                "P_Gauss_se": 0.015,
                "wilson_expectation": 0.334,
                "wilson_target_probability": 0.667,
                "imbalance": 0.16,
                "imbalance_se": 0.019,
                "gauss_only_imbalance": 0.194,
                "gauss_plus_wilson_imbalance": 0.195,
                "gauss_only_acceptance": 0.36,
                "gauss_plus_wilson_acceptance": 0.282,
            }
        )
        writer.writerow(
            {
                "case": "Wminus",
                "wilson_sector": -1,
                "shots": 1000,
                "P_Gauss": 0.321,
                "P_Gauss_se": 0.015,
                "wilson_expectation": -0.36,
                "wilson_target_probability": 0.32,
                "imbalance": 0.1045,
                "imbalance_se": 0.019,
                "gauss_only_imbalance": 0.100,
                "gauss_plus_wilson_imbalance": 0.292,
                "gauss_only_acceptance": 0.321,
                "gauss_plus_wilson_acceptance": 0.065,
            }
        )

    rows = read_periodic_iqm_hardware_csv(csv_path)
    paths = plot_periodic_iqm_hardware_readout(rows, tmp_path / "figures")
    assert [path.suffix for path in paths] == [".pdf", ".png"]
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)

