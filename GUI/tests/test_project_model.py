"""Tests for the CompLaB3D project data model and validation logic.

Covers dataclass construction, deep copy, and the comprehensive
validation method that checks domain, chemistry, microbiology,
equilibrium, and cross-references.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.project import (
    CompLaBProject, SimulationMode, DomainSettings, FluidSettings,
    IterationSettings, Substrate, Microbe, MicrobiologySettings,
    EquilibriumSettings, IOSettings, PathSettings,
)


class TestDataclassDefaults:
    """Ensure all dataclasses have sensible defaults."""

    def test_project_defaults(self):
        p = CompLaBProject()
        assert p.name == "Untitled"
        assert isinstance(p.domain, DomainSettings)
        assert isinstance(p.fluid, FluidSettings)
        assert p.substrates == []
        assert p.microbiology.microbes == []

    def test_substrate_defaults(self):
        s = Substrate()
        assert s.diffusion_in_pore == 1e-9
        assert s.left_boundary_type == "Dirichlet"

    def test_microbe_defaults(self):
        m = Microbe()
        assert m.solver_type == "CA"
        assert m.reaction_type == "kinetics"

    def test_domain_defaults(self):
        d = DomainSettings()
        assert d.nx == 50
        assert d.ny == 30
        assert d.nz == 30
        assert d.unit == "um"


class TestDeepCopy:
    def test_deep_copy_is_independent(self):
        p = CompLaBProject(name="Original")
        p.substrates.append(Substrate(name="DOC"))
        c = p.deep_copy()
        c.name = "Copy"
        c.substrates[0].name = "Modified"
        assert p.name == "Original"
        assert p.substrates[0].name == "DOC"


class TestValidationDomain:
    def test_negative_dimensions(self):
        p = CompLaBProject()
        p.domain.nx = 0
        errors = p.validate()
        assert any("nx" in e or "Dimensions" in e for e in errors)

    def test_nx_too_small(self):
        p = CompLaBProject()
        p.domain.nx = 2
        errors = p.validate()
        assert any("nx must be >= 3" in e for e in errors)

    def test_negative_dx(self):
        p = CompLaBProject()
        p.domain.dx = -1.0
        errors = p.validate()
        assert any("dx" in e for e in errors)

    def test_invalid_unit(self):
        p = CompLaBProject()
        p.domain.unit = "ft"
        errors = p.validate()
        assert any("Unit" in e for e in errors)

    def test_geometry_must_be_dat(self):
        p = CompLaBProject()
        p.domain.geometry_filename = "geometry.vtk"
        errors = p.validate()
        assert any(".dat" in e for e in errors)


class TestValidationFluid:
    def test_tau_too_low(self):
        p = CompLaBProject()
        p.fluid.tau = 0.3
        errors = p.validate()
        assert any("tau" in e for e in errors)

    def test_tau_too_high(self):
        p = CompLaBProject()
        p.fluid.tau = 3.0
        errors = p.validate()
        assert any("tau" in e for e in errors)

    def test_negative_delta_p(self):
        p = CompLaBProject()
        p.fluid.delta_P = -1.0
        errors = p.validate()
        assert any("delta_P" in e for e in errors)


class TestValidationSubstrates:
    def test_duplicate_names(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.substrates = [
            Substrate(name="DOC"),
            Substrate(name="DOC"),
        ]
        errors = p.validate()
        assert any("Duplicate" in e for e in errors)

    def test_negative_concentration(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.substrates = [Substrate(name="X", initial_concentration=-1.0)]
        errors = p.validate()
        assert any("negative" in e.lower() for e in errors)

    def test_invalid_boundary_type(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.substrates = [Substrate(name="X", left_boundary_type="Robin")]
        errors = p.validate()
        assert any("Dirichlet" in e or "Neumann" in e for e in errors)

    def test_biofilm_diffusion_greater_than_pore(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.substrates = [
            Substrate(name="X", diffusion_in_pore=1e-9, diffusion_in_biofilm=1e-8)
        ]
        errors = p.validate()
        assert any("Biofilm diffusion" in e for e in errors)


class TestValidationMicrobiology:
    def test_biotic_mode_no_microbes(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = True
        p.simulation_mode.enable_kinetics = True
        p.substrates = [Substrate(name="DOC")]
        errors = p.validate()
        assert any("no microbes" in e.lower() for e in errors)

    def test_ca_needs_material_number(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = True
        p.simulation_mode.enable_kinetics = True
        p.substrates = [Substrate(name="DOC")]
        p.microbiology.microbes = [
            Microbe(name="M1", solver_type="CA", material_number="",
                    half_saturation_constants="1e-5", maximum_uptake_flux="2.5")
        ]
        errors = p.validate()
        assert any("material_number" in e for e in errors)

    def test_invalid_solver_type(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = True
        p.simulation_mode.enable_kinetics = True
        p.substrates = [Substrate(name="DOC")]
        p.microbiology.microbes = [
            Microbe(name="M1", solver_type="INVALID",
                    half_saturation_constants="1e-5", maximum_uptake_flux="2.5")
        ]
        errors = p.validate()
        assert any("Solver type" in e for e in errors)


class TestValidationEquilibrium:
    def test_enabled_no_components(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.equilibrium.enabled = True
        p.substrates = [Substrate(name="X")]
        errors = p.validate()
        assert any("component" in e.lower() for e in errors)

    def test_stoichiometry_mismatch(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.equilibrium.enabled = True
        p.equilibrium.component_names = ["H+"]
        p.substrates = [Substrate(name="X"), Substrate(name="Y")]
        p.equilibrium.stoichiometry = [[1.0]]  # 1 row but 2 substrates
        p.equilibrium.log_k = [0.0, 0.0]
        errors = p.validate()
        assert any("Stoichiometry" in e for e in errors)


class TestValidationCrossChecks:
    def test_kinetics_no_substrates(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = True
        p.simulation_mode.enable_kinetics = True
        p.microbiology.microbes = [
            Microbe(name="M1", solver_type="LBM")
        ]
        errors = p.validate()
        assert any("no substrates" in e.lower() for e in errors)

    def test_abiotic_no_substrates(self):
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.simulation_mode.enable_abiotic_kinetics = True
        errors = p.validate()
        assert any("substrate" in e.lower() for e in errors)
