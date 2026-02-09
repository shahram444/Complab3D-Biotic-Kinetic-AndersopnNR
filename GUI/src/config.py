"""Application configuration stored as JSON."""

import json
import os
from pathlib import Path

DEFAULT_CONFIG = {
    "complab_executable": "",
    "default_project_dir": str(Path.home() / "CompLaB_Projects"),
    "recent_projects": [],
    "max_recent": 10,
    "theme": "dark",
    "font_size": 10,
    "auto_save": False,
    "auto_save_interval": 300,
    "max_console_lines": 10000,
}

CONFIG_DIR = Path.home() / ".complab_studio"
CONFIG_FILE = CONFIG_DIR / "config.json"


class Config:
    def __init__(self):
        self._data = dict(DEFAULT_CONFIG)
        self.load()

    def load(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r") as f:
                    stored = json.load(f)
                self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value

    def add_recent_project(self, path):
        recents = self._data.get("recent_projects", [])
        path = str(path)
        if path in recents:
            recents.remove(path)
        recents.insert(0, path)
        max_r = self._data.get("max_recent", 10)
        self._data["recent_projects"] = recents[:max_r]
        self.save()
