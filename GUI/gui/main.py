#!/usr/bin/env python3
"""
CompLaB Studio - Professional GUI for CompLaB Reactive Transport Simulations
A comprehensive interface for pore-scale biogeochemical modeling

Copyright (c) 2024 CompLaB Development Team
University of Georgia & Chungnam National University
"""

import sys
import os
from pathlib import Path

# Ensure gui directory is on path so 'src' is importable as a package
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QFile, QTextStream
from PySide6.QtGui import QFont, QFontDatabase, QIcon

from src.main_window import CompLaBMainWindow
from src.config import Config


def load_fonts():
    """Load custom fonts for the application"""
    font_dir = Path(__file__).parent / "resources" / "fonts"
    if font_dir.exists():
        for font_file in font_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))


def load_stylesheet(app):
    """Load the application stylesheet"""
    style_file = Path(__file__).parent / "styles" / "main.qss"
    if style_file.exists():
        with open(style_file, "r") as f:
            app.setStyleSheet(f.read())


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
    
    # Load fonts and styles
    load_fonts()
    load_stylesheet(app)
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Create and show main window
    window = CompLaBMainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
