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

import hashlib
import yaml
from dataclasses import dataclass
from typing import Dict, Any, Optional

from .acoustic_view import AcousticTopologyView, AcousticPatch, AcousticObserver
from .benchmark import AcousticBenchmarkDescriptor, evaluate_acoustic_benchmark_readiness
from .solver import (
    assemble_acoustic_operator_stub,
    evaluate_phy001_single_case, SingleCaseAcousticFormulationInput,
    evaluate_phy002_first_enclosure_case, FirstEnclosureFormulationInput,
    evaluate_phy003_port_inertance, PortInertanceFormulationInput,
    evaluate_lem001_driver_coupling_stub, DriverMetadata
)
from .optimizer import ObservableScoreDescriptor, compute_observable_score_stub

class PipelineStageError(Exception):
    def __init__(self, stage: str, message: str):
        self.stage = stage
        super().__init__(f"[{stage}] {message}")

@dataclass
class EndToEndPipelinePackage:
    pipeline_package_id: str
    selected_case_id: str
    formulation_summary: Dict[str, Any]
    coupling_summary: Optional[Dict[str, Any]]
    score_summary: Dict[str, Any]
    stage_status: Dict[str, str]
    input_signature: str
    
    pipeline_stage: str = "end_to_end_pipeline_stub"
    physical_solver: bool = False
    optimization_performed: bool = False
    visualization_generated: bool = False
    batch_mode: bool = False
    supported_cases_only: bool = True

