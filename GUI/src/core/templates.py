"""Predefined project templates for common simulation setups.

Each template returns a fully configured CompLaBProject with
sensible defaults for the given simulation type.

Templates (9 scenarios, each demonstrating one capability):
  1. Flow Only          - Pure Navier-Stokes (no chemistry)
  2. Diffusion Only     - Pure diffusion (Pe=0, no flow/reactions)
  3. Tracer Transport   - Flow + advection-diffusion (no reactions)
  4. Abiotic Reaction   - First-order decay A -> Product
  5. Abiotic Equilibrium- Carbonate speciation (no kinetic reactions)
  6. Biotic Sessile     - Single sessile biofilm (CA solver)
  7. Biotic Planktonic  - Single planktonic bacteria (LBM solver)
  8. Sessile+Planktonic - Both sessile and planktonic together
  9. Coupled Biotic-Abiotic - Biofilm + abiotic reaction simultaneously
"""

from .project import (
    CompLaBProject, SimulationMode, Substrate, Microbe,
    MicrobiologySettings, EquilibriumSettings, DomainSettings,
    FluidSettings, IterationSettings, IOSettings, PathSettings,
)
from .kinetics_templates import get_kinetics_info

# Template registry: {key: (display_name, description, factory_function)}
TEMPLATES = {}


def _register(key, name, desc):
    def decorator(fn):
        TEMPLATES[key] = (name, desc, fn)
        return fn
    return decorator


def get_template_list():
    """Return [(key, name, description), ...]."""
    return [(k, v[0], v[1]) for k, v in TEMPLATES.items()]


def create_from_template(key: str) -> CompLaBProject:
    """Create a project from template, including matching kinetics .hh code."""
    if key not in TEMPLATES:
        return CompLaBProject()
    project = TEMPLATES[key][2]()
    # Attach matching kinetics source code
    project.template_key = key
    info = get_kinetics_info(key)
    if info:
        project.kinetics_source = info.biotic_hh or ""
        project.abiotic_kinetics_source = info.abiotic_hh or ""
    return project


def _default_substrates_5():
    """Standard 5-substrate carbonate system (DOC, CO2, HCO3, CO3, H+)."""
    return [
        Substrate(name="DOC", initial_concentration=0.1,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.1, right_boundary_condition=0.0),
        Substrate(name="CO2", initial_concentration=1e-5,
                  diffusion_in_pore=1.9e-9, diffusion_in_biofilm=3.8e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1e-5, right_boundary_condition=0.0),
        Substrate(name="HCO3", initial_concentration=2e-3,
                  diffusion_in_pore=1.2e-9, diffusion_in_biofilm=2.4e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=2e-3, right_boundary_condition=0.0),
        Substrate(name="CO3", initial_concentration=1e-5,
                  diffusion_in_pore=0.9e-9, diffusion_in_biofilm=1.8e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1e-5, right_boundary_condition=0.0),
        Substrate(name="Hplus", initial_concentration=1e-7,
                  diffusion_in_pore=9.3e-9, diffusion_in_biofilm=1.86e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1e-7, right_boundary_condition=0.0),
    ]


# ── 1. Flow Only ────────────────────────────────────────────────────────

@_register("flow_only", "Flow Only",
           "Pure Navier-Stokes flow (no substrates, no reactions). "
           "Validates Poiseuille parabolic velocity profile.")
def _flow_only():
    p = CompLaBProject(name="Flow Only")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False)
    p.domain = DomainSettings(
        nx=30, ny=15, nz=15, dx=1.0, unit="um",
        characteristic_length=15.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.iteration = IterationSettings(
        ns_max_iT1=100000, ns_max_iT2=100000,
        ns_converge_iT1=1e-8, ns_converge_iT2=1e-6,
        ade_max_iT=0)
    return p


# ── 2. Diffusion Only ───────────────────────────────────────────────────

@_register("diffusion_only", "Diffusion Only",
           "Pure diffusion (Pe=0, no flow, no reactions). "
           "Validates linear steady-state concentration profile.")
def _diffusion_only():
    p = CompLaBProject(name="Diffusion Only")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False,
        enable_validation_diagnostics=True)
    p.domain = DomainSettings(
        nx=30, ny=10, nz=10, dx=1.0, unit="um",
        characteristic_length=10.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=0.0, peclet=0.0, tau=0.8, track_performance=False)
    p.iteration = IterationSettings(
        ade_max_iT=5000, ade_converge_iT=1e-10)
    p.substrates = [
        Substrate(name="Tracer", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
    ]
    p.io_settings = IOSettings(
        save_vtk_interval=1000, save_chk_interval=5000)
    return p


# ── 3. Tracer Transport ─────────────────────────────────────────────────

@_register("tracer_transport", "Tracer Transport (Flow + Diffusion)",
           "Flow + advection-diffusion of a passive tracer, no reactions. "
           "Validates tracer front propagation and steady-state uniformity.")
def _tracer_transport():
    p = CompLaBProject(name="Tracer Transport")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False)
    p.domain = DomainSettings(
        nx=40, ny=15, nz=15, dx=1.0, unit="um",
        characteristic_length=15.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="Tracer", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
    ]
    return p


