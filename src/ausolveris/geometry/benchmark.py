from pathlib import Path
import yaml


def solver_observables_to_yaml_string(observables: dict) -> str:
    return yaml.safe_dump(observables, sort_keys=False, default_flow_style=False)


def solver_observables_to_yaml_file(observables: dict, path) -> None:
    path = Path(path)
    yaml_text = solver_observables_to_yaml_string(observables)
    path.write_text(yaml_text, encoding="utf-8")
