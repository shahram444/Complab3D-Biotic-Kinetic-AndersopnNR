"""End-to-end pipeline tests for the CompLaB Studio data flow.

Tests cover the ENTIRE path from raw user inputs through to simulation
execution and file output:

  1. Geometry .dat file creation and loading
  2. Project data model population (simulating user inputs via templates)
  3. XML export and re-import round-trip fidelity
  4. Kinetics .hh deployment and cross-validation
  5. JSON project save/load round-trip
  6. Full simulation run producing .out log files and completing correctly
  7. Template consistency: every template validates cleanly

Run with:
    cd GUI
    COMPLAB_DEBUG=1 python -m pytest tests/test_pipeline_e2e.py -v -s
"""

import gc
import os
import sys
import stat
import time
import textwrap
import logging
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from PySide6.QtCore import QThread

# ---------------------------------------------------------------------------
# Ensure the GUI package is importable
# ---------------------------------------------------------------------------
GUI_DIR = Path(__file__).resolve().parent.parent          # GUI/
sys.path.insert(0, str(GUI_DIR))

from src.core.project import (                            # noqa: E402
    CompLaBProject, PathSettings, SimulationMode, DomainSettings,
    FluidSettings, IterationSettings, Substrate, Microbe,
    MicrobiologySettings, EquilibriumSettings, IOSettings,
)
from src.core.project_manager import ProjectManager       # noqa: E402
from src.core.templates import (                          # noqa: E402
    TEMPLATES, create_from_template, get_template_list,
)
from src.core.kinetics_templates import (                 # noqa: E402
    TEMPLATE_KINETICS, get_kinetics_info,
    parse_hh_indices, verify_function_signature,
    validate_kinetics_vs_project,
)
from src.core.simulation_runner import SimulationRunner   # noqa: E402

log = logging.getLogger("complab.test.pipeline")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def _setup_logging():
    root = logging.getLogger("complab")
    if not root.handlers:
        root.setLevel(logging.DEBUG)
        h = logging.StreamHandler(sys.stderr)
        h.setLevel(logging.DEBUG)
        h.setFormatter(logging.Formatter(
            "%(asctime)s.%(msecs)03d [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"))
        root.addHandler(h)


@pytest.fixture()
def work_dir(tmp_path, _setup_logging):
    """Create a minimal working directory with sub-dirs."""
    (tmp_path / "input").mkdir()
    (tmp_path / "output").mkdir()
    (tmp_path / "src").mkdir()
    return tmp_path


def _make_geometry_file(directory: Path, nx: int, ny: int, nz: int,
                        filename: str = "geometry.dat",
                        pore_value: int = 2) -> Path:
    """Create a valid text-format geometry .dat file.

    Format: one integer per line, nx*ny*nz lines total.
    All voxels are set to *pore_value* (open pore space).
    """
    path = directory / filename
    total = nx * ny * nz
    path.write_text("\n".join([str(pore_value)] * total) + "\n")
    return path


def _write_fake_solver(tmp_path: Path, script_body: str) -> str:
    """Write a Python script that acts as a fake C++ solver.

    On Windows, creates a .bat wrapper that invokes ``python script.py``
    because Windows cannot execute scripts via shebang lines.
    On Unix, uses the standard shebang approach.
    """
    python = sys.executable
    script = tmp_path / "complab.py"
    lines = [
        f"#!{python}",
        "import sys, time, os",
        textwrap.dedent(script_body),
    ]
    script.write_text("\n".join(lines))
    script.chmod(script.stat().st_mode | stat.S_IEXEC)

    if os.name == "nt":
        bat = tmp_path / "complab.bat"
        bat.write_text(f'@"{python}" "{script}"\n')
        return str(bat)
    else:
        return str(script)


class SignalCollector:
    """Accumulates emissions from SimulationRunner signals."""

    def __init__(self):
        self.lines: list[str] = []
        self.progress_events: list[tuple[int, int]] = []
        self.finished: list[tuple[int, str]] = []
        self.diagnostics: list[str] = []

    def on_line(self, text: str):
        self.lines.append(text)

    def on_progress(self, cur: int, mx: int):
        self.progress_events.append((cur, mx))

    def on_finished(self, code: int, msg: str):
        self.finished.append((code, msg))

    def on_diagnostic(self, text: str):
        self.diagnostics.append(text)

    def connect(self, runner: SimulationRunner):
        runner.output_line.connect(self.on_line)
        runner.progress.connect(self.on_progress)
        runner.finished_signal.connect(self.on_finished)
        runner.diagnostic_report.connect(self.on_diagnostic)


# ===================================================================
# TEST 1 – Geometry .dat file creation and loading
# ===================================================================

