"""Tests for src/config.py -- AppConfig persistent settings.

What this covers:
  AppConfig stores the user's application preferences (solver executable path,
  recent project list, theme, font size, etc.) as a JSON file at
  ~/.complab_studio/config.json.  It is the first thing the GUI reads at
  startup and the last thing it writes at shutdown.

  These tests redirect all file I/O to a temporary directory so they never
  touch the user's real ~/.complab_studio folder.

  No Qt or display is required.
"""

import json
import os
import sys
from pathlib import Path

import pytest

# Make GUI/src importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# We monkeypatch the config directory so tests don't write to ~/.complab_studio
from src import config as _config_module


# ---------------------------------------------------------------------------
# Fixture: redirect config I/O to tmp_path
# ---------------------------------------------------------------------------

@pytest.fixture()
def cfg(tmp_path, monkeypatch):
    """Create an AppConfig instance whose storage is in tmp_path."""
    cfg_dir = tmp_path / ".complab_studio"
    monkeypatch.setattr(
        _config_module.Path, "home", staticmethod(lambda: tmp_path)
    )
    # Re-import to get a fresh instance pointing at tmp_path
    from importlib import reload
    mod = reload(_config_module)
    return mod.AppConfig()


# ===========================================================================
# TestDefaults -- every setting has a documented default value
# ===========================================================================

class TestDefaults:
    """At first run (no config file exists), every setting must return its
    documented default.  If a default changes accidentally, any simulation
    that was set up without changing that setting will behave differently.
    """

    def test_complab_executable_default(self, cfg):
        assert cfg.get("complab_executable") == ""

    def test_default_project_dir_default(self, cfg):
        assert cfg.get("default_project_dir") == ""

    def test_auto_save_default_is_false(self, cfg):
        assert cfg.get("auto_save") is False

    def test_auto_save_interval_default(self, cfg):
        assert cfg.get("auto_save_interval") == 300

    def test_font_size_default(self, cfg):
        assert cfg.get("font_size") == 9

    def test_theme_default_is_dark(self, cfg):
        assert cfg.get("theme") == "Dark"

    def test_max_console_lines_default(self, cfg):
        assert cfg.get("max_console_lines") == 10000

    def test_recent_projects_default_is_empty_list(self, cfg):
        assert cfg.get("recent_projects") == []

    def test_unknown_key_returns_none(self, cfg):
        assert cfg.get("nonexistent_key_xyz") is None

    def test_unknown_key_returns_custom_default(self, cfg):
        assert cfg.get("nonexistent_key_xyz", "fallback") == "fallback"


# ===========================================================================
# TestGetSet -- set then get returns the new value
# ===========================================================================

class TestGetSet:
    """Setting a value must be reflected immediately in subsequent get() calls."""

    def test_set_string(self, cfg):
        cfg.set("theme", "Light")
        assert cfg.get("theme") == "Light"

    def test_set_integer(self, cfg):
        cfg.set("font_size", 12)
        assert cfg.get("font_size") == 12

    def test_set_boolean_true(self, cfg):
        cfg.set("auto_save", True)
        assert cfg.get("auto_save") is True

    def test_set_boolean_false(self, cfg):
        cfg.set("auto_save", False)
        assert cfg.get("auto_save") is False

    def test_set_path_string(self, cfg):
        cfg.set("complab_executable", "/usr/local/bin/complab")
        assert cfg.get("complab_executable") == "/usr/local/bin/complab"

    def test_set_does_not_affect_other_keys(self, cfg):
        cfg.set("font_size", 14)
        assert cfg.get("theme") == "Dark"  # unchanged

    def test_set_new_key(self, cfg):
        # AppConfig allows arbitrary keys (user-extensible)
        cfg.set("custom_key", "custom_value")
        assert cfg.get("custom_key") == "custom_value"

    def test_overwrite_existing_key(self, cfg):
        cfg.set("font_size", 10)
        cfg.set("font_size", 16)
        assert cfg.get("font_size") == 16


# ===========================================================================
# TestSaveLoad -- persistence across instances
# ===========================================================================

