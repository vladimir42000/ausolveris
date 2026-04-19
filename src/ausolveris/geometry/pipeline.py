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
