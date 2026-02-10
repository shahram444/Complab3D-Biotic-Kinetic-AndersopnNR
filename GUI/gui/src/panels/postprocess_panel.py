"""
Post-Processing / Results Panel
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QTabWidget, QSplitter,
    QFrame, QFileDialog, QTableWidget, QTableWidgetItem, QHeaderView,
    QProgressBar
)
from PySide6.QtCore import Qt, Signal

from .base_panel import BasePanel


class PostProcessPanel(BasePanel):
    """Panel for viewing and analyzing simulation results"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        header = self._create_header("Results & Post-Processing")
        main_layout.addWidget(header)
        
        # Main splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - file browser
        left_panel = QFrame()
        left_panel.setMaximumWidth(300)
        left_layout = QVBoxLayout(left_panel)
        
        files_group = QGroupBox("Output Files")
        files_layout = QVBoxLayout()
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_files)
        files_layout.addWidget(refresh_btn)
        
        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self._on_file_selected)
        self.file_list.itemDoubleClicked.connect(self._on_file_double_clicked)
        files_layout.addWidget(self.file_list)
        
        files_group.setLayout(files_layout)
        left_layout.addWidget(files_group)
        
        # Export options
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        
        export_vtk_btn = QPushButton("Export to ParaView...")
        export_vtk_btn.clicked.connect(self._export_paraview)
        export_layout.addWidget(export_vtk_btn)
        
        export_csv_btn = QPushButton("Export Data to CSV...")
        export_csv_btn.clicked.connect(self._export_csv)
        export_layout.addWidget(export_csv_btn)
        
        export_img_btn = QPushButton("Export Images...")
        export_img_btn.clicked.connect(self._export_images)
        export_layout.addWidget(export_img_btn)
        
        export_group.setLayout(export_layout)
        left_layout.addWidget(export_group)
        
        splitter.addWidget(left_panel)
        
        # Right panel - visualization/data
        right_panel = QFrame()
        right_layout = QVBoxLayout(right_panel)
        
        tabs = QTabWidget()
        
        # Summary tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout(summary_tab)
        
        stats_group = QGroupBox("Simulation Statistics")
        stats_layout = QFormLayout()
        
        self.total_time_label = QLabel("--")
        stats_layout.addRow("Total iterations:", self.total_time_label)
        
        self.vtk_count_label = QLabel("--")
        stats_layout.addRow("VTK files:", self.vtk_count_label)
        
        self.last_modified_label = QLabel("--")
        stats_layout.addRow("Last modified:", self.last_modified_label)
        
        stats_group.setLayout(stats_layout)
        summary_layout.addWidget(stats_group)
        
        # Mass balance
        mass_group = QGroupBox("Mass Balance")
        mass_layout = QVBoxLayout()
        
        self.mass_table = QTableWidget()
        self.mass_table.setColumnCount(4)
        self.mass_table.setHorizontalHeaderLabels(["Species", "Initial", "Final", "Change"])
        self.mass_table.horizontalHeader().setStretchLastSection(True)
        mass_layout.addWidget(self.mass_table)
        
        mass_group.setLayout(mass_layout)
        summary_layout.addWidget(mass_group)
        
        summary_layout.addStretch()
        tabs.addTab(summary_tab, "Summary")
        
        # Time series tab
        timeseries_tab = QWidget()
        ts_layout = QVBoxLayout(timeseries_tab)
        
        ts_controls = QHBoxLayout()
        
        self.ts_variable_combo = QComboBox()
        self.ts_variable_combo.addItems([
            "Average Concentration",
            "Total Biomass",
            "Porosity",
            "Flow Rate"
        ])
        ts_controls.addWidget(QLabel("Variable:"))
        ts_controls.addWidget(self.ts_variable_combo)
        
        ts_controls.addStretch()
        
        plot_btn = QPushButton("Generate Plot")
        plot_btn.clicked.connect(self._generate_timeseries)
        ts_controls.addWidget(plot_btn)
        
        ts_layout.addLayout(ts_controls)
        
        # Placeholder for plot
        self.ts_plot_label = QLabel("Select a variable and click 'Generate Plot'")
        self.ts_plot_label.setAlignment(Qt.AlignCenter)
        self.ts_plot_label.setMinimumHeight(300)
        self.ts_plot_label.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
        ts_layout.addWidget(self.ts_plot_label)
        
        tabs.addTab(timeseries_tab, "Time Series")
        
        # Profiles tab
        profiles_tab = QWidget()
        prof_layout = QVBoxLayout(profiles_tab)
        
        prof_controls = QHBoxLayout()
        
        self.prof_direction_combo = QComboBox()
        self.prof_direction_combo.addItems(["X (flow)", "Y", "Z"])
        prof_controls.addWidget(QLabel("Direction:"))
        prof_controls.addWidget(self.prof_direction_combo)
        
        self.prof_timestep_spin = QSpinBox()
        self.prof_timestep_spin.setRange(0, 100000)
        prof_controls.addWidget(QLabel("Timestep:"))
        prof_controls.addWidget(self.prof_timestep_spin)
        
        prof_controls.addStretch()
        
        prof_btn = QPushButton("Generate Profile")
        prof_btn.clicked.connect(self._generate_profile)
        prof_controls.addWidget(prof_btn)
        
        prof_layout.addLayout(prof_controls)
        
        self.prof_plot_label = QLabel("Select options and click 'Generate Profile'")
        self.prof_plot_label.setAlignment(Qt.AlignCenter)
        self.prof_plot_label.setMinimumHeight(300)
        self.prof_plot_label.setStyleSheet("background-color: #2a2a2a; border: 1px solid #444;")
        prof_layout.addWidget(self.prof_plot_label)
        
        tabs.addTab(profiles_tab, "Profiles")
        
        # Data table tab
        data_tab = QWidget()
        data_layout = QVBoxLayout(data_tab)
        
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(5)
        self.data_table.setHorizontalHeaderLabels([
            "Iteration", "Time [s]", "Avg Conc", "Total Bio", "Porosity"
        ])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        data_layout.addWidget(self.data_table)
        
        tabs.addTab(data_tab, "Data Table")
        
        right_layout.addWidget(tabs)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 600])
        
        main_layout.addWidget(splitter)
        
    def _populate_fields(self):
        """Populate with project data"""
        if not self.project:
            return
        self._refresh_files()
        
    def collect_data(self, project):
        """Nothing to collect - read-only panel"""
        pass
        
    def _refresh_files(self):
        """Refresh the file list"""
        self.file_list.clear()
        
        if not self.project or not self.project.path:
            return
            
        output_dir = self.project.get_output_dir()
        if not os.path.exists(output_dir):
            self.file_list.addItem("(No output files)")
            return
            
        vtk_count = 0
        for f in sorted(os.listdir(output_dir)):
            filepath = os.path.join(output_dir, f)
            
            # Determine icon based on file type
            if f.endswith('.vti') or f.endswith('.vtk'):
                icon = "🎨"
                vtk_count += 1
            elif f.endswith('.dat'):
                icon = "📊"
            elif f.endswith('.chk'):
                icon = "💾"
            else:
                icon = "📄"
                
            item = QListWidgetItem(f"{icon} {f}")
            item.setData(Qt.UserRole, filepath)
            self.file_list.addItem(item)
            
        self.vtk_count_label.setText(str(vtk_count))
        
        # Get last modified time
        if os.path.exists(output_dir):
            import time
            mtime = os.path.getmtime(output_dir)
            self.last_modified_label.setText(
                time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(mtime))
            )
            
    def _on_file_selected(self, item):
        """Handle file selection"""
        filepath = item.data(Qt.UserRole)
        if filepath:
            # Update info display
            pass
            
    def _on_file_double_clicked(self, item):
        """Handle file double-click - open in appropriate viewer"""
        filepath = item.data(Qt.UserRole)
        if filepath and os.path.exists(filepath):
            import subprocess
            import sys
            
            if sys.platform == 'win32':
                os.startfile(filepath)
            elif sys.platform == 'darwin':
                subprocess.run(['open', filepath])
            else:
                subprocess.run(['xdg-open', filepath])
                
    def _export_paraview(self):
        """Export to ParaView"""
        if not self.project:
            return
            
        output_dir = self.project.get_output_dir()
        # Could open ParaView with the output directory
        
    def _export_csv(self):
        """Export data to CSV"""
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV",
            "", "CSV Files (*.csv)"
        )
        if path:
            # Export logic here
            pass
            
    def _export_images(self):
        """Export visualization images"""
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Folder"
        )
        if path:
            # Export logic here
            pass
            
    def _generate_timeseries(self):
        """Generate time series plot"""
        variable = self.ts_variable_combo.currentText()
        self.ts_plot_label.setText(
            f"Time series plot for '{variable}'\n\n"
            "(Plotting requires matplotlib - would be displayed here)"
        )
        
    def _generate_profile(self):
        """Generate spatial profile"""
        direction = self.prof_direction_combo.currentText()
        timestep = self.prof_timestep_spin.value()
        self.prof_plot_label.setText(
            f"Profile in {direction} direction at t={timestep}\n\n"
            "(Plotting requires matplotlib - would be displayed here)"
        )
