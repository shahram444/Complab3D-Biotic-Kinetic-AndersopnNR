# CompLaB3D Testing Guide

This document is the single reference for every test in CompLaB3D. The first
half tells you **exactly how to run everything** (step-by-step). The second half
explains **what each test does**, the science behind it, and how the unit tests
work internally.

---

# Part 1 -- How to Run All Tests

## Quick-Start (run everything in 5 minutes)

```bash
# 1. GUI / Python tests  (about 30 s, no C++ solver needed)
cd GUI
pip install -e ".[dev]"
python -m pytest tests/ -v
cd ..

# 2. C++ unit tests  (about 20 s, needs CMake + g++)
cd tests/cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
cd ../../..

# 3. Analytical validation dry-run  (about 5 s, Python only)
python tests/run_validation.py --dry-run

# 4. (Optional) Full solver validation  (needs compiled solver + MPI)
python tests/run_validation.py --np 4
```

That's it. If all three green-bar, your checkout is healthy.

---

## 1.1  GUI Tests (Python / pytest)

**What you need:** Python 3.10-3.12, pip.

```bash
cd GUI
pip install -e ".[dev]"          # installs PySide6, pytest, pytest-qt
python -m pytest tests/ -v       # run all 275 tests
```

Useful flags:

| Flag | What it does |
|------|--------------|
| `-v` | Verbose -- prints every test name |
| `-x` | Stop on first failure |
| `-k "Monod"` | Run only tests whose name contains "Monod" |
| `--tb=short` | Shorter tracebacks |
| `-s` | Show print / log output |
| `COMPLAB_DEBUG=1` | Enable debug logging inside the tests |

Run a single file:

```bash
python -m pytest tests/test_kinetics.py -v
python -m pytest tests/test_simulation_runner.py -v -s
python -m pytest tests/test_gui_panels.py -v       # GUI panel unit tests
```

The GUI tests run fully **headless** -- no display server required. The
`conftest.py` fixture sets `QT_QPA_PLATFORM=offscreen` so PySide6 renders
to an invisible buffer.

### CI

`.github/workflows/gui-tests.yml` runs the full suite on **Python 3.10, 3.11,
and 3.12** on every push/PR that touches `GUI/`.

---

## 1.2  C++ Unit Tests (Google Test + CTest)

**What you need:** CMake 3.14+, a C++11 compiler (GCC, Clang, or MSVC),
internet on first build (GoogleTest is auto-fetched via FetchContent).

```bash
cd tests/cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

Run a single test binary directly for more detail:

```bash
./test_biotic_kinetics --gtest_filter="*MonodSaturation*"
./test_abiotic_kinetics --gtest_filter="*RateClamped*"
./test_stability --gtest_filter="*Mach*"
```

These tests compile **without Palabos or MPI**. A thin `plb_shim.h` header
provides just the `plb::plint` typedef so the production kinetics headers can
be included directly.

### CI

`.github/workflows/cpp-tests.yml` builds and runs these on every push/PR
that touches `src/`, kinetics headers, or `tests/cpp/`.

---

## 1.3  Analytical Validation Cases

Five abiotic test cases with known closed-form solutions live in
`test_cases/abiotic/`. An automated harness runs them:

```bash
# Dry-run: just verify the analytical math (no solver needed)
python tests/run_validation.py --dry-run

# Full run: copy headers -> rebuild -> run solver -> compare output
python tests/run_validation.py --np 4
```

Options:

| Flag | Default | What it does |
|------|---------|--------------|
| `--build-dir` | `build/` | CMake build directory |
| `--np` | `1` | Number of MPI processes |
| `--skip-build` | off | Skip recompilation between tests |
| `--dry-run` | off | Analytical verification only (no solver) |

To run **one test manually**:

```bash
# Example: Test 2 (first-order decay)
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cd build && make -j$(nproc) && cd ..
mpirun -np 1 ./complab test_cases/abiotic/test2_first_order_decay.xml
```

---

## 1.4  Adding New Tests

### New GUI test

1. Create `GUI/tests/test_<name>.py`.
2. Follow existing pytest conventions; use the fixtures in `conftest.py` for
   Qt widget testing.
3. The test is auto-discovered -- no registration needed.

### New C++ unit test

1. Create `tests/cpp/test_<name>.cpp` using Google Test macros.
2. Add an `add_executable` + `gtest_discover_tests` block in
   `tests/cpp/CMakeLists.txt`.
3. Include `plb_shim.h` if your code references Palabos types.

### New validation case

1. Create an XML config in `test_cases/abiotic/`.
2. Create the matching `defineAbioticKinetics_testN.hh`.
3. Add the test entry and validator function in `tests/run_validation.py`.
4. Document the analytical solution in `test_cases/abiotic/README.md`.

---

---

# Part 2 -- What Each Test Does (and the Science Behind It)

## Test Inventory at a Glance

| Layer | File | # Tests | Coverage area |
|-------|------|--------:|---------------|
| **C++ unit** | `test_abiotic_kinetics.cpp` | 8 | Abiotic rate computation, clamping, stats |
| **C++ unit** | `test_biotic_kinetics.cpp` | 11 | Monod growth, substrate clamping, mass balance |
| **C++ unit** | `test_stability.cpp` | 14 | LBM stability (Mach, CFL, tau, Peclet) |
| **Python** | `test_kinetics.py` | 86 | Kinetics `.hh` code generation and validation |
| **Python** | `test_templates.py` | 30 | All 9 simulation template creation/validation |
| **Python** | `test_project_model.py` | 27 | Data model validation (domain, fluid, chemistry) |
| **Python** | `test_xml_io.py` | 21 | XML/JSON round-trip serialisation |
| **Python** | `test_simulation_runner.py` | 18 | Subprocess lifecycle (mocked solver) |
| **Python** | `test_gui_panels.py` | 120+ | GUI panel construction, load/save, signals |
| **Python** | `test_pipeline_e2e.py` | 93 | End-to-end pipeline from input to output |
| **Validation** | `test_cases/abiotic/` | 5 | Analytical solutions (diffusion, decay, equilibrium) |

**Total: ~430+ automated tests.**

---

## 2.1  C++ Unit Tests -- Abiotic Kinetics

**File:** `tests/cpp/test_abiotic_kinetics.cpp`
**Tests:** 8
**What it covers:** The `defineAbioticRxnKinetics()` function -- the core abiotic
reaction engine called once per lattice cell per timestep.

### Science background

Abiotic reactions are chemical transformations that happen without biological
catalysis. In CompLaB3D they are modelled as source/sink terms in the
advection-diffusion equation (ADE):

```
dC/dt + u . grad(C) = D * laplacian(C) + R(C)
                                          ^^^^
                    this is what defineAbioticRxnKinetics computes
