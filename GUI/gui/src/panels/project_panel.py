"""
Project Overview Panel

Provides project metadata editing (name, description), simulation mode
configuration (biotic, kinetics, abiotic kinetics, validation diagnostics),
project path settings, and a read-only simulation summary.
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFrame, QGridLayout,
    QCheckBox, QFileDialog
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel
from ..core.project import SimulationMode


class ProjectPanel(BasePanel):
    """Panel for project overview, simulation mode, and path configuration."""

    # ------------------------------------------------------------------ #
    #  UI construction
    # ------------------------------------------------------------------ #
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)

        # ---- Welcome header ----
        header_frame = QFrame()
        header_frame.setObjectName("welcomeHeader")
        header_layout = QVBoxLayout(header_frame)

        title = QLabel("CompLaB Studio")
        title.setObjectName("welcomeTitle")
        title.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title)

        subtitle = QLabel("Reactive Transport Simulation for Porous Media")
        subtitle.setObjectName("welcomeSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(subtitle)

        main_layout.addWidget(header_frame)

        # ---- Two-column grid: details + summary ----
        grid = QGridLayout()
        grid.setSpacing(15)

        # -- Project details --
        details_group = self._create_group("Project Details")
        details_layout = self._create_form_layout()

        self.name_edit = self._create_line_edit("", "Project name")
        details_layout.addRow("Name:", self.name_edit)

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Project description...")
        self.description_edit.setMaximumHeight(80)
        details_layout.addRow("Description:", self.description_edit)

        self.created_label = QLabel("-")
        details_layout.addRow("Created:", self.created_label)

        self.modified_label = QLabel("-")
        details_layout.addRow("Modified:", self.modified_label)

        details_group.setLayout(details_layout)
        grid.addWidget(details_group, 0, 0)

        # -- Simulation summary (read-only) --
        stats_group = self._create_group("Simulation Summary")
        stats_layout = self._create_form_layout()

        self.domain_label = QLabel("-")
        stats_layout.addRow("Domain size:", self.domain_label)

        self.substrates_label = QLabel("-")
        stats_layout.addRow("Substrates:", self.substrates_label)

        self.microbes_label = QLabel("-")
        stats_layout.addRow("Microbes:", self.microbes_label)

        self.solver_label = QLabel("-")
        stats_layout.addRow("Solver:", self.solver_label)

        stats_group.setLayout(stats_layout)
        grid.addWidget(stats_group, 0, 1)

        main_layout.addLayout(grid)

        # ---- Simulation Mode ----
        mode_group = self._create_group("Simulation Mode")
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(8)
        mode_layout.setContentsMargins(15, 15, 15, 15)

        self.biotic_mode_cb = self._create_checkbox("Biotic mode (with microbes)")
        mode_layout.addWidget(self.biotic_mode_cb)

        self.enable_kinetics_cb = self._create_checkbox("Enable biotic kinetics")
        mode_layout.addWidget(self.enable_kinetics_cb)

        self.enable_abiotic_kinetics_cb = self._create_checkbox("Enable abiotic kinetics")
        mode_layout.addWidget(self.enable_abiotic_kinetics_cb)

        self.enable_validation_diagnostics_cb = self._create_checkbox("Validation diagnostics")
        mode_layout.addWidget(self.enable_validation_diagnostics_cb)

        # Wire up inter-dependencies: biotic kinetics only meaningful when
        # biotic mode is active.
        self.biotic_mode_cb.stateChanged.connect(self._on_biotic_mode_changed)

        mode_group.setLayout(mode_layout)
        main_layout.addWidget(mode_group)

        # ---- Paths ----
        paths_group = self._create_group("Project Paths")
        paths_layout = self._create_form_layout()

        self.src_path_edit = self._create_line_edit("", "Source directory (e.g. src)")
        self.src_path_browse = QPushButton("Browse...")
        self.src_path_browse.clicked.connect(lambda: self._browse_path(self.src_path_edit))
        src_row = QHBoxLayout()
        src_row.addWidget(self.src_path_edit)
        src_row.addWidget(self.src_path_browse)
        paths_layout.addRow("Source path:", src_row)

        self.input_path_edit = self._create_line_edit("", "Input directory (e.g. input)")
        self.input_path_browse = QPushButton("Browse...")
        self.input_path_browse.clicked.connect(lambda: self._browse_path(self.input_path_edit))
        input_row = QHBoxLayout()
        input_row.addWidget(self.input_path_edit)
        input_row.addWidget(self.input_path_browse)
        paths_layout.addRow("Input path:", input_row)

        self.output_path_edit = self._create_line_edit("", "Output directory (e.g. output)")
        self.output_path_browse = QPushButton("Browse...")
        self.output_path_browse.clicked.connect(lambda: self._browse_path(self.output_path_edit))
        output_row = QHBoxLayout()
        output_row.addWidget(self.output_path_edit)
        output_row.addWidget(self.output_path_browse)
        paths_layout.addRow("Output path:", output_row)

        paths_group.setLayout(paths_layout)
        main_layout.addWidget(paths_group)

        # ---- Quick actions ----
        actions_group = self._create_group("Quick Actions")
        actions_layout = QHBoxLayout()

        run_btn = QPushButton("Run Simulation")
        run_btn.setObjectName("primaryButton")
        run_btn.setMinimumHeight(40)
        actions_layout.addWidget(run_btn)

        validate_btn = QPushButton("Validate Setup")
        validate_btn.setMinimumHeight(40)
        actions_layout.addWidget(validate_btn)

        export_btn = QPushButton("Export XML")
        export_btn.setMinimumHeight(40)
        actions_layout.addWidget(export_btn)

        view3d_btn = QPushButton("View 3D")
        view3d_btn.setMinimumHeight(40)
        actions_layout.addWidget(view3d_btn)

        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)

        # ---- Information / getting started ----
        help_group = self._create_group("Getting Started")
        help_layout = QVBoxLayout()

        help_text = QLabel(
            "<b>Welcome to CompLaB Studio!</b><br><br>"
            "CompLaB is a 3D reactive transport simulation framework for "
            "pore-scale biogeochemical modeling using the Lattice Boltzmann "
            "Method.<br><br>"
            "<b>Simulation Mode Guide:</b><br>"
            "- <b>Biotic mode</b> enables microbe growth/decay coupled with "
            "substrate transport.<br>"
            "- <b>Biotic kinetics</b> activates Monod-type or custom "
            "growth-rate expressions that depend on biomass.<br>"
            "- <b>Abiotic kinetics</b> enables purely chemical (non-biological) "
            "rate laws such as first-order decay or bimolecular reactions.<br>"
            "- <b>Validation diagnostics</b> writes additional convergence and "
            "mass-balance output for model verification.<br><br>"
            "<b>Quick Start:</b><br>"
            "1. Configure your domain geometry in the <b>Domain</b> tab<br>"
            "2. Import or create geometry in the <b>Geometry</b> tab<br>"
            "3. Define substrates in the <b>Chemistry</b> tab<br>"
            "4. Add microbes and kinetics in the <b>Microbiology</b> tab<br>"
            "5. Set boundary conditions in the <b>Boundaries</b> tab<br>"
            "6. Configure solver settings in the <b>Solver</b> tab<br>"
            "7. Click <b>Run</b> to start your simulation!<br><br>"
            "For more information, visit the documentation or tutorials."
        )
        help_text.setWordWrap(True)
        help_layout.addWidget(help_text)

        help_group.setLayout(help_layout)
        main_layout.addWidget(help_group)

        main_layout.addStretch()

    # ------------------------------------------------------------------ #
    #  Slot helpers
    # ------------------------------------------------------------------ #
    def _on_biotic_mode_changed(self, state):
        """Grey-out biotic kinetics when biotic mode is unchecked."""
        biotic_on = self.biotic_mode_cb.isChecked()
        self.enable_kinetics_cb.setEnabled(biotic_on)
        if not biotic_on:
            self.enable_kinetics_cb.setChecked(False)

    def _browse_path(self, line_edit: QLineEdit):
        """Open a directory picker and put the result into *line_edit*."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory", line_edit.text()
        )
        if directory:
            line_edit.setText(directory)

    # ------------------------------------------------------------------ #
    #  Populate from project
    # ------------------------------------------------------------------ #
    def _populate_fields(self):
        if not self.project:
            return

        # -- Project details --
        self.name_edit.setText(self.project.name)
        self.description_edit.setText(self.project.description)

        if self.project.created:
            try:
                dt = datetime.fromisoformat(self.project.created)
                self.created_label.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                self.created_label.setText(self.project.created)

        if self.project.modified:
            try:
                dt = datetime.fromisoformat(self.project.modified)
                self.modified_label.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except Exception:
                self.modified_label.setText(self.project.modified)

        # -- Simulation mode --
        sm = self.project.simulation_mode
        self.biotic_mode_cb.setChecked(sm.biotic_mode)
        self.enable_kinetics_cb.setChecked(sm.enable_kinetics)
        self.enable_abiotic_kinetics_cb.setChecked(sm.enable_abiotic_kinetics)
        self.enable_validation_diagnostics_cb.setChecked(sm.enable_validation_diagnostics)
        # Ensure dependent state is correct after population
        self._on_biotic_mode_changed(None)

        # -- Paths --
        self.src_path_edit.setText(self.project.src_path)
        self.input_path_edit.setText(self.project.input_path)
        self.output_path_edit.setText(self.project.output_path)

        # -- Simulation summary --
        d = self.project.domain
        self.domain_label.setText(
            f"{d.nx} x {d.ny} x {d.nz} ({d.dx} {d.unit})"
        )

        self.substrates_label.setText(
            ", ".join(s.name for s in self.project.substrates) or "None"
        )

        self.microbes_label.setText(
            ", ".join(m.name for m in self.project.microbes) or "None"
        )

        solver_types = set(m.solver_type.value for m in self.project.microbes)
        self.solver_label.setText(", ".join(solver_types) or "N/A")

    # ------------------------------------------------------------------ #
    #  Collect into project
    # ------------------------------------------------------------------ #
    def collect_data(self, project):
        if not project:
            return

        # -- Project details --
        project.name = self.name_edit.text()
        project.description = self.description_edit.toPlainText()

        # -- Simulation mode --
        project.simulation_mode = SimulationMode(
            biotic_mode=self.biotic_mode_cb.isChecked(),
            enable_kinetics=self.enable_kinetics_cb.isChecked(),
            enable_abiotic_kinetics=self.enable_abiotic_kinetics_cb.isChecked(),
            enable_validation_diagnostics=self.enable_validation_diagnostics_cb.isChecked(),
        )

        # -- Paths (direct attributes on CompLaBProject) --
        project.src_path = self.src_path_edit.text()
        project.input_path = self.input_path_edit.text()
        project.output_path = self.output_path_edit.text()
