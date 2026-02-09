"""Chemistry panel - substrate management."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QStackedWidget,
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel
from ..core.project import Substrate


class SubstrateEditor(QWidget):
    """Editor for a single substrate's properties."""

    changed = None  # set by parent

    def __init__(self, on_change, parent=None):
        super().__init__(parent)
        self.changed = on_change
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        from PySide6.QtWidgets import QLineEdit, QDoubleSpinBox, QComboBox

        self._name = QLineEdit()
        self._name.textChanged.connect(self._on_change)

        self._init_conc = QDoubleSpinBox()
        self._init_conc.setRange(0, 1e30)
        self._init_conc.setDecimals(10)
        self._init_conc.setMinimumWidth(160)
        self._init_conc.valueChanged.connect(self._on_change)

        self._diff_pore = QDoubleSpinBox()
        self._diff_pore.setRange(0, 1e30)
        self._diff_pore.setDecimals(12)
        self._diff_pore.setMinimumWidth(160)
        self._diff_pore.valueChanged.connect(self._on_change)

        self._diff_biofilm = QDoubleSpinBox()
        self._diff_biofilm.setRange(0, 1e30)
        self._diff_biofilm.setDecimals(12)
        self._diff_biofilm.setMinimumWidth(160)
        self._diff_biofilm.valueChanged.connect(self._on_change)

        self._left_bc_type = QComboBox()
        self._left_bc_type.addItems(["Dirichlet", "Neumann"])
        self._left_bc_type.currentIndexChanged.connect(self._on_change)

        self._left_bc_val = QDoubleSpinBox()
        self._left_bc_val.setRange(-1e30, 1e30)
        self._left_bc_val.setDecimals(10)
        self._left_bc_val.setMinimumWidth(160)
        self._left_bc_val.valueChanged.connect(self._on_change)

        self._right_bc_type = QComboBox()
        self._right_bc_type.addItems(["Dirichlet", "Neumann"])
        self._right_bc_type.currentIndexChanged.connect(self._on_change)

        self._right_bc_val = QDoubleSpinBox()
        self._right_bc_val.setRange(-1e30, 1e30)
        self._right_bc_val.setDecimals(10)
        self._right_bc_val.setMinimumWidth(160)
        self._right_bc_val.valueChanged.connect(self._on_change)

        form.addRow("Name:", self._name)
        form.addRow("Initial concentration [mol/L]:", self._init_conc)
        form.addRow("Diffusion in pore [m2/s]:", self._diff_pore)
        form.addRow("Diffusion in biofilm [m2/s]:", self._diff_biofilm)
        form.addRow("Inlet (left) BC type:", self._left_bc_type)
        form.addRow("Inlet (left) BC value:", self._left_bc_val)
        form.addRow("Outlet (right) BC type:", self._right_bc_type)
        form.addRow("Outlet (right) BC value:", self._right_bc_val)

        layout.addLayout(form)
        layout.addStretch()

    def _on_change(self):
        if self.changed:
            self.changed()

    def load_substrate(self, s):
        self._name.blockSignals(True)
        self._init_conc.blockSignals(True)
        self._diff_pore.blockSignals(True)
        self._diff_biofilm.blockSignals(True)
        self._left_bc_type.blockSignals(True)
        self._left_bc_val.blockSignals(True)
        self._right_bc_type.blockSignals(True)
        self._right_bc_val.blockSignals(True)

        self._name.setText(s.name)
        self._init_conc.setValue(s.initial_concentration)
        self._diff_pore.setValue(s.diffusion_in_pore)
        self._diff_biofilm.setValue(s.diffusion_in_biofilm)
        idx_l = self._left_bc_type.findText(s.left_bc_type)
        if idx_l >= 0:
            self._left_bc_type.setCurrentIndex(idx_l)
        self._left_bc_val.setValue(s.left_bc_value)
        idx_r = self._right_bc_type.findText(s.right_bc_type)
        if idx_r >= 0:
            self._right_bc_type.setCurrentIndex(idx_r)
        self._right_bc_val.setValue(s.right_bc_value)

        self._name.blockSignals(False)
        self._init_conc.blockSignals(False)
        self._diff_pore.blockSignals(False)
        self._diff_biofilm.blockSignals(False)
        self._left_bc_type.blockSignals(False)
        self._left_bc_val.blockSignals(False)
        self._right_bc_type.blockSignals(False)
        self._right_bc_val.blockSignals(False)

    def save_to_substrate(self, s):
        s.name = self._name.text().strip()
        s.initial_concentration = self._init_conc.value()
        s.diffusion_in_pore = self._diff_pore.value()
        s.diffusion_in_biofilm = self._diff_biofilm.value()
        s.left_bc_type = self._left_bc_type.currentText()
        s.left_bc_value = self._left_bc_val.value()
        s.right_bc_type = self._right_bc_type.currentText()
        s.right_bc_value = self._right_bc_val.value()

    def get_name(self):
        return self._name.text().strip()


class ChemistryPanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._substrates = []
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("Chemistry"))
        layout.addWidget(self._create_subheading(
            "Define substrates (chemical species) transported in the simulation."))

        body = QHBoxLayout()
        body.setSpacing(12)

        # Left: list
        left = QVBoxLayout()
        left.setSpacing(4)
        self._list = QListWidget()
        self._list.setFixedWidth(200)
        self._list.currentRowChanged.connect(self._on_select)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._add_substrate)
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.clicked.connect(self._remove_substrate)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)

        left.addWidget(QLabel("Substrates"))
        left.addWidget(self._list)
        left.addLayout(btn_row)

        self._count_label = QLabel("0 substrates")
        self._count_label.setProperty("info", True)
        left.addWidget(self._count_label)

        # Right: editor
        self._editor = SubstrateEditor(self._on_editor_change)

        body.addLayout(left)
        body.addWidget(self._editor, 1)
        layout.addLayout(body, 1)

        outer.addWidget(self._create_scroll_area(w))

    def _add_substrate(self):
        idx = len(self._substrates)
        s = Substrate(name=f"substrate{idx}", initial_concentration=0.0,
                      diffusion_in_pore=1.0e-9, diffusion_in_biofilm=2.0e-10)
        self._substrates.append(s)
        self._list.addItem(s.name)
        self._list.setCurrentRow(len(self._substrates) - 1)
        self._update_count()
        self._emit_changed()

    def _remove_substrate(self):
        row = self._list.currentRow()
        if row < 0 or len(self._substrates) == 0:
            return
        self._substrates.pop(row)
        self._list.takeItem(row)
        if self._substrates:
            self._list.setCurrentRow(min(row, len(self._substrates) - 1))
        self._update_count()
        self._emit_changed()

    def _on_select(self, row):
        if row < 0 or row >= len(self._substrates):
            return
        self._editor.load_substrate(self._substrates[row])

    def _on_editor_change(self):
        row = self._list.currentRow()
        if row < 0 or row >= len(self._substrates):
            return
        self._editor.save_to_substrate(self._substrates[row])
        name = self._editor.get_name()
        if name:
            self._list.item(row).setText(name)
        self._emit_changed()

    def _update_count(self):
        n = len(self._substrates)
        self._count_label.setText(f"{n} substrate{'s' if n != 1 else ''}")

    def _populate_fields(self):
        if not self._project:
            return
        self._substrates = [Substrate(**s.to_dict()) for s in self._project.substrates]
        self._list.clear()
        for s in self._substrates:
            self._list.addItem(s.name)
        if self._substrates:
            self._list.setCurrentRow(0)
        self._update_count()

    def collect_data(self, project):
        row = self._list.currentRow()
        if 0 <= row < len(self._substrates):
            self._editor.save_to_substrate(self._substrates[row])
        project.substrates = [Substrate(**s.to_dict()) for s in self._substrates]
