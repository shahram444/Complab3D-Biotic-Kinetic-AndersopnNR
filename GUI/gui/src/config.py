"""
Configuration management for CompLaB Studio
"""

import os
import json
from pathlib import Path


class Config:
    """Application configuration manager"""
    
    DEFAULT_CONFIG = {
        "complab_executable": "",
        "paraview_path": "paraview",
        "default_project_dir": str(Path.home() / "CompLaB_Projects"),
        "recent_projects": [],
        "theme": "dark",
        "font_size": 10,
        "auto_save": True,
        "auto_save_interval": 300,  # seconds
        "show_welcome": True,
        "max_recent_projects": 10,
        "console_max_lines": 10000,
        "vtk_background_color": [0.1, 0.1, 0.15],
        "default_units": {
            "length": "um",
            "time": "s",
            "concentration": "mmol/L",
            "biomass": "kgDW/m3"
        }
    }
    
    def __init__(self):
        self.config_dir = Path.home() / ".complab_studio"
        self.config_file = self.config_dir / "config.json"
        self.config = dict(self.DEFAULT_CONFIG)
        self._load()
        
    def _load(self):
        """Load configuration from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    saved_config = json.load(f)
                    self.config.update(saved_config)
            except Exception as e:
                print(f"Warning: Failed to load config: {e}")
                
    def save(self):
        """Save configuration to file"""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
            
    def get(self, key, default=None):
        """Get configuration value"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """Set configuration value"""
        self.config[key] = value
        
    def reset(self):
        """Reset to default configuration"""
        self.config = dict(self.DEFAULT_CONFIG)
        self.save()
