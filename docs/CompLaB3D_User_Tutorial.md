# CompLaB3D User Tutorial
## Three-Dimensional Biogeochemical Reactive Transport Solver

**Version:** 2.0 (Biotic-Kinetic-Anderson-NR)
**Author:** Shahram Asgari
**Advisor:** Dr. Christof Meile
**Laboratory:** Meile Lab, University of Georgia (UGA)

---

# TABLE OF CONTENTS

| Part | Section | Description |
|------|---------|-------------|
| **PART I** | **INTRODUCTION** | Overview and getting started |
| | 1.1 | What is CompLaB3D? |
| | 1.2 | Simulation Workflow Overview |
| | 1.3 | Quick Start Guide |
| **PART II** | **CONFIGURATION** | XML options and settings |
| | 2.1 | XML File Structure |
| | 2.2 | Simulation Mode Options |
| | 2.3 | Validation Diagnostics |
| | 2.4 | Domain and Numerics |
| | 2.5 | Chemistry Settings |
| | 2.6 | Microbiology Settings |
| | 2.7 | CA Options (fraction vs half) |
| | 2.8 | Equilibrium Chemistry |
| **PART III** | **ABIOTIC SIMULATIONS** | Transport without microbes |
| | 3.1 | Pure Transport (No Reactions) |
| | 3.2 | Transport + Equilibrium Chemistry |
| **PART IV** | **BIOTIC SIMULATIONS** | Transport with microbes |
| | 4.1 | Biofilm with CA Solver |
| | 4.2 | Planktonic Bacteria (LBM Solver) |
| | 4.3 | Biofilm + Equilibrium |
| | 4.4 | Multi-Species Systems |
| **PART V** | **EQUILIBRIUM SOLVER** | Newton-Raphson + Anderson |
| | 5.1 | Why Equilibrium Chemistry? |
| | 5.2 | Newton-Raphson Method |
| | 5.3 | Anderson Acceleration |
| | 5.4 | Configuring Equilibrium |
| **PART VI** | **VALIDATION & DEBUGGING** | Diagnostics and testing |
| | 6.1 | enable_validation_diagnostics |
| | 6.2 | Understanding Diagnostic Output |
| | 6.3 | Mass Balance Verification |
| | 6.4 | Common Issues and Solutions |
| **PART VII** | **COMPLETE EXAMPLES** | Full XML + kinetics files |

---

# PART I: INTRODUCTION

## 1.1 What is CompLaB3D?

CompLaB3D simulates **biogeochemical reactive transport** in 3D porous media using:

```
+=============================================================================+
|                           CompLaB3D COMPONENTS                               |
+=============================================================================+
|                                                                              |
|   +------------------+     +------------------+     +------------------+     |
|   |   FLUID FLOW     |     | SOLUTE TRANSPORT |     |    REACTIONS     |     |
|   |  (Navier-Stokes) |     | (Advection-Diff) |     | (Kinetics + Eq)  |     |
|   |   LBM D3Q19      |     |   LBM D3Q7       |     |  Monod + NR      |     |
|   +------------------+     +------------------+     +------------------+     |
|            |                       |                        |                |
|            +-----------+-----------+                        |                |
|                        |                                    |                |
|                        v                                    v                |
|              +------------------+                  +------------------+      |
|              |  BIOFILM MODEL   |<---------------->|    BIOMASS       |      |
|              |  (CA or FD)      |                  |   (Growth/Decay) |      |
|              +------------------+                  +------------------+      |
|                                                                              |
+=============================================================================+
```

## 1.2 Simulation Workflow (10 Phases)

```
+============================================================================+
|                        SIMULATION PHASES                                     |
+============================================================================+

  PHASE 1: Load XML configuration
              |
              v
  PHASE 2: Geometry setup and preprocessing
              |
              v
  PHASE 3: Navier-Stokes flow simulation
              |
              +---> Calculate permeability
              +---> Adjust pressure for target Peclet
              |
              v
  PHASE 4: Create substrate and biomass lattices
              |
              v
  PHASE 5: Couple NS velocity to transport lattices
              |
              v
  PHASE 6: MAIN SIMULATION LOOP <=========================+
              |                                            |
              +---> STEP 6.1: LBM Collision               |
              +---> STEP 6.2: Kinetics (if enabled)       |
              +---> STEP 6.3: Equilibrium (if enabled)    |
              +---> STEP 6.4: CA Biomass Expansion        |
              +---> STEP 6.5: Update Flow (if biofilm)    |
              +---> STEP 6.6: LBM Streaming               |
              |                                            |
              +----------------> Continue -----------------+
              |
              v
  PHASE 7-10: Output results and cleanup

+============================================================================+
```

