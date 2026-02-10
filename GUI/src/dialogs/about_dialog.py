"""About dialog."""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import Qt


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About CompLaB Studio")
        self.setFixedSize(480, 420)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(32, 28, 32, 24)

        title = QLabel("CompLaB Studio")
        title.setProperty("heading", True)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel("Version 2.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setProperty("info", True)
        layout.addWidget(version)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        desc = QLabel(
            "3D Biogeochemical Reactive Transport Simulator\n\n"
            "Lattice Boltzmann Method for flow and transport\n"
            "Biotic and abiotic kinetics\n"
            "Equilibrium chemistry with Anderson acceleration\n"
            "Cellular automata biofilm modeling"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        # Credits
        dev_label = QLabel("Developed by")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_label.setProperty("info", True)
        layout.addWidget(dev_label)

        credits = QLabel(
            "Shahram Asgari\n"
            "PI: Christof Meile"
        )
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet("font-weight: bold;")
        layout.addWidget(credits)

        lab = QLabel(
            "Meile Lab\n"
            "Department of Marine Sciences\n"
            "University of Georgia, USA"
        )
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lab.setProperty("info", True)
        layout.addWidget(lab)

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
