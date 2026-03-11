"""Model Builder tree widget - COMSOL-style navigation tree with icons.

Displays the simulation model as a hierarchical tree:
  Project Name
  +-- Simulation Mode
  +-- Domain
  +-- Fluid / Flow
  +-- Chemistry
  |   +-- Substrate 0
  |   +-- Substrate 1 ...
  +-- Microbiology
  |   +-- Microbe 0
  |   +-- Microbe 1 ...
  +-- Equilibrium
  +-- Solver
  +-- I/O
  +-- Run
  +-- Post-Processing
"""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide6.QtCore import Signal, Qt, QSize, QPoint
from PySide6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QBrush, QPolygon


# Node identifiers used by the main window to switch panels
NODE_GENERAL = "general"
NODE_DOMAIN = "domain"
NODE_FLUID = "fluid"
NODE_CHEMISTRY = "chemistry"
NODE_SUBSTRATE = "substrate"        # + index
NODE_EQUILIBRIUM = "equilibrium"
NODE_MICROBIOLOGY = "microbiology"
NODE_MICROBE = "microbe"            # + index
NODE_SOLVER = "solver"
NODE_IO = "io"
NODE_PARALLEL = "parallel"
NODE_SWEEP = "sweep"
NODE_RUN = "run"
NODE_POSTPROCESS = "postprocess"


