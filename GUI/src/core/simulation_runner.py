"""Simulation runner - executes CompLaB3D in a background thread with error diagnostics."""

import os
import re
import time
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal


# Regex patterns for parsing solver output
_RE_ITERATION = re.compile(r"iT\s*=\s*(\d+)")
_RE_ADE_MAX = re.compile(r"ade_max_iT\s*=\s*(\d+)")
_RE_NS_MAX = re.compile(r"ns_max_iT\d?\s*=\s*(\d+)")
_RE_NS_RESIDUAL = re.compile(
    r"NS[:\s].*(?:residual|converge|error)\s*=\s*([0-9]+\.?[0-9]*[eE]?[+-]?\d*)", re.IGNORECASE)
_RE_ADE_RESIDUAL = re.compile(
    r"ADE[:\s].*(?:residual|converge|error)\s*=\s*([0-9]+\.?[0-9]*[eE]?[+-]?\d*)", re.IGNORECASE)
_RE_PHASE = re.compile(r"^[-=]{2,}\s*(Phase\s+\d+|Step\s+\d+|Running|Starting|Initializ)", re.IGNORECASE)

# ── Exit code mapping ──────────────────────────────────────────────────

EXIT_CODE_INFO = {
    0: {
        "type": "Success",
        "reason": "Simulation completed normally.",
        "suggestions": [],
    },
    1: {
        "type": "Configuration / File Error",
        "reason": "The solver reported a configuration error or could not find a required file.",
        "suggestions": [
            "Check the console output above for a specific error message (e.g. 'could not open geometry file').",
            "Verify the geometry .dat file exists inside the input/ folder.",
            "Make sure the geometry filename in Domain settings matches the actual file on disk.",
            "Ensure input_path and output_path in the XML are correct relative paths.",
        ],
    },
    -1: {
        "type": "Invalid Parameter / ADE Error",
        "reason": "A computed parameter is out of range (e.g. ADE tau invalid).",
        "suggestions": [
            "Check that Peclet number and pressure drop produce a valid tau (must be 0.5 < tau < 2).",
            "Reduce Peclet number or adjust delta_P.",
            "Verify diffusion coefficients are physically reasonable.",
        ],
    },
    -1073740940: {
        "type": "Heap Corruption (0xC0000374)",
        "reason": "The solver wrote past the end of an array — almost always a geometry size mismatch.",
        "suggestions": [
            "The geometry .dat file must contain exactly nx * ny * nz integer values.",
            "Open the geometry file and count its lines/values, then set nx, ny, nz to match.",
            "If geometry has 45000 values and your domain is 50x30x30 (=45000), that is correct.",
            "Do NOT include ghost-node padding — the solver adds +2 to nx internally.",
            "Try the sample geometry.dat from the repo's input/ folder with nx=50, ny=30, nz=30.",
        ],
    },
    -1073741819: {
        "type": "Access Violation (0xC0000005)",
        "reason": "The solver tried to read or write invalid memory.",
        "suggestions": [
            "This often means the geometry file is corrupt or has wrong dimensions.",
            "Verify geometry .dat file contains only integer values (0, 1, 2, 3, …).",
            "Make sure there are no blank lines or non-numeric characters in the geometry file.",
            "Check that material numbers in the geometry file match what is defined in the project.",
        ],
    },
    -1073741571: {
        "type": "Stack Overflow (0xC00000FD)",
        "reason": "The solver ran out of stack memory — domain may be too large for available RAM.",
        "suggestions": [
            "Reduce domain size (nx, ny, nz) and try again.",
            "Close other programs to free memory.",
            "For large domains, use MPI parallelism (Parallel settings) to distribute memory.",
        ],
    },
    -1073741515: {
        "type": "DLL Not Found (0xC0000135)",
        "reason": "A required DLL library could not be found.",
        "suggestions": [
            "Ensure the CompLaB executable and all its DLLs are in the same folder.",
            "Reinstall the CompLaB solver package.",
            "Check that Visual C++ Redistributable is installed on your system.",
        ],
    },
    -1073741676: {
        "type": "Integer Divide by Zero (0xC0000094)",
        "reason": "The solver attempted to divide by zero.",
        "suggestions": [
            "Check that domain dimensions (nx, ny, nz) are all > 0.",
            "Verify Peclet number is not zero if reactive transport is enabled.",
            "Ensure at least one substrate is defined if chemistry is enabled.",
        ],
    },
}

