# CompLaB Studio 2.1

GUI front-end for the CompLaB 3D pore-scale reactive transport simulator.
Built with PySide6 (Qt6), VTK for 3D visualization, and Matplotlib for
convergence plotting.

## Quick Start

```bash
# 1. Install dependencies
cd GUI
pip install -r requirements.txt

# 2. Launch
python main.py
```

## For Reviewers / Testers

### One-command setup

```bash
cd GUI
pip install -e ".[dev]"   # installs runtime + test dependencies
python main.py            # launch the GUI
```

### Run the test suite (no solver binary needed)

Tests use mock solvers written in Python, so you do **not** need the compiled
`complab` executable.

```bash
cd GUI
python -m pytest tests/ -v
```

Individual suites:

```bash
python -m pytest tests/test_pipeline_e2e.py -v       # data-flow pipeline
python -m pytest tests/test_simulation_runner.py -v   # subprocess lifecycle
```

Verbose diagnostics (writes to stderr):

```bash
COMPLAB_DEBUG=1 python -m pytest tests/ -v -s
```

### Load a sample project

The repository ships with ready-to-open project files:

| File | Description |
|------|-------------|
| `flow-only.complab` | Pure Navier-Stokes flow |
| `difusion-only.complab` | Diffusion without advection |
| `abiotic.complab` | Abiotic transport with equilibrium chemistry |
| `abio-firstdecay.complab` | First-order decay reaction |

Open any of them from **File > Open** or pass on the command line:

```bash
python main.py flow-only.complab
```

### Sample geometry data

Pre-built `.dat` geometry files are in `GUI/DAT/`:

```
DAT/
├── input/geometry.dat              # 50x30x30 channel (porosity 75%)
├── abiotic-paralel-plate/          # parallel-plate variants
├── abiotic-rctangular/             # rectangular channel variants
└── abiotic-reaction-chamb/         # reaction chamber variants
```

## Project Structure

```
GUI/
├── main.py                  # Entry point (splash screen, theme, launch)
├── pyproject.toml           # Package metadata and dev dependencies
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Test/dev dependencies
│
├── src/
│   ├── main_window.py       # 4-panel COMSOL-style layout
│   ├── config.py            # Persistent settings (~/.complab_studio/)
│   ├── core/
│   │   ├── project.py       # Data model (domain, fluid, chemistry, ...)
│   │   ├── project_manager.py  # XML/JSON I/O
│   │   ├── simulation_runner.py # QThread subprocess manager
│   │   ├── templates.py     # 9 built-in simulation templates
│   │   ├── kinetics_templates.py
│   │   └── xml_diagnostic.py
│   ├── dialogs/             # New-project wizard, geometry creator, etc.
│   ├── panels/              # 12 right-side settings panels
│   └── widgets/             # Model tree, VTK viewer, console, plots
│
├── styles/
│   ├── theme.qss            # Dark theme (default)
│   └── light.qss            # Light theme
│
├── tests/
│   ├── conftest.py          # Offscreen Qt platform setup
│   ├── test_pipeline_e2e.py # End-to-end data-flow tests
│   └── test_simulation_runner.py # Subprocess lifecycle tests
│
├── DAT/                     # Sample geometry files
└── *.complab                # Sample project files
```

## Requirements

- Python >= 3.10
- PySide6 >= 6.5.0
- NumPy >= 1.24.0
- VTK >= 9.2.0
- Matplotlib >= 3.7.0

For testing add: `pytest >= 7.4.0`, `pytest-qt >= 4.2.0`

## Environment Notes

- Tests run in **offscreen** mode (`QT_QPA_PLATFORM=offscreen`) so no display
  server is required.
- Logs are written to `~/.complab_studio/complab_gui.log`.
- Settings are stored in `~/.complab_studio/config.json`.
