"""
Microbiology Configuration Panel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QMessageBox,
    QGridLayout, QFrame, QTabWidget, QScrollArea, QTextEdit
)
from PySide6.QtCore import Qt, Signal

from .base_panel import BasePanel
from ..core.project import (
    Microbe, DiffusionCoefficients, BoundaryCondition, BoundaryType,
    SolverType, MicrobeDistribution, DistributionType, ReactionType
)


class MicrobeEditor(QWidget):
    """Editor widget for a single microbe"""
    
    data_changed = Signal()
    
    def __init__(self, num_substrates: int = 1, parent=None):
        super().__init__(parent)
        self.num_substrates = num_substrates
        self._setup_ui()
        
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)
        
        # Tabs for organization
        tabs = QTabWidget()
        
        # === General Tab ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Basic info
        info_group = QGroupBox("Basic Information")
        info_layout = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.data_changed.emit)
        info_layout.addRow("Microbe name:", self.name_edit)
        
        self.solver_combo = QComboBox()
        self.solver_combo.addItems(["Cellular Automata (CA)", "Lattice Boltzmann (LBM)", 
                                    "Finite Difference (FD)", "Kinetics Only"])
        self.solver_combo.currentIndexChanged.connect(self._on_solver_changed)
        info_layout.addRow("Solver type:", self.solver_combo)
        
        self.material_spin = QSpinBox()
        self.material_spin.setRange(3, 255)
        self.material_spin.setValue(3)
        self.material_spin.valueChanged.connect(self.data_changed.emit)
        info_layout.addRow("Material number:", self.material_spin)
        
        info_group.setLayout(info_layout)
        general_layout.addWidget(info_group)
        
        # Initial conditions
        init_group = QGroupBox("Initial Conditions")
        init_layout = QFormLayout()
        
        self.init_density_edit = QLineEdit("10.0")
        self.init_density_edit.textChanged.connect(self.data_changed.emit)
        init_layout.addRow("Initial density [kgDW/m³]:", self.init_density_edit)
        
        init_info = QLabel("Enter space-separated values for multiple zones")
        init_info.setStyleSheet("color: #888;")
        init_layout.addRow("", init_info)
        
        init_group.setLayout(init_layout)
        general_layout.addWidget(init_group)
        
        # Diffusion
        diff_group = QGroupBox("Biomass Diffusion")
        diff_layout = QFormLayout()
        
        self.diff_pore_spin = QDoubleSpinBox()
        self.diff_pore_spin.setRange(0, 1e-3)
        self.diff_pore_spin.setDecimals(12)
        self.diff_pore_spin.setValue(0)
        self.diff_pore_spin.valueChanged.connect(self.data_changed.emit)
        diff_layout.addRow("In pore [m²/s]:", self.diff_pore_spin)
        
        self.diff_biofilm_spin = QDoubleSpinBox()
        self.diff_biofilm_spin.setRange(0, 1e-3)
        self.diff_biofilm_spin.setDecimals(12)
        self.diff_biofilm_spin.setValue(0)
        self.diff_biofilm_spin.valueChanged.connect(self.data_changed.emit)
        diff_layout.addRow("In biofilm [m²/s]:", self.diff_biofilm_spin)
        
        diff_group.setLayout(diff_layout)
        general_layout.addWidget(diff_group)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "General")
        
        # === Kinetics Tab ===
        kinetics_tab = QWidget()
        kinetics_layout = QVBoxLayout(kinetics_tab)
        
        kinetics_group = QGroupBox("Kinetics Parameters")
        kinetics_form = QFormLayout()
        
        self.decay_spin = QDoubleSpinBox()
        self.decay_spin.setRange(0, 1)
        self.decay_spin.setDecimals(8)
        self.decay_spin.setValue(1e-6)
        self.decay_spin.setSingleStep(1e-7)
        self.decay_spin.valueChanged.connect(self.data_changed.emit)
        kinetics_form.addRow("Decay coefficient [1/s]:", self.decay_spin)
        
        self.half_sat_edit = QLineEdit("0.1")
        self.half_sat_edit.textChanged.connect(self.data_changed.emit)
        kinetics_form.addRow("Half-saturation constants [mmol/L]:", self.half_sat_edit)
        
        ks_info = QLabel("One value per substrate, space-separated")
        ks_info.setStyleSheet("color: #888;")
        kinetics_form.addRow("", ks_info)
        
        self.vmax_edit = QLineEdit("0.2 5.0")
        self.vmax_edit.textChanged.connect(self.data_changed.emit)
        kinetics_form.addRow("Max uptake flux [mmol/kgDW/h]:", self.vmax_edit)
        
        vmax_info = QLabel("First value: growth rate. Following values: uptake per substrate")
        vmax_info.setStyleSheet("color: #888;")
        kinetics_form.addRow("", vmax_info)
        
        kinetics_group.setLayout(kinetics_form)
        kinetics_layout.addWidget(kinetics_group)
        
        # Monod preview
        preview_group = QGroupBox("Monod Kinetics Preview")
        preview_layout = QVBoxLayout()
        self.monod_preview = QLabel()
        self.monod_preview.setWordWrap(True)
        self._update_monod_preview()
        preview_layout.addWidget(self.monod_preview)
        preview_group.setLayout(preview_layout)
        kinetics_layout.addWidget(preview_group)
        
        kinetics_layout.addStretch()
        tabs.addTab(kinetics_tab, "Kinetics")
        
        # === Boundaries Tab ===
        boundary_tab = QWidget()
        boundary_layout = QVBoxLayout(boundary_tab)
        
        bc_group = QGroupBox("Boundary Conditions")
        bc_grid = QGridLayout()
        
        bc_grid.addWidget(QLabel("Inlet (left):"), 0, 0)
        self.left_bc_type = QComboBox()
        self.left_bc_type.addItems(["Dirichlet", "Neumann"])
        self.left_bc_type.setCurrentIndex(1)
        self.left_bc_type.currentIndexChanged.connect(self.data_changed.emit)
        bc_grid.addWidget(self.left_bc_type, 0, 1)
        
        self.left_bc_value = QDoubleSpinBox()
        self.left_bc_value.setRange(-1e10, 1e10)
        self.left_bc_value.setDecimals(6)
        self.left_bc_value.setValue(0)
        self.left_bc_value.valueChanged.connect(self.data_changed.emit)
        bc_grid.addWidget(self.left_bc_value, 0, 2)
        
        bc_grid.addWidget(QLabel("Outlet (right):"), 1, 0)
        self.right_bc_type = QComboBox()
        self.right_bc_type.addItems(["Dirichlet", "Neumann"])
        self.right_bc_type.setCurrentIndex(1)
        self.right_bc_type.currentIndexChanged.connect(self.data_changed.emit)
        bc_grid.addWidget(self.right_bc_type, 1, 1)
        
        self.right_bc_value = QDoubleSpinBox()
        self.right_bc_value.setRange(-1e10, 1e10)
        self.right_bc_value.setDecimals(6)
        self.right_bc_value.setValue(0)
        self.right_bc_value.valueChanged.connect(self.data_changed.emit)
        bc_grid.addWidget(self.right_bc_value, 1, 2)
        
        bc_group.setLayout(bc_grid)
        boundary_layout.addWidget(bc_group)
        
        boundary_layout.addStretch()
        tabs.addTab(boundary_tab, "Boundaries")
        
        # === CA Settings Tab ===
        ca_tab = QWidget()
        ca_layout = QVBoxLayout(ca_tab)
        
        ca_group = QGroupBox("Cellular Automata Settings")
        ca_form = QFormLayout()
        
        self.visc_ratio_spin = QDoubleSpinBox()
        self.visc_ratio_spin.setRange(0, 1000)
        self.visc_ratio_spin.setDecimals(2)
        self.visc_ratio_spin.setValue(0)
        self.visc_ratio_spin.valueChanged.connect(self.data_changed.emit)
        ca_form.addRow("Viscosity ratio in biofilm:", self.visc_ratio_spin)
        
        ca_group.setLayout(ca_form)
        ca_layout.addWidget(ca_group)
        
        ca_layout.addStretch()
        tabs.addTab(ca_tab, "CA Settings")
        
        layout.addWidget(tabs)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def _on_solver_changed(self, index):
        """Handle solver type change"""
        self.data_changed.emit()
        self._update_monod_preview()
        
    def _update_monod_preview(self):
        """Update Monod kinetics preview"""
        ks = self.half_sat_edit.text() if hasattr(self, 'half_sat_edit') else "0.1"
        self.monod_preview.setText(
            f"<b>Growth rate:</b> μ = μ_max × C0/(C0 + {ks})<br>"
            f"<b>Substrate uptake:</b> dCi/dt = -V_max,i × B × Monod"
        )
        
    def set_microbe(self, microbe: Microbe, num_substrates: int = 1):
        """Populate fields with microbe data"""
        self.num_substrates = num_substrates
        
        self.name_edit.setText(microbe.name)
        
        # Solver type
        solver_idx = {
            SolverType.CELLULAR_AUTOMATA: 0,
            SolverType.LATTICE_BOLTZMANN: 1,
            SolverType.FINITE_DIFFERENCE: 2,
            SolverType.KINETICS: 3
        }.get(microbe.solver_type, 0)
        self.solver_combo.setCurrentIndex(solver_idx)
        
        self.material_spin.setValue(microbe.material_number)
        
        # Initial density
        densities = " ".join(str(d) for d in microbe.initial_densities)
        self.init_density_edit.setText(densities)
        
        # Diffusion
        self.diff_pore_spin.setValue(microbe.diffusion_coefficients.in_pore)
        self.diff_biofilm_spin.setValue(microbe.diffusion_coefficients.in_biofilm)
        
        # Kinetics
        self.decay_spin.setValue(microbe.decay_coefficient)
        ks_text = " ".join(str(k) for k in microbe.half_saturation_constants)
        self.half_sat_edit.setText(ks_text)
        vmax_text = " ".join(str(v) for v in microbe.maximum_uptake_flux)
        self.vmax_edit.setText(vmax_text)
        
        # Boundary conditions
        self.left_bc_type.setCurrentIndex(0 if microbe.left_boundary.bc_type == BoundaryType.DIRICHLET else 1)
        self.left_bc_value.setValue(microbe.left_boundary.value)
        self.right_bc_type.setCurrentIndex(0 if microbe.right_boundary.bc_type == BoundaryType.DIRICHLET else 1)
        self.right_bc_value.setValue(microbe.right_boundary.value)
        
        # CA settings
        self.visc_ratio_spin.setValue(microbe.viscosity_ratio_in_biofilm)
        
        self._update_monod_preview()
        
    def get_microbe(self) -> Microbe:
        """Get microbe data from fields"""
        # Parse densities
        density_text = self.init_density_edit.text().strip()
        try:
            densities = [float(d) for d in density_text.split()]
            if not densities:
                densities = [10.0]
        except ValueError:
            densities = [10.0]
            
        # Parse kinetics
        ks_text = self.half_sat_edit.text().strip()
        try:
            ks = [float(k) for k in ks_text.split()]
            if not ks:
                ks = [0.1]
        except ValueError:
            ks = [0.1]
            
        vmax_text = self.vmax_edit.text().strip()
        try:
            vmax = [float(v) for v in vmax_text.split()]
            if not vmax:
                vmax = [0.2]
        except ValueError:
            vmax = [0.2]
            
        solver_map = {
            0: SolverType.CELLULAR_AUTOMATA,
            1: SolverType.LATTICE_BOLTZMANN,
            2: SolverType.FINITE_DIFFERENCE,
            3: SolverType.KINETICS
        }
        
        return Microbe(
            name=self.name_edit.text() or "unnamed",
            solver_type=solver_map.get(self.solver_combo.currentIndex(), SolverType.CELLULAR_AUTOMATA),
            material_number=self.material_spin.value(),
            initial_densities=densities,
            diffusion_coefficients=DiffusionCoefficients(
                self.diff_pore_spin.value(),
                self.diff_biofilm_spin.value()
            ),
            left_boundary=BoundaryCondition(
                bc_type=BoundaryType.DIRICHLET if self.left_bc_type.currentIndex() == 0 else BoundaryType.NEUMANN,
                value=self.left_bc_value.value()
            ),
            right_boundary=BoundaryCondition(
                bc_type=BoundaryType.DIRICHLET if self.right_bc_type.currentIndex() == 0 else BoundaryType.NEUMANN,
                value=self.right_bc_value.value()
            ),
            decay_coefficient=self.decay_spin.value(),
            half_saturation_constants=ks,
            maximum_uptake_flux=vmax,
            viscosity_ratio_in_biofilm=self.visc_ratio_spin.value()
        )


class MicrobiologyPanel(BasePanel):
    """Panel for microbiology configuration"""
    
    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Left side - microbe list
        left_panel = QFrame()
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)
        
        header = self._create_header("Microbes", "🦠")
        left_layout.addWidget(header)
        
        self.microbe_list = QListWidget()
        self.microbe_list.currentRowChanged.connect(self._on_microbe_selected)
        left_layout.addWidget(self.microbe_list)
        
        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("➕ Add")
        add_btn.clicked.connect(self._add_microbe)
        remove_btn = QPushButton("➖ Remove")
        remove_btn.clicked.connect(self._remove_microbe)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        left_layout.addLayout(btn_layout)
        
        # Global settings
        global_group = QGroupBox("Global Settings")
        global_layout = QFormLayout()
        
        self.max_biomass_spin = QDoubleSpinBox()
        self.max_biomass_spin.setRange(0, 10000)
        self.max_biomass_spin.setValue(80)
        self.max_biomass_spin.valueChanged.connect(self.data_changed.emit)
        global_layout.addRow("Max biomass [kgDW/m³]:", self.max_biomass_spin)
        
        self.thrd_frac_spin = QDoubleSpinBox()
        self.thrd_frac_spin.setRange(0, 1)
        self.thrd_frac_spin.setDecimals(3)
        self.thrd_frac_spin.setValue(0.1)
        self.thrd_frac_spin.valueChanged.connect(self.data_changed.emit)
        global_layout.addRow("Biofilm threshold:", self.thrd_frac_spin)
        
        self.ca_method_combo = QComboBox()
        self.ca_method_combo.addItems(["fraction", "half"])
        self.ca_method_combo.currentIndexChanged.connect(self.data_changed.emit)
        global_layout.addRow("CA method:", self.ca_method_combo)
        
        global_group.setLayout(global_layout)
        left_layout.addWidget(global_group)
        
        main_layout.addWidget(left_panel)
        
        # Right side - microbe editor
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        editor_header = self._create_header("Microbe Properties", "")
        right_layout.addWidget(editor_header)
        
        self.microbe_editor = MicrobeEditor()
        self.microbe_editor.data_changed.connect(self._on_editor_changed)
        right_layout.addWidget(self.microbe_editor)
        
        main_layout.addWidget(right_panel, 1)
        
        # Store microbes
        self._microbes = []
        self._current_index = -1
        # *** FIX: Add flag to prevent recursion ***
        self._updating = False
        
    def _populate_fields(self):
        if not self.project:
            return
        
        # *** FIX: Set flag to prevent recursion during population ***
        self._updating = True
        try:
            self._microbes = list(self.project.microbes)
            self._update_list()
            
            # Global settings
            self.max_biomass_spin.setValue(self.project.microbiology.maximum_biomass_density)
            self.thrd_frac_spin.setValue(self.project.microbiology.thrd_biofilm_fraction)
            
            ca_idx = 0 if self.project.microbiology.ca_method == "fraction" else 1
            self.ca_method_combo.setCurrentIndex(ca_idx)
            
            if self._microbes:
                self.microbe_list.setCurrentRow(0)
                self._current_index = 0
                num_subs = len(self.project.substrates) if self.project else 1
                self.microbe_editor.set_microbe(self._microbes[0], num_subs)
                self.microbe_editor.setEnabled(True)
        finally:
            self._updating = False
            
    def collect_data(self, project):
        if not project:
            return
            
        # Save current editing
        self._save_current_microbe()
        
        project.microbes = list(self._microbes)
        
        # Global settings
        project.microbiology.maximum_biomass_density = self.max_biomass_spin.value()
        project.microbiology.thrd_biofilm_fraction = self.thrd_frac_spin.value()
        project.microbiology.ca_method = self.ca_method_combo.currentText()
        
    def _update_list(self):
        """Update the microbe list"""
        # *** FIX: Block signals while updating list ***
        self.microbe_list.blockSignals(True)
        try:
            current_row = self.microbe_list.currentRow()
            self.microbe_list.clear()
            for mic in self._microbes:
                solver_icon = {
                    SolverType.CELLULAR_AUTOMATA: "🔲",
                    SolverType.LATTICE_BOLTZMANN: "🌊",
                    SolverType.FINITE_DIFFERENCE: "📐",
                    SolverType.KINETICS: "⚗️",
                }.get(mic.solver_type, "🦠")
                item = QListWidgetItem(f"{solver_icon} {mic.name}")
                self.microbe_list.addItem(item)
            # Restore selection
            if 0 <= current_row < len(self._microbes):
                self.microbe_list.setCurrentRow(current_row)
            elif self._microbes:
                self.microbe_list.setCurrentRow(0)
        finally:
            self.microbe_list.blockSignals(False)
            
    def _on_microbe_selected(self, index):
        """Handle microbe selection"""
        # *** FIX: Prevent recursion ***
        if self._updating:
            return
            
        # Save current microbe before switching (without updating list)
        if 0 <= self._current_index < len(self._microbes):
            self._microbes[self._current_index] = self.microbe_editor.get_microbe()
        
        self._current_index = index
        if 0 <= index < len(self._microbes):
            num_subs = len(self.project.substrates) if self.project else 1
            self.microbe_editor.set_microbe(self._microbes[index], num_subs)
            self.microbe_editor.setEnabled(True)
        else:
            self.microbe_editor.setEnabled(False)
            
    def _save_current_microbe(self):
        """Save current editor state to microbe"""
        # *** FIX: Prevent recursion ***
        if self._updating:
            return
            
        if 0 <= self._current_index < len(self._microbes):
            self._microbes[self._current_index] = self.microbe_editor.get_microbe()
            # Update list item name only (don't trigger selection change)
            self._update_list()
                
    def _add_microbe(self):
        """Add a new microbe"""
        # *** FIX: Set flag to prevent recursion ***
        self._updating = True
        try:
            # Save current first
            if 0 <= self._current_index < len(self._microbes):
                self._microbes[self._current_index] = self.microbe_editor.get_microbe()
            
            # Generate unique name and material number
            base_name = "microbe"
            num = len(self._microbes)
            name = f"{base_name}{num}"
            while any(m.name == name for m in self._microbes):
                num += 1
                name = f"{base_name}{num}"
                
            # Find unused material number
            used_mats = {m.material_number for m in self._microbes}
            mat_num = 3
            while mat_num in used_mats:
                mat_num += 1
                
            num_subs = len(self.project.substrates) if self.project else 1
            new_mic = Microbe(
                name=name,
                material_number=mat_num,
                half_saturation_constants=[0.1] * num_subs
            )
            self._microbes.append(new_mic)
            self._update_list()
            
            # Select the new microbe
            new_index = len(self._microbes) - 1
            self._current_index = new_index
            self.microbe_list.setCurrentRow(new_index)
            self.microbe_editor.set_microbe(new_mic, num_subs)
            self.microbe_editor.setEnabled(True)
        finally:
            self._updating = False
        
        self.data_changed.emit()
        
    def _remove_microbe(self):
        """Remove selected microbe"""
        if self._current_index < 0:
            return
            
        reply = QMessageBox.question(
            self, "Remove Microbe",
            f"Remove microbe '{self._microbes[self._current_index].name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # *** FIX: Set flag to prevent recursion ***
            self._updating = True
            try:
                self._microbes.pop(self._current_index)
                self._update_list()
                
                if self._microbes:
                    new_index = min(self._current_index, len(self._microbes) - 1)
                    self._current_index = new_index
                    self.microbe_list.setCurrentRow(new_index)
                    num_subs = len(self.project.substrates) if self.project else 1
                    self.microbe_editor.set_microbe(self._microbes[new_index], num_subs)
                else:
                    self._current_index = -1
                    self.microbe_editor.setEnabled(False)
            finally:
                self._updating = False
                
            self.data_changed.emit()
            
    def _on_editor_changed(self):
        """Handle editor data changes"""
        # *** FIX: Prevent recursion ***
        if self._updating:
            return
        self._save_current_microbe()
        self.data_changed.emit()
