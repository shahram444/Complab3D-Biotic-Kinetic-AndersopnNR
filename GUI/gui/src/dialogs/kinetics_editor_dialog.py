"""
Kinetics Editor Dialog - Edit custom reaction kinetics

Provides two tabs:
  * Biotic Kinetics  -- Monod-type growth kinetics (mu_max, Ks, yield, decay)
  * Abiotic Kinetics -- First-order and bimolecular rate expressions for
                        purely chemical reactions without microbes

Each tab contains a kinetics-type selector, editable parameter fields, a C++
code editor, and a read-only preview of the generated defineKinetics.hh
function body.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QComboBox, QDialogButtonBox,
    QTabWidget, QWidget, QTextEdit, QSplitter, QListWidget,
    QListWidgetItem, QMessageBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor

import re

from ..core.project import KineticsModel, ReactionType


# -------------------------------------------------------------------- #
#  Syntax highlighter (shared by both tabs)
# -------------------------------------------------------------------- #
class CppHighlighter(QSyntaxHighlighter):
    """Simple C++ syntax highlighter for the code editors."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.highlighting_rules = []

        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "if", "else", "for", "while", "return", "void", "int", "float",
            "double", "bool", "true", "false", "const", "auto",
        ]
        for word in keywords:
            pattern = rf"\b{word}\b"
            self.highlighting_rules.append((re.compile(pattern), keyword_format))

        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((
            re.compile(r"\b[0-9]+\.?[0-9]*([eE][-+]?[0-9]+)?\b"),
            number_format,
        ))

        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((
            re.compile(r'"[^"]*"'),
            string_format,
        ))

        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        self.highlighting_rules.append((
            re.compile(r"//[^\n]*"),
            comment_format,
        ))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


