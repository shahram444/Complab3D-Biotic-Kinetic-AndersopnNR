# Changelog

All notable changes to CompLaB3D are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-03-10

### Added
- CompLaB Studio 2.1 GUI with PySide6 (Qt6) interface.
- 9 simulation scenario templates (flow-only through coupled biotic-abiotic).
- Template selector, XML generator, and kinetics code generator in GUI.
- 3D geometry viewer (VTK) and geometry creator dialog.
- Solver manager panel with MPI run support and progress monitoring.
- 93 automated tests (pytest + pytest-qt) covering pipeline and solver lifecycle.
- GitHub Actions CI for GUI tests (Python 3.10, 3.11, 3.12) and JOSS paper PDF.
- JOSS paper (paper.md, paper.bib, architecture figure).
- CITATION.cff, codemeta.json, CONTRIBUTING.md, CODE_OF_CONDUCT.md.
- Detailed INSTALL.md with platform-specific instructions.

### Changed
- Rewrote kinetics module to support 9 clean scenario templates.
- Improved geometry creator and solver runner GUI panels.

### Fixed
- Heap corruption in C++ solver: corrected buffer size and variable assignment.
- Flow-only template: Pe=0 changed to Pe=1, set simulation_mode, save VTI on exit.
- Geometry format: solver reads TEXT not binary format.
- MPI run panel integration issues.
- Solver crash (0xC0000005) when running with 0 substrates/microbes.
- Critical compilation bugs in all kinetics templates.

## [2.0.0] - 2025-01-01

### Added
- Initial C++ solver with LBM Navier-Stokes flow, advection-diffusion, Monod
  kinetics, abiotic reactions, cellular-automata biofilm, and Newton-Raphson
  equilibrium solver with Anderson acceleration.
- MPI parallel execution support.
- VTI output for ParaView visualisation.
- CMake build system.
- Example XML configuration files.
- Test cases for abiotic and biotic scenarios.
