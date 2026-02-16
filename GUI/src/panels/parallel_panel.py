"""Parallel execution panel - MPI auto-detect, core selection, and validation."""

import os
import sys
import shutil
import subprocess
import multiprocessing
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSlider, QSpinBox,
    QLineEdit, QPushButton, QFileDialog,
)
from PySide6.QtCore import Signal, Qt
from .base_panel import BasePanel


def _detect_system():
    """Detect machine config: CPU cores, RAM, MPI availability."""
    total_cores = multiprocessing.cpu_count()

    # RAM detection (cross-platform)
    total_ram_gb = 0.0
    try:
        total_ram_gb = (
            os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
            / (1024 ** 3)
        )
    except (AttributeError, ValueError):
        # Windows or unsupported platform
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            c_ulonglong = ctypes.c_ulonglong

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", c_ulonglong),
                    ("ullAvailPhys", c_ulonglong),
                    ("ullTotalPageFile", c_ulonglong),
                    ("ullAvailPageFile", c_ulonglong),
                    ("ullTotalVirtual", c_ulonglong),
                    ("ullAvailVirtual", c_ulonglong),
                    ("sullAvailExtendedVirtual", c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(stat)
            kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_ram_gb = stat.ullTotalPhys / (1024 ** 3)
        except Exception:
            total_ram_gb = 0.0

    # MPI detection
    mpi_cmd = ""
    mpi_path = shutil.which("mpirun")
    if mpi_path:
        mpi_cmd = "mpirun"
    else:
        mpi_path = shutil.which("mpiexec")
        if mpi_path:
            mpi_cmd = "mpiexec"

    return total_cores, total_ram_gb, mpi_cmd, mpi_path or ""


class ParallelPanel(BasePanel):
    """MPI parallel execution settings with auto-detection."""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__("Parallel Execution", parent)
        self._total_cores, self._total_ram, self._mpi_cmd, self._mpi_path = (
            _detect_system()
        )
        self._enabled = False
        self._num_cores = 1
        self._build_ui()

    def _build_ui(self):
        # ── System Detection ───────────────────────────────────
        self.add_section("System Detection")
        det_form = self.add_form()

        cores_str = f"{self._total_cores} cores"
        ram_str = (
            f"{self._total_ram:.1f} GB" if self._total_ram > 0 else "Unknown"
        )
        self._detected_lbl = QLabel(f"{cores_str},  {ram_str} RAM")
        self._detected_lbl.setProperty("info", True)
        det_form.addRow("Detected:", self._detected_lbl)

        if self._mpi_cmd:
            mpi_str = f"{self._mpi_cmd} found at {self._mpi_path}"
            self._mpi_status_lbl = QLabel(mpi_str)
            self._mpi_status_lbl.setStyleSheet(
                "color: #5ca060; font-weight: bold;")
        else:
            self._mpi_status_lbl = QLabel(
                "Not auto-detected. You can specify the path manually below.")
            self._mpi_status_lbl.setStyleSheet("color: #c0a040;")
        self._mpi_status_lbl.setWordWrap(True)
        det_form.addRow("MPI:", self._mpi_status_lbl)

        # ── MPI Path (manual entry) ───────────────────────────
        self.add_section("MPI Command")
        mpi_form = self.add_form()

        self._mpi_path_edit = QLineEdit(self._mpi_path or "mpirun")
        self._mpi_path_edit.setPlaceholderText(
            "Path to mpirun or mpiexec (e.g. /usr/bin/mpirun)")
        self._mpi_path_edit.setToolTip(
            "Full path to MPI launcher command.\n"
            "Common options:\n"
            "  mpirun   (OpenMPI)\n"
            "  mpiexec  (MPICH / MS-MPI)\n"
            "  srun     (Slurm)\n"
            "You can also type the full path manually.")
        self._mpi_path_edit.textChanged.connect(self._on_mpi_path_changed)
        mpi_form.addRow("MPI command:", self._mpi_path_edit)

        mpi_btn_row = QHBoxLayout()
        browse_btn = QPushButton("Browse...")
        browse_btn.setToolTip("Browse for MPI executable")
        browse_btn.clicked.connect(self._browse_mpi)
        mpi_btn_row.addWidget(browse_btn)

        detect_btn = QPushButton("Auto-detect")
        detect_btn.setToolTip(
            "Scan PATH for mpirun, mpiexec, or srun")
        detect_btn.clicked.connect(self._auto_detect_mpi)
        mpi_btn_row.addWidget(detect_btn)

        mpi_btn_row.addStretch()
        mpi_form.addRow("", mpi_btn_row)

        self._mpi_version_lbl = QLabel("")
        self._mpi_version_lbl.setProperty("info", True)
        self._mpi_version_lbl.setWordWrap(True)
        mpi_form.addRow("", self._mpi_version_lbl)

        # Show version info if auto-detected
        if self._mpi_path:
            self._verify_mpi_path(self._mpi_path)

        self.add_widget(self.make_info_label(
            "If MPI is not found automatically, install OpenMPI or MPICH:\n"
            "  Linux:   sudo apt install openmpi-bin\n"
            "  macOS:   brew install open-mpi\n"
            "  Windows: Install MS-MPI from microsoft.com"))

        # ── Enable MPI ─────────────────────────────────────────
        self.add_section("Configuration")
        cfg_form = self.add_form()

        self._enable_cb = self.make_checkbox("Enable MPI Parallel")
        # Always allow enabling - user may have set path manually
        self._enable_cb.toggled.connect(self._on_enable_toggled)
        cfg_form.addRow("", self._enable_cb)

        # Core selection slider + spinbox
        core_row = QHBoxLayout()

        self._core_slider = QSlider(Qt.Orientation.Horizontal)
        self._core_slider.setMinimum(1)
        self._core_slider.setMaximum(self._total_cores)
        self._core_slider.setValue(1)
        self._core_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._core_slider.setTickInterval(1)
        self._core_slider.setEnabled(False)
        self._core_slider.valueChanged.connect(self._on_slider_changed)
        core_row.addWidget(self._core_slider, 1)

        self._core_spin = QSpinBox()
        self._core_spin.setMinimum(1)
        self._core_spin.setMaximum(self._total_cores)
        self._core_spin.setValue(1)
        self._core_spin.setFixedWidth(60)
        self._core_spin.setEnabled(False)
        self._core_spin.valueChanged.connect(self._on_spin_changed)
        core_row.addWidget(self._core_spin)

        core_max_lbl = QLabel(f"/ {self._total_cores}")
        core_max_lbl.setProperty("info", True)
        core_row.addWidget(core_max_lbl)

        cfg_form.addRow("Cores:", core_row)

        # Recommended label
        recommended = max(1, self._total_cores - 1)
        self._rec_lbl = QLabel(
            f"Recommended: {recommended} (1 reserved for GUI + OS)"
        )
        self._rec_lbl.setProperty("info", True)
        cfg_form.addRow("", self._rec_lbl)

        # ── Warnings ───────────────────────────────────────────
        self.add_section("Warnings")
        self._warn_lbl = QLabel("")
        self._warn_lbl.setWordWrap(True)
        self._warn_lbl.setProperty("info", True)
        self.add_widget(self._warn_lbl)
        self._update_warnings()

        # ── Run Command Preview ────────────────────────────────
        self.add_section("Run Command Preview")
        _exe = "complab.exe" if sys.platform == "win32" else "./complab"
        self._cmd_lbl = QLabel(_exe)
        self._cmd_lbl.setWordWrap(True)
        self._cmd_lbl.setStyleSheet(
            "font-family: Consolas, monospace; padding: 4px;"
        )
        self.add_widget(self._cmd_lbl)
        self._update_cmd_preview()

        self.add_stretch()

    # ── MPI path handling ──────────────────────────────────────

    def _browse_mpi(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select MPI Launcher", "",
            "Executables (*);;All Files (*)")
        if path:
            self._mpi_path_edit.setText(path)

    def _auto_detect_mpi(self):
        """Scan PATH for known MPI commands."""
        for cmd in ("mpirun", "mpiexec", "srun"):
            path = shutil.which(cmd)
            if path:
                self._mpi_cmd = cmd
                self._mpi_path = path
                self._mpi_path_edit.setText(path)
                self._mpi_status_lbl.setText(f"{cmd} found at {path}")
                self._mpi_status_lbl.setStyleSheet(
                    "color: #5ca060; font-weight: bold;")
                self._verify_mpi_path(path)
                self._update_warnings()
                self._update_cmd_preview()
                self.data_changed.emit()
                return
        self._mpi_status_lbl.setText(
            "MPI not found on PATH. Specify the full path manually.")
        self._mpi_status_lbl.setStyleSheet("color: #c75050;")
        self._mpi_version_lbl.setText("")

    def _on_mpi_path_changed(self, text):
        """Update MPI command when user types or browses a path."""
        text = text.strip()
        if text:
            self._mpi_cmd = os.path.basename(text).replace(".exe", "")
            self._mpi_path = text
        else:
            self._mpi_cmd = ""
            self._mpi_path = ""
        self._update_warnings()
        self._update_cmd_preview()
        self.data_changed.emit()

    def _verify_mpi_path(self, path):
        """Try to run --version and display result."""
        try:
            result = subprocess.run(
                [path, "--version"],
                capture_output=True, text=True, timeout=5)
            first_line = (result.stdout or result.stderr).strip().split('\n')[0]
            if first_line:
                self._mpi_version_lbl.setText(f"Version: {first_line}")
                self._mpi_version_lbl.setStyleSheet("color: #5ca060;")
            else:
                self._mpi_version_lbl.setText("MPI found (no version info)")
                self._mpi_version_lbl.setStyleSheet("color: #5ca060;")
        except FileNotFoundError:
            self._mpi_version_lbl.setText(
                "Command not found at this path")
            self._mpi_version_lbl.setStyleSheet("color: #c75050;")
        except Exception:
            self._mpi_version_lbl.setText("")

    # ── Slots ──────────────────────────────────────────────────

    def _on_enable_toggled(self, checked):
        self._enabled = checked
        self._core_slider.setEnabled(checked)
        self._core_spin.setEnabled(checked)
        if checked and self._num_cores == 1:
            recommended = max(1, self._total_cores - 1)
            self._core_slider.setValue(recommended)
            self._core_spin.setValue(recommended)
            self._num_cores = recommended
        self._update_warnings()
        self._update_cmd_preview()
        self.data_changed.emit()

    def _on_slider_changed(self, value):
        self._num_cores = value
        self._core_spin.blockSignals(True)
        self._core_spin.setValue(value)
        self._core_spin.blockSignals(False)
        self._update_warnings()
        self._update_cmd_preview()
        self.data_changed.emit()

    def _on_spin_changed(self, value):
        self._num_cores = value
        self._core_slider.blockSignals(True)
        self._core_slider.setValue(value)
        self._core_slider.blockSignals(False)
        self._update_warnings()
        self._update_cmd_preview()
        self.data_changed.emit()

    def _update_warnings(self):
        warnings = []
        if self._enabled:
            if self._num_cores >= self._total_cores:
                warnings.append(
                    "Using all cores may freeze the GUI during simulation."
                )
            if self._total_ram > 0:
                ram_per_core = self._total_ram / self._num_cores
                if ram_per_core < 1.0:
                    warnings.append(
                        f"Low RAM per core: {ram_per_core:.1f} GB. "
                        "Consider using fewer cores."
                    )
            if not self._mpi_path:
                warnings.append(
                    "No MPI path specified. Set the MPI command above.")
        elif not self._mpi_path:
            warnings.append(
                "MPI runtime not found. Install OpenMPI or MPICH, "
                "or specify the path above to enable parallel execution."
            )

        if warnings:
            self._warn_lbl.setText("\n".join(f"  {w}" for w in warnings))
            self._warn_lbl.setStyleSheet("color: #c0a040;")
        else:
            self._warn_lbl.setText("No warnings.")
            self._warn_lbl.setStyleSheet("color: #5ca060;")

    def _update_cmd_preview(self):
        mpi_path = self._mpi_path_edit.text().strip()
        exe_name = "complab.exe" if sys.platform == "win32" else "./complab"
        if self._enabled and mpi_path and self._num_cores > 1:
            self._cmd_lbl.setText(
                f"{mpi_path} -np {self._num_cores} {exe_name}"
            )
        else:
            self._cmd_lbl.setText(exe_name)

    # ── Public API ─────────────────────────────────────────────

    def is_parallel_enabled(self) -> bool:
        return self._enabled and bool(self._mpi_path) and self._num_cores > 1

    def get_num_cores(self) -> int:
        return self._num_cores if self._enabled else 1

    def get_mpi_command(self) -> str:
        return self._mpi_path_edit.text().strip() or self._mpi_cmd

    def validate_for_domain(self, nx: int, ny: int, nz: int):
        """Update warnings based on domain size vs core count."""
        n_cells = nx * ny * nz
        extra = []
        if self._enabled and self._num_cores > 1:
            if n_cells < 1000:
                extra.append(
                    f"Domain too small ({n_cells:,} cells) for parallel. "
                    "Overhead may outweigh speedup."
                )
            cells_per_core = n_cells / self._num_cores
            if cells_per_core < 100:
                extra.append(
                    f"Only {cells_per_core:.0f} cells/core. "
                    "Consider using fewer cores for this domain."
                )
            min_dim = min(nx, ny, nz)
            if self._num_cores > min_dim:
                extra.append(
                    f"Cores ({self._num_cores}) > smallest dimension "
                    f"({min_dim}). Domain cannot be split efficiently."
                )
        self._update_warnings()
        if extra:
            current = self._warn_lbl.text()
            all_warnings = current.rstrip()
            if all_warnings == "No warnings.":
                all_warnings = ""
            for w in extra:
                all_warnings += f"\n  {w}"
            self._warn_lbl.setText(all_warnings.strip())
            self._warn_lbl.setStyleSheet("color: #c0a040;")
