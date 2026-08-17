from z2lgt.blindspot_circuits import CASES
from z2lgt.blindspot_response_iqm import (
    RESPONSE_BATCH,
    RESPONSE_SYNDROMES,
    response_mitigation_circuit_specs,
)


def test_response_mitigation_batch_structure():
    specs = response_mitigation_circuit_specs()
    assert RESPONSE_BATCH == "blindspot-response-mitigated"
    assert len(specs) == 19
    assert [spec["case"] for spec in specs[:3]] == list(CASES)
    assert [spec["true_syndrome"] for spec in specs[3:]] == list(RESPONSE_SYNDROMES)
    assert {spec["circuit"].num_clbits for spec in specs} == {4}
