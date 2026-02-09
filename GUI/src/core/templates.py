"""Predefined project templates for common simulation setups."""

from .project import (
    CompLaBProject, SimulationMode, Substrate, Microbe,
    MicrobiologySettings, EquilibriumSettings,
)


TEMPLATES = {
    "flow_only": {
        "label": "Flow Only",
        "group": "Basic",
        "description": "Navier-Stokes flow simulation without transport or reactions.",
    },
    "transport_only": {
        "label": "Transport Only",
        "group": "Basic",
        "description": "Flow with passive tracer transport (advection-diffusion). No reactions.",
    },
    "abiotic_first_order": {
        "label": "Abiotic: First-Order Decay",
        "group": "Abiotic Kinetics",
        "description": "Single substrate with first-order decay reaction (dA/dt = -k*A).",
    },
    "abiotic_bimolecular": {
        "label": "Abiotic: Bimolecular Reaction",
        "group": "Abiotic Kinetics",
        "description": "Bimolecular reaction A + B -> C with second-order kinetics.",
    },
    "abiotic_reversible": {
        "label": "Abiotic: Reversible Reaction",
        "group": "Abiotic Kinetics",
        "description": "Reversible reaction A <-> B approaching equilibrium.",
    },
    "biofilm_sessile": {
        "label": "Biofilm Growth (Sessile CA)",
        "group": "Biotic Kinetics",
        "description": "Sessile biofilm with Monod kinetics and cellular automata expansion.",
    },
    "planktonic": {
        "label": "Planktonic Bacteria (LBM)",
        "group": "Biotic Kinetics",
        "description": "Free-floating planktonic bacteria transported by flow with Monod kinetics.",
    },
    "biofilm_equilibrium": {
        "label": "Biofilm + Equilibrium Chemistry",
        "group": "Coupled Systems",
        "description": "Sessile biofilm with Monod kinetics and carbonate equilibrium chemistry.",
    },
    "full_coupled": {
        "label": "Full Coupled System",
        "group": "Coupled Systems",
        "description": "Biotic kinetics, abiotic kinetics, and equilibrium chemistry combined.",
    },
}


