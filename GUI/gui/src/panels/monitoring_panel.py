"""
Monitoring and Post-Processing Panels
"""

import html
import re
import time

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QPushButton, QProgressBar, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame, QTextEdit,
    QComboBox, QFileDialog, QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QTextCursor

from .base_panel import BasePanel


class MonitoringPanel(QWidget):
    """Real-time simulation monitoring panel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_time = None
        self._last_iteration = 0
        self._max_iterations = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Status section
        status_group = QGroupBox("Simulation Status")
        status_layout = QFormLayout()

        self.status_label = QLabel("Idle")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addRow("Status:", self.status_label)

        self.iteration_label = QLabel("0")
        status_layout.addRow("Iteration:", self.iteration_label)

        self.time_label = QLabel("0:00:00")
        status_layout.addRow("Elapsed:", self.time_label)

        self.eta_label = QLabel("-")
        status_layout.addRow("ETA:", self.eta_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v / %m)")
        layout.addWidget(self.progress_bar)

        # Convergence section
        conv_group = QGroupBox("Convergence")
        conv_layout = QFormLayout()

        self.ns_conv_label = QLabel("-")
        conv_layout.addRow("NS residual:", self.ns_conv_label)

        self.ade_conv_label = QLabel("-")
        conv_layout.addRow("ADE residual:", self.ade_conv_label)

        conv_group.setLayout(conv_layout)
        layout.addWidget(conv_group)

        # Real-time output display
        output_group = QGroupBox("Solver Output")
        output_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 9))
        self.output_text.setLineWrapMode(QTextEdit.NoWrap)
        self.output_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
            }
        """)
        output_layout.addWidget(self.output_text)

        output_group.setLayout(output_layout)
        layout.addWidget(output_group, stretch=1)

        # Output files
        files_group = QGroupBox("Output Files")
        files_layout = QVBoxLayout()

        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(120)
        files_layout.addWidget(self.files_list)

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self._refresh_files)
        files_layout.addWidget(refresh_btn)

        files_group.setLayout(files_layout)
        layout.addWidget(files_group)

    def update_progress(self, iteration, message):
        """Update progress display"""
        self.iteration_label.setText(str(iteration))
        self.status_label.setText(message)

        if iteration > 0:
            self.progress_bar.setValue(iteration)

    def set_running(self, running: bool):
        """Set running state"""
        if running:
            self._start_time = time.time()
            self._last_iteration = 0
            self.status_label.setText("Running...")
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.output_text.clear()
        else:
            self._start_time = None
            self.status_label.setText("Idle")
            self.status_label.setStyleSheet("font-weight: bold;")

    def append_output(self, line: str):
        """Append a line of real-time solver output and parse for progress info"""
        safe_line = html.escape(line)
        line_lower = line.lower()

        # Color-code output
        if "error" in line_lower:
            color = "#F44336"
        elif "warning" in line_lower:
            color = "#FFC107"
        elif "converge" in line_lower or "complete" in line_lower:
            color = "#4CAF50"
        else:
            color = "#D4D4D4"

        self.output_text.append(
            f'<span style="color: {color};">{safe_line}</span>'
        )
        # Auto-scroll to bottom
        self.output_text.verticalScrollBar().setValue(
            self.output_text.verticalScrollBar().maximum()
        )

        # Parse iteration info from solver output
        # CompLaB prints lines like: "Iteration 500 / 10000" or "iter= 500"
        iter_match = re.search(
            r'(?:iteration|iter|step)\s*[=:]?\s*(\d+)\s*(?:/\s*(\d+))?',
            line, re.IGNORECASE
        )
        if iter_match:
            current = int(iter_match.group(1))
            self._last_iteration = current
            self.iteration_label.setText(str(current))
            if iter_match.group(2):
                self._max_iterations = int(iter_match.group(2))
                self.progress_bar.setMaximum(self._max_iterations)
            if self._max_iterations > 0:
                self.progress_bar.setValue(current)
            # Update elapsed / ETA
            if self._start_time and current > 0:
                elapsed = time.time() - self._start_time
                h, rem = divmod(int(elapsed), 3600)
                m, s = divmod(rem, 60)
                self.time_label.setText(f"{h}:{m:02d}:{s:02d}")
                if self._max_iterations > 0 and current < self._max_iterations:
                    eta_seconds = elapsed * (self._max_iterations - current) / current
                    eh, erem = divmod(int(eta_seconds), 3600)
                    em, es = divmod(erem, 60)
                    self.eta_label.setText(f"{eh}:{em:02d}:{es:02d}")

        # Parse convergence residuals
        ns_match = re.search(r'NS\s*residual\s*[=:]\s*([0-9.eE+-]+)', line, re.IGNORECASE)
        if ns_match:
            self.ns_conv_label.setText(ns_match.group(1))
        ade_match = re.search(r'ADE\s*residual\s*[=:]\s*([0-9.eE+-]+)', line, re.IGNORECASE)
        if ade_match:
            self.ade_conv_label.setText(ade_match.group(1))

    def on_simulation_finished(self, exit_code: int):
        """Handle simulation completion"""
        if exit_code == 0:
            self.status_label.setText("Completed")
            self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
            self.progress_bar.setValue(self.progress_bar.maximum())
        elif exit_code == -1:
            self.status_label.setText("Cancelled")
            self.status_label.setStyleSheet("font-weight: bold; color: #FFC107;")
        else:
            self.status_label.setText(f"Failed (exit code {exit_code})")
            self.status_label.setStyleSheet("font-weight: bold; color: #F44336;")

        self.eta_label.setText("-")
        # Update final elapsed time
        if self._start_time:
            elapsed = time.time() - self._start_time
            h, rem = divmod(int(elapsed), 3600)
            m, s = divmod(rem, 60)
            self.time_label.setText(f"{h}:{m:02d}:{s:02d}")
            self._start_time = None
        # Refresh output files
        self._refresh_files()

    def _refresh_files(self):
        """Refresh output files list"""
        self.files_list.clear()
        # Would scan output directory for VTK/checkpoint files


