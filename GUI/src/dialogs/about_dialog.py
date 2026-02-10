"""About dialog."""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About CompLaB Studio")
        self.setFixedSize(420, 320)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 30, 30, 30)

        title = QLabel("CompLaB Studio")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("Version 2.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setProperty("info", True)
        layout.addWidget(version)

        desc = QLabel(
            "Graphical interface for CompLaB3D\n"
            "3D Biogeochemical Reactive Transport Simulator\n\n"
            "Lattice Boltzmann Method for flow and transport\n"
            "Biotic and abiotic kinetics\n"
            "Equilibrium chemistry with Anderson acceleration\n"
            "Cellular automata biofilm modeling"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        credits = QLabel(
            "University of Georgia, USA\n"
            "Chungnam National University, South Korea"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setProperty("info", True)
        layout.addWidget(credits)

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
