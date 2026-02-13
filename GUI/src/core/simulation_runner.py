"""Simulation runner - executes CompLaB3D in a background thread.

Supports:
  - Direct execution (single process)
  - MPI parallel execution via mpirun/mpiexec
  - Real-time stdout/stderr parsing
  - Progress tracking from iteration output
  - Cancellation support
"""

import os
import re
import time
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal


class SimulationRunner(QThread):
    """Runs the CompLaB3D solver as a subprocess.

    Signals:
        output_line(str): Each line of stdout/stderr.
        progress(int, int): (current_iteration, max_iterations)
        finished_signal(int, str): (return_code, summary_message)
    """

    output_line = Signal(str)
    progress = Signal(int, int)
    finished_signal = Signal(int, str)

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
        if not os.path.isfile(self._exe):
            self.output_line.emit(f"ERROR: Executable not found: {self._exe}")
            self.finished_signal.emit(-1, "Executable not found")
            return

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
            else:
                self.output_line.emit(
                    f"ERROR: Executable not found: {self._exe}")
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
        self.finished_signal.emit(rc, msg)

    def cancel(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