class PostProcessPanel(BasePanel):
    """Post-processing and results panel"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header = self._create_header("Results & Post-Processing", "📈")
        main_layout.addWidget(header)
        
        tabs = QTabWidget()
        
        # === Output Files Tab ===
        files_tab = QWidget()
        files_layout = QVBoxLayout(files_tab)
        
        files_group = self._create_group("Output Files")
        files_inner = QVBoxLayout()
        
        self.output_table = QTableWidget()
        self.output_table.setColumnCount(4)
        self.output_table.setHorizontalHeaderLabels(["File", "Type", "Iteration", "Size"])
        self.output_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.output_table.setAlternatingRowColors(True)
        files_inner.addWidget(self.output_table)
        
        btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._scan_output_files)
        btn_layout.addWidget(refresh_btn)
        
        open_folder_btn = QPushButton("📂 Open Folder")
        open_folder_btn.clicked.connect(self._open_output_folder)
        btn_layout.addWidget(open_folder_btn)
        
        paraview_btn = QPushButton("🎨 Open in ParaView")
        paraview_btn.clicked.connect(self._open_in_paraview)
        btn_layout.addWidget(paraview_btn)
        
        files_inner.addLayout(btn_layout)
        files_group.setLayout(files_inner)
        files_layout.addWidget(files_group)
        
        tabs.addTab(files_tab, "Files")
        
        # === Visualization Tab ===
        viz_tab = QWidget()
        viz_layout = QVBoxLayout(viz_tab)
        
        viz_group = self._create_group("Quick Visualization")
        viz_inner = QFormLayout()
        
        self.viz_file_combo = QComboBox()
        viz_inner.addRow("File:", self.viz_file_combo)
        
        self.viz_var_combo = QComboBox()
        self.viz_var_combo.addItems(["Velocity", "Pressure", "Substrate", "Biomass"])
        viz_inner.addRow("Variable:", self.viz_var_combo)
        
        view_btn = QPushButton("🎨 View in 3D Tab")
        view_btn.clicked.connect(self._view_in_3d)
        viz_inner.addRow("", view_btn)
        
        viz_group.setLayout(viz_inner)
        viz_layout.addWidget(viz_group)
        
        viz_layout.addStretch()
        tabs.addTab(viz_tab, "Visualization")
        
        # === Export Tab ===
        export_tab = QWidget()
        export_layout = QVBoxLayout(export_tab)
        
        export_group = self._create_group("Export Results")
        export_inner = QFormLayout()
        
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["VTK (.vti)", "CSV", "NumPy (.npy)", "MATLAB (.mat)"])
        export_inner.addRow("Format:", self.export_format_combo)
        
        export_btn = QPushButton("📤 Export")
        export_btn.clicked.connect(self._export_results)
        export_inner.addRow("", export_btn)
        
        export_group.setLayout(export_inner)
        export_layout.addWidget(export_group)
        
        export_layout.addStretch()
        tabs.addTab(export_tab, "Export")
        
        # === Statistics Tab ===
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)
        
        stats_group = self._create_group("Simulation Statistics")
        stats_inner = QFormLayout()
        
        self.total_time_label = QLabel("-")
        stats_inner.addRow("Total time:", self.total_time_label)
        
        self.iterations_label = QLabel("-")
        stats_inner.addRow("Iterations:", self.iterations_label)
        
        self.final_porosity_label = QLabel("-")
        stats_inner.addRow("Final porosity:", self.final_porosity_label)
        
        self.avg_velocity_label = QLabel("-")
        stats_inner.addRow("Avg velocity:", self.avg_velocity_label)
        
        self.mass_balance_label = QLabel("-")
        stats_inner.addRow("Mass balance:", self.mass_balance_label)
        
        calc_btn = QPushButton("📊 Calculate Statistics")
        calc_btn.clicked.connect(self._calculate_statistics)
        stats_inner.addRow("", calc_btn)
        
        stats_group.setLayout(stats_inner)
        stats_layout.addWidget(stats_group)
        
        stats_layout.addStretch()
        tabs.addTab(stats_tab, "Statistics")
        
        main_layout.addWidget(tabs)
        
    def _scan_output_files(self):
        """Scan output directory for result files"""
        import os
        
        if not self.project:
            return
            
        output_dir = self.project.get_output_dir()
        if not os.path.exists(output_dir):
            return
            
        self.output_table.setRowCount(0)
        self.viz_file_combo.clear()
        
        for filename in sorted(os.listdir(output_dir)):
            filepath = os.path.join(output_dir, filename)
            if os.path.isfile(filepath):
                ext = os.path.splitext(filename)[1]
                
                # Determine type
                if ext in ['.vti', '.vtk']:
                    ftype = "VTK"
                elif ext == '.chk':
                    ftype = "Checkpoint"
                else:
                    ftype = ext.upper()
                    
                # Extract iteration number
                import re
                match = re.search(r'(\d+)', filename)
                iteration = match.group(1) if match else "-"
                
                # File size
                size = os.path.getsize(filepath)
                if size > 1024*1024:
                    size_str = f"{size/(1024*1024):.1f} MB"
                elif size > 1024:
                    size_str = f"{size/1024:.1f} KB"
                else:
                    size_str = f"{size} B"
                    
                row = self.output_table.rowCount()
                self.output_table.insertRow(row)
                self.output_table.setItem(row, 0, QTableWidgetItem(filename))
                self.output_table.setItem(row, 1, QTableWidgetItem(ftype))
                self.output_table.setItem(row, 2, QTableWidgetItem(iteration))
                self.output_table.setItem(row, 3, QTableWidgetItem(size_str))
                
                if ext in ['.vti', '.vtk']:
                    self.viz_file_combo.addItem(filename)
                    
    def _open_output_folder(self):
        """Open output folder in file manager"""
        import os
        import subprocess
        import sys
        
        if not self.project:
            return
            
        output_dir = self.project.get_output_dir()
        
        if sys.platform == 'win32':
            os.startfile(output_dir)
        elif sys.platform == 'darwin':
            subprocess.run(['open', output_dir])
        else:
            subprocess.run(['xdg-open', output_dir])
            
    def _open_in_paraview(self):
        """Open results in ParaView"""
        # Would launch ParaView with output files
        pass
        
    def _view_in_3d(self):
        """View selected file in 3D viewer"""
        # Would load VTK file into 3D viewer tab
        pass
        
    def _export_results(self):
        """Export results to selected format"""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Results",
            "",
            "All Files (*)"
        )
        if file_path:
            # Would export based on selected format
            pass
            
    def _calculate_statistics(self):
        """Calculate simulation statistics"""
        # Would analyze output files and compute statistics
        pass
        
    def _populate_fields(self):
        if self.project:
            self._scan_output_files()
            
    def collect_data(self, project):
        pass
