"""Real-time convergence plot using matplotlib embedded in Qt."""

from collections import deque

from PySide6.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class ConvergencePlotWidget(QWidget):
    """Live-updating convergence residual plot (NS + ADE).

    Embedded matplotlib chart that shows residual vs iteration during
    a running simulation. Auto-scales Y axis in log scale.
    """

    MAX_POINTS = 2000  # Keep last N points to avoid memory bloat

    def __init__(self, parent=None):
        super().__init__(parent)
        self._ns_iters = deque(maxlen=self.MAX_POINTS)
        self._ns_vals = deque(maxlen=self.MAX_POINTS)
        self._ade_iters = deque(maxlen=self.MAX_POINTS)
        self._ade_vals = deque(maxlen=self.MAX_POINTS)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        if not HAS_MATPLOTLIB:
            lbl = QLabel(
                "matplotlib not installed.\n"
                "Install with: pip install matplotlib\n"
                "to enable real-time convergence plots."
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setProperty("info", True)
            layout.addWidget(lbl)
            return

        # Matplotlib figure
        self._fig = Figure(figsize=(5, 2.5), dpi=100)
        self._fig.patch.set_facecolor('none')
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setStyleSheet("background: transparent;")
        layout.addWidget(self._canvas)

        # Control buttons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(4, 2, 4, 2)

        clear_btn = QPushButton("Clear Plot")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self.clear)
        btn_row.addWidget(clear_btn)

        btn_row.addStretch()

        self._count_lbl = QLabel("0 data points")
        self._count_lbl.setProperty("info", True)
        btn_row.addWidget(self._count_lbl)

        layout.addLayout(btn_row)

        self._init_plot()

    def _init_plot(self):
        """Set up the initial plot axes and style."""
        if not HAS_MATPLOTLIB:
            return
        ax = self._ax
        ax.set_facecolor('#1e1f22')
        ax.set_xlabel('Iteration', fontsize=8, color='#bcbec4')
        ax.set_ylabel('Residual', fontsize=8, color='#bcbec4')
        ax.set_yscale('log')
        ax.tick_params(colors='#7a7d82', labelsize=7)
        ax.spines['bottom'].set_color('#393b40')
        ax.spines['left'].set_color('#393b40')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(True, alpha=0.2, color='#4b4d52')

        self._ns_line, = ax.plot([], [], color='#4a90d9', linewidth=1.2,
                                 label='NS', alpha=0.9)
        self._ade_line, = ax.plot([], [], color='#e08040', linewidth=1.2,
                                  label='ADE', alpha=0.9)
        ax.legend(fontsize=7, loc='upper right',
                  facecolor='#2b2d30', edgecolor='#393b40',
                  labelcolor='#bcbec4')
        self._fig.tight_layout(pad=1.5)

    def add_point(self, solver: str, iteration: int, residual: float):
        """Add a convergence data point and redraw."""
        if not HAS_MATPLOTLIB:
            return

        if solver == "NS":
            self._ns_iters.append(iteration)
            self._ns_vals.append(residual)
        elif solver == "ADE":
            self._ade_iters.append(iteration)
            self._ade_vals.append(residual)

        total = len(self._ns_iters) + len(self._ade_iters)
        self._count_lbl.setText(f"{total} data points")

        # Throttle redraws: only redraw every 10 points
        if total % 10 != 0:
            return

        self._redraw()

    def _redraw(self):
        """Update plot lines and redraw canvas."""
        if not HAS_MATPLOTLIB:
            return

        if self._ns_iters:
            self._ns_line.set_data(list(self._ns_iters),
                                   list(self._ns_vals))
        if self._ade_iters:
            self._ade_line.set_data(list(self._ade_iters),
                                    list(self._ade_vals))

        self._ax.relim()
        self._ax.autoscale_view()
        self._canvas.draw_idle()

    def clear(self):
        """Clear all data and reset plot."""
        self._ns_iters.clear()
        self._ns_vals.clear()
        self._ade_iters.clear()
        self._ade_vals.clear()
        if HAS_MATPLOTLIB:
            self._ns_line.set_data([], [])
            self._ade_line.set_data([], [])
            self._ax.relim()
            self._ax.autoscale_view()
            self._canvas.draw_idle()
            self._count_lbl.setText("0 data points")

    def force_redraw(self):
        """Force a redraw (call after simulation ends)."""
        if HAS_MATPLOTLIB and (self._ns_iters or self._ade_iters):
            self._redraw()
