"""Console output widget with color-coded messages."""

import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QFileDialog,
)
from PySide6.QtGui import QTextCursor, QColor
from PySide6.QtCore import Qt


class ConsoleWidget(QWidget):

    MAX_LINES = 10000

    def __init__(self, parent=None):
        super().__init__(parent)
        self._line_count = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(4, 2, 4, 2)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.clicked.connect(self.clear)

        self._save_btn = QPushButton("Save Log")
        self._save_btn.setFixedWidth(70)
        self._save_btn.clicked.connect(self._save_log)

        toolbar.addStretch()
        toolbar.addWidget(self._clear_btn)
        toolbar.addWidget(self._save_btn)

        self._output = QTextEdit()
        self._output.setReadOnly(True)
        self._output.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        self._output.setAcceptRichText(True)

        layout.addLayout(toolbar)
        layout.addWidget(self._output)

    def append(self, text, level="info"):
        color_map = {
            "info": "#888888",
            "output": "#cccccc",
            "success": "#4ec9b0",
            "warning": "#cca700",
            "error": "#f44747",
        }
        color = color_map.get(level, "#cccccc")
        # Auto-detect level from content
        if level == "info":
            lower = text.lower()
            if "[error]" in lower or "error" in lower:
                color = color_map["error"]
            elif "[warning]" in lower or "warning" in lower:
                color = color_map["warning"]
            elif "converge" in lower or "completed" in lower:
                color = color_map["success"]

        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        html = f'<span style="color:#555555">{timestamp}</span> <span style="color:{color}">{_escape(text)}</span>'
        self._output.append(html)
        self._line_count += 1

        if self._line_count > self.MAX_LINES:
            self._trim()

        self._output.moveCursor(QTextCursor.MoveOperation.End)

    def append_output(self, text):
        """Append simulation output, auto-detecting log level."""
        self.append(text, "info")

    def clear(self):
        self._output.clear()
        self._line_count = 0

    def _trim(self):
        cursor = self._output.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        cursor.movePosition(
            QTextCursor.MoveOperation.Down,
            QTextCursor.MoveMode.KeepAnchor,
            self._line_count - self.MAX_LINES,
        )
        cursor.removeSelectedText()
        self._line_count = self.MAX_LINES

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Console Log", "console.log",
            "Log Files (*.log);;Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "w") as f:
                f.write(self._output.toPlainText())


def _escape(text):
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace(" ", "&nbsp;"))
