"""New project creation dialog with template selection."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFileDialog, QGroupBox, QTextEdit,
)
from PySide6.QtCore import Qt

from ..core.templates import ProjectTemplates, TEMPLATES


class NewProjectDialog(QDialog):

    def __init__(self, default_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumSize(700, 500)
        self._default_dir = default_dir
        self._selected_template = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        heading = QLabel("Create New Project")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        body = QHBoxLayout()
        body.setSpacing(16)

        # Left: template list
        left = QVBoxLayout()
        left.addWidget(QLabel("Select Template:"))

        self._template_list = QListWidget()
        self._template_list.setMinimumWidth(260)
        current_group = ""
        for key, label, group, desc in ProjectTemplates.list_templates():
            if group != current_group:
                separator = QListWidgetItem(f"--- {group} ---")
                separator.setFlags(Qt.ItemFlag.NoItemFlags)
                self._template_list.addItem(separator)
                current_group = group
            item = QListWidgetItem(f"  {label}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._template_list.addItem(item)

        self._template_list.currentItemChanged.connect(self._on_template_selected)
        left.addWidget(self._template_list)

        # Right: details + project info
        right = QVBoxLayout()

        self._desc_label = QLabel("Select a template to see its description.")
        self._desc_label.setProperty("info", True)
        self._desc_label.setWordWrap(True)
        self._desc_label.setMinimumHeight(60)
        right.addWidget(self._desc_label)

        right.addWidget(self._separator())

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        self._name_edit = QLineEdit("MyProject")
        self._name_edit.textChanged.connect(self._update_path)

        dir_row = QHBoxLayout()
        self._dir_edit = QLineEdit(self._default_dir or str(Path.home() / "CompLaB_Projects"))
        self._browse_btn = QPushButton("Browse")
        self._browse_btn.setFixedWidth(80)
        self._browse_btn.clicked.connect(self._browse_dir)
        dir_row.addWidget(self._dir_edit)
        dir_row.addWidget(self._browse_btn)

        self._path_label = QLabel("")
        self._path_label.setProperty("info", True)

        self._description = QLineEdit()
        self._description.setPlaceholderText("Optional project description")

        form.addRow("Project name:", self._name_edit)
        form.addRow("Location:", dir_row)
        form.addRow("Full path:", self._path_label)
        form.addRow("Description:", self._description)

        right.addLayout(form)
        right.addStretch()

        body.addLayout(left)
        body.addLayout(right, 1)
        layout.addLayout(body, 1)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.clicked.connect(self.reject)
        self._create_btn = QPushButton("Create Project")
        self._create_btn.setProperty("primary", True)
        self._create_btn.clicked.connect(self.accept)
        self._create_btn.setEnabled(False)
        btn_row.addWidget(self._cancel_btn)
        btn_row.addWidget(self._create_btn)
        layout.addLayout(btn_row)

        self._update_path()

    def _separator(self):
        from PySide6.QtWidgets import QFrame
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        return line

    def _on_template_selected(self, current, previous):
        if current is None:
            return
        key = current.data(Qt.ItemDataRole.UserRole)
        if key and key in TEMPLATES:
            self._selected_template = key
            self._desc_label.setText(TEMPLATES[key]["description"])
            self._create_btn.setEnabled(True)
        else:
            self._selected_template = None
            self._create_btn.setEnabled(False)

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Select Project Location",
                                              self._dir_edit.text())
        if d:
            self._dir_edit.setText(d)
            self._update_path()

    def _update_path(self):
        name = self._name_edit.text().strip()
        directory = self._dir_edit.text().strip()
        if name and directory:
            self._path_label.setText(str(Path(directory) / name))
        else:
            self._path_label.setText("")

    def get_result(self):
        return {
            "name": self._name_edit.text().strip(),
            "directory": self._dir_edit.text().strip(),
            "template": self._selected_template,
            "description": self._description.text().strip(),
        }
