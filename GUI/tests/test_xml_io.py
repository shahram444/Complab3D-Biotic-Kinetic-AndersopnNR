"""Tests for XML export/import and JSON save/load round-trips.

Ensures that projects survive serialization without data loss, and that
the XML structure matches what the C++ solver expects.
"""
import pytest
import sys
import os
import tempfile
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.core.project import (
    CompLaBProject, Substrate, Microbe, MicrobiologySettings,
    EquilibriumSettings, SimulationMode, DomainSettings, FluidSettings,
)
from src.core.project_manager import ProjectManager
from src.core.templates import create_from_template


class TestXMLExportStructure:
    """Verify the exported XML has the correct element hierarchy."""

    @pytest.fixture
    def xml_path(self, tmp_path):
        p = create_from_template("abiotic_reaction")
        path = str(tmp_path / "CompLaB.xml")
        ProjectManager.export_xml(p, path)
        return path

    def test_root_is_parameters(self, xml_path):
        tree = ET.parse(xml_path)
        assert tree.getroot().tag == "parameters"

    def test_has_required_sections(self, xml_path):
        tree = ET.parse(xml_path)
        root = tree.getroot()
        required = ["path", "simulation_mode", "LB_numerics",
                    "chemistry", "microbiology", "equilibrium", "IO"]
        for section in required:
            assert root.find(section) is not None, f"Missing <{section}>"

    def test_substrate_count_in_xml(self, xml_path):
        tree = ET.parse(xml_path)
        chem = tree.getroot().find("chemistry")
        n = int(chem.find("number_of_substrates").text)
        assert n == 2

    def test_domain_dimensions(self, xml_path):
        tree = ET.parse(xml_path)
        dom = tree.getroot().find("LB_numerics/domain")
        assert int(dom.find("nx").text) == 30
        assert int(dom.find("ny").text) == 10

    def test_simulation_mode_values(self, xml_path):
        tree = ET.parse(xml_path)
        sm = tree.getroot().find("simulation_mode")
        assert sm.find("biotic_mode").text == "false"
        assert sm.find("enable_abiotic_kinetics").text == "true"


class TestXMLRoundTrip:
    """Export then import - data must survive the round trip."""

    @pytest.mark.parametrize("template_key", [
        "flow_only", "diffusion_only", "tracer_transport",
        "abiotic_reaction", "abiotic_equilibrium",
        "biotic_sessile", "biotic_planktonic",
        "biotic_sessile_planktonic", "coupled_biotic_abiotic",
    ])
    def test_round_trip(self, tmp_path, template_key):
        original = create_from_template(template_key)
        xml_path = str(tmp_path / "CompLaB.xml")
        ProjectManager.export_xml(original, xml_path)
        loaded = ProjectManager.import_xml(xml_path)

        # Check key fields
        assert loaded.domain.nx == original.domain.nx
        assert loaded.domain.ny == original.domain.ny
        assert loaded.domain.nz == original.domain.nz
        assert loaded.fluid.tau == original.fluid.tau
        assert len(loaded.substrates) == len(original.substrates)
        assert len(loaded.microbiology.microbes) == len(original.microbiology.microbes)

        # Check substrate names
        for s_orig, s_load in zip(original.substrates, loaded.substrates):
            assert s_load.name == s_orig.name

        # Check simulation mode
        assert loaded.simulation_mode.biotic_mode == original.simulation_mode.biotic_mode
        assert loaded.simulation_mode.enable_kinetics == original.simulation_mode.enable_kinetics


class TestJSONRoundTrip:
    """Save/load .complab (JSON) format."""

    @pytest.mark.parametrize("template_key", [
        "flow_only", "biotic_sessile", "coupled_biotic_abiotic",
    ])
    def test_json_round_trip(self, tmp_path, template_key):
        original = create_from_template(template_key)
        json_path = str(tmp_path / "test.complab")
        ProjectManager.save_project(original, json_path)
        loaded = ProjectManager.load_project(json_path)

        assert loaded.name == original.name
        assert loaded.domain.nx == original.domain.nx
        assert len(loaded.substrates) == len(original.substrates)
        assert len(loaded.microbiology.microbes) == len(original.microbiology.microbes)
        assert loaded.template_key == original.template_key


class TestKineticsDeployment:
    """Test that kinetics .hh files are correctly deployed to disk."""

    def test_deploy_biotic_and_abiotic(self, tmp_path):
        p = create_from_template("coupled_biotic_abiotic")
        deployed = ProjectManager.deploy_kinetics(p, str(tmp_path))
        assert len(deployed) == 2
        assert any("defineKinetics.hh" in d for d in deployed)
        assert any("defineAbioticKinetics.hh" in d for d in deployed)

    def test_deploy_only_stubs_for_flow_only(self, tmp_path):
        p = create_from_template("flow_only")
        deployed = ProjectManager.deploy_kinetics(p, str(tmp_path))
        assert len(deployed) >= 1  # At least biotic stub
        for path in deployed:
            content = open(path).read()
            assert "No-op stub" in content or "defineRxnKinetics" in content

    def test_deployed_files_contain_function(self, tmp_path):
        p = create_from_template("biotic_sessile")
        deployed = ProjectManager.deploy_kinetics(p, str(tmp_path))
        biotic_path = [d for d in deployed if "defineKinetics" in d][0]
        content = open(biotic_path).read()
        assert "defineRxnKinetics" in content
        assert "KineticsStats" in content


class TestEquilibriumXML:
    """Test equilibrium section serialization."""

    def test_equilibrium_exported(self, tmp_path):
        p = create_from_template("abiotic_equilibrium")
        xml_path = str(tmp_path / "CompLaB.xml")
        ProjectManager.export_xml(p, xml_path)

        tree = ET.parse(xml_path)
        eq = tree.getroot().find("equilibrium")
        assert eq.find("enabled").text == "true"
        assert eq.find("components") is not None
        assert eq.find("stoichiometry") is not None
        assert eq.find("logK") is not None

    def test_equilibrium_round_trip(self, tmp_path):
        p = create_from_template("abiotic_equilibrium")
        xml_path = str(tmp_path / "CompLaB.xml")
        ProjectManager.export_xml(p, xml_path)
        loaded = ProjectManager.import_xml(xml_path)

        assert loaded.equilibrium.enabled is True
        assert len(loaded.equilibrium.component_names) == 2
        assert len(loaded.equilibrium.stoichiometry) == 5
        assert len(loaded.equilibrium.log_k) == 5
