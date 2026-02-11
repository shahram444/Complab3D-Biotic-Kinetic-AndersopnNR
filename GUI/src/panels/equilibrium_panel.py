"""Equilibrium chemistry panel - components, stoichiometry matrix, logK.

Matches C++ solver in complab3d_processors_part4_eqsolver.hh:
  - PCF method + Anderson Acceleration
  - Default: max_iterations=200, tolerance=1e-10, anderson_depth=4
  - Species concentrations via mass action law
  - Solver params are now read from XML by C++ (with fallback to defaults)
"""

from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt
from .base_panel import BasePanel


class EquilibriumPanel(BasePanel):
    """Equilibrium chemistry: enable/disable, component names,
    stoichiometry matrix, and logK values.

    Anderson acceleration solver parameters are read from XML by the
    C++ solver (complab.cpp) with fallback to class defaults in
    complab3d_processors_part4_eqsolver.hh.
    """

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
            "PCF method with Anderson Acceleration (Awada et al. 2025).\n"
            "Mass action law: C_i = 10^(logK[i] + sum_j S[i][j]*logC[j])"))

        # Solver parameters section
        self.add_section("Solver Parameters")
        self.add_widget(self.make_info_label(
            "These parameters are exported to XML and read by the C++ solver\n"
            "(complab.cpp). If not present in XML, C++ uses defaults."))

        pform = self.add_form()
        self._max_iter = self.make_spin(200, 1, 10000)
        self._max_iter.setToolTip("Maximum Newton/Anderson iterations per cell.")
        pform.addRow("Max iterations:", self._max_iter)

        self._tolerance = self.make_double_spin(1e-10, 1e-16, 1.0, 12)
        self._tolerance.setToolTip(
            "Convergence tolerance for residual norm.\n"
            "Default: 1e-10.")
        pform.addRow("Tolerance:", self._tolerance)

        self._anderson_depth = self.make_spin(4, 0, 20)
        self._anderson_depth.setToolTip(
            "Anderson acceleration history depth.\n"
            "0 = simple fixed-point iteration.\n"
            "4 = default, good balance of speed and stability.")
        pform.addRow("Anderson depth:", self._anderson_depth)

        self._beta = self.make_double_spin(1.0, 0.01, 2.0, 4, step=0.1)
        self._beta.setToolTip("Relaxation parameter (damping). 1.0 = no damping.")
        pform.addRow("Relaxation (beta):", self._beta)

        self.add_section("Components")
        form2 = self.add_form()
        self._components = self.make_line_edit("", "e.g. HCO3 Hplus")
        self._components.setToolTip(
            "Space-separated list of equilibrium component names.\n"
            "These must match substrate names exactly as defined in Chemistry.\n"
            "Example: HCO3 Hplus for carbonate system.")
        self._components.textChanged.connect(self._on_components_changed)
        form2.addRow("Component names:", self._components)

        # Substrate count label (helps user see current state)
        self._subs_info = QLabel("")
        self._subs_info.setProperty("info", True)
        form2.addRow("Substrates:", self._subs_info)

        btn_row = QHBoxLayout()
        self._rebuild_btn = self.make_button("Rebuild Matrix", primary=True)
        self._rebuild_btn.setToolTip(
            "Rebuild stoichiometry table with current substrates and components.\n"
            "Preserves existing data where possible.")
        self._rebuild_btn.clicked.connect(self._rebuild_matrix)
        btn_row.addWidget(self._rebuild_btn)

        self._auto_rebuild = self.make_checkbox("Auto-rebuild when substrates change")
        self._auto_rebuild.setChecked(True)
        btn_row.addWidget(self._auto_rebuild)
        btn_row.addStretch()
        self.add_layout(btn_row)

        self._rebuild_status = QLabel("")
        self._rebuild_status.setProperty("info", True)
        self.add_widget(self._rebuild_status)

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
            "Rows with all-zero coefficients are non-equilibrium species (transport only).\n"
            "logK = equilibrium constant (log10) for the mass action expression.\n\n"
            "Physical bounds enforced by C++ solver:\n"
            "  MIN_CONC = 1e-30, MAX_CONC = 10.0\n"
            "  MAX_RELATIVE_CHANGE = 10% per step"))

        self.add_stretch()
        self._on_enabled_changed(False)

    def _on_enabled_changed(self, checked):
        self._components.setEnabled(checked)
        self._rebuild_btn.setEnabled(checked)
        self._table.setEnabled(checked)
        self._max_iter.setEnabled(checked)
        self._tolerance.setEnabled(checked)
        self._anderson_depth.setEnabled(checked)
        self._beta.setEnabled(checked)
        self._auto_rebuild.setEnabled(checked)
        self.data_changed.emit()

    def _on_components_changed(self):
        self.data_changed.emit()

    def _on_cell_changed(self, row, col):
        self.data_changed.emit()

    def _rebuild_matrix(self):
        """Rebuild the stoichiometry + logK table."""
        comp_text = self._components.text().strip()
        if not comp_text:
            self._rebuild_status.setText(
                "Enter component names first (e.g. 'HCO3 Hplus')")
            self._rebuild_status.setStyleSheet("color: #c75050;")
            return
        comp_names = comp_text.split()
        n_comp = len(comp_names)
        n_subs = len(self._substrate_names)
        if n_subs == 0:
            self._rebuild_status.setText(
                "No substrates defined yet. Add substrates in the Chemistry panel first,\n"
                "then return here and click Rebuild Matrix.")
            self._rebuild_status.setStyleSheet("color: #c75050;")
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

        self._rebuild_status.setText(
            f"Matrix built: {n_subs} species x {n_comp} components + logK")
        self._rebuild_status.setStyleSheet("color: #5ca060;")
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
        self._substrate_names = list(names)
        self._subs_info.setText(
            ", ".join(names) if names else "(none defined)")

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
                self._rebuild_status.setText(
                    f"Table resized to {n_subs} species")
                self._rebuild_status.setStyleSheet("color: #5ca060;")
            elif n_subs == self._table.rowCount():
                # Just update labels
                self._table.setVerticalHeaderLabels(names)
        elif len(names) > 0 and self._auto_rebuild.isChecked():
            # No table yet but we have substrates - auto-rebuild if components exist
            comp_text = self._components.text().strip()
            if comp_text:
                self._rebuild_matrix()

    def load_from_project(self, project):
        eq = project.equilibrium
        self.enabled.setChecked(eq.enabled)
        self._components.setText(" ".join(eq.component_names))

        # Load solver params (use defaults if not present)
        self._max_iter.setValue(getattr(eq, 'max_iterations', 200))
        self._tolerance.setValue(getattr(eq, 'tolerance', 1e-10))
        self._anderson_depth.setValue(getattr(eq, 'anderson_depth', 4))
        self._beta.setValue(getattr(eq, 'beta', 1.0))

        # Populate table
        n_comp = len(eq.component_names)
        n_subs = len(project.substrates)
        self._substrate_names = [s.name for s in project.substrates]
        self._subs_info.setText(
            ", ".join(self._substrate_names) if self._substrate_names else "(none defined)")

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

            self._rebuild_status.setText(
                f"Loaded: {n_subs} species x {n_comp} components + logK")
            self._rebuild_status.setStyleSheet("color: #5ca060;")
        else:
            self._table.setRowCount(0)
            self._table.setColumnCount(0)
            if n_subs > 0 and n_comp == 0:
                self._rebuild_status.setText(
                    "No components defined. Enter component names and click Rebuild Matrix.")
                self._rebuild_status.setStyleSheet("color: #c7a050;")
        self._table.blockSignals(False)

    def save_to_project(self, project):
        eq = project.equilibrium
        eq.enabled = self.enabled.isChecked()
        comp_text = self._components.text().strip()
        eq.component_names = comp_text.split() if comp_text else []

        # Save solver params
        eq.max_iterations = self._max_iter.value()
        eq.tolerance = self._tolerance.value()
        eq.anderson_depth = self._anderson_depth.value()
        eq.beta = self._beta.value()

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
