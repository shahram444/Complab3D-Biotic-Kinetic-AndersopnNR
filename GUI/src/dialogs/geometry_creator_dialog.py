"""Geometry Creator Dialog - GUI-based geometry generation.

Opens as a separate dialog (not terminal) for creating .dat geometry files.
Supports:
  - Synthetic porous media generation (open channel, packed spheres, etc.)
  - BMP image stack import
  - Microbe distribution seeding
  - Geometry preview and statistics
  - Saves .dat file + README with metadata
"""

import os
import struct
import datetime
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox,
    QComboBox, QCheckBox, QTabWidget, QWidget, QProgressBar,
    QTextEdit, QDoubleSpinBox, QMessageBox, QDialogButtonBox,
)
from PySide6.QtCore import Qt, Signal, QThread


class GeometryWorker(QThread):
    """Worker thread for geometry generation."""

    progress = Signal(int, str)
    finished = Signal(bool, str, str)  # success, message, output_path

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            p = self.params
            mode = p["mode"]
            nx, ny, nz = p["nx"], p["ny"], p["nz"]
            pore_val = p["pore_mat"]
            solid_val = p["solid_mat"]
            bb_val = p["bb_mat"]
            microbe_val = p.get("microbe_mat", 3)
            output_path = p["output_path"]
            output_dir = os.path.dirname(output_path) or "."

            total = nx * ny * nz
            self.progress.emit(5, f"Creating {nx}x{ny}x{nz} domain ({total:,} voxels)...")

            # Initialize domain
            geom = np.full((nx, ny, nz), pore_val, dtype=np.uint8)

            if mode == "open_channel":
                self.progress.emit(20, "Generating open channel...")
                # Bounce-back boundaries on y=0, y=ny-1, z=0, z=nz-1
                geom[:, 0, :] = bb_val
                geom[:, ny - 1, :] = bb_val
                geom[:, :, 0] = bb_val
                geom[:, :, nz - 1] = bb_val

            elif mode == "pipe":
                self.progress.emit(20, "Generating cylindrical pipe...")
                cy, cz = ny / 2.0, nz / 2.0
                radius = min(ny, nz) / 2.0 - 1
                for j in range(ny):
                    for k in range(nz):
                        dist = np.sqrt((j - cy + 0.5) ** 2 + (k - cz + 0.5) ** 2)
                        if dist > radius:
                            geom[:, j, k] = solid_val
                        elif dist > radius - 1:
                            geom[:, j, k] = bb_val

            elif mode == "random_spheres":
                self.progress.emit(20, "Generating random sphere packing...")
                n_spheres = p.get("n_spheres", 30)
                min_r = p.get("min_radius", 2)
                max_r = p.get("max_radius", 5)
                rng = np.random.default_rng(42)
                # Bounce-back walls
                geom[:, 0, :] = bb_val
                geom[:, ny - 1, :] = bb_val
                geom[:, :, 0] = bb_val
                geom[:, :, nz - 1] = bb_val
                for s_idx in range(n_spheres):
                    r = rng.integers(min_r, max_r + 1)
                    cx = rng.integers(r, nx - r)
                    cy = rng.integers(r + 1, ny - r - 1)
                    cz = rng.integers(r + 1, nz - r - 1)
                    for i in range(max(0, cx - r), min(nx, cx + r + 1)):
                        for j in range(max(1, cy - r), min(ny - 1, cy + r + 1)):
                            for k in range(max(1, cz - r), min(nz - 1, cz + r + 1)):
                                if (i - cx) ** 2 + (j - cy) ** 2 + (k - cz) ** 2 <= r * r:
                                    geom[i, j, k] = solid_val
                    if (s_idx + 1) % 5 == 0:
                        pct = 20 + int(40 * (s_idx + 1) / n_spheres)
                        self.progress.emit(pct, f"Placed {s_idx + 1}/{n_spheres} spheres...")

            elif mode == "bmp_import":
                self.progress.emit(20, "Importing BMP images...")
                bmp_folder = p["bmp_folder"]
                bmp_pattern = p.get("bmp_pattern", "*.bmp")
                threshold = p.get("threshold", 128)
                import glob
                files = sorted(glob.glob(os.path.join(bmp_folder, bmp_pattern)))
                if not files:
                    self.finished.emit(False, "No BMP files found.", "")
                    return
                try:
                    from PIL import Image
                except ImportError:
                    self.finished.emit(
                        False,
                        "Pillow (PIL) not installed. Run: pip install Pillow",
                        "")
                    return

                # Read first image to get dimensions
                img0 = Image.open(files[0]).convert("L")
                w, h = img0.size
                n_slices = len(files)
                geom = np.full((w, h, n_slices), pore_val, dtype=np.uint8)

                for k, fpath in enumerate(files):
                    img = np.array(Image.open(fpath).convert("L"))
                    for i in range(min(w, img.shape[1])):
                        for j in range(min(h, img.shape[0])):
                            if img[j, i] < threshold:
                                geom[i, j, k] = solid_val
                            else:
                                geom[i, j, k] = pore_val
                    if (k + 1) % 5 == 0:
                        pct = 20 + int(40 * (k + 1) / n_slices)
                        self.progress.emit(pct, f"Processed {k + 1}/{n_slices} slices...")

                nx, ny, nz = geom.shape

            else:
                # Default: simple open domain with walls
                self.progress.emit(20, "Generating simple open domain...")
                geom[:, 0, :] = bb_val
                geom[:, ny - 1, :] = bb_val
                geom[:, :, 0] = bb_val
                geom[:, :, nz - 1] = bb_val

            # Add microbe distribution if requested
            add_microbes = p.get("add_microbes", False)
            if add_microbes:
                self.progress.emit(70, "Adding microbe distribution...")
                dist_type = p.get("dist_type", "surface_layer")
                thickness = p.get("layer_thickness", 2)

                if dist_type == "surface_layer":
                    # Add microbes adjacent to solid surfaces
                    temp = geom.copy()
                    for i in range(nx):
                        for j in range(ny):
                            for k in range(nz):
                                if temp[i, j, k] == pore_val:
                                    # Check neighbors for solid/bb
                                    neighbors = []
                                    for di, dj, dk in [
                                        (-1, 0, 0), (1, 0, 0),
                                        (0, -1, 0), (0, 1, 0),
                                        (0, 0, -1), (0, 0, 1)
                                    ]:
                                        ni, nj, nk = i + di, j + dj, k + dk
                                        if (0 <= ni < nx and 0 <= nj < ny and
                                                0 <= nk < nz):
                                            neighbors.append(temp[ni, nj, nk])
                                    if solid_val in neighbors or bb_val in neighbors:
                                        geom[i, j, k] = microbe_val

                elif dist_type == "random_sparse":
                    frac = p.get("density_fraction", 0.05)
                    rng = np.random.default_rng(42)
                    for i in range(nx):
                        for j in range(ny):
                            for k in range(nz):
                                if geom[i, j, k] == pore_val:
                                    if rng.random() < frac:
                                        geom[i, j, k] = microbe_val

            self.progress.emit(85, "Writing geometry file...")

            # Write binary .dat file (column-major order matching MATLAB convention)
            os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "wb") as f:
                # Write in column-major (Fortran) order: z varies fastest
                for i in range(nx):
                    for j in range(ny):
                        for k in range(nz):
                            f.write(struct.pack("B", int(geom[i, j, k])))

            self.progress.emit(90, "Computing statistics...")

            # Compute statistics
            unique, counts = np.unique(geom, return_counts=True)
            total_voxels = nx * ny * nz
            pore_count = np.sum(geom == pore_val)
            solid_count = np.sum(geom == solid_val)
            bb_count = np.sum(geom == bb_val)
            microbe_count = np.sum(geom == microbe_val) if add_microbes else 0
            porosity = (pore_count + microbe_count) / total_voxels

            # Write README
            readme_path = output_path.replace(".dat", "_README.txt")
            with open(readme_path, "w") as f:
                f.write(f"CompLaB3D Geometry File Info\n")
                f.write(f"{'=' * 50}\n")
                f.write(f"Generated: {datetime.datetime.now().isoformat()}\n")
                f.write(f"File: {os.path.basename(output_path)}\n\n")
                f.write(f"Dimensions:\n")
                f.write(f"  nx = {nx}\n")
                f.write(f"  ny = {ny}\n")
                f.write(f"  nz = {nz}\n")
                f.write(f"  Total voxels = {total_voxels:,}\n\n")
                f.write(f"Material Numbers:\n")
                f.write(f"  Pore = {pore_val} ({pore_count:,} voxels, "
                        f"{100 * pore_count / total_voxels:.1f}%)\n")
                f.write(f"  Solid = {solid_val} ({solid_count:,} voxels, "
                        f"{100 * solid_count / total_voxels:.1f}%)\n")
                f.write(f"  Bounce-back = {bb_val} ({bb_count:,} voxels, "
                        f"{100 * bb_count / total_voxels:.1f}%)\n")
                if add_microbes:
                    f.write(f"  Microbe = {microbe_val} ({microbe_count:,} voxels, "
                            f"{100 * microbe_count / total_voxels:.1f}%)\n")
                f.write(f"\n  Porosity = {porosity:.4f}\n\n")
                f.write(f"Generation mode: {mode}\n")
                f.write(f"File format: unsigned 8-bit binary, column-major order\n")
                f.write(f"Expected file size: {total_voxels} bytes\n")

            self.progress.emit(100, "Done!")

            summary = (
                f"Geometry saved: {output_path}\n"
                f"Dimensions: {nx} x {ny} x {nz} = {total_voxels:,} voxels\n"
                f"Porosity: {porosity:.4f}\n"
                f"README: {readme_path}")

            self.finished.emit(True, summary, output_path)

        except Exception as e:
            self.finished.emit(False, f"Error: {e}", "")