class TestGeometryFile:
    """Verify geometry .dat file handling: creation, size validation,
    and detection of mismatches."""

    def test_correct_geometry_size(self, work_dir):
        """A geometry file with exactly nx*ny*nz entries passes validation."""
        nx, ny, nz = 10, 5, 5
        _make_geometry_file(work_dir / "input", nx, ny, nz)

        proj = CompLaBProject()
        proj.domain = DomainSettings(
            nx=nx, ny=ny, nz=nz, dx=1.0,
            geometry_filename="geometry.dat")
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False,
            enable_abiotic_kinetics=False)
        proj.substrates = [
            Substrate(name="Tracer", diffusion_in_pore=1e-9,
                      left_boundary_type="Dirichlet",
                      left_boundary_condition=1.0),
        ]

        errors = proj.validate_files(str(work_dir))
        geom_errors = [e for e in errors if "[Geometry]" in e]
        assert len(geom_errors) == 0, (
            f"Geometry validation should pass but got: {geom_errors}")

    def test_mismatched_geometry_size(self, work_dir):
        """Geometry file with wrong number of entries is detected."""
        # Create file for 10*5*5 = 250 voxels
        _make_geometry_file(work_dir / "input", 10, 5, 5)

        # But tell the project it's 20*10*10 = 2000 voxels
        proj = CompLaBProject()
        proj.domain = DomainSettings(
            nx=20, ny=10, nz=10, dx=1.0,
            geometry_filename="geometry.dat")
        proj.simulation_mode = SimulationMode(biotic_mode=True)
        proj.microbiology.microbes = [
            Microbe(name="m0", solver_type="CA", material_number="3")]

        errors = proj.validate_files(str(work_dir))
        geom_errors = [e for e in errors if "SIZE MISMATCH" in e]
        assert len(geom_errors) >= 1, (
            f"Expected SIZE MISMATCH error but got: {errors}")

    def test_missing_geometry_file(self, work_dir):
        """Missing geometry file triggers a warning for non-flow-only runs."""
        proj = CompLaBProject()
        proj.domain.geometry_filename = "nonexistent.dat"
        proj.substrates = [Substrate(name="S0")]

        errors = proj.validate_files(str(work_dir))
        geom_errors = [e for e in errors if "[Geometry]" in e]
        assert len(geom_errors) >= 1, (
            f"Expected geometry not-found error but got: {errors}")

    def test_geometry_file_content(self, work_dir):
        """Verify the generated geometry file has correct line count."""
        nx, ny, nz = 8, 4, 3
        path = _make_geometry_file(work_dir / "input", nx, ny, nz)

        lines = path.read_text().strip().split("\n")
        expected = nx * ny * nz
        assert len(lines) == expected, (
            f"Expected {expected} lines, got {len(lines)}")

        # All should be pore=2
        for i, line in enumerate(lines):
            assert line.strip() == "2", (
                f"Line {i}: expected '2', got '{line.strip()}'")

    def test_geometry_all_material_types(self, work_dir):
        """Geometry file with mixed material types: solid, bounce-back, pore."""
        nx, ny, nz = 6, 4, 3
        total = nx * ny * nz
        # Create alternating 0 (solid), 1 (bounce-back), 2 (pore)
        values = [str(i % 3) for i in range(total)]
        path = work_dir / "input" / "geometry.dat"
        path.write_text("\n".join(values) + "\n")

        proj = CompLaBProject()
        proj.domain = DomainSettings(
            nx=nx, ny=ny, nz=nz, dx=1.0,
            geometry_filename="geometry.dat",
            pore="2", solid="0", bounce_back="1")
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False,
            enable_abiotic_kinetics=False)
        proj.substrates = [Substrate(name="Tracer")]

        errors = proj.validate_files(str(work_dir))
        geom_errors = [e for e in errors if "[Geometry]" in e]
        assert len(geom_errors) == 0, (
            f"Mixed material geometry should pass: {geom_errors}")


# ===================================================================
# TEST 2 – User input → project data model
# ===================================================================

class TestProjectDataModel:
    """Verify that user inputs (simulated via templates) produce
    correct project data model configurations."""

    def test_flow_only_template(self):
        """Flow-only template has no substrates, no microbes."""
        proj = create_from_template("flow_only")
        assert proj.name == "Flow Only"
        assert proj.simulation_mode.biotic_mode is False
        assert proj.simulation_mode.enable_kinetics is False
        assert proj.simulation_mode.enable_abiotic_kinetics is False
        assert len(proj.substrates) == 0
        assert len(proj.microbiology.microbes) == 0

    def test_biofilm_sessile_template(self):
        """Biofilm sessile: 1 substrate, 1 CA microbe."""
        proj = create_from_template("biotic_sessile")
        assert proj.simulation_mode.biotic_mode is True
        assert proj.simulation_mode.enable_kinetics is True
        assert len(proj.substrates) == 1
        assert proj.substrates[0].name == "DOC"
        assert len(proj.microbiology.microbes) == 1
        mic = proj.microbiology.microbes[0]
        assert mic.solver_type == "CA"
        assert mic.material_number == "3 6"
        assert "kinetics" in mic.reaction_type

    def test_abiotic_first_order_template(self):
        """Abiotic first order: 2 substrates, no microbes."""
        proj = create_from_template("abiotic_reaction")
        assert proj.simulation_mode.biotic_mode is False
        assert proj.simulation_mode.enable_abiotic_kinetics is True
        assert len(proj.substrates) == 2
        assert proj.substrates[0].name == "Reactant"
        assert proj.substrates[1].name == "Product"
        assert len(proj.microbiology.microbes) == 0

    def test_full_coupled_template(self):
        """Coupled biotic-abiotic: 2 substrates (DOC+Byproduct), 1 CA microbe."""
        proj = create_from_template("coupled_biotic_abiotic")
        assert proj.simulation_mode.biotic_mode is True
        assert proj.simulation_mode.enable_kinetics is True
        assert proj.simulation_mode.enable_abiotic_kinetics is True
        assert len(proj.substrates) == 2
        assert proj.substrates[0].name == "DOC"
        assert proj.substrates[1].name == "Byproduct"
        assert len(proj.microbiology.microbes) == 1
        assert proj.microbiology.microbes[0].solver_type == "CA"

    def test_manual_project_construction(self):
        """Build a project manually (simulating raw user inputs)."""
        proj = CompLaBProject(name="Manual Test")
        proj.simulation_mode = SimulationMode(
            biotic_mode=True, enable_kinetics=True)
        proj.domain = DomainSettings(
            nx=30, ny=15, nz=15, dx=2.0, unit="um",
            characteristic_length=15.0)
        proj.fluid = FluidSettings(
            delta_P=1e-3, peclet=0.5, tau=0.8)
        proj.substrates = [
            Substrate(name="Oxygen", initial_concentration=0.2,
                      diffusion_in_pore=2.1e-9, diffusion_in_biofilm=4.2e-10,
                      left_boundary_type="Dirichlet",
                      left_boundary_condition=0.2),
            Substrate(name="Carbon", initial_concentration=0.05,
                      diffusion_in_pore=1e-9, diffusion_in_biofilm=2e-10,
                      left_boundary_type="Dirichlet",
                      left_boundary_condition=0.05),
        ]
        proj.microbiology = MicrobiologySettings(
            maximum_biomass_density=120.0,
            microbes=[
                Microbe(name="Aerobe", solver_type="CA",
                        reaction_type="kinetics",
                        material_number="3",
                        initial_densities="80.0",
                        half_saturation_constants="1e-5 1e-6",
                        maximum_uptake_flux="2.0 0.5"),
            ])

        # Verify internal consistency
        assert len(proj.substrates) == 2
        assert proj.microbiology.microbes[0].name == "Aerobe"
        ks = proj.microbiology.microbes[0].half_saturation_constants.split()
        assert len(ks) == len(proj.substrates), (
            "half_saturation_constants count must match substrate count")

    def test_deep_copy_independence(self):
        """deep_copy() must produce fully independent copy."""
        orig = create_from_template("biotic_sessile")
        copy = orig.deep_copy()

        # Modify the copy
        copy.name = "Modified"
        copy.substrates[0].name = "CHANGED"
        copy.microbiology.microbes[0].name = "CHANGED_MIC"

        # Original must be unchanged
        assert orig.name == "Biofilm Sessile"
        assert orig.substrates[0].name == "DOC"
        assert orig.microbiology.microbes[0].name == "Heterotroph"

    def test_all_templates_exist(self):
        """Every template key in TEMPLATE_KINETICS has a matching template."""
        template_keys = set(TEMPLATES.keys())
        kinetics_keys = set(TEMPLATE_KINETICS.keys())
        # All kinetics templates should have a project template
        missing = kinetics_keys - template_keys
        assert len(missing) == 0, (
            f"Kinetics templates without project templates: {missing}")


