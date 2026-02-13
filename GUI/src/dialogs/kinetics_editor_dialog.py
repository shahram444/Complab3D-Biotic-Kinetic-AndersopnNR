"""Kinetics C++ code editor dialog with separate Biotic / Abiotic tabs.

Each tab manages its own kinetics .hh file with syntax highlighting
and templates matching the C++ solver expectations.
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QFileDialog, QMessageBox, QTabWidget,
    QWidget,
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
            "namespace", "struct", "class", "const", "constexpr", "static",
            "double", "int", "float", "void", "return", "if", "else", "for",
            "while", "using", "typedef", "template", "typename", "true",
            "false", "T", "plint", "pluint", "std", "vector",
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


# ── Biotic kinetics templates ───────────────────────────────────────────

BIOTIC_MONOD = '''\
// defineKinetics.hh - Biotic kinetics (Monod growth)
// Compiled by the C++ solver. Modify parameters as needed.
//
// Function signature expected by CompLaB3D:
//   void defineRxnKinetics(vector<T>& C, vector<T>& subsR,
//                          vector<T>& B, vector<T>& bioR,
//                          plint mask)

#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

namespace KineticParams {
    constexpr double mu_max  = 2.5;      // [1/s] Maximum specific growth rate
    constexpr double Ks      = 1.0e-5;   // [mol/L] Half-saturation constant
    constexpr double Y       = 0.5;      // [-] Yield coefficient
    constexpr double k_decay = 1.0e-9;   // [1/s] Decay coefficient
    constexpr double MIN_CONC = 1.0e-20; // Minimum concentration floor
}

template<typename T>
void defineRxnKinetics(std::vector<T>& C, std::vector<T>& subsR,
                       std::vector<T>& B, std::vector<T>& bioR,
                       plb::plint mask) {
    using namespace KineticParams;

    // Monod kinetics: mu = mu_max * S / (Ks + S)
    T doc = (C[0] > MIN_CONC) ? C[0] : MIN_CONC;
    T growth_rate = mu_max * doc / (Ks + doc);
    T net_growth  = growth_rate - k_decay;

    // Substrate consumption: dDOC/dt = -mu * B / Y
    subsR[0] = -growth_rate * B[0] / Y;
    // CO2 production (1:1 stoichiometry)
    subsR[1] = -subsR[0];

    // Biomass growth
    bioR[0] = net_growth * B[0];
}

#endif
'''

BIOTIC_DUAL_MONOD = '''\
// defineKinetics.hh - Dual-Monod kinetics (electron donor + acceptor)
// Two-substrate limitation model

#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

namespace KineticParams {
    constexpr double mu_max   = 2.5;      // [1/s] Maximum growth rate
    constexpr double Ks_donor = 1.0e-5;   // [mol/L] Half-sat for electron donor
    constexpr double Ks_acc   = 2.0e-4;   // [mol/L] Half-sat for electron acceptor
    constexpr double Y        = 0.5;      // [-] Yield coefficient
    constexpr double k_decay  = 1.0e-9;   // [1/s] Decay coefficient
}

template<typename T>
void defineRxnKinetics(std::vector<T>& C, std::vector<T>& subsR,
                       std::vector<T>& B, std::vector<T>& bioR,
                       plb::plint mask) {
    using namespace KineticParams;

    T donor    = (C[0] > 1e-20) ? C[0] : 1e-20;
    T acceptor = (C[1] > 1e-20) ? C[1] : 1e-20;

    // Dual-Monod: mu = mu_max * S_d/(Ks_d+S_d) * S_a/(Ks_a+S_a)
    T growth = mu_max * donor / (Ks_donor + donor)
                      * acceptor / (Ks_acc + acceptor);

    subsR[0] = -growth * B[0] / Y;          // donor consumed
    subsR[1] = -growth * B[0] / (2.0 * Y);  // acceptor consumed
    bioR[0]  = (growth - k_decay) * B[0];
}

#endif
'''

BIOTIC_TEMPLATES = {
    "Monod (single substrate)": BIOTIC_MONOD,
    "Dual-Monod (donor + acceptor)": BIOTIC_DUAL_MONOD,
}

# ── Abiotic kinetics templates ──────────────────────────────────────────

ABIOTIC_FIRST_ORDER = '''\
// defineAbioticKinetics.hh - First-order decay
// Compiled by the C++ solver. Modify parameters as needed.
//
// Function signature expected by CompLaB3D:
//   void defineAbioticRxnKinetics(vector<T> C, vector<T>& subsR,
//                                 plint mask)

#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

namespace AbioticParams {
    constexpr double k_decay = 1.0e-3;  // [1/s] First-order decay rate
}

template<typename T>
void defineAbioticRxnKinetics(std::vector<T> C, std::vector<T>& subsR,
                              plb::plint mask) {
    using namespace AbioticParams;

    // First-order decay: dC/dt = -k * C
    subsR[0] = -k_decay * C[0];
}

#endif
'''

ABIOTIC_BIMOLECULAR = '''\
// defineAbioticKinetics.hh - Bimolecular reaction A + B -> C
// Second-order kinetics

#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

namespace AbioticParams {
    constexpr double k_forward = 1.0e-3;  // [L/(mol*s)] Rate constant
}

template<typename T>
void defineAbioticRxnKinetics(std::vector<T> C, std::vector<T>& subsR,
                              plb::plint mask) {
    using namespace AbioticParams;

    // A + B -> C:  rate = k * [A] * [B]
    T rate = k_forward * C[0] * C[1];
    subsR[0] = -rate;   // A consumed
    subsR[1] = -rate;   // B consumed
    subsR[2] =  rate;   // C produced
}

#endif
'''

ABIOTIC_REVERSIBLE = '''\
// defineAbioticKinetics.hh - Reversible reaction A <-> B
// Forward and backward rate constants

#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

namespace AbioticParams {
    constexpr double k_forward  = 1.0e-3;  // [1/s] Forward rate
    constexpr double k_backward = 1.0e-4;  // [1/s] Backward rate
}

template<typename T>
void defineAbioticRxnKinetics(std::vector<T> C, std::vector<T>& subsR,
                              plb::plint mask) {
    using namespace AbioticParams;

    // A <-> B:  net rate = k_f*[A] - k_b*[B]
    T net_rate = k_forward * C[0] - k_backward * C[1];
    subsR[0] = -net_rate;  // A
    subsR[1] =  net_rate;  // B
}

#endif
'''

ABIOTIC_DECAY_CHAIN = '''\
// defineAbioticKinetics.hh - Sequential decay chain A -> B -> C
// Bateman equations for radioactive decay or multi-step degradation

#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

namespace AbioticParams {
    constexpr double k1 = 2.0e-4;  // [1/s] A -> B decay rate
    constexpr double k2 = 1.0e-4;  // [1/s] B -> C decay rate
}

template<typename T>
void defineAbioticRxnKinetics(std::vector<T> C, std::vector<T>& subsR,
                              plb::plint mask) {
    using namespace AbioticParams;

    // A -> B -> C (sequential first-order decay)
    subsR[0] = -k1 * C[0];           // A decays
    subsR[1] = k1 * C[0] - k2 * C[1]; // B produced from A, decays to C
    subsR[2] = k2 * C[1];            // C produced from B
}

#endif
'''

ABIOTIC_TEMPLATES = {
    "First-order decay": ABIOTIC_FIRST_ORDER,
    "Bimolecular (A + B -> C)": ABIOTIC_BIMOLECULAR,
    "Reversible (A <-> B)": ABIOTIC_REVERSIBLE,
    "Decay chain (A -> B -> C)": ABIOTIC_DECAY_CHAIN,
}


def _make_editor_tab(templates: dict, default_filename: str):
    """Create a single kinetics editor tab widget.
    Returns (widget, editor, filepath_label, template_combo, filepath_holder).
    """
    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setSpacing(6)
    layout.setContentsMargins(4, 8, 4, 4)

    # Toolbar
    toolbar = QHBoxLayout()
    open_btn = QPushButton("Open")
    save_btn = QPushButton("Save")
    save_btn.setProperty("primary", True)
    save_as_btn = QPushButton("Save As")
    toolbar.addWidget(open_btn)
    toolbar.addWidget(save_btn)
    toolbar.addWidget(save_as_btn)
    toolbar.addStretch()
    toolbar.addWidget(QLabel("Template:"))
    template_combo = QComboBox()
    template_combo.addItems(list(templates.keys()))
    template_combo.setMinimumWidth(180)
    toolbar.addWidget(template_combo)
    load_btn = QPushButton("Load Template")
    toolbar.addWidget(load_btn)
    layout.addLayout(toolbar)

    # File path
    path_label = QLabel("No file loaded")
    path_label.setProperty("info", True)
    layout.addWidget(path_label)

    # Code editor
    editor = QTextEdit()
    font = QFont("Consolas", 10)
    font.setStyleHint(QFont.StyleHint.Monospace)
    editor.setFont(font)
    CppHighlighter(editor.document())
    layout.addWidget(editor, 1)

    # Store file path on the widget
    widget._filepath = ""
    widget._editor = editor
    widget._path_label = path_label
    widget._default_filename = default_filename

    def open_file_dlg():
        path, _ = QFileDialog.getOpenFileName(
            widget, "Open Kinetics File", "",
            "C++ Headers (*.hh *.h *.hpp);;All Files (*)")
        if path:
            _load_file(widget, path)

    def save_file():
        if not widget._filepath:
            save_as()
            return
        try:
            with open(widget._filepath, "w") as f:
                f.write(editor.toPlainText())
            path_label.setText(f"Saved: {widget._filepath}")
        except OSError as e:
            QMessageBox.critical(widget, "Save Error", str(e))

    def save_as():
        path, _ = QFileDialog.getSaveFileName(
            widget, "Save Kinetics File",
            widget._filepath or default_filename,
            "C++ Headers (*.hh *.h *.hpp);;All Files (*)")
        if path:
            widget._filepath = path
            save_file()

    def load_template():
        key = template_combo.currentText()
        if key in templates:
            editor.setPlainText(templates[key])

    open_btn.clicked.connect(open_file_dlg)
    save_btn.clicked.connect(save_file)
    save_as_btn.clicked.connect(save_as)
    load_btn.clicked.connect(load_template)

    return widget


def _load_file(tab_widget, filepath: str):
    """Load a file into a tab's editor."""
    if not Path(filepath).exists():
        tab_widget._editor.setPlainText(
            f"// File not found: {filepath}\n"
            "// Select a template to create a new file.\n")
        tab_widget._filepath = filepath
        tab_widget._path_label.setText(filepath)
        return
    tab_widget._filepath = filepath
    tab_widget._path_label.setText(filepath)
    with open(filepath, "r") as f:
        tab_widget._editor.setPlainText(f.read())


