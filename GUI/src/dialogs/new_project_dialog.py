"""New project creation dialog with template selection, kinetics preview,
and compilation hints.

When a user picks a template, the right-hand panel shows:
  - Template description
  - Which .hh files are required
  - Substrate / microbe summary
  - Step-by-step compilation instructions
  - Preview buttons for the generated .hh code
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QFileDialog,
    QFormLayout, QTextEdit, QSplitter, QGroupBox, QWidget,
    QScrollArea,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ..core.templates import get_template_list, create_from_template
from ..core.kinetics_templates import get_kinetics_info


class NewProjectDialog(QDialog):
    """Template selection wizard with kinetics hints and preview."""

    def __init__(self, default_dir: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Project")
        self.setMinimumSize(900, 620)
        self._default_dir = default_dir
        self._selected_key = ""
        self._project = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        heading = QLabel("Create New Project")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        # ── Main area: template list (left) + details (right) ──
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- Left: template list ---
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.addWidget(QLabel("Select a simulation template:"))

        self._list = QListWidget()
        templates = get_template_list()
        for key, name, desc in templates:
            item = QListWidgetItem(f"{name}\n  {desc}")
            item.setData(Qt.ItemDataRole.UserRole, key)
            self._list.addItem(item)
        self._list.currentItemChanged.connect(self._on_select)
        left_layout.addWidget(self._list, 1)
        splitter.addWidget(left)

        # --- Right: details / hints panel ---
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(8)

        # Template info
        info_group = QGroupBox("Template Details")
        info_layout = QVBoxLayout()

        self._info_label = QLabel("")
        self._info_label.setWordWrap(True)
        self._info_label.setStyleSheet(
            "padding: 6px; background: #1a2332; border-radius: 4px;")
        info_layout.addWidget(self._info_label)
        info_group.setLayout(info_layout)
        right_layout.addWidget(info_group)

        # Kinetics files info
        kin_group = QGroupBox("Kinetics Files")
        kin_layout = QVBoxLayout()

        self._kinetics_info = QLabel("")
        self._kinetics_info.setWordWrap(True)
        self._kinetics_info.setStyleSheet(
            "padding: 6px; background: #1a2332; border-radius: 4px;")
        kin_layout.addWidget(self._kinetics_info)

        # Preview buttons
        preview_row = QHBoxLayout()
        self._preview_biotic_btn = QPushButton("Preview defineKinetics.hh")
        self._preview_biotic_btn.clicked.connect(
            lambda: self._show_preview("biotic"))
        self._preview_biotic_btn.setEnabled(False)
        preview_row.addWidget(self._preview_biotic_btn)

        self._preview_abiotic_btn = QPushButton("Preview defineAbioticKinetics.hh")
        self._preview_abiotic_btn.clicked.connect(
            lambda: self._show_preview("abiotic"))
        self._preview_abiotic_btn.setEnabled(False)
        preview_row.addWidget(self._preview_abiotic_btn)
        preview_row.addStretch()
        kin_layout.addLayout(preview_row)

        kin_group.setLayout(kin_layout)
        right_layout.addWidget(kin_group)

        # Compilation hints
        compile_group = QGroupBox("How to Compile")
        compile_layout = QVBoxLayout()
        self._compile_hint = QLabel("")
        self._compile_hint.setWordWrap(True)
        self._compile_hint.setStyleSheet(
            "padding: 8px; background: #1e293b; color: #94a3b8; "
            "border: 1px solid #334155; border-radius: 4px; "
            "font-family: Consolas, monospace; font-size: 10px;")
        compile_layout.addWidget(self._compile_hint)
        compile_group.setLayout(compile_layout)
        right_layout.addWidget(compile_group)

        right_layout.addStretch()
        right_scroll.setWidget(right_widget)
        splitter.addWidget(right_scroll)

        splitter.setSizes([320, 560])
        layout.addWidget(splitter, 1)

        # ── Code preview area (hidden by default) ──
        self._preview_group = QGroupBox("Code Preview")
        preview_layout = QVBoxLayout()
        self._preview_text = QTextEdit()
        self._preview_text.setReadOnly(True)
        font = QFont("Consolas", 9)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._preview_text.setFont(font)
        self._preview_text.setStyleSheet(
            "QTextEdit { background: #1e1e1e; color: #d4d4d4; "
            "border: 1px solid #3c3c3c; }")
        self._preview_text.setMaximumHeight(200)
        preview_layout.addWidget(self._preview_text)

        hide_btn = QPushButton("Hide Preview")
        hide_btn.clicked.connect(lambda: self._preview_group.setVisible(False))
        preview_layout.addWidget(hide_btn)

        self._preview_group.setLayout(preview_layout)
        self._preview_group.setVisible(False)
        layout.addWidget(self._preview_group)

        # ── Project name and directory ──
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

        # ── Buttons ──
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

    # ── Event handlers ───────────────────────────────────────────────

    def _on_select(self, current, _prev=None):
        if not current:
            return
        self._selected_key = current.data(Qt.ItemDataRole.UserRole)
        info = get_kinetics_info(self._selected_key)

        # Update project name suggestion
        templates = get_template_list()
        for key, name, desc in templates:
            if key == self._selected_key:
                self._name_edit.setText(name.replace(" ", "_"))
                break

        if not info:
            self._info_label.setText("No additional information available.")
            self._kinetics_info.setText("No kinetics files needed.")
            self._compile_hint.setText("")
            self._preview_biotic_btn.setEnabled(False)
            self._preview_abiotic_btn.setEnabled(False)
            return

        # -- Info panel --
        self._info_label.setText(info.hint)

        # -- Kinetics files panel --
        kin_lines = []
        if info.needs_biotic or info.biotic_hh:
            kin_lines.append(
                "defineKinetics.hh: PROVIDED (biotic/Monod kinetics)")
            if info.biotic_substrate_indices:
                kin_lines.append(
                    f"  Substrate indices used: "
                    f"C[{'], C['.join(str(i) for i in info.biotic_substrate_indices)}]")
            if info.biotic_microbe_indices:
                kin_lines.append(
                    f"  Microbe indices used: "
                    f"B[{'], B['.join(str(i) for i in info.biotic_microbe_indices)}]")
        else:
            kin_lines.append("defineKinetics.hh: Not needed")

        if info.needs_abiotic or info.abiotic_hh:
            kin_lines.append(
                "\ndefineAbioticKinetics.hh: PROVIDED (abiotic kinetics)")
            if info.abiotic_substrate_indices:
                kin_lines.append(
                    f"  Substrate indices used: "
                    f"C[{'], C['.join(str(i) for i in info.abiotic_substrate_indices)}]")
        else:
            kin_lines.append("\ndefineAbioticKinetics.hh: Not needed")

        self._kinetics_info.setText("\n".join(kin_lines))

        # Enable/disable preview buttons
        self._preview_biotic_btn.setEnabled(bool(info.biotic_hh))
        self._preview_abiotic_btn.setEnabled(bool(info.abiotic_hh))

        # -- Compilation hints --
        if info.needs_biotic or info.needs_abiotic or self._selected_key == "scratch":
            files_needed = []
            if info.biotic_hh:
                files_needed.append("defineKinetics.hh")
            if info.abiotic_hh:
                files_needed.append("defineAbioticKinetics.hh")
            files_str = " and ".join(files_needed) if files_needed else "(none)"

            self._compile_hint.setText(
                "After creating the project:\n\n"
                f"  1. Export CompLaB.xml (the .hh files are saved automatically)\n\n"
                f"  2. Copy {files_str} to your CompLaB3D source root\n"
                "     (same directory as CMakeLists.txt)\n\n"
                "  3. The file names MUST be exactly:\n"
                "       defineKinetics.hh          (biotic kinetics)\n"
                "       defineAbioticKinetics.hh   (abiotic kinetics)\n"
                "     because the C++ solver has:\n"
                '       #include "../defineKinetics.hh"\n'
                '       #include "../defineAbioticKinetics.hh"\n'
                "     in src/complab3d_processors_part1.hh\n\n"
                "  4. Recompile the solver:\n"
                "       cd build\n"
                "       cmake ..\n"
                "       make -j$(nproc)          # Linux/Mac\n"
                "       cmake --build . --config Release  # Windows\n\n"
                "  5. Run with the newly compiled executable\n\n"
                "  NOTE: If you modify kinetics parameters later,\n"
                "  you must repeat steps 2-5 to recompile."
            )
        else:
            self._compile_hint.setText(
                "This template does not use kinetics reactions.\n"
                "No .hh files need to be compiled.\n"
                "You can run the simulation directly after exporting CompLaB.xml."
            )

    def _show_preview(self, kind: str):
        """Show a preview of the .hh source code."""
        info = get_kinetics_info(self._selected_key)
        if not info:
            return
        if kind == "biotic" and info.biotic_hh:
            self._preview_text.setPlainText(info.biotic_hh)
            self._preview_group.setTitle("Preview: defineKinetics.hh")
        elif kind == "abiotic" and info.abiotic_hh:
            self._preview_text.setPlainText(info.abiotic_hh)
            self._preview_group.setTitle("Preview: defineAbioticKinetics.hh")
        else:
            return
        self._preview_group.setVisible(True)

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