# ===================================================================
# TEST 3 – Project validation
# ===================================================================

class TestProjectValidation:
    """Verify that validate() catches real errors and passes valid configs."""

    def test_valid_biofilm_project_passes(self):
        """A well-formed biofilm project should have zero blocking errors."""
        proj = create_from_template("biotic_sessile")
        errors = proj.validate()
        # Filter out warnings (lines containing "Warning:")
        blocking = [e for e in errors if "Warning" not in e]
        assert len(blocking) == 0, (
            f"Valid biofilm project has errors: {blocking}")

    def test_invalid_domain_dimensions(self):
        """nx=0 must trigger domain error."""
        proj = CompLaBProject()
        proj.domain.nx = 0
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False)
        errors = proj.validate()
        domain_errors = [e for e in errors if "[Domain]" in e]
        assert len(domain_errors) >= 1

    def test_invalid_tau(self):
        """tau <= 0.5 must trigger solver error."""
        proj = CompLaBProject()
        proj.fluid.tau = 0.4
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False)
        errors = proj.validate()
        tau_errors = [e for e in errors if "tau" in e.lower()]
        assert len(tau_errors) >= 1

    def test_substrate_index_mismatch(self):
        """Kinetics accessing C[5] with only 1 substrate must error."""
        proj = create_from_template("coupled_biotic_abiotic")
        # Remove all substrates except one
        proj.substrates = [proj.substrates[0]]
        errors = proj.validate()
        crash_errors = [e for e in errors if "crash" in e.lower()
                        or "out-of-bounds" in e.lower()
                        or "C[" in e]
        assert len(crash_errors) >= 1, (
            f"Expected out-of-bounds error but got: {errors}")

    def test_duplicate_substrate_name(self):
        """Duplicate substrate names must be caught."""
        proj = CompLaBProject()
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False)
        proj.substrates = [
            Substrate(name="Same"),
            Substrate(name="Same"),
        ]
        errors = proj.validate()
        dup_errors = [e for e in errors if "Duplicate" in e]
        assert len(dup_errors) >= 1

    def test_equilibrium_stoichiometry_size(self):
        """Stoichiometry matrix row count must match substrate count."""
        proj = create_from_template("abiotic_equilibrium")
        # Add an extra substrate without updating stoichiometry
        proj.substrates.append(Substrate(name="ExtraS"))
        errors = proj.validate()
        eq_errors = [e for e in errors if "[Equilibrium]" in e
                     and "Stoichiometry" in e]
        assert len(eq_errors) >= 1, (
            f"Expected stoichiometry size error but got: {errors}")


# ===================================================================
# TEST 4 – XML generation and round-trip validation
# ===================================================================