# -------------------------------------------------------------------- #
#  Biotic kinetics templates
# -------------------------------------------------------------------- #
_BIOTIC_TEMPLATES = {
    "Monod Single Substrate": {
        "params": {
            "mu_max": (5.0, "Maximum specific growth rate [1/h]"),
            "Ks": (0.1, "Half-saturation constant [mmol/L]"),
            "Y": (0.5, "Yield coefficient [kgDW/mmol]"),
            "kd": (1e-6, "Decay rate [1/s]"),
        },
        "code": (
            "// Monod kinetics -- single substrate\n"
            "// C[0] = substrate concentration [mmol/L]\n"
            "// B[0] = biomass density [kgDW/m^3]\n"
            "\n"
            "double mu_max = {mu_max};  // Max specific growth rate [1/h]\n"
            "double Ks     = {Ks};      // Half-saturation [mmol/L]\n"
            "double Y      = {Y};       // Yield [kgDW/mmol]\n"
            "double kd     = {kd};      // Decay rate [1/s]\n"
            "\n"
            "// Monod term\n"
            "double monod = C[0] / (C[0] + Ks);\n"
            "\n"
            "// Substrate consumption (convert mu_max from 1/h to 1/s)\n"
            "subsR[0] = -(mu_max / 3600.0) * B[0] * monod / Y;\n"
            "\n"
            "// Biomass growth/decay\n"
            "bioR[0] = (mu_max / 3600.0) * B[0] * monod - kd * B[0];\n"
        ),
    },
    "Dual Substrate Monod": {
        "params": {
            "mu_max": (5.0, "Maximum specific growth rate [1/h]"),
            "Ks1": (0.1, "Half-saturation for substrate 1 [mmol/L]"),
            "Ks2": (0.05, "Half-saturation for substrate 2 [mmol/L]"),
            "Y": (0.5, "Yield coefficient [kgDW/mmol]"),
            "kd": (1e-6, "Decay rate [1/s]"),
        },
        "code": (
            "// Dual-substrate Monod kinetics\n"
            "// C[0] = electron donor, C[1] = electron acceptor\n"
            "\n"
            "double mu_max = {mu_max};\n"
            "double Ks1    = {Ks1};\n"
            "double Ks2    = {Ks2};\n"
            "double Y      = {Y};\n"
            "double kd     = {kd};\n"
            "\n"
            "double monod = (C[0] / (C[0] + Ks1)) * (C[1] / (C[1] + Ks2));\n"
            "\n"
            "subsR[0] = -(mu_max / 3600.0) * B[0] * monod / Y;\n"
            "subsR[1] = -(mu_max / 3600.0) * B[0] * monod / Y * 0.25;  // stoich\n"
            "\n"
            "bioR[0] = (mu_max / 3600.0) * B[0] * monod - kd * B[0];\n"
        ),
    },
    "Monod with Inhibition": {
        "params": {
            "mu_max": (5.0, "Maximum specific growth rate [1/h]"),
            "Ks": (0.1, "Half-saturation constant [mmol/L]"),
            "Ki": (1.0, "Inhibition constant [mmol/L]"),
            "Y": (0.5, "Yield coefficient [kgDW/mmol]"),
            "kd": (1e-6, "Decay rate [1/s]"),
        },
        "code": (
            "// Haldane / Andrews substrate inhibition\n"
            "\n"
            "double mu_max = {mu_max};\n"
            "double Ks     = {Ks};\n"
            "double Ki     = {Ki};\n"
            "double Y      = {Y};\n"
            "double kd     = {kd};\n"
            "\n"
            "double monod = C[0] / (Ks + C[0] + C[0]*C[0]/Ki);\n"
            "\n"
            "subsR[0] = -(mu_max / 3600.0) * B[0] * monod / Y;\n"
            "bioR[0]  = (mu_max / 3600.0) * B[0] * monod - kd * B[0];\n"
        ),
    },
    "Custom Biotic (Empty)": {
        "params": {
            "mu_max": (1.0, "User-defined max rate"),
            "Ks": (0.1, "User-defined half-saturation"),
            "Y": (0.5, "User-defined yield"),
            "kd": (1e-6, "User-defined decay"),
        },
        "code": (
            "// Custom biotic kinetics\n"
            "//\n"
            "// Available variables:\n"
            "//   C[i]  - substrate concentrations [mmol/L]\n"
            "//   B[j]  - biomass densities [kgDW/m^3]\n"
            "//   mask  - material number at this node\n"
            "//\n"
            "// Set output rates:\n"
            "//   subsR[i] - substrate rate [mmol/L/s]\n"
            "//   bioR[j]  - biomass rate  [kgDW/m^3/s]\n"
            "\n"
            "// Your code here...\n"
        ),
    },
}


