"""Equilibrium chemistry panel - components, stoichiometry matrix, logK."""

from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from .base_panel import BasePanel


class EquilibriumPanel(BasePanel):
    """Equilibrium chemistry: enable/disable, component names,
    stoichiometry matrix, and logK values."""

    def __init__(self, parent=None):
        super().__init__("Equilibrium Chemistry", parent)
        self._substrate_names = []
        self._build_ui()

    def _build_ui(self):
        self.add_section("Equilibrium Solver")
        form = self.add_form()

        self.enabled = self.make_checkbox("Enable equilibrium chemistry")
        self.enabled.toggled.connect(self._on_enabled_changed)
        form.addRow("", self.enabled)

        self.add_widget(self.make_info_label(
            "PCF method with Anderson Acceleration.\n"
            "Solver parameters (hardcoded in C++):\n"
            "  max_iterations = 200, tolerance = 1e-10, anderson_depth = 4"))

        self.add_section("Components")
        form2 = self.add_form()
        self._components = self.make_line_edit("", "e.g. HCO3- H+")
        self._components.setToolTip("Space-separated list of equilibrium component names.")
        self._components.textChanged.connect(self._on_components_changed)
        form2.addRow("Component names:", self._components)

        self._rebuild_btn = self.make_button("Rebuild Matrix")
        self._rebuild_btn.clicked.connect(self._rebuild_matrix)
        form2.addRow("", self._rebuild_btn)

        # Stoichiometry + logK table
        self.add_section("Stoichiometry Matrix and logK")
        self._table = QTableWidget()
        self._table.setMinimumHeight(200)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._table.cellChanged.connect(self._on_cell_changed)
        self.add_widget(self._table)

        self.add_widget(self.make_info_label(
            "Each row = one species (substrate). Columns = component coefficients + logK.\n"
            "Rows with all-zero coefficients are not participating in equilibrium."))

        self.add_stretch()
        self._on_enabled_changed(False)

    def _on_enabled_changed(self, checked):
        self._components.setEnabled(checked)
        self._rebuild_btn.setEnabled(checked)
        self._table.setEnabled(checked)
        self.data_changed.emit()

    def _on_components_changed(self):
        self.data_changed.emit()

    def _on_cell_changed(self, row, col):
        self.data_changed.emit()

    def _rebuild_matrix(self):
        comp_text = self._components.text().strip()
        if not comp_text:
            return
        comp_names = comp_text.split()
        n_comp = len(comp_names)
        n_subs = len(self._substrate_names)
        if n_comp == 0 or n_subs == 0:
            return

        # Preserve existing data where possible
        old_data = self._read_table()

        self._table.blockSignals(True)
        self._table.setRowCount(n_subs)
        self._table.setColumnCount(n_comp + 1)
        headers = comp_names + ["logK"]
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setVerticalHeaderLabels(self._substrate_names)

        for r in range(n_subs):
            for c in range(n_comp + 1):
                val = 0.0
                if r < len(old_data) and c < len(old_data[r]):
                    val = old_data[r][c]
                item = QTableWidgetItem(f"{val:.4g}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(r, c, item)
        self._table.blockSignals(False)
        self.data_changed.emit()

    def _read_table(self):
        """Read current table data as 2D list."""
        data = []
        for r in range(self._table.rowCount()):
            row = []
            for c in range(self._table.columnCount()):
                item = self._table.item(r, c)
                try:
                    row.append(float(item.text()) if item else 0.0)
                except (ValueError, AttributeError):
                    row.append(0.0)
            data.append(row)
        return data

    def set_substrate_names(self, names: list):
        """Called when substrates change in the Chemistry panel."""
        old_names = self._substrate_names
        self._substrate_names = list(names)

        # Update the vertical header labels if table has rows
        if self._table.rowCount() > 0:
            old_data = self._read_table()
            n_comp = self._table.columnCount() - 1 if self._table.columnCount() > 0 else 0
            n_subs = len(names)

            if n_subs != self._table.rowCount() and n_comp > 0:
                # Row count changed - resize table preserving data
                self._table.blockSignals(True)
                self._table.setRowCount(n_subs)
                self._table.setVerticalHeaderLabels(names)
                for r in range(n_subs):
                    for c in range(n_comp + 1):
                        val = 0.0
                        if r < len(old_data) and c < len(old_data[r]):
                            val = old_data[r][c]
                        item = QTableWidgetItem(f"{val:.4g}")
                        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                        self._table.setItem(r, c, item)
                self._table.blockSignals(False)
            elif n_subs == self._table.rowCount():
                # Just update labels
                self._table.setVerticalHeaderLabels(names)

    def load_from_project(self, project):
        eq = project.equilibrium
        self.enabled.setChecked(eq.enabled)
        self._components.setText(" ".join(eq.component_names))

        # Populate table
        n_comp = len(eq.component_names)
        n_subs = len(project.substrates)
        self._substrate_names = [s.name for s in project.substrates]

        self._table.blockSignals(True)
        if n_comp > 0 and n_subs > 0:
            self._table.setRowCount(n_subs)
            self._table.setColumnCount(n_comp + 1)
            headers = eq.component_names + ["logK"]
            self._table.setHorizontalHeaderLabels(headers)
            self._table.setVerticalHeaderLabels(self._substrate_names)

            for r in range(n_subs):
                for c in range(n_comp):
                    val = 0.0
                    if r < len(eq.stoichiometry) and c < len(eq.stoichiometry[r]):
                        val = eq.stoichiometry[r][c]
                    item = QTableWidgetItem(f"{val:.4g}")
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self._table.setItem(r, c, item)
                # logK column
                logk = eq.log_k[r] if r < len(eq.log_k) else 0.0
                item = QTableWidgetItem(f"{logk:.4g}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(r, n_comp, item)
        else:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
        self._table.blockSignals(False)

    def save_to_project(self, project):
        eq = project.equilibrium
        eq.enabled = self.enabled.isChecked()
        eq.component_names = self._components.text().strip().split()

        n_comp = len(eq.component_names)
        n_subs = self._table.rowCount()

        eq.stoichiometry = []
        eq.log_k = []
        for r in range(n_subs):
            row = []
            for c in range(n_comp):
                item = self._table.item(r, c)
                try:
                    row.append(float(item.text()) if item else 0.0)
                except (ValueError, AttributeError):
                    row.append(0.0)
            eq.stoichiometry.append(row)
            # logK
            logk_item = self._table.item(r, n_comp) if n_comp < self._table.columnCount() else None
            try:
                eq.log_k.append(float(logk_item.text()) if logk_item else 0.0)
            except (ValueError, AttributeError):
                eq.log_k.append(0.0)
