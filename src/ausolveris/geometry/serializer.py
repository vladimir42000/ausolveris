"""YAML serialization for GeometryModel using existing to_dict/from_dict."""

from pathlib import Path
from typing import Union
import yaml

from .model import GeometryModel  # relative import within package
from .schema import validate_geometry_dict


def geometry_model_to_yaml_string(model: GeometryModel) -> str:
    """
    Convert a GeometryModel instance to a YAML string.
    """
    data = model.to_dict()
    return yaml.safe_dump(data, sort_keys=False, default_flow_style=False)


def yaml_string_to_geometry_model(yaml_str: str) -> GeometryModel:
    """
    Parse a YAML string, validate it, and construct a GeometryModel.
    """
    data = yaml.safe_load(yaml_str)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    validate_geometry_dict(data)
    return GeometryModel.from_dict(data)


def geometry_model_to_yaml_file(model: GeometryModel, path: Union[str, Path]) -> None:
    """
    Write a GeometryModel to a YAML file.
    """
    path = Path(path)
    yaml_str = geometry_model_to_yaml_string(model)
    path.write_text(yaml_str, encoding="utf-8")


def yaml_file_to_geometry_model(path: Union[str, Path]) -> GeometryModel:
    """
    Read a YAML file and construct a GeometryModel from it.
    """
    path = Path(path)
    yaml_str = path.read_text(encoding="utf-8")
    return yaml_string_to_geometry_model(yaml_str)
