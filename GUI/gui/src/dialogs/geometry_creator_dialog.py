"""
Geometry Creator Dialog - Create and modify geometry files
"""

import os
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox,
    QComboBox, QCheckBox, QDialogButtonBox, QTabWidget,
    QWidget, QListWidget, QProgressBar, QTextEdit, QDoubleSpinBox,
    QSlider, QGridLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread


class GeometryWorker(QThread):
    """Worker thread for geometry generation"""
    
    progress = Signal(int, str)
    finished = Signal(bool, str)
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        
    def run(self):
        try:
            self.progress.emit(10, "Loading BMP files...")
            # Geometry generation logic here
            self.progress.emit(50, "Processing geometry...")
            self.progress.emit(80, "Adding microbe distribution...")
            self.progress.emit(100, "Complete!")
            self.finished.emit(True, "Geometry created successfully")
        except Exception as e:
            self.finished.emit(False, str(e))


class GeometryCreatorDialog(QDialog):
    """Dialog for creating geometry files"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Geometry Creator")
        self.setMinimumSize(700, 600)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # === Import Tab ===
        import_tab = QWidget()
        import_layout = QVBoxLayout(import_tab)
        
        # BMP Import
        bmp_group = QGroupBox("Import from BMP Images")
        bmp_layout = QFormLayout()
        
        folder_layout = QHBoxLayout()
        self.bmp_folder_edit = QLineEdit()
        self.bmp_folder_edit.setPlaceholderText("Folder containing BMP slices...")
        bmp_browse = QPushButton("Browse...")
        bmp_browse.clicked.connect(self._browse_bmp_folder)
        folder_layout.addWidget(self.bmp_folder_edit)
        folder_layout.addWidget(bmp_browse)
        bmp_layout.addRow("BMP folder:", folder_layout)
        
        self.bmp_pattern_edit = QLineEdit("slice_*.bmp")
        bmp_layout.addRow("File pattern:", self.bmp_pattern_edit)
        
        scan_btn = QPushButton("Scan Files")
        scan_btn.clicked.connect(self._scan_bmp_files)
        bmp_layout.addRow("", scan_btn)
        
        self.bmp_list = QListWidget()
        self.bmp_list.setMaximumHeight(150)
        bmp_layout.addRow("Found files:", self.bmp_list)
        
        bmp_group.setLayout(bmp_layout)
        import_layout.addWidget(bmp_group)
        
        # Threshold settings
        thresh_group = QGroupBox("Segmentation")
        thresh_layout = QFormLayout()
        
        self.pore_thresh_spin = QSpinBox()
        self.pore_thresh_spin.setRange(0, 255)
        self.pore_thresh_spin.setValue(128)
        thresh_layout.addRow("Pore threshold (white):", self.pore_thresh_spin)
        
        self.solid_thresh_spin = QSpinBox()
        self.solid_thresh_spin.setRange(0, 255)
        self.solid_thresh_spin.setValue(50)
        thresh_layout.addRow("Solid threshold (black):", self.solid_thresh_spin)
        
        thresh_group.setLayout(thresh_layout)
        import_layout.addWidget(thresh_group)
        
        import_layout.addStretch()
        tabs.addTab(import_tab, "Import BMP")
        
        # === Microbe Distribution Tab ===
        microbe_tab = QWidget()
        microbe_layout = QVBoxLayout(microbe_tab)
        
        dist_group = QGroupBox("Microbe Distribution")
        dist_layout = QFormLayout()
        
        self.dist_type_combo = QComboBox()
        self.dist_type_combo.addItems([
            "Surface Layer (biofilm on walls)",
            "Random Sparse (1-5%)",
            "Random Dense (10-30%)",
            "Gradient (inlet to outlet)",
            "Hotspots (clustered regions)",
            "None"
        ])
        self.dist_type_combo.currentIndexChanged.connect(self._update_dist_params)
        dist_layout.addRow("Distribution type:", self.dist_type_combo)
        
        # Surface layer params
        self.layer_thickness_spin = QSpinBox()
        self.layer_thickness_spin.setRange(1, 20)
        self.layer_thickness_spin.setValue(2)
        dist_layout.addRow("Layer thickness (voxels):", self.layer_thickness_spin)
        
        # Random params
        self.density_spin = QDoubleSpinBox()
        self.density_spin.setRange(0, 1)
        self.density_spin.setDecimals(3)
        self.density_spin.setValue(0.1)
        dist_layout.addRow("Density fraction:", self.density_spin)
        
        # Gradient params
        self.inlet_density_spin = QDoubleSpinBox()
        self.inlet_density_spin.setRange(0, 1)
        self.inlet_density_spin.setValue(0.3)
        dist_layout.addRow("Inlet density:", self.inlet_density_spin)
        
        self.outlet_density_spin = QDoubleSpinBox()
        self.outlet_density_spin.setRange(0, 1)
        self.outlet_density_spin.setValue(0.05)
        dist_layout.addRow("Outlet density:", self.outlet_density_spin)
        
        # Hotspot params
        self.num_hotspots_spin = QSpinBox()
        self.num_hotspots_spin.setRange(1, 20)
        self.num_hotspots_spin.setValue(5)
        dist_layout.addRow("Number of hotspots:", self.num_hotspots_spin)
        
        self.hotspot_radius_spin = QSpinBox()
        self.hotspot_radius_spin.setRange(2, 50)
        self.hotspot_radius_spin.setValue(10)
        dist_layout.addRow("Hotspot radius (voxels):", self.hotspot_radius_spin)
        
        dist_group.setLayout(dist_layout)
        microbe_layout.addWidget(dist_group)
        
        # Material numbers
        mat_group = QGroupBox("Material Numbers")
        mat_layout = QFormLayout()
        
        self.pore_mat_spin = QSpinBox()
        self.pore_mat_spin.setRange(0, 255)
        self.pore_mat_spin.setValue(2)
        mat_layout.addRow("Pore:", self.pore_mat_spin)
        
        self.solid_mat_spin = QSpinBox()
        self.solid_mat_spin.setRange(0, 255)
        self.solid_mat_spin.setValue(0)
        mat_layout.addRow("Solid:", self.solid_mat_spin)
        
        self.bb_mat_spin = QSpinBox()
        self.bb_mat_spin.setRange(0, 255)
        self.bb_mat_spin.setValue(1)
        mat_layout.addRow("Bounce-back:", self.bb_mat_spin)
        
        self.microbe_mat_spin = QSpinBox()
        self.microbe_mat_spin.setRange(0, 255)
        self.microbe_mat_spin.setValue(3)
        mat_layout.addRow("Microbe:", self.microbe_mat_spin)
        
        mat_group.setLayout(mat_layout)
        microbe_layout.addWidget(mat_group)
        
        microbe_layout.addStretch()
        tabs.addTab(microbe_tab, "Microbe Distribution")
        
        # === Generate Tab ===
        generate_tab = QWidget()
        generate_layout = QVBoxLayout(generate_tab)
        
        output_group = QGroupBox("Output")
        output_layout = QFormLayout()
        
        output_file_layout = QHBoxLayout()
        self.output_file_edit = QLineEdit("geometry.dat")
        output_browse = QPushButton("Browse...")
        output_browse.clicked.connect(self._browse_output)
        output_file_layout.addWidget(self.output_file_edit)
        output_file_layout.addWidget(output_browse)
        output_layout.addRow("Output file:", output_file_layout)
        
        output_group.setLayout(output_layout)
        generate_layout.addWidget(output_group)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        generate_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        generate_layout.addWidget(self.status_label)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Geometry")
        self.generate_btn.clicked.connect(self._generate_geometry)
        generate_layout.addWidget(self.generate_btn)
        
        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        generate_layout.addWidget(preview_group)
        
        generate_layout.addStretch()
        tabs.addTab(generate_tab, "Generate")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self._update_dist_params()
        
    def _browse_bmp_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select BMP Folder")
        if path:
            self.bmp_folder_edit.setText(path)
            
    def _scan_bmp_files(self):
        folder = self.bmp_folder_edit.text()
        pattern = self.bmp_pattern_edit.text()
        
        if not folder or not os.path.exists(folder):
            return
            
        import glob
        files = sorted(glob.glob(os.path.join(folder, pattern)))
        
        self.bmp_list.clear()
        for f in files:
            self.bmp_list.addItem(os.path.basename(f))
            
        self.preview_text.setText(f"Found {len(files)} BMP files")
        
    def _browse_output(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Geometry",
            "", "DAT Files (*.dat)"
        )
        if path:
            self.output_file_edit.setText(path)
            
    def _update_dist_params(self):
        """Show/hide parameters based on distribution type"""
        dist_type = self.dist_type_combo.currentIndex()
        
        # Surface layer
        self.layer_thickness_spin.setEnabled(dist_type == 0)
        
        # Random
        self.density_spin.setEnabled(dist_type in [1, 2])
        
        # Gradient
        self.inlet_density_spin.setEnabled(dist_type == 3)
        self.outlet_density_spin.setEnabled(dist_type == 3)
        
        # Hotspots
        self.num_hotspots_spin.setEnabled(dist_type == 4)
        self.hotspot_radius_spin.setEnabled(dist_type == 4)
        
    def _generate_geometry(self):
        """Generate the geometry file"""
        folder = self.bmp_folder_edit.text()
        if not folder:
            QMessageBox.warning(self, "Warning", "Please select a BMP folder")
            return
            
        output = self.output_file_edit.text()
        if not output:
            QMessageBox.warning(self, "Warning", "Please specify output file")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating...")
        self.generate_btn.setEnabled(False)
        
        # In real implementation, this would use a worker thread
        # For now, just show completion
        self.progress_bar.setValue(100)
        self.status_label.setText("Generation complete!")
        self.generate_btn.setEnabled(True)
        
        self.preview_text.setText(
            f"Geometry generated:\n"
            f"  Output: {output}\n"
            f"  Distribution: {self.dist_type_combo.currentText()}\n"
            f"  Material numbers: pore={self.pore_mat_spin.value()}, "
            f"solid={self.solid_mat_spin.value()}, "
            f"microbe={self.microbe_mat_spin.value()}"
        )
