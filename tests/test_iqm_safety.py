import pytest

from z2lgt.circuits import trotter_circuit
from z2lgt.gauss import localized_imbalance_bits
from z2lgt.iqm_interface import dry_run, get_iqm_backend
from z2lgt.model import Z2Model


def test_iqm_backend_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("Z2LGT_ALLOW_IQM_HARDWARE", raising=False)
    with pytest.raises(PermissionError, match="hardware is disabled"):
        get_iqm_backend()


def test_iqm_backend_requires_readiness_manifest(monkeypatch):
    monkeypatch.setenv("Z2LGT_ALLOW_IQM_HARDWARE", "YES")
    with pytest.raises(PermissionError, match="readiness manifest"):
        get_iqm_backend(allow_hardware=True)


def test_dry_run_reports_resources_without_hardware_execution():
    model = Z2Model(3)
    circuit = trotter_circuit(model, localized_imbalance_bits(model), 0.1, 0.1, measure=True)
    report = dry_run(circuit)
    assert report["mode"] == "dry-run"
    assert report["hardware_execution_enabled"] is False
    assert report["measurement_count"] == model.n_qubits
