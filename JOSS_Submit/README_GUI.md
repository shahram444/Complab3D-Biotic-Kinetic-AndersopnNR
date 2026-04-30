# CompLaB Studio — GUI Workflow Guide

CompLaB Studio is a desktop application that lets you configure, launch, and post-process CompLaB3D simulations without touching the command line. It is built with PySide6 and follows a COMSOL-style panel layout: one click per physics module, then press **Run**.

→ For headless / HPC cluster use, see [README_Standalone_HPC.md](README_Standalone_HPC.md)
→ For overview, tests, citation, and license, see [README.md](README.md)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installation](#2-installation)
3. [Launching the GUI](#3-launching-the-gui)
4. [Interface Overview](#4-interface-overview)
5. [Step-by-Step Workflow](#5-step-by-step-workflow)
6. [Panel Reference](#6-panel-reference)
7. [Kinetics Editor](#7-kinetics-editor)
8. [Running a Simulation](#8-running-a-simulation)
9. [Post-Processing](#9-post-processing)
10. [Project Files and XML Export](#10-project-files-and-xml-export)
11. [Preferences](#11-preferences)
12. [GUI Test Suite](#12-gui-test-suite)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Prerequisites

| Requirement | Minimum version | Notes |
|---|---|---|
| Python | 3.10 | 3.11+ recommended |
| PySide6 | 6.5.0 | Qt6 bindings |
| NumPy | 1.24.0 | Array ops |
| VTK | 9.2.0 | 3-D output viewer |
| Matplotlib | 3.7.0 | Convergence plots |
| CompLaB3D solver | any | Must be compiled separately (see [README_Standalone_HPC.md](README_Standalone_HPC.md)) |

The GUI does **not** include the C++ solver. You must build (or obtain) the `complab` (Linux/macOS) or `complab.exe` (Windows) binary before pressing **Run**. On Windows, build in an MSYS2 MinGW64 shell; on Linux/macOS, use CMake + GCC/Clang.

---

## 2. Installation

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

## 3. Launching the GUI

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

## 4. Interface Overview

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
│  • Geom  │  → Solver → I/O → Parallel      │  Convergence plot │
│  • Chem  │  → Post-process                  │  Stop / Save log  │
│  • ...   │                                  │                   │
└──────────┴──────────────────────────────────┴───────────────────┘
```

Clicking any item in the **Model Tree** (left) jumps to the corresponding panel (center). Changes in any panel are reflected immediately in the model tree and in the project data — there is no separate "Apply" button.

---

## 5. Step-by-Step Workflow

### Step 1 — Create or open a project

**File → New Project** (or `Ctrl+N`) opens the **New Project** wizard.

Select one of nine built-in templates:

| Template | Physics active |
|---|---|
| Flow Only | Navier-Stokes (no ADE, no reactions) |
| Diffusion Only | Pure ADE (Pe = 0, no reactions) |
| Tracer Transport (Flow + Diffusion) | NS + ADE passive tracer |
| Abiotic Reaction (First-Order Decay) | NS + ADE + abiotic kinetics |
| Abiotic Equilibrium (Carbonate) | NS + ADE + equilibrium speciation |
| Biofilm — Sessile (CA Solver) | NS + ADE + biotic CA |
| Planktonic Bacteria (LBM Solver) | NS + ADE + biotic LBM |
| Sessile + Planktonic (Dual Microbe) | NS + ADE + CA + LBM |
| Coupled Biotic-Abiotic | NS + ADE + biotic CA + abiotic kinetics |

The right-hand panel of the wizard shows a **Template Details** summary, lists which kinetics `.hh` files are required, allows you to preview the generated C++ code, and gives step-by-step compilation instructions for that template.

Give the project a name and choose a save directory, then click **Create**. The project folder is created immediately and contains:

```
<project_name>/
├── <project_name>.complab     ← project JSON (GUI state)
├── CompLaB.xml                ← solver input (auto-generated on Run)
├── defineKinetics.hh          ← biotic kinetics (if applicable)
├── defineAbioticKinetics.hh   ← abiotic kinetics (if applicable)
├── input/
│   └── geometry.dat           ← porous geometry voxel file
└── output/                    ← VTI / CHK files written by solver
```

To open an existing project: **File → Open Project** and select the `.complab` file.

---

### Step 2 — Domain panel

Set the lattice dimensions and physical units.

| Field | Description |
|---|---|
| Nx / Ny / Nz | Grid size in voxels |
| dx | Voxel edge length (μm, nm, or m) |
| Characteristic length | Used to compute the Péclet number |
| Geometry file | Path to `geometry.dat` (integer voxel mask) |
| Pore / Solid / Bounce-back labels | Integer codes in `geometry.dat` |

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

| Field | Description |
|---|---|
| ΔP (delta_P) | Pressure drop across the domain (LB units) |
| Péclet number | Pe = U·L / D; controls advection vs. diffusion |
| Tau (relaxation time) | LBM relaxation; must satisfy 0.5 < τ ≤ 2.0; τ = 0.8 is stable for most geometries |
| Track performance | Write per-step timing to log |

> **Stability rule:** τ = 1/(Re/Pe + 0.5) internally; for tracer runs with Pe ≈ 1–10 and τ = 0.8 the solver is unconditionally stable. Avoid τ < 0.6 unless Re is very small.

---

### Step 5 — Chemistry panel

Add one or more substrates and configure each one's transport and boundary conditions.

**Add / Remove** buttons manage the substrate list. Selecting a substrate in the list loads its properties into the editor below.

| Field | Description |
|---|---|
| Name | Label used in XML and VTK outputs |
| Initial concentration | Uniform initial value (mol/L or dimensionless) |
| Diffusion in pore | Molecular diffusivity in open pore space (m²/s) |
| Diffusion in biofilm | Effective diffusivity inside biofilm (typically 0.2–0.5× pore value). Written to XML always; ignored by solver in abiotic/tracer runs |
| Left / Right BC type | Dirichlet (fixed concentration) or Neumann (zero-flux) |
| Left / Right BC value | Concentration for Dirichlet; always 0.0 for Neumann |

Typical setup for a reactive transport run:
- Left BC: Dirichlet = inlet concentration
- Right BC: Neumann = 0 (outflow, no-flux condition)

---

### Step 6 — Equilibrium panel (optional)

Enable carbonate-type equilibrium speciation. This is only needed if your system includes fast acid-base reactions that should be treated as instantaneous equilibria rather than kinetic reactions.

| Field | Description |
|---|---|
| Enable equilibrium | Toggle |
| Component names | Species names (e.g., HCO3-, H+) |
| Stoichiometry matrix | One row per substrate, one column per component |
| Log K values | Log₁₀ of equilibrium constants |

For most reactive transport problems this panel can be left disabled.

---

### Step 7 — Microbiology panel (biotic runs only)

Visible only when **Biotic Mode** is enabled on the General panel.

**Global settings:**

| Field | Description |
|---|---|
| Maximum biomass density | Carrying capacity (g/m³ or mol/m³) |
| Biofilm fraction threshold | Volume fraction at which voxel is classified as biofilm |
| CA method | Spreading rule for CA biofilm growth (`half` or `fraction`) |

**Per-microbe settings** (Add / Remove buttons manage the microbe list):

| Field | Description |
|---|---|
| Name | Label for this microbial species |
| Solver type | `CA` (sessile biofilm) or `LBM` (planktonic) |
| Reaction type | `kinetics` (Monod) |
| Material number | Voxel codes in `geometry.dat` where microbes are seeded (space-separated integers; leave blank for LBM planktonic) |
| Initial densities | Biomass density at each seeding location (one per material number) |
| Decay coefficient | First-order endogenous decay rate (1/s) |
| Viscosity ratio in biofilm | How much biofilm increases local fluid viscosity |
| Half-saturation constants | Ks for each substrate (space-separated, one per substrate) |
| Maximum uptake flux | qmax for each substrate (space-separated) |
| Left / Right BC type | Dirichlet or Neumann for the biomass field |
| Left BC value | Inlet biomass concentration (Dirichlet only) |

---

### Step 8 — Solver panel

| Field | Description |
|---|---|
| NS max iterations (phase 1) | Navier-Stokes iterations before convergence check begins |
| NS max iterations (phase 2) | Maximum NS iterations after phase 1 |
| NS convergence tolerance (phase 1) | Velocity residual threshold for phase 1 end |
| NS convergence tolerance (phase 2) | Velocity residual threshold for final convergence |
| ADE max iterations | Maximum advection-diffusion iterations |
| ADE convergence tolerance | Concentration residual threshold |

For a first test run, the defaults from the selected template are appropriate. Increase ADE iterations for long reactive transport simulations.

---

### Step 9 — I/O panel

| Field | Description |
|---|---|
| VTK output interval | Write `.vti` files every N ADE steps |
| Checkpoint interval | Write `.chk` restart file every N steps |
| Output directory | Relative or absolute path (default: `output/`) |

---

### Step 10 — Parallel panel

Configure MPI decomposition for multi-core runs.

| Field | Description |
|---|---|
| Number of MPI processes | Total MPI ranks (`-np` value passed to `mpirun`) |
| Domain decomposition | Automatic (Palabos chooses) or manual (Nx×Ny×Nz ranks) |

For workstation runs, set **Number of MPI processes** to the number of physical CPU cores. For single-core testing, use 1.

> The solver always uses MPI even for `np = 1`. Ensure `mpirun` (OpenMPI or MPICH) is in your `PATH`.

---

## 6. Panel Reference

Quick lookup of all panels and what they control:

| Panel | Key parameters |
|---|---|
| General | Simulation mode (biotic/abiotic), enable kinetics flags, validation diagnostics |
| Domain | Grid dimensions, dx, geometry file, voxel labels |
| Geometry | Geometry creator / importer |
| Fluid | ΔP, Pe, τ, performance tracking |
| Chemistry | Substrates: name, C₀, D_pore, D_biofilm, BCs |
| Equilibrium | Fast equilibrium speciation (carbonate system) |
| Microbiology | Microbes: solver type, Monod parameters, BCs |
| Solver | NS and ADE iteration counts and tolerances |
| I/O | VTK interval, checkpoint interval, output directory |
| Parallel | MPI process count, domain decomposition |
| Sweep | (Advanced) Parameter sweep over any XML field |
| Post-process | Built-in VTK slice viewer and convergence plot |
| Run | Launch / stop simulation, real-time console, log export |

---

## 7. Kinetics Editor

Open via **Tools → Kinetics Editor** or the **Edit Kinetics** button on the Run panel.

The Kinetics Editor is a syntax-highlighted C++ code editor for `defineKinetics.hh` (biotic Monod reactions) and `defineAbioticKinetics.hh` (abiotic first-order or arbitrary reactions). These files are `#include`d directly into the solver at compile time.

**Workflow:**

1. Open the Kinetics Editor.
2. Edit the reaction rate expressions. The substrate concentration array is `C[i]` (indexed in the same order as the Chemistry panel). The microbe density array is `B[i]`.
3. Click **Save** — the `.hh` file is written to the project directory.
4. **Recompile the solver** in your build directory:
   ```bash
   # Copy .hh files to solver source root
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

## 8. Running a Simulation

### Pre-flight checks

When you click **▶ Run Simulation**, the GUI performs these checks automatically before launching the solver:

1. Verifies the CompLaB executable exists and is executable.
2. Exports `CompLaB.xml` to the project directory.
3. Deploys `geometry.dat` to `input/geometry.dat` if not already present.
4. Checks that `defineKinetics.hh` and `defineAbioticKinetics.hh` exist (if kinetics are enabled).
5. Validates that τ is in the safe range (0.5, 2.0].

If any check fails, an error dialog lists what is missing before any solver process is started.

### Launch command

The GUI runs:

```bash
mpirun -np <N> <complab_executable> CompLaB.xml
```

from the project directory. Standard output and stderr are captured and displayed in the console widget in real time.

### During a run

The **Run panel** (right column) shows:

- **Console** — scrollable live output from the solver, colour-coded (warnings in amber, errors in red).
- **Convergence plot** — residual vs. iteration, updated every solver output line. Two curves: NS (blue) and ADE (orange).
- **Stop** button — sends SIGTERM to the solver process; partial output files are retained.
- **Save Log** button — writes the full console output to a `.out` file in the project `output/` directory.

### Output files written by the solver

| File | Description |
|---|---|
| `output/nsLatticeFinal1_XXXXXXX.vti` | NS velocity field at final iteration |
| `output/adeLatticeFinal_N_XXXXXXX.vti` | ADE concentration field for substrate N |
| `output/biomassFinal_M_XXXXXXX.vti` | Biomass field for microbe M (biotic only) |
| `output/inputGeom.vti` | Geometry voxel field (written once at startup) |
| `output/nsLattice.chk` | NS checkpoint (restart file) |
| `output/simulation_TIMESTAMP.out` | Full solver log |
| `output/crash_diagnostic_TIMESTAMP.txt` | Diagnostic dump on abnormal exit |

All `.vti` files use VTK Image Data format and can be opened in [ParaView](https://www.paraview.org/) or the built-in viewer.

---

## 9. Post-Processing

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

All CompLaB3D `.vti` files use SI units internally. The solver writes the `dx` spacing into the VTK header so ParaView displays physical coordinates automatically.

---

## 10. Project Files and XML Export

### `.complab` project file

The project is saved as a JSON file (`<name>.complab`) that stores the complete GUI state: all panel values, substrate list, microbe list, preferences snapshot, and the paths to kinetics files. This file is the source of truth for the GUI; `CompLaB.xml` is always regenerated from it before a run.

Save: **File → Save** (`Ctrl+S`)
Save As: **File → Save As** (`Ctrl+Shift+S`)

Auto-save can be enabled in **Preferences → General** with a configurable interval (30–3600 s).

### Manual XML export

To export `CompLaB.xml` without launching a run (e.g., to transfer to a cluster):

**Simulation → Export XML** (`Ctrl+E`)

The exported file is a fully self-contained solver input. Copy it along with `defineKinetics.hh`, `defineAbioticKinetics.hh`, and `input/geometry.dat` to any machine that has the compiled solver.

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

## 11. Preferences

Open via **Edit → Preferences** (`Ctrl+,`).

### General tab

| Setting | Description |
|---|---|
| CompLaB executable | Absolute path to the compiled solver binary. Leave blank to auto-detect `complab` / `complab.exe` on `PATH` |
| Default project directory | Default save location for new projects |
| Enable auto-save | Periodically save the `.complab` file |
| Auto-save interval | Seconds between auto-saves (30–3600) |

### Display tab

| Setting | Description |
|---|---|
| Font size | Application font size in points (8–18 pt); applied immediately |
| Max console lines | Maximum lines retained in the run console (500–100 000) |
| Theme | Dark (default) or Light; applied immediately on save |

Changes to theme and font take effect instantly without restarting the application.

---

## 12. GUI Test Suite

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

## 13. Troubleshooting

| Problem | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: PySide6` | Dependencies not installed | `pip install -r requirements.txt` |
| `ModuleNotFoundError: vtkmodules` | VTK not installed | `pip install vtk` (Python 3.10–3.12 only) |
| Window opens but panels are blank | Qt platform plugin missing (Linux headless) | Set `DISPLAY=:0` or install `libxcb-util-dev` |
| "CompLaB executable not found" error | Solver not compiled or path not set | Build solver (see [README_Standalone_HPC.md](README_Standalone_HPC.md)), then set path in Preferences |
| "mpirun: command not found" | MPI not installed | Install `openmpi` or `mpich` via package manager |
| Solver crashes immediately (Windows) | omega=0 bug in older builds | Rebuild solver from latest source; this bug is patched |
| Solver crashes immediately (Linux) | Wrong MPI library version | Recompile with the same MPI library that is on `PATH` |
| Run panel shows no output | Executable did not start | Check the crash diagnostic file in `output/` |
| VTI file empty / zero bytes | Solver exited before writing output | Lower the VTK interval or increase max iterations |
| Geometry preview is black | `geometry.dat` not found or all-solid | Check file path in Domain panel; verify at least one voxel = 2 (pore) |
| Kinetics changes not reflected | `.hh` files modified but solver not recompiled | Recompile solver after every kinetics edit (see Section 7) |
| Auto-save conflicts with manual save | Race condition on network drives | Use a local project directory; auto-save is safe on local SSD |
| Theme does not switch | Qt style cache | Restart the application |
| `pytest` GUI tests fail on macOS | Qt accessibility security prompt | Run tests from a terminal launched via Finder, not SSH |
