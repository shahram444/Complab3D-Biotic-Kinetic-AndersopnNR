"""Run panel - simulation execution controls with convergence plot."""

import time
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar,
)
from PySide6.QtCore import Signal, QTimer
from .base_panel import BasePanel
from ..widgets.convergence_plot import ConvergencePlotWidget


class RunPanel(BasePanel):
    """Run controls: validate, start, stop simulation + live convergence plot."""

    run_requested = Signal()
    stop_requested = Signal()
    validate_requested = Signal()
    export_xml_requested = Signal()

    def __init__(self, parent=None):
        super().__init__("Run Simulation", parent)
        self._running = False
        self._start_time = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_elapsed)
        self._build_ui()

    def _build_ui(self):
        self.add_section("Pre-Run Checks")

        row1 = QHBoxLayout()
        validate_btn = self.make_button("Validate Configuration")
        validate_btn.clicked.connect(self.validate_requested.emit)
        row1.addWidget(validate_btn)

        export_btn = self.make_button("Export CompLaB.xml")
        export_btn.clicked.connect(self.export_xml_requested.emit)
        row1.addWidget(export_btn)
        row1.addStretch()
        self.add_layout(row1)

        self._validation_lbl = QLabel("")
        self._validation_lbl.setWordWrap(True)
        self.add_widget(self._validation_lbl)

        self.add_section("Execution")

        row2 = QHBoxLayout()
        self._run_btn = self.make_button("Run Simulation", primary=True)
        self._run_btn.clicked.connect(self._on_run)
        row2.addWidget(self._run_btn)

        self._stop_btn = self.make_button("Stop")
        self._stop_btn.setProperty("danger", True)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._on_stop)
        row2.addWidget(self._stop_btn)
        row2.addStretch()
        self.add_layout(row2)

        self.add_section("Status")
        form = self.add_form()

        self._status = QLabel("Ready")
        self._status.setProperty("info", True)
        form.addRow("Status:", self._status)

        self._elapsed = QLabel("0:00:00")
        form.addRow("Elapsed:", self._elapsed)

        self._progress = QProgressBar()
        self._progress.setValue(0)
        form.addRow("Progress:", self._progress)

        self._error_detail = QLabel("")
        self._error_detail.setWordWrap(True)
        self._error_detail.setStyleSheet("color: #c75050; padding: 4px;")
        self._error_detail.setVisible(False)
        form.addRow("", self._error_detail)

        # Convergence info
        self.add_section("Convergence")
        conv_form = self.add_form()

        self._ns_residual = QLabel("-")
        self._ns_residual.setProperty("info", True)
        conv_form.addRow("NS residual:", self._ns_residual)

        self._ade_residual = QLabel("-")
        self._ade_residual.setProperty("info", True)
        conv_form.addRow("ADE residual:", self._ade_residual)

        self._phase_lbl = QLabel("-")
        self._phase_lbl.setProperty("info", True)
        self._phase_lbl.setWordWrap(True)
        conv_form.addRow("Phase:", self._phase_lbl)

        # Live convergence plot
        self.add_section("Convergence Plot")
        self._conv_plot = ConvergencePlotWidget()
        self._conv_plot.setMinimumHeight(180)
        self.add_widget(self._conv_plot)

        self.add_stretch()

    def _on_run(self):
        self._running = True
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status.setText("Running...")
        self._status.setStyleSheet("")
        self._ns_residual.setText("-")
        self._ade_residual.setText("-")
        self._phase_lbl.setText("Starting...")
        self._conv_plot.clear()
        self._start_time = time.time()
        self._timer.start(1000)
        self.run_requested.emit()

    def _on_stop(self):
        self._stop_btn.setEnabled(False)
        self._status.setText("Stopping...")
        self.stop_requested.emit()

    def _update_elapsed(self):
        elapsed = int(time.time() - self._start_time)
        hrs, rem = divmod(elapsed, 3600)
        mins, secs = divmod(rem, 60)
        self._elapsed.setText(f"{hrs}:{mins:02d}:{secs:02d}")

    def on_finished(self, return_code: int, message: str):
        self._running = False
        self._timer.stop()
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        self._conv_plot.force_redraw()
        if return_code == 0:
            self._status.setText("Completed successfully")
            self._status.setStyleSheet("color: #5ca060;")
            self._phase_lbl.setText("Done")
            self._error_detail.setText("")
            self._error_detail.setVisible(False)
        else:
            self._status.setText(f"Failed (code {return_code})")
            self._status.setStyleSheet("color: #c75050;")
            # Show brief error type from exit code
            from ..core.simulation_runner import EXIT_CODE_INFO, _UNSIGNED_TO_SIGNED
            info = EXIT_CODE_INFO.get(return_code)
            if info is None:
                signed = _UNSIGNED_TO_SIGNED.get(return_code)
                if signed is not None:
                    info = EXIT_CODE_INFO.get(signed)
            if info is None and return_code > 2**31:
                info = EXIT_CODE_INFO.get(return_code - 2**32)
            if info and info["type"] != "Success":
                self._error_detail.setText(
                    f"Error: {info['type']}\n{info['reason']}")
                self._error_detail.setVisible(True)
            else:
                self._error_detail.setText(
                    "See console for error diagnostics.")
                self._error_detail.setVisible(True)

    def on_progress(self, current: int, maximum: int):
        _QT_INT_MAX = 2_147_483_647
        if maximum > 0:
            if maximum > _QT_INT_MAX:
                scale = _QT_INT_MAX / maximum
                maximum = _QT_INT_MAX
                current = min(int(current * scale), _QT_INT_MAX)
            self._progress.setMaximum(maximum)
            self._progress.setValue(min(current, maximum))

    def on_convergence(self, solver: str, iteration: int, residual: float):
        """Update convergence residual display + feed to plot."""
        text = f"{residual:.3e}  (iT={iteration})"
        if solver == "NS":
            self._ns_residual.setText(text)
        elif solver == "ADE":
            self._ade_residual.setText(text)
        self._conv_plot.add_point(solver, iteration, residual)

    def on_phase_changed(self, phase: str):
        """Update phase display."""
        self._phase_lbl.setText(phase)

    def show_validation(self, errors: list):
        if not errors:
            self._validation_lbl.setText("Configuration is valid.")
            self._validation_lbl.setStyleSheet("color: #5ca060;")
        else:
            text = "Validation errors:\n" + "\n".join(f"  - {e}" for e in errors)
            self._validation_lbl.setText(text)
            self._validation_lbl.setStyleSheet("color: #c75050;")
