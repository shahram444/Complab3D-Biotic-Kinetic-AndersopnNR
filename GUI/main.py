"""CompLaB Studio 2.0 - Entry Point with Splash Screen"""

import sys
import os
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QTimer

from src.config import AppConfig


def _make_splash_pixmap():
    """Try to load splash.png, fall back to programmatic splash."""
    resources = Path(__file__).parent / "gui" / "resources"
    splash_path = resources / "splash.png"
    if splash_path.exists():
        return QPixmap(str(splash_path))

    # Fallback: create a programmatic splash
    pm = QPixmap(640, 400)
    pm.fill(QColor("#0f1a2e"))
    p = QPainter(pm)
    p.setPen(QColor("#ffffff"))
    f = QFont("Segoe UI", 24, QFont.Weight.Bold)
    p.setFont(f)
    p.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "CompLaB Studio 2.0")
    p.end()
    return pm


def _draw_credits(splash):
    """Draw credit text on the splash screen."""
    pm = splash.pixmap().copy()
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Semi-transparent overlay at bottom
    p.fillRect(0, pm.height() - 110, pm.width(), 110, QColor(15, 26, 46, 200))

    # Credit text
    p.setPen(QColor("#c0c8d4"))
    f = QFont("Segoe UI", 9)
    p.setFont(f)

    y = pm.height() - 100
    lines = [
        "CompLaB Studio 2.0 - 3D Biogeochemical Reactive Transport Simulator",
        "",
        "Developer: Shahram Asgari    |    PI: Christof Meile",
        "Meile Lab  -  Department of Marine Sciences  -  University of Georgia",
        "Lattice Boltzmann | Biotic & Abiotic Kinetics | Equilibrium Chemistry | CA Biofilm",
    ]
    for line in lines:
        p.drawText(20, y, line)
        y += 17

    # Version in top-right
    p.setPen(QColor("#6a8aaa"))
    f2 = QFont("Segoe UI", 8)
    p.setFont(f2)
    p.drawText(pm.width() - 100, 20, "v2.0.0")

    p.end()
    splash.setPixmap(pm)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CompLaB Studio")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("MeileLab-UGA")

    config = AppConfig()

    # --- Splash Screen ---
    splash_pm = _make_splash_pixmap()
    splash = QSplashScreen(splash_pm, Qt.WindowType.WindowStaysOnTopHint)
    _draw_credits(splash)
    splash.show()
    splash.showMessage(
        "  Loading CompLaB Studio...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor("#8aa0b8"),
    )
    app.processEvents()

    # Load stylesheet based on theme preference
    theme = config.get("theme", "Dark")
    styles_dir = Path(__file__).parent / "styles"
    if theme == "Light":
        style_path = styles_dir / "light.qss"
    else:
        style_path = styles_dir / "theme.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    # Apply configured font size (default 9pt matches COMSOL)
    font_size = config.get("font_size", 9)
    font = QFont("Segoe UI", font_size)
    font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    app.setFont(font)

    # Set window icon
    icon_path = Path(__file__).parent / "gui" / "resources" / "icon.png"
    if icon_path.exists():
        from PySide6.QtGui import QIcon
        app.setWindowIcon(QIcon(str(icon_path)))

    splash.showMessage(
        "  Initializing interface...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor("#8aa0b8"),
    )
    app.processEvents()

    from src.main_window import CompLaBMainWindow
    window = CompLaBMainWindow()

    # Keep splash visible for a brief moment
    QTimer.singleShot(1500, lambda: (splash.finish(window), window.show()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
