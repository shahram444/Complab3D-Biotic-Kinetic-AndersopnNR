"""
Project Overview Panel
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QTextEdit, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel


class ProjectPanel(BasePanel):
    """Panel for project overview and summary"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        
        # Welcome header
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
        
        # Project info grid
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Project details
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
        
        # Quick stats
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
        
        # Quick actions
        actions_group = self._create_group("Quick Actions")
        actions_layout = QHBoxLayout()
        
        run_btn = QPushButton("▶ Run Simulation")
        run_btn.setObjectName("primaryButton")
        run_btn.setMinimumHeight(40)
        actions_layout.addWidget(run_btn)
        
        validate_btn = QPushButton("✓ Validate Setup")
        validate_btn.setMinimumHeight(40)
        actions_layout.addWidget(validate_btn)
        
        export_btn = QPushButton("📄 Export XML")
        export_btn.setMinimumHeight(40)
        actions_layout.addWidget(export_btn)
        
        view3d_btn = QPushButton("🎨 View 3D")
        view3d_btn.setMinimumHeight(40)
        actions_layout.addWidget(view3d_btn)
        
        actions_group.setLayout(actions_layout)
        main_layout.addWidget(actions_group)
        
        # Recent files / getting started
        help_group = self._create_group("Getting Started")
        help_layout = QVBoxLayout()
        
        help_text = QLabel(
            "<b>Welcome to CompLaB Studio!</b><br><br>"
            "CompLaB is a 3D reactive transport simulation framework for pore-scale "
            "biogeochemical modeling using the Lattice Boltzmann Method.<br><br>"
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
        
    def _populate_fields(self):
        if not self.project:
            return
            
        self.name_edit.setText(self.project.name)
        self.description_edit.setText(self.project.description)
        
        if self.project.created:
            try:
                dt = datetime.fromisoformat(self.project.created)
                self.created_label.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except:
                self.created_label.setText(self.project.created)
                
        if self.project.modified:
            try:
                dt = datetime.fromisoformat(self.project.modified)
                self.modified_label.setText(dt.strftime("%Y-%m-%d %H:%M"))
            except:
                self.modified_label.setText(self.project.modified)
                
        # Update summary
        d = self.project.domain
        self.domain_label.setText(f"{d.nx}×{d.ny}×{d.nz} ({d.dx} {d.unit})")
        
        self.substrates_label.setText(
            ", ".join(s.name for s in self.project.substrates) or "None"
        )
        
        self.microbes_label.setText(
            ", ".join(m.name for m in self.project.microbes) or "None"
        )
        
        solver_types = set(m.solver_type.value for m in self.project.microbes)
        self.solver_label.setText(", ".join(solver_types) or "N/A")
        
    def collect_data(self, project):
        if not project:
            return
            
        project.name = self.name_edit.text()
        project.description = self.description_edit.toPlainText()
