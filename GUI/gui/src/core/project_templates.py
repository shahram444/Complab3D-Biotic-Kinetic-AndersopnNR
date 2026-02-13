"""
Project Templates - Predefined simulation setups
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass


class TemplateType(Enum):
    """Available project templates"""
    FLOW_ONLY = "flow_only"
    FLOW_TRANSPORT = "flow_transport"
    FLOW_TRANSPORT_REACTION = "flow_transport_reaction"
    FLOW_TRANSPORT_MICROBE = "flow_transport_microbe"
    FLOW_TRANSPORT_REACTION_MICROBE = "flow_transport_reaction_microbe"
    FLOW_TRANSPORT_BIOFILM = "flow_transport_biofilm"
    ABIOTIC_FIRST_ORDER = "abiotic_first_order"
    ABIOTIC_BIMOLECULAR = "abiotic_bimolecular"
    ABIOTIC_DECAY_CHAIN = "abiotic_decay_chain"
    ABIOTIC_EQUILIBRIUM = "abiotic_equilibrium"
    PLANKTONIC_EQUILIBRIUM = "planktonic_equilibrium"
    BIOFILM_EQUILIBRIUM = "biofilm_equilibrium"
    FULL_COUPLED = "full_coupled"


@dataclass
class ProjectTemplate:
    """Project template definition"""
    name: str
    description: str
    template_type: TemplateType
    icon: str

    # Feature flags
    has_flow: bool = True
    has_transport: bool = False
    has_reaction: bool = False
    has_microbe: bool = False
    has_biofilm: bool = False
    has_custom_kinetics: bool = False
    has_equilibrium: bool = False

    # Default settings
    num_substrates: int = 0
    num_microbes: int = 0
    solver_type: str = "CA"  # CA, LBM, FD


# Define all templates
TEMPLATES: Dict[TemplateType, ProjectTemplate] = {

    TemplateType.FLOW_ONLY: ProjectTemplate(
        name="Flow Only",
        description="Navier-Stokes flow simulation only.\n"
                    "Computes velocity field in porous media.\n"
                    "No reactive transport or biology.",
        template_type=TemplateType.FLOW_ONLY,
        icon="flow",
        has_flow=True,
        num_substrates=0,
        num_microbes=0,
    ),

    TemplateType.FLOW_TRANSPORT: ProjectTemplate(
        name="Flow + Reactive Transport",
        description="Flow simulation with substrate transport.\n"
                    "Advection-diffusion of chemical species.\n"
                    "No biological reactions.",
        template_type=TemplateType.FLOW_TRANSPORT,
        icon="transport",
        has_flow=True,
        has_transport=True,
        num_substrates=1,
        num_microbes=0,
    ),

    TemplateType.FLOW_TRANSPORT_REACTION: ProjectTemplate(
        name="Flow + Transport + Custom Reactions",
        description="Flow and transport with user-defined reactions.\n"
                    "Define custom kinetic expressions.\n"
                    "No microbial populations.",
        template_type=TemplateType.FLOW_TRANSPORT_REACTION,
        icon="reaction",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_custom_kinetics=True,
        num_substrates=1,
        num_microbes=0,
    ),

    TemplateType.FLOW_TRANSPORT_MICROBE: ProjectTemplate(
        name="Planktonic Bacteria (LBM)",
        description="Flow and transport with planktonic bacteria.\n"
                    "Monod kinetics for substrate uptake.\n"
                    "Suspended microbes solved via LBM.",
        template_type=TemplateType.FLOW_TRANSPORT_MICROBE,
        icon="planktonic",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        num_substrates=1,
        num_microbes=1,
        solver_type="LBM",
    ),

    TemplateType.FLOW_TRANSPORT_REACTION_MICROBE: ProjectTemplate(
        name="Sessile Biofilm (CA)",
        description="Biotic simulation with CA sessile biofilm.\n"
                    "Monod kinetics + biomass spreading.\n"
                    "Cellular Automata for biofilm growth.",
        template_type=TemplateType.FLOW_TRANSPORT_REACTION_MICROBE,
        icon="biofilm",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=True,
        has_custom_kinetics=True,
        num_substrates=1,
        num_microbes=1,
        solver_type="CA",
    ),

    TemplateType.FLOW_TRANSPORT_BIOFILM: ProjectTemplate(
        name="Flow + Transport + Biofilm",
        description="Complete biofilm simulation.\n"
                    "Cellular Automata for biofilm growth.\n"
                    "Includes biomass spreading and detachment.",
        template_type=TemplateType.FLOW_TRANSPORT_BIOFILM,
        icon="biofilm",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=True,
        num_substrates=1,
        num_microbes=1,
        solver_type="CA",
    ),

    TemplateType.ABIOTIC_FIRST_ORDER: ProjectTemplate(
        name="Abiotic - First Order Decay",
        description="Transport with first-order abiotic decay kinetics.\n"
                    "No microbial populations.\n"
                    "Reactant -> Product with decay constant.",
        template_type=TemplateType.ABIOTIC_FIRST_ORDER,
        icon="reaction",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        num_substrates=2,
        num_microbes=0,
    ),

    TemplateType.ABIOTIC_BIMOLECULAR: ProjectTemplate(
        name="Abiotic - Bimolecular Reaction",
        description="Transport with bimolecular abiotic kinetics.\n"
                    "A + B -> C reaction.\n"
                    "Second-order reaction kinetics.",
        template_type=TemplateType.ABIOTIC_BIMOLECULAR,
        icon="reaction",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        num_substrates=3,
        num_microbes=0,
    ),

    TemplateType.ABIOTIC_DECAY_CHAIN: ProjectTemplate(
        name="Abiotic - Sequential Decay Chain",
        description="Sequential decay A -> B -> C (Bateman equations).\n"
                    "Three-species decay chain.\n"
                    "Closed-system (Neumann boundaries).",
        template_type=TemplateType.ABIOTIC_DECAY_CHAIN,
        icon="reaction",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_custom_kinetics=True,
        num_substrates=3,
        num_microbes=0,
    ),

    TemplateType.ABIOTIC_EQUILIBRIUM: ProjectTemplate(
        name="Abiotic + Equilibrium Solver",
        description="Abiotic kinetics coupled with equilibrium chemistry.\n"
                    "Carbonate system (CO2/HCO3/CO3/H+).\n"
                    "Anderson acceleration NR equilibrium solver.",
        template_type=TemplateType.ABIOTIC_EQUILIBRIUM,
        icon="equilibrium",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_equilibrium=True,
        num_substrates=5,
        num_microbes=0,
    ),

    TemplateType.PLANKTONIC_EQUILIBRIUM: ProjectTemplate(
        name="Planktonic + Equilibrium",
        description="Planktonic bacteria with LBM solver\n"
                    "coupled to equilibrium chemistry.\n"
                    "Carbonate system + Monod kinetics.",
        template_type=TemplateType.PLANKTONIC_EQUILIBRIUM,
        icon="planktonic",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_equilibrium=True,
        num_substrates=5,
        num_microbes=1,
        solver_type="LBM",
    ),

    TemplateType.BIOFILM_EQUILIBRIUM: ProjectTemplate(
        name="Biofilm + Equilibrium Chemistry",
        description="CA biofilm with Monod kinetics coupled\n"
                    "to equilibrium chemistry solver.\n"
                    "Carbonate system + biomass growth.",
        template_type=TemplateType.BIOFILM_EQUILIBRIUM,
        icon="biofilm",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=True,
        has_equilibrium=True,
        num_substrates=5,
        num_microbes=1,
        solver_type="CA",
    ),

    TemplateType.FULL_COUPLED: ProjectTemplate(
        name="Full Coupled System",
        description="Biofilm (CA) + planktonic (LBM)\n"
                    "with Monod kinetics + equilibrium.\n"
                    "Complete multi-physics simulation.",
        template_type=TemplateType.FULL_COUPLED,
        icon="coupled",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=True,
        has_equilibrium=True,
        num_substrates=5,
        num_microbes=2,
        solver_type="CA",
    ),
}


def get_template(template_type: TemplateType) -> ProjectTemplate:
    """Get template by type"""
    return TEMPLATES.get(template_type)


def get_all_templates() -> List[ProjectTemplate]:
    """Get all available templates"""
    return list(TEMPLATES.values())


def _default_substrates_5(project):
    """Standard 5-substrate carbonate system (DOC, CO2, HCO3, CO3, H+)."""
    from .project import (
        Substrate, DiffusionCoefficients, BoundaryCondition, BoundaryType,
    )
    project.substrates = [
        Substrate(
            name="DOC",
            diffusion_coefficients=DiffusionCoefficients(1e-9, 2e-10),
            initial_concentration=0.1,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 0.1),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ),
        Substrate(
            name="CO2",
            diffusion_coefficients=DiffusionCoefficients(1.9e-9, 3.8e-10),
            initial_concentration=1e-5,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1e-5),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ),
        Substrate(
            name="HCO3",
            diffusion_coefficients=DiffusionCoefficients(1.2e-9, 2.4e-10),
            initial_concentration=2e-3,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 2e-3),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ),
        Substrate(
            name="CO3",
            diffusion_coefficients=DiffusionCoefficients(0.9e-9, 1.8e-10),
            initial_concentration=1e-5,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1e-5),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ),
        Substrate(
            name="Hplus",
            diffusion_coefficients=DiffusionCoefficients(9.3e-9, 1.86e-9),
            initial_concentration=1e-7,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1e-7),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ),
    ]


def _default_equilibrium(project):
    """Standard carbonate equilibrium settings."""
    from .project import EquilibriumSettings
    project.equilibrium = EquilibriumSettings(
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


def apply_template(project, template_type: TemplateType):
    """Apply template settings to a project."""
    from .project import (
        Substrate, Microbe, DiffusionCoefficients,
        BoundaryCondition, BoundaryType, SolverType,
        SimulationMode, EquilibriumSettings,
    )

    template = get_template(template_type)
    if not template:
        return

    # Clear existing species
    project.substrates = []
    project.microbes = []

    # === FLOW ONLY ===
    if template_type == TemplateType.FLOW_ONLY:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=False,
        )
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.iterations.ns_max_iT1 = 50000
        project.iterations.ade_max_iT = 0

    # === FLOW + TRANSPORT ===
    elif template_type == TemplateType.FLOW_TRANSPORT:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=False,
        )
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.substrates.append(Substrate(
            name="tracer",
            diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.iterations.ade_max_iT = 100000

    # === FLOW + TRANSPORT + REACTION ===
    elif template_type == TemplateType.FLOW_TRANSPORT_REACTION:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=True,
        )
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.substrates.append(Substrate(
            name="substrate_A",
            diffusion_coefficients=DiffusionCoefficients(1e-9, 8e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.iterations.ade_max_iT = 100000

    # === PLANKTONIC (LBM) ===
    elif template_type == TemplateType.FLOW_TRANSPORT_MICROBE:
        project.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True,
        )
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.substrates.append(Substrate(
            name="glucose",
            diffusion_coefficients=DiffusionCoefficients(6e-10, 6e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.microbes.append(Microbe(
            name="Planktonic_Heterotroph",
            solver_type=SolverType.LATTICE_BOLTZMANN,
            material_number=3,
            initial_densities=[10.0],
            half_saturation_constants=[1e-5],
            maximum_uptake_flux=[2.5],
            decay_coefficient=1e-9,
            viscosity_ratio_in_biofilm=1.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 10.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.microbiology.ca_method = "none"
        project.iterations.ade_max_iT = 100000

    # === SESSILE BIOFILM (CA) ===
    elif template_type == TemplateType.FLOW_TRANSPORT_REACTION_MICROBE:
        project.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True,
        )
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.substrates.append(Substrate(
            name="glucose",
            diffusion_coefficients=DiffusionCoefficients(6e-10, 5e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.microbes.append(Microbe(
            name="Sessile_Heterotroph",
            solver_type=SolverType.CELLULAR_AUTOMATA,
            material_number=3,
            initial_densities=[99.0, 99.0],
            half_saturation_constants=[1e-5],
            maximum_uptake_flux=[2.5],
            decay_coefficient=1e-9,
            viscosity_ratio_in_biofilm=10.0,
        ))
        project.domain.pore_material = 2
        project.domain.solid_material = 0
        project.domain.bounce_back_material = 1
        project.microbiology.maximum_biomass_density = 100.0
        project.microbiology.thrd_biofilm_fraction = 0.1
        project.microbiology.ca_method = "half"
        project.iterations.ade_max_iT = 100000
        project.iterations.ns_update_interval = 100

    # === FLOW + TRANSPORT + BIOFILM ===
    elif template_type == TemplateType.FLOW_TRANSPORT_BIOFILM:
        project.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True,
        )
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.substrates.append(Substrate(
            name="glucose",
            diffusion_coefficients=DiffusionCoefficients(6e-10, 5e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.microbes.append(Microbe(
            name="biofilm_bacteria",
            solver_type=SolverType.CELLULAR_AUTOMATA,
            material_number=3,
            initial_densities=[10.0],
            half_saturation_constants=[0.1],
            maximum_uptake_flux=[0.2, 5.0],
            decay_coefficient=1e-6,
            viscosity_ratio_in_biofilm=10.0,
        ))
        project.microbiology.maximum_biomass_density = 80.0
        project.microbiology.thrd_biofilm_fraction = 0.1
        project.microbiology.ca_method = "fraction"
        project.iterations.ade_max_iT = 100000
        project.iterations.ns_update_interval = 100

    # === ABIOTIC - FIRST ORDER DECAY ===
    elif template_type == TemplateType.ABIOTIC_FIRST_ORDER:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=True,
        )
        project.substrates = [
            Substrate(
                name="Reactant",
                diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
                initial_concentration=1.0,
                left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
            Substrate(
                name="Product",
                diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
                initial_concentration=0.0,
                left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 0.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
        ]
        project.iterations.ade_max_iT = 100000

    # === ABIOTIC - BIMOLECULAR ===
    elif template_type == TemplateType.ABIOTIC_BIMOLECULAR:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=True,
        )
        project.substrates = [
            Substrate(
                name="A",
                diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
                initial_concentration=1.0,
                left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
            Substrate(
                name="B",
                diffusion_coefficients=DiffusionCoefficients(1.2e-9, 1.2e-9),
                initial_concentration=0.5,
                left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 0.5),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
            Substrate(
                name="C",
                diffusion_coefficients=DiffusionCoefficients(0.8e-9, 0.8e-9),
                initial_concentration=0.0,
                left_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
        ]
        project.iterations.ade_max_iT = 100000

    # === ABIOTIC - DECAY CHAIN ===
    elif template_type == TemplateType.ABIOTIC_DECAY_CHAIN:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=True,
        )
        project.substrates = [
            Substrate(
                name="Parent_A",
                diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
                initial_concentration=1.0,
                left_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
            Substrate(
                name="Daughter_B",
                diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
                initial_concentration=0.0,
                left_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
            Substrate(
                name="GrandDaughter_C",
                diffusion_coefficients=DiffusionCoefficients(1e-9, 1e-9),
                initial_concentration=0.0,
                left_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
        ]
        project.domain.nx = 20
        project.domain.ny = 10
        project.domain.nz = 10
        project.iterations.ade_max_iT = 50000
        project.io.save_vtk_interval = 10000

    # === ABIOTIC + EQUILIBRIUM ===
    elif template_type == TemplateType.ABIOTIC_EQUILIBRIUM:
        project.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False, enable_abiotic_kinetics=True,
        )
        _default_substrates_5(project)
        # No biofilm diffusion for abiotic
        for s in project.substrates:
            s.diffusion_coefficients.in_biofilm = s.diffusion_coefficients.in_pore
        _default_equilibrium(project)
        project.iterations.ade_max_iT = 100000

    # === PLANKTONIC + EQUILIBRIUM ===
    elif template_type == TemplateType.PLANKTONIC_EQUILIBRIUM:
        project.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True,
        )
        _default_substrates_5(project)
        for s in project.substrates:
            s.diffusion_coefficients.in_biofilm = s.diffusion_coefficients.in_pore
        _default_equilibrium(project)
        project.microbes.append(Microbe(
            name="Planktonic_Heterotroph",
            solver_type=SolverType.LATTICE_BOLTZMANN,
            material_number=3,
            initial_densities=[10.0],
            half_saturation_constants=[1e-5, 0.0, 0.0, 0.0, 0.0],
            maximum_uptake_flux=[2.5],
            decay_coefficient=1e-9,
            viscosity_ratio_in_biofilm=1.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 10.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        project.microbiology.ca_method = "none"
        project.iterations.ade_max_iT = 100000

    # === BIOFILM + EQUILIBRIUM ===
    elif template_type == TemplateType.BIOFILM_EQUILIBRIUM:
        project.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True,
        )
        _default_substrates_5(project)
        _default_equilibrium(project)
        project.microbes.append(Microbe(
            name="Sessile_Heterotroph",
            solver_type=SolverType.CELLULAR_AUTOMATA,
            material_number=3,
            initial_densities=[99.0, 99.0],
            half_saturation_constants=[1e-5, 0.0, 0.0, 0.0, 0.0],
            maximum_uptake_flux=[2.5],
            decay_coefficient=1e-9,
            viscosity_ratio_in_biofilm=10.0,
        ))
        project.microbiology.maximum_biomass_density = 100.0
        project.microbiology.thrd_biofilm_fraction = 0.1
        project.microbiology.ca_method = "half"
        project.iterations.ade_max_iT = 100000
        project.iterations.ns_update_interval = 100

    # === FULL COUPLED ===
    elif template_type == TemplateType.FULL_COUPLED:
        project.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True,
            enable_abiotic_kinetics=False,
        )
        _default_substrates_5(project)
        _default_equilibrium(project)
        project.microbes = [
            Microbe(
                name="Sessile_Heterotroph",
                solver_type=SolverType.CELLULAR_AUTOMATA,
                material_number=3,
                initial_densities=[99.0, 99.0],
                half_saturation_constants=[1e-5, 0.0, 0.0, 0.0, 0.0],
                maximum_uptake_flux=[2.5],
                decay_coefficient=1e-9,
                viscosity_ratio_in_biofilm=10.0,
            ),
            Microbe(
                name="Planktonic_Heterotroph",
                solver_type=SolverType.LATTICE_BOLTZMANN,
                material_number=4,
                initial_densities=[5.0],
                half_saturation_constants=[1e-5, 0.0, 0.0, 0.0, 0.0],
                maximum_uptake_flux=[1.5],
                decay_coefficient=1e-9,
                viscosity_ratio_in_biofilm=1.0,
                left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 5.0),
                right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
            ),
        ]
        project.microbiology.maximum_biomass_density = 100.0
        project.microbiology.thrd_biofilm_fraction = 0.1
        project.microbiology.ca_method = "half"
        project.iterations.ade_max_iT = 100000
        project.iterations.ns_update_interval = 100


def get_template_summary(template_type: TemplateType) -> str:
    """Get a summary of what the template includes"""
    template = get_template(template_type)
    if not template:
        return ""

    features = []
    if template.has_flow:
        features.append("Navier-Stokes flow")
    if template.has_transport:
        features.append(f"Substrate transport ({template.num_substrates} species)")
    if template.has_reaction:
        features.append("Chemical reactions")
    if template.has_custom_kinetics:
        features.append("Custom kinetics (defineKinetics.hh)")
    if template.has_microbe:
        features.append(f"Microbial populations ({template.num_microbes} species)")
    if template.has_biofilm:
        features.append("Biofilm formation (CA solver)")
    if template.has_equilibrium:
        features.append("Equilibrium chemistry solver")

    return "\n".join(features)
