"""CompLaB Studio 2.1 - Entry Point with Splash Screen"""

import sys
import os
import time
from pathlib import Path

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QColor, QLinearGradient,
    QPen, QBrush,
)
from PySide6.QtCore import Qt, QTimer, QRect, QRectF

from src.config import AppConfig

# Splash screen dimensions
SPLASH_W, SPLASH_H = 680, 440

# Version constant used everywhere
VERSION = "2.1.0"


def _make_splash_pixmap():
    """Build the splash screen pixmap.

    Priority:
      1. splash.png (full splash image) — scaled to fill canvas
      2. logo.png drawn on dark gradient background
      3. Pure programmatic splash (no images)
    """
    gui_dir = Path(__file__).resolve().parent
    resources = gui_dir / "gui" / "resources"
    splash_path = resources / "splash.png"
    logo_path = resources / "logo.png"

    # ── Try splash.png first ──────────────────────────────────────
    if splash_path.exists():
        raw = QPixmap(str(splash_path))
        if not raw.isNull() and raw.width() > 0:
            pm = QPixmap(SPLASH_W, SPLASH_H)
            pm.fill(QColor("#0d1829"))
            p = QPainter(pm)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            scaled = raw.scaledToWidth(
                SPLASH_W, Qt.TransformationMode.SmoothTransformation)
            y = (SPLASH_H - scaled.height()) // 2
            p.drawPixmap(0, y, scaled)
            p.end()
            return pm

    # ── Programmatic splash ───────────────────────────────────────
    pm = QPixmap(SPLASH_W, SPLASH_H)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Dark gradient background
    grad = QLinearGradient(0, 0, 0, SPLASH_H)
    grad.setColorAt(0.0, QColor("#0a1628"))
    grad.setColorAt(0.5, QColor("#0f1f3a"))
    grad.setColorAt(1.0, QColor("#0a1628"))
    p.fillRect(0, 0, SPLASH_W, SPLASH_H, grad)

    # Subtle grid pattern
    p.setPen(QPen(QColor(255, 255, 255, 8), 1))
    for gx in range(0, SPLASH_W, 40):
        p.drawLine(gx, 0, gx, SPLASH_H)
    for gy in range(0, SPLASH_H, 40):
        p.drawLine(0, gy, SPLASH_W, gy)

    # Try to draw the logo
    title_y = 100
    if logo_path.exists():
        logo_pm = QPixmap(str(logo_path))
        if not logo_pm.isNull() and logo_pm.width() > 0:
            scaled_logo = logo_pm.scaledToHeight(
                100, Qt.TransformationMode.SmoothTransformation)
            lx = (SPLASH_W - scaled_logo.width()) // 2
            p.drawPixmap(lx, 40, scaled_logo)
            title_y = 155

    # Title: "CompLaB"
    p.setPen(QColor("#e94560"))
    title_font = QFont("Segoe UI", 36, QFont.Weight.Bold)
    p.setFont(title_font)
    p.drawText(QRect(0, title_y, SPLASH_W, 50),
               Qt.AlignmentFlag.AlignCenter, "CompLaB")

    # Subtitle: "Studio 2.1"
    p.setPen(QColor("#ffffff"))
    sub_font = QFont("Segoe UI", 20, QFont.Weight.Light)
    p.setFont(sub_font)
    p.drawText(QRect(0, title_y + 48, SPLASH_W, 36),
               Qt.AlignmentFlag.AlignCenter, f"Studio {VERSION}")

    # Tagline
    p.setPen(QColor("#6a8aaa"))
    tag_font = QFont("Segoe UI", 10)
    p.setFont(tag_font)
    p.drawText(QRect(0, title_y + 90, SPLASH_W, 24),
               Qt.AlignmentFlag.AlignCenter,
               "Pore-Scale Reactive Transport Modeling")

    # Accent line
    line_y = title_y + 120
    p.setPen(Qt.PenStyle.NoPen)
    accent_grad = QLinearGradient(SPLASH_W * 0.2, 0, SPLASH_W * 0.8, 0)
    accent_grad.setColorAt(0.0, QColor(0, 0, 0, 0))
    accent_grad.setColorAt(0.3, QColor("#e94560"))
    accent_grad.setColorAt(0.7, QColor("#4a7cac"))
    accent_grad.setColorAt(1.0, QColor(0, 0, 0, 0))
    p.setBrush(QBrush(accent_grad))
    p.drawRect(QRectF(SPLASH_W * 0.15, line_y, SPLASH_W * 0.7, 2))

    p.end()
    return pm


def _draw_credits(splash):
    """Draw credit text and version on the splash screen."""
    pm = splash.pixmap().copy()
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Semi-transparent overlay at bottom
    bottom_grad = QLinearGradient(0, pm.height() - 120, 0, pm.height())
    bottom_grad.setColorAt(0.0, QColor(10, 22, 40, 180))
    bottom_grad.setColorAt(1.0, QColor(10, 22, 40, 230))
    p.fillRect(0, pm.height() - 120, pm.width(), 120, bottom_grad)

    # Credit text
    p.setPen(QColor("#b0b8c4"))
    f = QFont("Segoe UI", 8)
    p.setFont(f)

    y = pm.height() - 108
    lines = [
        "3D Biogeochemical Reactive Transport Simulator",
        "",
        "Developer: Shahram Asgari    |    PI: Christof Meile",
        "Meile Lab  -  Department of Marine Sciences  -  University of Georgia",
        "LBM Flow | Advection-Diffusion | Biotic & Abiotic Kinetics | Equilibrium Chemistry | CA Biofilm",
    ]
    for line in lines:
        p.drawText(20, y, line)
        y += 16

    # Version in top-right
    p.setPen(QColor("#4a6a8a"))
    f2 = QFont("Segoe UI", 8)
    p.setFont(f2)
    p.drawText(pm.width() - 80, 18, f"v{VERSION}")

    p.end()
    splash.setPixmap(pm)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CompLaB Studio")
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("MeileLab-UGA")

    config = AppConfig()

    # --- Splash Screen ---
    splash_pm = _make_splash_pixmap()
    splash = QSplashScreen(splash_pm, Qt.WindowType.WindowStaysOnTopHint)
    _draw_credits(splash)
    splash.show()
    splash.raise_()
    splash.activateWindow()
    splash.showMessage(
        "  Loading CompLaB Studio...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor("#8aa0b8"),
    )
    # Force multiple repaints so user sees the splash on all platforms
    app.processEvents()
    splash.repaint()
    time.sleep(0.2)
    app.processEvents()

    # Load stylesheet
    theme = config.get("theme", "Dark")
    styles_dir = Path(__file__).resolve().parent / "styles"
    if theme == "Light":
        style_path = styles_dir / "light.qss"
    else:
        style_path = styles_dir / "theme.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text(encoding="utf-8"))

    # Apply configured font size
    font_size = config.get("font_size", 9)
    font = QFont("Segoe UI", font_size)
    font.setStyleStrategy(QFont.StyleStrategy.PreferQuality)
    app.setFont(font)

    # Set window icon
    icon_path = Path(__file__).resolve().parent / "gui" / "resources" / "icon.png"
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
    app.processEvents()

    # Show splash for at least 3 seconds so user can read it
    splash.showMessage(
        "  Ready.",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft,
        QColor("#8aa0b8"),
    )
    app.processEvents()
    QTimer.singleShot(3000, lambda: (splash.finish(window), window.show()))

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
