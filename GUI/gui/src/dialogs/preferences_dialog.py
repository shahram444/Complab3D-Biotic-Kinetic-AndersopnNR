"""
Preferences Dialog

Provides a tabbed dialog for editing application preferences.
All settings are read from and written to the Config object.
An Apply button allows changes to take effect immediately without closing.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTabWidget,
    QSpinBox, QCheckBox, QComboBox, QDialogButtonBox, QWidget
)
from PySide6.QtCore import Qt, Signal


# Mapping between theme combo-box indices and config string values
_THEME_TO_INDEX = {"dark": 0, "light": 1, "system": 2}
_INDEX_TO_THEME = {v: k for k, v in _THEME_TO_INDEX.items()}


class PreferencesDialog(QDialog):
    """Application preferences dialog.

    Signals
    -------
    preferences_applied(dict)
        Emitted when the user clicks *Apply* or *OK*.  The payload is a
        dictionary of **all** preference values that were written to Config
        so that the caller can react (e.g. switch the theme or resize fonts).
    """

    preferences_applied = Signal(dict)

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("Preferences")
        self.setMinimumWidth(550)
        self._setup_ui()
        self._load_settings()

    # --------------------------------------------------------------------- #
    #  UI construction
    # --------------------------------------------------------------------- #
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        tabs = QTabWidget()

        # === General Tab ===
        general_tab = QWidget()
        general_layout = QVBoxLayout(general_tab)

        # -- Paths --
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

        # -- Auto-save --
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
        self.font_size_spin.setSuffix(" pt")
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
        self.console_lines_spin.setSingleStep(1000)
        console_layout.addRow("Max console lines:", self.console_lines_spin)

        console_group.setLayout(console_layout)
        sim_layout.addWidget(console_group)

        sim_layout.addStretch()
        tabs.addTab(sim_tab, "Simulation")

        layout.addWidget(tabs)

        # -- Button box (OK / Cancel / Apply / Restore Defaults) --
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
            | QDialogButtonBox.Apply
            | QDialogButtonBox.RestoreDefaults
        )
        button_box.accepted.connect(self._save_and_accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(
            self._apply_settings
        )
        button_box.button(QDialogButtonBox.RestoreDefaults).clicked.connect(
            self._restore_defaults
        )
        layout.addWidget(button_box)

    # --------------------------------------------------------------------- #
    #  Loading / saving
    # --------------------------------------------------------------------- #
    def _load_settings(self):
        """Populate every widget from the current Config values."""
        # Paths
        self.complab_edit.setText(self.config.get("complab_executable", ""))
        self.paraview_edit.setText(self.config.get("paraview_path", "paraview"))
        self.project_dir_edit.setText(self.config.get("default_project_dir", ""))

        # Auto-save
        self.autosave_check.setChecked(self.config.get("auto_save", True))
        self.autosave_interval_spin.setValue(
            self.config.get("auto_save_interval", 300)
        )

        # Theme / appearance
        theme = self.config.get("theme", "dark")
        self.theme_combo.setCurrentIndex(_THEME_TO_INDEX.get(theme, 0))
        self.font_size_spin.setValue(self.config.get("font_size", 10))

        # Console
        self.console_lines_spin.setValue(
            self.config.get("console_max_lines", 10000)
        )

    def _gather_values(self):
        """Read every widget and return a dict of preference key/value pairs."""
        return {
            "complab_executable": self.complab_edit.text(),
            "paraview_path": self.paraview_edit.text(),
            "default_project_dir": self.project_dir_edit.text(),
            "auto_save": self.autosave_check.isChecked(),
            "auto_save_interval": self.autosave_interval_spin.value(),
            "theme": _INDEX_TO_THEME.get(
                self.theme_combo.currentIndex(), "dark"
            ),
            "font_size": self.font_size_spin.value(),
            "console_max_lines": self.console_lines_spin.value(),
        }

    def _write_to_config(self):
        """Push the current widget values into Config and persist to disk."""
        values = self._gather_values()
        for key, value in values.items():
            self.config.set(key, value)
        self.config.save()
        return values

    # --------------------------------------------------------------------- #
    #  Button handlers
    # --------------------------------------------------------------------- #
    def _apply_settings(self):
        """Apply button -- save and emit signal, but keep the dialog open."""
        values = self._write_to_config()
        self.preferences_applied.emit(values)

    def _save_and_accept(self):
        """OK button -- save, emit signal, and close the dialog."""
        values = self._write_to_config()
        self.preferences_applied.emit(values)
        self.accept()

    def _restore_defaults(self):
        """Restore Defaults button -- reset Config and reload widgets."""
        self.config.reset()
        self._load_settings()

    # --------------------------------------------------------------------- #
    #  Browse helpers
    # --------------------------------------------------------------------- #
    def _browse_complab(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CompLaB Executable",
            "",
            "Executables (*.exe);;All Files (*)",
        )
        if path:
            self.complab_edit.setText(path)

    def _browse_paraview(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ParaView",
            "",
            "Executables (*.exe);;All Files (*)",
        )
        if path:
            self.paraview_edit.setText(path)

    def _browse_project_dir(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Default Project Directory"
        )
        if path:
            self.project_dir_edit.setText(path)

    # --------------------------------------------------------------------- #
    #  Public helpers
    # --------------------------------------------------------------------- #
    def get_values(self):
        """Return the current widget values as a dict (without saving).

        Useful after the dialog has been accepted so the caller can inspect
        the chosen preferences.
        """
        return self._gather_values()
