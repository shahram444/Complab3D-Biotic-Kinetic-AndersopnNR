"""Simulation runner - executes CompLaB3D in a background thread."""

import os
import re
import time
import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal


class SimulationRunner(QThread):
    output_received = Signal(str)
    progress_updated = Signal(int, int)  # current iteration, max
    status_changed = Signal(str)
    finished_signal = Signal(bool, str)  # success, message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._executable = ""
        self._project_dir = ""
        self._xml_file = ""
        self._process = None
        self._stop_requested = False

    def configure(self, executable, project_dir, xml_file="CompLaB.xml"):
        self._executable = executable
        self._project_dir = project_dir
        self._xml_file = xml_file

    def request_stop(self):
        self._stop_requested = True
        if self._process is not None:
            try:
                self._process.terminate()
            except Exception:
                pass

    def run(self):
        import subprocess

        self._stop_requested = False
        self.status_changed.emit("Starting")

        errors = self._preflight_checks()
        if errors:
            for e in errors:
                self.output_received.emit(f"[ERROR] {e}")
            self.finished_signal.emit(False, "Pre-flight checks failed")
            return

        xml_path = Path(self._project_dir) / self._xml_file
        log_name = f"simulation_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_path = Path(self._project_dir) / log_name

        cmd = [self._executable, str(xml_path)]
        self.output_received.emit(f"[INFO] Working directory: {self._project_dir}")
        self.output_received.emit(f"[INFO] Command: {' '.join(cmd)}")
        self.output_received.emit(f"[INFO] Log file: {log_path}")
        self.status_changed.emit("Running")

        try:
            self._process = subprocess.Popen(
                cmd,
                cwd=self._project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            with open(log_path, "w") as log_file:
                for line in iter(self._process.stdout.readline, ""):
                    if self._stop_requested:
                        break
                    line = line.rstrip("\n")
                    log_file.write(line + "\n")
                    self.output_received.emit(line)
                    self._parse_progress(line)

            self._process.wait()
            rc = self._process.returncode

            if self._stop_requested:
                self.output_received.emit("[INFO] Simulation stopped by user")
                self.finished_signal.emit(False, "Stopped by user")
                self.status_changed.emit("Stopped")
            elif rc == 0:
                self.output_received.emit("[INFO] Simulation completed successfully")
                self.finished_signal.emit(True, "Completed")
                self.status_changed.emit("Completed")
            else:
                msg = self._interpret_exit_code(rc)
                self.output_received.emit(f"[ERROR] Simulation failed (exit code {rc}): {msg}")
                self.finished_signal.emit(False, f"Failed: {msg}")
                self.status_changed.emit("Failed")

        except FileNotFoundError:
            self.output_received.emit(f"[ERROR] Executable not found: {self._executable}")
            self.finished_signal.emit(False, "Executable not found")
            self.status_changed.emit("Failed")
        except Exception as e:
            self.output_received.emit(f"[ERROR] {str(e)}")
            self.finished_signal.emit(False, str(e))
            self.status_changed.emit("Failed")
        finally:
            self._process = None

    def _preflight_checks(self):
        errors = []
        if not self._executable or not Path(self._executable).exists():
            errors.append(f"CompLaB executable not found: {self._executable}")
        if not Path(self._project_dir).is_dir():
            errors.append(f"Project directory not found: {self._project_dir}")
        xml_path = Path(self._project_dir) / self._xml_file
        if not xml_path.exists():
            errors.append(f"XML configuration not found: {xml_path}")
        return errors

    def _parse_progress(self, line):
        m = re.search(r"iT\s*=\s*(\d+)", line)
        if m:
            current = int(m.group(1))
            self.progress_updated.emit(current, 0)
            return
        m = re.search(r"Iteration[:\s]+(\d+)", line)
        if m:
            current = int(m.group(1))
            self.progress_updated.emit(current, 0)

    @staticmethod
    def _interpret_exit_code(rc):
        codes = {
            -6: "Aborted (assertion failure or abort signal)",
            -11: "Segmentation fault",
            -9: "Killed (out of memory or timeout)",
            1: "General error",
            2: "Misuse of shell command",
        }
        if rc in codes:
            return codes[rc]
        if rc < 0:
            return f"Terminated by signal {-rc}"
        return f"Unknown exit code {rc}"

    @staticmethod
    def find_executable():
        """Search standard locations for complab executable."""
        candidates = [
            "complab3d",
            "complab",
            str(Path.home() / ".local" / "bin" / "complab3d"),
            str(Path.home() / ".local" / "bin" / "complab"),
        ]
        # Windows paths
        if os.name == "nt":
            candidates.extend([
                str(Path.home() / "AppData" / "Local" / "CompLaB_Studio" / "bin" / "complab.exe"),
                str(Path.home() / "AppData" / "Local" / "CompLaB_Studio" / "bin" / "complab3d.exe"),
            ])
        for c in candidates:
            p = Path(c)
            if p.exists() and p.is_file():
                return str(p)
        return ""
