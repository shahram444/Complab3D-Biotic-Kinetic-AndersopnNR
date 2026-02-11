"""Parallel execution panel - MPI auto-detect, core selection, and validation."""

import os
import shutil
import multiprocessing
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QSlider, QSpinBox,
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
            mpi_str = f"{self._mpi_cmd} found"
            self._mpi_lbl = QLabel(mpi_str)
            self._mpi_lbl.setStyleSheet("color: #5ca060; font-weight: bold;")
        else:
            self._mpi_lbl = QLabel("Not found - install MPI to enable")
            self._mpi_lbl.setStyleSheet("color: #c75050;")
        det_form.addRow("MPI:", self._mpi_lbl)

        if self._mpi_path:
            path_lbl = QLabel(self._mpi_path)
            path_lbl.setProperty("info", True)
            path_lbl.setWordWrap(True)
            det_form.addRow("Path:", path_lbl)

        # ── Enable MPI ─────────────────────────────────────────
        self.add_section("Configuration")
        cfg_form = self.add_form()

        self._enable_cb = self.make_checkbox("Enable MPI Parallel")
        self._enable_cb.setEnabled(bool(self._mpi_cmd))
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
        self._cmd_lbl = QLabel("complab.exe CompLaB.xml")
        self._cmd_lbl.setWordWrap(True)
        self._cmd_lbl.setStyleSheet(
            "font-family: Consolas, monospace; padding: 4px;"
        )
        self.add_widget(self._cmd_lbl)
        self._update_cmd_preview()

        self.add_stretch()

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
                # Rough estimate: warn if < 1 GB per core
                ram_per_core = self._total_ram / self._num_cores
                if ram_per_core < 1.0:
                    warnings.append(
                        f"Low RAM per core: {ram_per_core:.1f} GB. "
                        "Consider using fewer cores."
                    )
        if not self._mpi_cmd:
            warnings.append(
                "MPI runtime not found. Install OpenMPI or MPICH to enable "
                "parallel execution."
            )

        if warnings:
            self._warn_lbl.setText("\n".join(f"  {w}" for w in warnings))
            self._warn_lbl.setStyleSheet("color: #c0a040;")
        else:
            self._warn_lbl.setText("No warnings.")
            self._warn_lbl.setStyleSheet("color: #5ca060;")

    def _update_cmd_preview(self):
        if self._enabled and self._mpi_cmd and self._num_cores > 1:
            self._cmd_lbl.setText(
                f"{self._mpi_cmd} -np {self._num_cores} complab.exe CompLaB.xml"
            )
        else:
            self._cmd_lbl.setText("complab.exe CompLaB.xml")

    # ── Public API ─────────────────────────────────────────────

    def is_parallel_enabled(self) -> bool:
        return self._enabled and bool(self._mpi_cmd) and self._num_cores > 1

    def get_num_cores(self) -> int:
        return self._num_cores if self._enabled else 1

    def get_mpi_command(self) -> str:
        return self._mpi_cmd

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
            # Warn if cores > any dimension (poor decomposition)
            min_dim = min(nx, ny, nz)
            if self._num_cores > min_dim:
                extra.append(
                    f"Cores ({self._num_cores}) > smallest dimension "
                    f"({min_dim}). Domain cannot be split efficiently."
                )
        # Rebuild warnings with domain-aware info
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
