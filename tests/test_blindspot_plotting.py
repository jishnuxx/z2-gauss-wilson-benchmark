from z2lgt.blindspot_analysis import analyze_joint_counts
from z2lgt.blindspot_plotting import make_blindspot_plots


def _record(mode, case, key):
    return {"mode": mode, "error_type": case, "analysis": analyze_joint_counts({key: 100})}


def test_all_required_blindspot_plots_run(tmp_path):
    cases = (("no_error", "0000"), ("gauge_violating", "0010"), ("gauge_preserving_string", "0001"))
    datasets = {}
    for mode in ("ideal", "noisy"):
        datasets[mode] = {
            "records": [_record(mode, case, key) for case, key in cases],
            "response": {"matrix_measured_given_true": [[float(i == j) for j in range(16)] for i in range(16)]},
            "depth_scan": [
                {"idle_layers": layer, "analysis": analyze_joint_counts({"0000": 100})}
                for layer in (0, 2, 4)
            ],
        }
    paths = make_blindspot_plots({"datasets": datasets}, tmp_path)
    assert len(paths) == 10
    assert all(path.exists() and path.stat().st_size > 0 for path in paths)
