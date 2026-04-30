# CompLaB3D — Windows Setup Guide

Complete walkthrough from a fresh Windows machine to running your first simulation
in the GUI, including compiling the C++ solver.

---

## Prerequisites at a glance

| Tool | Purpose | Where to get it |
|---|---|---|
| Git | Clone the repository | https://git-scm.com/download/win |
| MSYS2 | GCC / CMake / Make for Windows | https://www.msys2.org |
| MS-MPI | MPI runtime + SDK (parallel execution) | https://github.com/microsoft/Microsoft-MPI/releases |
| Python 3.11+ | Run the GUI | https://www.python.org/downloads/windows/ |

---

## Step 1 — Install Git

1. Download the installer from https://git-scm.com/download/win
2. Run it; default options are fine.
3. Open **Git Bash** (or any terminal) and verify:
   ```
   git --version
   ```

---

## Step 2 — Install MSYS2 (provides GCC, CMake, Make)

MSYS2 is the easiest way to get a full GCC toolchain on Windows.

1. Download the installer from https://www.msys2.org and run it.
   Install to the default location `C:\msys64`.

2. After installation, open the **MSYS2 MinGW 64-bit** terminal
   (search "MSYS2 MinGW 64-bit" in the Start menu — **use this terminal, not plain MSYS2**).

3. Update the package database:
   ```
   pacman -Syu
   ```
   If the window closes, reopen **MSYS2 MinGW 64-bit** and run:
   ```
   pacman -Su
   ```

4. Install GCC, CMake, and Make:
   ```
   pacman -S --needed mingw-w64-x86_64-gcc mingw-w64-x86_64-cmake mingw-w64-x86_64-make
   ```

5. Verify the tools are available:
   ```
   gcc --version
   cmake --version
   mingw32-make --version
   ```
   All three commands should print version numbers.

---

## Step 3 — Install MS-MPI (Microsoft MPI)

CompLaB3D uses MPI for parallel computation. You need **both** the runtime and the SDK.

1. Go to https://github.com/microsoft/Microsoft-MPI/releases
2. Download **both** files from the latest release:
   - `msmpisetup.exe`  ← runtime (needed to run)
   - `msmpisdk.msi`    ← SDK (needed to compile)
3. Install `msmpisetup.exe` first, then `msmpisdk.msi`.
4. Open **Command Prompt** (not MSYS2) and verify:
   ```
   mpiexec --version
   ```

> **Why both?** `msmpisetup.exe` installs the `msmpi.dll` library and `mpiexec` launcher.
> `msmpisdk.msi` installs the headers and `.lib` files that CMake needs to compile MPI code.

---

## Step 4 — Install Python 3.11 or newer

1. Download from https://www.python.org/downloads/windows/
2. Run the installer. On the first screen, **check "Add Python to PATH"** before clicking Install.
3. Verify in a new Command Prompt:
   ```
   python --version
   pip --version
   ```

---

## Step 5 — Clone the repository

Open **Git Bash** or **Command Prompt** and navigate to wherever you want to put the code:

```
git clone https://github.com/YOUR-ORG/Complab3D-Biotic-Kinetic-AndersopsonNR.git
cd Complab3D-Biotic-Kinetic-AndersopsonNR
```

The folder you end up in (containing `CMakeLists.txt`, `src/`, `GUI/`, etc.) is called
**JOSS_Submit** in these instructions.

> The Palabos library is bundled inside the repository at
> `ComapLB3D/versionControl/palabos-v2.3.0/` — no separate download needed.

---

## Step 6 — Compile the C++ solver

Everything is done inside the **MSYS2 MinGW 64-bit** terminal.

### 6a. Open MSYS2 MinGW 64-bit and navigate to JOSS_Submit

Windows paths are accessible in MSYS2 under `/c/`, `/d/`, etc.:

```bash
cd /c/Users/YourName/Complab3D-Biotic-Kinetic-AndersopsonNR/JOSS_Submit
```

