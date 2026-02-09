# CompLaB Studio

**Professional GUI for CompLaB Reactive Transport Simulations**

A comprehensive graphical interface for pore-scale biogeochemical modeling using the lattice Boltzmann method, inspired by OpenFOAM-style simulation tools.

![CompLaB Studio](docs/screenshot.png)

## Features

### 🎯 Project Management
- Create, save, and load simulation projects
- Import existing CompLaB XML configurations
- Project templates for common scenarios
- Recent projects quick access

### 📐 Domain Configuration
- Visual domain setup with 3D preview
- Import geometry from BMP image stacks
- Configurable material numbers
- Grid resolution controls

### ⚗️ Chemistry Setup
- Multiple substrate species support
- Diffusion coefficient configuration
- Boundary condition editor
- Unit conversion helpers

### 🦠 Microbiology Configuration  
- Multiple microbe types
- Monod kinetics editor
- Cellular automata settings
- Custom kinetics code editor

### ⚙️ Solver Settings
- Lattice Boltzmann parameters
- Convergence criteria
- Iteration controls
- I/O configuration

### 🎨 3D Visualization
- Real-time geometry preview
- VTK-based rendering
- Export to ParaView

### 📈 Results Analysis
- Time series plotting
- Spatial profiles
- Data export (CSV, VTK)
- Mass balance tracking

## Installation

### Prerequisites
- Python 3.9 or higher
- CompLaB simulation engine (compiled separately)

### Install from Source

```bash
# Clone the repository
git clone https://github.com/your-repo/complab-studio.git
cd complab-studio

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

### Build Standalone Executable (Windows)

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
python build.py --all

# Find executable in dist/CompLaB_Studio/
```

## Quick Start

1. **Create New Project**: File → New Project
2. **Configure Domain**: Set grid dimensions and import geometry
3. **Add Substrates**: Define chemical species and properties
4. **Configure Microbes**: Set up microbial parameters and kinetics
5. **Set Solver Options**: Configure numerical parameters
6. **Run Simulation**: Click ▶ Run to start
7. **View Results**: Open Results panel to analyze output

## Project Structure

```
CompLaB_GUI/
├── main.py              # Application entry point
├── build.py             # Build script for executables
├── requirements.txt     # Python dependencies
├── src/
│   ├── main_window.py   # Main application window
│   ├── config.py        # Configuration management
│   ├── core/            # Core data structures
│   │   ├── project.py   # Project data models
│   │   ├── project_manager.py  # Load/save/export
│   │   └── simulation_runner.py
│   ├── panels/          # UI panels
│   │   ├── domain_panel.py
│   │   ├── chemistry_panel.py
│   │   ├── microbiology_panel.py
│   │   └── ...
│   ├── dialogs/         # Dialog windows
│   │   ├── new_project_dialog.py
│   │   └── ...
│   └── widgets/         # Custom widgets
│       ├── console_widget.py
│       └── vtk_viewer.py
├── styles/
│   └── main.qss         # Qt stylesheet
├── icons/               # Application icons
└── resources/           # Additional resources
```

## Configuration

### Setting CompLaB Path

1. Go to Edit → Preferences
2. Set the path to your CompLaB executable
3. Optionally set ParaView path for visualization

### Project Files

CompLaB Studio uses two file types:
- `.complab` - Project file (JSON format)
- `.xml` - CompLaB configuration (auto-generated)

## Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| New Project | Ctrl+N |
| Open Project | Ctrl+O |
| Save Project | Ctrl+S |
| Run Simulation | F5 |
| Stop Simulation | Shift+F5 |
| Validate Setup | F6 |
| Preferences | Ctrl+, |
| Toggle Console | Ctrl+` |

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting pull requests.

## License

This project is licensed under the GNU AGPL v3 License - see the LICENSE file for details.

## Acknowledgments

- **CompLaB Core Engine**: University of Georgia & Chungnam National University
- **Contact**: Heewon Jung (hjung@cnu.ac.kr)
- **Repository**: https://bitbucket.org/MeileLab/complab

## Support

- 📖 [Documentation](https://bitbucket.org/MeileLab/complab/wiki)
- 🐛 [Report Issues](https://github.com/your-repo/complab-studio/issues)
- 💬 [Discussions](https://github.com/your-repo/complab-studio/discussions)
