# Scenario 9: Coupled Biotic + Abiotic Reactions

## Overview

This scenario couples a biotic process (biofilm consuming DOC via Monod kinetics) with an abiotic process (first-order decay of a metabolic byproduct) in a single simulation. The sessile biofilm consumes dissolved organic carbon (DOC) and produces a Byproduct. The Byproduct then undergoes abiotic first-order decay throughout the domain. This demonstrates CompLaB3D's ability to run biotic and abiotic reaction systems simultaneously.

## Reactions

**Biotic reaction -- Monod DOC consumption with Byproduct production:**

```
mu = mu_max * [DOC] / (Ks + [DOC])

dB/dt       = (mu - k_decay) * B               (biomass net growth)
dDOC/dt     = -mu * B / Y                      (DOC consumption)
dByproduct/dt = +mu * B / Y                    (Byproduct production, stoichiometric)
```

**Abiotic reaction -- First-order Byproduct decay:**

```
dByproduct/dt = -k_abiotic * [Byproduct]

k_abiotic = 1e-5 [1/s]
```

**Combined Byproduct rate:**

```
dByproduct/dt = (mu * B / Y) - k_abiotic * [Byproduct]
                ^^^^^^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^
                biotic source     abiotic sink
```

## Input Parameters

### Substrates

| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| `C0_DOC` | 0.1 | mol/L | Initial DOC concentration |
| `C0_Byproduct` | 0.0 | mol/L | Initial Byproduct concentration |
| `D_pore` (DOC) | 1e-9 | m2/s | DOC diffusion in pore space |
| `D_biofilm` (DOC) | 2e-10 | m2/s | DOC diffusion in biofilm |
| `D_pore` (Byproduct) | 1e-9 | m2/s | Byproduct diffusion in pore space |
| `D_biofilm` (Byproduct) | 2e-10 | m2/s | Byproduct diffusion in biofilm |

### Heterotroph (CA Solver, Sessile)

| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| `mu_max` | 0.05 | 1/s | Maximum specific growth rate |
| `Ks` | 1e-5 | mol/L | Half-saturation constant for DOC |
| `Y` | 0.4 | kg/mol | Yield coefficient |
| `k_decay` | 1e-7 | 1/s | Biomass decay rate |
| Material (core) | 3 | -- | Geometry mask for dense biofilm interior |
| Material (fringe) | 6 | -- | Geometry mask for active growth zone |
| Initial density | 99.0 | kg/m3 | Starting biomass in biofilm voxels |

### Abiotic Reaction

| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| `k_abiotic` | 1e-5 | 1/s | First-order decay rate for Byproduct |

### Flow and Numerics

| Parameter | Value | Units | Description |
|-----------|-------|-------|-------------|
| `delta_P` | 2e-3 | (lattice) | Pressure gradient |
| `tau` | 0.8 | (dimensionless) | LBM relaxation parameter |
| `dx` | 1e-6 | m | Voxel size (1 um) |

## Domain

- **Dimensions:** 30 x 15 x 15 voxels (NX x NY x NZ)
- **Geometry type:** Parallel plate channel with biofilm patches on wall surfaces
- **Voxel size:** dx = 1 um
- **Biofilm placement:** 1-2 patches of sessile biofilm on the solid walls
- **Material numbers:**
  - 0 = Solid wall
  - 1 = Bounce-back interface
  - 2 = Pore space
  - 3 = Microbe-1 Core (dense biofilm interior)
  - 6 = Microbe-1 Fringe (active growth zone)

## Boundary Conditions

| Species | Left (Inlet) | Right (Outlet) | Walls |
|---------|--------------|-----------------|-------|
| DOC | Dirichlet: C = 0.1 mol/L | Neumann: dC/dx = 0 | No flux |
| Byproduct | Dirichlet: C = 0.0 mol/L | Neumann: dC/dx = 0 | No flux |
| Biomass | N/A (CA solver) | N/A | Grows on walls |

**Flow:** Pressure-driven (delta_P = 2e-3) from left to right.

## Validation Criteria

A reviewer should check the following:

