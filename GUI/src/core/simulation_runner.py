"""Simulation runner - executes CompLaB3D in a background thread.

Supports:
  - Direct execution (single process)
  - MPI parallel execution via mpirun/mpiexec
  - Real-time stdout/stderr parsing
  - Progress tracking from iteration output
  - Auto-save all output to timestamped .out log file
  - Cancellation support
  - Crash diagnostics: analyses XML + kinetics headers on failure
"""

import os
import re
import struct
import time
import datetime
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal


class SimulationRunner(QThread):
    """Runs the CompLaB3D solver as a subprocess.

    Signals:
        output_line(str): Each line of stdout/stderr.
        progress(int, int): (current_iteration, max_iterations)
        finished_signal(int, str): (return_code, summary_message)
        diagnostic_report(str): Crash diagnostic text (emitted on failure).
    """

    output_line = Signal(str)
    progress = Signal(int, int)
    finished_signal = Signal(int, str)
    diagnostic_report = Signal(str)

    def __init__(self, executable: str, working_dir: str, parent=None,
                 mpi_enabled: bool = False, mpi_nprocs: int = 1,
                 mpi_command: str = "mpirun"):
        super().__init__(parent)
        self._exe = executable
        self._cwd = working_dir
        self._process = None
        self._cancelled = False
        self._mpi_enabled = mpi_enabled
        self._mpi_nprocs = mpi_nprocs
        self._mpi_command = mpi_command

    def run(self):
        import shutil as _shutil

        # Resolve the executable: accept both file paths and command names
        exe = self._exe
        if not os.path.isfile(exe):
            resolved = _shutil.which(exe)
            if resolved:
                exe = resolved
            else:
                self.output_line.emit(
                    f"ERROR: Executable not found: {self._exe}")
                self.finished_signal.emit(-1, "Executable not found")
                return
        self._exe = exe

        # Ensure executable permission on Unix
        if os.name != "nt" and not os.access(self._exe, os.X_OK):
            try:
                os.chmod(self._exe, os.stat(self._exe).st_mode | 0o111)
                self.output_line.emit(f"Set executable permission on {self._exe}")
            except OSError as e:
                self.output_line.emit(f"WARNING: Could not set +x: {e}")

        xml_path = os.path.join(self._cwd, "CompLaB.xml")
        if not os.path.isfile(xml_path):
            self.output_line.emit(
                f"ERROR: CompLaB.xml not found in {self._cwd}")
            self.finished_signal.emit(-1, "CompLaB.xml not found")
            return

        # Build command
        if self._mpi_enabled and self._mpi_nprocs > 1:
            cmd = [
                self._mpi_command,
                "-np", str(self._mpi_nprocs),
                self._exe,
            ]
            self.output_line.emit(
                f"Starting MPI: {self._mpi_command} -np {self._mpi_nprocs}"
                f" {self._exe}")
        else:
            cmd = [self._exe]
            self.output_line.emit(f"Starting: {self._exe}")

        self.output_line.emit(f"Working directory: {self._cwd}")

        # Open log file in the output directory (or working dir)
        log_file = None
        self._log_path = ""
        try:
            output_dir = os.path.join(self._cwd, "output")
            os.makedirs(output_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._log_path = os.path.join(output_dir, f"simulation_{ts}.out")
            log_file = open(self._log_path, "w", buffering=1)
            self.output_line.emit(f"Log file: {self._log_path}")
        except Exception as e:
            self.output_line.emit(f"WARNING: Could not create log file: {e}")

        self.output_line.emit("=" * 60)

        t0 = time.time()
        max_it = 0
        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=self._cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            for line in iter(self._process.stdout.readline, ""):
                if self._cancelled:
                    self._process.terminate()
                    self.output_line.emit(
                        "-- Simulation cancelled by user --")
                    break
                line = line.rstrip("\n")
                self.output_line.emit(line)
                if log_file:
                    log_file.write(line + "\n")
                # Parse iteration progress
                m = re.search(r"iT\s*=\s*(\d+)", line)
                if m:
                    cur = int(m.group(1))
                    if cur > max_it:
                        max_it = cur
                    self.progress.emit(cur, max_it)
                m2 = re.search(r"ade_max_iT\s*=\s*(\d+)", line)
                if m2:
                    max_it = int(m2.group(1))

            self._process.stdout.close()
            rc = self._process.wait()
        except FileNotFoundError:
            if self._mpi_enabled:
                self.output_line.emit(
                    f"ERROR: MPI command not found: {self._mpi_command}")
                self.output_line.emit(
                    "Make sure MPI is installed and the path is correct.")
                self.output_line.emit(
                    "  Linux:   sudo apt install openmpi-bin")
                self.output_line.emit(
                    "  macOS:   brew install open-mpi")
                self.output_line.emit(
                    "  Windows: Install MS-MPI from microsoft.com")
                self.output_line.emit(
                    "Or go to the Parallel panel and use Auto-detect / Browse.")
            else:
                self.output_line.emit(
                    f"ERROR: Executable not found: {self._exe}")
                self.output_line.emit(
                    "Build with: cd build && cmake .. && make")
            rc = -1
        except Exception as e:
            self.output_line.emit(f"ERROR: {e}")
            rc = -1

        elapsed = time.time() - t0
        mins, secs = divmod(int(elapsed), 60)
        hrs, mins = divmod(mins, 60)

        self.output_line.emit("=" * 60)

        if self._cancelled:
            msg = f"Cancelled after {hrs}h {mins}m {secs}s"
        elif rc == 0:
            msg = f"Completed successfully in {hrs}h {mins}m {secs}s"
        else:
            msg = f"Exited with code {rc} after {hrs}h {mins}m {secs}s"

        self.output_line.emit(msg)

        # Close log file
        if log_file:
            log_file.write("=" * 60 + "\n")
            log_file.write(msg + "\n")
            log_file.close()
            self.output_line.emit(f"Log saved: {self._log_path}")

        # Convert unsigned 32-bit Windows exit codes to signed to avoid
        # OverflowError in Qt Signal(int, str) which expects a C signed int.
        if rc > 2147483647 or rc < -2147483648:
            rc = struct.unpack('i', struct.pack('I', rc & 0xFFFFFFFF))[0]

        # ── Run crash diagnostics on failure ───────────────────────
        if rc != 0 and not self._cancelled:
            self._run_crash_diagnostic(rc)

        self.finished_signal.emit(rc, msg)

    def cancel(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()

    def _run_crash_diagnostic(self, rc: int):
        """Analyse CompLaB.xml + kinetics headers and emit a report."""
        xml_path = os.path.join(self._cwd, "CompLaB.xml")
        if not os.path.isfile(xml_path):
            return

        try:
            from .xml_diagnostic import diagnose_crash
            report = diagnose_crash(xml_path, rc, kinetics_dir=self._cwd)
        except Exception as exc:
            report = f"Crash diagnostic failed: {exc}"

        self.output_line.emit("")
        for line in report.split("\n"):
            self.output_line.emit(line)

        self.diagnostic_report.emit(report)
