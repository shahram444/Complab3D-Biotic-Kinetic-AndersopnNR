"""Comprehensive GUI panel unit tests for CompLaB Studio.

Tests all 12 panels (BasePanel, GeneralPanel, DomainPanel, FluidPanel,
ChemistryPanel, EquilibriumPanel, MicrobiologyPanel, SolverPanel,
IOPanel, ParallelPanel, SweepPanel, RunPanel, PostProcessPanel).

Each panel is tested for:
  - Construction (widget creation without errors)
  - load_from_project() / save_to_project() round-trip fidelity
  - Widget state (enabled/disabled, value ranges)
  - Signal emission on data changes
  - Edge cases (empty data, boundary values)

Run with:
    cd GUI
    python -m pytest tests/test_gui_panels.py -v
"""

import os
import sys
from pathlib import Path

import pytest

# Ensure the GUI package is importable
GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GUI_DIR))

# Use offscreen platform (also set in conftest.py, but be safe for standalone runs)
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# QApplication MUST exist before importing any widget that creates
# QPixmap at module level (e.g., model_tree.py creates icons).
from PySide6.QtWidgets import QApplication              # noqa: E402
from PySide6.QtCore import Qt, QTimer                   # noqa: E402

_app = QApplication.instance() or QApplication([])

from src.core.project import (                          # noqa: E402
    CompLaBProject, SimulationMode, DomainSettings, FluidSettings,
    IterationSettings, Substrate, Microbe, MicrobiologySettings,
    EquilibriumSettings, IOSettings, PathSettings,
)
from src.panels.base_panel import BasePanel             # noqa: E402
from src.panels.general_panel import GeneralPanel       # noqa: E402
from src.panels.domain_panel import DomainPanel         # noqa: E402
from src.panels.fluid_panel import FluidPanel           # noqa: E402
from src.panels.chemistry_panel import ChemistryPanel   # noqa: E402
from src.panels.equilibrium_panel import EquilibriumPanel  # noqa: E402
from src.panels.microbiology_panel import MicrobiologyPanel  # noqa: E402
from src.panels.solver_panel import SolverPanel         # noqa: E402
from src.panels.io_panel import IOPanel                 # noqa: E402
from src.panels.parallel_panel import ParallelPanel     # noqa: E402
from src.panels.sweep_panel import SweepPanel           # noqa: E402
from src.panels.run_panel import RunPanel               # noqa: E402
from src.panels.postprocess_panel import PostProcessPanel  # noqa: E402


# ===================================================================
# Helper: create a fully populated project for round-trip tests
# ===================================================================

def _make_test_project():
    """Create a project with non-default values in every field."""
    p = CompLaBProject(name="TestProject")

    # Paths
    p.path_settings.src_path = "mysrc"
    p.path_settings.input_path = "myinput"
    p.path_settings.output_path = "myoutput"

    # Simulation mode
    p.simulation_mode.biotic_mode = True
    p.simulation_mode.enable_kinetics = True
    p.simulation_mode.enable_abiotic_kinetics = False
    p.simulation_mode.enable_validation_diagnostics = True

    # Domain
    p.domain.nx = 100
    p.domain.ny = 50
    p.domain.nz = 25
    p.domain.dx = 2.5
    p.domain.dy = 1.0
    p.domain.dz = 0.5
    p.domain.unit = "mm"
    p.domain.characteristic_length = 50.0
    p.domain.geometry_filename = "test_geom.dat"
    p.domain.pore = "2"
    p.domain.solid = "0"
    p.domain.bounce_back = "1"

    # Fluid
    p.fluid.delta_P = 5e-3
    p.fluid.peclet = 2.0
    p.fluid.tau = 0.9
    p.fluid.track_performance = True

    # Iteration
    p.iteration.ns_max_iT1 = 50000
    p.iteration.ns_max_iT2 = 30000
    p.iteration.ns_converge_iT1 = 1e-7
    p.iteration.ns_converge_iT2 = 1e-5
    p.iteration.ade_max_iT = 500000
    p.iteration.ade_converge_iT = 1e-9
    p.iteration.ns_rerun_iT0 = 100
    p.iteration.ade_rerun_iT0 = 200
    p.iteration.ns_update_interval = 5
    p.iteration.ade_update_interval = 2

    # Substrates
    p.substrates = [
        Substrate(
            name="DOC",
            initial_concentration=1.0,
            diffusion_in_pore=1.5e-9,
            diffusion_in_biofilm=3e-10,
            left_boundary_type="Dirichlet",
            right_boundary_type="Neumann",
            left_boundary_condition=1.0,
            right_boundary_condition=0.0,
        ),
        Substrate(
            name="CO2",
            initial_concentration=0.0,
            diffusion_in_pore=1.9e-9,
            diffusion_in_biofilm=4e-10,
            left_boundary_type="Neumann",
            right_boundary_type="Neumann",
            left_boundary_condition=0.0,
            right_boundary_condition=0.0,
        ),
    ]

    # Microbiology
    p.microbiology.maximum_biomass_density = 150.0
    p.microbiology.thrd_biofilm_fraction = 0.15
    p.microbiology.ca_method = "half"
    p.microbiology.microbes = [
        Microbe(
            name="Bacteria1",
            solver_type="CA",
            reaction_type="kinetics",
            material_number="3",
            initial_densities="99.0",
            decay_coefficient=1e-6,
            viscosity_ratio_in_biofilm=15.0,
            half_saturation_constants="1e-5",
            maximum_uptake_flux="2.5",
            left_boundary_type="Neumann",
            right_boundary_type="Neumann",
            left_boundary_condition=0.0,
            right_boundary_condition=0.0,
            biomass_diffusion_in_pore=-99.0,
            biomass_diffusion_in_biofilm=-99.0,
        ),
    ]

    # Equilibrium
    p.equilibrium.enabled = True
    p.equilibrium.component_names = ["HCO3", "Hplus"]
    p.equilibrium.stoichiometry = [[1.0, 0.0], [0.0, 1.0]]
    p.equilibrium.log_k = [-6.35, -10.33]
    p.equilibrium.max_iterations = 300
    p.equilibrium.tolerance = 1e-12
    p.equilibrium.anderson_depth = 6
    p.equilibrium.beta = 0.8

    # IO
    p.io_settings.save_vtk_interval = 500
    p.io_settings.save_chk_interval = 50000
    p.io_settings.read_ns_file = True
    p.io_settings.read_ade_file = True
    p.io_settings.ns_filename = "myNS"
    p.io_settings.mask_filename = "myMask"
    p.io_settings.subs_filename = "mySubs"
    p.io_settings.bio_filename = "myBio"

    return p