```

The simplest abiotic reaction is **first-order decay**:

```
R(C) = dC/dt = -k * C

where k is the decay rate constant [1/s].
```

This is an exponential process: `C(t) = C0 * exp(-k*t)`. The half-life is
`t_half = ln(2)/k`.

### How the unit tests work

Each test calls `defineAbioticRxnKinetics(C, subsR, mask)` with controlled
inputs and checks the output rates in `subsR`:

| Test | What it checks | Why it matters |
|------|----------------|----------------|
| **ZeroConcentrationGivesNearZeroRate** | `C = {0.0}` -> `subsR[0] ~ 0` | Avoids spurious production from nothing. The code uses a `MIN_CONC` floor so even zero concentration produces a rate <= 1e-15. |
| **PositiveConcentrationGivesNegativeRate** | `C = {1.0}` -> `subsR[0] < 0` | First-order decay must always consume (negative rate). If the sign were wrong the solver would create mass from nothing. |
| **RateProportionalToConcentration** | `R(2C) / R(C) = 2.0 +/- 0.01` | First-order kinetics are LINEAR in concentration. Doubling C must double the rate. This catches incorrect exponents or saturation terms that should not be there. |
| **NoNanOrInfInOutput** | `!isnan && !isinf` | At very low concentrations (1e-5), floating-point underflow or division by near-zero could produce NaN/Inf. This would propagate through the entire lattice and crash the solver. |
| **MultipleSubstratesInitializedToZero** | 3-species vector: only `subsR[0]` gets a rate; `subsR[1]`, `subsR[2]` are zeroed | The function must zero-initialize all output slots, even those it does not touch. Leftover sentinel values (the test uses 999.0) would corrupt the ADE solve. |
| **RateClampedToFractionOfConcentration** | `-subsR[0] <= C * MAX_RATE_FRACTION / dt` | The **rate clamp** is a safety net: it prevents the operator-split kinetics from consuming more mass than physically exists in a cell during one timestep. Without clamping, large rate constants (or large dt) would drive concentrations negative. |
| **ParameterValidationPasses** | `validateParameters() == true` | A self-check that rate constants, dt, and clamp fractions are in physically reasonable ranges. Catches configuration errors at compile time. |
| **StatsAccumulateCorrectly** | Calling `accumulate` twice -> `total_calls=2`, `cells_reacting=1` | The statistics accumulator tracks how many cells have active reactions each iteration. Used for diagnostic output. A zero-rate cell is counted as "not reacting". |

### How rate clamping works

```cpp
// Compute raw rate
double rate = -k_decay * C[0];

// Clamp: never consume more than MAX_RATE_FRACTION of what exists
double max_consumption = C[0] * MAX_RATE_FRACTION / dt_kinetics;
if (-rate > max_consumption)
    rate = -max_consumption;
```

This is essential for **operator splitting**: CompLaB3D first advects/diffuses
for one LBM timestep, then applies kinetics. If kinetics could consume 100% of
a cell's mass in one step, the next advection step would see negative
concentrations and the simulation would diverge.

---

## 2.2  C++ Unit Tests -- Biotic Kinetics

**File:** `tests/cpp/test_biotic_kinetics.cpp`
**Tests:** 11
**What it covers:** The `defineRxnKinetics()` function -- biotic (Monod-based)
reaction rates for microbial growth and substrate consumption.

### Science background

Biotic reactions model microbial metabolism. The central equation is the
**Monod kinetic model**, the microbiology analogue of Michaelis-Menten enzyme
kinetics:

```
mu = mu_max * [DOC] / (Ks + [DOC])     specific growth rate [1/s]
```

Where:
- `mu_max` = maximum growth rate (when substrate is unlimited)
- `Ks` = half-saturation constant (the concentration at which growth is half of max)
- `[DOC]` = dissolved organic carbon concentration

From the growth rate, three things happen simultaneously:

```
dB/dt   = (mu - k_decay) * B          biomass net growth
dDOC/dt = -mu * B / Y                 substrate consumption
dCO2/dt = +(1-Y)/Y * mu * B           CO2 production (carbon balance)
```

Where `Y` is the **yield coefficient** (kg biomass produced per mol substrate
consumed) and `k_decay` is the first-order biomass decay rate.

**Monod saturation behavior:** At low substrate (`[DOC] << Ks`), growth is
approximately first-order in `[DOC]`. At high substrate (`[DOC] >> Ks`), growth
saturates at `mu_max`. The transition happens around `[DOC] = Ks`.

### How the unit tests work

Each test calls `defineRxnKinetics(B, C, subsR, bioR, mask)`:
- `B` = biomass vector (one entry per microbial species)
- `C` = substrate concentration vector
- `subsR` = output substrate rates (consumption/production)
- `bioR` = output biomass growth rates

| Test | What it checks | Why it matters |
|------|----------------|----------------|
| **NoBiomassNoReaction** | `B = {0}` -> all rates = 0 | No bacteria means no metabolism. This ensures the code does not produce reactions from nothing. |
| **HighSubstrateGivesGrowth** | `B = {10}, C = {1.0}` -> `bioR[0] > 0`, `subsR[0] < 0` | With ample food and bacteria, biomass must grow (positive) and DOC must be consumed (negative). This is the basic Monod sanity check. |
| **CO2ProducedWhenSubstrateConsumed** | `subsR[1] > 0` when `subsR[0] < 0` | Carbon balance: when DOC is consumed, CO2 must be produced. `subsR[0]` is DOC rate, `subsR[1]` is CO2 rate. If CO2 were not produced, carbon would vanish. |
| **MonodSaturationBehavior** | Growth at `C = 1000 >> Ks` exceeds growth at `C = Ks` | Verifies the hyperbolic saturation shape. At `C = Ks`, the Monod term equals `mu_max/2`. At very high `C`, it approaches `mu_max`. If the code had a linear model instead, rates would not saturate. |
| **SubstrateConsumptionClamped** | Huge biomass (`1e6`) + tiny DOC (`1e-4`) -> consumption <= `MAX_DOC_CONSUMPTION_FRACTION * DOC / dt` | Same safety principle as abiotic clamping. A massive biofilm colony next to a depleted pore could otherwise consume more DOC than exists. The clamp prevents negative concentrations. |
| **ZeroSubstrateGivesDecayOnly** | `C = {0}` -> `bioR[0] <= 0`, `subsR[0] = 0` | No food means no growth, only decay. `dB/dt = -k_decay * B` (always negative or zero). DOC consumption must be exactly zero -- you cannot eat what is not there. |
| **NoNanOrInfOutputs** | All outputs finite | Same floating-point safety as abiotic. The Monod term `C/(Ks+C)` can produce NaN if both are zero without the `MIN_CONC` guard. |
| **EmptyVectorsNoAction** | Empty B, C, subsR, bioR -> no crash | Defensive coding: the function must handle edge cases gracefully. The first lattice site call after initialization might have empty vectors. |
| **ParameterValidationPasses** | `validateParameters() == true` | Checks that `mu_max > 0`, `Ks > 0`, `Y in (0,1]`, `k_decay >= 0`, etc. Catches unit-conversion errors (e.g., decay rate in hours instead of seconds). |
| **StatsResetAndAccumulate** | Reset -> accumulate -> counters correct | Tracks cells with active biomass, cells with net growth, total calls. Used to produce iteration summaries like "3241 cells with biomass, 2890 growing". |
| **MassBalanceYieldRelation** | `|dDOC/dt| * Y ~ dB/dt + k_decay * B` | **The most important test.** Verifies the carbon mass balance: every mol of DOC consumed must produce exactly Y kg of biomass plus (1-Y)/Y of CO2. Rearranged: `DOC_consumed * Y = biomass_growth + decay_loss`. Tolerance: 1e-6. If this fails, carbon is being created or destroyed. |

### How the Monod calculation works internally

```cpp
// Guard against division by zero
double doc = std::max(C[0], MIN_CONC);

