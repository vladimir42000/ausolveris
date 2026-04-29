from typing import Dict, Tuple, Optional
import matplotlib.pyplot as plt
from .model import GeometryModel

class GeometryVisualizer:
    """Renders points (x,y from 3D) and edges from a GeometryModel."""
    
    def __init__(self, figsize: tuple = (8, 6)):
        self.figsize = figsize
        self.fig = None
        self.ax = None
    
    def create_figure(self):
        self.fig, self.ax = plt.subplots(figsize=self.figsize)
        self.ax.set_aspect('equal')
        self.ax.grid(True)
    
    def render_model(self, model: GeometryModel,
                     point_color='blue', point_marker='o', point_size=50,
                     edge_color='black', edge_linewidth=1):
        """Render all points and edges from a GeometryModel.
        Points are stored as (x, y, z); uses x, y only."""
        if not model.points:
            return
        # Points: dict id -> (x, y, z)
        xs = [p[0] for p in model.points.values()]
        ys = [p[1] for p in model.points.values()]
        self.ax.scatter(xs, ys, color=point_color, marker=point_marker, s=point_size)
        
        # Edges: dict id -> (start_id, end_id)
        for start_id, end_id in model.edges.values():
            if start_id in model.points and end_id in model.points:
                start = model.points[start_id]
                end = model.points[end_id]
                self.ax.plot([start[0], end[0]], [start[1], end[1]],
                             color=edge_color, linewidth=edge_linewidth)
    
    def save_png(self, filepath: str, dpi=150):
        if self.fig is None:
            raise RuntimeError("No figure created. Call create_figure() first.")
        self.fig.savefig(filepath, dpi=dpi, bbox_inches='tight')
        plt.close(self.fig)
    
    def show(self):
        if self.fig:
            plt.show()

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List
from .optimizer import ObservableScorePackage

REJECTED_LABELS = {
    "spl", "frequency_response", "closed_box_response", 
    "bass_reflex_response", "impedance", "transfer_function", 
    "spl_response", "impedance_curve", "cb_response", 
    "br_response", "optimized_design"
}

@dataclass
class ObservableVisualizationDescriptor:
    plot_label: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ObservableVisualizationPackage:
    plot_package_id: str
    source_package_id: str
    plot_label: str
    annotations: Dict[str, Any] = field(default_factory=dict)
    placeholder_x: List[float] = field(default_factory=list)
    placeholder_y: List[float] = field(default_factory=list)
    
    visualization_stage: str = "visualization_stub"
    non_physical_plot: bool = True
    spl_plot: bool = False
    frequency_response: bool = False
    impedance_plot: bool = False
    optimization_plot: bool = False
    cb_response_plot: bool = False
    br_response_plot: bool = False
    
    placeholder_data: bool = True
    physical_response: bool = False
    acoustic_units: str = "none"

def validate_visualization_label(label: str) -> None:
    if label.lower() in REJECTED_LABELS:
        raise ValueError(f"Visualization label '{label}' is strictly forbidden by VIS-001.")

def build_observable_visualization_stub(
    input_package: Any, 
    descriptor: ObservableVisualizationDescriptor
) -> ObservableVisualizationPackage:
    
    # Deferred import to break the circular dependency loop
    from .pipeline import EndToEndPipelinePackage
    
    validate_visualization_label(descriptor.plot_label)
    
    annotations = {}
    source_id = ""
    
    if isinstance(input_package, EndToEndPipelinePackage):
        source_id = input_package.pipeline_package_id
        if getattr(input_package, "coupling_summary", None):
            annotations["lem_scalar_sanity"] = input_package.coupling_summary
    elif isinstance(input_package, ObservableScorePackage):
        source_id = input_package.score_package_id
    else:
        raise TypeError("Unsupported package type. Expected EndToEndPipelinePackage or ObservableScorePackage.")
        
    raw_sig = f"{source_id}_{descriptor.plot_label}"
    hashed_id = hashlib.sha256(raw_sig.encode('utf-8')).hexdigest()[:16]
    package_id = f"vis_{hashed_id}"
    
    x_array = [0.0, 1.0] if descriptor.metadata.get("include_placeholders") else []
    y_array = [0.0, 0.0] if descriptor.metadata.get("include_placeholders") else []

    return ObservableVisualizationPackage(
        plot_package_id=package_id,
        source_package_id=source_id,
        plot_label=descriptor.plot_label,
        annotations=annotations,
        placeholder_x=x_array,
        placeholder_y=y_array
    )

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Any, List, Union
from .optimizer import ObservableScorePackage

REJECTED_LABELS = {
    "spl", "frequency_response", "closed_box_response", 
    "bass_reflex_response", "impedance", "transfer_function", 
    "spl_response", "impedance_curve", "cb_response", 
    "br_response", "optimized_design"
}

@dataclass
class ObservableVisualizationDescriptor:
    plot_label: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ObservableVisualizationPackage:
    plot_package_id: str
    source_package_id: str
    plot_label: str
    annotations: Dict[str, Any] = field(default_factory=dict)
    placeholder_x: List[float] = field(default_factory=list)
    placeholder_y: List[float] = field(default_factory=list)
    
    visualization_stage: str = "visualization_stub"
    non_physical_plot: bool = True
    spl_plot: bool = False
    frequency_response: bool = False
    impedance_plot: bool = False
    optimization_plot: bool = False
    cb_response_plot: bool = False
    br_response_plot: bool = False
    
    placeholder_data: bool = True
    physical_response: bool = False
    acoustic_units: str = "none"

def validate_visualization_label(label: str) -> None:
    if label.lower() in REJECTED_LABELS:
        raise ValueError(f"Visualization label '{label}' is strictly forbidden by VIS-001.")

def build_observable_visualization_stub(
    input_package: Any, 
    descriptor: ObservableVisualizationDescriptor
) -> ObservableVisualizationPackage:
    
    # Deferred import to break the circular dependency loop
    from .pipeline import EndToEndPipelinePackage
    
    validate_visualization_label(descriptor.plot_label)
    
    annotations = {}
    source_id = ""
    
    if isinstance(input_package, EndToEndPipelinePackage):
        source_id = input_package.pipeline_package_id
        if getattr(input_package, "coupling_summary", None):
            annotations["lem_scalar_sanity"] = input_package.coupling_summary
    elif isinstance(input_package, ObservableScorePackage):
        source_id = input_package.score_package_id
    else:
        raise TypeError("Unsupported package type. Expected EndToEndPipelinePackage or ObservableScorePackage.")
        
    raw_sig = f"{source_id}_{descriptor.plot_label}"
    hashed_id = hashlib.sha256(raw_sig.encode('utf-8')).hexdigest()[:16]
    package_id = f"vis_{hashed_id}"
    
    x_array = [0.0, 1.0] if descriptor.metadata.get("include_placeholders") else []
    y_array = [0.0, 0.0] if descriptor.metadata.get("include_placeholders") else []

    return ObservableVisualizationPackage(
        plot_package_id=package_id,
        source_package_id=source_id,
        plot_label=descriptor.plot_label,
        annotations=annotations,
        placeholder_x=x_array,
        placeholder_y=y_array
    )
