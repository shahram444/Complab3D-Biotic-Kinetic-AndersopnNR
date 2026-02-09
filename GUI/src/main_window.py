"""CompLaB Studio 2.0 - Main Window."""

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QMenuBar,
    QMenu, QToolBar, QStatusBar, QLabel, QMessageBox,
    QFileDialog, QApplication,
)
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtCore import Qt, QTimer

from .config import Config
from .core.project import CompLaBProject
from .core.project_manager import ProjectManager
from .core.templates import ProjectTemplates
from .core.simulation_runner import SimulationRunner
from .panels.simulation_mode_panel import SimulationModePanel
from .panels.domain_panel import DomainPanel
from .panels.chemistry_panel import ChemistryPanel
from .panels.equilibrium_panel import EquilibriumPanel
from .panels.microbiology_panel import MicrobiologyPanel
from .panels.boundary_panel import BoundaryPanel
from .panels.solver_panel import SolverPanel
from .panels.monitoring_panel import MonitoringPanel
from .panels.postprocess_panel import PostProcessPanel
from .widgets.console_widget import ConsoleWidget
from .widgets.vtk_viewer import VTKViewerWidget
from .dialogs.new_project_dialog import NewProjectDialog
from .dialogs.kinetics_editor_dialog import KineticsEditorDialog
from .dialogs.preferences_dialog import PreferencesDialog
from .dialogs.about_dialog import AboutDialog


# Navigation tree item keys mapped to panel indices
PANEL_KEYS = [
    "general",
    "domain",
    "chemistry",
    "equilibrium",
    "microbiology",
    "boundaries",
    "solver",
    "run",
    "postprocess",
    "viewer",
]


class CompLaBMainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._config = Config()
        self._project = None
        self._runner = SimulationRunner(self)
        self._unsaved = False

        self.setWindowTitle("CompLaB Studio 2.0")
        self.resize(1280, 820)

        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()
        self._setup_autosave()

    # ── UI Setup ─────────────────────────────────────────────────

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Main splitter: nav | content | (optional right)
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: navigation tree
        self._nav_tree = QTreeWidget()
        self._nav_tree.setHeaderHidden(True)
        self._nav_tree.setMinimumWidth(180)
        self._nav_tree.setMaximumWidth(280)
        self._build_nav_tree()
        self._nav_tree.currentItemChanged.connect(self._on_nav_changed)

        # Center: content stack + console
        center_splitter = QSplitter(Qt.Orientation.Vertical)

        self._panel_stack = QStackedWidget()
        self._panels = {}
        self._create_panels()

        self._console = ConsoleWidget()
        self._console.setMinimumHeight(100)

        center_splitter.addWidget(self._panel_stack)
        center_splitter.addWidget(self._console)
        center_splitter.setStretchFactor(0, 4)
        center_splitter.setStretchFactor(1, 1)

        self._main_splitter.addWidget(self._nav_tree)
        self._main_splitter.addWidget(center_splitter)
        self._main_splitter.setStretchFactor(0, 0)
        self._main_splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self._main_splitter)

    def _build_nav_tree(self):
        self._nav_tree.clear()

        items = [
            ("General", "general", None),
            ("Domain", "domain", None),
            ("Chemistry", "chemistry", None),
            ("Equilibrium", "equilibrium", None),
            ("Microbiology", "microbiology", None),
            ("Boundary Conditions", "boundaries", None),
            ("Solver", "solver", None),
            ("Run", "run", None),
            ("Post-Processing", "postprocess", None),
            ("3D Viewer", "viewer", None),
        ]

        for label, key, parent_key in items:
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, key)
            self._nav_tree.addTopLevelItem(item)

        self._nav_tree.expandAll()
        if self._nav_tree.topLevelItemCount() > 0:
            self._nav_tree.setCurrentItem(self._nav_tree.topLevelItem(0))

    def _create_panels(self):
        self._general_panel = SimulationModePanel()
        self._domain_panel = DomainPanel()
        self._chemistry_panel = ChemistryPanel()
        self._equilibrium_panel = EquilibriumPanel()
        self._microbiology_panel = MicrobiologyPanel()
        self._boundary_panel = BoundaryPanel()
        self._solver_panel = SolverPanel()
        self._monitoring_panel = MonitoringPanel()
        self._postprocess_panel = PostProcessPanel()
        self._vtk_viewer = VTKViewerWidget()

        panel_map = {
            "general": self._general_panel,
            "domain": self._domain_panel,
            "chemistry": self._chemistry_panel,
            "equilibrium": self._equilibrium_panel,
            "microbiology": self._microbiology_panel,
            "boundaries": self._boundary_panel,
            "solver": self._solver_panel,
            "run": self._monitoring_panel,
            "postprocess": self._postprocess_panel,
            "viewer": self._vtk_viewer,
        }

        for key, panel in panel_map.items():
            idx = self._panel_stack.addWidget(panel)
            self._panels[key] = idx

        # Connect data_changed for panels that have it
        for panel in [self._general_panel, self._domain_panel,
                      self._chemistry_panel, self._equilibrium_panel,
                      self._microbiology_panel, self._boundary_panel,
                      self._solver_panel]:
            panel.data_changed.connect(self._on_data_changed)

    def _setup_menus(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")

        new_act = QAction("New Project", self)
        new_act.setShortcut(QKeySequence("Ctrl+N"))
        new_act.triggered.connect(self._new_project)
        file_menu.addAction(new_act)

        open_act = QAction("Open Project", self)
        open_act.setShortcut(QKeySequence("Ctrl+O"))
        open_act.triggered.connect(self._open_project)
        file_menu.addAction(open_act)

        import_act = QAction("Import XML", self)
        import_act.triggered.connect(self._import_xml)
        file_menu.addAction(import_act)

        file_menu.addSeparator()

        save_act = QAction("Save", self)
        save_act.setShortcut(QKeySequence("Ctrl+S"))
        save_act.triggered.connect(self._save_project)
        file_menu.addAction(save_act)

        save_as_act = QAction("Save As", self)
        save_as_act.setShortcut(QKeySequence("Ctrl+Shift+S"))
        save_as_act.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_act)

        export_act = QAction("Export XML", self)
        export_act.triggered.connect(self._export_xml)
        file_menu.addAction(export_act)

        file_menu.addSeparator()

        # Recent projects
        self._recent_menu = file_menu.addMenu("Recent Projects")
        self._update_recent_menu()

        file_menu.addSeparator()

        quit_act = QAction("Quit", self)
        quit_act.setShortcut(QKeySequence("Ctrl+Q"))
        quit_act.triggered.connect(self.close)
        file_menu.addAction(quit_act)

        # Edit
        edit_menu = menubar.addMenu("Edit")
        prefs_act = QAction("Preferences", self)
        prefs_act.triggered.connect(self._show_preferences)
        edit_menu.addAction(prefs_act)

        # Tools
        tools_menu = menubar.addMenu("Tools")
        kinetics_act = QAction("Kinetics Editor", self)
        kinetics_act.triggered.connect(self._show_kinetics_editor)
        tools_menu.addAction(kinetics_act)

        validate_act = QAction("Validate Configuration", self)
        validate_act.triggered.connect(self._validate_project)
        tools_menu.addAction(validate_act)

        # Simulation
        sim_menu = menubar.addMenu("Simulation")
        self._run_act = QAction("Run", self)
        self._run_act.setShortcut(QKeySequence("F5"))
        self._run_act.triggered.connect(self._run_simulation)
        sim_menu.addAction(self._run_act)

        self._stop_act = QAction("Stop", self)
        self._stop_act.setEnabled(False)
        self._stop_act.triggered.connect(self._stop_simulation)
        sim_menu.addAction(self._stop_act)

        # Help
        help_menu = menubar.addMenu("Help")
        about_act = QAction("About", self)
        about_act.triggered.connect(self._show_about)
        help_menu.addAction(about_act)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)

        new_btn = QAction("New", self)
        new_btn.triggered.connect(self._new_project)
        toolbar.addAction(new_btn)

        open_btn = QAction("Open", self)
        open_btn.triggered.connect(self._open_project)
        toolbar.addAction(open_btn)

        save_btn = QAction("Save", self)
        save_btn.triggered.connect(self._save_project)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        run_btn = QAction("Run", self)
        run_btn.triggered.connect(self._run_simulation)
        toolbar.addAction(run_btn)

        stop_btn = QAction("Stop", self)
        stop_btn.triggered.connect(self._stop_simulation)
        toolbar.addAction(stop_btn)

        validate_btn = QAction("Validate", self)
        validate_btn.triggered.connect(self._validate_project)
        toolbar.addAction(validate_btn)

        self.addToolBar(toolbar)

    def _setup_statusbar(self):
        self._statusbar = QStatusBar()
        self.setStatusBar(self._statusbar)

        self._project_status = QLabel("No project loaded")
        self._sim_status = QLabel("Idle")
        self._statusbar.addWidget(self._project_status, 1)
        self._statusbar.addPermanentWidget(self._sim_status)

    def _connect_signals(self):
        # Monitoring panel buttons
        self._monitoring_panel.run_button.clicked.connect(self._run_simulation)
        self._monitoring_panel.stop_button.clicked.connect(self._stop_simulation)
        self._monitoring_panel.validate_button.clicked.connect(self._validate_project)

        # Simulation runner
        self._runner.output_received.connect(self._console.append_output)
        self._runner.progress_updated.connect(self._monitoring_panel.on_progress)
        self._runner.status_changed.connect(self._on_sim_status_changed)
        self._runner.finished_signal.connect(self._on_sim_finished)

    def _setup_autosave(self):
        self._autosave_timer = QTimer(self)
        self._autosave_timer.timeout.connect(self._auto_save)
        if self._config.get("auto_save", False):
            interval = self._config.get("auto_save_interval", 300) * 1000
            self._autosave_timer.start(interval)

    # ── Navigation ───────────────────────────────────────────────

    def _on_nav_changed(self, current, previous):
        if current is None:
            return
        key = current.data(0, Qt.ItemDataRole.UserRole)
        if key and key in self._panels:
            self._panel_stack.setCurrentIndex(self._panels[key])

    # ── Project Management ───────────────────────────────────────

    def _new_project(self):
        if not self._check_save():
            return
        dlg = NewProjectDialog(
            self._config.get("default_project_dir", ""), self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        result = dlg.get_result()
        template = result.get("template")
        if template:
            proj = ProjectTemplates.apply_template(template)
        else:
            proj = CompLaBProject()

        proj.name = result["name"]
        proj.description = result.get("description", "")
        proj_dir = Path(result["directory"]) / result["name"]
        proj_dir.mkdir(parents=True, exist_ok=True)
        (proj_dir / "input").mkdir(exist_ok=True)
        (proj_dir / "output").mkdir(exist_ok=True)
        proj.project_dir = str(proj_dir)

        import datetime
        proj.created = datetime.datetime.now().isoformat(timespec="seconds")
        proj.modified = proj.created

        self._set_project(proj)
        self._save_project()
        self._console.append(f"Created project: {proj.name}", "success")

    def _open_project(self):
        if not self._check_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Project", "",
            "CompLaB Projects (*.complab);;All Files (*)")
        if not path:
            return
        try:
            proj = ProjectManager.load_project(path)
            self._set_project(proj)
            self._config.add_recent_project(path)
            self._update_recent_menu()
            self._console.append(f"Opened project: {proj.name}", "success")
        except Exception as e:
            QMessageBox.critical(self, "Open Error", str(e))

    def _import_xml(self):
        if not self._check_save():
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CompLaB XML", "",
            "XML Files (*.xml);;All Files (*)")
        if not path:
            return
        try:
            proj = ProjectManager.import_from_xml(path)
            self._set_project(proj)
            self._console.append(f"Imported from: {path}", "success")
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def _save_project(self):
        if not self._project:
            return
        self._collect_all_data()
        try:
            filepath = ProjectManager.save_project(self._project)
            self._unsaved = False
            self._update_title()
            self._config.add_recent_project(filepath)
            self._update_recent_menu()
            self._console.append(f"Project saved: {filepath}", "success")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", str(e))

    def _save_project_as(self):
        if not self._project:
            return
        d = QFileDialog.getExistingDirectory(
            self, "Save Project As", self._project.project_dir or "")
        if not d:
            return
        self._project.project_dir = d
        self._save_project()

    def _export_xml(self):
        if not self._project:
            return
        self._collect_all_data()
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CompLaB XML", "CompLaB.xml",
            "XML Files (*.xml);;All Files (*)")
        if path:
            try:
                ProjectManager.export_to_xml(self._project, path)
                self._console.append(f"XML exported: {path}", "success")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _set_project(self, project):
        self._project = project
        self._unsaved = False
        self._update_title()
        self._project_status.setText(f"Project: {project.name}")

        # Push project to all panels
        for panel in [self._general_panel, self._domain_panel,
                      self._chemistry_panel, self._equilibrium_panel,
                      self._microbiology_panel, self._boundary_panel,
                      self._solver_panel, self._monitoring_panel,
                      self._postprocess_panel]:
            panel.set_project(project)

    def _collect_all_data(self):
        """Collect data from all panels into the project."""
        if not self._project:
            return
        for panel in [self._general_panel, self._domain_panel,
                      self._chemistry_panel, self._equilibrium_panel,
                      self._microbiology_panel, self._boundary_panel,
                      self._solver_panel]:
            panel.collect_data(self._project)

    def _on_data_changed(self):
        self._unsaved = True
        self._update_title()

    def _update_title(self):
        title = "CompLaB Studio 2.0"
        if self._project:
            title = f"{self._project.name} - {title}"
            if self._unsaved:
                title = f"* {title}"
        self.setWindowTitle(title)

    def _check_save(self):
        if self._unsaved and self._project:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "Save changes before proceeding?",
                QMessageBox.StandardButton.Save |
                QMessageBox.StandardButton.Discard |
                QMessageBox.StandardButton.Cancel)
            if reply == QMessageBox.StandardButton.Save:
                self._save_project()
                return True
            elif reply == QMessageBox.StandardButton.Cancel:
                return False
        return True

    def _update_recent_menu(self):
        self._recent_menu.clear()
        recents = self._config.get("recent_projects", [])
        for path in recents:
            act = QAction(path, self)
            act.triggered.connect(lambda checked, p=path: self._open_recent(p))
            self._recent_menu.addAction(act)
        if not recents:
            act = QAction("(none)", self)
            act.setEnabled(False)
            self._recent_menu.addAction(act)

    def _open_recent(self, path):
        if not Path(path).exists():
            QMessageBox.warning(self, "Not Found", f"File not found: {path}")
            return
        try:
            proj = ProjectManager.load_project(path)
            self._set_project(proj)
            self._console.append(f"Opened: {proj.name}", "success")
        except Exception as e:
            QMessageBox.critical(self, "Open Error", str(e))

    # ── Simulation ───────────────────────────────────────────────

    def _run_simulation(self):
        if not self._project:
            QMessageBox.warning(self, "No Project", "Create or open a project first.")
            return

        self._collect_all_data()
        self._save_project()

        exe = self._config.get("complab_executable", "")
        if not exe:
            exe = SimulationRunner.find_executable()
        if not exe:
            QMessageBox.warning(
                self, "No Executable",
                "CompLaB executable not found.\n"
                "Set the path in Edit > Preferences.")
            return

        self._runner.configure(exe, self._project.project_dir)
        self._monitoring_panel.on_simulation_started()
        self._run_act.setEnabled(False)
        self._stop_act.setEnabled(True)
        self._sim_status.setText("Running")
        self._runner.start()

        # Switch to Run panel
        for i in range(self._nav_tree.topLevelItemCount()):
            item = self._nav_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == "run":
                self._nav_tree.setCurrentItem(item)
                break

    def _stop_simulation(self):
        self._runner.request_stop()

    def _on_sim_status_changed(self, status):
        self._sim_status.setText(status)

    def _on_sim_finished(self, success, message):
        self._monitoring_panel.on_simulation_finished(success, message)
        self._run_act.setEnabled(True)
        self._stop_act.setEnabled(False)
        self._sim_status.setText("Completed" if success else "Failed")

    def _validate_project(self):
        if not self._project:
            QMessageBox.warning(self, "No Project", "Create or open a project first.")
            return
        self._collect_all_data()
        issues = self._project.validate()
        self._monitoring_panel.set_validation_results(issues)

        if not issues:
            self._console.append("Validation passed: no issues found.", "success")
        else:
            for level, msg in issues:
                if level == "error":
                    self._console.append(f"[ERROR] {msg}", "error")
                else:
                    self._console.append(f"[WARNING] {msg}", "warning")

        # Switch to Run panel to show results
        for i in range(self._nav_tree.topLevelItemCount()):
            item = self._nav_tree.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == "run":
                self._nav_tree.setCurrentItem(item)
                break

    # ── Dialogs ──────────────────────────────────────────────────

    def _show_preferences(self):
        dlg = PreferencesDialog(self._config, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            # Restart autosave if settings changed
            self._setup_autosave()

    def _show_kinetics_editor(self):
        proj_dir = self._project.project_dir if self._project else ""
        dlg = KineticsEditorDialog(proj_dir, self)
        dlg.exec()

    def _show_about(self):
        dlg = AboutDialog(self)
        dlg.exec()

    # ── Autosave ─────────────────────────────────────────────────

    def _auto_save(self):
        if self._unsaved and self._project:
            self._collect_all_data()
            try:
                ProjectManager.save_project(self._project)
                self._unsaved = False
                self._update_title()
            except Exception:
                pass  # Silent autosave failure

    # ── Close ────────────────────────────────────────────────────

    def closeEvent(self, event):
        if not self._check_save():
            event.ignore()
            return
        if self._runner.isRunning():
            reply = QMessageBox.question(
                self, "Simulation Running",
                "A simulation is running. Stop it and quit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
            self._runner.request_stop()
            self._runner.wait(5000)
        event.accept()
