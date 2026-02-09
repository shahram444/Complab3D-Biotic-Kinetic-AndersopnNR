"""CompLaB3D project data model.

Defines all dataclasses representing simulation parameters.
Maps directly to the CompLaB.xml configuration structure.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
import copy
import datetime


class BoundaryType(Enum):
    DIRICHLET = "Dirichlet"
    NEUMANN = "Neumann"


class SolverType(Enum):
    CA = "CA"
    LBM = "LBM"
    FD = "FD"
    KINETICS = "kinetics"


@dataclass
class SimulationMode:
    biotic_mode: bool = True
    enable_kinetics: bool = True
    enable_abiotic_kinetics: bool = False
    enable_validation_diagnostics: bool = False


@dataclass
class PathSettings:
    src_path: str = "src"
    input_path: str = "input"
    output_path: str = "output"


@dataclass
class DomainSettings:
    nx: int = 50
    ny: int = 30
    nz: int = 30
    dx: float = 1.0
    unit: str = "um"
    characteristic_length: float = 30.0
    geometry_file: str = "geometry.dat"
    pore_material: int = 2
    solid_material: int = 0
    bounce_back_material: int = 1


@dataclass
class FluidSettings:
    delta_p: float = 2.0e-3
    peclet: float = 1.0
    tau: float = 0.8


@dataclass
class IterationSettings:
    ns_max_iT1: int = 100000
    ns_max_iT2: int = 100000
    ns_converge_iT1: float = 1e-8
    ns_converge_iT2: float = 1e-6
    ns_update_interval: int = 1
    ade_max_iT: int = 50000
    ade_converge_iT: float = 1e-8
    ade_update_interval: int = 1


@dataclass
class IOSettings:
    read_ns_file: bool = False
    read_ade_file: bool = False
    ns_filename: str = "nsLattice"
    mask_filename: str = "maskLattice"
    subs_filename: str = "subsLattice"
    bio_filename: str = "bioLattice"
    save_vtk_interval: int = 500
    save_chk_interval: int = 5000


@dataclass
class Substrate:
    name: str = ""
    initial_concentration: float = 0.0
    diffusion_in_pore: float = 1.0e-9
    diffusion_in_biofilm: float = 2.0e-10
    left_bc_type: str = "Dirichlet"
    left_bc_value: float = 0.0
    right_bc_type: str = "Neumann"
    right_bc_value: float = 0.0

    def to_dict(self):
        return {
            "name": self.name,
            "initial_concentration": self.initial_concentration,
            "diffusion_in_pore": self.diffusion_in_pore,
            "diffusion_in_biofilm": self.diffusion_in_biofilm,
            "left_bc_type": self.left_bc_type,
            "left_bc_value": self.left_bc_value,
            "right_bc_type": self.right_bc_type,
            "right_bc_value": self.right_bc_value,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Microbe:
    name: str = ""
    solver_type: str = "CA"
    reaction_type: str = "kinetics"
    material_numbers: str = "3"
    initial_densities: str = "10.0 10.0"
    decay_coefficient: float = 1.0e-9
    viscosity_ratio: float = 10.0
    half_saturation_constants: str = ""
    max_uptake_flux: str = ""
    left_bc_type: str = "Neumann"
    left_bc_value: float = 0.0
    right_bc_type: str = "Neumann"
    right_bc_value: float = 0.0

    def to_dict(self):
        return {
            "name": self.name,
            "solver_type": self.solver_type,
            "reaction_type": self.reaction_type,
            "material_numbers": self.material_numbers,
            "initial_densities": self.initial_densities,
            "decay_coefficient": self.decay_coefficient,
            "viscosity_ratio": self.viscosity_ratio,
            "half_saturation_constants": self.half_saturation_constants,
            "max_uptake_flux": self.max_uptake_flux,
            "left_bc_type": self.left_bc_type,
            "left_bc_value": self.left_bc_value,
            "right_bc_type": self.right_bc_type,
            "right_bc_value": self.right_bc_value,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class MicrobiologySettings:
    max_biomass_density: float = 100.0
    thrd_biofilm_fraction: float = 0.1
    ca_method: str = "half"


@dataclass
class EquilibriumSettings:
    enabled: bool = False
    components: List[str] = field(default_factory=list)
    stoichiometry: List[List[float]] = field(default_factory=list)
    log_k: List[float] = field(default_factory=list)

    def to_dict(self):
        return {
            "enabled": self.enabled,
            "components": self.components[:],
            "stoichiometry": [row[:] for row in self.stoichiometry],
            "log_k": self.log_k[:],
        }

    @classmethod
    def from_dict(cls, d):
        obj = cls()
        obj.enabled = d.get("enabled", False)
        obj.components = d.get("components", [])[:]
        obj.stoichiometry = [row[:] for row in d.get("stoichiometry", [])]
        obj.log_k = d.get("log_k", [])[:]
        return obj


@dataclass
class CompLaBProject:
    name: str = "Untitled"
    description: str = ""
    project_dir: str = ""
    created: str = ""
    modified: str = ""
    paths: PathSettings = field(default_factory=PathSettings)
    simulation_mode: SimulationMode = field(default_factory=SimulationMode)
    domain: DomainSettings = field(default_factory=DomainSettings)
    fluid: FluidSettings = field(default_factory=FluidSettings)
    iteration: IterationSettings = field(default_factory=IterationSettings)
    io_settings: IOSettings = field(default_factory=IOSettings)
    substrates: List[Substrate] = field(default_factory=list)
    microbes: List[Microbe] = field(default_factory=list)
    microbiology: MicrobiologySettings = field(default_factory=MicrobiologySettings)
    equilibrium: EquilibriumSettings = field(default_factory=EquilibriumSettings)
    track_performance: bool = False

    def stamp_modified(self):
        self.modified = datetime.datetime.now().isoformat(timespec="seconds")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "project_dir": self.project_dir,
            "created": self.created,
            "modified": self.modified,
            "paths": {
                "src_path": self.paths.src_path,
                "input_path": self.paths.input_path,
                "output_path": self.paths.output_path,
            },
            "simulation_mode": {
                "biotic_mode": self.simulation_mode.biotic_mode,
                "enable_kinetics": self.simulation_mode.enable_kinetics,
                "enable_abiotic_kinetics": self.simulation_mode.enable_abiotic_kinetics,
                "enable_validation_diagnostics": self.simulation_mode.enable_validation_diagnostics,
            },
            "domain": {
                "nx": self.domain.nx,
                "ny": self.domain.ny,
                "nz": self.domain.nz,
                "dx": self.domain.dx,
                "unit": self.domain.unit,
                "characteristic_length": self.domain.characteristic_length,
                "geometry_file": self.domain.geometry_file,
                "pore_material": self.domain.pore_material,
                "solid_material": self.domain.solid_material,
                "bounce_back_material": self.domain.bounce_back_material,
            },
            "fluid": {
                "delta_p": self.fluid.delta_p,
                "peclet": self.fluid.peclet,
                "tau": self.fluid.tau,
            },
            "iteration": {
                "ns_max_iT1": self.iteration.ns_max_iT1,
                "ns_max_iT2": self.iteration.ns_max_iT2,
                "ns_converge_iT1": self.iteration.ns_converge_iT1,
                "ns_converge_iT2": self.iteration.ns_converge_iT2,
                "ns_update_interval": self.iteration.ns_update_interval,
                "ade_max_iT": self.iteration.ade_max_iT,
                "ade_converge_iT": self.iteration.ade_converge_iT,
                "ade_update_interval": self.iteration.ade_update_interval,
            },
            "io_settings": {
                "read_ns_file": self.io_settings.read_ns_file,
                "read_ade_file": self.io_settings.read_ade_file,
                "ns_filename": self.io_settings.ns_filename,
                "mask_filename": self.io_settings.mask_filename,
                "subs_filename": self.io_settings.subs_filename,
                "bio_filename": self.io_settings.bio_filename,
                "save_vtk_interval": self.io_settings.save_vtk_interval,
                "save_chk_interval": self.io_settings.save_chk_interval,
            },
            "substrates": [s.to_dict() for s in self.substrates],
            "microbes": [m.to_dict() for m in self.microbes],
            "microbiology": {
                "max_biomass_density": self.microbiology.max_biomass_density,
                "thrd_biofilm_fraction": self.microbiology.thrd_biofilm_fraction,
                "ca_method": self.microbiology.ca_method,
            },
            "equilibrium": self.equilibrium.to_dict(),
            "track_performance": self.track_performance,
        }

    @classmethod
    def from_dict(cls, d):
        proj = cls()
        proj.name = d.get("name", "Untitled")
        proj.description = d.get("description", "")
        proj.project_dir = d.get("project_dir", "")
        proj.created = d.get("created", "")
        proj.modified = d.get("modified", "")

        if "paths" in d:
            p = d["paths"]
            proj.paths = PathSettings(
                src_path=p.get("src_path", "src"),
                input_path=p.get("input_path", "input"),
                output_path=p.get("output_path", "output"),
            )

        if "simulation_mode" in d:
            sm = d["simulation_mode"]
            proj.simulation_mode = SimulationMode(
                biotic_mode=sm.get("biotic_mode", True),
                enable_kinetics=sm.get("enable_kinetics", True),
                enable_abiotic_kinetics=sm.get("enable_abiotic_kinetics", False),
                enable_validation_diagnostics=sm.get("enable_validation_diagnostics", False),
            )

        if "domain" in d:
            dd = d["domain"]
            proj.domain = DomainSettings(
                nx=dd.get("nx", 50), ny=dd.get("ny", 30), nz=dd.get("nz", 30),
                dx=dd.get("dx", 1.0), unit=dd.get("unit", "um"),
                characteristic_length=dd.get("characteristic_length", 30.0),
                geometry_file=dd.get("geometry_file", "geometry.dat"),
                pore_material=dd.get("pore_material", 2),
                solid_material=dd.get("solid_material", 0),
                bounce_back_material=dd.get("bounce_back_material", 1),
            )

        if "fluid" in d:
            f = d["fluid"]
            proj.fluid = FluidSettings(
                delta_p=f.get("delta_p", 2.0e-3),
                peclet=f.get("peclet", 1.0),
                tau=f.get("tau", 0.8),
            )

        if "iteration" in d:
            it = d["iteration"]
            proj.iteration = IterationSettings(
                ns_max_iT1=it.get("ns_max_iT1", 100000),
                ns_max_iT2=it.get("ns_max_iT2", 100000),
                ns_converge_iT1=it.get("ns_converge_iT1", 1e-8),
                ns_converge_iT2=it.get("ns_converge_iT2", 1e-6),
                ns_update_interval=it.get("ns_update_interval", 1),
                ade_max_iT=it.get("ade_max_iT", 50000),
                ade_converge_iT=it.get("ade_converge_iT", 1e-8),
                ade_update_interval=it.get("ade_update_interval", 1),
            )

        if "io_settings" in d:
            io = d["io_settings"]
            proj.io_settings = IOSettings(
                read_ns_file=io.get("read_ns_file", False),
                read_ade_file=io.get("read_ade_file", False),
                ns_filename=io.get("ns_filename", "nsLattice"),
                mask_filename=io.get("mask_filename", "maskLattice"),
                subs_filename=io.get("subs_filename", "subsLattice"),
                bio_filename=io.get("bio_filename", "bioLattice"),
                save_vtk_interval=io.get("save_vtk_interval", 500),
                save_chk_interval=io.get("save_chk_interval", 5000),
            )

        proj.substrates = [Substrate.from_dict(s) for s in d.get("substrates", [])]
        proj.microbes = [Microbe.from_dict(m) for m in d.get("microbes", [])]

        if "microbiology" in d:
            mb = d["microbiology"]
            proj.microbiology = MicrobiologySettings(
                max_biomass_density=mb.get("max_biomass_density", 100.0),
                thrd_biofilm_fraction=mb.get("thrd_biofilm_fraction", 0.1),
                ca_method=mb.get("ca_method", "half"),
            )

        if "equilibrium" in d:
            proj.equilibrium = EquilibriumSettings.from_dict(d["equilibrium"])

        proj.track_performance = d.get("track_performance", False)
        return proj

    def validate(self):
        """Return list of (level, message) tuples. level is 'error' or 'warning'."""
        issues = []
        if self.domain.nx < 1 or self.domain.ny < 1 or self.domain.nz < 1:
            issues.append(("error", "Domain dimensions must be positive"))
        if self.domain.dx <= 0:
            issues.append(("error", "Grid spacing dx must be positive"))
        if self.fluid.tau <= 0.5 or self.fluid.tau >= 2.0:
            issues.append(("warning", f"Relaxation time tau={self.fluid.tau} outside stable range (0.5, 2.0)"))
        if self.fluid.delta_p <= 0:
            issues.append(("error", "Pressure drop delta_P must be positive"))
        if self.simulation_mode.biotic_mode and len(self.microbes) == 0:
            issues.append(("warning", "Biotic mode enabled but no microbes defined"))
        if not self.simulation_mode.biotic_mode and len(self.microbes) > 0:
            issues.append(("warning", "Abiotic mode but microbes are defined (will be ignored)"))
        if self.equilibrium.enabled and len(self.equilibrium.components) == 0:
            issues.append(("error", "Equilibrium enabled but no components defined"))
        for i, s in enumerate(self.substrates):
            if not s.name.strip():
                issues.append(("error", f"Substrate {i} has no name"))
            if s.diffusion_in_pore <= 0:
                issues.append(("error", f"Substrate '{s.name}': pore diffusion must be positive"))
        for i, m in enumerate(self.microbes):
            if not m.name.strip():
                issues.append(("error", f"Microbe {i} has no name"))
        return issues