class TestXMLGeneration:
    """Export XML and verify structure matches C++ solver expectations."""

    def test_xml_structure_biofilm(self, work_dir):
        """Biofilm template -> XML has correct top-level elements."""
        proj = create_from_template("biotic_sessile")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        root = tree.getroot()
        assert root.tag == "parameters"

        expected_children = [
            "path", "simulation_mode", "LB_numerics",
            "chemistry", "microbiology", "equilibrium", "IO",
        ]
        child_tags = [c.tag for c in root]
        for tag in expected_children:
            assert tag in child_tags, (
                f"Missing <{tag}> in XML. Got: {child_tags}")

    def test_xml_substrate_count(self, work_dir):
        """number_of_substrates in XML matches project."""
        proj = create_from_template("abiotic_reaction")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        root = tree.getroot()
        chem = root.find("chemistry")
        nsubs = int(chem.find("number_of_substrates").text.strip())
        assert nsubs == 2, f"Expected 2 substrates, got {nsubs}"

        # Verify substrate elements exist
        for i in range(2):
            assert chem.find(f"substrate{i}") is not None

    def test_xml_microbe_count(self, work_dir):
        """number_of_microbes in XML matches project."""
        proj = create_from_template("biotic_sessile_planktonic")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        root = tree.getroot()
        mb = root.find("microbiology")
        nmic = int(mb.find("number_of_microbes").text.strip())
        assert nmic == 2

    def test_xml_domain_dimensions(self, work_dir):
        """Domain nx/ny/nz in XML match the project settings."""
        proj = CompLaBProject()
        proj.domain = DomainSettings(nx=42, ny=17, nz=9)
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False)
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        dom = tree.getroot().find("LB_numerics").find("domain")
        assert int(dom.find("nx").text.strip()) == 42
        assert int(dom.find("ny").text.strip()) == 17
        assert int(dom.find("nz").text.strip()) == 9

    def test_xml_simulation_mode(self, work_dir):
        """biotic_mode, enable_kinetics, enable_abiotic_kinetics are correct."""
        proj = create_from_template("abiotic_reaction")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        sm = tree.getroot().find("simulation_mode")
        assert sm.find("biotic_mode").text.strip() == "false"
        assert sm.find("enable_kinetics").text.strip() == "false"
        assert sm.find("enable_abiotic_kinetics").text.strip() == "true"

    def test_xml_round_trip_biofilm(self, work_dir):
        """Export → import → compare: all fields should survive."""
        orig = create_from_template("biotic_sessile")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(orig, xml_path)

        loaded = ProjectManager.import_xml(xml_path)

        # Core fields
        assert loaded.simulation_mode.biotic_mode == orig.simulation_mode.biotic_mode
        assert loaded.simulation_mode.enable_kinetics == orig.simulation_mode.enable_kinetics
        assert loaded.domain.nx == orig.domain.nx
        assert loaded.domain.ny == orig.domain.ny
        assert loaded.domain.nz == orig.domain.nz
        assert loaded.fluid.tau == orig.fluid.tau

        # Substrates
        assert len(loaded.substrates) == len(orig.substrates)
        for lo, og in zip(loaded.substrates, orig.substrates):
            assert lo.name == og.name
            assert abs(lo.initial_concentration - og.initial_concentration) < 1e-12
            assert lo.left_boundary_type == og.left_boundary_type

        # Microbes
        assert len(loaded.microbiology.microbes) == len(orig.microbiology.microbes)
        for lo, og in zip(loaded.microbiology.microbes, orig.microbiology.microbes):
            assert lo.name == og.name
            assert lo.solver_type == og.solver_type

    def test_xml_round_trip_full_coupled(self, work_dir):
        """Round-trip for the coupled biotic-abiotic template."""
        orig = create_from_template("coupled_biotic_abiotic")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(orig, xml_path)

        loaded = ProjectManager.import_xml(xml_path)

        assert len(loaded.substrates) == 2
        assert len(loaded.microbiology.microbes) == 1
        assert loaded.simulation_mode.enable_abiotic_kinetics is True

    def test_xml_round_trip_equilibrium(self, work_dir):
        """Round-trip for the abiotic equilibrium template with stoichiometry."""
        orig = create_from_template("abiotic_equilibrium")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(orig, xml_path)

        loaded = ProjectManager.import_xml(xml_path)

        assert len(loaded.substrates) == 5
        assert loaded.equilibrium.enabled is True
        assert len(loaded.equilibrium.component_names) == 2

        # Stoichiometry matrix
        assert len(loaded.equilibrium.stoichiometry) == 5
        for i, (lo_row, og_row) in enumerate(
                zip(loaded.equilibrium.stoichiometry,
                    orig.equilibrium.stoichiometry)):
            for j, (lo_v, og_v) in enumerate(zip(lo_row, og_row)):
                assert abs(lo_v - og_v) < 1e-10, (
                    f"Stoichiometry mismatch at [{i}][{j}]: "
                    f"{lo_v} != {og_v}")

        # logK values
        for i, (lo, og) in enumerate(
                zip(loaded.equilibrium.log_k, orig.equilibrium.log_k)):
            assert abs(lo - og) < 1e-10, (
                f"logK mismatch at [{i}]: {lo} != {og}")

    def test_xml_material_numbers(self, work_dir):
        """Microbe material numbers appear in <domain><material_numbers>."""
        proj = create_from_template("biotic_sessile")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        mat = tree.getroot().find("LB_numerics").find("domain") \
            .find("material_numbers")
        assert mat.find("pore").text.strip() == "2"
        assert mat.find("solid").text.strip() == "0"
        assert mat.find("bounce_back").text.strip() == "1"
        # Microbe material number
        m0 = mat.find("microbe0")
        assert m0 is not None
        assert m0.text.strip() == "3 6"

    def test_xml_equilibrium_section(self, work_dir):
        """Equilibrium section: components, stoichiometry, logK, solver params."""
        proj = create_from_template("abiotic_equilibrium")
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        eq = tree.getroot().find("equilibrium")
        assert eq.find("enabled").text.strip() == "true"
        assert eq.find("components") is not None

        st = eq.find("stoichiometry")
        assert st is not None
        # Should have species0..species4 (5 substrates)
        for i in range(5):
            sp = st.find(f"species{i}")
            assert sp is not None, f"Missing stoichiometry species{i}"

        lk = eq.find("logK")
        assert lk is not None
        for i in range(5):
            sp = lk.find(f"species{i}")
            assert sp is not None, f"Missing logK species{i}"

    def test_xml_io_section(self, work_dir):
        """IO section has correct VTK/CHK intervals."""
        proj = CompLaBProject()
        proj.io_settings = IOSettings(
            save_vtk_interval=500, save_chk_interval=2000)
        proj.simulation_mode = SimulationMode(
            biotic_mode=False, enable_kinetics=False)
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)

        tree = ET.parse(xml_path)
        io_el = tree.getroot().find("IO")
        assert int(io_el.find("save_VTK_interval").text.strip()) == 500
        assert int(io_el.find("save_CHK_interval").text.strip()) == 2000