# ── 4. Abiotic Reaction ─────────────────────────────────────────────────

@_register("abiotic_reaction", "Abiotic Reaction (First-Order Decay)",
           "First-order abiotic decay: A -> Product. "
           "Validates exponential decay and mass balance A+P=const.")
def _abiotic_reaction():
    p = CompLaBProject(name="Abiotic Reaction")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.domain = DomainSettings(
        nx=30, ny=10, nz=10, dx=1.0, unit="um",
        characteristic_length=10.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="Reactant", initial_concentration=1.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
        Substrate(name="Product", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
    ]
    return p


# ── 5. Abiotic Equilibrium ──────────────────────────────────────────────

@_register("abiotic_equilibrium", "Abiotic Equilibrium (Carbonate)",
           "Carbonate equilibrium speciation only (no kinetic reactions). "
           "Validates pH and carbonate ratios from log-K values.")
def _abiotic_equilibrium():
    p = CompLaBProject(name="Abiotic Equilibrium")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.domain = DomainSettings(
        nx=20, ny=10, nz=10, dx=1.0, unit="um",
        characteristic_length=10.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = _default_substrates_5()
    for s in p.substrates:
        s.diffusion_in_biofilm = s.diffusion_in_pore
    p.equilibrium = EquilibriumSettings(
        enabled=True,
        component_names=["HCO3-", "H+"],
        stoichiometry=[
            [0.0, 0.0],    # DOC (not in equilibrium)
            [1.0, 1.0],    # CO2 -> H2CO3
            [1.0, 0.0],    # HCO3-
            [1.0, -1.0],   # CO3--
            [0.0, 1.0],    # H+
        ],
        log_k=[0.0, 6.35, 0.0, -10.33, 0.0],
    )
    return p


# ── 6. Biotic Sessile ───────────────────────────────────────────────────

@_register("biotic_sessile", "Biofilm - Sessile (CA Solver)",
           "Single-species sessile biofilm with Monod kinetics. "
           "CA solver grows biofilm on solid surfaces.")
def _biotic_sessile():
    p = CompLaBProject(name="Biofilm Sessile")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True)
    p.domain = DomainSettings(
        nx=30, ny=15, nz=15, dx=1.0, unit="um",
        characteristic_length=15.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="DOC", initial_concentration=0.1,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.1, right_boundary_condition=0.0),
    ]
    p.domain.pore = "2"
    p.domain.solid = "0"
    p.domain.bounce_back = "1"
    p.microbiology = MicrobiologySettings(
        maximum_biomass_density=100.0,
        thrd_biofilm_fraction=0.1,
        ca_method="half",
        microbes=[
            Microbe(
                name="Heterotroph", solver_type="CA",
                reaction_type="kinetics",
                material_number="3 6",
                initial_densities="99.0 99.0",
                decay_coefficient=1e-7,
                viscosity_ratio_in_biofilm=10.0,
                half_saturation_constants="1e-5",
                maximum_uptake_flux="2.5",
                left_boundary_type="Neumann",
                right_boundary_type="Neumann",
            ),
        ],
    )
    return p


# ── 7. Biotic Planktonic ────────────────────────────────────────────────

@_register("biotic_planktonic", "Planktonic Bacteria (LBM Solver)",
           "Single-species planktonic bacteria with Monod kinetics. "
           "LBM solver transports bacteria as a dissolved field.")
