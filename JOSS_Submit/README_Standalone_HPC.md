# CompLaB3D — Standalone HPC & Command-Line Guide

This guide covers everything you need to build and run CompLaB3D on an HPC cluster or local Linux/macOS/Windows machine **without the GUI**. All configuration is done by editing two files: `CompLaB.xml` (parameters) and `defineKinetics.hh` / `defineAbioticKinetics.hh` (rate laws).

→ For the GUI workflow, see [README_GUI.md](README_GUI.md)
→ For overview, tests, citation, and license, see [README.md](README.md)

---

## Table of Contents

1. [Two Ways to Get the Solver](#1-two-ways-to-get-the-solver)
2. [Option A — Standalone Package (ComapLB3D): Recommended for Clusters](#2-option-a--standalone-package-comaplb3d-recommended-for-clusters)
3. [Option B — Build from Source (Full Repo)](#3-option-b--build-from-source-full-repo)
4. [Configuring a Simulation](#4-configuring-a-simulation)
5. [Running the Solver](#5-running-the-solver)
6. [HPC Job Submission — All Scheduler Types](#6-hpc-job-submission--all-scheduler-types)
7. [Choosing the Number of MPI Processes](#7-choosing-the-number-of-mpi-processes)
8. [Startup Output and Stability Report](#8-startup-output-and-stability-report)
9. [Output Files](#9-output-files)
10. [Editing Kinetics and Recompiling](#10-editing-kinetics-and-recompiling)
11. [Analytical Validation Cases](#11-analytical-validation-cases)
12. [Troubleshooting](#12-troubleshooting)

---

## 1. Two Ways to Get the Solver

| | Option A — Standalone Package | Option B — Build from Source |
|---|---|---|
| **Where** | `ComapLB3D/` folder in this repo | Root `CMakeLists.txt` + download Palabos |
| **Palabos** | Bundled and pre-compiled (GCC 11.3 / foss/2022a) | You download and compile Palabos yourself |
| **Best for** | UGA Sapelo2, most SLURM clusters running GCC 11+ | Custom architecture, macOS, Windows, or if the pre-compiled library fails |
| **Difficulty** | `cmake .. && make` — nothing else to install | More steps, but works anywhere |

---

## 2. Option A — Standalone Package (ComapLB3D): Recommended for Clusters

### 2.1 Package structure

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
├── output/                      # Solver writes VTI/checkpoint/CSV files here
└── build/                       # Run cmake from inside this directory
```

> **Do not delete or recompile anything inside `versionControl/palabos-v2.3.0/`.** The pre-compiled library was built for GCC 11.3 (foss/2022a). For other architectures, see §2.4.

### 2.2 UGA Sapelo2 / GACRC (reference configuration)

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

### 2.3 Other SLURM clusters (generic)

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

### 2.4 Adapting CMakeLists.txt for other architectures

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
> ```bash
> cd versionControl/palabos-v2.3.0 && mkdir -p build && cd build
> cmake .. -DCMAKE_BUILD_TYPE=Release
> make -j8
> ```
> Then proceed with `cmake .. && make -j8` in `ComapLB3D/build/`.

---

## 3. Option B — Build from Source (Full Repo)

Use this if you want to build from the root `CMakeLists.txt` and manage Palabos yourself, or if you're on macOS / Windows.

### 3.1 Download Palabos

**Linux / macOS:**
```bash
wget https://gitlab.com/unigespc/palabos/-/archive/v2.3.0/palabos-v2.3.0.tar.gz
tar -xzf palabos-v2.3.0.tar.gz
```

**Windows:** Download the zip from [gitlab.com/unigespc/palabos](https://gitlab.com/unigespc/palabos/-/releases) and extract manually.

### 3.2 Build — Linux and macOS

```bash
git clone https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR.git
cd Complab3D-Biotic-Kinetic-AndersopnNR/JOSS_Submit

cmake -S . -B build \
      -DCMAKE_BUILD_TYPE=Release \
      -DPLB_ROOT=/path/to/palabos-v2.3.0

cmake --build build --parallel 4
```

This produces `build/complab`.

### 3.3 Build — Windows (Visual Studio)

```bat
cmake -S . -B build ^
      -G "Visual Studio 17 2022" -A x64 ^
      -DCMAKE_BUILD_TYPE=Release ^
      -DPLB_ROOT=C:\path\to\palabos-v2.3.0

cmake --build build --config Release --parallel 4
```

Executable: `build\Release\complab.exe`.

### 3.4 Build — Windows (MSYS2 MinGW-w64)

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

### 3.5 HPC Cluster — module-based (generic)

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

## 4. Configuring a Simulation

Every CompLaB3D simulation is controlled by three files.

### 4.1 CompLaB.xml — simulation parameters

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

Full XML reference: `docs/CompLaB3D_User_Tutorial.md`.

### 4.2 Kinetics headers

For **biotic** simulations, edit `defineKinetics.hh` to define your Monod rate expressions. For **abiotic** simulations, edit `defineAbioticKinetics.hh`. These headers are compiled into the solver — **you must rebuild after every edit** (see §10).

### 4.3 Geometry file

Place `geometry.dat` in the `input/` folder (relative to where `CompLaB.xml` lives). The file is a text file with one integer per line representing the material number of each voxel, in Fortran-order (z fastest):

```
material[x=0,y=0,z=0]
material[x=0,y=0,z=1]
...
```

Material number meanings (set in `<material_numbers>` in the XML):

| Value | Meaning |
|-------|---------|
| 0 | Solid (no-slip wall) |
| 1 | Bounce-back boundary |
| 2 | Pore fluid |
| 3+ | Biofilm region (user-defined) |

**Generate a synthetic geometry:**
```bash
cd tools
python geometry_generator.py
# Follow prompts: choose medium type, set nx/ny/nz
# Output: input/geometry.dat
```

Or import a segmented micro-CT image stack (BMP/PNG/TIF) through the same script.

---

## 5. Running the Solver

### 5.1 Serial run

**Linux / macOS:**
```bash
./complab                        # reads CompLaB.xml in current directory
```

**Windows:**
```bat
complab.exe
```

### 5.2 MPI parallel run

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

## 6. HPC Job Submission — All Scheduler Types

### 6.1 SLURM (most common)

```bash
sbatch comp.sh
squeue -u $USER               # monitor
scancel <JOBID>               # cancel
sacct -j <JOBID>              # completed job details
scontrol show job <JOBID>     # full info including node
```

### 6.2 PBS / Torque (older university clusters, some national facilities)

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

### 6.3 LSF (IBM Spectrum LSF — national labs, some universities)

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

## 7. Choosing the Number of MPI Processes

CompLaB3D uses Palabos domain decomposition and supports any number of MPI ranks. For best performance, choose a rank count that divides the domain dimensions (nx, ny, nz) approximately evenly.

| Domain size | Suggested MPI ranks | Approximate voxels per rank |
|---|---|---|
| 50 × 50 × 50 | 4–8 | ~15 000 – 30 000 |
| 100 × 100 × 100 | 8–16 | ~60 000 – 125 000 |
| 200 × 200 × 200 | 32–64 | ~125 000 (optimal) |
| 400 × 400 × 400 | 128–256 | ~250 000 |

Edit `#SBATCH --ntasks` (or PBS `ppn`, LSF `-n`) and the `mpirun -np` / `srun -n` value to match.

---

## 8. Startup Output and Stability Report

On launch, CompLaB3D prints a banner, configuration summary, and stability check:

```
╔══════════════════════════════════════════════════════════════════════╗
║                            CompLaB3D                                 ║
║       Three-Dimensional Biogeochemical Reactive Transport Solver     ║
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

If any criterion fails the solver prints a descriptive error and exits before any computation.

**Stability criteria enforced:**

| Criterion | Requirement | Physical meaning |
|-----------|-------------|-----------------|
| Mach number | Ma < 0.3 (warn) / < 1.0 (hard) | Low-velocity incompressible flow |
| CFL | CFL = u_max < 1.0 | Numerical stability of streaming step |
| NS relaxation time | 0.5 < τ_NS < 2.0 | Viscosity physically representable |
| ADE relaxation time | 0.5 < τ_ADE < 2.0 | Diffusivity physically representable |
| Grid Péclet number | Pe_grid < 2.0 (warn) | Advection does not dominate per lattice cell |

---

## 9. Output Files

All output goes to the `output/` folder (relative to where CompLaB.xml lives):

| File | Format | Content |
|------|--------|---------|
| `substrate_NNNNNNN.vti` | VTK ImageData | Concentration field at iteration N |
| `velocity_NNNNNNN.vti` | VTK ImageData | Velocity field (u_x, u_y, u_z) |
| `biomass_NNNNNNN.vti` | VTK ImageData | Biomass density field |
| `maskLattice_NNNNNNN.vti` | VTK ImageData | Pore geometry / biofilm mask |
| `checkpoint_NNNNNNN.chk` | Binary | Restart checkpoint (use with `read_NS_file`, `read_ADE_file`) |
| `btc_*.csv` | CSV | Breakthrough curve time series per substrate |
| `moments_summary.csv` | CSV | First and second spatial moments |
| `domain_properties.csv` | CSV | Porosity, permeability, Pe, Ma, CFL, τ |
| `simulation_*.out` | Text | Full solver console log |

Open VTI files in **ParaView** (`File → Open → select all substrate*.vti → Apply Filters`).

---

## 10. Editing Kinetics and Recompiling

The rate law functions live in C++ header files that are compiled **into** the solver binary. Every time you edit them, you must rebuild.

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

## 11. Analytical Validation Cases

Five complete validation cases in `test_cases/abiotic/` verify solver correctness against closed-form analytical solutions. Each runs in a simple 1D channel geometry in under a minute.

| Case | XML file | Kinetics header |
|------|---------|-----------------|
| Pure diffusion | `test1_pure_diffusion.xml` | *(none — abiotic kinetics disabled)* |
| First-order decay | `test2_first_order_decay.xml` | `defineAbioticKinetics_test2.hh` |
| Bimolecular | `test3_bimolecular.xml` | `defineAbioticKinetics_test3.hh` |
| Reversible | `test4_reversible.xml` | `defineAbioticKinetics_test4.hh` |
| Sequential decay | `test5_decay_chain.xml` | `defineAbioticKinetics_test5.hh` |

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

**Dry-run check (XML + kinetics syntax only, no solver needed):**
```bash
python tests/run_validation.py --dry-run
```

Expected output values and physical interpretation: `test_cases/abiotic/README.md`.

---

## 12. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `cmake ..` fails with "Palabos not found" | `PLB_ROOT` path wrong | Set `-DPLB_ROOT=/absolute/path/to/palabos` |
| `make` fails: "undefined reference to `MPI_...`" | MPI not loaded | `module load openmpi` before building |
| Linker fails: "incompatible architecture" on pre-built library | CPU/ABI mismatch | Delete `versionControl/palabos-v2.3.0/build/` and recompile Palabos |
| Solver exits immediately: "CompLaB.xml not found" | Run from wrong directory | `cd` to the folder that contains `CompLaB.xml` before running |
| Solver exits: "geometry.dat not found" | Geometry file missing | Place it at `input/geometry.dat` (relative to CompLaB.xml) |
| Solver exits: "tau invalid" | τ outside (0.5, 2.0] | Adjust `<tau>` in XML or change `<Peclet>` to get a different diffusivity |
| Results diverge / NaN | CFL or Ma exceeded | Reduce `<delta_P>` or `<Peclet>` |
| Job runs too slowly | Too few MPI ranks or too many (memory overhead) | See §7 for recommended rank counts |
| Recompile needed but `make` says "Nothing to do" | CMake doesn't detect header change | `touch defineKinetics.hh` then `make -j8` |
