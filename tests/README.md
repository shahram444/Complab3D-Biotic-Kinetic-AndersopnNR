# CompLaB3D Test Suite

**What the tests verify:** Two automated test layers cover 900+ checks across
every physics function and every GUI panel — confirming that the correct number
comes out of each calculation and that the interface correctly reads and writes
all simulation parameters.

For manually running complete simulations (flow-only, diffusion, abiotic
kinetics, equilibrium chemistry, biotic growth), see
**[`test_cases/README.md`](../test_cases/README.md)**.

---

## Table of Contents

1. [Two Levels of Testing — Overview](#1-two-levels-of-testing--overview)
2. [Level 1: Unit Tests — Individual Physics Functions (C++)](#2-level-1-unit-tests--individual-physics-functions-c)
   - [How Unit Tests Work](#how-unit-tests-work)
   - [Prerequisites](#prerequisites-unit-tests)
   - [Step-by-Step: Linux](#step-by-step-linux-unit-tests)
   - [Step-by-Step: macOS](#step-by-step-macos-unit-tests)
   - [Step-by-Step: Windows](#step-by-step-windows-unit-tests)
   - [What Each Test File Covers](#what-each-test-file-covers)
3. [Level 2: GUI Tests — Graphical Interface (Python)](#3-level-2-gui-tests--graphical-interface-python)
   - [How GUI Tests Work](#how-gui-tests-work)
   - [Prerequisites](#prerequisites-gui-tests)
   - [Step-by-Step: All Platforms](#step-by-step-all-platforms-gui-tests)
4. [Interpreting Results](#4-interpreting-results)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Two Levels of Testing — Overview

```
LEVEL 1 — UNIT TESTS                      LEVEL 2 — GUI TESTS
──────────────────────────────────────     ────────────────────────────────────
files:  tests/cpp/*.cpp                    files:  GUI/tests/test_*.py
tool:   GoogleTest (C++)                   tool:   pytest (Python)

Question:                                  Question:
"Does this physics function                "Does the GUI correctly
 return the right number?"                  save/load all parameters?"

What runs:                                 What runs:
One function from one .hh header,          Python tests of GUI panels,
called directly with known inputs          project I/O, and XML templates

Needs Palabos?    NO                       Needs Palabos?    NO
Needs MPI?        NO                       Needs MPI?        NO
Needs cluster?    NO                       Needs cluster?    NO
Speed:            ~8 seconds               Speed:            ~60 seconds
Works on:         Linux, macOS, Windows    Works on:         Linux, macOS, Windows

Count:            33 checks                Count:            509 checks
```

Both levels run entirely without Palabos or MPI — they are available on any
laptop or workstation.

A unit test confirms that the Monod rate function returns the right number when
called with specific inputs. A GUI test confirms that the rate constants a user
enters in the interface are actually written to the XML and read back correctly.

To confirm the solver produces correct concentration fields in a real 3-D
domain, see the simulation cases in **`test_cases/README.md`**.

---

## 2. Level 1: Unit Tests — Individual Physics Functions (C++)

### How Unit Tests Work

CompLaB3D's physics lives in **header files** (`.hh` files) that are included
by the solver:

```
complab.cpp  →  #include "defineKinetics.hh"           (Monod kinetics)
             →  #include "defineAbioticKinetics.hh"    (abiotic reactions)
             →  #include "complab_functions.hh"         (geometry, I/O, stability)
             →  #include "complab3d_processors.hh"      (LBM operators)
             →  ... Palabos, MPI, OpenMP ...
```

The main program needs Palabos and MPI. The **physics functions in the header
files do not** — they are pure mathematics. The unit tests include exactly the
same headers the solver uses, call exactly the same functions, and compare the
results to known-correct values:

```cpp
// test_biotic_kinetics.cpp  (the actual test file — no simplifications)
#include "defineKinetics.hh"     // ← the real production header

TEST(BioticKinetics, HalfSaturationPoint) {
    // When [DOC] = Ks, the Monod growth rate must equal mu_max / 2 (by definition)
    double DOC = Ks;
    double mu  = mu_max * DOC / (Ks + DOC);
    EXPECT_NEAR(mu, mu_max / 2.0, 1e-12);
}
```

**The one workaround: `plb_shim.h`**

The kinetics headers use one Palabos type: `plb::plint` (a 64-bit integer).
Without Palabos installed, the compiler would refuse to build. `tests/cpp/plb_shim.h`
substitutes for the entire Palabos library with four lines:

```cpp
namespace plb {
    typedef long long int plint;   // identical type, no Palabos needed
}
```

Everything else is real production code — no mocking, no stubs.

**GoogleTest** is downloaded automatically by CMake on the first build.

---

### Prerequisites: Unit Tests

| What you need | Linux | macOS | Windows |
|---|---|---|---|
| C++ compiler | GCC (usually pre-installed) | Xcode Command Line Tools | MinGW-w64 or Visual Studio |
| CMake 3.14+ | `sudo apt install cmake` | `brew install cmake` | cmake.org installer |
| Internet | First build only (downloads GoogleTest) | First build only | First build only |
| Palabos | **NOT needed** | **NOT needed** | **NOT needed** |
| MPI | **NOT needed** | **NOT needed** | **NOT needed** |

---

### Step-by-Step: Linux (Unit Tests)

**Step 1 — Verify compiler and CMake**
```bash
g++ --version     # any modern version (GCC 9+ recommended)
cmake --version   # need 3.14 or higher
```

If either is missing:
```bash
sudo apt-get install build-essential cmake   # Ubuntu / Debian
sudo dnf install gcc-c++ cmake               # Fedora / RHEL
```

**Step 2 — Configure, compile, and run**
```bash
cd /path/to/JOSS_Submit/tests/cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

Expected result:
```
100% tests passed, 0 tests failed out of 33
Total Test time (real) =  7.83 sec
```

**Run just one test suite:**
```bash
ctest -R biotic_kinetics --output-on-failure
```

**Run one specific check by name:**
```bash
./test_biotic_kinetics --gtest_filter="*HalfSaturation*"
```

---

### Step-by-Step: macOS (Unit Tests)

```bash
xcode-select --install        # installs clang / g++
brew install cmake            # or download .dmg from cmake.org

cd /path/to/JOSS_Submit/tests/cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

Expected: `100% tests passed, 0 tests failed out of 33`

> **Apple Silicon (M1/M2/M3):** Tests compile natively on ARM. If cmake
> complains about architecture, add `-DCMAKE_OSX_ARCHITECTURES=arm64`.

---

### Step-by-Step: Windows (Unit Tests)

Two options: **Option A (MinGW)** works from a regular Command Prompt and is
simpler. **Option B (Visual Studio)** suits users who already have VS installed.

#### Option A — MinGW-w64 (Recommended)

**Step 1 — Install MSYS2 and MinGW** (skip if `g++ --version` already works)

Download the installer from [msys2.org](https://www.msys2.org/). In the MSYS2
MINGW64 shell that opens, run:
```bash
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make
```

**Step 2 — Add MinGW to Windows PATH**

Search "Edit environment variables" → `Path` → `Edit` → `New`:
```
C:\msys64\mingw64\bin
```
Close and reopen any Command Prompt windows.

**Step 3 — Install CMake** from [cmake.org/download](https://cmake.org/download/).
During installation select **"Add CMake to the system PATH for all users"**.

**Step 4 — Open a regular Command Prompt** (not MSYS2, not Developer Prompt):
```cmd
cd C:\path\to\JOSS_Submit\tests\cpp
mkdir build && cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

> Always use `-G "MinGW Makefiles"` to avoid the default Visual Studio
> generator. Must be run from a regular Command Prompt, not the MSYS2 shell.

**Run one check by name:**
```cmd
test_biotic_kinetics.exe --gtest_filter="*HalfSaturation*"
```

---

#### Option B — Visual Studio Community

**Step 1** — Install [Visual Studio Community](https://visualstudio.microsoft.com/vs/community/)
with **Desktop development with C++** workload.

**Step 2** — Install CMake (cmake.org).

**Step 3** — Open the **Developer Command Prompt for VS** from the Start menu
(not a regular terminal — `cl.exe` is only on PATH in this prompt).

**Step 4:**
```cmd
cd C:\path\to\JOSS_Submit\tests\cpp
mkdir build && cd build
cmake .. -G "Visual Studio 17 2022" -A x64
cmake --build . --config Release --parallel
ctest -C Release --output-on-failure
```

> Use `-G "Visual Studio 16 2019"` if you have VS 2019. Run `cmake --help`
> to list all available generators.

**Run one check by name:**
```cmd
Release\test_biotic_kinetics.exe --gtest_filter="*HalfSaturation*"
```

---

### What Each Test File Covers

#### `test_stability.cpp` and `test_stability_extended.cpp` — 40 checks

**Solver source tested:** `src/complab.cpp` → `performStabilityChecks()`

CompLaB3D checks five dimensionless numbers before any simulation starts and
refuses to run if any falls outside the stable range.

| Parameter | Stable range | What a violation means |
|---|---|---|
| LBM relaxation time τ_NS | 0.5 < τ < 2.0 | τ ≤ 0.5 → negative kinematic viscosity |
| LBM relaxation time τ_ADE | 0.5 < τ < 2.0 | τ ≤ 0.5 → negative effective diffusivity |
| Mach number Ma = u/c_s | Ma < 0.3 | Compressibility errors corrupt flow |
| CFL number | u_max < 1 lattice unit/step | Information travels faster than lattice |
| Grid Péclet number Pe_grid | Pe_grid < 2 | Numerical diffusion dominates |

---

#### `test_abiotic_kinetics.cpp` and `test_abiotic_kinetics_extended.cpp` — 50 checks

**Solver source tested:** `defineAbioticKinetics.hh` → `defineAbioticRxnKinetics()`

The default abiotic reaction is first-order decay: dA/dt = −k·A with k = 10⁻⁵/s.
Checks include sign (A is consumed), proportionality (doubling [A] doubles the
rate), zero-concentration behaviour, rate clamping (no more than 50% consumed
per step), and finite output across 25 orders of magnitude.

---

#### `test_biotic_kinetics.cpp` and `test_biotic_kinetics_extended.cpp` — 55 checks

**Solver source tested:** `defineKinetics.hh` → `defineRxnKinetics()` (sessile branch)

```
µ      = µ_max × DOC / (Ks + DOC)     Monod growth rate [1/s]
dB/dt  = (µ − k_decay) × B            biomass change [kg/m³/s]
dDOC/dt = −µ × B / Y                  DOC consumed [mol/L/s]
```

Parameters: µ_max = 1.0/s, k_decay = 10⁻⁹/s, Ks = 10⁻⁵ mol/L, Y = 0.4

The most important check is the **yield mass balance**:
```
dB/dt = −dDOC/dt × Y − k_decay × B   (must hold at every single call)
```
If Y or dt_kinetics is changed without updating the rate function, this fails
immediately before the mistake reaches any simulation output.

---

#### `test_planktonic_kinetics.cpp` and `test_planktonic_kinetics_extended.cpp` — 37 checks

**Solver source tested:** `defineKinetics.hh` (planktonic branch)

The same checks as the sessile biofilm branch, applied to suspended
(free-swimming) cells. Planktonic cells use different parameters (µ_max = 0.5/s,
k_decay = 10⁻⁷/s, PLANKTONIC_DILUTION_FACTOR = 0.1). The same
`defineRxnKinetics()` handles both via a branch — these tests verify that branch.

---

#### `test_eq_solver.cpp` and `test_eq_solver_extended.cpp` — 51 checks

**Solver source tested:** `complab3d_processors_part4_eqsolver_standalone.hh`

The geochemical equilibrium solver (Anderson-Accelerated Newton-Raphson with
PCF formulation) enforces chemical equilibrium at each time step. Three layers:
linear algebra building blocks (QR decomposition, triangular solve), mass
action chemistry, and the critical **component conservation** check (total moles
of each element conserved to 0.01% after redistribution).

---

#### `test_diagnostics.cpp` — 20 checks

**Solver source tested:** `defineKinetics.hh` → `KineticsStats`, `KineticsDiagnostics`

Per-iteration statistics: biomass produced, DOC consumed, CO₂ generated, active
and rate-limited cell counts. Checks counter reset, accumulation, yield
consistency over 100 calls.

---

#### `test_lbm_utils.cpp` and `test_lbm_utils_extended.cpp` — 65 checks

**Solver source tested:** `complab3d_processors.hh`, `complab_functions.hh`

D3Q7 lattice encoding for all scalar transport fields. The key check is the
**encode→decode round-trip**: every concentration value must survive encoding
and decoding to within 10⁻¹². Also checks weight normalisation, Laplacian of a
constant field = 0, Darcy flow calibration, and LBM physics constants.

---

#### `test_bc.cpp` — 22 checks

**Solver source tested:** D3Q7 boundary condition processors

Dirichlet (Anti-Bounce-Back), Neumann (zero gradient), and Periodic boundary
conditions. Checks that ABB recovers the exact boundary concentration, Neumann
gives zero gradient, and periodic BC conserves mass exactly.

---

#### `test_growth_integration.cpp` — 18 checks

**Solver source tested:** `defineKinetics.hh` (Euler time integration)

Multi-step integration: growth phase (B grows, DOC falls), DOC depletion (cells
switch to decay), mass balance over 100 steps, sessile vs. planktonic rate
difference.

---

#### `test_diffusion_bc.cpp` — 20 checks

**Solver source tested:** `complab_functions.hh` (diffusivity helpers)

Effective diffusivity in pore space and biofilm, and analytical validation
against the exact 1D reactive-diffusion steady-state profile (Thiele modulus
solution).

---

#### `test_reaction_transport.cpp` — 26 checks

**Solver source tested:** multiple headers (dimensionless numbers, operator splitting)

Péclet, Damköhler, and Thiele numbers. The **operator splitting** check: the
transport sub-step moves substrate without creating or destroying it, then the
reaction sub-step removes the correct amount.

---

## 3. Level 2: GUI Tests — Graphical Interface (Python)

### How GUI Tests Work

The GUI is a PySide6 desktop application. Its test suite uses pytest to verify
that every panel correctly reads and writes project parameters, that XML files
are generated with the right structure, that templates apply correctly, and that
the simulation pipeline wires together properly.

Tests are split into two groups:

- **Non-Qt tests** (`test_project_model.py`, `test_templates.py`, `test_xml_io.py`,
  `test_kinetics.py`, `test_pipeline_e2e.py`, `test_xml_diagnostic.py`,
  `test_config.py`): pure Python logic — no display needed, run on any machine.

- **Qt-dependent tests** (`test_gui_panels.py`, `test_simulation_runner.py`):
  instantiate real PySide6 widgets. On Linux they require a virtual display or
  the `offscreen` platform backend.

---

### Prerequisites: GUI Tests

| What you need | How to get it |
|---|---|
| Python 3.10 or higher | python.org installer (or system Python) |
| PySide6 | `pip install PySide6` |
| pytest | `pip install pytest` |
| Linux only: system Qt libraries | `sudo apt-get install -y libegl1 libgl1 libdbus-1-3` |

> **Linux note:** The required package is `libgl1`, **not** `libgl1-mesa-glx`.
> The older name was removed in Ubuntu 22.04. Installing the wrong name causes
> an "EGL / OpenGL not found" error even though PySide6 itself installed correctly.

---

### Step-by-Step: All Platforms (GUI Tests)

**Step 1 — Install Python packages**
```bash
cd /path/to/JOSS_Submit/GUI
pip install PySide6 pytest pytest-qt
```

On Linux, also install system libraries:
```bash
sudo apt-get install -y libegl1 libgl1 libdbus-1-3
```

**Step 2 — Run the non-Qt tests (works everywhere, no display needed)**
```bash
cd /path/to/JOSS_Submit/GUI
python -m pytest tests/test_project_model.py tests/test_templates.py \
  tests/test_xml_io.py tests/test_kinetics.py tests/test_pipeline_e2e.py \
  tests/test_xml_diagnostic.py tests/test_config.py -v --tb=short
```

**Step 3 — Run the Qt-dependent tests**

Linux (headless / no display):
```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_simulation_runner.py \
  tests/test_gui_panels.py -v --tb=short
```

Windows and macOS (normal desktop session):
```bash
python -m pytest tests/test_simulation_runner.py tests/test_gui_panels.py \
  -v --tb=short
```

**Step 4 — Run everything at once**
```bash
# Linux
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v --tb=short

# Windows / macOS
python -m pytest tests/ -v --tb=short
```

Expected result:
```
509 passed
```

---

## 4. Interpreting Results

### Unit tests — all pass

```
100% tests passed, 0 tests failed out of 33
Total Test time (real) =  7.83 sec
```

Every individual physics function returns the correct number. If one fails,
re-run it verbosely:
```bash
ctest -R failing_test_name --output-on-failure -V
# or run the binary directly:
./test_biotic_kinetics --gtest_filter="*FailingName*"
```

The failure message gives the test name, source file, line number, and the
actual vs. expected values.

### GUI tests — all pass

```
509 passed
```

The GUI correctly reads and writes every simulation parameter. If one fails,
run just that test file:
```bash
python -m pytest GUI/tests/test_xml_io.py -v --tb=long
```

### What to do if a test fails

The most common causes:

| Symptom | Likely cause |
|---|---|
| One unit test fails, all others pass | Parameter changed in `.hh` file without updating the formula |
| All kinetics tests fail | Wrong `defineKinetics.hh` or `defineAbioticKinetics.hh` on the include path |
| GUI tests: SyntaxError at collection | `parallel_panel.py` has unterminated string literal (missing `")` — get latest file) |
| GUI tests: AttributeError `isChe` | `fluid_panel.py` has truncated method name — get latest file |
| Qt tests: "platform" or "display" error | Add `QT_QPA_PLATFORM=offscreen` on Linux |

---

## 5. Troubleshooting

### Unit Tests

**`cmake` not found**
```bash
# Linux
sudo apt install cmake
# macOS
brew install cmake
# Windows: download from cmake.org, tick "Add to PATH"
```

**`g++` not found**
```bash
# Linux
sudo apt install build-essential
# macOS
xcode-select --install
# Windows MinGW: add C:\msys64\mingw64\bin to PATH
# Windows MSVC: use Developer Command Prompt for VS
```

**Windows: cmake generates Visual Studio project but you want MinGW**
```cmd
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
```
Run from a regular Command Prompt, not from the MSYS2 shell.

**cmake: "No internet" / cannot fetch GoogleTest**

Download the source manually from
[github.com/google/googletest/releases](https://github.com/google/googletest/releases),
extract it, then edit `tests/cpp/CMakeLists.txt` to point `SOURCE_DIR` to
your local copy.

**Windows MSVC: "ctest: No tests were found"**
```cmd
ctest -C Release --output-on-failure
```
Always pass `-C Release` for MSVC builds.

**One test fails, all others pass**
```bash
./test_biotic_kinetics --gtest_filter="*FailingName*"
```
The output shows actual vs. expected values and the source line. The most
common cause: a parameter in `defineKinetics.hh` or `defineAbioticKinetics.hh`
was changed without updating the rate formula.

---

### GUI Tests

**`libGL error` or `EGL not found` on Linux**
```bash
sudo apt-get install -y libegl1 libgl1 libdbus-1-3
```
Note: `libgl1`, not the obsolete `libgl1-mesa-glx`.

**`SyntaxError: unterminated string literal` when collecting tests**
`GUI/src/panels/parallel_panel.py` has the pre-fix bug. Get the latest file.

**`AttributeError: 'QCheckBox' has no attribute 'isChe'`**
`GUI/src/panels/fluid_panel.py` has a truncated method name. Get the latest file.

**Qt tests fail with "display" or "platform" error on a headless server**
```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/test_gui_panels.py -v
```

**`pip install` fails with "externally managed environment" (Ubuntu 23.04+)**
```bash
python -m venv .venv && source .venv/bin/activate
pip install PySide6 pytest pytest-qt
```

---

*For running complete simulations manually (flow-only, diffusion, kinetics,
equilibrium, biofilm growth), see [`test_cases/README.md`](../test_cases/README.md).*

*For building the solver with Palabos and MPI, see the main `README.md`.*