class TestSaveLoad:
    """Changes saved to disk must survive creating a new AppConfig instance.
    This simulates restarting the GUI application.
    """

    def test_save_and_reload_string(self, tmp_path):
        from importlib import reload
        mod = reload(_config_module)

        # Monkeypatch home to tmp_path
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)

        try:
            cfg1 = mod.AppConfig()
            cfg1.set("theme", "Light")
            cfg1.save()

            cfg2 = mod.AppConfig()
            assert cfg2.get("theme") == "Light"
        finally:
            _config_module.Path.home = original_home

    def test_save_and_reload_integer(self, tmp_path):
        from importlib import reload
        mod = reload(_config_module)

        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)

        try:
            cfg1 = mod.AppConfig()
            cfg1.set("font_size", 13)
            cfg1.save()

            cfg2 = mod.AppConfig()
            assert cfg2.get("font_size") == 13
        finally:
            _config_module.Path.home = original_home

    def test_unsaved_changes_not_persisted(self, tmp_path):
        from importlib import reload
        mod = reload(_config_module)

        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)

        try:
            cfg1 = mod.AppConfig()
            cfg1.set("font_size", 99)
            # Intentionally NOT calling cfg1.save()

            cfg2 = mod.AppConfig()
            # cfg2 reads from disk -- should still have the default
            assert cfg2.get("font_size") == 9  # default, not 99
        finally:
            _config_module.Path.home = original_home

    def test_save_creates_directory_if_missing(self, tmp_path):
        from importlib import reload
        mod = reload(_config_module)

        new_home = tmp_path / "new_home"
        new_home.mkdir()

        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: new_home)

        try:
            cfg = mod.AppConfig()
            cfg.set("theme", "Light")
            cfg.save()
            assert (new_home / ".complab_studio" / "config.json").exists()
        finally:
            _config_module.Path.home = original_home

    def test_saved_json_is_valid(self, tmp_path):
        from importlib import reload
        mod = reload(_config_module)

        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)

        try:
            cfg = mod.AppConfig()
            cfg.set("theme", "Light")
            cfg.save()

            config_path = tmp_path / ".complab_studio" / "config.json"
            with open(config_path) as f:
                data = json.load(f)
            assert data["theme"] == "Light"
        finally:
            _config_module.Path.home = original_home


# ===========================================================================
# TestRecentProjects -- MRU list management
# ===========================================================================

class TestRecentProjects:
    """The recent projects list keeps the 10 most recently opened projects,
    with the newest at index 0.  Duplicates are moved to the front rather
    than appearing twice.
    """

    def test_add_one_project(self, cfg):
        cfg.add_recent("/path/to/project.complab")
        recents = cfg.get("recent_projects")
        assert recents[0] == "/path/to/project.complab"

    def test_add_two_projects_newest_first(self, cfg):
        cfg.add_recent("/first.complab")
        cfg.add_recent("/second.complab")
        recents = cfg.get("recent_projects")
        assert recents[0] == "/second.complab"
        assert recents[1] == "/first.complab"

    def test_duplicate_moved_to_front(self, cfg):
        cfg.add_recent("/a.complab")
        cfg.add_recent("/b.complab")
        cfg.add_recent("/a.complab")  # re-open the first project
        recents = cfg.get("recent_projects")
        assert recents[0] == "/a.complab"
        assert recents.count("/a.complab") == 1  # no duplicates

    def test_max_ten_projects_kept(self, cfg):
        for i in range(15):
            cfg.add_recent(f"/project_{i}.complab")
        recents = cfg.get("recent_projects")
        assert len(recents) == 10

    def test_max_ten_keeps_most_recent(self, cfg):
        for i in range(15):
            cfg.add_recent(f"/project_{i}.complab")
        recents = cfg.get("recent_projects")
        # Most recent (project_14) should be at index 0
        assert recents[0] == "/project_14.complab"

    def test_oldest_project_dropped_after_ten(self, cfg):
        for i in range(11):
            cfg.add_recent(f"/project_{i}.complab")
        recents = cfg.get("recent_projects")
        # project_0 (the oldest) should have been dropped
        assert "/project_0.complab" not in recents

    def test_add_recent_saves_to_disk(self, tmp_path):
        """add_recent() must call save() internally."""
        from importlib import reload
        mod = reload(_config_module)

        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)

        try:
            cfg1 = mod.AppConfig()
            cfg1.add_recent("/my_project.complab")

            cfg2 = mod.AppConfig()
            assert "/my_project.complab" in cfg2.get("recent_projects")
        finally:
            _config_module.Path.home = original_home

    def test_empty_list_on_fresh_config(self, cfg):
        assert cfg.get("recent_projects") == []


