# CompLaB3D User Tutorial
## Three-Dimensional Biogeochemical Reactive Transport Solver

**Version:** 2.0 (Biotic-Kinetic-Anderson-NR)

**Author:** Shahram Asgari
**Advisor:** Dr. Christof Meile
**Laboratory:** Meile Lab
**Institution:** University of Georgia (UGA)

---

# Table of Contents

1. [Introduction](#1-introduction)
2. [Code Architecture](#2-code-architecture)
3. [Installation and Requirements](#3-installation-and-requirements)
4. [Configuration Files](#4-configuration-files)
5. [Simulation Modes](#5-simulation-modes)
6. [Kinetics System](#6-kinetics-system)
7. [Equilibrium Chemistry Solver](#7-equilibrium-chemistry-solver)
8. [Validation and Diagnostics](#8-validation-and-diagnostics)
9. [Test Cases and Examples](#9-test-cases-and-examples)
10. [Output Files](#10-output-files)
11. [Troubleshooting](#11-troubleshooting)

---

# 1. Introduction

## 1.1 What is CompLaB3D?

CompLaB3D (Computational Laboratory for Biogeochemistry in 3D) is a sophisticated numerical simulation tool for modeling reactive transport processes in porous media. The code combines:

- **Lattice Boltzmann Method (LBM)** for fluid flow and solute transport
- **Monod kinetics** for microbial growth and substrate consumption
- **Equilibrium chemistry solver** for fast chemical reactions
- **Cellular Automata (CA)** for biofilm expansion and redistribution

## 1.2 Key Features

| Feature | Description |
|---------|-------------|
| **3D Simulation** | Full three-dimensional domain with arbitrary geometry |
| **Multi-species Transport** | Multiple substrates with different diffusion coefficients |
| **Biotic/Abiotic Modes** | Flexible simulation with or without microbial activity |
| **Kinetics Control** | Enable/disable kinetic reactions independently |
| **Equilibrium Chemistry** | Newton-Raphson solver for fast equilibrium reactions |
| **Biofilm Modeling** | Sessile (attached) and planktonic (free-floating) bacteria |
| **Validation Diagnostics** | Optional detailed per-iteration output for debugging |

## 1.3 Physical Processes Modeled

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PHYSICAL PROCESSES                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. FLUID FLOW (Navier-Stokes via LBM-D3Q19)                        │
│     ∂u/∂t + (u·∇)u = -∇P/ρ + ν∇²u                                   │
│                                                                      │
│  2. SOLUTE TRANSPORT (Advection-Diffusion via LBM-D3Q7)             │
│     ∂C/∂t + u·∇C = D∇²C + R                                         │
│                                                                      │
│  3. MICROBIAL KINETICS (Monod Model)                                │
│     μ = μ_max × S/(K_s + S)                                          │
│     dB/dt = μ × B - k_decay × B                                      │
│     dS/dt = -μ × B / Y                                               │
│                                                                      │
│  4. EQUILIBRIUM CHEMISTRY (Mass Action Law)                          │
│     K = ∏[products]^ν / ∏[reactants]^ν                              │
│                                                                      │
│  5. BIOFILM EXPANSION (Cellular Automata)                            │
│     When B > B_max: redistribute excess to neighbors                 │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 2. Code Architecture

## 2.1 File Structure

```
CompLaB3D/
├── src/
│   ├── complab.cpp                    # Main simulation program
│   ├── complab_functions.hh           # Helper functions and XML parsing
│   ├── complab3d_processors.hh        # LBM data processors (includes part1 & part2)
│   ├── complab3d_processors_part1.hh  # Kinetics and biomass processors
│   └── complab3d_processors_part2.hh  # Mask and dynamics update processors
├── defineKinetics.hh                  # Kinetics equations (biofilm version)
├── defineKinetics_planktonic.hh       # Kinetics equations (planktonic version)
├── CompLaB.xml                        # Main configuration file
├── CompLaB_planktonic.xml             # Planktonic configuration file
├── input/
│   └── geometry.dat                   # Porous medium geometry
├── output/                            # Simulation results
└── docs/
    └── CompLaB3D_User_Tutorial.md     # This document
```

## 2.2 Simulation Flow (10 Phases)

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    CompLaB3D SIMULATION FLOW                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  PHASE 1: Load XML Configuration                                         ║
║           └─ Parse CompLaB.xml                                           ║
║           └─ Validate all input parameters                               ║
║           └─ Set simulation modes (biotic/abiotic, kinetics, etc.)       ║
║                                                                          ║
║  PHASE 2: Geometry Setup                                                 ║
║           └─ Read geometry.dat file                                      ║
║           └─ Create mask, distance, and age lattices                     ║
║           └─ Define boundary conditions                                  ║
║                                                                          ║
║  PHASE 3: Navier-Stokes Flow Simulation                                  ║
║           └─ STEP 3.1: Initial pressure simulation → measure u₀          ║
║           └─ STEP 3.2: Calculate permeability k = (u₀ × ν × L) / ΔP₀    ║
║           └─ STEP 3.3: Calculate target velocity u_target = (Pe × D) / L ║
║           └─ STEP 3.4: Correct pressure ΔP_new = (u_target × ν × L) / k  ║
║           └─ STEP 3.5: Second NS simulation → achieve target velocity    ║
║           └─ STEP 3.6: Stability checks (Ma < 0.3, CFL < 1, τ > 0.5)    ║
║                                                                          ║
║  PHASE 4: Reactive Transport Lattice Setup                               ║
║           └─ Initialize substrate lattices                               ║
║           └─ Initialize biomass lattices (if biotic mode)                ║
║           └─ Setup delta lattices (dC, dB) for reactions                 ║
║                                                                          ║
║  PHASE 5: NS-ADE Velocity Coupling                                       ║
║           └─ Transfer velocity field from NS to ADE lattices             ║
║           └─ Stabilize ADE lattices (10,000 iterations)                  ║
║                                                                          ║
║  PHASE 6: Main Simulation Loop                                           ║
║           ┌─────────────────────────────────────────────────────────┐    ║
║           │  for iT = 0 to ade_max_iT:                              │    ║
║           │    STEP 6.1: Collision (LBM collision operator)         │    ║
║           │    STEP 6.2: Kinetics (if enable_kinetics=true)         │    ║
║           │              └─ run_kinetics processor                  │    ║
║           │              └─ update_rxnLattices processor            │    ║
║           │    STEP 6.3: Equilibrium (if useEquilibrium=true)       │    ║
║           │              └─ Newton-Raphson solver                   │    ║
║           │    STEP 6.4: Biomass expansion (CA/FD)                  │    ║
║           │              └─ push/pull excess biomass                │    ║
║           │    STEP 6.5: Flow field update (if biofilm changed)     │    ║
║           │    STEP 6.6: Streaming (LBM streaming step)             │    ║
║           │    STEP 6.7: Output (VTI/CHK files at intervals)        │    ║
║           └─────────────────────────────────────────────────────────┘    ║
║                                                                          ║
║  PHASE 7: Final Output Files                                             ║
║           └─ Write final VTI files (concentrations, biomass, velocity)   ║
║           └─ Write checkpoint files for restart                          ║
║                                                                          ║
║  PHASE 8: Calculate Moments and Statistics                               ║
║           └─ Compute M₀, M₁, M₂ (moment analysis)                       ║
║           └─ Calculate breakthrough curve metrics                        ║
║                                                                          ║
║  PHASE 9: Write Summary Files                                            ║
║           └─ Domain_properties.csv                                       ║
║           └─ Moments_summary.csv                                         ║
║                                                                          ║
║  PHASE 10: Finalize and Cleanup                                          ║
║           └─ Print final summary                                         ║
║           └─ Free allocated memory                                       ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
```

## 2.3 Data Flow Diagram

```
                    ┌──────────────────┐
                    │   CompLaB.xml    │
                    │ (Configuration)  │
                    └────────┬─────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │          complab_functions.hh          │
         │    (XML Parsing & Initialization)      │
         └───────────────────┬───────────────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ▼                   ▼                   ▼
   ┌───────────┐      ┌───────────┐      ┌───────────┐
   │  NS Flow  │      │ Substrate │      │  Biomass  │
   │  Lattice  │      │ Lattices  │      │ Lattices  │
   │  (D3Q19)  │      │  (D3Q7)   │      │  (D3Q7)   │
   └─────┬─────┘      └─────┬─────┘      └─────┬─────┘
         │                  │                  │
         │    ┌─────────────┴─────────────┐    │
         │    │                           │    │
         │    ▼                           ▼    │
         │  ┌───────────────────────────────┐  │
         │  │      defineKinetics.hh        │  │
         └─▶│   (Monod Growth Equations)    │◀─┘
            │   dB/dt, dC/dt calculations   │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │    Equilibrium Solver         │
            │   (Newton-Raphson Method)     │
            │   Fast chemical equilibria    │
            └───────────────┬───────────────┘
                            │
                            ▼
            ┌───────────────────────────────┐
            │      Output Files             │
            │  VTI (visualization)          │
            │  CHK (checkpoint/restart)     │
            │  CSV (analysis data)          │
            └───────────────────────────────┘
```

---

# 3. Installation and Requirements

## 3.1 Dependencies

| Dependency | Version | Description |
|------------|---------|-------------|
| **Palabos** | 2.0+ | Lattice Boltzmann library |
| **C++ Compiler** | C++11+ | GCC 7+ or Clang 5+ |
| **MPI** | OpenMPI 2+ | Parallel computing (optional) |
| **CMake** | 3.10+ | Build system |

## 3.2 Building the Code

```bash
# Navigate to the source directory
cd CompLaB3D/src

# Compile with MPI support
mpicxx -O3 -std=c++11 -I/path/to/palabos/src \
       complab.cpp -o complab3d \
       -L/path/to/palabos/lib -lplb

# Or use the provided Makefile
make
```

## 3.3 Running Simulations

```bash
# Single processor
./complab3d

# Multiple processors (MPI)
mpirun -np 4 ./complab3d
```

---

# 4. Configuration Files

## 4.1 XML Configuration Structure

The main configuration file `CompLaB.xml` contains all simulation parameters organized in sections:

```xml
<?xml version="1.0" ?>
<parameters>
    <path>...</path>
    <simulation_mode>...</simulation_mode>
    <LB_numerics>...</LB_numerics>
    <chemistry>...</chemistry>
    <microbiology>...</microbiology>
    <equilibrium>...</equilibrium>
    <IO>...</IO>
</parameters>
```

## 4.2 Path Configuration

```xml
<path>
    <src_path>src</src_path>
    <input_path>input</input_path>
    <output_path>output</output_path>
</path>
```

## 4.3 Simulation Mode Control

```xml
<!-- ════════════════════════════════════════════════════════════════════════════
     SIMULATION MODE CONTROL
     ════════════════════════════════════════════════════════════════════════════
     biotic_mode: true/false or biotic/abiotic
       - true/biotic: Full simulation with microbes, biomass, and kinetics
       - false/abiotic: Transport only, no microbes (skips microbiology section)

     enable_kinetics: true/false
       - true: Kinetics reactions enabled (Monod growth, etc.)
       - false: Kinetics disabled, only equilibrium chemistry runs
       - Note: Automatically disabled when biotic_mode=false

     enable_validation_diagnostics: true/false
       - true: Detailed per-iteration output showing data flow verification:
               * Collision, kinetics, equilibrium steps
               * Sample concentrations at domain center
               * Mass balance checks
               * dC and dB values at sample points
       - false: Normal operation (no extra diagnostic output)
       - Note: Adds computational overhead, use for debugging only!
-->
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
    <enable_validation_diagnostics>false</enable_validation_diagnostics>
</simulation_mode>
```

## 4.4 LB Numerics

```xml
<LB_numerics>
    <domain>
        <nx>50</nx>                           <!-- Domain size in x (lattice units) -->
        <ny>30</ny>                           <!-- Domain size in y -->
        <nz>30</nz>                           <!-- Domain size in z -->
        <dx>1.0</dx>                          <!-- Grid spacing -->
        <unit>um</unit>                       <!-- Unit: m, mm, or um -->
        <characteristic_length>30</characteristic_length>  <!-- For Pe calculation -->
        <filename>geometry.dat</filename>     <!-- Geometry file -->
        <material_numbers>
            <pore>2</pore>                    <!-- Pore space tag -->
            <solid>0</solid>                  <!-- Solid (no dynamics) tag -->
            <bounce_back>1</bounce_back>      <!-- Bounce-back boundary tag -->
            <microbe0>3 4 5</microbe0>        <!-- Biomass material numbers -->
        </material_numbers>
    </domain>
    <delta_P>2.0e-3</delta_P>                <!-- Pressure gradient -->
    <Peclet>1.0</Peclet>                      <!-- Target Péclet number -->
    <tau>0.8</tau>                            <!-- LBM relaxation time -->
    <track_performance>false</track_performance>
    <iteration>
        <ns_max_iT1>100000</ns_max_iT1>       <!-- Max NS iterations (phase 1) -->
        <ns_max_iT2>100000</ns_max_iT2>       <!-- Max NS iterations (phase 2) -->
        <ns_converge_iT1>1e-8</ns_converge_iT1>
        <ns_converge_iT2>1e-6</ns_converge_iT2>
        <ade_max_iT>50000</ade_max_iT>        <!-- Max ADE iterations -->
        <ade_converge_iT>1e-8</ade_converge_iT>
        <ns_update_interval>1</ns_update_interval>
        <ade_update_interval>1</ade_update_interval>
    </iteration>
</LB_numerics>
```

## 4.5 Chemistry Configuration

```xml
<chemistry>
    <number_of_substrates>5</number_of_substrates>

    <substrate0>
        <name_of_substrates>DOC</name_of_substrates>
        <initial_concentration>0.1</initial_concentration>  <!-- mol/L -->
        <substrate_diffusion_coefficients>
            <in_pore>1.0e-9</in_pore>                       <!-- m²/s -->
            <in_biofilm>2.0e-10</in_biofilm>                <!-- Reduced in biofilm -->
        </substrate_diffusion_coefficients>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <right_boundary_type>Neumann</right_boundary_type>
        <left_boundary_condition>0.1</left_boundary_condition>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate0>

    <!-- Additional substrates: substrate1, substrate2, etc. -->
</chemistry>
```

## 4.6 Microbiology Configuration

```xml
<microbiology>
    <number_of_microbes>1</number_of_microbes>
    <maximum_biomass_density>200.0</maximum_biomass_density>  <!-- kg/m³ -->
    <thrd_biofilm_fraction>0.01</thrd_biofilm_fraction>
    <CA_method>fraction</CA_method>                           <!-- or 'half' -->

    <microbe0>
        <name_of_microbes>Heterotroph</name_of_microbes>
        <solver_type>CA</solver_type>                         <!-- CA, FD, or LBM -->
        <reaction_type>kinetics</reaction_type>               <!-- kinetics or none -->
        <initial_densities>100.0</initial_densities>          <!-- kg/m³ -->
        <decay_coefficient>1e-7</decay_coefficient>           <!-- 1/s -->
        <half_saturation_constants>1e-5 0 0 0 0</half_saturation_constants>  <!-- mol/L -->
        <maximum_uptake_flux>0.5 0 0 0 0</maximum_uptake_flux>               <!-- 1/s -->
        <biomass_diffusion_coefficients>
            <in_pore>1e-12</in_pore>
            <in_biofilm>1e-13</in_biofilm>
        </biomass_diffusion_coefficients>
        <viscosity_ratio_in_biofilm>100</viscosity_ratio_in_biofilm>
        <left_boundary_type>Neumann</left_boundary_type>
        <right_boundary_type>Neumann</right_boundary_type>
        <left_boundary_condition>0.0</left_boundary_condition>
        <right_boundary_condition>0.0</right_boundary_condition>
    </microbe0>
</microbiology>
```

## 4.7 Equilibrium Chemistry Configuration

```xml
<!-- ════════════════════════════════════════════════════════════════════════════
     EQUILIBRIUM CHEMISTRY (Newton-Raphson Solver)
     ════════════════════════════════════════════════════════════════════════════
     The equilibrium solver handles fast chemical reactions that reach equilibrium
     much faster than the transport timescale.

     Example: Carbonate system
       H₂CO₃ ⇌ HCO₃⁻ + H⁺       K₁ = 10^(-6.35)
       HCO₃⁻ ⇌ CO₃²⁻ + H⁺       K₂ = 10^(-10.33)

     Stoichiometry matrix format:
       Each row = one species
       Each column = one component (HCO3, H)
       Values = stoichiometric coefficients
-->
<equilibrium>
    <enabled>true</enabled>
    <components>HCO3 H</components>

    <stoichiometry>
        <!-- Species: DOC (not in equilibrium) -->
        <species0>0.0 0.0</species0>
        <!-- Species: CO2 = H2CO3 (in equilibrium) -->
        <species1>1.0 1.0</species1>
        <!-- Species: HCO3- (component) -->
        <species2>1.0 0.0</species2>
        <!-- Species: CO3-- -->
        <species3>1.0 -1.0</species3>
        <!-- Species: H+ (component) -->
        <species4>0.0 1.0</species4>
    </stoichiometry>

    <logK>
        <species0>0.0</species0>      <!-- DOC: not in equilibrium -->
        <species1>6.35</species1>     <!-- H2CO3: logK = 6.35 -->
        <species2>0.0</species2>      <!-- HCO3-: component, logK = 0 -->
        <species3>-10.33</species3>   <!-- CO3--: logK = -10.33 -->
        <species4>0.0</species4>      <!-- H+: component, logK = 0 -->
    </logK>
</equilibrium>
```

## 4.8 I/O Configuration

```xml
<IO>
    <read_NS_file>false</read_NS_file>
    <read_ADE_file>false</read_ADE_file>
    <ns_filename>nsLattice</ns_filename>
    <subs_filename>subsLattice</subs_filename>
    <bio_filename>bioLattice</bio_filename>
    <mask_filename>maskLattice</mask_filename>
    <save_VTK_interval>1000</save_VTK_interval>   <!-- Iterations between VTI saves -->
    <save_CHK_interval>100000</save_CHK_interval> <!-- Iterations between checkpoints -->
</IO>
```

---

# 5. Simulation Modes

## 5.1 Mode Combinations

CompLaB3D supports four main simulation configurations:

| biotic_mode | enable_kinetics | useEquilibrium | Description |
|-------------|-----------------|----------------|-------------|
| `false` | `false` (auto) | `false` | Pure abiotic transport |
| `false` | `false` (auto) | `true` | Abiotic with equilibrium chemistry |
| `true` | `false` | `true` | Biotic without kinetics (equilibrium only) |
| `true` | `true` | `true` | **Full simulation** (recommended) |
| `true` | `true` | `false` | Biotic with kinetics, no equilibrium |

## 5.2 Mode Flowchart

```
                    ┌──────────────────────┐
                    │     biotic_mode?     │
                    └──────────┬───────────┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ▼                                 ▼
        ┌──────────┐                      ┌──────────┐
        │  FALSE   │                      │   TRUE   │
        │ (Abiotic)│                      │ (Biotic) │
        └────┬─────┘                      └────┬─────┘
             │                                 │
             │ enable_kinetics = false         │
             │ num_of_microbes = 0             │
             │ kns_count = 0                   │
             │                                 │
             ▼                                 ▼
    ┌─────────────────┐              ┌─────────────────┐
    │ useEquilibrium? │              │ enable_kinetics?│
    └────────┬────────┘              └────────┬────────┘
             │                                │
      ┌──────┴──────┐                  ┌──────┴──────┐
      │             │                  │             │
      ▼             ▼                  ▼             ▼
  ┌───────┐   ┌───────────┐      ┌──────────┐ ┌──────────┐
  │ FALSE │   │   TRUE    │      │  FALSE   │ │   TRUE   │
  └───┬───┘   └─────┬─────┘      └────┬─────┘ └────┬─────┘
      │             │                 │            │
      ▼             ▼                 ▼            ▼
  ┌───────────┐ ┌───────────┐   ┌──────────┐ ┌──────────────┐
  │ Transport │ │ Transport │   │ Equilib. │ │   Kinetics   │
  │   Only    │ │ + Equil.  │   │   Only   │ │ + Equilib.   │
  └───────────┘ └───────────┘   └──────────┘ └──────────────┘
```

---

# 6. Kinetics System

## 6.1 Monod Kinetics Equations

The kinetics system implements Monod-type microbial growth:

### Growth Rate
```
μ = μ_max × (S / (K_s + S))

where:
  μ      = specific growth rate (1/s)
  μ_max  = maximum specific growth rate (1/s)
  S      = substrate concentration (mol/L)
  K_s    = half-saturation constant (mol/L)
```

### Biomass Change
```
dB/dt = μ × B - k_decay × B

where:
  B       = biomass concentration (kg/m³)
  k_decay = decay coefficient (1/s)
```

### Substrate Consumption
```
dS/dt = -μ × B / Y

where:
  Y = yield coefficient (kg biomass / mol substrate)
```

## 6.2 defineKinetics.hh Structure

The kinetics file defines the reaction equations:

```cpp
/* ============================================================================
 * defineKinetics.hh - Kinetics Equations for CompLaB3D
 * ============================================================================
 * This file contains user-defined kinetic rate expressions.
 *
 * REQUIRED FUNCTION:
 *   defineRxnKinetics() - Called every iteration for each voxel
 *
 * INPUTS:
 *   C[]  - Substrate concentrations (mol/L)
 *   B[]  - Biomass concentrations (kg/m³)
 *   dt   - Time step (s)
 *   Kc   - Half-saturation constants (mol/L)
 *   mu   - Maximum growth rates (1/s)
 *
 * OUTPUTS:
 *   dC[] - Change in substrate concentration (mol/L/iteration)
 *   dB[] - Change in biomass concentration (kg/m³/iteration)
 * ============================================================================
 */

#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

// ============================================================================
// KINETICS PARAMETERS
// ============================================================================
namespace KineticsParams {
    // Monod parameters
    const double mu_max = 0.5;       // Maximum specific growth rate (1/h converted)
    const double k_decay = 1e-7;     // Decay coefficient (1/s)
    const double Ks = 1e-5;          // Half-saturation constant (mol/L)
    const double Y = 0.4;            // Yield coefficient (kg/mol)
}

// ============================================================================
// VALIDATION FUNCTIONS
// ============================================================================
namespace KineticsValidation {
    // Validate parameters at startup
    inline void validateParameters() {
        using namespace KineticsParams;
        std::cout << "╔══════════════════════════════════════════════════════════════════╗\n";
        std::cout << "║              KINETICS PARAMETER VALIDATION                        ║\n";
        std::cout << "╠══════════════════════════════════════════════════════════════════╣\n";
        std::cout << "║  mu_max  = " << mu_max << " /s (max growth rate)\n";
        std::cout << "║  k_decay = " << k_decay << " /s (decay coefficient)\n";
        std::cout << "║  Ks      = " << Ks << " mol/L (half-saturation)\n";
        std::cout << "║  Y       = " << Y << " kg/mol (yield)\n";
        std::cout << "╚══════════════════════════════════════════════════════════════════╝\n";
    }
}

// ============================================================================
// DIAGNOSTICS FUNCTIONS
// ============================================================================
namespace KineticsDiagnostics {
    // Detailed per-iteration output
    inline void printIterationSummary(long iT, double dt,
                                       const std::vector<double>& C,
                                       const std::vector<double>& B,
                                       const std::vector<double>& dC,
                                       const std::vector<double>& dB) {
        using namespace KineticsParams;

        std::cout << "┌─────────────────────────────────────────────────────────────────┐\n";
        std::cout << "│ KINETICS ITERATION " << iT << " (dt = " << dt << " s)\n";
        std::cout << "├─────────────────────────────────────────────────────────────────┤\n";

        // Substrate status
        double S = C[0];  // Assuming DOC is substrate 0
        double mu = mu_max * S / (Ks + S);

        std::cout << "│ SUBSTRATES:\n";
        std::cout << "│   DOC: " << S << " mol/L\n";
        std::cout << "│   Growth rate μ = " << mu << " /s\n";

        // Biomass status
        std::cout << "│ BIOMASS:\n";
        for (size_t i = 0; i < B.size(); ++i) {
            std::cout << "│   B[" << i << "] = " << B[i] << " kg/m³";
            std::cout << " | dB = " << dB[i] << " kg/m³/iter\n";
        }

        std::cout << "└─────────────────────────────────────────────────────────────────┘\n";
    }
}

// ============================================================================
// MAIN KINETICS FUNCTION
// ============================================================================
inline void defineRxnKinetics(
    std::vector<double>& C,      // Substrate concentrations (in/out)
    std::vector<double>& B,      // Biomass concentrations (in)
    std::vector<double>& dC,     // Delta concentration (out)
    std::vector<double>& dB,     // Delta biomass (out)
    double dt,                    // Time step
    const std::vector<std::vector<double>>& Kc,  // Half-saturation constants
    const std::vector<double>& mu_vec)           // Growth rates
{
    using namespace KineticsParams;

    // Initialize deltas to zero
    for (size_t i = 0; i < dC.size(); ++i) dC[i] = 0.0;
    for (size_t i = 0; i < dB.size(); ++i) dB[i] = 0.0;

    // Skip if no biomass
    double totalB = 0.0;
    for (size_t i = 0; i < B.size(); ++i) totalB += B[i];
    if (totalB < 1e-14) return;

    // Get substrate concentration (DOC)
    double S = std::max(0.0, C[0]);

    // Calculate Monod growth rate
    double mu = mu_max * S / (Ks + S);

    // For each microbe
    for (size_t m = 0; m < B.size(); ++m) {
        if (B[m] < 1e-14) continue;

        // Net growth = growth - decay
        double growth = mu * B[m];
        double decay = k_decay * B[m];
        dB[m] = (growth - decay) * dt;

        // Substrate consumption
        dC[0] -= (growth / Y) * dt;
    }

    // Validate outputs (catch NaN/Inf)
    for (size_t i = 0; i < dC.size(); ++i) {
        if (std::isnan(dC[i]) || std::isinf(dC[i])) {
            dC[i] = 0.0;
        }
    }
    for (size_t i = 0; i < dB.size(); ++i) {
        if (std::isnan(dB[i]) || std::isinf(dB[i])) {
            dB[i] = 0.0;
        }
    }
}

#endif // DEFINE_KINETICS_HH
```

## 6.3 Kinetics Statistics (KineticsStats)

The code tracks kinetics statistics for debugging:

```cpp
namespace KineticsStats {
    static long cells_with_biomass = 0;
    static long cells_growing = 0;
    static double sum_dB = 0.0;
    static double max_B = 0.0;
    static double max_dB = 0.0;
    static double min_DOC = 1e10;

    inline void accumulate(double B, double dB, double DOC) {
        if (B > 1e-10) {
            cells_with_biomass++;
            max_B = std::max(max_B, B);
            min_DOC = std::min(min_DOC, DOC);
            if (dB > 0) {
                cells_growing++;
                sum_dB += dB;
                max_dB = std::max(max_dB, dB);
            }
        }
    }

    inline void resetIteration() {
        cells_with_biomass = 0;
        cells_growing = 0;
        sum_dB = 0.0;
        max_B = 0.0;
        max_dB = 0.0;
        min_DOC = 1e10;
    }
}
```

---

# 7. Equilibrium Chemistry Solver

## 7.1 Mathematical Foundation

The equilibrium solver uses the **Newton-Raphson method** to solve the mass action equations:

### Mass Action Law
For a reaction: `aA + bB ⇌ cC + dD`

```
K = [C]^c × [D]^d / ([A]^a × [B]^b)
```

### Component Mass Balance
```
T_j = Σ_i (ν_ij × C_i)

where:
  T_j   = Total concentration of component j
  ν_ij  = Stoichiometric coefficient of species i for component j
  C_i   = Concentration of species i
```

### Species Concentration from Components
```
C_i = K_i × Π_j (X_j)^ν_ij

where:
  X_j = Free component concentration
  K_i = Equilibrium constant (10^logK)
```

## 7.2 Newton-Raphson Iteration

The solver iteratively refines component concentrations:

```
X_new = X_old - J^(-1) × F(X_old)

where:
  F(X) = T_calc(X) - T_total  (residual)
  J    = ∂F/∂X (Jacobian matrix)
```

## 7.3 Carbonate System Example

```
┌─────────────────────────────────────────────────────────────────────┐
│           CARBONATE EQUILIBRIUM SYSTEM                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Reactions:                                                          │
│    H₂CO₃ ⇌ HCO₃⁻ + H⁺        K₁ = 10^(-6.35)                        │
│    HCO₃⁻ ⇌ CO₃²⁻ + H⁺        K₂ = 10^(-10.33)                       │
│                                                                      │
│  Components: HCO₃⁻, H⁺                                               │
│                                                                      │
│  Stoichiometry Matrix:                                               │
│                    HCO₃   H                                          │
│    H₂CO₃    [       1     1  ]  logK = 6.35                         │
│    HCO₃⁻    [       1     0  ]  logK = 0 (component)                │
│    CO₃²⁻   [       1    -1  ]  logK = -10.33                        │
│    H⁺       [       0     1  ]  logK = 0 (component)                │
│                                                                      │
│  Species concentrations:                                             │
│    [H₂CO₃] = K₁ × [HCO₃⁻] × [H⁺]                                   │
│    [HCO₃⁻] = [HCO₃⁻]  (component)                                   │
│    [CO₃²⁻] = K₂ × [HCO₃⁻] / [H⁺]                                   │
│    [H⁺]    = [H⁺]  (component)                                      │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

# 8. Validation and Diagnostics

## 8.1 Validation Diagnostics Option

Enable detailed per-iteration output for debugging:

```xml
<simulation_mode>
    <enable_validation_diagnostics>true</enable_validation_diagnostics>
</simulation_mode>
```

### Output Example

```
┌─────────────────────────────────────────────────────────────────────────┐
│ VALIDATION DIAGNOSTICS - Iteration 100                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ Time: 1.2345e-03 s
├─────────────────────────────────────────────────────────────────────────┤
│ STEP 6.1 [COLLISION]: LBM collision completed                           │
│ STEP 6.2 [KINETICS]: ACTIVE - 1 reaction(s)
│   DOC @center: C=9.9500e-02, dC=-5.1234e-06
│   CO2 @center: C=1.0500e-05, dC=2.5617e-06
│   Biomass @center: B=1.2000e+02, dB=3.4567e-03
│ STEP 6.3 [EQUILIBRIUM]: ACTIVE
│   DOC: min=9.9000e-02, max=1.0000e-01
│   CO2: min=1.0000e-05, max=1.1000e-05
├─────────────────────────────────────────────────────────────────────────┤
│ MASS BALANCE CHECK:
│   DOC total: 4.5000e+03
│   CO2 total: 4.7250e+01
│   Total biomass: 5.4000e+05
└─────────────────────────────────────────────────────────────────────────┘
```

## 8.2 Built-in Validation Checks

The code includes automatic validation:

| Check | Description | Action |
|-------|-------------|--------|
| **NaN Detection** | Checks for NaN in concentrations | Stops simulation with error |
| **Negative Concentration** | Flags negative values | Prints warning |
| **Biomass > Bmax** | Checks if B exceeds maximum | Triggers CA redistribution |
| **Stability (Ma, CFL)** | Checks LBM stability | Stops if Ma > 1.0 |

---

# 9. Test Cases and Examples

## 9.1 Test Case 1: Pure Abiotic Transport

### Description
Simulates conservative tracer transport without any reactions. Use this to verify flow field and transport without chemistry.

### Configuration

**CompLaB.xml:**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <src_path>src</src_path>
        <input_path>input</input_path>
        <output_path>output_abiotic_transport</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>false</biotic_mode>
        <enable_kinetics>false</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx>
            <ny>30</ny>
            <nz>30</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>2.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ns_max_iT1>100000</ns_max_iT1>
            <ns_max_iT2>100000</ns_max_iT2>
            <ade_max_iT>50000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>1</number_of_substrates>
        <substrate0>
            <name_of_substrates>Tracer</name_of_substrates>
            <initial_concentration>0.0</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>1.0e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>
    </chemistry>

    <equilibrium>
        <enabled>false</enabled>
    </equilibrium>

    <IO>
        <save_VTK_interval>1000</save_VTK_interval>
        <save_CHK_interval>100000</save_CHK_interval>
    </IO>
</parameters>
```

**defineKinetics.hh:** (Not used in abiotic mode, but must exist)
```cpp
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

// Empty kinetics for abiotic mode
inline void defineRxnKinetics(
    std::vector<double>& C,
    std::vector<double>& B,
    std::vector<double>& dC,
    std::vector<double>& dB,
    double dt,
    const std::vector<std::vector<double>>& Kc,
    const std::vector<double>& mu_vec)
{
    // No reactions
    for (size_t i = 0; i < dC.size(); ++i) dC[i] = 0.0;
    for (size_t i = 0; i < dB.size(); ++i) dB[i] = 0.0;
}

#endif
```

### Expected Results
- Tracer breakthrough curve following advection-dispersion equation
- No change in total mass (conservative transport)
- Pe_achieved ≈ Pe_target

---

## 9.2 Test Case 2: Abiotic with Equilibrium Chemistry

### Description
Simulates transport with carbonate equilibrium chemistry (no microbial activity).

### Reactions
```
CO₂(aq) + H₂O ⇌ H₂CO₃ ⇌ HCO₃⁻ + H⁺    K₁ = 10^(-6.35)
HCO₃⁻ ⇌ CO₃²⁻ + H⁺                    K₂ = 10^(-10.33)
```

### Configuration

**CompLaB.xml:**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_abiotic_equilibrium</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>false</biotic_mode>
        <enable_kinetics>false</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx>
            <ny>30</ny>
            <nz>30</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>2.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>50000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>4</number_of_substrates>

        <substrate0>
            <name_of_substrates>CO2</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.9e-9</in_pore>
                <in_biofilm>1.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-4</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>

        <substrate1>
            <name_of_substrates>HCO3</name_of_substrates>
            <initial_concentration>2.0e-3</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.2e-9</in_pore>
                <in_biofilm>1.2e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>2.0e-3</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate1>

        <substrate2>
            <name_of_substrates>CO3</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>0.9e-9</in_pore>
                <in_biofilm>0.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate2>

        <substrate3>
            <name_of_substrates>H</name_of_substrates>
            <initial_concentration>1.0e-7</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>9.3e-9</in_pore>
                <in_biofilm>9.3e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-7</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate3>
    </chemistry>

    <equilibrium>
        <enabled>true</enabled>
        <components>HCO3 H</components>
        <stoichiometry>
            <species0>1.0 1.0</species0>   <!-- CO2 = H2CO3 -->
            <species1>1.0 0.0</species1>   <!-- HCO3- -->
            <species2>1.0 -1.0</species2>  <!-- CO3-- -->
            <species3>0.0 1.0</species3>   <!-- H+ -->
        </stoichiometry>
        <logK>
            <species0>6.35</species0>
            <species1>0.0</species1>
            <species2>-10.33</species2>
            <species3>0.0</species3>
        </logK>
    </equilibrium>

    <IO>
        <save_VTK_interval>1000</save_VTK_interval>
    </IO>
</parameters>
```

### Expected Results
- Carbonate species maintain equilibrium as they transport
- pH (related to H⁺) varies spatially based on CO₂ injection
- Total inorganic carbon (TIC = CO₂ + HCO₃⁻ + CO₃²⁻) is conserved

---

## 9.3 Test Case 3: Biotic with Kinetics (No Equilibrium)

### Description
Simulates microbial DOC degradation with Monod kinetics but without equilibrium chemistry.

### Reactions
```
DOC + Microbe → CO₂ + Biomass

Kinetics:
  μ = μ_max × DOC / (K_s + DOC)
  dB/dt = μ × B - k_decay × B
  dDOC/dt = -μ × B / Y
  dCO2/dt = +μ × B / Y  (stoichiometric production)
```

### Configuration

**CompLaB.xml:**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_biotic_kinetics</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx>
            <ny>30</ny>
            <nz>30</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
                <microbe0>3</microbe0>
            </material_numbers>
        </domain>
        <delta_P>2.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>100000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>2</number_of_substrates>

        <substrate0>
            <name_of_substrates>DOC</name_of_substrates>
            <initial_concentration>0.1</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>2.0e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>0.1</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>

        <substrate1>
            <name_of_substrates>CO2</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.9e-9</in_pore>
                <in_biofilm>1.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate1>
    </chemistry>

    <microbiology>
        <number_of_microbes>1</number_of_microbes>
        <maximum_biomass_density>200.0</maximum_biomass_density>
        <thrd_biofilm_fraction>0.01</thrd_biofilm_fraction>
        <CA_method>fraction</CA_method>

        <microbe0>
            <name_of_microbes>Heterotroph</name_of_microbes>
            <solver_type>CA</solver_type>
            <reaction_type>kinetics</reaction_type>
            <initial_densities>100.0</initial_densities>
            <decay_coefficient>1e-7</decay_coefficient>
            <half_saturation_constants>1e-5 0.0</half_saturation_constants>
            <maximum_uptake_flux>0.5 0.0</maximum_uptake_flux>
            <biomass_diffusion_coefficients>
                <in_pore>1e-12</in_pore>
                <in_biofilm>1e-13</in_biofilm>
            </biomass_diffusion_coefficients>
            <viscosity_ratio_in_biofilm>100</viscosity_ratio_in_biofilm>
            <left_boundary_type>Neumann</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>0.0</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </microbe0>
    </microbiology>

    <equilibrium>
        <enabled>false</enabled>
    </equilibrium>

    <IO>
        <save_VTK_interval>5000</save_VTK_interval>
    </IO>
</parameters>
```

**defineKinetics.hh:**
```cpp
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

// ============================================================================
// KINETICS PARAMETERS - DOC degradation with CO2 production
// ============================================================================
namespace KineticsParams {
    const double mu_max = 5.787e-6;   // 0.5 /hr in /s
    const double k_decay = 1e-7;      // Decay coefficient (1/s)
    const double Ks = 1e-5;           // Half-saturation constant (mol/L)
    const double Y = 0.4;             // Yield coefficient (kg biomass / mol DOC)
}

// ============================================================================
// MAIN KINETICS FUNCTION
// ============================================================================
inline void defineRxnKinetics(
    std::vector<double>& C,      // [DOC, CO2]
    std::vector<double>& B,      // [Heterotroph]
    std::vector<double>& dC,     // [dDOC, dCO2]
    std::vector<double>& dB,     // [dHeterotroph]
    double dt,
    const std::vector<std::vector<double>>& Kc,
    const std::vector<double>& mu_vec)
{
    using namespace KineticsParams;

    // Initialize deltas
    for (size_t i = 0; i < dC.size(); ++i) dC[i] = 0.0;
    for (size_t i = 0; i < dB.size(); ++i) dB[i] = 0.0;

    // Skip if no biomass
    if (B[0] < 1e-14) return;

    // Get DOC concentration
    double DOC = std::max(0.0, C[0]);

    // Calculate Monod growth rate
    // μ = μ_max × S / (K_s + S)
    double mu = mu_max * DOC / (Ks + DOC);

    // Biomass change: dB/dt = μ × B - k_decay × B
    double growth = mu * B[0];
    double decay = k_decay * B[0];
    dB[0] = (growth - decay) * dt;

    // DOC consumption: dDOC/dt = -μ × B / Y
    dC[0] = -(growth / Y) * dt;

    // CO2 production: dCO2/dt = +μ × B / Y (stoichiometric)
    // Assuming 1:1 molar ratio DOC → CO2
    dC[1] = +(growth / Y) * dt;

    // Validate outputs
    for (size_t i = 0; i < dC.size(); ++i) {
        if (std::isnan(dC[i]) || std::isinf(dC[i])) dC[i] = 0.0;
    }
    if (std::isnan(dB[0]) || std::isinf(dB[0])) dB[0] = 0.0;
}

#endif
```

### Expected Results
- Biomass grows where DOC is available
- DOC concentration decreases near biofilm
- CO₂ concentration increases proportionally
- Biofilm expands via CA when B > B_max

---

## 9.4 Test Case 4: Full Simulation (Biotic + Kinetics + Equilibrium)

### Description
Complete simulation with microbial DOC degradation coupled to carbonate equilibrium chemistry.

### Reactions

**Kinetics (slow):**
```
DOC + O₂ → CO₂(aq) + Biomass

μ = μ_max × DOC/(K_DOC + DOC) × O₂/(K_O2 + O₂)
dB/dt = μ × B - k_decay × B
dDOC/dt = -μ × B / Y_DOC
dO₂/dt = -μ × B / Y_O2
dCO₂/dt = +μ × B / Y_CO2
```

**Equilibrium (fast):**
```
CO₂(aq) + H₂O ⇌ H₂CO₃ ⇌ HCO₃⁻ + H⁺
HCO₃⁻ ⇌ CO₃²⁻ + H⁺
```

### Configuration

**CompLaB.xml:**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_full_simulation</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx>
            <ny>30</ny>
            <nz>30</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
                <microbe0>3</microbe0>
            </material_numbers>
        </domain>
        <delta_P>2.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>100000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>6</number_of_substrates>

        <substrate0>
            <name_of_substrates>DOC</name_of_substrates>
            <initial_concentration>0.1</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>2.0e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>0.1</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>

        <substrate1>
            <name_of_substrates>O2</name_of_substrates>
            <initial_concentration>2.5e-4</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>2.1e-9</in_pore>
                <in_biofilm>2.1e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>2.5e-4</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate1>

        <substrate2>
            <name_of_substrates>CO2</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.9e-9</in_pore>
                <in_biofilm>1.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate2>

        <substrate3>
            <name_of_substrates>HCO3</name_of_substrates>
            <initial_concentration>2.0e-3</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.2e-9</in_pore>
                <in_biofilm>1.2e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>2.0e-3</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate3>

        <substrate4>
            <name_of_substrates>CO3</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>0.9e-9</in_pore>
                <in_biofilm>0.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate4>

        <substrate5>
            <name_of_substrates>H</name_of_substrates>
            <initial_concentration>1.0e-7</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>9.3e-9</in_pore>
                <in_biofilm>9.3e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-7</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate5>
    </chemistry>

    <microbiology>
        <number_of_microbes>1</number_of_microbes>
        <maximum_biomass_density>200.0</maximum_biomass_density>
        <thrd_biofilm_fraction>0.01</thrd_biofilm_fraction>
        <CA_method>fraction</CA_method>

        <microbe0>
            <name_of_microbes>Heterotroph</name_of_microbes>
            <solver_type>CA</solver_type>
            <reaction_type>kinetics</reaction_type>
            <initial_densities>100.0</initial_densities>
            <decay_coefficient>1e-7</decay_coefficient>
            <half_saturation_constants>1e-5 1e-5 0 0 0 0</half_saturation_constants>
            <maximum_uptake_flux>0.5 0 0 0 0 0</maximum_uptake_flux>
            <biomass_diffusion_coefficients>
                <in_pore>1e-12</in_pore>
                <in_biofilm>1e-13</in_biofilm>
            </biomass_diffusion_coefficients>
            <viscosity_ratio_in_biofilm>100</viscosity_ratio_in_biofilm>
            <left_boundary_type>Neumann</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
        </microbe0>
    </microbiology>

    <equilibrium>
        <enabled>true</enabled>
        <components>HCO3 H</components>
        <stoichiometry>
            <species0>0.0 0.0</species0>   <!-- DOC: not in equilibrium -->
            <species1>0.0 0.0</species1>   <!-- O2: not in equilibrium -->
            <species2>1.0 1.0</species2>   <!-- CO2 = H2CO3 -->
            <species3>1.0 0.0</species3>   <!-- HCO3- -->
            <species4>1.0 -1.0</species4>  <!-- CO3-- -->
            <species5>0.0 1.0</species5>   <!-- H+ -->
        </stoichiometry>
        <logK>
            <species0>0.0</species0>
            <species1>0.0</species1>
            <species2>6.35</species2>
            <species3>0.0</species3>
            <species4>-10.33</species4>
            <species5>0.0</species5>
        </logK>
    </equilibrium>

    <IO>
        <save_VTK_interval>5000</save_VTK_interval>
    </IO>
</parameters>
```

**defineKinetics.hh:**
```cpp
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

#include <vector>
#include <cmath>
#include <algorithm>

// ============================================================================
// KINETICS PARAMETERS - Dual Monod (DOC + O2 limitation)
// ============================================================================
namespace KineticsParams {
    const double mu_max = 5.787e-6;   // 0.5 /hr in /s
    const double k_decay = 1e-7;      // Decay coefficient (1/s)
    const double Ks_DOC = 1e-5;       // Half-saturation for DOC (mol/L)
    const double Ks_O2 = 1e-5;        // Half-saturation for O2 (mol/L)
    const double Y_DOC = 0.4;         // Yield on DOC (kg/mol)
    const double Y_O2 = 0.2;          // Yield on O2 (kg/mol)
}

// ============================================================================
// MAIN KINETICS FUNCTION - Full biogeochemistry
// ============================================================================
// Species indices:
//   C[0] = DOC
//   C[1] = O2
//   C[2] = CO2
//   C[3] = HCO3  (handled by equilibrium)
//   C[4] = CO3   (handled by equilibrium)
//   C[5] = H+    (handled by equilibrium)
// ============================================================================
inline void defineRxnKinetics(
    std::vector<double>& C,
    std::vector<double>& B,
    std::vector<double>& dC,
    std::vector<double>& dB,
    double dt,
    const std::vector<std::vector<double>>& Kc,
    const std::vector<double>& mu_vec)
{
    using namespace KineticsParams;

    // Initialize deltas
    for (size_t i = 0; i < dC.size(); ++i) dC[i] = 0.0;
    for (size_t i = 0; i < dB.size(); ++i) dB[i] = 0.0;

    // Skip if no biomass
    if (B[0] < 1e-14) return;

    // Get concentrations (ensure non-negative)
    double DOC = std::max(0.0, C[0]);
    double O2 = std::max(0.0, C[1]);

    // Dual Monod growth rate
    // μ = μ_max × [DOC/(Ks_DOC + DOC)] × [O2/(Ks_O2 + O2)]
    double f_DOC = DOC / (Ks_DOC + DOC);
    double f_O2 = O2 / (Ks_O2 + O2);
    double mu = mu_max * f_DOC * f_O2;

    // Biomass change
    double growth = mu * B[0];
    double decay = k_decay * B[0];
    dB[0] = (growth - decay) * dt;

    // Substrate changes
    // DOC consumption
    dC[0] = -(growth / Y_DOC) * dt;

    // O2 consumption
    dC[1] = -(growth / Y_O2) * dt;

    // CO2 production (from DOC oxidation)
    // Stoichiometry: 1 mol DOC → 1 mol CO2
    dC[2] = +(growth / Y_DOC) * dt;

    // HCO3, CO3, H: Leave to equilibrium solver (dC[3,4,5] = 0)

    // Validate outputs
    for (size_t i = 0; i < dC.size(); ++i) {
        if (std::isnan(dC[i]) || std::isinf(dC[i])) dC[i] = 0.0;
    }
    if (std::isnan(dB[0]) || std::isinf(dB[0])) dB[0] = 0.0;
}

#endif
```

### Expected Results
- Biomass grows where both DOC and O₂ are available
- DOC and O₂ decrease, CO₂ increases
- Carbonate equilibrium shifts as CO₂ is produced
- pH decreases near biofilm due to CO₂ production
- Biofilm expands into pore space

---

## 9.5 Test Case 5: Planktonic Bacteria (Free-floating)

### Description
Simulates transport of free-floating (planktonic) bacteria with growth kinetics.

### Configuration

**CompLaB_planktonic.xml:**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_planktonic</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx>
            <ny>30</ny>
            <nz>30</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
                <microbe0>2</microbe0>  <!-- Same as pore - planktonic -->
            </material_numbers>
        </domain>
        <delta_P>2.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>2</number_of_substrates>
        <substrate0>
            <name_of_substrates>DOC</name_of_substrates>
            <initial_concentration>0.1</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>1.0e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>0.1</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>
        <substrate1>
            <name_of_substrates>CO2</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.9e-9</in_pore>
                <in_biofilm>1.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate1>
    </chemistry>

    <microbiology>
        <number_of_microbes>1</number_of_microbes>

        <microbe0>
            <name_of_microbes>Planktonic</name_of_microbes>
            <solver_type>LBM</solver_type>  <!-- LBM for planktonic transport -->
            <reaction_type>kinetics</reaction_type>
            <initial_densities>10.0</initial_densities>  <!-- Lower initial density -->
            <decay_coefficient>1e-7</decay_coefficient>
            <half_saturation_constants>1e-5 0.0</half_saturation_constants>
            <maximum_uptake_flux>0.5 0.0</maximum_uptake_flux>
            <biomass_diffusion_coefficients>
                <in_pore>1e-10</in_pore>
                <in_biofilm>1e-10</in_biofilm>
            </biomass_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>10.0</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </microbe0>
    </microbiology>

    <equilibrium>
        <enabled>false</enabled>
    </equilibrium>
</parameters>
```

**defineKinetics_planktonic.hh:**
```cpp
#ifndef DEFINE_KINETICS_PLANKTONIC_HH
#define DEFINE_KINETICS_PLANKTONIC_HH

#include <vector>
#include <cmath>
#include <algorithm>

// ============================================================================
// KINETICS PARAMETERS - Planktonic bacteria
// ============================================================================
namespace KineticsParams {
    const double mu_max = 5.787e-6;   // Max growth rate (1/s)
    const double k_decay = 1e-7;      // Decay coefficient (1/s)
    const double Ks = 1e-5;           // Half-saturation (mol/L)
    const double Y = 0.4;             // Yield (kg/mol)
}

// ============================================================================
// MAIN KINETICS FUNCTION - Planktonic growth
// ============================================================================
inline void defineRxnKinetics(
    std::vector<double>& C,      // [DOC, CO2]
    std::vector<double>& B,      // [Planktonic]
    std::vector<double>& dC,
    std::vector<double>& dB,
    double dt,
    const std::vector<std::vector<double>>& Kc,
    const std::vector<double>& mu_vec)
{
    using namespace KineticsParams;

    for (size_t i = 0; i < dC.size(); ++i) dC[i] = 0.0;
    for (size_t i = 0; i < dB.size(); ++i) dB[i] = 0.0;

    if (B[0] < 1e-14) return;

    double DOC = std::max(0.0, C[0]);
    double mu = mu_max * DOC / (Ks + DOC);

    double growth = mu * B[0];
    double decay = k_decay * B[0];
    dB[0] = (growth - decay) * dt;

    dC[0] = -(growth / Y) * dt;  // DOC consumption
    dC[1] = +(growth / Y) * dt;  // CO2 production

    for (size_t i = 0; i < dC.size(); ++i) {
        if (std::isnan(dC[i]) || std::isinf(dC[i])) dC[i] = 0.0;
    }
    if (std::isnan(dB[0]) || std::isinf(dB[0])) dB[0] = 0.0;
}

#endif
```

### Expected Results
- Planktonic bacteria transported with flow
- Growth occurs throughout the domain where DOC is available
- No spatial attachment (unlike biofilm)
- Advection-diffusion of biomass

---

# 10. Output Files

## 10.1 VTI Files (Visualization)

VTI files are VTK ImageData format, viewable in ParaView:

| File Pattern | Description |
|--------------|-------------|
| `inputGeom.vti` | Porous medium geometry |
| `nsLattice_*.vti` | Flow velocity field |
| `DOC_*.vti` | Substrate concentration |
| `Heterotroph_*.vti` | Biomass concentration |
| `maskLattice_*.vti` | Material mask |

## 10.2 CHK Files (Checkpoints)

Binary checkpoint files for restart:

```bash
# Restart from checkpoint
./complab3d --restart output/subsLattice0_50000.chk
```

## 10.3 Console Output

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         SIMULATION COMPLETE                              ║
╠══════════════════════════════════════════════════════════════════════════╣
║ TIMING:                                                                  ║
║   Total iterations: 50000
║   Simulated time:   1.2345e-01 s
║   Wall clock:       3600.5 s (60.0 min)
╠══════════════════════════════════════════════════════════════════════════╣
║ SIMULATION MODE:                                                         ║
║   Biotic mode:      YES (with microbes)
║   Kinetics:         ENABLED
║   Equilibrium:      ENABLED
║   Validation diag:  DISABLED
╠══════════════════════════════════════════════════════════════════════════╣
║ BIOMASS RESULTS:                                                         ║
║   Initial max:      1.0000e+02 kg/m³
║   Final max:        1.8500e+02 kg/m³
║   Growth:           85.0%
║   CA triggers:      1234
║   Redistributions:  5678
╠══════════════════════════════════════════════════════════════════════════╣
║ FINAL CONCENTRATIONS:                                                    ║
║   DOC: min=5.0000e-02 avg=8.5000e-02 max=1.0000e-01
║   O2: min=1.0000e-04 avg=2.0000e-04 max=2.5000e-04
║   CO2: min=1.0000e-05 avg=5.0000e-05 max=1.0000e-04
╚══════════════════════════════════════════════════════════════════════════╝
```

---

# 11. Troubleshooting

## 11.1 Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `NaN detected at iter=X` | Numerical instability | Reduce time step, check parameters |
| `Ma > 0.3 warning` | High Mach number | Reduce pressure gradient or increase tau |
| `Stuck in CA loop` | Biomass redistribution failure | Check B_max, geometry |
| `Equilibrium solver did not converge` | Poor initial guess | Check initial concentrations |

## 11.2 Performance Tips

1. **Use track_performance=true** to identify bottlenecks
2. **Reduce VTI output frequency** for long simulations
3. **Use MPI parallelization** for large domains
4. **Disable validation_diagnostics** in production runs

## 11.3 Debugging Checklist

- [ ] Check XML syntax (valid XML)
- [ ] Verify geometry file exists and has correct dimensions
- [ ] Check that diffusion coefficients are positive
- [ ] Verify boundary conditions are appropriate
- [ ] Enable `enable_validation_diagnostics=true` for detailed output
- [ ] Check kinetics parameters are physically reasonable

---

# Appendix A: Symbol Table

| Symbol | Description | Units |
|--------|-------------|-------|
| ρ | Density | kg/m³ |
| u | Velocity | m/s |
| P | Pressure | Pa |
| ν | Kinematic viscosity | m²/s |
| D | Diffusion coefficient | m²/s |
| C | Concentration | mol/L |
| B | Biomass concentration | kg/m³ |
| μ | Specific growth rate | 1/s |
| μ_max | Maximum growth rate | 1/s |
| K_s | Half-saturation constant | mol/L |
| Y | Yield coefficient | kg/mol |
| k_decay | Decay coefficient | 1/s |
| τ | LBM relaxation time | - |
| ω | LBM relaxation frequency (1/τ) | - |
| Pe | Péclet number | - |
| Ma | Mach number | - |

---

# Appendix B: References

1. Palabos Library: https://palabos.unige.ch/
2. Lattice Boltzmann Method: Succi, S. (2001). The Lattice Boltzmann Equation for Fluid Dynamics and Beyond.
3. Monod Kinetics: Monod, J. (1949). The Growth of Bacterial Cultures.
4. Biofilm Modeling: Picioreanu, C. et al. (1998). Mathematical modeling of biofilm structure.

---

**Document Version:** 2.0
**Last Updated:** February 2026
**Contact:** Meile Lab, University of Georgia