class ProjectTemplates:

    @staticmethod
    def list_templates():
        """Return list of (key, label, group, description) tuples."""
        result = []
        for key, info in TEMPLATES.items():
            result.append((key, info["label"], info["group"], info["description"]))
        return result

    @staticmethod
    def apply_template(key):
        """Return a CompLaBProject configured for the given template."""
        proj = CompLaBProject()

        if key == "flow_only":
            proj.simulation_mode = SimulationMode(
                biotic_mode=False, enable_kinetics=False,
                enable_abiotic_kinetics=False)
            proj.description = TEMPLATES[key]["description"]

        elif key == "transport_only":
            proj.simulation_mode = SimulationMode(
                biotic_mode=False, enable_kinetics=False,
                enable_abiotic_kinetics=False)
            proj.substrates = [
                Substrate(name="Tracer", initial_concentration=0.0,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.description = TEMPLATES[key]["description"]

        elif key == "abiotic_first_order":
            proj.simulation_mode = SimulationMode(
                biotic_mode=False, enable_kinetics=False,
                enable_abiotic_kinetics=True)
            proj.substrates = [
                Substrate(name="A", initial_concentration=1.0,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.description = TEMPLATES[key]["description"]

        elif key == "abiotic_bimolecular":
            proj.simulation_mode = SimulationMode(
                biotic_mode=False, enable_kinetics=False,
                enable_abiotic_kinetics=True)
            proj.substrates = [
                Substrate(name="A", initial_concentration=1.0e-3,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-3,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="B", initial_concentration=1.0e-3,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-3,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="C", initial_concentration=0.0,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=0.0,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.description = TEMPLATES[key]["description"]

        elif key == "abiotic_reversible":
            proj.simulation_mode = SimulationMode(
                biotic_mode=False, enable_kinetics=False,
                enable_abiotic_kinetics=True)
            proj.substrates = [
                Substrate(name="A", initial_concentration=1.0e-3,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-3,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="B", initial_concentration=0.0,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=0.0,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.description = TEMPLATES[key]["description"]

        elif key == "biofilm_sessile":
            proj.simulation_mode = SimulationMode(
                biotic_mode=True, enable_kinetics=True,
                enable_abiotic_kinetics=False)
            proj.substrates = [
                Substrate(name="DOC", initial_concentration=0.1,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=2.0e-10,
                          left_bc_type="Dirichlet", left_bc_value=0.1,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="CO2", initial_concentration=1.0e-5,
                          diffusion_in_pore=1.9e-9, diffusion_in_biofilm=3.8e-10,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-5,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.microbes = [
                Microbe(name="Heterotroph", solver_type="CA",
                        reaction_type="kinetics",
                        material_numbers="3 6",
                        initial_densities="99.0 99.0",
                        decay_coefficient=1.0e-9, viscosity_ratio=10.0,
                        half_saturation_constants="1.0e-5 0.0",
                        max_uptake_flux="2.5 0.0"),
            ]
            proj.microbiology = MicrobiologySettings(
                max_biomass_density=100.0, thrd_biofilm_fraction=0.1,
                ca_method="half")
            proj.description = TEMPLATES[key]["description"]

        elif key == "planktonic":
            proj.simulation_mode = SimulationMode(
                biotic_mode=True, enable_kinetics=True,
                enable_abiotic_kinetics=False)
            proj.substrates = [
                Substrate(name="DOC", initial_concentration=0.1,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=1.0e-9,
                          left_bc_type="Dirichlet", left_bc_value=0.1,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="CO2", initial_concentration=1.0e-5,
                          diffusion_in_pore=1.9e-9, diffusion_in_biofilm=1.9e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-5,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.microbes = [
                Microbe(name="Planktonic_Heterotroph", solver_type="LBM",
                        reaction_type="kinetics",
                        material_numbers="2",
                        initial_densities="0.0 10.0",
                        decay_coefficient=1.0e-7, viscosity_ratio=1.0,
                        half_saturation_constants="1.0e-5 0.0",
                        max_uptake_flux="2.5 0.0",
                        left_bc_type="Dirichlet", left_bc_value=10.0),
            ]
            proj.microbiology = MicrobiologySettings(
                max_biomass_density=100.0, thrd_biofilm_fraction=0.1,
                ca_method="none")
            proj.description = TEMPLATES[key]["description"]

        elif key == "biofilm_equilibrium":
            proj.simulation_mode = SimulationMode(
                biotic_mode=True, enable_kinetics=True,
                enable_abiotic_kinetics=False)
            proj.substrates = [
                Substrate(name="DOC", initial_concentration=0.1,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=2.0e-10,
                          left_bc_type="Dirichlet", left_bc_value=0.1,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="CO2", initial_concentration=1.0e-5,
                          diffusion_in_pore=1.9e-9, diffusion_in_biofilm=3.8e-10,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-5,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="HCO3", initial_concentration=2.0e-3,
                          diffusion_in_pore=1.2e-9, diffusion_in_biofilm=2.4e-10,
                          left_bc_type="Dirichlet", left_bc_value=2.0e-3,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="CO3", initial_concentration=1.0e-5,
                          diffusion_in_pore=0.9e-9, diffusion_in_biofilm=1.8e-10,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-5,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="Hplus", initial_concentration=1.0e-7,
                          diffusion_in_pore=9.3e-9, diffusion_in_biofilm=1.86e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-7,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.microbes = [
                Microbe(name="Heterotroph", solver_type="CA",
                        reaction_type="kinetics",
                        material_numbers="3 6",
                        initial_densities="99.0 99.0",
                        decay_coefficient=1.0e-9, viscosity_ratio=10.0,
                        half_saturation_constants="1.0e-5 0.0 0.0 0.0 0.0",
                        max_uptake_flux="2.5 0.0 0.0 0.0 0.0"),
            ]
            proj.microbiology = MicrobiologySettings(
                max_biomass_density=100.0, thrd_biofilm_fraction=0.1,
                ca_method="half")
            proj.equilibrium = EquilibriumSettings(
                enabled=True,
                components=["HCO3", "Hplus"],
                stoichiometry=[
                    [0.0, 0.0],    # DOC
                    [0.0, 0.0],    # CO2
                    [1.0, 1.0],    # HCO3 (H2CO3 = HCO3- + H+)
                    [1.0, 0.0],    # CO3 (component)
                    [0.0, 1.0],    # H+ (component)
                ],
                log_k=[0.0, 0.0, 6.35, 0.0, -10.33],
            )
            proj.description = TEMPLATES[key]["description"]

        elif key == "full_coupled":
            proj.simulation_mode = SimulationMode(
                biotic_mode=True, enable_kinetics=True,
                enable_abiotic_kinetics=True)
            proj.substrates = [
                Substrate(name="DOC", initial_concentration=0.1,
                          diffusion_in_pore=1.0e-9, diffusion_in_biofilm=2.0e-10,
                          left_bc_type="Dirichlet", left_bc_value=0.1,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="CO2", initial_concentration=1.0e-5,
                          diffusion_in_pore=1.9e-9, diffusion_in_biofilm=3.8e-10,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-5,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="HCO3", initial_concentration=2.0e-3,
                          diffusion_in_pore=1.2e-9, diffusion_in_biofilm=2.4e-10,
                          left_bc_type="Dirichlet", left_bc_value=2.0e-3,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="CO3", initial_concentration=1.0e-5,
                          diffusion_in_pore=0.9e-9, diffusion_in_biofilm=1.8e-10,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-5,
                          right_bc_type="Neumann", right_bc_value=0.0),
                Substrate(name="Hplus", initial_concentration=1.0e-7,
                          diffusion_in_pore=9.3e-9, diffusion_in_biofilm=1.86e-9,
                          left_bc_type="Dirichlet", left_bc_value=1.0e-7,
                          right_bc_type="Neumann", right_bc_value=0.0),
            ]
            proj.microbes = [
                Microbe(name="Heterotroph", solver_type="CA",
                        reaction_type="kinetics",
                        material_numbers="3 6",
                        initial_densities="99.0 99.0",
                        decay_coefficient=1.0e-9, viscosity_ratio=10.0,
                        half_saturation_constants="1.0e-5 0.0 0.0 0.0 0.0",
                        max_uptake_flux="2.5 0.0 0.0 0.0 0.0"),
            ]
            proj.microbiology = MicrobiologySettings(
                max_biomass_density=100.0, thrd_biofilm_fraction=0.1,
                ca_method="half")
            proj.equilibrium = EquilibriumSettings(
                enabled=True,
                components=["HCO3", "Hplus"],
                stoichiometry=[
                    [0.0, 0.0],
                    [0.0, 0.0],
                    [1.0, 1.0],
                    [1.0, 0.0],
                    [0.0, 1.0],
                ],
                log_k=[0.0, 0.0, 6.35, 0.0, -10.33],
            )
            proj.description = TEMPLATES[key]["description"]

        return proj
