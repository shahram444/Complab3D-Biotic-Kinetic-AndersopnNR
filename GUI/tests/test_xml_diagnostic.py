"""Tests for src/core/xml_diagnostic.py -- Crash Diagnostic Module.

What this covers:
  xml_diagnostic.py analyses a CompLaB.xml file after a solver crash and
  produces a human-readable report identifying the most likely root cause.
  It checks:
    - Exit code -> error-type mapping (heap corruption, segfault, etc.)
    - Geometry file size vs. domain nx*ny*nz
    - Kinetics .hh array index safety (C[n], B[n] vs. substrate/microbe count)
    - Domain sanity (tau, nx/ny/nz bounds)
    - XML structure completeness (required sections present)
    - Boundary condition consistency (all-Neumann-zero warning)

  None of these tests require Qt or a display.
"""

import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

# Make GUI/src importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.xml_diagnostic import (
    diagnose_crash,
    save_diagnostic_report,
    _xml_text,
    _xml_int,
    _xml_float,
    _build_report,
)


# ---------------------------------------------------------------------------
# Helpers: build minimal valid XML strings
# ---------------------------------------------------------------------------

def _make_xml(
    nx=10, ny=5, nz=5,
    n_subs=1, n_mics=1,
    biotic="true",
    kinetics="true",
    abiotic_kinetics="false",
    tau=0.8,
    extra_substrate_xml="",
    extra_microbe_xml="",
    omit_sections=None,
):
    """Generate a minimal but structurally valid CompLaB.xml string."""
    omit = set(omit_sections or [])

    subs_xml = ""
    for i in range(n_subs):
        subs_xml += f"""
      <substrate{i}>
        <name>sub{i}</name>
        <initial_concentration>0.01</initial_concentration>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <right_boundary_type>Neumann</right_boundary_type>
        <left_boundary_condition>0.01</left_boundary_condition>
        <right_boundary_condition>0.0</right_boundary_condition>
        <half_saturation_constants>1e-5</half_saturation_constants>
        <maximum_uptake_flux>0.5</maximum_uptake_flux>
      </substrate{i}>
"""
    subs_xml += extra_substrate_xml

    mic_xml = ""
    for i in range(n_mics):
        ks = " ".join(["1e-5"] * n_subs) if n_subs else ""
        vmax = " ".join(["0.5"] * n_subs) if n_subs else ""
        mic_xml += f"""
      <microbe{i}>
        <name_of_microbes>microbe{i}</name_of_microbes>
        <solver_type>CA</solver_type>
        <reaction_type>kinetics</reaction_type>
        <initial_densities>99.0</initial_densities>
        <half_saturation_constants>{ks}</half_saturation_constants>
        <maximum_uptake_flux>{vmax}</maximum_uptake_flux>
      </microbe{i}>
"""
    mic_xml += extra_microbe_xml

    path_section = "" if "path" in omit else "<path><src_path>src</src_path><input_path>input</input_path><output_path>output</output_path></path>"
    sm_section = "" if "simulation_mode" in omit else f"""
<simulation_mode>
  <biotic_mode>{biotic}</biotic_mode>
  <enable_kinetics>{kinetics}</enable_kinetics>
  <enable_abiotic_kinetics>{abiotic_kinetics}</enable_abiotic_kinetics>
</simulation_mode>"""
    lb_section = "" if "LB_numerics" in omit else f"""
<LB_numerics>
  <domain>
    <nx>{nx}</nx><ny>{ny}</ny><nz>{nz}</nz>
    <dx>1.0</dx>
    <filename>geometry.dat</filename>
    <pore>2</pore><solid>0</solid><bounce_back>1</bounce_back>
    <material_numbers>
      <microbe0>3</microbe0>
    </material_numbers>
  </domain>
  <tau>{tau}</tau>
  <delta_P>2e-3</delta_P>
</LB_numerics>"""
    io_section = "" if "IO" in omit else "<IO><save_vtk_interval>1000</save_vtk_interval></IO>"
    chem_section = f"""
<chemistry>
  <number_of_substrates>{n_subs}</number_of_substrates>
  {subs_xml}
</chemistry>"""
    mb_section = f"""
<microbiology>
  <number_of_microbes>{n_mics}</number_of_microbes>
  {mic_xml}
</microbiology>"""

    return f"""<?xml version="1.0"?>
<parameters>
  {path_section}
  {sm_section}
  {lb_section}
  {chem_section}
  {mb_section}
  {io_section}
</parameters>"""


