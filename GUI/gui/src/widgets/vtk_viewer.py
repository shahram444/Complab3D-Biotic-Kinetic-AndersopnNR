"""
VTK 3D Viewer Widget with ParaView-like capabilities
Supports geometry, substrate, and flow field VTK files
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel,
    QPushButton, QComboBox, QSlider, QFrame, QMessageBox,
    QFileDialog, QGroupBox, QFormLayout, QDoubleSpinBox,
    QSplitter, QToolButton, QSpinBox, QCheckBox, QStatusBar,
    QSizePolicy
)
from PySide6.QtCore import Qt, Signal

# Try importing VTK
_VTK_AVAILABLE = False
try:
    import vtkmodules.vtkRenderingOpenGL2  # noqa - needed for rendering init
    from vtkmodules.vtkRenderingCore import (
        vtkRenderer, vtkRenderWindow, vtkRenderWindowInteractor,
        vtkPolyDataMapper, vtkActor, vtkColorTransferFunction,
        vtkDataSetMapper
    )
    from vtkmodules.vtkRenderingAnnotation import (
        vtkScalarBarActor, vtkAxesActor, vtkCubeAxesActor
    )
    from vtkmodules.vtkIOLegacy import vtkStructuredPointsReader, vtkDataSetReader
    from vtkmodules.vtkIOXML import vtkXMLImageDataReader, vtkXMLPolyDataReader
    from vtkmodules.vtkFiltersCore import vtkThreshold, vtkCutter, vtkClipDataSet
    from vtkmodules.vtkFiltersGeneral import vtkShrinkFilter
    from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter
    from vtkmodules.vtkCommonDataModel import vtkPlane
    from vtkmodules.vtkFiltersFlowPaths import vtkStreamTracer
    from vtkmodules.vtkFiltersSources import vtkArrowSource, vtkLineSource
    from vtkmodules.vtkFiltersCore import vtkGlyph3D
    from vtkmodules.vtkInteractionWidgets import vtkOrientationMarkerWidget
    from vtkmodules.vtkCommonColor import vtkNamedColors
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    _VTK_AVAILABLE = True
except ImportError:
    pass


class VTKViewer(QWidget):
    """Professional 3D visualization widget with ParaView-like capabilities"""

    file_loaded = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_file = None
        self._current_dataset = None
        self._current_mapper = None
        self._current_actor = None
        self._scalar_bar = None
        self._axes_actor = None
        self._orientation_widget = None
        self._renderer = None
        self._render_window = None
        self._interactor = None
        self._vtk_widget = None
        self._available_arrays = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top toolbar
        self._create_toolbar(layout)

        if not _VTK_AVAILABLE:
            # Placeholder when VTK is not installed
            placeholder = QLabel(
                "VTK is not installed.\n\n"
                "Install with: pip install vtk\n\n"
                "The 3D viewer requires VTK for rendering geometry,\n"
                "concentration fields, and flow field visualizations."
            )
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet(
                "color: #888; font-size: 13px; background: #1a1a2e; "
                "border: 1px solid #333; border-radius: 4px; padding: 40px;"
            )
            layout.addWidget(placeholder, 1)
        else:
            self._create_vtk_widget(layout)

        # Status bar
        self.status_bar = QLabel("No file loaded")
        self.status_bar.setStyleSheet(
            "background: #1e1e2e; color: #888; padding: 4px 8px; font-size: 11px; "
            "border-top: 1px solid #333;"
        )
        layout.addWidget(self.status_bar)

    def _create_toolbar(self, parent_layout):
        """Create the top toolbar with all controls"""
        toolbar = QFrame()
        toolbar.setObjectName("vtkToolbar")
        toolbar.setFixedHeight(36)
        toolbar.setStyleSheet(
            "QFrame#vtkToolbar { background: #252536; border-bottom: 1px solid #333; }"
        )
        tb_layout = QHBoxLayout(toolbar)
        tb_layout.setContentsMargins(6, 2, 6, 2)
        tb_layout.setSpacing(6)

        # Open file
        open_btn = QPushButton("Open")
        open_btn.setToolTip("Open VTK file")
        open_btn.setMaximumWidth(60)
        open_btn.clicked.connect(self._open_file)
        tb_layout.addWidget(open_btn)

        tb_layout.addWidget(self._make_separator())

        # Representation
        tb_layout.addWidget(QLabel("Repr:"))
        self.repr_combo = QComboBox()
        self.repr_combo.addItems(["Surface", "Wireframe", "Points", "Surface+Edges"])
        self.repr_combo.setMaximumWidth(120)
        self.repr_combo.currentIndexChanged.connect(self._on_repr_changed)
        tb_layout.addWidget(self.repr_combo)

        # Color by
        tb_layout.addWidget(QLabel("Color by:"))
        self.color_by_combo = QComboBox()
        self.color_by_combo.addItem("Solid Color")
        self.color_by_combo.setMaximumWidth(160)
        self.color_by_combo.currentIndexChanged.connect(self._on_color_by_changed)
        tb_layout.addWidget(self.color_by_combo)

        # Colormap
        tb_layout.addWidget(QLabel("Map:"))
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(["Viridis", "Rainbow", "Coolwarm", "Grayscale", "Jet"])
        self.colormap_combo.setMaximumWidth(100)
        self.colormap_combo.currentIndexChanged.connect(self._on_colormap_changed)
        tb_layout.addWidget(self.colormap_combo)

        # Rescale
        rescale_btn = QPushButton("Rescale")
        rescale_btn.setToolTip("Rescale color range to data")
        rescale_btn.setMaximumWidth(65)
        rescale_btn.clicked.connect(self._rescale_range)
        tb_layout.addWidget(rescale_btn)

        tb_layout.addWidget(self._make_separator())

        # Opacity
        tb_layout.addWidget(QLabel("Opacity:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(5, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setMaximumWidth(80)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        tb_layout.addWidget(self.opacity_slider)

        tb_layout.addWidget(self._make_separator())

        # Toggle buttons
        self.colorbar_btn = QPushButton("Bar")
        self.colorbar_btn.setCheckable(True)
        self.colorbar_btn.setChecked(True)
        self.colorbar_btn.setMaximumWidth(40)
        self.colorbar_btn.setToolTip("Toggle color bar")
        self.colorbar_btn.clicked.connect(self._toggle_colorbar)
        tb_layout.addWidget(self.colorbar_btn)

        self.axes_btn = QPushButton("Axes")
        self.axes_btn.setCheckable(True)
        self.axes_btn.setChecked(True)
        self.axes_btn.setMaximumWidth(45)
        self.axes_btn.setToolTip("Toggle axes")
        self.axes_btn.clicked.connect(self._toggle_axes)
        tb_layout.addWidget(self.axes_btn)

        tb_layout.addWidget(self._make_separator())

        # Camera presets
        for label, direction in [
            ("+X", (1, 0, 0)), ("-X", (-1, 0, 0)),
            ("+Y", (0, 1, 0)), ("-Y", (0, -1, 0)),
            ("+Z", (0, 0, 1)), ("-Z", (0, 0, -1)),
        ]:
            btn = QPushButton(label)
            btn.setMaximumWidth(30)
            btn.setToolTip(f"View from {label}")
            btn.clicked.connect(lambda checked, d=direction: self._set_camera_direction(d))
            tb_layout.addWidget(btn)

        reset_btn = QPushButton("Reset")
        reset_btn.setMaximumWidth(50)
        reset_btn.setToolTip("Reset camera")
        reset_btn.clicked.connect(self.reset_camera)
        tb_layout.addWidget(reset_btn)

        tb_layout.addStretch()
        parent_layout.addWidget(toolbar)

        # Second toolbar for filters
        filter_bar = QFrame()
        filter_bar.setObjectName("vtkFilterBar")
        filter_bar.setFixedHeight(32)
        filter_bar.setStyleSheet(
            "QFrame#vtkFilterBar { background: #1e1e30; border-bottom: 1px solid #333; }"
        )
        fb_layout = QHBoxLayout(filter_bar)
        fb_layout.setContentsMargins(6, 2, 6, 2)
        fb_layout.setSpacing(6)

        fb_layout.addWidget(QLabel("Filters:"))

        # Threshold filter
        self.threshold_btn = QPushButton("Threshold")
        self.threshold_btn.setCheckable(True)
        self.threshold_btn.setMaximumWidth(80)
        self.threshold_btn.clicked.connect(self._toggle_threshold)
        fb_layout.addWidget(self.threshold_btn)

        fb_layout.addWidget(QLabel("Min:"))
        self.thresh_min = QDoubleSpinBox()
        self.thresh_min.setRange(-1e20, 1e20)
        self.thresh_min.setDecimals(6)
        self.thresh_min.setMaximumWidth(100)
        self.thresh_min.valueChanged.connect(self._apply_threshold)
        fb_layout.addWidget(self.thresh_min)

        fb_layout.addWidget(QLabel("Max:"))
        self.thresh_max = QDoubleSpinBox()
        self.thresh_max.setRange(-1e20, 1e20)
        self.thresh_max.setDecimals(6)
        self.thresh_max.setValue(1e10)
        self.thresh_max.setMaximumWidth(100)
        self.thresh_max.valueChanged.connect(self._apply_threshold)
        fb_layout.addWidget(self.thresh_max)

        fb_layout.addWidget(self._make_separator())

        # Slice filter
        self.slice_btn = QPushButton("Slice")
        self.slice_btn.setCheckable(True)
        self.slice_btn.setMaximumWidth(50)
        self.slice_btn.clicked.connect(self._toggle_slice)
        fb_layout.addWidget(self.slice_btn)

        fb_layout.addWidget(QLabel("Plane:"))
        self.slice_plane = QComboBox()
        self.slice_plane.addItems(["XY", "XZ", "YZ"])
        self.slice_plane.setMaximumWidth(60)
        self.slice_plane.currentIndexChanged.connect(self._apply_slice)
        fb_layout.addWidget(self.slice_plane)

        fb_layout.addWidget(QLabel("Pos:"))
        self.slice_pos = QSlider(Qt.Horizontal)
        self.slice_pos.setRange(0, 100)
        self.slice_pos.setValue(50)
        self.slice_pos.setMaximumWidth(120)
        self.slice_pos.valueChanged.connect(self._apply_slice)
        fb_layout.addWidget(self.slice_pos)

        fb_layout.addWidget(self._make_separator())

        # Scale
        fb_layout.addWidget(QLabel("Scale X:"))
        self.scale_x = QDoubleSpinBox()
        self.scale_x.setRange(0.01, 100)
        self.scale_x.setValue(1.0)
        self.scale_x.setDecimals(2)
        self.scale_x.setMaximumWidth(65)
        self.scale_x.valueChanged.connect(self._apply_scale)
        fb_layout.addWidget(self.scale_x)

        fb_layout.addWidget(QLabel("Y:"))
        self.scale_y = QDoubleSpinBox()
        self.scale_y.setRange(0.01, 100)
        self.scale_y.setValue(1.0)
        self.scale_y.setDecimals(2)
        self.scale_y.setMaximumWidth(65)
        self.scale_y.valueChanged.connect(self._apply_scale)
        fb_layout.addWidget(self.scale_y)

        fb_layout.addWidget(QLabel("Z:"))
        self.scale_z = QDoubleSpinBox()
        self.scale_z.setRange(0.01, 100)
        self.scale_z.setValue(1.0)
        self.scale_z.setDecimals(2)
        self.scale_z.setMaximumWidth(65)
        self.scale_z.valueChanged.connect(self._apply_scale)
        fb_layout.addWidget(self.scale_z)

        # Vector glyph toggle (for flow fields)
        fb_layout.addWidget(self._make_separator())
        self.glyph_btn = QPushButton("Vectors")
        self.glyph_btn.setCheckable(True)
        self.glyph_btn.setMaximumWidth(65)
        self.glyph_btn.setToolTip("Show velocity arrows (for vector fields)")
        self.glyph_btn.clicked.connect(self._toggle_glyphs)
        fb_layout.addWidget(self.glyph_btn)

        fb_layout.addWidget(QLabel("Scale:"))
        self.glyph_scale = QDoubleSpinBox()
        self.glyph_scale.setRange(0.001, 1000)
        self.glyph_scale.setValue(1.0)
        self.glyph_scale.setDecimals(3)
        self.glyph_scale.setMaximumWidth(80)
        self.glyph_scale.valueChanged.connect(self._update_glyphs)
        fb_layout.addWidget(self.glyph_scale)

        fb_layout.addStretch()
        parent_layout.addWidget(filter_bar)

    def _make_separator(self):
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #444;")
        return sep

    def _create_vtk_widget(self, parent_layout):
        """Create the VTK render widget"""
        self._vtk_widget = QVTKRenderWindowInteractor(self)
        parent_layout.addWidget(self._vtk_widget, 1)

        self._renderer = vtkRenderer()
        self._renderer.SetBackground(0.11, 0.11, 0.18)
        self._renderer.SetBackground2(0.08, 0.08, 0.12)
        self._renderer.GradientBackgroundOn()

        self._render_window = self._vtk_widget.GetRenderWindow()
        self._render_window.AddRenderer(self._renderer)

        self._interactor = self._render_window.GetInteractor()
        self._interactor.SetInteractorStyle(
            __import__('vtkmodules.vtkInteractionStyle', fromlist=['vtkInteractorStyleTrackballCamera']).vtkInteractorStyleTrackballCamera()
        )

        # Add orientation marker
        self._axes_actor = vtkAxesActor()
        self._orientation_widget = vtkOrientationMarkerWidget()
        self._orientation_widget.SetOrientationMarker(self._axes_actor)
        self._orientation_widget.SetInteractor(self._interactor)
        self._orientation_widget.SetViewport(0.0, 0.0, 0.15, 0.15)
        self._orientation_widget.SetEnabled(1)
        self._orientation_widget.InteractiveOff()

        self._interactor.Initialize()

    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open VTK File", "",
            "VTK Files (*.vtk *.vti *.vtp);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """Load a VTK file and display it"""
        if not _VTK_AVAILABLE:
            QMessageBox.warning(self, "VTK Not Available",
                                "Please install VTK: pip install vtk")
            return

        self._current_file = file_path
        reader = None

        if file_path.endswith('.vti'):
            reader = vtkXMLImageDataReader()
        elif file_path.endswith('.vtp'):
            reader = vtkXMLPolyDataReader()
        elif file_path.endswith('.vtk'):
            reader = vtkDataSetReader()
        else:
            QMessageBox.warning(self, "Unsupported Format",
                                f"Cannot read: {file_path}")
            return

        reader.SetFileName(file_path)
        reader.Update()

        dataset = reader.GetOutput()
        if dataset is None:
            QMessageBox.warning(self, "Read Error", "Failed to read file.")
            return

        self._current_dataset = dataset

        # Collect available arrays
        self._available_arrays = []
        self.color_by_combo.blockSignals(True)
        self.color_by_combo.clear()
        self.color_by_combo.addItem("Solid Color")

        # Point data arrays
        pd = dataset.GetPointData()
        if pd:
            for i in range(pd.GetNumberOfArrays()):
                name = pd.GetArrayName(i)
                if name:
                    ncomp = pd.GetArray(i).GetNumberOfComponents()
                    label = f"{name} (point, {ncomp}D)"
                    self._available_arrays.append(("point", name, ncomp))
                    self.color_by_combo.addItem(label)

        # Cell data arrays
        cd = dataset.GetCellData()
        if cd:
            for i in range(cd.GetNumberOfArrays()):
                name = cd.GetArrayName(i)
                if name:
                    ncomp = cd.GetArray(i).GetNumberOfComponents()
                    label = f"{name} (cell, {ncomp}D)"
                    self._available_arrays.append(("cell", name, ncomp))
                    self.color_by_combo.addItem(label)

        self.color_by_combo.blockSignals(False)

        # Clear old actors
        self._renderer.RemoveAllViewProps()
        if self._orientation_widget:
            self._orientation_widget.SetEnabled(1)

        # Create mapper and actor
        surface = vtkDataSetSurfaceFilter()
        surface.SetInputData(dataset)
        surface.Update()

        self._current_mapper = vtkPolyDataMapper()
        self._current_mapper.SetInputConnection(surface.GetOutputPort())
        self._current_mapper.ScalarVisibilityOff()

        self._current_actor = vtkActor()
        self._current_actor.SetMapper(self._current_mapper)
        self._current_actor.GetProperty().SetColor(0.7, 0.7, 0.85)
        self._renderer.AddActor(self._current_actor)

        # Add scalar bar
        self._scalar_bar = vtkScalarBarActor()
        self._scalar_bar.SetLookupTable(self._current_mapper.GetLookupTable())
        self._scalar_bar.SetWidth(0.08)
        self._scalar_bar.SetHeight(0.4)
        self._scalar_bar.SetPosition(0.9, 0.3)
        self._scalar_bar.SetVisibility(0)
        self._renderer.AddActor2D(self._scalar_bar)

        # Auto-select first scalar array if available
        if self._available_arrays:
            self.color_by_combo.setCurrentIndex(1)

        self.reset_camera()

        # Update status
        n_points = dataset.GetNumberOfPoints()
        n_cells = dataset.GetNumberOfCells()
        import os
        fname = os.path.basename(file_path)
        self.status_bar.setText(
            f"File: {fname}  |  Points: {n_points:,}  |  Cells: {n_cells:,}  |  "
            f"Arrays: {len(self._available_arrays)}"
        )

        self.file_loaded.emit(file_path)

    def clear(self):
        """Clear the viewer"""
        if self._renderer:
            self._renderer.RemoveAllViewProps()
            if self._orientation_widget:
                self._orientation_widget.SetEnabled(1)
            self._render_window.Render()
        self._current_dataset = None
        self._current_actor = None
        self._current_mapper = None
        self.status_bar.setText("No file loaded")

    def reset_camera(self):
        """Reset camera to fit all data"""
        if self._renderer:
            self._renderer.ResetCamera()
            self._render_window.Render()

    # ---- Toolbar handlers ----

    def _on_repr_changed(self, idx):
        if not self._current_actor:
            return
        prop = self._current_actor.GetProperty()
        if idx == 0:  # Surface
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOff()
        elif idx == 1:  # Wireframe
            prop.SetRepresentationToWireframe()
        elif idx == 2:  # Points
            prop.SetRepresentationToPoints()
            prop.SetPointSize(3)
        elif idx == 3:  # Surface+Edges
            prop.SetRepresentationToSurface()
            prop.EdgeVisibilityOn()
            prop.SetEdgeColor(0.2, 0.2, 0.3)
        self._render_window.Render()

    def _on_color_by_changed(self, idx):
        if not self._current_mapper or not self._current_dataset:
            return

        if idx == 0:  # Solid color
            self._current_mapper.ScalarVisibilityOff()
            if self._scalar_bar:
                self._scalar_bar.SetVisibility(0)
        else:
            arr_idx = idx - 1
            if arr_idx < len(self._available_arrays):
                assoc, name, ncomp = self._available_arrays[arr_idx]
                self._current_mapper.ScalarVisibilityOn()
                if assoc == "point":
                    self._current_mapper.SetScalarModeToUsePointFieldData()
                else:
                    self._current_mapper.SetScalarModeToUseCellFieldData()

                if ncomp > 1:
                    # For vector fields, color by magnitude
                    self._current_mapper.SetScalarModeToDefault()
                    self._current_mapper.ScalarVisibilityOn()
                    # Compute magnitude
                    dataset = self._current_dataset
                    if assoc == "point":
                        arr = dataset.GetPointData().GetArray(name)
                    else:
                        arr = dataset.GetCellData().GetArray(name)
                    if arr:
                        from vtkmodules.vtkCommonCore import vtkDoubleArray
                        import math
                        mag_arr = vtkDoubleArray()
                        mag_arr.SetName(f"{name}_magnitude")
                        mag_arr.SetNumberOfTuples(arr.GetNumberOfTuples())
                        for i in range(arr.GetNumberOfTuples()):
                            vals = [arr.GetComponent(i, c) for c in range(ncomp)]
                            mag_arr.SetValue(i, math.sqrt(sum(v**2 for v in vals)))
                        if assoc == "point":
                            dataset.GetPointData().AddArray(mag_arr)
                            self._current_mapper.SetScalarModeToUsePointFieldData()
                        else:
                            dataset.GetCellData().AddArray(mag_arr)
                            self._current_mapper.SetScalarModeToUseCellFieldData()
                        self._current_mapper.SelectColorArray(f"{name}_magnitude")
                        data_range = mag_arr.GetRange()
                        self._current_mapper.SetScalarRange(data_range)
                else:
                    self._current_mapper.SelectColorArray(name)
                    if assoc == "point":
                        data_range = self._current_dataset.GetPointData().GetArray(name).GetRange()
                    else:
                        data_range = self._current_dataset.GetCellData().GetArray(name).GetRange()
                    self._current_mapper.SetScalarRange(data_range)

                self._apply_colormap()

                if self._scalar_bar:
                    self._scalar_bar.SetLookupTable(self._current_mapper.GetLookupTable())
                    self._scalar_bar.SetTitle(name)
                    self._scalar_bar.SetVisibility(1 if self.colorbar_btn.isChecked() else 0)

        self._render_window.Render()

    def _on_colormap_changed(self, idx):
        self._apply_colormap()
        if self._render_window:
            self._render_window.Render()

    def _apply_colormap(self):
        if not self._current_mapper:
            return
        lut = vtkColorTransferFunction()
        sr = self._current_mapper.GetScalarRange()
        lo, hi = sr[0], sr[1]
        if abs(hi - lo) < 1e-30:
            hi = lo + 1.0

        cmap = self.colormap_combo.currentText()
        if cmap == "Viridis":
            lut.AddRGBPoint(lo, 0.267, 0.004, 0.329)
            lut.AddRGBPoint(lo + 0.25*(hi-lo), 0.282, 0.140, 0.458)
            lut.AddRGBPoint(lo + 0.5*(hi-lo), 0.127, 0.566, 0.551)
            lut.AddRGBPoint(lo + 0.75*(hi-lo), 0.544, 0.773, 0.247)
            lut.AddRGBPoint(hi, 0.993, 0.906, 0.144)
        elif cmap == "Rainbow":
            lut.AddRGBPoint(lo, 0.0, 0.0, 1.0)
            lut.AddRGBPoint(lo + 0.25*(hi-lo), 0.0, 1.0, 1.0)
            lut.AddRGBPoint(lo + 0.5*(hi-lo), 0.0, 1.0, 0.0)
            lut.AddRGBPoint(lo + 0.75*(hi-lo), 1.0, 1.0, 0.0)
            lut.AddRGBPoint(hi, 1.0, 0.0, 0.0)
        elif cmap == "Coolwarm":
            lut.AddRGBPoint(lo, 0.231, 0.299, 0.754)
            lut.AddRGBPoint(lo + 0.5*(hi-lo), 0.865, 0.865, 0.865)
            lut.AddRGBPoint(hi, 0.706, 0.016, 0.150)
        elif cmap == "Grayscale":
            lut.AddRGBPoint(lo, 0.0, 0.0, 0.0)
            lut.AddRGBPoint(hi, 1.0, 1.0, 1.0)
        elif cmap == "Jet":
            lut.AddRGBPoint(lo, 0.0, 0.0, 0.5)
            lut.AddRGBPoint(lo + 0.125*(hi-lo), 0.0, 0.0, 1.0)
            lut.AddRGBPoint(lo + 0.375*(hi-lo), 0.0, 1.0, 1.0)
            lut.AddRGBPoint(lo + 0.5*(hi-lo), 0.0, 1.0, 0.0)
            lut.AddRGBPoint(lo + 0.625*(hi-lo), 1.0, 1.0, 0.0)
            lut.AddRGBPoint(lo + 0.875*(hi-lo), 1.0, 0.0, 0.0)
            lut.AddRGBPoint(hi, 0.5, 0.0, 0.0)

        self._current_mapper.SetLookupTable(lut)
        if self._scalar_bar:
            self._scalar_bar.SetLookupTable(lut)

    def _rescale_range(self):
        if not self._current_mapper or not self._current_dataset:
            return
        sr = self._current_mapper.GetInput()
        if sr:
            sr.GetScalarRange()
        self._on_color_by_changed(self.color_by_combo.currentIndex())

    def _on_opacity_changed(self, val):
        if self._current_actor:
            self._current_actor.GetProperty().SetOpacity(val / 100.0)
            self._render_window.Render()

    def _toggle_colorbar(self):
        if self._scalar_bar:
            self._scalar_bar.SetVisibility(1 if self.colorbar_btn.isChecked() else 0)
            self._render_window.Render()

    def _toggle_axes(self):
        if self._orientation_widget:
            self._orientation_widget.SetEnabled(1 if self.axes_btn.isChecked() else 0)
            self._render_window.Render()

    def _set_camera_direction(self, direction):
        if not self._renderer:
            return
        camera = self._renderer.GetActiveCamera()
        camera.SetPosition(direction[0] * 500, direction[1] * 500, direction[2] * 500)
        camera.SetViewUp(0, 0, 1) if direction[2] == 0 else camera.SetViewUp(0, 1, 0)
        camera.SetFocalPoint(0, 0, 0)
        self._renderer.ResetCamera()
        self._render_window.Render()

    # ---- Filter handlers ----

    def _toggle_threshold(self):
        if self.threshold_btn.isChecked():
            self._apply_threshold()
        else:
            self._restore_original()

    def _apply_threshold(self):
        if not self.threshold_btn.isChecked() or not self._current_dataset:
            return
        thresh = vtkThreshold()
        thresh.SetInputData(self._current_dataset)

        # Use current scalar array
        idx = self.color_by_combo.currentIndex() - 1
        if 0 <= idx < len(self._available_arrays):
            assoc, name, _ = self._available_arrays[idx]
            if assoc == "point":
                thresh.SetInputArrayToProcess(0, 0, 0, 0, name)
            else:
                thresh.SetInputArrayToProcess(0, 0, 0, 1, name)

        lo = self.thresh_min.value()
        hi = self.thresh_max.value()
        thresh.SetLowerThreshold(lo)
        thresh.SetUpperThreshold(hi)
        thresh.Update()

        surface = vtkDataSetSurfaceFilter()
        surface.SetInputConnection(thresh.GetOutputPort())
        surface.Update()

        self._current_mapper.SetInputConnection(surface.GetOutputPort())
        self._render_window.Render()

    def _restore_original(self):
        if not self._current_dataset:
            return
        surface = vtkDataSetSurfaceFilter()
        surface.SetInputData(self._current_dataset)
        surface.Update()
        self._current_mapper.SetInputConnection(surface.GetOutputPort())
        self._render_window.Render()

    def _toggle_slice(self):
        if self.slice_btn.isChecked():
            self._apply_slice()
        else:
            self._restore_original()

    def _apply_slice(self):
        if not self.slice_btn.isChecked() or not self._current_dataset:
            return

        bounds = self._current_dataset.GetBounds()
        plane = vtkPlane()
        pos_frac = self.slice_pos.value() / 100.0

        plane_idx = self.slice_plane.currentIndex()
        if plane_idx == 0:  # XY
            plane.SetNormal(0, 0, 1)
            z = bounds[4] + pos_frac * (bounds[5] - bounds[4])
            plane.SetOrigin(0, 0, z)
        elif plane_idx == 1:  # XZ
            plane.SetNormal(0, 1, 0)
            y = bounds[2] + pos_frac * (bounds[3] - bounds[2])
            plane.SetOrigin(0, y, 0)
        else:  # YZ
            plane.SetNormal(1, 0, 0)
            x = bounds[0] + pos_frac * (bounds[1] - bounds[0])
            plane.SetOrigin(x, 0, 0)

        cutter = vtkCutter()
        cutter.SetCutFunction(plane)
        cutter.SetInputData(self._current_dataset)
        cutter.Update()

        self._current_mapper.SetInputConnection(cutter.GetOutputPort())
        self._render_window.Render()

    def _apply_scale(self):
        if self._current_actor:
            self._current_actor.SetScale(
                self.scale_x.value(),
                self.scale_y.value(),
                self.scale_z.value()
            )
            self._render_window.Render()

    def _toggle_glyphs(self):
        """Toggle velocity glyph rendering for vector fields"""
        if not _VTK_AVAILABLE or not self._current_dataset:
            return

        if self.glyph_btn.isChecked():
            self._update_glyphs()
        else:
            # Remove glyph actor if exists
            if hasattr(self, '_glyph_actor') and self._glyph_actor:
                self._renderer.RemoveActor(self._glyph_actor)
                self._glyph_actor = None
                self._render_window.Render()

    def _update_glyphs(self):
        if not self.glyph_btn.isChecked() or not self._current_dataset:
            return

        # Find first vector array
        vec_name = None
        vec_assoc = None
        for assoc, name, ncomp in self._available_arrays:
            if ncomp == 3:
                vec_name = name
                vec_assoc = assoc
                break

        if not vec_name:
            return

        # Remove old glyph actor
        if hasattr(self, '_glyph_actor') and self._glyph_actor:
            self._renderer.RemoveActor(self._glyph_actor)

        # Set active vectors
        if vec_assoc == "point":
            self._current_dataset.GetPointData().SetActiveVectors(vec_name)
        else:
            self._current_dataset.GetCellData().SetActiveVectors(vec_name)

        arrow = vtkArrowSource()
        arrow.SetTipResolution(12)
        arrow.SetShaftResolution(12)

        glyph = vtkGlyph3D()
        glyph.SetInputData(self._current_dataset)
        glyph.SetSourceConnection(arrow.GetOutputPort())
        glyph.SetVectorModeToUseVector()
        glyph.SetScaleModeToScaleByVector()
        glyph.SetScaleFactor(self.glyph_scale.value())
        glyph.OrientOn()
        glyph.Update()

        mapper = vtkPolyDataMapper()
        mapper.SetInputConnection(glyph.GetOutputPort())
        mapper.ScalarVisibilityOn()

        self._glyph_actor = vtkActor()
        self._glyph_actor.SetMapper(mapper)
        self._glyph_actor.GetProperty().SetColor(0.2, 0.6, 1.0)
        self._renderer.AddActor(self._glyph_actor)
        self._render_window.Render()
