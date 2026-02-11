"""
Data models for CompLaB projects
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from enum import Enum


class SolverType(Enum):
    """Solver type enumeration"""
    KINETICS = "kinetics"
    CELLULAR_AUTOMATA = "CA"
    FINITE_DIFFERENCE = "FD"
    LATTICE_BOLTZMANN = "LBM"
    

class BoundaryType(Enum):
    """Boundary condition type"""
    DIRICHLET = "Dirichlet"
    NEUMANN = "Neumann"


class DistributionType(Enum):
    """Microbe distribution patterns"""
    SURFACE_LAYER = "surface_layer"
    RANDOM_SPARSE = "random_sparse"
    RANDOM_DENSE = "random_dense"
    GRADIENT = "gradient"
    HOTSPOTS = "hotspots"
    UNIFORM = "uniform"


@dataclass
class DomainSettings:
    """Domain configuration"""
    nx: int = 100
    ny: int = 100
    nz: int = 100
    dx: float = 10.0  # um
    dy: float = 10.0
    dz: float = 10.0
    unit: str = "um"
    characteristic_length: float = 10.0
    geometry_file: str = ""
    
    # Material numbers
    pore_material: int = 2
    solid_material: int = 0
    bounce_back_material: int = 1


@dataclass 
class FluidSettings:
    """Fluid/flow settings"""
    delta_p: float = 1e-3
    peclet: float = 1.0
    tau: float = 0.8
    

@dataclass
class IterationSettings:
    """Iteration/convergence settings"""
    # NS solver
    ns_rerun_iT0: int = 0
    ns_max_iT1: int = 10000
    ns_max_iT2: int = 5000
    ns_converge_iT1: float = 1e-6
    ns_converge_iT2: float = 1e-5
    ns_update_interval: int = 10
    
    # ADE solver
    ade_rerun_iT0: int = 0
    ade_max_iT: int = 100000
    ade_converge_iT: float = 1e-7
    ade_update_interval: int = 1
    

@dataclass
class IOSettings:
    """Input/Output settings"""
    read_ns_file: bool = False
    read_ade_file: bool = False
    ns_filename: str = "nsLattice"
    mask_filename: str = "maskLattice"
    subs_filename: str = "subsLattice"
    bio_filename: str = "bioLattice"
    save_vtk_interval: int = 100
    save_chk_interval: int = 1000
    track_performance: bool = False


@dataclass
class DiffusionCoefficients:
    """Diffusion coefficients in different zones"""
    in_pore: float = 1e-9
    in_biofilm: float = 1e-10
    

@dataclass
class BoundaryCondition:
    """Boundary condition specification"""
    bc_type: BoundaryType = BoundaryType.DIRICHLET
    value: float = 0.0


@dataclass
class Substrate:
    """Substrate/chemical species configuration"""
    name: str = "substrate"
    diffusion_coefficients: DiffusionCoefficients = field(default_factory=DiffusionCoefficients)
    initial_concentration: float = 1.0
    left_boundary: BoundaryCondition = field(default_factory=lambda: BoundaryCondition(BoundaryType.DIRICHLET, 1.0))
    right_boundary: BoundaryCondition = field(default_factory=lambda: BoundaryCondition(BoundaryType.NEUMANN, 0.0))
    

@dataclass
class MicrobeDistribution:
    """Microbe spatial distribution configuration"""
    dist_type: DistributionType = DistributionType.UNIFORM
    density: float = 0.1  # fraction
    thickness: int = 1  # for surface layer
    inlet_density: float = 0.3  # for gradient
    outlet_density: float = 0.05
    num_hotspots: int = 3
    hotspot_radius: int = 10
    hotspot_density: float = 0.5


@dataclass
class Microbe:
    """Microbe/biomass configuration"""
    name: str = "microbe"
    solver_type: SolverType = SolverType.CELLULAR_AUTOMATA
    material_number: int = 3
    
    # Initial conditions
    initial_densities: List[float] = field(default_factory=lambda: [10.0])
    distribution: MicrobeDistribution = field(default_factory=MicrobeDistribution)
    
    # Diffusion
    diffusion_coefficients: DiffusionCoefficients = field(default_factory=lambda: DiffusionCoefficients(0, 0))
    
    # Boundaries
    left_boundary: BoundaryCondition = field(default_factory=lambda: BoundaryCondition(BoundaryType.NEUMANN, 0.0))
    right_boundary: BoundaryCondition = field(default_factory=lambda: BoundaryCondition(BoundaryType.NEUMANN, 0.0))
    
    # Kinetics parameters
    decay_coefficient: float = 1e-6  # 1/s
    half_saturation_constants: List[float] = field(default_factory=lambda: [0.1])
    maximum_uptake_flux: List[float] = field(default_factory=lambda: [0.2, 5.0])
    
    # CA specific
    viscosity_ratio_in_biofilm: float = 0.0


@dataclass
class KineticsModel:
    """Custom kinetics model definition"""
    name: str = "default"
    description: str = ""
    code: str = ""  # Custom C++ code for defineKinetics.hh
    parameters: Dict[str, float] = field(default_factory=dict)


@dataclass
class MicrobiologySettings:
    """Global microbiology settings"""
    maximum_biomass_density: float = 80.0
    thrd_biofilm_fraction: float = 0.1
    ca_method: str = "fraction"  # "fraction" or "half"


class CompLaBProject:
    """Main project class containing all simulation settings"""
    
    def __init__(self, name: str = "Untitled"):
        self.name = name
        self.path: Optional[str] = None
        self.created: str = ""
        self.modified: str = ""
        self.description: str = ""
        
        # Settings
        self.domain = DomainSettings()
        self.fluid = FluidSettings()
        self.iterations = IterationSettings()
        self.io = IOSettings()
        self.microbiology = MicrobiologySettings()
        
        # Species
        self.substrates: List[Substrate] = []
        self.microbes: List[Microbe] = []
        
        # Custom kinetics
        self.kinetics_model: Optional[KineticsModel] = None
        
        # Paths
        self.input_path: str = "input"
        self.output_path: str = "output"
        
    @property
    def num_substrates(self) -> int:
        return len(self.substrates)
        
    @property
    def num_microbes(self) -> int:
        return len(self.microbes)
        
    def add_substrate(self, substrate: Substrate):
        """Add a substrate to the project"""
        self.substrates.append(substrate)
        # Update half-saturation constants for all microbes
        for microbe in self.microbes:
            if len(microbe.half_saturation_constants) < len(self.substrates):
                microbe.half_saturation_constants.append(0.1)
                
    def remove_substrate(self, index: int):
        """Remove a substrate from the project"""
        if 0 <= index < len(self.substrates):
            self.substrates.pop(index)
            # Update microbe parameters
            for microbe in self.microbes:
                if len(microbe.half_saturation_constants) > index:
                    microbe.half_saturation_constants.pop(index)
                    
    def add_microbe(self, microbe: Microbe):
        """Add a microbe to the project"""
        self.microbes.append(microbe)
        
    def remove_microbe(self, index: int):
        """Remove a microbe from the project"""
        if 0 <= index < len(self.microbes):
            self.microbes.pop(index)
            
    def get_project_dir(self) -> str:
        """Get project directory"""
        if self.path:
            return os.path.dirname(self.path)
        return ""
        
    def get_input_dir(self) -> str:
        """Get input directory path"""
        return os.path.join(self.get_project_dir(), self.input_path)
        
    def get_output_dir(self) -> str:
        """Get output directory path"""
        return os.path.join(self.get_project_dir(), self.output_path)
        
    def get_xml_path(self) -> str:
        """Get XML configuration file path - CompLaB.xml in project root"""
        return os.path.join(self.get_project_dir(), "CompLaB.xml")
        
    def has_results(self) -> bool:
        """Check if project has simulation results"""
        output_dir = self.get_output_dir()
        if os.path.exists(output_dir):
            # Check for VTK files
            for f in os.listdir(output_dir):
                if f.endswith('.vti') or f.endswith('.vtk'):
                    return True
        return False
        
    def validate(self) -> List[str]:
        """Validate project settings, return list of errors"""
        errors = []
        
        # Domain validation
        if self.domain.nx <= 0 or self.domain.ny <= 0 or self.domain.nz <= 0:
            errors.append("Domain dimensions must be positive")
        if self.domain.dx <= 0:
            errors.append("Grid spacing must be positive")
            
        # Geometry file
        if not self.domain.geometry_file:
            errors.append("Geometry file not specified")
        elif self.path:
            geom_path = os.path.join(self.get_input_dir(), self.domain.geometry_file)
            if not os.path.exists(geom_path):
                errors.append(f"Geometry file not found: {self.domain.geometry_file}")
                
        # Fluid settings
        if self.fluid.tau < 0.5:
            errors.append("Tau must be >= 0.5 for stability")
            
        # Substrates
        if len(self.substrates) == 0:
            errors.append("At least one substrate is required")
            
        for i, sub in enumerate(self.substrates):
            if not sub.name:
                errors.append(f"Substrate {i} has no name")
            if sub.diffusion_coefficients.in_pore <= 0:
                errors.append(f"Substrate '{sub.name}' has invalid diffusion coefficient")
                
        # Microbes
        for i, mic in enumerate(self.microbes):
            if not mic.name:
                errors.append(f"Microbe {i} has no name")
            if len(mic.half_saturation_constants) != len(self.substrates):
                errors.append(f"Microbe '{mic.name}' has wrong number of half-saturation constants")
            if mic.solver_type == SolverType.CELLULAR_AUTOMATA:
                if self.microbiology.maximum_biomass_density <= 0:
                    errors.append("Maximum biomass density must be positive for CA solver")
                    
        return errors
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert project to dictionary for serialization"""
        def convert_enum(obj):
            if isinstance(obj, Enum):
                return obj.value
            elif isinstance(obj, dict):
                return {k: convert_enum(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_enum(v) for v in obj]
            elif hasattr(obj, '__dataclass_fields__'):
                return {k: convert_enum(v) for k, v in asdict(obj).items()}
            return obj
            
        return {
            "name": self.name,
            "description": self.description,
            "created": self.created,
            "modified": self.modified,
            "domain": convert_enum(asdict(self.domain)),
            "fluid": convert_enum(asdict(self.fluid)),
            "iterations": convert_enum(asdict(self.iterations)),
            "io": convert_enum(asdict(self.io)),
            "microbiology": convert_enum(asdict(self.microbiology)),
            "substrates": [convert_enum(asdict(s)) for s in self.substrates],
            "microbes": [convert_enum(asdict(m)) for m in self.microbes],
            "input_path": self.input_path,
            "output_path": self.output_path,
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompLaBProject':
        """Create project from dictionary"""
        project = cls(data.get("name", "Untitled"))
        project.description = data.get("description", "")
        project.created = data.get("created", "")
        project.modified = data.get("modified", "")
        
        # Load settings
        if "domain" in data:
            project.domain = DomainSettings(**data["domain"])
        if "fluid" in data:
            project.fluid = FluidSettings(**data["fluid"])
        if "iterations" in data:
            project.iterations = IterationSettings(**data["iterations"])
        if "io" in data:
            project.io = IOSettings(**data["io"])
        if "microbiology" in data:
            project.microbiology = MicrobiologySettings(**data["microbiology"])
            
        # Load substrates
        for sub_data in data.get("substrates", []):
            # Handle nested dataclasses
            if "diffusion_coefficients" in sub_data:
                sub_data["diffusion_coefficients"] = DiffusionCoefficients(**sub_data["diffusion_coefficients"])
            if "left_boundary" in sub_data:
                lb = sub_data["left_boundary"]
                sub_data["left_boundary"] = BoundaryCondition(
                    BoundaryType(lb["bc_type"]) if isinstance(lb["bc_type"], str) else lb["bc_type"],
                    lb["value"]
                )
            if "right_boundary" in sub_data:
                rb = sub_data["right_boundary"]
                sub_data["right_boundary"] = BoundaryCondition(
                    BoundaryType(rb["bc_type"]) if isinstance(rb["bc_type"], str) else rb["bc_type"],
                    rb["value"]
                )
            project.substrates.append(Substrate(**sub_data))
            
        # Load microbes
        for mic_data in data.get("microbes", []):
            if "solver_type" in mic_data:
                mic_data["solver_type"] = SolverType(mic_data["solver_type"])
            if "diffusion_coefficients" in mic_data:
                mic_data["diffusion_coefficients"] = DiffusionCoefficients(**mic_data["diffusion_coefficients"])
            if "distribution" in mic_data:
                dist = mic_data["distribution"]
                if "dist_type" in dist:
                    dist["dist_type"] = DistributionType(dist["dist_type"])
                mic_data["distribution"] = MicrobeDistribution(**dist)
            if "left_boundary" in mic_data:
                lb = mic_data["left_boundary"]
                mic_data["left_boundary"] = BoundaryCondition(
                    BoundaryType(lb["bc_type"]) if isinstance(lb["bc_type"], str) else lb["bc_type"],
                    lb["value"]
                )
            if "right_boundary" in mic_data:
                rb = mic_data["right_boundary"]
                mic_data["right_boundary"] = BoundaryCondition(
                    BoundaryType(rb["bc_type"]) if isinstance(rb["bc_type"], str) else rb["bc_type"],
                    rb["value"]
                )
            project.microbes.append(Microbe(**mic_data))
            
        project.input_path = data.get("input_path", "input")
        project.output_path = data.get("output_path", "output")
        
        return project
