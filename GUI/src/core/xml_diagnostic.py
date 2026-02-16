"""XML & Kinetics crash diagnostic - deep analysis of CompLaB.xml and defineKinetics.

When the solver crashes with an opaque error code (e.g. 0xC0000374 heap corruption),
this module parses the XML, geometry file, and kinetics headers to identify the
most likely root cause and produce a human-readable diagnostic report.

The report is:
  1. Printed to the GUI console
  2. Saved as crash_diagnostic.txt in the output folder
"""

import os
import re
import datetime
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple, Optional


# ── Exit-code → human description ─────────────────────────────────────────
_EXIT_CODE_MAP = {
    # Signed int values (after struct.pack conversion)
    -1073740940: ("Heap Corruption (0xC0000374)",
                  "An array or vector was accessed out of bounds."),
    -1073741819: ("Access Violation (0xC0000005)",
                  "A null or invalid pointer was dereferenced."),
    -1073741571: ("Stack Overflow (0xC00000FD)",
                  "Domain is too large or recursion depth exceeded."),
    -1073741676: ("Integer Divide-by-Zero (0xC0000094)",
                  "Division by zero in the solver."),
    -1073741675: ("Float Divide-by-Zero (0xC0000093)",
                  "Floating-point division by zero in kinetics."),
    -1073741674: ("Float Overflow (0xC0000091)",
                  "Floating-point overflow — rate or concentration is infinite."),
    -6:  ("Abort / Assert Failure (SIGABRT)",
          "An internal assertion failed."),
    -11: ("Segmentation Fault (SIGSEGV)",
          "Memory access error — array out of bounds."),
    134: ("Abort (Linux SIGABRT)",
          "Assertion failure in the solver."),
    139: ("Segfault (Linux SIGSEGV)",
          "Memory access error — array out of bounds."),
    1:   ("Configuration Error",
          "The solver rejected the XML parameters."),
    2:   ("File Not Found",
          "A required input file is missing."),
}


