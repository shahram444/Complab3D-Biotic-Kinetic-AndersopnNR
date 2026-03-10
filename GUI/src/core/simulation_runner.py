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
import signal
import struct
import time
import datetime
import logging
import subprocess
from pathlib import Path

from PySide6.QtCore import QThread, Signal

log = logging.getLogger("complab.runner")


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
        self._lines_read = 0
        log.info("[RUNNER] SimulationRunner created  exe=%s  cwd=%s  "
                 "mpi=%s  nprocs=%d  id=%s",
                 executable, working_dir, mpi_enabled, mpi_nprocs, id(self))

    # ------------------------------------------------------------------
    # QThread entry point
    # ------------------------------------------------------------------
    def run(self):
        import shutil as _shutil

        log.info("[RUNNER] QThread.run() STARTED  thread=%s  id=%s",
                 QThread.currentThread(), id(self))

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
                log.error("[RUNNER] Executable not found: %s", self._exe)
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
            log.error("[RUNNER] CompLaB.xml missing in %s", self._cwd)
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
        log.info("[RUNNER] Command: %s", cmd)
        log.info("[RUNNER] Environment PATH: %s",
                 os.environ.get("PATH", "(unset)"))

        # Open log file in the output directory (or working dir)
        log_file = None
        self._log_path = ""
        try:
            output_dir = os.path.join(self._cwd, "output")
            os.makedirs(output_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            self._log_path = os.path.join(output_dir, f"simulation_{ts}.out")
            log_file = open(self._log_path, "w", encoding="utf-8", buffering=1)
            self.output_line.emit(f"Log file: {self._log_path}")
        except Exception as e:
            self.output_line.emit(f"WARNING: Could not create log file: {e}")
            log.warning("[RUNNER] Log file creation failed: %s", e)

        self.output_line.emit("=" * 60)

        t0 = time.time()
        max_it = 0
        self._lines_read = 0
        try:
            log.info("[RUNNER] Launching subprocess …")
            self._process = subprocess.Popen(
                cmd,
                cwd=self._cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                # Put child into its own process group so we can kill the
                # whole MPI tree with os.killpg() instead of just the
                # launcher.  Only available on POSIX.
                **({'preexec_fn': os.setsid} if os.name != 'nt' else {}),
            )
            log.info("[RUNNER] Subprocess PID=%d  started", self._process.pid)

            for line in iter(self._process.stdout.readline, ""):
                if self._cancelled:
                    log.info("[RUNNER] Cancel flag detected in read loop")
                    self._kill_process_tree()
                    self.output_line.emit(
                        "-- Simulation cancelled by user --")
                    break
                line = line.rstrip("\n")
                self._lines_read += 1

                # Diagnostic: log every 500th line and the first 5
                if self._lines_read <= 5 or self._lines_read % 500 == 0:
                    log.debug("[RUNNER] line #%d (len=%d): %.120s",
                              self._lines_read, len(line), line)

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

            log.info("[RUNNER] Read loop exited after %d lines "
                     "(cancelled=%s)", self._lines_read, self._cancelled)
            self._process.stdout.close()
            rc = self._process.wait()
            log.info("[RUNNER] Subprocess exited  rc=%d  pid=%d",
                     rc, self._process.pid)
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
            log.error("[RUNNER] FileNotFoundError – cmd=%s", cmd)
        except Exception as e:
            self.output_line.emit(f"ERROR: {e}")
            rc = -1
            log.exception("[RUNNER] Unexpected exception in read loop")

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
        log.info("[RUNNER] %s  (lines_read=%d)", msg, self._lines_read)

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

        log.info("[RUNNER] Emitting finished_signal  rc=%d", rc)
        self.finished_signal.emit(rc, msg)
        log.info("[RUNNER] QThread.run() ENDING  id=%s", id(self))

    # ------------------------------------------------------------------
    # Cancellation
    # ------------------------------------------------------------------
    def cancel(self):
        log.info("[RUNNER] cancel() called  cancelled_before=%s  "
                 "process=%s", self._cancelled, self._process)
        self._cancelled = True
        self._kill_process_tree()

    def _kill_process_tree(self):
        """Terminate the subprocess *and* its entire process group.

        MPI launchers (mpirun, mpiexec) spawn child worker processes.
        A plain ``terminate()`` only sends SIGTERM to the launcher, which
        may or may not forward it.  By killing the whole process group we
        ensure every worker is stopped.
        """
        proc = self._process
        if proc is None or proc.poll() is not None:
            return

        pid = proc.pid
        log.info("[RUNNER] Killing process tree  pid=%d", pid)

        # 1. Try SIGTERM on the whole group (POSIX only)
        if os.name != 'nt':
            try:
                pgid = os.getpgid(pid)
                os.killpg(pgid, signal.SIGTERM)
                log.info("[RUNNER] Sent SIGTERM to pgid=%d", pgid)
            except (ProcessLookupError, PermissionError, OSError) as e:
                log.warning("[RUNNER] killpg SIGTERM failed: %s", e)
                proc.terminate()
        else:
            proc.terminate()

        # 2. Give the tree a moment to exit, then escalate to SIGKILL
        try:
            proc.wait(timeout=5)
            log.info("[RUNNER] Process exited after SIGTERM")
        except subprocess.TimeoutExpired:
            log.warning("[RUNNER] SIGTERM timeout – sending SIGKILL")
            if os.name != 'nt':
                try:
                    os.killpg(os.getpgid(pid), signal.SIGKILL)
                except (ProcessLookupError, PermissionError, OSError):
                    proc.kill()
            else:
                proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                log.error("[RUNNER] Process still alive after SIGKILL!")

    # ------------------------------------------------------------------
    # Crash diagnostics
    # ------------------------------------------------------------------
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
