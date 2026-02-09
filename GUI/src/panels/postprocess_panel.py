"""Post-processing panel - output file browsing and results."""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout, QFormLayout, QPushButton, QListWidget,
    QFileDialog,
)
from PySide6.QtCore import Signal
from .base_panel import BasePanel


class PostProcessPanel(BasePanel):
    """Browse and visualize output files from completed simulations."""

    file_selected = Signal(str)  # VTI file path

    def __init__(self, parent=None):
        super().__init__("Post-Processing", parent)
        self._output_dir = ""
        self._build_ui()

    def _build_ui(self):
        self.add_section("Output Directory")
        form = self.add_form()

        row = QHBoxLayout()
        self._dir_edit = self.make_line_edit("", "Select output directory")
        self._dir_edit.setReadOnly(True)
        browse_btn = QPushButton("Browse")
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self._browse_dir)
        row.addWidget(self._dir_edit, 1)
        row.addWidget(browse_btn)
        form.addRow("Directory:", row)

        self.add_section("VTK Output Files")
        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(200)
        self._file_list.currentTextChanged.connect(self._on_file_selected)
        self.add_widget(self._file_list)

        row2 = QHBoxLayout()
        refresh_btn = self.make_button("Refresh")
        refresh_btn.clicked.connect(self._refresh_files)
        row2.addWidget(refresh_btn)
        row2.addStretch()
        self.add_layout(row2)

        self.add_section("File Info")
        self._info_lbl = self.make_info_label("Select an output file to view details.")
        self.add_widget(self._info_lbl)

        self.add_stretch()

    def _browse_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self._output_dir)
        if d:
            self._output_dir = d
            self._dir_edit.setText(d)
            self._refresh_files()

    def _refresh_files(self):
        self._file_list.clear()
        if not self._output_dir or not os.path.isdir(self._output_dir):
            return
        vti_files = sorted(Path(self._output_dir).glob("*.vti"))
        for f in vti_files:
            self._file_list.addItem(f.name)

        vtk_files = sorted(Path(self._output_dir).glob("*.vtk"))
        for f in vtk_files:
            self._file_list.addItem(f.name)

        if self._file_list.count() == 0:
            self._info_lbl.setText("No VTK files found in directory.")
        else:
            self._info_lbl.setText(f"Found {self._file_list.count()} output files.")

    def _on_file_selected(self, name):
        if not name:
            return
        path = os.path.join(self._output_dir, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            size_str = f"{size / 1024:.1f} KB" if size < 1048576 else f"{size / 1048576:.1f} MB"
            self._info_lbl.setText(f"File: {name}\nSize: {size_str}")
            self.file_selected.emit(path)

    def set_output_directory(self, directory: str):
        self._output_dir = directory
        self._dir_edit.setText(directory)
        self._refresh_files()