# -------------------------------------------------------------------- #
#  Abiotic kinetics templates
# -------------------------------------------------------------------- #
_ABIOTIC_TEMPLATES = {
    "First-Order Decay": {
        "params": {
            "k1": (1e-4, "First-order rate constant [1/s]"),
        },
        "code": (
            "// First-order decay  (no biomass)\n"
            "// dC/dt = -k1 * C\n"
            "\n"
            "double k1 = {k1};  // Rate constant [1/s]\n"
            "\n"
            "subsR[0] = -k1 * C[0];\n"
        ),
    },
    "Bimolecular Reaction": {
        "params": {
            "k2": (1e-3, "Second-order rate constant [L/(mmol s)]"),
            "stoich_B": (1.0, "Stoichiometric coefficient for reactant B"),
        },
        "code": (
            "// Bimolecular reaction  A + stoich_B * B -> products\n"
            "// Rate = k2 * C_A * C_B\n"
            "\n"
            "double k2      = {k2};       // [L/(mmol s)]\n"
            "double stoichB = {stoich_B};  // stoichiometry of B\n"
            "\n"
            "double rate = k2 * C[0] * C[1];\n"
            "\n"
            "subsR[0] = -rate;\n"
            "subsR[1] = -stoichB * rate;\n"
        ),
    },
    "Reversible First-Order": {
        "params": {
            "kf": (1e-4, "Forward rate constant [1/s]"),
            "kr": (1e-5, "Reverse rate constant [1/s]"),
        },
        "code": (
            "// Reversible first-order  A <=> B\n"
            "// dC_A/dt = -kf*C_A + kr*C_B\n"
            "\n"
            "double kf = {kf};  // Forward [1/s]\n"
            "double kr = {kr};  // Reverse [1/s]\n"
            "\n"
            "subsR[0] = -kf * C[0] + kr * C[1];\n"
            "subsR[1] =  kf * C[0] - kr * C[1];\n"
        ),
    },
    "Mineral Dissolution (TST)": {
        "params": {
            "k_diss": (1e-8, "Dissolution rate constant [mol/m^2/s]"),
            "A_s": (100.0, "Reactive surface area [m^2/m^3]"),
            "C_eq": (0.01, "Equilibrium concentration [mmol/L]"),
        },
        "code": (
            "// Transition-State-Theory mineral dissolution\n"
            "// Rate = k_diss * A_s * (1 - C/C_eq)\n"
            "\n"
            "double k_diss = {k_diss};  // [mol/m^2/s]\n"
            "double A_s    = {A_s};     // [m^2/m^3]\n"
            "double C_eq   = {C_eq};    // [mmol/L]\n"
            "\n"
            "double saturation = C[0] / C_eq;\n"
            "if (saturation < 1.0) {{\n"
            "    subsR[0] = k_diss * A_s * (1.0 - saturation);\n"
            "}} else {{\n"
            "    subsR[0] = 0.0;\n"
            "}}\n"
        ),
    },
    "Custom Abiotic (Empty)": {
        "params": {
            "k1": (1e-4, "User-defined rate constant"),
        },
        "code": (
            "// Custom abiotic kinetics (no biomass terms)\n"
            "//\n"
            "// Available variables:\n"
            "//   C[i]  - substrate concentrations [mmol/L]\n"
            "//   mask  - material number at this node\n"
            "//\n"
            "// Set output rates:\n"
            "//   subsR[i] - substrate rate [mmol/L/s]\n"
            "//\n"
            "// Note: bioR is NOT available in abiotic mode.\n"
            "\n"
            "// Your code here...\n"
        ),
    },
}


# -------------------------------------------------------------------- #
#  Helpers to build a tab
# -------------------------------------------------------------------- #
def _make_code_editor():
    """Return a QTextEdit styled as a dark code editor."""
    editor = QTextEdit()
    editor.setFont(QFont("Consolas", 10))
    editor.setStyleSheet(
        "QTextEdit {"
        "  background-color: #1E1E1E;"
        "  color: #D4D4D4;"
        "  border: 1px solid #3C3C3C;"
        "}"
    )
    return editor


def _make_preview():
    """Return a read-only QTextEdit for the function preview."""
    preview = QTextEdit()
    preview.setReadOnly(True)
    preview.setMaximumHeight(150)
    preview.setFont(QFont("Consolas", 9))
    return preview


