"""
VTK 3D Viewer Widget
"""

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QLabel,
    QPushButton, QComboBox, QSlider, QFrame, QMessageBox,
    QFileDialog, QGroupBox, QFormLayout, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal


class VTKViewerWidget(QWidget):
    """3D visualization widget using VTK"""
    
    file_loaded = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._vtk_available = False
        self._current_data = None
        self._setup_ui()
        self._check_vtk()
        
    def _check_vtk(self):
        """Check if VTK is available"""
        try:
            import vtkmodules.vtkRenderingCore
            from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
            self._vtk_available = True
        except ImportError:
            self._vtk_available = False
            
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QToolBar()
        toolbar.setObjectName("vtkToolbar")
        
        # File operations
        open_btn = QPushButton("📂 Open")
        open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        # View controls
        reset_btn = QPushButton("🏠 Reset View")
        reset_btn.clicked.connect(self._reset_view)
        toolbar.addWidget(reset_btn)
        
        # View presets
        view_combo = QComboBox()
        view_combo.addItems(["+X", "-X", "+Y", "-Y", "+Z", "-Z", "Isometric"])
        view_combo.setCurrentIndex(6)
        view_combo.currentIndexChanged.connect(self._set_view_preset)
        toolbar.addWidget(QLabel(" View: "))
        toolbar.addWidget(view_combo)
        
        toolbar.addSeparator()
        
        # Display mode
        display_combo = QComboBox()
        display_combo.addItems(["Surface", "Wireframe", "Points", "Surface + Edges"])
        display_combo.currentIndexChanged.connect(self._set_display_mode)
        toolbar.addWidget(QLabel(" Display: "))
        toolbar.addWidget(display_combo)
        
        toolbar.addSeparator()
        
        # Variable selection
        self.var_combo = QComboBox()
        self.var_combo.addItems(["Geometry", "Velocity", "Pressure", "Concentration", "Biomass"])
        self.var_combo.currentIndexChanged.connect(self._change_variable)
        toolbar.addWidget(QLabel(" Variable: "))
        toolbar.addWidget(self.var_combo)
        
        toolbar.addSeparator()
        
        # Screenshot
        screenshot_btn = QPushButton("📷 Screenshot")
        screenshot_btn.clicked.connect(self._take_screenshot)
        toolbar.addWidget(screenshot_btn)
        
        layout.addWidget(toolbar)
        
        # Main viewer area
        if self._vtk_available:
            self._setup_vtk_widget(layout)
        else:
            self._setup_fallback_widget(layout)
            
        # Info panel at bottom
        info_panel = QFrame()
        info_panel.setObjectName("vtkInfoPanel")
        info_layout = QHBoxLayout(info_panel)
        info_layout.setContentsMargins(10, 5, 10, 5)
        
        self.info_label = QLabel("No data loaded")
        info_layout.addWidget(self.info_label)
        
        info_layout.addStretch()
        
        self.coords_label = QLabel("X: - Y: - Z: -")
        info_layout.addWidget(self.coords_label)
        
        layout.addWidget(info_panel)
        
    def _setup_vtk_widget(self, layout):
        """Setup actual VTK render widget"""
        try:
            from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
            import vtkmodules.vtkRenderingOpenGL2
            from vtkmodules.vtkRenderingCore import vtkRenderer, vtkActor
            from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
            
            self.vtk_widget = QVTKRenderWindowInteractor(self)
            layout.addWidget(self.vtk_widget, 1)
            
            # Setup renderer
            self.renderer = vtkRenderer()
            self.renderer.SetBackground(0.1, 0.1, 0.15)
            self.vtk_widget.GetRenderWindow().AddRenderer(self.renderer)
            
            # Setup interactor
            self.interactor = self.vtk_widget.GetRenderWindow().GetInteractor()
            style = vtkInteractorStyleTrackballCamera()
            self.interactor.SetInteractorStyle(style)
            
            self.interactor.Initialize()
            
        except Exception as e:
            self._vtk_available = False
            self._setup_fallback_widget(layout)
            
    def _setup_fallback_widget(self, layout):
        """Setup fallback widget when VTK is not available"""
        fallback = QFrame()
        fallback.setObjectName("vtkFallback")
        fallback_layout = QVBoxLayout(fallback)
        fallback_layout.setAlignment(Qt.AlignCenter)
        
        icon = QLabel("🎨")
        icon.setStyleSheet("font-size: 64px;")
        icon.setAlignment(Qt.AlignCenter)
        fallback_layout.addWidget(icon)
        
        title = QLabel("3D Visualization")
        title.setStyleSheet("font-size: 24px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        fallback_layout.addWidget(title)
        
        if not self._vtk_available:
            msg = QLabel(
                "VTK library not installed.\n\n"
                "To enable 3D visualization, install VTK:\n"
                "pip install vtk\n\n"
                "Alternatively, use ParaView for visualization."
            )
        else:
            msg = QLabel("Load a geometry or result file to view in 3D.")
            
        msg.setAlignment(Qt.AlignCenter)
        msg.setWordWrap(True)
        fallback_layout.addWidget(msg)
        
        if not self._vtk_available:
            paraview_btn = QPushButton("Open ParaView")
            paraview_btn.clicked.connect(self._open_paraview)
            fallback_layout.addWidget(paraview_btn, alignment=Qt.AlignCenter)
            
        layout.addWidget(fallback, 1)
        
    def _open_file(self):
        """Open VTK/geometry file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open 3D File",
            "",
            "VTK Files (*.vti *.vtk *.vtu);;DAT Files (*.dat);;All Files (*)"
        )
        
        if file_path:
            self.load_file(file_path)
            
    def load_file(self, file_path: str):
        """Load and display a file"""
        if not self._vtk_available:
            QMessageBox.warning(self, "VTK Not Available",
                              "VTK is required for 3D visualization.")
            return
            
        try:
            import os
            ext = os.path.splitext(file_path)[1].lower()
            
            if ext == '.vti':
                self._load_vti(file_path)
            elif ext == '.vtk':
                self._load_vtk(file_path)
            elif ext == '.dat':
                self._load_dat(file_path)
            else:
                QMessageBox.warning(self, "Unsupported Format",
                                  f"Cannot load {ext} files")
                return
                
            self.info_label.setText(f"Loaded: {os.path.basename(file_path)}")
            self.file_loaded.emit(file_path)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
            
    def _load_vti(self, file_path):
        """Load VTI file"""
        from vtkmodules.vtkIOXML import vtkXMLImageDataReader
        from vtkmodules.vtkRenderingCore import vtkActor, vtkDataSetMapper
        
        reader = vtkXMLImageDataReader()
        reader.SetFileName(file_path)
        reader.Update()
        
        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        
        self.renderer.RemoveAllViewProps()
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        
    def _load_vtk(self, file_path):
        """Load legacy VTK file"""
        from vtkmodules.vtkIOLegacy import vtkStructuredPointsReader
        from vtkmodules.vtkRenderingCore import vtkActor, vtkDataSetMapper
        
        reader = vtkStructuredPointsReader()
        reader.SetFileName(file_path)
        reader.Update()
        
        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(reader.GetOutputPort())
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        
        self.renderer.RemoveAllViewProps()
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        
    def _load_dat(self, file_path):
        """Load DAT geometry file and create VTK representation"""
        # Read DAT file
        with open(file_path, 'r') as f:
            lines = f.readlines()
            
        # Parse data (simplified)
        data = []
        dimensions = None
        
        for line in lines:
            parts = line.strip().split()
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                if dimensions is None:
                    dimensions = tuple(int(p) for p in parts)
                    continue
            for p in parts:
                try:
                    data.append(int(p))
                except ValueError:
                    continue
                    
        if dimensions:
            nx, ny, nz = dimensions
        else:
            total = len(data)
            nx = ny = nz = int(np.cbrt(total))
            
        # Create VTK image data
        from vtkmodules.vtkCommonDataModel import vtkImageData
        from vtkmodules.util.numpy_support import numpy_to_vtk
        from vtkmodules.vtkRenderingCore import vtkActor, vtkDataSetMapper
        from vtkmodules.vtkFiltersCore import vtkThreshold
        
        image_data = vtkImageData()
        image_data.SetDimensions(nx, ny, nz)
        
        vtk_array = numpy_to_vtk(np.array(data[:nx*ny*nz]), deep=True)
        vtk_array.SetName("Material")
        image_data.GetPointData().SetScalars(vtk_array)
        
        # Threshold to show only solid/biofilm
        threshold = vtkThreshold()
        threshold.SetInputData(image_data)
        threshold.SetLowerThreshold(0)
        threshold.SetUpperThreshold(1)
        threshold.Update()
        
        mapper = vtkDataSetMapper()
        mapper.SetInputConnection(threshold.GetOutputPort())
        
        actor = vtkActor()
        actor.SetMapper(mapper)
        
        self.renderer.RemoveAllViewProps()
        self.renderer.AddActor(actor)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        
    def _reset_view(self):
        """Reset camera to default view"""
        if self._vtk_available and hasattr(self, 'renderer'):
            self.renderer.ResetCamera()
            self.vtk_widget.GetRenderWindow().Render()
            
    def _set_view_preset(self, index):
        """Set camera to preset view"""
        if not self._vtk_available or not hasattr(self, 'renderer'):
            return
            
        camera = self.renderer.GetActiveCamera()
        
        views = [
            (1, 0, 0, 0, 0, 1),   # +X
            (-1, 0, 0, 0, 0, 1),  # -X
            (0, 1, 0, 0, 0, 1),   # +Y
            (0, -1, 0, 0, 0, 1),  # -Y
            (0, 0, 1, 0, 1, 0),   # +Z
            (0, 0, -1, 0, 1, 0),  # -Z
            (1, 1, 1, 0, 0, 1),   # Isometric
        ]
        
        pos = views[index][:3]
        up = views[index][3:]
        
        self.renderer.ResetCamera()
        camera.SetPosition(*pos)
        camera.SetViewUp(*up)
        self.renderer.ResetCamera()
        self.vtk_widget.GetRenderWindow().Render()
        
    def _set_display_mode(self, index):
        """Set display mode"""
        if not self._vtk_available:
            return
            
        # Would iterate through actors and set representation
        
    def _change_variable(self, index):
        """Change displayed variable"""
        # Would update scalar display
        pass
        
    def _take_screenshot(self):
        """Take screenshot of current view"""
        if not self._vtk_available:
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot",
            "screenshot.png",
            "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
        )
        
        if file_path:
            from vtkmodules.vtkIOImage import vtkPNGWriter
            from vtkmodules.vtkRenderingCore import vtkWindowToImageFilter
            
            w2i = vtkWindowToImageFilter()
            w2i.SetInput(self.vtk_widget.GetRenderWindow())
            w2i.Update()
            
            writer = vtkPNGWriter()
            writer.SetFileName(file_path)
            writer.SetInputConnection(w2i.GetOutputPort())
            writer.Write()
            
    def _open_paraview(self):
        """Open ParaView"""
        import subprocess
        try:
            subprocess.Popen(["paraview"])
        except FileNotFoundError:
            QMessageBox.warning(self, "ParaView Not Found",
                              "ParaView executable not found in PATH.")
