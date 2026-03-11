"""Microbiology panel - microbe species management with full parameter editing."""

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QWidget,
    QPushButton, QListWidget, QTabWidget, QComboBox,
)
from PySide6.QtCore import Signal, Qt
from .base_panel import BasePanel
from ..core.project import Microbe
from ..widgets.collapsible_section import CollapsibleSection


class MicrobiologyPanel(BasePanel):
    """Microbe management with global settings and per-microbe editor.

    Supports CA (cellular automata), LBM (lattice Boltzmann),
    and FD (finite difference) solver types.
    Material numbers can be multiple (e.g., '3 6' for core+fringe biofilm).
    """

    microbes_changed = Signal(list)  # emits list of microbe names

    def __init__(self, parent=None):
        super().__init__("Microbiology", parent)
        self._microbes = []
        self._current_idx = -1
        self._loading = False  # guard against signal cascades
        self._build_ui()

    def _build_ui(self):
        # Global settings
        self.add_section("Global Biomass Settings")
        gform = self.add_form()

        self.max_density = self.make_double_spin(100.0, 0, 1e12, 4)
        self.max_density.setToolTip("Maximum biomass density (required for CA solver).")
        gform.addRow("Max biomass density:", self.max_density)

        self.thrd_fraction = self.make_double_spin(0.1, 0, 1.0, 4, step=0.01)
        self.thrd_fraction.setToolTip(
            "Threshold biofilm fraction for CA expansion.\n"
            "When biomass exceeds max_density * threshold, expansion occurs.")
        gform.addRow("Threshold fraction:", self.thrd_fraction)

        self.ca_method = self.make_combo(["fraction", "half"])
        self.ca_method.setToolTip(
            "CA biomass expansion method:\n"
            "  fraction: Proportional distribution (default)\n"
            "  half: Split equally between parent and child\n"
            "Note: C++ solver only accepts 'fraction' or 'half'.")
        gform.addRow("CA method:", self.ca_method)

        # Microbe list
        self.add_section("Microbe Species")
        row = QHBoxLayout()
        self._list = QListWidget()
        self._list.setMaximumHeight(100)
        self._list.currentRowChanged.connect(self._on_select)
        row.addWidget(self._list, 1)

        btn_col = QVBoxLayout()
        add_btn = self.make_button("Add")
        add_btn.clicked.connect(self._add_microbe)
        rem_btn = self.make_button("Remove")
        rem_btn.setProperty("danger", True)
        rem_btn.clicked.connect(self._remove_microbe)
        btn_col.addWidget(add_btn)
        btn_col.addWidget(rem_btn)
        btn_col.addStretch()
        row.addLayout(btn_col)
        self.add_layout(row)

        # Per-microbe editor tabs
        self._tabs = QTabWidget()
        self.add_widget(self._tabs)

        # Tab 1: General
        t1 = QWidget()
        f1 = QFormLayout(t1)
        f1.setLabelAlignment(Qt.AlignmentFlag.AlignRight)  # AlignRight
        f1.setHorizontalSpacing(12)
        f1.setVerticalSpacing(6)

        self._name = self.make_line_edit("", "Microbe name")
        self._name.textChanged.connect(self._on_edited)
        f1.addRow("Name:", self._name)

        self._solver = self.make_combo(["CA", "LBM", "FD"])
        self._solver.currentTextChanged.connect(self._on_solver_changed)
        f1.addRow("Solver type:", self._solver)

        self._reaction = self.make_combo(["kinetics", "none"])
        self._reaction.currentTextChanged.connect(self._on_edited)
        f1.addRow("Reaction type:", self._reaction)

        self._mat_num = self.make_line_edit("3", "e.g. 3 or 3 6")
        self._mat_num.setToolTip(
            "Material number(s) in the geometry file.\n"
            "Space-separated for multiple (e.g., '3 6' for core + fringe).\n"
            "Length must match initial_densities.")
        self._mat_num.textChanged.connect(self._on_edited)
        f1.addRow("Material number(s):", self._mat_num)

        self._init_dens = self.make_line_edit("99.0", "e.g. 99.0 or 99.0 99.0")
        self._init_dens.setToolTip(
            "Initial biomass densities, space-separated.\n"
            "Must have same count as material numbers.")
        self._init_dens.textChanged.connect(self._on_edited)
        f1.addRow("Initial densities:", self._init_dens)

        self._tabs.addTab(t1, "General")

        # Tab 2: Kinetics
        t2 = QWidget()
        f2 = QFormLayout(t2)
        f2.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        f2.setHorizontalSpacing(12)
        f2.setVerticalSpacing(6)

        self._decay = self.make_double_spin(0.0, 0, 1e6, 10)
        self._decay.valueChanged.connect(self._on_edited)
        f2.addRow("Decay coefficient:", self._decay)

        self._ks = self.make_line_edit("", "Space-separated, one per substrate")
        self._ks.setToolTip("Half-saturation constants, one per substrate.")
        self._ks.textChanged.connect(self._on_edited)
        f2.addRow("Half-saturation (Ks):", self._ks)

        self._vmax = self.make_line_edit("", "Space-separated, one per substrate")
        self._vmax.setToolTip("Maximum uptake flux, one per substrate.")
        self._vmax.textChanged.connect(self._on_edited)
        f2.addRow("Max uptake flux (Vmax):", self._vmax)

        self._tabs.addTab(t2, "Kinetics")

        # Tab 3: Biofilm / Physical
        t3 = QWidget()
        f3 = QFormLayout(t3)
        f3.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        f3.setHorizontalSpacing(12)
        f3.setVerticalSpacing(6)

        self._visc_ratio = self.make_double_spin(10.0, 0, 1e6, 4)
        self._visc_ratio.setToolTip(
            "Viscosity ratio in biofilm (required for CA solver).\n"
            "Reduces flow velocity within biofilm voxels.")
        self._visc_ratio.valueChanged.connect(self._on_edited)
        f3.addRow("Viscosity ratio in biofilm:", self._visc_ratio)

        self._bd_pore = self.make_double_spin(-99.0, -100, 1e6, 10)
        self._bd_pore.setToolTip(
            "Biomass diffusion coefficient in pore (required for FD solver).\n"
            "-99 = not applicable.")
        self._bd_pore.valueChanged.connect(self._on_edited)
        f3.addRow("Biomass diffusion in pore:", self._bd_pore)

        self._bd_biofilm = self.make_double_spin(-99.0, -100, 1e6, 10)
        self._bd_biofilm.setToolTip(
            "Biomass diffusion coefficient in biofilm (required for FD solver).\n"
            "-99 = not applicable.")
        self._bd_biofilm.valueChanged.connect(self._on_edited)
        f3.addRow("Biomass diffusion in biofilm:", self._bd_biofilm)

        self._tabs.addTab(t3, "Physical")

        # Tab 4: Boundary Conditions
        t4 = QWidget()
        f4 = QFormLayout(t4)
        f4.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        f4.setHorizontalSpacing(12)
        f4.setVerticalSpacing(6)

        self._left_type = self.make_combo(["Neumann", "Dirichlet"])
        self._left_type.currentIndexChanged.connect(self._on_edited)
        f4.addRow("Left BC type:", self._left_type)

        self._left_val = self.make_double_spin(0.0, -1e12, 1e12, 6)
        self._left_val.valueChanged.connect(self._on_edited)
        f4.addRow("Left BC value:", self._left_val)

        self._right_type = self.make_combo(["Neumann", "Dirichlet"])
        self._right_type.currentIndexChanged.connect(self._on_edited)
        f4.addRow("Right BC type:", self._right_type)

        self._right_val = self.make_double_spin(0.0, -1e12, 1e12, 6)
        self._right_val.valueChanged.connect(self._on_edited)
        f4.addRow("Right BC value:", self._right_val)

        self._tabs.addTab(t4, "Boundaries")

        self.add_stretch()

    def _on_solver_changed(self, solver):
        is_ca = solver == "CA"
        is_fd = solver == "FD"
        self._visc_ratio.setEnabled(is_ca)
        self._bd_pore.setEnabled(is_fd)
        self._bd_biofilm.setEnabled(is_fd)
        if not self._loading:
            self._on_edited()

    def _add_microbe(self):
        idx = len(self._microbes)
        m = Microbe(name=f"microbe_{idx}")
        self._microbes.append(m)
        self._list.addItem(m.name)
        self._list.setCurrentRow(idx)
        self._emit_names()

    def _remove_microbe(self):
        idx = self._list.currentRow()
        if idx < 0:
            return
        self._microbes.pop(idx)
        self._list.takeItem(idx)
        self._current_idx = -1
        if self._list.count() > 0:
            self._list.setCurrentRow(min(idx, self._list.count() - 1))
        self._emit_names()

    def _on_select(self, idx):
        if self._loading:
            return
        self._save_current()
        self._current_idx = idx
        if 0 <= idx < len(self._microbes):
            m = self._microbes[idx]
            self._loading = True
            self._name.setText(m.name)
            self._solver.setCurrentText(m.solver_type)
            self._reaction.setCurrentText(m.reaction_type)
            self._mat_num.setText(m.material_number)
            self._init_dens.setText(m.initial_densities)
            self._decay.setValue(m.decay_coefficient)
            self._ks.setText(m.half_saturation_constants)
            self._vmax.setText(m.maximum_uptake_flux)
            self._visc_ratio.setValue(m.viscosity_ratio_in_biofilm)
            self._bd_pore.setValue(m.biomass_diffusion_in_pore)
            self._bd_biofilm.setValue(m.biomass_diffusion_in_biofilm)
            self._left_type.setCurrentText(m.left_boundary_type)
            self._left_val.setValue(m.left_boundary_condition)
            self._right_type.setCurrentText(m.right_boundary_type)
            self._right_val.setValue(m.right_boundary_condition)
            self._loading = False

    def _on_edited(self):
        if self._loading:
            return
        self._save_current()
        if 0 <= self._current_idx < self._list.count():
            self._list.blockSignals(True)
            self._list.item(self._current_idx).setText(self._name.text())
            self._list.blockSignals(False)
        self._emit_names()

    def _save_current(self):
        idx = self._current_idx
        if idx < 0 or idx >= len(self._microbes):
            return
        m = self._microbes[idx]
        m.name = self._name.text()
        m.solver_type = self._solver.currentText()
        m.reaction_type = self._reaction.currentText()
        m.material_number = self._mat_num.text().strip()
        m.initial_densities = self._init_dens.text().strip()
        m.decay_coefficient = self._decay.value()
        m.half_saturation_constants = self._ks.text().strip()
        m.maximum_uptake_flux = self._vmax.text().strip()
        m.viscosity_ratio_in_biofilm = self._visc_ratio.value()
        m.biomass_diffusion_in_pore = self._bd_pore.value()
        m.biomass_diffusion_in_biofilm = self._bd_biofilm.value()
        m.left_boundary_type = self._left_type.currentText()
        m.left_boundary_condition = self._left_val.value()
        m.right_boundary_type = self._right_type.currentText()
        m.right_boundary_condition = self._right_val.value()

    def _emit_names(self):
        names = [m.name for m in self._microbes]
        self.microbes_changed.emit(names)
        self.data_changed.emit()

    def load_from_project(self, project):
        self._loading = True
        self._current_idx = -1
        mb = project.microbiology
        self.max_density.setValue(mb.maximum_biomass_density)
        self.thrd_fraction.setValue(mb.thrd_biofilm_fraction)
        ca_idx = {"fraction": 0, "half": 1}.get(mb.ca_method, 0)
        self.ca_method.setCurrentIndex(ca_idx)
        self._microbes = []
        for m in mb.microbes:
            mic = Microbe(
                name=m.name, solver_type=m.solver_type,
                reaction_type=m.reaction_type,
                material_number=m.material_number,
                initial_densities=m.initial_densities,
                decay_coefficient=m.decay_coefficient,
                viscosity_ratio_in_biofilm=m.viscosity_ratio_in_biofilm,
                half_saturation_constants=m.half_saturation_constants,
                maximum_uptake_flux=m.maximum_uptake_flux,
                left_boundary_type=m.left_boundary_type,
                right_boundary_type=m.right_boundary_type,
                left_boundary_condition=m.left_boundary_condition,
                right_boundary_condition=m.right_boundary_condition,
                biomass_diffusion_in_pore=m.biomass_diffusion_in_pore,
                biomass_diffusion_in_biofilm=m.biomass_diffusion_in_biofilm,
            )
            self._microbes.append(mic)
        self._list.clear()
        for m in self._microbes:
            self._list.addItem(m.name)
        self._loading = False
        if self._microbes:
            self._list.setCurrentRow(0)
        self._emit_names()

    def save_to_project(self, project):
        self._save_current()
        mb = project.microbiology
        mb.maximum_biomass_density = self.max_density.value()
        mb.thrd_biofilm_fraction = self.thrd_fraction.value()
        mb.ca_method = self.ca_method.currentText()
        mb.microbes = []
        for m in self._microbes:
            mic = Microbe(
                name=m.name, solver_type=m.solver_type,
                reaction_type=m.reaction_type,
                material_number=m.material_number,
                initial_densities=m.initial_densities,
                decay_coefficient=m.decay_coefficient,
                viscosity_ratio_in_biofilm=m.viscosity_ratio_in_biofilm,
                half_saturation_constants=m.half_saturation_constants,
                maximum_uptake_flux=m.maximum_uptake_flux,
                left_boundary_type=m.left_boundary_type,
                right_boundary_type=m.right_boundary_type,
                left_boundary_condition=m.left_boundary_condition,
                right_boundary_condition=m.right_boundary_condition,
                biomass_diffusion_in_pore=m.biomass_diffusion_in_pore,
                biomass_diffusion_in_biofilm=m.biomass_diffusion_in_biofilm,
            )
            mb.microbes.append(mic)

    def select_microbe(self, index: int):
        if 0 <= index < self._list.count():
            self._list.setCurrentRow(index)