# -------------------------------------------------------------------- #
#  Single-tab widget (reused for biotic and abiotic)
# -------------------------------------------------------------------- #
class _KineticsTab(QWidget):
    """One tab inside the KineticsEditorDialog.

    Parameters
    ----------
    templates : dict
        Mapping of template name -> {"params": {...}, "code": str}.
    kinetics_type : str
        Either ``"biotic"`` or ``"abiotic"``.
    function_signature : str
        The C++ function signature shown in the preview pane.
    """

    def __init__(self, templates: dict, kinetics_type: str,
                 function_signature: str, parent=None):
        super().__init__(parent)
        self.templates = templates
        self.kinetics_type = kinetics_type
        self.function_signature = function_signature
        self._param_spins: dict[str, QDoubleSpinBox] = {}
        self._setup_ui()

    # ---- UI --------------------------------------------------------- #
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Horizontal)

        # -- Left: type selector + parameters -------------------------
        left = QWidget()
        left_layout = QVBoxLayout(left)

        # Type selector
        type_group = QGroupBox("Kinetics Type")
        type_layout = QVBoxLayout()

        self.type_combo = QComboBox()
        self.type_combo.addItems(list(self.templates.keys()))
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(self.type_combo)

        type_group.setLayout(type_layout)
        left_layout.addWidget(type_group)

        # Parameters (built dynamically)
        self.params_group = QGroupBox("Parameters")
        self.params_form = QFormLayout()
        self.params_group.setLayout(self.params_form)
        left_layout.addWidget(self.params_group)

        # Load-template button
        load_btn = QPushButton("Apply Template")
        load_btn.clicked.connect(self._load_template)
        left_layout.addWidget(load_btn)

        left_layout.addStretch()
        splitter.addWidget(left)

        # -- Right: code editor + preview -----------------------------
        right = QWidget()
        right_layout = QVBoxLayout(right)

        editor_label = QLabel("defineKinetics.hh Code:")
        editor_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(editor_label)

        self.code_editor = _make_code_editor()
        self.highlighter = CppHighlighter(self.code_editor.document())
        right_layout.addWidget(self.code_editor)

        preview_group = QGroupBox("Generated Function Preview")
        preview_layout = QVBoxLayout()
        self.preview_text = _make_preview()
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)

        splitter.addWidget(right)
        splitter.setSizes([300, 600])

        layout.addWidget(splitter)

        # Initialise with first template
        self._on_type_changed(self.type_combo.currentText())
        self._load_template()

    # ---- Slots ------------------------------------------------------ #
    def _on_type_changed(self, name: str):
        """Rebuild the parameter form for the newly selected template."""
        tpl = self.templates.get(name)
        if tpl is None:
            return

        # Clear existing rows
        while self.params_form.rowCount() > 0:
            self.params_form.removeRow(0)
        self._param_spins.clear()

        for pname, (default, tooltip) in tpl["params"].items():
            spin = QDoubleSpinBox()
            spin.setDecimals(8)
            spin.setRange(-1e20, 1e20)
            spin.setValue(default)
            spin.setToolTip(tooltip)
            spin.setMinimumWidth(140)
            self._param_spins[pname] = spin
            self.params_form.addRow(f"{pname}:", spin)

    def _load_template(self):
        """Insert the template code with current parameter values."""
        name = self.type_combo.currentText()
        tpl = self.templates.get(name)
        if tpl is None:
            return

        values = {k: spin.value() for k, spin in self._param_spins.items()}
        try:
            code = tpl["code"].format(**values)
        except KeyError:
            code = tpl["code"]

        self.code_editor.setPlainText(code)
        self._update_preview()

    def _update_preview(self):
        """Wrap the user code in the defineKinetics function signature."""
        code = self.code_editor.toPlainText()
        preview = self.function_signature + "{\n" + code + "\n}"
        self.preview_text.setPlainText(preview)

    # ---- Public API ------------------------------------------------- #
    def validate_syntax(self) -> list[str]:
        """Return a list of warning/error strings (empty == OK)."""
        code = self.code_editor.toPlainText()
        errors: list[str] = []

        if self.kinetics_type == "biotic":
            if "subsR" not in code and "bioR" not in code:
                errors.append(
                    "Warning: No rate assignments found (subsR or bioR)")
        else:
            if "subsR" not in code:
                errors.append(
                    "Warning: No substrate rate assignment found (subsR)")

        if code.count("{") != code.count("}"):
            errors.append("Error: Mismatched curly braces")
        if code.count("(") != code.count(")"):
            errors.append("Error: Mismatched parentheses")

        return errors

    def get_code(self) -> str:
        return self.code_editor.toPlainText()

    def get_kinetics_model(self) -> KineticsModel:
        """Build a KineticsModel from the current state."""
        params = {k: spin.value() for k, spin in self._param_spins.items()}
        return KineticsModel(
            name=self.type_combo.currentText(),
            kinetics_type=self.kinetics_type,
            description=f"{self.kinetics_type} kinetics",
            code=self.get_code(),
            parameters=params,
        )

    def set_kinetics_model(self, model: KineticsModel):
        """Populate the tab from an existing KineticsModel."""
        # Try to select matching template name
        idx = self.type_combo.findText(model.name)
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        # Push stored parameters into spin boxes
        for pname, value in model.parameters.items():
            spin = self._param_spins.get(pname)
            if spin is not None:
                spin.setValue(value)

        self.code_editor.setPlainText(model.code)
        self._update_preview()


