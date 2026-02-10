"""Preferences dialog - application settings."""

import sys
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit,
    QPushButton, QHBoxLayout, QTabWidget, QWidget,
    QSpinBox, QCheckBox, QFileDialog, QComboBox,
)
from PySide6.QtCore import Qt


class PreferencesDialog(QDialog):

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setMinimumSize(520, 400)
        self._config = config
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("Preferences")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        tabs = QTabWidget()

        # --- General Tab ---
        gen_w = QWidget()
        gf = QFormLayout(gen_w)
        gf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        gf.setHorizontalSpacing(12)
        gf.setVerticalSpacing(8)

        exe_row = QHBoxLayout()
        self._exe_path = QLineEdit(self._config.get("complab_executable", ""))
        self._exe_path.setPlaceholderText("Path to complab3d executable")
        exe_browse = QPushButton("Browse")
        exe_browse.setFixedWidth(80)
        exe_browse.clicked.connect(self._browse_exe)
        exe_row.addWidget(self._exe_path)
        exe_row.addWidget(exe_browse)

        dir_row = QHBoxLayout()
        self._proj_dir = QLineEdit(self._config.get("default_project_dir", ""))
        self._proj_dir.setPlaceholderText("Default directory for new projects")
        dir_browse = QPushButton("Browse")
        dir_browse.setFixedWidth(80)
        dir_browse.clicked.connect(self._browse_dir)
        dir_row.addWidget(self._proj_dir)
        dir_row.addWidget(dir_browse)

        self._auto_save = QCheckBox("Enable auto-save")
        self._auto_save.setChecked(self._config.get("auto_save", False))

        self._auto_interval = QSpinBox()
        self._auto_interval.setRange(30, 3600)
        self._auto_interval.setValue(self._config.get("auto_save_interval", 300))
        self._auto_interval.setSuffix(" sec")

        gf.addRow("CompLaB executable:", exe_row)
        gf.addRow("Default project directory:", dir_row)
        gf.addRow("", self._auto_save)
        gf.addRow("Auto-save interval:", self._auto_interval)
        tabs.addTab(gen_w, "General")

        # --- Display Tab ---
        disp_w = QWidget()
        df = QFormLayout(disp_w)
        df.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        df.setHorizontalSpacing(12)
        df.setVerticalSpacing(8)

        self._font_size = QSpinBox()
        self._font_size.setRange(8, 18)
        self._font_size.setValue(self._config.get("font_size", 10))
        self._font_size.setSuffix(" pt")
        self._font_size.setToolTip(
            "Application font size. Applied on next restart.")

        self._max_console = QSpinBox()
        self._max_console.setRange(500, 100000)
        self._max_console.setSingleStep(1000)
        self._max_console.setValue(self._config.get("max_console_lines", 10000))
        self._max_console.setToolTip(
            "Maximum number of lines kept in the console output. "
            "Older lines are trimmed automatically.")

        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["Dark", "Light"])
        current_theme = self._config.get("theme", "Dark")
        idx = self._theme_combo.findText(current_theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

        df.addRow("Font size:", self._font_size)
        df.addRow("Max console lines:", self._max_console)
        df.addRow("Theme:", self._theme_combo)

        note = QLabel("Font size and theme changes take effect on restart.")
        note.setProperty("info", True)
        df.addRow("", note)

        tabs.addTab(disp_w, "Display")

        layout.addWidget(tabs, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton("Save")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self._save_and_close)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _browse_exe(self):
        if sys.platform == "win32":
            filt = "Executables (*.exe);;All Files (*)"
        else:
            filt = "All Files (*)"
        path, _ = QFileDialog.getOpenFileName(
            self, "Select CompLaB Executable", "", filt)
        if path:
            self._exe_path.setText(path)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select Default Project Directory", self._proj_dir.text())
        if d:
            self._proj_dir.setText(d)

    def _save_and_close(self):
        self._config.set("complab_executable", self._exe_path.text())
        self._config.set("default_project_dir", self._proj_dir.text())
        self._config.set("auto_save", self._auto_save.isChecked())
        self._config.set("auto_save_interval", self._auto_interval.value())
        self._config.set("font_size", self._font_size.value())
        self._config.set("max_console_lines", self._max_console.value())
        self._config.set("theme", self._theme_combo.currentText())
        self._config.save()
        self.accept()
