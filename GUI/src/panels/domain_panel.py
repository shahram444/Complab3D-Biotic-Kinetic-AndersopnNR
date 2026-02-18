"""Domain configuration panel - grid, geometry (.dat), material numbers + preview."""

import os
import shutil
from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QPushButton, QFileDialog,
    QDialog, QVBoxLayout, QLabel, QComboBox, QDialogButtonBox,
    QMessageBox,
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
            "Browse a .dat file to auto-detect dimensions and copy to input/.\n"
            "The file must contain integer material numbers (nx*ny*nz values)."))

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

    # ── Geometry file browsing with auto-detect ─────────────────────

    def _browse_geometry(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Geometry File", "",
            "DAT Files (*.dat);;All Files (*)")
        if not path:
            return

        basename = os.path.basename(path)
        self.geom_file.setText(basename)
        self._geom_filepath = path

        # Count values and try to auto-detect dimensions
        total, nz_from_lines = self._analyze_dat_file(path)
        if total <= 0:
            QMessageBox.warning(
                self, "Invalid File",
                f"Could not read any integer values from:\n{basename}")
            return

        current_nx = self.nx.value()
        current_ny = self.ny.value()
        current_nz = self.nz.value()

        # If current dimensions already match, just keep them
        if current_nx * current_ny * current_nz == total:
            self._finish_geometry_load(path, current_nx, current_ny, current_nz)
            return

        # Try to find valid factorizations
        factorizations = self._find_factorizations(total, nz_from_lines)

        if not factorizations:
            QMessageBox.warning(
                self, "Dimension Detection",
                f"File has {total:,} values but no valid 3D factorization found.\n"
                f"Please set nx, ny, nz manually so that nx*ny*nz = {total:,}.")
            return

        if len(factorizations) == 1:
            # Only one option - auto-apply
            nx, ny, nz = factorizations[0]
            self._apply_dimensions(nx, ny, nz)
            self._finish_geometry_load(path, nx, ny, nz)
            return

        # Multiple options - let user choose
        chosen = self._show_dimension_picker(basename, total, factorizations)
        if chosen:
            nx, ny, nz = chosen
            self._apply_dimensions(nx, ny, nz)
            self._finish_geometry_load(path, nx, ny, nz)

    def _apply_dimensions(self, nx, ny, nz):
        """Set the nx, ny, nz spin boxes (block signals to avoid preview thrash)."""
        self.nx.blockSignals(True)
        self.ny.blockSignals(True)
        self.nz.blockSignals(True)
        self.nx.setValue(nx)
        self.ny.setValue(ny)
        self.nz.setValue(nz)
        self.nx.blockSignals(False)
        self.ny.blockSignals(False)
        self.nz.blockSignals(False)

    def _finish_geometry_load(self, path, nx, ny, nz):
        """Emit signal and load preview after geometry is set."""
        try:
            self.geometry_loaded.emit(path, nx, ny, nz)
        except Exception:
            pass
        self._geom_preview.load_geometry(path, nx, ny, nz)
        self._validate_inputs()

    # ── .dat file analysis ──────────────────────────────────────────

    @staticmethod
    def _analyze_dat_file(filepath):
        """Count integer values and detect line structure in a .dat file.

        Handles both binary format (1 byte per voxel, used by the solver)
        and text format (one integer per line or space-separated).

        Returns (total_values, nz_hint) where nz_hint is the consistent
        tokens-per-line if > 1, or 0 if one-value-per-line / binary.
        """
        import numpy as np

        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return 0, 0

        # Try binary format first: raw bytes where every byte is a valid
        # material number (small integers, typically 0-10).
        try:
            raw = np.fromfile(filepath, dtype=np.uint8)
            if raw.max() <= 10:
                # Looks like binary: all values are small material numbers
                return int(raw.size), 0
        except Exception:
            pass

        # Fall back to text format
        total = 0
        tokens_per_line = {}  # count -> frequency

        try:
            with open(filepath, "r") as f:
                for line in f:
                    stripped = line.strip()
                    if not stripped:
                        continue
                    tokens = stripped.split()
                    valid = 0
                    for t in tokens:
                        try:
                            int(t)
                            valid += 1
                        except ValueError:
                            pass
                    total += valid
                    if valid > 0:
                        tokens_per_line[valid] = tokens_per_line.get(valid, 0) + 1
        except Exception:
            return 0, 0

        # Detect nz from consistent multi-value lines
        nz_hint = 0
        if tokens_per_line:
            # Find the most common token count
            most_common = max(tokens_per_line, key=tokens_per_line.get)
            if most_common > 1:
                # Check if at least 90% of lines have this count
                total_lines = sum(tokens_per_line.values())
                if tokens_per_line[most_common] >= total_lines * 0.9:
                    nz_hint = most_common

        return total, nz_hint

    @staticmethod
    def _find_factorizations(total, nz_hint=0):
        """Find valid (nx, ny, nz) triples where nx*ny*nz == total.

        Constraints: all dimensions >= 3 (solver needs at least 3 for ghost nodes).
        If nz_hint > 0, only consider factorizations with nz == nz_hint.
        Returns list sorted by how "cubic" the shape is (most balanced first).
        """
        if total < 27:  # 3*3*3 minimum
            return []

        results = []
        # If nz is known from line structure, constrain it
        nz_candidates = [nz_hint] if nz_hint > 0 else None

        if nz_candidates is None:
            # Find all divisors of total for nz
            nz_candidates = []
            for nz in range(3, int(total ** (1/3)) + 2):
                if total % nz == 0:
                    nz_candidates.append(nz)

        for nz in nz_candidates:
            if nz < 3 or total % nz != 0:
                continue
            remaining = total // nz
            for ny in range(nz, int(remaining ** 0.5) + 1):
                if remaining % ny != 0:
                    continue
                nx = remaining // ny
                if nx < 3:
                    continue
                # nx >= ny >= nz (canonical ordering, nx is longest axis)
                results.append((nx, ny, nz))

        # Also add permutations where ny > nx (user might have thin domains)
        expanded = set()
        for nx, ny, nz in results:
            # Add all permutations but keep nz fixed if we had a hint
            if nz_hint > 0:
                expanded.add((nx, ny, nz))
                expanded.add((ny, nx, nz))
            else:
                for perm in [(nx, ny, nz), (nx, nz, ny), (ny, nx, nz),
                             (ny, nz, nx), (nz, nx, ny), (nz, ny, nx)]:
                    if all(d >= 3 for d in perm):
                        expanded.add(perm)

        # Sort: prefer most "cubic" (smallest max/min ratio), then nx descending
        result_list = sorted(expanded,
                             key=lambda t: (max(t) / max(min(t), 1), -t[0]))

        # Deduplicate and limit to reasonable number
        return result_list[:20]

    def _show_dimension_picker(self, filename, total, factorizations):
        """Show a dialog for the user to pick dimensions. Returns (nx, ny, nz) or None."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Detect Dimensions")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel(
            f"<b>{filename}</b> has <b>{total:,}</b> values.\n"))
        layout.addWidget(QLabel(
            "Select the grid dimensions (nx * ny * nz):"))

        combo = QComboBox()
        for nx, ny, nz in factorizations:
            combo.addItem(f"nx={nx}  ny={ny}  nz={nz}   ({nx}x{ny}x{nz})")
        layout.addWidget(combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)

        if dlg.exec() == QDialog.Accepted:
            idx = combo.currentIndex()
            if 0 <= idx < len(factorizations):
                return factorizations[idx]
        return None

    # ── Copy to input directory ─────────────────────────────────────

    def copy_geometry_to_input(self, input_dir):
        """Copy the browsed geometry file into the project's input directory.

        Call this from main_window after saving the project, so we know
        where the input directory is.  Returns the destination path or ''.
        """
        if not self._geom_filepath or not os.path.isfile(self._geom_filepath):
            return ""
        basename = os.path.basename(self._geom_filepath)
        dest = os.path.join(input_dir, basename)
        # Don't copy if already in the right place
        if os.path.abspath(self._geom_filepath) == os.path.abspath(dest):
            return dest
        os.makedirs(input_dir, exist_ok=True)
        shutil.copy2(self._geom_filepath, dest)
        self._geom_filepath = dest
        return dest

    # ── Other helpers ───────────────────────────────────────────────

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
