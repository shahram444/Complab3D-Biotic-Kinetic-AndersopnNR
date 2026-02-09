"""Simulation mode configuration panel."""

from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QFormLayout, QLabel
from PySide6.QtCore import Qt
from .base_panel import BasePanel


class SimulationModePanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        content = self._build_content()
        outer.addWidget(self._create_scroll_area(content))

    def _build_content(self):
        widget = self._build_widget()
        return widget

    def _build_widget(self):
        from PySide6.QtWidgets import QWidget
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("General Settings"))
        layout.addWidget(self._create_subheading(
            "Configure simulation mode, solver selection, and file paths."))

        # --- Simulation Mode ---
        group = self._create_group("Simulation Mode")
        g_layout = QVBoxLayout(group)

        self._biotic_check = self._create_checkbox("Biotic mode (include microorganisms)", True)
        self._kinetics_check = self._create_checkbox("Enable biotic kinetics (Monod growth)", True)
        self._abiotic_check = self._create_checkbox("Enable abiotic kinetics (chemical reactions)", False)
        self._diagnostics_check = self._create_checkbox("Enable validation diagnostics (debug output)", False)

        self._biotic_check.stateChanged.connect(self._on_biotic_changed)

        g_layout.addWidget(self._biotic_check)
        g_layout.addWidget(self._kinetics_check)
        g_layout.addWidget(self._abiotic_check)
        g_layout.addWidget(self._diagnostics_check)

        mode_info = QLabel(
            "Biotic mode: Includes microbial growth, biomass, and biofilm expansion.\n"
            "Abiotic mode: Transport with optional chemical reactions, no microorganisms.\n"
            "Both kinetics modes can be enabled simultaneously for coupled simulations."
        )
        mode_info.setProperty("info", True)
        mode_info.setWordWrap(True)
        g_layout.addWidget(mode_info)

        layout.addWidget(group)

        # --- Active Solvers Summary ---
        solver_group = self._create_group("Active Solvers")
        s_layout = QVBoxLayout(solver_group)
        self._solver_summary = QLabel("")
        self._solver_summary.setWordWrap(True)
        s_layout.addWidget(self._solver_summary)
        layout.addWidget(solver_group)

        # --- Paths ---
        path_group = self._create_group("File Paths")
        pf = self._create_form()
        self._src_path = self._create_line_edit("src")
        self._input_path = self._create_line_edit("input")
        self._output_path = self._create_line_edit("output")
        pf.addRow("Source path:", self._src_path)
        pf.addRow("Input path:", self._input_path)
        pf.addRow("Output path:", self._output_path)
        path_group.setLayout(pf)
        layout.addWidget(path_group)

        layout.addStretch()
        self._update_solver_summary()
        return w

    def _on_biotic_changed(self, state):
        biotic = self._biotic_check.isChecked()
        self._kinetics_check.setEnabled(biotic)
        if not biotic:
            self._kinetics_check.setChecked(False)
        self._update_solver_summary()
        self._emit_changed()

    def _update_solver_summary(self):
        lines = []
        lines.append("Navier-Stokes flow solver (always active)")
        lines.append("Advection-diffusion transport solver (always active)")
        if self._biotic_check.isChecked() and self._kinetics_check.isChecked():
            lines.append("Biotic kinetics solver (Monod growth / decay)")
        if self._abiotic_check.isChecked():
            lines.append("Abiotic kinetics solver (chemical reactions)")
        lines.append("Equilibrium chemistry solver (configure in Equilibrium panel)")
        self._solver_summary.setText("\n".join(f"  {l}" for l in lines))

    def _populate_fields(self):
        if not self._project:
            return
        sm = self._project.simulation_mode
        self._biotic_check.setChecked(sm.biotic_mode)
        self._kinetics_check.setChecked(sm.enable_kinetics)
        self._kinetics_check.setEnabled(sm.biotic_mode)
        self._abiotic_check.setChecked(sm.enable_abiotic_kinetics)
        self._diagnostics_check.setChecked(sm.enable_validation_diagnostics)
        self._src_path.setText(self._project.paths.src_path)
        self._input_path.setText(self._project.paths.input_path)
        self._output_path.setText(self._project.paths.output_path)
        self._update_solver_summary()

    def collect_data(self, project):
        project.simulation_mode.biotic_mode = self._biotic_check.isChecked()
        project.simulation_mode.enable_kinetics = self._kinetics_check.isChecked()
        project.simulation_mode.enable_abiotic_kinetics = self._abiotic_check.isChecked()
        project.simulation_mode.enable_validation_diagnostics = self._diagnostics_check.isChecked()
        project.paths.src_path = self._src_path.text()
        project.paths.input_path = self._input_path.text()
        project.paths.output_path = self._output_path.text()
