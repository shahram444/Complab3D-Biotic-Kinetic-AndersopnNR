"""CompLaB Studio 2.1 - COMSOL-Style Main Window.

4-panel layout:
  Left:   Model Builder tree (navigation)
  Center: VTK 3D viewer (always visible)
  Right:  Context-sensitive settings panel
  Bottom: Console output + progress
"""

import copy
import os
import time
from pathlib import Path

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QStackedWidget, QMenuBar, QMenu,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QDragEnterEvent, QDropEvent

from .config import AppConfig
from .core.project import CompLaBProject
from .core.project_manager import ProjectManager
from .core.simulation_runner import SimulationRunner

from .widgets.model_tree import (
    ModelTree, NODE_GENERAL, NODE_DOMAIN, NODE_FLUID,
    NODE_CHEMISTRY, NODE_SUBSTRATE, NODE_EQUILIBRIUM,
    NODE_MICROBIOLOGY, NODE_MICROBE, NODE_SOLVER,
    NODE_IO, NODE_PARALLEL, NODE_SWEEP, NODE_RUN, NODE_POSTPROCESS,
)
from .widgets.console_widget import ConsoleWidget
from .widgets.vtk_viewer import VTKViewer

from .panels.general_panel import GeneralPanel
from .panels.domain_panel import DomainPanel
from .panels.fluid_panel import FluidPanel
from .panels.chemistry_panel import ChemistryPanel
from .panels.equilibrium_panel import EquilibriumPanel
from .panels.microbiology_panel import MicrobiologyPanel
from .panels.solver_panel import SolverPanel
from .panels.io_panel import IOPanel
from .panels.parallel_panel import ParallelPanel
from .panels.sweep_panel import SweepPanel
from .panels.run_panel import RunPanel
from .panels.postprocess_panel import PostProcessPanel

from .dialogs.new_project_dialog import NewProjectDialog
from .dialogs.kinetics_editor_dialog import KineticsEditorDialog
from .dialogs.preferences_dialog import PreferencesDialog
from .dialogs.about_dialog import AboutDialog