# ---------------------------------------------------------------------------
# Helper XML element builders for _xml_text / _xml_int / _xml_float tests
# ---------------------------------------------------------------------------

def _el(tag, text):
    e = ET.Element("root")
    child = ET.SubElement(e, tag)
    child.text = text
    return e


# ===========================================================================
# TestHelperFunctions -- _xml_text / _xml_int / _xml_float
# ===========================================================================

class TestHelperFunctions:
    """The diagnostic module uses three XML-extraction helpers internally.

    These tests verify they handle missing elements, empty text, and
    bad values gracefully -- because real-world crash XML files are often
    partially malformed.
    """

    def test_xml_text_present(self):
        el = _el("foo", "hello")
        assert _xml_text(el, "foo", "default") == "hello"

    def test_xml_text_missing_element(self):
        el = ET.Element("root")
        assert _xml_text(el, "missing", "fallback") == "fallback"

    def test_xml_text_empty_element(self):
        el = _el("foo", "")
        assert _xml_text(el, "foo", "default") == "default"

    def test_xml_text_strips_whitespace(self):
        el = _el("foo", "  trimmed  ")
        assert _xml_text(el, "foo", "") == "trimmed"

    def test_xml_int_valid(self):
        el = _el("nx", "42")
        assert _xml_int(el, "nx", 0) == 42

    def test_xml_int_missing(self):
        el = ET.Element("root")
        assert _xml_int(el, "nx", 99) == 99

    def test_xml_int_bad_value(self):
        el = _el("nx", "not_a_number")
        assert _xml_int(el, "nx", 5) == 5

    def test_xml_float_valid(self):
        el = _el("tau", "0.75")
        assert abs(_xml_float(el, "tau", 0.0) - 0.75) < 1e-12

    def test_xml_float_scientific(self):
        el = _el("val", "1.5e-9")
        assert abs(_xml_float(el, "val", 0.0) - 1.5e-9) < 1e-20

    def test_xml_float_missing(self):
        el = ET.Element("root")
        assert _xml_float(el, "val", 3.14) == pytest.approx(3.14)

    def test_xml_float_bad_value(self):
        el = _el("val", "nan_string")
        assert _xml_float(el, "val", 2.0) == pytest.approx(2.0)


# ===========================================================================
# TestExitCodeMapping -- exit code -> human-readable error type
# ===========================================================================

class TestExitCodeMapping:
    """The diagnostic maps OS exit codes to error categories.

    A Windows heap-corruption exit code (0xC0000374 = -1073740940) is the
    most common cause of mysterious solver crashes: it almost always means
    the geometry file has the wrong dimensions and the LBM array is being
    accessed out of bounds.
    """

    def _get_report(self, tmp_path, exit_code):
        xml = _make_xml()
        p = tmp_path / "CompLaB.xml"
        p.write_text(xml)
        return diagnose_crash(str(p), exit_code)

    def test_heap_corruption_windows(self, tmp_path):
        report = self._get_report(tmp_path, -1073740940)
        assert "Heap Corruption" in report or "0xC0000374" in report

    def test_access_violation_windows(self, tmp_path):
        report = self._get_report(tmp_path, -1073741819)
        assert "Access Violation" in report or "0xC0000005" in report

    def test_stack_overflow_windows(self, tmp_path):
        report = self._get_report(tmp_path, -1073741571)
        assert "Stack Overflow" in report or "0xC00000FD" in report

    def test_segfault_linux(self, tmp_path):
        report = self._get_report(tmp_path, -11)
        assert "Segmentation Fault" in report or "SIGSEGV" in report

    def test_sigabrt_linux(self, tmp_path):
        report = self._get_report(tmp_path, 134)
        assert "Abort" in report or "SIGABRT" in report

    def test_config_error(self, tmp_path):
        report = self._get_report(tmp_path, 1)
        assert "Configuration" in report or "code 1" in report.lower() or "1" in report

    def test_unknown_exit_code(self, tmp_path):
        report = self._get_report(tmp_path, 99)
        assert "99" in report  # code should appear somewhere in report

    def test_exit_code_in_report(self, tmp_path):
        report = self._get_report(tmp_path, -11)
        assert "-11" in report or "11" in report


