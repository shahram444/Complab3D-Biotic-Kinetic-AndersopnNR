"""Parameter sweep panel - queue multiple simulations with varying parameters."""

from PySide6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
)
from PySide6.QtCore import Signal, Qt
from .base_panel import BasePanel


# Parameters that can be swept
SWEEP_PARAMS = {
    "Peclet number": ("fluid", "peclet"),
    "Pressure drop (delta_P)": ("fluid", "delta_P"),
    "Relaxation time (tau)": ("fluid", "tau"),
    "ADE max iterations": ("iteration", "ade_max_iT"),
    "NS max iterations (phase 1)": ("iteration", "ns_max_iT1"),
    "NS convergence (phase 1)": ("iteration", "ns_converge_iT1"),
    "ADE convergence": ("iteration", "ade_converge_iT"),
    "Domain nx": ("domain", "nx"),
    "Domain ny": ("domain", "ny"),
    "Domain nz": ("domain", "nz"),
    "Grid spacing dx": ("domain", "dx"),
    "Max biomass density": ("microbiology", "maximum_biomass_density"),
    "Biofilm fraction threshold": ("microbiology", "thrd_biofilm_fraction"),
    "Save VTK interval": ("io_settings", "save_vtk_interval"),
}


class SweepPanel(BasePanel):
    """Configure and queue parameter sweeps for batch execution."""

    sweep_requested = Signal(list)  # list of (param_name, values)

    def __init__(self, parent=None):
        super().__init__("Parameter Sweep", parent)
        self._build_ui()

    def _build_ui(self):
        self.add_section("Sweep Configuration")
        self.add_widget(self.make_info_label(
            "Define a parameter to sweep across multiple values.\n"
            "Each value generates a separate simulation run."))

        form = self.add_form()

        # Parameter selector
        self._param_combo = QComboBox()
        self._param_combo.addItems(list(SWEEP_PARAMS.keys()))
        form.addRow("Parameter:", self._param_combo)

        # Sweep mode
        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["Linear range", "Custom values"])
        self._mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        form.addRow("Mode:", self._mode_combo)

        # Linear range controls
        self.add_section("Linear Range")
        range_form = self.add_form()
        self._start = self.make_double_spin(0.1, -1e30, 1e30, 6, step=0.1)
        self._end = self.make_double_spin(10.0, -1e30, 1e30, 6, step=0.1)
        self._steps = self.make_spin(5, 2, 100)
        range_form.addRow("Start:", self._start)
        range_form.addRow("End:", self._end)
        range_form.addRow("Steps:", self._steps)

        # Custom values
        self.add_section("Custom Values")
        self._custom_edit = self.make_line_edit(
            "", "e.g. 0.1, 0.5, 1.0, 2.0, 5.0")
        self._custom_edit.setToolTip(
            "Comma-separated list of values to sweep over.")
        self.add_widget(self._custom_edit)

        # Generate preview
        self.add_section("Sweep Preview")

        gen_row = QHBoxLayout()
        gen_btn = self.make_button("Generate Preview", primary=True)
        gen_btn.clicked.connect(self._generate_preview)
        gen_row.addWidget(gen_btn)

        clear_btn = self.make_button("Clear")
        clear_btn.clicked.connect(self._clear_preview)
        gen_row.addWidget(clear_btn)
        gen_row.addStretch()
        self.add_layout(gen_row)

        # Preview table
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["#", "Parameter", "Value"])
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch)
        self._table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setMinimumHeight(150)
        self.add_widget(self._table)

        self._summary_lbl = QLabel("")
        self._summary_lbl.setProperty("info", True)
        self.add_widget(self._summary_lbl)

        # Queue button
        self.add_section("Execution")
        self.add_widget(self.make_info_label(
            "Queue all sweep runs. Each run creates a subdirectory with "
            "its own CompLaB.xml and output files."))

        queue_row = QHBoxLayout()
        self._queue_btn = self.make_button("Queue Sweep Runs", primary=True)
        self._queue_btn.setEnabled(False)
        self._queue_btn.clicked.connect(self._queue_runs)
        queue_row.addWidget(self._queue_btn)
        queue_row.addStretch()
        self.add_layout(queue_row)

        self.add_stretch()

    def _on_mode_changed(self, idx):
        """Toggle visibility based on mode."""
        pass  # Both sections always visible for simplicity

    def _generate_preview(self):
        """Generate the sweep values and populate the table."""
        param_name = self._param_combo.currentText()
        mode = self._mode_combo.currentIndex()

        if mode == 0:  # Linear range
            start = self._start.value()
            end = self._end.value()
            steps = self._steps.value()
            if steps < 2:
                steps = 2
            step_size = (end - start) / (steps - 1)
            values = [start + i * step_size for i in range(steps)]
        else:  # Custom values
            text = self._custom_edit.text().strip()
            if not text:
                self._summary_lbl.setText("Enter comma-separated values.")
                return
            try:
                values = [float(v.strip()) for v in text.split(",") if v.strip()]
            except ValueError:
                self._summary_lbl.setText("Invalid values. Use comma-separated numbers.")
                return

        # Populate table
        self._table.setRowCount(len(values))
        for i, val in enumerate(values):
            self._table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._table.setItem(i, 1, QTableWidgetItem(param_name))
            self._table.setItem(i, 2, QTableWidgetItem(f"{val:.6g}"))

        self._summary_lbl.setText(
            f"{len(values)} runs queued for '{param_name}'")
        self._queue_btn.setEnabled(len(values) > 0)

    def _clear_preview(self):
        self._table.setRowCount(0)
        self._summary_lbl.setText("")
        self._queue_btn.setEnabled(False)

    def _queue_runs(self):
        """Emit the sweep configuration."""
        runs = []
        for row in range(self._table.rowCount()):
            param = self._table.item(row, 1).text()
            value = float(self._table.item(row, 2).text())
            runs.append((param, value))
        if runs:
            self.sweep_requested.emit(runs)

    def get_sweep_config(self):
        """Return list of (section, field, value) tuples for the sweep."""
        param_name = self._param_combo.currentText()
        if param_name not in SWEEP_PARAMS:
            return []

        section, field = SWEEP_PARAMS[param_name]
        configs = []
        for row in range(self._table.rowCount()):
            value = float(self._table.item(row, 2).text())
            configs.append((section, field, value))
        return configs
