import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

import pytest
from ausolveris.geometry.model import GeometryModel
from ausolveris.geometry.pipeline import run_optimization_pipeline

def test_pipeline_renders_baseline_geometry(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    out_dir = str(tmp_path / "out1")
    res = run_optimization_pipeline(model, output_dir=out_dir, solver_params={"max_steps": 1})
    assert os.path.exists(res['output_files']['baseline_path'])
    assert os.path.getsize(res['output_files']['baseline_path']) > 0

def test_pipeline_renders_optimized_geometry(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    out_dir = str(tmp_path / "out2")
    res = run_optimization_pipeline(model, output_dir=out_dir, solver_params={"max_steps": 1})
    assert os.path.exists(res['output_files']['optimized_path'])
    assert os.path.getsize(res['output_files']['optimized_path']) > 0

def test_pipeline_renders_history_plot(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    out_dir = str(tmp_path / "out3")
    res = run_optimization_pipeline(model, output_dir=out_dir, render_history_plot=True, solver_params={"max_steps": 1})
    assert os.path.exists(res['output_files']['history_plot_path'])
    assert os.path.getsize(res['output_files']['history_plot_path']) > 0

def test_analysis_metrics_overlaid(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    res = run_optimization_pipeline(model, output_dir=str(tmp_path), solver_params={"max_steps": 1})
    assert 'initial_score' in res['analysis']
    assert 'final_score' in res['analysis']
    assert 'converged' in res['analysis']

def test_pipeline_returns_expected_structure(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    res = run_optimization_pipeline(model, output_dir=str(tmp_path), solver_params={"max_steps": 1})
    assert 'optimized_model' in res
    assert 'history' in res
    assert 'analysis' in res
    assert 'converged' in res
    assert 'output_files' in res

def test_output_dir_created_if_missing(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    non_existent_dir = tmp_path / "new_folder" / "deep"
    res = run_optimization_pipeline(model, output_dir=str(non_existent_dir), solver_params={"max_steps": 1})
    assert os.path.isdir(non_existent_dir)

def test_solver_params_passed_correctly(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0.1,0), "B": (1,0.5,0)}
    model.edges = {"AB": ("A", "B")}
    res = run_optimization_pipeline(model, output_dir=str(tmp_path), solver_params={"max_steps": 1})
    assert len(res['history']) == 2  # initial + 1 step

def test_render_params_applied(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    # Visualizer should absorb harmless render kwargs
    res = run_optimization_pipeline(model, output_dir=str(tmp_path), render_params={"point_color": "blue"}, solver_params={"max_steps": 1})
    assert 'baseline_path' in res['output_files']

def test_no_history_plot_when_disabled(tmp_path):
    model = GeometryModel()
    model.points = {"A": (0,0,0), "B": (1,0,0)}
    model.edges = {"AB": ("A", "B")}
    res = run_optimization_pipeline(model, output_dir=str(tmp_path), render_history_plot=False, solver_params={"max_steps": 1})
    assert 'history_plot_path' not in res['output_files']

def test_pipeline_handles_empty_model(tmp_path):
    model = GeometryModel() # empty
    res = run_optimization_pipeline(model, output_dir=str(tmp_path), solver_params={"max_steps": 1})
    assert 'baseline_path' in res['output_files']
    assert 'optimized_path' in res['output_files']
    assert len(res['history']) == 1 # Short circuits on empty model -> [0.0]