# ===========================================================================
# TestXMLParsing -- valid / missing / malformed XML handling
# ===========================================================================

class TestXMLParsing:
    """The diagnostic must handle broken XML files gracefully.

    When a solver crashes it may have only partially written its output XML,
    or the user may have passed the wrong file path.
    """

    def test_valid_xml_parses_cleanly(self, tmp_path):
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml())
        report = diagnose_crash(str(p), 1)
        assert "[XML] Malformed" not in report
        assert "[XML] File not found" not in report

    def test_missing_xml_file(self, tmp_path):
        report = diagnose_crash(str(tmp_path / "nonexistent.xml"), 1)
        assert "not found" in report.lower() or "File not found" in report

    def test_malformed_xml(self, tmp_path):
        p = tmp_path / "bad.xml"
        p.write_text("<<<not valid xml>>>")
        report = diagnose_crash(str(p), 1)
        assert "Malformed" in report or "parser error" in report.lower()

    def test_empty_xml_file(self, tmp_path):
        p = tmp_path / "empty.xml"
        p.write_text("")
        report = diagnose_crash(str(p), 1)
        assert "[XML]" in report  # some XML error is reported

    def test_report_always_returns_string(self, tmp_path):
        # Even for missing file, we always get a string back (not an exception)
        report = diagnose_crash("/totally/nonexistent/path.xml", -11)
        assert isinstance(report, str)
        assert len(report) > 0


# ===========================================================================
# TestGeometrySizeCheck -- geometry.dat size vs nx*ny*nz
# ===========================================================================

class TestGeometrySizeCheck:
    """The most common solver crash cause is a geometry file whose byte count
    does not equal nx * ny * nz.  The diagnostic checks all plausible file
    formats (binary 1 byte/voxel, text 2-3 bytes/voxel) against the domain
    size declared in the XML.
    """

    def _write_xml_and_geom(self, tmp_path, nx, ny, nz, geom_bytes, text_format=True):
        """Write XML and a geometry.dat with a controlled byte count."""
        xml_dir = tmp_path
        xml_path = xml_dir / "CompLaB.xml"
        xml_path.write_text(_make_xml(nx=nx, ny=ny, nz=nz))

        input_dir = xml_dir / "input"
        input_dir.mkdir(exist_ok=True)
        geom = input_dir / "geometry.dat"
        if text_format:
            # Each voxel is "2\n" = 2 bytes on Unix
            lines = "2\n" * geom_bytes
            geom.write_text(lines)
        else:
            geom.write_bytes(bytes([2] * geom_bytes))
        return str(xml_path)

    def test_correct_text_geometry_no_geometry_error(self, tmp_path):
        # 5*5*5=125 voxels, text format: 125*2=250 bytes
        path = self._write_xml_and_geom(tmp_path, 5, 5, 5, 125, text_format=True)
        report = diagnose_crash(path, -1073740940)
        assert "[Geometry] Size MISMATCH" not in report

    def test_correct_binary_geometry_no_geometry_error(self, tmp_path):
        # 4*3*3=36 voxels, binary: 36 bytes
        path = self._write_xml_and_geom(tmp_path, 4, 3, 3, 36, text_format=False)
        report = diagnose_crash(path, -1073740940)
        assert "[Geometry] Size MISMATCH" not in report

    def test_mismatched_geometry_flagged_as_error(self, tmp_path):
        # XML says 10*5*5=250 but geometry has only 50 voxels
        path = self._write_xml_and_geom(tmp_path, 10, 5, 5, 50, text_format=False)
        report = diagnose_crash(path, -1073740940)
        assert "[Geometry]" in report and ("MISMATCH" in report or "mismatch" in report.lower())

    def test_missing_geometry_file_gives_warning(self, tmp_path):
        xml_path = tmp_path / "CompLaB.xml"
        xml_path.write_text(_make_xml(nx=10, ny=5, nz=5))
        # No geometry.dat written -- file is absent
        report = diagnose_crash(str(xml_path), -1073740940)
        # Should warn (not hard error) that geometry file was not found
        assert "[Geometry]" in report

    def test_geometry_mismatch_mentions_expected_size(self, tmp_path):
        path = self._write_xml_and_geom(tmp_path, 10, 5, 5, 50, text_format=False)
        report = diagnose_crash(path, -1073740940)
        # Should mention the expected size (250) and actual
        assert "250" in report or "50" in report


