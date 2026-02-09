"""General / Simulation Mode settings panel."""

from PySide6.QtWidgets import QFormLayout, QLabel, QHBoxLayout, QLineEdit
from PySide6.QtCore import Qt
from .base_panel import BasePanel


class GeneralPanel(BasePanel):
    """Simulation mode configuration: biotic/abiotic, kinetics, paths."""

    def __init__(self, parent=None):
        super().__init__("Simulation Mode", parent)
        self._build_ui()

    def _build_ui(self):
        self.add_section("Mode Selection")
        form = self.add_form()

        self.biotic_mode = self.make_checkbox("Biotic mode (with microbes)")
        self.biotic_mode.setToolTip(
            "Enable biotic simulation with microbes and biomass.\n"
            "Disable for transport-only or abiotic kinetics.")
        form.addRow("", self.biotic_mode)

        self.enable_kinetics = self.make_checkbox("Enable biotic kinetics")
        self.enable_kinetics.setToolTip(
            "Enable Monod growth kinetics for biotic reactions.\n"
            "Requires biotic_mode=true.")
        form.addRow("", self.enable_kinetics)

        self.enable_abiotic = self.make_checkbox("Enable abiotic kinetics")
        self.enable_abiotic.setToolTip(
            "Enable chemical reactions between substrates (no microbes).\n"
            "Examples: first-order decay, bimolecular reactions.")
        form.addRow("", self.enable_abiotic)

        self.enable_diagnostics = self.make_checkbox("Validation diagnostics")
        self.enable_diagnostics.setToolTip(
            "Print detailed per-iteration output for debugging.\n"
            "Adds computational overhead - use for debugging only.")
        form.addRow("", self.enable_diagnostics)

        # Connections
        self.biotic_mode.toggled.connect(self._on_biotic_changed)
        self.biotic_mode.toggled.connect(lambda: self.data_changed.emit())
        self.enable_kinetics.toggled.connect(lambda: self.data_changed.emit())
        self.enable_abiotic.toggled.connect(lambda: self.data_changed.emit())
        self.enable_diagnostics.toggled.connect(lambda: self.data_changed.emit())

        self.add_section("Paths")
        form2 = self.add_form()
        self.src_path = self.make_line_edit("src", "Source directory")
        self.input_path = self.make_line_edit("input", "Input directory")
        self.output_path = self.make_line_edit("output", "Output directory")
        form2.addRow("Source path:", self.src_path)
        form2.addRow("Input path:", self.input_path)
        form2.addRow("Output path:", self.output_path)

        self.add_section("Information")
        info = self.make_info_label(
            "CompLaB3D supports multiple simulation modes:\n\n"
            "Biotic: Microbes with Monod kinetics, CA/LBM/FD biomass solvers\n"
            "Abiotic: Chemical kinetics without microbes (first-order, bimolecular)\n"
            "Equilibrium: Speciation solver with Anderson acceleration\n"
            "Any combination of the above can be enabled simultaneously.")
        self.add_widget(info)

        self.add_stretch()

    def _on_biotic_changed(self, checked):
        self.enable_kinetics.setEnabled(checked)
        if not checked:
            self.enable_kinetics.setChecked(False)

    def load_from_project(self, project):
        sm = project.simulation_mode
        self.biotic_mode.setChecked(sm.biotic_mode)
        self.enable_kinetics.setChecked(sm.enable_kinetics)
        self.enable_abiotic.setChecked(sm.enable_abiotic_kinetics)
        self.enable_diagnostics.setChecked(sm.enable_validation_diagnostics)
        self.src_path.setText(project.path_settings.src_path)
        self.input_path.setText(project.path_settings.input_path)
        self.output_path.setText(project.path_settings.output_path)

    def save_to_project(self, project):
        sm = project.simulation_mode
        sm.biotic_mode = self.biotic_mode.isChecked()
        sm.enable_kinetics = self.enable_kinetics.isChecked()
        sm.enable_abiotic_kinetics = self.enable_abiotic.isChecked()
        sm.enable_validation_diagnostics = self.enable_diagnostics.isChecked()
        project.path_settings.src_path = self.src_path.text()
        project.path_settings.input_path = self.input_path.text()
        project.path_settings.output_path = self.output_path.text()