## 1.3 Quick Start Guide

**Step 1:** Copy the appropriate XML template:
```bash
# For biofilm simulation:
cp CompLaB.xml my_simulation.xml

# For planktonic simulation:
cp CompLaB_planktonic.xml my_simulation.xml
```

**Step 2:** Edit your XML file (see Part II)

**Step 3:** Compile and run:
```bash
cd src
make
./complab3d ../my_simulation.xml
```

---

# PART II: CONFIGURATION

## 2.1 XML File Structure

```xml
<?xml version="1.0" ?>
<parameters>
    <path>...</path>                  <!-- Input/output directories -->
    <simulation_mode>...</simulation_mode>  <!-- Mode controls -->
    <LB_numerics>...</LB_numerics>    <!-- LBM parameters -->
    <chemistry>...</chemistry>        <!-- Substrate definitions -->
    <microbiology>...</microbiology>  <!-- Microbe definitions -->
    <equilibrium>...</equilibrium>    <!-- Equilibrium chemistry -->
    <IO>...</IO>                      <!-- File I/O settings -->
</parameters>
```

## 2.2 Simulation Mode Options

The `<simulation_mode>` section controls three critical flags:

```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
    <enable_validation_diagnostics>false</enable_validation_diagnostics>
</simulation_mode>
```

### Option 1: biotic_mode

| Value | Description |
|-------|-------------|
| `true` or `biotic` | Full simulation with microbes, biomass growth, and kinetics |
| `false` or `abiotic` | Transport only - no microbes, skips microbiology section |

**When to use `abiotic`:**
- Testing pure transport without biological effects
- Equilibrium chemistry only simulations
- Debugging flow field or transport parameters

### Option 2: enable_kinetics

| Value | Description |
|-------|-------------|
| `true` | Monod kinetics reactions are calculated each iteration |
| `false` | Kinetics disabled, only equilibrium chemistry runs |

**Note:** When `biotic_mode=false`, kinetics is automatically disabled.

### Option 3: enable_validation_diagnostics

| Value | Description |
|-------|-------------|
| `true` | Detailed per-iteration output for debugging |
| `false` | Normal operation (faster) |

**WARNING:** Enabling diagnostics adds computational overhead. Use only for debugging!

## 2.3 Validation Diagnostics

When `enable_validation_diagnostics=true`, the code prints detailed information at each iteration (every 100 iterations + first 10):

### XML Example:
```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
    <enable_validation_diagnostics>true</enable_validation_diagnostics>
</simulation_mode>
```

### Sample Output:
```
+-----------------------------------------------------------------------------+
| VALIDATION DIAGNOSTICS - Iteration 100                                       |
+-----------------------------------------------------------------------------+
| Time: 7.5000e-01 s                                                          |
+-----------------------------------------------------------------------------+
| STEP 6.1 [COLLISION]: LBM collision completed                               |
| STEP 6.2 [KINETICS]: ACTIVE - 1 reaction(s)                                 |
|   DOC @center: C=9.87e-02, dC=-2.34e-06                                     |
|   Biomass @center: B=9.90e+01, dB=1.23e-05                                  |
| STEP 6.3 [EQUILIBRIUM]: ACTIVE                                              |
|   DOC: min=9.50e-02, max=1.00e-01                                           |
+-----------------------------------------------------------------------------+
| MASS BALANCE CHECK:                                                          |
|   DOC total: 4.56e+02                                                        |
|   Total biomass: 1.23e+04                                                    |
+-----------------------------------------------------------------------------+
```

### What Each Step Shows:

| Step | What it Verifies |
|------|------------------|
| **STEP 6.1 COLLISION** | LBM collision completed successfully |
| **STEP 6.2 KINETICS** | Whether kinetics is running, sample dC and dB values |
| **STEP 6.3 EQUILIBRIUM** | Whether equilibrium solver is running, min/max concentrations |
| **MASS BALANCE** | Total mass in system for conservation checks |

## 2.4 Domain and Numerics