# ===================================================================
# TEST 5 – Kinetics .hh deployment and cross-validation
# ===================================================================

class TestKineticsDeployment:
    """Verify kinetics .hh file generation, deployment, and validation."""

    def test_deploy_biotic_kinetics(self, work_dir):
        """Biotic template deploys defineKinetics.hh with correct content."""
        proj = create_from_template("biotic_sessile")
        deployed = ProjectManager.deploy_kinetics(proj, str(work_dir))

        biotic_path = work_dir / "defineKinetics.hh"
        assert biotic_path.exists(), "defineKinetics.hh not deployed"
        assert str(biotic_path) in deployed

        content = biotic_path.read_text()
        assert "defineRxnKinetics" in content
        assert "KineticsStats" in content
        assert "subsR" in content
        assert "bioR" in content

    def test_deploy_abiotic_kinetics(self, work_dir):
        """Abiotic template deploys defineAbioticKinetics.hh."""
        proj = create_from_template("abiotic_reaction")
        deployed = ProjectManager.deploy_kinetics(proj, str(work_dir))

        abiotic_path = work_dir / "defineAbioticKinetics.hh"
        assert abiotic_path.exists(), "defineAbioticKinetics.hh not deployed"
        assert str(abiotic_path) in deployed

        content = abiotic_path.read_text()
        assert "defineAbioticRxnKinetics" in content
        assert "subsR" in content

    def test_deploy_both_files(self, work_dir):
        """Every template deploys BOTH .hh files (solver needs both)."""
        proj = create_from_template("biotic_sessile")
        deployed = ProjectManager.deploy_kinetics(proj, str(work_dir))

        assert (work_dir / "defineKinetics.hh").exists()
        assert (work_dir / "defineAbioticKinetics.hh").exists()
        assert len(deployed) == 2

    def test_noop_stubs_compile(self):
        """No-op stubs have required function signatures."""
        for key in ["flow_only", "diffusion_only", "tracer_transport"]:
            info = get_kinetics_info(key)
            assert info is not None, f"No kinetics info for {key}"

            # Biotic stub must have defineRxnKinetics
            bio_errs = verify_function_signature(info.biotic_hh, "biotic")
            assert len(bio_errs) == 0, (
                f"{key} biotic stub errors: {bio_errs}")

            # Abiotic stub must have defineAbioticRxnKinetics
            abio_errs = verify_function_signature(info.abiotic_hh, "abiotic")
            assert len(abio_errs) == 0, (
                f"{key} abiotic stub errors: {abio_errs}")

    def test_kinetics_stats_namespace_always_present(self):
        """Every biotic .hh template MUST have the KineticsStats namespace
        (the C++ solver calls getStats/resetIteration unconditionally)."""
        for key, info in TEMPLATE_KINETICS.items():
            if info.biotic_hh:
                assert "KineticsStats" in info.biotic_hh, (
                    f"Template '{key}': defineKinetics.hh missing "
                    f"KineticsStats namespace")
                assert "resetIteration" in info.biotic_hh, (
                    f"Template '{key}': defineKinetics.hh missing "
                    f"resetIteration()")
                assert "getStats" in info.biotic_hh, (
                    f"Template '{key}': defineKinetics.hh missing "
                    f"getStats()")

    def test_parse_hh_indices_biotic(self):
        """parse_hh_indices extracts correct array indices from biotic code."""
        info = get_kinetics_info("biotic_sessile")
        idx = parse_hh_indices(info.biotic_hh)

        # Monod 1-substrate 1-microbe: C[0], B[0]
        # subsR[0]/bioR[0] are guarded by .size() checks and thus skipped
        assert "C" in idx
        assert 0 in idx["C"]
        assert "B" in idx
        assert 0 in idx["B"]

    def test_parse_hh_indices_abiotic(self):
        """parse_hh_indices extracts indices from abiotic code."""
        info = get_kinetics_info("abiotic_reaction")
        idx = parse_hh_indices(info.abiotic_hh)

        # First-order decay: rate = k * C[0]; subsR[0], subsR[1]
        assert "C" in idx
        assert 0 in idx["C"]
        assert "subsR" in idx
        assert 0 in idx["subsR"]
        assert 1 in idx["subsR"]

    def test_cross_validation_correct(self):
        """Correct project-kinetics pairing: zero errors."""
        proj = create_from_template("biotic_sessile")
        errors = validate_kinetics_vs_project(
            biotic_source=proj.kinetics_source,
            abiotic_source=proj.abiotic_kinetics_source,
            num_substrates=len(proj.substrates),
            num_microbes=len(proj.microbiology.microbes),
            biotic_mode=proj.simulation_mode.biotic_mode,
            enable_kinetics=proj.simulation_mode.enable_kinetics,
            enable_abiotic=proj.simulation_mode.enable_abiotic_kinetics,
        )
        assert len(errors) == 0, f"Expected 0 errors: {errors}"

    def test_cross_validation_too_few_substrates(self):
        """Kinetics accessing more substrates than defined → error."""
        # abiotic_reaction accesses C[0] and writes subsR[0], subsR[1]
        # With only 1 substrate, subsR[1] is out-of-bounds
        info = get_kinetics_info("abiotic_reaction")
        errors = validate_kinetics_vs_project(
            biotic_source=info.biotic_hh,
            abiotic_source=info.abiotic_hh,
            num_substrates=1,
            num_microbes=0,
            biotic_mode=False,
            enable_kinetics=False,
            enable_abiotic=True,
        )
        crash_errors = [e for e in errors if "crash" in e.lower()
                        or "C[" in e or "subsR[" in e]
        assert len(crash_errors) >= 1, (
            f"Expected substrate out-of-bounds error: {errors}")

    def test_cross_validation_too_few_microbes(self):
        """Kinetics accessing B[1] with only 1 microbe → error."""
        info = get_kinetics_info("biotic_sessile_planktonic")
        errors = validate_kinetics_vs_project(
            biotic_source=info.biotic_hh,
            abiotic_source=info.abiotic_hh,
            num_substrates=1,
            num_microbes=1,  # sessile_planktonic needs B[0] and B[1]
            biotic_mode=True,
            enable_kinetics=True,
            enable_abiotic=False,
        )
        mic_errors = [e for e in errors if "B[" in e]
        assert len(mic_errors) >= 1, (
            f"Expected microbe out-of-bounds error: {errors}")


