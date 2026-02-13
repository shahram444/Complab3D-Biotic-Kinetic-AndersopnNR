"""Console output widget with color-coded messages, search, and run controls."""

import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QProgressBar, QFileDialog, QLineEdit,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor, QColor, QTextDocument


class ConsoleWidget(QWidget):
    """Bottom panel: console log + progress bar + search + run controls."""

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

        # Search bar
        search_bar = QHBoxLayout()
        search_bar.setContentsMargins(6, 2, 6, 2)

        search_icon = QLabel("Search:")
        search_icon.setProperty("info", True)
        search_bar.addWidget(search_icon)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("Type to search console output...")
        self._search_edit.setFixedHeight(24)
        self._search_edit.setClearButtonEnabled(True)
        self._search_edit.returnPressed.connect(self._search_next)
        search_bar.addWidget(self._search_edit, 1)

        self._search_prev_btn = QPushButton("Prev")
        self._search_prev_btn.setFixedWidth(50)
        self._search_prev_btn.clicked.connect(self._search_prev)
        search_bar.addWidget(self._search_prev_btn)

        self._search_next_btn = QPushButton("Next")
        self._search_next_btn.setFixedWidth(50)
        self._search_next_btn.clicked.connect(self._search_next)
        search_bar.addWidget(self._search_next_btn)

        self._search_count = QLabel("")
        self._search_count.setProperty("info", True)
        self._search_count.setFixedWidth(80)
        search_bar.addWidget(self._search_count)

        layout.addLayout(search_bar)

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

    def log_warning(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.append(f"[{ts}] WARNING: {text}", "#c0a040")

    def log_success(self, text: str):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.append(f"[{ts}] {text}", "#5ca060")

    def log_diagnostic(self, report: str):
        """Append a multi-line diagnostic report with color coding."""
        for line in report.split("\n"):
            lower = line.lower()
            if line.startswith("=") or line.startswith("-" * 10):
                self.append(line, "#c0a040")
            elif "error" in lower or "reason:" in lower:
                self.append(line, "#c75050")
            elif "suggested fix" in lower or "how to fix" in lower or "checklist" in lower:
                self.append(line, "#6a9ec7")
            elif line.strip().startswith(("1.", "2.", "3.", "4.", "5.", "6.", "7.", "8.", "9.")):
                self.append(line, "#6a9ec7")
            elif line.strip().startswith("- ") or line.strip().startswith("[ ]"):
                self.append(line, "#6a9ec7")
            elif "detected" in lower:
                self.append(line, "#c0a040")
            elif line.strip().startswith(">>"):
                self.append(line, "#c75050")
            else:
                self.append(line)

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
        self._search_count.setText("")

    def set_max_lines(self, n: int):
        self._max_lines = n

    # ── Search ──────────────────────────────────────────────────────

    def _search_next(self):
        """Find next occurrence of search text."""
        query = self._search_edit.text()
        if not query:
            self._search_count.setText("")
            return
        found = self._text.find(query)
        if not found:
            # Wrap around to beginning
            cursor = self._text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            self._text.setTextCursor(cursor)
            found = self._text.find(query)
        self._update_search_count(query)

    def _search_prev(self):
        """Find previous occurrence of search text."""
        query = self._search_edit.text()
        if not query:
            self._search_count.setText("")
            return
        found = self._text.find(query, QTextDocument.FindFlag.FindBackward)
        if not found:
            # Wrap around to end
            cursor = self._text.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)
            self._text.setTextCursor(cursor)
            found = self._text.find(query, QTextDocument.FindFlag.FindBackward)
        self._update_search_count(query)

    def _update_search_count(self, query: str):
        """Count total matches and show in label."""
        if not query:
            self._search_count.setText("")
            return
        text = self._text.toPlainText()
        count = text.lower().count(query.lower())
        self._search_count.setText(f"{count} match{'es' if count != 1 else ''}")

    # ── Save log ────────────────────────────────────────────────────

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
            .replace(">", "&gt;"))
