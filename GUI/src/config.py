"""Application configuration stored as JSON."""

import json
import os
from pathlib import Path


class AppConfig:
    """Persistent app settings at ~/.complab_studio/config.json."""

    _DEFAULTS = {
        "complab_executable": "",
        "default_project_dir": "",
        "auto_save": False,
        "auto_save_interval": 300,
        "font_size": 10,
        "max_console_lines": 10000,
        "recent_projects": [],
    }

    def __init__(self):
        self._dir = Path.home() / ".complab_studio"
        self._path = self._dir / "config.json"
        self._data = dict(self._DEFAULTS)
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                with open(self._path, "r") as f:
                    stored = json.load(f)
                self._data.update(stored)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key: str, default=None):
        return self._data.get(key, default if default is not None else self._DEFAULTS.get(key))

    def set(self, key: str, value):
        self._data[key] = value

    def add_recent(self, filepath: str):
        recents = self._data.get("recent_projects", [])
        if filepath in recents:
            recents.remove(filepath)
        recents.insert(0, filepath)
        self._data["recent_projects"] = recents[:10]
        self.save()
