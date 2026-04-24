from pathlib import Path

from .benchmark import (
    solver_observables_to_yaml_file as _solver_observables_to_yaml_file,
    solver_observables_to_yaml_string as _solver_observables_to_yaml_string,
)
from .serializer import yaml_file_to_geometry_model, yaml_string_to_geometry_model
from .solver import run_geometry_solver_stub


def run_solver_pipeline_from_yaml_string(yaml_text: str) -> dict:
    model = yaml_string_to_geometry_model(yaml_text)
    return run_geometry_solver_stub(model)


def run_solver_pipeline_from_yaml_file(path: str | Path) -> dict:
    model = yaml_file_to_geometry_model(path)
    return run_geometry_solver_stub(model)


def solver_pipeline_observables_to_yaml_string(yaml_text: str) -> str:
    observables = run_solver_pipeline_from_yaml_string(yaml_text)
    return _solver_observables_to_yaml_string(observables)


def solver_pipeline_observables_to_yaml_file(yaml_text: str, path: str | Path) -> None:
    observables = run_solver_pipeline_from_yaml_string(yaml_text)
    _solver_observables_to_yaml_file(observables, path)

import os
import matplotlib.pyplot as plt
from typing import Dict, Any, Optional
from .solver import optimize
from .analysis import analyze_solver_history
from .visualizer import GeometryVisualizer

def run_optimization_pipeline(
    model: 'GeometryModel',
    solver_params: Optional[Dict[str, Any]] = None,
    render_params: Optional[Dict[str, Any]] = None,
    output_dir: str = "output",
    render_history_plot: bool = True,
) -> Dict[str, Any]:
    """
    Run solver + visualization pipeline.
    """
    if solver_params is None:
        solver_params = {}
    if render_params is None:
        render_params = {}
    
    # Run solver
    opt_model, info = optimize(model, **solver_params)
    history = info['history']
    converged = info['converged']
    
    # Analyze
    analysis = analyze_solver_history(history)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    output_files = {}
    
    # Render baseline geometry
    base_path = os.path.join(output_dir, "baseline.png")
    viz = GeometryVisualizer()
    viz.create_figure()
    viz.render_model(model, **render_params)
    viz.save_png(base_path)
    output_files['baseline_path'] = base_path
    
    # Render optimized geometry
    opt_path = os.path.join(output_dir, "optimized.png")
    viz2 = GeometryVisualizer()
    viz2.create_figure()
    viz2.render_model(opt_model, **render_params)
    viz2.save_png(opt_path)
    output_files['optimized_path'] = opt_path
    
    # Render history plot
    if render_history_plot:
        plt.figure()
        plt.plot(history, marker='o')
        plt.xlabel('Step')
        plt.ylabel('Objective')
        plt.title('Optimization History')
        hist_path = os.path.join(output_dir, "history_plot.png")
        plt.savefig(hist_path)
        plt.close()
        output_files['history_plot_path'] = hist_path
        
    return {
        'optimized_model': opt_model,
        'history': history,
        'analysis': analysis,
        'converged': converged,
        'output_files': output_files
    }
