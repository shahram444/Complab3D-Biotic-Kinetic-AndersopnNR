# Installation Guide

CompLaB3D has two components: a C++ solver and a Python GUI (CompLaB Studio).
You can install either or both depending on your needs.

## Prerequisites

### C++ Solver

| Dependency | Minimum Version | Notes |
|-----------|----------------|-------|
| C++ compiler | GCC 9+, Clang 10+, or MSVC 2019+ | C++11 support required |
| CMake | 3.5+ | Build system |
| MPI | OpenMPI 4+ or MPICH 3+ | Parallel execution |
| Palabos | 2.3.0 | LBM library (included in `versionControl/`) |

### Python GUI (CompLaB Studio)

| Dependency | Minimum Version |
|-----------|----------------|
| Python | 3.10+ |
| PySide6 | 6.5.0+ |
| NumPy | 1.24.0+ |
| VTK | 9.2.0+ |
| Matplotlib | 3.7.0+ |

## Installing the C++ Solver

### 1. Clone the repository

```bash
git clone https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR.git
cd Complab3D-Biotic-Kinetic-AndersopnNR
```

### 2. Build with CMake

```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

The executable `complab` is placed in the project root.

### 3. Custom Palabos location (optional)

If Palabos is installed elsewhere:

```bash
cmake .. -DPALABOS_ROOT=/path/to/palabos-v2.3.0 -DCMAKE_BUILD_TYPE=Release
```

### 4. Verify the build

```bash
cd ..
mpirun -np 1 ./complab --help
```

## Installing CompLaB Studio (Python GUI)

### 1. Create a virtual environment (recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or: .venv\Scripts\activate  # Windows
```

### 2. Install the package

```bash
cd GUI
pip install -e ".[dev]"
```

This installs runtime dependencies and test/development tools.

### 3. Launch the GUI

```bash
complab-studio
# or: python -m src.main
# or: python main.py
```

### 4. Run the test suite

Tests do **not** require the compiled C++ solver binary. They use mock
solvers written in Python.

```bash
cd GUI
python -m pytest tests/ -v
```

Expected output: **93 tests passed**.

## Platform-Specific Notes

### Linux (Ubuntu/Debian)

```bash
sudo apt-get install build-essential cmake libopenmpi-dev openmpi-bin
sudo apt-get install python3-dev python3-venv
# For Qt GUI rendering:
sudo apt-get install libegl1 libgl1-mesa-glx
```

### macOS

```bash
brew install cmake open-mpi python@3.12
```

### Windows

- Install Visual Studio 2019+ with C++ workload.
- Install Microsoft MPI from https://docs.microsoft.com/en-us/message-passing-interface/microsoft-mpi
- Install Python 3.10+ from https://python.org

## Running a Simulation

```bash
# From the project root, after building the solver:
mpirun -np 4 ./complab CompLaB.xml
```

Results are written to `output/` as VTI files viewable in ParaView.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `cmake` can't find MPI | Set `MPI_HOME` or install OpenMPI/MPICH |
| Qt platform plugin error | `export QT_QPA_PLATFORM=offscreen` (headless) |
| VTK import error | `pip install vtk>=9.2.0` |
| Tests fail with display error | `QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v` |