```xml
<LB_numerics>
    <domain>
        <nx>50</nx>                  <!-- Domain size (voxels) -->
        <ny>30</ny>
        <nz>30</nz>
        <dx>1.0</dx>                 <!-- Voxel size -->
        <unit>um</unit>              <!-- Units: m, mm, or um -->
        <characteristic_length>30</characteristic_length>
        <filename>geometry.dat</filename>
        <material_numbers>
            <pore>2</pore>           <!-- Pore space tag -->
            <solid>0</solid>         <!-- Solid/no dynamics tag -->
            <bounce_back>1</bounce_back>  <!-- Solid boundary tag -->
            <microbe0>3 6</microbe0>      <!-- Biofilm cell tags -->
        </material_numbers>
    </domain>
    <delta_P>2.0e-3</delta_P>       <!-- Pressure drop -->
    <Peclet>1.0</Peclet>            <!-- Target Peclet number -->
    <tau>0.8</tau>                  <!-- LBM relaxation time -->
    <iteration>
        <ade_max_iT>50000</ade_max_iT>
        <ade_converge_iT>1e-8</ade_converge_iT>
    </iteration>
</LB_numerics>
```

## 2.5 Chemistry Settings

```xml
<chemistry>
    <number_of_substrates>5</number_of_substrates>

    <substrate0>
        <name_of_substrates>DOC</name_of_substrates>
        <initial_concentration>0.1</initial_concentration>
        <substrate_diffusion_coefficients>
            <in_pore>1.0e-9</in_pore>      <!-- D in pore space [m2/s] -->
            <in_biofilm>2.0e-10</in_biofilm>  <!-- D in biofilm [m2/s] -->
        </substrate_diffusion_coefficients>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <right_boundary_type>Neumann</right_boundary_type>
        <left_boundary_condition>0.1</left_boundary_condition>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate0>
    <!-- ... more substrates ... -->
</chemistry>
```

## 2.6 Microbiology Settings

```xml
<microbiology>
    <number_of_microbes>1</number_of_microbes>
    <maximum_biomass_density>100.0</maximum_biomass_density>
    <thrd_biofilm_fraction>0.1</thrd_biofilm_fraction>
    <CA_method>half</CA_method>   <!-- See Section 2.7 -->

    <microbe0>
        <name_of_microbes>Heterotroph</name_of_microbes>
        <solver_type>CA</solver_type>      <!-- CA, LBM, or FD -->
        <reaction_type>kinetics</reaction_type>
        <initial_densities>99.0 99.0</initial_densities>
        <decay_coefficient>1.0e-9</decay_coefficient>
        <viscosity_ratio_in_biofilm>10.0</viscosity_ratio_in_biofilm>
        <half_saturation_constants>1.0e-5 0.0 0.0 0.0 0.0</half_saturation_constants>
        <maximum_uptake_flux>2.5 0.0 0.0 0.0 0.0</maximum_uptake_flux>
    </microbe0>
</microbiology>
```

## 2.7 CA Options: fraction vs half

The `<CA_method>` option controls how excess biomass is redistributed when a cell exceeds `maximum_biomass_density`.

```xml
<CA_method>fraction</CA_method>   <!-- or "half" -->
```

### Method Comparison:

```
+=============================================================================+
|                    CA REDISTRIBUTION METHODS                                 |
+=============================================================================+

   FRACTION METHOD (<CA_method>fraction</CA_method>)
   ------------------------------------------------

   When B > B_max:

   +-------+-------+-------+        +-------+-------+-------+
   |       |  B1   |       |        |       |B1+dB/6|       |
   +-------+-------+-------+        +-------+-------+-------+
   |  B2   | B_exc |  B3   |  --->  |B2+dB/6| B_max |B3+dB/6|
   +-------+-------+-------+        +-------+-------+-------+
   |       |  B4   |       |        |       |B4+dB/6|       |
   +-------+-------+-------+        +-------+-------+-------+

   Excess = B_exc - B_max is distributed PROPORTIONALLY to all 6 neighbors
   Each neighbor gets: dB = Excess / 6

   PROS: Smoother distribution, more gradual expansion
   CONS: Can take many iterations to stabilize


   HALF METHOD (<CA_method>half</CA_method>)
   -----------------------------------------

   When B > B_max:

   +-------+-------+-------+        +-------+-------+-------+
   |       |  B1   |       |        |       |  B1   |       |
   +-------+-------+-------+        +-------+-------+-------+
   |  B2   | B_exc |  B3   |  --->  |  B2   | B_mid |B3+half|
   +-------+-------+-------+        +-------+-------+-------+
   |       |  B4   |       |        |       |  B4   |       |
   +-------+-------+-------+        +-------+-------+-------+

   HALF of excess goes to the neighbor with SHORTEST DISTANCE to pore space
   This promotes expansion TOWARD open pore space

   PROS: Faster stabilization, biologically realistic (grows toward nutrients)
   CONS: Can cause directional bias

+=============================================================================+
```

