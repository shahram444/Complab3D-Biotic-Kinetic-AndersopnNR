"""Shared pytest-qt configuration and fixtures."""

import os
import sys
from pathlib import Path

# Make sure GUI/src is on the path
GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GUI_DIR))

# Use offscreen platform so tests don't need a display server
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

# A QApplication must exist before any module-level QPixmap/QIcon constructors
# run during test collection (e.g. the icon table at the top of
# src/widgets/model_tree.py). Pytest-qt's `qapp` fixture creates one only when
# requested by a test, which is too late — collection imports happen first and
# Qt aborts the process. Create it here, eagerly.
from PySide6.QtWidgets import QApplication  # noqa: E402

_qapp = QApplication.instance() or QApplication(sys.argv)
