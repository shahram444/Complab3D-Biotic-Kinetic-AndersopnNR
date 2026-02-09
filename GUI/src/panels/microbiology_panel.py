"""Microbiology panel - microbe species management."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget,
    QPushButton, QListWidget, QGroupBox, QTabWidget, QComboBox,
    QLineEdit, QDoubleSpinBox,
)
from PySide6.QtCore import Qt

from .base_panel import BasePanel
from ..core.project import Microbe


class MicrobeEditor(QWidget):
    """Editor for a single microbe's properties."""

    def __init__(self, on_change, parent=None):
        super().__init__(parent)
        self._on_change = on_change
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()

        # --- General Tab ---
        gen_w = QWidget()
        gf = QFormLayout(gen_w)
        gf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        gf.setHorizontalSpacing(12)
        gf.setVerticalSpacing(8)

        self._name = QLineEdit()
        self._name.textChanged.connect(self._changed)

        self._solver_type = QComboBox()
        self._solver_type.addItems(["CA", "LBM", "FD", "kinetics"])
        self._solver_type.currentIndexChanged.connect(self._on_solver_changed)

        self._reaction_type = QComboBox()
        self._reaction_type.addItems(["kinetics", "none"])
        self._reaction_type.currentIndexChanged.connect(self._changed)

        self._material_numbers = QLineEdit()
        self._material_numbers.setPlaceholderText("e.g., 3 6")
        self._material_numbers.textChanged.connect(self._changed)

        self._initial_densities = QLineEdit()
        self._initial_densities.setPlaceholderText("e.g., 99.0 99.0")
        self._initial_densities.textChanged.connect(self._changed)

        self._decay = QDoubleSpinBox()
        self._decay.setRange(0, 1e30)
        self._decay.setDecimals(12)
        self._decay.setMinimumWidth(160)
        self._decay.valueChanged.connect(self._changed)

        gf.addRow("Name:", self._name)
        gf.addRow("Solver type:", self._solver_type)
        gf.addRow("Reaction type:", self._reaction_type)
        gf.addRow("Material numbers:", self._material_numbers)
        gf.addRow("Initial densities [kg/m3]:", self._initial_densities)
        gf.addRow("Decay coefficient [1/s]:", self._decay)

        solver_info = QLabel(
            "CA: Cellular automata for sessile biofilm (attached to surface)\n"
            "LBM: Lattice Boltzmann for planktonic bacteria (transported by flow)\n"
            "FD: Finite difference biomass diffusion\n"
            "kinetics: Kinetics only, no biomass transport")
        solver_info.setProperty("info", True)
        solver_info.setWordWrap(True)
        gf.addRow(solver_info)

        tabs.addTab(gen_w, "General")

        # --- Kinetics Tab ---
        kin_w = QWidget()
        kf = QFormLayout(kin_w)
        kf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        kf.setHorizontalSpacing(12)
        kf.setVerticalSpacing(8)

        self._ks = QLineEdit()
        self._ks.setPlaceholderText("space-separated, one per substrate")
        self._ks.textChanged.connect(self._changed)

        self._vmax = QLineEdit()
        self._vmax.setPlaceholderText("space-separated, one per substrate")
        self._vmax.textChanged.connect(self._changed)

        kf.addRow("Half-saturation Ks [mol/L]:", self._ks)
        kf.addRow("Max uptake flux Vmax:", self._vmax)

        ks_info = QLabel(
            "Provide one value per substrate, space-separated.\n"
            "Set to 0.0 for substrates not consumed by this microbe.\n"
            "Monod kinetics: mu = Vmax * S / (Ks + S)")
        ks_info.setProperty("info", True)
        ks_info.setWordWrap(True)
        kf.addRow(ks_info)

        tabs.addTab(kin_w, "Kinetics")

        # --- Biofilm Tab ---
        bio_w = QWidget()
        bf = QFormLayout(bio_w)
        bf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        bf.setHorizontalSpacing(12)
        bf.setVerticalSpacing(8)

        self._viscosity = QDoubleSpinBox()
        self._viscosity.setRange(0.0, 10000.0)
        self._viscosity.setDecimals(2)
        self._viscosity.setValue(10.0)
        self._viscosity.setMinimumWidth(120)
        self._viscosity.valueChanged.connect(self._changed)

        bf.addRow("Viscosity ratio in biofilm:", self._viscosity)

        visc_info = QLabel(
            "Ratio of effective viscosity inside biofilm to bulk fluid viscosity.\n"
            "Value of 1.0 means no flow reduction (planktonic).\n"
            "Higher values reduce flow through biofilm regions.")
        visc_info.setProperty("info", True)
        visc_info.setWordWrap(True)
        bf.addRow(visc_info)

        tabs.addTab(bio_w, "Biofilm")

        # --- Boundary Conditions Tab ---
        bc_w = QWidget()
        bcf = QFormLayout(bc_w)
        bcf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        bcf.setHorizontalSpacing(12)
        bcf.setVerticalSpacing(8)

        self._left_bc_type = QComboBox()
        self._left_bc_type.addItems(["Dirichlet", "Neumann"])
        self._left_bc_type.currentIndexChanged.connect(self._changed)

        self._left_bc_val = QDoubleSpinBox()
        self._left_bc_val.setRange(-1e30, 1e30)
        self._left_bc_val.setDecimals(6)
        self._left_bc_val.setMinimumWidth(160)
        self._left_bc_val.valueChanged.connect(self._changed)

        self._right_bc_type = QComboBox()
        self._right_bc_type.addItems(["Dirichlet", "Neumann"])
        self._right_bc_type.currentIndexChanged.connect(self._changed)

        self._right_bc_val = QDoubleSpinBox()
        self._right_bc_val.setRange(-1e30, 1e30)
        self._right_bc_val.setDecimals(6)
        self._right_bc_val.setMinimumWidth(160)
        self._right_bc_val.valueChanged.connect(self._changed)

        bcf.addRow("Inlet (left) BC type:", self._left_bc_type)
        bcf.addRow("Inlet (left) BC value:", self._left_bc_val)
        bcf.addRow("Outlet (right) BC type:", self._right_bc_type)
        bcf.addRow("Outlet (right) BC value:", self._right_bc_val)

        tabs.addTab(bc_w, "Boundaries")

        layout.addWidget(tabs)

    def _changed(self):
        if self._on_change:
            self._on_change()

    def _on_solver_changed(self):
        solver = self._solver_type.currentText()
        # For planktonic (LBM), viscosity ratio is typically 1.0
        if solver == "LBM":
            self._viscosity.setValue(1.0)
        self._changed()

    def load_microbe(self, m):
        for w in [self._name, self._solver_type, self._reaction_type,
                   self._material_numbers, self._initial_densities, self._decay,
                   self._ks, self._vmax, self._viscosity,
                   self._left_bc_type, self._left_bc_val,
                   self._right_bc_type, self._right_bc_val]:
            w.blockSignals(True)

        self._name.setText(m.name)
        idx = self._solver_type.findText(m.solver_type)
        if idx >= 0:
            self._solver_type.setCurrentIndex(idx)
        idx = self._reaction_type.findText(m.reaction_type)
        if idx >= 0:
            self._reaction_type.setCurrentIndex(idx)
        self._material_numbers.setText(m.material_numbers)
        self._initial_densities.setText(m.initial_densities)
        self._decay.setValue(m.decay_coefficient)
        self._ks.setText(m.half_saturation_constants)
        self._vmax.setText(m.max_uptake_flux)
        self._viscosity.setValue(m.viscosity_ratio)

        idx_l = self._left_bc_type.findText(m.left_bc_type)
        if idx_l >= 0:
            self._left_bc_type.setCurrentIndex(idx_l)
        self._left_bc_val.setValue(m.left_bc_value)
        idx_r = self._right_bc_type.findText(m.right_bc_type)
        if idx_r >= 0:
            self._right_bc_type.setCurrentIndex(idx_r)
        self._right_bc_val.setValue(m.right_bc_value)

        for w in [self._name, self._solver_type, self._reaction_type,
                   self._material_numbers, self._initial_densities, self._decay,
                   self._ks, self._vmax, self._viscosity,
                   self._left_bc_type, self._left_bc_val,
                   self._right_bc_type, self._right_bc_val]:
            w.blockSignals(False)

    def save_to_microbe(self, m):
        m.name = self._name.text().strip()
        m.solver_type = self._solver_type.currentText()
        m.reaction_type = self._reaction_type.currentText()
        m.material_numbers = self._material_numbers.text().strip()
        m.initial_densities = self._initial_densities.text().strip()
        m.decay_coefficient = self._decay.value()
        m.half_saturation_constants = self._ks.text().strip()
        m.max_uptake_flux = self._vmax.text().strip()
        m.viscosity_ratio = self._viscosity.value()
        m.left_bc_type = self._left_bc_type.currentText()
        m.left_bc_value = self._left_bc_val.value()
        m.right_bc_type = self._right_bc_type.currentText()
        m.right_bc_value = self._right_bc_val.value()

    def get_name(self):
        return self._name.text().strip()


class MicrobiologyPanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._microbes = []
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("Microbiology"))
        layout.addWidget(self._create_subheading(
            "Define microbial species with growth kinetics and transport behavior."))

        body = QHBoxLayout()
        body.setSpacing(12)

        # Left: list + global settings
        left = QVBoxLayout()
        left.setSpacing(4)

        self._list = QListWidget()
        self._list.setFixedWidth(200)
        self._list.currentRowChanged.connect(self._on_select)

        btn_row = QHBoxLayout()
        self._add_btn = QPushButton("Add")
        self._add_btn.clicked.connect(self._add_microbe)
        self._remove_btn = QPushButton("Remove")
        self._remove_btn.clicked.connect(self._remove_microbe)
        btn_row.addWidget(self._add_btn)
        btn_row.addWidget(self._remove_btn)

        left.addWidget(QLabel("Microbial Species"))
        left.addWidget(self._list)
        left.addLayout(btn_row)

        # Global settings
        global_group = self._create_group("Global Settings")
        gf = self._create_form()
        self._max_biomass = self._create_double_spin(0.0, 1e6, 100.0, 2, 1.0, "kg/m3")
        self._thrd_fraction = self._create_double_spin(0.0, 1.0, 0.1, 3, 0.01)
        self._ca_method = self._create_combo(["half", "fraction", "none"], "half")
        gf.addRow("Max biomass density:", self._max_biomass)
        gf.addRow("Biofilm threshold fraction:", self._thrd_fraction)
        gf.addRow("CA expansion method:", self._ca_method)
        global_group.setLayout(gf)
        left.addWidget(global_group)

        ca_info = QLabel(
            "half: Push half of excess biomass to preferred neighbor\n"
            "fraction: Distribute excess equally to all valid neighbors\n"
            "none: No CA expansion (use for planktonic simulations)")
        ca_info.setProperty("info", True)
        ca_info.setWordWrap(True)
        left.addWidget(ca_info)

        # Right: editor
        self._editor = MicrobeEditor(self._on_editor_change)

        body.addLayout(left)
        body.addWidget(self._editor, 1)
        layout.addLayout(body, 1)

        outer.addWidget(self._create_scroll_area(w))

    def _add_microbe(self):
        idx = len(self._microbes)
        m = Microbe(name=f"microbe{idx}", solver_type="CA",
                    reaction_type="kinetics", material_numbers="3",
                    initial_densities="10.0 10.0",
                    decay_coefficient=1.0e-9, viscosity_ratio=10.0)
        self._microbes.append(m)
        self._list.addItem(m.name)
        self._list.setCurrentRow(len(self._microbes) - 1)
        self._emit_changed()

    def _remove_microbe(self):
        row = self._list.currentRow()
        if row < 0 or len(self._microbes) == 0:
            return
        self._microbes.pop(row)
        self._list.takeItem(row)
        if self._microbes:
            self._list.setCurrentRow(min(row, len(self._microbes) - 1))
        self._emit_changed()

    def _on_select(self, row):
        if row < 0 or row >= len(self._microbes):
            return
        self._editor.load_microbe(self._microbes[row])

    def _on_editor_change(self):
        row = self._list.currentRow()
        if row < 0 or row >= len(self._microbes):
            return
        self._editor.save_to_microbe(self._microbes[row])
        name = self._editor.get_name()
        if name:
            self._list.item(row).setText(name)
        self._emit_changed()

    def _populate_fields(self):
        if not self._project:
            return
        self._microbes = [Microbe(**m.to_dict()) for m in self._project.microbes]
        self._list.clear()
        for m in self._microbes:
            self._list.addItem(m.name)
        if self._microbes:
            self._list.setCurrentRow(0)

        mb = self._project.microbiology
        self._max_biomass.setValue(mb.max_biomass_density)
        self._thrd_fraction.setValue(mb.thrd_biofilm_fraction)
        idx = self._ca_method.findText(mb.ca_method)
        if idx >= 0:
            self._ca_method.setCurrentIndex(idx)

    def collect_data(self, project):
        row = self._list.currentRow()
        if 0 <= row < len(self._microbes):
            self._editor.save_to_microbe(self._microbes[row])
        project.microbes = [Microbe(**m.to_dict()) for m in self._microbes]
        project.microbiology.max_biomass_density = self._max_biomass.value()
        project.microbiology.thrd_biofilm_fraction = self._thrd_fraction.value()
        project.microbiology.ca_method = self._ca_method.currentText()
