"""
Solver Configuration Panel
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel, CollapsibleSection


class SolverPanel(BasePanel):
    """Panel for solver/numerical settings"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header
        header = self._create_header("Solver Settings", "⚙️")
        main_layout.addWidget(header)
        
        desc = self._create_info_label(
            "Configure numerical solver parameters including relaxation time, "
            "convergence criteria, and iteration limits."
        )
        main_layout.addWidget(desc)
        
        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        # Tabs for different solver sections
        tabs = QTabWidget()
        
        # === Flow Solver Tab ===
        flow_tab = QWidget()
        flow_layout = QVBoxLayout(flow_tab)
        
        # LBM Parameters
        lbm_group = self._create_group("Lattice Boltzmann Parameters")
        lbm_layout = self._create_form_layout()
        
        self.tau_spin = self._create_double_spin(0.5, 10, 0.8, 4, 0.01)
        lbm_layout.addRow("Relaxation time (τ):", self.tau_spin)
        
        tau_info = self._create_info_label(
            "τ must be > 0.5 for stability. Typical: 0.8-1.0. "
            "Higher values = higher viscosity."
        )
        lbm_layout.addRow("", tau_info)
        
        self.delta_p_spin = self._create_double_spin(0, 1, 1e-3, 6, 1e-4)
        lbm_layout.addRow("Pressure gradient (ΔP):", self.delta_p_spin)
        
        self.peclet_spin = self._create_double_spin(0.001, 1000, 1.0, 3, 0.1)
        lbm_layout.addRow("Péclet number:", self.peclet_spin)
        
        lbm_group.setLayout(lbm_layout)
        flow_layout.addWidget(lbm_group)
        
        # NS Iteration settings
        ns_group = self._create_group("Navier-Stokes Solver Iterations")
        ns_layout = self._create_form_layout()
        
        self.ns_rerun_spin = self._create_spin_box(0, 1000000, 0)
        ns_layout.addRow("Rerun from iteration:", self.ns_rerun_spin)
        
        self.ns_max_iT1_spin = self._create_spin_box(100, 10000000, 10000)
        ns_layout.addRow("Max iterations (phase 1):", self.ns_max_iT1_spin)
        
        self.ns_conv_iT1_spin = self._create_double_spin(1e-12, 1, 1e-6, 12, 1e-7)
        ns_layout.addRow("Convergence (phase 1):", self.ns_conv_iT1_spin)
        
        self.ns_max_iT2_spin = self._create_spin_box(100, 10000000, 5000)
        ns_layout.addRow("Max iterations (phase 2):", self.ns_max_iT2_spin)
        
        self.ns_conv_iT2_spin = self._create_double_spin(1e-12, 1, 1e-5, 12, 1e-6)
        ns_layout.addRow("Convergence (phase 2):", self.ns_conv_iT2_spin)
        
        self.ns_update_spin = self._create_spin_box(1, 10000, 10)
        ns_layout.addRow("Update interval:", self.ns_update_spin)
        
        ns_group.setLayout(ns_layout)
        flow_layout.addWidget(ns_group)
        
        flow_layout.addStretch()
        tabs.addTab(flow_tab, "Flow Solver")
        
        # === Transport Solver Tab ===
        transport_tab = QWidget()
        transport_layout = QVBoxLayout(transport_tab)
        
        ade_group = self._create_group("Advection-Diffusion Solver Iterations")
        ade_layout = self._create_form_layout()
        
        self.ade_rerun_spin = self._create_spin_box(0, 1000000, 0)
        ade_layout.addRow("Rerun from iteration:", self.ade_rerun_spin)
        
        self.ade_max_spin = self._create_spin_box(1000, 100000000, 100000)
        ade_layout.addRow("Max iterations:", self.ade_max_spin)
        
        self.ade_conv_spin = self._create_double_spin(1e-15, 1, 1e-7, 15, 1e-8)
        ade_layout.addRow("Convergence criterion:", self.ade_conv_spin)
        
        self.ade_update_spin = self._create_spin_box(1, 10000, 1)
        ade_layout.addRow("Update interval:", self.ade_update_spin)
        
        ade_group.setLayout(ade_layout)
        transport_layout.addWidget(ade_group)
        
        transport_layout.addStretch()
        tabs.addTab(transport_tab, "Transport Solver")
        
        # === I/O Settings Tab ===
        io_tab = QWidget()
        io_layout = QVBoxLayout(io_tab)
        
        restart_group = self._create_group("Restart Settings")
        restart_layout = self._create_form_layout()
        
        self.read_ns_check = self._create_checkbox("Read NS lattice from file", False)
        restart_layout.addRow("", self.read_ns_check)
        
        self.read_ade_check = self._create_checkbox("Read ADE lattice from file", False)
        restart_layout.addRow("", self.read_ade_check)
        
        self.ns_filename_edit = self._create_line_edit("nsLattice", "NS lattice filename")
        restart_layout.addRow("NS filename:", self.ns_filename_edit)
        
        self.mask_filename_edit = self._create_line_edit("maskLattice", "Mask filename")
        restart_layout.addRow("Mask filename:", self.mask_filename_edit)
        
        self.subs_filename_edit = self._create_line_edit("subsLattice", "Substrates filename")
        restart_layout.addRow("Substrates filename:", self.subs_filename_edit)
        
        self.bio_filename_edit = self._create_line_edit("bioLattice", "Biomass filename")
        restart_layout.addRow("Biomass filename:", self.bio_filename_edit)
        
        restart_group.setLayout(restart_layout)
        io_layout.addWidget(restart_group)
        
        output_group = self._create_group("Output Settings")
        output_layout = self._create_form_layout()
        
        self.vtk_interval_spin = self._create_spin_box(1, 1000000, 100)
        output_layout.addRow("VTK save interval:", self.vtk_interval_spin)
        
        self.chk_interval_spin = self._create_spin_box(1, 1000000, 1000)
        output_layout.addRow("Checkpoint save interval:", self.chk_interval_spin)
        
        self.track_perf_check = self._create_checkbox("Track performance metrics", False)
        output_layout.addRow("", self.track_perf_check)
        
        output_group.setLayout(output_layout)
        io_layout.addWidget(output_group)
        
        io_layout.addStretch()
        tabs.addTab(io_tab, "I/O Settings")

        # === MPI / Parallel Execution Tab ===
        mpi_tab = QWidget()
        mpi_layout = QVBoxLayout(mpi_tab)

        mpi_group = self._create_group("MPI Parallel Execution")
        mpi_inner = self._create_form_layout()

        self.mpi_enabled_check = self._create_checkbox("Enable MPI parallel run", False)
        mpi_inner.addRow("", self.mpi_enabled_check)

        self.mpi_nprocs_spin = self._create_spin_box(1, 1024, 4)
        mpi_inner.addRow("Number of processes:", self.mpi_nprocs_spin)

        self.mpi_command_edit = self._create_line_edit("mpirun", "MPI launch command")
        mpi_inner.addRow("MPI command:", self.mpi_command_edit)

        mpi_info = self._create_info_label(
            "Uses mpirun/mpiexec to launch CompLaB in parallel. "
            "Number of processes should match your CPU core count. "
            "Leave MPI command empty for auto-detection."
        )
        mpi_inner.addRow("", mpi_info)

        mpi_group.setLayout(mpi_inner)
        mpi_layout.addWidget(mpi_group)

        mpi_layout.addStretch()
        tabs.addTab(mpi_tab, "Parallel (MPI)")

        content_layout.addWidget(tabs)
        
        scroll.setWidget(content)
        main_layout.addWidget(scroll)
        
    def _populate_fields(self):
        if not self.project:
            return
            
        # Fluid/LBM settings
        self.tau_spin.setValue(self.project.fluid.tau)
        self.delta_p_spin.setValue(self.project.fluid.delta_p)
        self.peclet_spin.setValue(self.project.fluid.peclet)
        
        # NS iterations
        self.ns_rerun_spin.setValue(self.project.iterations.ns_rerun_iT0)
        self.ns_max_iT1_spin.setValue(self.project.iterations.ns_max_iT1)
        self.ns_conv_iT1_spin.setValue(self.project.iterations.ns_converge_iT1)
        self.ns_max_iT2_spin.setValue(self.project.iterations.ns_max_iT2)
        self.ns_conv_iT2_spin.setValue(self.project.iterations.ns_converge_iT2)
        self.ns_update_spin.setValue(self.project.iterations.ns_update_interval)
        
        # ADE iterations
        self.ade_rerun_spin.setValue(self.project.iterations.ade_rerun_iT0)
        self.ade_max_spin.setValue(self.project.iterations.ade_max_iT)
        self.ade_conv_spin.setValue(self.project.iterations.ade_converge_iT)
        self.ade_update_spin.setValue(self.project.iterations.ade_update_interval)
        
        # I/O settings
        self.read_ns_check.setChecked(self.project.io.read_ns_file)
        self.read_ade_check.setChecked(self.project.io.read_ade_file)
        self.ns_filename_edit.setText(self.project.io.ns_filename)
        self.mask_filename_edit.setText(self.project.io.mask_filename)
        self.subs_filename_edit.setText(self.project.io.subs_filename)
        self.bio_filename_edit.setText(self.project.io.bio_filename)
        self.vtk_interval_spin.setValue(self.project.io.save_vtk_interval)
        self.chk_interval_spin.setValue(self.project.io.save_chk_interval)
        self.track_perf_check.setChecked(self.project.io.track_performance)
        
    def collect_data(self, project):
        if not project:
            return
            
        # Fluid/LBM settings
        project.fluid.tau = self.tau_spin.value()
        project.fluid.delta_p = self.delta_p_spin.value()
        project.fluid.peclet = self.peclet_spin.value()
        
        # NS iterations
        project.iterations.ns_rerun_iT0 = self.ns_rerun_spin.value()
        project.iterations.ns_max_iT1 = self.ns_max_iT1_spin.value()
        project.iterations.ns_converge_iT1 = self.ns_conv_iT1_spin.value()
        project.iterations.ns_max_iT2 = self.ns_max_iT2_spin.value()
        project.iterations.ns_converge_iT2 = self.ns_conv_iT2_spin.value()
        project.iterations.ns_update_interval = self.ns_update_spin.value()
        
        # ADE iterations
        project.iterations.ade_rerun_iT0 = self.ade_rerun_spin.value()
        project.iterations.ade_max_iT = self.ade_max_spin.value()
        project.iterations.ade_converge_iT = self.ade_conv_spin.value()
        project.iterations.ade_update_interval = self.ade_update_spin.value()
        
        # I/O settings
        project.io.read_ns_file = self.read_ns_check.isChecked()
        project.io.read_ade_file = self.read_ade_check.isChecked()
        project.io.ns_filename = self.ns_filename_edit.text()
        project.io.mask_filename = self.mask_filename_edit.text()
        project.io.subs_filename = self.subs_filename_edit.text()
        project.io.bio_filename = self.bio_filename_edit.text()
        project.io.save_vtk_interval = self.vtk_interval_spin.value()
        project.io.save_chk_interval = self.chk_interval_spin.value()
        project.io.track_performance = self.track_perf_check.isChecked()