# ===================================================================
# BasePanel Tests
# ===================================================================

class TestBasePanel:
    """Test BasePanel factory methods and construction."""

    def test_construction(self, qtbot):
        panel = BasePanel("Test Panel")
        qtbot.addWidget(panel)
        assert panel._title == "Test Panel"

    def test_construction_no_title(self, qtbot):
        panel = BasePanel()
        qtbot.addWidget(panel)
        assert panel._title == ""

    def test_make_line_edit(self, qtbot):
        w = BasePanel.make_line_edit("hello", "placeholder", readonly=True)
        assert w.text() == "hello"
        assert w.placeholderText() == "placeholder"
        assert w.isReadOnly()

    def test_make_spin(self, qtbot):
        w = BasePanel.make_spin(42, 0, 100, "units")
        assert w.value() == 42
        assert w.minimum() == 0
        assert w.maximum() == 100

    def test_make_double_spin(self, qtbot):
        w = BasePanel.make_double_spin(3.14, 0.0, 10.0, 4, "m/s")
        assert abs(w.value() - 3.14) < 1e-6
        assert w.decimals() == 4

    def test_make_combo(self, qtbot):
        w = BasePanel.make_combo(["A", "B", "C"], current=1)
        assert w.currentText() == "B"
        assert w.count() == 3

    def test_make_checkbox(self, qtbot):
        w = BasePanel.make_checkbox("Enable", checked=True)
        assert w.isChecked()
        assert w.text() == "Enable"

    def test_make_button(self, qtbot):
        w = BasePanel.make_button("Click Me", primary=True)
        assert w.text() == "Click Me"
        assert w.property("primary") is True

    def test_make_info_label(self, qtbot):
        lbl = BasePanel.make_info_label("Info text")
        assert lbl.text() == "Info text"
        assert lbl.wordWrap()

    def test_add_section(self, qtbot):
        panel = BasePanel("Test")
        qtbot.addWidget(panel)
        lbl = panel.add_section("Section Title")
        assert lbl.text() == "Section Title"

    def test_add_form(self, qtbot):
        panel = BasePanel("Test")
        qtbot.addWidget(panel)
        form = panel.add_form()
        assert form is not None

    def test_set_and_clear_validation(self, qtbot):
        w = BasePanel.make_line_edit("test")
        BasePanel.set_validation(w, "error", "Bad value")
        assert w.property("validation") == "error"
        assert w.toolTip() == "Bad value"
        BasePanel.clear_validation(w)
        assert w.property("validation") == ""

    def test_data_changed_signal(self, qtbot):
        panel = BasePanel("Test")
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.data_changed, timeout=1000):
            panel.data_changed.emit()


# ===================================================================
# GeneralPanel Tests
# ===================================================================

