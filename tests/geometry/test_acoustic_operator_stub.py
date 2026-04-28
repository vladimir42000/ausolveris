import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.acoustic_view import AcousticTopologyView, AcousticPatch, AcousticInterface, AcousticObserver
from ausolveris.geometry.solver import assemble_acoustic_operator_stub, AcousticOperatorAssemblyStub, BoundaryConditionPlaceholder

@pytest.fixture
def valid_view():
    view = AcousticTopologyView(
        patches={
            "p1": AcousticPatch("p1", "o1", "f1", (1,0,0), source_group="src1"),
            "p2": AcousticPatch("p2", "o2", "f2", (0,1,0))
        },
        interfaces={"i1": AcousticInterface("i1", "p1", "p2")},
        observers={"obs1": AcousticObserver("pt1")}
    )
    view.is_benchmark_ready = True
    return view

def test_valid_topology_assembles_placeholder(valid_view):
    pkg = assemble_acoustic_operator_stub(valid_view, "bmark_01")
    assert pkg.non_physical is True
    assert pkg.solver_stage == "operator_assembly_stub"
    assert len(pkg.entries) == 4 # 2 patches, 1 interface, 1 observer

def test_invalid_interface_side_metadata_rejected(valid_view):
    valid_view.interfaces["i1"].side_b = "p1" # side_a == side_b
    with pytest.raises(ValueError, match="side_a == side_b"):
        assemble_acoustic_operator_stub(valid_view, "bmark_01")

def test_missing_observer_mapping_rejected(valid_view):
    valid_view.observers = {}
    with pytest.raises(ValueError, match="Missing observer mapping"):
        assemble_acoustic_operator_stub(valid_view, "bmark_01")

def test_missing_source_patch_grouping_rejected(valid_view):
    valid_view.patches["p1"].source_group = None
    with pytest.raises(ValueError, match="Missing source patch grouping"):
        assemble_acoustic_operator_stub(valid_view, "bmark_01")

def test_unsupported_boundary_condition_rejected(valid_view):
    valid_view.patches["p1"].bc_label = "bem_neumann"
    with pytest.raises(ValueError, match="Unsupported boundary condition label"):
        assemble_acoustic_operator_stub(valid_view, "bmark_01")

def test_deterministic_assembly_ordering(valid_view):
    pkg1 = assemble_acoustic_operator_stub(valid_view, "bmark_01")
    # Change iteration order artificially if possible, but sorted() guarantees it.
    assert pkg1.entries[0].entry_id == "patch_p1"
    assert pkg1.entries[1].entry_id == "patch_p2"
    assert pkg1.entries[2].entry_id == "interface_i1"
    assert pkg1.entries[3].entry_id == "observer_obs1"

def test_repeated_assembly_stable(valid_view):
    pkg1 = assemble_acoustic_operator_stub(valid_view, "bmark_01")
    pkg2 = assemble_acoustic_operator_stub(valid_view, "bmark_01")
    assert pkg1.operator_package_id == pkg2.operator_package_id
    assert pkg1.topology_signature == pkg2.topology_signature

def test_output_explicitly_non_physical(valid_view):
    pkg = assemble_acoustic_operator_stub(valid_view, "bmark_01")
    assert pkg.non_physical is True
    assert pkg.numerical_values_present is False
    assert pkg.physical_kernel == "none"

def test_no_acoustic_numerical_quantities(valid_view):
    pkg = assemble_acoustic_operator_stub(valid_view, "bmark_01")
    for entry in pkg.entries:
        assert not hasattr(entry, "pressure")
        assert not hasattr(entry, "velocity")
        assert not hasattr(entry, "matrix_coefficient")

def test_consumes_benchmark_ready_path(valid_view):
    valid_view.is_benchmark_ready = False
    with pytest.raises(ValueError, match="not benchmark-ready"):
        assemble_acoustic_operator_stub(valid_view, "bmark_01")
