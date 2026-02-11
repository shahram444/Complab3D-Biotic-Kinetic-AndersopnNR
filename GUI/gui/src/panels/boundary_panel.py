"""
Boundary Conditions Panel - Configure inlet/outlet conditions
Fixed styling for visibility and correct enum values
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QComboBox, QDoubleSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QFrame, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from .base_panel import BasePanel
from ..core.project import BoundaryCondition, BoundaryType


class BoundaryConditionsPanel(BasePanel):
    """Panel for configuring boundary conditions"""
    
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Header
        header = self._create_header("Boundary Conditions", "🔲")
        main_layout.addWidget(header)
        
        # Description
        desc = self._create_info_label(
            "Configure inlet (left) and outlet (right) boundary conditions for "
            "substrates, microbes, and flow. Dirichlet sets a fixed value, "
            "Neumann sets a fixed flux (gradient)."
        )
        main_layout.addWidget(desc)
        
        # Tabs for different BC types
        self.bc_tabs = QTabWidget()
        
        # Substrates BC tab
        substrates_tab = QWidget()
        substrates_layout = QVBoxLayout(substrates_tab)
        self.substrates_table = self._create_bc_table("substrate")
        substrates_layout.addWidget(self.substrates_table)
        self.bc_tabs.addTab(substrates_tab, "Substrates")
        
        # Microbes BC tab
        microbes_tab = QWidget()
        microbes_layout = QVBoxLayout(microbes_tab)
        self.microbes_table = self._create_bc_table("microbe")
        microbes_layout.addWidget(self.microbes_table)
        self.bc_tabs.addTab(microbes_tab, "Microbes")
        
        # Flow BC tab
        flow_tab = QWidget()
        flow_layout = QVBoxLayout(flow_tab)
        self._create_flow_bc(flow_layout)
        self.bc_tabs.addTab(flow_tab, "Flow")
        
        main_layout.addWidget(self.bc_tabs)
        
        # Legend
        legend_group = self._create_group("Boundary Condition Types")
        legend_layout = QVBoxLayout()
        
        legend_text = QLabel(
            "<b>Dirichlet:</b> Fixed value at boundary (e.g., concentration = 1.0)<br>"
            "<b>Neumann:</b> Fixed flux/gradient at boundary (e.g., ∂C/∂x = 0 for no-flux)"
        )
        legend_text.setWordWrap(True)
        legend_layout.addWidget(legend_text)
        
        legend_group.setLayout(legend_layout)
        main_layout.addWidget(legend_group)
        
        main_layout.addStretch()
        
    def _create_bc_table(self, bc_type):
        """Create a table for boundary conditions with proper styling"""
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Name" if bc_type == "substrate" else "Microbe",
            "Inlet Type", "Inlet Value", 
            "Outlet Type", "Outlet Value"
        ])
        
        # Set column widths
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        # Style the table for dark theme visibility
        table.setStyleSheet("""
            QTableWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                gridline-color: #444444;
                border: 1px solid #444444;
            }
            QTableWidget::item {
                padding: 5px;
                color: #ffffff;
                background-color: #2d2d2d;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QHeaderView::section {
                background-color: #3d3d3d;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #444444;
                font-weight: bold;
            }
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
                border: 1px solid #555555;
            }
            QDoubleSpinBox, QSpinBox, QLineEdit {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
            }
            QDoubleSpinBox:hover, QSpinBox:hover, QLineEdit:hover {
                border: 1px solid #0078d4;
            }
        """)
        
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.verticalHeader().setVisible(False)
        
        return table
        
    def _create_bc_combo(self):
        """Create a styled combo box for BC type"""
        combo = QComboBox()
        # Use the enum VALUES (title case), not the enum NAMES (uppercase)
        combo.addItems(["Dirichlet", "Neumann"])
        combo.setStyleSheet("""
            QComboBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #0078d4;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QComboBox QAbstractItemView {
                background-color: #3d3d3d;
                color: #ffffff;
                selection-background-color: #0078d4;
                selection-color: #ffffff;
                border: 1px solid #555555;
            }
        """)
        return combo
        
    def _create_bc_spinbox(self, value=0.0):
        """Create a styled spin box for BC value"""
        spin = QDoubleSpinBox()
        spin.setRange(-1e10, 1e10)
        spin.setDecimals(6)
        spin.setValue(value)
        spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #3d3d3d;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                min-width: 80px;
            }
            QDoubleSpinBox:hover {
                border: 1px solid #0078d4;
            }
        """)
        return spin
        
    def _create_flow_bc(self, layout):
        """Create flow boundary conditions section"""
        info = self._create_info_label(
            "Flow boundary conditions are controlled by the pressure gradient (Delta P) "
            "in the Solver settings. Inlet and outlet use pressure-driven flow."
        )
        layout.addWidget(info)
        
        # Flow BC group
        flow_group = self._create_group("Flow Boundary Settings")
        flow_layout = QFormLayout()
        
        # Inlet
        inlet_label = QLabel("Pressure-driven inlet (x = 0)")
        inlet_label.setStyleSheet("color: #88ff88;")
        flow_layout.addRow("Inlet:", inlet_label)
        
        # Outlet
        outlet_label = QLabel("Pressure-driven outlet (x = Lx)")
        outlet_label.setStyleSheet("color: #88ff88;")
        flow_layout.addRow("Outlet:", outlet_label)
        
        # Walls
        wall_label = QLabel("No-slip walls (y, z boundaries)")
        wall_label.setStyleSheet("color: #ffff88;")
        flow_layout.addRow("Walls:", wall_label)
        
        flow_group.setLayout(flow_layout)
        layout.addWidget(flow_group)
        
        layout.addStretch()
        
    def _populate_fields(self):
        """Populate tables with project data"""
        if not self.project:
            return
            
        # Populate substrates table
        self.substrates_table.setRowCount(len(self.project.substrates))
        for i, substrate in enumerate(self.project.substrates):
            # Name
            name_item = QTableWidgetItem(substrate.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            name_item.setForeground(QColor("#ffffff"))
            self.substrates_table.setItem(i, 0, name_item)
            
            # Inlet type - use .value to get the string value from enum
            inlet_type_combo = self._create_bc_combo()
            inlet_type_combo.setCurrentText(substrate.left_boundary.bc_type.value)
            self.substrates_table.setCellWidget(i, 1, inlet_type_combo)
            
            # Inlet value
            inlet_value_spin = self._create_bc_spinbox(substrate.left_boundary.value)
            self.substrates_table.setCellWidget(i, 2, inlet_value_spin)
            
            # Outlet type - use .value to get the string value from enum
            outlet_type_combo = self._create_bc_combo()
            outlet_type_combo.setCurrentText(substrate.right_boundary.bc_type.value)
            self.substrates_table.setCellWidget(i, 3, outlet_type_combo)
            
            # Outlet value
            outlet_value_spin = self._create_bc_spinbox(substrate.right_boundary.value)
            self.substrates_table.setCellWidget(i, 4, outlet_value_spin)
            
        # Populate microbes table
        self.microbes_table.setRowCount(len(self.project.microbes))
        for i, microbe in enumerate(self.project.microbes):
            # Name
            name_item = QTableWidgetItem(microbe.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            name_item.setForeground(QColor("#ffffff"))
            self.microbes_table.setItem(i, 0, name_item)
            
            # Inlet type
            inlet_type_combo = self._create_bc_combo()
            inlet_type_combo.setCurrentText(microbe.left_boundary.bc_type.value)
            self.microbes_table.setCellWidget(i, 1, inlet_type_combo)
            
            # Inlet value
            inlet_value_spin = self._create_bc_spinbox(microbe.left_boundary.value)
            self.microbes_table.setCellWidget(i, 2, inlet_value_spin)
            
            # Outlet type
            outlet_type_combo = self._create_bc_combo()
            outlet_type_combo.setCurrentText(microbe.right_boundary.bc_type.value)
            self.microbes_table.setCellWidget(i, 3, outlet_type_combo)
            
            # Outlet value
            outlet_value_spin = self._create_bc_spinbox(microbe.right_boundary.value)
            self.microbes_table.setCellWidget(i, 4, outlet_value_spin)
            
    def collect_data(self, project):
        """Collect BC data from tables into project"""
        if not project:
            return
            
        # Collect substrate BCs
        for i, substrate in enumerate(project.substrates):
            if i < self.substrates_table.rowCount():
                # Inlet
                inlet_type_widget = self.substrates_table.cellWidget(i, 1)
                inlet_value_widget = self.substrates_table.cellWidget(i, 2)
                if inlet_type_widget and inlet_value_widget:
                    # Convert string to BoundaryType enum
                    bc_type = BoundaryType(inlet_type_widget.currentText())
                    substrate.left_boundary = BoundaryCondition(bc_type, inlet_value_widget.value())
                
                # Outlet
                outlet_type_widget = self.substrates_table.cellWidget(i, 3)
                outlet_value_widget = self.substrates_table.cellWidget(i, 4)
                if outlet_type_widget and outlet_value_widget:
                    bc_type = BoundaryType(outlet_type_widget.currentText())
                    substrate.right_boundary = BoundaryCondition(bc_type, outlet_value_widget.value())
                    
        # Collect microbe BCs
        for i, microbe in enumerate(project.microbes):
            if i < self.microbes_table.rowCount():
                # Inlet
                inlet_type_widget = self.microbes_table.cellWidget(i, 1)
                inlet_value_widget = self.microbes_table.cellWidget(i, 2)
                if inlet_type_widget and inlet_value_widget:
                    bc_type = BoundaryType(inlet_type_widget.currentText())
                    microbe.left_boundary = BoundaryCondition(bc_type, inlet_value_widget.value())
                
                # Outlet
                outlet_type_widget = self.microbes_table.cellWidget(i, 3)
                outlet_value_widget = self.microbes_table.cellWidget(i, 4)
                if outlet_type_widget and outlet_value_widget:
                    bc_type = BoundaryType(outlet_type_widget.currentText())
                    microbe.right_boundary = BoundaryCondition(bc_type, outlet_value_widget.value())
