"""Fluid / Flow settings panel."""

from .base_panel import BasePanel


class FluidPanel(BasePanel):
    """Navier-Stokes flow parameters: pressure, Peclet, relaxation time."""

    def __init__(self, parent=None):
        super().__init__("Fluid / Flow Settings", parent)
        self._build_ui()

    def _build_ui(self):
        self.add_section("Flow Parameters")
        form = self.add_form()

        self.delta_P = self.make_double_spin(2e-3, 0, 1e6, 8)
        self.delta_P.setToolTip(
            "Pressure gradient across the domain (lattice units).\n"
            "Set to 0 for no flow (diffusion only).")
        form.addRow("Pressure gradient (delta_P):", self.delta_P)

        self.peclet = self.make_double_spin(1.0, 0, 1e6, 4)
        self.peclet.setToolTip(
            "Peclet number: ratio of advective to diffusive transport.\n"
            "Pe = u * L / D. Set to 0 if delta_P = 0.")
        form.addRow("Peclet number:", self.peclet)

        self.tau = self.make_double_spin(0.8, 0.501, 2.0, 4)
        self.tau.setToolTip(
            "LBM relaxation time for Navier-Stokes.\n"
            "Must be > 0.5 for stability. Typical: 0.6 - 1.5.")
        form.addRow("Relaxation time (tau):", self.tau)

        self.add_section("Performance")
        form2 = self.add_form()
        self.track_perf = self.make_checkbox("Track performance metrics")
        self.track_perf.setToolTip("Log computational performance per iteration.")
        form2.addRow("", self.track_perf)

        self.add_section("Stability Guidelines")
        self.add_widget(self.make_info_label(
            "LBM stability requirements:\n"
            "  - tau > 0.5 (strict)\n"
            "  - Mach number Ma < 0.3 (guideline)\n"
            "  - CFL < 1 (strict)\n"
            "  - Grid Peclet < 2 (guideline)\n\n"
            "The solver performs automatic stability checks after "
            "the initial flow simulation."))
        self.add_stretch()

        # Real-time validation
        self.tau.valueChanged.connect(self._validate_tau)
        self.delta_P.valueChanged.connect(self._validate_delta_P)

    def _validate_tau(self):
        val = self.tau.value()
        if val <= 0.5:
            self.set_validation(self.tau, "error",
                                "tau must be > 0.5 for LBM stability.")
        elif val > 1.5:
            self.set_validation(self.tau, "warning",
                                "tau > 1.5 may cause slow convergence.")
        else:
            self.clear_validation(self.tau)

    def _validate_delta_P(self):
        val = self.delta_P.value()
        if val < 0:
            self.set_validation(self.delta_P, "error",
                                "Pressure gradient cannot be negative.")
        elif val > 0.1:
            self.set_validation(self.delta_P, "warning",
                                "High pressure gradient may cause instability.")
        else:
            self.clear_validation(self.delta_P)

    def load_from_project(self, project):
        f = project.fluid
        self.delta_P.setValue(f.delta_P)
        self.peclet.setValue(f.peclet)
        self.tau.setValue(f.tau)
        self.track_perf.setChecked(f.track_performance)

    def save_to_project(self, project):
        f = project.fluid
        f.delta_P = self.delta_P.value()
        f.peclet = self.peclet.value()
        f.tau = self.tau.value()
        f.track_performance = self.track_perf.isChecked()
