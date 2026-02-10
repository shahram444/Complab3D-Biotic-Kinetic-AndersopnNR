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
        icon="💧",
        has_flow=True,
        has_transport=False,
        has_reaction=False,
        has_microbe=False,
        has_biofilm=False,
        num_substrates=0,
        num_microbes=0,
    ),
    
    TemplateType.FLOW_TRANSPORT: ProjectTemplate(
        name="Flow + Reactive Transport",
        description="Flow simulation with substrate transport.\n"
                    "Advection-diffusion of chemical species.\n"
                    "No biological reactions.",
        template_type=TemplateType.FLOW_TRANSPORT,
        icon="🌊",
        has_flow=True,
        has_transport=True,
        has_reaction=False,
        has_microbe=False,
        has_biofilm=False,
        num_substrates=1,
        num_microbes=0,
    ),
    
    TemplateType.FLOW_TRANSPORT_REACTION: ProjectTemplate(
        name="Flow + Transport + Custom Reactions",
        description="Flow and transport with user-defined reactions.\n"
                    "Define custom kinetic expressions.\n"
                    "No microbial populations.",
        template_type=TemplateType.FLOW_TRANSPORT_REACTION,
        icon="⚗️",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=False,
        has_biofilm=False,
        has_custom_kinetics=True,
        num_substrates=1,
        num_microbes=0,
    ),
    
    TemplateType.FLOW_TRANSPORT_MICROBE: ProjectTemplate(
        name="Flow + Transport + Microbes",
        description="Flow and transport with microbial populations.\n"
                    "Monod kinetics for substrate uptake.\n"
                    "Planktonic (suspended) microbes.",
        template_type=TemplateType.FLOW_TRANSPORT_MICROBE,
        icon="🦠",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=False,
        num_substrates=1,
        num_microbes=1,
        solver_type="LBM",
    ),
    
    TemplateType.FLOW_TRANSPORT_REACTION_MICROBE: ProjectTemplate(
        name="Flow + Transport + Reactions + Microbes",
        description="Full simulation with custom reactions and microbes.\n"
                    "User-defined kinetics with microbial populations.\n"
                    "Both planktonic and attached cells.",
        template_type=TemplateType.FLOW_TRANSPORT_REACTION_MICROBE,
        icon="🧬",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=False,
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
        icon="🧫",
        has_flow=True,
        has_transport=True,
        has_reaction=True,
        has_microbe=True,
        has_biofilm=True,
        num_substrates=1,
        num_microbes=1,
        solver_type="CA",
    ),
}


def get_template(template_type: TemplateType) -> ProjectTemplate:
    """Get template by type"""
    return TEMPLATES.get(template_type)


def get_all_templates() -> List[ProjectTemplate]:
    """Get all available templates"""
    return list(TEMPLATES.values())


