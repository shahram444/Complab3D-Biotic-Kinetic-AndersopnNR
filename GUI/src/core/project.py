"""CompLaB3D project data model - exact match to C++ solver XML parameters."""

from dataclasses import dataclass, field
from typing import List
import copy


@dataclass
class PathSettings:
    """<path> section of CompLaB.xml."""
    src_path: str = "src"
    input_path: str = "input"
    output_path: str = "output"


@dataclass
class SimulationMode:
    """<simulation_mode> section."""
    biotic_mode: bool = True
    enable_kinetics: bool = True
    enable_abiotic_kinetics: bool = False
    enable_validation_diagnostics: bool = False


@dataclass
class DomainSettings:
    """<LB_numerics><domain> section.

    Note: C++ solver adds +2 to nx internally for ghost boundary nodes.
    The GUI stores the user-facing value (what goes into XML).
    dy/dz default to dx if set to 0.
    """
    nx: int = 50
    ny: int = 30
    nz: int = 30
    dx: float = 1.0
    dy: float = 0.0
    dz: float = 0.0
    unit: str = "um"
    characteristic_length: float = 30.0
    geometry_filename: str = "geometry.dat"
    pore: str = "2"
    solid: str = "0"
    bounce_back: str = "1"


@dataclass
class FluidSettings:
    """<LB_numerics> flow parameters."""
    delta_P: float = 2.0e-3
    peclet: float = 1.0
    tau: float = 0.8
    track_performance: bool = False


@dataclass
class IterationSettings:
    """<LB_numerics><iteration> section."""
    ns_max_iT1: int = 100000
    ns_max_iT2: int = 100000
    ns_converge_iT1: float = 1e-8
    ns_converge_iT2: float = 1e-6
    ade_max_iT: int = 50000
    ade_converge_iT: float = 1e-8
    ns_rerun_iT0: int = 0
    ade_rerun_iT0: int = 0
    ns_update_interval: int = 1
    ade_update_interval: int = 1


@dataclass
class Substrate:
    """Single substrate in <chemistry><substrate{i}> section."""
    name: str = "substrate_0"
    initial_concentration: float = 0.0
    diffusion_in_pore: float = 1e-9
    diffusion_in_biofilm: float = 2e-10
    left_boundary_type: str = "Dirichlet"
    right_boundary_type: str = "Neumann"
    left_boundary_condition: float = 0.0
    right_boundary_condition: float = 0.0


@dataclass
class Microbe:
    """Single microbe in <microbiology><microbe{i}> section.

    material_number: space-separated integers, e.g. "3" or "3 6" for core+fringe.
    initial_densities: space-separated floats, must match material_number count.
    half_saturation_constants / maximum_uptake_flux: space-separated floats,
        length must equal number of substrates.
    """
    name: str = "microbe_0"
    solver_type: str = "CA"
    reaction_type: str = "kinetics"
    material_number: str = ""
    initial_densities: str = "99.0"
    decay_coefficient: float = 0.0
    viscosity_ratio_in_biofilm: float = 10.0
    half_saturation_constants: str = ""
    maximum_uptake_flux: str = ""
    left_boundary_type: str = "Neumann"
    right_boundary_type: str = "Neumann"
    left_boundary_condition: float = 0.0
    right_boundary_condition: float = 0.0
    biomass_diffusion_in_pore: float = -99.0
    biomass_diffusion_in_biofilm: float = -99.0


@dataclass
class MicrobiologySettings:
    """<microbiology> global settings + microbe list."""
    maximum_biomass_density: float = 100.0
    thrd_biofilm_fraction: float = 0.1
    ca_method: str = "fraction"
    microbes: List[Microbe] = field(default_factory=list)


@dataclass
class EquilibriumSettings:
    """<equilibrium> section.

    stoichiometry: 2D list [species_index][component_index].
    log_k: list of floats, one per species (substrate).
    Solver parameters match C++ defaults in complab3d_processors_part4_eqsolver.hh.
    """
    enabled: bool = False
    component_names: List[str] = field(default_factory=list)
    stoichiometry: List[List[float]] = field(default_factory=list)
    log_k: List[float] = field(default_factory=list)
    max_iterations: int = 200
    tolerance: float = 1e-8
    anderson_depth: int = 4
    beta: float = 1.0


@dataclass
class IOSettings:
    """<IO> section."""
    read_ns_file: bool = False
    read_ade_file: bool = False
    ns_filename: str = "nsLattice"
    mask_filename: str = "maskLattice"
    subs_filename: str = "subsLattice"
    bio_filename: str = "bioLattice"
    save_vtk_interval: int = 500
    save_chk_interval: int = 5000