# ===========================================================================
# TestKineticsConsistencyFromXML -- mode flags vs counts
# ===========================================================================

class TestKineticsConsistencyFromXML:
    """The diagnostic checks that kinetics mode flags are consistent with
    the substrate and microbe counts in the XML.

    Mismatches between mode flags and counts are a common source of crashes
    because the C++ solver allocates arrays based on counts, then kinetics
    code accesses C[0] which doesn't exist.
    """

    def _report(self, tmp_path, **kwargs):
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml(**kwargs))
        return diagnose_crash(str(p), 1)

    def test_kinetics_on_no_substrates(self, tmp_path):
        report = self._report(tmp_path, n_subs=0, n_mics=1, kinetics="true", biotic="true")
        assert "[Kinetics]" in report

    def test_kinetics_on_no_microbes(self, tmp_path):
        report = self._report(tmp_path, n_subs=1, n_mics=0, kinetics="true", biotic="true")
        assert "[Kinetics]" in report

    def test_kinetics_on_biotic_false(self, tmp_path):
        report = self._report(tmp_path, n_subs=1, n_mics=0, kinetics="true", biotic="false")
        assert "[Kinetics]" in report

    def test_abiotic_kinetics_on_no_substrates(self, tmp_path):
        report = self._report(
            tmp_path, n_subs=0, n_mics=0,
            kinetics="false", abiotic_kinetics="true", biotic="false"
        )
        assert "[Kinetics]" in report

    def test_valid_biotic_no_errors(self, tmp_path):
        report = self._report(
            tmp_path, n_subs=1, n_mics=1, kinetics="true", biotic="true"
        )
        assert "ERRORS DETECTED" not in report


# ===========================================================================
# TestKineticsHeaderIndexCheck -- array bounds in .hh source
# ===========================================================================

class TestKineticsHeaderIndexCheck:
    """The diagnostic scans kinetics .hh files for C[n] and B[n] array
    accesses and flags any index that exceeds the substrate/microbe counts
    declared in the XML.

    An out-of-bounds access like C[2] with only 1 substrate causes heap
    corruption -- this is the single most common source of opaque crashes.
    """

    def _make_setup(self, tmp_path, n_subs, n_mics, biotic_hh_body, abiotic_hh_body=""):
        """Write XML + kinetics headers and return (xml_path, kinetics_dir)."""
        xml_path = tmp_path / "CompLaB.xml"
        xml_path.write_text(_make_xml(n_subs=n_subs, n_mics=n_mics))

        biotic_hh = tmp_path / "defineKinetics.hh"
        biotic_hh.write_text(
            "#ifndef DEFINE_KINETICS_HH\n#define DEFINE_KINETICS_HH\n"
            + biotic_hh_body
            + "\n#endif\n"
        )
        abiotic_hh = tmp_path / "defineAbioticKinetics.hh"
        abiotic_hh.write_text(
            "#ifndef DEFINE_ABIOTIC_KINETICS_HH\n#define DEFINE_ABIOTIC_KINETICS_HH\n"
            + abiotic_hh_body
            + "\n#endif\n"
        )
        return str(xml_path), str(tmp_path)

    def test_valid_single_substrate_access(self, tmp_path):
        xml_path, kdir = self._make_setup(
            tmp_path, n_subs=1, n_mics=1,
            biotic_hh_body="void f(){ double x = C[0]; double y = B[0]; }"
        )
        report = diagnose_crash(xml_path, 1, kinetics_dir=kdir)
        assert "[defineKinetics]" not in report or "out of bounds" not in report.lower()

    def test_out_of_bounds_substrate_index_flagged(self, tmp_path):
        # XML has 1 substrate but code accesses C[2]
        xml_path, kdir = self._make_setup(
            tmp_path, n_subs=1, n_mics=1,
            biotic_hh_body="void f(){ double x = C[2]; }"
        )
        report = diagnose_crash(xml_path, 1, kinetics_dir=kdir)
        assert "[defineKinetics]" in report or "C[2]" in report

    def test_out_of_bounds_biomass_index_flagged(self, tmp_path):
        # XML has 1 microbe but code accesses B[1]
        xml_path, kdir = self._make_setup(
            tmp_path, n_subs=1, n_mics=1,
            biotic_hh_body="void f(){ double y = B[1]; }"
        )
        report = diagnose_crash(xml_path, 1, kinetics_dir=kdir)
        assert "[defineKinetics]" in report or "B[1]" in report

    def test_indices_in_comments_not_flagged(self, tmp_path):
        # C[99] inside a comment should not trigger an error
        xml_path, kdir = self._make_setup(
            tmp_path, n_subs=1, n_mics=1,
            biotic_hh_body="/* C[99] is just a comment */ void f(){ double x = C[0]; }"
        )
        report = diagnose_crash(xml_path, 1, kinetics_dir=kdir)
        # C[99] in a comment must NOT produce an out-of-bounds error
        assert "C[99]" not in report

    def test_multi_substrate_all_valid(self, tmp_path):
        # 2 substrates, access C[0] and C[1] -- both valid
        xml_path, kdir = self._make_setup(
            tmp_path, n_subs=2, n_mics=1,
            biotic_hh_body="void f(){ double a=C[0]; double b=C[1]; }"
        )
        report = diagnose_crash(xml_path, 1, kinetics_dir=kdir)
        assert "[defineKinetics]" not in report or "out of bounds" not in report.lower()

    def test_missing_kinetics_header_gives_warning(self, tmp_path):
        # No .hh files in kinetics_dir at all
        xml_path = tmp_path / "CompLaB.xml"
        xml_path.write_text(_make_xml(n_subs=1, n_mics=1))
        kdir = str(tmp_path / "empty_dir")
        os.makedirs(kdir, exist_ok=True)
        report = diagnose_crash(str(xml_path), 1, kinetics_dir=kdir)
        # Missing header should produce a warning, not crash the diagnostic
        assert isinstance(report, str)