# ===========================================================================
# TestMalformedJSON -- graceful handling of corrupted config files
# ===========================================================================

class TestMalformedJSON:
    """If config.json is corrupted (e.g. partially written during a crash),
    AppConfig must fall back to defaults rather than raising an exception.
    A corrupted config file must never prevent the GUI from starting.
    """

    def _write_bad_config(self, tmp_path, content):
        cfg_dir = tmp_path / ".complab_studio"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "config.json").write_text(content)

    def test_malformed_json_falls_back_to_defaults(self, tmp_path):
        self._write_bad_config(tmp_path, "{ this is not valid json }")

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            # Should fall back to default, not raise
            assert cfg.get("theme") == "Dark"
        finally:
            _config_module.Path.home = original_home

    def test_truncated_json_falls_back_to_defaults(self, tmp_path):
        self._write_bad_config(tmp_path, '{"theme": "Light", "font_si')

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            assert cfg.get("theme") == "Dark"
        finally:
            _config_module.Path.home = original_home

    def test_empty_json_file_falls_back_to_defaults(self, tmp_path):
        self._write_bad_config(tmp_path, "")

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            assert cfg.get("font_size") == 9
        finally:
            _config_module.Path.home = original_home

    def test_wrong_type_json_falls_back_to_defaults(self, tmp_path):
        # Valid JSON but wrong top-level type (list instead of dict)
        self._write_bad_config(tmp_path, "[1, 2, 3]")

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            # .update() on a list would raise TypeError -- should be handled
            assert isinstance(cfg.get("theme"), str)
        finally:
            _config_module.Path.home = original_home


# ===========================================================================
# TestMissingConfigFile -- no config file at all (fresh install)
# ===========================================================================

class TestMissingConfigFile:
    """On a fresh install, ~/.complab_studio/config.json doesn't exist.
    AppConfig must start up cleanly with all defaults.
    """

    def test_no_config_file_starts_with_defaults(self, tmp_path):
        # tmp_path is clean -- no .complab_studio directory
        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            assert cfg.get("theme") == "Dark"
            assert cfg.get("font_size") == 9
            assert cfg.get("recent_projects") == []
        finally:
            _config_module.Path.home = original_home

    def test_no_config_directory_starts_with_defaults(self, tmp_path):
        empty_home = tmp_path / "clean_home"
        empty_home.mkdir()

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: empty_home)
        try:
            cfg = mod.AppConfig()
            assert cfg.get("auto_save") is False
        finally:
            _config_module.Path.home = original_home


# ===========================================================================
# TestPartialConfig -- config file with only some keys set
# ===========================================================================

class TestPartialConfig:
    """A config file from an older version of the GUI may only contain some
    keys.  The missing keys should fall back to defaults, not cause KeyError.
    """

    def _write_partial_config(self, tmp_path, data):
        cfg_dir = tmp_path / ".complab_studio"
        cfg_dir.mkdir(parents=True, exist_ok=True)
        (cfg_dir / "config.json").write_text(json.dumps(data))

    def test_partial_config_merges_with_defaults(self, tmp_path):
        # Only 'theme' is set -- everything else should use defaults
        self._write_partial_config(tmp_path, {"theme": "Light"})

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            assert cfg.get("theme") == "Light"       # from file
            assert cfg.get("font_size") == 9         # from default
            assert cfg.get("auto_save") is False      # from default
        finally:
            _config_module.Path.home = original_home

    def test_extra_keys_in_config_are_preserved(self, tmp_path):
        # An unknown key in the file should be preserved (forward compatibility)
        self._write_partial_config(tmp_path, {"future_feature": "enabled"})

        from importlib import reload
        mod = reload(_config_module)
        original_home = _config_module.Path.home
        _config_module.Path.home = staticmethod(lambda: tmp_path)
        try:
            cfg = mod.AppConfig()
            # The unknown key should still be retrievable
            assert cfg.get("future_feature") == "enabled"
        finally:
            _config_module.Path.home = original_home
