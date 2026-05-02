# CompLaB Studio GUI Test Suite

**Authors:** Shahram Asgari and Christof Meile  
**Affiliation:** Meile Lab, Department of Marine Sciences, University of Georgia (UGA), Athens, GA, USA  
**Contact:** [shahram.asgari@uga.edu](mailto:shahram.asgari@uga.edu)




**What the tests actually do:** Every time someone changes the GUI code,
362+ automated checks run in about one second. Each check verifies a specific
behaviour of the GUI -- that a parameter is correctly saved, that an error
is correctly detected before the simulation starts, that a crash report
correctly identifies the cause. This prevents bugs from silently corrupting
your simulation setup.

---

## What Does the GUI Do, and What Can Go Wrong?

CompLaB Studio is a graphical interface that helps you:

1. Set up simulation parameters (domain size, flow velocity, substrate
   properties, microbial kinetics, geochemical equilibria)
2. Export those parameters as `CompLaB.xml` -- the file the C++ solver reads
3. Deploy `defineKinetics.hh` and `defineAbioticKinetics.hh` alongside the XML
4. Launch the solver and monitor its progress in real time

There are three places where things can go wrong silently:

- **Data loss in the GUI**: you type a value in one panel, save the project,
  re-open it, and the value is gone because the load/save code has a bug
- **Invalid XML exported**: the XML is syntactically correct but contains a
  value that causes the C++ solver to crash with an opaque error code
- **Wrong kinetics deployed**: the substrate/microbe count in the XML does not
  match what the `.hh` kinetics code accesses (C[2] when only 1 substrate
  is defined causes heap corruption)

The test suite is designed to catch all three categories.

---

## Running the Tests (One Minute, No Solver Required)

The commands below are identical on Linux, macOS, and Windows.
Use **Terminal** on Linux/macOS, or **Command Prompt / PowerShell** on Windows.

### Step 1 — Install Python 3.10 or later

