"""Simulation runner - executes CompLaB3D in a background thread."""

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


class SimulationRunner(QThread):
    """Runs the CompLaB3D solver as a subprocess.

    Signals:
        output_line(str): Each line of stdout/stderr.
        progress(int, int): (current_iteration, max_iterations)
        convergence(str, int, float): (solver_name, iteration, residual)
        phase_changed(str): Current simulation phase description.
        finished_signal(int, str): (return_code, summary_message)
    """

    output_line = Signal(str)
    progress = Signal(int, int)
    convergence = Signal(str, int, float)
    phase_changed = Signal(str)
    finished_signal = Signal(int, str)

    def __init__(self, executable: str, working_dir: str, parent=None):
        super().__init__(parent)
        self._exe = executable
        self._cwd = working_dir
        self._process = None
        self._cancelled = False

    def run(self):
        if not os.path.isfile(self._exe):
            self.output_line.emit(f"ERROR: Executable not found: {self._exe}")
            self.finished_signal.emit(-1, "Executable not found")
            return

        xml_path = os.path.join(self._cwd, "CompLaB.xml")
        if not os.path.isfile(xml_path):
            self.output_line.emit(f"ERROR: CompLaB.xml not found in {self._cwd}")
            self.finished_signal.emit(-1, "CompLaB.xml not found")
            return

        self.output_line.emit(f"Starting: {self._exe}")
        self.output_line.emit(f"Working directory: {self._cwd}")
        self.output_line.emit("-" * 60)

        t0 = time.time()
        try:
            self._process = subprocess.Popen(
                [self._exe],
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
        self.finished_signal.emit(rc, msg)

    def cancel(self):
        self._cancelled = True
        if self._process and self._process.poll() is None:
            self._process.terminate()
