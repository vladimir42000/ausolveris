import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.analysis import analyze_solver_history

def test_empty_history():
    result = analyze_solver_history([])
    assert result == {}

def test_single_step_history():
    result = analyze_solver_history([0.5])
    assert result['initial_score'] == 0.5
    assert result['final_score'] == 0.5
    assert result['best_score'] == 0.5
    assert result['best_step'] == 0
    assert result['total_steps'] == 0
    assert result['converged'] is False

def test_converged_history():
    # Sequence: 1.0 -> 0.9 (0.1), 0.9 -> 0.81 (0.09), 0.81 -> 0.73 (0.08), 
    # 0.73 -> 0.72 (0.01), 0.72 -> 0.719 (0.001)
    hist = [1.0, 0.9, 0.81, 0.73, 0.72, 0.719] 
    # With tolerance 0.01, step 4 (change=0.01) is NOT < 0.01.
    # Step 5 (change=0.001) IS < 0.01.
    result = analyze_solver_history(hist, tolerance=1e-2)
    assert result['converged'] is True
    assert result['convergence_step'] == 5 

def test_non_converged_history():
    hist = [1.0, 0.5, 0.6, 0.55, 0.57]
    result = analyze_solver_history(hist, tolerance=1e-6)
    assert result['converged'] is False
    assert result['convergence_step'] is None

def test_best_metric_capture():
    hist = [3.0, 2.0, 1.0, 4.0, 2.5]
    result = analyze_solver_history(hist)
    assert result['best_score'] == 1.0
    assert result['best_step'] == 2
    assert result['score_range'] == 3.0

def test_improvement_calculation():
    hist = [10.0, 8.0, 5.0]
    result = analyze_solver_history(hist)
    assert result['improvement'] == 5.0

def test_total_steps():
    hist = [1.0, 0.9, 0.8, 0.7]
    result = analyze_solver_history(hist)
    assert result['total_steps'] == 3

def test_convergence_step_indexing():
    hist = [1.0, 0.9, 0.8, 0.79]
    # change at step 3 is 0.01, which is < 0.015
    result = analyze_solver_history(hist, tolerance=0.015)
    assert result['convergence_step'] == 3

def test_no_convergence_when_tolerance_zero():
    hist = [1.0, 0.999, 0.998]
    result = analyze_solver_history(hist, tolerance=0.0)
    assert result['converged'] is False

def test_non_monotonic_best_step():
    hist = [5.0, 3.0, 4.0, 2.0, 2.5]
    result = analyze_solver_history(hist)
    assert result['best_step'] == 3
