"""Base panel class with common factory methods."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QGroupBox, QScrollArea, QFrame, QPushButton,
)
from PySide6.QtCore import Signal, Qt


class BasePanel(QWidget):
    data_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._project = None
        self._updating = False

    def set_project(self, project):
        self._project = project
        self._updating = True
        try:
            self._populate_fields()
        finally:
            self._updating = False

    def collect_data(self, project):
        """Override to write widget values back to project."""
        pass

    def _populate_fields(self):
        """Override to read project and fill widgets."""
        pass

    def _emit_changed(self):
        if not self._updating:
            self.data_changed.emit()

    # --- Factory methods ---

    @staticmethod
    def _create_heading(text):
        label = QLabel(text)
        label.setProperty("heading", True)
        return label

    @staticmethod
    def _create_subheading(text):
        label = QLabel(text)
        label.setProperty("subheading", True)
        return label

    @staticmethod
    def _create_section_label(text):
        label = QLabel(text)
        label.setProperty("section", True)
        return label

    @staticmethod
    def _create_info_label(text):
        label = QLabel(text)
        label.setProperty("info", True)
        label.setWordWrap(True)
        return label

    @staticmethod
    def _create_separator():
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        return line

    def _create_spin(self, min_val=0, max_val=999999, value=0, suffix=""):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        if suffix:
            spin.setSuffix(f" {suffix}")
        spin.setMinimumWidth(120)
        spin.valueChanged.connect(self._emit_changed)
        return spin

    def _create_double_spin(self, min_val=0.0, max_val=1e30, value=0.0,
                             decimals=6, step=0.1, suffix=""):
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(decimals)
        spin.setSingleStep(step)
        spin.setValue(value)
        if suffix:
            spin.setSuffix(f" {suffix}")
        spin.setMinimumWidth(150)
        spin.valueChanged.connect(self._emit_changed)
        return spin

    def _create_sci_spin(self, min_val=-1e30, max_val=1e30, value=0.0, decimals=10):
        """Double spin box for scientific notation values."""
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(decimals)
        spin.setValue(value)
        spin.setMinimumWidth(160)
        spin.valueChanged.connect(self._emit_changed)
        return spin

    def _create_line_edit(self, text="", placeholder=""):
        edit = QLineEdit(text)
        if placeholder:
            edit.setPlaceholderText(placeholder)
        edit.setMinimumWidth(150)
        edit.textChanged.connect(self._emit_changed)
        return edit

    def _create_combo(self, items, current=0):
        combo = QComboBox()
        combo.addItems(items)
        if isinstance(current, int):
            combo.setCurrentIndex(current)
        elif isinstance(current, str):
            idx = combo.findText(current)
            if idx >= 0:
                combo.setCurrentIndex(idx)
        combo.currentIndexChanged.connect(self._emit_changed)
        return combo

    def _create_checkbox(self, text, checked=False):
        cb = QCheckBox(text)
        cb.setChecked(checked)
        cb.stateChanged.connect(self._emit_changed)
        return cb

    def _create_group(self, title):
        group = QGroupBox(title)
        return group

    @staticmethod
    def _create_form():
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)
        return form

    @staticmethod
    def _create_scroll_area(widget):
        scroll = QScrollArea()
        scroll.setWidget(widget)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        return scroll
