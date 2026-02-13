"""
Kinetics Editor Dialog - Edit custom reaction kinetics
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


class CppHighlighter(QSyntaxHighlighter):
    """Simple C++ syntax highlighter"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.highlighting_rules = []
        
        # Keywords
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#569CD6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = [
            "if", "else", "for", "while", "return", "void", "int", "float",
            "double", "bool", "true", "false", "const", "auto"
        ]
        for word in keywords:
            pattern = rf"\b{word}\b"
            self.highlighting_rules.append((re.compile(pattern), keyword_format))
            
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#B5CEA8"))
        self.highlighting_rules.append((
            re.compile(r"\b[0-9]+\.?[0-9]*([eE][-+]?[0-9]+)?\b"),
            number_format
        ))
        
        # Strings
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#CE9178"))
        self.highlighting_rules.append((
            re.compile(r'"[^"]*"'),
            string_format
        ))
        
        # Comments
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6A9955"))
        self.highlighting_rules.append((
            re.compile(r"//[^\n]*"),
            comment_format
        ))
        
    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


class KineticsEditorDialog(QDialog):
    """Dialog for editing reaction kinetics"""
    
    TEMPLATES = {
        "Monod Single Substrate": '''// Monod kinetics with single substrate
// C[0] = substrate concentration [mmol/L]
// B[0] = biomass density [kgDW/m³]

double Ks = {ks};     // Half-saturation constant [mmol/L]
double Vmax = {vmax}; // Maximum uptake rate [mmol/kgDW/h]
double Y = {yield_coeff};   // Yield coefficient [kgDW/mmol]
double kd = {kd};     // Decay rate [1/s]

// Monod term
double monod = C[0] / (C[0] + Ks);

// Substrate consumption rate
subsR[0] = -Vmax * B[0] * monod / 3600.0;  // Convert to per second

// Biomass growth rate
bioR[0] = Y * (-subsR[0]) - kd * B[0];
''',
        "Dual Substrate": '''// Dual-substrate Monod kinetics
// Example: Carbon source (C[0]) and electron acceptor (C[1])

double Ks1 = {ks1};   // Half-saturation for substrate 1
double Ks2 = {ks2};   // Half-saturation for substrate 2
double Vmax = {vmax}; // Maximum rate
double Y = {yield_coeff};   // Yield
double kd = {kd};     // Decay

// Dual Monod
double monod = (C[0]/(C[0]+Ks1)) * (C[1]/(C[1]+Ks2));

// Rates
subsR[0] = -Vmax * B[0] * monod / 3600.0;
subsR[1] = -Vmax * B[0] * monod / 3600.0 * 0.25;  // stoichiometry

bioR[0] = Y * (-subsR[0]) - kd * B[0];
''',
        "Inhibition": '''// Substrate inhibition kinetics
// Ki = inhibition constant

double Ks = {ks};
double Ki = {ki};     // Inhibition constant
double Vmax = {vmax};
double Y = {yield_coeff};
double kd = {kd};

// Haldane/Andrews inhibition
double monod = C[0] / (Ks + C[0] + C[0]*C[0]/Ki);

subsR[0] = -Vmax * B[0] * monod / 3600.0;
bioR[0] = Y * (-subsR[0]) - kd * B[0];
''',
        "Adsorption-Desorption": '''// Adsorption-desorption with reaction
// Based on Geobacter case study

double kads = {kads};   // Adsorption rate [1/s]
double kdes = {kdes};   // Desorption rate [1/s]
double mu = {mu};       // Decay rate [1/s]

// Adsorption of substrate to biomass
subsR[0] = -kads * C[0] * B[0] + kdes * B[0];

// Biomass change due to adsorption/decay
bioR[0] = kads * C[0] * B[0] - kdes * B[0] - mu * B[0];
''',
        "Abiotic Decay Chain": '''// Abiotic sequential decay chain: A -> B -> C
// Three-species Bateman equations
// C[0] = Parent A, C[1] = Daughter B, C[2] = GrandDaughter C

double k1 = 1e-4;  // Decay rate A -> B [1/s]
double k2 = 5e-5;  // Decay rate B -> C [1/s]

// First-order decay rates
subsR[0] = -k1 * C[0];              // Parent decays
subsR[1] = k1 * C[0] - k2 * C[1];  // Daughter: produced from A, decays to C
subsR[2] = k2 * C[1];               // GrandDaughter: produced from B
''',
        "Custom (Empty)": '''// Custom kinetics
// Define your own reaction rates here
//
// Available variables:
//   C[i] - substrate concentrations [mmol/L]
//   B[j] - biomass densities [kgDW/m³]
//   mask - material number at this node
//
// Set output rates:
//   subsR[i] - substrate rate [mmol/L/s]
//   bioR[j] - biomass rate [kgDW/m³/s]

// Your code here...
'''
    }
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kinetics Editor")
        self.setMinimumSize(900, 700)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - templates and parameters
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Template selection
        template_group = QGroupBox("Templates")
        template_layout = QVBoxLayout()
        
        self.template_list = QListWidget()
        for name in self.TEMPLATES.keys():
            self.template_list.addItem(name)
        self.template_list.currentRowChanged.connect(self._on_template_selected)
        template_layout.addWidget(self.template_list)
        
        load_btn = QPushButton("Load Template")
        load_btn.clicked.connect(self._load_template)
        template_layout.addWidget(load_btn)
        
        template_group.setLayout(template_layout)
        left_layout.addWidget(template_group)
        
        # Parameters
        params_group = QGroupBox("Common Parameters")
        params_layout = QFormLayout()
        
        self.ks_spin = QDoubleSpinBox()
        self.ks_spin.setRange(0, 1000)
        self.ks_spin.setDecimals(4)
        self.ks_spin.setValue(0.1)
        params_layout.addRow("Ks [mmol/L]:", self.ks_spin)
        
        self.vmax_spin = QDoubleSpinBox()
        self.vmax_spin.setRange(0, 1000)
        self.vmax_spin.setDecimals(4)
        self.vmax_spin.setValue(5.0)
        params_layout.addRow("Vmax [mmol/kgDW/h]:", self.vmax_spin)
        
        self.yield_spin = QDoubleSpinBox()
        self.yield_spin.setRange(0, 10)
        self.yield_spin.setDecimals(4)
        self.yield_spin.setValue(0.5)
        params_layout.addRow("Yield [kgDW/mmol]:", self.yield_spin)
        
        self.kd_spin = QDoubleSpinBox()
        self.kd_spin.setRange(0, 1)
        self.kd_spin.setDecimals(8)
        self.kd_spin.setValue(1e-6)
        params_layout.addRow("Decay [1/s]:", self.kd_spin)
        
        params_group.setLayout(params_layout)
        left_layout.addWidget(params_group)
        
        splitter.addWidget(left_panel)
        
        # Right panel - code editor
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        editor_label = QLabel("defineKinetics.hh Code:")
        editor_label.setStyleSheet("font-weight: bold;")
        right_layout.addWidget(editor_label)
        
        self.code_editor = QTextEdit()
        self.code_editor.setFont(QFont("Consolas", 10))
        self.code_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3C3C3C;
            }
        """)
        self.highlighter = CppHighlighter(self.code_editor.document())
        right_layout.addWidget(self.code_editor)
        
        # Preview
        preview_group = QGroupBox("Generated Function Preview")
        preview_layout = QVBoxLayout()
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(150)
        self.preview_text.setFont(QFont("Consolas", 9))
        preview_layout.addWidget(self.preview_text)
        preview_group.setLayout(preview_layout)
        right_layout.addWidget(preview_group)
        
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 600])
        
        layout.addWidget(splitter)
        
        # Recompilation help
        recomp_group = QGroupBox("Recompilation Required")
        recomp_layout = QVBoxLayout()
        recomp_label = QLabel(
            "<b>After modifying defineKinetics.hh you must recompile CompLaB:</b><br>"
            "<pre>"
            "cd /path/to/complab/build\n"
            "cmake .. -DCMAKE_BUILD_TYPE=Release\n"
            "make -j$(nproc)"
            "</pre>"
            "<b>The kinetics file location:</b><br>"
            "<code>src/complab3d_processors_part1.hh</code> contains defineRxnKinetics()<br><br>"
            "<b>Steps:</b><br>"
            "1. Save the kinetics code above to <code>defineKinetics.hh</code><br>"
            "2. Place it in the CompLaB source directory<br>"
            "3. Recompile with cmake/make<br>"
            "4. Copy the new <code>complab</code> binary to your project or PATH"
        )
        recomp_label.setWordWrap(True)
        recomp_label.setTextFormat(Qt.RichText)
        recomp_label.setStyleSheet("padding: 8px; font-size: 11px;")
        recomp_layout.addWidget(recomp_label)
        recomp_group.setLayout(recomp_layout)
        layout.addWidget(recomp_group)

        # Buttons
        button_layout = QHBoxLayout()

        validate_btn = QPushButton("Validate Syntax")
        validate_btn.clicked.connect(self._validate_syntax)
        button_layout.addWidget(validate_btn)

        preview_btn = QPushButton("Update Preview")
        preview_btn.clicked.connect(self._update_preview)
        button_layout.addWidget(preview_btn)

        button_layout.addStretch()

        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)
        
        # Load default template
        self.template_list.setCurrentRow(0)
        self._load_template()
        
    def _on_template_selected(self, index):
        """Handle template selection"""
        pass
        
    def _load_template(self):
        """Load selected template"""
        item = self.template_list.currentItem()
        if not item:
            return
            
        template_name = item.text()
        template = self.TEMPLATES.get(template_name, "")
        
        # Substitute parameters
        try:
            code = template.format(
                ks=self.ks_spin.value(),
                ks1=self.ks_spin.value(),
                ks2=self.ks_spin.value() * 0.5,
                ki=self.ks_spin.value() * 10,
                vmax=self.vmax_spin.value(),
                yield_coeff=self.yield_spin.value(),
                kd=self.kd_spin.value(),
                kads="2.1e-3",
                kdes="1.2e-5",
                mu=self.kd_spin.value()
            )
        except (KeyError, IndexError):
            code = template  # Use raw template if substitution fails
        
        self.code_editor.setPlainText(code)
        self._update_preview()
        
    def _validate_syntax(self):
        """Basic syntax validation"""
        code = self.code_editor.toPlainText()
        
        # Check for common errors
        errors = []
        
        if "subsR" not in code and "bioR" not in code:
            errors.append("Warning: No rate assignments found (subsR or bioR)")
            
        # Check bracket matching
        if code.count("{") != code.count("}"):
            errors.append("Error: Mismatched curly braces")
        if code.count("(") != code.count(")"):
            errors.append("Error: Mismatched parentheses")
            
        if errors:
            QMessageBox.warning(self, "Validation", "\n".join(errors))
        else:
            QMessageBox.information(self, "Validation", "Syntax appears valid!")
            
    def _update_preview(self):
        """Update the function preview"""
        code = self.code_editor.toPlainText()
        
        preview = '''void defineRxnKinetics(
    std::vector<T>& B,      // Biomass [kgDW/m³]
    std::vector<T>& C,      // Substrates [mmol/L]
    std::vector<T>& subsR,  // Substrate rates [mmol/L/s]
    std::vector<T>& bioR,   // Biomass rates [kgDW/m³/s]
    int mask)               // Material number
{
''' + code + '''
}'''
        
        self.preview_text.setPlainText(preview)
        
    def get_kinetics_code(self):
        """Get the kinetics code"""
        return self.code_editor.toPlainText()