def apply_template(project, template_type: TemplateType):
    """
    Apply template settings to a project.
    
    Args:
        project: CompLaBProject instance
        template_type: Template to apply
    """
    from .project import (
        Substrate, Microbe, DiffusionCoefficients, 
        BoundaryCondition, BoundaryType, SolverType
    )
    
    template = get_template(template_type)
    if not template:
        return
    
    # Clear existing species
    project.substrates = []
    project.microbes = []
    
    # === FLOW ONLY ===
    if template_type == TemplateType.FLOW_ONLY:
        # Just flow - set Peclet > 0, no substrates/microbes
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        project.iterations.ns_max_iT1 = 50000
        project.iterations.ade_max_iT = 0  # No ADE
        
    # === FLOW + TRANSPORT ===
    elif template_type == TemplateType.FLOW_TRANSPORT:
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        
        # Add one substrate
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
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        
        # Add substrate with reaction
        project.substrates.append(Substrate(
            name="substrate_A",
            diffusion_coefficients=DiffusionCoefficients(1e-9, 8e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        
        # Note: Custom kinetics will be defined in defineKinetics.hh
        project.iterations.ade_max_iT = 100000
        
    # === FLOW + TRANSPORT + MICROBE ===
    elif template_type == TemplateType.FLOW_TRANSPORT_MICROBE:
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        
        # Add substrate (electron donor)
        project.substrates.append(Substrate(
            name="glucose",
            diffusion_coefficients=DiffusionCoefficients(6e-10, 5e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        
        # Add planktonic microbe
        project.microbes.append(Microbe(
            name="bacteria",
            solver_type=SolverType.LATTICE_BOLTZMANN,
            material_number=3,
            initial_densities=[1.0],
            half_saturation_constants=[0.1],
            maximum_uptake_flux=[0.2, 5.0],
            decay_coefficient=1e-6,
        ))
        
        project.iterations.ade_max_iT = 100000
        
    # === FLOW + TRANSPORT + REACTION + MICROBE ===
    elif template_type == TemplateType.FLOW_TRANSPORT_REACTION_MICROBE:
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        
        # Add substrate
        project.substrates.append(Substrate(
            name="glucose",
            diffusion_coefficients=DiffusionCoefficients(6e-10, 5e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        
        # Add microbe with CA solver
        project.microbes.append(Microbe(
            name="bacteria",
            solver_type=SolverType.CELLULAR_AUTOMATA,
            material_number=3,
            initial_densities=[10.0],
            half_saturation_constants=[0.1],
            maximum_uptake_flux=[0.2, 5.0],
            decay_coefficient=1e-6,
        ))
        
        project.microbiology.maximum_biomass_density = 80.0
        project.microbiology.thrd_biofilm_fraction = 0.1
        project.iterations.ade_max_iT = 100000
        
    # === FLOW + TRANSPORT + BIOFILM ===
    elif template_type == TemplateType.FLOW_TRANSPORT_BIOFILM:
        project.fluid.peclet = 1.0
        project.fluid.delta_p = 0.001
        
        # Add substrate (electron donor)
        project.substrates.append(Substrate(
            name="glucose",
            diffusion_coefficients=DiffusionCoefficients(6e-10, 5e-10),
            initial_concentration=0.0,
            left_boundary=BoundaryCondition(BoundaryType.DIRICHLET, 1.0),
            right_boundary=BoundaryCondition(BoundaryType.NEUMANN, 0.0),
        ))
        
        # Add biofilm-forming microbe
        project.microbes.append(Microbe(
            name="biofilm_bacteria",
            solver_type=SolverType.CELLULAR_AUTOMATA,
            material_number=3,
            initial_densities=[10.0],
            half_saturation_constants=[0.1],
            maximum_uptake_flux=[0.2, 5.0],
            decay_coefficient=1e-6,
            viscosity_ratio_in_biofilm=10.0,  # Increased viscosity in biofilm
        ))
        
        # Biofilm settings
        project.microbiology.maximum_biomass_density = 80.0
        project.microbiology.thrd_biofilm_fraction = 0.1
        project.microbiology.ca_method = "fraction"
        
        project.iterations.ade_max_iT = 100000
        project.iterations.ns_update_interval = 100  # Update flow as biofilm grows


def get_template_summary(template_type: TemplateType) -> str:
    """Get a summary of what the template includes"""
    template = get_template(template_type)
    if not template:
        return ""
    
    features = []
    if template.has_flow:
        features.append("✓ Navier-Stokes flow")
    if template.has_transport:
        features.append(f"✓ Substrate transport ({template.num_substrates} species)")
    if template.has_reaction:
        features.append("✓ Chemical reactions")
    if template.has_custom_kinetics:
        features.append("✓ Custom kinetics (defineKinetics.hh)")
    if template.has_microbe:
        features.append(f"✓ Microbial populations ({template.num_microbes} species)")
    if template.has_biofilm:
        features.append("✓ Biofilm formation (CA solver)")
    
    return "\n".join(features)