Adjust the path to match where you cloned the repo.

### 6b. Create a build directory and run CMake

```bash
mkdir -p build
cd build
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release
```

CMake will scan for MS-MPI automatically. You should see lines like:
```
Enabling MPI
-- Found MPI_CXX: ...
```

If CMake cannot find MPI, make sure MS-MPI SDK was installed and try:
```bash
cmake .. -G "MinGW Makefiles" -DCMAKE_BUILD_TYPE=Release -DENABLE_MPI=OFF
```
(This disables MPI and produces a serial build; the simulation will still run
on a single core.)

### 6c. Compile

```bash
mingw32-make -j4
```

`-j4` uses 4 CPU threads; raise it if your machine has more cores.

Compilation takes **5–20 minutes** the first time because Palabos is compiled from
source. Subsequent builds are much faster.

### 6d. Confirm the executable was created

The compiled binary is placed one level above the build directory — in JOSS_Submit:

```bash
ls ../complab.exe
```

You should see `../complab.exe` listed. Note the full Windows path for Step 8:
```
C:\Users\YourName\Complab3D-Biotic-Kinetic-AndersopsonNR\JOSS_Submit\complab.exe
```

---

## Step 7 — Install Python packages for the GUI

Open **Command Prompt** (not MSYS2) and navigate to the GUI folder:

```
cd C:\Users\YourName\Complab3D-Biotic-Kinetic-AndersopsonNR\JOSS_Submit\GUI
pip install PySide6 numpy
```

**Optional** — install these for 3D VTK visualization and convergence plots:
```
pip install vtk matplotlib
```

The GUI starts and runs without `vtk` and `matplotlib`; those panels simply show
an install hint when they are absent.

---

## Step 8 — Launch the GUI

In **Command Prompt**:

```
cd C:\Users\YourName\Complab3D-Biotic-Kinetic-AndersopsonNR\JOSS_Submit\GUI
python main.py
```

The CompLaB3D window will open.

---

## Step 9 — Configure Preferences

1. In the menu bar go to **Edit → Preferences** (or press `Ctrl+,`).
2. **General tab → Default project directory**: click **Browse** and choose
   a folder where new projects will be saved (e.g., `C:\Users\YourName\CompLabProjects`).
3. Click **Apply & Close**.