// Monod specific growth rate
double mu = mu_max * doc / (Ks + doc);

// Net biomass rate = growth - decay
double dBdt = (mu - k_decay) * B[0];

// DOC consumption (negative = consumption)
double dDOCdt = -mu * B[0] / Y;

// Clamp DOC consumption
double max_consumption = C[0] * MAX_DOC_CONSUMPTION_FRACTION / dt_kinetics;
if (-dDOCdt > max_consumption) {
    dDOCdt = -max_consumption;
    // Scale growth proportionally
    dBdt = (-dDOCdt) * Y - k_decay * B[0];
}

subsR[0] = dDOCdt;
subsR[1] = -dDOCdt * (1.0 - Y) / Y;  // CO2 production
bioR[0]  = dBdt;
```

---

## 2.3  C++ Unit Tests -- LBM Stability Checks

**File:** `tests/cpp/test_stability.cpp`
**Tests:** 14
**What it covers:** The `performStabilityChecks()` function that validates
Lattice Boltzmann Method numerical parameters before a simulation runs.

### Science background

The Lattice Boltzmann Method (LBM) solves the Navier-Stokes equations on a
discrete lattice. It has strict numerical stability constraints:

**Mach number (Ma):** The ratio of flow velocity to the lattice speed of sound.
```
Ma = u_max / cs     where cs = 1/sqrt(3) in lattice units

Ma < 0.3  ->  safe (compressibility errors < 10%)
Ma < 1.0  ->  runs but inaccurate
Ma >= 1.0 ->  supersonic -> LBM becomes unstable
```

**CFL condition:** In LBM the CFL number equals the lattice velocity. Must be < 1:
```
CFL = u_max * dt/dx = u_max   (since dt/dx = 1 in lattice units)
```

**Relaxation time (tau):** Controls viscosity via `nu = cs^2 * (tau - 0.5)`.
```
tau > 0.5   ->  required for positive viscosity
tau < 2.0   ->  recommended for stability
tau = 0.5   ->  zero viscosity (inviscid limit, unstable)
```

There are two tau values: `tau_NS` for the Navier-Stokes (flow) solve and
`tau_ADE` for the advection-diffusion (transport) solve.

**Grid Peclet number (Pe):** Ratio of advective to diffusive transport at the
grid scale.
```
Pe_grid = u_max / D_lattice

Pe_grid < 2  ->  safe (no numerical oscillations)
Pe_grid >= 2 ->  wiggles appear in concentration fields
```

### How the unit tests work

Each test calls `performStabilityChecks(u_max, tau_NS, tau_ADE, D_lattice)` and
inspects the returned `StabilityReport` struct:

| Test | Input | What it checks |
|------|-------|----------------|
| **LowMachIsOk** | u=0.01 | `Ma_ok=true`, `Ma_warning=false`, `Ma ~ 0.01/sqrt(1/3)` |
| **HighMachNotOk** | u=0.7 | `Ma_ok=false` (supersonic), `Ma_warning=true` |
| **MachWarningRange** | u=0.2 | `Ma_ok=true` but `Ma_warning=true` (0.3 < Ma < 1.0) |
| **CflBelowOne** | u=0.5 | `CFL_ok=true`, `CFL=0.5` exactly |
| **CflAboveOne** | u=1.5 | `CFL_ok=false` |
| **ValidTauNS** | tau=0.8 | `tau_NS_ok=true` (in the safe range 0.5-2.0) |
| **TauNSTooLow** | tau=0.4 | `tau_NS_ok=false`, `all_ok=false` (negative viscosity) |
| **TauNSTooHigh** | tau=2.5 | `tau_NS_ok=false` (high viscosity, slow convergence) |
| **TauADETooLow** | tau_ADE=0.3 | `tau_ADE_ok=false`, `all_ok=false` |
| **PeGridBelowTwo** | u=0.01, D=0.1 | `Pe=0.1`, `Pe_grid_ok=true` |
| **PeGridAboveTwo** | u=0.5, D=0.1 | `Pe=5.0`, `Pe_grid_ok=false`, `has_warnings=true` |
| **ZeroDiffusionGivesPeZero** | D=0.0 | `Pe=0.0` (special case: no diffusion -> Pe=0, not Inf) |
| **AllOkWhenEverythingGood** | All safe values | `all_ok=true` |
| **AllNotOkWithBadTau** | Both taus bad | `all_ok=false` |

### How the composite flags work

```cpp
report.all_ok = Ma_ok && CFL_ok && tau_NS_ok && tau_ADE_ok;
report.has_warnings = Ma_warning || !Pe_grid_ok;
```

`all_ok` gates simulation launch (red errors). `has_warnings` shows yellow
warnings but lets the simulation proceed.

---

## 2.4  Python Tests -- Kinetics Code Generation

**File:** `GUI/tests/test_kinetics.py`
**Tests:** 86
**What it covers:** Generation, parsing, and cross-validation of the C++ `.hh`
kinetics header files that CompLaB Studio produces.

### Science background

CompLaB3D uses **operator splitting**: the LBM flow solver and the ADE transport
solver are written in compiled C++, but the reaction kinetics are defined in
swappable `.hh` header files. Each simulation scenario needs two headers:

- `defineKinetics.hh` -- biotic reactions (Monod growth)
- `defineAbioticKinetics.hh` -- abiotic reactions (decay, equilibrium)

The GUI generates these headers from templates, parameterised by the user's
substrate and microbe configuration. This test suite ensures the generated code
is valid.

### Test classes and what they verify

**TestKineticsRegistry (9 x 2 = 18 tests):**
For each of the 9 simulation scenarios (flow_only, diffusion_only,
tracer_transport, abiotic_reaction, abiotic_equilibrium, biotic_sessile,
biotic_planktonic, biotic_sessile_planktonic, coupled_biotic_abiotic):
- The kinetics info exists in the registry
- Both `.hh` bodies (biotic and abiotic) are non-empty

**TestHHCodeValidity (9 x 6 = 54 tests):**
For every generated `.hh` across all 9 scenarios:
- Has correct `#ifndef`/`#define`/`#endif` include guards
- Contains the required function name (`defineRxnKinetics` or `defineAbioticRxnKinetics`)
- Contains `KineticsStats` usage (for diagnostics)
- Includes `<vector>` (the function signatures use `std::vector<double>`)

