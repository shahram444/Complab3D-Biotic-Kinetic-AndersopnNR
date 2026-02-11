"""Geometry 2D slice preview widget using matplotlib."""

import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QWidget, QLabel, QSlider, QComboBox,
)
from PySide6.QtCore import Qt

try:
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.colors import ListedColormap
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


# Material colormap: 0=solid(gray), 1=bounce-back(dark), 2=pore(blue), 3+=microbes(warm)
_MATERIAL_COLORS = [
    '#404040',  # 0 - solid
    '#1a1a2e',  # 1 - bounce-back
    '#4a90d9',  # 2 - pore
    '#c06060',  # 3 - microbe 1
    '#e0a040',  # 4 - microbe 2
    '#50b060',  # 5 - microbe 3
    '#a060c0',  # 6 - fringe
    '#c09040',  # 7
]


class GeometryPreviewWidget(QWidget):
    """Show a 2D slice of a geometry.dat file.

    Allows user to pick axis (XY/XZ/YZ) and scroll through slices.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = None  # 3D numpy array (nx, ny, nz)
        self._nx = self._ny = self._nz = 0
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        if not HAS_MATPLOTLIB:
            lbl = QLabel("matplotlib not installed. Install to enable geometry preview.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setProperty("info", True)
            layout.addWidget(lbl)
            self._info_lbl = lbl
            return

        # Controls row
        ctrl = QHBoxLayout()

        ctrl.addWidget(QLabel("Plane:"))
        self._plane_combo = QComboBox()
        self._plane_combo.addItems(["XY (Z slice)", "XZ (Y slice)", "YZ (X slice)"])
        self._plane_combo.currentIndexChanged.connect(self._on_plane_changed)
        ctrl.addWidget(self._plane_combo)

        ctrl.addWidget(QLabel("Slice:"))
        self._slice_slider = QSlider(Qt.Orientation.Horizontal)
        self._slice_slider.setMinimum(0)
        self._slice_slider.setMaximum(0)
        self._slice_slider.valueChanged.connect(self._on_slice_changed)
        ctrl.addWidget(self._slice_slider, 1)

        self._slice_lbl = QLabel("0 / 0")
        self._slice_lbl.setFixedWidth(60)
        self._slice_lbl.setProperty("info", True)
        ctrl.addWidget(self._slice_lbl)

        layout.addLayout(ctrl)

        # Matplotlib figure
        self._fig = Figure(figsize=(4, 3), dpi=100)
        self._fig.patch.set_facecolor('none')
        self._ax = self._fig.add_subplot(111)
        self._canvas = FigureCanvas(self._fig)
        self._canvas.setStyleSheet("background: transparent;")
        layout.addWidget(self._canvas)

        # Info label
        self._info_lbl = QLabel("Load a geometry file to preview.")
        self._info_lbl.setProperty("info", True)
        self._info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._info_lbl)

        self._init_plot()

    def _init_plot(self):
        if not HAS_MATPLOTLIB:
            return
        ax = self._ax
        ax.set_facecolor('#1e1f22')
        ax.tick_params(colors='#7a7d82', labelsize=7)
        ax.spines['bottom'].set_color('#393b40')
        ax.spines['left'].set_color('#393b40')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self._fig.tight_layout(pad=1.0)

    def load_geometry(self, filepath: str, nx: int, ny: int, nz: int):
        """Load a .dat geometry file and display the middle slice."""
        try:
            raw = np.loadtxt(filepath, dtype=int)
            flat = raw.flatten()
            expected = nx * ny * nz
            if flat.size != expected:
                self._info_lbl.setText(
                    f"Size mismatch: file has {flat.size} values, "
                    f"expected {nx}x{ny}x{nz}={expected}"
                )
                return

            # Reshape: file is stored as nz slices of (ny x nx)
            self._data = flat.reshape((nz, ny, nx))
            self._nx, self._ny, self._nz = nx, ny, nz

            # Set slider to middle slice
            self._on_plane_changed(self._plane_combo.currentIndex())

            n_unique = len(np.unique(self._data))
            self._info_lbl.setText(
                f"Loaded: {nx}x{ny}x{nz} = {nx*ny*nz:,} cells, "
                f"{n_unique} material types"
            )
        except Exception as e:
            self._info_lbl.setText(f"Failed to load: {e}")

    def _on_plane_changed(self, idx):
        """Update slider range when plane changes."""
        if self._data is None:
            return
        if idx == 0:  # XY -> Z axis
            max_val = self._nz - 1
        elif idx == 1:  # XZ -> Y axis
            max_val = self._ny - 1
        else:  # YZ -> X axis
            max_val = self._nx - 1

        self._slice_slider.setMaximum(max_val)
        self._slice_slider.setValue(max_val // 2)
        self._draw_slice()

    def _on_slice_changed(self, val):
        """Redraw when slice index changes."""
        self._draw_slice()

    def _draw_slice(self):
        """Draw the current 2D slice."""
        if not HAS_MATPLOTLIB or self._data is None:
            return

        plane = self._plane_combo.currentIndex()
        idx = self._slice_slider.value()
        max_val = self._slice_slider.maximum()
        self._slice_lbl.setText(f"{idx} / {max_val}")

        ax = self._ax
        ax.clear()
        ax.set_facecolor('#1e1f22')
        ax.tick_params(colors='#7a7d82', labelsize=7)

        # Extract 2D slice
        if plane == 0:  # XY at Z=idx
            slice_2d = self._data[idx, :, :]
            ax.set_xlabel('X', fontsize=8, color='#bcbec4')
            ax.set_ylabel('Y', fontsize=8, color='#bcbec4')
            ax.set_title(f'XY plane, Z={idx}', fontsize=8, color='#bcbec4')
        elif plane == 1:  # XZ at Y=idx
            slice_2d = self._data[:, idx, :]
            ax.set_xlabel('X', fontsize=8, color='#bcbec4')
            ax.set_ylabel('Z', fontsize=8, color='#bcbec4')
            ax.set_title(f'XZ plane, Y={idx}', fontsize=8, color='#bcbec4')
        else:  # YZ at X=idx
            slice_2d = self._data[:, :, idx]
            ax.set_xlabel('Y', fontsize=8, color='#bcbec4')
            ax.set_ylabel('Z', fontsize=8, color='#bcbec4')
            ax.set_title(f'YZ plane, X={idx}', fontsize=8, color='#bcbec4')

        # Build colormap
        max_mat = int(slice_2d.max())
        n_colors = max(max_mat + 1, len(_MATERIAL_COLORS))
        colors = _MATERIAL_COLORS[:n_colors]
        # Pad if more materials than defined colors
        while len(colors) <= max_mat:
            colors.append('#808080')
        cmap = ListedColormap(colors[:max_mat + 1])

        ax.imshow(slice_2d, cmap=cmap, origin='lower', interpolation='nearest',
                  vmin=0, vmax=max_mat, aspect='equal')

        self._fig.tight_layout(pad=1.0)
        self._canvas.draw_idle()
