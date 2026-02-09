"""Domain configuration panel - grid, geometry (.dat), materials."""

import os
import threading
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget,
    QPushButton, QFileDialog, QGroupBox, QMessageBox,
)
from PySide6.QtCore import Qt, Signal, QThread

from .base_panel import BasePanel

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class DomainPanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("Domain"))
        layout.addWidget(self._create_subheading("Grid dimensions, geometry file, and material assignments."))

        # --- Grid Dimensions ---
        grid_group = self._create_group("Grid Dimensions")
        gf = self._create_form()
        self._nx = self._create_spin(1, 10000, 50)
        self._ny = self._create_spin(1, 10000, 30)
        self._nz = self._create_spin(1, 10000, 30)
        gf.addRow("Nx (streamwise):", self._nx)
        gf.addRow("Ny (lateral):", self._ny)
        gf.addRow("Nz (vertical):", self._nz)
        grid_group.setLayout(gf)
        layout.addWidget(grid_group)

        # --- Grid Spacing ---
        space_group = self._create_group("Grid Spacing")
        sf = self._create_form()
        self._dx = self._create_double_spin(1e-10, 1e6, 1.0, 6, 0.1)
        self._unit = self._create_combo(["um", "mm", "cm", "m"], "um")
        self._char_length = self._create_double_spin(0.001, 1e6, 30.0, 3, 1.0)
        sf.addRow("dx (grid spacing):", self._dx)
        sf.addRow("Unit:", self._unit)
        sf.addRow("Characteristic length:", self._char_length)
        space_group.setLayout(sf)
        layout.addWidget(space_group)

        # --- Geometry File ---
        geom_group = self._create_group("Geometry File (.dat)")
        gl = QVBoxLayout(geom_group)
        file_row = QHBoxLayout()
        self._geom_file = self._create_line_edit("geometry.dat", "geometry.dat")
        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setFixedWidth(80)
        self._browse_btn.clicked.connect(self._browse_geometry)
        file_row.addWidget(self._geom_file)
        file_row.addWidget(self._browse_btn)
        gl.addLayout(file_row)

        self._validate_btn = QPushButton("Validate Geometry")
        self._validate_btn.clicked.connect(self._validate_geometry)
        gl.addWidget(self._validate_btn)

        self._geom_info = QLabel("Load a .dat file to see geometry statistics.")
        self._geom_info.setProperty("info", True)
        self._geom_info.setWordWrap(True)
        gl.addWidget(self._geom_info)
        layout.addWidget(geom_group)

        # --- Material Numbers ---
        mat_group = self._create_group("Material Numbers")
        mf = self._create_form()
        self._pore_mat = self._create_spin(0, 255, 2)
        self._solid_mat = self._create_spin(0, 255, 0)
        self._bb_mat = self._create_spin(0, 255, 1)
        mf.addRow("Pore:", self._pore_mat)
        mf.addRow("Solid:", self._solid_mat)
        mf.addRow("Bounce-back:", self._bb_mat)
        mat_info = QLabel(
            "Microbe material numbers are set per-species in the Microbiology panel.")
        mat_info.setProperty("info", True)
        mat_info.setWordWrap(True)
        mat_group.setLayout(mf)
        mv = QVBoxLayout()
        mv.addLayout(mf)
        mv.addWidget(mat_info)
        mat_group.setLayout(mv)
        layout.addWidget(mat_group)

        # --- Summary ---
        summary_group = self._create_group("Domain Summary")
        self._summary = QLabel("")
        self._summary.setWordWrap(True)
        sl = QVBoxLayout(summary_group)
        sl.addWidget(self._summary)
        layout.addWidget(summary_group)

        layout.addStretch()

        # Connect dimension changes to summary update
        self._nx.valueChanged.connect(self._update_summary)
        self._ny.valueChanged.connect(self._update_summary)
        self._nz.valueChanged.connect(self._update_summary)
        self._dx.valueChanged.connect(self._update_summary)
        self._unit.currentTextChanged.connect(self._update_summary)
        self._update_summary()

        outer.addWidget(self._create_scroll_area(w))

    def _browse_geometry(self):
        start_dir = ""
        if self._project and self._project.project_dir:
            inp = Path(self._project.project_dir) / self._project.paths.input_path
            if inp.is_dir():
                start_dir = str(inp)
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Geometry File", start_dir,
            "DAT Files (*.dat);;All Files (*)")
        if path:
            self._geom_file.setText(Path(path).name)
            self._emit_changed()

    def _validate_geometry(self):
        if not HAS_NUMPY:
            QMessageBox.warning(self, "NumPy Required", "NumPy is required for geometry validation.")
            return
        if not self._project:
            QMessageBox.warning(self, "No Project", "Open or create a project first.")
            return

        filename = self._geom_file.text().strip()
        if not filename:
            return

        # Search for the file
        candidates = []
        if self._project.project_dir:
            candidates.append(Path(self._project.project_dir) / self._project.paths.input_path / filename)
            candidates.append(Path(self._project.project_dir) / filename)
        candidates.append(Path(filename))

        filepath = None
        for c in candidates:
            if c.exists():
                filepath = c
                break

        if filepath is None:
            self._geom_info.setText(f"File not found: {filename}")
            self._geom_info.setProperty("error", True)
            self._geom_info.style().polish(self._geom_info)
            return

        try:
            with open(filepath, "r") as f:
                values = [int(line.strip()) for line in f if line.strip()]

            total = len(values)
            expected = self._nx.value() * self._ny.value() * self._nz.value()

            arr = np.array(values)
            unique, counts = np.unique(arr, return_counts=True)
            mat_info = ", ".join(f"{u}: {c}" for u, c in zip(unique, counts))
            porosity = np.sum(arr == self._pore_mat.value()) / total * 100 if total > 0 else 0

            status = "VALID" if total == expected else "MISMATCH"
            text = (
                f"Status: {status}\n"
                f"Values in file: {total:,}\n"
                f"Expected (Nx*Ny*Nz): {expected:,}\n"
                f"Material counts: {mat_info}\n"
                f"Porosity: {porosity:.1f}%"
            )
            self._geom_info.setText(text)
            is_err = total != expected
            self._geom_info.setProperty("error", is_err)
            self._geom_info.setProperty("success", not is_err)
            self._geom_info.style().polish(self._geom_info)
        except Exception as e:
            self._geom_info.setText(f"Error reading file: {e}")
            self._geom_info.setProperty("error", True)
            self._geom_info.style().polish(self._geom_info)

    def _update_summary(self):
        nx, ny, nz = self._nx.value(), self._ny.value(), self._nz.value()
        dx = self._dx.value()
        unit = self._unit.currentText()
        total = nx * ny * nz
        mem_mb = total * 8 * 20 / (1024 * 1024)  # rough estimate
        self._summary.setText(
            f"Total lattice nodes: {total:,}\n"
            f"Physical size: {nx * dx:.2f} x {ny * dx:.2f} x {nz * dx:.2f} {unit}\n"
            f"Estimated memory: ~{mem_mb:.0f} MB"
        )

    def _populate_fields(self):
        if not self._project:
            return
        d = self._project.domain
        self._nx.setValue(d.nx)
        self._ny.setValue(d.ny)
        self._nz.setValue(d.nz)
        self._dx.setValue(d.dx)
        idx = self._unit.findText(d.unit)
        if idx >= 0:
            self._unit.setCurrentIndex(idx)
        self._char_length.setValue(d.characteristic_length)
        self._geom_file.setText(d.geometry_file)
        self._pore_mat.setValue(d.pore_material)
        self._solid_mat.setValue(d.solid_material)
        self._bb_mat.setValue(d.bounce_back_material)
        self._update_summary()

    def collect_data(self, project):
        project.domain.nx = self._nx.value()
        project.domain.ny = self._ny.value()
        project.domain.nz = self._nz.value()
        project.domain.dx = self._dx.value()
        project.domain.unit = self._unit.currentText()
        project.domain.characteristic_length = self._char_length.value()
        project.domain.geometry_file = self._geom_file.text().strip()
        project.domain.pore_material = self._pore_mat.value()
        project.domain.solid_material = self._solid_mat.value()
        project.domain.bounce_back_material = self._bb_mat.value()