### Which Method to Choose?

| Use Case | Recommended Method |
|----------|-------------------|
| General biofilm simulation | `half` |
| Smooth, diffuse biofilm growth | `fraction` |
| Fast simulation with quick stabilization | `half` |
| Detailed biofilm morphology study | `fraction` |

## 2.8 Equilibrium Chemistry

```xml
<equilibrium>
    <enabled>true</enabled>
    <components>HCO3 Hplus</components>
    <stoichiometry>
        <species0>0.0 0.0</species0>   <!-- DOC: not in equilibrium -->
        <species1>1.0 1.0</species1>   <!-- CO2: H2CO3 = HCO3- + H+ -->
        <species2>1.0 0.0</species2>   <!-- HCO3: component -->
        <species3>1.0 -1.0</species3>  <!-- CO3: HCO3- = CO3-- + H+ -->
        <species4>0.0 1.0</species4>   <!-- H+: component -->
    </stoichiometry>
    <logK>
        <species0>0.0</species0>
        <species1>6.35</species1>     <!-- pKa1 of carbonic acid -->
        <species2>0.0</species2>
        <species3>-10.33</species3>   <!-- pKa2 of carbonic acid -->
        <species4>0.0</species4>
    </logK>
</equilibrium>
```

---

# PART III: ABIOTIC SIMULATIONS

Abiotic simulations model transport **without microbial activity**. Use `<biotic_mode>false</biotic_mode>`.

## 3.1 Pure Transport (No Reactions)

**Use case:** Testing advection-diffusion, studying conservative tracer transport.

### XML Configuration:
```xml
<simulation_mode>
    <biotic_mode>false</biotic_mode>
    <enable_kinetics>false</enable_kinetics>
    <enable_validation_diagnostics>false</enable_validation_diagnostics>
</simulation_mode>

<!-- No microbiology section needed -->
<microbiology>
    <number_of_microbes>0</number_of_microbes>
</microbiology>

<equilibrium>
    <enabled>false</enabled>
</equilibrium>
```

### What Happens:
1. Flow field is computed (if Pe > 0)
2. Substrate transport via advection-diffusion
3. No kinetics, no equilibrium, no biomass

### Expected Output:
```
+======================================================================+
| SIMULATION MODE: ABIOTIC (no microbes - transport only)              |
+======================================================================+
Note: Kinetics disabled (abiotic mode)

Equilibrium chemistry: DISABLED
```

## 3.2 Transport + Equilibrium Chemistry

**Use case:** Studying carbonate chemistry, pH-dependent reactions without biology.

### XML Configuration:
```xml
<simulation_mode>
    <biotic_mode>false</biotic_mode>
    <enable_kinetics>false</enable_kinetics>
</simulation_mode>

<microbiology>
    <number_of_microbes>0</number_of_microbes>
</microbiology>

<equilibrium>
    <enabled>true</enabled>
    <components>HCO3 Hplus</components>
    <stoichiometry>
        <species0>0.0 0.0</species0>   <!-- Tracer -->
        <species1>1.0 1.0</species1>   <!-- CO2 -->
        <species2>1.0 0.0</species2>   <!-- HCO3 -->
        <species3>1.0 -1.0</species3>  <!-- CO3 -->
        <species4>0.0 1.0</species4>   <!-- H+ -->
    </stoichiometry>
    <logK>
        <species0>0.0</species0>
        <species1>6.35</species1>
        <species2>0.0</species2>
        <species3>-10.33</species3>
        <species4>0.0</species4>
    </logK>
</equilibrium>
```

### What Happens:
1. Transport of all substrates
2. Equilibrium chemistry solver adjusts pH-dependent species
3. No microbial growth or consumption

---

# PART IV: BIOTIC SIMULATIONS

Biotic simulations include **microbial activity**: growth, substrate consumption, and biofilm dynamics.

## 4.1 Biofilm with CA Solver

**Use case:** Simulating attached bacteria that grow on surfaces and expand into pore space.