# Convert unsigned 32-bit Windows codes to signed for lookup
# e.g. 3221226356 (unsigned) == -1073740940 (signed)
_UNSIGNED_TO_SIGNED = {}
for _code in list(EXIT_CODE_INFO.keys()):
    if _code < 0:
        _unsigned = _code + 2**32
        _UNSIGNED_TO_SIGNED[_unsigned] = _code


# ── Solver output error patterns ────────────────────────────────────────

_ERROR_PATTERNS = [
    (re.compile(r"[Ee]rror:\s*could not open geometry file\s*(.*)", re.IGNORECASE), "geometry_missing"),
    (re.compile(r"[Ee]rror:\s*could not open\s+(.*)", re.IGNORECASE), "file_missing"),
    (re.compile(r"\[ADE\]\s*ERROR:\s*tau\s*=\s*([0-9.eE+-]+)\s*invalid", re.IGNORECASE), "ade_tau_invalid"),
    (re.compile(r"Error:\s*Updating mask failed", re.IGNORECASE), "mask_update_failed"),
    (re.compile(r"[Ss]egmentation fault", re.IGNORECASE), "segfault"),
    (re.compile(r"[Oo]ut of memory", re.IGNORECASE), "oom"),
    (re.compile(r"[Nn]ot enough memory", re.IGNORECASE), "oom"),
    (re.compile(r"NaN|nan|inf\b", re.IGNORECASE), "nan_detected"),
    (re.compile(r"[Dd]iverg", re.IGNORECASE), "divergence"),
    (re.compile(r"[Nn]ot found", re.IGNORECASE), "not_found"),
    (re.compile(r"[Pp]ermission denied", re.IGNORECASE), "permission_denied"),
]

_PATTERN_DIAGNOSTICS = {
    "geometry_missing": {
        "reason": "The geometry .dat file could not be found at the expected path.",
        "suggestions": [
            "Copy your geometry .dat file into the project's input/ folder.",
            "In Domain settings, make sure the geometry filename matches the actual file.",
            "The solver looks for: <working_directory>/input/<geometry_filename>.",
        ],
    },
    "file_missing": {
        "reason": "A required input file could not be opened.",
        "suggestions": [
            "Check the error message above for the exact filename.",
            "Verify the file exists in the project's input/ directory.",
            "Check file permissions — the file may be locked by another program.",
        ],
    },
    "ade_tau_invalid": {
        "reason": "The computed ADE relaxation time (tau) is outside the stable range (0.5, 2.0).",
        "suggestions": [
            "Reduce the Peclet number in Fluid settings.",
            "Adjust pressure drop (delta_P) to lower flow velocity.",
            "Check diffusion coefficients — very small values push tau out of range.",
            "Increase grid spacing (dx) to bring tau into range.",
        ],
    },
    "mask_update_failed": {
        "reason": "The CA biofilm mask update failed — geometry or material numbers are inconsistent.",
        "suggestions": [
            "Verify material numbers in geometry .dat match the Microbe material_number settings.",
            "Check that pore=2, solid=0, bounce_back=1 match your geometry convention.",
            "Ensure microbe material numbers (3, 4, …) exist in the geometry file.",
        ],
    },
    "segfault": {
        "reason": "Segmentation fault — the solver accessed invalid memory.",
        "suggestions": [
            "Geometry file dimensions likely don't match nx * ny * nz.",
            "Verify the geometry file has exactly nx * ny * nz values.",
            "Check for corrupt or truncated geometry files.",
        ],
    },
    "oom": {
        "reason": "The system ran out of memory during the simulation.",
        "suggestions": [
            "Reduce domain size (nx, ny, nz).",
            "Close other applications to free RAM.",
            "Check the memory estimate in the status bar — your domain may be too large.",
            "For large problems, enable MPI parallelism.",
        ],
    },
    "nan_detected": {
        "reason": "NaN (Not a Number) or Inf values appeared — the simulation is diverging.",
        "suggestions": [
            "Increase relaxation time tau (try 0.8 or higher).",
            "Reduce pressure drop (delta_P).",
            "Check boundary conditions for unphysical values.",
            "Ensure initial concentrations are reasonable.",
        ],
    },
    "divergence": {
        "reason": "The solver is diverging — residuals are increasing instead of decreasing.",
        "suggestions": [
            "Increase tau (relaxation time) for better stability.",
            "Reduce pressure drop (delta_P) to lower the Reynolds number.",
            "Increase maximum iterations to give the solver more time.",
            "Check boundary conditions for consistency.",
        ],
    },
    "not_found": {
        "reason": "A required resource was not found.",
        "suggestions": [
            "Check the console output above for the specific file or resource name.",
            "Verify all input files are in the correct directories.",
        ],
    },
    "permission_denied": {
        "reason": "The solver does not have permission to read/write a file.",
        "suggestions": [
            "Close any programs that might have the file open (Excel, text editors).",
            "Check that the output/ directory is writable.",
            "Try running the GUI as Administrator if permissions are restricted.",
        ],
    },
}


