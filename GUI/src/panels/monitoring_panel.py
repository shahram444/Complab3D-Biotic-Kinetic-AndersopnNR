"""Simulation monitoring panel - run controls and live status."""

import time
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QWidget, QPushButton,
    QGroupBox, QProgressBar, QFormLayout,
)
from PySide6.QtCore import Qt, QTimer

from .base_panel import BasePanel


class MonitoringPanel(BasePanel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self._start_time = None
        self._iteration = 0
        self._setup_ui()

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(self._create_heading("Run Simulation"))
        layout.addWidget(self._create_subheading(
            "Launch, monitor, and control the CompLaB3D simulation."))

        # Controls
        ctrl_group = self._create_group("Controls")
        cl = QHBoxLayout(ctrl_group)
        self._run_btn = QPushButton("Run Simulation")
        self._run_btn.setProperty("primary", True)
        self._run_btn.setMinimumHeight(36)
        self._stop_btn = QPushButton("Stop")
        self._stop_btn.setEnabled(False)
        self._stop_btn.setMinimumHeight(36)
        self._validate_btn = QPushButton("Validate")
        self._validate_btn.setMinimumHeight(36)
        cl.addWidget(self._run_btn)
        cl.addWidget(self._stop_btn)
        cl.addWidget(self._validate_btn)
        layout.addWidget(ctrl_group)

        # Status
        status_group = self._create_group("Status")
        sf = QFormLayout(status_group)
        sf.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        self._status_label = QLabel("Idle")
        self._iter_label = QLabel("0")
        self._elapsed_label = QLabel("--:--:--")
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)

        sf.addRow("Status:", self._status_label)
        sf.addRow("Iteration:", self._iter_label)
        sf.addRow("Elapsed:", self._elapsed_label)
        sf.addRow("Progress:", self._progress)
        layout.addWidget(status_group)

        # Validation results
        val_group = self._create_group("Validation Results")
        vl = QVBoxLayout(val_group)
        self._val_output = QLabel("Run validation to check configuration.")
        self._val_output.setProperty("info", True)
        self._val_output.setWordWrap(True)
        self._val_output.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        vl.addWidget(self._val_output)
        layout.addWidget(val_group)

        layout.addStretch()

        # Timer for elapsed time
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._update_elapsed)

        outer.addWidget(self._create_scroll_area(w))

    @property
    def run_button(self):
        return self._run_btn

    @property
    def stop_button(self):
        return self._stop_btn

    @property
    def validate_button(self):
        return self._validate_btn

    def on_simulation_started(self):
        self._start_time = time.time()
        self._iteration = 0
        self._status_label.setText("Running")
        self._status_label.setProperty("success", True)
        self._status_label.style().polish(self._status_label)
        self._progress.setVisible(True)
        self._run_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._timer.start()

    def on_simulation_finished(self, success, message):
        self._timer.stop()
        self._progress.setVisible(False)
        self._run_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
        if success:
            self._status_label.setText("Completed")
            self._status_label.setProperty("success", True)
        else:
            self._status_label.setText(f"Failed: {message}")
            self._status_label.setProperty("error", True)
        self._status_label.style().polish(self._status_label)

    def on_progress(self, iteration, max_iter):
        self._iteration = iteration
        self._iter_label.setText(f"{iteration:,}")

    def set_validation_results(self, issues):
        if not issues:
            self._val_output.setText("All checks passed.")
            self._val_output.setProperty("success", True)
        else:
            lines = []
            for level, msg in issues:
                prefix = "[ERROR]" if level == "error" else "[WARNING]"
                lines.append(f"{prefix} {msg}")
            self._val_output.setText("\n".join(lines))
            has_errors = any(l == "error" for l, _ in issues)
            self._val_output.setProperty("error", has_errors)
            self._val_output.setProperty("warning", not has_errors)
        self._val_output.style().polish(self._val_output)

    def _update_elapsed(self):
        if self._start_time:
            elapsed = int(time.time() - self._start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self._elapsed_label.setText(f"{h:02d}:{m:02d}:{s:02d}")

    def _populate_fields(self):
        pass

    def collect_data(self, project):
        pass
