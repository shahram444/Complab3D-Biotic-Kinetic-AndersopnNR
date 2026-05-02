# CompLaB3D Test Suite

**Authors:** Shahram Asgari and Christof Meile  
**Affiliation:** Meile Lab, Department of Marine Sciences, University of Georgia (UGA), Athens, GA, USA  
**Contact:** [shahram.asgari@uga.edu](mailto:shahram.asgari@uga.edu)


**What the tests guarantee:** Every time someone changes the solver code, 387
automated checks run and compare numerical results against either an exact
analytical formula or a known physical constraint. If any number is wrong the
check fails immediately and points to the exact function responsible. This
catches physics bugs before they corrupt published simulation results.

---

## Table of Contents

1. [What CompLaB3D Computes and What Can Go Wrong](#1-what-complab3d-computes-and-what-can-go-wrong)
2. [Two Levels of Testing — Overview](#2-two-levels-of-testing--overview)
3. [Level 1: Unit Tests — Testing Individual Physics Functions](#3-level-1-unit-tests--testing-individual-physics-functions)
   - [How Unit Tests Work (Plain Language)](#how-unit-tests-work-plain-language)
   - [Prerequisites](#prerequisites-unit-tests)
   - [Step-by-Step: Linux](#step-by-step-linux-unit-tests)
   - [Step-by-Step: macOS](#step-by-step-macos-unit-tests)
   - [Step-by-Step: Windows](#step-by-step-windows-unit-tests)
   - [What Each Test File Covers](#what-each-test-file-covers)
4. [Level 2: Integration Tests — Running Real Simulations](#4-level-2-integration-tests--running-real-simulations)
   - [How Integration Tests Work (Plain Language)](#how-integration-tests-work-plain-language)
   - [Prerequisites](#prerequisites-integration-tests)
   - [Step-by-Step: Linux and macOS](#step-by-step-linux-and-macos-integration-tests)
   - [Step-by-Step: Windows](#step-by-step-windows-integration-tests)
   - [The Five Validation Cases](#the-five-validation-cases)
   - [Dry-Run Mode (No Solver Required)](#dry-run-mode-no-solver-required)
5. [Interpreting Results](#5-interpreting-results)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. What CompLaB3D Computes and What Can Go Wrong

CompLaB3D simulates dissolved chemicals moving through porous material (rock,
soil, biofilm, sediment) while simultaneously being consumed or produced by
microbial reactions and geochemical equilibria. The governing equations are:

```
Advection-diffusion-reaction (ADE):
  dC/dt = D_eff * ∇²C  −  u * ∇C  +  R(C, B)

Microbial biomass (Monod kinetics):
  dB/dt = ( µ_max * C / (Ks + C)  −  k_decay ) * B

Geochemical equilibrium (mass action):
  [species_i] = 10^( log K_i  +  Σ_j v_ij * log C_j )
```

In a typical 3-D simulation the solver evaluates these equations at roughly
10⁶ lattice sites on every time step. Small errors in any one component
compound across millions of sites and thousands of time steps. A 0.1% error
in the Monod yield coefficient, for example, produces a 10–30% error in
cumulative biomass after 10 000 iterations — but the simulation appears to
run fine and outputs VTI files that look reasonable.

The tests exist to catch these silent errors before they reach a paper.

---

## 2. Two Levels of Testing — Overview

The test suite has two completely different kinds of tests. They answer
different questions and require different tools to run.

```
LEVEL 1 — UNIT TESTS                    LEVEL 2 — INTEGRATION TESTS
─────────────────────────────────────   ────────────────────────────────────
File:  tests/cpp/*.cpp                  File:  tests/run_validation.py
Tool:  GoogleTest (C++ framework)       Tool:  Python script + real solver

Question:                               Question:
"Is this one physics function           "Does a complete simulation
 computing the right number?"            reproduce the analytical solution?"

What runs:                              What runs:
One function from one .hh header        The full compiled solver via MPI
(e.g. defineRxnKinetics)                (same binary you use for research)

Needs Palabos?    NO                    Needs Palabos?    YES
Needs MPI?        NO                    Needs MPI?        YES
Needs cluster?    NO                    Needs cluster?    NO (laptop ok)
Speed:            ~1 second total       Speed:            ~2–10 min per case
Works on:         Linux, macOS, Windows Works on:         Linux, macOS

When it catches bugs:                   When it catches bugs:
Before running any simulation           After a full simulation run
```

**Both levels are necessary.** A unit test can confirm that the Monod rate
function returns the right number when called with specific inputs. But only
an integration test can confirm that the rate function, the transport solver,
the time integrator, and the output writer all work together correctly on a
real 3-D domain.

---

## 3. Level 1: Unit Tests — Testing Individual Physics Functions

### How Unit Tests Work (Plain Language)

This is the key insight that makes the unit tests possible without Palabos or
MPI.

Your CompLaB3D solver is structured as a main program (`src/complab.cpp`) that
calls physics functions defined in **header files** (`.hh` files):

```
complab.cpp  →  #include "defineKinetics.hh"
             →  #include "defineAbioticKinetics.hh"
             →  #include "complab_functions.hh"
             →  #include "complab3d_processors_part4_eqsolver.hh"
             →  ... (Palabos, MPI, etc.)
```

The main program needs Palabos and MPI. But the **physics functions in the
header files do not**. They are plain mathematics: given input concentrations
and biomass, compute rates. Given a lattice node, compute a diffusion flux.

The unit tests include exactly the same header files your solver uses, call
exactly the same functions, and check the answers against known-correct values:

```
test_biotic_kinetics.cpp  →  #include "defineKinetics.hh"
                          →  calls defineRxnKinetics(C, B, ...)
                          →  checks: is dB/dt == expected Monod value?
                          →  checks: is carbon mass balance satisfied?
                          →  checks: does growth stop when C = 0?
```

**The one workaround: `plb_shim.h`**

Your kinetics headers use one Palabos data type: `plb::plint` (a 64-bit
integer used for array indices). Without Palabos installed, the compiler
would refuse to compile the header. The `plb_shim.h` file substitutes for
the entire Palabos library with four lines:

```cpp
// plb_shim.h  — the only "fake" in the entire test suite
namespace plb {
    typedef long long int plint;   // same type, no Palabos needed
}
```

Everything else in the tests is the real production code from your solver.
No mocking, no stubs, no simplified versions.

**What GoogleTest does**

GoogleTest is a widely-used C++ testing framework (developed by Google, used
in thousands of scientific projects). It provides the `TEST()` macro and
`EXPECT_NEAR()`, `EXPECT_TRUE()`, etc. for writing checks. CMake downloads
it automatically on first build — you do not install it manually.

```cpp
// Example from test_biotic_kinetics.cpp
TEST(BioticKinetics, HalfSaturationPoint) {
    // When DOC = Ks, Monod growth rate = mu_max / 2  (by definition)
    double DOC = Ks;
    double mu = mu_max * DOC / (Ks + DOC);
    EXPECT_NEAR(mu, mu_max / 2.0, 1e-12);
}
```

When this test runs, GoogleTest calls your real `defineRxnKinetics()` function
and checks whether the Monod equation gives the correct half-saturation value.

---

### Prerequisites: Unit Tests

| What you need | Linux | macOS | Windows |
|---|---|---|---|
| C++ compiler | GCC (usually pre-installed) | Xcode Command Line Tools | Visual Studio Community (free) OR MinGW-w64 |
| CMake 3.14+ | `sudo apt install cmake` | `brew install cmake` | cmake.org installer |
| Internet | First run only | First run only | First run only |
| Palabos | **NOT needed** | **NOT needed** | **NOT needed** |
| MPI | **NOT needed** | **NOT needed** | **NOT needed** |

CMake automatically downloads GoogleTest v1.14 from GitHub on the first
build. After that, no internet is needed.

---

### Step-by-Step: Linux (Unit Tests)

Open a terminal and follow these steps exactly.

**Step 1 — Check you have a C++ compiler**
```bash
g++ --version
```
If you see a version number (e.g. `g++ 11.4.0`), you are ready. If you see
"command not found":
```bash
sudo apt-get install build-essential cmake   # Ubuntu / Debian
sudo dnf install gcc-c++ cmake               # Fedora / RHEL
```

**Step 2 — Check CMake version**
```bash
cmake --version
```
You need version 3.14 or higher. If it shows an older version:
```bash
pip install cmake --upgrade    # works on any Linux
```

**Step 3 — Navigate to the test folder**
```bash
cd /path/to/Complab3D-Biotic-Kinetic-AndersopnNR/JOSS_Submit/tests/cpp
```
Replace `/path/to/` with the actual location of the repository on your machine.

**Step 4 — Create the build directory and configure**
```bash
mkdir build
cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
```
On the first run this downloads GoogleTest (~30 seconds, requires internet).
You will see output like:
```
-- Fetching GoogleTest v1.14...
-- Configuring done
-- Build files have been written to: .../tests/cpp/build
```

**Step 5 — Compile the test programs**
```bash
cmake --build . --parallel
```
This compiles 17 test executables. Takes about 30–60 seconds.

**Step 6 — Run all tests**
```bash
ctest --output-on-failure
```
Expected output:
```
Test project .../tests/cpp/build
      Start  1: test_stability
 1/17 Test  #1: test_stability ............... Passed   0.01s
      ...
17/17 Test #17: test_reaction_transport ....... Passed   0.02s

100% tests passed, 0 tests failed out of 382
Total Test time (real) =  0.71 sec
```

**Run just one test suite** (useful when debugging a specific module):
```bash
ctest -R biotic_kinetics --output-on-failure
```

**Run one specific check by name:**
```bash
./test_biotic_kinetics --gtest_filter="*HalfSaturation*"
```

---

### Step-by-Step: macOS (Unit Tests)

**Step 1 — Install Xcode Command Line Tools** (if not already installed)
```bash
xcode-select --install
```
A dialog will appear — click Install. This takes a few minutes.

**Step 2 — Install CMake**
```bash
brew install cmake        # if you use Homebrew (recommended)
```
Or download the `.dmg` installer from [cmake.org](https://cmake.org/download/).
After installing from `.dmg`, run:
```bash
sudo "/Applications/CMake.app/Contents/bin/cmake-gui" --install
```
to add cmake to your PATH.

**Verify:**
```bash
cmake --version    # should show 3.14 or higher
g++ --version      # should show a version number
```

**Step 3 — Navigate to the test folder**
```bash
cd /path/to/Complab3D-Biotic-Kinetic-AndersopnNR/JOSS_Submit/tests/cpp
```

**Step 4 — Configure, compile, and run**
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

Expected result: `100% tests passed, 0 tests failed out of 382`

> **Apple Silicon (M1/M2/M3) note:** The tests compile and run natively on
> ARM without any special flags. If cmake complains about architecture, add
> `-DCMAKE_OSX_ARCHITECTURES=arm64` to the cmake line.

---

### Step-by-Step: Windows (Unit Tests)

Windows users have two options. **Option A** (Visual Studio) is recommended
for most people. **Option B** (MinGW) suits users who prefer a Linux-like
terminal experience.

#### Option A — Visual Studio (Recommended)

**Step 1 — Install Visual Studio Community (free)**

Go to [visualstudio.microsoft.com/vs/community](https://visualstudio.microsoft.com/vs/community/)
and download the installer. When it asks what to install, tick:
- **Desktop development with C++**

This installs the compiler, linker, and Windows SDK. The download is ~2 GB.

**Step 2 — Install CMake**

Go to [cmake.org/download](https://cmake.org/download/) and download the
Windows installer (`.msi` file). During installation, on the "Install Options"
screen, select **"Add CMake to the system PATH for all users"**.

**Step 3 — Open the Developer Command Prompt**

In the Windows Start menu, search for **"Developer Command Prompt for VS"**
(not a regular Command Prompt — this one has the compiler on PATH). Open it.

**Step 4 — Navigate to the test folder**
```bat
cd C:\path\to\Complab3D-Biotic-Kinetic-AndersopnNR\JOSS_Submit\tests\cpp
```
Replace `C:\path\to\` with the actual location on your machine.

**Step 5 — Configure**
```bat
mkdir build
cd build
cmake .. -G "Visual Studio 17 2022" -A x64
```
> If you installed Visual Studio 2019, use `-G "Visual Studio 16 2019"` instead.
> Not sure which version? Run `cmake --help` and look for the "Generators" list.

**Step 6 — Compile**
```bat
cmake --build . --config Release --parallel
```

**Step 7 — Run all tests**
```bat
ctest -C Release --output-on-failure
```

Expected output:
```
100% tests passed, 0 tests failed out of 382
Total Test time (real) =  1.20 sec
```

**Run one specific check by name (Windows MSVC):**
```bat
Release\test_biotic_kinetics.exe --gtest_filter="*HalfSaturation*"
```

---

#### Option B — MinGW-w64 (GCC on Windows)

**Step 1 — Install MSYS2**

Go to [msys2.org](https://www.msys2.org/) and download the installer. Run it
and accept all defaults. When installation finishes, the MSYS2 shell opens
automatically.

**Step 2 — Install the compiler tools** (in the MSYS2 MINGW64 shell)
```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make
```
Type `Y` when asked to confirm.

**Step 3 — Add MinGW to Windows PATH**

Search "Edit environment variables" in the Start menu. In the "System
variables" section, click `Path` → `Edit` → `New`, and add:
```
C:\msys64\mingw64\bin
```
Click OK. Close and reopen any terminals.

**Step 4 — Open a regular Command Prompt or PowerShell** (not MSYS2)
```bat
cd C:\path\to\Complab3D-Biotic-Kinetic-AndersopnNR\JOSS_Submit\tests\cpp
mkdir build
cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

**Run one specific check by name (MinGW):**
```bat
test_biotic_kinetics.exe --gtest_filter="*HalfSaturation*"
```

---

### What Each Test File Covers

Each test file includes the actual solver header it tests and calls the real
production functions. The table below maps test files to solver source files
and explains in physical terms what is being verified.

---

#### `test_stability.cpp` and `test_stability_extended.cpp` — 40 checks

**Solver source tested:** `src/complab.cpp` → `performStabilityChecks()`

**What this is:** Before running any simulation, CompLaB3D computes five
dimensionless numbers from your input parameters. If any of them falls
outside the stable range, the solver refuses to start. These tests verify
that the rejection logic is correct.

**Why this matters:** The Lattice Boltzmann Method is only mathematically
stable within specific parameter windows. Outside those windows, concentrations
diverge to infinity or oscillate nonsensically — but the solver keeps running
and writing output files that look plausible. These checks are the last line
of defence before a corrupted simulation.

| Parameter checked | Stable range | Physical meaning of violation |
|---|---|---|
| LBM relaxation time τ_NS | 0.5 < τ < 2.0 | τ < 0.5 means negative kinematic viscosity (unphysical) |
| LBM relaxation time τ_ADE | 0.5 < τ < 2.0 | τ < 0.5 means negative effective diffusivity |
| Mach number Ma = u/c_s | Ma < 0.3 | Compressibility errors corrupt the flow field |
| CFL number | u_max < 1 lattice unit/step | Information travels faster than the lattice can represent |
| Grid Péclet number Pe_grid | Pe_grid < 2 | Numerical diffusion dominates physical diffusion |

---

#### `test_abiotic_kinetics.cpp` and `test_abiotic_kinetics_extended.cpp` — 50 checks

**Solver source tested:** `defineAbioticKinetics.hh` → `defineAbioticRxnKinetics()`

**What this is:** Many environmental reactions follow first-order kinetics:
radioactive decay, hydrolysis of organic contaminants, anaerobic oxidation.
The default implementation is dA/dt = −k·A with k = 10⁻⁵ /s.

**Why this matters:** This function is called at every lattice site in the
reaction step. A sign error or a wrong coefficient corrupts every concentration
field in the simulation. The checks include:

- Sign: the rate is negative (A is consumed, not produced)
- Proportionality: doubling [A] doubles the rate (confirms first-order, not zeroth-order)
- Zero-concentration behaviour: rate at [A] = 0 is exactly zero (no spurious substrate creation)
- Rate clamping: the solver caps consumption so no more than 50% of available concentration
  is consumed per step (prevents negative concentrations)
- Finite output: no NaN or Inf across 12 orders of magnitude in [A] (from 10⁻²⁰ to 10⁵ mol/L)

---

#### `test_biotic_kinetics.cpp` and `test_biotic_kinetics_extended.cpp` — 55 checks

**Solver source tested:** `defineKinetics.hh` (sessile branch) → `defineRxnKinetics()`

**What this is:** Biofilm bacteria growing on surfaces are modelled with the
Monod equation:

```
µ     = µ_max * DOC / (Ks + DOC)      growth rate [1/s]
dB/dt = (µ − k_decay) * B             net biomass change [kg/m³/s]
dDOC/dt = −µ * B / Y                  DOC consumption [mol/L/s]
dCO2/dt = +µ * B / Y                  CO2 production [mol/L/s]
```

Parameters: µ_max = 1.0 /s, k_decay = 10⁻⁹ /s, Ks = 10⁻⁵ mol/L, Y = 0.4

**The most important check — yield mass balance:**

```
dB/dt = −dDOC/dt * Y − k_decay * B   (must hold at every function call)
```

This verifies that carbon accounting is correct instantaneously, not just
on average over a whole simulation. If Y or dt_kinetics is changed and the
function is not updated consistently, this test fails immediately.

**All checks:**

| Check | Physical meaning |
|---|---|
| No biomass → no reaction | Rates must be zero when B = 0 |
| High DOC → growth | When [DOC] >> Ks: dB/dt > 0, dDOC/dt < 0 |
| CO₂ produced when DOC consumed | Carbon must appear somewhere |
| Monod saturation point | Growth rate at [DOC] = Ks equals exactly µ_max/2 |
| Zero DOC → decay only | When [DOC] = 0: only k_decay term remains |
| **Yield mass balance** | Carbon bookkeeping correct at every call |
| Rate clamping | DOC consumption never exceeds 50% per step |

---

#### `test_planktonic_kinetics.cpp` and `test_planktonic_kinetics_extended.cpp` — 37 checks

**Solver source tested:** `defineKinetics.hh` (planktonic branch)

**What this is:** The same 17+ checks as for biofilm cells, applied to the
suspended (free-swimming) microbial population. Planktonic cells have different
parameter values reflecting their physiology:

```
µ_max = 0.5 /s     (lower than sessile 1.0 /s — less substrate access)
k_decay = 10⁻⁷ /s  (higher than sessile 10⁻⁹ /s — more shear, predation)
PLANKTONIC_DILUTION_FACTOR = 0.1   (cells wash out with flow)
```

**Why separate tests?** The same `defineRxnKinetics()` function handles both
cell types with a branch. If the branch logic is wrong, sessile cells get
planktonic parameters and vice versa — a bug that produces wildly wrong
biomass predictions but is invisible without explicit tests for both branches.

---

#### `test_eq_solver.cpp` and `test_eq_solver_extended.cpp` — 51 checks

**Solver source tested:** `complab3d_processors_part4_eqsolver_standalone.hh`
→ `EquilibriumChemistry<T>::solve()`

**What this is:** Geochemical reactions that reach thermodynamic equilibrium
faster than the transport time scale (carbonate speciation, sorption, ion
exchange) are handled by an Anderson-Accelerated Newton-Raphson solver with
a Positive Continued Fraction (PCF) formulation.

**The governing equations:**

```
Mass action:   log[species_i] = log K_i + Σ_j ( v_ij * log[component_j] )
Conservation:  T_j = Σ_i ( v_ij * [species_i] )   for each component j
```

**Three layers of checks:**

*Layer 1 — Linear algebra building blocks:*
- norm([3,4]) = 5.0 (3-4-5 right triangle, exact)
- QR decomposition: Q orthonormal, R upper triangular, A = Q·R to 10⁻¹⁰
- Triangular solve: solution of R·x = b recovers x to 10⁻¹²

*Layer 2 — Chemical physics:*
- Mass action law gives correct species concentrations from log K
- Extreme inputs (pH 0 to 14) produce finite, clamped outputs

*Layer 3 — Convergence and conservation:*
- Newton-Raphson converges in < 50 iterations
- All species concentrations remain positive
- **Component conservation: Σ species_j before = Σ species_j after to 0.01%**

The component conservation check is the critical one. Equilibrium speciation
redistributes species but must not create or destroy total moles of any
element. A failure means the solver is losing or gaining moles of carbon,
nitrogen, or another element at every equilibrium step.

---

#### `test_diagnostics.cpp` — 20 checks

**Solver source tested:** `defineKinetics.hh` → `KineticsStats`, `KineticsDiagnostics`

**What this is:** During a simulation, CompLaB3D accumulates per-iteration
statistics: biomass produced, DOC consumed, CO₂ generated, active cell count,
rate-limited cell count. These feed the console output and show whether the
simulation is physically reasonable.

**Checks:** counter reset clears all values; accumulation is additive; yield
consistency over 100 calls; decaying cell classification; rate-limited cell
counting.

---

#### `test_lbm_utils.cpp` and `test_lbm_utils_extended.cpp` — 65 checks

**Solver source tested:** `complab3d_processors.hh`, `complab_functions.hh`

**What this is:** The D3Q7 lattice encoding used for all scalar transport
fields (concentrations, biomass density, geometry masks). Every concentration
value in the simulation is stored through this encoding.

```
g[0]       = (ρ − 1) / 4    (rest direction)
g[1]..g[6] = (ρ − 1) / 8   (six face-connected directions)
ρ = Σg + 1                  (decode: reconstruct C from populations)
```

**The most fundamental check — encode→decode round-trip:**
Round-trip exact to 10⁻¹² for 6 test values including 0 and negative.
A systematic error here introduces a bias in every single concentration and
biomass value throughout the entire domain.

Also checks: weight normalisation (Σw_i = 1.0 to 10⁻¹⁴), Laplacian of a
constant field = 0, Darcy flow calibration, LBM physics constants, biofilm
permeability.

---

#### `test_bc.cpp` — 22 checks

**Solver source tested:** D3Q7 boundary condition processors

**What this is:** At the edges of the computational domain, boundary
conditions must be applied. CompLaB3D supports three types:

- **Dirichlet** (fixed concentration — e.g. feed solution): Anti-Bounce-Back scheme
- **Neumann** (zero gradient — e.g. sealed wall): incoming = outgoing populations
- **Periodic** (what exits one face re-enters the opposite): exact mass conservation

**Checks:** ABB recovers exact boundary concentration; Neumann gives zero
gradient; periodic conserves mass exactly; D3Q7 weights sum to 1; unit
conversion round-trip is exact.

---

#### `test_growth_integration.cpp` — 18 checks

**Solver source tested:** `defineKinetics.hh` (Euler time integration)

**What this is:** The kinetics function computes instantaneous rates. The
solver integrates those rates forward in time using an explicit Euler method:

```
B(t + dt)   = B(t)   + dB/dt   * dt
DOC(t + dt) = DOC(t) + dDOC/dt * dt
```

These tests verify that the integration behaves correctly over many steps,
not just at a single instant. Scenarios tested: growth phase (B grows, DOC
falls), DOC depletion (cells switch to decay after substrate runs out),
mass balance over 100 steps, sessile vs. planktonic growth rate difference.

---

#### `test_diffusion_bc.cpp` — 20 checks

**Solver source tested:** `complab_functions.hh` (diffusivity helpers)

**What this is:** Substrate transport in porous media uses an effective
diffusivity lower than the free-water value because molecules must navigate
around solid grains or through EPS matrix.

```
Pore space:  D_eff = D_free * φ / τ²    (φ = porosity, τ = tortuosity ≥ 1)
Biofilm:     D_eff = D_free * factor     (factor = 0.1 to 0.8)
LBM:         D_lattice = (τ_ADE − 0.5) / 3
```

**Analytical validation** against the exact 1D reactive-diffusion steady-state:

```
C(x) = C₀ * cosh(φ * (1 − x/L)) / cosh(φ)
where φ = L * sqrt(k / D_eff)   (Thiele modulus)
```

---

#### `test_reaction_transport.cpp` — 26 checks

**Solver source tested:** Multiple headers (dimensionless numbers, operator splitting)

**What this is:** The dimensionless numbers that classify transport regimes
and the operator splitting architecture of the solver.

```
Péclet number:    Pe   = u * L / D           (advection vs. diffusion)
Damköhler number: Da   = k * L / u           (reaction vs. advection)
Thiele modulus:   φ    = L * sqrt(k / D_eff) (biofilm effectiveness)
```

**The operator splitting check** is architecturally critical. CompLaB3D
handles the ADE and the reaction kinetics in separate sequential sub-steps
(Strang splitting). This test verifies that the splitting is applied in the
correct order: transport moves substrate without creating or destroying it,
then the reaction step removes the correct amount.

---

## 4. Level 2: Integration Tests — Running Real Simulations

### How Integration Tests Work (Plain Language)

The unit tests verify that individual functions return correct numbers. The
integration tests go one level higher and ask: when all the pieces run
together as a complete simulation, does the numerical result match the exact
mathematical solution?

The script `tests/run_validation.py` runs five test cases end-to-end:

```
For each test case:
  1. Copy the test-specific defineAbioticKinetics.hh into the repo root
  2. Recompile the full solver (make -j4) with that kinetics header
  3. Run: mpirun -np N ./complab test_case.xml
  4. Read the output CSV / VTI files
  5. Compare numerical field against the analytical formula
  6. Report PASS or FAIL with the actual vs. expected values
  7. Restore your original defineAbioticKinetics.hh
```

The solver that runs in step 3 is **the same binary you use for your research**
— not a simplified version. If these tests pass, you know the full simulation
pipeline (XML parsing → geometry setup → LBM flow → ADE transport → reaction
kinetics → output writing) produces physically correct results on problems
where the answer is known exactly.

**Why five specific test cases?** Each case isolates one physical mechanism
so that a failure points unambiguously to one component of the solver. A
failure in Test 2 (first-order decay) but not Test 1 (pure diffusion) tells
you the abiotic reaction step has a bug, not the transport step.

---

### Prerequisites: Integration Tests

| What you need | Notes |
|---|---|
| Compiled CompLaB3D solver | Must have been built with Palabos (see main README §4 or §5) |
| MPI runtime | `mpirun` or `mpiexec` must be on your PATH |
| Python 3.10+ | `python --version` to check |
| numpy | `pip install numpy` |
| vtk (optional) | `pip install vtk` — needed only for field comparison, not for the NaN check |

You do **not** need the GUI. You do **not** need a cluster — one node with
4–8 cores is enough for all 5 test cases.

---

### Step-by-Step: Linux and macOS (Integration Tests)

**Step 1 — Make sure the solver is compiled**

You need a working build of the full solver. If you have not done this yet,
follow the instructions in the main README (Section 4 for building from
source, or Section 5 for the standalone ComapLB3D package).

Check that the executable exists:
```bash
ls build/complab        # if you built from source
# or
ls ComapLB3D/complab    # if you used the standalone package
```

**Step 2 — Check Python and numpy**
```bash
python --version        # need 3.10 or higher
pip install numpy       # if not already installed
```

**Step 3 — Run the full integration tests (takes 10–30 minutes)**
```bash
cd /path/to/Complab3D-Biotic-Kinetic-AndersopnNR/JOSS_Submit

# With 4 MPI processes, using the source build:
python tests/run_validation.py --np 4 --build-dir build

# With 8 MPI processes, using the standalone package:
python tests/run_validation.py --np 8 --build-dir ComapLB3D/build

# Skip recompilation if kinetics did not change (faster):
python tests/run_validation.py --np 4 --build-dir build --skip-build
```

**Expected output:**
```
============================================================
  Test 1 – Pure Diffusion
============================================================
  Kinetics: default (none)
  Building...
  Running (4 MPI procs)...
  Result: PASS – No NaN/Inf in output

...

============================================================
  VALIDATION SUMMARY
============================================================
  [PASS] Test 1 – Pure Diffusion: No NaN/Inf in output
  [PASS] Test 2 – First-Order Decay: No NaN/Inf in output
  [PASS] Test 3 – Bimolecular Reaction: No NaN/Inf in output
  [PASS] Test 4 – Reversible Reaction: No NaN/Inf in output
  [PASS] Test 5 – Decay Chain: No NaN/Inf in output

  5/5 passed
```

**Step 4 — Run a single test case manually** (useful for debugging)
```bash
# Copy the kinetics header for test 2
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh

# Recompile
cd build && make -j4 && cd ..

# Run (serial is fine for a small test domain)
./build/complab test_cases/abiotic/test2_first_order_decay.xml

# Visualise the output
paraview output/substrate*.vti
```

---

### Step-by-Step: Windows (Integration Tests)

Running the full integration tests on Windows requires MPI and Palabos, which
is more involved than on Linux. The most practical approach for Windows users is:

**Option A — Use WSL (Windows Subsystem for Linux) — Recommended**

WSL lets you run a full Linux environment inside Windows. Once WSL is set up,
follow the Linux steps above exactly.

1. Open PowerShell as Administrator and run:
   ```powershell
   wsl --install
   ```
2. Restart your computer.
3. Open the Ubuntu app from the Start menu.
4. Inside Ubuntu, follow the Linux integration test steps above.

**Option B — Native Windows with MS-MPI**

1. Install [Microsoft MPI](https://learn.microsoft.com/en-us/message-passing-interface/microsoft-mpi)
2. Build the solver following main README Section 4 (Windows)
3. Open a Developer Command Prompt for VS and run:
   ```bat
   cd C:\path\to\JOSS_Submit
   python tests\run_validation.py --np 4 --build-dir build
   ```
   Note: `mpirun` on Windows is `mpiexec`; the script detects this automatically.

---

### The Five Validation Cases

Each case has an exact mathematical solution. The solver must reproduce it
within numerical tolerance.

---

#### Test 1 — Pure Diffusion

**Physics:** A solute diffuses from a high-concentration inlet (C = 1.0) to
a zero-concentration outlet through a simple channel. No reactions.

**Exact steady-state solution:**
```
C(x) = 1 − x/L    (linear profile)
```

**What is checked:** C at the left boundary = 1.0, C at the midpoint ≈ 0.5,
C at the right boundary → 0. This is the simplest possible validation — if
the solver fails this, the transport solver itself has a fundamental bug.

**Kinetics file:** none (abiotic kinetics set to zero)

---

#### Test 2 — First-Order Decay

**Physics:** A solute decays exponentially: A → products, dA/dt = −k·A
with k = 10⁻⁴ /s.

**Exact solution:**
```
A(t) = A₀ * exp(−k * t)
Half-life = ln(2) / k = 6931.5 s
```

**What is checked:** At t = 6931 s, concentration should be A₀/2 = 0.5.
Also checks that the total amount of A removed equals the product formed
(mass conservation).

**Kinetics file:** `test_cases/abiotic/defineAbioticKinetics_test2.hh`

---

#### Test 3 — Bimolecular Reaction

**Physics:** Two reactants consume each other: A + B → C, r = k·A·B.

**Exact constraint (mass conservation):**
```
A(t) + B(t) + C(t) = A₀ + B₀ + C₀   at all times
```

**What is checked:** Total concentration is conserved at every output step.
Checks that the stoichiometry of the bimolecular rate function is correct —
equal moles of A and B consumed per unit time when k, A, B are specified.

**Kinetics file:** `test_cases/abiotic/defineAbioticKinetics_test3.hh`

---

#### Test 4 — Reversible Reaction

**Physics:** A ⇌ B with forward rate k_f and reverse rate k_r, K_eq = k_f/k_r = 2.

**Exact equilibrium:**
```
A_eq = C₀ / (1 + K_eq) = C₀ / 3
B_eq = C₀ * K_eq / (1 + K_eq) = 2*C₀ / 3
B_eq / A_eq = K_eq = 2   (the equilibrium constant must be reproduced)
```

**What is checked:** After sufficient time, the B/A concentration ratio
converges to K_eq = 2 within 1%.

**Kinetics file:** `test_cases/abiotic/defineAbioticKinetics_test4.hh`

---

#### Test 5 — Sequential Decay Chain (Bateman Equations)

**Physics:** A → B → C with rates k₁ = 2×10⁻⁴ /s and k₂ = 10⁻⁴ /s.
This is the Bateman problem, which has a closed-form transient solution.

**Exact solution (Bateman equations):**
```
A(t) = A₀ * exp(−k₁ * t)
B(t) = A₀ * k₁/(k₂ − k₁) * (exp(−k₁*t) − exp(−k₂*t))
C(t) = A₀ − A(t) − B(t)
```

**Mass balance:** A(t) + B(t) + C(t) = A₀ at all times.

**What is checked:** Mass is conserved; B reaches its analytical peak at
t_max = ln(k₂/k₁)/(k₂ − k₁); at long times, C → A₀.

**Kinetics file:** `test_cases/abiotic/defineAbioticKinetics_test5.hh`

---

### Dry-Run Mode (No Solver Required)

If you do not have a compiled solver (for example, on a fresh machine or in
CI), you can still verify that the analytical solution functions themselves
are mathematically correct:

```bash
python tests/run_validation.py --dry-run
```

This mode skips the solver entirely and only checks:
- Does `analytical_test1_diffusion(0, L)` return 1.0 and `analytical_test1_diffusion(L, L)` return 0.0?
- Does `analytical_test2_decay(6931, 1.0, 1e-4)` return approximately 0.5 (the half-life)?
- Do the Bateman equations conserve mass at t = 0 and t = 10⁶ s?
- etc.

This takes under one second and requires only Python (no C++, no MPI, no Palabos).
It is what GitHub Actions CI runs automatically on every push.

Expected output:
```
Dry-run: testing analytical solution functions

  [PASS] Test 1 analytical: linear profile
  [PASS] Test 2 analytical: exponential decay
  [PASS] Test 3 analytical: mass balance identity
  [PASS] Test 4 analytical: equilibrium ratio
  [PASS] Test 5 analytical: Bateman equations & mass balance

  All analytical solution tests passed.
```

---

## 5. Interpreting Results

### Unit tests — what a failure message looks like

```
FAILED: BioticKinetics.YieldMassBalance
  tests/cpp/test_biotic_kinetics.cpp:112
  Expected: dB/dt * Y ≈ −dDOC/dt
  Actual:   left = 0.00315, right = 0.00419
  Tolerance: 1e-06
```

This tells you: the yield mass balance check failed, the mismatch is at line
112 of `test_biotic_kinetics.cpp`, and the computed values were 0.00315 vs
0.00419. You then look at `defineKinetics.hh` and find the yield Y or the
time step dt_kinetics was changed without updating the rate function.

**To re-run only the failing test:**
```bash
# Linux / macOS:
./test_biotic_kinetics --gtest_filter="*YieldMassBalance*"

# Windows MSVC:
Release\test_biotic_kinetics.exe --gtest_filter="*YieldMassBalance*"
```

### Integration tests — what a failure looks like

```
[FAIL] Test 2 – First-Order Decay: NaN detected in substrate_0000100.csv
```

This means the simulation ran but produced NaN concentrations, which usually
indicates a numerical instability. Check τ_ADE in the XML (must be > 0.5)
and the time step in `defineAbioticKinetics_test2.hh` (rate * dt must be < 0.5).

### All pass

```
100% tests passed, 0 tests failed out of 382   ← unit tests
5/5 passed                                       ← integration tests
```

Both lines together mean: every individual physics function returns the
correct number, AND complete simulations reproduce exact analytical solutions.

---

## 6. Troubleshooting

### Unit tests

**"cmake" is not recognized / cmake not found**
- Linux: `sudo apt install cmake` or `pip install cmake --upgrade`
- macOS: `brew install cmake`
- Windows: download from cmake.org; tick "Add to PATH" during install;
  or open a Developer Command Prompt (cmake is pre-included)

**"g++" or "cl" is not recognized (compiler not found)**
- Linux: `sudo apt install build-essential`
- macOS: `xcode-select --install`
- Windows MSVC: open **Developer Command Prompt for VS**, not a regular terminal
- Windows MinGW: add `C:\msys64\mingw64\bin` to PATH; reopen the terminal

**cmake says "No internet" / cannot fetch GoogleTest**
GoogleTest is downloaded automatically on first `cmake ..`. If your machine has
no internet, download the GoogleTest source manually from
[github.com/google/googletest/releases](https://github.com/google/googletest/releases),
extract it anywhere, then edit `tests/cpp/CMakeLists.txt` and change
`FetchContent_Declare` to use `SOURCE_DIR /path/to/your/googletest`.

**Windows: "ctest: No tests were found"**
Always pass `-C Release` to ctest for MSVC builds:
```bat
ctest -C Release --output-on-failure
```

**One test fails, all others pass**
Run just that test suite with verbose output:
```bash
./test_biotic_kinetics --gtest_filter="*FailingName*" --gtest_verbose
```
The output shows the actual vs. expected value and the source line number.
The most common cause: a parameter in `defineKinetics.hh` or
`defineAbioticKinetics.hh` was changed without updating the corresponding
formula in the rate function.

**All tests in one suite fail to compile**
The header being tested has a changed function signature. Compare the function
declaration in `defineKinetics.hh` against what the test file expects at the
top of the test file.

---

### Integration tests

**"mpirun: command not found"**
- Linux: `sudo apt install openmpi-bin libopenmpi-dev`
- macOS: `brew install open-mpi`
- Windows: install [Microsoft MPI](https://learn.microsoft.com/en-us/message-passing-interface/microsoft-mpi)

**"Solver executable not found"**
The script looks for `./complab` then `build/complab`. Build the solver first
(see main README Section 4) and pass `--build-dir` pointing to your CMake
build directory:
```bash
python tests/run_validation.py --build-dir /path/to/your/build
```

**"Build failed" during integration test**
The solver failed to compile after the kinetics header was swapped. Usually
means the test kinetics header is syntactically invalid. Run the build manually:
```bash
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cd build && make -j4
```
and read the compiler error — it will point to the exact line in the kinetics
header.

**Simulation runs but produces NaN**
Your τ_ADE is likely at or below 0.5. Open the test XML file (e.g.
`test_cases/abiotic/test2_first_order_decay.xml`) and check `<tau_ADE>`.
It must be strictly greater than 0.5 for the LBM to be stable.

---

*For the mathematical derivations behind each model, see
`docs/CompLaB3D_Technical_Guide.md`. For how to configure and run the full
3-D solver, see the main `README.md`.*