class SimulationRunner(QThread):
    """Runs the CompLaB3D solver as a subprocess with full error diagnostics.

    Signals:
        output_line(str): Each line of stdout/stderr.
        progress(int, int): (current_iteration, max_iterations)
        convergence(str, int, float): (solver_name, iteration, residual)
        phase_changed(str): Current simulation phase description.
        finished_signal(int, str): (return_code, summary_message)
        diagnostic_signal(str): Detailed error diagnostic report.
    """

    output_line = Signal(str)
    progress = Signal(int, int)
    convergence = Signal(str, int, float)
    phase_changed = Signal(str)
    finished_signal = Signal(int, str)
    diagnostic_signal = Signal(str)

    def __init__(self, executable: str, working_dir: str, parent=None,
                 mpi_command: str = "", num_cores: int = 1,
                 project=None):
        super().__init__(parent)
        self._exe = executable
        self._cwd = working_dir
        self._mpi_cmd = mpi_command
        self._num_cores = num_cores
        self._project = project
        self._process = None
        self._cancelled = False
        self._output_buffer = []

    def _build_command(self) -> list:
        """Build the command list, with or without MPI."""
        if self._mpi_cmd and self._num_cores > 1:
            return [
                self._mpi_cmd, "-np", str(self._num_cores),
                self._exe, "CompLaB.xml",
            ]
        return [self._exe]

    # ── Pre-flight checks ──────────────────────────────────────────

    def _preflight_checks(self) -> list:
        """Run pre-flight validation. Returns list of (error, reason, suggestions)."""
        issues = []

        # 1. Executable exists
        if not os.path.isfile(self._exe):
            issues.append({
                "error": f"Executable not found: {self._exe}",
                "reason": "The CompLaB solver executable does not exist at the configured path.",
                "suggestions": [
                    "Go to Edit > Preferences and set the correct path to complab.exe.",
                    "Check that CompLaB is installed (look in AppData/Local/CompLaB_Studio/bin/).",
                    "If you moved the executable, update the path in Preferences.",
                ],
            })
            return issues  # Can't continue without executable

        # 2. Working directory
        if not os.path.isdir(self._cwd):
            issues.append({
                "error": f"Working directory does not exist: {self._cwd}",
                "reason": "The project directory could not be found on disk.",
                "suggestions": [
                    "Save the project first (Ctrl+S) to create the project directory.",
                    "If you moved the project folder, re-open it from the new location.",
                ],
            })
            return issues

        # 3. Input directory
        input_dir = os.path.join(self._cwd, "input")
        if not os.path.isdir(input_dir):
            issues.append({
                "error": f"Input directory missing: {input_dir}",
                "reason": "The solver expects an 'input' folder inside the project directory.",
                "suggestions": [
                    f"Create the folder: {input_dir}",
                    "Copy your geometry .dat file into this input/ folder.",
                ],
            })

        # 4. Geometry file
        if self._project:
            geom_name = self._project.domain.geometry_filename
            if geom_name:
                geom_path = os.path.join(input_dir, geom_name)
                if os.path.isdir(input_dir) and not os.path.isfile(geom_path):
                    issues.append({
                        "error": f"Geometry file not found: {geom_path}",
                        "reason": (
                            f"The geometry file '{geom_name}' does not exist in the input/ folder. "
                            "The solver will crash immediately when it tries to read it."
                        ),
                        "suggestions": [
                            f"Copy your geometry .dat file to: {geom_path}",
                            "Or change the geometry filename in Domain settings to match an existing file.",
                            "You can use Tools > Geometry Generator to create a new geometry file.",
                        ],
                    })
                elif os.path.isfile(geom_path):
                    # 5. Geometry dimension check
                    self._check_geometry_dimensions(geom_path, issues)

        # 6. Output directory (create if needed, warn if not writable)
        output_dir = os.path.join(self._cwd, "output")
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
            except OSError as e:
                issues.append({
                    "error": f"Cannot create output directory: {output_dir}",
                    "reason": f"Failed to create the output folder: {e}",
                    "suggestions": [
                        "Check disk space and folder permissions.",
                        f"Manually create the folder: {output_dir}",
                    ],
                })

        return issues

    def _check_geometry_dimensions(self, geom_path: str, issues: list):
        """Validate that geometry file value count matches nx*ny*nz."""
        if not self._project:
            return
        nx = self._project.domain.nx
        ny = self._project.domain.ny
        nz = self._project.domain.nz
        expected = nx * ny * nz

        try:
            value_count = 0
            bad_lines = []
            with open(geom_path, "r") as f:
                for line_num, line in enumerate(f, 1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    # Each line may have one or multiple space-separated values
                    tokens = stripped.split()
                    for token in tokens:
                        try:
                            int(token)
                            value_count += 1
                        except ValueError:
                            if len(bad_lines) < 5:
                                bad_lines.append(f"  Line {line_num}: '{token}'")

            if bad_lines:
                issues.append({
                    "error": "Geometry file contains non-integer values.",
                    "reason": (
                        "The geometry .dat file must contain only integer values "
                        "(0=solid, 1=bounce-back, 2=pore, 3+=biomass). "
                        "Non-integer values were found."
                    ),
                    "suggestions": [
                        "Fix the following lines in the geometry file:",
                    ] + bad_lines + [
                        "Each value must be a non-negative integer.",
                    ],
                })

            if value_count != expected:
                issues.append({
                    "error": (
                        f"Geometry size mismatch: file has {value_count:,} values, "
                        f"expected {expected:,} (nx={nx} x ny={ny} x nz={nz})."
                    ),
                    "reason": (
                        "The number of values in the geometry file must equal nx * ny * nz. "
                        "A mismatch causes the solver to read past array bounds, "
                        "resulting in a heap corruption crash (exit code 0xC0000374)."
                    ),
                    "suggestions": [
                        f"Your geometry file has {value_count:,} values.",
                        f"Your domain settings require {expected:,} values ({nx} x {ny} x {nz}).",
                        "Either adjust nx, ny, nz in Domain settings to match the file,",
                        "or regenerate the geometry file with the correct dimensions.",
                        "Use Tools > Geometry Generator to create a correctly-sized file.",
                    ],
                })
        except Exception:
            pass  # Don't block simulation for read errors

    # ── Main run loop ──────────────────────────────────────────────

    def run(self):
        # Run pre-flight checks
        preflight_issues = self._preflight_checks()
        blocking = False
        for issue in preflight_issues:
            diag = self._format_single_diagnostic(issue)
            self.diagnostic_signal.emit(diag)
            self.output_line.emit(f"ERROR: {issue['error']}")
            # Block on: missing files, geometry mismatch, or non-integer values
            err_lower = issue["error"].lower()
            if ("not found" in err_lower
                    or "missing" in err_lower
                    or "mismatch" in err_lower
                    or "non-integer" in err_lower):
                blocking = True

        if blocking:
            self.output_line.emit("-" * 60)
            self.output_line.emit(
                "Simulation aborted due to pre-flight errors. Fix the issues above and try again.")
            self.finished_signal.emit(-1, "Pre-flight check failed")
            return

        # Non-blocking warnings
        if preflight_issues:
            self.output_line.emit(
                f"WARNING: {len(preflight_issues)} issue(s) found — simulation may fail. See diagnostics above.")

        # XML check
        xml_path = os.path.join(self._cwd, "CompLaB.xml")
        if not os.path.isfile(xml_path):
            diag = self._format_single_diagnostic({
                "error": f"CompLaB.xml not found in {self._cwd}",
                "reason": "The solver configuration file was not exported to the project directory.",
                "suggestions": [
                    "The GUI should export this automatically before running.",
                    "Try clicking 'Export CompLaB.xml' in the Run panel.",
                    "Save the project (Ctrl+S) and try running again.",
                ],
            })
            self.diagnostic_signal.emit(diag)
            self.output_line.emit(f"ERROR: CompLaB.xml not found in {self._cwd}")
            self.finished_signal.emit(-1, "CompLaB.xml not found")
            return

        cmd = self._build_command()
        cmd_str = " ".join(cmd)

        if self._num_cores > 1:
            self.output_line.emit(f"MPI: {self._mpi_cmd} with {self._num_cores} cores")
        self.output_line.emit(f"Command: {cmd_str}")
        self.output_line.emit(f"Working directory: {self._cwd}")
        self.output_line.emit("-" * 60)

        self._output_buffer.clear()
        t0 = time.time()
        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=self._cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            max_it = 0
            cur_it = 0
            for line in iter(self._process.stdout.readline, ""):
                if self._cancelled:
                    self._process.terminate()
                    self.output_line.emit("-- Simulation cancelled by user --")
                    break
                line = line.rstrip("\n")
                self.output_line.emit(line)
                self._output_buffer.append(line)

                # Parse iteration progress
                m = _RE_ITERATION.search(line)
                if m:
                    cur_it = int(m.group(1))
                    if cur_it > max_it:
                        max_it = cur_it
                    self.progress.emit(cur_it, max_it)

                m2 = _RE_ADE_MAX.search(line)
                if m2:
                    max_it = int(m2.group(1))

                m3 = _RE_NS_MAX.search(line)
                if m3:
                    val = int(m3.group(1))
                    if val > max_it:
                        max_it = val

                # Parse convergence residuals
                m_ns = _RE_NS_RESIDUAL.search(line)
                if m_ns:
                    try:
                        residual = float(m_ns.group(1))
                        self.convergence.emit("NS", cur_it, residual)
                    except ValueError:
                        pass

                m_ade = _RE_ADE_RESIDUAL.search(line)
                if m_ade:
                    try:
                        residual = float(m_ade.group(1))
                        self.convergence.emit("ADE", cur_it, residual)
                    except ValueError:
                        pass

                # Parse phase changes
                m_phase = _RE_PHASE.match(line)
                if m_phase:
                    self.phase_changed.emit(line.strip(" -="))

            self._process.stdout.close()
            rc = self._process.wait()
        except Exception as e:
            self.output_line.emit(f"ERROR: {e}")
            self._output_buffer.append(f"ERROR: {e}")
            rc = -1

        elapsed = time.time() - t0
        mins, secs = divmod(int(elapsed), 60)
        hrs, mins = divmod(mins, 60)

        if self._cancelled:
            msg = f"Cancelled after {hrs}h {mins}m {secs}s"
        elif rc == 0:
            msg = f"Completed successfully in {hrs}h {mins}m {secs}s"
        else:
            msg = f"Exited with code {rc} after {hrs}h {mins}m {secs}s"

        self.output_line.emit("-" * 60)
        self.output_line.emit(msg)

        # Generate error diagnostics for non-zero exit codes
        if rc != 0 and not self._cancelled:
            report = self._build_diagnostic_report(rc)
            self.diagnostic_signal.emit(report)

        self.finished_signal.emit(rc, msg)

    def cancel(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()

    # ── Diagnostic report generation ───────────────────────────────

    def _build_diagnostic_report(self, exit_code: int) -> str:
        """Build a detailed diagnostic report from exit code + captured output."""
        lines = []
        lines.append("=" * 60)
        lines.append("  ERROR DIAGNOSTIC REPORT")
        lines.append("=" * 60)

        # 1. Exit code analysis
        code_info = self._lookup_exit_code(exit_code)
        lines.append("")
        lines.append(f"  Exit Code: {exit_code}")
        if exit_code < 0:
            lines.append(f"  (Hex: 0x{(exit_code + 2**32):08X})")
        lines.append(f"  Error Type: {code_info['type']}")
        lines.append("")
        lines.append(f"  REASON: {code_info['reason']}")

        if code_info["suggestions"]:
            lines.append("")
            lines.append("  SUGGESTED FIXES:")
            for i, s in enumerate(code_info["suggestions"], 1):
                lines.append(f"    {i}. {s}")

        # 2. Output pattern analysis
        detected = self._analyze_output()
        if detected:
            lines.append("")
            lines.append("-" * 60)
            lines.append("  DETECTED IN SOLVER OUTPUT:")
            for pattern_key, match_text in detected:
                diag = _PATTERN_DIAGNOSTICS.get(pattern_key, {})
                reason = diag.get("reason", "")
                suggestions = diag.get("suggestions", [])
                lines.append("")
                lines.append(f"  >> {match_text}")
                if reason:
                    lines.append(f"     Reason: {reason}")
                if suggestions:
                    for s in suggestions:
                        lines.append(f"     - {s}")

        # 3. Quick-check summary
        lines.append("")
        lines.append("-" * 60)
        lines.append("  QUICK CHECKLIST:")
        lines.append("    [ ] Geometry file exists in input/ folder?")
        lines.append("    [ ] Geometry values count = nx * ny * nz?")
        lines.append("    [ ] Domain dimensions (nx, ny, nz) set correctly?")
        lines.append("    [ ] Material numbers in geometry match project settings?")
        lines.append("    [ ] Relaxation time tau > 0.5?")
        lines.append("    [ ] At least one substrate defined if chemistry is on?")
        lines.append("=" * 60)

        return "\n".join(lines)

    def _lookup_exit_code(self, code: int) -> dict:
        """Look up exit code info, handling unsigned/signed Windows codes."""
        # Direct lookup
        if code in EXIT_CODE_INFO:
            return EXIT_CODE_INFO[code]

        # Try unsigned -> signed conversion
        signed = _UNSIGNED_TO_SIGNED.get(code)
        if signed is not None and signed in EXIT_CODE_INFO:
            return EXIT_CODE_INFO[signed]

        # Try manual conversion for any unsigned Windows code
        if code > 2**31:
            signed_code = code - 2**32
            if signed_code in EXIT_CODE_INFO:
                return EXIT_CODE_INFO[signed_code]

        # Unknown code
        return {
            "type": f"Unknown Error (code {code})",
            "reason": (
                "The solver exited with an unrecognized error code. "
                "Check the console output above for clues."
            ),
            "suggestions": [
                "Look for error messages in the solver output above.",
                "Verify all input files exist and have correct format.",
                "Try running with the sample geometry.dat and default settings to isolate the issue.",
                "If the problem persists, save the console log (Save Log button) and report it.",
            ],
        }

    def _analyze_output(self) -> list:
        """Scan buffered output for known error patterns. Returns [(pattern_key, matched_line)]."""
        detected = []
        seen_keys = set()
        for line in self._output_buffer:
            for regex, key in _ERROR_PATTERNS:
                if key in seen_keys:
                    continue
                if regex.search(line):
                    detected.append((key, line.strip()))
                    seen_keys.add(key)
        return detected

    @staticmethod
    def _format_single_diagnostic(issue: dict) -> str:
        """Format a single pre-flight issue into a diagnostic string."""
        lines = []
        lines.append("-" * 60)
        lines.append(f"  PRE-FLIGHT ERROR: {issue['error']}")
        lines.append(f"  Reason: {issue['reason']}")
        if issue["suggestions"]:
            lines.append("  How to fix:")
            for i, s in enumerate(issue["suggestions"], 1):
                lines.append(f"    {i}. {s}")
        lines.append("-" * 60)
        return "\n".join(lines)
