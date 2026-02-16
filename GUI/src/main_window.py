"""CompLaB Studio 2.0 - COMSOL-Style Main Window.

4-panel layout:
  Left:   Model Builder tree (navigation)
  Center: VTK 3D viewer (always visible)
  Right:  Context-sensitive settings panel
  Bottom: Console output + progress
"""

import os
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QSplitter, QStackedWidget, QMenuBar, QMenu,
    QToolBar, QStatusBar, QFileDialog, QMessageBox, QLabel,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence

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
        self.setWindowTitle("CompLaB Studio 2.0")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        self._config = AppConfig()
        self._project = CompLaBProject()
        self._project_file = ""
        self._runner = None
        self._modified = False

        self._setup_panels()
        self._setup_layout()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        # Auto-save timer
        self._auto_save_timer = QTimer()
        self._auto_save_timer.timeout.connect(self._auto_save)
        if self._config.get("auto_save"):
            interval = self._config.get("auto_save_interval", 300) * 1000
            self._auto_save_timer.start(interval)

        self._load_project_to_panels()
        self._console.log_info("CompLaB Studio 2.0 ready.")

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
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.addWidget(self._tree)
        h_splitter.addWidget(self._viewer)
        h_splitter.addWidget(self._panel_stack)
        h_splitter.setStretchFactor(0, 0)   # Tree: fixed
        h_splitter.setStretchFactor(1, 3)   # Viewer: takes most space
        h_splitter.setStretchFactor(2, 1)   # Settings: moderate
        h_splitter.setSizes([220, 600, 380])

        # Vertical splitter: [h_splitter] / console
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.addWidget(h_splitter)
        v_splitter.addWidget(self._console)
        v_splitter.setStretchFactor(0, 4)
        v_splitter.setStretchFactor(1, 1)
        v_splitter.setSizes([650, 180])

        self.setCentralWidget(v_splitter)

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

    def _setup_statusbar(self):
        sb = QStatusBar()
        self.setStatusBar(sb)
        self._status_label = QLabel("Ready")
        sb.addPermanentWidget(self._status_label)

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

        # Parallel panel -> sync MPI config to Run panel
        self._parallel_panel.data_changed.connect(self._sync_mpi_from_parallel)

        # Sweep panel
        self._sweep_panel.sweep_requested.connect(self._run_sweep)

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
        self.setWindowTitle(f"CompLaB Studio 2.0 - {name}{mod}")

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
            # Deploy kinetics .hh files alongside the XML
            xml_dir = str(Path(path).parent)
            deployed = ProjectManager.deploy_kinetics(self._project, xml_dir)
            for dp in deployed:
                self._console.log_success(f"Deployed: {dp}")
            if deployed:
                self._console.log_info(
                    "Kinetics .hh files saved. Copy them to your solver "
                    "source root and recompile to use the new kinetics.")
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

    def _find_executable(self, work_dir: str) -> str:
        """Auto-detect the complab executable in common locations."""
        import sys
        exe_name = "complab.exe" if sys.platform == "win32" else "complab"

        # 1. Check user-configured path first
        configured = self._config.get("complab_executable", "")
        if configured and os.path.isfile(configured):
            return configured

        # 2. Search common locations relative to the working directory
        search_dirs = [
            work_dir,                                    # project root
            os.path.join(work_dir, "build"),             # build directory
            os.path.join(work_dir, "Release"),           # MSVC Release
            os.path.join(work_dir, "Debug"),             # MSVC Debug
            os.path.join(work_dir, "GUI", "bin"),        # GUI bundled
        ]
        # Also search relative to the GUI directory
        gui_dir = str(Path(__file__).resolve().parent.parent)
        search_dirs.append(os.path.join(gui_dir, "bin"))
        # And one level up from GUI (the repo root)
        repo_root = str(Path(gui_dir).parent)
        if repo_root != work_dir:
            search_dirs.extend([
                repo_root,
                os.path.join(repo_root, "build"),
                os.path.join(repo_root, "Release"),
            ])

        for d in search_dirs:
            candidate = os.path.join(d, exe_name)
            if os.path.isfile(candidate):
                return candidate

        return ""

    def _run_simulation(self):
        self._save_panels_to_project()

        # Determine working directory
        if self._project_file:
            work_dir = str(Path(self._project_file).parent)
        else:
            work_dir = os.getcwd()

        # Auto-detect executable
        exe = self._find_executable(work_dir)
        if not exe:
            self._console.log_error(
                "CompLaB executable not found. Searched project root, "
                "build/, Release/, and GUI/bin/. "
                "Set the path in Edit > Preferences, or build with "
                "'cd build && cmake .. && make'.")
            return

        self._console.log_info(f"Using executable: {exe}")

        # Export XML first
        xml_path = os.path.join(work_dir, "CompLaB.xml")
        try:
            ProjectManager.export_xml(self._project, xml_path)
            self._console.log_info(f"Exported {xml_path}")
            # Deploy kinetics .hh files alongside the XML
            deployed = ProjectManager.deploy_kinetics(self._project, work_dir)
            for dp in deployed:
                self._console.log_info(f"Deployed: {dp}")
        except Exception as e:
            self._console.log_error(f"XML export failed: {e}")
            return

        self._act_run.setEnabled(False)
        self._act_stop.setEnabled(True)

        # Sync MPI settings from parallel panel before reading run panel config
        self._sync_mpi_from_parallel()

        # Get MPI config from run panel
        mpi_enabled, mpi_nprocs, mpi_command = self._run_panel.get_mpi_config()

        self._runner = SimulationRunner(
            exe, work_dir, self,
            mpi_enabled=mpi_enabled,
            mpi_nprocs=mpi_nprocs,
            mpi_command=mpi_command,
        )
        self._runner.output_line.connect(self._console.append)
        self._runner.output_line.connect(self._run_panel.on_output_line)
        self._runner.progress.connect(self._run_panel.on_progress)
        self._runner.progress.connect(
            lambda c, m: self._console.set_progress(c, m))
        self._runner.finished_signal.connect(self._on_sim_finished)
        self._runner.diagnostic_report.connect(self._on_diagnostic_report)
        self._runner.start()
        self._console.set_status("Running...")

    def _stop_simulation(self):
        if self._runner:
            self._runner.cancel()

    def _on_sim_finished(self, code, msg):
        self._run_panel.on_finished(code, msg)
        self._console.set_status("Ready")
        self._console.set_progress(0, 0)
        self._act_run.setEnabled(True)
        self._act_stop.setEnabled(False)
        if code == 0:
            self._console.log_success(msg)
        else:
            self._console.log_error(msg)

    def _on_diagnostic_report(self, report: str):
        """Handle crash diagnostic report: show in console + save to output."""
        # Forward to the run panel's validation tab
        self._run_panel.on_diagnostic_report(report)

        # Print a colour-coded version to the console widget
        self._console.log_diagnostic(report)

        # Save report to the project's output folder
        output_dir = self._project.path_settings.output_path
        if not os.path.isabs(output_dir):
            # Make relative to project file or cwd
            if self._project_file:
                base = str(Path(self._project_file).parent)
            else:
                base = os.getcwd()
            output_dir = os.path.join(base, output_dir)

        from .core.xml_diagnostic import save_diagnostic_report
        saved_path = save_diagnostic_report(report, output_dir)
        if saved_path:
            self._console.log_info(
                f"Crash diagnostic saved: {saved_path}")
        else:
            self._console.log_warning(
                f"Could not save crash diagnostic to {output_dir}")

    def _sync_mpi_from_parallel(self):
        """Push parallel-panel MPI settings into the run-panel widgets."""
        pp = self._parallel_panel
        rp = self._run_panel
        is_on = pp.is_parallel_enabled()
        rp.set_mpi_config(
            enabled=is_on,
            nprocs=pp.get_num_cores() if is_on else 1,
            command=pp.get_mpi_command() if is_on else "",
        )

    def _run_sweep(self, runs: list):
        """Execute a parameter sweep: run simulation for each value."""
        if not runs:
            return
        self._save_panels_to_project()

        if self._project_file:
            base_dir = str(Path(self._project_file).parent)
        else:
            base_dir = os.getcwd()

        exe = self._find_executable(base_dir)
        if not exe:
            self._console.log_error(
                "CompLaB executable not found. Set path in Edit > Preferences "
                "or build with 'cd build && cmake .. && make'.")
            return

        self._sync_mpi_from_parallel()
        mpi_enabled, mpi_nprocs, mpi_command = self._run_panel.get_mpi_config()

        self._console.log_info(
            f"Starting parameter sweep: {len(runs)} runs")

        for i, (param_name, value) in enumerate(runs):
            run_dir = os.path.join(base_dir, f"sweep_{i+1:03d}_{param_name}_{value}")
            os.makedirs(run_dir, exist_ok=True)

            # Apply swept parameter to project
            from .panels.sweep_panel import SWEEP_PARAMS
            if param_name in SWEEP_PARAMS:
                section, field = SWEEP_PARAMS[param_name]
                self._apply_sweep_param(section, field, value)

            # Export XML for this run
            xml_path = os.path.join(run_dir, "CompLaB.xml")
            try:
                ProjectManager.export_xml(self._project, xml_path)
            except Exception as e:
                self._console.log_error(f"Sweep run {i+1}: XML export failed: {e}")
                continue

            # Copy geometry file if it exists in base_dir
            geom_src = os.path.join(base_dir, "geometry.dat")
            geom_dst = os.path.join(run_dir, "geometry.dat")
            if os.path.isfile(geom_src) and not os.path.isfile(geom_dst):
                import shutil
                shutil.copy2(geom_src, geom_dst)

            self._console.log_info(
                f"  Run {i+1}/{len(runs)}: {param_name} = {value} -> {run_dir}")

        self._console.log_success(
            f"Sweep setup complete. {len(runs)} run directories created in {base_dir}")

    def _apply_sweep_param(self, section: str, field: str, value):
        """Apply a single swept parameter value to the project."""
        p = self._project
        try:
            if section == "fluid":
                setattr(p.fluid, field, value)
            elif section == "iteration":
                setattr(p.iteration, field, int(value) if "iT" in field else value)
            elif section == "domain":
                setattr(p.domain, field, int(value) if field in ("nx", "ny", "nz") else value)
            elif section == "microbiology":
                setattr(p.microbiology, field, value)
            elif section == "io_settings":
                setattr(p.io_settings, field, int(value))
        except Exception as e:
            self._console.log_error(f"Failed to set {section}.{field} = {value}: {e}")

    # ── Validation ──────────────────────────────────────────────────

    def _validate(self):
        self._save_panels_to_project()

        # If project has no embedded kinetics, try to read from disk
        self._load_kinetics_from_disk_if_empty()

        errors = self._project.validate()
        self._run_panel.show_validation(errors)
        if errors:
            self._console.log_error(
                f"Validation: {len(errors)} error(s) found.")
            for e in errors:
                self._console.log_error(f"  {e}")
        else:
            self._console.log_success("Validation passed - no errors.")

    def _load_kinetics_from_disk_if_empty(self):
        """If the project has no embedded kinetics source, try to read
        defineKinetics.hh / defineAbioticKinetics.hh from the project
        directory so that validation can cross-check them."""
        if self._project.kinetics_source and self._project.abiotic_kinetics_source:
            return  # already have both

        if self._project_file:
            base = str(Path(self._project_file).parent)
        else:
            base = os.getcwd()

        if not self._project.kinetics_source:
            biotic_path = os.path.join(base, "defineKinetics.hh")
            if os.path.isfile(biotic_path):
                try:
                    with open(biotic_path, "r") as f:
                        self._project.kinetics_source = f.read()
                    self._console.log_info(
                        f"Loaded defineKinetics.hh from {biotic_path} for validation")
                except OSError:
                    pass

        if not self._project.abiotic_kinetics_source:
            abiotic_path = os.path.join(base, "defineAbioticKinetics.hh")
            if os.path.isfile(abiotic_path):
                try:
                    with open(abiotic_path, "r") as f:
                        self._project.abiotic_kinetics_source = f.read()
                    self._console.log_info(
                        f"Loaded defineAbioticKinetics.hh from {abiotic_path} for validation")
                except OSError:
                    pass

    # ── View toggles ───────────────────────────────────────────────

    def _toggle_console(self):
        self._console.setVisible(not self._console.isVisible())

    def _clear_3d_scene(self):
        """Remove all data from the 3D viewer."""
        self._viewer._remove_geometry()

    # ── Dialogs ─────────────────────────────────────────────────────

    def _open_kinetics_editor(self):
        self._save_panels_to_project()
        dlg = KineticsEditorDialog(self)
        # Pre-load project kinetics source into the editor
        if self._project.kinetics_source:
            dlg._biotic_tab._editor.setPlainText(self._project.kinetics_source)
            dlg._biotic_tab._path_label.setText("(from project template)")
        if self._project.abiotic_kinetics_source:
            dlg._abiotic_tab._editor.setPlainText(
                self._project.abiotic_kinetics_source)
            dlg._abiotic_tab._path_label.setText("(from project template)")
        if dlg.exec():
            # Save any edits back to the project
            biotic_text = dlg._biotic_tab._editor.toPlainText()
            abiotic_text = dlg._abiotic_tab._editor.toPlainText()
            if biotic_text.strip():
                self._project.kinetics_source = biotic_text
            if abiotic_text.strip():
                self._project.abiotic_kinetics_source = abiotic_text
            self._modified = True
            self._update_title()
            self._console.log_info("Kinetics source updated from editor.")

    def _open_geometry_generator(self):
        """Open the geometry generator as a GUI dialog."""
        from .dialogs.geometry_creator_dialog import GeometryCreatorDialog
        dlg = GeometryCreatorDialog(self._project, self._config, self)
        dlg.exec()
        self._console.log_info("Geometry creator closed.")

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

    def _auto_save(self):
        if self._modified and self._project_file:
            self._save_project()
            self._console.log_info("Auto-saved.")

    def closeEvent(self, event):
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