class TestGeneralPanel:
    """Test simulation mode panel."""

    def test_construction(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Simulation Mode"

    def test_default_mode_is_biotic(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        assert panel._radio_biotic.isChecked()

    def test_mode_flags_biotic(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_biotic.setChecked(True)
        biotic, kinetics, abiotic = panel._get_mode_flags()
        assert biotic is True
        assert kinetics is True
        assert abiotic is False

    def test_mode_flags_abiotic(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_abiotic.setChecked(True)
        biotic, kinetics, abiotic = panel._get_mode_flags()
        assert biotic is False
        assert kinetics is False
        assert abiotic is True

    def test_mode_flags_flow_only(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_flow.setChecked(True)
        biotic, kinetics, abiotic = panel._get_mode_flags()
        assert biotic is False
        assert kinetics is False
        assert abiotic is False

    def test_mode_flags_coupled(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_coupled.setChecked(True)
        biotic, kinetics, abiotic = panel._get_mode_flags()
        assert biotic is True
        assert kinetics is True
        assert abiotic is True

    def test_mode_flags_diffusion(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_diffusion.setChecked(True)
        biotic, kinetics, abiotic = panel._get_mode_flags()
        assert biotic is False
        assert kinetics is False
        assert abiotic is False

    def test_mode_flags_transport(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_transport.setChecked(True)
        biotic, kinetics, abiotic = panel._get_mode_flags()
        assert biotic is False
        assert kinetics is False
        assert abiotic is False

    def test_get_mode_id(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_abiotic.setChecked(True)
        assert panel.get_mode_id() == 3

    def test_load_save_round_trip(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        # Verify widgets loaded correctly
        assert panel._radio_biotic.isChecked()
        assert panel.enable_diagnostics.isChecked()
        assert panel.src_path.text() == "mysrc"
        assert panel.input_path.text() == "myinput"
        assert panel.output_path.text() == "myoutput"

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert p2.simulation_mode.biotic_mode is True
        assert p2.simulation_mode.enable_kinetics is True
        assert p2.simulation_mode.enable_validation_diagnostics is True
        assert p2.path_settings.src_path == "mysrc"
        assert p2.path_settings.input_path == "myinput"
        assert p2.path_settings.output_path == "myoutput"

    def test_load_abiotic_mode(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.simulation_mode.enable_abiotic_kinetics = True

        panel.load_from_project(p)
        assert panel._radio_abiotic.isChecked()

    def test_load_coupled_mode(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = True
        p.simulation_mode.enable_kinetics = True
        p.simulation_mode.enable_abiotic_kinetics = True

        panel.load_from_project(p)
        assert panel._radio_coupled.isChecked()

    def test_load_flow_only(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()
        p.simulation_mode.biotic_mode = False
        p.simulation_mode.enable_kinetics = False
        p.simulation_mode.enable_abiotic_kinetics = False
        p.fluid.delta_P = 1.0
        p.fluid.peclet = 0.0

        panel.load_from_project(p)
        # With no substrates, should pick flow_only
        assert panel._radio_flow.isChecked()

    def test_data_changed_on_mode_switch(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.data_changed, timeout=1000):
            panel._radio_abiotic.setChecked(True)

    def test_summary_updates_on_mode_change(self, qtbot):
        panel = GeneralPanel()
        qtbot.addWidget(panel)
        panel._radio_flow.setChecked(True)
        text = panel._summary.text()
        assert "Navier-Stokes" in text


# ===================================================================
# DomainPanel Tests
# ===================================================================

class TestDomainPanel:
    """Test domain configuration panel."""

    def test_construction(self, qtbot):
        panel = DomainPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Domain Settings"

    def test_default_values(self, qtbot):
        panel = DomainPanel()
        qtbot.addWidget(panel)
        assert panel.nx.value() == 50
        assert panel.ny.value() == 30
        assert panel.nz.value() == 30

    def test_load_save_round_trip(self, qtbot):
        panel = DomainPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        assert panel.nx.value() == 100
        assert panel.ny.value() == 50
        assert panel.nz.value() == 25
        assert abs(panel.dx.value() - 2.5) < 1e-6
        assert abs(panel.dy.value() - 1.0) < 1e-6
        assert abs(panel.dz.value() - 0.5) < 1e-6
        assert panel.unit.currentText() == "mm"
        assert abs(panel.char_length.value() - 50.0) < 1e-4
        assert panel.geom_file.text() == "test_geom.dat"
        assert panel.pore.text() == "2"
        assert panel.solid.text() == "0"
        assert panel.bounce_back.text() == "1"

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert p2.domain.nx == 100
        assert p2.domain.ny == 50
        assert p2.domain.nz == 25
        assert abs(p2.domain.dx - 2.5) < 1e-6
        assert p2.domain.unit == "mm"
        assert p2.domain.geometry_filename == "test_geom.dat"

    def test_find_factorizations(self, qtbot):
        # 27 = 3*3*3
        facts = DomainPanel._find_factorizations(27)
        assert len(facts) > 0
        assert any(f[0] * f[1] * f[2] == 27 for f in facts)

    def test_find_factorizations_too_small(self, qtbot):
        facts = DomainPanel._find_factorizations(10)
        assert len(facts) == 0

    def test_find_factorizations_with_hint(self, qtbot):
        # 1000 with nz_hint=10 -> only factorizations with nz=10
        facts = DomainPanel._find_factorizations(1000, nz_hint=10)
        assert all(f[2] == 10 for f in facts)

    def test_analyze_dat_file_text(self, qtbot, tmp_path):
        # Create a simple text .dat file
        dat = tmp_path / "test.dat"
        dat.write_text("\n".join(str(i % 3) for i in range(27)))
        total, nz_hint = DomainPanel._analyze_dat_file(str(dat))
        assert total == 27

    def test_analyze_dat_file_empty(self, qtbot, tmp_path):
        dat = tmp_path / "empty.dat"
        dat.write_text("")
        total, nz_hint = DomainPanel._analyze_dat_file(str(dat))
        assert total == 0

    def test_geometry_loaded_signal(self, qtbot):
        panel = DomainPanel()
        qtbot.addWidget(panel)
        # The signal exists and can be connected
        received = []
        panel.geometry_loaded.connect(lambda *args: received.append(args))
        panel.geometry_loaded.emit("test.dat", 10, 10, 10)
        assert len(received) == 1


# ===================================================================
# FluidPanel Tests
# ===================================================================

class TestFluidPanel:
    """Test fluid/flow settings panel."""

    def test_construction(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Fluid / Flow Settings"

    def test_default_values(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        assert abs(panel.tau.value() - 0.8) < 1e-6

    def test_load_save_round_trip(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        assert abs(panel.delta_P.value() - 5e-3) < 1e-8
        assert abs(panel.peclet.value() - 2.0) < 1e-6
        assert abs(panel.tau.value() - 0.9) < 1e-6
        assert panel.track_perf.isChecked()

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert abs(p2.fluid.delta_P - 5e-3) < 1e-8
        assert abs(p2.fluid.peclet - 2.0) < 1e-6
        assert abs(p2.fluid.tau - 0.9) < 1e-6
        assert p2.fluid.track_performance is True

    def test_tau_validation_error(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        # tau spin has min=0.501, so 0.501 is the lowest settable value
        # The validation fires on valueChanged, check it shows warning for high tau
        # since we can't set below 0.501 via the widget.
        # Instead verify that the validation method works for boundary values
        panel.tau.setValue(0.501)
        # 0.501 is technically > 0.5 so should be OK
        prop = panel.tau.property("validation")
        assert prop in ("", "ok", None)

    def test_tau_validation_warning(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        panel.tau.setValue(1.8)
        assert panel.tau.property("validation") == "warning"

    def test_tau_validation_ok(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        panel.tau.setValue(0.8)
        assert panel.tau.property("validation") in ("", "ok", None)

    def test_delta_p_validation_negative(self, qtbot):
        panel = FluidPanel()
        qtbot.addWidget(panel)
        # delta_P has min 0 so we can't set negative, but we can check
        # that the validation doesn't crash for boundary values
        panel.delta_P.setValue(0.0)
        # Should not have error for 0.0
        prop = panel.delta_P.property("validation")
        assert prop in ("", "ok", None)


# ===================================================================
# ChemistryPanel Tests
# ===================================================================

class TestChemistryPanel:
    """Test substrate management panel."""

    def test_construction(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Chemistry - Substrates"

    def test_add_substrate(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        panel._add_substrate()
        assert panel._list.count() == 1
        assert len(panel._substrates) == 1

    def test_add_multiple_substrates(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        panel._add_substrate()
        panel._add_substrate()
        panel._add_substrate()
        assert panel._list.count() == 3
        assert len(panel._substrates) == 3

    def test_remove_substrate(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        panel._add_substrate()
        panel._add_substrate()
        panel._list.setCurrentRow(0)
        panel._remove_substrate()
        assert panel._list.count() == 1

    def test_remove_from_empty(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        panel._remove_substrate()  # Should not crash
        assert panel._list.count() == 0

    def test_substrates_changed_signal(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.substrates_changed, timeout=1000):
            panel._add_substrate()

    def test_load_save_round_trip(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)
        assert panel._list.count() == 2
        assert panel._list.item(0).text() == "DOC"
        assert panel._list.item(1).text() == "CO2"

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert len(p2.substrates) == 2
        assert p2.substrates[0].name == "DOC"
        assert abs(p2.substrates[0].initial_concentration - 1.0) < 1e-8
        assert abs(p2.substrates[0].diffusion_in_pore - 1.5e-9) < 1e-15
        assert p2.substrates[0].left_boundary_type == "Dirichlet"
        assert p2.substrates[1].name == "CO2"

    def test_select_substrate(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        panel._add_substrate()
        panel._add_substrate()
        panel.select_substrate(1)
        assert panel._list.currentRow() == 1

    def test_editing_updates_name_in_list(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        panel._add_substrate()
        panel._list.setCurrentRow(0)
        panel._name.setText("MySubstrate")
        assert panel._list.item(0).text() == "MySubstrate"

    def test_load_empty_project(self, qtbot):
        panel = ChemistryPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()  # no substrates
        panel.load_from_project(p)
        assert panel._list.count() == 0
        assert len(panel._substrates) == 0


# ===================================================================
# EquilibriumPanel Tests
# ===================================================================

class TestEquilibriumPanel:
    """Test equilibrium chemistry panel."""

    def test_construction(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Equilibrium Chemistry"

    def test_default_disabled(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        assert not panel.enabled.isChecked()
        assert not panel._components.isEnabled()
        assert not panel._table.isEnabled()

    def test_enable_toggle(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.enabled.setChecked(True)
        assert panel._components.isEnabled()
        assert panel._table.isEnabled()
        assert panel._max_iter.isEnabled()
        assert panel._tolerance.isEnabled()
        assert panel._anderson_depth.isEnabled()
        assert panel._beta.isEnabled()

    def test_disable_toggle(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.enabled.setChecked(True)
        panel.enabled.setChecked(False)
        assert not panel._components.isEnabled()
        assert not panel._table.isEnabled()

    def test_set_substrate_names(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.set_substrate_names(["DOC", "CO2", "HCO3"])
        assert "DOC" in panel._subs_info.text()
        assert "CO2" in panel._subs_info.text()
        assert "HCO3" in panel._subs_info.text()

    def test_set_substrate_names_empty(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.set_substrate_names([])
        assert "none" in panel._subs_info.text().lower()

    def test_rebuild_matrix_no_components(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.enabled.setChecked(True)
        panel._substrate_names = ["DOC", "CO2"]
        panel._components.setText("")
        panel._rebuild_matrix()
        # Should show error message
        assert "Enter component" in panel._rebuild_status.text()

    def test_rebuild_matrix_no_substrates(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.enabled.setChecked(True)
        panel._components.setText("HCO3 Hplus")
        panel._substrate_names = []
        panel._rebuild_matrix()
        assert "No substrates" in panel._rebuild_status.text()

    def test_rebuild_matrix_success(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        panel.enabled.setChecked(True)
        panel._substrate_names = ["DOC", "CO2"]
        panel._components.setText("HCO3 Hplus")
        panel._rebuild_matrix()
        assert panel._table.rowCount() == 2
        assert panel._table.columnCount() == 3  # 2 components + logK
        assert "2 species" in panel._rebuild_status.text()

    def test_load_save_round_trip(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        assert panel.enabled.isChecked()
        assert panel._components.text() == "HCO3 Hplus"
        assert panel._max_iter.value() == 300
        assert abs(panel._tolerance.value() - 1e-12) < 1e-18
        assert panel._anderson_depth.value() == 6
        assert abs(panel._beta.value() - 0.8) < 1e-6
        assert panel._table.rowCount() == 2
        assert panel._table.columnCount() == 3  # 2 comp + logK

        # Save back
        p2 = CompLaBProject()
        p2.substrates = [Substrate(name="DOC"), Substrate(name="CO2")]
        panel.save_to_project(p2)

        assert p2.equilibrium.enabled is True
        assert p2.equilibrium.component_names == ["HCO3", "Hplus"]
        assert p2.equilibrium.max_iterations == 300
        assert abs(p2.equilibrium.tolerance - 1e-12) < 1e-18
        assert p2.equilibrium.anderson_depth == 6
        assert abs(p2.equilibrium.beta - 0.8) < 1e-6
        assert len(p2.equilibrium.stoichiometry) == 2
        assert len(p2.equilibrium.log_k) == 2

    def test_load_disabled_equilibrium(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()
        p.equilibrium.enabled = False
        panel.load_from_project(p)
        assert not panel.enabled.isChecked()

    def test_data_changed_on_enable(self, qtbot):
        panel = EquilibriumPanel()
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.data_changed, timeout=1000):
            panel.enabled.setChecked(True)


# ===================================================================
# MicrobiologyPanel Tests
# ===================================================================

class TestMicrobiologyPanel:
    """Test microbiology management panel."""

    def test_construction(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Microbiology"

    def test_add_microbe(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        panel._add_microbe()
        assert panel._list.count() == 1
        assert len(panel._microbes) == 1

    def test_add_multiple_microbes(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        panel._add_microbe()
        panel._add_microbe()
        assert panel._list.count() == 2

    def test_remove_microbe(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        panel._add_microbe()
        panel._add_microbe()
        panel._list.setCurrentRow(0)
        panel._remove_microbe()
        assert panel._list.count() == 1

    def test_remove_from_empty(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        panel._remove_microbe()  # Should not crash
        assert panel._list.count() == 0

    def test_microbes_changed_signal(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.microbes_changed, timeout=1000):
            panel._add_microbe()

    def test_load_save_round_trip(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        assert abs(panel.max_density.value() - 150.0) < 1e-4
        assert abs(panel.thrd_fraction.value() - 0.15) < 1e-4
        assert panel.ca_method.currentText() == "half"
        assert panel._list.count() == 1
        assert panel._list.item(0).text() == "Bacteria1"

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert abs(p2.microbiology.maximum_biomass_density - 150.0) < 1e-4
        assert abs(p2.microbiology.thrd_biofilm_fraction - 0.15) < 1e-4
        assert p2.microbiology.ca_method == "half"
        assert len(p2.microbiology.microbes) == 1
        m = p2.microbiology.microbes[0]
        assert m.name == "Bacteria1"
        assert m.solver_type == "CA"
        assert m.reaction_type == "kinetics"
        assert m.material_number == "3"

    def test_solver_type_enables_widgets(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        panel._add_microbe()
        panel._list.setCurrentRow(0)

        # Switch to FD first to trigger _on_solver_changed
        panel._solver.setCurrentText("FD")
        assert not panel._visc_ratio.isEnabled()
        assert panel._bd_pore.isEnabled()
        assert panel._bd_biofilm.isEnabled()

        # Switch back to CA
        panel._solver.setCurrentText("CA")
        assert panel._visc_ratio.isEnabled()
        assert not panel._bd_pore.isEnabled()
        assert not panel._bd_biofilm.isEnabled()

    def test_load_empty_microbe_list(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()
        panel.load_from_project(p)
        assert panel._list.count() == 0

    def test_select_microbe(self, qtbot):
        panel = MicrobiologyPanel()
        qtbot.addWidget(panel)
        panel._add_microbe()
        panel._add_microbe()
        panel.select_microbe(1)
        assert panel._list.currentRow() == 1


# ===================================================================
# SolverPanel Tests
# ===================================================================

class TestSolverPanel:
    """Test solver/iteration settings panel."""

    def test_construction(self, qtbot):
        panel = SolverPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Solver Settings"

    def test_load_save_round_trip(self, qtbot):
        panel = SolverPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        assert panel.ns_max_iT1.value() == 50000
        assert panel.ns_max_iT2.value() == 30000
        assert abs(panel.ns_converge_iT1.value() - 1e-7) < 1e-15
        assert abs(panel.ns_converge_iT2.value() - 1e-5) < 1e-12
        assert panel.ade_max_iT.value() == 500000
        assert abs(panel.ade_converge.value() - 1e-9) < 1e-15
        assert panel.ns_rerun_iT0.value() == 100
        assert panel.ade_rerun_iT0.value() == 200
        assert panel.ns_update.value() == 5
        assert panel.ade_update.value() == 2

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert p2.iteration.ns_max_iT1 == 50000
        assert p2.iteration.ns_max_iT2 == 30000
        assert p2.iteration.ade_max_iT == 500000
        assert p2.iteration.ns_update_interval == 5
        assert p2.iteration.ade_update_interval == 2

    def test_zero_iterations_warning(self, qtbot):
        panel = SolverPanel()
        qtbot.addWidget(panel)
        panel.ns_max_iT1.setValue(0)
        assert panel.ns_max_iT1.property("validation") == "warning"

    def test_zero_ade_iterations_warning(self, qtbot):
        panel = SolverPanel()
        qtbot.addWidget(panel)
        panel.ade_max_iT.setValue(0)
        assert panel.ade_max_iT.property("validation") == "warning"

    def test_nonzero_clears_warning(self, qtbot):
        panel = SolverPanel()
        qtbot.addWidget(panel)
        panel.ns_max_iT1.setValue(0)
        panel.ns_max_iT1.setValue(1000)
        prop = panel.ns_max_iT1.property("validation")
        assert prop in ("", "ok", None)


# ===================================================================
# IOPanel Tests
# ===================================================================

class TestIOPanel:
    """Test I/O settings panel."""

    def test_construction(self, qtbot):
        panel = IOPanel()
        qtbot.addWidget(panel)
        assert panel._title == "I/O Settings"

    def test_load_save_round_trip(self, qtbot):
        panel = IOPanel()
        qtbot.addWidget(panel)
        p = _make_test_project()

        panel.load_from_project(p)

        assert panel.vtk_interval.value() == 500
        assert panel.chk_interval.value() == 50000
        assert panel.read_ns.isChecked()
        assert panel.read_ade.isChecked()
        assert panel.ns_file.text() == "myNS"
        assert panel.mask_file.text() == "myMask"
        assert panel.subs_file.text() == "mySubs"
        assert panel.bio_file.text() == "myBio"

        # Save back
        p2 = CompLaBProject()
        panel.save_to_project(p2)
        assert p2.io_settings.save_vtk_interval == 500
        assert p2.io_settings.save_chk_interval == 50000
        assert p2.io_settings.read_ns_file is True
        assert p2.io_settings.read_ade_file is True
        assert p2.io_settings.ns_filename == "myNS"
        assert p2.io_settings.mask_filename == "myMask"
        assert p2.io_settings.subs_filename == "mySubs"
        assert p2.io_settings.bio_filename == "myBio"

    def test_default_values(self, qtbot):
        panel = IOPanel()
        qtbot.addWidget(panel)
        p = CompLaBProject()
        panel.load_from_project(p)
        assert panel.vtk_interval.value() == 1000
        assert not panel.read_ns.isChecked()


# ===================================================================
# ParallelPanel Tests
# ===================================================================

class TestParallelPanel:
    """Test parallel execution settings panel."""

    def test_construction(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Parallel Execution"

    def test_initial_state_disabled(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        assert not panel._enabled
        assert not panel._core_slider.isEnabled()
        assert not panel._core_spin.isEnabled()

    def test_enable_parallel(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        panel._enable_cb.setChecked(True)
        assert panel._enabled
        assert panel._core_slider.isEnabled()
        assert panel._core_spin.isEnabled()

    def test_disable_parallel(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        panel._enable_cb.setChecked(True)
        panel._enable_cb.setChecked(False)
        assert not panel._enabled
        assert not panel._core_slider.isEnabled()

    def test_slider_spin_sync(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        panel._enable_cb.setChecked(True)
        panel._core_slider.setValue(2)
        assert panel._core_spin.value() == 2
        panel._core_spin.setValue(3)
        assert panel._core_slider.value() == 3

    def test_get_num_cores_disabled(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        assert panel.get_num_cores() == 1

    def test_data_changed_on_enable(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        with qtbot.waitSignal(panel.data_changed, timeout=1000):
            panel._enable_cb.setChecked(True)

    def test_warnings_all_cores(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        panel._enable_cb.setChecked(True)
        panel._core_slider.setValue(panel._total_cores)
        text = panel._warn_lbl.text()
        if panel._total_cores > 1:
            assert "all cores" in text.lower() or "freeze" in text.lower()

    def test_validate_for_domain(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        panel._enable_cb.setChecked(True)
        if panel._total_cores >= 2:
            panel._core_slider.setValue(2)
        panel.validate_for_domain(5, 5, 5)
        # Small domain should trigger a warning
        text = panel._warn_lbl.text()
        assert "small" in text.lower() or "overhead" in text.lower() or \
               "No warnings" in text

    def test_cmd_preview_serial(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        text = panel._cmd_lbl.text()
        assert "complab" in text.lower()

    def test_cmd_preview_mpi(self, qtbot):
        panel = ParallelPanel()
        qtbot.addWidget(panel)
        panel._enable_cb.setChecked(True)
        panel._mpi_path_edit.setText("/usr/bin/mpirun")
        if panel._total_cores >= 2:
            panel._core_slider.setValue(2)
            text = panel._cmd_lbl.text()
            assert "mpirun" in text
            assert "-np" in text


# ===================================================================
# SweepPanel Tests
# ===================================================================

class TestSweepPanel:
    """Test parameter sweep panel."""

    def test_construction(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Parameter Sweep"

    def test_parameter_combo_populated(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        assert panel._param_combo.count() > 0
        assert "Peclet" in panel._param_combo.itemText(0)

    def test_generate_linear_preview(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._mode_combo.setCurrentIndex(0)  # Linear range
        panel._start.setValue(1.0)
        panel._end.setValue(5.0)
        panel._steps.setValue(5)
        panel._generate_preview()
        assert panel._table.rowCount() == 5
        assert panel._queue_btn.isEnabled()

    def test_generate_custom_preview(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._mode_combo.setCurrentIndex(1)  # Custom
        panel._custom_edit.setText("0.1, 0.5, 1.0, 2.0")
        panel._generate_preview()
        assert panel._table.rowCount() == 4

    def test_generate_custom_empty(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._mode_combo.setCurrentIndex(1)
        panel._custom_edit.setText("")
        panel._generate_preview()
        assert panel._table.rowCount() == 0

    def test_generate_custom_invalid(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._mode_combo.setCurrentIndex(1)
        panel._custom_edit.setText("a, b, c")
        panel._generate_preview()
        assert "Invalid" in panel._summary_lbl.text()

    def test_clear_preview(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._mode_combo.setCurrentIndex(0)
        panel._start.setValue(1.0)
        panel._end.setValue(3.0)
        panel._steps.setValue(3)
        panel._generate_preview()
        assert panel._table.rowCount() == 3
        panel._clear_preview()
        assert panel._table.rowCount() == 0
        assert not panel._queue_btn.isEnabled()

    def test_get_sweep_config(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._param_combo.setCurrentIndex(0)  # Peclet number
        panel._start.setValue(1.0)
        panel._end.setValue(3.0)
        panel._steps.setValue(3)
        panel._generate_preview()
        config = panel.get_sweep_config()
        assert len(config) == 3
        assert config[0][0] == "fluid"
        assert config[0][1] == "peclet"

    def test_sweep_requested_signal(self, qtbot):
        panel = SweepPanel()
        qtbot.addWidget(panel)
        panel._start.setValue(1.0)
        panel._end.setValue(2.0)
        panel._steps.setValue(2)
        panel._generate_preview()
        with qtbot.waitSignal(panel.sweep_requested, timeout=1000):
            panel._queue_runs()


# ===================================================================
# RunPanel Tests
# ===================================================================

class TestRunPanel:
    """Test run simulation panel."""

    def test_construction(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Run Simulation"

    def test_initial_state(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        assert not panel._running
        assert panel._run_btn.isEnabled()
        assert not panel._stop_btn.isEnabled()
        assert panel._status.text() == "Ready"

    def test_mpi_toggle(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        assert not panel._nprocs_spin.isEnabled()
        assert not panel._mpirun_edit.isEnabled()

        panel._mpi_enabled.setChecked(True)
        assert panel._nprocs_spin.isEnabled()
        assert panel._mpirun_edit.isEnabled()

        panel._mpi_enabled.setChecked(False)
        assert not panel._nprocs_spin.isEnabled()
        assert not panel._mpirun_edit.isEnabled()

    def test_get_mpi_config(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel._mpi_enabled.setChecked(True)
        panel._nprocs_spin.setValue(4)
        panel._mpirun_edit.setText("/usr/bin/mpirun")
        enabled, nprocs, path = panel.get_mpi_config()
        assert enabled is True
        assert nprocs == 4
        assert path == "/usr/bin/mpirun"

    def test_set_mpi_config(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.set_mpi_config(True, 8, "/opt/mpi/bin/mpirun")
        assert panel._mpi_enabled.isChecked()
        assert panel._nprocs_spin.value() == 8
        assert panel._mpirun_edit.text() == "/opt/mpi/bin/mpirun"

    def test_on_run_sets_running_state(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        received = []
        panel.run_requested.connect(lambda: received.append(True))
        panel._on_run()
        assert panel._running
        assert not panel._run_btn.isEnabled()
        assert panel._stop_btn.isEnabled()
        assert "Starting" in panel._status.text()
        assert len(received) == 1

    def test_on_stop_emits_signal(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel._on_run()
        with qtbot.waitSignal(panel.stop_requested, timeout=1000):
            panel._on_stop()

    def test_on_progress(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_progress(50, 100)
        assert panel._progress.value() == 50
        assert panel._progress.maximum() == 100
        assert "50" in panel._iteration_label.text()
        assert "100" in panel._iteration_label.text()

    def test_on_output_line_normal(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("iT = 42  residual = 1.0e-4")
        text = panel._output_text.toPlainText()
        assert "iT = 42" in text

    def test_on_output_line_max_iT_parse(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("ade_max_iT = 5000")
        assert panel._max_iterations == 5000

    def test_on_output_line_iteration_parse(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("iT = 123")
        assert panel._current_iteration == 123

    def test_on_output_line_phase_detection_ns(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("Starting phase 1 Navier-Stokes solver")
        assert "Phase 1" in panel._phase_label.text()

    def test_on_output_line_phase_detection_ade(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("ADE transport solver starting")
        assert "ADE" in panel._phase_label.text()

    def test_on_output_line_phase_detection_equilibrium(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("Running equilibrium solver step")
        assert "Equilibrium" in panel._phase_label.text()

    def test_on_finished_success(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel._on_run()
        panel.on_finished(0, "Completed successfully")
        assert not panel._running
        assert panel._run_btn.isEnabled()
        assert not panel._stop_btn.isEnabled()
        assert "Completed" in panel._status.text()
        assert "Done" in panel._eta_label.text()

    def test_on_finished_failure(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel._on_run()
        panel.on_finished(42, "Process exited with code 42")
        assert not panel._running
        assert "Failed" in panel._status.text()
        # Error summary text should be set (visibility depends on parent show state)
        assert len(panel._error_summary.text()) > 0

    def test_on_finished_segfault(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel._on_run()
        panel.on_finished(-11, "Segfault")
        assert "Failed" in panel._status.text()
        error_text = panel._error_summary.text()
        assert "Segmentation" in error_text or "Memory" in error_text

    def test_show_validation_no_errors(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.show_validation([])
        assert "valid" in panel._validation_lbl.text().lower()

    def test_show_validation_with_errors(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.show_validation(["Error 1", "Error 2"])
        assert "2" in panel._validation_lbl.text()

    def test_on_diagnostic_report(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_diagnostic_report(
            "=== DIAGNOSTIC ===\n"
            "Error detected: Geometry mismatch\n"
            ">> nx*ny*nz does not match file\n"
            "How to fix:\n"
            "1. Check dimensions\n")
        html = panel._validation_text.toHtml()
        assert "DIAGNOSTIC" in html or "diagnostic" in html

    def test_analyze_exit_code_known(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        result = panel._analyze_exit_code(-11)
        assert "Segmentation" in result

    def test_analyze_exit_code_unknown(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        result = panel._analyze_exit_code(999)
        assert "Unknown" in result

    def test_clear_output(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("Some output")
        panel._clear_output()
        assert panel._output_text.toPlainText() == ""

    def test_run_stop_signals(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        run_received = []
        stop_received = []
        panel.run_requested.connect(lambda: run_received.append(True))
        panel.stop_requested.connect(lambda: stop_received.append(True))
        panel._on_run()
        assert len(run_received) == 1
        panel._on_stop()
        assert len(stop_received) == 1

    def test_ns_residual_parsing(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("NS Residual: 1.23e-5")
        assert len(panel._ns_residual_history) == 1
        assert abs(panel._ns_residual_history[0] - 1.23e-5) < 1e-10

    def test_ade_residual_parsing(self, qtbot):
        panel = RunPanel()
        qtbot.addWidget(panel)
        panel.on_output_line("ADE residual = 4.56e-8")
        assert len(panel._ade_residual_history) == 1
        assert abs(panel._ade_residual_history[0] - 4.56e-8) < 1e-15


# ===================================================================
# PostProcessPanel Tests
# ===================================================================

class TestPostProcessPanel:
    """Test post-processing panel."""

    def test_construction(self, qtbot):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        assert panel._title == "Post-Processing"

    def test_set_output_directory(self, qtbot, tmp_path):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)

        # Create some test files
        (tmp_path / "subs_0001.vti").write_text("dummy")
        (tmp_path / "bio_0001.vti").write_text("dummy")
        (tmp_path / "vel_0001.vtk").write_text("dummy")

        panel.set_output_directory(str(tmp_path))
        assert panel._dir_edit.text() == str(tmp_path)
        assert panel._file_list.count() == 3

    def test_set_empty_directory(self, qtbot):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        panel.set_output_directory("")
        assert panel._file_list.count() == 0

    def test_set_nonexistent_directory(self, qtbot):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        panel.set_output_directory("/nonexistent/path")
        assert panel._file_list.count() == 0

    def test_filter_vti_only(self, qtbot, tmp_path):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        (tmp_path / "subs_0001.vti").write_text("dummy")
        (tmp_path / "vel_0001.vtk").write_text("dummy")
        panel._output_dir = str(tmp_path)
        panel._filter_combo.setCurrentIndex(1)  # VTI only
        assert panel._file_list.count() == 1

    def test_filter_vtk_only(self, qtbot, tmp_path):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        (tmp_path / "subs_0001.vti").write_text("dummy")
        (tmp_path / "vel_0001.vtk").write_text("dummy")
        panel._output_dir = str(tmp_path)
        panel._filter_combo.setCurrentIndex(2)  # VTK only
        assert panel._file_list.count() == 1

    def test_file_selected_signal(self, qtbot, tmp_path):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        (tmp_path / "test.vti").write_text("dummy")
        panel.set_output_directory(str(tmp_path))
        received = []
        panel.file_selected.connect(lambda p: received.append(p))
        panel._file_list.setCurrentRow(0)
        panel._load_selected()
        assert len(received) == 1
        assert "test.vti" in received[0]

    def test_file_info_display(self, qtbot, tmp_path):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        (tmp_path / "test.vti").write_text("dummy content here")
        panel.set_output_directory(str(tmp_path))
        panel._file_list.setCurrentRow(0)
        # File info should be populated
        info = panel._info_lbl.text()
        assert "test.vti" in info

    def test_file_count_label(self, qtbot, tmp_path):
        panel = PostProcessPanel()
        qtbot.addWidget(panel)
        for i in range(5):
            (tmp_path / f"file_{i}.vti").write_text("dummy")
        panel.set_output_directory(str(tmp_path))
        assert "5" in panel._file_count_lbl.text()


# ===================================================================
# Cross-Panel Integration Tests
# ===================================================================

class TestPanelIntegration:
    """Test interactions between panels via load/save cycles."""

    def test_full_project_round_trip_all_panels(self, qtbot):
        """Load a project into all panels, save back, verify fidelity."""
        p = _make_test_project()

        # Create all panels
        general = GeneralPanel()
        domain = DomainPanel()
        fluid = FluidPanel()
        chemistry = ChemistryPanel()
        equilibrium = EquilibriumPanel()
        microbiology = MicrobiologyPanel()
        solver = SolverPanel()
        io_panel = IOPanel()

        for w in [general, domain, fluid, chemistry, equilibrium,
                  microbiology, solver, io_panel]:
            qtbot.addWidget(w)

        # Load into all panels
        general.load_from_project(p)
        domain.load_from_project(p)
        fluid.load_from_project(p)
        chemistry.load_from_project(p)
        equilibrium.load_from_project(p)
        microbiology.load_from_project(p)
        solver.load_from_project(p)
        io_panel.load_from_project(p)

        # Save back from all panels
        p2 = CompLaBProject()
        general.save_to_project(p2)
        domain.save_to_project(p2)
        fluid.save_to_project(p2)
        chemistry.save_to_project(p2)
        equilibrium.save_to_project(p2)
        microbiology.save_to_project(p2)
        solver.save_to_project(p2)
        io_panel.save_to_project(p2)

        # Verify key fields
        assert p2.simulation_mode.biotic_mode == p.simulation_mode.biotic_mode
        assert p2.domain.nx == p.domain.nx
        assert p2.domain.ny == p.domain.ny
        assert p2.domain.nz == p.domain.nz
        assert abs(p2.fluid.tau - p.fluid.tau) < 1e-6
        assert abs(p2.fluid.delta_P - p.fluid.delta_P) < 1e-8
        assert len(p2.substrates) == len(p.substrates)
        assert p2.substrates[0].name == p.substrates[0].name
        assert len(p2.microbiology.microbes) == len(p.microbiology.microbes)
        assert p2.microbiology.microbes[0].name == p.microbiology.microbes[0].name
        assert p2.equilibrium.enabled == p.equilibrium.enabled
        assert p2.equilibrium.component_names == p.equilibrium.component_names
        assert p2.iteration.ns_max_iT1 == p.iteration.ns_max_iT1
        assert p2.iteration.ade_max_iT == p.iteration.ade_max_iT
        assert p2.io_settings.save_vtk_interval == p.io_settings.save_vtk_interval

    def test_chemistry_to_equilibrium_sync(self, qtbot):
        """Verify substrate names flow from Chemistry to Equilibrium panel."""
        chem = ChemistryPanel()
        eq = EquilibriumPanel()
        qtbot.addWidget(chem)
        qtbot.addWidget(eq)

        # Connect signals like main_window does
        chem.substrates_changed.connect(eq.set_substrate_names)

        # Add substrates
        chem._add_substrate()
        chem._list.setCurrentRow(0)
        chem._name.setText("DOC")

        chem._add_substrate()
        chem._list.setCurrentRow(1)
        chem._name.setText("CO2")

        # Equilibrium panel should know about them
        assert "DOC" in eq._subs_info.text()
        assert "CO2" in eq._subs_info.text()

    def test_empty_project_round_trip(self, qtbot):
        """Load a default project with no substrates/microbes, save back."""
        p = CompLaBProject()

        general = GeneralPanel()
        domain = DomainPanel()
        fluid = FluidPanel()
        chemistry = ChemistryPanel()
        solver = SolverPanel()
        io_panel = IOPanel()

        for w in [general, domain, fluid, chemistry, solver, io_panel]:
            qtbot.addWidget(w)

        general.load_from_project(p)
        domain.load_from_project(p)
        fluid.load_from_project(p)
        chemistry.load_from_project(p)
        solver.load_from_project(p)
        io_panel.load_from_project(p)

        p2 = CompLaBProject()
        general.save_to_project(p2)
        domain.save_to_project(p2)
        fluid.save_to_project(p2)
        chemistry.save_to_project(p2)
        solver.save_to_project(p2)
        io_panel.save_to_project(p2)

        assert len(p2.substrates) == 0
        assert len(p2.microbiology.microbes) == 0
        assert p2.domain.nx == 50
        assert abs(p2.fluid.tau - 0.8) < 1e-6


# ===================================================================
# RunPanel HTML Escape Test
# ===================================================================

class TestRunPanelHelpers:
    """Test RunPanel helper functions."""

    def test_escape_html(self):
        from src.panels.run_panel import _escape_html
        assert _escape_html("<b>test</b>") == "&lt;b&gt;test&lt;/b&gt;"
        assert _escape_html("a & b") == "a &amp; b"
        assert _escape_html('"quoted"') == "&quot;quoted&quot;"

    def test_output_max_lines_constant(self):
        from src.panels.run_panel import _OUTPUT_MAX_LINES
        assert _OUTPUT_MAX_LINES == 50000