def diagnose_crash(xml_path: str, exit_code: int,
                   kinetics_dir: str = "") -> str:
    """Run a comprehensive diagnostic and return the report as a string.

    Parameters
    ----------
    xml_path : str
        Path to the CompLaB.xml that was fed to the solver.
    exit_code : int
        The process return code (signed int).
    kinetics_dir : str, optional
        Directory containing defineKinetics.hh / defineAbioticKinetics.hh.
        Defaults to one level above the XML file's directory.

    Returns
    -------
    str
        Multi-line diagnostic report.
    """
    errors: List[str] = []
    warnings: List[str] = []
    info: List[str] = []

    # ── 0. Exit-code interpretation ────────────────────────────────────
    code_name, code_desc = _EXIT_CODE_MAP.get(
        exit_code, (f"Unknown Error (code {exit_code})",
                    "Unrecognised exit code."))

    # ── 1. Parse the XML ───────────────────────────────────────────────
    root = None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        info.append(f"XML parsed successfully: {xml_path}")
    except ET.ParseError as exc:
        errors.append(f"[XML] Malformed XML — parser error: {exc}")
    except FileNotFoundError:
        errors.append(f"[XML] File not found: {xml_path}")
    except Exception as exc:
        errors.append(f"[XML] Cannot read file: {exc}")

    if root is None:
        return _build_report(exit_code, code_name, code_desc,
                             errors, warnings, info,
                             xml_path)

    # ── 2. Extract key counts from XML ─────────────────────────────────
    nx = _xml_int(root, ".//domain/nx", 0)
    ny = _xml_int(root, ".//domain/ny", 0)
    nz = _xml_int(root, ".//domain/nz", 0)
    n_subs = _xml_int(root, ".//chemistry/number_of_substrates", 0)
    n_mics = _xml_int(root, ".//microbiology/number_of_microbes", 0)
    biotic = _xml_text(root, ".//simulation_mode/biotic_mode", "false").lower() in (
        "true", "yes", "1", "biotic")
    kinetics_on = _xml_text(root, ".//simulation_mode/enable_kinetics", "false").lower() in (
        "true", "yes", "1")
    abiotic_kinetics_on = _xml_text(
        root, ".//simulation_mode/enable_abiotic_kinetics", "false").lower() in (
        "true", "yes", "1")

    info.append(f"Domain: nx={nx}, ny={ny}, nz={nz}  (total={nx*ny*nz})")
    info.append(f"Substrates: {n_subs}")
    info.append(f"Microbes: {n_mics}")
    info.append(f"Biotic mode: {biotic}, kinetics: {kinetics_on}, "
                f"abiotic kinetics: {abiotic_kinetics_on}")

    # ── 3. Geometry file size check ────────────────────────────────────
    geom_fname = _xml_text(root, ".//domain/filename", "geometry.dat")
    input_path = _xml_text(root, ".//path/input_path", "input")
    xml_dir = str(Path(xml_path).parent)

    # Try several possible locations for the geometry file
    geom_candidates = [
        os.path.join(xml_dir, input_path, geom_fname),
        os.path.join(xml_dir, geom_fname),
        os.path.join(input_path, geom_fname),
    ]
    geom_file = None
    for c in geom_candidates:
        if os.path.isfile(c):
            geom_file = c
            break

    expected_size = nx * ny * nz
    if geom_file:
        actual_bytes = os.path.getsize(geom_file)
        # Geometry is stored as raw bytes (1 byte per voxel)
        if actual_bytes == expected_size:
            info.append(f"Geometry file OK: {actual_bytes} bytes = "
                        f"nx*ny*nz ({nx}*{ny}*{nz}={expected_size})")
        else:
            errors.append(
                f"[Geometry] Size MISMATCH: file has {actual_bytes} bytes "
                f"but nx*ny*nz = {nx}*{ny}*{nz} = {expected_size}.\n"
                f"    >> This is the most common cause of heap corruption!\n"
                f"    >> Fix: change nx/ny/nz in XML to match the geometry file,\n"
                f"    >>       or regenerate geometry.dat with the correct dimensions.\n"
                f"    File: {geom_file}")
    else:
        if expected_size > 0:
            warnings.append(
                f"[Geometry] File not found: {geom_fname}\n"
                f"    Searched: {', '.join(geom_candidates)}")

    # ── 4. Substrate / microbe parameter consistency ───────────────────
    chem = root.find("chemistry")
    if chem is not None:
        for i in range(n_subs):
            s_el = chem.find(f"substrate{i}")
            if s_el is None:
                errors.append(
                    f"[XML] <substrate{i}> element is missing but "
                    f"number_of_substrates={n_subs}.")

    mb_el = root.find("microbiology")
    if mb_el is not None and biotic:
        for i in range(n_mics):
            m_el = mb_el.find(f"microbe{i}")
            if m_el is None:
                errors.append(
                    f"[XML] <microbe{i}> element is missing but "
                    f"number_of_microbes={n_mics}.")
                continue

            mic_name = _xml_text(m_el, "name_of_microbes", f"microbe{i}")
            rxn_type = _xml_text(m_el, "reaction_type", "").lower()

            # Half-saturation constants count
            ks_text = _xml_text(m_el, "half_saturation_constants", "").strip()
            if ks_text:
                ks_count = len(ks_text.split())
                if ks_count != n_subs:
                    errors.append(
                        f"[Kinetics] Microbe '{mic_name}': "
                        f"half_saturation_constants has {ks_count} value(s) "
                        f"but there are {n_subs} substrate(s).\n"
                        f"    >> The solver allocates arrays of size {n_subs}. "
                        f"Reading {ks_count} values causes heap corruption.\n"
                        f"    >> Fix: provide exactly {n_subs} space-separated "
                        f"Ks values.")

            # Maximum uptake flux count
            vmax_text = _xml_text(m_el, "maximum_uptake_flux", "").strip()
            if vmax_text:
                vmax_count = len(vmax_text.split())
                if vmax_count != n_subs:
                    errors.append(
                        f"[Kinetics] Microbe '{mic_name}': "
                        f"maximum_uptake_flux has {vmax_count} value(s) "
                        f"but there are {n_subs} substrate(s).\n"
                        f"    >> Fix: provide exactly {n_subs} space-separated "
                        f"Vmax values.")

            # Material numbers vs initial densities
            solver = _xml_text(m_el, "solver_type", "").upper()
            if solver in ("CA", "CELLULAR AUTOMATA"):
                mat_el = root.find(".//domain/material_numbers")
                if mat_el is not None:
                    mat_text = _xml_text(mat_el, f"microbe{i}", "").strip()
                    dens_text = _xml_text(m_el, "initial_densities", "").strip()
                    if mat_text and dens_text:
                        mat_count = len(mat_text.split())
                        dens_count = len(dens_text.split())
                        if mat_count != dens_count:
                            errors.append(
                                f"[Kinetics] Microbe '{mic_name}': "
                                f"material_number has {mat_count} value(s) "
                                f"but initial_densities has {dens_count}.\n"
                                f"    >> These must match. Fix: use the same "
                                f"count for both.")

    # ── 5. Kinetics mode vs data consistency ───────────────────────────
    if kinetics_on and n_subs == 0:
        errors.append(
            "[Kinetics] enable_kinetics=true but number_of_substrates=0.\n"
            "    >> The solver will create zero-size substrate arrays and "
            "kinetics will access C[0] → crash.\n"
            "    >> Fix: add at least one substrate, or set "
            "enable_kinetics=false.")

    if kinetics_on and not biotic:
        errors.append(
            "[Kinetics] enable_kinetics=true but biotic_mode=false.\n"
            "    >> Biotic kinetics (defineKinetics.hh) requires microbes.\n"
            "    >> Fix: set biotic_mode=true, or use "
            "enable_abiotic_kinetics instead.")

    if kinetics_on and biotic and n_mics == 0:
        errors.append(
            "[Kinetics] enable_kinetics=true and biotic_mode=true but "
            "number_of_microbes=0.\n"
            "    >> The kinetics function reads B[0] from an empty vector → crash.\n"
            "    >> Fix: add at least one microbe, or disable kinetics.")

    if abiotic_kinetics_on and n_subs == 0:
        errors.append(
            "[Kinetics] enable_abiotic_kinetics=true but "
            "number_of_substrates=0.\n"
            "    >> defineAbioticRxnKinetics reads C[i] from an empty "
            "vector → crash.\n"
            "    >> Fix: add substrates or disable abiotic kinetics.")

    # ── 6. Analyse defineKinetics.hh for array-index mismatches ────────
    if not kinetics_dir:
        kinetics_dir = str(Path(xml_dir).parent)

    _check_kinetics_header(
        kinetics_dir, "defineKinetics.hh",
        n_subs, n_mics, "biotic", kinetics_on,
        errors, warnings, info)

    _check_kinetics_header(
        kinetics_dir, "defineAbioticKinetics.hh",
        n_subs, n_mics, "abiotic", abiotic_kinetics_on,
        errors, warnings, info)

    # ── 7. Domain sanity ───────────────────────────────────────────────
    if nx < 3:
        errors.append(
            f"[Domain] nx={nx} is too small (minimum 3: "
            f"inlet + at least 1 cell + outlet).")
    if ny < 1 or nz < 1:
        errors.append(
            f"[Domain] ny={ny}, nz={nz} must be >= 1.")

    tau = _xml_float(root, ".//tau", 0.0)
    if tau > 0 and tau <= 0.5:
        errors.append(
            f"[Solver] tau={tau} is <= 0.5 → LBM is unstable.\n"
            "    >> Fix: set tau > 0.5 (typical range 0.51 – 1.5).")

    # ── 8. Missing required sections ───────────────────────────────────
    required_sections = ["path", "simulation_mode", "LB_numerics", "IO"]
    for sect in required_sections:
        if root.find(sect) is None:
            errors.append(
                f"[XML] Required section <{sect}> is missing from CompLaB.xml.")

    if n_subs > 0 and root.find("chemistry") is None:
        errors.append("[XML] Substrates referenced but <chemistry> section missing.")

    if biotic and root.find("microbiology") is None:
        errors.append("[XML] Biotic mode but <microbiology> section missing.")

    # ── 9. Boundary condition checks ───────────────────────────────────
    if chem is not None:
        all_neumann_zero = True
        for i in range(n_subs):
            s_el = chem.find(f"substrate{i}")
            if s_el is None:
                continue
            lbt = _xml_text(s_el, "left_boundary_type", "").strip()
            rbt = _xml_text(s_el, "right_boundary_type", "").strip()
            lbc = _xml_float(s_el, "left_boundary_condition", 0.0)
            rbc = _xml_float(s_el, "right_boundary_condition", 0.0)
            ic = _xml_float(s_el, "initial_concentration", 0.0)
            if lbt == "Dirichlet" or rbt == "Dirichlet" or ic != 0.0:
                all_neumann_zero = False
        if all_neumann_zero and n_subs > 0:
            warnings.append(
                "[Boundary] All substrates have Neumann BCs and zero initial "
                "concentration — no substrate source exists.\n"
                "    >> The simulation will have zero concentrations everywhere.")

    return _build_report(exit_code, code_name, code_desc,
                         errors, warnings, info, xml_path)


