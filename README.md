# CompLaB3D

**Three-Dimensional Pore-Scale Biogeochemical Reactive Transport Solver**

[![C++ Tests](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/actions/workflows/cpp-tests.yml/badge.svg)](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/actions/workflows/cpp-tests.yml)
[![GUI Tests](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/actions/workflows/gui-tests.yml/badge.svg)](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/actions/workflows/gui-tests.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

CompLaB3D couples a Lattice Boltzmann Method (LBM) flow and transport solver
with Monod-based microbial kinetics, abiotic chemical reactions, and an
Anderson-accelerated equilibrium chemistry solver to simulate biogeochemical
processes in 3D porous media at the pore scale.

## Features

- **LBM Flow Solver**: D3Q19 Navier-Stokes for incompressible flow in complex pore geometries
- **LBM Transport Solver**: D3Q7 advection-diffusion for multiple dissolved species
- **Biotic Kinetics**: Monod saturation model for microbial growth, substrate consumption, and CO2 production
- **Abiotic Kinetics**: First-order decay, bimolecular, and reversible reactions
- **Equilibrium Chemistry**: Newton-Raphson + Anderson acceleration for aqueous speciation
- **Biofilm Model**: Cellular automaton (CA) for sessile biofilm growth and expansion with flow feedback
- **Planktonic Bacteria**: LBM-transported suspended microbes
- **CompLaB Studio GUI**: Cross-platform PySide6 interface for project setup, code generation, and simulation management
- **MPI Parallel**: Distributed-memory parallelism via Palabos

## Quick Start

### Prerequisites

- C++11 compiler (GCC 7+ or Clang 5+)
- [Palabos](https://palabos.unige.ch/) LBM library
- MPI implementation (OpenMPI or MPICH)
- CMake 3.14+ (for tests)
- Python 3.10+ (for GUI and Python tests)

### Build the Solver

```bash
cd src
make
```

### Run a Simulation

```bash
# Serial
./src/complab3d CompLaB.xml

# Parallel (4 processes)
mpirun -np 4 ./src/complab3d CompLaB.xml
```

### Use CompLaB Studio (GUI)

```bash
cd GUI
pip install -e .
complab-studio
```

The GUI provides visual configuration for all nine simulation modes, automatic
kinetics header generation, MPI launch management, and post-processing.

## Repository Structure

```
CompLaB3D/
├── src/                        # C++ solver source (~5,800 lines)
│   ├── complab.cpp             # Main 10-phase solver
│   ├── complab_functions.hh    # I/O, domain setup, pressure gradient
│   ├── complab3d_processors_part1.hh  # Kinetics, biomass expansion
│   ├── complab3d_processors_part2.hh  # Mask updates, FD diffusion
│   ├── complab3d_processors_part3.hh  # Geometry, initialization
│   └── complab3d_processors_part4_eqsolver.hh  # Equilibrium solver
├── GUI/                        # CompLaB Studio (PySide6)
│   ├── main.py                 # Entry point
│   ├── src/                    # Application source
│   └── tests/                  # 275+ pytest tests
├── tests/
│   ├── cpp/                    # 130 GoogleTest unit tests
│   └── run_validation.py       # Analytical validation runner
├── test_cases/
│   ├── abiotic/                # 5 analytical validation cases
│   └── biotic/                 # Biofilm test case
├── docs/                       # User tutorial, technical guide
├── paper/                      # JOSS paper (paper.md, paper.bib)
├── tools/                      # Geometry generator
├── defineKinetics.hh           # Default biotic kinetics header
├── defineAbioticKinetics.hh    # Default abiotic kinetics header
├── CompLaB.xml                 # Biofilm configuration template
└── CompLaB_planktonic.xml      # Planktonic configuration template
```

## Testing

CompLaB3D has 400+ automated tests. See [TESTING.md](TESTING.md) for the
complete guide.

### Run All Tests

```bash
# 1. C++ unit tests (130 tests, ~20 s)
cd tests/cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
cd ../../..

# 2. GUI / Python tests (275+ tests, ~30 s)
cd GUI
pip install -e ".[dev]"
python -m pytest tests/ -v
cd ..

# 3. Analytical validation dry-run
python tests/run_validation.py --dry-run
```

### What Is Tested

| Component | Tests | Framework |
|-----------|-------|-----------|
| LBM stability checks | 14 | GoogleTest |
| Abiotic kinetics | 8 | GoogleTest |
| Biotic (Monod) kinetics | 11 | GoogleTest |
| Planktonic kinetics | 17 | GoogleTest |
| Equilibrium solver | 27 | GoogleTest |
| Diagnostics & mass balance | 21 | GoogleTest |
| LBM utilities (D3Q7, Darcy, etc.) | 30 | GoogleTest |
| GUI panels & widgets | 120+ | pytest-qt |
| Kinetics code generation | 86 | pytest |
| XML/JSON serialization | 21 | pytest |
| Simulation runner lifecycle | 18 | pytest |
| End-to-end pipeline | 93 | pytest |
| Analytical validation | 5 | Python + solver |

## Documentation

- **[User Tutorial](docs/CompLaB3D_User_Tutorial.md)** -- Step-by-step guide from installation to running simulations
- **[Technical Guide](docs/CompLaB3D_Technical_Guide.md)** -- Kinetics models, CA algorithm, equilibrium solver theory
- **[Geometry Generator Tutorial](docs/Geometry_Generator_Tutorial.md)** -- Creating pore geometries from images
- **[Testing Guide](TESTING.md)** -- How to run tests + what each test does (with science)

## Simulation Modes

CompLaB3D supports nine simulation configurations:

| Mode | Flow | Transport | Biotic | Abiotic | Equilibrium |
|------|------|-----------|--------|---------|-------------|
| Flow only | Yes | -- | -- | -- | -- |
| Diffusion only | -- | Yes | -- | -- | -- |
| Tracer transport | Yes | Yes | -- | -- | -- |
| Abiotic reaction | Yes | Yes | -- | Yes | -- |
| Abiotic equilibrium | Yes | Yes | -- | -- | Yes |
| Biotic sessile | Yes | Yes | Yes (CA) | -- | -- |
| Biotic planktonic | Yes | Yes | Yes (LBM) | -- | -- |
| Sessile + planktonic | Yes | Yes | Yes (both) | -- | -- |
| Coupled biotic-abiotic | Yes | Yes | Yes | Yes | Optional |

## Citation

If you use CompLaB3D in your research, please cite:

```bibtex
@article{Asgari:2026,
  title   = {{CompLaB3D}: A Three-Dimensional Pore-Scale Reactive Transport
             Solver Coupling Lattice Boltzmann Methods with Biogeochemical
             Kinetics},
  author  = {Asgari, Shahram and Meile, Christof},
  journal = {Journal of Open Source Software},
  year    = {2026},
  doi     = {pending}
}
```

## Contributing

We welcome contributions. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for
guidelines.

## License

CompLaB3D is released under the [GNU General Public License v3.0](LICENSE).

## Acknowledgements

CompLaB3D is developed at the Meile Lab, Department of Marine Sciences,
University of Georgia. The solver is built on the [Palabos](https://palabos.unige.ch/)
open-source LBM library.