### XML Configuration:
```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
</simulation_mode>

<microbiology>
    <number_of_microbes>1</number_of_microbes>
    <maximum_biomass_density>100.0</maximum_biomass_density>
    <thrd_biofilm_fraction>0.1</thrd_biofilm_fraction>
    <CA_method>half</CA_method>

    <microbe0>
        <name_of_microbes>Heterotroph</name_of_microbes>
        <solver_type>CA</solver_type>
        <reaction_type>kinetics</reaction_type>
        <initial_densities>99.0 99.0</initial_densities>
        <decay_coefficient>1.0e-9</decay_coefficient>
        <viscosity_ratio_in_biofilm>10.0</viscosity_ratio_in_biofilm>
        <half_saturation_constants>1.0e-5 0.0 0.0 0.0 0.0</half_saturation_constants>
        <maximum_uptake_flux>2.5 0.0 0.0 0.0 0.0</maximum_uptake_flux>
    </microbe0>
</microbiology>
```

### defineKinetics.hh for Biofilm:
```cpp
namespace KineticParams {
    constexpr double mu_max   = 1.0;       // Maximum growth rate [1/s]
    constexpr double Ks       = 1.0e-5;    // Half-saturation [mol/L]
    constexpr double Y        = 0.4;       // Yield coefficient
    constexpr double k_decay  = 1.0e-9;    // Decay rate [1/s]
}
```

### Workflow:
```
BIOFILM CA SIMULATION WORKFLOW
==============================

1. Kinetics calculates dB/dt for each biofilm cell:
   dB/dt = (mu - k_decay) * B

2. Biomass is updated:
   B_new = B_old + dB/dt * dt

3. If B_new > B_max:
   CA redistributes excess based on <CA_method>

4. Flow field is updated if biofilm expanded:
   - New cells become bounce-back or permeable
   - NS solver re-converges
```

## 4.2 Planktonic Bacteria (LBM Solver)

**Use case:** Free-floating bacteria transported with the flow.

### XML Configuration (CompLaB_planktonic.xml):
```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
</simulation_mode>

<microbiology>
    <number_of_microbes>1</number_of_microbes>
    <maximum_biomass_density>100.0</maximum_biomass_density>
    <CA_method>none</CA_method>   <!-- No CA for planktonic -->

    <microbe0>
        <name_of_microbes>Planktonic_Heterotroph</name_of_microbes>
        <solver_type>LBM</solver_type>   <!-- LBM for advection-diffusion -->
        <reaction_type>kinetics</reaction_type>
        <initial_densities>0.0 10.0</initial_densities>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <left_boundary_condition>10.0</left_boundary_condition>
    </microbe0>
</microbiology>
```

### Key Differences from Biofilm:
| Feature | Biofilm (CA) | Planktonic (LBM) |
|---------|--------------|------------------|
| Transport | Stationary | Advected with flow |
| Material numbers | Assigned cells | Same as pore |
| Diffusion | In_biofilm value | In_pore value |
| CA expansion | Yes | No |
| Typical decay rate | Low (protected) | Higher (exposed) |

### defineKinetics_planktonic.hh:
```cpp
namespace KineticParams {
    constexpr double mu_max   = 0.5;       // Lower than biofilm
    constexpr double Ks       = 1.0e-5;
    constexpr double Y        = 0.4;
    constexpr double k_decay  = 1.0e-7;    // Higher than biofilm
}
```

## 4.3 Biofilm + Equilibrium Chemistry

**Use case:** Biofilm affecting pH through CO2 production, with fast equilibrium adjustments.

### XML Configuration:
```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
</simulation_mode>

<microbiology>
    <number_of_microbes>1</number_of_microbes>
    <microbe0>
        <solver_type>CA</solver_type>
        <reaction_type>kinetics</reaction_type>
        <!-- ... standard biofilm settings ... -->
    </microbe0>
</microbiology>

<equilibrium>
    <enabled>true</enabled>
    <components>HCO3 Hplus</components>
    <!-- ... equilibrium settings ... -->
</equilibrium>
```

### Simulation Flow:
```
For each iteration:
  1. Kinetics: DOC consumed, CO2 produced, biomass grows
  2. Equilibrium: CO2 + H2O <-> H2CO3 <-> HCO3- + H+ <-> CO3-- + 2H+
  3. Result: pH changes based on biological activity
```

## 4.4 Multi-Species Systems

For multiple microbe types, add additional `<microbeN>` sections:

