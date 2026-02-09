"""Chemistry panel - substrate list and per-substrate editor."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget,
    QPushButton, QListWidget, QListWidgetItem,
)
from PySide6.QtCore import Signal
from .base_panel import BasePanel
from ..core.project import Substrate


class ChemistryPanel(BasePanel):
    """Substrate management: add/remove substrates, edit properties."""

    substrates_changed = Signal(list)  # emits list of substrate names

    def __init__(self, parent=None):
        super().__init__("Chemistry - Substrates", parent)
        self._substrates = []
        self._current_idx = -1
        self._build_ui()

    def _build_ui(self):
        self.add_section("Substrates")

        # List + buttons
        row = QHBoxLayout()
        self._list = QListWidget()
        self._list.setMaximumHeight(120)
        self._list.currentRowChanged.connect(self._on_select)
        row.addWidget(self._list, 1)

        btn_col = QVBoxLayout()
        add_btn = self.make_button("Add")
        add_btn.clicked.connect(self._add_substrate)
        rem_btn = self.make_button("Remove")
        rem_btn.setProperty("danger", True)
        rem_btn.clicked.connect(self._remove_substrate)
        btn_col.addWidget(add_btn)
        btn_col.addWidget(rem_btn)
        btn_col.addStretch()
        row.addLayout(btn_col)
        self.add_layout(row)

        # Editor
        self.add_section("Substrate Properties")
        form = self.add_form()

        self._name = self.make_line_edit("", "Substrate name")
        self._name.textChanged.connect(self._on_edited)
        form.addRow("Name:", self._name)

        self._c0 = self.make_double_spin(0.0, 0, 1e12, 8)
        self._c0.valueChanged.connect(self._on_edited)
        form.addRow("Initial concentration:", self._c0)

        self._d_pore = self.make_double_spin(1e-9, 0, 1e6, 10)
        self._d_pore.valueChanged.connect(self._on_edited)
        form.addRow("Diffusion in pore:", self._d_pore)

        self._d_biofilm = self.make_double_spin(2e-10, 0, 1e6, 10)
        self._d_biofilm.valueChanged.connect(self._on_edited)
        form.addRow("Diffusion in biofilm:", self._d_biofilm)

        self.add_section("Boundary Conditions")
        form2 = self.add_form()

        self._left_type = self.make_combo(["Dirichlet", "Neumann"])
        self._left_type.currentIndexChanged.connect(self._on_edited)
        form2.addRow("Left BC type:", self._left_type)

        self._left_val = self.make_double_spin(0.0, -1e12, 1e12, 8)
        self._left_val.valueChanged.connect(self._on_edited)
        form2.addRow("Left BC value:", self._left_val)

        self._right_type = self.make_combo(["Dirichlet", "Neumann"])
        self._right_type.currentIndexChanged.connect(self._on_edited)
        form2.addRow("Right BC type:", self._right_type)

        self._right_val = self.make_double_spin(0.0, -1e12, 1e12, 8)
        self._right_val.valueChanged.connect(self._on_edited)
        form2.addRow("Right BC value:", self._right_val)

        self.add_stretch()

    def _add_substrate(self):
        idx = len(self._substrates)
        s = Substrate(name=f"substrate_{idx}")
        self._substrates.append(s)
        self._list.addItem(s.name)
        self._list.setCurrentRow(idx)
        self._emit_names()

    def _remove_substrate(self):
        idx = self._list.currentRow()
        if idx < 0:
            return
        self._substrates.pop(idx)
        self._list.takeItem(idx)
        self._current_idx = -1
        if self._list.count() > 0:
            self._list.setCurrentRow(min(idx, self._list.count() - 1))
        self._emit_names()

    def _on_select(self, idx):
        self._save_current()
        self._current_idx = idx
        if 0 <= idx < len(self._substrates):
            s = self._substrates[idx]
            self._name.blockSignals(True)
            self._name.setText(s.name)
            self._name.blockSignals(False)
            self._c0.setValue(s.initial_concentration)
            self._d_pore.setValue(s.diffusion_in_pore)
            self._d_biofilm.setValue(s.diffusion_in_biofilm)
            self._left_type.setCurrentText(s.left_boundary_type)
            self._left_val.setValue(s.left_boundary_condition)
            self._right_type.setCurrentText(s.right_boundary_type)
            self._right_val.setValue(s.right_boundary_condition)

    def _on_edited(self):
        self._save_current()
        # Update list item name
        if 0 <= self._current_idx < self._list.count():
            self._list.item(self._current_idx).setText(self._name.text())
        self._emit_names()

    def _save_current(self):
        idx = self._current_idx
        if idx < 0 or idx >= len(self._substrates):
            return
        s = self._substrates[idx]
        s.name = self._name.text()
        s.initial_concentration = self._c0.value()
        s.diffusion_in_pore = self._d_pore.value()
        s.diffusion_in_biofilm = self._d_biofilm.value()
        s.left_boundary_type = self._left_type.currentText()
        s.left_boundary_condition = self._left_val.value()
        s.right_boundary_type = self._right_type.currentText()
        s.right_boundary_condition = self._right_val.value()

    def _emit_names(self):
        names = [s.name for s in self._substrates]
        self.substrates_changed.emit(names)
        self.data_changed.emit()

    def load_from_project(self, project):
        self._current_idx = -1
        self._substrates = [Substrate(
            name=s.name,
            initial_concentration=s.initial_concentration,
            diffusion_in_pore=s.diffusion_in_pore,
            diffusion_in_biofilm=s.diffusion_in_biofilm,
            left_boundary_type=s.left_boundary_type,
            right_boundary_type=s.right_boundary_type,
            left_boundary_condition=s.left_boundary_condition,
            right_boundary_condition=s.right_boundary_condition,
        ) for s in project.substrates]
        self._list.clear()
        for s in self._substrates:
            self._list.addItem(s.name)
        if self._substrates:
            self._list.setCurrentRow(0)
        self._emit_names()

    def save_to_project(self, project):
        self._save_current()
        project.substrates = [Substrate(
            name=s.name,
            initial_concentration=s.initial_concentration,
            diffusion_in_pore=s.diffusion_in_pore,
            diffusion_in_biofilm=s.diffusion_in_biofilm,
            left_boundary_type=s.left_boundary_type,
            right_boundary_type=s.right_boundary_type,
            left_boundary_condition=s.left_boundary_condition,
            right_boundary_condition=s.right_boundary_condition,
        ) for s in self._substrates]

    def select_substrate(self, index: int):
        if 0 <= index < self._list.count():
            self._list.setCurrentRow(index)
