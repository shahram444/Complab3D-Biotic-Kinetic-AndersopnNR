# Testing Guide

This document describes every test layer in CompLaB3D and how to run them.

---

## 1. GUI Tests (Python – pytest)

**275 automated tests** covering CompLaB Studio, running on Python 3.10, 3.11,
and 3.12 in CI.

| File | Tests | What it covers |
|------|------:|----------------|
| `test_pipeline_e2e.py` | 93 | End-to-end pipeline flows |
| `test_kinetics.py` | 86 | Kinetics `.hh` code generation and validation |
| `test_templates.py` | 30 | All 9 simulation template creation/validation |
| `test_project_model.py` | 27 | Data model validation (domain, fluid, chemistry) |
| `test_xml_io.py` | 21 | XML/JSON round-trip serialisation |
| `test_simulation_runner.py` | 18 | Subprocess lifecycle (mocked solver) |

### How to run

```bash
cd GUI
pip install -e ".[dev]"
python -m pytest tests/ -v
```

All tests run without the C++ binary (the solver is mocked).

### CI

The workflow `.github/workflows/gui-tests.yml` runs the full suite on every
push/PR that touches `GUI/`.

---

## 2. C++ Unit Tests (Google Test + CTest)

Unit tests for core C++ logic that can be compiled and run without the full
Palabos library or MPI.

| File | What it covers |
|------|----------------|
| `test_stability.cpp` | `StabilityReport` / `performStabilityChecks` (Mach, CFL, tau, Pe) |
| `test_abiotic_kinetics.cpp` | `defineAbioticRxnKinetics`, rate clamping, stats accumulator |
| `test_biotic_kinetics.cpp` | `defineRxnKinetics`, Monod saturation, substrate clamping, mass balance |

### Prerequisites

- CMake 3.14+
- C++11 compiler (GCC, Clang, or MSVC)
- Internet connection on first build (GoogleTest is fetched automatically)

### How to run

```bash
cd tests/cpp
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

### CI

The workflow `.github/workflows/cpp-tests.yml` builds and runs these tests on
every push/PR that touches `src/`, kinetics headers, or `tests/cpp/`.

---

## 3. C++ Validation Cases (Analytical Solutions)

Five abiotic test cases in `test_cases/abiotic/` with known analytical
solutions.

| Test | Reaction | Analytical check |
|------|----------|------------------|
| 1 – Pure Diffusion | None | Linear steady-state profile C(x) = 1 − x/L |
| 2 – First-Order Decay | A → products | Exponential decay C(t) = C₀ exp(−kt) |
| 3 – Bimolecular | A + B → C | Mass balance A + B + C = const |
| 4 – Reversible | A ⇌ B | Equilibrium ratio [B]/[A] = K\_eq |
| 5 – Decay Chain | A → B → C | Bateman equations, transient peak in B |

### Automated harness

The script `tests/run_validation.py` automates the full workflow: copy
kinetics header → rebuild → run solver → check output.

```bash
# Full run (requires compiled solver + MPI):
python tests/run_validation.py --np 4

# Analytical-only dry run (no build/solver needed):
python tests/run_validation.py --dry-run
```

Options:

| Flag | Default | Description |
|------|---------|-------------|
| `--build-dir` | `build/` | CMake build directory |
| `--np` | 1 | Number of MPI processes |
| `--skip-build` | off | Skip recompilation between tests |
| `--dry-run` | off | Validate analytical solutions only |

### Manual run (single test)

```bash
# Example: Test 2 (first-order decay)
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cd build && make -j$(nproc) && cd ..
mpirun -np 1 ./complab test_cases/abiotic/test2_first_order_decay.xml
```

Detailed analytical solutions and validation criteria are documented in
`test_cases/abiotic/README.md`.

### CI

The dry-run (analytical solution verification) is included in
`.github/workflows/cpp-tests.yml`. Full simulation validation requires
Palabos and MPI, so it is intended for local or dedicated CI runners.

---

## 4. Running Everything

```bash
# 1. GUI tests
cd GUI && python -m pytest tests/ -v && cd ..

# 2. C++ unit tests
cd tests/cpp && mkdir -p build && cd build
cmake .. && cmake --build . --parallel && ctest --output-on-failure
cd ../../..

# 3. Validation dry-run
python tests/run_validation.py --dry-run

# 4. (Optional) Full validation with solver
python tests/run_validation.py --np 4
```

---

## 5. Adding New Tests

### New GUI test

Add a test file under `GUI/tests/` following the existing pytest conventions.
Use the fixtures in `conftest.py` for Qt widget testing.

### New C++ unit test

1. Create `tests/cpp/test_<name>.cpp` using Google Test macros.
2. Add an `add_executable` + `gtest_discover_tests` block in
   `tests/cpp/CMakeLists.txt`.
3. Include `plb_shim.h` if your code references `plb::plint`.

### New validation case

1. Create an XML configuration in `test_cases/abiotic/`.
2. Create the corresponding `defineAbioticKinetics_testN.hh`.
3. Add the test entry and validator function in `tests/run_validation.py`.
4. Document the analytical solution in `test_cases/abiotic/README.md`.
