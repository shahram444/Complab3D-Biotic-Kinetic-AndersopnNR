"""
Console Widget for simulation output
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QPushButton,
    QLabel, QFrame, QLineEdit
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor


class ConsoleWidget(QFrame):
    """Console widget for displaying simulation output"""
    
    command_entered = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("consoleWidget")
        self._setup_ui()
        self._max_lines = 10000
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header
        header = QWidget()
        header.setObjectName("consoleHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(10, 5, 10, 5)
        
        title = QLabel("📟 Console Output")
        title.setObjectName("consoleTitle")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        clear_btn = QPushButton("Clear")
        clear_btn.setObjectName("consoleClearBtn")
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)
        
        save_btn = QPushButton("Save Log")
        save_btn.setObjectName("consoleSaveBtn")
        save_btn.clicked.connect(self._save_log)
        header_layout.addWidget(save_btn)
        
        layout.addWidget(header)
        
        # Text area
        self.text_area = QTextEdit()
        self.text_area.setObjectName("consoleTextArea")
        self.text_area.setReadOnly(True)
        self.text_area.setFont(QFont("Consolas", 10))
        self.text_area.setLineWrapMode(QTextEdit.NoWrap)
        layout.addWidget(self.text_area)
        
        # Input line (optional command input)
        input_widget = QWidget()
        input_layout = QHBoxLayout(input_widget)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        prompt = QLabel("❯")
        prompt.setStyleSheet("color: #4CAF50; font-weight: bold;")
        input_layout.addWidget(prompt)
        
        self.input_line = QLineEdit()
        self.input_line.setPlaceholderText("Enter command...")
        self.input_line.returnPressed.connect(self._on_command_entered)
        self.input_line.setVisible(False)  # Hidden by default
        input_layout.addWidget(self.input_line)
        
        layout.addWidget(input_widget)
        
    def log(self, message: str, level: str = "info"):
        """Log a message with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Color based on level
        colors = {
            "info": "#CCCCCC",
            "success": "#4CAF50",
            "warning": "#FFC107",
            "error": "#F44336",
            "debug": "#9E9E9E",
        }
        color = colors.get(level, "#CCCCCC")
        
        html = f'<span style="color: #666;">[{timestamp}]</span> <span style="color: {color};">{message}</span>'
        self.text_area.append(html)
        
        # Scroll to bottom
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )
        
        self._trim_lines()
        
    def append_output(self, text: str):
        """Append raw output text (from simulation)"""
        # Parse for errors/warnings
        text_lower = text.lower()
        
        if "error" in text_lower:
            color = "#F44336"
        elif "warning" in text_lower:
            color = "#FFC107"
        elif "converge" in text_lower or "complete" in text_lower:
            color = "#4CAF50"
        else:
            color = "#AAAAAA"
            
        html = f'<span style="color: {color}; font-family: Consolas, monospace;">{text}</span>'
        self.text_area.append(html)
        
        # Scroll to bottom
        self.text_area.verticalScrollBar().setValue(
            self.text_area.verticalScrollBar().maximum()
        )
        
        self._trim_lines()
        
    def clear(self):
        """Clear the console"""
        self.text_area.clear()
        self.log("Console cleared", "debug")
        
    def _save_log(self):
        """Save log to file"""
        from PySide6.QtWidgets import QFileDialog
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Log",
            "complab_log.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.text_area.toPlainText())
            self.log(f"Log saved to {file_path}", "success")
            
    def _on_command_entered(self):
        """Handle command input"""
        command = self.input_line.text().strip()
        if command:
            self.log(f"❯ {command}", "debug")
            self.command_entered.emit(command)
            self.input_line.clear()
            
    def _trim_lines(self):
        """Trim old lines if exceeding max"""
        doc = self.text_area.document()
        if doc.blockCount() > self._max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 
                              doc.blockCount() - self._max_lines)
            cursor.removeSelectedText()
            
    def show_command_input(self, show: bool = True):
        """Show/hide command input"""
        self.input_line.setVisible(show)
