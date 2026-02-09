"""
Domain Configuration Panel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QComboBox, QPushButton,
    QFileDialog, QGridLayout
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel


class DomainPanel(BasePanel):
    """Panel for domain/geometry configuration"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header = self._create_header("Domain Configuration", "📐")
        main_layout.addWidget(header)
        
        # Description
        desc = self._create_info_label(
            "Configure the computational domain dimensions, grid resolution, "
            "and material numbers for your simulation."
        )
        main_layout.addWidget(desc)
        
        # Grid layout for groups
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Domain dimensions group
        dim_group = self._create_group("Domain Dimensions")
        dim_layout = self._create_form_layout()
        
        self.nx_spin = self._create_spin_box(1, 10000, 100)
        self.ny_spin = self._create_spin_box(1, 10000, 100)
        self.nz_spin = self._create_spin_box(1, 10000, 100)
        
        dim_layout.addRow("Nx (flow direction):", self.nx_spin)
        dim_layout.addRow("Ny:", self.ny_spin)
        dim_layout.addRow("Nz:", self.nz_spin)
        
        # Add calculated domain size label
        self.domain_size_label = QLabel("")
        dim_layout.addRow("Domain size:", self.domain_size_label)
        
        dim_group.setLayout(dim_layout)
        grid.addWidget(dim_group, 0, 0)
        
        # Grid spacing group
        grid_group = self._create_group("Grid Spacing")
        grid_layout = self._create_form_layout()
        
        self.dx_spin = self._create_double_spin(0.001, 10000, 10, 3, 1)
        
        self.unit_combo = self._create_combo_box(["um", "mm", "cm", "m"], 0)
        
        unit_layout = QHBoxLayout()
        unit_layout.addWidget(self.dx_spin)
        unit_layout.addWidget(self.unit_combo)
        unit_layout.setContentsMargins(0, 0, 0, 0)
        unit_widget = QWidget()
        unit_widget.setLayout(unit_layout)
        
        grid_layout.addRow("Grid spacing (dx):", unit_widget)
        
        self.char_length_spin = self._create_double_spin(0.001, 10000, 10, 3, 1)
        grid_layout.addRow("Characteristic length:", self.char_length_spin)
        
        grid_group.setLayout(grid_layout)
        grid.addWidget(grid_group, 0, 1)
        
        # Material numbers group
        mat_group = self._create_group("Material Numbers")
        mat_layout = self._create_form_layout()
        
        self.pore_mat_spin = self._create_spin_box(0, 255, 2)
        self.solid_mat_spin = self._create_spin_box(0, 255, 0)
        self.bb_mat_spin = self._create_spin_box(0, 255, 1)
        
        mat_layout.addRow("Pore space:", self.pore_mat_spin)
        mat_layout.addRow("Solid (no dynamics):", self.solid_mat_spin)
        mat_layout.addRow("Bounce-back (walls):", self.bb_mat_spin)
        
        mat_info = self._create_info_label(
            "Material numbers identify different regions in your geometry file. "
            "Microbe material numbers are set in the Microbiology panel."
        )
        mat_layout.addRow("", mat_info)
        
        mat_group.setLayout(mat_layout)
        grid.addWidget(mat_group, 1, 0)
        
        # Geometry file group
        geom_group = self._create_group("Geometry File")
        geom_layout = self._create_form_layout()
        
        file_layout = QHBoxLayout()
        self.geom_file_edit = self._create_line_edit("", "geometry.dat")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_geometry)
        file_layout.addWidget(self.geom_file_edit)
        file_layout.addWidget(browse_btn)
        file_layout.setContentsMargins(0, 0, 0, 0)
        file_widget = QWidget()
        file_widget.setLayout(file_layout)
        
        geom_layout.addRow("Geometry file:", file_widget)
        
        geom_info = self._create_info_label(
            "The geometry file should be a .dat file containing integer material numbers. "
            "Use the Geometry panel to create or import geometry from BMP images."
        )
        geom_layout.addRow("", geom_info)
        
        geom_group.setLayout(geom_layout)
        grid.addWidget(geom_group, 1, 1)
        
        main_layout.addLayout(grid)
        
        # Summary section
        summary_group = self._create_group("Domain Summary")
        summary_layout = QVBoxLayout()
        self.summary_label = QLabel("")
        self.summary_label.setWordWrap(True)
        summary_layout.addWidget(self.summary_label)
        summary_group.setLayout(summary_layout)
        main_layout.addWidget(summary_group)
        
        main_layout.addStretch()
        
        # Connect signals for summary update
        self.nx_spin.valueChanged.connect(self._update_summary)
        self.ny_spin.valueChanged.connect(self._update_summary)
        self.nz_spin.valueChanged.connect(self._update_summary)
        self.dx_spin.valueChanged.connect(self._update_summary)
        self.unit_combo.currentTextChanged.connect(self._update_summary)
        
    def _populate_fields(self):
        if not self.project:
            return
            
        domain = self.project.domain
        
        self.nx_spin.setValue(domain.nx)
        self.ny_spin.setValue(domain.ny)
        self.nz_spin.setValue(domain.nz)
        self.dx_spin.setValue(domain.dx)
        self.char_length_spin.setValue(domain.characteristic_length)
        
        # Set unit
        unit_idx = self.unit_combo.findText(domain.unit)
        if unit_idx >= 0:
            self.unit_combo.setCurrentIndex(unit_idx)
            
        self.pore_mat_spin.setValue(domain.pore_material)
        self.solid_mat_spin.setValue(domain.solid_material)
        self.bb_mat_spin.setValue(domain.bounce_back_material)
        
        self.geom_file_edit.setText(domain.geometry_file)
        
        self._update_summary()
        
    def collect_data(self, project):
        if not project:
            return
            
        project.domain.nx = self.nx_spin.value()
        project.domain.ny = self.ny_spin.value()
        project.domain.nz = self.nz_spin.value()
        project.domain.dx = self.dx_spin.value()
        project.domain.dy = self.dx_spin.value()
        project.domain.dz = self.dx_spin.value()
        project.domain.characteristic_length = self.char_length_spin.value()
        project.domain.unit = self.unit_combo.currentText()
        
        project.domain.pore_material = self.pore_mat_spin.value()
        project.domain.solid_material = self.solid_mat_spin.value()
        project.domain.bounce_back_material = self.bb_mat_spin.value()
        
        # *** FIX: Only update geometry_file if field has a value ***
        # *** Or if project doesn't already have one set ***
        geom_file_text = self.geom_file_edit.text().strip()
        if geom_file_text:
            project.domain.geometry_file = geom_file_text
        elif not project.domain.geometry_file:
            # Set default if nothing is set
            project.domain.geometry_file = "geometry.dat"
        # If field is empty but project already has a geometry file, keep it
        
    def _browse_geometry(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Geometry File",
            "",
            "DAT Files (*.dat);;All Files (*)"
        )
        if file_path:
            import os
            self.geom_file_edit.setText(os.path.basename(file_path))
            
    def _update_summary(self):
        nx = self.nx_spin.value()
        ny = self.ny_spin.value()
        nz = self.nz_spin.value()
        dx = self.dx_spin.value()
        unit = self.unit_combo.currentText()
        
        total_cells = nx * ny * nz
        domain_x = (nx - 2) * dx  # Subtract boundary layers
        domain_y = ny * dx
        domain_z = nz * dx
        
        self.domain_size_label.setText(f"{domain_x:.1f} × {domain_y:.1f} × {domain_z:.1f} {unit}")
        
        summary = (
            f"<b>Total lattice nodes:</b> {total_cells:,} ({nx}×{ny}×{nz})<br>"
            f"<b>Physical domain:</b> {domain_x:.1f} × {domain_y:.1f} × {domain_z:.1f} {unit}<br>"
            f"<b>Memory estimate:</b> ~{(total_cells * 8 * 7 * 2) / (1024**3):.2f} GB "
            f"(for D3Q7 substrate lattice)"
        )
        
        self.summary_label.setText(summary)
    
    def set_geometry_file(self, filename):
        """Set geometry file from external source (e.g., mesh panel)"""
        self.geom_file_edit.setText(filename)
        if self.project:
            self.project.domain.geometry_file = filename
