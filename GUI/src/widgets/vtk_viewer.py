"""3D visualization widget with VTK or fallback."""

import os
import struct
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt

try:
    import vtk
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    HAS_VTK = True
except ImportError:
    HAS_VTK = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class VTKViewerWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 4, 4, 4)

        self._open_btn = QPushButton("Open File")
        self._open_btn.clicked.connect(self._open_file)

        self._reset_btn = QPushButton("Reset View")
        self._reset_btn.clicked.connect(self._reset_view)

        self._view_combo = QComboBox()
        self._view_combo.addItems(["+X", "-X", "+Y", "-Y", "+Z", "-Z", "Isometric"])
        self._view_combo.setCurrentText("Isometric")
        self._view_combo.currentTextChanged.connect(self._set_view_preset)

        self._display_combo = QComboBox()
        self._display_combo.addItems(["Surface", "Wireframe", "Points"])
        self._display_combo.currentTextChanged.connect(self._set_display_mode)

        self._info_label = QLabel("")
        self._info_label.setProperty("info", True)

        toolbar.addWidget(self._open_btn)
        toolbar.addWidget(self._reset_btn)
        toolbar.addWidget(QLabel("View:"))
        toolbar.addWidget(self._view_combo)
        toolbar.addWidget(QLabel("Display:"))
        toolbar.addWidget(self._display_combo)
        toolbar.addStretch()
        toolbar.addWidget(self._info_label)

        layout.addLayout(toolbar)

        if HAS_VTK:
            self._vtk_widget = QVTKRenderWindowInteractor(self)
            self._renderer = vtk.vtkRenderer()
            self._renderer.SetBackground(0.12, 0.12, 0.12)
            self._vtk_widget.GetRenderWindow().AddRenderer(self._renderer)

            style = vtk.vtkInteractorStyleTrackballCamera()
            self._vtk_widget.GetRenderWindow().GetInteractor().SetInteractorStyle(style)

            layout.addWidget(self._vtk_widget)
            self._actor = None
        else:
            fallback = QLabel(
                "VTK is not installed.\n\n"
                "Install with: pip install vtk\n\n"
                "Alternatively, use ParaView to view .vti output files."
            )
            fallback.setAlignment(Qt.AlignmentFlag.AlignCenter)
            fallback.setProperty("info", True)
            layout.addWidget(fallback)

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Visualization File", "",
            "VTK ImageData (*.vti);;VTK Legacy (*.vtk);;Geometry (*.dat);;All Files (*)")
        if path:
            self.load_file(path)

    def load_file(self, filepath):
        if not HAS_VTK:
            return
        filepath = str(filepath)
        ext = Path(filepath).suffix.lower()

        try:
            if ext == ".vti":
                self._load_vti(filepath)
            elif ext == ".vtk":
                self._load_vtk(filepath)
            elif ext == ".dat":
                self._load_dat(filepath)
            else:
                QMessageBox.warning(self, "Unsupported", f"Unsupported file format: {ext}")
                return
            self._current_file = filepath
            self._info_label.setText(Path(filepath).name)
        except Exception as e:
            QMessageBox.critical(self, "Load Error", str(e))

    def _load_vti(self, filepath):
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(filepath)
        reader.Update()
        self._display_structured(reader.GetOutput())

    def _load_vtk(self, filepath):
        reader = vtk.vtkStructuredPointsReader()
        reader.SetFileName(filepath)
        reader.Update()
        self._display_structured(reader.GetOutput())

    def _load_dat(self, filepath):
        """Load headerless .dat geometry file. Requires dimensions set externally."""
        if not HAS_NUMPY:
            QMessageBox.warning(self, "NumPy Required", "NumPy is required to load .dat files.")
            return

        with open(filepath, "r") as f:
            values = []
            for line in f:
                line = line.strip()
                if line:
                    try:
                        values.append(int(line))
                    except ValueError:
                        try:
                            values.append(int(float(line)))
                        except ValueError:
                            continue

        if not values:
            QMessageBox.warning(self, "Empty File", "No valid data found in .dat file.")
            return

        n = len(values)
        # Try to infer cubic dimensions
        side = round(n ** (1 / 3))
        if side ** 3 != n:
            QMessageBox.warning(
                self, "Dimension Mismatch",
                f"File has {n} values. Cannot auto-detect 3D dimensions.\n"
                "Set domain dimensions in the Domain panel first."
            )
            return

        arr = np.array(values, dtype=np.int32).reshape((side, side, side))
        self._display_voxels(arr)

    def _display_structured(self, data):
        threshold = vtk.vtkThreshold()
        threshold.SetInputData(data)
        threshold.SetUpperThreshold(0.5)
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_UPPER)
        threshold.Update()

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputConnection(threshold.GetOutputPort())
        mapper.ScalarVisibilityOn()

        if self._actor:
            self._renderer.RemoveActor(self._actor)

        self._actor = vtk.vtkActor()
        self._actor.SetMapper(mapper)
        self._renderer.AddActor(self._actor)
        self._renderer.ResetCamera()
        self._vtk_widget.GetRenderWindow().Render()

    def _display_voxels(self, arr):
        nx, ny, nz = arr.shape
        image_data = vtk.vtkImageData()
        image_data.SetDimensions(nx, ny, nz)
        image_data.SetSpacing(1.0, 1.0, 1.0)
        image_data.AllocateScalars(vtk.VTK_INT, 1)

        for i in range(nx):
            for j in range(ny):
                for k in range(nz):
                    image_data.SetScalarComponentFromFloat(i, j, k, 0, float(arr[i, j, k]))

        self._display_structured(image_data)

    def _reset_view(self):
        if HAS_VTK:
            self._renderer.ResetCamera()
            self._vtk_widget.GetRenderWindow().Render()

    def _set_view_preset(self, name):
        if not HAS_VTK:
            return
        camera = self._renderer.GetActiveCamera()
        camera.SetFocalPoint(0, 0, 0)
        presets = {
            "+X": (1, 0, 0, 0, 0, 1),
            "-X": (-1, 0, 0, 0, 0, 1),
            "+Y": (0, 1, 0, 0, 0, 1),
            "-Y": (0, -1, 0, 0, 0, 1),
            "+Z": (0, 0, 1, 0, 1, 0),
            "-Z": (0, 0, -1, 0, 1, 0),
            "Isometric": (1, 1, 1, 0, 0, 1),
        }
        if name in presets:
            px, py, pz, ux, uy, uz = presets[name]
            camera.SetPosition(px * 100, py * 100, pz * 100)
            camera.SetViewUp(ux, uy, uz)
        self._renderer.ResetCamera()
        self._vtk_widget.GetRenderWindow().Render()

    def _set_display_mode(self, mode):
        if not HAS_VTK or not self._actor:
            return
        modes = {"Surface": 1, "Wireframe": 0, "Points": 2}
        rep = modes.get(mode, 1)
        self._actor.GetProperty().SetRepresentation(rep)
        self._vtk_widget.GetRenderWindow().Render()
