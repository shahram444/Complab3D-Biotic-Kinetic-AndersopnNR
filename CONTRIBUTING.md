# Contributing to CompLaB3D

Thank you for your interest in contributing to CompLaB3D! This document
provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository on GitHub.
2. Clone your fork locally:
   ```bash
   git clone https://github.com/<your-username>/Complab3D-Biotic-Kinetic-AndersopnNR.git
   ```
3. Create a feature branch:
   ```bash
   git checkout -b feature/my-improvement
   ```

## Development Setup

### C++ Solver

**Prerequisites:**
- C++17 compiler (GCC 9+, Clang 10+, or MSVC 2019+)
- CMake 3.16+
- MPI implementation (OpenMPI or MPICH)
- Palabos library (included as submodule)

**Build:**
```bash
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

### Python GUI (CompLaB Studio)

**Prerequisites:**
- Python 3.10+

**Install with development dependencies:**
```bash
cd GUI
pip install -e ".[dev]"
```

**Run tests:**
```bash
cd GUI
python -m pytest tests/ -v
```

## How to Contribute

### Reporting Bugs

- Use the GitHub Issues tab.
- Include: steps to reproduce, expected vs. actual behaviour, OS, compiler
  version, Python version, and any relevant log output.

### Suggesting Enhancements

- Open a GitHub Issue describing the enhancement.
- Explain the use case and how it benefits the project.

### Submitting Changes

1. Make your changes on a feature branch.
2. Write or update tests if applicable.
3. Ensure all tests pass: `python -m pytest tests/ -v` (from `GUI/`).
4. Commit with a clear message describing *what* and *why*.
5. Push to your fork and open a Pull Request against `main`.

### Code Style

- **C++:** Follow the existing code style in `src/`. Use descriptive variable
  names. Keep functions focused and well-documented.
- **Python:** Follow PEP 8. The project uses PySide6 (Qt6) for the GUI.

## Adding New Kinetics Templates

CompLaB3D supports pluggable kinetics via `.hh` header files. To add a new
reaction scenario:

1. Create your kinetics header in `kinetics/` following the pattern of existing
   templates (e.g., `defineKinetics.hh`).
2. Register the template in `GUI/src/core/templates.py` and
   `GUI/src/core/kinetics_templates.py`.
3. Add corresponding tests in `GUI/tests/test_pipeline_e2e.py`.

## Code of Conduct

This project follows a [Code of Conduct](CODE_OF_CONDUCT.md). By participating
you agree to uphold a respectful, harassment-free environment.

## License

By contributing you agree that your contributions will be licensed under the
[GPL-3.0 License](LICENSE).
