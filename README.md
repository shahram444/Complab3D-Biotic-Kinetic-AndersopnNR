# CompLaB3D

**A 3D Pore-Scale Biogeochemical Reactive Transport Simulator**

CompLaB3D couples Lattice Boltzmann Method (LBM) fluid flow and
advection-diffusion with biotic/abiotic kinetics, cellular-automata biofilm
growth, and Newton-Raphson/Anderson equilibrium solving at the pore scale.

It ships with **CompLaB Studio 2.1**, a Python GUI for configuring scenarios,
generating 3D geometries, running the solver, and visualising results.

---

## Features

- **Navier-Stokes flow** via LBM (Palabos 2.3.0)
- **Advection-diffusion** for multiple dissolved substrates
- **Biotic kinetics** (Monod model) for sessile and planktonic microbes
- **Abiotic kinetics** (first-order decay, bimolecular reactions)
- **Equilibrium chemistry** solved with Newton-Raphson + Anderson acceleration
- **Cellular-automata biofilm** growth and detachment
- **Operator splitting** architecture: Transport, Kinetics, Equilibrium
- **9 pluggable scenario templates** from flow-only to fully coupled
- **MPI parallel** execution
- **VTI output** for ParaView visualisation
- **CompLaB Studio GUI** with XML editor, 3D viewer, and solver manager

## Repository Layout

```
CompLaB3D/
  src/              C++ solver source (complab.cpp)
  kinetics/         9 kinetics template folders with .hh headers
  GUI/              CompLaB Studio 2.1 (Python/PySide6)
    src/core/       Template engine, XML builder, kinetics code-gen
    src/panels/     GUI panels (substrate, microbe, solver, geometry, ...)
    tests/          93 automated tests (pytest + pytest-qt)
  docs/             Technical guide, user tutorial, geometry tutorial
  tools/            geometry_generator.py utility
  test_cases/       Abiotic and biotic example configurations
  CMakeLists.txt    CMake build for the C++ solver
```

## Quick Start

### 1. Build the C++ Solver

**Prerequisites:** C++11 compiler (GCC 9+, Clang 10+, or MSVC 2019+),
CMake 3.5+, MPI (OpenMPI or MPICH), Palabos 2.3.0.

```bash
# Clone with Palabos in versionControl/palabos-v2.3.0, then:
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

The executable `complab` is placed in the project root.

To point CMake at a custom Palabos location:

```bash
cmake .. -DPALABOS_ROOT=/path/to/palabos-v2.3.0
```

### 2. Install the GUI

**Prerequisites:** Python 3.10+

```bash
cd GUI
pip install -e ".[dev]"
complab-studio          # launch the GUI
# or:  python -m src.main
```

### 3. Run a Simulation

1. Open CompLaB Studio and pick a template (e.g. *Biotic Sessile*).
2. Configure substrates, microbes, and solver parameters.
3. Export the XML and kinetics header.
4. Run the solver from the GUI's Solver panel or from the terminal:

```bash
mpirun -np 4 ./complab CompLaB.xml
```

Results are written to `output/` as VTI files viewable in ParaView.

## Simulation Templates

| # | Template | Type | Description |
|---|----------|------|-------------|
| 1 | flow_only | Abiotic | Pure Navier-Stokes flow, no chemistry |
| 2 | diffusion_only | Abiotic | Pure diffusion (Pe = 0), no reactions |
| 3 | tracer_transport | Abiotic | Flow + passive tracer, no reactions |
| 4 | abiotic_reaction | Abiotic | First-order decay: A to Product |
| 5 | abiotic_equilibrium | Abiotic | Carbonate equilibrium (no kinetic rxn) |
| 6 | biotic_sessile | Biotic | Sessile biofilm with CA solver, 1 microbe |
| 7 | biotic_planktonic | Biotic | Planktonic bacteria via LBM, 1 microbe |
| 8 | biotic_sessile_planktonic | Biotic | Sessile + planktonic, 2 microbes |
| 9 | coupled_biotic_abiotic | Coupled | Biofilm + abiotic decay simultaneously |

## Testing

```bash
cd GUI
python -m pytest tests/ -v
```

All 93 tests run without the C++ binary (mocked solver). They cover template
generation, XML building/parsing, kinetics code generation, cross-validation,
and end-to-end pipeline flows.

## Documentation

| Document | Contents |
|----------|----------|
| [Technical Guide](docs/CompLaB3D_Technical_Guide.md) | Monod kinetics, CA biofilm, equilibrium solver internals |
| [User Tutorial](docs/CompLaB3D_User_Tutorial.md) | Step-by-step GUI walkthrough |
| [Geometry Tutorial](docs/Geometry_Generator_Tutorial.md) | 3D pore geometry generation |
| [GUI README](GUI/README.md) | Reviewer/tester quick-start for the Python GUI |
| [Kinetics README](kinetics/README.md) | Details on each of the 9 scenario templates |

## How to Cite

If you use CompLaB3D in your research, please cite:

```bibtex
@software{complab3d,
  author    = {Asgari, Shahram},
  title     = {{CompLaB3D}: A 3D Pore-Scale Biogeochemical Reactive
               Transport Simulator},
  version   = {2.1.0},
  url       = {https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR},
  license   = {GPL-3.0}
}
```

See also [CITATION.cff](CITATION.cff) for machine-readable citation metadata.

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
before opening a pull request. All participants are expected to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## License

CompLaB3D is released under the
[GNU General Public License v3.0](LICENSE).
