import os
from pathlib import Path

PLAN_PATH = Path("repo-docs-pack/docs/30-spec/09-bem-rigid-sphere-execution-plan-v0.1.md")

def test_bem_plan001_document_exists():
    assert PLAN_PATH.exists(), "BEM-PLAN-001 planning document is missing"

def test_bem_plan001_contains_phase_boundary_markers():
    content = PLAN_PATH.read_text().lower()
    assert "no solver logic exists" in content or "no scattering solve" in content
    assert "no matrix assembly" in content
    assert "not executed" in content

def test_bem_plan001_contains_staged_future_sequence():
    content = PLAN_PATH.read_text()
    assert "BEM-001" in content
    assert "BEM-002" in content
    assert "BEM-003" in content
    assert "BEM-004" in content
    assert "Scalar Helmholtz Green-function utility" in content
    assert "Rigid-sphere benchmark mesh" in content

def test_bem_plan001_identifies_core_conventions():
    content = PLAN_PATH.read_text().lower()
    assert "ben004_rigid_sphere_scattering_registered" in content
    assert "rigid sphere" in content
    assert "neumann" in content or "sound-hard" in content
    assert "analytical" in content
    assert "tolerance policy" in content
