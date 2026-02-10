"""
Preferences Dialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTabWidget,
    QSpinBox, QCheckBox, QComboBox, QDialogButtonBox, QWidget
)
from PySide6.QtCore import Qt


class PreferencesDialog(QDialog):
    """Application preferences dialog"""
    
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(550)
        self._setup_ui()
        self._load_settings()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        tabs = QTabWidget()
        
        # === General Tab ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)
        
        # Paths
        paths_group = QGroupBox("Application Paths")
        paths_layout = QFormLayout()
        
        # CompLaB executable
        complab_layout = QHBoxLayout()
        self.complab_edit = QLineEdit()
        self.complab_edit.setPlaceholderText("Path to CompLaB executable")
        complab_browse = QPushButton("Browse...")
        complab_browse.clicked.connect(self._browse_complab)
        complab_layout.addWidget(self.complab_edit)
        complab_layout.addWidget(complab_browse)
        paths_layout.addRow("CompLaB executable:", complab_layout)
        
        # ParaView
        paraview_layout = QHBoxLayout()
        self.paraview_edit = QLineEdit()
        self.paraview_edit.setPlaceholderText("Path to ParaView")
        paraview_browse = QPushButton("Browse...")
        paraview_browse.clicked.connect(self._browse_paraview)
        paraview_layout.addWidget(self.paraview_edit)
        paraview_layout.addWidget(paraview_browse)
        paths_layout.addRow("ParaView:", paraview_layout)
        
        # Default project directory
        project_dir_layout = QHBoxLayout()
        self.project_dir_edit = QLineEdit()
        project_dir_browse = QPushButton("Browse...")
        project_dir_browse.clicked.connect(self._browse_project_dir)
        project_dir_layout.addWidget(self.project_dir_edit)
        project_dir_layout.addWidget(project_dir_browse)
        paths_layout.addRow("Default project directory:", project_dir_layout)
        
        paths_group.setLayout(paths_layout)
        general_layout.addWidget(paths_group)
        
        # Auto-save
        save_group = QGroupBox("Auto-save")
        save_layout = QFormLayout()
        
        self.autosave_check = QCheckBox("Enable auto-save")
        save_layout.addRow("", self.autosave_check)
        
        self.autosave_interval_spin = QSpinBox()
        self.autosave_interval_spin.setRange(30, 3600)
        self.autosave_interval_spin.setSuffix(" seconds")
        save_layout.addRow("Auto-save interval:", self.autosave_interval_spin)
        
        save_group.setLayout(save_layout)
        general_layout.addWidget(save_group)
        
        general_layout.addStretch()
        tabs.addTab(general_tab, "General")
        
        # === Appearance Tab ===
        appearance_tab = QWidget()
        appearance_layout = QVBoxLayout(appearance_tab)
        
        theme_group = QGroupBox("Theme")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light", "System"])
        theme_layout.addRow("Color theme:", self.theme_combo)
        
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 16)
        theme_layout.addRow("Font size:", self.font_size_spin)
        
        theme_group.setLayout(theme_layout)
        appearance_layout.addWidget(theme_group)
        
        appearance_layout.addStretch()
        tabs.addTab(appearance_tab, "Appearance")
        
        # === Simulation Tab ===
        sim_tab = QWidget()
        sim_layout = QVBoxLayout(sim_tab)
        
        console_group = QGroupBox("Console")
        console_layout = QFormLayout()
        
        self.console_lines_spin = QSpinBox()
        self.console_lines_spin.setRange(1000, 100000)
        console_layout.addRow("Max console lines:", self.console_lines_spin)
        
        console_group.setLayout(console_layout)
        sim_layout.addWidget(console_group)
        
        sim_layout.addStretch()
        tabs.addTab(sim_tab, "Simulation")
        
        layout.addWidget(tabs)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addWidget(button_box)
        
    def _load_settings(self):
        """Load settings from config"""
        self.complab_edit.setText(self.config.get("complab_executable", ""))
        self.paraview_edit.setText(self.config.get("paraview_path", "paraview"))
        self.project_dir_edit.setText(self.config.get("default_project_dir", ""))
        
        self.autosave_check.setChecked(self.config.get("auto_save", True))
        self.autosave_interval_spin.setValue(self.config.get("auto_save_interval", 300))
        
        theme = self.config.get("theme", "dark")
        theme_map = {"dark": 0, "light": 1, "system": 2}
        self.theme_combo.setCurrentIndex(theme_map.get(theme, 0))
        
        self.font_size_spin.setValue(self.config.get("font_size", 10))
        self.console_lines_spin.setValue(self.config.get("console_max_lines", 10000))
        
    def _browse_complab(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CompLaB Executable",
            "", "Executables (*.exe);;All Files (*)"
        )
        if path:
            self.complab_edit.setText(path)
            
    def _browse_paraview(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select ParaView",
            "", "Executables (*.exe);;All Files (*)"
        )
        if path:
            self.paraview_edit.setText(path)
            
    def _browse_project_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Default Project Directory"
        )
        if path:
            self.project_dir_edit.setText(path)
            
    def _save_and_accept(self):
        """Save settings and close"""
        self.config.set("complab_executable", self.complab_edit.text())
        self.config.set("paraview_path", self.paraview_edit.text())
        self.config.set("default_project_dir", self.project_dir_edit.text())
        
        self.config.set("auto_save", self.autosave_check.isChecked())
        self.config.set("auto_save_interval", self.autosave_interval_spin.value())
        
        theme_map = {0: "dark", 1: "light", 2: "system"}
        self.config.set("theme", theme_map.get(self.theme_combo.currentIndex(), "dark"))
        
        self.config.set("font_size", self.font_size_spin.value())
        self.config.set("console_max_lines", self.console_lines_spin.value())
        
        self.accept()
        
    def _restore_defaults(self):
        """Restore default settings"""
        self.config.reset()
        self._load_settings()