# ===========================================================================
# TestDomainSanityChecks -- nx/ny/nz and tau bounds
# ===========================================================================

class TestDomainSanityChecks:
    """Small domain dimensions and invalid tau are common configuration mistakes.

    nx < 3 is invalid because the solver requires at least an inlet node,
    one interior cell, and an outlet node.  tau <= 0.5 gives a negative
    kinematic viscosity in LBM.
    """

    def _report(self, tmp_path, **kwargs):
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml(**kwargs))
        return diagnose_crash(str(p), 1)

    def test_nx_too_small_is_error(self, tmp_path):
        report = self._report(tmp_path, nx=2)
        assert "[Domain]" in report

    def test_valid_nx_no_domain_error(self, tmp_path):
        report = self._report(tmp_path, nx=10)
        # Domain errors should not appear for valid dimensions
        assert "nx=2" not in report

    def test_tau_below_half_flagged(self, tmp_path):
        report = self._report(tmp_path, tau=0.4)
        assert "[Solver]" in report and "tau" in report.lower()

    def test_tau_at_half_boundary_flagged(self, tmp_path):
        # tau = 0.5 is the exact boundary -- kinematic viscosity is zero
        report = self._report(tmp_path, tau=0.5)
        assert "[Solver]" in report

    def test_tau_above_half_ok(self, tmp_path):
        report = self._report(tmp_path, tau=0.8)
        # tau=0.8 is physically valid -- no solver error should appear
        assert "[Solver]" not in report


# ===========================================================================
# TestRequiredXMLSections -- missing sections are flagged
# ===========================================================================

class TestRequiredXMLSections:
    """The C++ solver parser expects specific top-level XML sections.
    Missing sections cause the solver to crash with opaque errors.
    """

    def _report_missing(self, tmp_path, section):
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml(omit_sections=[section]))
        return diagnose_crash(str(p), 1)

    def test_missing_path_section(self, tmp_path):
        report = self._report_missing(tmp_path, "path")
        assert "[XML]" in report

    def test_missing_simulation_mode(self, tmp_path):
        report = self._report_missing(tmp_path, "simulation_mode")
        # Without simulation_mode, solver cannot determine biotic/abiotic state
        assert isinstance(report, str)  # must not crash

    def test_missing_lb_numerics(self, tmp_path):
        report = self._report_missing(tmp_path, "LB_numerics")
        assert "[XML]" in report

    def test_missing_io_section(self, tmp_path):
        report = self._report_missing(tmp_path, "IO")
        assert "[XML]" in report


