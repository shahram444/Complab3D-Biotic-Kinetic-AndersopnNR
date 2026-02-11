"""3D VTK visualization widget with ParaView-like capabilities.

Supports:
  - .vti (vtkImageData) files: substrate concentrations, biomass, masks
  - .vtk legacy files: flow velocity fields, pressure, geometry
  - .dat binary geometry files
  - Filters: threshold, contour, slice, clip, glyph (vectors)
  - Controls: scalar range, colormap, opacity, scale factor
  - View presets: axis-aligned and isometric
  - Remove loaded geometry (button + menu + keyboard shortcut)
"""

import struct
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSlider, QDoubleSpinBox, QCheckBox, QFileDialog,
    QFormLayout, QSplitter, QFrame, QTabWidget, QSizePolicy,
    QToolButton, QSpacerItem, QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence

try:
    import vtk
    from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    HAS_VTK = True
except ImportError:
    HAS_VTK = False


class VTKViewer(QWidget):
    """3D viewer with ParaView-like filter and display controls."""

    geometry_removed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._actor = None
        self._filter_actor = None
        self._scalar_bar = None
        self._reader_output = None
        self._data_arrays = []
        self._current_file = ""
        self._renderer = None
        self._vtk_widget = None
        self._loaded_files = []  # track multiple loaded files
        self._setup_ui()

    def _setup_ui(self):
        if not HAS_VTK:
            layout = QVBoxLayout(self)
            placeholder = QFrame()
            placeholder.setFrameStyle(QFrame.Shape.StyledPanel)
            placeholder.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            ph_layout = QVBoxLayout(placeholder)
            msg = QLabel(
                "VTK not installed.\n\n"
                "Install with:\n  pip install vtk\n\n"
                "Then restart CompLaB Studio.")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg.setProperty("info", True)
            ph_layout.addWidget(msg)
            layout.addWidget(placeholder, 1)
            return

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── Top toolbar ─────────────────────────────────────────────
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(6, 3, 6, 3)
        toolbar.setSpacing(4)

        # File operations
        open_btn = QPushButton("\u2750 Open VTK")
        open_btn.setToolTip("Open VTK file (.vti, .vtk, .dat)")
        open_btn.setFixedHeight(28)
        open_btn.clicked.connect(self._open_file_dialog)
        toolbar.addWidget(open_btn)

        self._remove_btn = QPushButton("\u2716 Remove Loaded")
        self._remove_btn.setToolTip(
            "Remove loaded VTK data from the 3D viewer (Delete key)")
        self._remove_btn.setFixedHeight(28)
        self._remove_btn.setProperty("danger", True)
        self._remove_btn.setEnabled(False)
        self._remove_btn.clicked.connect(self._remove_geometry)
        toolbar.addWidget(self._remove_btn)

        # Delete key shortcut for remove
        self._remove_action = QAction("Remove Loaded VTK", self)
        self._remove_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        self._remove_action.triggered.connect(self._remove_geometry)
        self.addAction(self._remove_action)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setFixedWidth(2)
        toolbar.addWidget(sep1)

        # Array selector
        toolbar.addWidget(QLabel("Array:"))
        self._array_combo = QComboBox()
        self._array_combo.setMinimumWidth(120)
        self._array_combo.setFixedHeight(24)
        self._array_combo.currentTextChanged.connect(self._on_array_changed)
        toolbar.addWidget(self._array_combo)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.VLine)
        sep2.setFixedWidth(2)
        toolbar.addWidget(sep2)

        # View presets
        toolbar.addWidget(QLabel("View:"))
        self._view_combo = QComboBox()
        self._view_combo.addItems(["+X", "-X", "+Y", "-Y", "+Z", "-Z", "Iso"])
        self._view_combo.setCurrentText("Iso")
        self._view_combo.setFixedHeight(24)
        self._view_combo.currentTextChanged.connect(self._set_view)
        toolbar.addWidget(self._view_combo)

        reset_btn = QPushButton("Fit")
        reset_btn.setToolTip("Fit view to data")
        reset_btn.setFixedHeight(28)
        reset_btn.clicked.connect(self._reset_view)
        toolbar.addWidget(reset_btn)

        toolbar.addStretch()

        self._file_label = QLabel("No file loaded")
        self._file_label.setProperty("info", True)
        toolbar.addWidget(self._file_label)

        layout.addLayout(toolbar)

        # Context menu for the viewer
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        # ── Main area: viewer + controls sidebar ────────────────────
        body = QSplitter(Qt.Orientation.Horizontal)

        # VTK render widget
        self._vtk_widget = QVTKRenderWindowInteractor(self)
        self._renderer = vtk.vtkRenderer()
        self._renderer.SetBackground(0.15, 0.15, 0.17)
        self._renderer.SetBackground2(0.22, 0.22, 0.25)
        self._renderer.GradientBackgroundOn()
        self._vtk_widget.GetRenderWindow().AddRenderer(self._renderer)
        body.addWidget(self._vtk_widget)

        # Orientation axes
        self._axes_widget = vtk.vtkOrientationMarkerWidget()
        axes_actor = vtk.vtkAxesActor()
        self._axes_widget.SetOrientationMarker(axes_actor)
        self._axes_widget.SetInteractor(self._vtk_widget)
        self._axes_widget.SetViewport(0.0, 0.0, 0.15, 0.15)
        self._axes_widget.EnabledOn()
        self._axes_widget.InteractiveOff()

        # ── Controls sidebar ────────────────────────────────────────
        controls = QWidget()
        controls.setMinimumWidth(200)
        controls.setMaximumWidth(260)
        ctrl_layout = QVBoxLayout(controls)
        ctrl_layout.setContentsMargins(2, 2, 2, 2)
        ctrl_layout.setSpacing(2)

        ctrl_tabs = QTabWidget()

        # -- Display tab --
        display_w = QWidget()
        dform = QFormLayout(display_w)
        dform.setContentsMargins(6, 6, 6, 6)
        dform.setVerticalSpacing(5)

        self._colormap_combo = QComboBox()
        self._colormap_combo.addItems([
            "Viridis", "Jet", "Coolwarm", "Grayscale",
            "Rainbow", "Plasma", "Inferno",
        ])
        self._colormap_combo.currentTextChanged.connect(self._on_colormap_changed)
        dform.addRow("Colormap:", self._colormap_combo)

        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(10, 100)
        self._opacity_slider.setValue(100)
        self._opacity_slider.valueChanged.connect(self._on_opacity_changed)
        dform.addRow("Opacity:", self._opacity_slider)

        self._range_min = QDoubleSpinBox()
        self._range_min.setDecimals(6)
        self._range_min.setRange(-1e20, 1e20)
        self._range_min.valueChanged.connect(self._on_range_changed)
        dform.addRow("Range min:", self._range_min)

        self._range_max = QDoubleSpinBox()
        self._range_max.setDecimals(6)
        self._range_max.setRange(-1e20, 1e20)
        self._range_max.setValue(1.0)
        self._range_max.valueChanged.connect(self._on_range_changed)
        dform.addRow("Range max:", self._range_max)

        rescale_btn = QPushButton("Rescale to Data")
        rescale_btn.clicked.connect(self._rescale_to_data)
        dform.addRow("", rescale_btn)

        self._show_edges = QCheckBox("Show edges")
        self._show_edges.toggled.connect(self._on_edges_changed)
        dform.addRow("", self._show_edges)

        self._show_scalar_bar = QCheckBox("Scalar bar")
        self._show_scalar_bar.setChecked(True)
        self._show_scalar_bar.toggled.connect(self._on_scalar_bar_toggled)
        dform.addRow("", self._show_scalar_bar)

        self._wireframe_mode = QCheckBox("Wireframe")
        self._wireframe_mode.toggled.connect(self._on_wireframe_changed)
        dform.addRow("", self._wireframe_mode)

        ctrl_tabs.addTab(display_w, "Display")

        # -- Filters tab --
        filter_w = QWidget()
        fform = QFormLayout(filter_w)
        fform.setContentsMargins(6, 6, 6, 6)
        fform.setVerticalSpacing(5)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems([
            "None", "Threshold", "Contour", "Clip",
            "Slice X", "Slice Y", "Slice Z",
        ])
        self._filter_combo.currentTextChanged.connect(self._on_filter_changed)
        fform.addRow("Filter:", self._filter_combo)

        self._filter_label1 = QLabel("Value / Min:")
        self._filter_val1 = QDoubleSpinBox()
        self._filter_val1.setDecimals(6)
        self._filter_val1.setRange(-1e20, 1e20)
        self._filter_val1.valueChanged.connect(self._apply_filter)
        fform.addRow(self._filter_label1, self._filter_val1)

        self._filter_label2 = QLabel("Max:")
        self._filter_val2 = QDoubleSpinBox()
        self._filter_val2.setDecimals(6)
        self._filter_val2.setRange(-1e20, 1e20)
        self._filter_val2.setValue(1.0)
        self._filter_val2.valueChanged.connect(self._apply_filter)
        fform.addRow(self._filter_label2, self._filter_val2)

        self._slice_pos = QSlider(Qt.Orientation.Horizontal)
        self._slice_pos.setRange(0, 100)
        self._slice_pos.setValue(50)
        self._slice_pos.valueChanged.connect(self._apply_filter)
        self._slice_label = QLabel("Position:")
        fform.addRow(self._slice_label, self._slice_pos)

        self._invert_filter = QCheckBox("Invert")
        self._invert_filter.toggled.connect(self._apply_filter)
        fform.addRow("", self._invert_filter)

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Apply")
        apply_btn.setProperty("primary", True)
        apply_btn.clicked.connect(self._apply_filter)
        btn_row.addWidget(apply_btn)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_filter)
        btn_row.addWidget(clear_btn)
        fform.addRow("", btn_row)

        # Initialize filter control visibility
        self._filter_val2.setEnabled(False)
        self._filter_label2.setEnabled(False)
        self._slice_pos.setEnabled(False)
        self._slice_label.setEnabled(False)
        self._invert_filter.setEnabled(False)

        ctrl_tabs.addTab(filter_w, "Filters")

        # -- Transform tab --
        xform_w = QWidget()
        xform_form = QFormLayout(xform_w)
        xform_form.setContentsMargins(6, 6, 6, 6)
        xform_form.setVerticalSpacing(5)

        self._scale_x = QDoubleSpinBox()
        self._scale_x.setRange(0.01, 100.0)
        self._scale_x.setValue(1.0)
        self._scale_x.setDecimals(2)
        self._scale_x.valueChanged.connect(self._on_scale_changed)
        xform_form.addRow("Scale X:", self._scale_x)

        self._scale_y = QDoubleSpinBox()
        self._scale_y.setRange(0.01, 100.0)
        self._scale_y.setValue(1.0)
        self._scale_y.setDecimals(2)
        self._scale_y.valueChanged.connect(self._on_scale_changed)
        xform_form.addRow("Scale Y:", self._scale_y)

        self._scale_z = QDoubleSpinBox()
        self._scale_z.setRange(0.01, 100.0)
        self._scale_z.setValue(1.0)
        self._scale_z.setDecimals(2)
        self._scale_z.valueChanged.connect(self._on_scale_changed)
        xform_form.addRow("Scale Z:", self._scale_z)

        self._uniform_scale = QCheckBox("Uniform scale")
        self._uniform_scale.setChecked(True)
        xform_form.addRow("", self._uniform_scale)

        reset_scale_btn = QPushButton("Reset Scale")
        reset_scale_btn.clicked.connect(self._reset_scale)
        xform_form.addRow("", reset_scale_btn)

        ctrl_tabs.addTab(xform_w, "Transform")

        # -- Info tab --
        info_w = QWidget()
        info_form = QFormLayout(info_w)
        info_form.setContentsMargins(6, 6, 6, 6)
        info_form.setVerticalSpacing(5)

        self._info_file = QLabel("--")
        self._info_file.setWordWrap(True)
        info_form.addRow("File:", self._info_file)

        self._info_dims = QLabel("--")
        info_form.addRow("Dimensions:", self._info_dims)

        self._info_points = QLabel("--")
        info_form.addRow("Points:", self._info_points)

        self._info_cells = QLabel("--")
        info_form.addRow("Cells:", self._info_cells)

        self._info_arrays = QLabel("--")
        self._info_arrays.setWordWrap(True)
        info_form.addRow("Arrays:", self._info_arrays)

        self._info_range = QLabel("--")
        info_form.addRow("Scalar range:", self._info_range)

        ctrl_tabs.addTab(info_w, "Info")

        ctrl_layout.addWidget(ctrl_tabs, 1)
        body.addWidget(controls)
        body.setSizes([600, 210])

        layout.addWidget(body, 1)
        self._vtk_widget.Initialize()

    # ── Public API ──────────────────────────────────────────────────

    def load_vti(self, filepath: str):
        """Load a VTK file (.vti or .vtk) - main entry point."""
        if not HAS_VTK:
            return
        filepath = str(filepath)
        ext = Path(filepath).suffix.lower()
        if ext == ".vtk":
            self._load_vtk_legacy(filepath)
        elif ext == ".vti":
            self._load_vti_file(filepath)
        else:
            self._load_vti_file(filepath)

    def load_file(self, filepath: str):
        """Load any supported file type by extension."""
        self.load_vti(filepath)

    def load_geometry_dat(self, filepath: str, nx: int, ny: int, nz: int):
        """Load binary .dat geometry file as vtkImageData."""
        if not HAS_VTK or not self._renderer:
            return
        filepath = str(filepath)
        try:
            with open(filepath, "rb") as f:
                raw = f.read()
            n_cells = nx * ny * nz
            expected = n_cells * 4  # int32
            if len(raw) >= expected:
                img = vtk.vtkImageData()
                img.SetDimensions(nx, ny, nz)
                img.SetSpacing(1.0, 1.0, 1.0)
                arr = vtk.vtkIntArray()
                arr.SetName("MaterialNumber")
                arr.SetNumberOfTuples(n_cells)
                for i in range(n_cells):
                    val = struct.unpack_from("<i", raw, i * 4)[0]
                    arr.SetValue(i, val)
                img.GetPointData().SetScalars(arr)
                self._display_dataset(img, filepath)
            else:
                with open(filepath, "r") as f:
                    values = [int(x) for line in f for x in line.split()]
                if len(values) >= n_cells:
                    img = vtk.vtkImageData()
                    img.SetDimensions(nx, ny, nz)
                    img.SetSpacing(1.0, 1.0, 1.0)
                    arr = vtk.vtkIntArray()
                    arr.SetName("MaterialNumber")
                    arr.SetNumberOfTuples(n_cells)
                    for i, val in enumerate(values[:n_cells]):
                        arr.SetValue(i, val)
                    img.GetPointData().SetScalars(arr)
                    self._display_dataset(img, filepath)
        except Exception:
            pass

    def add_output_files(self, directory: str):
        """Scan a directory for VTK files and add to array combo."""
        pass  # handled by post-process panel

    def has_data(self) -> bool:
        """Return True if a dataset is currently loaded."""
        return self._reader_output is not None

    # ── File loading internals ──────────────────────────────────────

    def _load_vti_file(self, filepath: str):
        reader = vtk.vtkXMLImageDataReader()
        reader.SetFileName(filepath)
        reader.Update()
        output = reader.GetOutput()
        if output:
            self._display_dataset(output, filepath)

    def _load_vtk_legacy(self, filepath: str):
        """Load legacy .vtk files (structured/rectilinear/unstructured/polydata)."""
        reader = vtk.vtkGenericDataObjectReader()
        reader.SetFileName(filepath)
        reader.Update()
        output = reader.GetOutput()
        if output is not None:
            self._display_dataset(output, filepath)

    def _display_dataset(self, dataset, filepath: str):
        """Display any VTK dataset with scalars."""
        self.clear_scene()
        self._current_file = filepath
        self._reader_output = dataset
        self._file_label.setText(Path(filepath).name)
        self._remove_btn.setEnabled(True)

        # Enumerate available arrays
        self._data_arrays = []
        self._array_combo.blockSignals(True)
        self._array_combo.clear()

        pd = dataset.GetPointData()
        for i in range(pd.GetNumberOfArrays()):
            name = pd.GetArrayName(i)
            if name:
                self._data_arrays.append(("point", name))
                self._array_combo.addItem(f"[P] {name}")

        cd = dataset.GetCellData()
        for i in range(cd.GetNumberOfArrays()):
            name = cd.GetArrayName(i)
            if name:
                self._data_arrays.append(("cell", name))
                self._array_combo.addItem(f"[C] {name}")

        # Auto-select first array
        if self._data_arrays:
            loc, name = self._data_arrays[0]
            if loc == "point":
                dataset.GetPointData().SetActiveScalars(name)
            else:
                dataset.GetCellData().SetActiveScalars(name)

        self._array_combo.blockSignals(False)

        # Create mapper
        mapper = vtk.vtkDataSetMapper()
        mapper.SetInputData(dataset)

        if self._data_arrays:
            mapper.ScalarVisibilityOn()
            scalar_range = dataset.GetScalarRange()
            mapper.SetScalarRange(scalar_range)
            self._setup_colormap(mapper)

            # Update range spinboxes
            self._range_min.blockSignals(True)
            self._range_max.blockSignals(True)
            self._range_min.setValue(scalar_range[0])
            self._range_max.setValue(scalar_range[1])
            self._range_min.blockSignals(False)
            self._range_max.blockSignals(False)

            # Update filter value defaults to match data range
            self._filter_val1.blockSignals(True)
            self._filter_val2.blockSignals(True)
            self._filter_val1.setValue(scalar_range[0])
            self._filter_val2.setValue(scalar_range[1])
            self._filter_val1.blockSignals(False)
            self._filter_val2.blockSignals(False)

            # Scalar bar
            self._add_scalar_bar(mapper)
        else:
            mapper.ScalarVisibilityOff()

        self._actor = vtk.vtkActor()
        self._actor.SetMapper(mapper)
        self._actor.GetProperty().SetOpacity(
            self._opacity_slider.value() / 100.0)
        if self._show_edges.isChecked():
            self._actor.GetProperty().EdgeVisibilityOn()
        self._renderer.AddActor(self._actor)
        self._renderer.ResetCamera()
        self._vtk_widget.GetRenderWindow().Render()

        # Update info tab
        self._update_info(dataset, filepath)

    def _update_info(self, dataset, filepath):
        """Populate the Info tab with dataset metadata."""
        self._info_file.setText(Path(filepath).name)

        if hasattr(dataset, 'GetDimensions'):
            dims = dataset.GetDimensions()
            self._info_dims.setText(f"{dims[0]} x {dims[1]} x {dims[2]}")
        else:
            self._info_dims.setText("--")

        self._info_points.setText(f"{dataset.GetNumberOfPoints():,}")
        self._info_cells.setText(f"{dataset.GetNumberOfCells():,}")

        arr_names = []
        pd = dataset.GetPointData()
        for i in range(pd.GetNumberOfArrays()):
            name = pd.GetArrayName(i)
            if name:
                arr_names.append(name)
        cd = dataset.GetCellData()
        for i in range(cd.GetNumberOfArrays()):
            name = cd.GetArrayName(i)
            if name:
                arr_names.append(name)
        self._info_arrays.setText(", ".join(arr_names) if arr_names else "--")

        sr = dataset.GetScalarRange()
        self._info_range.setText(f"[{sr[0]:.6g}, {sr[1]:.6g}]")

    # ── Context menu ──────────────────────────────────────────────

    def _show_context_menu(self, pos):
        """Right-click context menu for the 3D viewer."""
        menu = QMenu(self)
        act_open = menu.addAction("Open VTK File...")
        act_open.triggered.connect(self._open_file_dialog)
        menu.addSeparator()

        act_remove = menu.addAction("Remove Loaded VTK")
        act_remove.setEnabled(self._reader_output is not None)
        act_remove.triggered.connect(self._remove_geometry)

        act_clear_filter = menu.addAction("Clear Filter")
        act_clear_filter.triggered.connect(self._clear_filter)
        menu.addSeparator()

        act_fit = menu.addAction("Fit View")
        act_fit.triggered.connect(self._reset_view)

        view_sub = menu.addMenu("View Preset")
        for d in ["+X", "-X", "+Y", "-Y", "+Z", "-Z", "Iso"]:
            a = view_sub.addAction(d)
            a.triggered.connect(lambda checked, dd=d: self._set_view(dd))

        menu.addSeparator()
        act_rescale = menu.addAction("Rescale to Data")
        act_rescale.triggered.connect(self._rescale_to_data)

        menu.exec(self.mapToGlobal(pos))

    # ── Remove geometry ─────────────────────────────────────────────

    def _remove_geometry(self):
        """Remove all loaded geometry from the scene."""
        if not self._reader_output and not self._actor:
            return
        self.clear_scene()
        self._current_file = ""
        self._loaded_files.clear()
        self._file_label.setText("No file loaded")
        self._remove_btn.setEnabled(False)
        self._info_file.setText("--")
        self._info_dims.setText("--")
        self._info_points.setText("--")
        self._info_cells.setText("--")
        self._info_arrays.setText("--")
        self._info_range.setText("--")
        self._range_min.setValue(0)
        self._range_max.setValue(1)
        if self._renderer:
            self._vtk_widget.GetRenderWindow().Render()
        self.geometry_removed.emit()

    # ── Array / Colormap / Display ──────────────────────────────────

    def _on_array_changed(self, text: str):
        if not self._reader_output or not text:
            return
        idx = self._array_combo.currentIndex()
        if idx < 0 or idx >= len(self._data_arrays):
            return
        loc, name = self._data_arrays[idx]
        ds = self._reader_output
        if loc == "point":
            ds.GetPointData().SetActiveScalars(name)
        else:
            ds.GetCellData().SetActiveScalars(name)

        if self._actor:
            mapper = self._actor.GetMapper()
            mapper.SetInputData(ds)
            mapper.ScalarVisibilityOn()
            scalar_range = ds.GetScalarRange()
            mapper.SetScalarRange(scalar_range)
            self._range_min.blockSignals(True)
            self._range_max.blockSignals(True)
            self._range_min.setValue(scalar_range[0])
            self._range_max.setValue(scalar_range[1])
            self._range_min.blockSignals(False)
            self._range_max.blockSignals(False)

            # Update filter defaults too
            self._filter_val1.blockSignals(True)
            self._filter_val2.blockSignals(True)
            self._filter_val1.setValue(scalar_range[0])
            self._filter_val2.setValue(scalar_range[1])
            self._filter_val1.blockSignals(False)
            self._filter_val2.blockSignals(False)

            if self._scalar_bar:
                self._scalar_bar.SetTitle(name)
            self._info_range.setText(f"[{scalar_range[0]:.6g}, {scalar_range[1]:.6g}]")
            self._vtk_widget.GetRenderWindow().Render()

    def _setup_colormap(self, mapper):
        lut = vtk.vtkLookupTable()
        cmap = self._colormap_combo.currentText()
        self._apply_lut(lut, cmap)
        mapper.SetLookupTable(lut)

    def _apply_lut(self, lut, cmap_name):
        """Configure a lookup table for the given colormap name."""
        n = 256
        lut.SetNumberOfTableValues(n)
        if cmap_name == "Jet":
            lut.SetHueRange(0.667, 0.0)
            lut.Build()
        elif cmap_name == "Coolwarm":
            ctf = vtk.vtkColorTransferFunction()
            ctf.AddRGBPoint(0.0, 0.231, 0.298, 0.753)
            ctf.AddRGBPoint(0.5, 0.865, 0.865, 0.865)
            ctf.AddRGBPoint(1.0, 0.706, 0.016, 0.150)
            for i in range(n):
                r, g, b = ctf.GetColor(i / (n - 1))
                lut.SetTableValue(i, r, g, b, 1.0)
            lut.Build()
        elif cmap_name == "Grayscale":
            lut.SetHueRange(0.0, 0.0)
            lut.SetSaturationRange(0.0, 0.0)
            lut.SetValueRange(0.2, 1.0)
            lut.Build()
        elif cmap_name == "Rainbow":
            lut.SetHueRange(0.0, 0.667)
            lut.Build()
        elif cmap_name in ("Viridis", "Plasma", "Inferno"):
            ctf = vtk.vtkColorTransferFunction()
            if cmap_name == "Viridis":
                ctf.AddRGBPoint(0.0, 0.267, 0.004, 0.329)
                ctf.AddRGBPoint(0.25, 0.282, 0.140, 0.458)
                ctf.AddRGBPoint(0.5, 0.127, 0.566, 0.551)
                ctf.AddRGBPoint(0.75, 0.544, 0.774, 0.247)
                ctf.AddRGBPoint(1.0, 0.993, 0.906, 0.144)
            elif cmap_name == "Plasma":
                ctf.AddRGBPoint(0.0, 0.050, 0.030, 0.528)
                ctf.AddRGBPoint(0.25, 0.494, 0.012, 0.658)
                ctf.AddRGBPoint(0.5, 0.798, 0.280, 0.470)
                ctf.AddRGBPoint(0.75, 0.973, 0.585, 0.253)
                ctf.AddRGBPoint(1.0, 0.940, 0.975, 0.131)
            elif cmap_name == "Inferno":
                ctf.AddRGBPoint(0.0, 0.001, 0.0, 0.014)
                ctf.AddRGBPoint(0.25, 0.341, 0.062, 0.429)
                ctf.AddRGBPoint(0.5, 0.735, 0.215, 0.330)
                ctf.AddRGBPoint(0.75, 0.973, 0.557, 0.055)
                ctf.AddRGBPoint(1.0, 0.988, 1.0, 0.644)
            for i in range(n):
                r, g, b = ctf.GetColor(i / (n - 1))
                lut.SetTableValue(i, r, g, b, 1.0)
            lut.Build()
        else:
            lut.SetHueRange(0.667, 0.0)
            lut.Build()

    def _on_colormap_changed(self, _text):
        if self._actor:
            mapper = self._actor.GetMapper()
            lut = mapper.GetLookupTable()
            if lut is None:
                lut = vtk.vtkLookupTable()
            self._apply_lut(lut, self._colormap_combo.currentText())
            mapper.SetLookupTable(lut)
            if self._scalar_bar:
                self._scalar_bar.SetLookupTable(lut)
            self._vtk_widget.GetRenderWindow().Render()

    def _on_opacity_changed(self, val):
        if self._actor:
            self._actor.GetProperty().SetOpacity(val / 100.0)
            self._vtk_widget.GetRenderWindow().Render()

    def _on_range_changed(self):
        if self._actor:
            mapper = self._actor.GetMapper()
            mapper.SetScalarRange(
                self._range_min.value(), self._range_max.value())
            self._vtk_widget.GetRenderWindow().Render()

    def _rescale_to_data(self):
        if self._reader_output:
            sr = self._reader_output.GetScalarRange()
            self._range_min.setValue(sr[0])
            self._range_max.setValue(sr[1])

    def _on_edges_changed(self, checked):
        if self._actor:
            prop = self._actor.GetProperty()
            if checked:
                prop.EdgeVisibilityOn()
                prop.SetEdgeColor(0.3, 0.3, 0.3)
            else:
                prop.EdgeVisibilityOff()
            self._vtk_widget.GetRenderWindow().Render()

    def _on_wireframe_changed(self, checked):
        if self._actor:
            prop = self._actor.GetProperty()
            if checked:
                prop.SetRepresentationToWireframe()
            else:
                prop.SetRepresentationToSurface()
            self._vtk_widget.GetRenderWindow().Render()

    def _on_scalar_bar_toggled(self, checked):
        if self._scalar_bar:
            self._scalar_bar.SetVisibility(checked)
            self._vtk_widget.GetRenderWindow().Render()

    def _add_scalar_bar(self, mapper):
        if self._scalar_bar:
            self._renderer.RemoveActor2D(self._scalar_bar)
        self._scalar_bar = vtk.vtkScalarBarActor()
        self._scalar_bar.SetLookupTable(mapper.GetLookupTable())
        self._scalar_bar.SetNumberOfLabels(5)
        self._scalar_bar.SetMaximumWidthInPixels(80)
        tp = self._scalar_bar.GetTitleTextProperty()
        tp.SetColor(0.9, 0.9, 0.9)
        tp.SetFontSize(10)
        lp = self._scalar_bar.GetLabelTextProperty()
        lp.SetColor(0.8, 0.8, 0.8)
        lp.SetFontSize(9)
        idx = self._array_combo.currentIndex()
        if 0 <= idx < len(self._data_arrays):
            self._scalar_bar.SetTitle(self._data_arrays[idx][1])
        self._scalar_bar.SetVisibility(self._show_scalar_bar.isChecked())
        self._renderer.AddActor2D(self._scalar_bar)

    # ── Filters ─────────────────────────────────────────────────────

    def _on_filter_changed(self, text):
        """Update filter control visibility based on selected filter type."""
        is_threshold = (text == "Threshold")
        is_contour = (text == "Contour")
        is_clip = (text == "Clip")
        is_slice = text.startswith("Slice")

        # Value 1 is used by threshold (min), contour (iso-value), clip (value)
        self._filter_val1.setEnabled(text != "None")
        self._filter_label1.setEnabled(text != "None")
        if is_contour:
            self._filter_label1.setText("Iso-value:")
        elif is_threshold:
            self._filter_label1.setText("Min:")
        elif is_clip:
            self._filter_label1.setText("Value:")
        else:
            self._filter_label1.setText("Value:")

        # Value 2 only for threshold (max)
        self._filter_val2.setEnabled(is_threshold)
        self._filter_label2.setEnabled(is_threshold)

        # Slice position slider
        self._slice_pos.setEnabled(is_slice)
        self._slice_label.setEnabled(is_slice)

        # Invert for threshold and clip
        self._invert_filter.setEnabled(is_threshold or is_clip)

    def _apply_filter(self):
        if not self._reader_output:
            return
        self._clear_filter_actor()

        filter_type = self._filter_combo.currentText()
        if filter_type == "None":
            # Restore main actor opacity
            if self._actor:
                self._actor.GetProperty().SetOpacity(
                    self._opacity_slider.value() / 100.0)
                self._vtk_widget.GetRenderWindow().Render()
            return

        ds = self._reader_output
        filtered = None

        if filter_type == "Threshold":
            filt = vtk.vtkThreshold()
            filt.SetInputData(ds)
            low = self._filter_val1.value()
            high = self._filter_val2.value()
            if self._invert_filter.isChecked():
                # Invert: show values outside range
                filt.SetLowerThreshold(low)
                filt.SetUpperThreshold(high)
                filt.SetInvert(True)
                filt.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)
            else:
                filt.SetLowerThreshold(low)
                filt.SetUpperThreshold(high)
                filt.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)
            filt.Update()
            filtered = filt.GetOutput()

        elif filter_type == "Contour":
            filt = vtk.vtkContourFilter()
            filt.SetInputData(ds)
            filt.SetValue(0, self._filter_val1.value())
            filt.Update()
            filtered = filt.GetOutput()

        elif filter_type == "Clip":
            filt = vtk.vtkClipDataSet()
            filt.SetInputData(ds)
            filt.SetValue(self._filter_val1.value())
            if self._invert_filter.isChecked():
                filt.InsideOutOn()
            filt.Update()
            filtered = filt.GetOutput()

        elif filter_type.startswith("Slice"):
            bounds = ds.GetBounds()
            plane = vtk.vtkPlane()
            pos_frac = self._slice_pos.value() / 100.0

            if filter_type == "Slice X":
                origin_val = bounds[0] + pos_frac * (bounds[1] - bounds[0])
                plane.SetOrigin(origin_val, 0, 0)
                plane.SetNormal(1, 0, 0)
            elif filter_type == "Slice Y":
                origin_val = bounds[2] + pos_frac * (bounds[3] - bounds[2])
                plane.SetOrigin(0, origin_val, 0)
                plane.SetNormal(0, 1, 0)
            else:  # Slice Z
                origin_val = bounds[4] + pos_frac * (bounds[5] - bounds[4])
                plane.SetOrigin(0, 0, origin_val)
                plane.SetNormal(0, 0, 1)

            cutter = vtk.vtkCutter()
            cutter.SetInputData(ds)
            cutter.SetCutFunction(plane)
            cutter.Update()
            filtered = cutter.GetOutput()

        if filtered and filtered.GetNumberOfCells() > 0:
            mapper = vtk.vtkDataSetMapper()
            mapper.SetInputData(filtered)
            mapper.ScalarVisibilityOn()
            mapper.SetScalarRange(
                self._range_min.value(), self._range_max.value())
            if self._actor:
                mapper.SetLookupTable(
                    self._actor.GetMapper().GetLookupTable())
            self._filter_actor = vtk.vtkActor()
            self._filter_actor.SetMapper(mapper)
            self._renderer.AddActor(self._filter_actor)

            # Dim the main actor so filter result stands out
            if self._actor:
                self._actor.GetProperty().SetOpacity(0.15)

            self._vtk_widget.GetRenderWindow().Render()
        elif filtered and filtered.GetNumberOfCells() == 0:
            # Filter produced empty result - restore main actor
            if self._actor:
                self._actor.GetProperty().SetOpacity(
                    self._opacity_slider.value() / 100.0)
                self._vtk_widget.GetRenderWindow().Render()

    def _clear_filter(self):
        self._clear_filter_actor()
        self._filter_combo.setCurrentText("None")
        if self._actor:
            self._actor.GetProperty().SetOpacity(
                self._opacity_slider.value() / 100.0)
            self._vtk_widget.GetRenderWindow().Render()

    def _clear_filter_actor(self):
        if self._filter_actor:
            self._renderer.RemoveActor(self._filter_actor)
            self._filter_actor = None

    # ── Transform / Scale ───────────────────────────────────────────

    def _on_scale_changed(self):
        if self._uniform_scale.isChecked():
            sender = self.sender()
            val = sender.value() if sender else 1.0
            self._scale_x.blockSignals(True)
            self._scale_y.blockSignals(True)
            self._scale_z.blockSignals(True)
            self._scale_x.setValue(val)
            self._scale_y.setValue(val)
            self._scale_z.setValue(val)
            self._scale_x.blockSignals(False)
            self._scale_y.blockSignals(False)
            self._scale_z.blockSignals(False)

        if self._actor:
            self._actor.SetScale(
                self._scale_x.value(),
                self._scale_y.value(),
                self._scale_z.value())
            self._renderer.ResetCamera()
            self._vtk_widget.GetRenderWindow().Render()

    def _reset_scale(self):
        self._scale_x.setValue(1.0)
        self._scale_y.setValue(1.0)
        self._scale_z.setValue(1.0)

    # ── View presets ────────────────────────────────────────────────

    def _set_view(self, direction: str):
        if not self._renderer:
            return
        cam = self._renderer.GetActiveCamera()
        dist = cam.GetDistance() if cam.GetDistance() > 0 else 100
        fp = cam.GetFocalPoint()

        view_map = {
            "+X": ((fp[0] + dist, fp[1], fp[2]), (0, 0, 1)),
            "-X": ((fp[0] - dist, fp[1], fp[2]), (0, 0, 1)),
            "+Y": ((fp[0], fp[1] + dist, fp[2]), (0, 0, 1)),
            "-Y": ((fp[0], fp[1] - dist, fp[2]), (0, 0, 1)),
            "+Z": ((fp[0], fp[1], fp[2] + dist), (0, 1, 0)),
            "-Z": ((fp[0], fp[1], fp[2] - dist), (0, 1, 0)),
            "Iso": ((fp[0] + dist * 0.577, fp[1] + dist * 0.577,
                     fp[2] + dist * 0.577), (0, 0, 1)),
        }
        if direction in view_map:
            pos, up = view_map[direction]
            cam.SetPosition(*pos)
            cam.SetViewUp(*up)
            self._renderer.ResetCamera()
            self._vtk_widget.GetRenderWindow().Render()

    def _reset_view(self):
        if self._renderer:
            self._renderer.ResetCamera()
            self._vtk_widget.GetRenderWindow().Render()

    def _open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open VTK File", "",
            "VTK Files (*.vti *.vtk);;DAT Files (*.dat);;All Files (*)")
        if path:
            self.load_file(path)

    def reset_view(self):
        """Public reset view method."""
        self._reset_view()

    def clear_scene(self):
        """Remove all actors except orientation axes."""
        if not HAS_VTK or not self._renderer:
            return
        self._clear_filter_actor()
        if self._actor:
            self._renderer.RemoveActor(self._actor)
            self._actor = None
        if self._scalar_bar:
            self._renderer.RemoveActor2D(self._scalar_bar)
            self._scalar_bar = None
        self._reader_output = None
        self._data_arrays = []
        if hasattr(self, '_array_combo'):
            self._array_combo.clear()
        self._vtk_widget.GetRenderWindow().Render()
