"""About dialog with full credits."""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap


class AboutDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About CompLaB Studio")
        self.setFixedSize(500, 480)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(32, 24, 32, 20)

        # Logo
        logo_path = Path(__file__).parent.parent.parent / "gui" / "resources" / "logo.png"
        if logo_path.exists():
            logo_lbl = QLabel()
            pm = QPixmap(str(logo_path))
            scaled = pm.scaledToHeight(60, Qt.TransformationMode.SmoothTransformation)
            logo_lbl.setPixmap(scaled)
            logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(logo_lbl)

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
            "Lattice Boltzmann Method for flow and solute transport\n"
            "Biotic kinetics with Monod growth models\n"
            "Abiotic kinetics for chemical reactions\n"
            "Equilibrium chemistry with Anderson acceleration\n"
            "Cellular automata biofilm modeling\n"
            "Multi-species, multi-substrate reactive transport"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep2)

        dev_label = QLabel("Developed by")
        dev_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dev_label.setProperty("info", True)
        layout.addWidget(dev_label)

        credits = QLabel("Shahram Asgari")
        credits.setAlignment(Qt.AlignmentFlag.AlignCenter)
        credits.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(credits)

        pi_label = QLabel("Principal Investigator")
        pi_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pi_label.setProperty("info", True)
        layout.addWidget(pi_label)

        pi = QLabel("Christof Meile")
        pi.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pi.setStyleSheet("font-weight: bold; font-size: 11pt;")
        layout.addWidget(pi)

        sep3 = QFrame()
        sep3.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep3)

        lab = QLabel(
            "Meile Lab\n"
            "Department of Marine Sciences\n"
            "University of Georgia, Athens, GA, USA"
        )
        lab.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lab)

        layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)
