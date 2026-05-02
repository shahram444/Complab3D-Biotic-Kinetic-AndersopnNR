# CompLaB Studio — GUI Setup Guide

**Authors:** Shahram Asgari and Christof Meile  
**Affiliation:** Meile Lab, Department of Marine Sciences, University of Georgia (UGA), Athens, GA, USA  
**Contact:** [shahram.asgari@uga.edu](mailto:shahram.asgari@uga.edu)


CompLaB Studio is the graphical interface for CompLaB3D. It lets you configure
simulations visually, export `CompLaB.xml`, and launch the C++ solver — all
without touching a terminal once the solver is compiled.

---

## Requirements

| Dependency | Version | Notes |
|---|---|---|
| Python | ≥ 3.9 | |
| PySide6 | ≥ 6.4 | `pip install PySide6` |
| CompLaB3D solver | any | must be compiled first (see below) |

---

## Step 1 — Compile the CompLaB3D Solver

The GUI launches the C++ solver as a subprocess. You must compile it once
before the GUI can run simulations. The GUI itself runs without the solver
(you can edit and export XML files freely), but clicking **Run** requires
a compiled executable.

### Linux / macOS

```bash
# From the repository root (JOSS_Submit/ or the top-level repo)
cd JOSS_Submit
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
make -j$(nproc)
```

The compiled binary will be at `build/complab` (or `build/Release/complab`
on some systems). Note its full path — you will paste it into the GUI in
Step 3.

### Windows (MinGW / MSVC)

```bat
cd JOSS_Submit
mkdir build && cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
mingw32-make -j4
```

The binary will be `build\complab.exe`. Note its full path.

### MPI note

CompLaB3D uses MPI for parallelism. If you want multi-core runs from the GUI,
make sure `mpirun` (Linux/macOS) or `mpiexec` (Windows) is on your PATH and
that your MPI implementation matches the one used at compile time (OpenMPI,
MPICH, or MS-MPI).

---

## Step 2 — Install GUI Dependencies

```bash
cd JOSS_Submit/GUI
pip install PySide6
```

No other Python packages are required for normal GUI operation.

---

## Step 3 — Launch the GUI

```bash
cd JOSS_Submit/GUI
python main.py
```

On first launch you will see the main window in **dark theme** with an empty
project tree. Before running simulations, set two paths in Preferences.

---

## Step 4 — Configure Preferences

Go to **Edit → Preferences** (or press `Ctrl+,`).

### CompLaB Executable

This is the full path to the compiled `complab` binary from Step 1.

- Click **Browse** next to "CompLaB executable"
- Navigate to your `build/` folder and select `complab` (or `complab.exe`)
- Example Linux path: `/home/alice/complab3d/JOSS_Submit/build/complab`
- Example Windows path: `C:\Users\alice\complab3d\JOSS_Submit\build\complab.exe`

If you leave this field blank the GUI searches automatically in these locations
(in order): the project directory, `build/`, `Release/`, `Debug/`, `GUI/bin/`,
and the system PATH. If it still cannot find the binary, clicking **Run** will
show an error asking you to set the path manually.

### Default Project Directory

This is the folder where your simulation projects (XML files, input geometry,
output VTK files) will live.

- Click **Browse** and select or create a folder, e.g. `~/complab_projects/`
- The GUI will default to opening and saving files here
- Each simulation case should get its own subdirectory with an `input/` folder
  containing `geometry.dat`

### Theme

Choose **Dark** (default) or **Light**. The theme applies immediately when you
click **Apply & Close**. Your choice is saved to `~/.complab_studio/config.json`
and restored on the next launch.

Click **Apply & Close** to save.

---

## Step 5 — Set Up a Simulation Project

A minimal project folder looks like this:

```
my_simulation/
├── CompLaB.xml          ← exported by the GUI (or copied from test_cases/)
├── input/
│   └── geometry.dat     ← pore-geometry file
└── output/              ← created automatically by the solver
```

In the GUI:

1. **File → New Project** — creates the folder structure above
2. Fill in the parameter panels (Domain, Flow, Chemistry, Microbiology, I/O)
3. **File → Export XML** — writes `CompLaB.xml` to the project folder
4. Click **Run** — the GUI calls `mpirun -np N complab` in the project folder
   and streams solver output to the console panel

---

## Troubleshooting

### GUI opens but Run fails with "executable not found"

Set the path in **Edit → Preferences → CompLaB executable** as described in
Step 4.

### Light theme has no effect

This is fixed in the current version. If you are running an older copy of the
GUI, make sure the `gui/styles/` folder exists inside `JOSS_Submit/GUI/` and
contains `light.qss` and `main.qss`. These files should be present in the
repository; if they are missing, copy them from `GUI/gui/styles/` in the
top-level repo.

### Theme reverts to dark on next launch

This is a known bug in older versions (the saved theme name was lowercase
`"dark"` but the dropdown search was case-sensitive). It is fixed in the
current version. If you still see it, delete `~/.complab_studio/config.json`
and re-set your preferences.

### MPI errors when clicking Run

Make sure `mpirun` is on your PATH:

```bash
which mpirun        # Linux / macOS
where mpiexec       # Windows
```

If it is not found, install OpenMPI (`sudo apt install libopenmpi-dev` on
Ubuntu) or set the number of MPI ranks to 1 in the Run dialog.

### Geometry file not found

The solver always looks for `input/geometry.dat` relative to the directory
where `CompLaB.xml` is located. Make sure the `input/` subfolder exists and
contains a valid geometry file. Sample geometry files are provided in
`test_cases/abiotic/input/` and `test_cases/biotic/input/`.

---

## File Locations

| File | Purpose |
|---|---|
| `~/.complab_studio/config.json` | Saved preferences (executable path, theme, font size) |
| `JOSS_Submit/GUI/gui/styles/main.qss` | Dark theme stylesheet |
| `JOSS_Submit/GUI/gui/styles/light.qss` | Light theme stylesheet |
| `JOSS_Submit/GUI/src/` | GUI source code |
| `JOSS_Submit/GUI/tests/` | Automated GUI test suite |

---

## Running the GUI Tests

The GUI ships with 362+ automated checks that verify parameter save/load,
XML export correctness, and crash diagnostics. These do not require a compiled
solver or a display server.

```bash
cd JOSS_Submit/GUI
pip install pytest PySide6
pytest tests/ -v
```

See `tests/README.md` for a full description of what each test covers.