# ── Internal helpers ──────────────────────────────────────────────────────

def _xml_text(parent: ET.Element, path: str, default: str) -> str:
    el = parent.find(path)
    if el is not None and el.text:
        return el.text.strip()
    return default


def _xml_int(parent: ET.Element, path: str, default: int) -> int:
    try:
        return int(_xml_text(parent, path, str(default)))
    except ValueError:
        return default


def _xml_float(parent: ET.Element, path: str, default: float) -> float:
    try:
        return float(_xml_text(parent, path, str(default)))
    except ValueError:
        return default


def _check_kinetics_header(
        kinetics_dir: str,
        filename: str,
        n_subs: int,
        n_mics: int,
        kind: str,
        enabled: bool,
        errors: List[str],
        warnings: List[str],
        info: List[str]):
    """Scan a kinetics .hh file for array-index accesses that exceed XML counts."""
    header_path = os.path.join(kinetics_dir, filename)
    if not os.path.isfile(header_path):
        # Also try one level deeper (repo root often has these)
        alt = os.path.join(kinetics_dir, "..", filename)
        if os.path.isfile(alt):
            header_path = alt
        else:
            if enabled:
                warnings.append(
                    f"[Kinetics] {filename} not found at {kinetics_dir}.\n"
                    f"    Cannot verify array-index safety.")
            return

    try:
        with open(header_path, "r", errors="replace") as f:
            source = f.read()
    except Exception as exc:
        warnings.append(f"[Kinetics] Cannot read {filename}: {exc}")
        return

    info.append(f"Analysing {filename} ({len(source)} bytes)")

    # Strip block comments and line comments for reliable matching
    source_clean = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)
    source_clean = re.sub(r'//.*', '', source_clean)

    # Find C[n] and subsR[n] accesses (substrate array)
    c_indices = set()
    for m in re.finditer(r'\bC\s*\[\s*(\d+)\s*\]', source_clean):
        c_indices.add(int(m.group(1)))
    for m in re.finditer(r'\bsubsR\s*\[\s*(\d+)\s*\]', source_clean):
        c_indices.add(int(m.group(1)))

    if c_indices and n_subs > 0:
        max_c_idx = max(c_indices)
        if max_c_idx >= n_subs:
            errors.append(
                f"[defineKinetics] {filename} accesses C[{max_c_idx}] / "
                f"subsR[{max_c_idx}] but XML has only {n_subs} substrate(s) "
                f"(valid indices: 0..{n_subs-1}).\n"
                f"    >> This out-of-bounds access causes heap corruption!\n"
                f"    >> Fix: add more substrates in the XML, or edit {filename}\n"
                f"    >>       to only access C[0]..C[{n_subs-1}].\n"
                f"    Indices found in code: {sorted(c_indices)}")
        else:
            info.append(
                f"{filename}: substrate indices {sorted(c_indices)} — "
                f"all within 0..{n_subs-1} OK")

    # Find B[n] and bioR[n] accesses (biomass array)
    b_indices = set()
    for m in re.finditer(r'\bB\s*\[\s*(\d+)\s*\]', source_clean):
        b_indices.add(int(m.group(1)))
    for m in re.finditer(r'\bbioR\s*\[\s*(\d+)\s*\]', source_clean):
        b_indices.add(int(m.group(1)))

    if b_indices and n_mics > 0:
        max_b_idx = max(b_indices)
        if max_b_idx >= n_mics:
            errors.append(
                f"[defineKinetics] {filename} accesses B[{max_b_idx}] / "
                f"bioR[{max_b_idx}] but XML has only {n_mics} microbe(s) "
                f"(valid indices: 0..{n_mics-1}).\n"
                f"    >> This out-of-bounds access causes heap corruption!\n"
                f"    >> Fix: add more microbes in the XML, or edit {filename}\n"
                f"    >>       to only access B[0]..B[{n_mics-1}].\n"
                f"    Indices found in code: {sorted(b_indices)}")
        else:
            info.append(
                f"{filename}: biomass indices {sorted(b_indices)} — "
                f"all within 0..{n_mics-1} OK")

    # Check for .size() guards (good practice)
    has_size_guard = bool(re.search(
        r'(?:C|subsR|B|bioR)\s*\.\s*size\s*\(\s*\)', source_clean))
    if has_size_guard:
        info.append(f"{filename}: uses .size() bounds checks (good)")
    elif c_indices or b_indices:
        warnings.append(
            f"[defineKinetics] {filename} accesses arrays by hard-coded index "
            f"without .size() guards.\n"
            f"    >> If the XML substrate/microbe count is less than expected, "
            f"it will crash.\n"
            f"    >> Suggestion: add  if (C.size() > idx)  checks.")


