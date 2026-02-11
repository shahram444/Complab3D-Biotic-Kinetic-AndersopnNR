"""Domain configuration panel - grid, geometry (.dat), material numbers + preview."""

import os
from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QPushButton, QFileDialog,
)
from PySide6.QtCore import Signal
from .base_panel import BasePanel
from ..widgets.collapsible_section import CollapsibleSection
from ..widgets.geometry_preview import GeometryPreviewWidget


class DomainPanel(BasePanel):
    """Domain grid dimensions, geometry file, material numbers, and 2D preview."""

    geometry_loaded = Signal(str, int, int, int)  # filepath, nx, ny, nz

    def __init__(self, parent=None):
        super().__init__("Domain Settings", parent)
        self._geom_filepath = ""
        self._build_ui()

    def _build_ui(self):
        # Grid dimensions
        self.add_section("Grid Dimensions")
        form = self.add_form()
        self.nx = self.make_spin(50, 1)
        self.ny = self.make_spin(30, 1)
        self.nz = self.make_spin(30, 1)
        self.nx.setToolTip("Number of grid cells in X direction.\n"
                           "Note: solver adds +2 internally for ghost nodes.")
        form.addRow("nx:", self.nx)
        form.addRow("ny:", self.ny)
        form.addRow("nz:", self.nz)

        # Grid spacing
        self.add_section("Grid Spacing")
        form2 = self.add_form()
        self.dx = self.make_double_spin(1.0, 1e-12, 1e6, 6)
        self.unit = self.make_combo(["um", "mm", "m"])
        form2.addRow("dx:", self.dx)
        form2.addRow("Unit:", self.unit)
        self.char_length = self.make_double_spin(30.0, 0, 1e6, 4)
        self.char_length.setToolTip(
            "Characteristic length for Peclet number calculation.\n"
            "Typically the domain width in grid units.")
        form2.addRow("Characteristic length:", self.char_length)

        # Advanced: dy, dz
        adv = CollapsibleSection("Advanced Grid Spacing")
        adv_form = QFormLayout()
        self.dy = self.make_double_spin(0.0, 0, 1e6, 6)
        self.dy.setToolTip("Grid spacing in Y. 0 = use dx.")
        self.dz = self.make_double_spin(0.0, 0, 1e6, 6)
        self.dz.setToolTip("Grid spacing in Z. 0 = use dx.")
        adv_form.addRow("dy (0=dx):", self.dy)
        adv_form.addRow("dz (0=dx):", self.dz)
        adv.set_content_layout(adv_form)
        self.add_widget(adv)

        # Geometry file
        self.add_section("Geometry File (.dat)")
        form3 = self.add_form()
        row = QHBoxLayout()
        self.geom_file = self.make_line_edit("geometry.dat", "geometry.dat")
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_geometry)
        row.addWidget(self.geom_file)
        row.addWidget(browse_btn)
        form3.addRow("Filename:", row)

        self.add_widget(self.make_info_label(
            "Geometry file must be a .dat file with integer material numbers.\n"
            "Format: nx*ny*nz values, one slice per row."))

        # Material numbers
        self.add_section("Material Numbers")
        form4 = self.add_form()
        self.pore = self.make_line_edit("2")
        self.pore.setToolTip("Pore material number(s). Can be space-separated for multiple.")
        self.solid = self.make_line_edit("0")
        self.bounce_back = self.make_line_edit("1")
        form4.addRow("Pore:", self.pore)
        form4.addRow("Solid (no-dynamics):", self.solid)
        form4.addRow("Bounce-back:", self.bounce_back)

        self.add_widget(self.make_info_label(
            "Material numbers define what each voxel value represents.\n"
            "Microbe material numbers are set in the Microbiology section.\n"
            "CA biofilm can use multiple numbers (e.g., '3 6' for core + fringe)."))

        # Geometry 2D slice preview
        self.add_section("Geometry Preview")
        self._geom_preview = GeometryPreviewWidget()
        self._geom_preview.setMinimumHeight(250)
        self.add_widget(self._geom_preview)

        self.add_stretch()

        # Connect dimension changes to auto-reload preview + validation
        self.nx.valueChanged.connect(self._on_dimensions_changed)
        self.ny.valueChanged.connect(self._on_dimensions_changed)
        self.nz.valueChanged.connect(self._on_dimensions_changed)
        self.dx.valueChanged.connect(self._validate_inputs)
        self.pore.textChanged.connect(self._validate_material_numbers)
        self.solid.textChanged.connect(self._validate_material_numbers)
        self.bounce_back.textChanged.connect(self._validate_material_numbers)

    def _browse_geometry(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Geometry File", "",
            "DAT Files (*.dat);;All Files (*)")
        if path:
            self.geom_file.setText(os.path.basename(path))
            self._geom_filepath = path
            nx = self.nx.value()
            ny = self.ny.value()
            nz = self.nz.value()
            try:
                self.geometry_loaded.emit(path, nx, ny, nz)
            except Exception:
                pass
            # Load preview
            self._geom_preview.load_geometry(path, nx, ny, nz)

    def _try_load_preview(self):
        """Try to load geometry preview from current settings."""
        if self._geom_filepath and os.path.isfile(self._geom_filepath):
            self._geom_preview.load_geometry(
                self._geom_filepath,
                self.nx.value(), self.ny.value(), self.nz.value(),
            )

    def _on_dimensions_changed(self):
        """Auto-reload geometry preview when nx/ny/nz change."""
        self._validate_inputs()
        self._try_load_preview()

    def _validate_inputs(self):
        """Real-time validation of domain inputs."""
        nx, ny, nz = self.nx.value(), self.ny.value(), self.nz.value()
        n_cells = nx * ny * nz

        # Warn on very large domains (>50M cells)
        if n_cells > 50_000_000:
            self.set_validation(self.nx, "warning",
                                f"Large domain: {n_cells:,} cells. May require significant memory.")
        else:
            self.clear_validation(self.nx)

        # Validate dx > 0
        if self.dx.value() <= 0:
            self.set_validation(self.dx, "error", "Grid spacing must be positive.")
        else:
            self.clear_validation(self.dx)

    def _validate_material_numbers(self):
        """Validate that material number fields contain valid integers."""
        for widget, name in [(self.pore, "Pore"), (self.solid, "Solid"),
                             (self.bounce_back, "Bounce-back")]:
            text = widget.text().strip()
            if not text:
                self.set_validation(widget, "error", f"{name} material number is required.")
                continue
            try:
                parts = text.split()
                for p in parts:
                    int(p)
                self.clear_validation(widget)
            except ValueError:
                self.set_validation(widget, "error",
                                    f"{name}: must be space-separated integers.")

    def load_from_project(self, project):
        d = project.domain
        self.nx.setValue(d.nx)
        self.ny.setValue(d.ny)
        self.nz.setValue(d.nz)
        self.dx.setValue(d.dx)
        self.dy.setValue(d.dy)
        self.dz.setValue(d.dz)
        idx = {"um": 0, "mm": 1, "m": 2}.get(d.unit, 0)
        self.unit.setCurrentIndex(idx)
        self.char_length.setValue(d.characteristic_length)
        self.geom_file.setText(d.geometry_filename)
        self.pore.setText(d.pore)
        self.solid.setText(d.solid)
        self.bounce_back.setText(d.bounce_back)

    def save_to_project(self, project):
        d = project.domain
        d.nx = self.nx.value()
        d.ny = self.ny.value()
        d.nz = self.nz.value()
        d.dx = self.dx.value()
        d.dy = self.dy.value()
        d.dz = self.dz.value()
        d.unit = self.unit.currentText()
        d.characteristic_length = self.char_length.value()
        d.geometry_filename = self.geom_file.text()
        d.pore = self.pore.text().strip()
        d.solid = self.solid.text().strip()
        d.bounce_back = self.bounce_back.text().strip()
