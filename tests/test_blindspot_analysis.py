import numpy as np

from z2lgt.blindspot_analysis import analyze_joint_counts, canonical_syndrome_bits, filter_counts, response_matrix
from z2lgt.blindspot_workflow import ideal_processed_rows, write_ideal_processed_csv


def test_bit_order_and_processed_metrics():
    assert canonical_syndrome_bits("0010") == (0, 1, 0, 0)
    result = analyze_joint_counts({"0000": 50, "0001": 30, "0010": 20})
    assert np.isclose(result["P_Gauss"], 0.8)
    assert np.isclose(result["wilson_expectation"], 0.4)
    assert np.isclose(result["gauss_plus_string_acceptance"], 0.5)


def test_gauss_only_accepts_string_error_but_joint_filter_rejects_it():
    counts = {"0000": 10, "0001": 7, "0010": 5}
    assert filter_counts(counts, require_gauss=True, require_string=False) == {"0000": 10, "0001": 7}
    assert filter_counts(counts, require_gauss=True, require_string=True) == {"0000": 10}


def test_response_matrix_orientation():
    records = [{"true_syndrome": true, "counts": {f"{true:04b}": 20}} for true in range(16)]
    assert np.allclose(response_matrix(records), np.eye(16))


def test_ideal_processed_output_has_expected_blindspot_pattern(tmp_path):
    records = []
    for case, key in (
        ("no_error", "0000"),
        ("gauge_violating", "0010"),
        ("gauge_preserving_string", "0001"),
    ):
        records.append(
            {
                "error_type": case,
                "backend_name": "AerSimulator",
                "analysis": analyze_joint_counts({key: 100}),
            }
        )
    payload = {"records": records}
    rows = ideal_processed_rows(payload)
    assert [(row["p_gauss"], row["wilson"]) for row in rows] == [
        (1.0, 1.0),
        (0.0, 1.0),
        (1.0, -1.0),
    ]

    path = write_ideal_processed_csv(payload, tmp_path / "blindspot_ideal.csv")
    assert path.read_text(encoding="utf-8").splitlines()[0] == (
        "case,backend,p_gauss,p_gauss_err,wilson,wilson_err,interpretation"
    )
