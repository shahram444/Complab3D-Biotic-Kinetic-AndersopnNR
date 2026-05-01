# CompLaB3D

[![Public since](https://img.shields.io/badge/public%20since-2026--02--05-blue)](https://api.github.com/repos/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR)
[![First commit](https://img.shields.io/badge/first%20commit-2026--02--05-green)](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/commit/c51ff499f226b82936b6a57b7a29fbd5d49b54b3)

## Proof of public availability

This repository has been **publicly available on GitHub since 2026-02-05**.
You don't have to take our word for it — every claim below is independently verifiable:

| What | Where to verify it yourself |
|------|------------------------------|
| Repo `created_at` field | [api.github.com/repos/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR](https://api.github.com/repos/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR) — look for `"created_at": "2026-02-05T15:17:47Z"` |
| First commit on GitHub | [`c51ff49` — 2026-02-05](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/commit/c51ff499f226b82936b6a57b7a29fbd5d49b54b3) |
| Full commit history | [Commits page](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/commits/main/) — scroll to the bottom |
| Public-since git tag | [`public-since-2026-02-05`](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/releases/tag/public-since-2026-02-05) |
| Independent web archive | [Wayback Machine snapshots](https://web.archive.org/web/*/github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR) |

**Quick verification from your terminal:**

```bash
# 1. Repo creation date straight from GitHub's API
curl -s https://api.github.com/repos/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR \
  | grep -E '"(created_at|pushed_at|visibility)"'

# 2. Earliest commit in the repo (after cloning)
git clone https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR.git
cd Complab3D-Biotic-Kinetic-AndersopnNR
git log --reverse --format="%ai %h %s" | head -1
# → 2026-02-05 10:18:28 -0500 c51ff49 Add files via upload
```

Expected API response:

```json
{
  "created_at": "2026-02-05T15:17:47Z",
  "visibility": "public",
  "pushed_at": "2026-05-01T06:05:14Z"
}
```

**A 3D Pore-Scale Biogeochemical Reactive Transport Simulator**

CompLaB3D couples Lattice Boltzmann Method (LBM) fluid flow and
advection-diffusion with biotic/abiotic kinetics, cellular-automata biofilm
growth, and Newton-Raphson/Anderson equilibrium solving at the pore scale.

<<<<<<< Updated upstream
It ships with **CompLaB Studio 2.1**, a Python GUI for configuring scenarios,
generating 3D geometries, running the solver, and visualising results.
=======
CompLaB3D is an open-source **three-dimensional pore-scale reactive transport solver** that couples Lattice Boltzmann Method (LBM) fluid flow and solute transport with Monod-based microbial kinetics, user-defined abiotic chemical reactions, an Anderson-accelerated equilibrium chemistry solver, and a cellular automaton (CA) biofilm model — all MPI-parallelised through the [Palabos](https://palabos.unige.ch/) library.

**CompLaB Studio** (v2.1.0) is the companion graphical interface: a COMSOL-style 4-panel desktop application built with PySide6 that handles the complete workflow from project setup and geometry generation through simulation launch and 3D post-processing — without ever touching a text editor.
>>>>>>> Stashed changes

---

## Features

<<<<<<< Updated upstream
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
    tests/          275 automated tests (pytest + pytest-qt)
  docs/             Technical guide, user tutorial, geometry tutorial
  tools/            geometry_generator.py utility
  test_cases/       Abiotic and biotic example configurations
  CMakeLists.txt    CMake build for the C++ solver
=======
1. [Overview and Solver Pipeline](#1-overview-and-solver-pipeline)
2. [Repository Structure](#2-repository-structure)
3. [Prerequisites](#3-prerequisites)
4. [Building the Solver from Source](#4-building-the-solver-from-source)
5. [Standalone HPC Package (ComapLB3D)](#5-standalone-hpc-package-comaplb3d)
6. [Running the Solver Without the GUI](#6-running-the-solver-without-the-gui)
7. [Running CompLaB Studio (GUI)](#7-running-complab-studio-gui)
8. [XML Configuration Reference](#8-xml-configuration-reference)
9. [Output Files](#9-output-files)
10. [Test Suite](#10-test-suite)
11. [Analytical Validation Cases](#11-analytical-validation-cases)
12. [Documentation](#12-documentation)
13. [For JOSS Editors and Reviewers](#13-for-joss-editors-and-reviewers)
14. [Citation](#14-citation)
15. [License](#15-license)
16. [Acknowledgements](#16-acknowledgements)

---

## 1. Overview and Solver Pipeline

CompLaB3D executes a **10-phase pipeline** on every simulation run:

| Phase | Description |
|-------|-------------|
| 1 | Load XML configuration and validate all inputs |
| 2 | Geometry setup and preprocessing (solid/pore/biofilm classification) |
| 3 | Navier-Stokes flow field (D3Q19 LBM): initial pressure → permeability → target velocity → corrected pressure → final flow → stability checks (Ma, CFL, τ) |
| 4 | Reactive transport lattice setup — D3Q7 ADE for each substrate and planktonic biomass species |
| 5 | NS-ADE velocity field coupling |
| 6 | **Main simulation loop**: collision → kinetic reactions (Monod/abiotic) → equilibrium chemistry (Anderson-NR PCF) → biomass redistribution (CA/FD) → flow update if geometry changed → streaming |
| 7 | Write VTI / CHK output files |
| 8 | Breakthrough curve analysis and spatial moment calculations |
| 9 | Write summary CSV files |
| 10 | Finalise and clean up |

**Simulation modes** (set in `CompLaB.xml`):

| Mode | `biotic_mode` | `enable_kinetics` | `enable_abiotic_kinetics` |
|------|:---:|:---:|:---:|
| Flow only | false | false | false |
| Tracer transport | false | false | false |
| Abiotic reactions | false | false | true |
| Biotic (sessile CA) | true | true | false |
| Biotic (planktonic) | true | true | false |
| Full coupled | true | true | true |

---

## 2. Repository Structure

```
CompLaB3D/                                       # Repository root
│
├── src/                                         # C++ solver source
│   ├── complab.cpp                              # Main entry point (10-phase pipeline)
│   ├── complab_functions.hh                     # XML parser, geometry I/O, BTC analysis
│   ├── complab3d_processors.hh                  # LBM collision/streaming processors
│   ├── complab3d_processors_part1.hh            # NS flow processors
│   ├── complab3d_processors_part2.hh            # ADE transport processors
│   ├── complab3d_processors_part3.hh            # Biofilm CA and FD processors
│   ├── complab3d_processors_part4_eqsolver.hh   # Anderson-NR equilibrium solver
│   └── complab3d_processors_part4_eqsolver_NR_reserve.hh  # NR reference implementation
│
├── GUI/                                         # CompLaB Studio graphical interface
│   ├── main.py                                  # Entry point — splash screen + launch
│   ├── src/                                     # Active GUI source (v2.1.0)
│   │   ├── main_window.py                       # COMSOL-style 4-panel main window
│   │   ├── config.py                            # App configuration (theme, font, paths)
│   │   ├── core/
│   │   │   ├── project.py                       # CompLaBProject data model
│   │   │   ├── project_manager.py               # Save/load .complab project files
│   │   │   ├── simulation_runner.py             # Subprocess launcher + real-time monitoring
│   │   │   ├── templates.py                     # Six project templates
│   │   │   ├── kinetics_templates.py            # Built-in rate-law code generators
│   │   │   └── xml_diagnostic.py                # Crash diagnostic on solver failure
│   │   ├── panels/                              # 13 configuration panels
│   │   │   ├── base_panel.py                    # Abstract base class for all panels
│   │   │   ├── general_panel.py                 # Project setup, template selection
│   │   │   ├── domain_panel.py                  # Grid dimensions, geometry file
│   │   │   ├── fluid_panel.py                   # Flow parameters, pressure gradient
│   │   │   ├── chemistry_panel.py               # Substrates, diffusion coefficients, BCs
│   │   │   ├── equilibrium_panel.py             # Aqueous speciation (log K, stoichiometry)
│   │   │   ├── microbiology_panel.py            # Microbial populations, Monod parameters
│   │   │   ├── solver_panel.py                  # Iterations, output frequency, stability
│   │   │   ├── io_panel.py                      # Paths: executable, output directory
│   │   │   ├── parallel_panel.py                # MPI: enable, number of processes, mpirun path
│   │   │   ├── run_panel.py                     # Pre-flight validation + launch + monitoring
│   │   │   ├── postprocess_panel.py             # Results viewer, time series, ParaView
│   │   │   └── sweep_panel.py                   # Parameter sweep configuration
│   │   ├── dialogs/
│   │   │   ├── new_project_dialog.py            # Template picker
│   │   │   ├── kinetics_editor_dialog.py        # Code editor with syntax highlighting
│   │   │   ├── geometry_creator_dialog.py       # Geometry generator (7 medium types)
│   │   │   ├── preferences_dialog.py            # Theme, font, paths
│   │   │   └── about_dialog.py
│   │   └── widgets/
│   │       ├── model_tree.py                    # Left-panel navigation tree
│   │       ├── vtk_viewer.py                    # Embedded VTK 3D viewer
│   │       ├── console_widget.py                # Color-coded console output
│   │       ├── convergence_plot.py              # Real-time residual plot
│   │       ├── geometry_preview.py              # 2D geometry preview widget
│   │       └── collapsible_section.py
│   ├── tests/                                   # pytest test suite (7 test files)
│   │   ├── test_gui_panels.py
│   │   ├── test_kinetics.py
│   │   ├── test_pipeline_e2e.py
│   │   ├── test_project_model.py
│   │   ├── test_simulation_runner.py
│   │   ├── test_templates.py
│   │   └── test_xml_io.py
│   ├── pyproject.toml                           # Package metadata (setuptools)
│   ├── requirements.txt                         # Runtime dependencies
│   └── requirements-dev.txt                     # Development/test dependencies
│
├── ComapLB3D/                                   # Standalone HPC package (see Section 5)
│   ├── src/                                     # C++ solver source (identical to root src/)
│   ├── versionControl/                          # Palabos library container
│   │   └── palabos-v2.3.0/                     # Bundled Palabos (pre-compiled, do not modify)
│   ├── CompLaB.xml                              # Simulation template
│   ├── defineKinetics.hh                        # Biotic kinetics (edit and recompile)
│   ├── defineAbioticKinetics.hh                 # Abiotic kinetics (edit and recompile)
│   ├── CMakeLists.txt                           # Build system (see §5.3 for path adaptation)
│   ├── comp.sh                                  # SLURM job script (UGA Sapelo2)
│   ├── input/                                   # Geometry input (geometry.dat)
│   ├── output/                                  # Simulation output
│   └── build/                                   # CMake build directory
│
├── tests/                                       # C++ unit tests + analytical validation
│   ├── README.md                                # Test documentation for reviewers
│   ├── cpp/                                     # 256 C++ GoogleTest unit tests (no Palabos needed)
│   │   ├── CMakeLists.txt                       # Fetches GoogleTest v1.14 automatically
│   │   ├── plb_shim.h                           # Palabos-free shim (enables Palabos-free build)
│   │   ├── complab3d_processors_part4_eqsolver_standalone.hh  # Standalone eq-solver header
│   │   ├── test_stability.cpp / _extended.cpp
│   │   ├── test_abiotic_kinetics.cpp / _extended.cpp
│   │   ├── test_biotic_kinetics.cpp / _extended.cpp
│   │   ├── test_planktonic_kinetics.cpp / _extended.cpp
│   │   ├── test_eq_solver.cpp / _extended.cpp
│   │   ├── test_diagnostics.cpp
│   │   └── test_lbm_utils.cpp / _extended.cpp
│   └── run_validation.py                        # Analytical validation runner
│
├── test_cases/
│   ├── abiotic/                                 # 5 analytical validation cases
│   │   ├── README.md                            # Full description with expected values
│   │   ├── defineAbioticKinetics_test2.hh       # Kinetics header for test 2
│   │   ├── defineAbioticKinetics_test3.hh       # Kinetics header for test 3
│   │   ├── defineAbioticKinetics_test4.hh       # Kinetics header for test 4
│   │   ├── defineAbioticKinetics_test5.hh       # Kinetics header for test 5
│   │   ├── test1_pure_diffusion.xml
│   │   ├── test2_first_order_decay.xml
│   │   ├── test3_bimolecular.xml
│   │   ├── test4_reversible.xml
│   │   └── test5_decay_chain.xml
│   └── biotic/
│       ├── CompLaB.xml                          # Biofilm simulation example
│       └── defineKinetics.hh                    # Monod kinetics for the biofilm case
│
├── docs/
│   ├── CompLaB3D_User_Tutorial.md               # Step-by-step tutorial
│   ├── CompLaB3D_Technical_Guide.md             # Mathematical formulation and algorithms
│   └── Geometry_Generator_Tutorial.md
│
├── paper/
│   ├── paper.md                                 # JOSS manuscript
│   ├── paper.bib                                # Bibliography
│   ├── paper.pdf                                # Compiled manuscript PDF
│   ├── figure1.png                              # Solver pipeline flowchart
│   ├── figure2.png                              # GUI workflow flowchart
│   └── Appendices/                              # Mathematical appendices A, B, C
│
├── tools/
│   └── geometry_generator.py                    # Standalone geometry creation utility
│
├── .github/workflows/
│   ├── cpp-tests.yml                            # CI: C++ unit tests (Ubuntu, auto)
│   ├── gui-tests.yml                            # CI: Python GUI tests (Python 3.10–3.12)
│   └── draft-pdf.yml                            # CI: JOSS paper PDF compilation
│
├── defineKinetics.hh                            # Default biotic kinetics (user-editable)
├── defineAbioticKinetics.hh                     # Default abiotic kinetics (user-editable)
├── CompLaB.xml                                  # Biofilm simulation template
├── CompLaB_planktonic.xml                       # Planktonic simulation template
├── CITATION.cff                                 # Machine-readable citation
├── codemeta.json                                # Software metadata
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── HOW_TO_RUN_TESTS.txt                         # Quick-start test instructions
├── JOSS_CHECKLIST.md                            # Submission checklist
├── TESTING.md                                   # Detailed testing guide
└── LICENSE                                      # GNU AGPL v3
>>>>>>> Stashed changes
```

## Quick Start

### 1. Build the C++ Solver

<<<<<<< Updated upstream
**Prerequisites:** C++11 compiler (GCC 9+, Clang 10+, or MSVC 2019+),
CMake 3.5+, MPI (OpenMPI or MPICH), Palabos 2.3.0.

```bash
# Clone with Palabos in versionControl/palabos-v2.3.0, then:
mkdir build && cd build
=======
### 3.1 Solver (C++ — required to run simulations)

| Requirement | Minimum version | Notes |
|-------------|----------------|-------|
| C++ compiler | GCC 7+ or Clang 5+ | Must support C++11 |
| [Palabos](https://palabos.unige.ch/) | 2.2+ | LBM library (AGPL-3.0). **Required at compile time only** |
| OpenMPI or MPICH | OpenMPI 4+ / MPICH 3+ | Required for parallel runs |
| GNU Make or CMake | Make 3.81+ / CMake 3.14+ | CMake only needed for C++ unit tests |

**Ubuntu / Debian:**
```bash
sudo apt-get update
sudo apt-get install -y g++ openmpi-bin libopenmpi-dev make cmake git
```

**macOS (Homebrew):**
```bash
brew install gcc open-mpi cmake
```

**Download Palabos** (place alongside the repo):
```bash
wget https://gitlab.com/unigespc/palabos/-/archive/v2.3.0/palabos-v2.3.0.tar.gz
tar -xzf palabos-v2.3.0.tar.gz
mv palabos-v2.3.0 palabos
```

### 3.2 GUI — CompLaB Studio (optional)

The GUI is **not required** to run simulations. It is a convenience tool for users who prefer not to edit XML and C++ files by hand.

| Requirement | Minimum version |
|-------------|----------------|
| Python | 3.10+ |
| PySide6 | 6.5+ |
| NumPy | 1.24+ |
| VTK | 9.2+ |
| Matplotlib | 3.7+ |

All Python dependencies install automatically — see Section 7.

---

## 4. Building the Solver from Source

The solver uses a `CMakeLists.txt` at the repository root that links against Palabos.

```bash
# Clone the repository
git clone https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR.git
cd Complab3D-Biotic-Kinetic-AndersopnNR

# Configure — tell CMake where Palabos is
cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DPLB_ROOT=/path/to/palabos

# Build (use -j N for parallel compilation)
cmake --build build --parallel 4
```

This produces the `complab` executable inside `build/`.

> **Tip — quick recompile after editing kinetics:**
> After modifying `defineKinetics.hh` or `defineAbioticKinetics.hh`, just re-run `cmake --build build --parallel 4`. CMake detects the changed header and recompiles only the affected translation units.

---

## 5. Standalone HPC Package (ComapLB3D)

The `JOSS_Submit/ComapLB3D/` folder is a **self-contained, batteries-included package** designed for users who want to run CompLaB3D on an HPC cluster or local Linux machine without managing a separate Palabos installation. Palabos v2.3.0 is **bundled inside the folder** under `versionControl/palabos-v2.3.0/` with a pre-compiled static library (`versionControl/palabos-v2.3.0/build/libpalabos.a`) so that only the CompLaB3D solver itself needs to be compiled.

### 5.1 Folder structure

```
ComapLB3D/
├── CMakeLists.txt               # Build configuration (edit Palabos paths for your system)
├── CompLaB.xml                  # Simulation template — edit before running
├── defineKinetics.hh            # Biotic (Monod) rate expressions — edit and recompile
├── defineAbioticKinetics.hh     # Abiotic rate expressions — edit and recompile
├── comp.sh                      # SLURM job script (configured for UGA Sapelo2)
├── src/                         # CompLaB3D C++ source
├── versionControl/              # Palabos library container
│   └── palabos-v2.3.0/         # Bundled Palabos — do NOT delete or recompile
│       └── build/libpalabos.a  # Pre-compiled static library (GCC 11.3 / foss/2022a)
├── input/                       # Place geometry.dat here before running
├── output/                      # Simulation output written here automatically
└── build/                       # Run cmake from inside this directory
```

> **Do not delete or recompile anything inside `versionControl/palabos-v2.3.0/`.** The pre-compiled library was built for the UGA Sapelo2 cluster (GCC 11.3, foss/2022a toolchain). For other architectures, see §5.3.

### 5.2 Building on UGA Sapelo2 (and compatible clusters)

```bash
# 1. Load required environment modules
module purge
module load foss/2022a
module load CMake/3.24.3-GCCcore-11.3.0

# 2. Configure and compile
cd ComapLB3D/build
cmake ..
make -j8
```

The compiled `complab` binary is placed in `ComapLB3D/` (one level above `build/`), alongside `CompLaB.xml`.

### 5.3 Adapting CMakeLists.txt for other systems

`CMakeLists.txt` contains absolute paths pointing to Palabos on the UGA cluster. To use the bundled copy on any other machine, replace those four lines:

```cmake
# Original (UGA cluster absolute paths) — change these:
# include_directories("/scratch/sa01687/.../palabos-v2.3.0/src")
# ...

# Replace with paths to the bundled copy:
include_directories("../versionControl/palabos-v2.3.0/src")
include_directories("../versionControl/palabos-v2.3.0/externalLibraries")
include_directories("../versionControl/palabos-v2.3.0/externalLibraries/Eigen3")
file(GLOB_RECURSE PALABOS_SRC "../versionControl/palabos-v2.3.0/src/*.cpp")
file(GLOB_RECURSE EXT_SRC    "../versionControl/palabos-v2.3.0/externalLibraries/tinyxml/*.cpp")
```

> **Architecture mismatch:** If the pre-compiled `libpalabos.a` was built for a different CPU or ABI, the linker will fail. In that case, delete `palabos-v2.3.0/build/` and recompile Palabos for your system:
> ```bash
> cd versionControl/palabos-v2.3.0 && mkdir -p build && cd build
> cmake .. -DCMAKE_BUILD_TYPE=Release
> make -j8
> ```
> Then proceed with building CompLaB3D as above.

### 5.4 Configuring and running a simulation

Before running, edit the three files in `ComapLB3D/`:

| File | What to change |
|------|----------------|
| `CompLaB.xml` | Grid size (nx, ny, nz), Péclet number, substrate parameters, iteration counts |
| `defineKinetics.hh` | Monod rate expressions for biotic runs — **requires `make -j8` after editing** |
| `defineAbioticKinetics.hh` | Abiotic chemical rate expressions — **requires `make -j8` after editing** |

Place your geometry file at `input/geometry.dat` (see Section 8 for geometry generation).

**Interactive / local run:**
```bash
# Serial
./complab

# MPI parallel (8 processes)
mpirun -np 8 ./complab
```

**SLURM batch submission:**
```bash
sbatch comp.sh
```

The provided `comp.sh` is pre-configured for the UGA Sapelo2 `meile_p` partition. Edit the SLURM directives to match your cluster's queue name, core count, memory, and wall time:

```bash
#!/bin/bash
#SBATCH --job-name=complb
#SBATCH --partition=meile_p       # change to your partition
#SBATCH --nodes=1
#SBATCH --ntasks=8                # MPI ranks (match to your domain size)
#SBATCH --mem=16gb
#SBATCH --time=4:00:00            # wall time HH:MM:SS
#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.err

module purge
module load foss/2022a            # provides GCC + OpenMPI

cd $SLURM_SUBMIT_DIR
srun ./complab
```

Output VTI files and CSV summaries are written to `output/`.

---

## 6. Running the Solver Without the GUI

This is the recommended approach for HPC clusters, batch jobs, and reproducibility.

### 6.1 Prepare the three required inputs

**a) XML configuration file**

Copy and edit one of the provided templates:
```bash
cp CompLaB.xml my_simulation.xml   # biofilm (biotic) template
# or
cp CompLaB_planktonic.xml my_simulation.xml   # planktonic template
```

The most important settings are in the `<simulation_mode>` block (see Section 8).

**b) Geometry file**

Generate a synthetic pore geometry with the built-in geometry tool:
```bash
cd tools
python geometry_generator.py
# Follow prompts: choose medium type, set dimensions
# Output: input/geometry.dat (binary voxel mask)
```

Or import a segmented micro-CT image stack (BMP/PNG/TIF/JPG) through the same script.

**c) Kinetics headers**

For biotic simulations, edit `defineKinetics.hh` to define your Monod rate expressions.
For abiotic simulations, edit `defineAbioticKinetics.hh`.
These headers are compiled into the solver — **rebuild after every edit**.

### 6.2 Serial run

```bash
./build/complab my_simulation.xml
```

### 6.3 Parallel run (MPI)

```bash
# 4 MPI processes
mpirun -np 4 ./build/complab my_simulation.xml

# SLURM cluster
srun -n 16 ./build/complab my_simulation.xml
```

CompLaB3D uses Palabos domain decomposition — the grid is split automatically across processes. Any number of processes is supported; choose a value that divides the domain dimensions evenly for best efficiency.

### 6.4 Startup output

On launch, the solver prints a stability check report:

```
╔══════════════════════════════════════════════════════════════╗
║              STABILITY CHECK REPORT                          ║
╠══════════════════════════════════════════════════════════════╣
║ Ma = 0.0231 OK   CFL = 0.0400 OK                            ║
║ tau_NS = 0.8000 OK   tau_ADE = 0.7500 OK                    ║
║ Pe_grid = 1.2000 OK                                          ║
╚══════════════════════════════════════════════════════════════╝
```

If any criterion fails, the solver prints a descriptive error and exits before running.

**Stability criteria enforced:**

| Criterion | Requirement | Physical meaning |
|-----------|-------------|-----------------|
| Mach number | Ma < 0.3 (warn) / < 1.0 (hard limit) | Low-velocity incompressible flow |
| CFL | CFL = u_max < 1.0 | Numerical stability of streaming step |
| NS relaxation time | 0.5 < τ_NS < 2.0 | Viscosity physically representable |
| ADE relaxation time | 0.5 < τ_ADE < 2.0 | Diffusivity physically representable |
| Grid Péclet number | Pe_grid < 2.0 (warn) | Advection does not dominate per lattice cell |

---

## 7. Running CompLaB Studio (GUI)

CompLaB Studio is an optional graphical interface for users who prefer not to edit XML and C++ files directly. **The solver must be compiled separately** (Section 4 or 5) before using the GUI to launch simulations.

### 7.1 Install

```bash
cd GUI

# Recommended: install as an editable package
pip install -e .

# Or install runtime dependencies only
pip install -r requirements.txt
```

### 7.2 Launch

```bash
# From the GUI/ directory:
python main.py

# Or, if installed as a package:
complab-studio
```

A splash screen appears for ~3 seconds, then the main window opens.

> **Debug mode:** Set the environment variable `COMPLAB_DEBUG=1` before launching to enable verbose stderr logging alongside the rotating log file at `~/.complab_studio/complab_gui.log`.

### 7.3 Main window layout

The interface uses a **COMSOL-style 4-panel layout** (minimum window size: 1200 × 800 px):

```
┌─────────────────┬──────────────────────────────┬─────────────────────┐
│  Model Builder  │                              │  Configuration      │
│  (navigation    │    VTK 3D Viewer             │  Panel              │
│   tree)         │    (always visible)          │  (context-sensitive)│
│                 │                              │                     │
├─────────────────┴──────────────────────────────┴─────────────────────┤
│  Console output (color-coded)  │  Real-time convergence residual plot │
└────────────────────────────────┴─────────────────────────────────────┘
```

### 7.4 Workflow step by step

1. **New Project** — `File → New Project` → choose one of six templates:

   | Template | Description |
   |----------|-------------|
   | Flow Only | NS solver only, no transport |
   | Flow + Transport | Tracer advection-diffusion |
   | Flow + Transport + Custom Reactions | Abiotic kinetics |
   | Flow + Transport + Microbes | Planktonic microbial transport |
   | Flow + Transport + Reactions + Microbes | Coupled biotic + abiotic |
   | Flow + Transport + Biofilm | Full CA biofilm simulation |

2. **Domain** — set grid dimensions (Nx, Ny, Nz) and porosity target.

3. **Geometry** — generate a synthetic geometry (7 medium types: sphere packs, Gaussian random fields, parallel plates, fibrous media, etc.) or import a segmented micro-CT image stack. Set initial biofilm distribution (14 spatial scenarios available).

4. **Chemistry** — define dissolved substrates: name, diffusion coefficient, initial concentration, boundary conditions (Dirichlet / Neumann).

5. **Equilibrium** *(optional)* — configure aqueous speciation reactions: component names, stoichiometric matrix, log K values.

6. **Microbiology** — define microbial populations: Monod kinetic parameters (μ_max, K_s, yield, decay), solver type (CA / LBM / FD / kinetics-only), initial biomass.

7. **Kinetics Editor** — choose a built-in rate-law template or write custom C++ expressions:

   | Built-in template | Rate law |
   |-------------------|----------|
   | Monod | μ = μ_max × S/(K_s + S) |
   | Dual-substrate Monod | μ = μ_max × S1/(K1+S1) × S2/(K2+S2) |
   | Haldane inhibition | μ = μ_max × S/(K_s + S + S²/K_i) |
   | First-order decay | dA/dt = −k·A |
   | Bimolecular | dA/dt = dB/dt = −k·A·B |
   | Reversible | A ⇌ B, K_eq = k_f/k_r |
   | Mineral dissolution | Rate = k·(1 − Ω) |

8. **Run panel** — pre-flight validation checks all stability criteria before launch. The panel shows real-time iteration count, elapsed time, ETA, NS/ADE residuals, and color-coded console output. MPI settings (number of processes, mpirun path) are configured here.

9. **Post-processing** — open VTI files in the built-in VTK viewer: threshold filters, slice planes, vector glyphs for velocity fields. Click "Open in ParaView" for full-featured visualization.

### 7.5 Preferences

`Edit → Preferences`:
- **Theme**: dark (default) or light
- **Font size**: adjustable
- **Paths**: compiled `complab` executable path, ParaView installation path

---

## 8. XML Configuration Reference

All solver parameters are controlled by a single XML file. The annotated templates `CompLaB.xml` and `CompLaB_planktonic.xml` at the repository root are the best starting point. Key blocks:

```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>               <!-- true = with microbes -->
    <enable_kinetics>true</enable_kinetics>         <!-- Monod kinetics on/off -->
    <enable_abiotic_kinetics>false</enable_abiotic_kinetics>
    <enable_validation_diagnostics>false</enable_validation_diagnostics> <!-- slow; debug only -->
</simulation_mode>

<domain>
    <nx>50</nx>  <ny>50</ny>  <nz>50</nz>          <!-- lattice dimensions -->
    <geometry_file>input/geometry.dat</geometry_file>
</domain>

<numerics>
    <tau_NS>0.8</tau_NS>            <!-- NS relaxation time → viscosity -->
    <Pe>2.0</Pe>                    <!-- target Péclet number (sets pressure gradient) -->
    <max_iterations>50000</max_iterations>
    <output_frequency>1000</output_frequency>
    <checkpoint_frequency>5000</checkpoint_frequency>
</numerics>

<chemistry>
    <number_of_substrates>2</number_of_substrates>
    <substrate id="0">
        <name>DOC</name>
        <D_pore>1.0e-9</D_pore>           <!-- diffusion in pore fluid [m²/s] -->
        <D_biofilm>5.0e-10</D_biofilm>    <!-- diffusion in biofilm -->
        <inlet_concentration>1.0e-4</inlet_concentration>
    </substrate>
</chemistry>

<microbiology>
    <number_of_species>1</number_of_species>
    <species id="0">
        <solver_type>CA</solver_type>      <!-- CA, LBM, FD, kinetics_only -->
        <initial_biomass>0.1</initial_biomass>
        <B_max>1.0</B_max>
    </species>
</microbiology>

<output>
    <output_path>output/</output_path>
    <save_velocity>true</save_velocity>
    <save_geometry>true</save_geometry>
</output>
```

Full XML reference: `docs/CompLaB3D_User_Tutorial.md`.

---

## 9. Output Files

All output goes to the directory specified by `<output_path>` in the XML:

| File pattern | Format | Content |
|-------------|--------|---------|
| `substrate_NNNNNNN.vti` | VTK ImageData | Concentration field at iteration N |
| `velocity_NNNNNNN.vti` | VTK ImageData | Velocity field (u_x, u_y, u_z) |
| `biomass_NNNNNNN.vti` | VTK ImageData | Biomass density field |
| `maskLattice_NNNNNNN.vti` | VTK ImageData | Pore geometry / mask (changes with biofilm) |
| `checkpoint_NNNNNNN.chk` | Binary | Restart checkpoint (resume interrupted runs) |
| `btc_*.csv` | CSV | Breakthrough curve time series per substrate |
| `moments_summary.csv` | CSV | First and second spatial moments of BTCs |
| `domain_properties.csv` | CSV | Porosity, permeability, Pe, Ma, CFL, τ |
| `simulation_*.out` | Text | Full solver console log |

VTI files open directly in **ParaView** or the built-in GUI viewer.

---

## 10. Test Suite

CompLaB3D has **553+ automated tests** in three categories, all integrated with GitHub Actions CI.

### 10.1 C++ Unit Tests — 256 tests (no Palabos required)

The C++ tests use **GoogleTest v1.14** fetched automatically by CMake via `FetchContent`, plus a Palabos-free shim (`tests/cpp/plb_shim.h`). You do **not** need Palabos or MPI installed to build and run these tests.

```bash
cd tests/cpp
mkdir -p build && cd build
>>>>>>> Stashed changes
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

<<<<<<< Updated upstream
The executable `complab` is placed in the project root.

To point CMake at a custom Palabos location:

```bash
cmake .. -DPALABOS_ROOT=/path/to/palabos-v2.3.0
```

### 2. Install the GUI

**Prerequisites:** Python 3.10+

```bash
cd GUI
=======
Expected result: **256 tests passed, 0 failed** (runtime ~20 seconds on a laptop).

**Test executables and coverage:**

| Executable | What is tested | # Tests |
|------------|---------------|---------|
| `test_stability` | Ma, CFL, τ_NS, τ_ADE, Pe_grid bounds | 14 |
| `test_stability_extended` | Edge cases, boundary values, combined failures | ~20 |
| `test_abiotic_kinetics` | First-order decay, bimolecular, reversible, decay chain | 8 |
| `test_abiotic_kinetics_extended` | Multi-species coupling, mass conservation | ~15 |
| `test_biotic_kinetics` | Monod growth, substrate uptake, biomass yield | 11 |
| `test_biotic_kinetics_extended` | Haldane inhibition, endogenous decay, clamping | ~20 |
| `test_planktonic_kinetics` | Suspended biomass transport + Monod | 17 |
| `test_planktonic_kinetics_extended` | Multi-population, edge cases | ~20 |
| `test_eq_solver` | Anderson-accelerated NR equilibrium solver, PCF formulation | 27 |
| `test_eq_solver_extended` | Convergence on stiff systems, log K ranges | ~25 |
| `test_diagnostics` | Mass balance checking, per-iteration diagnostic output | 21 |
| `test_lbm_utils` | D3Q7 weights, Darcy velocity, FD Laplacian | 30 |
| `test_lbm_utils_extended` | Unit conversions, lattice math, boundary conditions | ~28 |

Run a single executable for detailed output:
```bash
./test_biotic_kinetics --gtest_verbose
./test_eq_solver --gtest_filter="*Anderson*"
```

### 10.2 Python / GUI Tests — 297+ tests

The GUI test suite uses **pytest** and **pytest-qt**, covering all configuration panels, dialogs, kinetics code generation, XML/JSON serialisation, the simulation runner subprocess lifecycle, and full end-to-end pipeline workflows.

```bash
cd GUI

# Install with dev dependencies
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
```

All 275 tests run without the C++ binary (mocked solver). They cover template
generation, XML building/parsing, kinetics code generation, cross-validation,
project data model validation, and end-to-end pipeline flows.

## Documentation

| Document | Contents |
|----------|----------|
| [Technical Guide](docs/CompLaB3D_Technical_Guide.md) | Monod kinetics, CA biofilm, equilibrium solver internals |
| [User Tutorial](docs/CompLaB3D_User_Tutorial.md) | Step-by-step GUI walkthrough |
| [Geometry Tutorial](docs/Geometry_Generator_Tutorial.md) | 3D pore geometry generation |
| [GUI README](GUI/README.md) | Reviewer/tester quick-start for the Python GUI |
| [Kinetics README](kinetics/README.md) | Details on each of the 9 scenario templates |
| [Installation Guide](INSTALL.md) | Platform-specific build and install instructions |
| [Changelog](CHANGELOG.md) | Version history and release notes |

## How to Cite
=======

# Run a specific module
python -m pytest tests/test_kinetics.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=term-missing

# Headless (CI / no display server)
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v --tb=short
```

Expected result: **297+ tests passed, 0 failed** (runtime ~30 seconds).

**Test modules:**

| Module | What is tested | # Tests |
|--------|---------------|---------|
| `test_gui_panels.py` | All 13 configuration panels: render, populate, validate | 120+ |
| `test_kinetics.py` | Code generation for all 7 built-in rate-law templates | 86 |
| `test_xml_io.py` | XML export/import round-trips, schema validation | 21 |
| `test_project_model.py` | `CompLaBProject` data model, serialisation to/from JSON | ~30 |
| `test_simulation_runner.py` | Subprocess launch, cancellation, crash handling, MPI | 18 |
| `test_templates.py` | All 6 project templates produce valid XML configurations | ~15 |
| `test_pipeline_e2e.py` | End-to-end: create project → configure → export XML → validate | 93 |

### 10.3 Continuous Integration

All tests run automatically on GitHub Actions on every push:

| Workflow | Trigger | Runs on |
|----------|---------|---------|
| `cpp-tests.yml` | Push/PR to `src/`, `tests/cpp/`, `defineKinetics.hh` | Ubuntu latest |
| `gui-tests.yml` | Push/PR to `GUI/` | Ubuntu, Python 3.10, 3.11, 3.12 |
| `draft-pdf.yml` | Push/PR to `paper/paper.md`, `paper.bib`, figures | Ubuntu (JOSS editorial bot) |

---

## 11. Analytical Validation Cases

Five complete validation cases in `test_cases/abiotic/` let you verify solver correctness against closed-form analytical solutions. Each case runs in a simple 1D channel geometry and finishes in under a minute on a laptop.

| Case | Reaction | Analytical solution | Key check |
|------|----------|---------------------|-----------|
| **Test 1** — Pure diffusion | ∂C/∂t = D∇²C | Linear steady-state C(x) = C₀(1 − x/L) | C_left=1, C_mid≈0.5, C_right→0 |
| **Test 2** — First-order decay | A → products, dA/dt = −k·A | Exponential: A(t) = A₀·e^(−kt), k = 1×10⁻⁴ s⁻¹ | Half-life at t = 6930 s |
| **Test 3** — Bimolecular | A + B → C, r = k·A·B | Mass conservation: A+B+C = 1.5 mol/L | B exhausted, C = 0.5 mol/L |
| **Test 4** — Reversible | A ⇌ B, K_eq = k_f/k_r = 2 | Equilibrium: B/A → 2, A_eq = 0.333, B_eq = 0.667 | A+B = 1.0 mol/L constant |
| **Test 5** — Sequential decay | A → B → C (Bateman) | Transient peak in B at t_max ≈ 6932 s | A+B+C = 1.0 mol/L constant |

### Running a validation case

```bash
# Step 1 — copy the kinetics header for this test
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh

# Step 2 — rebuild (required after changing the kinetics header)
cmake --build build --parallel 4

# Step 3 — generate a channel geometry
cd tools && python geometry_generator.py && cd ..

# Step 4 — run
./build/complab test_cases/abiotic/test2_first_order_decay.xml

# Step 5 — visualise
paraview output_abiotic_test2_decay/substrate*.vti
```

### Dry-run validation (checks XML and kinetics files without running the solver)

```bash
python tests/run_validation.py --dry-run
```

This script verifies that all five XML files and their associated kinetics headers are syntactically correct and internally self-consistent. It runs in seconds with no Palabos or MPI installation required and is part of the CI pipeline (`cpp-tests.yml`).

Full case descriptions with expected output values and troubleshooting: `test_cases/abiotic/README.md`.

---

## 12. Documentation

| Document | Location | Audience |
|----------|----------|---------|
| User Tutorial | `docs/CompLaB3D_User_Tutorial.md` | New users: installation through first simulation |
| Technical Guide | `docs/CompLaB3D_Technical_Guide.md` | Developers: full equations, algorithms, data structures |
| Geometry Generator Tutorial | `docs/Geometry_Generator_Tutorial.md` | Creating synthetic geometries and importing micro-CT data |
| Testing Guide | `TESTING.md` | All test types, what each covers, CI configuration |
| JOSS Paper | `paper/paper.md` | Scientific context, state of field, research impact |
| Mathematical Appendices | `paper/Appendices/` | Appendix A: equilibrium solver; B: CA algorithm; C: GUI details |

---

## 13. For JOSS Editors and Reviewers

This section consolidates the JOSS review checklist in one place.

### Licenses

| Component | License | File |
|-----------|---------|------|
| Solver (`src/`) | GNU Affero General Public License v3.0 | `LICENSE` |
| GUI (`GUI/`) | UGA Research Foundation proprietary | `GUI/LICENSE` |
| Upstream Palabos | AGPL-3.0 (compatible) | https://palabos.unige.ch/ |

### Verify the C++ unit tests (~20 seconds, no Palabos required)

```bash
cd tests/cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

Expected: **256 passed, 0 failed.**

### Verify the GUI tests (~30 seconds)

```bash
cd GUI
pip install -e ".[dev]"
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v --tb=short
```

Expected: **297+ passed, 0 failed.**

### Verify the analytical validation dry-run (~5 seconds)

```bash
python tests/run_validation.py --dry-run
```

Expected: all 5 cases report OK.

### Compile and run the solver

Requires Palabos (see Section 3) and MPI. Test 2 (first-order decay, 1D channel) runs in under a minute:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPLB_ROOT=/path/to/palabos
cmake --build build --parallel 4
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cmake --build build --parallel 4   # recompile with test kinetics
./build/complab test_cases/abiotic/test2_first_order_decay.xml
```

Alternatively, use the standalone `ComapLB3D/` package (Section 5) which requires no separate Palabos installation.

### Verify the JOSS paper PDF

The PDF is compiled on every push via `draft-pdf.yml` (JOSS editorial bot). Download the artifact from the Actions tab, or compile locally with Docker:

```bash
docker run --rm \
  -v $(pwd)/paper:/data \
  openjournals/inara \
  -o pdf paper.md
```

### JOSS paper sections

| Section | Present | Lines in paper.md |
|---------|---------|------------------|
| Summary | ✅ | ~26–30 |
| Statement of Need | ✅ | ~32–34 |
| Model Description | ✅ | ~36–96 |
| State of the Field | ✅ | ~98–100 |
| Research Impact | ✅ | ~102–104 |
| AI Usage Disclosure | ✅ | ~106–108 |

### Installation instructions
Sections 3, 4, 5, and 7 of this README.

### Example usage
`CompLaB.xml` and `CompLaB_planktonic.xml` at the repository root are fully-annotated ready-to-run templates. The five cases in `test_cases/abiotic/` are minimal working examples with known analytical solutions.

### API / configuration documentation
Full XML reference in `docs/CompLaB3D_User_Tutorial.md`. Kinetics API documented in the annotated `defineKinetics.hh` and `defineAbioticKinetics.hh` headers.

### Community guidelines
`CONTRIBUTING.md` — how to contribute, report issues, request features.
`CODE_OF_CONDUCT.md` — Contributor Covenant v2.1.

---

## 14. Citation
>>>>>>> Stashed changes

If you use CompLaB3D in your research, please cite:

```bibtex
<<<<<<< Updated upstream
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
=======
@article{Asgari:2026,
  title   = {{CompLaB3D}: A Three-Dimensional Pore-Scale Reactive Transport
             Model Framework and Graphical User Interface Coupling Lattice
             Boltzmann Flow with Biogeochemical Kinetics, Equilibrium Chemistry
             and Biofilm Dynamics},
  author  = {Asgari, Shahram and Meile, Christof},
  journal = {Journal of Open Source Software},
  year    = {2026},
  doi     = {pending}
}
```

A machine-readable citation is in `CITATION.cff`.
>>>>>>> Stashed changes

## Contributing

<<<<<<< Updated upstream
Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md)
before opening a pull request. All participants are expected to follow the
[Code of Conduct](CODE_OF_CONDUCT.md).

## License

CompLaB3D is released under the
[GNU General Public License v3.0](LICENSE).
=======
## 15. License

**Solver (`src/`):** GNU Affero General Public License v3.0 — see `LICENSE`.
CompLaB3D is built on [Palabos](https://palabos.unige.ch/) (AGPL-3.0, University of Geneva).

**GUI (`GUI/`):** © 2025–2026 University of Georgia Research Foundation, Inc.
CompLaB Studio was created by Shahram Asgari and Christof Meile at the Department of Marine Sciences, University of Georgia.
For licensing inquiries: https://uga.flintbox.com/#technologies/aa12627e-b4e4-43dc-b458-ff56d0cb4480

---

## 16. Acknowledgements

CompLaB3D is developed at the **Meile Lab**, Department of Marine Sciences, University of Georgia. The solver is built on the [Palabos](https://palabos.unige.ch/) open-source LBM library (University of Geneva). Development was supported by the U.S. Department of Energy, Office of Science, Office of Biological and Environmental Research, Genomic Science Program, Award Number DE-SC0022991.
>>>>>>> Stashed changes