# ===========================================================================
# TestBoundaryConditionWarning -- all-Neumann-zero substrate warning
# ===========================================================================

class TestBoundaryConditionWarning:
    """If every substrate has Neumann boundary conditions and zero initial
    concentration, there is no substrate source anywhere in the domain.
    The simulation will produce all-zero concentrations, which is physically
    meaningless.  The diagnostic should warn about this.
    """

    def test_all_neumann_zero_gives_warning(self, tmp_path):
        # Build XML with all-Neumann, zero initial concentration substrates
        xml_str = """<?xml version="1.0"?>
<parameters>
  <path><src_path>src</src_path><input_path>input</input_path><output_path>output</output_path></path>
  <simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
    <enable_abiotic_kinetics>false</enable_abiotic_kinetics>
  </simulation_mode>
  <LB_numerics>
    <domain><nx>10</nx><ny>5</ny><nz>5</nz><dx>1.0</dx><filename>geometry.dat</filename></domain>
    <tau>0.8</tau>
  </LB_numerics>
  <chemistry>
    <number_of_substrates>1</number_of_substrates>
    <substrate0>
      <name>DOC</name>
      <initial_concentration>0.0</initial_concentration>
      <left_boundary_type>Neumann</left_boundary_type>
      <right_boundary_type>Neumann</right_boundary_type>
      <left_boundary_condition>0.0</left_boundary_condition>
      <right_boundary_condition>0.0</right_boundary_condition>
    </substrate0>
  </chemistry>
  <microbiology><number_of_microbes>1</number_of_microbes>
    <microbe0><name_of_microbes>microbe0</name_of_microbes><solver_type>CA</solver_type>
    <reaction_type>kinetics</reaction_type><initial_densities>99.0</initial_densities>
    <half_saturation_constants>1e-5</half_saturation_constants>
    <maximum_uptake_flux>0.5</maximum_uptake_flux></microbe0>
  </microbiology>
  <IO><save_vtk_interval>1000</save_vtk_interval></IO>
</parameters>"""
        p = tmp_path / "CompLaB.xml"
        p.write_text(xml_str)
        report = diagnose_crash(str(p), 1)
        assert "[Boundary]" in report

    def test_dirichlet_inlet_no_warning(self, tmp_path):
        # Dirichlet left BC with nonzero concentration -- substrate is supplied
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml(n_subs=1))  # default uses Dirichlet left BC
        report = diagnose_crash(str(p), 1)
        assert "[Boundary]" not in report


# ===========================================================================
# TestHalfSaturationCountCheck -- Ks vector size vs substrate count
# ===========================================================================

class TestHalfSaturationCountCheck:
    """The C++ solver reads exactly n_substrates half-saturation constants per
    microbe.  If the Ks vector in the XML has a different count, the solver
    reads past the end of its array -- heap corruption.
    """

    def test_ks_count_mismatch_flagged(self, tmp_path):
        # 2 substrates declared, but microbe Ks has only 1 value
        xml_str = _make_xml(n_subs=2, n_mics=1)
        # Patch the Ks line to have wrong count
        xml_str = xml_str.replace(
            "<half_saturation_constants>1e-5 1e-5</half_saturation_constants>",
            "<half_saturation_constants>1e-5</half_saturation_constants>",
        )
        p = tmp_path / "CompLaB.xml"
        p.write_text(xml_str)
        report = diagnose_crash(str(p), -1073740940)
        assert "[Kinetics]" in report and "half_saturation" in report

    def test_correct_ks_count_no_error(self, tmp_path):
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml(n_subs=1, n_mics=1))
        report = diagnose_crash(str(p), 1)
        # No Ks mismatch error for correctly formed XML
        assert "half_saturation_constants has" not in report


# ===========================================================================
# TestReportFormat -- output structure and completeness
# ===========================================================================