class KineticsEditorDialog(QDialog):
    """C++ kinetics file editor with Biotic / Abiotic tabs."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kinetics File Editor")
        self.setMinimumSize(780, 560)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        heading = QLabel("C++ Kinetics Editor")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        info = QLabel(
            "Edit the C++ kinetics header files used by the CompLaB3D solver. "
            "Biotic kinetics (defineKinetics.hh) define microbial growth reactions. "
            "Abiotic kinetics (defineAbioticKinetics.hh) define chemical reactions "
            "without microbes.")
        info.setWordWrap(True)
        info.setProperty("info", True)
        layout.addWidget(info)

        # Tabs: Biotic / Abiotic
        self._tabs = QTabWidget()
        self._biotic_tab = _make_editor_tab(
            BIOTIC_TEMPLATES, "defineKinetics.hh")
        self._abiotic_tab = _make_editor_tab(
            ABIOTIC_TEMPLATES, "defineAbioticKinetics.hh")
        self._tabs.addTab(self._biotic_tab, "Biotic Kinetics")
        self._tabs.addTab(self._abiotic_tab, "Abiotic Kinetics")
        layout.addWidget(self._tabs, 1)

        # Recompilation help
        recompile_group = QLabel(
            "After modifying kinetics files, you must recompile CompLaB3D:\n\n"
            "  1. Save the .hh file to the project root directory\n"
            "     (same folder as CompLaB.xml)\n\n"
            "  2. Recompile the solver:\n"
            "     cd /path/to/CompLaB3D\n"
            "     make clean && make\n\n"
            "  3. If using CMake:\n"
            "     cd build\n"
            "     cmake .. && make -j$(nproc)\n\n"
            "  4. The solver reads defineKinetics.hh (biotic) or\n"
            "     defineAbioticKinetics.hh (abiotic) at compile time.\n"
            "     These are #include'd in the source code.\n\n"
            "  NOTE: Biotic kinetics file must define:\n"
            "    void defineRxnKinetics(vector<T>& C, vector<T>& subsR,\n"
            "                           vector<T>& B, vector<T>& bioR,\n"
            "                           plint mask)\n\n"
            "  NOTE: Abiotic kinetics file must define:\n"
            "    void defineAbioticRxnKinetics(vector<T> C, vector<T>& subsR,\n"
            "                                  plint mask)")
        recompile_group.setWordWrap(True)
        recompile_group.setStyleSheet(
            "background: #1e293b; color: #94a3b8; padding: 12px; "
            "border: 1px solid #334155; border-radius: 4px; "
            "font-family: Consolas, monospace; font-size: 10px;")
        layout.addWidget(recompile_group)

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

    def open_biotic_file(self, filepath: str):
        """Open a specific biotic kinetics file for editing."""
        _load_file(self._biotic_tab, filepath)
        self._tabs.setCurrentWidget(self._biotic_tab)

    def open_abiotic_file(self, filepath: str):
        """Open a specific abiotic kinetics file for editing."""
        _load_file(self._abiotic_tab, filepath)
        self._tabs.setCurrentWidget(self._abiotic_tab)

    def open_file(self, filepath: str):
        """Open a file, auto-detecting type from filename."""
        name = Path(filepath).name.lower()
        if "abiotic" in name:
            self.open_abiotic_file(filepath)
        else:
            self.open_biotic_file(filepath)
