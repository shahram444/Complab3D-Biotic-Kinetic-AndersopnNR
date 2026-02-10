"""
Splash Screen for CompLaB Studio
Shows logo and loading progress on startup
"""

import os
from PySide6.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont


class CompLaBSplashScreen(QSplashScreen):
    """Custom splash screen with logo and progress bar"""
    
    def __init__(self):
        # Try to load logo image
        logo_path = self._find_logo()
        
        if logo_path and os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale if too large
            if pixmap.width() > 600:
                pixmap = pixmap.scaledToWidth(600, Qt.SmoothTransformation)
        else:
            # Create a default splash screen
            pixmap = self._create_default_splash()
            
        super().__init__(pixmap)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        
        # Progress tracking
        self.progress = 0
        self.status_message = "Initializing..."
        
    def _find_logo(self):
        """Find the logo file in various locations"""
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        possible_paths = [
            os.path.join(base_path, "resources", "splash.png"),
            os.path.join(base_path, "resources", "logo.png"),
            os.path.join(base_path, "splash.png"),
            os.path.join(base_path, "logo.png"),
            os.path.join(base_path, "images", "splash.png"),
            os.path.join(base_path, "images", "logo.png"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
                
        return None
        
    def _create_default_splash(self):
        """Create a default splash screen if no logo found"""
        width, height = 500, 350
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor("#1a1a2e"))
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw gradient background
        from PySide6.QtGui import QLinearGradient
        gradient = QLinearGradient(0, 0, 0, height)
        gradient.setColorAt(0, QColor("#1a1a2e"))
        gradient.setColorAt(1, QColor("#16213e"))
        painter.fillRect(0, 0, width, height, gradient)
        
        # Draw title
        painter.setPen(QColor("#e94560"))
        font = QFont("Arial", 36, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 80, width, 60, Qt.AlignCenter, "CompLaB")
        
        # Draw subtitle
        painter.setPen(QColor("#0f4c75"))
        font = QFont("Arial", 24, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 130, width, 40, Qt.AlignCenter, "Studio")
        
        # Draw description
        painter.setPen(QColor("#ffffff"))
        font = QFont("Arial", 12)
        painter.setFont(font)
        painter.drawText(0, 180, width, 30, Qt.AlignCenter, "Pore-Scale Reactive Transport Modeling")
        
        # Draw version
        painter.setPen(QColor("#888888"))
        font = QFont("Arial", 10)
        painter.setFont(font)
        painter.drawText(0, 210, width, 25, Qt.AlignCenter, "Version 1.0")
        
        # Draw credits
        painter.setPen(QColor("#666666"))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(0, 280, width, 20, Qt.AlignCenter, "Developed by Shahram Asgari")
        painter.drawText(0, 300, width, 20, Qt.AlignCenter, "University of Georgia")
        
        # Draw border
        painter.setPen(QColor("#e94560"))
        painter.drawRect(0, 0, width-1, height-1)
        
        painter.end()
        
        return pixmap
        
    def drawContents(self, painter):
        """Draw progress bar and status on splash screen"""
        super().drawContents(painter)
        
        # Get dimensions
        width = self.pixmap().width()
        height = self.pixmap().height()
        
        # Draw progress bar background
        bar_height = 6
        bar_y = height - 40
        bar_margin = 30
        bar_width = width - 2 * bar_margin
        
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor("#333333"))
        painter.drawRect(bar_margin, bar_y, bar_width, bar_height)
        
        # Draw progress bar fill
        fill_width = int(bar_width * self.progress / 100)
        painter.setBrush(QColor("#e94560"))
        painter.drawRect(bar_margin, bar_y, fill_width, bar_height)
        
        # Draw status message
        painter.setPen(QColor("#aaaaaa"))
        font = QFont("Arial", 9)
        painter.setFont(font)
        painter.drawText(bar_margin, bar_y + 12, bar_width, 20, 
                        Qt.AlignLeft, self.status_message)
        
    def set_progress(self, value, message=""):
        """Update progress bar and message"""
        self.progress = min(100, max(0, value))
        if message:
            self.status_message = message
        self.repaint()
        
    def show_message(self, message, color=Qt.white):
        """Show a status message"""
        self.status_message = message
        self.repaint()


def show_splash_and_load(app, main_window_class):
    """
    Show splash screen while loading the main window.
    
    Usage:
        from splash_screen import show_splash_and_load
        from main_window import CompLaBMainWindow
        
        app = QApplication(sys.argv)
        window = show_splash_and_load(app, CompLaBMainWindow)
        window.show()
        sys.exit(app.exec())
    """
    splash = CompLaBSplashScreen()
    splash.show()
    app.processEvents()
    
    # Simulate loading stages
    stages = [
        (10, "Loading configuration..."),
        (25, "Initializing UI components..."),
        (40, "Loading project manager..."),
        (55, "Setting up simulation engine..."),
        (70, "Loading panels..."),
        (85, "Preparing workspace..."),
        (100, "Ready!"),
    ]
    
    for progress, message in stages:
        splash.set_progress(progress, message)
        app.processEvents()
        QTimer.singleShot(100, lambda: None)  # Small delay
        import time
        time.sleep(0.15)  # Brief pause for visual effect
    
    # Create main window
    splash.set_progress(100, "Starting CompLaB Studio...")
    app.processEvents()
    
    window = main_window_class()
    
    # Close splash and show main window
    import time
    time.sleep(0.3)
    splash.finish(window)
    
    return window
