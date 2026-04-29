import os
from pathlib import Path

def test_readme_capability_disclaimer():
    readme_path = Path("README.md")
    assert readme_path.exists(), "README.md is missing"
    content = readme_path.read_text().lower()
    
    assert "not a validated bem solver" in content, "Missing BEM disclaimer"
    assert "does not compute spl" in content, "Missing SPL disclaimer"
    assert "does not compute impedance" in content, "Missing impedance disclaimer"

def test_governance_docs_exist_and_contain_markers():
    gov_doc = Path("repo-docs-pack/docs/00-governance/07-phase-boundary-review-v0.1.md")
    assert gov_doc.exists(), "Phase boundary review missing"
    content = gov_doc.read_text().lower()
    
    assert "benchmark registration only" in content, "Missing BEN-004 non-capability marker"
    assert "visualization descriptor" in content, "Missing VIS-001 non-capability marker"
    
    changelog_path = Path("CHANGELOG.md")
    assert changelog_path.exists(), "CHANGELOG.md is missing"
    changelog_content = changelog_path.read_text().lower()
    
    assert "no solver capability added" in changelog_content, "Missing solver expansion rejection in CHANGELOG"
