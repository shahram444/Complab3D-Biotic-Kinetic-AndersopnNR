"""
CompLaB Studio Main Window
Professional interface for reactive transport simulations
"""

import os
import json
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTreeWidget, QTreeWidgetItem, QStackedWidget, QToolBar,
    QStatusBar, QMenuBar, QMenu, QFileDialog, QMessageBox,
    QDockWidget, QTextEdit, QProgressBar, QLabel, QFrame,
    QTabWidget, QToolButton, QSizePolicy, QApplication
)
from PySide6.QtCore import Qt, QSize, Signal, QTimer, QThread
from PySide6.QtGui import QAction, QIcon, QFont, QColor, QPalette, QPixmap

from .panels.project_panel import ProjectPanel
from .panels.domain_panel import DomainPanel
from .panels.chemistry_panel import ChemistryPanel
from .panels.microbiology_panel import MicrobiologyPanel
from .panels.solver_panel import SolverPanel
from .panels.mesh_panel import MeshPanel
from .panels.boundary_panel import BoundaryConditionsPanel
from .panels.monitoring_panel import MonitoringPanel
from .panels.postprocess_panel import PostProcessPanel
from .dialogs.new_project_dialog import NewProjectDialog
from .dialogs.preferences_dialog import PreferencesDialog
from .dialogs.about_dialog import AboutDialog
from .widgets.console_widget import ConsoleWidget
from .widgets.vtk_viewer import VTKViewerWidget
from .core.project_manager import ProjectManager
from .core.simulation_runner import SimulationRunner
from .config import Config