def _make_icon(color: str, shape: str = "circle") -> QIcon:
    """Create a small colored icon for tree nodes (COMSOL style)."""
    size = 16
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    c = QColor(color)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(c))
    if shape == "circle":
        p.drawEllipse(2, 2, size - 4, size - 4)
    elif shape == "square":
        p.drawRoundedRect(2, 2, size - 4, size - 4, 2, 2)
    elif shape == "diamond":
        poly = QPolygon([
            QPoint(size // 2, 1), QPoint(size - 2, size // 2),
            QPoint(size // 2, size - 2), QPoint(2, size // 2),
        ])
        p.drawPolygon(poly)
    elif shape == "triangle":
        poly = QPolygon([
            QPoint(size // 2, 2), QPoint(size - 2, size - 3),
            QPoint(2, size - 3),
        ])
        p.drawPolygon(poly)
    p.end()
    return QIcon(pm)


# COMSOL-like icon color scheme
ICON_PROJECT   = _make_icon("#4a90d9", "square")   # Blue square
ICON_GENERAL   = _make_icon("#6a8aaa", "circle")   # Slate
ICON_DOMAIN    = _make_icon("#e0a040", "square")    # Amber grid
ICON_FLUID     = _make_icon("#4a90d9", "circle")    # Blue flow
ICON_CHEM      = _make_icon("#50b060", "diamond")   # Green chem
ICON_SUBSTRATE = _make_icon("#70c080", "circle")    # Light green
ICON_MICRO     = _make_icon("#c06060", "diamond")   # Red bio
ICON_MICROBE   = _make_icon("#d08080", "circle")    # Light red
ICON_EQUIL     = _make_icon("#a060c0", "diamond")   # Purple eq
ICON_SOLVER    = _make_icon("#c09040", "triangle")  # Orange solver
ICON_IO        = _make_icon("#607090", "square")    # Gray IO
ICON_PARALLEL  = _make_icon("#e08040", "square")    # Orange parallel
ICON_SWEEP     = _make_icon("#c060c0", "diamond")   # Purple sweep
ICON_RUN       = _make_icon("#40a040", "triangle")  # Green play
ICON_POST      = _make_icon("#4080c0", "square")    # Blue post


class ModelTree(QTreeWidget):
    """Hierarchical model builder tree."""

    node_selected = Signal(str, int)  # (node_type, index)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)
        self.setIndentation(18)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(True)
        self.setRootIsDecorated(True)
        self.setMinimumWidth(220)
        self.setIconSize(QSize(16, 16))

        bold = QFont()
        bold.setBold(True)

        self._root = QTreeWidgetItem(self, ["CompLaB3D Model"])
        self._root.setFont(0, bold)
        self._root.setIcon(0, ICON_PROJECT)
        self._root.setData(0, Qt.ItemDataRole.UserRole, (NODE_GENERAL, -1))

        self._general = QTreeWidgetItem(self._root, ["Simulation Mode"])
        self._general.setIcon(0, ICON_GENERAL)
        self._general.setData(0, Qt.ItemDataRole.UserRole, (NODE_GENERAL, -1))

        self._domain = QTreeWidgetItem(self._root, ["Domain"])
        self._domain.setIcon(0, ICON_DOMAIN)
        self._domain.setData(0, Qt.ItemDataRole.UserRole, (NODE_DOMAIN, -1))

        self._fluid = QTreeWidgetItem(self._root, ["Fluid / Flow"])
        self._fluid.setIcon(0, ICON_FLUID)
        self._fluid.setData(0, Qt.ItemDataRole.UserRole, (NODE_FLUID, -1))

        self._chem = QTreeWidgetItem(self._root, ["Chemistry"])
        self._chem.setIcon(0, ICON_CHEM)
        self._chem.setData(0, Qt.ItemDataRole.UserRole, (NODE_CHEMISTRY, -1))
        self._chem.setFont(0, bold)
        self._sub_items = []

        self._micro = QTreeWidgetItem(self._root, ["Microbiology"])
        self._micro.setIcon(0, ICON_MICRO)
        self._micro.setData(0, Qt.ItemDataRole.UserRole, (NODE_MICROBIOLOGY, -1))
        self._micro.setFont(0, bold)
        self._mic_items = []

        self._eq = QTreeWidgetItem(self._root, ["Equilibrium Chemistry"])
        self._eq.setIcon(0, ICON_EQUIL)
        self._eq.setData(0, Qt.ItemDataRole.UserRole, (NODE_EQUILIBRIUM, -1))

        self._solver = QTreeWidgetItem(self._root, ["Solver Settings"])
        self._solver.setIcon(0, ICON_SOLVER)
        self._solver.setData(0, Qt.ItemDataRole.UserRole, (NODE_SOLVER, -1))

        self._io = QTreeWidgetItem(self._root, ["I/O Settings"])
        self._io.setIcon(0, ICON_IO)
        self._io.setData(0, Qt.ItemDataRole.UserRole, (NODE_IO, -1))

        self._parallel = QTreeWidgetItem(self._root, ["Parallel Execution"])
        self._parallel.setIcon(0, ICON_PARALLEL)
        self._parallel.setData(0, Qt.ItemDataRole.UserRole, (NODE_PARALLEL, -1))

        self._sweep = QTreeWidgetItem(self._root, ["Parameter Sweep"])
        self._sweep.setIcon(0, ICON_SWEEP)
        self._sweep.setData(0, Qt.ItemDataRole.UserRole, (NODE_SWEEP, -1))

        self._run = QTreeWidgetItem(self._root, ["Run"])
        self._run.setIcon(0, ICON_RUN)
        self._run.setData(0, Qt.ItemDataRole.UserRole, (NODE_RUN, -1))
        self._run.setFont(0, bold)

        self._post = QTreeWidgetItem(self._root, ["Post-Processing"])
        self._post.setIcon(0, ICON_POST)
        self._post.setData(0, Qt.ItemDataRole.UserRole, (NODE_POSTPROCESS, -1))

        self._root.setExpanded(True)
        self._chem.setExpanded(True)
        self._micro.setExpanded(True)

        self.currentItemChanged.connect(self._on_item_changed)

    def _on_item_changed(self, current, _previous):
        if current is None:
            return
        data = current.data(0, Qt.ItemDataRole.UserRole)
        if data:
            node_type, index = data
            self.node_selected.emit(node_type, index)

    def update_substrates(self, names: list):
        """Rebuild substrate child nodes."""
        for item in self._sub_items:
            self._chem.removeChild(item)
        self._sub_items.clear()
        for i, name in enumerate(names):
            item = QTreeWidgetItem(self._chem, [name])
            item.setIcon(0, ICON_SUBSTRATE)
            item.setData(0, Qt.ItemDataRole.UserRole, (NODE_SUBSTRATE, i))
            self._sub_items.append(item)

    def update_microbes(self, names: list):
        """Rebuild microbe child nodes."""
        for item in self._mic_items:
            self._micro.removeChild(item)
        self._mic_items.clear()
        for i, name in enumerate(names):
            item = QTreeWidgetItem(self._micro, [name])
            item.setIcon(0, ICON_MICROBE)
            item.setData(0, Qt.ItemDataRole.UserRole, (NODE_MICROBE, i))
            self._mic_items.append(item)

    def select_node(self, node_type: str, index: int = -1):
        """Programmatically select a tree node."""
        def _find(parent):
            for i in range(parent.childCount()):
                child = parent.child(i)
                data = child.data(0, Qt.ItemDataRole.UserRole)
                if data and data[0] == node_type and data[1] == index:
                    return child
                found = _find(child)
                if found:
                    return found
            return None

        target = _find(self._root)
        if target:
            self.setCurrentItem(target)
        elif node_type == NODE_GENERAL:
            self.setCurrentItem(self._general)

    def update_project_name(self, name: str):
        self._root.setText(0, name or "CompLaB3D Model")
