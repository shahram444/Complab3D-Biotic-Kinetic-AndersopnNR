"""CompLaB Studio 2.0 - Entry Point"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from src.main_window import CompLaBMainWindow
from src.config import AppConfig


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CompLaB Studio")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("MeileLab-UGA")

    config = AppConfig()

    # Load stylesheet based on theme preference
    theme = config.get("theme", "Dark")
    styles_dir = Path(__file__).parent / "styles"
    if theme == "Light":
        style_path = styles_dir / "light.qss"
    else:
        style_path = styles_dir / "theme.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    # Apply configured font size
    font_size = config.get("font_size", 10)
    font = QFont("Segoe UI", font_size)
    font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    app.setFont(font)

    window = CompLaBMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
