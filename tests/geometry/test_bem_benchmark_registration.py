import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.benchmark import (
    AcousticBenchmarkDescriptor,
    AnalyticalBEMBenchmarkDescriptor,
    validate_analytical_bem_benchmark,
    validate_acoustic_benchmark_descriptor
)

@pytest.fixture
def valid_ben004():
    return AnalyticalBEMBenchmarkDescriptor(
        benchmark_id="ben004_rigid_sphere_scattering_registered",
        label="rigid sphere scattering",
        category="bem_analytical",
        source_citation="Analytical Acoustics, Eq 10.1",
        reference_data_fields=["pressure_real", "pressure_imag", "theta"],
        execution_status="registered_not_executed",
        physical_result_computed=False,
        bem_implemented=False,
        reference_matching_performed=False
    )

def test_ben004_validates_completely(valid_ben004):
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert not errors

def test_missing_source_citation_rejected(valid_ben004):
    valid_ben004.source_citation = ""
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert any("source_citation required" in e for e in errors)

def test_missing_reference_fields_rejected(valid_ben004):
    valid_ben004.reference_data_fields = []
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert any("expected reference fields must be declared" in e for e in errors)

def test_execution_attempt_rejected_status(valid_ben004):
    valid_ben004.execution_status = "executed"
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert any("must be 'registered_not_executed'" in e for e in errors)

def test_execution_attempt_rejected_physical_result(valid_ben004):
    valid_ben004.physical_result_computed = True
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert any("physical result/BEM must be false" in e for e in errors)

def test_execution_attempt_rejected_bem_implemented(valid_ben004):
    valid_ben004.bem_implemented = True
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert any("bem_implemented must be false" in e for e in errors)

def test_execution_attempt_rejected_reference_matching(valid_ben004):
    valid_ben004.reference_matching_performed = True
    errors = validate_analytical_bem_benchmark(valid_ben004)
    assert any("reference_matching_performed must be false" in e for e in errors)

def test_existing_cases_unaffected():
    desc = AcousticBenchmarkDescriptor(benchmark_id="old_case", label="old", category="old")
    errors = validate_acoustic_benchmark_descriptor(desc)
    assert not errors
    assert not hasattr(desc, "source_citation")

def test_deterministic_descriptor_loading(valid_ben004):
    desc2 = AnalyticalBEMBenchmarkDescriptor(
        benchmark_id="ben004_rigid_sphere_scattering_registered",
        label="rigid sphere scattering",
        category="bem_analytical",
        source_citation="Analytical Acoustics, Eq 10.1",
        reference_data_fields=["pressure_real", "pressure_imag", "theta"],
        execution_status="registered_not_executed",
        physical_result_computed=False,
        bem_implemented=False,
        reference_matching_performed=False
    )
    assert valid_ben004 == desc2

def test_metadata_constraints_exact_match(valid_ben004):
    assert valid_ben004.execution_status == "registered_not_executed"
    assert valid_ben004.physical_result_computed is False
    assert valid_ben004.bem_implemented is False
    assert valid_ben004.reference_matching_performed is False