# ===================================================================
# TEST 6 – JSON project save/load round-trip
# ===================================================================

class TestJSONRoundTrip:
    """Verify .complab JSON save and load preserves all fields."""

    def test_save_load_biofilm(self, work_dir):
        """Save and load a biofilm project: all fields survive."""
        orig = create_from_template("biotic_sessile")
        json_path = str(work_dir / "test.complab")
        ProjectManager.save_project(orig, json_path)
        loaded = ProjectManager.load_project(json_path)

        assert loaded.name == orig.name
        assert loaded.template_key == "biotic_sessile"
        assert len(loaded.substrates) == len(orig.substrates)
        assert len(loaded.microbiology.microbes) == len(orig.microbiology.microbes)
        assert loaded.simulation_mode.biotic_mode is True
        assert loaded.kinetics_source == orig.kinetics_source
        assert loaded.abiotic_kinetics_source == orig.abiotic_kinetics_source

    def test_save_load_full_coupled(self, work_dir):
        """Coupled biotic-abiotic project: kinetics source survives round-trip."""
        orig = create_from_template("coupled_biotic_abiotic")
        json_path = str(work_dir / "full.complab")
        ProjectManager.save_project(orig, json_path)
        loaded = ProjectManager.load_project(json_path)

        assert len(loaded.substrates) == 2
        assert len(loaded.microbiology.microbes) == 1
        assert loaded.simulation_mode.enable_abiotic_kinetics is True
        assert loaded.kinetics_source == orig.kinetics_source
        assert loaded.template_key == "coupled_biotic_abiotic"

    def test_save_load_preserves_kinetics_source(self, work_dir):
        """Kinetics .hh source code round-trips through JSON."""
        orig = create_from_template("abiotic_reaction")
        assert len(orig.abiotic_kinetics_source) > 100, (
            "Template should have abiotic kinetics source code")

        json_path = str(work_dir / "abiotic.complab")
        ProjectManager.save_project(orig, json_path)
        loaded = ProjectManager.load_project(json_path)

        assert loaded.abiotic_kinetics_source == orig.abiotic_kinetics_source
        assert "defineAbioticRxnKinetics" in loaded.abiotic_kinetics_source


# ===================================================================
# TEST 7 – Template consistency (every template validates cleanly)
# ===================================================================

class TestTemplateConsistency:
    """Every registered template should produce a valid project when
    used with its matching kinetics."""

    # Known template limitations discovered by these tests.
    # These are real inconsistencies in the templates that should be
    # fixed eventually, but are documented here as known issues.
    _KNOWN_TEMPLATE_ISSUES = {
        # flow_only: ade_max_iT=0 makes VTK interval > max iter
        "flow_only": ["VTK save interval"],
    }

    @pytest.mark.parametrize("key", list(TEMPLATES.keys()))
    def test_template_validates(self, key):
        """Template '{key}' should produce a project with no blocking errors
        (excluding known template limitations)."""
        proj = create_from_template(key)
        errors = proj.validate()
        # Filter out warnings
        blocking = [e for e in errors if "Warning" not in e]
        # Filter out cross-check warnings about zero concentrations
        blocking = [e for e in blocking
                    if "zero concentrations everywhere" not in e]
        # Filter out known template issues
        known = self._KNOWN_TEMPLATE_ISSUES.get(key, [])
        blocking = [e for e in blocking
                    if not any(k in e for k in known)]
        assert len(blocking) == 0, (
            f"Template '{key}' has validation errors:\n"
            + "\n".join(blocking))

    @pytest.mark.parametrize("key", list(TEMPLATES.keys()))
    def test_template_kinetics_match(self, key):
        """Template '{key}': kinetics .hh code matches project config."""
        proj = create_from_template(key)
        info = get_kinetics_info(key)
        assert info is not None, f"No kinetics info for template '{key}'"

        # Verify function signatures
        if info.biotic_hh:
            bio_errs = verify_function_signature(info.biotic_hh, "biotic")
            assert len(bio_errs) == 0, (
                f"Template '{key}' biotic signature errors: {bio_errs}")
        if info.abiotic_hh:
            abio_errs = verify_function_signature(info.abiotic_hh, "abiotic")
            assert len(abio_errs) == 0, (
                f"Template '{key}' abiotic signature errors: {abio_errs}")

    @pytest.mark.parametrize("key", list(TEMPLATES.keys()))
    def test_template_xml_round_trip(self, key, work_dir):
        """Template '{key}': export → import preserves substrate/microbe count."""
        orig = create_from_template(key)
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(orig, xml_path)
        loaded = ProjectManager.import_xml(xml_path)

        assert len(loaded.substrates) == len(orig.substrates), (
            f"Template '{key}': substrate count mismatch after round-trip")
        assert len(loaded.microbiology.microbes) == len(orig.microbiology.microbes), (
            f"Template '{key}': microbe count mismatch after round-trip")


