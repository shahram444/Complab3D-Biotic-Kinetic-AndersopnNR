"""
About Dialog for CompLaB Studio
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap


class AboutDialog(QDialog):
    """About dialog showing application information and credits"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About CompLaB Studio")
        self.setFixedSize(520, 480)
        self.setModal(True)

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(30, 25, 30, 25)

        # Title
        title = QLabel("CompLaB Studio")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(22)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Version
        version = QLabel("Version 1.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(version)

        # Separator
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background-color: #444;")
        layout.addWidget(line1)

        # Description
        desc = QLabel(
            "<b>Professional GUI for CompLaB 3D Reactive Transport Simulations</b><br><br>"
            "A comprehensive interface for pore-scale biogeochemical modeling using "
            "the lattice Boltzmann method."
        )
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Separator
        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setStyleSheet("background-color: #444;")
        layout.addWidget(line2)

        # Development Credits
        credits_header = QLabel("<b>Development Team</b>")
        credits_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits_header)

        developer = QLabel(
            "<b>Developer:</b> Shahram Asgari<br>"
            "<a href='mailto:shahram.asgari@uga.edu'>shahram.asgari@uga.edu</a>"
        )
        developer.setAlignment(Qt.AlignCenter)
        developer.setOpenExternalLinks(True)
        layout.addWidget(developer)

        pi_label = QLabel(
            "<b>Principal Investigator:</b> Christof Meile<br>"
            "<a href='mailto:cmeile@uga.edu'>cmeile@uga.edu</a>"
        )
        pi_label.setAlignment(Qt.AlignCenter)
        pi_label.setOpenExternalLinks(True)
        layout.addWidget(pi_label)

        lab_label = QLabel(
            "<b>MeileLab</b> | University of Georgia"
        )
        lab_label.setAlignment(Qt.AlignCenter)
        lab_label.setStyleSheet("color: #aaa;")
        layout.addWidget(lab_label)

        # Separator
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setStyleSheet("background-color: #444;")
        layout.addWidget(line3)

        # Links
        links = QLabel(
            "<a href='https://bitbucket.org/MeileLab/complab'>bitbucket.org/MeileLab/complab</a>"
        )
        links.setAlignment(Qt.AlignCenter)
        links.setOpenExternalLinks(True)
        layout.addWidget(links)

        # License
        license_label = QLabel("Licensed under GNU AGPL v3")
        license_label.setAlignment(Qt.AlignCenter)
        license_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(license_label)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