class CompLaBMainWindow(QMainWindow):
    """Main application window with COMSOL-style 4-panel layout."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CompLaB Studio 2.1")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self._config = AppConfig()
        self._project = CompLaBProject()
        self._project_file = ""
        self._runner = None
        self._modified = False
        self._sim_start_time = 0.0
        self._sim_last_it = 0
        self._sim_last_it_time = 0.0
        self._sim_max_it = 0

        self._setup_panels()
        self._setup_layout()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        # Elapsed time timer for status bar
        self._elapsed_timer = QTimer()
        self._elapsed_timer.timeout.connect(self._update_statusbar_elapsed)

        # Auto-save timer
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        if self._config.get("auto_save"):
            interval = self._config.get("auto_save_interval", 300) * 1000
            self._auto_save_timer.start(interval)

        # Enable drag-and-drop on main window
        self.setAcceptDrops(True)

        # Restore window state from config
        self._restore_window_state()

        self._load_project_to_panels()
        self._console.log_info("CompLaB Studio 2.1 ready.")

    # ── Panel setup ─────────────────────────────────────────────────

    def _setup_panels(self):
        """Create all settings panels."""
        self._general_panel = GeneralPanel()
        self._domain_panel = DomainPanel()
        self._fluid_panel = FluidPanel()
        self._chemistry_panel = ChemistryPanel()
        self._equilibrium_panel = EquilibriumPanel()
        self._micro_panel = MicrobiologyPanel()
        self._solver_panel = SolverPanel()
        self._io_panel = IOPanel()
        self._parallel_panel = ParallelPanel()
        self._sweep_panel = SweepPanel()
        self._run_panel = RunPanel()
        self._post_panel = PostProcessPanel()

        # Stacked widget for right panel
        self._panel_stack = QStackedWidget()
        self._panel_stack.addWidget(self._general_panel)    # 0
        self._panel_stack.addWidget(self._domain_panel)     # 1
        self._panel_stack.addWidget(self._fluid_panel)      # 2
        self._panel_stack.addWidget(self._chemistry_panel)  # 3
        self._panel_stack.addWidget(self._equilibrium_panel)  # 4
        self._panel_stack.addWidget(self._micro_panel)      # 5
        self._panel_stack.addWidget(self._solver_panel)     # 6
        self._panel_stack.addWidget(self._io_panel)         # 7
        self._panel_stack.addWidget(self._parallel_panel)   # 8
        self._panel_stack.addWidget(self._sweep_panel)      # 9
        self._panel_stack.addWidget(self._run_panel)        # 10
        self._panel_stack.addWidget(self._post_panel)       # 11

        self._panel_map = {
            NODE_GENERAL: 0,
            NODE_DOMAIN: 1,
            NODE_FLUID: 2,
            NODE_CHEMISTRY: 3,
            NODE_SUBSTRATE: 3,
            NODE_EQUILIBRIUM: 4,
            NODE_MICROBIOLOGY: 5,
            NODE_MICROBE: 5,
            NODE_SOLVER: 6,
            NODE_IO: 7,
            NODE_PARALLEL: 8,
            NODE_SWEEP: 9,
            NODE_RUN: 10,
            NODE_POSTPROCESS: 11,
        }

    def _setup_layout(self):
        """Create the 4-panel COMSOL-style layout using splitters."""
        # Left: Model tree
        self._tree = ModelTree()
        self._tree.setMinimumWidth(200)
        self._tree.setMaximumWidth(350)

        # Center: VTK viewer
        self._viewer = VTKViewer()

        # Right: Settings panels
        self._panel_stack.setMinimumWidth(340)

        # Bottom: Console
        self._console = ConsoleWidget()
        self._console.setMinimumHeight(100)
        self._console.set_max_lines(
            self._config.get("max_console_lines", 10000))

        # Horizontal splitter: tree | viewer | settings
        self._h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._h_splitter.addWidget(self._tree)
        self._h_splitter.addWidget(self._viewer)
        self._h_splitter.addWidget(self._panel_stack)
        self._h_splitter.setStretchFactor(0, 0)   # Tree: fixed
        self._h_splitter.setStretchFactor(1, 3)   # Viewer: takes most space
        self._h_splitter.setStretchFactor(2, 1)   # Settings: moderate
        self._h_splitter.setSizes([220, 600, 380])

        # Vertical splitter: [h_splitter] / console
        self._v_splitter = QSplitter(Qt.Orientation.Vertical)
        self._v_splitter.addWidget(self._h_splitter)
        self._v_splitter.addWidget(self._console)
        self._v_splitter.setStretchFactor(0, 4)
        self._v_splitter.setStretchFactor(1, 1)
        self._v_splitter.setSizes([650, 180])

        self.setCentralWidget(self._v_splitter)

    # ── Menus ───────────────────────────────────────────────────────

    def _setup_menus(self):
        mb = self.menuBar()

        # ─── File ───
        file_menu = mb.addMenu("&File")
        self._act_new = file_menu.addAction("&New Project...")
        self._act_new.setShortcut(QKeySequence.StandardKey.New)
        self._act_new.triggered.connect(self._new_project)

        self._act_open = file_menu.addAction("&Open Project...")
        self._act_open.setShortcut(QKeySequence.StandardKey.Open)
        self._act_open.triggered.connect(self._open_project)

        self._act_save = file_menu.addAction("&Save Project")
        self._act_save.setShortcut(QKeySequence.StandardKey.Save)
        self._act_save.triggered.connect(self._save_project)

        self._act_save_as = file_menu.addAction("Save Project &As...")
        self._act_save_as.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self._act_save_as.triggered.connect(self._save_project_as)

        file_menu.addSeparator()

        self._act_import = file_menu.addAction("&Import CompLaB.xml...")
        self._act_import.triggered.connect(self._import_xml)

        self._act_export = file_menu.addAction("&Export CompLaB.xml...")
        self._act_export.triggered.connect(self._export_xml)

        file_menu.addSeparator()

        # Recent projects submenu
        self._recent_menu = file_menu.addMenu("Recent Projects")
        self._update_recent_menu()

        file_menu.addSeparator()

        act_quit = file_menu.addAction("&Quit")
        act_quit.setShortcut(QKeySequence.StandardKey.Quit)
        act_quit.triggered.connect(self.close)

        # ─── Edit ───
        edit_menu = mb.addMenu("&Edit")
        act_prefs = edit_menu.addAction("&Preferences...")
        act_prefs.setShortcut(QKeySequence("Ctrl+,"))
        act_prefs.triggered.connect(self._open_preferences)

        # ─── Tools ───
        tools_menu = mb.addMenu("&Tools")
        self._act_validate = tools_menu.addAction("&Validate Configuration")
        self._act_validate.setShortcut(QKeySequence("F5"))
        self._act_validate.triggered.connect(self._validate)

        tools_menu.addSeparator()

        act_kinetics = tools_menu.addAction("Kinetics &Editor...")
        act_kinetics.triggered.connect(self._open_kinetics_editor)

        act_geom_gen = tools_menu.addAction("&Geometry Generator...")
        act_geom_gen.setToolTip(
            "Open the geometry generator tool for creating .dat files")
        act_geom_gen.triggered.connect(self._open_geometry_generator)

        tools_menu.addSeparator()

        self._act_run = tools_menu.addAction("&Run Simulation")
        self._act_run.setShortcut(QKeySequence("F6"))
        self._act_run.triggered.connect(self._run_simulation)

        self._act_stop = tools_menu.addAction("&Stop Simulation")
        self._act_stop.setShortcut(QKeySequence("Shift+F6"))
        self._act_stop.setEnabled(False)
        self._act_stop.triggered.connect(self._stop_simulation)

        # ─── View ───
        view_menu = mb.addMenu("&View")
        self._act_toggle_console = view_menu.addAction("Toggle Console")
        self._act_toggle_console.setShortcut(QKeySequence("Ctrl+`"))
        self._act_toggle_console.triggered.connect(self._toggle_console)

        view_menu.addSeparator()

        act_reset_view = view_menu.addAction("Reset 3D View")
        act_reset_view.setShortcut(QKeySequence("Ctrl+R"))
        act_reset_view.triggered.connect(
            lambda: self._viewer.reset_view())

        act_remove_vtk = view_menu.addAction("Remove Loaded VTK")
        act_remove_vtk.setShortcut(QKeySequence("Ctrl+Shift+R"))
        act_remove_vtk.triggered.connect(self._clear_3d_scene)

        act_clear_scene = view_menu.addAction("Clear 3D Scene")
        act_clear_scene.triggered.connect(self._clear_3d_scene)

        view_menu.addSeparator()

        act_open_vtk = view_menu.addAction("Open VTK in Viewer...")
        act_open_vtk.triggered.connect(self._viewer._open_file_dialog)

        # ─── Navigate (Alt+1..9) ───
        nav_menu = mb.addMenu("&Navigate")
        nav_nodes = [
            ("1", "Simulation Mode", NODE_GENERAL),
            ("2", "Domain", NODE_DOMAIN),
            ("3", "Fluid / Flow", NODE_FLUID),
            ("4", "Chemistry", NODE_CHEMISTRY),
            ("5", "Microbiology", NODE_MICROBIOLOGY),
            ("6", "Solver Settings", NODE_SOLVER),
            ("7", "I/O Settings", NODE_IO),
            ("8", "Run", NODE_RUN),
            ("9", "Post-Processing", NODE_POSTPROCESS),
        ]
        for key, label, node in nav_nodes:
            act = nav_menu.addAction(f"&{label}")
            act.setShortcut(QKeySequence(f"Alt+{key}"))
            act.triggered.connect(
                lambda checked, n=node: self._tree.select_node(n))

        # ─── Help ───
        help_menu = mb.addMenu("&Help")
        act_about = help_menu.addAction("&About CompLaB Studio")
        act_about.triggered.connect(self._show_about)

    def _setup_toolbar(self):
        tb = QToolBar("Main")
        tb.setMovable(False)
        tb.setFloatable(False)
        tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.addToolBar(tb)

        # Project section
        self._act_new.setText("New")
        self._act_open.setText("Open")
        self._act_save.setText("Save")
        tb.addAction(self._act_new)
        tb.addAction(self._act_open)
        tb.addAction(self._act_save)
        tb.addSeparator()

        # XML section
        self._act_import.setText("Import XML")
        self._act_export.setText("Export XML")
        tb.addAction(self._act_import)
        tb.addAction(self._act_export)
        tb.addSeparator()

        # Build section
        self._act_validate.setText("Validate")
        tb.addAction(self._act_validate)
        tb.addSeparator()

        # Run section
        self._act_run.setText("Run")
        self._act_stop.setText("Stop")
        tb.addAction(self._act_run)
        tb.addAction(self._act_stop)
        tb.addSeparator()

        # Theme toggle
        current_theme = self._config.get("theme", "Dark")
        theme_label = "Light" if current_theme == "Dark" else "Dark"
        self._act_theme = tb.addAction(f"Theme: {theme_label}")
        self._act_theme.setToolTip("Toggle between Dark and Light themes")
        self._act_theme.triggered.connect(self._toggle_theme)

    def _setup_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("Ready")
        sb.addWidget(self._status_label, 1)
        self._elapsed_label = QLabel("")
        sb.addPermanentWidget(self._elapsed_label)
        self._eta_label = QLabel("")
        sb.addPermanentWidget(self._eta_label)
        self._resource_label = QLabel("")
        sb.addPermanentWidget(self._resource_label)
        self._mem_label = QLabel("")
        sb.addPermanentWidget(self._mem_label)

    # ── Signal connections ──────────────────────────────────────────

    def _connect_signals(self):
        # Tree navigation
        self._tree.node_selected.connect(self._on_node_selected)

        # Chemistry <-> tree sync
        self._chemistry_panel.substrates_changed.connect(
            self._on_substrates_changed)
        self._micro_panel.microbes_changed.connect(
            self._on_microbes_changed)

        # Domain geometry preview
        self._domain_panel.geometry_loaded.connect(
            self._viewer.load_geometry_dat)

        # Run panel
        self._run_panel.run_requested.connect(self._run_simulation)
        self._run_panel.stop_requested.connect(self._stop_simulation)
        self._run_panel.validate_requested.connect(self._validate)
        self._run_panel.export_xml_requested.connect(self._export_xml)

        # Post-process file selection -> viewer
        self._post_panel.file_selected.connect(self._viewer.load_vti)
        self._post_panel.remove_vtk_requested.connect(self._clear_3d_scene)

        # Data changed -> mark modified
        for panel in [
            self._general_panel, self._domain_panel, self._fluid_panel,
            self._chemistry_panel, self._equilibrium_panel,
            self._micro_panel, self._solver_panel, self._io_panel,
        ]:
            panel.data_changed.connect(self._on_data_changed)

        # Domain/chemistry/micro changes -> update memory estimate
        self._domain_panel.data_changed.connect(self._on_domain_changed)
        self._chemistry_panel.substrates_changed.connect(
            lambda _: self._update_memory_estimate())
        self._micro_panel.microbes_changed.connect(
            lambda _: self._update_memory_estimate())

        # Parallel panel data_changed
        self._parallel_panel.data_changed.connect(self._on_data_changed)

        # Sweep panel
        self._sweep_panel.sweep_requested.connect(self._on_sweep_requested)

    def _on_node_selected(self, node_type: str, index: int):
        """Switch right panel based on tree selection."""
        panel_idx = self._panel_map.get(node_type, 0)
        self._panel_stack.setCurrentIndex(panel_idx)

        # Select specific substrate or microbe
        if node_type == NODE_SUBSTRATE and index >= 0:
            self._chemistry_panel.select_substrate(index)
        elif node_type == NODE_MICROBE and index >= 0:
            self._micro_panel.select_microbe(index)

    def _on_substrates_changed(self, names: list):
        self._tree.update_substrates(names)
        self._equilibrium_panel.set_substrate_names(names)

    def _on_microbes_changed(self, names: list):
        self._tree.update_microbes(names)

    def _on_data_changed(self):
        self._modified = True
        self._update_title()

    def _on_domain_changed(self):
        """Update memory estimate when domain dimensions change."""
        self._save_panels_to_project()
        self._update_memory_estimate()

    # ── Project load/save ───────────────────────────────────────────

    def _load_project_to_panels(self):
        """Push project data to all panels."""
        p = self._project
        self._general_panel.load_from_project(p)
        self._domain_panel.load_from_project(p)
        self._fluid_panel.load_from_project(p)
        self._chemistry_panel.load_from_project(p)
        self._equilibrium_panel.load_from_project(p)
        self._micro_panel.load_from_project(p)
        self._solver_panel.load_from_project(p)
        self._io_panel.load_from_project(p)

        self._tree.update_project_name(p.name)
        self._tree.update_substrates([s.name for s in p.substrates])
        self._tree.update_microbes([m.name for m in p.microbiology.microbes])
        self._tree.select_node(NODE_GENERAL)
        self._modified = False
        self._update_title()

        # Auto-detect output directory for post-processing
        self._update_postprocess_output_dir()

        # Update domain memory estimate in status bar
        self._update_memory_estimate()

    def _save_panels_to_project(self):
        """Pull data from all panels into project."""
        p = self._project
        self._general_panel.save_to_project(p)
        self._domain_panel.save_to_project(p)
        self._fluid_panel.save_to_project(p)
        self._chemistry_panel.save_to_project(p)
        self._equilibrium_panel.save_to_project(p)
        self._micro_panel.save_to_project(p)
        self._solver_panel.save_to_project(p)
        self._io_panel.save_to_project(p)

    def _update_title(self):
        name = self._project.name or "Untitled"
        mod = " *" if self._modified else ""
        self.setWindowTitle(f"CompLaB Studio 2.1 - {name}{mod}")

    # ── File actions ────────────────────────────────────────────────

    def _new_project(self):
        if self._modified and not self._confirm_discard():
            return
        dlg = NewProjectDialog(
            self._config.get("default_project_dir", ""), self)
        if dlg.exec():
            self._project = dlg.get_project()
            self._project_file = ""
            self._load_project_to_panels()
            self._console.log_info(f"New project: {self._project.name}")

    def _open_project(self):
        if self._modified and not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "",
            "CompLaB Project (*.complab);;All Files (*)")
        if not path:
            return
        try:
            self._project = ProjectManager.load_project(path)
            self._project_file = path
            self._config.add_recent(path)
            self._update_recent_menu()
            self._load_project_to_panels()
            self._console.log_success(f"Opened: {path}")
        except Exception as e:
            self._console.log_error(f"Failed to open project: {e}")
            QMessageBox.critical(self, "Open Error", str(e))

    def _save_project(self):
        if not self._project_file:
            self._save_project_as()
            return
        self._save_panels_to_project()
        try:
            ProjectManager.save_project(self._project, self._project_file)
            self._modified = False
            self._update_title()
            self._console.log_success(f"Saved: {self._project_file}")
        except Exception as e:
            self._console.log_error(f"Save failed: {e}")

    def _save_project_as(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As", self._project.name + ".complab",
            "CompLaB Project (*.complab);;All Files (*)")
        if not path:
            return
        self._project_file = path
        self._config.add_recent(path)
        self._update_recent_menu()
        self._save_project()

    def _import_xml(self):
        if self._modified and not self._confirm_discard():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CompLaB.xml", "",
            "XML Files (*.xml);;All Files (*)")
        if not path:
            return
        try:
            self._project = ProjectManager.import_xml(path)
            self._project_file = ""
            self._load_project_to_panels()
            self._console.log_success(f"Imported: {path}")
        except Exception as e:
            self._console.log_error(f"Import failed: {e}")
            QMessageBox.critical(self, "Import Error", str(e))

    def _export_xml(self):
        self._save_panels_to_project()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CompLaB.xml", "CompLaB.xml",
            "XML Files (*.xml);;All Files (*)")
        if not path:
            return
        try:
            ProjectManager.export_xml(self._project, path)
            self._console.log_success(f"Exported: {path}")
        except Exception as e:
            self._console.log_error(f"Export failed: {e}")

    def _update_recent_menu(self):
        self._recent_menu.clear()
        recents = self._config.get("recent_projects", [])
        for path in recents:
            act = self._recent_menu.addAction(path)
            act.triggered.connect(lambda checked, p=path: self._open_recent(p))
        if not recents:
            act = self._recent_menu.addAction("(no recent projects)")
            act.setEnabled(False)

    def _open_recent(self, path):
        if not os.path.exists(path):
            self._console.log_error(f"File not found: {path}")
            return
        try:
            self._project = ProjectManager.load_project(path)
            self._project_file = path
            self._load_project_to_panels()
            self._console.log_success(f"Opened: {path}")
        except Exception as e:
            self._console.log_error(f"Failed to open: {e}")

    # ── Simulation ──────────────────────────────────────────────────

    def _run_simulation(self):
        self._save_panels_to_project()
        exe = self._config.get("complab_executable", "")
        if not exe:
            self._console.log_error(
                "CompLaB executable not set. Go to Edit > Preferences.")
            return

        # Determine working directory
        if self._project_file:
            work_dir = str(Path(self._project_file).parent)
        else:
            work_dir = os.getcwd()

        # Export XML first
        xml_path = os.path.join(work_dir, "CompLaB.xml")
        try:
            ProjectManager.export_xml(self._project, xml_path)
            self._console.log_info(f"Exported {xml_path}")
        except Exception as e:
            self._console.log_error(f"XML export failed: {e}")
            return

        self._act_run.setEnabled(False)
        self._act_stop.setEnabled(True)

        # MPI parallel settings
        mpi_cmd = ""
        num_cores = 1
        if self._parallel_panel.is_parallel_enabled():
            mpi_cmd = self._parallel_panel.get_mpi_command()
            num_cores = self._parallel_panel.get_num_cores()

        # Validate domain vs core count
        d = self._project.domain
        self._parallel_panel.validate_for_domain(d.nx, d.ny, d.nz)

        self._runner = SimulationRunner(
            exe, work_dir, self,
            mpi_command=mpi_cmd, num_cores=num_cores,
            project=self._project,
        )
        self._runner.output_line.connect(self._console.append)
        self._runner.progress.connect(self._run_panel.on_progress)
        self._runner.progress.connect(
            lambda c, m: self._console.set_progress(c, m))
        self._runner.progress.connect(self._on_sim_progress)
        self._runner.convergence.connect(self._on_convergence)
        self._runner.phase_changed.connect(self._on_phase_changed)
        self._runner.finished_signal.connect(self._on_sim_finished)
        self._runner.diagnostic_signal.connect(self._on_diagnostic)

        # Start elapsed / ETA tracking
        self._sim_start_time = time.time()
        self._sim_last_it = 0
        self._sim_last_it_time = 0.0
        self._sim_max_it = 0
        self._elapsed_timer.start(1000)

        self._runner.start()
        self._console.set_status("Running...")
        self._status_label.setText("Running...")

    def _stop_simulation(self):
        if self._runner:
            self._runner.cancel()

    def _on_sim_progress(self, current: int, maximum: int):
        """Track iteration progress for ETA calculation."""
        now = time.time()
        if current > self._sim_last_it:
            self._sim_last_it_time = now
            self._sim_last_it = current
        if maximum > self._sim_max_it:
            self._sim_max_it = maximum

    def _on_convergence(self, solver: str, iteration: int, residual: float):
        """Log convergence data from the solver."""
        self._run_panel.on_convergence(solver, iteration, residual)

    def _on_phase_changed(self, phase: str):
        """Update status when simulation phase changes."""
        self._status_label.setText(phase)
        self._console.log_info(f"Phase: {phase}")

    def _update_statusbar_elapsed(self):
        """Update elapsed + ETA + resource labels every second."""
        elapsed = time.time() - self._sim_start_time
        self._elapsed_label.setText(
            f"Elapsed: {self._fmt_duration(elapsed)}")
        # ETA calculation
        if self._sim_max_it > 0 and self._sim_last_it > 0:
            rate = self._sim_last_it / elapsed  # iterations per second
            if rate > 0:
                remaining_it = self._sim_max_it - self._sim_last_it
                eta_secs = remaining_it / rate
                self._eta_label.setText(
                    f"ETA: {self._fmt_duration(eta_secs)}  "
                    f"({self._sim_last_it}/{self._sim_max_it})")
            else:
                self._eta_label.setText("ETA: --")
        else:
            self._eta_label.setText("")
        # Resource monitor
        if HAS_PSUTIL:
            cpu = psutil.cpu_percent(interval=0)
            ram = psutil.virtual_memory()
            self._resource_label.setText(
                f"CPU: {cpu:.0f}%  RAM: {ram.percent:.0f}% "
                f"({ram.used / (1024**3):.1f}/{ram.total / (1024**3):.1f} GB)"
            )

    @staticmethod
    def _fmt_duration(seconds: float) -> str:
        s = int(seconds)
        hrs, rem = divmod(s, 3600)
        mins, secs = divmod(rem, 60)
        if hrs > 0:
            return f"{hrs}:{mins:02d}:{secs:02d}"
        return f"{mins}:{secs:02d}"

    def _on_diagnostic(self, report: str):
        """Display a diagnostic report in the console with color coding."""
        self._console.log_diagnostic(report)

    def _on_sim_finished(self, code, msg):
        self._elapsed_timer.stop()
        self._run_panel.on_finished(code, msg)
        self._console.set_status("Ready")
        self._console.set_progress(0, 0)
        self._act_run.setEnabled(True)
        self._act_stop.setEnabled(False)
        self._status_label.setText("Ready")
        self._eta_label.setText("")
        self._resource_label.setText("")
        if code == 0:
            self._console.log_success(msg)
            # Show final elapsed time
            elapsed = time.time() - self._sim_start_time
            self._elapsed_label.setText(
                f"Finished in {self._fmt_duration(elapsed)}")
        else:
            self._console.log_error(msg)
            self._elapsed_label.setText("")

        # Auto-refresh post-process output directory
        self._update_postprocess_output_dir()

    # ── Sweep execution ─────────────────────────────────────────────

    def _on_sweep_requested(self, runs: list):
        """Handle parameter sweep: create subdirectories and queue runs."""
        self._save_panels_to_project()
        exe = self._config.get("complab_executable", "")
        if not exe:
            self._console.log_error(
                "CompLaB executable not set. Go to Edit > Preferences.")
            return

        if self._project_file:
            base_dir = str(Path(self._project_file).parent)
        else:
            base_dir = os.getcwd()

        sweep_configs = self._sweep_panel.get_sweep_config()
        if not sweep_configs:
            self._console.log_error("No sweep configuration generated.")
            return

        sweep_dir = os.path.join(base_dir, "sweep_runs")
        os.makedirs(sweep_dir, exist_ok=True)

        self._console.log_info(
            f"Queuing {len(sweep_configs)} sweep runs in {sweep_dir}")

        for i, (section, field, value) in enumerate(sweep_configs):
            run_dir = os.path.join(sweep_dir, f"run_{i:03d}")
            os.makedirs(run_dir, exist_ok=True)

            # Clone project and override the swept parameter
            proj_copy = copy.deepcopy(self._project)
            sub_obj = getattr(proj_copy, section, None)
            if sub_obj is not None and hasattr(sub_obj, field):
                setattr(sub_obj, field, value)
            elif isinstance(sub_obj, dict):
                sub_obj[field] = value

            xml_path = os.path.join(run_dir, "CompLaB.xml")
            try:
                ProjectManager.export_xml(proj_copy, xml_path)
            except Exception as e:
                self._console.log_error(
                    f"Sweep run {i}: XML export failed: {e}")
                continue

            self._console.log_info(
                f"  Run {i}: {section}.{field} = {value}  -> {run_dir}")

        self._console.log_success(
            f"{len(sweep_configs)} sweep run directories created in "
            f"{sweep_dir}.\nRun each manually or implement batch execution.")

    # ── Validation ──────────────────────────────────────────────────

    def _validate(self):
        self._save_panels_to_project()
        errors = self._project.validate()
        self._run_panel.show_validation(errors)
        if errors:
            self._console.log_error(
                f"Validation: {len(errors)} error(s) found.")
            for e in errors:
                self._console.log_error(f"  {e}")
        else:
            self._console.log_success("Validation passed - no errors.")

    # ── View toggles ───────────────────────────────────────────────

    def _toggle_console(self):
        self._console.setVisible(not self._console.isVisible())

    def _toggle_theme(self):
        """Switch between Dark and Light themes."""
        current = self._config.get("theme", "Dark")
        new_theme = "Light" if current == "Dark" else "Dark"
        self._config.set("theme", new_theme)
        self._config.save()

        styles_dir = Path(__file__).parent.parent / "styles"
        if new_theme == "Light":
            style_path = styles_dir / "light.qss"
        else:
            style_path = styles_dir / "theme.qss"

        if style_path.exists():
            from PySide6.QtWidgets import QApplication
            QApplication.instance().setStyleSheet(
                style_path.read_text(encoding="utf-8"))

        # Update button label to show the opposite
        next_theme = "Light" if new_theme == "Dark" else "Dark"
        self._act_theme.setText(f"Theme: {next_theme}")
        self._console.log_info(f"Switched to {new_theme} theme.")

    def _clear_3d_scene(self):
        """Remove all data from the 3D viewer."""
        self._viewer._remove_geometry()

    # ── Dialogs ─────────────────────────────────────────────────────

    def _open_kinetics_editor(self):
        dlg = KineticsEditorDialog(self)
        dlg.exec()

    def _open_geometry_generator(self):
        """Open the geometry generator script via system default."""
        gen_path = Path(__file__).parent.parent.parent / "tools" / "geometry_generator.py"
        if gen_path.exists():
            import subprocess
            import sys
            try:
                subprocess.Popen([sys.executable, str(gen_path)])
                self._console.log_info(f"Launched geometry generator: {gen_path}")
            except Exception as e:
                self._console.log_error(f"Failed to launch geometry generator: {e}")
        else:
            self._console.log_error(
                f"Geometry generator not found at: {gen_path}\n"
                "Expected: tools/geometry_generator.py"
            )
            QMessageBox.warning(
                self, "Not Found",
                "Geometry generator tool not found.\n"
                f"Expected at: {gen_path}"
            )

    def _open_preferences(self):
        dlg = PreferencesDialog(self._config, self)
        if dlg.exec():
            self._console.set_max_lines(
                self._config.get("max_console_lines", 10000))
            # Re-apply auto-save timer
            self._auto_save_timer.stop()
            if self._config.get("auto_save"):
                interval = self._config.get("auto_save_interval", 300) * 1000
                self._auto_save_timer.start(interval)

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    # ── Helpers ─────────────────────────────────────────────────────

    def _confirm_discard(self) -> bool:
        reply = QMessageBox.question(
            self, "Unsaved Changes",
            "Current project has unsaved changes. Discard?",
            QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
        )
        return reply == QMessageBox.StandardButton.Discard

    def _update_postprocess_output_dir(self):
        """Set PostProcess panel output dir from project path + output_path."""
        base_dir = ""
        if self._project_file:
            base_dir = str(Path(self._project_file).parent)
        elif os.getcwd():
            base_dir = os.getcwd()
        if base_dir:
            out_path = self._project.path_settings.output_path or "output"
            out_dir = os.path.join(base_dir, out_path)
            if os.path.isdir(out_dir):
                self._post_panel.set_output_directory(out_dir)

    def _update_memory_estimate(self):
        """Show estimated memory usage for current domain in status bar."""
        d = self._project.domain
        n_cells = d.nx * d.ny * d.nz
        n_subs = max(len(self._project.substrates), 1)
        n_mic = len(self._project.microbiology.microbes)
        # NS lattice: D3Q19 = 19 doubles per cell
        # ADE lattice: D3Q7 = 7 doubles per cell per substrate
        # Biomass: 1 double per cell per microbe
        # Mask: 1 int per cell
        bytes_per_cell = (
            19 * 8                  # NS lattice (D3Q19, double)
            + 7 * 8 * n_subs       # ADE lattices (D3Q7 per substrate)
            + 8 * n_mic            # Biomass fields
            + 4                    # Mask (int32)
        )
        total_bytes = n_cells * bytes_per_cell
        if total_bytes < 1024 ** 2:
            mem_str = f"{total_bytes / 1024:.0f} KB"
        elif total_bytes < 1024 ** 3:
            mem_str = f"{total_bytes / (1024 ** 2):.1f} MB"
        else:
            mem_str = f"{total_bytes / (1024 ** 3):.2f} GB"
        self._mem_label.setText(f"Est. memory: {mem_str} ({n_cells:,} cells)")

    def _auto_save(self):
        if self._modified and self._project_file:
            self._save_project()
            self._console.log_info("Auto-saved.")

    # ── Drag-and-drop ────────────────────────────────────────────────

    _DROP_EXTENSIONS = {
        ".complab": "project",
        ".xml": "xml",
        ".dat": "geometry",
        ".vti": "vtk",
        ".vtk": "vtk",
    }

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                suffix = Path(url.toLocalFile()).suffix.lower()
                if suffix in self._DROP_EXTENSIONS:
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            filepath = url.toLocalFile()
            suffix = Path(filepath).suffix.lower()
            kind = self._DROP_EXTENSIONS.get(suffix)
            if not kind:
                continue
            if kind == "project":
                self._drop_open_project(filepath)
            elif kind == "xml":
                self._drop_import_xml(filepath)
            elif kind == "geometry":
                self._drop_load_geometry(filepath)
            elif kind == "vtk":
                self._drop_load_vtk(filepath)
            break  # Handle first recognized file only
        event.acceptProposedAction()

    def _drop_open_project(self, path: str):
        if self._modified and not self._confirm_discard():
            return
        try:
            self._project = ProjectManager.load_project(path)
            self._project_file = path
            self._config.add_recent(path)
            self._update_recent_menu()
            self._load_project_to_panels()
            self._console.log_success(f"Opened (drop): {path}")
        except Exception as e:
            self._console.log_error(f"Failed to open: {e}")

    def _drop_import_xml(self, path: str):
        if self._modified and not self._confirm_discard():
            return
        try:
            self._project = ProjectManager.import_xml(path)
            self._project_file = ""
            self._load_project_to_panels()
            self._console.log_success(f"Imported (drop): {path}")
        except Exception as e:
            self._console.log_error(f"Import failed: {e}")

    def _drop_load_geometry(self, path: str):
        self._domain_panel.geom_file.setText(os.path.basename(path))
        self._domain_panel._geom_filepath = path
        nx = self._domain_panel.nx.value()
        ny = self._domain_panel.ny.value()
        nz = self._domain_panel.nz.value()
        self._domain_panel._geom_preview.load_geometry(path, nx, ny, nz)
        self._tree.select_node(NODE_DOMAIN)
        self._console.log_info(f"Geometry loaded (drop): {path}")

    def _drop_load_vtk(self, path: str):
        self._viewer.load_vti(path)
        self._tree.select_node(NODE_POSTPROCESS)
        self._console.log_info(f"VTK loaded (drop): {path}")

    # ── Window state persistence ─────────────────────────────────────

    def _save_window_state(self):
        """Save window geometry and splitter positions to config."""
        geo = self.geometry()
        self._config.set("window_geometry", [
            geo.x(), geo.y(), geo.width(), geo.height()])
        self._config.set("window_maximized", self.isMaximized())
        self._config.set("h_splitter_sizes", self._h_splitter.sizes())
        self._config.set("v_splitter_sizes", self._v_splitter.sizes())
        self._config.save()

    def _restore_window_state(self):
        """Restore window geometry and splitter positions from config."""
        geo = self._config.get("window_geometry")
        if geo and len(geo) == 4:
            self.setGeometry(geo[0], geo[1], geo[2], geo[3])
        if self._config.get("window_maximized"):
            self.showMaximized()
        h_sizes = self._config.get("h_splitter_sizes")
        if h_sizes and len(h_sizes) == 3:
            self._h_splitter.setSizes(h_sizes)
        v_sizes = self._config.get("v_splitter_sizes")
        if v_sizes and len(v_sizes) == 2:
            self._v_splitter.setSizes(v_sizes)

    # ── Close event ──────────────────────────────────────────────────

    def closeEvent(self, event):
        self._save_window_state()
        if self._modified:
            reply = QMessageBox.question(
                self, "Quit",
                "Save changes before quitting?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_project()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        if self._runner and self._runner.isRunning():
            self._runner.cancel()
            self._runner.wait(3000)
        event.accept()