**TestFunctionSignatureVerification (4 tests):**
- Valid biotic code passes verification
- Valid abiotic code passes verification
- Code with a wrong function name is flagged
- Code missing `KineticsStats` is flagged

**TestHHIndexParsing (3 tests):**
The parser extracts array indices from the `.hh` code (e.g., `subsR[0]`,
`C[2]`, `B[1]`) to cross-check against the project configuration:
- Parses simple `var[N]` expressions
- Ignores indices inside comments (`//`)
- Ignores `.size()` calls (not actual data access)

**TestCrossValidation (5 tests):**
Cross-validates that the `.hh` code accesses only valid indices:
- Valid template + matching config -> no errors
- `.hh` uses `C[2]` but project has 0 substrates -> error flagged
- `.hh` uses `B[1]` but project has only 1 microbe -> error flagged
- Empty biotic source when kinetics enabled -> error flagged
- Empty abiotic source when abiotic enabled -> error flagged

### Why this matters

A mismatch between the generated kinetics code and the project configuration
would cause a **buffer overrun** in the C++ solver (accessing `C[3]` when only
2 substrates exist). These cross-validation tests prevent that.

---

## 2.5  Python Tests -- Simulation Templates

**File:** `GUI/tests/test_templates.py`
**Tests:** 30
**What it covers:** All 9 simulation scenario templates -- verifying that each
creates a valid, self-consistent project.

### The 9 scenarios

| # | Template key | Biotic? | Substrates | Microbes | Special |
|---|-------------|---------|------------|----------|---------|
| 1 | `flow_only` | No | 0 | 0 | Pure Navier-Stokes |
| 2 | `diffusion_only` | No | 1 (Tracer) | 0 | Pe = 0, no flow |
| 3 | `tracer_transport` | No | 1 (Tracer) | 0 | Pe = 1, passive transport |
| 4 | `abiotic_reaction` | No | 2 (Reactant + Product) | 0 | First-order decay |
| 5 | `abiotic_equilibrium` | No | 5 | 0 | Carbonate equilibrium system |
| 6 | `biotic_sessile` | Yes | 1 (DOC) | 1 (CA) | Attached biofilm |
| 7 | `biotic_planktonic` | Yes | 1 (DOC) | 1 (LBM) | Suspended bacteria |
| 8 | `biotic_sessile_planktonic` | Yes | 1 (DOC) | 2 (CA + LBM) | Mixed biofilm + planktonic |
| 9 | `coupled_biotic_abiotic` | Yes | 2 (DOC + Byproduct) | 1 (CA) | Monod + abiotic decay |

### Test classes

**TestTemplateRegistry (4 tests):**
- All 9 templates registered
- Each key exists
- `get_template_list()` returns (key, name, description) tuples
- Unknown key returns a default project (not an error)