- **Linux (Ubuntu/Debian):** `sudo apt install python3 python3-pip`
- **macOS:** download from [python.org](https://www.python.org/downloads/)
  or `brew install python`
- **Windows:** download from [python.org](https://www.python.org/downloads/).
  On the first installer screen, tick **"Add Python to PATH"** before clicking Install.

Verify it worked: `python --version` should print `Python 3.10.x` or higher.

### Step 2 — Install the required packages (first run only)

```bash
cd GUI
pip install PySide6 pytest pytest-qt
```

On some Linux systems pip may refuse to install into the system Python.
If you see an "externally managed environment" error, use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows (Command Prompt)
pip install PySide6 pytest pytest-qt
```

### Step 3 — Run the tests

```bash
python -m pytest tests/ -v
```

**Expected output:**

```
362 passed, 5 skipped in 1.02s
```

The 5 skipped tests are the full end-to-end simulation runner tests
(TestFullSimulationRun). These use a fake solver subprocess and require
a graphical Qt backend. They run correctly on Linux with a display,
macOS, and **Windows**. On headless CI servers, set `QT_QPA_PLATFORM=offscreen`
(done automatically by conftest.py).

No C++ compiler, no MPI, no Palabos, and no actual simulation runs are
needed for any of the 362 non-skipped tests.

---

## Test Files and What Each Covers

There are 9 test files. Each is described below in plain terms -- what
physical or software concept it protects.

---

### test_project_model.py -- Parameter Validation Before Export

**Source tested:** src/core/project.py -- the CompLaBProject data model
and its validate() method.

**What is being tested:** Before the GUI exports CompLaB.xml, it runs
validate() to check that all user-entered values are physically and logically
consistent. This test file verifies that validate() correctly catches every
known category of error.

**Why this matters:** The C++ solver does not produce helpful error messages
when given bad input -- it either crashes with a heap-corruption code or
silently produces wrong results. The GUI's job is to catch problems before the
solver ever sees them.

**Checks performed:**

| Category     | What is flagged                                                                                                                                      |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| Domain       | nx = 0 (no lattice sites); dx < 0 (negative spacing); unit not in ["um","mm","m"]                                                                    |
| Fluid        | tau < 0.5 or tau > 2.0 (LBM unstable); delta_P < 0 (unphysical pressure)                                                                             |
| Substrates   | Duplicate names; negative initial concentration; D_biofilm > D_pore (physically impossible -- EPS always reduces diffusivity); invalid boundary type |
| Microbiology | Biotic mode enabled with zero microbes; CA solver with no material number; solver_type not in ["CA","LBM"]                                           |
| Equilibrium  | Enabled with no components; stoichiometry matrix row count != substrate count                                                                        |
| Cross-checks | Kinetics enabled but no substrates; abiotic kinetics enabled but no substrates                                                                       |

**What PASS means:** Every category of user input error is detected and
reported with a helpful message before the solver starts. A failure here means
a malformed XML will be silently exported, leading to an opaque crash.

---

### test_templates.py -- Simulation Starting Points

**Source tested:** src/core/templates.py -- all 9 built-in simulation templates.

**What is being tested:** When a user opens CompLaB Studio for the first time,
they choose from 9 pre-configured templates. Each template sets up a complete,
self-consistent simulation. These tests verify that every template produces a
valid configuration with no blocking errors.

**The 9 templates:**

| Template               | Physics                          | Substrates            | Microbes     |
| ---------------------- | -------------------------------- | --------------------- | ------------ |
| Flow only              | Navier-Stokes flow, no chemistry | 0                     | 0            |
| Diffusion only         | Pure Fickian diffusion, Pe = 0   | 1 (Tracer)            | 0            |
| Tracer transport       | Advection-diffusion, Pe = 1      | 1 (Tracer)            | 0            |
| Abiotic reaction       | First-order decay A -> B         | 2 (Reactant, Product) | 0            |
| Abiotic equilibrium    | Carbonate speciation             | 5 (species)           | 0            |
| Biotic sessile         | Biofilm growth on surfaces       | 1 (DOC)               | 1 (CA)       |
| Biotic planktonic      | Suspended microbial growth       | 1 (DOC)               | 1 (LBM)      |
| Sessile + planktonic   | Biofilm + suspended cells        | 1 (DOC)               | 2 (CA + LBM) |
| Coupled biotic-abiotic | Biofilm + abiotic reaction       | 2 (DOC, byproduct)    | 1 (CA)       |

**Key checks:**

- Each template passes validate() with zero errors (ready to run out of the box)
- Simulation mode flags match the template type (biotic_mode, enable_kinetics)
- Substrate count and names match the template description
- Microbe solver type matches (CA for sessile, LBM for planktonic)
- Both defineKinetics.hh and defineAbioticKinetics.hh are attached, even
  for templates that don't use kinetics (the solver requires both files unconditionally)

**What PASS means:** Any user who picks a template and clicks "Run" without
changing any parameters will get a valid, working simulation. A failure means
a template is broken out of the box.

---

### test_xml_io.py -- XML and Project File Serialisation

**Source tested:** src/core/project_manager.py -- XML export/import and
JSON project save/load.

**What is being tested:** Two file formats:

1. CompLaB.xml: The configuration file read by the C++ solver. Its
   structure must exactly match what the solver's XML parser (TinyXML) expects.
   Every field name, tag hierarchy, and value format must be correct.

2. .complab JSON: The GUI's own project file, which stores everything
   needed to restore the full GUI state including kinetics source code.

**XML structure checks:**

- Root element is <parameters> (solver crashes if this is wrong)
- All 7 required sections present: path, simulation_mode, LB_numerics,
  chemistry, microbiology, equilibrium, IO
- Substrate and microbe counts in <number_of_substrates> match the number
  of <substrate{i}> child elements
- Boolean values are the strings "true" / "false" (not Python True/False)
- Floating-point values use scientific notation correctly (1.000000e-09)

**Round-trip checks (export then re-import):**

For all 9 templates, the following fields must survive export then import unchanged:
domain dimensions (nx, ny, nz, dx), fluid tau, substrate names and diffusion
coefficients, boundary condition types, simulation mode flags, microbe names
and solver types, equilibrium stoichiometry matrix, log K values.

**What PASS means:** The XML exported by the GUI is structurally correct for
the C++ solver, and no data is lost when a project is saved and reopened.

---

### test_kinetics.py -- Kinetics C++ Code Generation

**Source tested:** src/core/kinetics_templates.py -- the system that generates
defineKinetics.hh and defineAbioticKinetics.hh C++ source code.

**What is being tested:** The kinetics .hh files are user-editable C++ code
that is compiled as part of the solver. If the generated code is syntactically
invalid or accesses the wrong array indices, the solver either fails to compile
or crashes at runtime.

**Code validity checks (for all 9 template kinetics):**

- Include guards present (#ifndef, #define, #endif)
- Required function name defineRxnKinetics is present (solver calls this by name)
- Required namespace KineticsStats is present (solver calls getStats() unconditionally)
- Both defineKinetics.hh and defineAbioticKinetics.hh are non-empty

**Array-index cross-validation:**

The validate_kinetics_vs_project() function parses the C++ source and extracts
which array indices are accessed (C[0], B[1], subsR[2], etc.), then checks
them against the actual substrate and microbe counts in the project.

Example: biotic_sessile template uses C[0] and B[0].
  Project has 1 substrate and 1 microbe -> indices 0..0 are valid -> OK.

Example: user edits kinetics to access C[2] but project has only 1 substrate.
  Index 2 >= substrate count 1 -> flagged as out-of-bounds -> error reported
  before compilation even starts.

**What PASS means:** All template kinetics files are valid C++, and the
cross-validation system correctly catches index mismatches before compilation.

---

### test_simulation_runner.py -- Subprocess Lifecycle

**Source tested:** src/core/simulation_runner.py -- the Qt thread that
launches the C++ solver as a subprocess.

**What is being tested:** The subprocess management layer is the most complex
component in the GUI. It must launch the solver and read its output line by line
without blocking, parse iteration progress, handle crashes, cancel on user
request, and handle edge cases including stdout flooding, partial final lines,
MPI process groups, and Qt garbage collection.

**How it works (no real solver needed):**
Each test writes a small Python script that mimics the C++ solver's output
format. The SimulationRunner runs this fake solver and the test verifies
the signals it emits.

| Test scenario             | What is verified                                            |
| ------------------------- | ----------------------------------------------------------- |
| Normal completion         | exit code 0; all progress events captured; log file written |
| Stdout flood (5000 lines) | reader keeps up; process exits cleanly                      |
| Cancel after 3 iterations | process is actually dead (not just signal sent)             |
| MPI path wrong            | exit code -1; "not found" in error message                  |
| Solver exits 42           | exit code 42 captured and reported correctly                |
| SIGSEGV (segfault)        | exit code -11 captured; crash diagnostic triggered          |
| No geometry file          | exit code -1; "not found" in output                         |
| Qt garbage collection     | parent reference prevents premature destruction             |

**What PASS means:** The simulation runner handles all subprocess lifecycle
events correctly.

---

### test_pipeline_e2e.py -- Full End-to-End Workflow

**Source tested:** All of src/core/ together -- project model, templates,
XML export, kinetics deployment, file validation, simulation runner.

**What is being tested:** The complete workflow from choosing a template through
running a simulation, exercising every component in sequence.

**The workflow covered:**

```
1. Create project from template
2. Construct a geometry.dat file (controlled voxel counts)
3. validate() -- check all settings
4. Export CompLaB.xml
5. Deploy defineKinetics.hh and defineAbioticKinetics.hh
6. validate_files() -- check exported files match project settings
7. Run SimulationRunner with fake solver
8. Verify: exit code, progress events, log file created
```

**Geometry file validation:** validate_files() checks that geometry.dat
has exactly nx * ny * nz lines. A mismatch between the geometry file and the
XML domain dimensions is the single most common cause of heap-corruption crashes.

| Geometry test        | What it catches                                   |
| -------------------- | ------------------------------------------------- |
| Correct size passes  | No false positives                                |
| Wrong size flagged   | User changed nx in GUI but not the geometry file  |
| Missing file flagged | User forgot to create the geometry before running |

**What PASS means:** The entire workflow from GUI setup to simulation start
is internally consistent. Every component hands off correctly to the next.

---

### test_xml_diagnostic.py -- Crash Diagnostic Analysis

**Source tested:** src/core/xml_diagnostic.py -- the module that analyses
CompLaB.xml after a solver crash.

**What is being tested:** When the C++ solver crashes with an opaque exit code
(e.g. Windows 0xC0000374 = Heap Corruption), the diagnostic module reads the
XML and kinetics headers to identify the most likely root cause. This produces
a human-readable report rather than leaving the user with a bare exit code.

**Exit codes that are mapped to explanations:**

| Exit code   | Error type                    | Most likely cause                |
| ----------- | ----------------------------- | -------------------------------- |
| -1073740940 | Heap Corruption (0xC0000374)  | Geometry file size != nx*ny*nz   |
| -1073741819 | Access Violation (0xC0000005) | Null pointer in kinetics code    |
| -11         | Segmentation Fault (SIGSEGV)  | Array out-of-bounds access       |
| 134         | Abort (SIGABRT)               | Internal assertion failure       |
| 1           | Configuration Error           | Bad XML value rejected by solver |

**What the diagnostic checks:**

- Geometry file byte count vs. nx*ny*nz (supports binary and text formats)
- C[n] and B[n] array accesses in kinetics .hh vs. substrate/microbe count
- tau <= 0.5 produces negative LBM viscosity
- nx < 3 means no interior lattice cells exist
- Required XML sections missing (path, simulation_mode, LB_numerics, IO)
- half_saturation_constants count != substrate count
- All-Neumann + zero initial concentration means no substrate enters the domain

**What the tests verify:**

- Known exit codes produce the correct error-type label in the report
- Missing XML file produces an error message, not a Python exception
- Malformed XML produces a parse-error message, not a Python exception
- Geometry size mismatch is flagged; correct geometry size passes cleanly
- C[2] in kinetics with only 1 substrate is flagged
- C[99] in a comment is NOT flagged (comment stripping works correctly)
- The diagnostic report always contains the required sections
- save_diagnostic_report() creates the file and returns its path

**Bug fixed during testing:** The original save_diagnostic_report() had
os.makedirs() outside the exception handler, so it could crash instead of
returning "" on failure. The test found the bug; the fix was applied to
xml_diagnostic.py.

**Why this was not tested before:** xml_diagnostic.py is a 522-line module
that is only invoked after a crash, making it hard to test manually. These
47 tests exercise the diagnostic logic systematically for the first time.

---

### test_config.py -- Application Settings Persistence

**Source tested:** src/config.py -- the AppConfig class.

**What is being tested:** The GUI stores user preferences (solver executable
path, recent project list, theme, font size) as a JSON file at
~/.complab_studio/config.json. These settings are read at startup and written
at shutdown. If they are corrupted or lost, the user has to reconfigure from
scratch.

**Checks performed:**

| Category           | What is verified                                                               |
| ------------------ | ------------------------------------------------------------------------------ |
| Defaults           | Every setting has the correct default value on first run                       |
| Get/Set            | set(key, value) is immediately reflected by get(key)                           |
| Persistence        | Saved values survive creating a new AppConfig instance (simulates app restart) |
| Recent projects    | Newest at index 0; duplicates moved to front; list capped at 10 entries        |
| add_recent() saves | Re-opening the GUI shows the updated list (add_recent calls save())            |
| Malformed JSON     | Corrupted config file falls back to defaults -- GUI still starts               |
| Truncated JSON     | Partial JSON file falls back to defaults                                       |
| Wrong JSON type    | JSON array instead of object falls back to defaults                            |
| Missing file       | Fresh install with no config file starts with all defaults                     |
| Partial config     | Config from older GUI version merges correctly with new defaults               |

**Bug fixed during testing:** The original _load() method caught
json.JSONDecodeError and OSError but not TypeError, which is raised when the
config file contains a valid JSON array [1, 2, 3] instead of an object {...}.
This would crash the GUI at startup. The test found the bug; the fix (adding
TypeError and ValueError to the except clause) was applied to config.py.

**What PASS means:** The GUI always starts cleanly regardless of config file
state, and user preferences are reliably saved and restored.

---

## Test Count Summary

| Test file                 | Checks           | Qt needed?   |
| ------------------------- | ---------------- | ------------ |
| test_project_model.py     | 24               | No           |
| test_templates.py         | 38               | No           |
| test_xml_io.py            | 48               | No           |
| test_kinetics.py          | 70               | No           |
| test_pipeline_e2e.py      | 82 (+ 5 with Qt) | 5 tests only |
| test_simulation_runner.py | ~11              | Yes (all)    |
| test_gui_panels.py        | ~80              | Yes (all)    |
| test_xml_diagnostic.py    | 47               | No           |
| test_config.py            | 36               | No           |
| **Total without Qt**      | **~362**         |              |
| **Total with Qt**         | **~458**         |              |

The "without Qt" tests run anywhere: headless CI, WSL, any Python 3.10+
environment. The "with Qt" tests additionally require PySide6 to be installed
with a working EGL/OpenGL backend (standard on Linux desktops, macOS, Windows).

---

## Prerequisites and Installation

| Requirement | Minimum | How to check                                           | Works on          |
| ----------- | ------- | ------------------------------------------------------ | ----------------- |
| Python      | 3.10+   | `python --version`                                     | Linux, macOS, Windows |
| PySide6     | 6.5+    | `python -c "import PySide6; print(PySide6.__version__)"` | Linux, macOS, Windows |
| pytest      | 7.4+    | `python -m pytest --version`                           | Linux, macOS, Windows |
| pytest-qt   | 4.2+    | listed in: `python -m pytest --version` (plugins)      | Linux, macOS, Windows |

```bash
# Install everything in one step:
pip install PySide6 pytest pytest-qt

# Or, if you have a requirements file:
pip install -r requirements.txt -r requirements-dev.txt

# Verify Qt works (needed for panel and runner tests):
python -c "from PySide6.QtWidgets import QApplication; app = QApplication([]); print('OK')"
```

**No C++ solver needed.** All subprocess-dependent tests use a Python script
as a fake solver that mimics the real solver's output format.

**PySide6 on Windows** bundles its own Qt libraries and OpenGL backend — no
extra installation is required. Just `pip install PySide6` and the GUI tests
will find everything they need automatically.

---

## Running Specific Tests

```bash
# All tests (requires Qt for full count):
python -m pytest tests/ -v

# Only tests that don't need Qt (fast, works anywhere):
python -m pytest tests/test_project_model.py tests/test_templates.py \
  tests/test_xml_io.py tests/test_kinetics.py tests/test_pipeline_e2e.py \
  tests/test_xml_diagnostic.py tests/test_config.py -v

# One specific test class:
python -m pytest tests/test_project_model.py::TestValidationFluid -v

# One specific test:
python -m pytest tests/test_xml_diagnostic.py::TestGeometrySizeCheck::test_mismatched_geometry_flagged_as_error -v

# All tests matching a name pattern:
python -m pytest tests/ -k "round_trip" -v
python -m pytest tests/ -k "kinetics" -v
python -m pytest tests/ -k "geometry" -v
```

---

## Interpreting Test Output

**All tests pass:**

```
362 passed in 1.02s
```

Every verified behaviour is correct.

**A test fails:**

```
FAILED tests/test_xml_io.py::TestXMLRoundTrip::test_substrate_names_survive
  AssertionError: assert 'DOC' == 'substrate_0'
```

The message shows actual vs. expected values. In this example, the substrate
name was not preserved through an XML export/import cycle -- look at
export_xml() or import_xml() in project_manager.py for where substrate names
are written or read.

**An ImportError on collection (Linux only):**

```
ERROR tests/test_gui_panels.py -- ImportError: libEGL.so.1: cannot open shared object file
```

This is a Linux-only issue. PySide6 is installed but the system OpenGL/EGL
library is missing. Fix:
```bash
sudo apt install libegl1    # Ubuntu / Debian
```
This error does **not** occur on macOS or Windows — PySide6 bundles its own
graphics backend on those platforms. If you are on a headless Linux server
(no display at all), run only the non-Qt tests:
```bash
python -m pytest tests/test_project_model.py tests/test_templates.py \
  tests/test_xml_io.py tests/test_kinetics.py tests/test_pipeline_e2e.py \
  tests/test_xml_diagnostic.py tests/test_config.py -v
```

---

## Continuous Integration

GitHub Actions runs on every push that touches GUI/:

```yaml
QT_QPA_PLATFORM=offscreen python -m pytest tests/ -v
# across Python 3.10, 3.11, 3.12
```

The GUI Tests badge on the main README reflects the most recent run.

---

## Troubleshooting

### All Platforms

**ModuleNotFoundError: No module named 'src'**
You must run pytest from the `GUI/` directory, not from the repo root:
```bash
cd GUI
python -m pytest tests/ -v
```

**fixture 'qtbot' not found**
```bash
pip install pytest-qt
```

**test_templates.py fails with unexpected validation errors**
```bash
python -m pytest tests/test_templates.py -v -s
```
The `assert len(errors) == 0, f"Unexpected errors: {errors}"` message shows
exactly which validation check failed and what value triggered it.

**test_xml_diagnostic.py fails with format mismatch**
The diagnostic output format was changed. Tests check for specific strings
like `[Geometry]`, `[Kinetics]`, `HOW TO FIX`. If these were renamed in
xml_diagnostic.py, update the corresponding assertions in test_xml_diagnostic.py.

---

### Linux Only

**ImportError: libEGL.so.1**
```bash
sudo apt install libegl1    # Ubuntu / Debian
```
This is not needed on macOS or Windows.

**"externally managed environment" error from pip**
Use a virtual environment:
```bash
python -m venv venv
source venv/bin/activate
pip install PySide6 pytest pytest-qt
python -m pytest tests/ -v
```

---

### Windows Only

**"python" is not recognized**
Python was not added to PATH during installation. Re-run the Python installer
and tick **"Add Python to PATH"**, or add `C:\Users\YourName\AppData\Local\Programs\Python\Python311`
to PATH manually via Start → "Edit environment variables".

**pip install fails with SSL error**
Update pip first:
```bat
python -m pip install --upgrade pip
```

**Tests hang or Qt window appears briefly then closes**
This is normal on Windows during the Qt-dependent tests. The window is the
offscreen Qt application created during the test run. It closes automatically
when the test ends.

---

For the mathematical description of the simulation physics, see
docs/CompLaB3D_Technical_Guide.md. For how to run the C++ unit tests,
see tests/README.md at the repository root.


