"""Kinetics C++ code editor dialog for biotic and abiotic kinetics files.

Opens the kinetics .hh files for editing with syntax highlighting.
Supports templates for common kinetics patterns.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QFileDialog, QMessageBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor

import re


class CppHighlighter(QSyntaxHighlighter):
    """Basic C++ syntax highlighter for kinetics editor."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#569cd6"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "namespace", "struct", "class", "const", "static", "double",
            "int", "float", "void", "return", "if", "else", "for", "while",
            "using", "typedef", "template", "typename", "true", "false",
            "T", "plint", "pluint",
        ]
        for kw in keywords:
            self._rules.append((re.compile(rf"\b{kw}\b"), kw_fmt))

        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#b5cea8"))
        self._rules.append((re.compile(r"\b\d+\.?\d*(?:[eE][+-]?\d+)?\b"), num_fmt))

        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#ce9178"))
        self._rules.append((re.compile(r'"[^"]*"'), str_fmt))

        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6a9955"))
        self._rules.append((re.compile(r"//[^\n]*"), comment_fmt))

        preproc_fmt = QTextCharFormat()
        preproc_fmt.setForeground(QColor("#c586c0"))
        self._rules.append((re.compile(r"^\s*#.*$", re.MULTILINE), preproc_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


# Kinetics templates
BIOTIC_TEMPLATE = '''\
// Biotic kinetics - Monod growth
// This file is compiled by the C++ solver.
// Modify parameters and rate expressions as needed.

#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

namespace KineticParams {
    // Monod kinetic parameters
    const double mu_max  = 2.5;     // Maximum specific growth rate
    const double Ks      = 1e-5;    // Half-saturation constant
    const double Y       = 0.5;     // Yield coefficient
    const double k_decay = 1e-9;    // Decay coefficient
}

template<typename T>
T bioticReactionRate(T substrate_conc, T biomass_density) {
    using namespace KineticParams;
    // Monod kinetics: mu = mu_max * S / (Ks + S)
    T growth = mu_max * substrate_conc / (Ks + substrate_conc);
    return growth * biomass_density;
}

#endif
'''

ABIOTIC_TEMPLATE = '''\
// Abiotic kinetics - Chemical reactions without microbes
// This file is compiled by the C++ solver.

#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

namespace AbioticParams {
    const double k_forward  = 1e-3;  // Forward rate constant
    const double k_backward = 1e-4;  // Backward rate constant
}

template<typename T>
T abioticReactionRate(T reactant_conc, T product_conc) {
    using namespace AbioticParams;
    // Reversible reaction: A <-> B
    return k_forward * reactant_conc - k_backward * product_conc;
}

#endif
'''

PLANKTONIC_TEMPLATE = '''\
// Planktonic kinetics - Free-swimming bacteria
// This file is compiled by the C++ solver.

#ifndef DEFINE_KINETICS_PLANKTONIC_HH
#define DEFINE_KINETICS_PLANKTONIC_HH

namespace PlanktonicParams {
    const double mu_max  = 2.5;     // Maximum specific growth rate
    const double Ks      = 1e-5;    // Half-saturation constant
    const double Y       = 0.5;     // Yield coefficient
    const double k_decay = 1e-9;    // Decay coefficient
}

template<typename T>
T planktonicReactionRate(T substrate_conc, T biomass_density) {
    using namespace PlanktonicParams;
    T growth = mu_max * substrate_conc / (Ks + substrate_conc);
    return growth * biomass_density;
}

#endif
'''

TEMPLATES = {
    "Biotic (Monod) kinetics": BIOTIC_TEMPLATE,
    "Abiotic kinetics": ABIOTIC_TEMPLATE,
    "Planktonic kinetics": PLANKTONIC_TEMPLATE,
}


class KineticsEditorDialog(QDialog):
    """C++ kinetics file editor with syntax highlighting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kinetics File Editor")
        self.setMinimumSize(700, 500)
        self._filepath = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        heading = QLabel("C++ Kinetics Editor")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        # Toolbar
        toolbar = QHBoxLayout()

        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self._open_file)
        toolbar.addWidget(open_btn)

        save_btn = QPushButton("Save")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self._save_file)
        toolbar.addWidget(save_btn)

        save_as_btn = QPushButton("Save As")
        save_as_btn.clicked.connect(self._save_as)
        toolbar.addWidget(save_as_btn)

        toolbar.addStretch()

        toolbar.addWidget(QLabel("Template:"))
        self._template_combo = QComboBox()
        self._template_combo.addItems(list(TEMPLATES.keys()))
        toolbar.addWidget(self._template_combo)

        insert_btn = QPushButton("Load Template")
        insert_btn.clicked.connect(self._load_template)
        toolbar.addWidget(insert_btn)

        layout.addLayout(toolbar)

        # File path display
        self._path_label = QLabel("No file loaded")
        self._path_label.setProperty("info", True)
        layout.addWidget(self._path_label)

        # Editor
        self._editor = QTextEdit()
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._editor.setFont(font)
        self._highlighter = CppHighlighter(self._editor.document())
        layout.addWidget(self._editor, 1)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def open_file(self, filepath: str):
        """Open a specific file for editing."""
        if not Path(filepath).exists():
            self._editor.setPlainText(f"// File not found: {filepath}\n"
                                       "// Select a template to create a new file.\n")
            self._filepath = filepath
            self._path_label.setText(filepath)
            return
        self._filepath = filepath
        self._path_label.setText(filepath)
        with open(filepath, "r") as f:
            self._editor.setPlainText(f.read())

    def _open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Kinetics File", "",
            "C++ Headers (*.hh *.h *.hpp);;All Files (*)")
        if path:
            self.open_file(path)

    def _save_file(self):
        if not self._filepath:
            self._save_as()
            return
        try:
            with open(self._filepath, "w") as f:
                f.write(self._editor.toPlainText())
            self._path_label.setText(f"Saved: {self._filepath}")
        except OSError as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _save_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Kinetics File", self._filepath or "defineKinetics.hh",
            "C++ Headers (*.hh *.h *.hpp);;All Files (*)")
        if path:
            self._filepath = path
            self._save_file()

    def _load_template(self):
        key = self._template_combo.currentText()
        if key in TEMPLATES:
            self._editor.setPlainText(TEMPLATES[key])