> **Auto-detection**: The GUI automatically searches for `complab.exe` in the
> repository root (`JOSS_Submit\`), `build\`, `Release\`, and several other
> standard locations. If you compiled the solver in Step 6, **no executable path
> is required in Preferences** — the GUI will find it automatically.
>
> Only set **CompLaB executable** manually if you see "CompLaB executable not found"
> in the Console panel when clicking Run. In that case, click **Browse** and
> navigate to:
> ```
> C:\Users\YourName\...\JOSS_Submit\complab.exe
> ```

---

## Step 10 — Create a new project

1. **File → New Project** (or `Ctrl+N`).
2. In the dialog that opens:
   - **Left panel**: click a simulation template (e.g., *Aerobic Degradation*).
   - **Right panel**: read the template description, kinetics file summary,
     and compilation notes.
   - **Project name**: type a name (e.g., `MyFirstSim`).
   - **Save directory**: should already be the folder from Preferences.
3. Click **Create**.

The GUI creates the project folder automatically:
```
<projects_dir>\MyFirstSim\
    input\
        geometry.dat        ← sample pore geometry (50×30×30)
    output\                 ← simulation results will go here
    defineKinetics.hh       ← biotic kinetics (matches your template)
    defineAbioticKinetics.hh
```

> **Important**: `defineKinetics.hh` and `defineAbioticKinetics.hh` are placed in
> your **project folder**, not in JOSS_Submit. They are read by the solver at runtime
> through `#include "../defineKinetics.hh"`. Before running, copy them to the
> **JOSS_Submit root** (same folder as `CMakeLists.txt`) and recompile if you changed
> kinetics parameters. See the "Recompile after changing kinetics" note below.

---

## Step 11 — Review and edit simulation parameters

Use the **Parameters** panel in the main window to set:

- Domain dimensions (must match your `geometry.dat` file)
- Number of timesteps, output interval
- Substrate concentrations, diffusion coefficients
- Biofilm kinetics parameters

The sample `geometry.dat` is 50 × 30 × 30 voxels. Set the domain size to match.

---

## Step 12 — Export the XML input file (optional preview step)

You can review the generated XML before running:

**File → Export CompLaB.xml** (or `Ctrl+Shift+E`).

The file is saved as `CompLaB.xml` in your project folder.

> **Note**: Clicking **Run** in the next step automatically exports a fresh
> `CompLaB.xml` to your project folder, so this manual export step is not
> strictly required. It is useful if you want to inspect or version-control
> the XML before running.

---

## Step 13 — Run the simulation

Click the green **Run** button in the toolbar (or **Simulation → Run**).

The GUI launches `complab.exe` with `CompLaB.xml`, streams the solver output to
the **Console** panel, and updates the convergence plot in real time.

Output `.vti` and `.vtk` files appear in `output\` as the simulation progresses.
Open them in the **3D Viewer** tab using **View → Open VTK in Viewer**.

---

## Recompile after changing kinetics parameters

Kinetics equations are compiled into the solver at build time (via
`#include "../defineKinetics.hh"`). If you change kinetics parameters in the GUI,
you must recompile the solver before those changes take effect:

1. When you click **Run**, the GUI writes updated `defineKinetics.hh` and
   `defineAbioticKinetics.hh` files to your **project folder**.

2. Copy those two files to the **JOSS_Submit root** (the folder that contains
   `CMakeLists.txt`), overwriting the existing ones:
   ```
   copy "C:\...\MyProject\defineKinetics.hh"         "C:\...\JOSS_Submit\"
   copy "C:\...\MyProject\defineAbioticKinetics.hh"  "C:\...\JOSS_Submit\"
   ```

3. Recompile in the MSYS2 MinGW 64-bit terminal:
   ```bash
   cd /c/Users/YourName/.../JOSS_Submit/build
   mingw32-make -j4
   ```
   Only the changed files are recompiled — this is fast (< 1 minute usually).

4. Click **Run** again in the GUI. The updated `complab.exe` is now active.

---

## Troubleshooting

### `cmake` cannot find MPI
Make sure `msmpisdk.msi` was installed. Then try specifying the MPI paths manually
or disable MPI with `-DENABLE_MPI=OFF` for a serial build.

### `mingw32-make: command not found`
You are probably in a plain MSYS2 shell instead of **MSYS2 MinGW 64-bit**. Close
the terminal and reopen it using "MSYS2 MinGW 64-bit" from the Start menu.

### `Palabos source not found` CMake error
The repo was cloned without the bundled Palabos subdirectory. Run:
```
git submodule update --init --recursive
```

### GUI opens but clicking "Preferences" does nothing
This is usually a Python environment issue. Confirm PySide6 is installed in the
same Python you use to launch `main.py`:
```
python -c "import PySide6; print(PySide6.__version__)"
```

### `complab.exe` not found when clicking Run
Go to **Edit → Preferences → General** and set the executable path to the full
path of `complab.exe` compiled in Step 6.

### Geometry not found / domain mismatch error
The default geometry is 50 × 30 × 30. Make sure the **Nx / Ny / Nz** fields in
the Parameters panel match the actual dimensions of your `.dat` file.

### GUI shows "VTK not installed" in the 3D viewer
Install vtk: `pip install vtk`. The rest of the GUI works fine without it.

### Simulation exits immediately with an XML error
Check the Console panel for the diagnostic message. Common causes:
- `CompLaB.xml` has not been exported yet (do **File → Export CompLaB.xml** first).
- The XML file is in the wrong directory (must be in the same folder as `complab.exe`
  or passed as a path argument — the GUI handles this automatically).
