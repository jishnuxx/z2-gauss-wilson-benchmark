from z2lgt.periodic_depth_reduction import (
    depth_reduction_audit,
    recommended_depth_candidate,
)


def test_depth_reduction_recommends_matter_only_two_step_candidate():
    report = depth_reduction_audit(
        [(0.4, 1), (0.8, 2)],
        min_trotter_separation=0.10,
        min_fidelity=0.85,
    )
    recommended = report["recommended"]
    assert recommended["candidate"] == "t=0.8,dt=0.4"
    assert recommended["readout_mode"] == "matter_only"
    assert recommended["source_max_two_qubit_gate_count"] < report["baseline"][
        "source_max_two_qubit_gate_count"
    ]


def test_recommendation_returns_none_when_signal_gate_fails():
    assert recommended_depth_candidate(
        [
            {
                "readout_mode": "matter_only",
                "algorithmic_gate_passed": False,
                "source_max_two_qubit_gate_count": 1,
                "source_max_depth": 1,
                "trotter_sector_separation": 0.0,
            }
        ]
    ) is None