**Per-template tests (2 per template = 18 tests):**
Each template has a `test_create` (verifies fields) and `test_validates_clean`
(the project's own validation passes with zero errors):

- **FlowOnly:** `biotic_mode=false`, `enable_kinetics=false`, 0 substrates
- **DiffusionOnly:** 1 substrate named "Tracer", `peclet=0.0`
- **TracerTransport:** 1 substrate, `peclet=1.0`
- **AbioticReaction:** 2 substrates (Reactant + Product), `enable_abiotic_kinetics=true`
- **AbioticEquilibrium:** 5 substrates, 2 equilibrium components, stoichiometry matrix dimensions match, logK count matches
- **BioticSessile:** 1 DOC + 1 CA microbe
- **BioticPlanktonic:** 1 DOC + 1 LBM microbe
- **BioticSessilePlanktonic:** 2 microbes with `solver_type in {CA, LBM}`
- **CoupledBioticAbiotic:** `biotic_mode=true`, `enable_kinetics=true`, `enable_abiotic_kinetics=true`, 2 substrates + 1 microbe

**Cross-template checks (9 x 2 = 18 parametrised):**
- Every template has `kinetics_source` attached (even no-op stubs)
- Every template has `template_key` set correctly

---

## 2.6  Python Tests -- Project Data Model

**File:** `GUI/tests/test_project_model.py`
**Tests:** 27
**What it covers:** The `CompLaBProject` dataclass tree and its comprehensive
validation logic.

### Test classes

**TestDataclassDefaults (4 tests):**
- `CompLaBProject()` has sensible defaults (name = "Untitled", empty substrates, etc.)
- `Substrate()` defaults: `diffusion_in_pore = 1e-9`, `left_boundary_type = "Dirichlet"`
- `Microbe()` defaults: `solver_type = "CA"`, `reaction_type = "kinetics"`
- `DomainSettings()` defaults: `nx=50, ny=30, nz=30, unit="um"`

**TestDeepCopy (1 test):**
Modifying a deep copy does not affect the original. This prevents the GUI from
accidentally sharing state between the undo stack and the live project.

**TestValidationDomain (5 tests):**
- `nx = 0` -> error (non-positive dimension)
- `nx = 2` -> error (minimum is 3 for LBM to have an interior node)
- `dx = -1.0` -> error (negative voxel size is unphysical)
- `unit = "ft"` -> error (only um, mm, cm, m accepted)
- `geometry_filename = "geometry.vtk"` -> error (must be `.dat`)

**TestValidationFluid (3 tests):**
- `tau = 0.3` -> error (below 0.5 means negative viscosity)
- `tau = 3.0` -> error (above 2.0 means very high viscosity, likely a mistake)
- `delta_P = -1.0` -> error (negative pressure gradient is unphysical)

**TestValidationSubstrates (4 tests):**
- Two substrates both named "DOC" -> duplicate name error
- `initial_concentration = -1.0` -> negative concentration error
- `left_boundary_type = "Robin"` -> invalid (only Dirichlet or Neumann)
- `diffusion_in_biofilm > diffusion_in_pore` -> warning (biofilm always slows diffusion)

**TestValidationMicrobiology (3 tests):**
- `biotic_mode = true` with 0 microbes -> error
- CA microbe with empty `material_number` -> error (CA solver needs to know which geometry voxels are biofilm)
- `solver_type = "INVALID"` -> error (only CA or LBM)

**TestValidationEquilibrium (2 tests):**
- Equilibrium enabled but 0 components -> error
- Stoichiometry matrix rows != number of substrates -> dimension mismatch error

**TestValidationCrossChecks (2 tests):**
- `enable_kinetics = true` but 0 substrates -> error (kinetics needs something to react)
- `enable_abiotic_kinetics = true` but 0 substrates -> same error

---

## 2.7  Python Tests -- XML/JSON Serialisation

**File:** `GUI/tests/test_xml_io.py`
**Tests:** 21
**What it covers:** Round-trip fidelity of project data through XML export/import
and JSON save/load.

### Why this matters

The XML file is the contract between the GUI and the C++ solver. If a field is
lost or misformatted during serialisation, the solver will read wrong values
or crash.

### Test classes

**TestXMLExportStructure (5 tests):**
- Root element is `<parameters>`
- Required sections exist: `path`, `simulation_mode`, `LB_numerics`, `chemistry`, `microbiology`, `equilibrium`, `IO`
- Substrate count in XML matches template (e.g., 2 for abiotic_reaction)
- Domain dimensions in XML match template (e.g., nx=30, ny=10)
- Simulation mode booleans are correctly formatted ("true" / "false")

**TestXMLRoundTrip (9 tests, parametrised):**
For each of the 9 templates: export to XML -> import back -> verify all key fields
match (domain dimensions, tau, substrate names, microbe count, simulation mode).

**TestJSONRoundTrip (3 tests):**
Save/load `.complab` (JSON) format for flow_only, biotic_sessile, and
coupled_biotic_abiotic. Checks name, domain, substrates, microbes, template_key.

**TestKineticsDeployment (3 tests):**
- Coupled biotic+abiotic deploys 2 `.hh` files (`defineKinetics.hh` + `defineAbioticKinetics.hh`)
- Flow-only deploys only no-op stubs
- Deployed biotic file contains `defineRxnKinetics` and `KineticsStats`

**TestEquilibriumXML (2 tests):**
- Equilibrium section exported with `enabled=true`, `components`, `stoichiometry`, `logK`
- Round-trip preserves 2 components, 5-row stoichiometry, 5 logK values

---

## 2.8  Python Tests -- Simulation Runner (Subprocess Lifecycle)

**File:** `GUI/tests/test_simulation_runner.py`
**Tests:** 18
**What it covers:** The `SimulationRunner` class that manages the C++ solver
subprocess from the GUI.

### How these tests work

Instead of running the real C++ solver, each test writes a **fake solver** -- a
tiny Python script that mimics solver output (`iT = 1`, `iT = 2`, etc.). The
`SimulationRunner` launches it as a subprocess and processes its stdout/stderr
just like the real solver. This lets us test every edge case deterministically.

### Test classes

**Test 1 -- NormalCompletion (1 test):**
Fake solver prints `ade_max_iT = 5` then `iT = 1..5` then "Completed
successfully". Verifies: exit code 0, "successfully" in message, progress
events emitted, last progress is (5, 5).

**Test 2 -- BufferOverflow (2 tests):**
- 5000 lines at full speed with 200+ character lines. Verifies the process
  does not block on stdout. (The OS pipe buffer is typically 64 KB -- if the
  reader cannot keep up, the writer blocks and appears hung.)
- Partial line without trailing newline. Verifies it is still captured on
  process exit.

**Test 3 -- GarbageCollection (2 tests):**
- Runner with a `QObject` parent survives Python GC. (PySide6 prevents C++
  destruction while the parent is alive.)
- Runner without parent: demonstrates it IS vulnerable to GC. Documents that
  `main_window.py` must keep a strong reference.

**Test 4 -- CancelTerminate (2 tests):**
- `cancel()` during a running simulation stops it. Verifies "cancelled" in
  message and `_process.poll() is not None`.
- Solver that traps SIGTERM (ignores it). Runner must escalate to SIGKILL.
  Verifies the process is dead after cancel.

**Test 5 -- WorkingDirectory (2 tests):**
- Solver prints its `os.getcwd()` -- must match `work_dir`.
- Missing `CompLaB.xml` -> runner emits "not found" error, exit code -1.

**Test 6 -- ExitCodes (2 tests):**
- `sys.exit(42)` -> exit code 42, "42" in message.
- Simulated segfault (SIGSEGV) -> exit code -11 on Linux, 139 on Windows.

**Test 7 -- RaceConditions (1 test):**
Start -> get progress -> cancel -> verify dead -> start new runner -> get progress ->
cancel -> verify dead. Ensures no orphaned processes from rapid restart.

**Test 8 -- MPIErrors (1 test):**
MPI command set to `/nonexistent/mpirun` -> "not found" error, exit code -1.

**Test 9 -- ProgressParsing (1 test):**
Solver prints `iT = 1, 10, 50, 100`. Verifies all iteration numbers are parsed
from stdout and progress events contain the correct current/max values.

**Test 10 -- SlowOutput (1 test):**
Solver sleeps 1 second between each line. Verifies the process is not killed for
being "too slow" (no timeout misfire).

**Test 11 -- LogFile (1 test):**
Verifies an `output/simulation_*.out` log file is created containing the solver
output.

---

## 2.9  Python Tests -- GUI Panel Unit Tests

**File:** `GUI/tests/test_gui_panels.py`
**Tests:** 120+
**What it covers:** Every GUI panel widget -- construction, load/save round-trip,
signal emission, real-time validation, and cross-panel integration.

### Why GUI panel tests matter

The GUI panels are the user-facing layer between the `CompLaBProject` data model
and the actual Qt widgets. Each panel has two critical methods:

- `load_from_project(project)` -- populates widgets from the data model
- `save_to_project(project)` -- writes widget values back to the data model

If these methods have a bug (wrong widget read, forgotten field, type mismatch),
the user sees correct settings in the GUI but the exported XML contains wrong
values. The C++ solver then runs with incorrect parameters -- silently producing
wrong results or crashing. These tests catch such bugs.

### Test architecture

All tests run **headless** using `QT_QPA_PLATFORM=offscreen` (set in
`conftest.py`). No display server, window manager, or GPU is needed. The
`qtbot` fixture from `pytest-qt` handles QApplication lifecycle and provides
signal-waiting helpers.

A shared `_make_test_project()` helper creates a `CompLaBProject` with
non-default values in every field. This ensures round-trip tests catch fields
that silently revert to defaults.

### Test classes and what they verify

**TestBasePanel (13 tests):**
Factory methods and utility functions shared by all panels.

| Test | What it checks |
|------|----------------|
| `test_construction` | Panel creates without error, title is set |
| `test_construction_no_title` | Empty-title panel works |
| `test_make_line_edit` | Text, placeholder, readonly state |
| `test_make_spin` | Value, min, max, suffix |
| `test_make_double_spin` | Value, decimals, suffix |
| `test_make_combo` | Items, current selection |
| `test_make_checkbox` | Checked state, label text |
| `test_make_button` | Text, primary property |
| `test_make_info_label` | Text, word wrap enabled |
| `test_add_section` | Section label created with correct text |
| `test_add_form` | QFormLayout created |
| `test_set_and_clear_validation` | Error/warning styling applied and cleared |
| `test_data_changed_signal` | Signal emits correctly |

**TestGeneralPanel (14 tests):**
Simulation mode radio buttons and paths.

| Test | What it checks |
|------|----------------|
| `test_default_mode_is_biotic` | Default radio is "Biotic" |
| `test_mode_flags_*` (6 tests) | Each radio maps to correct (biotic, kinetics, abiotic) tuple |
| `test_get_mode_id` | Returns correct integer for current selection |
| `test_load_save_round_trip` | Biotic mode, diagnostics, paths survive round-trip |
| `test_load_abiotic_mode` | Abiotic flags select the abiotic radio |
| `test_load_coupled_mode` | Both biotic+abiotic flags select the coupled radio |
| `test_load_flow_only` | All-false flags with no substrates select flow_only |
| `test_data_changed_on_mode_switch` | Signal fires when radio changes |
| `test_summary_updates_on_mode_change` | Summary label reflects current mode |

**TestDomainPanel (8 tests):**
Grid dimensions, geometry file analysis, and factorization.

| Test | What it checks |
|------|----------------|
| `test_default_values` | nx=50, ny=30, nz=30 |
| `test_load_save_round_trip` | All domain fields (nx, ny, nz, dx, dy, dz, unit, char_length, geometry, material numbers) |
| `test_find_factorizations` | Finds valid (nx, ny, nz) triples for a given total |
| `test_find_factorizations_too_small` | Returns empty for total < 27 |
| `test_find_factorizations_with_hint` | Respects nz_hint constraint |
| `test_analyze_dat_file_text` | Counts values in text-format .dat |
| `test_analyze_dat_file_empty` | Returns 0 for empty file |
| `test_geometry_loaded_signal` | Signal emits (path, nx, ny, nz) |

**TestFluidPanel (6 tests):**
Flow parameters and real-time validation.

| Test | What it checks |
|------|----------------|
| `test_default_values` | tau = 0.8 |
| `test_load_save_round_trip` | delta_P, peclet, tau, track_performance |
| `test_tau_validation_error` | tau < 0.5 shows error styling |
| `test_tau_validation_warning` | tau > 1.5 shows warning styling |
| `test_tau_validation_ok` | tau in safe range clears validation |
| `test_delta_p_validation_negative` | Boundary value handling |

**TestChemistryPanel (9 tests):**
Substrate list add/remove, editing, and round-trip.

| Test | What it checks |
|------|----------------|
| `test_add_substrate` | List count increments, substrate object created |
| `test_add_multiple_substrates` | 3 substrates added correctly |
| `test_remove_substrate` | List count decrements, correct item removed |
| `test_remove_from_empty` | No crash on remove from empty list |
| `test_substrates_changed_signal` | Signal fires on add |
| `test_load_save_round_trip` | 2 substrates with all fields (name, concentration, diffusion, BCs) |
| `test_select_substrate` | Programmatic selection works |
| `test_editing_updates_name_in_list` | Typing in name field updates list item |
| `test_load_empty_project` | Empty substrate list handled |

**TestEquilibriumPanel (11 tests):**
Enable/disable, matrix rebuild, solver parameters.

| Test | What it checks |
|------|----------------|
| `test_default_disabled` | Widgets disabled when equilibrium off |
| `test_enable_toggle` | All solver param widgets enabled |
| `test_disable_toggle` | Widgets disabled again |
| `test_set_substrate_names` | Info label shows substrate names |
| `test_set_substrate_names_empty` | Shows "(none defined)" |
| `test_rebuild_matrix_no_components` | Error message when no components entered |
| `test_rebuild_matrix_no_substrates` | Error message when no substrates defined |
| `test_rebuild_matrix_success` | Correct table dimensions (n_subs x n_comp + logK) |
| `test_load_save_round_trip` | Components, stoichiometry, logK, solver params (max_iter, tolerance, anderson_depth, beta) |
| `test_load_disabled_equilibrium` | Checkbox unchecked for disabled equilibrium |
| `test_data_changed_on_enable` | Signal fires when enabled checkbox toggled |

**TestMicrobiologyPanel (9 tests):**
Microbe list, solver-type-dependent widget enabling, and round-trip.

| Test | What it checks |
|------|----------------|
| `test_add_microbe` | List count increments |
| `test_add_multiple_microbes` | Multiple microbes added |
| `test_remove_microbe` | Correct microbe removed |
| `test_remove_from_empty` | No crash on empty remove |
| `test_microbes_changed_signal` | Signal fires on add |
| `test_load_save_round_trip` | Global settings (max_density, threshold, ca_method) + per-microbe fields (name, solver, kinetics, material_number, densities, decay, viscosity, Ks, Vmax, BCs) |
| `test_solver_type_enables_widgets` | CA: viscosity ratio on, FD: biomass diffusion on |
| `test_load_empty_microbe_list` | Empty list handled |
| `test_select_microbe` | Programmatic selection |

**TestSolverPanel (4 tests):**
Iteration parameters and zero-iteration warnings.

| Test | What it checks |
|------|----------------|
| `test_load_save_round_trip` | All 10 iteration fields round-trip correctly |
| `test_zero_iterations_warning` | NS max_iT1 = 0 shows warning |
| `test_zero_ade_iterations_warning` | ADE max_iT = 0 shows warning |
| `test_nonzero_clears_warning` | Restoring a positive value clears warning |

**TestIOPanel (2 tests):**
VTK interval, checkpoint interval, restart files, filenames.

| Test | What it checks |
|------|----------------|
| `test_load_save_round_trip` | All 8 I/O fields (intervals, restart flags, filenames) |
| `test_default_values` | Default VTK interval = 1000, restart = off |

**TestParallelPanel (10 tests):**
MPI enable/disable, core selection, warnings, and command preview.

| Test | What it checks |
|------|----------------|
| `test_initial_state_disabled` | Slider and spin disabled initially |
| `test_enable_parallel` | Slider and spin enabled |
| `test_disable_parallel` | Slider and spin disabled again |
| `test_slider_spin_sync` | Moving slider updates spin and vice versa |
| `test_get_num_cores_disabled` | Returns 1 when disabled |
| `test_data_changed_on_enable` | Signal fires on enable toggle |
| `test_warnings_all_cores` | Warning when using all cores |
| `test_validate_for_domain` | Small domain triggers appropriate warning |
| `test_cmd_preview_serial` | Shows `./complab` when MPI off |
| `test_cmd_preview_mpi` | Shows `mpirun -np N ./complab` when MPI on |

**TestSweepPanel (8 tests):**
Parameter sweep preview generation and queueing.

| Test | What it checks |
|------|----------------|
| `test_parameter_combo_populated` | Sweep parameter list has entries |
| `test_generate_linear_preview` | 5-step linear range produces 5 rows |
| `test_generate_custom_preview` | Custom comma-separated values parsed |
| `test_generate_custom_empty` | Empty input produces 0 rows |
| `test_generate_custom_invalid` | Non-numeric input shows error message |
| `test_clear_preview` | Table cleared, queue button disabled |
| `test_get_sweep_config` | Returns (section, field, value) tuples |
| `test_sweep_requested_signal` | Signal fires on queue |

**TestRunPanel (24 tests):**
MPI configuration, run/stop lifecycle, progress parsing, output line
parsing, phase detection, convergence residual extraction, validation display,
diagnostic reports, and exit code analysis.

| Test | What it checks |
|------|----------------|
| `test_initial_state` | Ready, run enabled, stop disabled |
| `test_mpi_toggle` | Enable/disable MPI controls |
| `test_get_mpi_config` | Returns (enabled, nprocs, path) tuple |
| `test_set_mpi_config` | Programmatic MPI configuration |
| `test_on_run_sets_running_state` | Running flag, button states, status text |
| `test_on_stop_emits_signal` | Stop signal fires |
| `test_on_progress` | Progress bar and iteration label updated |
| `test_on_output_line_normal` | Text appears in output widget |
| `test_on_output_line_max_iT_parse` | `ade_max_iT = N` parsed correctly |
| `test_on_output_line_iteration_parse` | `iT = N` parsed correctly |
| `test_on_output_line_phase_detection_*` (3) | NS, ADE, equilibrium phases detected |
| `test_on_finished_success` | Exit 0: "Completed", buttons reset |
| `test_on_finished_failure` | Exit 42: "Failed", error summary visible |
| `test_on_finished_segfault` | Exit -11: segfault analysis shown |
| `test_show_validation_*` (2) | Valid config vs errors display |
| `test_on_diagnostic_report` | Crash diagnostic HTML formatted |
| `test_analyze_exit_code_*` (2) | Known and unknown exit codes |
| `test_clear_output` | Output text cleared |
| `test_run_stop_signals` | Both signals fire correctly |
| `test_ns_residual_parsing` | NS residual extracted from output |
| `test_ade_residual_parsing` | ADE convergence extracted from output |

**TestPostProcessPanel (8 tests):**
Output directory browsing, file filtering, and file information display.

| Test | What it checks |
|------|----------------|
| `test_set_output_directory` | Files listed from directory |
| `test_set_empty_directory` | Empty path shows 0 files |
| `test_set_nonexistent_directory` | Invalid path shows 0 files |
| `test_filter_vti_only` | VTI filter shows only .vti files |
| `test_filter_vtk_only` | VTK filter shows only .vtk files |
| `test_file_selected_signal` | Signal emits file path on load |
| `test_file_info_display` | File name, type, size shown |
| `test_file_count_label` | Count label shows correct number |

**TestPanelIntegration (3 tests):**
Cross-panel data flow.

| Test | What it checks |
|------|----------------|
| `test_full_project_round_trip_all_panels` | Load project into all 8 panels, save back, verify every field matches |
| `test_chemistry_to_equilibrium_sync` | `substrates_changed` signal updates equilibrium panel's substrate info |
| `test_empty_project_round_trip` | Default project (no substrates/microbes) survives full round-trip |

**TestRunPanelHelpers (2 tests):**
Utility functions.

| Test | What it checks |
|------|----------------|
| `test_escape_html` | `<`, `>`, `&`, `"` escaped correctly |
| `test_output_max_lines_constant` | Buffer limit is 50000 |

---

## 2.10  Python Tests -- End-to-End Pipeline

**File:** `GUI/tests/test_pipeline_e2e.py`
**Tests:** 93
**What it covers:** The complete data flow from user input through simulation
execution and file output.

### What "end-to-end" means here

These tests simulate the full pipeline a user follows:
1. Create geometry `.dat` file
2. Populate project data model (via templates, simulating user input)
3. Export to XML -> re-import and verify round-trip fidelity
4. Deploy kinetics `.hh` files and cross-validate
5. Save/load `.complab` (JSON) project files
6. Run a (fake) simulation, verify it produces `.out` logs and completes
7. Verify every template validates cleanly

### Key test areas

- **Geometry creation and loading:** Writes `.dat` file, verifies it can be read
- **XML fidelity for all 9 templates:** Full round-trip for every field
- **Kinetics deployment for all 9 templates:** Both `.hh` files deployed, valid C++
- **JSON project persistence:** Save + load, all fields preserved
- **Simulation execution:** Uses mocked solver, checks progress, exit code, log files
- **Template consistency:** Every template validates with 0 errors
- **Edge cases:** Missing files, invalid configs, partial outputs

---

## 2.11  Analytical Validation Cases (Abiotic)

**Directory:** `test_cases/abiotic/`
**Tests:** 5
**What they cover:** Full solver runs compared against known analytical
(closed-form) solutions.

These are the highest-fidelity tests -- they run the actual compiled solver and
compare its output to exact mathematical solutions. They verify that the LBM
flow solver, ADE transport solver, and abiotic kinetics all work correctly
together.

### Test 1: Pure Diffusion (no reactions)

**PDE:**
```
dC/dt = D * laplacian(C)
```

**Boundary conditions:** C(0) = 1.0 (Dirichlet), dC/dx at x=L = 0 (Neumann)

**Analytical steady-state:** `C(x) = 1 - x/L` (linear profile)

**What it validates:** The ADE solver correctly handles diffusion without any
reaction terms. The steady-state must be a linear gradient.

### Test 2: First-Order Decay

**Reaction:** A -> products, `dA/dt = -k * [A]`

**Analytical solution:** `[A](t) = [A]_0 * exp(-k*t)`

**Parameters:** k = 1.0e-4 s^-1, half-life = 6930 s

**What it validates:** The operator-split coupling between ADE transport and
abiotic kinetics correctly produces exponential decay. No negative concentrations.

### Test 3: Bimolecular Reaction

**Reaction:** A + B -> C, `r = k * [A] * [B]`

**Parameters:** k = 1.0e-2 L/mol/s, [A]_0 = 1.0, [B]_0 = 0.5, [C]_0 = 0.0

**Analytical validation:** Mass balance `[A] + [B] + [C] = 1.5 mol/L` at all times.
At completion: [A] = 0.5, [B] = 0.0, [C] = 0.5.

**What it validates:** Two-body reaction kinetics, stoichiometric coupling between
species, and mass conservation in a multi-species system.

### Test 4: Reversible Reaction

**Reaction:** A <-> B, forward rate k_f = 1.0e-3 s^-1, reverse k_r = 5.0e-4 s^-1

**Equilibrium constant:** K_eq = k_f/k_r = 2.0

**Analytical equilibrium:**
```
[A]_eq = 1/(1 + K_eq) = 0.333 mol/L
[B]_eq = K_eq/(1 + K_eq) = 0.667 mol/L
```

**Conservation:** [A] + [B] = 1.0 mol/L at all times.

**What it validates:** Forward + reverse reactions reach the correct thermodynamic
equilibrium, and mass is conserved throughout the approach to equilibrium.

### Test 5: Sequential Decay Chain (Bateman Equations)

**Reaction:** A -> B -> C, with k1 = 2.0e-4 s^-1, k2 = 1.0e-4 s^-1

**Analytical solutions (Bateman equations):**
```
[A](t) = A0 * exp(-k1*t)
[B](t) = A0 * k1/(k2-k1) * (exp(-k1*t) - exp(-k2*t))
[C](t) = A0 * [1 + (k1*exp(-k2*t) - k2*exp(-k1*t))/(k2-k1)]
```

**Key feature:** Intermediate species B shows a **transient peak** at
t_max = ln(k1/k2)/(k1-k2) ~ 6932 s, then decays to zero.

**Conservation:** [A] + [B] + [C] = 1.0 at all times.

**What it validates:** Multi-step sequential kinetics, transient intermediate
dynamics, and long-time convergence to final state ([C] -> 1.0).

---

## 2.12  Kinetics Scenario Templates (Integration)

**Directory:** `kinetics/` (9 folders, `01_flow_only/` through `09_coupled_biotic_abiotic/`)

Each folder contains a matched pair of `.hh` files, an XML config, and a README
with the full reaction system, parameters, and validation criteria. These are not
automated unit tests but serve as **integration test specifications**:

| Scenario | Reaction system | Key validation |
|----------|----------------|----------------|
| 01 -- Flow only | Navier-Stokes, no chemistry | Velocity profile matches Poiseuille/Stokes |
| 02 -- Diffusion only | ADE with Pe=0 | Linear steady-state profile |
| 03 -- Tracer transport | ADE with Pe=1 | Tracer advected and dispersed |
| 04 -- Abiotic reaction | First-order decay | Exponential decay |
| 05 -- Abiotic equilibrium | Carbonate system | Equilibrium speciation |
| 06 -- Biotic sessile | Monod + CA biofilm | DOC depletion near biofilm, biomass growth |
| 07 -- Biotic planktonic | Monod + LBM transport | Suspended bacteria follow flow |
| 08 -- Sessile + planktonic | Dual microbe system | Both solver types interact |
| 09 -- Coupled biotic-abiotic | Monod + abiotic decay | Byproduct produced biotically, decays abiotically |

---

## 2.13  CI Workflows

### `.github/workflows/gui-tests.yml`

- **Trigger:** Push/PR touching `GUI/`
- **Matrix:** Python 3.10, 3.11, 3.12 on Ubuntu
- **Steps:** Install system deps (EGL, Mesa) -> `pip install -e ".[dev]"` -> `pytest tests/ -v`
- **Environment:** `QT_QPA_PLATFORM=offscreen`, `COMPLAB_DEBUG=1`

### `.github/workflows/cpp-tests.yml`

- **Trigger:** Push/PR touching `src/`, kinetics headers, `tests/cpp/`, or `CMakeLists.txt`
- **Jobs:**
  1. **unit-tests:** CMake build -> CTest (Google Test)
  2. **validation-dry-run:** `python tests/run_validation.py --dry-run` (analytical solutions only)

---

## Glossary

| Term | Meaning |
|------|---------|
| **ADE** | Advection-Diffusion Equation: dC/dt + u.grad(C) = D*laplacian(C) + R |
| **CA** | Cellular Automaton -- discrete solver for sessile biofilm growth |
| **CFL** | Courant-Friedrichs-Lewy stability condition |
| **DOC** | Dissolved Organic Carbon -- primary substrate for microbial growth |
| **Ks** | Half-saturation constant in Monod kinetics [mol/L] |
| **LBM** | Lattice Boltzmann Method -- mesoscopic flow solver |
| **Ma** | Mach number -- ratio of flow velocity to speed of sound |
| **Monod** | mu = mu_max * S/(Ks + S) -- microbial growth rate model |
| **Pe** | Peclet number -- ratio of advective to diffusive transport |
| **tau** | LBM relaxation time -- controls viscosity/diffusivity |
| **Y** | Yield coefficient -- biomass produced per substrate consumed |
| **Operator splitting** | Solving transport and reactions in alternating sub-steps |