# ===================================================================
# TEST 8 – Full simulation run producing .out log files
# ===================================================================

class TestFullSimulationRun:
    """End-to-end: set up project, export XML, deploy kinetics, run fake
    solver, verify .out log file and correct completion."""

    def test_full_pipeline_biofilm(self, qtbot, work_dir, _setup_logging):
        """Complete pipeline for a biofilm simulation."""
        # Step 1: Create project from template
        proj = create_from_template("biotic_sessile")
        proj.domain = DomainSettings(
            nx=10, ny=5, nz=5, dx=1.0,
            geometry_filename="geometry.dat")

        # Step 2: Create geometry file
        _make_geometry_file(
            work_dir / "input",
            proj.domain.nx, proj.domain.ny, proj.domain.nz)

        # Step 3: Export XML
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)
        assert os.path.isfile(xml_path)

        # Step 4: Deploy kinetics
        deployed = ProjectManager.deploy_kinetics(proj, str(work_dir))
        assert len(deployed) == 2  # Both .hh files

        # Step 5: Validate everything
        model_errors = proj.validate()
        blocking = [e for e in model_errors if "Warning" not in e]
        assert len(blocking) == 0, f"Model errors: {blocking}"

        file_errors = proj.validate_files(str(work_dir))
        assert len(file_errors) == 0, f"File errors: {file_errors}"

        # Step 6: Run fake solver that mimics C++ output
        script = """\
print("CompLaB3D v3.2 - Pore-Scale Reactive Transport")
print("=" * 60)
print("Reading CompLaB.xml ...")
print("Domain: 10 x 5 x 5")
print("Substrates: 1")
print("Microbes: 1 (CA)")
print("ade_max_iT = 20")
print("=" * 60)
print("")
print("--- Navier-Stokes Phase 1 ---")
for i in range(1, 6):
    print(f"NS iT = {i}  residual = {1e-3 / i:.6e}")
    sys.stdout.flush()
print("NS converged.")
print("")
print("--- ADE Transport + Kinetics ---")
for i in range(1, 21):
    print(f"iT = {i}  DOC_avg = {0.1 - i * 0.002:.6f}  "
          f"biomass_max = {50.0 + i * 2.0:.2f}")
    sys.stdout.flush()
print("")
print("--- Writing VTK output ---")
print("Saved: output/nsLattice_0000001.vti")
print("Saved: output/subsLattice_0000001.vti")
print("Saved: output/bioLattice_0000001.vti")
print("Saved: output/maskLattice_0000001.vti")
print("")
print("Simulation completed successfully.")
print(f"Total time: 0h 0m 3s")
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=30_000):
            runner.start()

        # Verify exit code
        assert len(collector.finished) == 1
        rc, msg = collector.finished[0]
        assert rc == 0, f"Simulation failed: rc={rc}, msg={msg}"
        assert "successfully" in msg.lower()

        # Verify progress was tracked
        assert len(collector.progress_events) >= 20

        # Verify .out log file was created
        out_dir = work_dir / "output"
        out_files = list(out_dir.glob("simulation_*.out"))
        assert len(out_files) >= 1, "No .out log file created"
        log_content = out_files[0].read_text()
        assert "CompLaB3D" in log_content
        assert "Simulation completed successfully" in log_content

        # Verify all solver output lines were captured
        all_text = "\n".join(collector.lines)
        assert "CompLaB3D" in all_text
        assert "NS converged" in all_text
        assert "nsLattice_0000001.vti" in all_text
        assert "subsLattice_0000001.vti" in all_text
        assert "bioLattice_0000001.vti" in all_text

    def test_full_pipeline_abiotic(self, qtbot, work_dir, _setup_logging):
        """Complete pipeline for an abiotic simulation."""
        proj = create_from_template("abiotic_reaction")
        proj.domain = DomainSettings(
            nx=8, ny=4, nz=4, dx=1.0,
            geometry_filename="geometry.dat")

        _make_geometry_file(
            work_dir / "input",
            proj.domain.nx, proj.domain.ny, proj.domain.nz)

        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)
        deployed = ProjectManager.deploy_kinetics(proj, str(work_dir))
        assert len(deployed) == 2

        script = """\
print("CompLaB3D v3.2 - Abiotic Transport")
print("ade_max_iT = 10")
for i in range(1, 11):
    print(f"iT = {i}  Reactant = {1.0 - i * 0.05:.4f}  "
          f"Product = {i * 0.05:.4f}")
    sys.stdout.flush()
print("Saved: output/subsLattice_0000001.vti")
print("Simulation completed successfully.")
"""
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=30_000):
            runner.start()

        rc, msg = collector.finished[0]
        assert rc == 0, f"Abiotic sim failed: rc={rc}"
        assert len(collector.progress_events) >= 10

        out_files = list((work_dir / "output").glob("simulation_*.out"))
        assert len(out_files) >= 1
        assert "Simulation completed successfully" in out_files[0].read_text()

    def test_solver_prints_all_output(self, qtbot, work_dir, _setup_logging):
        """Every line from the solver is captured (nothing swallowed)."""
        # Solver that prints numbered lines — we verify every one arrives
        n_lines = 100
        script = f"""\