```xml
<microbiology>
    <number_of_microbes>2</number_of_microbes>

    <microbe0>
        <name_of_microbes>Aerobic_Heterotroph</name_of_microbes>
        <solver_type>CA</solver_type>
        <!-- consumes DOC, produces CO2 -->
    </microbe0>

    <microbe1>
        <name_of_microbes>Methanogen</name_of_microbes>
        <solver_type>CA</solver_type>
        <!-- consumes CO2, produces CH4 -->
    </microbe1>
</microbiology>
```

---

# PART V: EQUILIBRIUM SOLVER

## 5.1 Why Equilibrium Chemistry?

Many chemical reactions are **fast compared to transport** and reach equilibrium instantaneously:
- Acid-base reactions (protonation/deprotonation)
- Carbonate system speciation
- Metal complexation

Instead of tracking these kinetically (which would require tiny timesteps), we solve for equilibrium at each iteration.

## 5.2 Newton-Raphson Method

The equilibrium solver uses the **Newton-Raphson method** to find concentrations that satisfy mass action laws:

```
MASS ACTION LAW:
K = [products]^v / [reactants]^v

For example, carbonic acid dissociation:
H2CO3 <-> HCO3- + H+
K1 = [HCO3-][H+] / [H2CO3] = 10^(-6.35)

NEWTON-RAPHSON ITERATION:
Given current concentrations C_n:
1. Calculate residual: R(C_n) = mass balance error
2. Calculate Jacobian: J = dR/dC
3. Solve: J * dC = -R
4. Update: C_{n+1} = C_n + dC
5. Repeat until ||R|| < tolerance
```

## 5.3 Anderson Acceleration

**Problem:** Newton-Raphson can converge slowly or oscillate near the solution.

**Solution:** Anderson Acceleration stabilizes and accelerates convergence by using history of previous iterates.

```
STANDARD NEWTON-RAPHSON:
  C_{n+1} = C_n + dC_n

ANDERSON ACCELERATED NEWTON-RAPHSON:
  C_{n+1} = Sum(alpha_i * C_{n-i}) + dC_n

  where alpha_i are optimized to minimize residual
```

### Why We Use Anderson Acceleration:

| Issue | Without Anderson | With Anderson |
|-------|------------------|---------------|
| Slow convergence | 50-100 iterations | 10-20 iterations |
| Oscillation near solution | Common | Rare |
| Robustness for stiff systems | Poor | Good |

### Code Configuration:
```cpp
// In complab.cpp
eqSolver.setMaxIterations(200);   // Max NR iterations
eqSolver.setTolerance(1e-10);     // Convergence tolerance
eqSolver.setAndersonDepth(4);     // History depth for Anderson
```

The **Anderson depth** (m=4 by default) controls how many previous iterates are used:
- `m=0`: Pure Newton-Raphson
- `m=4`: Uses last 4 iterates (recommended)
- `m>6`: Diminishing returns, more memory

## 5.4 Configuring Equilibrium

### Stoichiometry Matrix Setup

Each row represents a species, each column a component:

```
                   Component 1   Component 2
                   (HCO3-)       (H+)
Species 0 (DOC)      0.0          0.0      <- Not in equilibrium
Species 1 (CO2)      1.0          1.0      <- CO2 = HCO3- + H+ - K1
Species 2 (HCO3-)    1.0          0.0      <- Component itself
Species 3 (CO3--)    1.0         -1.0      <- CO3 = HCO3- - H+ + K2
Species 4 (H+)       0.0          1.0      <- Component itself
```

### Log K Values

For reaction: aA + bB <-> cC + dD, K = [C]^c[D]^d / [A]^a[B]^b

```xml
<logK>
    <species0>0.0</species0>      <!-- DOC: not in equilibrium -->
    <species1>6.35</species1>     <!-- H2CO3 = HCO3- + H+, pKa1 -->
    <species2>0.0</species2>      <!-- HCO3-: component -->
    <species3>-10.33</species3>   <!-- HCO3- = CO3-- + H+, pKa2 -->
    <species4>0.0</species4>      <!-- H+: component -->
</logK>
```

---

# PART VI: VALIDATION & DEBUGGING

## 6.1 enable_validation_diagnostics

### Enabling in XML:
```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
    <enable_validation_diagnostics>true</enable_validation_diagnostics>
</simulation_mode>
```

### What Gets Printed:

**Every 100 iterations (and first 10):**
```
+-----------------------------------------------------------------------------+
| VALIDATION DIAGNOSTICS - Iteration 100                                       |
+-----------------------------------------------------------------------------+
| Time: 7.5000e-01 s                                                          |
+-----------------------------------------------------------------------------+
| STEP 6.1 [COLLISION]: LBM collision completed                               |
| STEP 6.2 [KINETICS]: ACTIVE - 1 reaction(s)                                 |
|   DOC @center: C=9.87e-02, dC=-2.34e-06                                     |
|   CO2 @center: C=1.05e-05, dC=2.34e-06                                      |
|   Biomass @center: B=9.90e+01, dB=1.23e-05                                  |
| STEP 6.3 [EQUILIBRIUM]: ACTIVE                                              |
|   DOC: min=9.50e-02, max=1.00e-01                                           |
|   CO2: min=1.00e-05, max=1.10e-05                                           |
+-----------------------------------------------------------------------------+
| MASS BALANCE CHECK:                                                          |
|   DOC total: 4.56e+02                                                        |
|   CO2 total: 5.67e-02                                                        |
|   Total biomass: 1.23e+04                                                    |
+-----------------------------------------------------------------------------+
```

## 6.2 Understanding Diagnostic Output

### Key Values to Check:

| Field | Normal Value | Problem Indicator |
|-------|--------------|-------------------|
| `dC` (substrate change) | Small negative for consumed | Zero = no kinetics |
| `dB` (biomass change) | Small positive for growth | Zero = no growth |
| `C @center` | Reasonable concentration | NaN or Inf |
| `Mass total` | Changes slowly | Sudden jumps |

### Step-by-Step Verification:

```
WHAT TO LOOK FOR:
=================

1. COLLISION step completes without error
   -> If error here: Check LBM parameters (tau, omega)

2. KINETICS shows non-zero dC and dB
   -> If zero: Check defineKinetics.hh parameters
   -> If NaN: Check for division by zero or negative concentrations

3. EQUILIBRIUM shows reasonable min/max
   -> If all same: Equilibrium not working
   -> If negative: Check logK signs

4. MASS BALANCE changes appropriately
   -> Substrate decreases as biomass grows
   -> Total mass conserved (within boundaries)
```

## 6.3 Mass Balance Verification

### Expected Behavior:

For a closed system with Neumann boundaries:
```
Initial DOC mass + DOC influx = Final DOC mass + DOC consumed by kinetics
```

For Dirichlet boundaries:
```
Mass is not conserved (flux through boundaries)
But: Rate of consumption should match rate of biomass production / Y
```

### Kinetics Mass Balance Check:

In the kinetics output:
```
| MASS BALANCE CHECK:
|   Expected DOC use:    1.23e-05 mol/L/s   <- dB/Y
|   Actual DOC use:      1.21e-05 mol/L/s   <- -dDOC
|   Balance error:       1.63% OK           <- Should be <5%
```

If error > 5%: Check if substrate clamping is active (normal for low DOC).

## 6.4 Common Issues and Solutions

### Issue 1: No Biomass Growth
```
| STEP 6.2 [KINETICS]: ACTIVE
|   Biomass @center: B=0.00e+00, dB=0.00e+00
```

**Solutions:**
- Check `initial_densities` in XML
- Check `MIN_BIOMASS` threshold in defineKinetics.hh
- Verify material numbers match geometry

### Issue 2: Kinetics Disabled
```
| STEP 6.2 [KINETICS]: DISABLED (enable_kinetics=false, kns_count=0)
```

**Solutions:**
- Set `<enable_kinetics>true</enable_kinetics>`
- Set `<reaction_type>kinetics</reaction_type>` for microbe

### Issue 3: NaN Values
```
| DOC @center: C=nan, dC=nan
```

**Solutions:**
- Check for negative concentrations
- Reduce dt_kinetics in defineKinetics.hh
- Check for division by zero (Ks=0?)

### Issue 4: Equilibrium Not Changing Values
```
| STEP 6.3 [EQUILIBRIUM]: ACTIVE
|   All species: min=max (identical values)
```

**Solutions:**
- Check stoichiometry matrix is correct
- Verify logK values have correct signs
- Ensure components are not all zeros

---

# PART VII: COMPLETE EXAMPLES

## Example 1: Abiotic Transport Only

**File: CompLaB_abiotic_transport.xml**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_abiotic</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>false</biotic_mode>
        <enable_kinetics>false</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx><ny>30</ny><nz>30</nz>
            <dx>1.0</dx><unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore><solid>0</solid><bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>2.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>10000</ade_max_iT>
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

    <microbiology>
        <number_of_microbes>0</number_of_microbes>
    </microbiology>

    <equilibrium>
        <enabled>false</enabled>
    </equilibrium>

    <IO>
        <save_VTK_interval>100</save_VTK_interval>
    </IO>
