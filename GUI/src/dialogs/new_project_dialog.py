"""New project creation dialog with template selection."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFileDialog,
    QFormLayout,
)
from PySide6.QtCore import Qt

from ..core.templates import get_template_list, create_from_template


class NewProjectDialog(QDialog):
    """Template selection wizard for new project creation."""

    def __init__(self, default_dir: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumSize(550, 450)
        self._default_dir = default_dir
        self._selected_key = ""
        self._project = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("Create New Project")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        layout.addWidget(QLabel("Select a simulation template:"))

        # Template list
        self._list = QListWidget()
        templates = get_template_list()
        for key, name, desc in templates:
            item = QListWidgetItem(f"{name}\n  {desc}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_select)
        layout.addWidget(self._list, 1)

        # Description
        self._desc = QLabel("")
        self._desc.setProperty("info", True)
        self._desc.setWordWrap(True)
        layout.addWidget(self._desc)

        # Project name and directory
        form = QFormLayout()
        form.setHorizontalSpacing(12)

        self._name_edit = QLineEdit("Untitled")
        form.addRow("Project name:", self._name_edit)

        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit(self._default_dir)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self._dir_edit)
        dir_row.addWidget(browse_btn)
        form.addRow("Save directory:", dir_row)
        layout.addLayout(form)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        create_btn = QPushButton("Create")
        create_btn.setProperty("primary", True)
        create_btn.clicked.connect(self._create)
        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(create_btn)
        layout.addLayout(btn_row)

        if self._list.count() > 0:
            self._list.setCurrentRow(0)

    def _on_select(self, current, _prev=None):
        if current:
            self._selected_key = current.data(Qt.ItemDataRole.UserRole)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select Project Directory", self._dir_edit.text())
        if d:
            self._dir_edit.setText(d)

    def _create(self):
        if not self._selected_key:
            return
        self._project = create_from_template(self._selected_key)
        name = self._name_edit.text().strip()
        if name:
            self._project.name = name
        self.accept()

    def get_project(self):
        return self._project

    def get_directory(self) -> str:
        return self._dir_edit.text()
