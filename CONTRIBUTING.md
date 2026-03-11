# Contributing to CompLaB3D

Thank you for your interest in contributing to CompLaB3D! This document
provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

1. Check the [issue tracker](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/issues) to see if the bug has already been reported.
2. If not, open a new issue with:
   - A clear, descriptive title
   - Steps to reproduce the problem
   - Expected behavior vs. actual behavior
   - Your environment (OS, compiler version, Python version, Palabos version)
   - Any relevant log output or error messages

### Suggesting Features

Open an issue with the "enhancement" label describing:
- The problem your feature would solve
- Your proposed solution
- Any alternatives you have considered

### Submitting Changes

1. Fork the repository and create a branch from `main`.
2. Make your changes, following the coding style of the existing codebase.
3. Add tests for any new functionality:
   - C++ tests go in `tests/cpp/` using GoogleTest
   - Python tests go in `GUI/tests/` using pytest
4. Ensure all existing tests pass:
   ```bash
   # C++ tests
   cd tests/cpp/build && cmake .. && cmake --build . && ctest

   # Python tests
   cd GUI && python -m pytest tests/ -v
   ```
5. Submit a pull request with a clear description of your changes.

## Development Setup

### C++ Solver

```bash
# Build solver (requires Palabos)
cd src && make

# Build and run unit tests (no Palabos needed)
cd tests/cpp
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
cmake --build . --parallel
ctest --output-on-failure
```

### Python GUI

```bash
cd GUI
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Code Style

- **C++**: Follow the existing style in `src/`. Use descriptive variable names.
  Keep functions focused and reasonably sized.
- **Python**: Follow PEP 8. Use type hints where practical.

## Adding a New Kinetics System

To add a new reaction system:

1. Create a new `.hh` header file following the pattern in `defineKinetics.hh`
   or `defineAbioticKinetics.hh`.
2. Implement the `defineRxnKinetics()` or `defineAbioticRxnKinetics()` function.
3. Add unit tests in `tests/cpp/`.
4. Add corresponding GUI template in `GUI/src/core/templates.py` if applicable.
5. Document the reaction system in the test case README.

## Questions?

Open an issue or contact the maintainers.
