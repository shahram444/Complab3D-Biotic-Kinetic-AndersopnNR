"""Model Builder tree widget - COMSOL-style navigation tree.

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
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont


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
NODE_RUN = "run"
NODE_POSTPROCESS = "postprocess"


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
        self.setMinimumWidth(200)

        bold = QFont()
        bold.setBold(True)

        self._root = QTreeWidgetItem(self, ["CompLaB3D Model"])
        self._root.setFont(0, bold)
        self._root.setData(0, Qt.ItemDataRole.UserRole, (NODE_GENERAL, -1))

        self._general = QTreeWidgetItem(self._root, ["Simulation Mode"])
        self._general.setData(0, Qt.ItemDataRole.UserRole, (NODE_GENERAL, -1))

        self._domain = QTreeWidgetItem(self._root, ["Domain"])
        self._domain.setData(0, Qt.ItemDataRole.UserRole, (NODE_DOMAIN, -1))

        self._fluid = QTreeWidgetItem(self._root, ["Fluid / Flow"])
        self._fluid.setData(0, Qt.ItemDataRole.UserRole, (NODE_FLUID, -1))

        self._chem = QTreeWidgetItem(self._root, ["Chemistry"])
        self._chem.setData(0, Qt.ItemDataRole.UserRole, (NODE_CHEMISTRY, -1))
        self._chem.setFont(0, bold)
        self._sub_items = []

        self._micro = QTreeWidgetItem(self._root, ["Microbiology"])
        self._micro.setData(0, Qt.ItemDataRole.UserRole, (NODE_MICROBIOLOGY, -1))
        self._micro.setFont(0, bold)
        self._mic_items = []

        self._eq = QTreeWidgetItem(self._root, ["Equilibrium Chemistry"])
        self._eq.setData(0, Qt.ItemDataRole.UserRole, (NODE_EQUILIBRIUM, -1))

        self._solver = QTreeWidgetItem(self._root, ["Solver Settings"])
        self._solver.setData(0, Qt.ItemDataRole.UserRole, (NODE_SOLVER, -1))

        self._io = QTreeWidgetItem(self._root, ["I/O Settings"])
        self._io.setData(0, Qt.ItemDataRole.UserRole, (NODE_IO, -1))

        self._run = QTreeWidgetItem(self._root, ["Run"])
        self._run.setData(0, Qt.ItemDataRole.UserRole, (NODE_RUN, -1))
        self._run.setFont(0, bold)

        self._post = QTreeWidgetItem(self._root, ["Post-Processing"])
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
            item.setData(0, Qt.ItemDataRole.UserRole, (NODE_SUBSTRATE, i))
            self._sub_items.append(item)

    def update_microbes(self, names: list):
        """Rebuild microbe child nodes."""
        for item in self._mic_items:
            self._micro.removeChild(item)
        self._mic_items.clear()
        for i, name in enumerate(names):
            item = QTreeWidgetItem(self._micro, [name])
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
