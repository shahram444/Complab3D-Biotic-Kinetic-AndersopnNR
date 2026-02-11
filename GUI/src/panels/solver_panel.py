"""Solver / iteration settings panel."""

from .base_panel import BasePanel
from ..widgets.collapsible_section import CollapsibleSection
from PySide6.QtWidgets import QFormLayout


class SolverPanel(BasePanel):
    """Iteration control parameters for NS and ADE solvers."""

    def __init__(self, parent=None):
        super().__init__("Solver Settings", parent)
        self._build_ui()

    def _build_ui(self):
        # Navier-Stokes
        self.add_section("Navier-Stokes (Flow) Solver")
        form = self.add_form()

        self.ns_max_iT1 = self.make_spin(100000, 0)
        self.ns_max_iT1.setToolTip("Max NS iterations for initial flow solve (phase 1).")
        form.addRow("Phase 1 max iterations:", self.ns_max_iT1)

        self.ns_converge_iT1 = self.make_double_spin(1e-8, 0, 1, 12)
        self.ns_converge_iT1.setToolTip("Convergence criterion for initial NS solve.")
        form.addRow("Phase 1 convergence:", self.ns_converge_iT1)

        self.ns_max_iT2 = self.make_spin(100000, 0)
        self.ns_max_iT2.setToolTip("Max NS iterations per coupled step (phase 2).")
        form.addRow("Phase 2 max iterations:", self.ns_max_iT2)

        self.ns_converge_iT2 = self.make_double_spin(1e-6, 0, 1, 12)
        self.ns_converge_iT2.setToolTip("Convergence criterion for coupled NS updates.")
        form.addRow("Phase 2 convergence:", self.ns_converge_iT2)

        self.ns_update = self.make_spin(1, 1)
        self.ns_update.setToolTip("Recompute NS flow every N ADE iterations.")
        form.addRow("NS update interval:", self.ns_update)

        # ADE
        self.add_section("Advection-Diffusion (Transport) Solver")
        form2 = self.add_form()

        self.ade_max_iT = self.make_spin(50000, 0)
        self.ade_max_iT.setToolTip("Maximum ADE iterations for transport.")
        form2.addRow("Max ADE iterations:", self.ade_max_iT)

        self.ade_converge = self.make_double_spin(1e-8, 0, 1, 12)
        self.ade_converge.setToolTip("ADE convergence criterion (parsed but currently unused in solver).")
        form2.addRow("ADE convergence:", self.ade_converge)

        self.ade_update = self.make_spin(1, 1)
        self.ade_update.setToolTip("ADE update interval.")
        form2.addRow("ADE update interval:", self.ade_update)

        # Restart
        adv = CollapsibleSection("Restart Settings")
        adv_form = QFormLayout()
        self.ns_rerun_iT0 = self.make_spin(0, 0)
        self.ns_rerun_iT0.setToolTip(
            "Starting iteration for NS restart (when read_NS_file=true).\n"
            "0 = start from beginning.")
        adv_form.addRow("NS restart iteration:", self.ns_rerun_iT0)

        self.ade_rerun_iT0 = self.make_spin(0, 0)
        self.ade_rerun_iT0.setToolTip(
            "Starting iteration for ADE restart (when read_ADE_file=true).\n"
            "0 = start from beginning.")
        adv_form.addRow("ADE restart iteration:", self.ade_rerun_iT0)
        adv.set_content_layout(adv_form)
        self.add_widget(adv)

        self.add_stretch()

        # Real-time validation
        self.ns_max_iT1.valueChanged.connect(self._validate_iterations)
        self.ade_max_iT.valueChanged.connect(self._validate_iterations)

    def _validate_iterations(self):
        """Warn on zero max iterations (would skip solver phase)."""
        if self.ns_max_iT1.value() == 0:
            self.set_validation(self.ns_max_iT1, "warning",
                                "0 iterations = NS phase 1 skipped.")
        else:
            self.clear_validation(self.ns_max_iT1)

        if self.ade_max_iT.value() == 0:
            self.set_validation(self.ade_max_iT, "warning",
                                "0 iterations = ADE transport skipped.")
        else:
            self.clear_validation(self.ade_max_iT)

    def load_from_project(self, project):
        it = project.iteration
        self.ns_max_iT1.setValue(it.ns_max_iT1)
        self.ns_max_iT2.setValue(it.ns_max_iT2)
        self.ns_converge_iT1.setValue(it.ns_converge_iT1)
        self.ns_converge_iT2.setValue(it.ns_converge_iT2)
        self.ns_update.setValue(it.ns_update_interval)
        self.ade_max_iT.setValue(it.ade_max_iT)
        self.ade_converge.setValue(it.ade_converge_iT)
        self.ade_update.setValue(it.ade_update_interval)
        self.ns_rerun_iT0.setValue(it.ns_rerun_iT0)
        self.ade_rerun_iT0.setValue(it.ade_rerun_iT0)

    def save_to_project(self, project):
        it = project.iteration
        it.ns_max_iT1 = self.ns_max_iT1.value()
        it.ns_max_iT2 = self.ns_max_iT2.value()
        it.ns_converge_iT1 = self.ns_converge_iT1.value()
        it.ns_converge_iT2 = self.ns_converge_iT2.value()
        it.ns_update_interval = self.ns_update.value()
        it.ade_max_iT = self.ade_max_iT.value()
        it.ade_converge_iT = self.ade_converge.value()
        it.ade_update_interval = self.ade_update.value()
        it.ns_rerun_iT0 = self.ns_rerun_iT0.value()
        it.ade_rerun_iT0 = self.ade_rerun_iT0.value()
