"""Post-processing panel - output file browsing, VTK viewing, and results."""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout, QFormLayout, QPushButton, QListWidget, QLabel,
    QFileDialog, QComboBox,
)
from PySide6.QtCore import Signal
from .base_panel import BasePanel


class PostProcessPanel(BasePanel):
    """Browse and visualize output files from completed simulations."""

    file_selected = Signal(str)  # VTI/VTK file path
    remove_vtk_requested = Signal()  # Remove loaded VTK from viewer

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

        self.add_section("File Filter")
        fform = self.add_form()
        self._filter_combo = QComboBox()
        self._filter_combo.addItems([
            "All VTK files (*.vti, *.vtk)",
            "VTI files only (*.vti)",
            "VTK legacy files only (*.vtk)",
            "Substrate fields",
            "Biomass fields",
            "Velocity fields",
            "Mask / Geometry",
        ])
        self._filter_combo.currentIndexChanged.connect(self._refresh_files)
        fform.addRow("Show:", self._filter_combo)

        self.add_section("Output Files")
        self._file_list = QListWidget()
        self._file_list.setMinimumHeight(200)
        self._file_list.currentTextChanged.connect(self._on_file_selected)
        self.add_widget(self._file_list)

        row2 = QHBoxLayout()
        refresh_btn = self.make_button("Refresh")
        refresh_btn.clicked.connect(self._refresh_files)
        row2.addWidget(refresh_btn)

        load_btn = self.make_button("Load in Viewer", primary=True)
        load_btn.setToolTip("Load selected file into the 3D viewer")
        load_btn.clicked.connect(self._load_selected)
        row2.addWidget(load_btn)

        remove_btn = self.make_button("Remove from Viewer")
        remove_btn.setProperty("danger", True)
        remove_btn.setToolTip("Remove currently loaded VTK data from the 3D viewer")
        remove_btn.clicked.connect(self.remove_vtk_requested.emit)
        row2.addWidget(remove_btn)

        row2.addStretch()
        self.add_layout(row2)

        self.add_section("File Information")
        self._info_lbl = self.make_info_label("Select an output file to view details.")
        self.add_widget(self._info_lbl)

        self._file_count_lbl = QLabel("")
        self._file_count_lbl.setProperty("info", True)
        self.add_widget(self._file_count_lbl)

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

        filter_idx = self._filter_combo.currentIndex()
        out_dir = Path(self._output_dir)

        files = []
        if filter_idx in (0, 1):
            files.extend(sorted(out_dir.glob("*.vti")))
        if filter_idx in (0, 2):
            files.extend(sorted(out_dir.glob("*.vtk")))
        if filter_idx == 3:  # Substrate
            files = sorted(out_dir.glob("*subs*.vti")) + sorted(out_dir.glob("*substrate*.vti"))
        elif filter_idx == 4:  # Biomass
            files = sorted(out_dir.glob("*bio*.vti")) + sorted(out_dir.glob("*biomass*.vti"))
        elif filter_idx == 5:  # Velocity
            files = sorted(out_dir.glob("*vel*.vti")) + sorted(out_dir.glob("*ns*.vti")) + \
                    sorted(out_dir.glob("*velocity*.vtk"))
        elif filter_idx == 6:  # Mask
            files = sorted(out_dir.glob("*mask*.vti")) + sorted(out_dir.glob("*geom*.vti"))

        for f in files:
            self._file_list.addItem(f.name)

        count = self._file_list.count()
        if count == 0:
            self._file_count_lbl.setText("No matching files found.")
        else:
            self._file_count_lbl.setText(f"{count} file(s) found.")

    def _on_file_selected(self, name):
        if not name:
            return
        path = os.path.join(self._output_dir, name)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1048576:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / 1048576:.1f} MB"

            ext = Path(name).suffix.lower()
            ftype = "VTK ImageData" if ext == ".vti" else "VTK Legacy" if ext == ".vtk" else ext

            self._info_lbl.setText(
                f"File: {name}\n"
                f"Type: {ftype}\n"
                f"Size: {size_str}\n"
                f"Path: {path}")

    def _load_selected(self):
        """Load the currently selected file into the 3D viewer."""
        name = self._file_list.currentItem()
        if name:
            path = os.path.join(self._output_dir, name.text())
            if os.path.isfile(path):
                self.file_selected.emit(path)

    def set_output_directory(self, directory: str):
        self._output_dir = directory
        self._dir_edit.setText(directory)
        self._refresh_files()