def _build_report(exit_code: int, code_name: str, code_desc: str,
                  errors: List[str], warnings: List[str],
                  info: List[str], xml_path: str) -> str:
    """Format the final diagnostic report."""
    lines = []
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines.append("=" * 72)
    lines.append("  CompLaB CRASH DIAGNOSTIC REPORT")
    lines.append(f"  Generated: {ts}")
    lines.append("=" * 72)
    lines.append("")
    lines.append(f"Exit code : {exit_code}")
    lines.append(f"Error type: {code_name}")
    lines.append(f"Reason    : {code_desc}")
    lines.append(f"XML file  : {xml_path}")
    lines.append("")

    if errors:
        lines.append("-" * 72)
        lines.append(f"  ERRORS DETECTED: {len(errors)}")
        lines.append("-" * 72)
        for i, e in enumerate(errors, 1):
            lines.append(f"  {i}. {e}")
            lines.append("")
    else:
        lines.append("-" * 72)
        lines.append("  No configuration errors detected.")
        lines.append("  The crash may be caused by:")
        lines.append("    - A bug in the C++ solver")
        lines.append("    - Numerical instability during iteration")
        lines.append("    - Insufficient memory for the domain size")
        lines.append("-" * 72)
        lines.append("")

    if warnings:
        lines.append("-" * 72)
        lines.append(f"  WARNINGS: {len(warnings)}")
        lines.append("-" * 72)
        for i, w in enumerate(warnings, 1):
            lines.append(f"  {i}. {w}")
            lines.append("")

    if info:
        lines.append("-" * 72)
        lines.append("  DIAGNOSTIC INFO")
        lines.append("-" * 72)
        for item in info:
            lines.append(f"  - {item}")
        lines.append("")

    # Suggested fix checklist
    lines.append("-" * 72)
    lines.append("  HOW TO FIX")
    lines.append("-" * 72)
    if errors:
        lines.append("  Fix the errors above, then:")
    lines.append("  1. Run 'Validate Configuration' in the Run panel")
    lines.append("  2. Verify geometry file has exactly nx * ny * nz bytes")
    lines.append("  3. Check that defineKinetics.hh array indices match substrate count")
    lines.append("  4. Check half_saturation_constants / maximum_uptake_flux counts")
    lines.append("  5. Re-export CompLaB.xml and run again")
    lines.append("")
    lines.append("=" * 72)

    return "\n".join(lines)


def save_diagnostic_report(report: str, output_dir: str) -> str:
    """Save the diagnostic report to the output folder.

    Returns the path of the saved file, or empty string on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"crash_diagnostic_{ts}.txt"
    filepath = os.path.join(output_dir, filename)
    try:
        with open(filepath, "w") as f:
            f.write(report)
        return filepath
    except Exception:
        return ""
