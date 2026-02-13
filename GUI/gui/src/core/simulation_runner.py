"""
Simulation Runner - Execute CompLaB simulations with MPI support
"""

import os
import re
import shutil
import subprocess
import struct
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

from PySide6.QtCore import QThread, Signal

from .project import CompLaBProject


class SimulationRunner(QThread):
    """Run CompLaB simulation in a separate thread with MPI support."""

    # Signals
    started_signal = Signal()
    finished_signal = Signal(int, str)  # exit code, summary message
    progress = Signal(int, str)  # iteration, message
    output = Signal(str)  # console output line
    error = Signal(str)  # error message

    def __init__(self, project: CompLaBProject, parent=None):
        super().__init__(parent)
        self.project = project
        self._process: Optional[subprocess.Popen] = None
        self._stop_requested = False
        self._log_file = None
        self._log_path = None
        self._output_buffer: List[str] = []

        # MPI settings
        self.mpi_enabled = False
        self.mpi_nprocs = 1
        self.mpi_command = ""  # auto-detect if empty

        # Custom executable path override
        self.complab_exe_override = ""

    # ------------------------------------------------------------------
    # Main execution
    # ------------------------------------------------------------------
    def run(self):
        """Execute the simulation (runs in worker thread)."""
        try:
            self._stop_requested = False
            self._output_buffer = []
            self.started_signal.emit()

            # === PRE-FLIGHT CHECKS ===
            self._log_and_emit("=" * 60)
            self._log_and_emit("CompLaB Pre-Flight Checks")
            self._log_and_emit("=" * 60)

            # 1. Find executable
            complab_exe = self._find_complab_executable()
            if not complab_exe:
                self._emit_preflight_error(
                    "CompLaB executable not found",
                    "Could not locate 'complab' binary.",
                    [
                        "Set the COMPLAB_PATH environment variable to the executable.",
                        "Or place it in your PATH, or in the project directory.",
                        "On Linux: check ~/complab, ./complab, /usr/local/bin/complab",
                    ],
                )
                self.finished_signal.emit(-1, "Executable not found")
                return
            self._log_and_emit(f"[OK] Executable: {complab_exe}")

            # 2. Project directory
            project_dir = self.project.get_project_dir()
            if not project_dir or not os.path.isdir(project_dir):
                self._emit_preflight_error(
                    "Project directory not found",
                    f"Directory does not exist: {project_dir}",
                    ["Save the project before running."],
                )
                self.finished_signal.emit(-1, "Project directory missing")
                return
            self._log_and_emit(f"[OK] Project dir: {project_dir}")

            # 3. Input directory
            input_dir = self.project.get_input_dir()
            if not os.path.isdir(input_dir):
                os.makedirs(input_dir, exist_ok=True)
                self._log_and_emit(f"[OK] Created input dir: {input_dir}")
            else:
                self._log_and_emit(f"[OK] Input dir: {input_dir}")

            # 4. Geometry file (binary .dat with material numbers)
            geom_file = self.project.domain.geometry_file
            if not geom_file:
                self._emit_preflight_error(
                    "No geometry file specified",
                    "The geometry filename is empty.",
                    [
                        "Go to the Domain tab and specify a geometry file.",
                        "Example: geometry.dat, FibHbase3D.dat",
                    ],
                )
                self.finished_signal.emit(-1, "No geometry file")
                return

            geom_path = os.path.join(input_dir, geom_file)
            if not os.path.isfile(geom_path):
                self._emit_preflight_error(
                    "Geometry file not found",
                    f"File does not exist: {geom_path}",
                    [
                        f"Place '{geom_file}' in the input/ folder.",
                        "Use Geometry Creator or MATLAB createDAT_with_microbes.m",
                    ],
                )
                self.finished_signal.emit(-1, "Geometry file missing")
                return

            expected_n = (
                self.project.domain.nx
                * self.project.domain.ny
                * self.project.domain.nz
            )
            geom_size = os.path.getsize(geom_path)
            self._log_and_emit(
                f"[OK] Geometry: {geom_file} ({geom_size:,} bytes, "
                f"domain {self.project.domain.nx}x{self.project.domain.ny}x{self.project.domain.nz})"
            )

            # 5. XML file
            xml_path = os.path.join(project_dir, "CompLaB.xml")
            if not os.path.isfile(xml_path):
                self._emit_preflight_error(
                    "XML configuration not found",
                    f"No CompLaB.xml in: {project_dir}",
                    ["Click 'Save' to generate the XML configuration."],
                )
                self.finished_signal.emit(-1, "XML missing")
                return
            self._log_and_emit(f"[OK] XML config: CompLaB.xml")

            # 6. MPI check
            mpi_cmd = None
            if self.mpi_enabled and self.mpi_nprocs > 1:
                mpi_cmd = self._find_mpi_command()
                if not mpi_cmd:
                    self._emit_preflight_error(
                        "MPI not found",
                        "MPI is enabled but mpirun/mpiexec not found.",
                        [
                            "Install OpenMPI or MPICH.",
                            "Or disable MPI in the run configuration.",
                        ],
                    )
                    self.finished_signal.emit(-1, "MPI not found")
                    return
                self._log_and_emit(f"[OK] MPI: {mpi_cmd} -np {self.mpi_nprocs}")

            # 7. Output directory
            output_dir = self.project.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            self._log_and_emit(f"[OK] Output dir: {output_dir}")

            # Setup log file
            self._setup_log_file()

            # === START SIMULATION ===
            self._log_and_emit("")
            self._log_and_emit("=" * 60)
            self._log_and_emit("Starting CompLaB Simulation")
            self._log_and_emit(
                f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self._log_and_emit(
                f"Domain: {self.project.domain.nx} x "
                f"{self.project.domain.ny} x {self.project.domain.nz}"
            )
            self._log_and_emit(f"Substrates: {len(self.project.substrates)}")
            self._log_and_emit(f"Microbes: {len(self.project.microbes)}")
            if self.mpi_enabled and self.mpi_nprocs > 1:
                self._log_and_emit(f"MPI processes: {self.mpi_nprocs}")
            self._log_and_emit("=" * 60)

            # Build command
            if mpi_cmd and self.mpi_nprocs > 1:
                cmd = [mpi_cmd, "-np", str(self.mpi_nprocs), complab_exe, "CompLaB.xml"]
            else:
                cmd = [complab_exe, "CompLaB.xml"]

            self._log_and_emit(f"Command: {' '.join(cmd)}")
            self._log_and_emit("-" * 60)

            # Launch process
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=project_dir,
                bufsize=1,
                universal_newlines=True,
            )

            # Read output line by line
            for line in iter(self._process.stdout.readline, ""):
                if self._stop_requested:
                    self._log_and_emit("\n*** Simulation stopped by user ***")
                    self._process.terminate()
                    try:
                        self._process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self._process.kill()
                    break

                line = line.rstrip("\n\r")
                if line:
                    self._log_and_emit(line)
                    self._parse_progress(line)

            # Wait for exit
            if self._process.poll() is None:
                self._process.wait()

            exit_code = self._process.returncode

            self._log_and_emit("-" * 60)

            if self._stop_requested:
                summary = "Stopped by user"
                self._log_and_emit(summary)
            elif exit_code == 0:
                summary = "Simulation completed successfully!"
                self._log_and_emit(f"[OK] {summary}")
            else:
                summary = f"Simulation failed (exit code {exit_code})"
                self._log_and_emit(f"[FAIL] {summary}")
                self._analyze_failure(exit_code)

            self._log_and_emit(
                f"End: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            self._log_and_emit("=" * 60)
            self._close_log_file()
            # Convert unsigned 32-bit Windows exit codes to signed to avoid
            # OverflowError in Qt Signal(int, str) which expects a C signed int.
            if exit_code > 2147483647 or exit_code < -2147483648:
                exit_code = struct.unpack('i', struct.pack('I', exit_code & 0xFFFFFFFF))[0]
            self.finished_signal.emit(exit_code, summary)

        except Exception as e:
            import traceback

            msg = f"Exception: {e}\n{traceback.format_exc()}"
            self._log_and_emit(f"ERROR: {msg}")
            self.error.emit(msg)
            self._close_log_file()
            self.finished_signal.emit(-1, str(e))

    # ------------------------------------------------------------------
    # Stop
    # ------------------------------------------------------------------
    def stop(self):
        """Request simulation stop."""
        self._stop_requested = True
        if self._process and self._process.poll() is None:
            self._process.terminate()

    # ------------------------------------------------------------------
    # Executable discovery
    # ------------------------------------------------------------------
    def _find_complab_executable(self) -> Optional[str]:
        """Find the CompLaB executable."""
        candidates = []

        # User override
        if self.complab_exe_override:
            candidates.append(self.complab_exe_override)

        # Environment variable
        env_path = os.environ.get("COMPLAB_PATH", "")
        if env_path:
            candidates.append(env_path)

        # Project directory
        project_dir = self.project.get_project_dir()
        if project_dir:
            candidates.append(os.path.join(project_dir, "complab"))
            candidates.append(os.path.join(project_dir, "complab.exe"))

        # Common locations
        home = os.path.expanduser("~")
        if os.name == "nt":
            local = os.environ.get("LOCALAPPDATA", "")
            candidates += [
                os.path.join(local, "CompLaB_Studio", "bin", "complab.exe"),
                os.path.join(home, "CompLaB_Studio", "bin", "complab.exe"),
                os.path.join(os.environ.get("PROGRAMFILES", ""), "CompLaB", "complab.exe"),
            ]
        else:
            candidates += [
                os.path.join(home, "complab"),
                os.path.join(home, "CompLaB", "complab"),
                os.path.join(home, "CompLaB_Studio", "bin", "complab"),
                os.path.join(home, ".local", "bin", "complab"),
                "/usr/local/bin/complab",
                "/usr/bin/complab",
            ]

        # Check PATH via shutil.which
        which_result = shutil.which("complab")
        if which_result:
            candidates.insert(0, which_result)

        for path in candidates:
            if path and os.path.isfile(path) and os.access(path, os.X_OK):
                return path

        return None

    def _find_mpi_command(self) -> Optional[str]:
        """Find mpirun or mpiexec."""
        if self.mpi_command:
            if shutil.which(self.mpi_command):
                return self.mpi_command

        for cmd in ["mpirun", "mpiexec", "srun"]:
            found = shutil.which(cmd)
            if found:
                return found
        return None

    # ------------------------------------------------------------------
    # Progress parsing
    # ------------------------------------------------------------------
    def _parse_progress(self, line: str):
        """Parse iteration progress from solver output."""
        patterns = [
            r"iT\s*=\s*(\d+)",
            r"[Ii]teration[:\s]+(\d+)",
            r"Step[:\s]+(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, line)
            if match:
                iteration = int(match.group(1))
                self.progress.emit(iteration, f"Iteration {iteration}")
                return

        if "converge" in line.lower():
            self.progress.emit(0, "Checking convergence...")
        elif "completed" in line.lower():
            self.progress.emit(0, "Completed")

    # ------------------------------------------------------------------
    # Error analysis
    # ------------------------------------------------------------------
    def _analyze_failure(self, exit_code: int):
        """Analyze simulation failure and provide helpful messages."""
        info = {
            -1: ("General Error", "Unspecified error."),
            1: ("Configuration Error", "Invalid configuration or missing parameters."),
            2: ("File Not Found", "A required file could not be opened."),
            -6: ("Abort (SIGABRT)", "Program aborted - possible assertion failure."),
            -9: ("Killed (SIGKILL)", "Process was killed, possibly out of memory."),
            -11: ("Segfault (SIGSEGV)", "Memory access error - check geometry dimensions."),
            -1073740940: ("Heap Corruption", "Array bounds violation (Windows)."),
            -1073741819: ("Access Violation", "Invalid memory access (Windows)."),
            -1073741571: ("Stack Overflow", "Domain may be too large (Windows)."),
        }

        err_type, desc = info.get(exit_code, (f"Unknown (code {exit_code})", ""))
        self._log_and_emit(f"\nError Type: {err_type}")
        if desc:
            self._log_and_emit(f"Description: {desc}")

        # Search output for clues
        clues = []
        for line in self._output_buffer:
            ll = line.lower()
            if any(kw in ll for kw in ["error", "failed", "not found", "invalid",
                                        "mismatch", "exception", "terminating"]):
                clues.append(line.strip())
        if clues:
            self._log_and_emit("\nError clues from output:")
            for c in clues[:10]:
                self._log_and_emit(f"  > {c}")

        self._log_and_emit("\nSuggestions:")
        self._log_and_emit("  1. Verify geometry dimensions match nx*ny*nz")
        self._log_and_emit("  2. Check XML config is valid (save project again)")
        self._log_and_emit("  3. Try running from command line for detailed output")
        if self.mpi_enabled:
            self._log_and_emit("  4. Try running without MPI first to isolate issues")

    def _emit_preflight_error(self, title: str, desc: str, suggestions: List[str]):
        """Emit a formatted pre-flight error."""
        self._log_and_emit(f"\n[FAIL] {title}")
        self._log_and_emit(f"  {desc}")
        if suggestions:
            self._log_and_emit("  Suggestions:")
            for s in suggestions:
                self._log_and_emit(f"    - {s}")
        self._log_and_emit("")
        self.error.emit(f"{title}\n{desc}")

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log_and_emit(self, message: str):
        """Log to file and emit to console."""
        self.output.emit(message)
        self._output_buffer.append(message)
        if self._log_file:
            try:
                self._log_file.write(message + "\n")
                self._log_file.flush()
            except Exception:
                pass

    def _setup_log_file(self):
        """Create log file in output directory."""
        try:
            output_dir = self.project.get_output_dir()
            os.makedirs(output_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self._log_path = os.path.join(output_dir, f"simulation_{timestamp}.log")
            self._log_file = open(self._log_path, "w", encoding="utf-8")
        except Exception as e:
            self._log_file = None

    def _close_log_file(self):
        """Close the log file."""
        if self._log_file:
            try:
                if self._log_path:
                    self._log_and_emit(f"\nLog saved to: {self._log_path}")
                self._log_file.close()
            except Exception:
                pass
            self._log_file = None


class SimulationMonitor:
    """Monitor simulation progress and estimate completion."""

    def __init__(self, project: CompLaBProject):
        self.project = project
        self.current_iteration = 0
        self.total_iterations = project.iterations.ade_max_iT
        self._start_time = None

    def start(self):
        self._start_time = datetime.now()

    def update(self, iteration: int):
        self.current_iteration = iteration

    @property
    def progress_percent(self) -> float:
        if self.total_iterations > 0:
            return min(100.0, (self.current_iteration / self.total_iterations) * 100)
        return 0

    @property
    def elapsed_seconds(self) -> float:
        if self._start_time:
            return (datetime.now() - self._start_time).total_seconds()
        return 0

    @property
    def eta_seconds(self) -> Optional[float]:
        pct = self.progress_percent
        if pct > 0 and self._start_time:
            elapsed = self.elapsed_seconds
            return (elapsed / pct) * (100 - pct)
        return None
