"""
Mesh/Geometry Panel - Import and preview geometry from MATLAB .dat files
.dat files from MATLAB do NOT have header - just material numbers
"""

import os
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QComboBox,
    QSpinBox, QProgressBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QThread

from .base_panel import BasePanel


class GeometryLoaderThread(QThread):
    """Background thread for loading geometry files"""
    
    progress = Signal(int, str)
    finished = Signal(object)
    error = Signal(str)
    
    def __init__(self, file_path, nx, ny, nz, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.nx = nx
        self.ny = ny
        self.nz = nz
        
    def run(self):
        try:
            self.progress.emit(10, "Reading file...")
            data = self._load_dat_file()
            self.progress.emit(100, "Complete")
            self.finished.emit(data)
        except Exception as e:
            self.error.emit(str(e))
            
    def _load_dat_file(self):
        """Load .dat geometry file (NO header - from MATLAB)"""
        self.progress.emit(20, "Parsing DAT file...")
        
        # Read all values from file
        data_values = []
        with open(self.file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        val = int(line)
                        data_values.append(val)
                    except ValueError:
                        # Skip non-integer lines
                        continue
        
        self.progress.emit(60, "Building 3D array...")
        
        expected_count = self.nx * self.ny * self.nz
        actual_count = len(data_values)
        
        if actual_count != expected_count:
            raise ValueError(
                f"Data count mismatch!\n"
                f"File has {actual_count} values\n"
                f"Expected {expected_count} for {self.nx}×{self.ny}×{self.nz}"
            )
        
        # Reshape to 3D array
        # MATLAB writes column-major, we read row by row
        data = np.array(data_values, dtype=np.int8).reshape((self.nz, self.ny, self.nx))
        data = np.transpose(data, (2, 1, 0))  # Reorder to (nx, ny, nz)
        
        self.progress.emit(90, "Analyzing geometry...")
        
        unique_values = np.unique(data)
        
        # Calculate statistics
        total = data.size
        counts = {int(v): int(np.sum(data == v)) for v in unique_values}
        
        return {
            'data': data,
            'dimensions': (self.nx, self.ny, self.nz),
            'unique_values': unique_values,
            'counts': counts,
            'file_path': self.file_path
        }


class MeshPanel(BasePanel):
    """Panel for importing geometry from MATLAB .dat files"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header = self._create_header("Geometry Import", "🔲")
        main_layout.addWidget(header)
        
        # Description
        desc = self._create_info_label(
            "Import geometry from MATLAB-generated .dat files. "
            "The .dat file should contain material numbers (0, 1, 2, 3...) "
            "without a header line. Specify the dimensions from your MATLAB script."
        )
        main_layout.addWidget(desc)
        
        # === File Selection Group ===
        file_group = self._create_group("Geometry File")
        file_layout = QFormLayout()
        
        # File path
        file_row = QHBoxLayout()
        self.file_path_edit = self._create_line_edit("", "Select .dat file from input folder...")
        self.file_path_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_geometry)
        file_row.addWidget(self.file_path_edit)
        file_row.addWidget(browse_btn)
        file_widget = QWidget()
        file_widget.setLayout(file_row)
        file_layout.addRow("File:", file_widget)
        
        file_group.setLayout(file_layout)
        main_layout.addWidget(file_group)
        
        # === Dimensions Group ===
        dim_group = self._create_group("Dimensions (from MATLAB)")
        dim_layout = QFormLayout()
        
        dim_info = self._create_info_label(
            "Enter the dimensions used when creating the geometry in MATLAB. "
            "These must match exactly or the simulation will fail."
        )
        dim_layout.addRow("", dim_info)
        
        self.nx_spin = self._create_spin_box(1, 10000, 100)
        self.ny_spin = self._create_spin_box(1, 10000, 100)
        self.nz_spin = self._create_spin_box(1, 10000, 100)
        
        dim_layout.addRow("Nx (flow direction):", self.nx_spin)
        dim_layout.addRow("Ny:", self.ny_spin)
        dim_layout.addRow("Nz:", self.nz_spin)
        
        # Expected values label
        self.expected_label = QLabel("")
        dim_layout.addRow("Expected values:", self.expected_label)
        
        dim_group.setLayout(dim_layout)
        main_layout.addWidget(dim_group)
        
        # Load button
        load_btn = QPushButton("Load and Validate Geometry")
        load_btn.clicked.connect(self._load_geometry)
        load_btn.setMinimumHeight(40)
        load_btn.setStyleSheet("QPushButton { font-weight: bold; }")
        main_layout.addWidget(load_btn)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        main_layout.addWidget(self.progress_label)
        
        # === Geometry Info Group ===
        info_group = self._create_group("Geometry Information")
        info_layout = QFormLayout()
        
        self.status_label = QLabel("No geometry loaded")
        self.status_label.setStyleSheet("color: gray;")
        info_layout.addRow("Status:", self.status_label)
        
        self.dim_label = QLabel("-")
        info_layout.addRow("Dimensions:", self.dim_label)
        
        self.voxels_label = QLabel("-")
        info_layout.addRow("Total voxels:", self.voxels_label)
        
        self.materials_label = QLabel("-")
        info_layout.addRow("Material numbers:", self.materials_label)
        
        self.porosity_label = QLabel("-")
        info_layout.addRow("Porosity:", self.porosity_label)
        
        # Material counts
        self.mat_counts_label = QLabel("-")
        self.mat_counts_label.setWordWrap(True)
        info_layout.addRow("Material counts:", self.mat_counts_label)
        
        info_group.setLayout(info_layout)
        main_layout.addWidget(info_group)
        
        main_layout.addStretch()
        
        # Connect dimension spinners
        self.nx_spin.valueChanged.connect(self._update_expected)
        self.ny_spin.valueChanged.connect(self._update_expected)
        self.nz_spin.valueChanged.connect(self._update_expected)
        
        # Initialize
        self._geometry_data = None
        self._loader_thread = None
        self._update_expected()
        
    def _update_expected(self):
        """Update expected values count"""
        nx = self.nx_spin.value()
        ny = self.ny_spin.value()
        nz = self.nz_spin.value()
        total = nx * ny * nz
        self.expected_label.setText(f"{total:,} values")
        
    def _populate_fields(self):
        """Load data from project"""
        if not self.project:
            return
            
        self.nx_spin.setValue(self.project.domain.nx)
        self.ny_spin.setValue(self.project.domain.ny)
        self.nz_spin.setValue(self.project.domain.nz)
        
        if self.project.domain.geometry_file:
            self.file_path_edit.setText(self.project.domain.geometry_file)
            
    def collect_data(self, project):
        """Save data to project"""
        if not project:
            return
            
        project.domain.nx = self.nx_spin.value()
        project.domain.ny = self.ny_spin.value()
        project.domain.nz = self.nz_spin.value()
        
        filename = self.file_path_edit.text()
        if filename:
            project.domain.geometry_file = os.path.basename(filename)
            
    def _browse_geometry(self):
        """Browse for geometry file"""
        # Start in project input folder if available
        start_dir = ""
        if self.project and self.project.path:
            input_dir = self.project.get_input_dir()
            if os.path.exists(input_dir):
                start_dir = input_dir
                
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Geometry File",
            start_dir,
            "DAT Files (*.dat);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            
            # Count lines to help user verify dimensions
            try:
                with open(file_path, 'r') as f:
                    line_count = sum(1 for line in f if line.strip())
                self.progress_label.setText(f"File has {line_count:,} data values")
            except Exception as e:
                self.progress_label.setText(f"Error reading file: {e}")
                
    def _load_geometry(self):
        """Load and validate geometry file"""
        file_path = self.file_path_edit.text()
        
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Warning", 
                "Please select a geometry file first.")
            return
            
        nx = self.nx_spin.value()
        ny = self.ny_spin.value()
        nz = self.nz_spin.value()
        
        # Start loading
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Loading...")
        self.status_label.setStyleSheet("color: orange;")
        
        self._loader_thread = GeometryLoaderThread(file_path, nx, ny, nz, self)
        self._loader_thread.progress.connect(self._on_load_progress)
        self._loader_thread.finished.connect(self._on_load_finished)
        self._loader_thread.error.connect(self._on_load_error)
        self._loader_thread.start()
        
    def _on_load_progress(self, value, message):
        """Handle loading progress"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def _on_load_finished(self, data):
        """Handle loading complete"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        
        self._geometry_data = data
        
        # Update info labels
        nx, ny, nz = data['dimensions']
        self.dim_label.setText(f"{nx} × {ny} × {nz}")
        self.voxels_label.setText(f"{nx*ny*nz:,}")
        self.materials_label.setText(", ".join(str(v) for v in data['unique_values']))
        
        # Calculate porosity (material >= 2 is pore space)
        arr = data['data']
        pore_count = np.sum(arr >= 2)
        total = arr.size
        porosity = pore_count / total
        self.porosity_label.setText(f"{porosity:.2%}")
        
        # Material counts
        counts_str = "\n".join(f"  {mat}: {count:,} voxels ({100*count/total:.1f}%)" 
                               for mat, count in sorted(data['counts'].items()))
        self.mat_counts_label.setText(counts_str)
        
        # Update status
        self.status_label.setText("✓ Geometry loaded successfully")
        self.status_label.setStyleSheet("color: green;")
        
        # Update project
        if self.project:
            self.project.domain.nx = nx
            self.project.domain.ny = ny
            self.project.domain.nz = nz
            self.project.domain.geometry_file = os.path.basename(data['file_path'])
            
        QMessageBox.information(self, "Success", 
            f"Geometry loaded successfully!\n\n"
            f"Dimensions: {nx} × {ny} × {nz}\n"
            f"Total voxels: {nx*ny*nz:,}\n"
            f"Porosity: {porosity:.2%}\n"
            f"Materials: {', '.join(str(v) for v in data['unique_values'])}")
            
    def _on_load_error(self, error):
        """Handle loading error"""
        self.progress_bar.setVisible(False)
        self.progress_label.setText("")
        
        self.status_label.setText("✗ Load failed")
        self.status_label.setStyleSheet("color: red;")
        
        QMessageBox.critical(self, "Error", 
            f"Failed to load geometry:\n\n{error}\n\n"
            f"Make sure the dimensions match your MATLAB script.")
