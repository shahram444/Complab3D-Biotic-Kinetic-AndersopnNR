"""Predefined project templates for common simulation setups.

Each template returns a fully configured CompLaBProject with
sensible defaults for the given simulation type.
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


# ── Templates ───────────────────────────────────────────────────────────

@_register("flow_only", "Flow Only",
           "Navier-Stokes flow simulation only (no substrates defined).")
def _flow_only():
    p = CompLaBProject(name="Flow Only")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False)
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.iteration = IterationSettings(
        ns_max_iT1=100000, ns_max_iT2=100000,
        ns_converge_iT1=1e-8, ns_converge_iT2=1e-6,
        ade_max_iT=0)  # No ADE (no substrates)
    # No substrates, no microbes → solver runs NS then exits (pure flow mode)
    return p


@_register("diffusion_only", "Diffusion Only",
           "Pure diffusion transport with Pe=0 (no advection/flow).")
def _diffusion_only():
    p = CompLaBProject(name="Diffusion Only")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False,
        enable_validation_diagnostics=True)
    p.path_settings.output_path = "output_diffusion"
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


@_register("transport_only", "Transport (Flow + Diffusion)",
           "Flow + advection-diffusion transport, no reactions.")
def _transport_only():
    p = CompLaBProject(name="Transport")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False)
    p.fluid = FluidSettings(
        delta_P=2e-3, peclet=1.0, tau=0.8, track_performance=False)
    p.substrates = [
        Substrate(name="Tracer", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
    ]
    return p


@_register("abiotic_first_order", "Abiotic - First Order Decay",
           "Transport with first-order abiotic decay kinetics.")
def _abiotic_first_order():
    p = CompLaBProject(name="Abiotic First Order")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.substrates = [
        Substrate(name="Reactant", initial_concentration=1.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
        Substrate(name="Product", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
    ]
    return p


@_register("abiotic_bimolecular", "Abiotic - Bimolecular Reaction",
           "Transport with bimolecular abiotic kinetics (A + B -> C).")
def _abiotic_bimolecular():
    p = CompLaBProject(name="Abiotic Bimolecular")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.substrates = [
        Substrate(name="A", initial_concentration=1.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
        Substrate(name="B", initial_concentration=0.5,
                  diffusion_in_pore=1.2e-9, diffusion_in_biofilm=1.2e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=0.5, right_boundary_condition=0.0),
        Substrate(name="C", initial_concentration=0.0,
                  diffusion_in_pore=0.8e-9, diffusion_in_biofilm=0.8e-9,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
    ]
    return p


@_register("abiotic_reversible", "Abiotic - Reversible Reaction",
           "Transport with reversible abiotic kinetics (A <-> B).")
def _abiotic_reversible():
    p = CompLaBProject(name="Abiotic Reversible")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.substrates = [
        Substrate(name="A", initial_concentration=1.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
        Substrate(name="B", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
    ]
    return p


@_register("biofilm_sessile", "Biofilm - Sessile (CA)",
           "Simple biofilm: 1 substrate (DOC), 1 microbe (CA). "
           "Matches kinetics/05_biofilm_single_substrate/.")
def _biofilm_sessile():
    p = CompLaBProject(name="Biofilm Sessile")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True)
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


@_register("planktonic", "Planktonic Bacteria (LBM)",
           "Simple planktonic: 1 substrate (DOC), 1 microbe (LBM). "
           "Matches kinetics/06_planktonic_single_substrate/.")
def _planktonic():
    p = CompLaBProject(name="Planktonic")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True)
    p.path_settings.output_path = "output_planktonic"
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


@_register("biofilm_equilibrium", "Biofilm + Equilibrium Chemistry",
           "CA biofilm with Monod kinetics coupled to equilibrium solver.")
def _biofilm_equilibrium():
    p = _biofilm_sessile()
    p.name = "Biofilm + Equilibrium"
    p.equilibrium = EquilibriumSettings(
        enabled=True,
        component_names=["HCO3-", "H+"],
        stoichiometry=[
            [0.0, 0.0],    # DOC
            [1.0, 1.0],    # CO2 -> H2CO3
            [1.0, 0.0],    # HCO3-
            [1.0, -1.0],   # CO3--
            [0.0, 1.0],    # H+
        ],
        log_k=[0.0, 6.35, 0.0, -10.33, 0.0],
    )
    return p


@_register("abiotic_decay_chain", "Abiotic - Sequential Decay Chain",
           "Sequential decay A -> B -> C (Bateman equations).")
def _abiotic_decay_chain():
    p = CompLaBProject(name="Abiotic Decay Chain")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.domain = DomainSettings(
        nx=20, ny=10, nz=10, dx=1.0,
        geometry_filename="geometry_open.dat")
    p.iteration.ade_max_iT = 50000
    p.substrates = [
        Substrate(name="Parent_A", initial_concentration=1.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
        Substrate(name="Daughter_B", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
        Substrate(name="GrandDaughter_C", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-9,
                  left_boundary_type="Neumann", right_boundary_type="Neumann",
                  left_boundary_condition=0.0, right_boundary_condition=0.0),
    ]
    p.io_settings.save_vtk_interval = 10000
    return p


@_register("abiotic_equilibrium", "Abiotic + Equilibrium Solver",
           "Abiotic kinetics coupled with equilibrium chemistry solver.")
def _abiotic_equilibrium():
    p = CompLaBProject(name="Abiotic + Equilibrium")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=True)
    p.substrates = _default_substrates_5()
    # No biofilm diffusion needed for abiotic
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


@_register("planktonic_equilibrium", "Planktonic + Equilibrium",
           "Planktonic bacteria with LBM solver coupled to equilibrium chemistry.")
def _planktonic_equilibrium():
    p = _planktonic()
    p.name = "Planktonic + Equilibrium"
    p.equilibrium = EquilibriumSettings(
        enabled=True,
        component_names=["HCO3-", "H+"],
        stoichiometry=[
            [0.0, 0.0], [1.0, 1.0], [1.0, 0.0], [1.0, -1.0], [0.0, 1.0],
        ],
        log_k=[0.0, 6.35, 0.0, -10.33, 0.0],
    )
    return p


@_register("full_coupled", "Full Coupled System",
           "Biofilm (CA) + planktonic (LBM) with Monod kinetics + equilibrium.")
def _full_coupled():
    p = CompLaBProject(name="Full Coupled")
    p.simulation_mode = SimulationMode(
        biotic_mode=True, enable_kinetics=True,
        enable_abiotic_kinetics=False)
    p.substrates = _default_substrates_5()
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
                decay_coefficient=1e-9,
                viscosity_ratio_in_biofilm=10.0,
                half_saturation_constants="1e-5 0.0 0.0 0.0 0.0",
                maximum_uptake_flux="2.5 0.0 0.0 0.0 0.0",
            ),
            Microbe(
                name="Planktonic_Heterotroph", solver_type="LBM",
                reaction_type="kinetics",
                material_number="",
                initial_densities="5.0",
                decay_coefficient=1e-9,
                viscosity_ratio_in_biofilm=1.0,
                half_saturation_constants="1e-5 0.0 0.0 0.0 0.0",
                maximum_uptake_flux="1.5 0.0 0.0 0.0 0.0",
                left_boundary_type="Dirichlet",
                left_boundary_condition=5.0,
            ),
        ],
    )
    p.equilibrium = EquilibriumSettings(
        enabled=True,
        component_names=["HCO3-", "H+"],
        stoichiometry=[
            [0.0, 0.0], [1.0, 1.0], [1.0, 0.0], [1.0, -1.0], [0.0, 1.0],
        ],
        log_k=[0.0, 6.35, 0.0, -10.33, 0.0],
    )
    return p


@_register("scratch", "Start from Scratch",
           "Blank project with empty kinetics templates. "
           "Configure everything yourself from the ground up.")
def _scratch():
    p = CompLaBProject(name="Custom Project")
    p.simulation_mode = SimulationMode(
        biotic_mode=False, enable_kinetics=False,
        enable_abiotic_kinetics=False)
    p.substrates = [
        Substrate(name="substrate_0", initial_concentration=0.0,
                  diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                  left_boundary_type="Dirichlet", right_boundary_type="Neumann",
                  left_boundary_condition=1.0, right_boundary_condition=0.0),
    ]
    return p
