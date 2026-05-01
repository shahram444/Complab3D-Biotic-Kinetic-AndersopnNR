# Testing CompLaB3D

CompLaB3D ships with three independent test layers. Each can be run on its own,
without compiling the full solver, so reviewers can verify correctness quickly.

| Layer | Framework | Location | Approx. Runtime |
|-------|-----------|----------|-----------------|
| C++ unit tests   | GoogleTest                | `tests/cpp/`           | ~1 sec    |
| GUI unit tests   | pytest + pytest-qt        | `GUI/tests/`           | ~12 sec   |
| Validation       | analytical reference cases| `test_cases/abiotic/`  | varies    |

---

## 1. C++ Unit Tests (GoogleTest)

These tests cover stability checks, kinetics (biotic, abiotic, planktonic),
the equilibrium solver (PCF + Anderson acceleration), boundary conditions,
diffusion physics, growth integration, coupled reaction–transport, and LBM
utilities. **They do not require Palabos or MPI.**

### Build and run

```bash
cd tests/cpp
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel
cd build
ctest --output-on-failure
```

Expected: **all tests pass** (typically a few hundred individual cases
discovered by `gtest_discover_tests`).

### Continuous integration

GitHub Actions workflow `.github/workflows/cpp-tests.yml` runs this matrix on
every push and pull request that touches `src/`, `tests/cpp/`, or
`CMakeLists.txt`:

- Ubuntu latest / GCC
- Ubuntu latest / Clang
- macOS latest / Clang

### What each test file covers

| File                                     | What it verifies                                   |
|------------------------------------------|----------------------------------------------------|
| `test_stability.cpp`                     | Mach, CFL, relaxation-time bounds                  |
| `test_stability_extended.cpp`            | Edge cases for stability checks                    |
| `test_abiotic_kinetics.cpp`              | Abiotic rate-law evaluation                        |
| `test_abiotic_kinetics_extended.cpp`     | Stoichiometry, multi-reaction networks             |
| `test_biotic_kinetics.cpp`               | Monod-style biofilm kinetics                       |
| `test_biotic_kinetics_extended.cpp`      | Multi-microbial-population scenarios               |
| `test_planktonic_kinetics.cpp`           | Suspended biomass growth/decay                     |
| `test_planktonic_kinetics_extended.cpp`  | Coupled planktonic–sessile transitions             |
| `test_eq_solver.cpp`                     | PCF + Anderson acceleration convergence            |
| `test_eq_solver_extended.cpp`            | Acid–base, complexation, ill-conditioned systems   |
| `test_diagnostics.cpp`                   | Mass-balance diagnostics                           |
| `test_lbm_utils.cpp`                     | D3Q7 weights, FD Laplacian, flow math              |
| `test_lbm_utils_extended.cpp`            | Edge cases for LBM utilities                       |
| `test_bc.cpp`                            | Dirichlet, Neumann, periodic boundary conditions   |
| `test_diffusion_bc.cpp`                  | Tortuosity, analytical diffusion, Peclet           |
| `test_growth_integration.cpp`            | Time-stepping, sessile vs planktonic switching     |
| `test_reaction_transport.cpp`            | Damkohler/Thiele numbers, breakthrough curves      |

---

## 2. GUI Unit Tests (pytest + pytest-qt)

These tests cover XML configuration generation, panel-to-XML mapping, project
templates, kinetics editor parsing, geometry generator I/O, and validation
diagnostics. They run headless using the Qt offscreen platform plugin.

### Install and run

```bash
cd GUI
pip install -r requirements-dev.txt

# Linux / macOS:
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v

# Windows (PowerShell):
$env:QT_QPA_PLATFORM = "offscreen"
python -m pytest tests/ -v
```

Expected: tests pass with possibly a handful skipped on platforms missing
optional dependencies (e.g., display-dependent rendering tests).

### Continuous integration

GitHub Actions workflow `.github/workflows/gui-tests.yml` runs the matrix:

- ubuntu-latest, windows-latest, macos-latest
- Python 3.10, 3.11, 3.12

On Linux, system Qt/OpenGL libraries are installed before pytest runs.

### Major test files

| File                          | What it verifies                                         |
|-------------------------------|----------------------------------------------------------|
| `tests/test_config.py`        | App-config persistence and round-trip                    |
| `tests/test_xml_diagnostic.py`| XML emission, schema conformance, diagnostic outputs     |

See `GUI/tests/README.md` for the full breakdown of test categories.

---

## 3. Analytical Validation

`test_cases/abiotic/` contains five validation problems with closed-form
analytical solutions: 1D diffusion, 1D advection–diffusion, two reaction-rate
benchmarks, and an equilibrium-chemistry comparison.

A dry-run check verifies the cases are configured correctly without running
the full solver:

```bash
python tests/run_validation.py --dry-run
```

To run the cases for real (requires the compiled solver and Palabos):

```bash
# 1. Build the solver (see README §13)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --parallel

# 2. Pick one of the test_cases/abiotic/ kinetics files and copy it to root
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh

# 3. Use the matching XML config
./complab test_cases/abiotic/test2.xml
```

Each case writes a results file that `tests/run_validation.py` compares
against the analytical solution and reports the L2 error.

---

## 4. Reproducibility for Reviewers

If you only have an hour and want to verify the project compiles, runs, and
its tests pass:

```bash
# C++ unit tests (~1 sec, no Palabos)
cd tests/cpp && cmake -S . -B build && cmake --build build --parallel \
  && cd build && ctest --output-on-failure

# GUI tests (~12 sec, no solver)
cd ../../GUI && pip install -r requirements-dev.txt
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v

# Validation dry-run (no solver)
python ../tests/run_validation.py --dry-run
```

All three should report success. If anything fails, please open an issue at
<https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/issues>
with the full output and your platform details.

---

## 5. Test Configuration Notes

- **Qt offscreen platform.** GUI tests set `QT_QPA_PLATFORM=offscreen` so they
  run on CI without a display server. On Linux, `xvfb` is also available as a
  fallback through `pytest-xvfb`.
- **MPI not required for unit tests.** Both C++ unit tests and GUI tests are
  designed to run without an MPI installation. MPI is only required to run the
  full solver.
- **Palabos not required for unit tests.** The C++ tests link against
  `gtest_main` directly and use stand-alone copies of the kinetics headers, so
  reviewers do not need to download Palabos to verify them.

---

## 6. Adding New Tests

When contributing a bug fix or new feature, please add a regression test in
the appropriate location:

- C++ logic → new file under `tests/cpp/`, register it in
  `tests/cpp/CMakeLists.txt`.
- GUI behavior → new `test_*.py` under `GUI/tests/`.
- Validation case → new XML + `defineAbioticKinetics_*.hh` under
  `test_cases/abiotic/` and a matching entry in `tests/run_validation.py`.

See `CONTRIBUTING.md` for the full pull-request workflow.