@dataclass
class CompLaBProject:
    """Root project data model, maps 1:1 to CompLaB.xml structure."""
    name: str = "Untitled"
    path_settings: PathSettings = field(default_factory=PathSettings)
    simulation_mode: SimulationMode = field(default_factory=SimulationMode)
    domain: DomainSettings = field(default_factory=DomainSettings)
    fluid: FluidSettings = field(default_factory=FluidSettings)
    iteration: IterationSettings = field(default_factory=IterationSettings)
    substrates: List[Substrate] = field(default_factory=list)
    microbiology: MicrobiologySettings = field(default_factory=MicrobiologySettings)
    equilibrium: EquilibriumSettings = field(default_factory=EquilibriumSettings)
    io_settings: IOSettings = field(default_factory=IOSettings)

    def deep_copy(self) -> "CompLaBProject":
        return copy.deepcopy(self)

    def validate(self) -> List[str]:
        """Return list of validation error strings. Empty = valid."""
        errors = []
        d = self.domain
        if d.nx < 1 or d.ny < 1 or d.nz < 1:
            errors.append("Domain dimensions must be positive integers.")
        if d.dx <= 0:
            errors.append("Grid spacing dx must be positive.")
        if d.unit not in ("m", "mm", "um"):
            errors.append("Unit must be m, mm, or um.")
        if not d.geometry_filename:
            errors.append("Geometry filename is required.")
        if not d.geometry_filename.endswith(".dat"):
            errors.append("Geometry file must be a .dat file.")

        f = self.fluid
        if f.tau <= 0.5:
            errors.append("Relaxation time tau must be > 0.5 for stability.")

        num_subs = len(self.substrates)
        for i, s in enumerate(self.substrates):
            if not s.name:
                errors.append(f"Substrate {i} must have a name.")
            if s.left_boundary_type not in ("Dirichlet", "Neumann"):
                errors.append(f"Substrate {i}: left BC must be Dirichlet or Neumann.")
            if s.right_boundary_type not in ("Dirichlet", "Neumann"):
                errors.append(f"Substrate {i}: right BC must be Dirichlet or Neumann.")

        sm = self.simulation_mode
        if sm.biotic_mode:
            for i, m in enumerate(self.microbiology.microbes):
                if m.solver_type not in ("CA", "LBM", "FD"):
                    errors.append(f"Microbe {i}: solver must be CA, LBM, or FD.")
                # Material number is only required for sessile (CA) microbes
                if m.material_number.strip():
                    mat_nums = m.material_number.strip().split()
                    init_dens = m.initial_densities.strip().split()
                    if len(mat_nums) != len(init_dens):
                        errors.append(
                            f"Microbe {i}: material_number count ({len(mat_nums)}) "
                            f"must match initial_densities count ({len(init_dens)})."
                        )
                if m.solver_type == "CA":
                    if self.microbiology.maximum_biomass_density <= 0:
                        errors.append("CA solver requires positive maximum_biomass_density.")
                if m.solver_type == "FD":
                    if m.biomass_diffusion_in_pore < 0:
                        errors.append(f"Microbe {i}: FD solver requires biomass_diffusion_in_pore.")
                    if m.biomass_diffusion_in_biofilm < 0:
                        errors.append(f"Microbe {i}: FD solver requires biomass_diffusion_in_biofilm.")
                if num_subs > 0 and m.half_saturation_constants.strip():
                    ks_vals = m.half_saturation_constants.strip().split()
                    if len(ks_vals) != num_subs:
                        errors.append(
                            f"Microbe {i}: half_saturation_constants length ({len(ks_vals)}) "
                            f"must equal number of substrates ({num_subs})."
                        )
                if num_subs > 0 and m.maximum_uptake_flux.strip():
                    vmax_vals = m.maximum_uptake_flux.strip().split()
                    if len(vmax_vals) != num_subs:
                        errors.append(
                            f"Microbe {i}: maximum_uptake_flux length ({len(vmax_vals)}) "
                            f"must equal number of substrates ({num_subs})."
                        )

        if sm.enable_abiotic_kinetics and num_subs < 1:
            errors.append("Abiotic kinetics requires at least one substrate.")

        eq = self.equilibrium
        if eq.enabled:
            if not eq.component_names:
                errors.append("Equilibrium enabled but no components defined.")
            n_comp = len(eq.component_names)
            for i, row in enumerate(eq.stoichiometry):
                if len(row) != n_comp:
                    errors.append(
                        f"Stoichiometry row {i} length ({len(row)}) "
                        f"must match component count ({n_comp})."
                    )

        return errors
