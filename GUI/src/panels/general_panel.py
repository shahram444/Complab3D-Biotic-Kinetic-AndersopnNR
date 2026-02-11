"""General / Simulation Mode settings panel."""

from PySide6.QtWidgets import (
    QFormLayout, QLabel, QHBoxLayout, QLineEdit, QButtonGroup,
    QRadioButton,
)
from PySide6.QtCore import Qt
from .base_panel import BasePanel


class GeneralPanel(BasePanel):
    """Simulation mode configuration: biotic/abiotic, kinetics, paths."""

    def __init__(self, parent=None):
        super().__init__("Simulation Mode", parent)
        self._build_ui()

    def _build_ui(self):
        # ── Simulation Type ─────────────────────────────────────────
        self.add_section("Simulation Type")
        info1 = self.make_info_label(
            "Select the primary simulation type. This controls which "
            "kinetics modules are active in the solver.")
        self.add_widget(info1)

        self._mode_group = QButtonGroup(self)
        self._mode_group.setExclusive(True)

        self._radio_transport = QRadioButton(
            "Transport only  (flow + advection-diffusion, no reactions)")
        self._radio_abiotic = QRadioButton(
            "Abiotic  (chemical kinetics between substrates, no microbes)")
        self._radio_biotic = QRadioButton(
            "Biotic  (microbial growth with Monod kinetics)")
        self._radio_coupled = QRadioButton(
            "Coupled  (biotic + abiotic kinetics simultaneously)")

        self._mode_group.addButton(self._radio_transport, 0)
        self._mode_group.addButton(self._radio_abiotic, 1)
        self._mode_group.addButton(self._radio_biotic, 2)
        self._mode_group.addButton(self._radio_coupled, 3)

        for rb in [self._radio_transport, self._radio_abiotic,
                   self._radio_biotic, self._radio_coupled]:
            self.add_widget(rb)

        self._radio_biotic.setChecked(True)
        self._mode_group.idToggled.connect(self._on_mode_changed)

        # ── Additional Options ──────────────────────────────────────
        self.add_section("Additional Options")

        self.enable_diagnostics = self.make_checkbox("Validation diagnostics")
        self.enable_diagnostics.setToolTip(
            "Print detailed per-iteration output for debugging.\n"
            "Adds computational overhead - use for debugging only.")
        form0 = self.add_form()
        form0.addRow("", self.enable_diagnostics)
        self.enable_diagnostics.toggled.connect(lambda: self.data_changed.emit())

        # ── Paths ───────────────────────────────────────────────────
        self.add_section("Paths")
        form2 = self.add_form()
        self.src_path = self.make_line_edit("src", "Source directory")
        self.input_path = self.make_line_edit("input", "Input directory")
        self.output_path = self.make_line_edit("output", "Output directory")
        form2.addRow("Source path:", self.src_path)
        form2.addRow("Input path:", self.input_path)
        form2.addRow("Output path:", self.output_path)

        # ── Mode summary ────────────────────────────────────────────
        self.add_section("Active Modules Summary")
        self._summary = QLabel()
        self._summary.setWordWrap(True)
        self._summary.setProperty("info", True)
        self.add_widget(self._summary)
        self._update_summary()

        self.add_stretch()

    def _on_mode_changed(self, _id, _checked):
        self._update_summary()
        self.data_changed.emit()

    def _update_summary(self):
        mode_id = self._mode_group.checkedId()
        lines = []
        if mode_id == 0:
            lines = [
                "Navier-Stokes flow solver: ON",
                "Advection-Diffusion transport: ON",
                "Biotic kinetics (defineKinetics.hh): OFF",
                "Abiotic kinetics (defineAbioticKinetics.hh): OFF",
                "Microbiology / biomass: OFF",
            ]
        elif mode_id == 1:
            lines = [
                "Navier-Stokes flow solver: ON",
                "Advection-Diffusion transport: ON",
                "Biotic kinetics: OFF",
                "Abiotic kinetics (defineAbioticKinetics.hh): ON",
                "Microbiology / biomass: OFF",
            ]
        elif mode_id == 2:
            lines = [
                "Navier-Stokes flow solver: ON",
                "Advection-Diffusion transport: ON",
                "Biotic kinetics (defineKinetics.hh): ON",
                "Abiotic kinetics: OFF",
                "Microbiology / biomass: ON",
            ]
        elif mode_id == 3:
            lines = [
                "Navier-Stokes flow solver: ON",
                "Advection-Diffusion transport: ON",
                "Biotic kinetics (defineKinetics.hh): ON",
                "Abiotic kinetics (defineAbioticKinetics.hh): ON",
                "Microbiology / biomass: ON",
            ]
        self._summary.setText("\n".join(lines))

    def _get_mode_flags(self):
        """Convert radio selection to the three boolean flags."""
        mode_id = self._mode_group.checkedId()
        if mode_id == 0:  # Transport only
            return False, False, False
        elif mode_id == 1:  # Abiotic
            return False, False, True
        elif mode_id == 2:  # Biotic
            return True, True, False
        else:  # Coupled
            return True, True, True

    def _set_mode_from_flags(self, biotic, kinetics, abiotic):
        """Set radio button from the three boolean flags."""
        if biotic and abiotic:
            self._radio_coupled.setChecked(True)
        elif biotic and kinetics:
            self._radio_biotic.setChecked(True)
        elif abiotic:
            self._radio_abiotic.setChecked(True)
        else:
            self._radio_transport.setChecked(True)

    def load_from_project(self, project):
        sm = project.simulation_mode
        self._set_mode_from_flags(
            sm.biotic_mode, sm.enable_kinetics, sm.enable_abiotic_kinetics)
        self.enable_diagnostics.setChecked(sm.enable_validation_diagnostics)
        self.src_path.setText(project.path_settings.src_path)
        self.input_path.setText(project.path_settings.input_path)
        self.output_path.setText(project.path_settings.output_path)
        self._update_summary()

    def save_to_project(self, project):
        biotic, kinetics, abiotic = self._get_mode_flags()
        sm = project.simulation_mode
        sm.biotic_mode = biotic
        sm.enable_kinetics = kinetics
        sm.enable_abiotic_kinetics = abiotic
        sm.enable_validation_diagnostics = self.enable_diagnostics.isChecked()
        project.path_settings.src_path = self.src_path.text()
        project.path_settings.input_path = self.input_path.text()
        project.path_settings.output_path = self.output_path.text()
