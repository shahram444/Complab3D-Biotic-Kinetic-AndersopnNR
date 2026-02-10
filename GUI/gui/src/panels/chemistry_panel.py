"""
Chemistry Configuration Panel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QDoubleSpinBox, QComboBox, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QMessageBox,
    QGridLayout, QFrame
)
from PySide6.QtCore import Qt, Signal

from .base_panel import BasePanel, CollapsibleSection
from ..core.project import Substrate, DiffusionCoefficients, BoundaryCondition, BoundaryType


class SubstrateEditor(QWidget):
    """Editor widget for a single substrate"""

    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Name
        name_group = QGroupBox("General")
        name_layout = QFormLayout()

        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self.data_changed.emit)
        name_layout.addRow("Substrate name:", self.name_edit)

        self.init_conc_spin = QDoubleSpinBox()
        self.init_conc_spin.setRange(0, 1e10)
        self.init_conc_spin.setDecimals(8)
        self.init_conc_spin.setValue(1.0)
        self.init_conc_spin.valueChanged.connect(self.data_changed.emit)
        name_layout.addRow("Initial concentration [mol/L]:", self.init_conc_spin)

        name_group.setLayout(name_layout)
        layout.addWidget(name_group)

        # Diffusion coefficients
        diff_group = QGroupBox("Diffusion Coefficients")
        diff_layout = QFormLayout()

        self.diff_pore_spin = QDoubleSpinBox()
        self.diff_pore_spin.setRange(0, 1e-3)
        self.diff_pore_spin.setDecimals(12)
        self.diff_pore_spin.setValue(1e-9)
        self.diff_pore_spin.setSingleStep(1e-10)
        self.diff_pore_spin.valueChanged.connect(self.data_changed.emit)
        diff_layout.addRow("In pore space [m^2/s]:", self.diff_pore_spin)

        self.diff_biofilm_spin = QDoubleSpinBox()
        self.diff_biofilm_spin.setRange(0, 1e-3)
        self.diff_biofilm_spin.setDecimals(12)
        self.diff_biofilm_spin.setValue(1e-10)
        self.diff_biofilm_spin.setSingleStep(1e-11)
        self.diff_biofilm_spin.valueChanged.connect(self.data_changed.emit)
        diff_layout.addRow("In biofilm [m^2/s]:", self.diff_biofilm_spin)

        diff_info = QLabel("Typical aqueous diffusion: 1e-9 m^2/s. Biofilm: 10-50% of aqueous.")
        diff_info.setWordWrap(True)
        diff_info.setStyleSheet("color: #888;")
        diff_layout.addRow("", diff_info)

        diff_group.setLayout(diff_layout)
        layout.addWidget(diff_group)

        # Boundary conditions
        bc_group = QGroupBox("Boundary Conditions")
        bc_layout = QGridLayout()

        # Left boundary (inlet)
        bc_layout.addWidget(QLabel("Inlet (left):"), 0, 0)
        self.left_bc_type = QComboBox()
        self.left_bc_type.addItems(["Dirichlet", "Neumann"])
        self.left_bc_type.currentIndexChanged.connect(self.data_changed.emit)
        bc_layout.addWidget(self.left_bc_type, 0, 1)

        self.left_bc_value = QDoubleSpinBox()
        self.left_bc_value.setRange(-1e10, 1e10)
        self.left_bc_value.setDecimals(8)
        self.left_bc_value.setValue(1.0)
        self.left_bc_value.valueChanged.connect(self.data_changed.emit)
        bc_layout.addWidget(self.left_bc_value, 0, 2)

        # Right boundary (outlet)
        bc_layout.addWidget(QLabel("Outlet (right):"), 1, 0)
        self.right_bc_type = QComboBox()
        self.right_bc_type.addItems(["Dirichlet", "Neumann"])
        self.right_bc_type.setCurrentIndex(1)  # Default to Neumann
        self.right_bc_type.currentIndexChanged.connect(self.data_changed.emit)
        bc_layout.addWidget(self.right_bc_type, 1, 1)

        self.right_bc_value = QDoubleSpinBox()
        self.right_bc_value.setRange(-1e10, 1e10)
        self.right_bc_value.setDecimals(8)
        self.right_bc_value.setValue(0.0)
        self.right_bc_value.valueChanged.connect(self.data_changed.emit)
        bc_layout.addWidget(self.right_bc_value, 1, 2)

        bc_info = QLabel("Dirichlet: fixed concentration. Neumann: fixed flux (gradient).")
        bc_info.setWordWrap(True)
        bc_info.setStyleSheet("color: #888;")
        bc_layout.addWidget(bc_info, 2, 0, 1, 3)

        bc_group.setLayout(bc_layout)
        layout.addWidget(bc_group)

        layout.addStretch()

    def set_substrate(self, substrate: Substrate):
        """Populate fields from substrate"""
        self.name_edit.setText(substrate.name)
        self.init_conc_spin.setValue(substrate.initial_concentration)
        self.diff_pore_spin.setValue(substrate.diffusion_coefficients.in_pore)
        self.diff_biofilm_spin.setValue(substrate.diffusion_coefficients.in_biofilm)

        # Boundary conditions
        self.left_bc_type.setCurrentIndex(
            0 if substrate.left_boundary.bc_type == BoundaryType.DIRICHLET else 1
        )
        self.left_bc_value.setValue(substrate.left_boundary.value)

        self.right_bc_type.setCurrentIndex(
            0 if substrate.right_boundary.bc_type == BoundaryType.DIRICHLET else 1
        )
        self.right_bc_value.setValue(substrate.right_boundary.value)

    def get_substrate(self) -> Substrate:
        """Create substrate from fields"""
        return Substrate(
            name=self.name_edit.text(),
            diffusion_coefficients=DiffusionCoefficients(
                in_pore=self.diff_pore_spin.value(),
                in_biofilm=self.diff_biofilm_spin.value()
            ),
            initial_concentration=self.init_conc_spin.value(),
            left_boundary=BoundaryCondition(
                bc_type=BoundaryType.DIRICHLET if self.left_bc_type.currentIndex() == 0 else BoundaryType.NEUMANN,
                value=self.left_bc_value.value()
            ),
            right_boundary=BoundaryCondition(
                bc_type=BoundaryType.DIRICHLET if self.right_bc_type.currentIndex() == 0 else BoundaryType.NEUMANN,
                value=self.right_bc_value.value()
            )
        )


class ChemistryPanel(BasePanel):
    """Panel for chemistry/substrate configuration"""

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setSpacing(10)

        # Left side - substrate list
        left_panel = QFrame()
        left_panel.setMaximumWidth(250)
        left_layout = QVBoxLayout(left_panel)

        header = self._create_header("Substrates", "")
        left_layout.addWidget(header)

        self.substrate_list = QListWidget()
        self.substrate_list.currentRowChanged.connect(self._on_substrate_selected)
        left_layout.addWidget(self.substrate_list)

        # Buttons
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self._add_substrate)
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(self._remove_substrate)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        left_layout.addLayout(btn_layout)

        main_layout.addWidget(left_panel)

        # Right side - substrate editor
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)

        editor_header = self._create_header("Substrate Properties", "")
        right_layout.addWidget(editor_header)

        self.substrate_editor = SubstrateEditor()
        self.substrate_editor.data_changed.connect(self._on_editor_changed)
        right_layout.addWidget(self.substrate_editor)

        main_layout.addWidget(right_panel, 1)

        # Store substrates
        self._substrates = []
        self._current_index = -1
        self._updating = False

    def _populate_fields(self):
        if not self.project:
            return

        self._updating = True
        try:
            self._substrates = list(self.project.substrates)
            self._update_list()

            if self._substrates:
                self.substrate_list.setCurrentRow(0)
                self._current_index = 0
                self.substrate_editor.set_substrate(self._substrates[0])
                self.substrate_editor.setEnabled(True)
        finally:
            self._updating = False

    def collect_data(self, project):
        if not project:
            return

        # Save current editing
        if not self._updating:
            self._save_current_substrate_data()

        project.substrates = list(self._substrates)

    def _update_list(self):
        """Update the substrate list widget"""
        self.substrate_list.blockSignals(True)
        try:
            current_row = self.substrate_list.currentRow()
            self.substrate_list.clear()
            for sub in self._substrates:
                item = QListWidgetItem(sub.name)
                self.substrate_list.addItem(item)
            # Restore selection
            if 0 <= current_row < len(self._substrates):
                self.substrate_list.setCurrentRow(current_row)
            elif self._substrates:
                self.substrate_list.setCurrentRow(0)
        finally:
            self.substrate_list.blockSignals(False)

    def _on_substrate_selected(self, index):
        """Handle substrate selection"""
        if self._updating:
            return

        # Save current substrate data before switching
        if 0 <= self._current_index < len(self._substrates):
            self._substrates[self._current_index] = self.substrate_editor.get_substrate()

        self._current_index = index
        if 0 <= index < len(self._substrates):
            self._updating = True
            try:
                self.substrate_editor.set_substrate(self._substrates[index])
                self.substrate_editor.setEnabled(True)
            finally:
                self._updating = False
        else:
            self.substrate_editor.setEnabled(False)

    def _save_current_substrate_data(self):
        """Save current editor state to substrate list (no list rebuild)"""
        if 0 <= self._current_index < len(self._substrates):
            self._substrates[self._current_index] = self.substrate_editor.get_substrate()
            # Update just the item text, don't rebuild the list
            item = self.substrate_list.item(self._current_index)
            if item:
                item.setText(self._substrates[self._current_index].name)

    def _add_substrate(self):
        """Add a new substrate"""
        self._updating = True
        try:
            # Save current first
            if 0 <= self._current_index < len(self._substrates):
                self._substrates[self._current_index] = self.substrate_editor.get_substrate()

            # Generate unique name
            base_name = "substrate"
            num = len(self._substrates)
            name = f"{base_name}{num}"
            while any(s.name == name for s in self._substrates):
                num += 1
                name = f"{base_name}{num}"

            new_sub = Substrate(name=name)
            self._substrates.append(new_sub)
            self._update_list()

            new_index = len(self._substrates) - 1
            self._current_index = new_index
            self.substrate_list.setCurrentRow(new_index)
            self.substrate_editor.set_substrate(new_sub)
            self.substrate_editor.setEnabled(True)
        finally:
            self._updating = False

        self.data_changed.emit()

    def _remove_substrate(self):
        """Remove selected substrate"""
        if self._current_index < 0:
            return

        if len(self._substrates) <= 1:
            QMessageBox.warning(self, "Warning", "At least one substrate is required.")
            return

        reply = QMessageBox.question(
            self, "Remove Substrate",
            f"Remove substrate '{self._substrates[self._current_index].name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self._updating = True
            try:
                self._substrates.pop(self._current_index)
                self._update_list()

                if self._substrates:
                    new_index = min(self._current_index, len(self._substrates) - 1)
                    self._current_index = new_index
                    self.substrate_list.setCurrentRow(new_index)
                    self.substrate_editor.set_substrate(self._substrates[new_index])
                else:
                    self._current_index = -1
                    self.substrate_editor.setEnabled(False)
            finally:
                self._updating = False

            self.data_changed.emit()

    def _on_editor_changed(self):
        """Handle editor data changes"""
        if self._updating:
            return
        self._save_current_substrate_data()
        self.data_changed.emit()
