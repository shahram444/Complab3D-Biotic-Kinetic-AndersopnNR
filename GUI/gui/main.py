#!/usr/bin/env python3
"""
CompLaB Studio - Professional GUI for CompLaB Reactive Transport Simulations
A comprehensive interface for pore-scale biogeochemical modeling

Copyright (c) 2024 MeileLab, University of Georgia
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QFile, QTextStream
from PySide6.QtGui import QFont, QFontDatabase, QIcon

from src.main_window import CompLaBMainWindow
from src.config import Config


# --------------------------------------------------------------------------- #
#  Stylesheet / theme helpers
# --------------------------------------------------------------------------- #
_STYLES_DIR = Path(__file__).parent / "styles"

# A minimal light-theme stylesheet that mirrors the structure of the dark
# theme in main.qss but uses conventional light colours.  It is used as a
# fallback when no ``styles/light.qss`` file is shipped with the application.
_BUILT_IN_LIGHT_THEME = """\
/* CompLaB Studio - Built-in Light Theme */

QWidget {
    background-color: #f5f5f5;
    color: #1e1e1e;
    font-family: "Segoe UI", "SF Pro Display", sans-serif;
}

QMainWindow { background-color: #f5f5f5; }

QMenuBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #cccccc;
    padding: 4px;
}
QMenuBar::item { padding: 6px 12px; border-radius: 4px; }
QMenuBar::item:selected { background-color: #d0d0d0; }

QMenu {
    background-color: #ffffff;
    border: 1px solid #cccccc;
    border-radius: 4px;
    padding: 4px;
}
QMenu::item { padding: 8px 30px 8px 20px; border-radius: 3px; }
QMenu::item:selected { background-color: #cce5ff; }
QMenu::separator { height: 1px; background-color: #cccccc; margin: 4px 10px; }

QToolBar {
    background-color: #e8e8e8;
    border-bottom: 1px solid #cccccc;
    padding: 4px; spacing: 4px;
}
QToolButton {
    background-color: transparent;
    border: none; border-radius: 4px;
    padding: 6px 12px; margin: 2px;
}
QToolButton:hover { background-color: #d0d0d0; }
QToolButton:pressed { background-color: #b0c4de; }
QToolButton#runButton { background-color: #2ea043; color: white; }
QToolButton#runButton:hover { background-color: #3fb950; }
QToolButton#runButton:disabled { background-color: #c8e6c9; color: #81c784; }
QToolButton#stopButton { background-color: #da3633; color: white; }
QToolButton#stopButton:hover { background-color: #f85149; }
QToolButton#stopButton:disabled { background-color: #ffcdd2; color: #e57373; }

QStatusBar { background-color: #007acc; color: white; border-top: none; }
QStatusBar::item { border: none; }
QStatusBar QLabel { color: white; padding: 2px 8px; }

QFrame#leftPanel, QFrame#rightPanel { background-color: #fafafa; border: none; }
QLabel#panelHeader {
    background-color: #e8e8e8; padding: 10px;
    font-weight: bold; font-size: 11pt;
    border-bottom: 1px solid #cccccc;
}

QTreeWidget { background-color: #fafafa; border: none; outline: none; }
QTreeWidget::item { padding: 6px 4px; border-radius: 3px; }
QTreeWidget::item:hover { background-color: #e8e8e8; }
QTreeWidget::item:selected { background-color: #cce5ff; }

QTabWidget::pane { background-color: #f5f5f5; border: 1px solid #cccccc; border-top: none; }
QTabBar::tab {
    background-color: #e8e8e8; border: 1px solid #cccccc;
    border-bottom: none; padding: 8px 16px; margin-right: 2px;
}
QTabBar::tab:selected { background-color: #f5f5f5; border-bottom: 2px solid #007acc; }
QTabBar::tab:hover:!selected { background-color: #d0d0d0; }

QGroupBox {
    background-color: #fafafa; border: 1px solid #cccccc;
    border-radius: 6px; margin-top: 12px; padding-top: 12px; font-weight: bold;
}
QGroupBox::title {
    subcontrol-origin: margin; subcontrol-position: top left;
    left: 12px; padding: 0 6px; background-color: #fafafa; color: #1e1e1e;
}

QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #ffffff; border: 1px solid #bbbbbb;
    border-radius: 4px; padding: 6px 10px; selection-background-color: #cce5ff;
}
QLineEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border-color: #007acc;
}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #eeeeee; color: #aaaaaa;
}
QComboBox::drop-down { border: none; width: 24px; }
QComboBox QAbstractItemView {
    background-color: #ffffff; border: 1px solid #cccccc;
    selection-background-color: #cce5ff;
}
QSpinBox::up-button, QDoubleSpinBox::up-button {
    subcontrol-origin: border; subcontrol-position: top right;
    width: 20px; border-left: 1px solid #bbbbbb; background-color: #f0f0f0;
}
QSpinBox::down-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border; subcontrol-position: bottom right;
    width: 20px; border-left: 1px solid #bbbbbb; background-color: #f0f0f0;
}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {
    background-color: #e0e0e0;
}

QPushButton {
    background-color: #0e639c; border: none; border-radius: 4px;
    padding: 8px 16px; color: white; font-weight: 500;
}
QPushButton:hover { background-color: #1177bb; }
QPushButton:pressed { background-color: #094771; }
QPushButton:disabled { background-color: #cccccc; color: #999999; }

QCheckBox { spacing: 8px; }
QCheckBox::indicator {
    width: 18px; height: 18px; border-radius: 3px;
    border: 1px solid #bbbbbb; background-color: #ffffff;
}
QCheckBox::indicator:checked { background-color: #007acc; border-color: #007acc; }
QCheckBox::indicator:hover { border-color: #007acc; }

QListWidget {
    background-color: #fafafa; border: 1px solid #cccccc;
    border-radius: 4px; outline: none;
}
QListWidget::item { padding: 8px; border-radius: 3px; }
QListWidget::item:hover { background-color: #e8e8e8; }
QListWidget::item:selected { background-color: #cce5ff; }

QTableWidget { background-color: #fafafa; border: 1px solid #cccccc; gridline-color: #cccccc; }
QTableWidget::item { padding: 6px; }
QTableWidget::item:selected { background-color: #cce5ff; }
QHeaderView::section {
    background-color: #e8e8e8; border: none;
    border-right: 1px solid #cccccc; border-bottom: 1px solid #cccccc;
    padding: 8px; font-weight: bold;
}

QTextEdit {
    background-color: #ffffff; border: 1px solid #cccccc;
    border-radius: 4px; selection-background-color: #cce5ff;
}
QTextEdit#consoleOutput {
    font-family: "Cascadia Code", "Consolas", "Monaco", monospace;
    font-size: 9pt; background-color: #f8f8f8;
}

QScrollBar:vertical { background-color: #f5f5f5; width: 12px; margin: 0; }
QScrollBar::handle:vertical {
    background-color: #c0c0c0; border-radius: 6px; min-height: 30px; margin: 2px;
}
QScrollBar::handle:vertical:hover { background-color: #a0a0a0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background-color: #f5f5f5; height: 12px; margin: 0; }
QScrollBar::handle:horizontal {
    background-color: #c0c0c0; border-radius: 6px; min-width: 30px; margin: 2px;
}
QScrollBar::handle:horizontal:hover { background-color: #a0a0a0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QProgressBar {
    background-color: #e0e0e0; border: none; border-radius: 4px;
    text-align: center; height: 20px;
}
QProgressBar::chunk { background-color: #007acc; border-radius: 4px; }

QSplitter::handle { background-color: #cccccc; }
QSplitter::handle:horizontal { width: 2px; }
QSplitter::handle:vertical { height: 2px; }
QSplitter::handle:hover { background-color: #007acc; }

QDialog { background-color: #f0f0f0; }
QDialogButtonBox QPushButton { min-width: 80px; }

QToolTip {
    background-color: #ffffff; border: 1px solid #cccccc;
    color: #1e1e1e; padding: 6px; border-radius: 4px;
}

QLabel#infoLabel { color: #666666; font-size: 9pt; padding: 4px; }

QPushButton#collapseButton {
    background-color: transparent; border: none;
    text-align: left; padding: 8px; font-weight: bold;
}
QPushButton#collapseButton:hover { background-color: #e8e8e8; }

QLabel#simStatus { font-weight: bold; padding: 0 12px; }
"""


def load_fonts():
    """Load custom fonts for the application."""
    font_dir = Path(__file__).parent / "resources" / "fonts"
    if font_dir.exists():
        for font_file in font_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))


def _read_stylesheet(path):
    """Return the contents of *path* as a string, or empty string on failure."""
    try:
        with open(path, "r") as fh:
            return fh.read()
    except OSError:
        return ""


def get_theme_stylesheet(theme_name):
    """Return the QSS stylesheet string for the given *theme_name*.

    Parameters
    ----------
    theme_name : str
        One of ``"dark"``, ``"light"``, or ``"system"``.

    Returns
    -------
    str
        The full stylesheet text.  For ``"system"`` an empty string is
        returned so that the platform-native look is used.
    """
    if theme_name == "dark":
        dark_path = _STYLES_DIR / "main.qss"
        return _read_stylesheet(dark_path)

    if theme_name == "light":
        # Prefer an on-disk light stylesheet if one exists.
        light_path = _STYLES_DIR / "light.qss"
        if light_path.exists():
            return _read_stylesheet(light_path)
        return _BUILT_IN_LIGHT_THEME

    # "system" -- no custom stylesheet
    return ""


def apply_theme(app, config):
    """Apply the theme and font settings from *config* to *app*.

    This function can be called at any time -- at startup **and** later when
    the user changes preferences -- to switch the active theme and font size
    without restarting the application.

    Parameters
    ----------
    app : QApplication
        The running application instance.
    config : Config
        The application configuration object.
    """
    theme = config.get("theme", "dark")
    font_size = config.get("font_size", 10)

    # Apply the stylesheet for the selected theme
    stylesheet = get_theme_stylesheet(theme)
    app.setStyleSheet(stylesheet)

    # Apply the configured font size globally
    font = QFont("Segoe UI", font_size)
    app.setFont(font)


# --------------------------------------------------------------------------- #
#  Entry point
# --------------------------------------------------------------------------- #
def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("CompLaB Studio")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("CompLaB")
    app.setOrganizationDomain("complab.org")

    # Set application icon
    icon_path = Path(__file__).parent / "icons" / "complab_icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Load custom fonts
    load_fonts()

    # Load configuration and apply the saved theme
    config = Config()
    apply_theme(app, config)

    # Create and show main window
    window = CompLaBMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