class CompLaBMainWindow(QMainWindow):
    """Main application window for CompLaB Studio"""
    
    simulation_started = Signal()
    simulation_finished = Signal(int)
    simulation_progress = Signal(int, str)
    
    def __init__(self):
        super().__init__()
        
        self.config = Config()
        self.project_manager = ProjectManager()
        self.simulation_runner = None
        self.current_project = None
        
        self._setup_ui()
        self._create_menus()
        self._create_toolbars()
        self._create_dock_widgets()
        self._create_status_bar()
        self._connect_signals()
        self._load_recent_projects()
        
        # Set window properties
        self.setWindowTitle("CompLaB Studio - Reactive Transport Simulation")
        self.setMinimumSize(1400, 900)
        self.resize(1600, 1000)
        
        # Center on screen
        self._center_on_screen()
        
    def _center_on_screen(self):
        """Center the window on the primary screen"""
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )
    
    def _setup_ui(self):
        """Setup the main user interface"""
        # Central widget with main splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Main horizontal splitter
        self.main_splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(self.main_splitter)
        
        # Left panel - Project tree and navigation
        self.left_panel = self._create_left_panel()
        self.main_splitter.addWidget(self.left_panel)
        
        # Center - Main content area with vertical splitter
        self.center_splitter = QSplitter(Qt.Vertical)
        self.main_splitter.addWidget(self.center_splitter)
        
        # Top center - Configuration panels / 3D viewer
        self.content_tabs = QTabWidget()
        self.content_tabs.setTabPosition(QTabWidget.North)
        self.content_tabs.setMovable(True)
        self.content_tabs.setDocumentMode(True)
        
        # Create all panels
        self._create_panels()
        
        self.center_splitter.addWidget(self.content_tabs)
        
        # Bottom center - Console output
        self.console = ConsoleWidget()
        self.center_splitter.addWidget(self.console)
        
        # Right panel - Properties and monitoring
        self.right_panel = self._create_right_panel()
        self.main_splitter.addWidget(self.right_panel)
        
        # Set splitter sizes
        self.main_splitter.setSizes([280, 900, 320])
        self.center_splitter.setSizes([700, 200])
        
    def _create_left_panel(self):
        """Create the left navigation panel"""
        panel = QFrame()
        panel.setObjectName("leftPanel")
        panel.setMaximumWidth(350)
        panel.setMinimumWidth(200)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Panel header
        header = QLabel("  📁 Project Navigator")
        header.setObjectName("panelHeader")
        header.setFixedHeight(40)
        layout.addWidget(header)
        
        # Project tree
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderHidden(True)
        self.project_tree.setObjectName("projectTree")
        self.project_tree.setAnimated(True)
        self.project_tree.setIndentation(20)
        self.project_tree.itemClicked.connect(self._on_tree_item_clicked)
        self.project_tree.itemDoubleClicked.connect(self._on_tree_item_double_clicked)
        
        layout.addWidget(self.project_tree)
        
        return panel
    
    def _create_right_panel(self):
        """Create the right properties panel"""
        panel = QFrame()
        panel.setObjectName("rightPanel")
        panel.setMaximumWidth(400)
        panel.setMinimumWidth(250)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Properties tabs
        self.properties_tabs = QTabWidget()
        self.properties_tabs.setObjectName("propertiesTabs")
        
        # Monitoring panel
        self.monitoring_panel = MonitoringPanel()
        self.properties_tabs.addTab(self.monitoring_panel, "📊 Monitor")
        
        # Quick properties
        self.quick_props = QTextEdit()
        self.quick_props.setReadOnly(True)
        self.quick_props.setPlaceholderText("Select an item to view properties...")
        self.properties_tabs.addTab(self.quick_props, "📋 Properties")
        
        layout.addWidget(self.properties_tabs)
        
        return panel
    
    def _create_panels(self):
        """Create all configuration panels"""
        # Project overview panel
        self.project_panel = ProjectPanel()
        self.content_tabs.addTab(self.project_panel, "🏠 Project")
        
        # Domain/Geometry panel
        self.domain_panel = DomainPanel()
        self.content_tabs.addTab(self.domain_panel, "📐 Domain")
        
        # Mesh/Geometry panel
        self.mesh_panel = MeshPanel()
        self.content_tabs.addTab(self.mesh_panel, "🔲 Geometry")
        
        # Chemistry panel
        self.chemistry_panel = ChemistryPanel()
        self.content_tabs.addTab(self.chemistry_panel, "⚗️ Chemistry")
        
        # Microbiology panel
        self.microbiology_panel = MicrobiologyPanel()
        self.content_tabs.addTab(self.microbiology_panel, "🦠 Microbiology")
        
        # Boundary conditions panel
        self.boundary_panel = BoundaryConditionsPanel()
        self.content_tabs.addTab(self.boundary_panel, "🔲 Boundaries")
        
        # Solver settings panel
        self.solver_panel = SolverPanel()
        self.content_tabs.addTab(self.solver_panel, "⚙️ Solver")
        
        # 3D Viewer panel
        self.vtk_viewer = VTKViewerWidget()
        self.content_tabs.addTab(self.vtk_viewer, "🎨 3D View")
        
        # Post-processing panel
        self.postprocess_panel = PostProcessPanel()
        self.content_tabs.addTab(self.postprocess_panel, "📈 Results")
        
    def _create_menus(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        menubar.setObjectName("mainMenuBar")
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        new_action = QAction("&New Project...", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("&Open Project...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_project)
        file_menu.addAction(open_action)
        
        # Recent projects submenu
        self.recent_menu = file_menu.addMenu("Recent Projects")
        
        file_menu.addSeparator()
        
        save_action = QAction("&Save Project", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save Project &As...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        import_menu = file_menu.addMenu("Import")
        import_geom_action = QAction("Geometry (BMP/DAT)...", self)
        import_geom_action.triggered.connect(self._import_geometry)
        import_menu.addAction(import_geom_action)
        
        import_xml_action = QAction("CompLaB XML...", self)
        import_xml_action.triggered.connect(self._import_xml)
        import_menu.addAction(import_xml_action)
        
        export_menu = file_menu.addMenu("Export")
        export_xml_action = QAction("CompLaB XML...", self)
        export_xml_action.triggered.connect(self._export_xml)
        export_menu.addAction(export_xml_action)
        
        export_vtk_action = QAction("VTK Files...", self)
        export_vtk_action.triggered.connect(self._export_vtk)
        export_menu.addAction(export_vtk_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit menu
        edit_menu = menubar.addMenu("&Edit")
        
        prefs_action = QAction("&Preferences...", self)
        prefs_action.setShortcut("Ctrl+,")
        prefs_action.triggered.connect(self._show_preferences)
        edit_menu.addAction(prefs_action)
        
        # Simulation menu
        sim_menu = menubar.addMenu("&Simulation")
        
        self.run_action = QAction("▶ &Run Simulation", self)
        self.run_action.setShortcut("F5")
        self.run_action.triggered.connect(self._run_simulation)
        sim_menu.addAction(self.run_action)
        
        self.stop_action = QAction("⏹ &Stop Simulation", self)
        self.stop_action.setShortcut("Shift+F5")
        self.stop_action.triggered.connect(self._stop_simulation)
        self.stop_action.setEnabled(False)
        sim_menu.addAction(self.stop_action)
        
        sim_menu.addSeparator()
        
        validate_action = QAction("✓ &Validate Setup...", self)
        validate_action.setShortcut("F6")
        validate_action.triggered.connect(self._validate_setup)
        sim_menu.addAction(validate_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("&Tools")
        
        geom_creator_action = QAction("Geometry Creator...", self)
        geom_creator_action.triggered.connect(self._show_geometry_creator)
        tools_menu.addAction(geom_creator_action)
        
        kinetics_editor_action = QAction("Kinetics Editor...", self)
        kinetics_editor_action.triggered.connect(self._show_kinetics_editor)
        tools_menu.addAction(kinetics_editor_action)
        
        tools_menu.addSeparator()
        
        paraview_action = QAction("Open in ParaView...", self)
        paraview_action.triggered.connect(self._open_paraview)
        tools_menu.addAction(paraview_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        toggle_console_action = QAction("Toggle Console", self)
        toggle_console_action.setShortcut("Ctrl+`")
        toggle_console_action.triggered.connect(self._toggle_console)
        view_menu.addAction(toggle_console_action)
        
        toggle_tree_action = QAction("Toggle Project Tree", self)
        toggle_tree_action.setShortcut("Ctrl+1")
        toggle_tree_action.triggered.connect(self._toggle_project_tree)
        view_menu.addAction(toggle_tree_action)
        
        toggle_props_action = QAction("Toggle Properties", self)
        toggle_props_action.setShortcut("Ctrl+2")
        toggle_props_action.triggered.connect(self._toggle_properties)
        view_menu.addAction(toggle_props_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        # Quick Start Tutorial (local .txt file)
        tutorial_action = QAction("Quick Start Tutorial", self)
        tutorial_action.setShortcut("F1")
        tutorial_action.triggered.connect(self._show_tutorial)
        help_menu.addAction(tutorial_action)
        
        # User Guide (local .docx file)
        user_guide_action = QAction("User Guide (Word)", self)
        user_guide_action.triggered.connect(self._show_user_guide)
        help_menu.addAction(user_guide_action)
        
        help_menu.addSeparator()
        
        # Online Resources
        online_action = QAction("Online Documentation", self)
        online_action.triggered.connect(self._show_online_docs)
        help_menu.addAction(online_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About CompLaB Studio", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
    def _create_toolbars(self):
        """Create the main toolbar"""
        # Main toolbar
        main_toolbar = QToolBar("Main Toolbar")
        main_toolbar.setObjectName("mainToolbar")
        main_toolbar.setMovable(False)
        main_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(main_toolbar)
        
        # New project button
        new_btn = QToolButton()
        new_btn.setText("📁 New")
        new_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        new_btn.clicked.connect(self._new_project)
        main_toolbar.addWidget(new_btn)
        
        # Open button
        open_btn = QToolButton()
        open_btn.setText("📂 Open")
        open_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        open_btn.clicked.connect(self._open_project)
        main_toolbar.addWidget(open_btn)
        
        # Save button
        save_btn = QToolButton()
        save_btn.setText("💾 Save")
        save_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        save_btn.clicked.connect(self._save_project)
        main_toolbar.addWidget(save_btn)
        
        main_toolbar.addSeparator()
        
        # Run button
        self.run_btn = QToolButton()
        self.run_btn.setText("▶ Run")
        self.run_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.run_btn.setObjectName("runButton")
        self.run_btn.clicked.connect(self._run_simulation)
        main_toolbar.addWidget(self.run_btn)
        
        # Stop button
        self.stop_btn = QToolButton()
        self.stop_btn.setText("⏹ Stop")
        self.stop_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_simulation)
        main_toolbar.addWidget(self.stop_btn)
        
        main_toolbar.addSeparator()
        
        # Validate button
        validate_btn = QToolButton()
        validate_btn.setText("✓ Validate")
        validate_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        validate_btn.clicked.connect(self._validate_setup)
        main_toolbar.addWidget(validate_btn)
        
        # 3D View button
        view3d_btn = QToolButton()
        view3d_btn.setText("🎨 3D View")
        view3d_btn.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        view3d_btn.clicked.connect(lambda: self.content_tabs.setCurrentWidget(self.vtk_viewer))
        main_toolbar.addWidget(view3d_btn)
        
        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        main_toolbar.addWidget(spacer)
        
        # Progress indicator
        self.progress_label = QLabel("")
        main_toolbar.addWidget(self.progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        main_toolbar.addWidget(self.progress_bar)
        
    def _create_dock_widgets(self):
        """Create dock widgets (can be detached/moved)"""
        pass  # Using splitter layout instead for cleaner look
        
    def _create_status_bar(self):
        """Create the status bar"""
        status_bar = QStatusBar()
        status_bar.setObjectName("mainStatusBar")
        self.setStatusBar(status_bar)
        
        # Project status
        self.project_status = QLabel("No project loaded")
        status_bar.addWidget(self.project_status)
        
        # Spacer
        spacer = QLabel()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        status_bar.addWidget(spacer)
        
        # Simulation status
        self.sim_status = QLabel("Ready")
        self.sim_status.setObjectName("simStatus")
        status_bar.addPermanentWidget(self.sim_status)
        
        # Memory usage
        self.memory_label = QLabel("Memory: --")
        status_bar.addPermanentWidget(self.memory_label)
        
    def _connect_signals(self):
        """Connect signals and slots"""
        self.simulation_started.connect(self._on_simulation_started)
        self.simulation_finished.connect(self._on_simulation_finished)
        self.simulation_progress.connect(self._on_simulation_progress)
        
    def _load_recent_projects(self):
        """Load recent projects list"""
        recent = self.config.get("recent_projects", [])
        self.recent_menu.clear()
        
        for project_path in recent[:10]:
            if os.path.exists(project_path):
                action = QAction(os.path.basename(project_path), self)
                action.setData(project_path)
                action.triggered.connect(lambda checked, p=project_path: self._open_project_path(p))
                self.recent_menu.addAction(action)
                
        if not recent:
            no_recent = QAction("No recent projects", self)
            no_recent.setEnabled(False)
            self.recent_menu.addAction(no_recent)
            
    def _update_project_tree(self):
        """Update the project tree with current project structure"""
        self.project_tree.clear()
        
        if not self.current_project:
            return
            
        # Root item
        root = QTreeWidgetItem(self.project_tree)
        root.setText(0, f"📁 {self.current_project.name}")
        root.setExpanded(True)
        root.setData(0, Qt.UserRole, "project")
        
        # Domain section
        domain_item = QTreeWidgetItem(root)
        domain_item.setText(0, "📐 Domain")
        domain_item.setData(0, Qt.UserRole, "domain")
        
        geom_item = QTreeWidgetItem(domain_item)
        geom_item.setText(0, "🔲 Geometry")
        geom_item.setData(0, Qt.UserRole, "geometry")
        
        # Chemistry section
        chem_item = QTreeWidgetItem(root)
        chem_item.setText(0, "⚗️ Chemistry")
        chem_item.setData(0, Qt.UserRole, "chemistry")
        
        for i, substrate in enumerate(self.current_project.substrates):
            sub_item = QTreeWidgetItem(chem_item)
            sub_item.setText(0, f"  {substrate.name}")
            sub_item.setData(0, Qt.UserRole, f"substrate_{i}")
            
        # Microbiology section
        bio_item = QTreeWidgetItem(root)
        bio_item.setText(0, "🦠 Microbiology")
        bio_item.setData(0, Qt.UserRole, "microbiology")
        
        for i, microbe in enumerate(self.current_project.microbes):
            mic_item = QTreeWidgetItem(bio_item)
            mic_item.setText(0, f"  {microbe.name}")
            mic_item.setData(0, Qt.UserRole, f"microbe_{i}")
            
        # Boundary Conditions
        bc_item = QTreeWidgetItem(root)
        bc_item.setText(0, "🔲 Boundary Conditions")
        bc_item.setData(0, Qt.UserRole, "boundaries")
        
        # Solver settings
        solver_item = QTreeWidgetItem(root)
        solver_item.setText(0, "⚙️ Solver Settings")
        solver_item.setData(0, Qt.UserRole, "solver")
        
        # Results (if any)
        if self.current_project.has_results():
            results_item = QTreeWidgetItem(root)
            results_item.setText(0, "📈 Results")
            results_item.setData(0, Qt.UserRole, "results")
            
        self.project_tree.expandAll()
        
    def _on_tree_item_clicked(self, item, column):
        """Handle tree item click"""
        item_type = item.data(0, Qt.UserRole)
        
        panel_map = {
            "project": self.project_panel,
            "domain": self.domain_panel,
            "geometry": self.mesh_panel,
            "chemistry": self.chemistry_panel,
            "microbiology": self.microbiology_panel,
            "boundaries": self.boundary_panel,
            "solver": self.solver_panel,
            "results": self.postprocess_panel,
        }
        
        if item_type in panel_map:
            self.content_tabs.setCurrentWidget(panel_map[item_type])
            
    def _on_tree_item_double_clicked(self, item, column):
        """Handle tree item double click"""
        # Same as single click for now
        self._on_tree_item_clicked(item, column)
        
    # ============== File Operations ==============
    
    def _new_project(self):
        """Create a new project"""
        dialog = NewProjectDialog(self)
        if dialog.exec():
            project_data = dialog.get_project_data()
            self.current_project = self.project_manager.create_project(project_data)
            self._update_project_tree()
            self._update_all_panels()
            self.project_status.setText(f"Project: {self.current_project.name}")
            self.console.log(f"Created new project: {self.current_project.name}")
            
    def _open_project(self):
        """Open an existing project"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Project",
            self.config.get("last_project_dir", ""),
            "CompLaB Projects (*.complab);;All Files (*)"
        )
        if file_path:
            self._open_project_path(file_path)
            
    def _open_project_path(self, path):
        """Open a project from path"""
        try:
            self.current_project = self.project_manager.load_project(path)
            self._update_project_tree()
            self._update_all_panels()
            self.project_status.setText(f"Project: {self.current_project.name}")
            self.console.log(f"Opened project: {path}")
            
            # Update recent projects
            recent = self.config.get("recent_projects", [])
            if path in recent:
                recent.remove(path)
            recent.insert(0, path)
            self.config.set("recent_projects", recent[:10])
            self._load_recent_projects()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open project:\n{str(e)}")
            
    def _save_project(self):
        """Save current project"""
        if not self.current_project:
            QMessageBox.warning(self, "Warning", "No project to save")
            return
            
        if not self.current_project.path:
            self._save_project_as()
            return
            
        try:
            self._collect_panel_data()
            self.project_manager.save_project(self.current_project)
            self.console.log(f"Project saved: {self.current_project.path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save project:\n{str(e)}")
            
    def _save_project_as(self):
        """Save project with new name"""
        if not self.current_project:
            QMessageBox.warning(self, "Warning", "No project to save")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Project As",
            self.config.get("last_project_dir", ""),
            "CompLaB Projects (*.complab)"
        )
        if file_path:
            if not file_path.endswith(".complab"):
                file_path += ".complab"
            self.current_project.path = file_path
            self._save_project()
            
    def _import_geometry(self):
        """Import geometry files"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Geometry",
            "",
            "DAT Files (*.dat);;BMP Files (*.bmp);;All Files (*)"
        )
        if file_path:
            self.mesh_panel.import_geometry(file_path)
            self.console.log(f"Imported geometry: {file_path}")
            
    def _import_xml(self):
        """Import CompLaB XML configuration"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import CompLaB XML",
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        if file_path:
            try:
                self.current_project = self.project_manager.import_from_xml(file_path)
                self._update_project_tree()
                self._update_all_panels()
                self.console.log(f"Imported XML: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to import XML:\n{str(e)}")
                
    def _export_xml(self):
        """Export to CompLaB XML format"""
        if not self.current_project:
            QMessageBox.warning(self, "Warning", "No project to export")
            return
            
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export CompLaB XML",
            "",
            "XML Files (*.xml)"
        )
        if file_path:
            try:
                self._collect_panel_data()
                self.project_manager.export_to_xml(self.current_project, file_path)
                self.console.log(f"Exported XML: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export XML:\n{str(e)}")
                
    def _export_vtk(self):
        """Export VTK files"""
        pass  # TODO: Implement
        
    # ============== Simulation Operations ==============
    
    def _run_simulation(self):
        """Start the simulation"""
        if not self.current_project:
            QMessageBox.warning(self, "Warning", "No project loaded")
            return
            
        # Validate first
        if not self._validate_setup(show_success=False):
            return
            
        # Collect all panel data
        self._collect_panel_data()
        
        # Export XML for CompLaB
        xml_path = self.current_project.get_xml_path()
        self.project_manager.export_to_xml(self.current_project, xml_path)
        
        # Start simulation
        self.simulation_runner = SimulationRunner(self.current_project)
        self.simulation_runner.started_signal.connect(self._on_simulation_started)
        self.simulation_runner.progress.connect(self._on_simulation_progress)
        self.simulation_runner.finished_signal.connect(self._on_simulation_finished)
        self.simulation_runner.output.connect(self.console.append_output)
        self.simulation_runner.output.connect(self.monitoring_panel.append_output)
        self.simulation_runner.error.connect(
            lambda msg: self.console.log(msg, "error")
        )
        self.simulation_runner.start()
        
    def _stop_simulation(self):
        """Stop the running simulation"""
        if self.simulation_runner:
            self.simulation_runner.stop()
            self.console.log("Simulation stop requested...")
            
    def _validate_setup(self, show_success=True):
        """Validate the simulation setup"""
        if not self.current_project:
            QMessageBox.warning(self, "Warning", "No project loaded")
            return False
            
        self._collect_panel_data()
        errors = self.current_project.validate()
        
        if errors:
            msg = "Validation errors:\n\n" + "\n".join(f"• {e}" for e in errors)
            QMessageBox.warning(self, "Validation Failed", msg)
            return False
        elif show_success:
            QMessageBox.information(self, "Validation Passed", 
                                   "All settings are valid. Ready to run simulation.")
        return True
        
    def _on_simulation_started(self):
        """Handle simulation start"""
        self.run_btn.setEnabled(False)
        self.run_action.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.stop_action.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.sim_status.setText("Running...")
        self.sim_status.setStyleSheet("color: #4CAF50;")
        
    def _on_simulation_finished(self, exit_code, summary=""):
        """Handle simulation completion"""
        self.run_btn.setEnabled(True)
        self.run_action.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.stop_action.setEnabled(False)
        self.progress_bar.setVisible(False)

        if exit_code == 0:
            self.sim_status.setText("Completed")
            self.sim_status.setStyleSheet("color: #4CAF50;")
            self.console.log(summary or "Simulation completed successfully!", "success")
            self._update_project_tree()  # Show results
        else:
            self.sim_status.setText("Failed")
            self.sim_status.setStyleSheet("color: #f44336;")
            self.console.log(summary or f"Simulation failed (exit code {exit_code})", "error")

        self.monitoring_panel.on_simulation_finished(exit_code)
            
    def _on_simulation_progress(self, iteration, message):
        """Handle simulation progress update"""
        self.progress_label.setText(message)
        self.monitoring_panel.update_progress(iteration, message)
        
    # ============== View Operations ==============
    
    def _toggle_console(self):
        """Toggle console visibility"""
        self.console.setVisible(not self.console.isVisible())
        
    def _toggle_project_tree(self):
        """Toggle project tree visibility"""
        self.left_panel.setVisible(not self.left_panel.isVisible())
        
    def _toggle_properties(self):
        """Toggle properties panel visibility"""
        self.right_panel.setVisible(not self.right_panel.isVisible())
        
    # ============== Tools ==============
    
    def _show_geometry_creator(self):
        """Show geometry creator dialog"""
        from .dialogs.geometry_creator_dialog import GeometryCreatorDialog
        dialog = GeometryCreatorDialog(self)
        dialog.exec()
        
    def _show_kinetics_editor(self):
        """Show kinetics editor dialog"""
        from .dialogs.kinetics_editor_dialog import KineticsEditorDialog
        dialog = KineticsEditorDialog(self)
        dialog.exec()
        
    def _open_paraview(self):
        """Open results in ParaView"""
        if not self.current_project:
            return
            
        paraview_path = self.config.get("paraview_path", "paraview")
        output_dir = self.current_project.get_output_dir()
        
        try:
            import subprocess
            subprocess.Popen([paraview_path, output_dir])
        except Exception as e:
            QMessageBox.warning(self, "Error", 
                              f"Failed to start ParaView:\n{str(e)}\n\n"
                              "Please set ParaView path in Preferences.")
            
    # ============== Help ==============
    
    def _show_preferences(self):
        """Show preferences dialog"""
        dialog = PreferencesDialog(self.config, self)
        if dialog.exec():
            self.config.save()
            
    def _show_tutorial(self):
        """Show quick start tutorial (local .txt file)"""
        import subprocess
        
        # Look for tutorial file
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        tutorial_path = os.path.join(base_path, "CompLaB_Tutorial.txt")
        
        if os.path.exists(tutorial_path):
            # Open with default text editor
            if os.name == 'nt':  # Windows
                os.startfile(tutorial_path)
            else:  # Linux/Mac
                subprocess.run(['xdg-open', tutorial_path])
        else:
            QMessageBox.warning(
                self, 
                "Tutorial Not Found",
                f"Tutorial file not found at:\n{tutorial_path}\n\n"
                f"Please ensure CompLaB_Tutorial.txt is in the gui/ folder."
            )
    
    def _show_user_guide(self):
        """Show user guide (local .docx file)"""
        import subprocess
        
        # Look for user guide in docs folder
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        docs_path = os.path.join(base_path, "docs")
        user_guide_path = os.path.join(docs_path, "CompLaB_Studio_User_Guide.docx")
        
        # Also check directly in gui folder
        alt_path = os.path.join(base_path, "CompLaB_Studio_User_Guide.docx")
        
        if os.path.exists(user_guide_path):
            path_to_open = user_guide_path
        elif os.path.exists(alt_path):
            path_to_open = alt_path
        else:
            QMessageBox.warning(
                self,
                "User Guide Not Found",
                f"User Guide not found at:\n{user_guide_path}\n\n"
                f"Please ensure CompLaB_Studio_User_Guide.docx is in the gui/docs/ folder."
            )
            return
        
        # Open with default application
        if os.name == 'nt':  # Windows
            os.startfile(path_to_open)
        else:  # Linux/Mac
            subprocess.run(['xdg-open', path_to_open])
    
    def _show_online_docs(self):
        """Show online documentation"""
        import webbrowser
        webbrowser.open("https://bitbucket.org/MeileLab/complab/wiki")
        
    def _show_about(self):
        """Show about dialog"""
        dialog = AboutDialog(self)
        dialog.exec()
        
    # ============== Helpers ==============
    
    def _update_all_panels(self):
        """Update all panels with current project data"""
        if not self.current_project:
            return
            
        self.project_panel.set_project(self.current_project)
        self.domain_panel.set_project(self.current_project)
        self.mesh_panel.set_project(self.current_project)
        self.chemistry_panel.set_project(self.current_project)
        self.microbiology_panel.set_project(self.current_project)
        self.boundary_panel.set_project(self.current_project)
        self.solver_panel.set_project(self.current_project)
        
    def _collect_panel_data(self):
        """Collect data from all panels into project"""
        if not self.current_project:
            return
            
        self.project_panel.collect_data(self.current_project)
        self.domain_panel.collect_data(self.current_project)
        self.mesh_panel.collect_data(self.current_project)
        self.chemistry_panel.collect_data(self.current_project)
        self.microbiology_panel.collect_data(self.current_project)
        self.boundary_panel.collect_data(self.current_project)
        self.solver_panel.collect_data(self.current_project)
        
    def closeEvent(self, event):
        """Handle window close"""
        if self.simulation_runner and self.simulation_runner.isRunning():
            reply = QMessageBox.question(
                self, "Simulation Running",
                "A simulation is still running. Are you sure you want to exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                event.ignore()
                return
            self.simulation_runner.stop()
            
        # Save window state
        self.config.set("window_geometry", self.saveGeometry().toHex().data().decode())
        self.config.set("window_state", self.saveState().toHex().data().decode())
        self.config.save()
        
        event.accept()
