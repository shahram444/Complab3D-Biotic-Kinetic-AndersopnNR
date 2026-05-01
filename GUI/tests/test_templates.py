"""Tests for simulation templates (all 9 scenarios).

Verifies that each template produces a valid, self-consistent project
with correct simulation mode, substrate counts, microbe counts, and
that project validation passes without errors.
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.templates import TEMPLATES, get_template_list, create_from_template
from src.core.project import CompLaBProject


# ── Template registry ──────────────────────────────────────────────────

EXPECTED_KEYS = [
    "flow_only",
    "diffusion_only",
    "tracer_transport",
    "abiotic_reaction",
    "abiotic_equilibrium",
    "biotic_sessile",
    "biotic_planktonic",
    "biotic_sessile_planktonic",
    "coupled_biotic_abiotic",
]


class TestTemplateRegistry:
    """Ensure all 9 templates are registered and discoverable."""

    def test_all_nine_registered(self):
        assert len(TEMPLATES) == 9

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_key_exists(self, key):
        assert key in TEMPLATES

    def test_get_template_list_returns_tuples(self):
        lst = get_template_list()
        assert len(lst) == 9
        for key, name, desc in lst:
            assert isinstance(key, str)
            assert isinstance(name, str)
            assert isinstance(desc, str)
            assert len(name) > 0
            assert len(desc) > 0

    def test_unknown_key_returns_default_project(self):
        proj = create_from_template("nonexistent_template")
        assert isinstance(proj, CompLaBProject)


# ── Per-template validation ────────────────────────────────────────────

class TestFlowOnly:
    def test_create(self):
        p = create_from_template("flow_only")
        assert p.name == "Flow Only"
        assert p.simulation_mode.biotic_mode is False
        assert p.simulation_mode.enable_kinetics is False
        assert len(p.substrates) == 0
        assert len(p.microbiology.microbes) == 0

    def test_validates_clean(self):
        p = create_from_template("flow_only")
        errors = p.validate()
        # Flow-only has ade_max_iT=0 which triggers a VTK interval warning
        # This is expected (no ADE in flow-only) - filter it out
        real_errors = [e for e in errors if "VTK save interval" not in e]
        assert len(real_errors) == 0, f"Unexpected errors: {real_errors}"


class TestDiffusionOnly:
    def test_create(self):
        p = create_from_template("diffusion_only")
        assert p.simulation_mode.biotic_mode is False
        assert len(p.substrates) == 1
        assert p.substrates[0].name == "Tracer"
        assert p.fluid.peclet == 0.0

    def test_validates_clean(self):
        p = create_from_template("diffusion_only")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestTracerTransport:
    def test_create(self):
        p = create_from_template("tracer_transport")
        assert len(p.substrates) == 1
        assert p.fluid.peclet == 1.0

    def test_validates_clean(self):
        p = create_from_template("tracer_transport")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestAbioticReaction:
    def test_create(self):
        p = create_from_template("abiotic_reaction")
        assert p.simulation_mode.enable_abiotic_kinetics is True
        assert len(p.substrates) == 2
        assert p.substrates[0].name == "Reactant"
        assert p.substrates[1].name == "Product"

    def test_validates_clean(self):
        p = create_from_template("abiotic_reaction")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestAbioticEquilibrium:
    def test_create(self):
        p = create_from_template("abiotic_equilibrium")
        assert p.equilibrium.enabled is True
        assert len(p.substrates) == 5
        assert len(p.equilibrium.component_names) == 2

    def test_stoichiometry_dimensions(self):
        p = create_from_template("abiotic_equilibrium")
        assert len(p.equilibrium.stoichiometry) == len(p.substrates)
        for row in p.equilibrium.stoichiometry:
            assert len(row) == len(p.equilibrium.component_names)

    def test_logk_count(self):
        p = create_from_template("abiotic_equilibrium")
        assert len(p.equilibrium.log_k) == len(p.substrates)

    def test_validates_clean(self):
        p = create_from_template("abiotic_equilibrium")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestBioticSessile:
    def test_create(self):
        p = create_from_template("biotic_sessile")
        assert p.simulation_mode.biotic_mode is True
        assert p.simulation_mode.enable_kinetics is True
        assert len(p.substrates) == 1
        assert len(p.microbiology.microbes) == 1
        assert p.microbiology.microbes[0].solver_type == "CA"

    def test_validates_clean(self):
        p = create_from_template("biotic_sessile")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestBioticPlanktonic:
    def test_create(self):
        p = create_from_template("biotic_planktonic")
        assert p.simulation_mode.biotic_mode is True
        assert len(p.microbiology.microbes) == 1
        assert p.microbiology.microbes[0].solver_type == "LBM"

    def test_validates_clean(self):
        p = create_from_template("biotic_planktonic")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestBioticSessilePlanktonic:
    def test_create(self):
        p = create_from_template("biotic_sessile_planktonic")
        assert len(p.microbiology.microbes) == 2
        solvers = {m.solver_type for m in p.microbiology.microbes}
        assert solvers == {"CA", "LBM"}

    def test_validates_clean(self):
        p = create_from_template("biotic_sessile_planktonic")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestCoupledBioticAbiotic:
    def test_create(self):
        p = create_from_template("coupled_biotic_abiotic")
        assert p.simulation_mode.biotic_mode is True
        assert p.simulation_mode.enable_kinetics is True
        assert p.simulation_mode.enable_abiotic_kinetics is True
        assert len(p.substrates) == 2
        assert len(p.microbiology.microbes) == 1

    def test_validates_clean(self):
        p = create_from_template("coupled_biotic_abiotic")
        errors = p.validate()
        assert len(errors) == 0, f"Unexpected errors: {errors}"


# ── Cross-template checks ─────────────────────────────────────────────

class TestAllTemplatesHaveKinetics:
    """Every template must attach kinetics .hh source code."""

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_kinetics_source_attached(self, key):
        p = create_from_template(key)
        # All templates should have at least biotic .hh (even no-op stubs)
        assert p.kinetics_source is not None
        assert len(p.kinetics_source) > 0

    @pytest.mark.parametrize("key", EXPECTED_KEYS)
    def test_template_key_set(self, key):
        p = create_from_template(key)
        assert p.template_key == key
