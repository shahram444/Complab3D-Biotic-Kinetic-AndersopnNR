"""Base panel class with factory methods for consistent widget creation."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox,
    QPushButton, QScrollArea, QFrame, QGroupBox, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal


class BasePanel(QWidget):
    """Base for all right-side settings panels.

    Provides factory methods for uniform widget styling
    and a scroll area for content that may exceed panel height.
    """

    data_changed = Signal()

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._title = title
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)

        # Scroll area wrapping content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameStyle(QFrame.Shape.NoFrame)

        self._content = QWidget()
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(10, 6, 10, 6)
        self._content_layout.setSpacing(6)

        if title:
            heading = QLabel(title)
            heading.setProperty("heading", True)
            self._content_layout.addWidget(heading)

        scroll.setWidget(self._content)
        self._main_layout.addWidget(scroll)

    def add_section(self, title: str) -> QLabel:
        lbl = QLabel(title)
        lbl.setProperty("section", True)
        self._content_layout.addWidget(lbl)
        return lbl

    def add_form(self) -> QFormLayout:
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setHorizontalSpacing(10)
        form.setVerticalSpacing(5)
        self._content_layout.addLayout(form)
        return form

    def add_group(self, title: str) -> QGroupBox:
        group = QGroupBox(title)
        self._content_layout.addWidget(group)
        return group

    def add_stretch(self):
        self._content_layout.addStretch()

    def add_separator(self):
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        self._content_layout.addWidget(line)

    def add_widget(self, widget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    # ── Factory methods ─────────────────────────────────────────────

    @staticmethod
    def make_line_edit(text: str = "", placeholder: str = "",
                       readonly: bool = False) -> QLineEdit:
        w = QLineEdit(text)
        w.setPlaceholderText(placeholder)
        w.setReadOnly(readonly)
        return w

    @staticmethod
    def make_spin(value: int = 0, min_val: int = 0,
                  max_val: int = 999999999, suffix: str = "") -> QSpinBox:
        w = QSpinBox()
        w.setRange(min_val, max_val)
        w.setValue(value)
        if suffix:
            w.setSuffix(f" {suffix}")
        return w

    @staticmethod
    def make_double_spin(value: float = 0.0, min_val: float = -1e30,
                         max_val: float = 1e30, decimals: int = 6,
                         suffix: str = "", step: float = 0.0) -> QDoubleSpinBox:
        w = QDoubleSpinBox()
        w.setDecimals(decimals)
        w.setRange(min_val, max_val)
        w.setValue(value)
        if suffix:
            w.setSuffix(f" {suffix}")
        if step > 0:
            w.setSingleStep(step)
        return w

    @staticmethod
    def make_combo(items: list, current: int = 0) -> QComboBox:
        w = QComboBox()
        w.addItems(items)
        if 0 <= current < len(items):
            w.setCurrentIndex(current)
        return w

    @staticmethod
    def make_checkbox(text: str = "", checked: bool = False) -> QCheckBox:
        w = QCheckBox(text)
        w.setChecked(checked)
        return w

    @staticmethod
    def make_button(text: str, primary: bool = False) -> QPushButton:
        w = QPushButton(text)
        if primary:
            w.setProperty("primary", True)
        return w

    @staticmethod
    def make_info_label(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("info", True)
        lbl.setWordWrap(True)
        return lbl

    @staticmethod
    def set_validation(widget, state: str, tooltip: str = ""):
        """Mark a widget's validation state for QSS styling.

        Args:
            widget: The input widget (QLineEdit, QSpinBox, etc.)
            state: "error", "warning", "ok", or "" to clear
            tooltip: Optional tooltip message explaining the issue
        """
        widget.setProperty("validation", state or "")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
        if tooltip:
            widget.setToolTip(tooltip)

    @staticmethod
    def clear_validation(widget):
        """Remove validation styling from a widget."""
        widget.setProperty("validation", "")
        widget.style().unpolish(widget)
        widget.style().polish(widget)