class GeometryCreatorDialog(QDialog):
    """GUI dialog for creating geometry files."""

    def __init__(self, project=None, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Geometry Creator")
        self.setMinimumSize(700, 650)
        self._project = project
        self._config = config
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        heading = QLabel("Geometry Creator")
        heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(heading)

        info = QLabel(
            "Create geometry .dat files for CompLaB3D simulations. "
            "Choose a generation mode, configure parameters, and generate. "
            "The output includes a .dat binary file and a README with metadata.")
        info.setWordWrap(True)
        layout.addWidget(info)

        tabs = QTabWidget()

        # === Domain Tab ===
        domain_tab = QWidget()
        domain_layout = QVBoxLayout(domain_tab)

        size_group = QGroupBox("Domain Size")
        size_form = QFormLayout()

        self._nx_spin = QSpinBox()
        self._nx_spin.setRange(3, 1000)
        self._nx_spin.setValue(50)
        self._nx_spin.setToolTip(
            "Domain size in X direction (flow direction).\n"
            "Inlet at x=0, outlet at x=nx-1.")
        size_form.addRow("nx (flow direction):", self._nx_spin)

        self._ny_spin = QSpinBox()
        self._ny_spin.setRange(3, 1000)
        self._ny_spin.setValue(30)
        size_form.addRow("ny:", self._ny_spin)

        self._nz_spin = QSpinBox()
        self._nz_spin.setRange(3, 1000)
        self._nz_spin.setValue(30)
        size_form.addRow("nz:", self._nz_spin)

        size_group.setLayout(size_form)
        domain_layout.addWidget(size_group)

        # Geometry type
        type_group = QGroupBox("Geometry Type")
        type_form = QFormLayout()

        self._mode_combo = QComboBox()
        self._mode_combo.addItems([
            "Open Channel (walls on y/z boundaries)",
            "Cylindrical Pipe",
            "Random Sphere Packing",
            "Import BMP Image Stack",
        ])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        type_form.addRow("Mode:", self._mode_combo)

        # Sphere packing options
        self._n_spheres_spin = QSpinBox()
        self._n_spheres_spin.setRange(1, 1000)
        self._n_spheres_spin.setValue(30)
        type_form.addRow("Number of spheres:", self._n_spheres_spin)

        self._min_radius_spin = QSpinBox()
        self._min_radius_spin.setRange(1, 50)
        self._min_radius_spin.setValue(2)
        type_form.addRow("Min sphere radius:", self._min_radius_spin)

        self._max_radius_spin = QSpinBox()
        self._max_radius_spin.setRange(1, 50)
        self._max_radius_spin.setValue(5)
        type_form.addRow("Max sphere radius:", self._max_radius_spin)

        type_group.setLayout(type_form)
        domain_layout.addWidget(type_group)

        # BMP import options
        bmp_group = QGroupBox("BMP Import (if selected)")
        bmp_form = QFormLayout()

        bmp_row = QHBoxLayout()
        self._bmp_folder_edit = QLineEdit()
        self._bmp_folder_edit.setPlaceholderText("Folder with BMP slices...")
        bmp_browse = QPushButton("Browse...")
        bmp_browse.clicked.connect(self._browse_bmp)
        bmp_row.addWidget(self._bmp_folder_edit)
        bmp_row.addWidget(bmp_browse)
        bmp_form.addRow("BMP folder:", bmp_row)

        self._bmp_pattern_edit = QLineEdit("*.bmp")
        bmp_form.addRow("File pattern:", self._bmp_pattern_edit)

        self._threshold_spin = QSpinBox()
        self._threshold_spin.setRange(0, 255)
        self._threshold_spin.setValue(128)
        self._threshold_spin.setToolTip(
            "Pixels below this value = solid, above = pore.")
        bmp_form.addRow("Threshold:", self._threshold_spin)

        bmp_group.setLayout(bmp_form)
        domain_layout.addWidget(bmp_group)

        domain_layout.addStretch()
        tabs.addTab(domain_tab, "Domain")

        # === Materials Tab ===
        mat_tab = QWidget()
        mat_layout = QVBoxLayout(mat_tab)

        mat_group = QGroupBox("Material Numbers")
        mat_form = QFormLayout()

        self._pore_mat_spin = QSpinBox()
        self._pore_mat_spin.setRange(0, 255)
        self._pore_mat_spin.setValue(2)
        mat_form.addRow("Pore:", self._pore_mat_spin)

        self._solid_mat_spin = QSpinBox()
        self._solid_mat_spin.setRange(0, 255)
        self._solid_mat_spin.setValue(0)
        mat_form.addRow("Solid:", self._solid_mat_spin)

        self._bb_mat_spin = QSpinBox()
        self._bb_mat_spin.setRange(0, 255)
        self._bb_mat_spin.setValue(1)
        mat_form.addRow("Bounce-back:", self._bb_mat_spin)

        mat_group.setLayout(mat_form)
        mat_layout.addWidget(mat_group)

        # Microbe distribution
        mic_group = QGroupBox("Microbe Distribution (Optional)")
        mic_form = QFormLayout()

        self._add_microbes_check = QCheckBox("Add microbes to geometry")
        mic_form.addRow("", self._add_microbes_check)

        self._microbe_mat_spin = QSpinBox()
        self._microbe_mat_spin.setRange(0, 255)
        self._microbe_mat_spin.setValue(3)
        mic_form.addRow("Microbe material:", self._microbe_mat_spin)

        self._dist_combo = QComboBox()
        self._dist_combo.addItems([
            "Surface Layer (biofilm on walls)",
            "Random Sparse (scattered)",
        ])
        mic_form.addRow("Distribution:", self._dist_combo)

        self._layer_spin = QSpinBox()
        self._layer_spin.setRange(1, 20)
        self._layer_spin.setValue(2)
        mic_form.addRow("Layer thickness:", self._layer_spin)

        self._density_spin = QDoubleSpinBox()
        self._density_spin.setRange(0.001, 0.5)
        self._density_spin.setDecimals(3)
        self._density_spin.setValue(0.05)
        mic_form.addRow("Random fraction:", self._density_spin)

        mic_group.setLayout(mic_form)
        mat_layout.addWidget(mic_group)

        mat_layout.addStretch()
        tabs.addTab(mat_tab, "Materials")

        # === Output Tab ===
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)

        out_group = QGroupBox("Output")
        out_form = QFormLayout()

        out_row = QHBoxLayout()
        self._output_edit = QLineEdit("geometry.dat")
        out_browse = QPushButton("Browse...")
        out_browse.clicked.connect(self._browse_output)
        out_row.addWidget(self._output_edit)
        out_row.addWidget(out_browse)
        out_form.addRow("Output file:", out_row)

        out_group.setLayout(out_form)
        output_layout.addWidget(out_group)

        # Generate button
        gen_row = QHBoxLayout()
        self._gen_btn = QPushButton("Generate Geometry")
        self._gen_btn.setStyleSheet(
            "QPushButton { background: #0078d4; color: white; "
            "padding: 8px 24px; font-weight: bold; }")
        self._gen_btn.clicked.connect(self._generate)
        gen_row.addWidget(self._gen_btn)
        gen_row.addStretch()
        output_layout.addLayout(gen_row)

        # Progress
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        output_layout.addWidget(self._progress)

        self._status_lbl = QLabel("")
        output_layout.addWidget(self._status_lbl)

        # Result
        self._result_text = QTextEdit()
        self._result_text.setReadOnly(True)
        self._result_text.setMaximumHeight(200)
        output_layout.addWidget(self._result_text)

        output_layout.addStretch()
        tabs.addTab(output_tab, "Generate")

        layout.addWidget(tabs)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # Initialize state
        self._on_mode_changed(0)

        # Pre-fill from project if available
        if self._project:
            self._nx_spin.setValue(self._project.domain.nx)
            self._ny_spin.setValue(self._project.domain.ny)
            self._nz_spin.setValue(self._project.domain.nz)
            try:
                self._pore_mat_spin.setValue(int(self._project.domain.pore))
                self._solid_mat_spin.setValue(int(self._project.domain.solid))
                self._bb_mat_spin.setValue(int(self._project.domain.bounce_back))
            except ValueError:
                pass

    def _on_mode_changed(self, index):
        is_spheres = (index == 2)
        self._n_spheres_spin.setEnabled(is_spheres)
        self._min_radius_spin.setEnabled(is_spheres)
        self._max_radius_spin.setEnabled(is_spheres)

        is_bmp = (index == 3)
        self._bmp_folder_edit.setEnabled(is_bmp)
        self._bmp_pattern_edit.setEnabled(is_bmp)
        self._threshold_spin.setEnabled(is_bmp)

        # Disable domain size for BMP (determined by images)
        self._nx_spin.setEnabled(not is_bmp)
        self._ny_spin.setEnabled(not is_bmp)
        self._nz_spin.setEnabled(not is_bmp)

    def _browse_bmp(self):
        path = QFileDialog.getExistingDirectory(self, "Select BMP Folder")
        if path:
            self._bmp_folder_edit.setText(path)

    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Geometry File", "geometry.dat",
            "DAT Files (*.dat);;All Files (*)")
        if path:
            self._output_edit.setText(path)

    def _generate(self):
        mode_idx = self._mode_combo.currentIndex()
        modes = ["open_channel", "pipe", "random_spheres", "bmp_import"]
        mode = modes[mode_idx]

        output_path = self._output_edit.text().strip()
        if not output_path:
            QMessageBox.warning(self, "Error", "Please specify an output file.")
            return

        if mode == "bmp_import" and not self._bmp_folder_edit.text().strip():
            QMessageBox.warning(self, "Error", "Please select a BMP folder.")
            return

        params = {
            "mode": mode,
            "nx": self._nx_spin.value(),
            "ny": self._ny_spin.value(),
            "nz": self._nz_spin.value(),
            "pore_mat": self._pore_mat_spin.value(),
            "solid_mat": self._solid_mat_spin.value(),
            "bb_mat": self._bb_mat_spin.value(),
            "microbe_mat": self._microbe_mat_spin.value(),
            "output_path": output_path,
            "add_microbes": self._add_microbes_check.isChecked(),
            "dist_type": ["surface_layer", "random_sparse"][
                self._dist_combo.currentIndex()],
            "layer_thickness": self._layer_spin.value(),
            "density_fraction": self._density_spin.value(),
            "n_spheres": self._n_spheres_spin.value(),
            "min_radius": self._min_radius_spin.value(),
            "max_radius": self._max_radius_spin.value(),
            "bmp_folder": self._bmp_folder_edit.text().strip(),
            "bmp_pattern": self._bmp_pattern_edit.text().strip(),
            "threshold": self._threshold_spin.value(),
        }

        self._gen_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status_lbl.setText("Generating...")
        self._result_text.clear()

        self._worker = GeometryWorker(params)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, pct, msg):
        self._progress.setValue(pct)
        self._status_lbl.setText(msg)

    def _on_finished(self, success, message, output_path):
        self._gen_btn.setEnabled(True)
        self._progress.setValue(100 if success else 0)

        if success:
            self._status_lbl.setText("Generation complete!")
            self._status_lbl.setStyleSheet("color: #5ca060;")
            self._result_text.setPlainText(message)
        else:
            self._status_lbl.setText(f"Failed: {message}")
            self._status_lbl.setStyleSheet("color: #c75050;")
            self._result_text.setPlainText(f"ERROR: {message}")
