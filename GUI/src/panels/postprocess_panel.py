"""Post-processing panel - output file browsing and results."""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton,
    QGroupBox, QListWidget, QListWidgetItem, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel


class PostProcessPanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("Post-Processing"))
        layout.addWidget(self._create_subheading(
            "Browse output files and view simulation results."))

        tabs = QTabWidget()

        # --- Output Files Tab ---
        files_w = QWidget()
        fl = QVBoxLayout(files_w)

        btn_row = QHBoxLayout()
        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._refresh_files)
        self._open_dir_btn = QPushButton("Open Output Directory")
        self._open_dir_btn.clicked.connect(self._open_output_dir)
        btn_row.addWidget(self._refresh_btn)
        btn_row.addWidget(self._open_dir_btn)
        btn_row.addStretch()
        fl.addLayout(btn_row)

        self._file_list = QListWidget()
        fl.addWidget(self._file_list)

        self._file_info = QLabel("")
        self._file_info.setProperty("info", True)
        self._file_info.setWordWrap(True)
        fl.addWidget(self._file_info)

        tabs.addTab(files_w, "Output Files")

        # --- Summary Tab ---
        summary_w = QWidget()
        sl = QVBoxLayout(summary_w)

        self._summary_table = QTableWidget()
        self._summary_table.setColumnCount(2)
        self._summary_table.setHorizontalHeaderLabels(["Property", "Value"])
        self._summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._summary_table.setAlternatingRowColors(True)
        self._summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        sl.addWidget(self._summary_table)

        tabs.addTab(summary_w, "Summary")

        # --- Export Tab ---
        export_w = QWidget()
        el = QVBoxLayout(export_w)

        self._export_csv_btn = QPushButton("Export Data to CSV")
        self._export_csv_btn.clicked.connect(self._export_csv)
        el.addWidget(self._export_csv_btn)

        el.addWidget(self._create_info_label(
            "For advanced visualization, open .vti files directly in ParaView.\n"
            "VTK ImageData files contain all field variables at each saved timestep."))
        el.addStretch()

        tabs.addTab(export_w, "Export")

        layout.addWidget(tabs, 1)
        outer.addWidget(self._create_scroll_area(w))

    def _refresh_files(self):
        self._file_list.clear()
        if not self._project or not self._project.project_dir:
            return

        output_dir = Path(self._project.project_dir) / self._project.paths.output_path
        if not output_dir.is_dir():
            self._file_info.setText("Output directory does not exist yet.")
            return

        files = sorted(output_dir.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
        vti_count = 0
        chk_count = 0
        for f in files:
            if f.is_file():
                suffix = f.suffix.lower()
                size_kb = f.stat().st_size / 1024
                label = f"{f.name}  ({size_kb:.0f} KB)"
                self._file_list.addItem(label)
                if suffix == ".vti":
                    vti_count += 1
                elif suffix in (".dat", ".chk"):
                    chk_count += 1

        self._file_info.setText(
            f"Total files: {len(files)}  |  VTI: {vti_count}  |  Checkpoints: {chk_count}")

        # Update summary
        self._update_summary(output_dir, len(files), vti_count)

    def _update_summary(self, output_dir, total, vti_count):
        rows = [
            ("Output directory", str(output_dir)),
            ("Total files", str(total)),
            ("VTK files", str(vti_count)),
        ]
        self._summary_table.setRowCount(len(rows))
        for i, (prop, val) in enumerate(rows):
            self._summary_table.setItem(i, 0, QTableWidgetItem(prop))
            self._summary_table.setItem(i, 1, QTableWidgetItem(val))

    def _open_output_dir(self):
        if not self._project or not self._project.project_dir:
            return
        output_dir = Path(self._project.project_dir) / self._project.paths.output_path
        if output_dir.is_dir():
            import subprocess
            import sys
            if sys.platform == "win32":
                os.startfile(str(output_dir))
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(output_dir)])
            else:
                subprocess.Popen(["xdg-open", str(output_dir)])

    def _export_csv(self):
        from PySide6.QtWidgets import QFileDialog
        if not self._project:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CSV", "results.csv",
            "CSV Files (*.csv);;All Files (*)")
        if not path:
            return
        # Export summary table
        with open(path, "w") as f:
            for i in range(self._summary_table.rowCount()):
                prop = self._summary_table.item(i, 0)
                val = self._summary_table.item(i, 1)
                if prop and val:
                    f.write(f"{prop.text()},{val.text()}\n")

    def _populate_fields(self):
        self._refresh_files()

    def collect_data(self, project):
        pass
