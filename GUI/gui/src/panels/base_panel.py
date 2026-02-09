"""
Base panel class and common utilities for configuration panels
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
    QCheckBox, QPushButton, QScrollArea, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont


class BasePanel(QWidget):
    """Base class for all configuration panels"""
    
    data_changed = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.project = None
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the panel UI - override in subclasses"""
        pass
        
    def set_project(self, project):
        """Set the project and populate fields"""
        self.project = project
        self._populate_fields()
        
    def _populate_fields(self):
        """Populate fields from project - override in subclasses"""
        pass
        
    def collect_data(self, project):
        """Collect data from fields into project - override in subclasses"""
        pass
        
    def _create_header(self, title: str, icon: str = "") -> QLabel:
        """Create a styled header label"""
        label = QLabel(f"{icon} {title}" if icon else title)
        label.setObjectName("panelHeader")
        font = QFont()
        font.setPointSize(14)
        font.setBold(True)
        label.setFont(font)
        return label
        
    def _create_group(self, title: str) -> QGroupBox:
        """Create a styled group box"""
        group = QGroupBox(title)
        group.setObjectName("configGroup")
        return group
        
    def _create_form_layout(self) -> QFormLayout:
        """Create a form layout with standard settings"""
        layout = QFormLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setLabelAlignment(Qt.AlignRight)
        return layout
        
    def _create_spin_box(self, min_val: int, max_val: int, value: int = 0) -> QSpinBox:
        """Create a styled spin box"""
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        spin.setMinimumWidth(100)
        spin.valueChanged.connect(lambda: self.data_changed.emit())
        return spin
        
    def _create_double_spin(self, min_val: float, max_val: float, value: float = 0.0,
                           decimals: int = 6, step: float = 0.1) -> QDoubleSpinBox:
        """Create a styled double spin box"""
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        spin.setMinimumWidth(120)
        spin.valueChanged.connect(lambda: self.data_changed.emit())
        return spin
        
    def _create_line_edit(self, text: str = "", placeholder: str = "") -> QLineEdit:
        """Create a styled line edit"""
        edit = QLineEdit(text)
        edit.setPlaceholderText(placeholder)
        edit.textChanged.connect(lambda: self.data_changed.emit())
        return edit
        
    def _create_combo_box(self, items: list, current: int = 0) -> QComboBox:
        """Create a styled combo box"""
        combo = QComboBox()
        combo.addItems(items)
        combo.setCurrentIndex(current)
        combo.currentIndexChanged.connect(lambda: self.data_changed.emit())
        return combo
        
    def _create_checkbox(self, text: str, checked: bool = False) -> QCheckBox:
        """Create a styled checkbox"""
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.stateChanged.connect(lambda: self.data_changed.emit())
        return cb
        
    def _create_scroll_area(self, widget: QWidget) -> QScrollArea:
        """Create a scroll area containing the widget"""
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        return scroll
        
    def _create_info_label(self, text: str) -> QLabel:
        """Create an info/hint label"""
        label = QLabel(text)
        label.setObjectName("infoLabel")
        label.setWordWrap(True)
        return label
        
    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        return line


class CollapsibleSection(QWidget):
    """A collapsible section widget"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        self.toggle_button = QPushButton(f"▼ {title}")
        self.toggle_button.setCheckable(True)
        self.toggle_button.setChecked(True)
        self.toggle_button.setObjectName("collapseButton")
        self.toggle_button.clicked.connect(self._toggle)
        
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(20, 5, 5, 5)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.toggle_button)
        layout.addWidget(self.content_area)
        
        self.title = title
        
    def _toggle(self):
        """Toggle visibility"""
        visible = self.toggle_button.isChecked()
        self.content_area.setVisible(visible)
        symbol = "▼" if visible else "▶"
        self.toggle_button.setText(f"{symbol} {self.title}")
        
    def add_widget(self, widget: QWidget):
        """Add widget to content area"""
        self.content_layout.addWidget(widget)
        
    def set_layout(self, layout):
        """Set content layout"""
        # Remove old layout
        QWidget().setLayout(self.content_area.layout())
        self.content_area.setLayout(layout)


class UnitSelector(QWidget):
    """Widget for value with unit selection"""
    
    value_changed = Signal(float, str)
    
    def __init__(self, units: list, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        self.spin = QDoubleSpinBox()
        self.spin.setRange(-1e20, 1e20)
        self.spin.setDecimals(6)
        self.spin.setMinimumWidth(100)
        
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(units)
        self.unit_combo.setMaximumWidth(80)
        
        layout.addWidget(self.spin, 1)
        layout.addWidget(self.unit_combo)
        
        self.spin.valueChanged.connect(self._emit_change)
        self.unit_combo.currentTextChanged.connect(self._emit_change)
        
    def _emit_change(self):
        self.value_changed.emit(self.spin.value(), self.unit_combo.currentText())
        
    def set_value(self, value: float, unit: str = None):
        """Set the value and optionally the unit"""
        self.spin.setValue(value)
        if unit:
            idx = self.unit_combo.findText(unit)
            if idx >= 0:
                self.unit_combo.setCurrentIndex(idx)
                
    def value(self) -> float:
        return self.spin.value()
        
    def unit(self) -> str:
        return self.unit_combo.currentText()


class ParameterTable(QTableWidget):
    """Table widget for parameter editing"""
    
    def __init__(self, headers: list, parent=None):
        super().__init__(parent)
        
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        
    def add_row(self, values: list):
        """Add a row with values"""
        row = self.rowCount()
        self.insertRow(row)
        for col, value in enumerate(values):
            item = QTableWidgetItem(str(value))
            self.setItem(row, col, item)
            
    def get_row_values(self, row: int) -> list:
        """Get values from a row"""
        values = []
        for col in range(self.columnCount()):
            item = self.item(row, col)
            values.append(item.text() if item else "")
        return values
        
    def clear_rows(self):
        """Clear all rows"""
        while self.rowCount() > 0:
            self.removeRow(0)
