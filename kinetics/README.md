# CompLaB3D Kinetics Templates

Pre-configured kinetics `.hh` files for each simulation scenario.

Each folder contains a matched pair of C++ header files:
- `defineKinetics.hh` — biotic (Monod) reaction rates
- `defineAbioticKinetics.hh` — abiotic reaction rates
- `README.md` — scenario description, parameters, validation criteria

**Both files must always exist** (the solver `#includes` them unconditionally).
Unused files are no-op stubs that compile but do nothing.

## Scenarios

| # | Folder | Type | Description |
|---|--------|------|-------------|
| 1 | `01_flow_only/` | Abiotic | Pure Navier-Stokes flow, no chemistry |
| 2 | `02_diffusion_only/` | Abiotic | Pure diffusion (Pe=0), no reactions |
| 3 | `03_tracer_transport/` | Abiotic | Flow + passive tracer, no reactions |
| 4 | `04_abiotic_reaction/` | Abiotic | First-order decay: A → Product |
| 5 | `05_abiotic_equilibrium/` | Abiotic | Carbonate equilibrium (no kinetic rxn) |
| 6 | `06_biotic_sessile/` | Biotic | Sessile biofilm (CA solver), 1 microbe |
| 7 | `07_biotic_planktonic/` | Biotic | Planktonic bacteria (LBM solver), 1 microbe |
| 8 | `08_biotic_sessile_planktonic/` | Biotic | Sessile + planktonic, 2 microbes |
| 9 | `09_coupled_biotic_abiotic/` | Coupled | Biofilm + abiotic decay simultaneously |

## How to Use

### Option A: Via CompLaB Studio GUI
1. **File > New Project** — select a template
2. The GUI auto-generates matching `.hh` files on export
3. Copy both `.hh` files to the solver source root (next to `CMakeLists.txt`)
4. Recompile: `cd build && cmake .. && make -j$(nproc)`

### Option B: Manual
1. Copy both `.hh` files from the desired scenario folder to the solver source root
2. Recompile the solver
3. Create/edit `CompLaB.xml` to match the scenario parameters

## When to Recompile

**Must recompile** when you change:
- Kinetics equations (`.hh` code)
- Template (switches `.hh` code)
- Number of substrates or microbes

**No recompile needed** for:
- Concentrations, boundary conditions, diffusion coefficients
- Domain dimensions (but regenerate geometry)
- Iteration count, output settings
- Fluid properties (delta_P, tau)
