"""Collapsible section widget for advanced options."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QSizePolicy, QFrame,
)
from PySide6.QtCore import Qt, QPropertyAnimation, QParallelAnimationGroup


class CollapsibleSection(QWidget):
    """A section with a clickable header that expands/collapses content.

    Usage:
        section = CollapsibleSection("Advanced Options")
        layout = QFormLayout()
        layout.addRow("Param:", QLineEdit())
        section.set_content_layout(layout)
    """

    def __init__(self, title: str = "Advanced", expanded: bool = False, parent=None):
        super().__init__(parent)

        self._toggle_btn = QPushButton(f"  {title}")
        self._toggle_btn.setProperty("collapsible", True)
        self._toggle_btn.setCheckable(True)
        self._toggle_btn.setChecked(expanded)
        self._toggle_btn.setStyleSheet("")  # Use QSS from theme
        self._toggle_btn.clicked.connect(self._toggle)

        self._content = QWidget()
        self._content.setVisible(expanded)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self._toggle_btn)
        main_layout.addWidget(self._content)

        self._update_arrow()

    def set_content_layout(self, layout):
        """Set the layout for the collapsible content area."""
        old = self._content.layout()
        if old:
            # Remove old layout
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
        self._content.setLayout(layout)

    def _toggle(self, checked):
        self._content.setVisible(checked)
        self._update_arrow()

    def _update_arrow(self):
        title = self._toggle_btn.text().lstrip()
        # Remove existing arrow prefix
        for prefix in (">> ", "vv ", "\u25b6 ", "\u25bc "):
            if title.startswith(prefix):
                title = title[len(prefix):]
        if self._toggle_btn.isChecked():
            self._toggle_btn.setText(f"  \u25bc {title}")
        else:
            self._toggle_btn.setText(f"  \u25b6 {title}")

    def is_expanded(self) -> bool:
        return self._toggle_btn.isChecked()

    def set_expanded(self, expanded: bool):
        self._toggle_btn.setChecked(expanded)
        self._content.setVisible(expanded)
        self._update_arrow()
