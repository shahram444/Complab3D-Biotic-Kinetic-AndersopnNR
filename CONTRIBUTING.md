# Contributing to CompLaB3D

Thank you for your interest in contributing to CompLaB3D and CompLaB Studio.
This document describes the workflow we use, the kinds of contributions we
welcome, and how to get in touch.

---

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).
By participating, you agree to uphold its terms. Please report unacceptable
behavior to the maintainers (see contact details at the bottom of this file).

---

## Ways to Contribute

We welcome the following kinds of contributions:

- **Bug reports** — open an issue describing what you observed, what you
  expected, and how to reproduce it.
- **Feature requests** — open an issue describing the use case and the
  scientific motivation.
- **Documentation improvements** — fix typos, clarify wording, add examples,
  or expand the technical guides.
- **Test cases** — add validation cases (analytical solutions, benchmark
  comparisons, regression tests).
- **Bug fixes and feature implementations** — submit a pull request following
  the workflow described below.
- **Citations and adoption notes** — if you used CompLaB3D in a publication,
  let us know via an issue so we can add it to the project's reference list.

---

## Reporting Issues

Before opening a new issue:

1. Search [existing issues](https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/issues)
   to see whether the problem has already been reported.
2. If not, open a new issue and include:
   - **A clear description** of the problem.
   - **Reproduction steps** (XML configuration, geometry file, GUI screenshots
     if relevant).
   - **Environment details**: OS, compiler version, Palabos version, Python /
     PySide6 version (for GUI issues), MPI implementation if applicable.
   - **Expected vs. actual behavior**.
   - **Console output, error messages, or stack traces**.

Issue templates may be available in the repository's `.github/` folder.

---

## Submitting a Pull Request

We follow a standard fork-and-PR workflow:

1. **Fork** the repository on GitHub.
2. **Create a feature branch** from `main`:

   ```bash
   git checkout -b feat/short-descriptive-name
   ```

3. **Make your changes** in small, logical commits with descriptive messages.
4. **Run the test suite** locally before pushing (see [TESTING.md](TESTING.md)
   for full instructions). At minimum:

   ```bash
   # C++ unit tests
   cd tests/cpp && mkdir -p build && cd build
   cmake .. -DCMAKE_BUILD_TYPE=Release && cmake --build . --parallel
   ctest --output-on-failure

   # Python / GUI tests
   cd GUI && pip install -e ".[dev]"
   QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v
   ```

5. **Push** your branch to your fork:

   ```bash
   git push origin feat/short-descriptive-name
   ```

6. **Open a pull request** against the upstream `main` branch. Fill in the
   PR template (if present) and link any related issues with `Closes #N`.
7. **Respond to review feedback.** A maintainer will review the PR; please be
   patient — turnaround may take a few days.
8. Once approved and CI is green, the PR will be merged.

---

## Coding Standards

### C++ (solver)

- C++14 or later.
- Match the existing style in `src/complab.cpp` (4-space indentation,
  `lowerCamelCase` for functions and variables, `UpperCamelCase` for types).
- Keep new functions documented with brief Doxygen-style comments
  (`/// @brief ...`).
- Avoid introducing new external dependencies without prior discussion.

### Python (GUI)

- Python 3.10+.
- We use `black` formatting (line length 100) and `ruff` for linting. Run:

  ```bash
  black GUI/src GUI/tests
  ruff check GUI/src GUI/tests
  ```

- Type hints are encouraged on all new functions.
- Keep PySide6-specific code in panel modules; keep XML / config-generation
  code separate so it remains unit-testable without a Qt application.

### Tests

- Every bug fix should include a regression test that fails on `main` and
  passes on your branch.
- Every new feature should include unit tests covering the typical paths and
  at least one edge case.

### Commit messages

We follow a lightweight Conventional Commits style:

```
feat: add new boundary condition type for periodic flow
fix: prevent NaN propagation when biofilm density is zero
docs: clarify XML schema for equilibrium chemistry section
test: add regression test for issue #42
refactor: split kinetic-rate evaluation into its own header
```

---

## Adding New Test Cases

Test cases live in `test_cases/` (analytical/validation) and `tests/cpp/`
(unit tests). To add a new validation case:

1. Create a new subdirectory under `test_cases/` with a clear name
   (e.g., `test_cases/diffusion_dirichlet/`).
2. Include the XML configuration, geometry file, and an `expected_output/`
   folder with reference VTI files or CSV summaries.
3. Add a `README.md` documenting the analytical solution being checked, the
   expected error tolerance, and how to run it.
4. Hook it into `tests/run_validation.py` so it runs automatically in CI.

---

## Editing Reaction Kinetics

User-defined kinetics live in `defineKinetics.hh` and
`defineAbioticKinetics.hh`. If your change affects the reaction templates,
please:

- Document the new rate-expression conventions in the file's header comment.
- Add an example XML configuration that exercises the new template.
- Update the GUI's Kinetics Editor (`GUI/src/.../kinetics_editor.py`) so the
  GUI can generate the new templates without manual editing.

---

## Getting Support

- **Bug reports / feature requests:** open an issue at
  <https://github.com/shahram444/Complab3D-Biotic-Kinetic-AndersopnNR/issues>.
- **General questions / scientific discussion:** open a GitHub Discussion
  (when enabled) or email the maintainers.
- **Commercial licensing of CompLaB Studio:** see
  <https://uga.flintbox.com/#technologies/aa12627e-b4e4-43dc-b458-ff56d0cb4480>.

---

## Maintainers

- **Shahram Asgari** — Department of Marine Sciences, University of Georgia
  ([Shahram.Asgari@uga.edu](mailto:Shahram.Asgari@uga.edu),
  ORCID [0009-0004-3810-2739](https://orcid.org/0009-0004-3810-2739))
- **Christof Meile** — Department of Marine Sciences, University of Georgia
  ([cmeile@uga.edu](mailto:cmeile@uga.edu),
  ORCID [0000-0002-0825-4596](https://orcid.org/0000-0002-0825-4596))

---

## License

By contributing to CompLaB3D, you agree that your contributions will be
licensed under the same terms as the rest of the project: the GNU Affero
General Public License, version 3 (AGPL-3.0). See [LICENSE](LICENSE) and
[GUI/LICENSE](GUI/LICENSE) for full terms, including the dual-licensing
arrangement applied to CompLaB Studio.
