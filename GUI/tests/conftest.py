"""Shared pytest-qt configuration and fixtures."""

import os
import sys
from pathlib import Path

# Make sure GUI/src is on the path
GUI_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(GUI_DIR))

# Use offscreen platform so tests don't need a display server
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
