"""Solver configuration panel - numerics, iteration, and I/O settings."""

from PySide6.QtWidgets import (
    QVBoxLayout, QFormLayout, QLabel, QWidget, QTabWidget, QGroupBox,
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel


class SolverPanel(BasePanel):

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

        layout.addWidget(self._create_heading("Solver Settings"))
        layout.addWidget(self._create_subheading(
            "LBM numerics, iteration control, and output configuration."))

        tabs = QTabWidget()

        # --- Numerics Tab ---
        num_w = QWidget()
        nf = QVBoxLayout(num_w)

        flow_group = self._create_group("Flow Parameters")
        ff = self._create_form()
        self._tau = self._create_double_spin(0.501, 1.999, 0.8, 4, 0.01)
        self._delta_p = self._create_sci_spin(0, 1e10, 2.0e-3)
        self._peclet = self._create_double_spin(0.001, 1000.0, 1.0, 3, 0.1)
        self._track_perf = self._create_checkbox("Track performance metrics")
        ff.addRow("Relaxation time (tau):", self._tau)
        ff.addRow("Pressure drop (delta_P) [Pa]:", self._delta_p)
        ff.addRow("Peclet number:", self._peclet)
        ff.addRow("", self._track_perf)
        flow_group.setLayout(ff)
        nf.addWidget(flow_group)

        stability_info = QLabel(
            "Stability constraints:\n"
            "  tau: Must be in range (0.5, 2.0). Closer to 1.0 is more stable.\n"
            "  Peclet: Pe = u*L/D. Higher values mean advection-dominated transport.\n"
            "  Grid Peclet: Pe_grid < 2.0 for numerical stability.")
        stability_info.setProperty("info", True)
        stability_info.setWordWrap(True)
        nf.addWidget(stability_info)
        nf.addStretch()

        tabs.addTab(num_w, "Numerics")

        # --- Iteration Tab ---
        iter_w = QWidget()
        il = QVBoxLayout(iter_w)

        ns_group = self._create_group("Navier-Stokes Solver")
        nsf = self._create_form()
        self._ns_max1 = self._create_spin(100, 10000000, 100000)
        self._ns_max2 = self._create_spin(100, 10000000, 100000)
        self._ns_conv1 = self._create_sci_spin(0, 1.0, 1e-8)
        self._ns_conv2 = self._create_sci_spin(0, 1.0, 1e-6)
        self._ns_interval = self._create_spin(1, 100000, 1)
        nsf.addRow("Phase 1 max iterations:", self._ns_max1)
        nsf.addRow("Phase 1 convergence:", self._ns_conv1)
        nsf.addRow("Phase 2 max iterations:", self._ns_max2)
        nsf.addRow("Phase 2 convergence:", self._ns_conv2)
        nsf.addRow("Update interval:", self._ns_interval)
        ns_group.setLayout(nsf)
        il.addWidget(ns_group)

        ade_group = self._create_group("Advection-Diffusion Solver")
        af = self._create_form()
        self._ade_max = self._create_spin(100, 10000000, 50000)
        self._ade_conv = self._create_sci_spin(0, 1.0, 1e-8)
        self._ade_interval = self._create_spin(1, 100000, 1)
        af.addRow("Max iterations:", self._ade_max)
        af.addRow("Convergence criterion:", self._ade_conv)
        af.addRow("Update interval:", self._ade_interval)
        ade_group.setLayout(af)
        il.addWidget(ade_group)

        il.addWidget(self._create_info_label(
            "Phase 1: Initial flow field calculation (strict convergence).\n"
            "Phase 2: Flow field updates during reactive transport (relaxed convergence)."))
        il.addStretch()

        tabs.addTab(iter_w, "Iteration Control")

        # --- I/O Tab ---
        io_w = QWidget()
        iol = QVBoxLayout(io_w)

        restart_group = self._create_group("Restart Files")
        rf = self._create_form()
        self._read_ns = self._create_checkbox("Read NS restart file")
        self._read_ade = self._create_checkbox("Read ADE restart file")
        self._ns_file = self._create_line_edit("nsLattice")
        self._mask_file = self._create_line_edit("maskLattice")
        self._subs_file = self._create_line_edit("subsLattice")
        self._bio_file = self._create_line_edit("bioLattice")
        rf.addRow("", self._read_ns)
        rf.addRow("", self._read_ade)
        rf.addRow("NS filename:", self._ns_file)
        rf.addRow("Mask filename:", self._mask_file)
        rf.addRow("Substrate filename:", self._subs_file)
        rf.addRow("Biomass filename:", self._bio_file)
        restart_group.setLayout(rf)
        iol.addWidget(restart_group)

        output_group = self._create_group("Output Intervals")
        of = self._create_form()
        self._vtk_interval = self._create_spin(1, 10000000, 500)
        self._chk_interval = self._create_spin(1, 10000000, 5000)
        of.addRow("Save VTK every N iterations:", self._vtk_interval)
        of.addRow("Save checkpoint every N iterations:", self._chk_interval)
        output_group.setLayout(of)
        iol.addWidget(output_group)
        iol.addStretch()

        tabs.addTab(io_w, "I/O Settings")

        layout.addWidget(tabs, 1)
        outer.addWidget(self._create_scroll_area(w))

    def _populate_fields(self):
        if not self._project:
            return
        p = self._project
        self._tau.setValue(p.fluid.tau)
        self._delta_p.setValue(p.fluid.delta_p)
        self._peclet.setValue(p.fluid.peclet)
        self._track_perf.setChecked(p.track_performance)

        it = p.iteration
        self._ns_max1.setValue(it.ns_max_iT1)
        self._ns_max2.setValue(it.ns_max_iT2)
        self._ns_conv1.setValue(it.ns_converge_iT1)
        self._ns_conv2.setValue(it.ns_converge_iT2)
        self._ns_interval.setValue(it.ns_update_interval)
        self._ade_max.setValue(it.ade_max_iT)
        self._ade_conv.setValue(it.ade_converge_iT)
        self._ade_interval.setValue(it.ade_update_interval)

        io = p.io_settings
        self._read_ns.setChecked(io.read_ns_file)
        self._read_ade.setChecked(io.read_ade_file)
        self._ns_file.setText(io.ns_filename)
        self._mask_file.setText(io.mask_filename)
        self._subs_file.setText(io.subs_filename)
        self._bio_file.setText(io.bio_filename)
        self._vtk_interval.setValue(io.save_vtk_interval)
        self._chk_interval.setValue(io.save_chk_interval)

    def collect_data(self, project):
        project.fluid.tau = self._tau.value()
        project.fluid.delta_p = self._delta_p.value()
        project.fluid.peclet = self._peclet.value()
        project.track_performance = self._track_perf.isChecked()

        it = project.iteration
        it.ns_max_iT1 = self._ns_max1.value()
        it.ns_max_iT2 = self._ns_max2.value()
        it.ns_converge_iT1 = self._ns_conv1.value()
        it.ns_converge_iT2 = self._ns_conv2.value()
        it.ns_update_interval = self._ns_interval.value()
        it.ade_max_iT = self._ade_max.value()
        it.ade_converge_iT = self._ade_conv.value()
        it.ade_update_interval = self._ade_interval.value()

        io = project.io_settings
        io.read_ns_file = self._read_ns.isChecked()
        io.read_ade_file = self._read_ade.isChecked()
        io.ns_filename = self._ns_file.text().strip()
        io.mask_filename = self._mask_file.text().strip()
        io.subs_filename = self._subs_file.text().strip()
        io.bio_filename = self._bio_file.text().strip()
        io.save_vtk_interval = self._vtk_interval.value()
        io.save_chk_interval = self._chk_interval.value()