</parameters>
```

## Example 2: Biofilm with CA (fraction method)

**File: CompLaB_biofilm_fraction.xml**
```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_biofilm_fraction</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>50</nx><ny>30</ny><nz>30</nz>
            <dx>1.0</dx><unit>um</unit>
            <characteristic_length>30</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore><solid>0</solid><bounce_back>1</bounce_back>
                <microbe0>3 6</microbe0>
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
                <in_biofilm>3.8e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate1>
    </chemistry>

    <microbiology>
        <number_of_microbes>1</number_of_microbes>
        <maximum_biomass_density>100.0</maximum_biomass_density>
        <thrd_biofilm_fraction>0.1</thrd_biofilm_fraction>
        <CA_method>fraction</CA_method>

        <microbe0>
            <name_of_microbes>Heterotroph</name_of_microbes>
            <solver_type>CA</solver_type>
            <reaction_type>kinetics</reaction_type>
            <initial_densities>99.0 99.0</initial_densities>
            <decay_coefficient>1.0e-9</decay_coefficient>
            <viscosity_ratio_in_biofilm>10.0</viscosity_ratio_in_biofilm>
            <half_saturation_constants>1.0e-5 0.0</half_saturation_constants>
            <maximum_uptake_flux>2.5 0.0</maximum_uptake_flux>
        </microbe0>
    </microbiology>

    <equilibrium>
        <enabled>false</enabled>
    </equilibrium>

    <IO>
        <save_VTK_interval>500</save_VTK_interval>
    </IO>
</parameters>
```

**Corresponding defineKinetics.hh:**
```cpp
namespace KineticParams {
    constexpr double mu_max   = 1.0;
    constexpr double Ks       = 1.0e-5;
    constexpr double Y        = 0.4;
    constexpr double k_decay  = 1.0e-9;
    constexpr double dt_kinetics = 0.0075;
}
```

## Example 3: Planktonic Bacteria

**File: CompLaB_planktonic.xml** (already exists in project)

Key differences:
- `<solver_type>LBM</solver_type>` for advected transport
- `<CA_method>none</CA_method>` since no CA needed
- Dirichlet BC for bacteria inlet
- Use defineKinetics_planktonic.hh

## Example 4: Biofilm + Equilibrium Chemistry

```xml
<!-- Add to biofilm XML -->
<equilibrium>
    <enabled>true</enabled>
    <components>HCO3 Hplus</components>
    <stoichiometry>
        <species0>0.0 0.0</species0>   <!-- DOC -->
        <species1>1.0 1.0</species1>   <!-- CO2 -->
    </stoichiometry>
    <logK>
        <species0>0.0</species0>
        <species1>6.35</species1>
    </logK>
</equilibrium>
```

---

# QUICK REFERENCE TABLES

## Simulation Mode Combinations

| biotic_mode | enable_kinetics | equilibrium | Result |
|-------------|-----------------|-------------|--------|
| false | (auto-false) | false | Pure transport |
| false | (auto-false) | true | Transport + equilibrium |
| true | true | false | Biofilm + kinetics |
| true | true | true | Biofilm + kinetics + equilibrium |
| true | false | true | Biofilm (no growth) + equilibrium |

## CA Method Selection

| Scenario | Recommended CA_method |
|----------|----------------------|
| General simulation | half |
| Detailed morphology study | fraction |
| Fast stabilization needed | half |
| Smooth diffuse growth | fraction |

## Solver Type Selection

| Microbe Type | solver_type | Description |
|--------------|-------------|-------------|
| Attached biofilm | CA | Cells stay in place, expand via CA |
| Planktonic (mobile) | LBM | Cells advected with flow |
| Diffusing microbes | FD | Finite difference diffusion |

## Parameter Checklist

Before running a simulation, verify:

- [ ] `biotic_mode` matches your intent
- [ ] `enable_kinetics` is set correctly
- [ ] `solver_type` matches microbe type
- [ ] `reaction_type` is set to "kinetics"
- [ ] `initial_densities` are non-zero where biomass should exist
- [ ] `material_numbers` match your geometry file
- [ ] `defineKinetics.hh` has correct parameters
- [ ] `enable_validation_diagnostics` is false for production runs

---

**End of Tutorial**

For questions or issues, contact the Meile Lab at University of Georgia.