def _biotic_planktonic():
    p = CompLaBProject(name="Planktonic")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True)
    p.domain = DomainSettings(
        nx=30, ny=15, nz=15, dx=1.0, unit="um",
        characteristic_length=15.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="DOC", initial_concentration=0.1,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.1, right_boundary_condition=0.0),
    ]
    p.microbiology = MicrobiologySettings(
        maximum_biomass_density=100.0,
        thrd_biofilm_fraction=0.1,
        ca_method="fraction",
        microbes=[
            Microbe(
                name="Planktonic_Heterotroph", solver_type="LBM",
                reaction_type="kinetics",
                material_number="",
                initial_densities="10.0",
                decay_coefficient=1e-7,
                viscosity_ratio_in_biofilm=1.0,
                half_saturation_constants="1e-5",
                maximum_uptake_flux="2.5",
                left_boundary_type="Dirichlet",
                right_boundary_type="Neumann",
                left_boundary_condition=10.0,
            ),
        ],
    )
    return p


# ── 8. Sessile + Planktonic ─────────────────────────────────────────────

@_register("biotic_sessile_planktonic", "Sessile + Planktonic (Dual Microbe)",
           "Both sessile (CA) and planktonic (LBM) bacteria competing for DOC. "
           "Demonstrates dual-solver coupling.")
def _biotic_sessile_planktonic():
    p = CompLaBProject(name="Sessile + Planktonic")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True)
    p.domain = DomainSettings(
        nx=30, ny=15, nz=15, dx=1.0, unit="um",
        characteristic_length=15.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="DOC", initial_concentration=0.1,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.1, right_boundary_condition=0.0),
    ]
    p.domain.pore = "2"
    p.domain.solid = "0"
    p.domain.bounce_back = "1"
    p.microbiology = MicrobiologySettings(
        maximum_biomass_density=100.0,
        thrd_biofilm_fraction=0.1,
        ca_method="half",
        microbes=[
            Microbe(
                name="Sessile_Heterotroph", solver_type="CA",
                reaction_type="kinetics",
                material_number="3 6",
                initial_densities="99.0 99.0",
                decay_coefficient=1e-7,
                viscosity_ratio_in_biofilm=10.0,
                half_saturation_constants="1e-5",
                maximum_uptake_flux="2.5",
                left_boundary_type="Neumann",
                right_boundary_type="Neumann",
            ),
            Microbe(
                name="Planktonic_Heterotroph", solver_type="LBM",
                reaction_type="kinetics",
                material_number="",
                initial_densities="5.0",
                decay_coefficient=1e-7,
                viscosity_ratio_in_biofilm=1.0,
                half_saturation_constants="1e-5",
                maximum_uptake_flux="1.5",
                left_boundary_type="Dirichlet",
                right_boundary_type="Neumann",
                left_boundary_condition=5.0,
            ),
        ],
    )
    return p


# ── 9. Coupled Biotic-Abiotic ───────────────────────────────────────────

@_register("coupled_biotic_abiotic",
           "Coupled Biotic-Abiotic",
           "Biofilm (CA) consumes DOC -> produces Byproduct; "
           "Byproduct decays abiotically. Both kinetics active simultaneously.")
def _coupled_biotic_abiotic():
    p = CompLaBProject(name="Coupled Biotic-Abiotic")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True,
        enable_abiotic_kinetics=True)
    p.domain = DomainSettings(
        nx=30, ny=15, nz=15, dx=1.0, unit="um",
        characteristic_length=15.0, geometry_filename="geometry.dat")
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="DOC", initial_concentration=0.1,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.1, right_boundary_condition=0.0),
        Substrate(name="Byproduct", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=5e-10,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
    ]
    p.domain.pore = "2"
    p.domain.solid = "0"
    p.domain.bounce_back = "1"
    p.microbiology = MicrobiologySettings(
        maximum_biomass_density=100.0,
        thrd_biofilm_fraction=0.1,
        ca_method="half",
        microbes=[
            Microbe(
                name="Heterotroph", solver_type="CA",
                reaction_type="kinetics",
                material_number="3 6",
                initial_densities="99.0 99.0",
                decay_coefficient=1e-7,
                viscosity_ratio_in_biofilm=10.0,
                half_saturation_constants="1e-5 0.0",
                maximum_uptake_flux="2.5 0.0",
                left_boundary_type="Neumann",
                right_boundary_type="Neumann",
            ),
        ],
    )
    return p