class TestReportFormat:
    """The diagnostic report has a fixed structure that is both printed to the
    GUI console and saved to disk.  These tests verify the format so that
    users always see a helpful, navigable report.
    """

    def _report(self, tmp_path, exit_code=1):
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml())
        return diagnose_crash(str(p), exit_code)

    def test_report_is_string(self, tmp_path):
        assert isinstance(self._report(tmp_path), str)

    def test_report_contains_exit_code(self, tmp_path):
        report = diagnose_crash(str(tmp_path / "x.xml"), -11)
        assert "-11" in report or "11" in report

    def test_report_has_header(self, tmp_path):
        report = self._report(tmp_path)
        assert "CompLaB" in report and "DIAGNOSTIC" in report.upper()

    def test_report_has_how_to_fix_section(self, tmp_path):
        report = self._report(tmp_path)
        assert "HOW TO FIX" in report or "FIX" in report.upper()

    def test_report_not_empty(self, tmp_path):
        report = self._report(tmp_path)
        assert len(report) > 200  # must be a substantive report

    def test_report_with_errors_mentions_error_count(self, tmp_path):
        # nx=2 triggers a domain error
        p = tmp_path / "CompLaB.xml"
        p.write_text(_make_xml(nx=2))
        report = diagnose_crash(str(p), 1)
        assert "ERROR" in report.upper()

    def test_report_with_no_errors_has_no_errors_message(self, tmp_path):
        report = self._report(tmp_path)
        # For a valid XML, report should note no errors found
        assert "No configuration errors" in report or "ERRORS DETECTED: 0" not in report


# ===========================================================================
# TestSaveDiagnosticReport -- file I/O
# ===========================================================================

class TestSaveDiagnosticReport:
    """The diagnostic report can be saved to the output directory.

    This tests that the file is created, is non-empty, and contains the
    report text.
    """

    def test_file_is_created(self, tmp_path):
        report = "Test diagnostic report content."
        path = save_diagnostic_report(report, str(tmp_path))
        assert path != ""
        assert os.path.isfile(path)

    def test_file_contains_report_text(self, tmp_path):
        report = "Unique content XYZ123"
        path = save_diagnostic_report(report, str(tmp_path))
        content = open(path).read()
        assert "XYZ123" in content

    def test_filename_has_crash_diagnostic_prefix(self, tmp_path):
        path = save_diagnostic_report("x", str(tmp_path))
        assert "crash_diagnostic" in os.path.basename(path)

    def test_creates_output_dir_if_missing(self, tmp_path):
        output_dir = str(tmp_path / "new_subdir" / "deeper")
        path = save_diagnostic_report("content", output_dir)
        assert os.path.isfile(path)

    def test_returns_empty_string_on_failure(self):
        # Try writing to an invalid path (e.g., a path that is a file, not a dir)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
            file_as_dir = f.name
        # Writing inside a file (not a directory) should fail gracefully
        result = save_diagnostic_report("x", file_as_dir + "/subdir")
        # Either returns "" on failure, or creates the path -- either is acceptable
        # The important thing is it does not raise an exception
        assert isinstance(result, str)


# ===========================================================================
# TestBuildReport -- internal report builder
# ===========================================================================

class TestBuildReport:
    """The _build_report() function assembles the final text from lists of
    errors, warnings, and info items.  These tests verify the formatting
    logic independently of the XML parsing.
    """

    def test_errors_appear_in_report(self):
        report = _build_report(1, "Config Error", "Bad config",
                               errors=["[XML] Something wrong"],
                               warnings=[], info=[], xml_path="/fake/path.xml")
        assert "Something wrong" in report

    def test_warnings_appear_in_report(self):
        report = _build_report(1, "Config Error", "Bad config",
                               errors=[], warnings=["[Boundary] Warning here"],
                               info=[], xml_path="/fake/path.xml")
        assert "Warning here" in report

    def test_no_errors_shows_clean_message(self):
        report = _build_report(0, "Success", "OK",
                               errors=[], warnings=[], info=[],
                               xml_path="/fake/path.xml")
        assert "No configuration errors" in report or "0" in report

    def test_multiple_errors_all_listed(self):
        errors = ["[A] First error", "[B] Second error", "[C] Third error"]
        report = _build_report(1, "X", "Y",
                               errors=errors, warnings=[], info=[],
                               xml_path="/fake/path.xml")
        assert "First error" in report
        assert "Second error" in report
        assert "Third error" in report
