"""
New Project Dialog - Create new projects with template selection
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit,
    QListWidget, QListWidgetItem, QFrame, QMessageBox,
    QSplitter, QWidget
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..core.project_templates import (
    TemplateType, get_all_templates, get_template, 
    get_template_summary, apply_template
)


class TemplateListItem(QListWidgetItem):
    """Custom list item for templates"""
    
    def __init__(self, template):
        super().__init__()
        self.template = template
        self.setText(f"{template.icon}  {template.name}")
        self.setToolTip(template.description)


class NewProjectDialog(QDialog):
    """Dialog for creating a new project with template selection"""
    
    # Signal emitted when project is created
    project_created = Signal(object)  # Emits project data dict
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumSize(700, 500)
        self.selected_template = None
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("Create New Project")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        layout.addWidget(title)
        
        # Main content - splitter for template list and details
        splitter = QSplitter(Qt.Horizontal)
        
        # === Left side: Template list ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        template_label = QLabel("Select Template:")
        template_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        left_layout.addWidget(template_label)
        
        self.template_list = QListWidget()
        self.template_list.setMinimumWidth(200)
        self.template_list.setFont(QFont("Segoe UI", 10))
        self.template_list.itemSelectionChanged.connect(self._on_template_selected)
        
        # Add templates to list
        for template in get_all_templates():
            item = TemplateListItem(template)
            self.template_list.addItem(item)
        
        left_layout.addWidget(self.template_list)
        splitter.addWidget(left_widget)
        
        # === Right side: Template details and project settings ===
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(10, 0, 0, 0)
        
        # Template description
        desc_group = QGroupBox("Template Description")
        desc_layout = QVBoxLayout()
        
        self.template_desc = QLabel("Select a template to see description")
        self.template_desc.setWordWrap(True)
        self.template_desc.setStyleSheet("color: #ccc;")
        desc_layout.addWidget(self.template_desc)
        
        # Features list
        self.features_label = QLabel("")
        self.features_label.setWordWrap(True)
        self.features_label.setStyleSheet("color: #8f8; font-family: monospace;")
        desc_layout.addWidget(self.features_label)
        
        desc_group.setLayout(desc_layout)
        right_layout.addWidget(desc_group)
        
        # Project settings
        settings_group = QGroupBox("Project Settings")
        settings_layout = QFormLayout()
        
        # Project name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter project name")
        self.name_edit.textChanged.connect(self._update_path)
        settings_layout.addRow("Project Name:", self.name_edit)
        
        # Project location
        location_layout = QHBoxLayout()
        self.location_edit = QLineEdit()
        self.location_edit.setPlaceholderText("Select project location")
        
        # Default location
        default_path = os.path.join(os.path.expanduser("~"), "CompLaB_Projects")
        self.location_edit.setText(default_path)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(self.location_edit)
        location_layout.addWidget(browse_btn)
        settings_layout.addRow("Location:", location_layout)
        
        # Full path preview
        self.path_preview = QLabel("")
        self.path_preview.setStyleSheet("color: #888; font-size: 9pt;")
        settings_layout.addRow("Full Path:", self.path_preview)
        
        # Description
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Optional project description...")
        self.desc_edit.setMaximumHeight(60)
        settings_layout.addRow("Description:", self.desc_edit)
        
        settings_group.setLayout(settings_layout)
        right_layout.addWidget(settings_group)
        
        right_layout.addStretch()
        splitter.addWidget(right_widget)
        
        # Set splitter sizes
        splitter.setSizes([250, 450])
        layout.addWidget(splitter)
        
        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #444;")
        layout.addWidget(line)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        self.create_btn = QPushButton("Create Project")
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._create_project)
        self.create_btn.setStyleSheet(
            "QPushButton { background-color: #2a7; color: white; font-weight: bold; "
            "padding: 8px 20px; }"
            "QPushButton:hover { background-color: #3b8; }"
            "QPushButton:disabled { background-color: #555; color: #888; }"
        )
        button_layout.addWidget(self.create_btn)
        
        layout.addLayout(button_layout)
        
        # Select first template by default
        if self.template_list.count() > 0:
            self.template_list.setCurrentRow(0)
            
    def _on_template_selected(self):
        """Handle template selection"""
        items = self.template_list.selectedItems()
        if not items:
            self.selected_template = None
            self.template_desc.setText("Select a template to see description")
            self.features_label.setText("")
            return
            
        item = items[0]
        if isinstance(item, TemplateListItem):
            self.selected_template = item.template
            self.template_desc.setText(self.selected_template.description)
            self.features_label.setText(get_template_summary(self.selected_template.template_type))
            
        self._validate()
        
    def _browse_location(self):
        """Browse for project location"""
        folder = QFileDialog.getExistingDirectory(
            self, "Select Project Location",
            self.location_edit.text()
        )
        if folder:
            self.location_edit.setText(folder)
            self._update_path()
            
    def _update_path(self):
        """Update full path preview"""
        name = self.name_edit.text().strip()
        location = self.location_edit.text().strip()
        
        if name and location:
            full_path = os.path.join(location, name, f"{name}.complab")
            self.path_preview.setText(full_path)
        else:
            self.path_preview.setText("")
            
        self._validate()
        
    def _validate(self):
        """Validate inputs and enable/disable create button"""
        name = self.name_edit.text().strip()
        location = self.location_edit.text().strip()
        
        valid = (
            bool(name) and 
            bool(location) and 
            self.selected_template is not None
        )
        
        self.create_btn.setEnabled(valid)
        
    def _create_project(self):
        """Create the project"""
        name = self.name_edit.text().strip()
        location = self.location_edit.text().strip()
        description = self.desc_edit.toPlainText().strip()
        
        # Create project directory
        project_dir = os.path.join(location, name)
        project_file = os.path.join(project_dir, f"{name}.complab")
        
        # Check if exists
        if os.path.exists(project_dir):
            result = QMessageBox.question(
                self, "Project Exists",
                f"A folder named '{name}' already exists.\n\nDo you want to use it anyway?",
                QMessageBox.Yes | QMessageBox.No
            )
            if result != QMessageBox.Yes:
                return
        
        # Create directories
        try:
            os.makedirs(project_dir, exist_ok=True)
            os.makedirs(os.path.join(project_dir, "input"), exist_ok=True)
            os.makedirs(os.path.join(project_dir, "output"), exist_ok=True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create directories:\n{e}")
            return
        
        # Emit project data
        project_data = {
            "name": name,
            "path": project_file,
            "description": description,
            "template": self.selected_template.template_type,
            "add_default_substrate": False,  # Template will handle this
            "add_default_microbe": False,
        }
        
        self.project_created.emit(project_data)
        self.accept()
        
    def get_project_data(self) -> dict:
        """Get the project data (after dialog accepted)"""
        return {
            "name": self.name_edit.text().strip(),
            "path": self.path_preview.text(),
            "description": self.desc_edit.toPlainText().strip(),
            "template": self.selected_template.template_type if self.selected_template else None,
        }
