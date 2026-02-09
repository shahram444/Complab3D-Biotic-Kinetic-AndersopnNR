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
        self.setFixedSize(500, 520)
        self.setModal(True)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title
        title = QLabel("CompLaB Studio")
        title.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Version
        version = QLabel("Version 1.0.0")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #888;")
        layout.addWidget(version)
        
        # Separator
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setStyleSheet("background-color: #444;")
        layout.addWidget(line1)
        
        # Main description
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
        
        # 3D GUI Development Credits
        gui_header = QLabel("<b>CompLaB Studio 3D GUI</b>")
        gui_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(gui_header)
        
        gui_dev = QLabel(
            "<b>Developed by:</b> Shahram Asgari<br>"
            "<a href='mailto:shahram.asgari@uga.edu'>shahram.asgari@uga.edu</a>"
        )
        gui_dev.setAlignment(Qt.AlignCenter)
        gui_dev.setOpenExternalLinks(True)
        layout.addWidget(gui_dev)
        
        advisor = QLabel(
            "<b>Advisor:</b> Christof Meile<br>"
            "<a href='mailto:cmeile@uga.edu'>cmeile@uga.edu</a>"
        )
        advisor.setAlignment(Qt.AlignCenter)
        advisor.setOpenExternalLinks(True)
        layout.addWidget(advisor)
        
        # Separator
        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setStyleSheet("background-color: #444;")
        layout.addWidget(line3)
        
        # Original CompLaB 2D Credits
        core_header = QLabel("<b>CompLaB Core Engine (2D)</b>")
        core_header.setAlignment(Qt.AlignCenter)
        layout.addWidget(core_header)
        
        core_dev = QLabel(
            "<b>Original Developer:</b> Heewon Jung<br>"
            "<a href='mailto:hjung@cnu.ac.kr'>hjung@cnu.ac.kr</a>"
        )
        core_dev.setAlignment(Qt.AlignCenter)
        core_dev.setOpenExternalLinks(True)
        layout.addWidget(core_dev)
        
        universities = QLabel(
            "University of Georgia & Chungnam National University"
        )
        universities.setAlignment(Qt.AlignCenter)
        universities.setStyleSheet("color: #aaa;")
        layout.addWidget(universities)
        
        # Separator
        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setStyleSheet("background-color: #444;")
        layout.addWidget(line4)
        
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
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setFixedWidth(100)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