1. **DOC consumed by biofilm** -- DOC concentration should decrease near biofilm patches, with a gradient from bulk fluid toward the biofilm surface.
2. **Byproduct produced in biofilm regions** -- Byproduct concentration should be highest near biofilm patches where DOC is being consumed.
3. **Byproduct decays abiotically** -- Away from the biofilm (and everywhere in the domain), Byproduct should undergo first-order decay. Byproduct concentration should decrease with distance from the biofilm source.
4. **Steady-state balance** -- At steady state, the rate of Byproduct production by the biofilm should approximately balance the rate of abiotic decay plus advective/diffusive removal, resulting in a stable Byproduct concentration profile.
5. **Both reaction systems active** -- The simulation log or diagnostic output should confirm that both biotic (Monod) and abiotic (first-order) kinetics are being evaluated each time step.
6. **No negative concentrations** -- DOC and Byproduct must remain >= 0 everywhere.
7. **Biomass growth** -- Sessile biomass should grow where DOC is available and the biofilm should spread via CA rules.
8. **Byproduct starts at zero** -- At t=0, Byproduct should be 0.0 everywhere. It should only appear after the biofilm begins consuming DOC.

## Expected Runtime

Approximately **5 minutes** on a standard workstation.

## Files in This Folder

| File | Description |
|------|-------------|
| `README.md` | This file |
| `CompLaB.xml` | XML configuration (generated by GUI or provided as template) |
| `defineKinetics.hh` | Biotic kinetics C++ header (Monod growth, DOC consumption, Byproduct production) |
| `defineAbioticKinetics.hh` | Abiotic kinetics C++ header (first-order Byproduct decay) |
| `geometry.dat` | Domain geometry file (generated by Geometry Generator) |

## How to Use

### Using the GUI (CompLaB Studio)

1. **Create project:** Open CompLaB Studio. Go to **File > New Project** and select template **9 - Coupled Biotic-Abiotic**.
2. **Review parameters:** Verify the Domain and Fluid panels. In the **Chemistry** panel, confirm two substrates are defined: DOC (C0=0.1) and Byproduct (C0=0.0). In the **Microbiology** panel, confirm one CA sessile microbe with the Monod parameters listed above.
3. **Generate geometry:** Go to **Tools > Geometry Generator**. Select **SESSILE BIOFILM Generator** (option 2). Choose **Parallel Plates** as the medium type. Set dimensions to 30 x 15 x 15. Choose a single-species scenario (e.g., scenario 8 for random patches), set biofilm thickness to 2, and coverage to 0.5.
4. **Validate:** Click **Validate** in the Run panel. Fix any red errors before proceeding.
5. **Review kinetics code:** Go to **Tools > Kinetics Editor**. Verify that:
   - The **biotic** tab (`defineKinetics.hh`) contains Monod DOC consumption and Byproduct production terms.
   - The **abiotic** tab (`defineAbioticKinetics.hh`) contains the first-order decay term for Byproduct (`dByproduct/dt = -k * [Byproduct]`).
6. **Export and compile:** Export the project. Recompile the solver:
   ```bash
   cd build && cmake .. && make -j$(nproc)
   ```
7. **Run:** Click **Run** in the GUI, or from the terminal:
   ```bash
   ./complab
   ```
8. **Inspect output:** Open the VTK files in the `output/` folder with ParaView. Visualize both DOC and Byproduct concentration fields side by side. Confirm that DOC decreases near the biofilm while Byproduct increases there and decays away from it.

### Using the Command Line

1. Copy the kinetics files from this folder to the source root:
   ```bash
   cp kinetics/09_coupled_biotic_abiotic/defineKinetics.hh src/
   cp kinetics/09_coupled_biotic_abiotic/defineAbioticKinetics.hh src/
   ```
2. Recompile:
   ```bash
   cd build && cmake .. && make -j$(nproc)
   ```
3. Generate geometry using the geometry generator:
   ```bash
   cd tools
   python geometry_generator.py
   # Select option 2 (SESSILE BIOFILM Generator)
   # Parallel Plates, 30x15x15, 1 species, thickness=2, coverage=0.5
   ```
4. Run the simulation:
   ```bash
   ./complab ../kinetics/09_coupled_biotic_abiotic/CompLaB.xml
   ```
5. Visualize results in ParaView. Use two side-by-side views to compare DOC and Byproduct fields.

---

Meile Lab, University of Georgia
