"""Boundary conditions overview panel."""

from PySide6.QtWidgets import (
    QVBoxLayout, QLabel, QWidget, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel


class BoundaryPanel(BasePanel):

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

        layout.addWidget(self._create_heading("Boundary Conditions"))
        layout.addWidget(self._create_subheading(
            "Summary of all boundary conditions. Edit individual values in "
            "Chemistry and Microbiology panels."))

        tabs = QTabWidget()

        # Substrates BC table
        self._subs_table = QTableWidget()
        self._subs_table.setColumnCount(5)
        self._subs_table.setHorizontalHeaderLabels([
            "Substrate", "Inlet Type", "Inlet Value", "Outlet Type", "Outlet Value"
        ])
        self._subs_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._subs_table.setAlternatingRowColors(True)
        self._subs_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabs.addTab(self._subs_table, "Substrates")

        # Microbes BC table
        self._micro_table = QTableWidget()
        self._micro_table.setColumnCount(5)
        self._micro_table.setHorizontalHeaderLabels([
            "Microbe", "Inlet Type", "Inlet Value", "Outlet Type", "Outlet Value"
        ])
        self._micro_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._micro_table.setAlternatingRowColors(True)
        self._micro_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tabs.addTab(self._micro_table, "Microbes")

        # Flow BC info
        flow_w = QWidget()
        fl = QVBoxLayout(flow_w)
        fl.addWidget(QLabel("Flow Boundary Conditions"))
        fl.addWidget(self._create_separator())
        fl.addWidget(self._create_info_label(
            "Flow is driven by a pressure gradient (delta_P) applied across the domain.\n\n"
            "Inlet (left): Prescribed pressure\n"
            "Outlet (right): Prescribed pressure\n"
            "Walls (top/bottom/sides): No-slip bounce-back\n\n"
            "Adjust delta_P in the Solver panel to control flow velocity."))
        fl.addStretch()
        tabs.addTab(flow_w, "Flow")

        layout.addWidget(tabs, 1)

        outer.addWidget(self._create_scroll_area(w))

    def _populate_fields(self):
        if not self._project:
            return

        # Substrates
        subs = self._project.substrates
        self._subs_table.setRowCount(len(subs))
        for i, s in enumerate(subs):
            self._subs_table.setItem(i, 0, QTableWidgetItem(s.name))
            self._subs_table.setItem(i, 1, QTableWidgetItem(s.left_bc_type))
            self._subs_table.setItem(i, 2, QTableWidgetItem(f"{s.left_bc_value:.6g}"))
            self._subs_table.setItem(i, 3, QTableWidgetItem(s.right_bc_type))
            self._subs_table.setItem(i, 4, QTableWidgetItem(f"{s.right_bc_value:.6g}"))

        # Microbes
        mics = self._project.microbes
        self._micro_table.setRowCount(len(mics))
        for i, m in enumerate(mics):
            self._micro_table.setItem(i, 0, QTableWidgetItem(m.name))
            self._micro_table.setItem(i, 1, QTableWidgetItem(m.left_bc_type))
            self._micro_table.setItem(i, 2, QTableWidgetItem(f"{m.left_bc_value:.6g}"))
            self._micro_table.setItem(i, 3, QTableWidgetItem(m.right_bc_type))
            self._micro_table.setItem(i, 4, QTableWidgetItem(f"{m.right_bc_value:.6g}"))

    def collect_data(self, project):
        # This panel is read-only summary; actual data edited in Chemistry/Microbiology
        pass
