"""3D visualization widget using VTK or a placeholder fallback.

Provides geometry preview and result viewing capabilities.
Falls back gracefully if VTK is not installed.
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QFrame, QFileDialog, QSizePolicy,
)
from PySide6.QtCore import Qt

try:
    import vtk
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    HAS_VTK = True
except ImportError:
    HAS_VTK = False


class VTKViewer(QWidget):
    """Center panel: 3D visualization area."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._renderer = None
        self._vtk_widget = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(8, 4, 8, 4)

        lbl = QLabel("3D Viewer")
        lbl.setProperty("subheading", True)
        toolbar.addWidget(lbl)
        toolbar.addStretch()

        self._file_combo = QComboBox()
        self._file_combo.setFixedWidth(200)
        self._file_combo.setPlaceholderText("Select VTK file...")
        self._file_combo.currentIndexChanged.connect(self._on_file_changed)
        toolbar.addWidget(self._file_combo)

        open_btn = QPushButton("Open VTK")
        open_btn.setFixedWidth(80)
        open_btn.clicked.connect(self._open_vtk_file)
        toolbar.addWidget(open_btn)

        self._view_combo = QComboBox()
        self._view_combo.addItems(["+X", "-X", "+Y", "-Y", "+Z", "-Z", "Iso"])
        self._view_combo.setCurrentIndex(6)
        self._view_combo.setFixedWidth(60)
        self._view_combo.currentTextChanged.connect(self._set_view)
        toolbar.addWidget(self._view_combo)

        reset_btn = QPushButton("Reset")
        reset_btn.setFixedWidth(60)
        reset_btn.clicked.connect(self.reset_view)
        toolbar.addWidget(reset_btn)

        layout.addLayout(toolbar)

        # Viewer area
        if HAS_VTK:
            self._vtk_widget = QVTKRenderWindowInteractor(self)
            self._renderer = vtk.vtkRenderer()
            self._renderer.SetBackground(0.12, 0.12, 0.14)
            self._renderer.SetBackground2(0.18, 0.19, 0.21)
            self._renderer.GradientBackgroundOn()
            self._vtk_widget.GetRenderWindow().AddRenderer(self._renderer)
            layout.addWidget(self._vtk_widget, 1)
            self._vtk_widget.Initialize()
            self._add_axes()
        else:
            placeholder = QFrame()
            placeholder.setFrameStyle(QFrame.Shape.StyledPanel)
            placeholder.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            ph_layout = QVBoxLayout(placeholder)
            msg = QLabel("VTK not installed.\n\nInstall with: pip install vtk\n\n"
                         "Geometry and results will display here.")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setProperty("info", True)
            ph_layout.addWidget(msg)
            layout.addWidget(placeholder, 1)

    def _add_axes(self):
        """Add orientation axes widget."""
        if not HAS_VTK or not self._renderer:
            return
        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(axes)
        widget.SetInteractor(self._vtk_widget.GetRenderWindow().GetInteractor())
        widget.SetViewport(0.0, 0.0, 0.15, 0.15)
        widget.EnabledOn()
        widget.InteractiveOff()
        self._axes_widget = widget

    def load_vti(self, filepath: str):
        """Load a VTK ImageData (.vti) file."""
        if not HAS_VTK or not self._renderer:
            return
        self._renderer.RemoveAllViewProps()
        self._add_axes()

        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(filepath)
        reader.Update()

        data = reader.GetOutput()
        if data is None:
            return

        # Choose first array for display
        pd = data.GetPointData()
        if pd.GetNumberOfArrays() > 0:
            pd.SetActiveScalars(pd.GetArrayName(0))

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(data)
        mapper.ScalarVisibilityOn()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        self._renderer.AddActor(actor)

        # Add scalar bar
        sbar = vtk.vtkScalarBarActor()
        sbar.SetLookupTable(mapper.GetLookupTable())
        sbar.SetTitle(pd.GetArrayName(0) if pd.GetNumberOfArrays() > 0 else "")
        sbar.SetNumberOfLabels(5)
        self._renderer.AddActor2D(sbar)

        self._renderer.ResetCamera()
        self._render()

    def load_geometry_dat(self, filepath: str, nx: int, ny: int, nz: int):
        """Load a .dat geometry file as structured grid."""
        if not HAS_VTK or not self._renderer:
            return
        if not os.path.isfile(filepath):
            return

        try:
            with open(filepath, "r") as f:
                values = [int(x) for line in f for x in line.split()]
        except (ValueError, OSError):
            return

        expected = nx * ny * nz
        if len(values) < expected:
            return

        self._renderer.RemoveAllViewProps()
        self._add_axes()

        image = vtk.vtkImageData()
        image.SetDimensions(nx, ny, nz)

        arr = vtk.vtkIntArray()
        arr.SetName("Material")
        arr.SetNumberOfTuples(nx * ny * nz)
        for idx, val in enumerate(values[:expected]):
            arr.SetValue(idx, val)
        image.GetPointData().SetScalars(arr)

        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(image)
        mapper.ScalarVisibilityOn()

        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        self._renderer.AddActor(actor)
        self._renderer.ResetCamera()
        self._render()

    def reset_view(self):
        if self._renderer:
            self._renderer.ResetCamera()
            self._render()

    def clear_scene(self):
        if self._renderer:
            self._renderer.RemoveAllViewProps()
            self._add_axes()
            self._render()

    def _set_view(self, direction: str):
        if not self._renderer:
            return
        cam = self._renderer.GetActiveCamera()
        cam.SetFocalPoint(0, 0, 0)
        d = 100
        views = {
            "+X": (d, 0, 0, 0, 0, 1),
            "-X": (-d, 0, 0, 0, 0, 1),
            "+Y": (0, d, 0, 0, 0, 1),
            "-Y": (0, -d, 0, 0, 0, 1),
            "+Z": (0, 0, d, 0, 1, 0),
            "-Z": (0, 0, -d, 0, 1, 0),
            "Iso": (d, d, d, 0, 0, 1),
        }
        if direction in views:
            px, py, pz, ux, uy, uz = views[direction]
            cam.SetPosition(px, py, pz)
            cam.SetViewUp(ux, uy, uz)
        self._renderer.ResetCamera()
        self._render()

    def _render(self):
        if self._vtk_widget:
            self._vtk_widget.GetRenderWindow().Render()

    def _open_vtk_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open VTK File", "",
            "VTK ImageData (*.vti);;All Files (*)")
        if path:
            self._file_combo.addItem(Path(path).name, path)
            self._file_combo.setCurrentIndex(self._file_combo.count() - 1)

    def _on_file_changed(self, index):
        if index < 0:
            return
        path = self._file_combo.itemData(index)
        if path and os.path.isfile(path):
            self.load_vti(path)

    def add_output_files(self, directory: str):
        """Scan a directory for VTI files and add to combo."""
        self._file_combo.clear()
        if not os.path.isdir(directory):
            return
        vti_files = sorted(Path(directory).glob("*.vti"))
        for f in vti_files:
            self._file_combo.addItem(f.name, str(f))
