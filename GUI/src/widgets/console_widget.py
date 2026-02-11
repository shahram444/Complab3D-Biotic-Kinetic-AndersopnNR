"""Console output widget with color-coded messages and run controls."""

import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QProgressBar, QFileDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QColor


class ConsoleWidget(QWidget):
    """Bottom panel: console log + progress bar + run controls."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._max_lines = 10000
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(6, 2, 6, 2)
        lbl = QLabel("Messages")
        lbl.setProperty("subheading", True)
        header.addWidget(lbl)
        header.addStretch()

        self._progress = QProgressBar()
        self._progress.setFixedWidth(200)
        self._progress.setTextVisible(True)
        self._progress.setValue(0)
        self._progress.setVisible(False)
        header.addWidget(self._progress)

        self._status_lbl = QLabel("Ready")
        self._status_lbl.setProperty("info", True)
        self._status_lbl.setFixedWidth(200)
        self._status_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self._status_lbl)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.setFixedWidth(60)
        self._clear_btn.clicked.connect(self.clear)
        header.addWidget(self._clear_btn)

        self._save_btn = QPushButton("Save Log")
        self._save_btn.setFixedWidth(70)
        self._save_btn.clicked.connect(self._save_log)
        header.addWidget(self._save_btn)

        layout.addLayout(header)

        # Text area
        self._text = QTextEdit()
        self._text.setReadOnly(True)
        self._text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        layout.addWidget(self._text)

    def append(self, text: str, color: str = None):
        """Append a line to the console."""
        if color:
            html = f'<span style="color:{color}">{_escape(text)}</span>'
        else:
            # Auto-color based on content
            lower = text.lower()
            if "error" in lower or "fail" in lower or "terminat" in lower:
                html = f'<span style="color:#c75050">{_escape(text)}</span>'
            elif "warning" in lower or "warn" in lower:
                html = f'<span style="color:#c0a040">{_escape(text)}</span>'
            elif text.startswith("--") or text.startswith("=="):
                html = f'<span style="color:#6a9ec7">{_escape(text)}</span>'
            else:
                html = _escape(text)

        cursor = self._text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self._text.setTextCursor(cursor)
        self._text.append(html)

        # Trim old lines
        doc = self._text.document()
        if doc.blockCount() > self._max_lines:
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.movePosition(
                QTextCursor.MoveOperation.Down,
                QTextCursor.MoveMode.KeepAnchor,
                doc.blockCount() - self._max_lines
            )
            cursor.removeSelectedText()

    def log_info(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.append(f"[{ts}] {text}")

    def log_error(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.append(f"[{ts}] ERROR: {text}", "#c75050")

    def log_success(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.append(f"[{ts}] {text}", "#5ca060")

    def set_progress(self, current: int, maximum: int):
        if maximum > 0:
            self._progress.setVisible(True)
            self._progress.setMaximum(maximum)
            self._progress.setValue(current)
        else:
            self._progress.setVisible(False)

    def set_status(self, text: str):
        self._status_lbl.setText(text)

    def clear(self):
        self._text.clear()

    def set_max_lines(self, n: int):
        self._max_lines = n

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Console Log", "console_log.txt",
            "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "w") as f:
                f.write(self._text.toPlainText())


def _escape(text: str) -> str:
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace(" ", "&nbsp;"))
