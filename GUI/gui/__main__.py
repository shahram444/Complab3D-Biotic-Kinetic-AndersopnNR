"""
CompLaB Studio - Main Entry Point with Splash Screen

Run from the CompLaB_Studio folder with:
    python -m gui

Or create a shortcut to run:
    pythonw -m gui
"""

import sys
import os
import time

from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont, QLinearGradient, QIcon


class CompLaBSplash(QSplashScreen):
    """Splash screen for CompLaB Studio"""
    
    def __init__(self, gui_dir):
        self.gui_dir = gui_dir
        
        # Try to load custom splash image
        splash_path = os.path.join(gui_dir, "resources", "splash.png")
        
        if os.path.exists(splash_path):
            pixmap = QPixmap(splash_path)
            if pixmap.width() > 550:
                pixmap = pixmap.scaledToWidth(550, Qt.SmoothTransformation)
        else:
            pixmap = self._create_default_splash()
            
        super().__init__(pixmap)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.progress = 0
        self.message = "Starting..."
        
    def _create_default_splash(self):
        """Create default splash screen"""
        w, h = 500, 350
        pixmap = QPixmap(w, h)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Background gradient
        gradient = QLinearGradient(0, 0, 0, h)
        gradient.setColorAt(0, QColor("#1a1a2e"))
        gradient.setColorAt(1, QColor("#16213e"))
        painter.fillRect(0, 0, w, h, gradient)
        
        # Title
        painter.setPen(QColor("#e94560"))
        painter.setFont(QFont("Arial", 42, QFont.Bold))
        painter.drawText(0, 60, w, 70, Qt.AlignCenter, "CompLaB")
        
        # Subtitle
        painter.setPen(QColor("#0f4c75"))
        painter.setFont(QFont("Arial", 28, QFont.Bold))
        painter.drawText(0, 120, w, 50, Qt.AlignCenter, "Studio 3D")
        
        # Description
        painter.setPen(QColor("#ffffff"))
        painter.setFont(QFont("Arial", 11))
        painter.drawText(0, 175, w, 25, Qt.AlignCenter, "Pore-Scale Reactive Transport Modeling")
        
        # Version
        painter.setPen(QColor("#888888"))
        painter.setFont(QFont("Arial", 10))
        painter.drawText(0, 205, w, 20, Qt.AlignCenter, "Version 1.0")
        
        # Credits
        painter.setPen(QColor("#666666"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(0, 270, w, 18, Qt.AlignCenter, "Developed by Shahram Asgari")
        painter.drawText(0, 288, w, 18, Qt.AlignCenter, "University of Georgia")
        
        # Border
        painter.setPen(QColor("#e94560"))
        painter.drawRect(0, 0, w-1, h-1)
        
        painter.end()
        return pixmap
        
    def drawContents(self, painter):
        """Draw progress bar"""
        super().drawContents(painter)
        
        w = self.pixmap().width()
        h = self.pixmap().height()
        
        # Progress bar
        bar_y = h - 35
        bar_margin = 30
        bar_w = w - 2 * bar_margin
        bar_h = 5
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#333333"))
        painter.drawRect(bar_margin, bar_y, bar_w, bar_h)
        
        fill_w = int(bar_w * self.progress / 100)
        painter.setBrush(QColor("#e94560"))
        painter.drawRect(bar_margin, bar_y, fill_w, bar_h)
        
        # Status text
        painter.setPen(QColor("#aaaaaa"))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(bar_margin, bar_y + 10, bar_w, 18, Qt.AlignLeft, self.message)
        
    def update_progress(self, value, msg=""):
        """Update progress"""
        self.progress = value
        if msg:
            self.message = msg
        self.repaint()
        QApplication.processEvents()


def main():
    """Main entry point with splash screen"""
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("CompLaB Studio")
    app.setOrganizationName("University of Georgia")
    
    # Get gui directory
    gui_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Set icon if exists
    icon_path = os.path.join(gui_dir, "resources", "icon.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Show splash
    splash = CompLaBSplash(gui_dir)
    splash.show()
    app.processEvents()
    
    # Loading stages
    stages = [
        (10, "Loading configuration..."),
        (25, "Initializing UI..."),
        (40, "Loading project manager..."),
        (55, "Setting up panels..."),
        (70, "Loading simulation engine..."),
        (85, "Preparing workspace..."),
        (95, "Almost ready..."),
    ]
    
    for progress, msg in stages:
        splash.update_progress(progress, msg)
        time.sleep(0.1)
    
    # Load stylesheet
    style_path = os.path.join(gui_dir, "styles", "dark_theme.qss")
    if os.path.exists(style_path):
        with open(style_path, 'r') as f:
            app.setStyleSheet(f.read())
    
    # Import main window (this is where the actual loading happens)
    splash.update_progress(100, "Starting CompLaB Studio...")
    app.processEvents()
    
    from .src.main_window import CompLaBMainWindow
    
    window = CompLaBMainWindow()
    
    time.sleep(0.2)
    splash.finish(window)
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