def run_end_to_end_pipeline_stub(config_yaml: str) -> EndToEndPipelinePackage:
    stage_status = {}
    try:
        # 1. Geometry Stage
        stage = "geometry_stage"
        stage_status[stage] = "running"
        try:
            config = yaml.safe_load(config_yaml)
        except Exception as e:
            raise PipelineStageError(stage, f"Invalid YAML: {e}")
        if not isinstance(config, dict):
            raise PipelineStageError(stage, "YAML must be a dict")
        stage_status[stage] = "passed"
        
        # 2. Topology Stage
        stage = "topology_stage"
        stage_status[stage] = "running"
        if "topology" not in config:
            raise PipelineStageError(stage, "Missing topology config")
        try:
            t_cfg = config["topology"]
            patches = {k: AcousticPatch(k, "o", "f", (1,0,0), source_group=v.get("source_group")) 
                       for k, v in t_cfg.get("patches", {}).items()}
            observers = {k: AcousticObserver(k) for k in t_cfg.get("observers", {})}
            view = AcousticTopologyView(patches=patches, observers=observers)
            view.is_benchmark_ready = t_cfg.get("is_benchmark_ready", False)
        except Exception as e:
            raise PipelineStageError(stage, f"Topology derivation failed: {e}")
        stage_status[stage] = "passed"
        
        # 3. Benchmark Stage
        stage = "benchmark_stage"
        stage_status[stage] = "running"
        if not view.is_benchmark_ready:
            raise PipelineStageError(stage, "Topology not benchmark-ready")
        case_id = config.get("case_id")
        if not case_id:
            raise PipelineStageError(stage, "Missing case_id")
        try:
            operator_pkg = assemble_acoustic_operator_stub(view, case_id)
        except Exception as e:
            raise PipelineStageError(stage, f"Operator assembly failed: {e}")
        stage_status[stage] = "passed"
        
        # 4. Formulation Stage
        stage = "formulation_stage"
        stage_status[stage] = "running"
        formulation_result = None
        try:
            if case_id == "phy001_free_field_monopole_pressure":
                inp = SingleCaseAcousticFormulationInput(
                    topology_view=view, operator_package=operator_pkg, benchmark_id=case_id,
                    frequency_hz=config.get("frequency_hz", 100.0),
                    source_distance_m=config.get("source_distance_m", 1.0)
                )
                formulation_result = evaluate_phy001_single_case(inp)
                form_summary = {"pressure_magnitude": formulation_result.pressure_magnitude}
                
            elif case_id == "phy002_rigid_cavity_compliance":
                inp = FirstEnclosureFormulationInput(
                    topology_view=view, operator_package=operator_pkg, benchmark_id=case_id,
                    cavity_volume_m3=config.get("cavity_volume_m3")
                )
                formulation_result = evaluate_phy002_first_enclosure_case(inp)
                form_summary = {"compliance": formulation_result.acoustic_compliance_m5_per_n}
                
            elif case_id == "phy003_simple_port_inertance":
                inp = PortInertanceFormulationInput(
                    topology_view=view, operator_package=operator_pkg, benchmark_id=case_id,
                    effective_port_length_m=config.get("effective_port_length_m"),
                    port_area_m2=config.get("port_area_m2")
                )
                formulation_result = evaluate_phy003_port_inertance(inp)
                form_summary = {"inertance": formulation_result.acoustic_inertance_kg_per_m4}
            else:
                raise PipelineStageError(stage, f"Unsupported case_id: {case_id}")
        except PipelineStageError:
            raise
        except Exception as e:
            raise PipelineStageError(stage, f"Formulation failed: {e}")
        stage_status[stage] = "passed"
        
        # 5. Coupling Stage
        stage = "coupling_stage"
        coupling_summary = None
        coupling_mode = config.get("coupling_mode")
        if coupling_mode:
            stage_status[stage] = "running"
            try:
                d_cfg = config.get("driver", {})
                d_meta = DriverMetadata(fs_hz=d_cfg.get("fs_hz", 0), qts=d_cfg.get("qts", 0), vas_m3=d_cfg.get("vas_m3", 0)) if d_cfg else None
                
                if coupling_mode == "lem001_closed_box_resonance_sanity":
                    c_pkg = evaluate_lem001_driver_coupling_stub(coupling_mode, d_meta, formulation_result)
                elif coupling_mode == "lem001_port_cavity_resonance_sanity":
                    p_inp = PortInertanceFormulationInput(
                        topology_view=view, operator_package=operator_pkg, benchmark_id="phy003_simple_port_inertance",
                        effective_port_length_m=config.get("effective_port_length_m"),
                        port_area_m2=config.get("port_area_m2")
                    )
                    p_res = evaluate_phy003_port_inertance(p_inp)
                    c_pkg = evaluate_lem001_driver_coupling_stub(coupling_mode, d_meta, formulation_result, p_res)
                else:
                    raise PipelineStageError(stage, f"Unsupported coupling mode: {coupling_mode}")
                coupling_summary = {"resonance_hz": c_pkg.resonance_hz}
            except PipelineStageError:
                raise
            except Exception as e:
                raise PipelineStageError(stage, f"Coupling failed: {e}")
            stage_status[stage] = "passed"
            
        # 6. Score Stage
        stage = "score_stage"
        stage_status[stage] = "running"
        try:
            score_desc = ObservableScoreDescriptor(descriptor_id="pipe", target_observable="target")
            score_pkg = compute_observable_score_stub(formulation_result, score_desc)
            score_summary = {"score_package_id": score_pkg.score_package_id, "score": score_pkg.normalized_placeholder_score}
        except Exception as e:
            raise PipelineStageError(stage, f"Score stub failed: {e}")
        stage_status[stage] = "passed"
        
        raw_sig = f"{case_id}_{config_yaml}"
        package_id = f"pipe_{hashlib.sha256(raw_sig.encode('utf-8')).hexdigest()[:16]}"
        
        return EndToEndPipelinePackage(
            pipeline_package_id=package_id,
            selected_case_id=case_id,
            formulation_summary=form_summary,
            coupling_summary=coupling_summary,
            score_summary=score_summary,
            stage_status=stage_status,
            input_signature=raw_sig
        )
        
    except PipelineStageError as e:
        stage_status[e.stage] = "failed"
        raise
