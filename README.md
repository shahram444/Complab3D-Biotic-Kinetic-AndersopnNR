# CompLaB3D

**Three-Dimensional Pore-Scale Biogeochemical Reactive Transport Modeling Framework**

**Authors:** Shahram Asgari and Christof Meile  
**Affiliation:** Meile Lab, Department of Marine Sciences, University of Georgia (UGA), Athens, GA, USA  
**Contact:** [shahram.asgari@uga.edu](mailto:shahram.asgari@uga.edu)

The 3-D extension presented here was created by Shahram Asgari and Christof Meile (Meile Lab, UGA). Its 2-D predecessor *CompLaB v1.0* was developed by Heewon Jung, Hyun-Seob Song, and Christof Meile.

CompLaB3D is an open-source three-dimensional pore-scale reactive transport model that couples Lattice Boltzmann Method (LBM) fluid flow and solute transport with Monod-based microbial kinetics, user-defined abiotic chemical reactions, an Anderson-accelerated equilibrium chemistry model, and a cellular automaton (CA) biofilm model — all MPI-parallelised through the [Palabos](https://palabos.unige.ch/) library.

**CompLaB Studio** (v2.1.0) is the companion graphical interface: a desktop application built with PySide6 that handles the complete workflow from project setup and geometry generation through simulation launch and 3D post-processing — without ever touching a text editor.

---

## Table of Contents

**[PART 1 — Overview & Reference](#part-1--overview--reference)**

1. [Overview](#1-overview)
2. [Repository Structure](#2-repository-structure)
3. [Prerequisites](#3-prerequisites)
4. [Quick Start](#4-quick-start)
5. [Test Suite](#5-test-suite)
6. [Analytical Validation Cases](#6-analytical-validation-cases)
7. [Output Files](#7-output-files)
8. [Documentation](#8-documentation)
9. [For JOSS Editors and Reviewers](#9-for-joss-editors-and-reviewers)
10. [Citation](#10-citation)
11. [License](#11-license)
12. [Acknowledgements](#12-acknowledgements)

**[PART 2 — Standalone HPC & Command-Line Guide](#part-2--standalone-hpc--command-line-guide)**

13. [Two Ways to Get the Model](#13-two-ways-to-get-the-model)
14. [Option A — Standalone Package (ComapLB3D)](#14-option-a--standalone-package-comaplb3d-recommended-for-clusters)
15. [Option B — Build from Source](#15-option-b--build-from-source-full-repo)
16. [Configuring a Simulation](#16-configuring-a-simulation)
17. [Running the Model](#17-running-the-model)
18. [HPC Job Submission — All Scheduler Types](#18-hpc-job-submission--all-scheduler-types)
19. [Choosing the Number of MPI Processes](#19-choosing-the-number-of-mpi-processes)
20. [Startup Output and Stability Report](#20-startup-output-and-stability-report)
21. [Output Files (Cluster Runs)](#21-output-files-cluster-runs)
22. [Editing Kinetics and Recompiling](#22-editing-kinetics-and-recompiling)
23. [Validation Cases — Run-Through Procedure](#23-validation-cases--run-through-procedure)
24. [HPC / CLI Troubleshooting](#24-hpc--cli-troubleshooting)

**[PART 3 — GUI Workflow Guide (CompLaB Studio)](#part-3--gui-workflow-guide-complab-studio)**

25. [GUI Prerequisites](#25-gui-prerequisites)
26. [GUI Installation](#26-gui-installation)
27. [Launching the GUI](#27-launching-the-gui)
28. [Interface Overview](#28-interface-overview)
29. [Step-by-Step Workflow](#29-step-by-step-workflow)
30. [Panel Reference](#30-panel-reference)
31. [Kinetics Editor](#31-kinetics-editor)
32. [Running a Simulation from the GUI](#32-running-a-simulation-from-the-gui)
33. [Post-Processing](#33-post-processing)
34. [Project Files and XML Export](#34-project-files-and-xml-export)
35. [Preferences](#35-preferences)
36. [GUI Test Suite](#36-gui-test-suite)
37. [GUI Troubleshooting](#37-gui-troubleshooting)

---

---

# PART 1 — Overview & Reference

---

## 1. Overview

CompLaB3D executes a **10-phase pipeline** on every simulation run:

| Phase | Description                                                                                                                                                                                          |
| ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1     | Load XML configuration and validate all inputs                                                                                                                                                       |
| 2     | Geometry setup and preprocessing (solid / pore / biofilm classification)                                                                                                                             |
| 3     | Navier-Stokes flow field (D3Q19 LBM): initial pressure → permeability → target velocity → corrected pressure → final flow → stability checks (Ma, CFL, τ)                                            |
| 4     | Reactive transport lattice setup — D3Q7 ADE for each substrate and planktonic biomass species                                                                                                        |
| 5     | NS-ADE velocity field coupling                                                                                                                                                                       |
| 6     | **Main simulation loop**: collision → kinetic reactions (Monod / abiotic) → equilibrium chemistry (Anderson-NR PCF) → biomass redistribution (CA / FD) → flow update if geometry changed → streaming |
| 7     | Write VTI / CHK output files                                                                                                                                                                         |
| 8     | Breakthrough curve analysis and spatial moment calculations                                                                                                                                          |
| 9     | Write summary CSV files                                                                                                                                                                              |
| 10    | Finalise and clean up                                                                                                                                                                                |

**Simulation modes:**

| Mode                | `biotic_mode` | `enable_kinetics` | `enable_abiotic_kinetics` |
| ------------------- |:-------------:|:-----------------:|:-------------------------:|
| Flow only           | false         | false             | false                     |
| Tracer transport    | false         | false             | false                     |
| Abiotic reactions   | false         | false             | true                      |
| Biotic (sessile CA) | true          | true              | false                     |
| Biotic (planktonic) | true          | true              | false                     |
| Full coupled        | true          | true              | true                      |

---

## 2. Repository Structure

```

│
├── src/                                         # C++ model source
│   ├── complab.cpp                              # Main entry point (10-phase pipeline)
│   ├── complab_functions.hh                     # XML parser, geometry I/O, BTC analysis
│   ├── complab3d_processors.hh                  # LBM collision/streaming processors
│   ├── complab3d_processors_part1–3.hh          # NS / ADE / biofilm CA+FD processors
│   └── complab3d_processors_part4_eqsolver.hh  # Anderson-NR equilibrium module
│
├── GUI/                                         # CompLaB Studio (v2.1.0)
│   ├── main.py                                  # Entry point — splash screen + launch
│   ├── src/                                     # GUI source
│   │   ├── main_window.py                       # COMSOL-style 4-panel main window
│   │   ├── core/                                # Project model, XML I/O, simulation runner
│   │   ├── panels/                              # 13 configuration panels
│   │   ├── dialogs/                             # New project, kinetics editor, preferences
│   │   └── widgets/                             # VTK viewer, console, convergence plot
│   ├── pyproject.toml                           # Python packaging
│   ├── requirements.txt                         # Runtime dependencies
│   ├── requirements-dev.txt                     # Test/dev dependencies
│   └── tests/                                   # pytest test suite
│
├── ComapLB3D/                                   # Standalone HPC package (Palabos bundled)
│   ├── src/                                     # Identical to root src/
│   ├── versionControl/palabos-v2.3.0/          # Bundled Palabos (pre-compiled)
│   ├── CompLaB.xml                              # Simulation template
│   ├── defineKinetics.hh                        # Biotic kinetics (edit and recompile)
│   ├── defineAbioticKinetics.hh                 # Abiotic kinetics (edit and recompile)
│   ├── comp.sh                                  # SLURM job script (UGA Sapelo2)
│   ├── input/                                   # Place geometry.dat here
│   └── output/                                  # Output VTK/checkpoint files written here
│
├── tests/                                       # C++ unit tests + analytical validation
│   ├── README.md
│   ├── cpp/                                     # GoogleTest C++ unit tests
│   └── run_validation.py                        # Analytical validation runner
│
├── test_cases/
│   ├── abiotic/                                 # 5 analytical validation cases
│   ├── biotic/                                  # Biofilm simulation example
│   └── flow_only/                               # Pure flow benchmark
│
├── paper/                                       # JOSS manuscript (paper.md, paper.bib, figures)
├── tools/
│   └── geometry_generator.py                    # Standalone CLI geometry generator (v6.0)
├── .github/workflows/                           # CI: cpp-tests, gui-tests, draft-pdf
├── defineKinetics.hh
├── defineAbioticKinetics.hh
├── CompLaB.xml
├── CITATION.cff
├── codemeta.json
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── TESTING.md
├── .gitignore
└── LICENSE                                      # GNU AGPL v3
```

---

## 3. Prerequisites

### Model (C++ — required to build and run simulations)

| Requirement                          | Minimum version                | Notes                                   |
| ------------------------------------ | ------------------------------ | --------------------------------------- |
| C++ compiler                         | GCC 7+ / Clang 5+ / MSVC 2019+ | C++11 required                          |
| [Palabos](https://palabos.unige.ch/) | 2.2+                           | AGPL-3.0; required at compile time only |
| OpenMPI or MPICH                     | OpenMPI 4+ / MPICH 3+          | Required for parallel (MPI) runs        |
| CMake                                | 3.14+                          |                                         |

**Linux (Ubuntu / Debian):**

```bash
sudo apt-get install -y g++ openmpi-bin libopenmpi-dev make cmake git
```

**macOS:**

```bash
brew install gcc open-mpi cmake
```

**Windows:** Install [MS-MPI](https://learn.microsoft.com/en-us/message-passing-interface/microsoft-mpi) then either Visual Studio with C++ workload or MSYS2/MinGW-w64.

> **Cluster users:** The `ComapLB3D/` folder bundles Palabos v2.3.0 pre-compiled for GCC 11.3 (UGA Sapelo2 / foss/2022a). Most cluster users only need to run `cmake .. && make` — see [Part 2](#part-2--standalone-hpc--command-line-guide).

### GUI — CompLaB Studio (optional)

| Requirement | Minimum version |
| ----------- | --------------- |
| Python      | 3.10+           |
| PySide6     | 6.5+            |
| NumPy       | 1.24+           |
| VTK         | 9.2+            |
| Matplotlib  | 3.7+            |

The GUI is **not required** to run simulations. Install with:

```bash
cd GUI && pip install -r requirements.txt
```

---

## 4. Quick Start

### Option A — Standalone HPC / command-line

```bash
# 1. Load modules (UGA Sapelo2 example)
module purge && module load foss/2022a && module load CMake/3.24.3-GCCcore-11.3.0

# 2. Build
cd ComapLB3D/build && cmake .. && make -j8

# 3. Edit CompLaB.xml and place geometry.dat in input/

# 4. Run
cd ..
mpirun -np 8 ./complab          # local
sbatch comp.sh                  # SLURM cluster
```

→ Full cluster guide: [Part 2 — Standalone HPC](#part-2--standalone-hpc--command-line-guide)

### Option B — CompLaB Studio GUI

```bash
# 1. Install
cd GUI && pip install -r requirements.txt

# 2. Launch
python main.py
```

→ Full GUI guide: [Part 3 — GUI Workflow](#part-3--gui-workflow-guide-complab-studio)

---

## 5. Test Suite

CompLaB3D has **744+ automated tests** in two categories, all running on GitHub Actions CI.

### 5.1 C++ Unit Tests — 382 tests (no Palabos required)

**Linux / macOS:**

```bash
cd tests/cpp && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

**Windows (Visual Studio Developer Command Prompt):**

```bat
cd tests\cpp && mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release --parallel
ctest -C Release --output-on-failure
```

Expected result: **382 passed, 0 failed** (~1 second on a laptop).

| Executable                                                                           | What is tested                                                | Tests   |
| ------------------------------------------------------------------------------------ | ------------------------------------------------------------- | ------- |
| `test_stability` / `_extended`                                                       | Ma, CFL, τ, Pe_grid bounds and edge cases                     | 40      |
| `test_abiotic_kinetics` / `_extended`                                                | First-order decay, bimolecular, reversible, mass conservation | 50      |
| `test_biotic_kinetics` / `_extended`                                                 | Monod growth, substrate uptake, Haldane inhibition, decay     | 55      |
| `test_planktonic_kinetics` / `_extended`                                             | Suspended biomass transport + Monod, multi-population         | 37      |
| `test_eq_solver` / `_extended`                                                       | Anderson-NR equilibrium model, stiff systems, log K ranges    | 51      |
| `test_diagnostics`                                                                   | Mass balance checking, diagnostic output                      | 20      |
| `test_lbm_utils` / `_extended`                                                       | D3Q7 weights, Darcy velocity, FD Laplacian, unit conversions  | 65      |
| `test_bc`, `test_growth_integration`, `test_diffusion_bc`, `test_reaction_transport` | BCs, Euler integration, 1D profiles, Pe/Da/Thiele             | 64      |
| **Total**                                                                            |                                                               | **382** |

Full descriptions: `tests/README.md`.

### 5.2 Python / GUI Tests — 362+ tests (no model required)

```bash
cd GUI
pip install PySide6 pytest pytest-qt
python -m pytest tests/ -v
# Headless Linux (CI):
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v
```

Expected: **362 passed, 5 skipped** (5 skipped require a graphical Qt display; they pass on desktop).

| Module                      | What is tested                                         | Tests |
| --------------------------- | ------------------------------------------------------ | ----- |
| `test_project_model.py`     | Parameter validation before XML export                 | 24    |
| `test_templates.py`         | All 9 built-in templates produce valid configs         | 38    |
| `test_xml_io.py`            | XML export/import round-trips, schema validation       | 48    |
| `test_kinetics.py`          | C++ code generation, array-index cross-validation      | 70    |
| `test_pipeline_e2e.py`      | End-to-end: template → XML → kinetics → fake model run | 87    |
| `test_xml_diagnostic.py`    | Crash diagnostic module                                | 47    |
| `test_config.py`            | AppConfig persistence, malformed-JSON recovery         | 36    |
| `test_simulation_runner.py` | Subprocess launch, cancel, crash, MPI, stdout flood    | ~11   |
| `test_gui_panels.py`        | All 13 configuration panels: load/save round-trips     | ~80   |

Full descriptions: `GUI/tests/README.md`.

### 5.3 Continuous Integration

| Workflow        | Trigger                                              | Runs on                     |
| --------------- | ---------------------------------------------------- | --------------------------- |
| `cpp-tests.yml` | Push/PR to `src/`, `tests/cpp/`, `defineKinetics.hh` | Ubuntu latest               |
| `gui-tests.yml` | Push/PR to `GUI/`                                    | Ubuntu, Python 3.10–3.12    |
| `draft-pdf.yml` | Push/PR to `paper/`                                  | Ubuntu (JOSS editorial bot) |

---

## 6. Analytical Validation Cases

Five complete validation cases in `test_cases/abiotic/` verify model correctness against closed-form analytical solutions.

| Case                           | Reaction              | Key check                                   |
| ------------------------------ | --------------------- | ------------------------------------------- |
| **Test 1** — Pure diffusion    | ∂C/∂t = D∇²C          | C_left=1, C_mid≈0.5, C_right→0              |
| **Test 2** — First-order decay | A → products, r = k·A | Half-life at t = 6930 s (k = 1×10⁻⁴ s⁻¹)    |
| **Test 3** — Bimolecular       | A + B → C, r = k·A·B  | B exhausted, C = 0.5 mol/L; A+B+C conserved |
| **Test 4** — Reversible        | A ⇌ B, K_eq = 2       | B/A → 2; A+B = 1.0 mol/L constant           |
| **Test 5** — Sequential decay  | A → B → C (Bateman)   | Transient B peak; A+B+C = 1.0 constant      |

**Dry-run check (no model needed):**

```bash
python tests/run_validation.py --dry-run
```

**Full run (Test 2 example):**

```bash
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cmake --build build --parallel 4
./build/complab test_cases/abiotic/test2_first_order_decay.xml
```

Full descriptions: `test_cases/abiotic/README.md`.

---

## 7. Output Files

All output goes to the directory specified by `<output_path>` in the XML:

| File pattern              | Format        | Content                                |
| ------------------------- | ------------- | -------------------------------------- |
| `substrate_NNNNNNN.vti`   | VTK ImageData | Concentration field at iteration N     |
| `velocity_NNNNNNN.vti`    | VTK ImageData | Velocity field (u_x, u_y, u_z)         |
| `biomass_NNNNNNN.vti`     | VTK ImageData | Biomass density field                  |
| `maskLattice_NNNNNNN.vti` | VTK ImageData | Pore geometry / mask                   |
| `checkpoint_NNNNNNN.chk`  | Binary        | Restart checkpoint                     |
| `btc_*.csv`               | CSV           | Breakthrough curve time series         |
| `moments_summary.csv`     | CSV           | First and second spatial moments       |
| `domain_properties.csv`   | CSV           | Porosity, permeability, Pe, Ma, CFL, τ |
| `simulation_*.out`        | Text          | Full model console log                 |

VTI files open directly in **ParaView** or the built-in GUI viewer.

---

## 8. Documentation

| Document                      | Location                                         |
| ----------------------------- | ------------------------------------------------ |
| Top-level README (this file)  | `README.md`                                      |
| GUI README                    | `GUI/README.md`                                  |
| Paper README                  | `paper/README.md`                                |
| C++ Test Descriptions         | `tests/README.md`                                |
| GUI Test Descriptions         | `GUI/tests/README.md`                            |
| Combined testing guide        | `TESTING.md`                                     |
| Contribution guidelines       | `CONTRIBUTING.md`                                |
| Code of Conduct               | `CODE_OF_CONDUCT.md`                             |
| JOSS Paper                    | `paper/paper.md`                                 |
| Annotated XML config template | `CompLaB.xml` (root) and `ComapLB3D/CompLaB.xml` |
| Annotated kinetics template   | `defineKinetics.hh`, `defineAbioticKinetics.hh`  |

---

## 9. For JOSS Editors and Reviewers

### Licenses

| Component        | License                                | File                      |
| ---------------- | -------------------------------------- | ------------------------- |
| Model (`src/`)   | GNU Affero General Public License v3.0 | `LICENSE`                 |
| GUI (`GUI/`)     | AGPL-3.0 OR commercial (UGARF)         | `GUI/LICENSE`             |
| Upstream Palabos | AGPL-3.0 (compatible)                  | https://palabos.unige.ch/ |

The GUI is dual-licensed by the University of Georgia Research Foundation:
AGPL-3.0 for open-source / academic use, or a separate commercial license
available through <https://uga.flintbox.com/#technologies/aa12627e-b4e4-43dc-b458-ff56d0cb4480>.
See §11 below for the full license details.

### Verify the C++ unit tests (~1 second, no Palabos required)

```bash
cd tests/cpp && mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

Expected: **382 passed, 0 failed.**

### Verify the GUI tests (~12 seconds, no model required)

```bash
cd GUI
pip install PySide6 pytest pytest-qt
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v
```

Expected: **362 passed, 5 skipped.**

### Verify the analytical validation dry-run

```bash
python tests/run_validation.py --dry-run
```

Expected: all 5 cases report OK.

### Compile and run the model

Requires Palabos and MPI. Test 2 runs in under a minute:

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPLB_ROOT=/path/to/palabos
cmake --build build --parallel 4
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cmake --build build --parallel 4
./build/complab test_cases/abiotic/test2_first_order_decay.xml
```

Alternatively, use the standalone `ComapLB3D/` package (see [Part 2](#part-2--standalone-hpc--command-line-guide)).

### Verify the JOSS paper PDF

```bash
docker run --rm -v $(pwd)/paper:/data openjournals/inara -o pdf paper.md
```

### JOSS paper sections

| Section             | Present | Lines in paper.md |
| ------------------- | ------- | ----------------- |
| Summary             | ✅       | ~26–30            |
| Statement of Need   | ✅       | ~32–34            |
| Model Description   | ✅       | ~36–96            |
| State of the Field  | ✅       | ~98–100           |
| Research Impact     | ✅       | ~102–104          |
| AI Usage Disclosure | ✅       | ~106–108          |

### Community guidelines

- `CONTRIBUTING.md` — how to contribute, report issues, request features
- `CODE_OF_CONDUCT.md` — Contributor Covenant v2.1

---

## 10. Citation

If you use CompLaB3D in your research, please cite:

```bibtex
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

---

## 11. License

CompLaB3D is distributed under a **dual-component licensing model**: the C++
model is open-source under the GNU Affero General Public License v3.0, while
the CompLaB Studio GUI is dual-licensed by the University of Georgia Research
Foundation (AGPL-3.0 for open-source / academic use, with a separate commercial
license available).

### Model — `src/` and root `CMakeLists.txt`

GNU Affero General Public License v3.0 — see [`LICENSE`](LICENSE).

CompLaB3D is built on [Palabos](https://palabos.unige.ch/) (AGPL-3.0,
University of Geneva), included in `versionControl/palabos-v2.3.0/`.

### GUI — `GUI/`

© 2025–2026 University of Georgia Research Foundation, Inc.

CompLaB Studio (the graphical user interface for CompLaB3D, comprising
everything in this `GUI/` directory) was created by Shahram Asgari and
Christof Meile at the University of Georgia, Department of Marine Sciences.

The GUI is **dual-licensed** by UGARF:

1. **Open-source / academic use** — GNU Affero General Public License v3.0.
   Use, copy, modify, and redistribute under the terms of the AGPL-3.0
   (see [`GUI/LICENSE`](GUI/LICENSE)).
2. **Commercial license** — Organizations that prefer not to be bound by the
   AGPL-3.0 copyleft requirements may obtain a separate commercial license.

Please contact us at this link for additional licensing opportunities:
<https://uga.flintbox.com/#technologies/aa12627e-b4e4-43dc-b458-ff56d0cb4480>

### Summary table

| Component        | License                                                    | File                         |
| ---------------- | ---------------------------------------------------------- | ---------------------------- |
| Model (`src/`)   | GNU Affero General Public License v3.0                     | [`LICENSE`](LICENSE)         |
| GUI (`GUI/`)     | AGPL-3.0 OR commercial (UGARF) | [`GUI/LICENSE`](GUI/LICENSE) |
| Upstream Palabos | AGPL-3.0 (compatible)                                      | <https://palabos.unige.ch/>  |

---

## 12. Acknowledgements

CompLaB3D is developed at the **Meile Lab**, Department of Marine Sciences, University of Georgia. Development was supported by the U.S. Department of Energy, Office of Science, Office of Biological and Environmental Research, Genomic Science Program, Award Number DE-SC0022991.

---

---

# PART 2 — Standalone HPC & Command-Line Guide

This section covers everything you need to build and run CompLaB3D on an HPC cluster or local Linux/macOS/Windows machine **without the GUI**. All configuration is done by editing two files: `CompLaB.xml` (parameters) and `defineKinetics.hh` / `defineAbioticKinetics.hh` (rate laws).

---

## 13. Two Ways to Get the Model

|                | Option A — Standalone Package                    | Option B — Build from Source                                              |
| -------------- | ------------------------------------------------ | ------------------------------------------------------------------------- |
| **Where**      | `ComapLB3D/` folder in this repo                 | Root `CMakeLists.txt` + download Palabos                                  |
| **Palabos**    | Bundled and pre-compiled (GCC 11.3 / foss/2022a) | You download and compile Palabos yourself                                 |
| **Best for**   | UGA Sapelo2, most SLURM clusters running GCC 11+ | Custom architecture, macOS, Windows, or if the pre-compiled library fails |
| **Difficulty** | `cmake .. && make` — nothing else to install     | More steps, but works anywhere                                            |

---

## 14. Option A — Standalone Package (ComapLB3D): Recommended for Clusters

### 14.1 Package structure

```
ComapLB3D/
├── CMakeLists.txt               # Build configuration
├── CompLaB.xml                  # Simulation parameters — edit before running
├── defineKinetics.hh            # Biotic (Monod) rate expressions — edit and recompile
├── defineAbioticKinetics.hh     # Abiotic chemical rate expressions — edit and recompile
├── comp.sh                      # SLURM job script (configured for UGA Sapelo2)
├── src/                         # CompLaB3D C++ source (identical to root src/)
├── versionControl/
│   └── palabos-v2.3.0/
│       └── build/libpalabos.a  # Pre-compiled static library — do NOT delete
├── input/                       # Place geometry.dat here before running
├── output/                      # Model writes VTI/checkpoint/CSV files here
└── build/                       # Run cmake from inside this directory
```

> **Do not delete or recompile anything inside `versionControl/palabos-v2.3.0/`.** The pre-compiled library was built for GCC 11.3 (foss/2022a). For other architectures, see §14.4.

### 14.2 UGA Sapelo2 / GACRC (reference configuration)

This is the exact toolchain the bundled library was compiled with. Everything should work out-of-the-box.

```bash
# Step 1 — load modules
module purge
module load foss/2022a
module load CMake/3.24.3-GCCcore-11.3.0

# Step 2 — build
cd ComapLB3D/build
cmake ..
make -j8

# Step 3 — configure your simulation
cd ..
# Edit CompLaB.xml and (if using kinetics) defineKinetics.hh
# Place geometry.dat in input/

# Step 4 — submit the job
sbatch comp.sh
```

**Monitor your job:**

```bash
squeue -u $USER               # queue position and status
sacct -j <JOBID>              # details after completion
scancel <JOBID>               # cancel
```

### 14.3 Other SLURM clusters (generic)

The build steps are identical — only the module names change.

```bash
# Step 1 — find and load available modules
module avail gcc              # list available GCC versions
module avail openmpi
module avail cmake

# Load (adjust version numbers to what your cluster provides):
module purge
module load gcc/12.2.0
module load openmpi/4.1.4
module load cmake/3.26.0

# Step 2 — build
cd ComapLB3D/build
cmake ..
make -j8

# Step 3 — configure and submit
cd ..
sbatch comp.sh
```

Edit `comp.sh` to match your cluster's partition name, core count, memory, and wall time:

```bash
#!/bin/bash
#SBATCH --job-name=complb
#SBATCH --partition=YOUR_PARTITION    # change this
#SBATCH --nodes=1
#SBATCH --ntasks=8                    # MPI ranks — match to your domain
#SBATCH --mem=16gb
#SBATCH --time=4:00:00                # HH:MM:SS
#SBATCH --output=%x.%j.out
#SBATCH --error=%x.%j.err

module purge
module load foss/2022a                # change to your cluster's module

cd $SLURM_SUBMIT_DIR
srun ./complab
```

### 14.4 Adapting CMakeLists.txt for other architectures

`CMakeLists.txt` in `ComapLB3D/` contains absolute paths pointing to Palabos on the UGA cluster. To use the bundled copy on any other machine, replace those lines with relative paths:

```cmake
# Replace the absolute /scratch/... lines with:
include_directories("../versionControl/palabos-v2.3.0/src")
include_directories("../versionControl/palabos-v2.3.0/externalLibraries")
include_directories("../versionControl/palabos-v2.3.0/externalLibraries/Eigen3")
file(GLOB_RECURSE PALABOS_SRC "../versionControl/palabos-v2.3.0/src/*.cpp")
file(GLOB_RECURSE EXT_SRC    "../versionControl/palabos-v2.3.0/externalLibraries/tinyxml/*.cpp")
```

> **Architecture mismatch:** If the linker fails because `libpalabos.a` was built for a different CPU or ABI, delete `palabos-v2.3.0/build/` and recompile Palabos for your system:
> 
> ```bash
> cd versionControl/palabos-v2.3.0 && mkdir -p build && cd build
> cmake .. -DCMAKE_BUILD_TYPE=Release
> make -j8
> ```
> 
> Then proceed with `cmake .. && make -j8` in `ComapLB3D/build/`.

---

## 15. Option B — Build from Source (Full Repo)

Use this if you want to build from the root `CMakeLists.txt` and manage Palabos yourself, or if you're on macOS / Windows.

### 15.1 Download Palabos

**Linux / macOS:**

```bash
wget https://gitlab.com/unigespc/palabos/-/archive/v2.3.0/palabos-v2.3.0.tar.gz
tar -xzf palabos-v2.3.0.tar.gz
```

**Windows:** Download the zip from [gitlab.com/unigespc/palabos](https://gitlab.com/unigespc/palabos/-/releases) and extract manually.

### 15.2 Build — Linux and macOS

```bash
git clone https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR.git
cd Complab3D-Biotic-Kinetic-AndersopnNR/JOSS_Submit

cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DPLB_ROOT=/path/to/palabos-v2.3.0

cmake --build build --parallel 4
```

This produces `build/complab`.

### 15.3 Build — Windows (Visual Studio)

```bat
cmake -S . -B build ^
      -G "Visual Studio 17 2022" -A x64 ^
      -DCMAKE_BUILD_TYPE=Release ^
      -DPLB_ROOT=C:\path\to\palabos-v2.3.0

cmake --build build --config Release --parallel 4
```

Executable: `build\Release\complab.exe`.

### 15.4 Build — Windows (MSYS2 MinGW-w64)

Open the **MSYS2 MinGW64** shell:

```bash
# Install tools if not already installed:
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make

# Build:
cd JOSS_Submit
mkdir build && cd build
cmake .. -G "MinGW Makefiles" \
         -DCMAKE_BUILD_TYPE=Release \
         -DPLB_ROOT=/c/path/to/palabos-v2.3.0
mingw32-make -j4
```

### 15.5 HPC Cluster — module-based (generic)

```bash
# Step 1 — load modules
module purge
module load gcc/11.3.0
module load openmpi/4.1.4
module load cmake/3.24.0

# Step 2 — build
cd JOSS_Submit
cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DPLB_ROOT=/path/to/palabos-v2.3.0
cmake --build build --parallel 8
```

---

## 16. Configuring a Simulation

Every CompLaB3D simulation is controlled by three files.

### 16.1 CompLaB.xml — simulation parameters

The annotated template at the repo root is the best starting point. Key blocks:

```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>             <!-- true = with microbes -->
    <enable_kinetics>true</enable_kinetics>
    <enable_abiotic_kinetics>false</enable_abiotic_kinetics>
</simulation_mode>

<LB_numerics>
    <domain>
        <nx>50</nx>  <ny>50</ny>  <nz>50</nz>   <!-- lattice dimensions -->
        <dx>1.0e-6</dx>                          <!-- grid spacing [m] -->
        <characteristic_length>30</characteristic_length>
        <filename>geometry.dat</filename>
        <material_numbers>
            <pore>2</pore>    <solid>0</solid>   <bounce_back>1</bounce_back>
        </material_numbers>
    </domain>
    <Peclet>2.0</Peclet>            <!-- target Péclet number -->
    <tau>0.8</tau>                  <!-- NS relaxation time → viscosity -->
    <iteration>
        <ns_max_iT1>100000</ns_max_iT1>
        <ade_max_iT>10000000</ade_max_iT>
        <ade_converge_iT>1e-8</ade_converge_iT>
    </iteration>
</LB_numerics>

<chemistry>
    <number_of_substrates>1</number_of_substrates>
    <substrate0>
        <name_of_substrates>DOC</name_of_substrates>
        <initial_concentration>0.0</initial_concentration>
        <substrate_diffusion_coefficients>
            <in_pore>1.0e-9</in_pore>        <!-- [m²/s] -->
            <in_biofilm>5.0e-10</in_biofilm>
        </substrate_diffusion_coefficients>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <left_boundary_condition>1.0e-4</left_boundary_condition>
        <right_boundary_type>Neumann</right_boundary_type>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate0>
</chemistry>
```

Full XML reference: see the annotated `CompLaB.xml` template at the repo root.

### 16.2 Kinetics headers

For **biotic** simulations, edit `defineKinetics.hh` to define your Monod rate expressions. For **abiotic** simulations, edit `defineAbioticKinetics.hh`. These headers are compiled into the model — **you must rebuild after every edit** (see §22).

### 16.3 Geometry file

Place `geometry.dat` in the `input/` folder (relative to where `CompLaB.xml` lives). The file is a text file with one integer per line representing the material number of each voxel, in Fortran-order (z fastest):

```
material[x=0,y=0,z=0]
material[x=0,y=0,z=1]
...
```

Material number meanings (set in `<material_numbers>` in the XML):

| Value | Meaning                       |
| ----- | ----------------------------- |
| 0     | Solid (no-slip wall)          |
| 1     | Bounce-back boundary          |
| 2     | Pore fluid                    |
| 3+    | Biofilm region (user-defined) |

**Generate a synthetic geometry:**

Two options:

1. **GUI** — CompLaB Studio's Geometry Creator (Tools → Geometry Creator) supports
   seven synthetic medium types (sphere pack, slit pore, open channel, etc.) and
   imports segmented micro-CT image stacks (BMP/PNG/TIF). See [Part 3](#part-3--gui-workflow-guide-complab-studio).

2. **Standalone CLI script** — `tools/geometry_generator.py` (v6.0) provides the
   same functionality from the command line, with three generators (abiotic
   porous media, sessile biofilm, image-stack converter):
   
   ```bash
   cd tools
   python geometry_generator.py
   # Follow the guided menu: choose generator type and parameters
   # Output: <project>/input/geometry.dat
   ```

---

## 17. Running the Model

### 17.1 Serial run

**Linux / macOS:**

```bash
./complab                        # reads CompLaB.xml in current directory
```

**Windows:**

```bat
complab.exe
```

### 17.2 MPI parallel run

**Linux / macOS:**

```bash
mpirun -np 8 ./complab           # 8 MPI processes
srun -n 16 ./complab             # SLURM launcher (inside a job script)
```

**Windows (MS-MPI):**

```bat
mpiexec -n 4 complab.exe
```

CompLaB3D uses Palabos domain decomposition — the grid is split automatically across all processes. Any number of processes is supported; choose a value that divides the domain dimensions evenly (see §7).

---

## 18. HPC Job Submission — All Scheduler Types

### 18.1 SLURM (most common)

```bash
sbatch comp.sh
squeue -u $USER               # monitor
scancel <JOBID>               # cancel
sacct -j <JOBID>              # completed job details
scontrol show job <JOBID>     # full info including node
```

### 18.2 PBS / Torque (older university clusters, some national facilities)

PBS uses `qsub` instead of `sbatch` and `#PBS` directives.

```bash
# Build (identical to SLURM):
module purge
module load gcc/11.3.0 openmpi/4.1.4 cmake/3.24.0
cd ComapLB3D/build && cmake .. && make -j8
cd ..

# Submit:
qsub comp_pbs.sh
```

Create `comp_pbs.sh`:

```bash
#!/bin/bash
#PBS -N complb
#PBS -q normal                    # change to your queue name
#PBS -l nodes=1:ppn=8             # 1 node, 8 cores
#PBS -l mem=16gb
#PBS -l walltime=4:00:00
#PBS -o complb.out
#PBS -e complb.err

module purge
module load gcc/11.3.0
module load openmpi/4.1.4

cd $PBS_O_WORKDIR
mpirun -np 8 ./complab
```

PBS monitoring:

```bash
qstat -u $USER                # list your jobs
qdel <JOBID>                  # cancel
qstat -f <JOBID>              # detailed job info
```

### 18.3 LSF (IBM Spectrum LSF — national labs, some universities)

LSF uses `bsub` and `#BSUB` directives.

```bash
# Build (identical):
module purge
module load gcc/11.3.0 openmpi/4.1.4 cmake/3.24.0
cd ComapLB3D/build && cmake .. && make -j8
cd ..

# Submit:
bsub < comp_lsf.sh
```

Create `comp_lsf.sh`:

```bash
#!/bin/bash
#BSUB -J complb
#BSUB -q normal
#BSUB -n 8                        # total MPI tasks
#BSUB -R "span[hosts=1]"          # all tasks on one node
#BSUB -M 16000                    # memory in MB
#BSUB -W 4:00                     # wall time HH:MM
#BSUB -o complb.%J.out
#BSUB -e complb.%J.err

module purge
module load gcc/11.3.0
module load openmpi/4.1.4

mpirun -np 8 ./complab
```

LSF monitoring:

```bash
bjobs                             # running and pending jobs
bkill <JOBID>                     # cancel
bhist -l <JOBID>                  # completed job history
```

---

## 19. Choosing the Number of MPI Processes

CompLaB3D uses Palabos domain decomposition and supports any number of MPI ranks. For best performance, choose a rank count that divides the domain dimensions (nx, ny, nz) approximately evenly.

| Domain size     | Suggested MPI ranks | Approximate voxels per rank |
| --------------- | ------------------- | --------------------------- |
| 50 × 50 × 50    | 4–8                 | ~15 000 – 30 000            |
| 100 × 100 × 100 | 8–16                | ~60 000 – 125 000           |
| 200 × 200 × 200 | 32–64               | ~125 000 (optimal)          |
| 400 × 400 × 400 | 128–256             | ~250 000                    |

Edit `#SBATCH --ntasks` (or PBS `ppn`, LSF `-n`) and the `mpirun -np` / `srun -n` value to match.

---

## 20. Startup Output and Stability Report

On launch, CompLaB3D prints a banner, configuration summary, and stability check:

```
╔══════════════════════════════════════════════════════════════════════╗
║                            CompLaB3D                                 ║
║       Three-Dimensional Biogeochemical Reactive Transport Model     ║
╚══════════════════════════════════════════════════════════════════════╝
...
╔════════════════════════════════════════════════════════════╗
║              STABILITY CHECK REPORT                        ║
╠════════════════════════════════════════════════════════════╣
║ Ma = 0.0231 OK   CFL = 0.0400 OK                          ║
║ tau_NS = 0.8000 OK   tau_ADE = 0.7500 OK                  ║
║ Pe_grid = 1.2000 OK                                        ║
╚════════════════════════════════════════════════════════════╝
```

If any criterion fails the model prints a descriptive error and exits before any computation.

**Stability criteria enforced:**

| Criterion           | Requirement                    | Physical meaning                             |
| ------------------- | ------------------------------ | -------------------------------------------- |
| Mach number         | Ma < 0.3 (warn) / < 1.0 (hard) | Low-velocity incompressible flow             |
| CFL                 | CFL = u_max < 1.0              | Numerical stability of streaming step        |
| NS relaxation time  | 0.5 < τ_NS < 2.0               | Viscosity physically representable           |
| ADE relaxation time | 0.5 < τ_ADE < 2.0              | Diffusivity physically representable         |
| Grid Péclet number  | Pe_grid < 2.0 (warn)           | Advection does not dominate per lattice cell |

---

## 21. Output Files (Cluster Runs)

All output goes to the `output/` folder (relative to where CompLaB.xml lives).
This duplicates the field list from §7 with the cluster-specific notes added:

| File                      | Format        | Content                                                       |
| ------------------------- | ------------- | ------------------------------------------------------------- |
| `substrate_NNNNNNN.vti`   | VTK ImageData | Concentration field at iteration N                            |
| `velocity_NNNNNNN.vti`    | VTK ImageData | Velocity field (u_x, u_y, u_z)                                |
| `biomass_NNNNNNN.vti`     | VTK ImageData | Biomass density field                                         |
| `maskLattice_NNNNNNN.vti` | VTK ImageData | Pore geometry / biofilm mask                                  |
| `checkpoint_NNNNNNN.chk`  | Binary        | Restart checkpoint (use with `read_NS_file`, `read_ADE_file`) |
| `btc_*.csv`               | CSV           | Breakthrough curve time series per substrate                  |
| `moments_summary.csv`     | CSV           | First and second spatial moments                              |
| `domain_properties.csv`   | CSV           | Porosity, permeability, Pe, Ma, CFL, τ                        |
| `simulation_*.out`        | Text          | Full model console log                                        |

Open VTI files in **ParaView** (`File → Open → select all substrate*.vti → Apply Filters`).

---

## 22. Editing Kinetics and Recompiling

The rate law functions live in C++ header files that are compiled **into** the model binary. Every time you edit them, you must rebuild.

**Biotic (Monod) kinetics** — `defineKinetics.hh`:

```cpp
// Rate of substrate uptake by microbe 0 from substrate 0:
void computeKinetics(T* C, T* B, T* rates) {
    T mu_max = 1.5e-5;   // [1/s]  maximum specific growth rate
    T K_s    = 1.0e-4;   // [mol/L] half-saturation constant
    rates[0] = -mu_max * C[0] / (K_s + C[0]) * B[0];  // substrate consumption
    rates[1] =  mu_max * C[0] / (K_s + C[0]) * B[0];  // biomass growth
}
```

**Abiotic kinetics** — `defineAbioticKinetics.hh`:

```cpp
void computeAbioticKinetics(T* C, T* rates) {
    T k = 1.0e-4;   // [1/s]  first-order decay constant
    rates[0] = -k * C[0];
}
```

After editing, rebuild:

```bash
# If using ComapLB3D/ standalone package:
cd ComapLB3D/build && make -j8

# If using root CMakeLists.txt:
cmake --build build --parallel 4
```

CMake detects the changed header and recompiles only the affected translation unit.

---

## 23. Validation Cases — Run-Through Procedure

Five complete validation cases in `test_cases/abiotic/` verify model correctness against closed-form analytical solutions (overview in §6). This section gives the full HPC run-through. Each case runs in a simple 1D channel geometry in under a minute.

| Case              | XML file                      | Kinetics header                      |
| ----------------- | ----------------------------- | ------------------------------------ |
| Pure diffusion    | `test1_pure_diffusion.xml`    | *(none — abiotic kinetics disabled)* |
| First-order decay | `test2_first_order_decay.xml` | `defineAbioticKinetics_test2.hh`     |
| Bimolecular       | `test3_bimolecular.xml`       | `defineAbioticKinetics_test3.hh`     |
| Reversible        | `test4_reversible.xml`        | `defineAbioticKinetics_test4.hh`     |
| Sequential decay  | `test5_decay_chain.xml`       | `defineAbioticKinetics_test5.hh`     |

**Run Test 2 (first-order decay):**

```bash
# 1. Copy the kinetics header
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh

# 2. Rebuild
cmake --build build --parallel 4

# 3. Run
./build/complab test_cases/abiotic/test2_first_order_decay.xml

# 4. Visualise in ParaView
paraview output_abiotic_test2_decay/substrate*.vti
```

**Dry-run check (XML + kinetics syntax only, no model needed):**

```bash
python tests/run_validation.py --dry-run
```

Expected output values and physical interpretation: `test_cases/abiotic/README.md`.

---

## 24. HPC / CLI Troubleshooting

| Symptom                                                        | Likely cause                                    | Fix                                                                       |
| -------------------------------------------------------------- | ----------------------------------------------- | ------------------------------------------------------------------------- |
| `cmake ..` fails with "Palabos not found"                      | `PLB_ROOT` path wrong                           | Set `-DPLB_ROOT=/absolute/path/to/palabos`                                |
| `make` fails: "undefined reference to `MPI_...`"               | MPI not loaded                                  | `module load openmpi` before building                                     |
| Linker fails: "incompatible architecture" on pre-built library | CPU/ABI mismatch                                | Delete `versionControl/palabos-v2.3.0/build/` and recompile Palabos       |
| Model exits immediately: "CompLaB.xml not found"               | Run from wrong directory                        | `cd` to the folder that contains `CompLaB.xml` before running             |
| Model exits: "geometry.dat not found"                          | Geometry file missing                           | Place it at `input/geometry.dat` (relative to CompLaB.xml)                |
| Model exits: "tau invalid"                                     | τ outside (0.5, 2.0]                            | Adjust `<tau>` in XML or change `<Peclet>` to get a different diffusivity |
| Results diverge / NaN                                          | CFL or Ma exceeded                              | Reduce `<delta_P>` or `<Peclet>`                                          |
| Job runs too slowly                                            | Too few MPI ranks or too many (memory overhead) | See §7 for recommended rank counts                                        |
| Recompile needed but `make` says "Nothing to do"               | CMake doesn't detect header change              | `touch defineKinetics.hh` then `make -j8`                                 |

---

---

# PART 3 — GUI Workflow Guide (CompLaB Studio)

CompLaB Studio is a desktop application that lets you configure, launch, and post-process CompLaB3D simulations without touching the command line. It is built with PySide6 and follows a COMSOL-style panel layout: one click per physics module, then press **Run**.

---

## 25. GUI Prerequisites

| Requirement     | Minimum version | Notes                                                                                   |
| --------------- | --------------- | --------------------------------------------------------------------------------------- |
| Python          | 3.10            | 3.11+ recommended                                                                       |
| PySide6         | 6.5.0           | Qt6 bindings                                                                            |
| NumPy           | 1.24.0          | Array ops                                                                               |
| VTK             | 9.2.0           | 3-D output viewer                                                                       |
| Matplotlib      | 3.7.0           | Convergence plots                                                                       |
| CompLaB3D model | any             | Must be compiled separately (see [Part 2](#part-2--standalone-hpc--command-line-guide)) |

The GUI does **not** include the C++ model. You must build (or obtain) the `complab` (Linux/macOS) or `complab.exe` (Windows) binary before pressing **Run**. On Windows, build in an MSYS2 MinGW64 shell; on Linux/macOS, use CMake + GCC/Clang.

---

## 26. GUI Installation

```bash
# Clone the repository
git clone https://github.com/your-org/CompLaB3D.git
cd CompLaB3D/JOSS_Submit/GUI

# Install runtime dependencies
pip install -r requirements.txt

# (Optional) install development/testing extras
pip install -r requirements-dev.txt
```

`requirements.txt` contains:

```
PySide6>=6.5.0
numpy>=1.24.0
vtk>=9.2.0
matplotlib>=3.7.0
```

> **Conda users:** `conda install -c conda-forge pyside6 vtk matplotlib numpy` works equally well; the pip step above is not required.

> **Windows note:** If PySide6 or VTK wheels fail to install, ensure you are using Python 3.10–3.12 (64-bit) and have the latest pip: `python -m pip install --upgrade pip`.

---

## 27. Launching the GUI

```bash
cd JOSS_Submit/GUI
python main.py
```

Or, if installed as a package:

```bash
complab-studio
```

The application window opens at approximately 1400 × 900 pixels. On first launch it shows the **New Project** dialog automatically.

---

## 28. Interface Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  Menu bar:  File │ Edit │ Simulation │ Tools │ Help             │
├──────────┬──────────────────────────────────┬───────────────────┤
│  Model   │                                  │                   │
│  Tree    │   Configuration Panels           │  Run / Console    │
│  (left)  │   (center — scrollable tabs)     │  (right)          │
│          │                                  │                   │
│  • General│  Domain → Geometry → Chemistry  │  ▶ Run Simulation │
│  • Domain │  → Equilibrium → Microbiology   │  Console output   │
│  • Geom  │  → Model → I/O → Parallel      │  Convergence plot │
│  • Chem  │  → Post-process                  │  Stop / Save log  │
│  • ...   │                                  │                   │
└──────────┴──────────────────────────────────┴───────────────────┘
```

Clicking any item in the **Model Tree** (left) jumps to the corresponding panel (center). Changes in any panel are reflected immediately in the model tree and in the project data — there is no separate "Apply" button.

---

## 29. Step-by-Step Workflow

### Step 1 — Create or open a project

**File → New Project** (or `Ctrl+N`) opens the **New Project** wizard.

Select one of nine built-in templates:

| Template                             | Physics active                          |
| ------------------------------------ | --------------------------------------- |
| Flow Only                            | Navier-Stokes (no ADE, no reactions)    |
| Diffusion Only                       | Pure ADE (Pe = 0, no reactions)         |
| Tracer Transport (Flow + Diffusion)  | NS + ADE passive tracer                 |
| Abiotic Reaction (First-Order Decay) | NS + ADE + abiotic kinetics             |
| Abiotic Equilibrium (Carbonate)      | NS + ADE + equilibrium speciation       |
| Biofilm — Sessile (CA Model)         | NS + ADE + biotic CA                    |
| Planktonic Bacteria (LBM Model)      | NS + ADE + biotic LBM                   |
| Sessile + Planktonic (Dual Microbe)  | NS + ADE + CA + LBM                     |
| Coupled Biotic-Abiotic               | NS + ADE + biotic CA + abiotic kinetics |

The right-hand panel of the wizard shows a **Template Details** summary, lists which kinetics `.hh` files are required, allows you to preview the generated C++ code, and gives step-by-step compilation instructions for that template.

Give the project a name and choose a save directory, then click **Create**. The project folder is created immediately and contains:

```
<project_name>/
├── <project_name>.complab     ← project JSON (GUI state)
├── CompLaB.xml                ← model input (auto-generated on Run)
├── defineKinetics.hh          ← biotic kinetics (if applicable)
├── defineAbioticKinetics.hh   ← abiotic kinetics (if applicable)
├── input/
│   └── geometry.dat           ← porous geometry voxel file
└── output/                    ← VTI / CHK files written by model
```

To open an existing project: **File → Open Project** and select the `.complab` file.

---

### Step 2 — Domain panel

Set the lattice dimensions and physical units.

| Field                             | Description                                 |
| --------------------------------- | ------------------------------------------- |
| Nx / Ny / Nz                      | Grid size in voxels                         |
| dx                                | Voxel edge length (μm, nm, or m)            |
| Characteristic length             | Used to compute the Péclet number           |
| Geometry file                     | Path to `geometry.dat` (integer voxel mask) |
| Pore / Solid / Bounce-back labels | Integer codes in `geometry.dat`             |

The **Geometry Preview** button opens an interactive 3-D view of the loaded `geometry.dat` so you can verify the porous structure before running.

---

### Step 3 — Geometry panel

Use the built-in **Geometry Creator** dialog (**Tools → Geometry Creator**) to generate standard test geometries or import a custom one.

Available generators:

- **Open channel** — fully open rectangular tube (all pore voxels)
- **Sphere pack** — random or structured sphere packing
- **Slit pore** — flat plate channel with adjustable aperture
- **Import raw** — load an external integer-valued 3-D array

Generated geometries are saved as `input/geometry.dat` (space-delimited integers, one slice per block, `0` = solid, `1` = bounce-back (wall), `2` = pore).

---

### Step 4 — Fluid panel

Set Navier-Stokes parameters.

| Field                 | Description                                                                       |
| --------------------- | --------------------------------------------------------------------------------- |
| ΔP (delta_P)          | Pressure drop across the domain (LB units)                                        |
| Péclet number         | Pe = U·L / D; controls advection vs. diffusion                                    |
| Tau (relaxation time) | LBM relaxation; must satisfy 0.5 < τ ≤ 2.0; τ = 0.8 is stable for most geometries |
| Track performance     | Write per-step timing to log                                                      |

> **Stability rule:** τ = 1/(Re/Pe + 0.5) internally; for tracer runs with Pe ≈ 1–10 and τ = 0.8 the model is unconditionally stable. Avoid τ < 0.6 unless Re is very small.

---

### Step 5 — Chemistry panel

Add one or more substrates and configure each one's transport and boundary conditions.

**Add / Remove** buttons manage the substrate list. Selecting a substrate in the list loads its properties into the editor below.

| Field                 | Description                                                                                                                          |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Name                  | Label used in XML and VTK outputs                                                                                                    |
| Initial concentration | Uniform initial value (mol/L or dimensionless)                                                                                       |
| Diffusion in pore     | Molecular diffusivity in open pore space (m²/s)                                                                                      |
| Diffusion in biofilm  | Effective diffusivity inside biofilm (typically 0.2–0.5× pore value). Written to XML always; ignored by model in abiotic/tracer runs |
| Left / Right BC type  | Dirichlet (fixed concentration) or Neumann (zero-flux)                                                                               |
| Left / Right BC value | Concentration for Dirichlet; always 0.0 for Neumann                                                                                  |

Typical setup for a reactive transport run:

- Left BC: Dirichlet = inlet concentration
- Right BC: Neumann = 0 (outflow, no-flux condition)

---

### Step 6 — Equilibrium panel (optional)

Enable carbonate-type equilibrium speciation. This is only needed if your system includes fast acid-base reactions that should be treated as instantaneous equilibria rather than kinetic reactions.

| Field                | Description                                     |
| -------------------- | ----------------------------------------------- |
| Enable equilibrium   | Toggle                                          |
| Component names      | Species names (e.g., HCO3-, H+)                 |
| Stoichiometry matrix | One row per substrate, one column per component |
| Log K values         | Log₁₀ of equilibrium constants                  |

For most reactive transport problems this panel can be left disabled.

---

### Step 7 — Microbiology panel (biotic runs only)

Visible only when **Biotic Mode** is enabled on the General panel.

**Global settings:**

| Field                      | Description                                                 |
| -------------------------- | ----------------------------------------------------------- |
| Maximum biomass density    | Carrying capacity (g/m³ or mol/m³)                          |
| Biofilm fraction threshold | Volume fraction at which voxel is classified as biofilm     |
| CA method                  | Spreading rule for CA biofilm growth (`half` or `fraction`) |

**Per-microbe settings** (Add / Remove buttons manage the microbe list):

| Field                      | Description                                                                                                        |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Name                       | Label for this microbial species                                                                                   |
| Model type                 | `CA` (sessile biofilm) or `LBM` (planktonic)                                                                       |
| Reaction type              | `kinetics` (Monod)                                                                                                 |
| Material number            | Voxel codes in `geometry.dat` where microbes are seeded (space-separated integers; leave blank for LBM planktonic) |
| Initial densities          | Biomass density at each seeding location (one per material number)                                                 |
| Decay coefficient          | First-order endogenous decay rate (1/s)                                                                            |
| Viscosity ratio in biofilm | How much biofilm increases local fluid viscosity                                                                   |
| Half-saturation constants  | Ks for each substrate (space-separated, one per substrate)                                                         |
| Maximum uptake flux        | qmax for each substrate (space-separated)                                                                          |
| Left / Right BC type       | Dirichlet or Neumann for the biomass field                                                                         |
| Left BC value              | Inlet biomass concentration (Dirichlet only)                                                                       |

---

### Step 8 — Model panel

| Field                              | Description                                              |
| ---------------------------------- | -------------------------------------------------------- |
| NS max iterations (phase 1)        | Navier-Stokes iterations before convergence check begins |
| NS max iterations (phase 2)        | Maximum NS iterations after phase 1                      |
| NS convergence tolerance (phase 1) | Velocity residual threshold for phase 1 end              |
| NS convergence tolerance (phase 2) | Velocity residual threshold for final convergence        |
| ADE max iterations                 | Maximum advection-diffusion iterations                   |
| ADE convergence tolerance          | Concentration residual threshold                         |

For a first test run, the defaults from the selected template are appropriate. Increase ADE iterations for long reactive transport simulations.

---

### Step 9 — I/O panel

| Field               | Description                                    |
| ------------------- | ---------------------------------------------- |
| VTK output interval | Write `.vti` files every N ADE steps           |
| Checkpoint interval | Write `.chk` restart file every N steps        |
| Output directory    | Relative or absolute path (default: `output/`) |

---

### Step 10 — Parallel panel

Configure MPI decomposition for multi-core runs.

| Field                   | Description                                            |
| ----------------------- | ------------------------------------------------------ |
| Number of MPI processes | Total MPI ranks (`-np` value passed to `mpirun`)       |
| Domain decomposition    | Automatic (Palabos chooses) or manual (Nx×Ny×Nz ranks) |

For workstation runs, set **Number of MPI processes** to the number of physical CPU cores. For single-core testing, use 1.

> The model always uses MPI even for `np = 1`. Ensure `mpirun` (OpenMPI or MPICH) is in your `PATH`.

---

## 30. Panel Reference

Quick lookup of all panels and what they control:

| Panel        | Key parameters                                                                  |
| ------------ | ------------------------------------------------------------------------------- |
| General      | Simulation mode (biotic/abiotic), enable kinetics flags, validation diagnostics |
| Domain       | Grid dimensions, dx, geometry file, voxel labels                                |
| Geometry     | Geometry creator / importer                                                     |
| Fluid        | ΔP, Pe, τ, performance tracking                                                 |
| Chemistry    | Substrates: name, C₀, D_pore, D_biofilm, BCs                                    |
| Equilibrium  | Fast equilibrium speciation (carbonate system)                                  |
| Microbiology | Microbes: model type, Monod parameters, BCs                                     |
| Model        | NS and ADE iteration counts and tolerances                                      |
| I/O          | VTK interval, checkpoint interval, output directory                             |
| Parallel     | MPI process count, domain decomposition                                         |
| Sweep        | (Advanced) Parameter sweep over any XML field                                   |
| Post-process | Built-in VTK slice viewer and convergence plot                                  |
| Run          | Launch / stop simulation, real-time console, log export                         |

---

## 31. Kinetics Editor

Open via **Tools → Kinetics Editor** or the **Edit Kinetics** button on the Run panel.

The Kinetics Editor is a syntax-highlighted C++ code editor for `defineKinetics.hh` (biotic Monod reactions) and `defineAbioticKinetics.hh` (abiotic first-order or arbitrary reactions). These files are `#include`d directly into the model at compile time.

**Workflow:**

1. Open the Kinetics Editor.

2. Edit the reaction rate expressions. The substrate concentration array is `C[i]` (indexed in the same order as the Chemistry panel). The microbe density array is `B[i]`.

3. Click **Save** — the `.hh` file is written to the project directory.

4. **Recompile the model** in your build directory:
   
   ```bash
   # Copy .hh files to model source root
   cp defineKinetics.hh       /path/to/CompLaB3D/src/../
   cp defineAbioticKinetics.hh /path/to/CompLaB3D/src/../
   
   # Recompile
   cd /path/to/CompLaB3D/build
   cmake ..
   make -j$(nproc)
   ```

5. Point the GUI to the newly compiled executable in **Preferences → General → CompLaB executable**.

> **Important:** Every time you change kinetics, you must recompile. The GUI cannot recompile for you; it only edits and saves the source file.

The New Project wizard shows template kinetics code as a preview (click **Preview defineKinetics.hh**) so you can understand the expected structure before editing.

---

## 32. Running a Simulation

### Pre-flight checks

When you click **▶ Run Simulation**, the GUI performs these checks automatically before launching the model:

1. Verifies the CompLaB executable exists and is executable.
2. Exports `CompLaB.xml` to the project directory.
3. Deploys `geometry.dat` to `input/geometry.dat` if not already present.
4. Checks that `defineKinetics.hh` and `defineAbioticKinetics.hh` exist (if kinetics are enabled).
5. Validates that τ is in the safe range (0.5, 2.0].

If any check fails, an error dialog lists what is missing before any model process is started.

### Launch command

The GUI runs:

```bash
mpirun -np <N> <complab_executable> CompLaB.xml
```

from the project directory. Standard output and stderr are captured and displayed in the console widget in real time.

### During a run

The **Run panel** (right column) shows:

- **Console** — scrollable live output from the model, colour-coded (warnings in amber, errors in red).
- **Convergence plot** — residual vs. iteration, updated every model output line. Two curves: NS (blue) and ADE (orange).
- **Stop** button — sends SIGTERM to the model process; partial output files are retained.
- **Save Log** button — writes the full console output to a `.out` file in the project `output/` directory.

### Output files written by the model

| File                                    | Description                                    |
| --------------------------------------- | ---------------------------------------------- |
| `output/nsLatticeFinal1_XXXXXXX.vti`    | NS velocity field at final iteration           |
| `output/adeLatticeFinal_N_XXXXXXX.vti`  | ADE concentration field for substrate N        |
| `output/biomassFinal_M_XXXXXXX.vti`     | Biomass field for microbe M (biotic only)      |
| `output/inputGeom.vti`                  | Geometry voxel field (written once at startup) |
| `output/nsLattice.chk`                  | NS checkpoint (restart file)                   |
| `output/simulation_TIMESTAMP.out`       | Full model log                                 |
| `output/crash_diagnostic_TIMESTAMP.txt` | Diagnostic dump on abnormal exit               |

All `.vti` files use VTK Image Data format and can be opened in [ParaView](https://www.paraview.org/) or the built-in viewer.

---

## 33. Post-Processing

### Built-in viewer

The **Post-process panel** provides a lightweight 3-D slice viewer powered by VTK.

1. Click **Load VTI** and select any `.vti` file from the `output/` directory.
2. Use the **X / Y / Z slice** sliders to navigate through the volume.
3. Choose the scalar field to display from the drop-down (velocity magnitude, concentration, biomass density, etc.).
4. Click **Export PNG** to save the current slice as an image.

The convergence plot (residual vs. iteration) can be exported as PDF via **File → Export Convergence Plot**.

### ParaView (recommended for publication figures)

For full-featured visualization — volume rendering, streamlines, animations — open the `.vti` files in [ParaView](https://www.paraview.org/) (free, cross-platform).

```
File → Open → select output/nsLatticeFinal1_*.vti
Apply
Filters → Slice → set normal and origin
Filters → Warp By Scalar (for concentration isosurfaces)
```

All CompLaB3D `.vti` files use SI units internally. The model writes the `dx` spacing into the VTK header so ParaView displays physical coordinates automatically.

---

## 34. Project Files and XML Export

### `.complab` project file

The project is saved as a JSON file (`<name>.complab`) that stores the complete GUI state: all panel values, substrate list, microbe list, preferences snapshot, and the paths to kinetics files. This file is the source of truth for the GUI; `CompLaB.xml` is always regenerated from it before a run.

Save: **File → Save** (`Ctrl+S`)
Save As: **File → Save As** (`Ctrl+Shift+S`)

Auto-save can be enabled in **Preferences → General** with a configurable interval (30–3600 s).

### Manual XML export

To export `CompLaB.xml` without launching a run (e.g., to transfer to a cluster):

**Simulation → Export XML** (`Ctrl+E`)

The exported file is a fully self-contained model input. Copy it along with `defineKinetics.hh`, `defineAbioticKinetics.hh`, and `input/geometry.dat` to any machine that has the compiled model.

### XML structure (key sections)

```xml
<CompLaB>
  <simulation_mode> ... </simulation_mode>   <!-- biotic, kinetics flags -->
  <domain> ... </domain>                     <!-- nx, ny, nz, dx, geometry file -->
  <fluid> ... </fluid>                       <!-- delta_P, Pe, tau -->
  <substrates>
    <substrate id="0"> ... </substrate>      <!-- name, C0, D_pore, D_biofilm, BCs -->
  </substrates>
  <microbiology> ... </microbiology>         <!-- microbes, Monod params -->
  <equilibrium> ... </equilibrium>           <!-- log-K matrix (optional) -->
  <iterations> ... </iterations>             <!-- NS/ADE max iT, tolerances -->
  <io> ... </io>                             <!-- VTK/CHK intervals, output dir -->
  <parallel> ... </parallel>                 <!-- MPI decomposition -->
</CompLaB>
```

---

## 35. Preferences

Open via **Edit → Preferences** (`Ctrl+,`).

### General tab

| Setting                   | Description                                                                                                |
| ------------------------- | ---------------------------------------------------------------------------------------------------------- |
| CompLaB executable        | Absolute path to the compiled model binary. Leave blank to auto-detect `complab` / `complab.exe` on `PATH` |
| Default project directory | Default save location for new projects                                                                     |
| Enable auto-save          | Periodically save the `.complab` file                                                                      |
| Auto-save interval        | Seconds between auto-saves (30–3600)                                                                       |

### Display tab

| Setting           | Description                                                    |
| ----------------- | -------------------------------------------------------------- |
| Font size         | Application font size in points (8–18 pt); applied immediately |
| Max console lines | Maximum lines retained in the run console (500–100 000)        |
| Theme             | Dark (default) or Light; applied immediately on save           |

Changes to theme and font take effect instantly without restarting the application.

---

## 36. GUI Test Suite

The GUI ships with 362 automated tests covering all panels, the project data model, XML round-tripping, the kinetics editor, and the simulation runner stub.

```bash
cd JOSS_Submit/GUI
pip install -r requirements-dev.txt   # adds pytest and pytest-qt
pytest tests/ -v
```

Expected output:

```
tests/test_config.py              ...    PASSED
tests/test_gui_panels.py          ...    PASSED   (requires display or Xvfb)
tests/test_kinetics.py            ...    PASSED
tests/test_pipeline_e2e.py        ...    PASSED
tests/test_project_model.py       ...    PASSED
tests/test_simulation_runner.py   ...    PASSED
tests/test_templates.py           ...    PASSED
tests/test_xml_diagnostic.py      ...    PASSED
tests/test_xml_io.py              ...    PASSED
362 passed in ~12 s
```

On a headless Linux server (CI), run with a virtual framebuffer:

```bash
Xvfb :99 -screen 0 1280x1024x24 &
DISPLAY=:99 pytest tests/ -v
```

---

## 37. GUI Troubleshooting

| Problem                              | Likely cause                                | Fix                                                                                                       |
| ------------------------------------ | ------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| `ModuleNotFoundError: PySide6`       | Dependencies not installed                  | `pip install -r requirements.txt`                                                                         |
| `ModuleNotFoundError: vtkmodules`    | VTK not installed                           | `pip install vtk` (Python 3.10–3.12 only)                                                                 |
| Window opens but panels are blank    | Qt platform plugin missing (Linux headless) | Set `DISPLAY=:0` or install `libxcb-util-dev`                                                             |
| "CompLaB execut