"""Equilibrium chemistry panel - stoichiometry matrix and logK editor."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QCheckBox,
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel
from ..core.project import EquilibriumSettings


class EquilibriumPanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("Equilibrium Chemistry"))
        layout.addWidget(self._create_subheading(
            "Configure fast equilibrium reactions solved via the PCF/Anderson method."))

        # Enable toggle
        self._enabled = self._create_checkbox("Enable equilibrium chemistry solver", False)
        self._enabled.stateChanged.connect(self._on_enable_changed)
        layout.addWidget(self._enabled)

        # Components
        comp_group = self._create_group("Equilibrium Components")
        cl = QVBoxLayout(comp_group)

        comp_row = QHBoxLayout()
        comp_row.addWidget(QLabel("Components (space-separated):"))
        self._components_edit = QLineEdit()
        self._components_edit.setPlaceholderText("e.g., HCO3 Hplus")
        self._components_edit.textChanged.connect(self._emit_changed)
        comp_row.addWidget(self._components_edit, 1)

        self._update_table_btn = QPushButton("Update Table")
        self._update_table_btn.clicked.connect(self._rebuild_table)
        comp_row.addWidget(self._update_table_btn)

        cl.addLayout(comp_row)
        cl.addWidget(self._create_info_label(
            "Components are the master species whose log-concentrations are solved. "
            "Other species are expressed as mass-action products of these components."))
        layout.addWidget(comp_group)

        # Stoichiometry matrix
        stoich_group = self._create_group("Stoichiometry Matrix and logK Values")
        sl = QVBoxLayout(stoich_group)

        sl.addWidget(self._create_info_label(
            "Each row is a species (substrate). Columns are stoichiometric coefficients "
            "for each component. logK is the equilibrium constant (log10).\n"
            "Species not participating in equilibrium should have all zeros."))

        self._table = QTableWidget()
        self._table.setAlternatingRowColors(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.cellChanged.connect(self._on_table_changed)
        sl.addWidget(self._table)

        layout.addWidget(stoich_group)
        layout.addStretch()

        self._content_widget = w
        outer.addWidget(self._create_scroll_area(w))
        self._on_enable_changed()

    def _on_enable_changed(self):
        enabled = self._enabled.isChecked()
        self._components_edit.setEnabled(enabled)
        self._update_table_btn.setEnabled(enabled)
        self._table.setEnabled(enabled)
        self._emit_changed()

    def _rebuild_table(self):
        """Rebuild the stoichiometry table from component names and current substrates."""
        components = self._components_edit.text().strip().split()
        if not components:
            return

        # Get substrate names from project
        substrate_names = []
        if self._project:
            substrate_names = [s.name for s in self._project.substrates]

        if not substrate_names:
            substrate_names = [f"species{i}" for i in range(5)]

        n_species = len(substrate_names)
        n_comp = len(components)

        # Save existing data
        old_data = self._read_table_data()

        self._table.blockSignals(True)
        self._table.setRowCount(n_species)
        self._table.setColumnCount(n_comp + 1)  # +1 for logK

        headers = components + ["logK"]
        self._table.setHorizontalHeaderLabels(headers)
        self._table.setVerticalHeaderLabels(substrate_names)

        for i in range(n_species):
            for j in range(n_comp):
                val = 0.0
                if i < len(old_data) and j < len(old_data[i]):
                    val = old_data[i][j]
                item = QTableWidgetItem(f"{val}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(i, j, item)
            # logK column
            logk = 0.0
            if i < len(old_data) and len(old_data[i]) > 0:
                logk = old_data[i][-1] if len(old_data[i]) > n_comp else 0.0
            item = QTableWidgetItem(f"{logk}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, n_comp, item)

        self._table.blockSignals(False)
        self._emit_changed()

    def _read_table_data(self):
        """Read current table into list of lists."""
        data = []
        for i in range(self._table.rowCount()):
            row = []
            for j in range(self._table.columnCount()):
                item = self._table.item(i, j)
                try:
                    row.append(float(item.text()) if item else 0.0)
                except ValueError:
                    row.append(0.0)
            data.append(row)
        return data

    def _on_table_changed(self, row, col):
        self._emit_changed()

    def set_substrate_names(self, names):
        """Called externally when substrates change."""
        if self._table.rowCount() != len(names):
            self._rebuild_table()
        else:
            self._table.setVerticalHeaderLabels(names)

    def _populate_fields(self):
        if not self._project:
            return
        eq = self._project.equilibrium
        self._enabled.setChecked(eq.enabled)
        self._components_edit.setText(" ".join(eq.components))

        substrate_names = [s.name for s in self._project.substrates]
        n_species = len(substrate_names) if substrate_names else max(len(eq.stoichiometry), len(eq.log_k))
        n_comp = len(eq.components)

        if n_species == 0 and n_comp == 0:
            return

        self._table.blockSignals(True)
        self._table.setRowCount(n_species)
        self._table.setColumnCount(n_comp + 1)
        self._table.setHorizontalHeaderLabels(eq.components + ["logK"])
        if substrate_names:
            self._table.setVerticalHeaderLabels(substrate_names)

        for i in range(n_species):
            for j in range(n_comp):
                val = 0.0
                if i < len(eq.stoichiometry) and j < len(eq.stoichiometry[i]):
                    val = eq.stoichiometry[i][j]
                item = QTableWidgetItem(f"{val}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(i, j, item)
            logk = 0.0
            if i < len(eq.log_k):
                logk = eq.log_k[i]
            item = QTableWidgetItem(f"{logk}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, n_comp, item)

        self._table.blockSignals(False)
        self._on_enable_changed()

    def collect_data(self, project):
        project.equilibrium.enabled = self._enabled.isChecked()
        project.equilibrium.components = self._components_edit.text().strip().split()

        n_comp = len(project.equilibrium.components)
        project.equilibrium.stoichiometry = []
        project.equilibrium.log_k = []

        for i in range(self._table.rowCount()):
            row = []
            for j in range(n_comp):
                item = self._table.item(i, j)
                try:
                    row.append(float(item.text()) if item else 0.0)
                except ValueError:
                    row.append(0.0)
            project.equilibrium.stoichiometry.append(row)

            logk_item = self._table.item(i, n_comp)
            try:
                project.equilibrium.log_k.append(float(logk_item.text()) if logk_item else 0.0)
            except ValueError:
                project.equilibrium.log_k.append(0.0)
