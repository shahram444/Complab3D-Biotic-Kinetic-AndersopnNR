"""Kinetics C++ code editor dialog for biotic and abiotic kinetics files."""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QTabWidget, QWidget, QTextEdit, QMessageBox,
    QFileDialog, QGroupBox,
)
from PySide6.QtGui import (
    QSyntaxHighlighter, QTextCharFormat, QColor, QFont,
)
from PySide6.QtCore import Qt, QRegularExpression


class CppHighlighter(QSyntaxHighlighter):
    """Basic C++ syntax highlighter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []

        # Keywords
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#569cd6"))
        kw_fmt.setFontWeight(QFont.Weight.Bold)
        keywords = [
            "void", "int", "double", "float", "bool", "char", "long",
            "const", "constexpr", "static", "inline", "return", "if",
            "else", "for", "while", "do", "switch", "case", "break",
            "continue", "namespace", "using", "class", "struct", "enum",
            "template", "typename", "std", "size_t", "true", "false",
        ]
        for kw in keywords:
            pattern = QRegularExpression(rf"\b{kw}\b")
            self._rules.append((pattern, kw_fmt))

        # Numbers
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#b5cea8"))
        self._rules.append((QRegularExpression(r"\b[0-9]+\.?[0-9]*([eE][+-]?[0-9]+)?\b"), num_fmt))

        # Strings
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#ce9178"))
        self._rules.append((QRegularExpression(r'"[^"]*"'), str_fmt))

        # Preprocessor
        pp_fmt = QTextCharFormat()
        pp_fmt.setForeground(QColor("#c586c0"))
        self._rules.append((QRegularExpression(r"#\w+"), pp_fmt))

        # Comments
        self._comment_fmt = QTextCharFormat()
        self._comment_fmt.setForeground(QColor("#6a9955"))
        self._rules.append((QRegularExpression(r"//[^\n]*"), self._comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


# Template code for each kinetics type
BIOTIC_TEMPLATE = '''/* defineKinetics.hh - Monod Kinetics (Biofilm)
 * CompLaB3D
 *
 * Modify parameters and rate expressions below.
 */
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

namespace KineticParams {
    constexpr double mu_max   = 1.0;       // [1/s] max specific growth rate
    constexpr double Ks       = 1.0e-5;    // [mol/L] half-saturation constant
    constexpr double Y        = 0.4;       // [-] yield coefficient
    constexpr double k_decay  = 1.0e-9;    // [1/s] decay rate
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MIN_BIOMASS = 0.1;
    constexpr double MAX_DOC_CONSUMPTION_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask
) {
    using namespace KineticParams;

    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    for (size_t i = 0; i < bioR.size(); ++i) bioR[i] = 0.0;

    if (B.empty() || C.empty()) return;
    double biomass = std::max(B[0], 0.0);
    if (biomass < MIN_BIOMASS) return;

    double DOC = std::max(C[0], MIN_CONC);

    // Monod growth
    double mu = mu_max * DOC / (Ks + DOC);
    double dB_dt = (mu - k_decay) * biomass;
    double dDOC_dt = -mu * biomass / Y;

    // Clamp substrate consumption
    double max_rate = DOC * MAX_DOC_CONSUMPTION_FRACTION / dt_kinetics;
    if (-dDOC_dt > max_rate) {
        dDOC_dt = -max_rate;
        double actual_mu = max_rate * Y / biomass;
        dB_dt = (actual_mu - k_decay) * biomass;
    }

    if (subsR.size() > 0) subsR[0] = dDOC_dt;
    if (subsR.size() > 1) subsR[1] = -dDOC_dt;  // CO2 production
    if (bioR.size() > 0) bioR[0] = dB_dt;
}

#endif
'''

PLANKTONIC_TEMPLATE = '''/* defineKinetics_planktonic.hh - Monod Kinetics (Planktonic)
 * CompLaB3D
 *
 * Planktonic bacteria: transported by flow, moderate growth, higher decay.
 */
#ifndef DEFINE_KINETICS_PLANKTONIC_HH
#define DEFINE_KINETICS_PLANKTONIC_HH

#include <vector>
#include <cmath>
#include <algorithm>

namespace KineticParams {
    constexpr double mu_max   = 0.5;       // [1/s] lower than biofilm
    constexpr double Ks       = 1.0e-5;    // [mol/L] half-saturation
    constexpr double Y        = 0.4;       // [-] yield
    constexpr double k_decay  = 1.0e-7;    // [1/s] higher decay (exposed)
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MIN_BIOMASS = 0.01;
    constexpr double MAX_DOC_CONSUMPTION_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask
) {
    using namespace KineticParams;

    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;
    for (size_t i = 0; i < bioR.size(); ++i) bioR[i] = 0.0;

    if (B.empty() || C.empty()) return;
    double biomass = std::max(B[0], 0.0);
    if (biomass < MIN_BIOMASS) return;

    double DOC = std::max(C[0], MIN_CONC);
    double mu = mu_max * DOC / (Ks + DOC);
    double dB_dt = (mu - k_decay) * biomass;
    double dDOC_dt = -mu * biomass / Y;

    double max_rate = DOC * MAX_DOC_CONSUMPTION_FRACTION / dt_kinetics;
    if (-dDOC_dt > max_rate) {
        dDOC_dt = -max_rate;
        double actual_mu = max_rate * Y / biomass;
        dB_dt = (actual_mu - k_decay) * biomass;
    }

    if (subsR.size() > 0) subsR[0] = dDOC_dt;
    if (subsR.size() > 1) subsR[1] = -dDOC_dt;
    if (bioR.size() > 0) bioR[0] = dB_dt;
}

#endif
'''

ABIOTIC_FIRST_ORDER = '''/* defineAbioticKinetics.hh - First-Order Decay
 * CompLaB3D
 *
 * Reaction: A -> products, rate = -k * [A]
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

namespace AbioticParams {
    constexpr double k_decay = 1.0e-5;     // [1/s]
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    using namespace AbioticParams;
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;

    if (C.size() > 0) {
        double A = std::max(C[0], MIN_CONC);
        double dA_dt = -k_decay * A;
        double max_rate = A * MAX_RATE_FRACTION / dt_kinetics;
        if (-dA_dt > max_rate) dA_dt = -max_rate;
        subsR[0] = dA_dt;
    }
}

#endif
'''

ABIOTIC_BIMOLECULAR = '''/* defineAbioticKinetics.hh - Bimolecular Reaction
 * CompLaB3D
 *
 * Reaction: A + B -> C, rate = k * [A] * [B]
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

namespace AbioticParams {
    constexpr double k_reaction = 1.0e-3;  // [L/mol/s]
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    using namespace AbioticParams;
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;

    if (C.size() >= 3) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);
        double rate = k_reaction * A * B;

        double max_A = A * MAX_RATE_FRACTION / dt_kinetics;
        double max_B = B * MAX_RATE_FRACTION / dt_kinetics;
        rate = std::min({rate, max_A, max_B});

        subsR[0] = -rate;  // A consumed
        subsR[1] = -rate;  // B consumed
        subsR[2] = +rate;  // C produced
    }
}

#endif
'''

ABIOTIC_REVERSIBLE = '''/* defineAbioticKinetics.hh - Reversible Reaction
 * CompLaB3D
 *
 * Reaction: A <-> B, forward k_f, reverse k_r
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

namespace AbioticParams {
    constexpr double k_forward = 1.0e-4;   // [1/s]
    constexpr double k_reverse = 1.0e-5;   // [1/s]
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    using namespace AbioticParams;
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;

    if (C.size() >= 2) {
        double A = std::max(C[0], MIN_CONC);
        double B = std::max(C[1], MIN_CONC);
        double net = k_forward * A - k_reverse * B;

        double max_A = A * MAX_RATE_FRACTION / dt_kinetics;
        double max_B = B * MAX_RATE_FRACTION / dt_kinetics;
        if (net > 0 && net > max_A) net = max_A;
        if (net < 0 && -net > max_B) net = -max_B;

        subsR[0] = -net;
        subsR[1] = +net;
    }
}

#endif
'''

ABIOTIC_CUSTOM = '''/* defineAbioticKinetics.hh - Custom Abiotic Reactions
 * CompLaB3D
 *
 * Define your own reaction rate expressions below.
 */
#ifndef DEFINE_ABIOTIC_KINETICS_HH
#define DEFINE_ABIOTIC_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

namespace AbioticParams {
    // Define your rate constants here
    constexpr double MIN_CONC = 1.0e-20;
    constexpr double MAX_RATE_FRACTION = 0.5;
    constexpr double dt_kinetics = 0.0075;
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    using namespace AbioticParams;
    for (size_t i = 0; i < subsR.size(); ++i) subsR[i] = 0.0;

    // Add your reaction rate expressions here
    // C[i] = concentration of substrate i
    // subsR[i] = rate of change for substrate i [mol/L/s]
    // Negative = consumption, Positive = production
}

#endif
'''

TEMPLATES_MAP = {
    "Biotic: Monod (Biofilm)": BIOTIC_TEMPLATE,
    "Biotic: Monod (Planktonic)": PLANKTONIC_TEMPLATE,
    "Abiotic: First-Order Decay": ABIOTIC_FIRST_ORDER,
    "Abiotic: Bimolecular A+B->C": ABIOTIC_BIMOLECULAR,
    "Abiotic: Reversible A<->B": ABIOTIC_REVERSIBLE,
    "Abiotic: Custom (Empty)": ABIOTIC_CUSTOM,
}


class KineticsEditorDialog(QDialog):

    def __init__(self, project_dir="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kinetics Editor")
        self.setMinimumSize(800, 600)
        self._project_dir = project_dir
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        heading = QLabel("Kinetics Code Editor")
        heading.setProperty("heading", True)
        layout.addWidget(heading)

        info = QLabel(
            "Edit the C++ kinetics source files used by the CompLaB3D solver. "
            "Select a template to start from, then customize the rate expressions.")
        info.setProperty("info", True)
        info.setWordWrap(True)
        layout.addWidget(info)

        # Template selector
        tmpl_row = QHBoxLayout()
        tmpl_row.addWidget(QLabel("Template:"))
        self._template_combo = QComboBox()
        self._template_combo.addItems(list(TEMPLATES_MAP.keys()))
        self._template_combo.currentTextChanged.connect(self._on_template_changed)
        self._load_tmpl_btn = QPushButton("Load Template")
        self._load_tmpl_btn.clicked.connect(self._load_template)
        tmpl_row.addWidget(self._template_combo, 1)
        tmpl_row.addWidget(self._load_tmpl_btn)
        layout.addLayout(tmpl_row)

        # Tabs for biotic and abiotic editors
        self._tabs = QTabWidget()

        self._biotic_editor = QTextEdit()
        self._biotic_editor.setFontFamily("Consolas, Courier New, monospace")
        self._biotic_highlighter = CppHighlighter(self._biotic_editor.document())
        self._tabs.addTab(self._biotic_editor, "defineKinetics.hh (Biotic)")

        self._abiotic_editor = QTextEdit()
        self._abiotic_editor.setFontFamily("Consolas, Courier New, monospace")
        self._abiotic_highlighter = CppHighlighter(self._abiotic_editor.document())
        self._tabs.addTab(self._abiotic_editor, "defineAbioticKinetics.hh (Abiotic)")

        layout.addWidget(self._tabs, 1)

        # Buttons
        btn_row = QHBoxLayout()
        self._load_file_btn = QPushButton("Load from File")
        self._load_file_btn.clicked.connect(self._load_from_file)
        self._save_btn = QPushButton("Save to Project")
        self._save_btn.setProperty("primary", True)
        self._save_btn.clicked.connect(self._save_to_project)
        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._load_file_btn)
        btn_row.addStretch()
        btn_row.addWidget(self._save_btn)
        btn_row.addWidget(self._close_btn)
        layout.addLayout(btn_row)

        # Load existing files if available
        self._load_existing_files()

    def _on_template_changed(self, name):
        pass  # Preview only; actual load on button click

    def _load_template(self):
        name = self._template_combo.currentText()
        code = TEMPLATES_MAP.get(name, "")
        if not code:
            return

        if name.startswith("Biotic"):
            self._biotic_editor.setPlainText(code)
            self._tabs.setCurrentIndex(0)
        else:
            self._abiotic_editor.setPlainText(code)
            self._tabs.setCurrentIndex(1)

    def _load_existing_files(self):
        if not self._project_dir:
            return
        biotic_path = Path(self._project_dir) / "defineKinetics.hh"
        if biotic_path.exists():
            self._biotic_editor.setPlainText(biotic_path.read_text())

        abiotic_path = Path(self._project_dir) / "defineAbioticKinetics.hh"
        if abiotic_path.exists():
            self._abiotic_editor.setPlainText(abiotic_path.read_text())

    def _load_from_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Kinetics File", self._project_dir,
            "C++ Header Files (*.hh *.h *.hpp);;All Files (*)")
        if not path:
            return
        text = Path(path).read_text()
        if "Abiotic" in Path(path).name or "abiotic" in Path(path).name:
            self._abiotic_editor.setPlainText(text)
            self._tabs.setCurrentIndex(1)
        else:
            self._biotic_editor.setPlainText(text)
            self._tabs.setCurrentIndex(0)

    def _save_to_project(self):
        if not self._project_dir:
            QMessageBox.warning(self, "No Project",
                                "No project directory set. Save your project first.")
            return

        proj_dir = Path(self._project_dir)
        saved = []

        biotic_text = self._biotic_editor.toPlainText().strip()
        if biotic_text:
            biotic_path = proj_dir / "defineKinetics.hh"
            biotic_path.write_text(biotic_text)
            saved.append(str(biotic_path))

        abiotic_text = self._abiotic_editor.toPlainText().strip()
        if abiotic_text:
            abiotic_path = proj_dir / "defineAbioticKinetics.hh"
            abiotic_path.write_text(abiotic_text)
            saved.append(str(abiotic_path))

        if saved:
            QMessageBox.information(
                self, "Saved",
                f"Kinetics files saved:\n" + "\n".join(saved))
        else:
            QMessageBox.information(self, "Nothing to Save",
                                    "Both editors are empty.")
