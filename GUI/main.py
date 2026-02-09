"""CompLaB Studio 2.0 - Entry Point"""

import sys
import os
from pathlib import Path

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont

from src.main_window import CompLaBMainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CompLaB Studio")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("UGA-CNU")

    # Load stylesheet
    style_path = Path(__file__).parent / "styles" / "theme.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text())

    # Default font
    font = QFont("Segoe UI", 10)
    font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    app.setFont(font)

    window = CompLaBMainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