# -------------------------------------------------------------------- #
#  Main dialog
# -------------------------------------------------------------------- #
class KineticsEditorDialog(QDialog):
    """Dialog with two tabs for editing biotic and abiotic kinetics."""

    _BIOTIC_SIGNATURE = (
        "void defineRxnKinetics(\n"
        "    std::vector<T>& B,      // Biomass [kgDW/m^3]\n"
        "    std::vector<T>& C,      // Substrates [mmol/L]\n"
        "    std::vector<T>& subsR,  // Substrate rates [mmol/L/s]\n"
        "    std::vector<T>& bioR,   // Biomass rates [kgDW/m^3/s]\n"
        "    int mask)               // Material number\n"
    )

    _ABIOTIC_SIGNATURE = (
        "void defineAbioticKinetics(\n"
        "    std::vector<T>& C,      // Substrates [mmol/L]\n"
        "    std::vector<T>& subsR,  // Substrate rates [mmol/L/s]\n"
        "    int mask)               // Material number\n"
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kinetics Editor")
        self.setMinimumSize(950, 750)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ---- Tab widget ----
        self.tabs = QTabWidget()

        self.biotic_tab = _KineticsTab(
            templates=_BIOTIC_TEMPLATES,
            kinetics_type="biotic",
            function_signature=self._BIOTIC_SIGNATURE,
        )
        self.tabs.addTab(self.biotic_tab, "Biotic Kinetics")

        self.abiotic_tab = _KineticsTab(
            templates=_ABIOTIC_TEMPLATES,
            kinetics_type="abiotic",
            function_signature=self._ABIOTIC_SIGNATURE,
        )
        self.tabs.addTab(self.abiotic_tab, "Abiotic Kinetics")

        layout.addWidget(self.tabs)

        # ---- Bottom button bar ----
        button_layout = QHBoxLayout()

        validate_btn = QPushButton("Validate Syntax")
        validate_btn.clicked.connect(self._validate_current_tab)
        button_layout.addWidget(validate_btn)

        preview_btn = QPushButton("Update Preview")
        preview_btn.clicked.connect(self._update_current_preview)
        button_layout.addWidget(preview_btn)

        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    # ---- Convenience accessors ------------------------------------- #
    def _current_tab(self) -> _KineticsTab:
        return self.tabs.currentWidget()

    def _validate_current_tab(self):
        errors = self._current_tab().validate_syntax()
        if errors:
            QMessageBox.warning(self, "Validation", "\n".join(errors))
        else:
            QMessageBox.information(self, "Validation",
                                    "Syntax appears valid!")

    def _update_current_preview(self):
        self._current_tab()._update_preview()

    # ---- Public API ------------------------------------------------ #
    def get_biotic_kinetics_code(self) -> str:
        """Return the biotic kinetics C++ code."""
        return self.biotic_tab.get_code()

    def get_abiotic_kinetics_code(self) -> str:
        """Return the abiotic kinetics C++ code."""
        return self.abiotic_tab.get_code()

    def get_biotic_model(self) -> KineticsModel:
        """Return a KineticsModel for the biotic tab."""
        return self.biotic_tab.get_kinetics_model()

    def get_abiotic_model(self) -> KineticsModel:
        """Return a KineticsModel for the abiotic tab."""
        return self.abiotic_tab.get_kinetics_model()

    def set_biotic_model(self, model: KineticsModel):
        """Load an existing biotic KineticsModel into the dialog."""
        self.biotic_tab.set_kinetics_model(model)

    def set_abiotic_model(self, model: KineticsModel):
        """Load an existing abiotic KineticsModel into the dialog."""
        self.abiotic_tab.set_kinetics_model(model)

    def get_kinetics_code(self) -> str:
        """Legacy helper -- returns the active tab's code."""
        return self._current_tab().get_code()
