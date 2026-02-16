"""Run panel - comprehensive simulation execution, monitoring, and MPI support.

Completely rebuilt to provide:
  - MPI configuration (number of processes, mpirun path)
  - Real-time console output from simulation
  - Progress tracking with iteration counter and ETA
  - Convergence residual monitoring
  - Elapsed time tracking
  - Detailed validation before run
  - Error analysis on failure
"""

import os
import re
import time
from collections import deque
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox, QFormLayout, QSpinBox,
    QLineEdit, QTextEdit, QCheckBox, QTabWidget,
    QWidget, QFileDialog, QMessageBox, QComboBox,
    QSizePolicy,
)
from PySide6.QtCore import Signal, QTimer, Qt
from PySide6.QtGui import QFont, QTextCursor, QColor

from .base_panel import BasePanel


class RunPanel(BasePanel):
    """Comprehensive run controls: MPI config, validate, start, stop, monitor."""

    run_requested = Signal()
    stop_requested = Signal()
    validate_requested = Signal()
    export_xml_requested = Signal()
    mpi_config_changed = Signal(int, str)  # nprocs, mpirun_path

    def __init__(self, parent=None):
        super().__init__("Run Simulation", parent)
        self._running = False
        self._start_time = 0.0
        self._max_iterations = 0
        self._current_iteration = 0
        self._ns_residual_history = deque(maxlen=200)
        self._ade_residual_history = deque(maxlen=200)
        self._iteration_history = deque(maxlen=200)

        self._timer = QTimer()
        self._timer.timeout.connect(self._update_elapsed)
        self._build_ui()

    # ── UI construction ─────────────────────────────────────────────

    def _build_ui(self):
        tabs = QTabWidget()

        # === Tab 1: Run Controls ===
        controls_tab = QWidget()
        controls_layout = QVBoxLayout(controls_tab)
        controls_layout.setSpacing(8)

        # -- Pre-Run Checks --
        checks_group = QGroupBox("Pre-Run Checks")
        checks_layout = QVBoxLayout()
        checks_layout.setSpacing(6)

        btn_row = QHBoxLayout()
        validate_btn = self.make_button("Validate Configuration")
        validate_btn.setToolTip("Check all settings for errors before running")
        validate_btn.clicked.connect(self.validate_requested.emit)
        btn_row.addWidget(validate_btn)

        export_btn = self.make_button("Export CompLaB.xml")
        export_btn.setToolTip("Export current settings to CompLaB.xml")
        export_btn.clicked.connect(self.export_xml_requested.emit)
        btn_row.addWidget(export_btn)
        btn_row.addStretch()
        checks_layout.addLayout(btn_row)

        self._validation_lbl = QLabel("")
        self._validation_lbl.setWordWrap(True)
        checks_layout.addWidget(self._validation_lbl)

        checks_group.setLayout(checks_layout)
        controls_layout.addWidget(checks_group)

        # -- MPI Configuration --
        mpi_group = QGroupBox("MPI / Parallel Execution")
        mpi_layout = QFormLayout()
        mpi_layout.setHorizontalSpacing(10)

        self._mpi_enabled = self.make_checkbox("Enable MPI parallel execution")
        self._mpi_enabled.setToolTip(
            "Run simulation with mpirun for parallel processing.\n"
            "Requires MPI (OpenMPI or MPICH) installed on your system.")
        self._mpi_enabled.toggled.connect(self._on_mpi_toggled)
        mpi_layout.addRow("", self._mpi_enabled)

        self._nprocs_spin = self.make_spin(value=1, min_val=1, max_val=256)
        self._nprocs_spin.setToolTip("Number of MPI processes")
        self._nprocs_spin.setEnabled(False)
        mpi_layout.addRow("Number of processes:", self._nprocs_spin)

        self._mpirun_edit = self.make_line_edit(
            text="mpirun", placeholder="Path to mpirun (e.g., mpirun, mpiexec)")
        self._mpirun_edit.setToolTip(
            "MPI launcher command. Common options:\n"
            "  mpirun  (OpenMPI)\n"
            "  mpiexec (MPICH / MS-MPI)\n"
            "Or provide full path: /usr/bin/mpirun")
        self._mpirun_edit.setEnabled(False)
        mpi_layout.addRow("MPI command:", self._mpirun_edit)

        mpi_browse_row = QHBoxLayout()
        self._mpi_browse_btn = self.make_button("Browse...")
        self._mpi_browse_btn.setEnabled(False)
        self._mpi_browse_btn.clicked.connect(self._browse_mpirun)
        mpi_browse_row.addWidget(self._mpi_browse_btn)

        self._mpi_detect_btn = self.make_button("Auto-detect")
        self._mpi_detect_btn.setEnabled(False)
        self._mpi_detect_btn.clicked.connect(self._detect_mpi)
        mpi_browse_row.addWidget(self._mpi_detect_btn)
        mpi_browse_row.addStretch()
        mpi_layout.addRow("", mpi_browse_row)

        self._mpi_status_lbl = self.make_info_label("")
        mpi_layout.addRow("", self._mpi_status_lbl)

        mpi_group.setLayout(mpi_layout)
        controls_layout.addWidget(mpi_group)

        # -- Execution --
        exec_group = QGroupBox("Execution")
        exec_layout = QVBoxLayout()

        run_row = QHBoxLayout()
        self._run_btn = self.make_button("Run Simulation", primary=True)
        self._run_btn.setToolTip("Start the simulation (F6)")
        self._run_btn.clicked.connect(self._on_run)
        run_row.addWidget(self._run_btn)

        self._stop_btn = self.make_button("Stop")
        self._stop_btn.setProperty("danger", True)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setToolTip("Stop the running simulation (Shift+F6)")
        self._stop_btn.clicked.connect(self._on_stop)
        run_row.addWidget(self._stop_btn)
        run_row.addStretch()
        exec_layout.addLayout(run_row)

        exec_group.setLayout(exec_layout)
        controls_layout.addWidget(exec_group)

        # -- Status --
        status_group = QGroupBox("Status")
        status_form = QFormLayout()
        status_form.setHorizontalSpacing(10)

        self._status = QLabel("Ready")
        self._status.setProperty("info", True)
        self._status.setStyleSheet("font-weight: bold; font-size: 12px;")
        status_form.addRow("Status:", self._status)

        self._elapsed = QLabel("0:00:00")
        status_form.addRow("Elapsed:", self._elapsed)

        self._eta_label = QLabel("-")
        status_form.addRow("ETA:", self._eta_label)

        self._iteration_label = QLabel("0 / 0")
        status_form.addRow("Iteration:", self._iteration_label)

        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setFormat("%p% (%v / %m)")
        status_form.addRow("Progress:", self._progress)

        status_group.setLayout(status_form)
        controls_layout.addWidget(status_group)

        # -- Convergence --
        conv_group = QGroupBox("Convergence Residuals")
        conv_form = QFormLayout()

        self._ns_residual_label = QLabel("-")
        conv_form.addRow("NS residual:", self._ns_residual_label)

        self._ade_residual_label = QLabel("-")
        conv_form.addRow("ADE residual:", self._ade_residual_label)

        self._phase_label = QLabel("-")
        conv_form.addRow("Current phase:", self._phase_label)

        conv_group.setLayout(conv_form)
        controls_layout.addWidget(conv_group)

        controls_layout.addStretch()
        tabs.addTab(controls_tab, "Controls")

        # === Tab 2: Simulation Output ===
        output_tab = QWidget()
        output_layout = QVBoxLayout(output_tab)

        output_header = QHBoxLayout()
        output_lbl = QLabel("Real-time Simulation Output")
        output_lbl.setStyleSheet("font-weight: bold;")
        output_header.addWidget(output_lbl)
        output_header.addStretch()

        self._auto_scroll_check = QCheckBox("Auto-scroll")
        self._auto_scroll_check.setChecked(True)
        output_header.addWidget(self._auto_scroll_check)

        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self._clear_output)
        output_header.addWidget(clear_btn)

        save_log_btn = QPushButton("Save Log")
        save_log_btn.clicked.connect(self._save_log)
        output_header.addWidget(save_log_btn)

        output_layout.addLayout(output_header)

        self._output_text = QTextEdit()
        self._output_text.setReadOnly(True)
        self._output_text.setFont(QFont("Consolas", 9))
        self._output_text.setStyleSheet(
            "QTextEdit {"
            "  background-color: #1e1e1e;"
            "  color: #cccccc;"
            "  border: 1px solid #3c3c3c;"
            "  selection-background-color: #264f78;"
            "}")
        self._output_text.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)
        output_layout.addWidget(self._output_text)

        # Error summary
        self._error_summary = QLabel("")
        self._error_summary.setWordWrap(True)
        self._error_summary.setVisible(False)
        output_layout.addWidget(self._error_summary)

        tabs.addTab(output_tab, "Output")

        # === Tab 3: Validation Details ===
        validation_tab = QWidget()
        validation_layout = QVBoxLayout(validation_tab)

        val_header = QLabel("Configuration Validation Report")
        val_header.setStyleSheet("font-weight: bold;")
        validation_layout.addWidget(val_header)

        val_info = self.make_info_label(
            "Click 'Validate Configuration' to check all settings.\n"
            "Validation checks domain, chemistry, microbiology, solver,\n"
            "I/O settings, file paths, and cross-references for consistency.")
        validation_layout.addWidget(val_info)

        self._validation_text = QTextEdit()
        self._validation_text.setReadOnly(True)
        self._validation_text.setFont(QFont("Consolas", 9))
        validation_layout.addWidget(self._validation_text)

        tabs.addTab(validation_tab, "Validation")

        self.add_widget(tabs)

    # ── MPI handlers ────────────────────────────────────────────────

    def _on_mpi_toggled(self, enabled):
        self._nprocs_spin.setEnabled(enabled)
        self._mpirun_edit.setEnabled(enabled)
        self._mpi_browse_btn.setEnabled(enabled)
        self._mpi_detect_btn.setEnabled(enabled)
        if enabled:
            self._detect_mpi()

    def _browse_mpirun(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select MPI launcher", "",
            "Executables (*);;All Files (*)")
        if path:
            self._mpirun_edit.setText(path)

    def _detect_mpi(self):
        """Auto-detect MPI installation."""
        import shutil
        mpi_commands = ["mpirun", "mpiexec", "srun"]
        for cmd in mpi_commands:
            path = shutil.which(cmd)
            if path:
                self._mpirun_edit.setText(path)
                self._mpi_status_lbl.setText(f"Found: {path}")
                self._mpi_status_lbl.setStyleSheet("color: #5ca060;")
                # Try to get version
                try:
                    import subprocess
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True, text=True, timeout=5)
                    first_line = result.stdout.strip().split('\n')[0]
                    self._mpi_status_lbl.setText(
                        f"Found: {path}\n{first_line}")
                except Exception:
                    pass
                return

        self._mpi_status_lbl.setText(
            "MPI not found on PATH. Install OpenMPI or MPICH,\n"
            "or specify the full path to mpirun/mpiexec.")
        self._mpi_status_lbl.setStyleSheet("color: #c75050;")

    def get_mpi_config(self):
        """Return (enabled, nprocs, mpirun_path)."""
        return (
            self._mpi_enabled.isChecked(),
            self._nprocs_spin.value(),
            self._mpirun_edit.text().strip(),
        )

    def set_mpi_config(self, enabled: bool, nprocs: int = 1, command: str = ""):
        """Set MPI config from an external source (e.g., Parallel panel)."""
        self._mpi_enabled.setChecked(enabled)
        if enabled:
            self._nprocs_spin.setValue(nprocs)
            if command:
                self._mpirun_edit.setText(command)

    # ── Run / Stop ──────────────────────────────────────────────────

    def _on_run(self):
        self._running = True
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status.setText("Starting...")
        self._status.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #5ca060;")
        self._start_time = time.time()
        self._current_iteration = 0
        self._max_iterations = 0
        self._ns_residual_history.clear()
        self._ade_residual_history.clear()
        self._iteration_history.clear()
        self._error_summary.setVisible(False)
        self._progress.setValue(0)
        self._eta_label.setText("-")
        self._phase_label.setText("Initializing...")
        self._ns_residual_label.setText("-")
        self._ade_residual_label.setText("-")
        self._iteration_label.setText("0 / 0")
        self._timer.start(1000)
        self.run_requested.emit()

    def _on_stop(self):
        self._stop_btn.setEnabled(False)
        self._status.setText("Stopping...")
        self._status.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #e0a040;")
        self.stop_requested.emit()

    # ── Timer update ────────────────────────────────────────────────

    def _update_elapsed(self):
        if not self._running:
            return
        elapsed = int(time.time() - self._start_time)
        hrs, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self._elapsed.setText(f"{hrs}:{mins:02d}:{secs:02d}")

        # Calculate ETA
        if self._current_iteration > 0 and self._max_iterations > 0:
            rate = elapsed / self._current_iteration
            remaining = (self._max_iterations - self._current_iteration) * rate
            if remaining > 0:
                rem_hrs, rem_rem = divmod(int(remaining), 3600)
                rem_mins, rem_secs = divmod(rem_rem, 60)
                self._eta_label.setText(f"{rem_hrs}:{rem_mins:02d}:{rem_secs:02d}")

    # ── Progress / output from simulation runner ────────────────────

    def on_progress(self, current: int, maximum: int):
        """Called by main window when runner emits progress."""
        self._current_iteration = current
        if maximum > self._max_iterations:
            self._max_iterations = maximum
        if self._max_iterations > 0:
            self._progress.setMaximum(self._max_iterations)
            self._progress.setValue(current)
        self._iteration_label.setText(f"{current:,} / {self._max_iterations:,}")

    def on_output_line(self, line: str):
        """Called for each line of simulation output - parse and display."""
        # Append to output text with color coding
        color = "#cccccc"
        line_lower = line.lower()

        if "error" in line_lower or "fail" in line_lower:
            color = "#f44336"
        elif "warning" in line_lower:
            color = "#ffc107"
        elif "converge" in line_lower or "complete" in line_lower:
            color = "#5ca060"
        elif line.startswith("---") or line.startswith("==="):
            color = "#569cd6"
        elif "iT =" in line or "iT=" in line:
            color = "#9cdcfe"

        self._output_text.append(
            f'<span style="color:{color};">{_escape_html(line)}</span>')

        if self._auto_scroll_check.isChecked():
            sb = self._output_text.verticalScrollBar()
            sb.setValue(sb.maximum())

        # Parse convergence data
        self._parse_output_line(line)

    def _parse_output_line(self, line: str):
        """Extract iteration, residual, and phase info from output."""
        # Iteration counter: iT = 1234
        m = re.search(r"iT\s*=\s*(\d+)", line)
        if m:
            it = int(m.group(1))
            self._current_iteration = it
            self._iteration_history.append(it)

        # Max iterations from XML echo: ade_max_iT = 50000
        m2 = re.search(r"ade_max_iT\s*=\s*(\d+)", line)
        if m2:
            self._max_iterations = int(m2.group(1))
            self._progress.setMaximum(self._max_iterations)

        # NS residual
        m3 = re.search(r"[Nn][Ss].*[Rr]esidual\s*[:=]\s*([0-9.eE+-]+)", line)
        if m3:
            try:
                val = float(m3.group(1))
                self._ns_residual_history.append(val)
                self._ns_residual_label.setText(f"{val:.4e}")
            except ValueError:
                pass

        # ADE residual / convergence
        m4 = re.search(
            r"[Aa][Dd][Ee].*(?:[Rr]esidual|[Cc]onverg)\s*[:=]\s*([0-9.eE+-]+)",
            line)
        if m4:
            try:
                val = float(m4.group(1))
                self._ade_residual_history.append(val)
                self._ade_residual_label.setText(f"{val:.4e}")
            except ValueError:
                pass

        # Phase detection
        if "phase 1" in line.lower() or "navier-stokes" in line.lower():
            self._phase_label.setText("NS Flow Solver (Phase 1)")
            self._status.setText("Running - NS Phase 1")
        elif "phase 2" in line.lower():
            self._phase_label.setText("NS Flow Solver (Phase 2)")
            self._status.setText("Running - NS Phase 2")
        elif "ade" in line.lower() and ("start" in line.lower() or "transport" in line.lower()):
            self._phase_label.setText("ADE Transport Solver")
            self._status.setText("Running - Transport")
        elif "equilibrium" in line.lower():
            self._phase_label.setText("Equilibrium Solver")
            self._status.setText("Running - Equilibrium")
        elif "kinetics" in line.lower():
            self._phase_label.setText("Kinetics")
        elif "biomass" in line.lower() and ("spread" in line.lower() or "push" in line.lower()):
            self._phase_label.setText("Biomass Redistribution")

    def on_finished(self, return_code: int, message: str):
        """Called when simulation finishes."""
        self._running = False
        self._timer.stop()
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)

        # Final elapsed time
        elapsed = time.time() - self._start_time
        hrs, rem = divmod(int(elapsed), 3600)
        mins, secs = divmod(rem, 60)
        self._elapsed.setText(f"{hrs}:{mins:02d}:{secs:02d}")
        self._eta_label.setText("Done")

        if return_code == 0:
            self._status.setText("Completed successfully")
            self._status.setStyleSheet(
                "font-weight: bold; font-size: 12px; color: #5ca060;")
            self._phase_label.setText("Finished")
            self._progress.setValue(self._progress.maximum())
        else:
            self._status.setText(f"Failed (exit code {return_code})")
            self._status.setStyleSheet(
                "font-weight: bold; font-size: 12px; color: #c75050;")
            self._phase_label.setText("Error")

            # Show error analysis
            error_info = self._analyze_exit_code(return_code)
            self._error_summary.setText(error_info)
            self._error_summary.setStyleSheet(
                "color: #f44336; background: #2a1515;"
                "border: 1px solid #f44336; padding: 8px;"
                "border-radius: 4px;")
            self._error_summary.setVisible(True)

    def _analyze_exit_code(self, code: int) -> str:
        """Return human-readable error analysis."""
        known = {
            -1: ("General Error",
                 "Check console output for details."),
            1: ("Configuration Error",
                "Invalid XML or missing parameters. Run Validate first."),
            2: ("File Not Found",
                "Geometry file or required input file missing."),
            -6: ("Abort / Assert Failure",
                 "Internal assertion failed. Check domain dimensions and geometry."),
            -11: ("Segmentation Fault",
                  "Memory access error. Geometry file dimensions likely mismatch "
                  "nx*ny*nz. Verify geometry file."),
            -1073740940: ("Heap Corruption (Windows)",
                          "Array bounds violation. Check geometry dimensions."),
            -1073741819: ("Access Violation (Windows)",
                          "Memory error. Check geometry file format."),
            -1073741571: ("Stack Overflow (Windows)",
                          "Domain too large for available memory."),
            139: ("Segfault (Linux signal 11)",
                  "Geometry mismatch or memory error. Check nx*ny*nz vs geometry file."),
            134: ("Abort (Linux signal 6)",
                  "Assertion failure in solver. Check parameters."),
        }
        error_type, desc = known.get(code, (
            f"Unknown Error (code {code})",
            "Run from command line for more details."))

        return (
            f"Error: {error_type}\n"
            f"{desc}\n\n"
            f"Suggestions:\n"
            f"  1. Run 'Validate Configuration' to check settings\n"
            f"  2. Verify geometry file has exactly nx*ny*nz values\n"
            f"  3. Check the Output tab for error details\n"
            f"  4. Try running from command line: ./complab"
        )

    # ── Validation display ──────────────────────────────────────────

    def show_validation(self, errors: list):
        """Display validation results (called from main window)."""
        if not errors:
            self._validation_lbl.setText("Configuration is valid.")
            self._validation_lbl.setStyleSheet("color: #5ca060;")
            self._validation_text.setHtml(
                '<span style="color:#5ca060; font-weight:bold;">'
                'All checks passed - configuration is valid.</span>')
        else:
            count = len(errors)
            self._validation_lbl.setText(
                f"{count} validation error(s) found. See Validation tab.")
            self._validation_lbl.setStyleSheet("color: #c75050;")

            html_parts = [
                '<span style="color:#c75050; font-weight:bold;">'
                f'Validation Report: {count} error(s)</span><br><br>']
            for i, err in enumerate(errors, 1):
                html_parts.append(
                    f'<span style="color:#f44336;">'
                    f'{i}. {_escape_html(err)}</span><br>')
            html_parts.append(
                '<br><span style="color:#9e9e9e;">'
                'Fix the errors above and validate again before running.</span>')
            self._validation_text.setHtml("".join(html_parts))

    # ── Output helpers ──────────────────────────────────────────────

    def _clear_output(self):
        self._output_text.clear()

    def _save_log(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Simulation Log",
            "simulation_log.txt", "Text Files (*.txt);;All Files (*)")
        if path:
            with open(path, "w") as f:
                f.write(self._output_text.toPlainText())


def _escape_html(text: str) -> str:
    """Escape HTML special characters for QTextEdit display."""
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;"))