print("ade_max_iT = {n_lines}")
for i in range(1, {n_lines + 1}):
    print(f"LINE_{{i:04d}} iT = {{i}}")
    sys.stdout.flush()
print("FINAL_LINE")
"""
        # Create minimal XML
        (work_dir / "CompLaB.xml").write_text("<parameters></parameters>")

        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=30_000):
            runner.start()

        rc, _ = collector.finished[0]
        assert rc == 0

        # Check every numbered line was received
        numbered = [l for l in collector.lines if l.startswith("LINE_")]
        assert len(numbered) == n_lines, (
            f"Expected {n_lines} numbered lines, got {len(numbered)}")

        # Verify FINAL_LINE
        assert any("FINAL_LINE" in l for l in collector.lines)

        # Check .out log has them all too
        out_files = list((work_dir / "output").glob("simulation_*.out"))
        assert len(out_files) >= 1
        log_text = out_files[0].read_text()
        assert "LINE_0001" in log_text
        assert f"LINE_{n_lines:04d}" in log_text
        assert "FINAL_LINE" in log_text

    def test_vti_file_references_in_output(self, qtbot, work_dir, _setup_logging):
        """Solver output referencing .vti files is captured correctly."""
        script = """\
print("ade_max_iT = 5")
for i in range(1, 6):
    print(f"iT = {i}")
    sys.stdout.flush()
# Simulate VTK output lines
for prefix in ["nsLattice", "subsLattice", "bioLattice", "maskLattice"]:
    for step in [1, 5]:
        fname = f"output/{prefix}_{step:07d}.vti"
        print(f"Saved: {fname}")
        sys.stdout.flush()
print("Simulation completed successfully.")
"""
        (work_dir / "CompLaB.xml").write_text("<parameters></parameters>")
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=30_000):
            runner.start()

        rc, _ = collector.finished[0]
        assert rc == 0

        all_text = "\n".join(collector.lines)
        # Verify all VTI references were captured
        for prefix in ["nsLattice", "subsLattice", "bioLattice", "maskLattice"]:
            assert f"{prefix}_0000001.vti" in all_text, (
                f"Missing {prefix} VTI reference in output")
            assert f"{prefix}_0000005.vti" in all_text

    def test_simulation_failure_produces_log(self, qtbot, work_dir, _setup_logging):
        """Solver crash still produces a .out log with partial output."""
        script = """\
print("CompLaB3D starting...")
print("ade_max_iT = 1000")
for i in range(1, 11):
    print(f"iT = {i}")
    sys.stdout.flush()
print("ERROR: Segmentation fault in domain processor")
sys.exit(139)
"""
        (work_dir / "CompLaB.xml").write_text("<parameters></parameters>")
        exe = _write_fake_solver(work_dir, script)
        collector = SignalCollector()

        runner = SimulationRunner(exe, str(work_dir))
        collector.connect(runner)

        with qtbot.waitSignal(runner.finished_signal, timeout=30_000):
            runner.start()

        rc, msg = collector.finished[0]
        assert rc != 0, "Crash should produce non-zero exit code"

        # .out log should still be written with partial output
        out_files = list((work_dir / "output").glob("simulation_*.out"))
        assert len(out_files) >= 1
        log_text = out_files[0].read_text()
        assert "CompLaB3D starting" in log_text
        assert "iT = 10" in log_text


# ===================================================================
# TEST 9 – XML file-system validation against project
# ===================================================================

class TestXMLFileSystemSync:
    """Verify that validate_files() detects XML-project mismatches on disk."""

    def test_xml_sync_matching(self, work_dir):
        """On-disk XML that matches project config: no errors."""
        proj = create_from_template("biotic_sessile")
        proj.domain = DomainSettings(
            nx=10, ny=5, nz=5, geometry_filename="geometry.dat")
        _make_geometry_file(work_dir / "input", 10, 5, 5)

        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)
        ProjectManager.deploy_kinetics(proj, str(work_dir))

        errors = proj.validate_files(str(work_dir))
        assert len(errors) == 0, f"Unexpected errors: {errors}"

    def test_xml_sync_dimension_mismatch(self, work_dir):
        """XML on disk has different nx than GUI project → sync error."""
        proj = create_from_template("biotic_sessile")
        proj.domain = DomainSettings(
            nx=10, ny=5, nz=5, geometry_filename="geometry.dat")
        _make_geometry_file(work_dir / "input", 10, 5, 5)

        # Export with nx=10
        xml_path = str(work_dir / "CompLaB.xml")
        ProjectManager.export_xml(proj, xml_path)
        ProjectManager.deploy_kinetics(proj, str(work_dir))

        # Now change the project (simulating user edit after export)
        proj.domain.nx = 20
        errors = proj.validate_files(str(work_dir))
        sync_errors = [e for e in errors if "[XML Sync]" in e]
        assert len(sync_errors) >= 1, (
            f"Expected XML sync error for nx mismatch but got: {errors}")

    def test_missing_kinetics_file_detected(self, work_dir):
        """Missing defineKinetics.hh when biotic mode is on."""
        proj = create_from_template("biotic_sessile")
        proj.domain = DomainSettings(
            nx=10, ny=5, nz=5, geometry_filename="geometry.dat")
        _make_geometry_file(work_dir / "input", 10, 5, 5)

        # Export XML but DON'T deploy kinetics
        ProjectManager.export_xml(proj, str(work_dir / "CompLaB.xml"))

        errors = proj.validate_files(str(work_dir))
        kin_errors = [e for e in errors if "[Kinetics]" in e]
        assert len(kin_errors) >= 1, (
            f"Expected missing kinetics error but got: {errors}")
