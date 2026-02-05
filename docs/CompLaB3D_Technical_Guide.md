# CompLaB3D Technical Guide
## Understanding the Code: Kinetics, CA, and Equilibrium Solver

**Version:** 2.0 (Biotic-Kinetic-Anderson-NR)
**Author:** Shahram Asgari / University of Georgia

---

# TABLE OF CONTENTS

1. [Introduction](#1-introduction)
2. [Biotic Kinetics (Monod Model)](#2-biotic-kinetics-monod-model)
3. [Abiotic Kinetics (Chemical Reactions)](#3-abiotic-kinetics-chemical-reactions)
4. [Cellular Automata (CA) Biofilm Expansion](#4-cellular-automata-ca-biofilm-expansion)
5. [Equilibrium Solver (Newton-Raphson + Anderson)](#5-equilibrium-solver-newton-raphson--anderson)
6. [Data Flow in the Simulation Loop](#6-data-flow-in-the-simulation-loop)
7. [Complete Examples](#7-complete-examples)

---

# 1. Introduction

CompLaB3D uses **operator splitting** to solve reactive transport:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    OPERATOR SPLITTING APPROACH                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Each timestep Δt is split into sequential sub-steps:                      │
│                                                                              │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│   │  TRANSPORT   │ --> │   KINETICS   │ --> │ EQUILIBRIUM  │                │
│   │  (LBM ADE)   │     │   (Monod)    │     │   (NR+AA)    │                │
│   └──────────────┘     └──────────────┘     └──────────────┘                │
│          │                    │                    │                         │
│          v                    v                    v                         │
│   ∂C/∂t = ∇·(D∇C-uC)    dB/dt = μ·B         K = [C][D]/[CD]               │
│                          dC/dt = -μ·B/Y                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 2. Biotic Kinetics (Monod Model)

## 2.1 The Governing Equations

Biotic kinetics uses the **Monod model** for microbial growth:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MONOD KINETICS EQUATIONS                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  GROWTH RATE (Monod):                                                        │
│                                                                              │
│                            C                                                 │
│       μ = μ_max · ─────────────                                              │
│                      K_s + C                                                 │
│                                                                              │
│  where:                                                                      │
│       μ     = specific growth rate [1/s]                                     │
│       μ_max = maximum growth rate [1/s]                                      │
│       C     = substrate concentration [mol/L]                                │
│       K_s   = half-saturation constant [mol/L]                               │
│                                                                              │
│  BIOMASS CHANGE:                                                             │
│                                                                              │
│       dB/dt = (μ - k_decay) · B                                              │
│                                                                              │
│  where:                                                                      │
│       B       = biomass concentration [kg/m³]                                │
│       k_decay = decay/death rate [1/s]                                       │
│                                                                              │
│  SUBSTRATE CONSUMPTION (with yield):                                         │
│                                                                              │
│       dC/dt = -μ · B / Y                                                     │
│                                                                              │
│  where:                                                                      │
│       Y = yield coefficient [kg biomass / mol substrate]                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 2.2 How It Works in the Code

The kinetics is implemented in `defineKinetics.hh`:

```cpp
// File: defineKinetics.hh

namespace KineticParams {
    constexpr double mu_max   = 1.0;       // [1/s] maximum growth rate
    constexpr double Ks       = 1.0e-5;    // [mol/L] half saturation
    constexpr double Y        = 0.4;       // [-] yield coefficient
    constexpr double k_decay  = 1.0e-9;    // [1/s] decay rate
}

void defineRxnKinetics(
    std::vector<double> B,      // Biomass concentrations [kg/m³]
    std::vector<double> C,      // Substrate concentrations [mol/L]
    std::vector<double>& subsR, // Output: substrate rates [mol/L/s]
    std::vector<double>& bioR,  // Output: biomass rates [kg/m³/s]
    plb::plint mask             // Cell type
) {
    double biomass = B[0];
    double DOC = C[0];

    // Step 1: Calculate Monod term
    double monod = DOC / (Ks + DOC);        // Range: 0 to 1

    // Step 2: Calculate growth rate
    double mu = mu_max * monod;              // [1/s]
    double net_mu = mu - k_decay;            // Net growth rate

    // Step 3: Calculate rates
    double dB_dt = net_mu * biomass;         // [kg/m³/s]
    double dDOC_dt = -mu * biomass / Y;      // [mol/L/s] (negative = consumption)

    // Step 4: Output
    subsR[0] = dDOC_dt;  // Substrate rate
    bioR[0] = dB_dt;     // Biomass rate
}
```

## 2.3 The Monod Curve

```
                     Monod Kinetics: μ vs Substrate Concentration

    μ/μ_max │
       1.0  │                                    ___________________
            │                                ___/
            │                            ___/
            │                        ___/
       0.5  │ · · · · · · · · · ·/· · · · · · · · · · · · · · · · · ·
            │                  /│
            │                /  │
            │              /    │
            │            /      │
            │          /        │
       0.0  │________/__________|______________________________________
            0       K_s                                            [C]
                     │
                     └── At C = K_s, growth rate = 50% of maximum
```

## 2.4 Numerical Stability (Clamping)

The code prevents numerical instability by limiting substrate consumption:

```cpp
// Maximum fraction of substrate that can be consumed per timestep
constexpr double MAX_DOC_CONSUMPTION_FRACTION = 0.5;

double max_consumable_DOC = DOC * MAX_DOC_CONSUMPTION_FRACTION;
double max_consumption_rate = max_consumable_DOC / dt_kinetics;

if (-dDOC_dt > max_consumption_rate) {
    // Substrate-limited: reduce consumption
    dDOC_dt = -max_consumption_rate;

    // Recalculate biomass growth based on actual consumption
    double actual_mu = max_consumption_rate * Y / biomass;
    dB_dt = (actual_mu - k_decay) * biomass;
}
```

## 2.5 How to Customize Biotic Kinetics

Edit `defineKinetics.hh`:

```cpp
// Example: Two substrates with inhibition
void defineRxnKinetics(...) {
    double DOC = C[0];      // Carbon source
    double O2 = C[1];       // Oxygen (electron acceptor)
    double NH4 = C[2];      // Inhibitor (ammonia)

    // Dual Monod with inhibition
    double monod_DOC = DOC / (Ks_DOC + DOC);
    double monod_O2 = O2 / (Ks_O2 + O2);
    double inhibition = Ki / (Ki + NH4);  // Non-competitive inhibition

    double mu = mu_max * monod_DOC * monod_O2 * inhibition;

    // ... rest of calculations
}
```

---

# 3. Abiotic Kinetics (Chemical Reactions)

## 3.1 When to Use Abiotic Kinetics

Use abiotic kinetics for **chemical reactions WITHOUT microbes**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ABIOTIC KINETICS USE CASES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. FIRST-ORDER DECAY:                                                       │
│     • Radioactive decay:  ²³⁸U → ²³⁴Th + α                                  │
│     • Photodegradation:   Organic + hν → Products                           │
│     • Hydrolysis:         Ester + H₂O → Acid + Alcohol                      │
│                                                                              │
│     Rate law:  dA/dt = -k · [A]                                             │
│                                                                              │
│  2. BIMOLECULAR REACTIONS:                                                   │
│     • Oxidation:          Fe²⁺ + ¼O₂ + H⁺ → Fe³⁺ + ½H₂O                    │
│     • Precipitation:      Ca²⁺ + CO₃²⁻ → CaCO₃(s)                           │
│                                                                              │
│     Rate law:  dA/dt = -k · [A] · [B]                                       │
│                                                                              │
│  3. REVERSIBLE REACTIONS:                                                    │
│     • Equilibrium approach: A ⇌ B                                           │
│                                                                              │
│     Rate law:  dA/dt = -k_f · [A] + k_r · [B]                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 3.2 Enabling Abiotic Kinetics

In your XML file:

```xml
<simulation_mode>
    <biotic_mode>false</biotic_mode>          <!-- No microbes -->
    <enable_abiotic_kinetics>true</enable_abiotic_kinetics>  <!-- Enable chemical reactions -->
</simulation_mode>
```

## 3.3 The Code Implementation

File: `defineAbioticKinetics.hh`

```cpp
namespace AbioticParams {
    constexpr double k_decay_0 = 1.0e-5;   // [1/s] first-order decay
    constexpr double k_reaction = 1.0e-3;  // [L/mol/s] second-order rate
}

void defineAbioticRxnKinetics(
    std::vector<double> C,      // Substrate concentrations [mol/L]
    std::vector<double>& subsR, // Output: reaction rates [mol/L/s]
    plb::plint mask             // Cell type
) {
    // Initialize all rates to zero
    for (size_t i = 0; i < subsR.size(); ++i) {
        subsR[i] = 0.0;
    }

    // EXAMPLE: First-order decay of substrate 0
    // Reaction: A → products
    // Rate: dA/dt = -k · [A]

    if (C.size() > 0) {
        double A = C[0];
        double dA_dt = -k_decay_0 * A;

        // Stability clamp
        double max_rate = A * 0.5 / dt_kinetics;
        if (-dA_dt > max_rate) {
            dA_dt = -max_rate;
        }

        subsR[0] = dA_dt;
    }
}
```

## 3.4 Example: Bimolecular Reaction A + B → C

```cpp
// In defineAbioticKinetics.hh, add:

if (C.size() >= 3) {
    double A = C[0];  // Reactant A
    double B = C[1];  // Reactant B
    // C[2] is product C

    // Second-order reaction rate
    double rate = k_reaction * A * B;  // [mol/L/s]

    // Stability: don't consume more than 50% of limiting reactant
    double max_rate_A = A * 0.5 / dt_kinetics;
    double max_rate_B = B * 0.5 / dt_kinetics;
    double max_rate = std::min(max_rate_A, max_rate_B);
    if (rate > max_rate) {
        rate = max_rate;
    }

    // Stoichiometry: A + B → C
    subsR[0] = -rate;  // A consumed
    subsR[1] = -rate;  // B consumed
    subsR[2] = +rate;  // C produced
}
```

## 3.5 Data Flow for Abiotic Kinetics

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ABIOTIC KINETICS DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Lattice Order: [C0, C1, ..., Cn, dC0, dC1, ..., dCn, mask]                 │
│                 ├── Concentrations ──┤├── Rate changes ──┤                  │
│                                                                              │
│  Step 1: run_abiotic_kinetics processor                                     │
│          • Read C[i] from concentration lattices                            │
│          • Call defineAbioticRxnKinetics(C, subsR, mask)                    │
│          • Write dC = subsR[i] * dt to delta lattices                       │
│                                                                              │
│  Step 2: update_abiotic_rxnLattices processor                               │
│          • Read dC from delta lattices                                      │
│          • Add dC to concentration lattices: C_new = C_old + dC             │
│          • Reset delta lattices to zero                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 4. Cellular Automata (CA) Biofilm Expansion

## 4.1 The Problem: Biomass Exceeds Capacity

When biomass grows beyond the maximum density (B > B_max), it must be redistributed:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BIOFILM EXPANSION PROBLEM                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Before expansion:              After expansion:                             │
│                                                                              │
│  ┌─────┬─────┬─────┐           ┌─────┬─────┬─────┐                          │
│  │  0  │  0  │  0  │           │  0  │ 30  │  0  │                          │
│  ├─────┼─────┼─────┤           ├─────┼─────┼─────┤                          │
│  │  0  │ 150 │  0  │  ──────>  │ 30  │ 100 │ 30  │   B_max = 100           │
│  ├─────┼─────┼─────┤           ├─────┼─────┼─────┤                          │
│  │  0  │  0  │  0  │           │  0  │ 30  │  0  │                          │
│  └─────┴─────┴─────┘           └─────┴─────┴─────┘                          │
│                                                                              │
│  Excess = 150 - 100 = 50                                                    │
│  Distributed to 4 neighbors: 50/4 ≈ 12.5 each                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.2 Two CA Methods: "fraction" vs "half"

### Method 1: Fraction (Default)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CA METHOD: FRACTION (halfflag=0)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Algorithm:                                                                  │
│    1. If B > B_max, calculate excess = B - B_max                            │
│    2. Find ALL valid neighbors (not solid, not already full)                │
│    3. Distribute entire excess equally to neighbors                         │
│    4. One step per iteration                                                 │
│                                                                              │
│  Characteristics:                                                            │
│    • Faster spreading                                                        │
│    • More uniform distribution                                               │
│    • Less computational overhead                                             │
│                                                                              │
│  XML: <ca_type>fraction</ca_type>                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Method 2: Half

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CA METHOD: HALF (halfflag=1)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Algorithm:                                                                  │
│    1. If B > B_max, calculate excess = (B - B_max) / 2                      │
│    2. Find ONE random neighbor (not solid, prefers lower distance)          │
│    3. Push half of excess to that neighbor                                  │
│    4. May require multiple iterations to fully redistribute                  │
│                                                                              │
│  Characteristics:                                                            │
│    • More realistic fingering patterns                                       │
│    • Slower, more gradual spreading                                          │
│    • Better for studying biofilm morphology                                  │
│                                                                              │
│  XML: <ca_type>half</ca_type>                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 4.3 The Code Implementation

File: `complab3d_processors_part1.hh`

```cpp
// FRACTION method: pushExcessBiomass3D
if (bMt > Bmax) {
    // Find all valid neighbors
    for (each neighbor) {
        if (neighbor is not solid && not bounceback) {
            // Distribute evenly
            shove_bmass = (bMt - Bmax) / num_valid_neighbors;
            // Transfer to neighbor
            lattices[neighbor] += shove_bmass;
            lattices[current] -= shove_bmass;
        }
    }
}

// HALF method: halfPushExcessBiomass3D
if (bMt > Bmax) {
    T bMd = bMt * 0.5;  // Push only half

    // Step 1: Try to push to neighbor with capacity
    for (each neighbor in random order) {
        if (neighbor_biomass < Bmax) {
            T hold_capacity = Bmax - neighbor_biomass;
            T partial = min(bMd, hold_capacity);
            // Transfer partial amount
            lattices[neighbor] += partial;
            lattices[current] -= partial;
            bMd -= partial;
            if (bMd == 0) break;
        }
    }

    // Step 2: If still excess, use distance field to guide direction
    if (bMd > 0) {
        // Find neighbor with lowest distance from solid
        // Push remaining excess there (biofilm expands into pore)
    }
}
```

## 4.4 Distance Field for Biofilm Direction

The CA uses a **distance field** to guide expansion toward pore space:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        DISTANCE FIELD EXAMPLE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Geometry:                       Distance from solid:                        │
│  ┌─────┬─────┬─────┬─────┐      ┌─────┬─────┬─────┬─────┐                   │
│  │  S  │  S  │  S  │  S  │      │  0  │  0  │  0  │  0  │                   │
│  ├─────┼─────┼─────┼─────┤      ├─────┼─────┼─────┼─────┤                   │
│  │  S  │  P  │  P  │  P  │      │  0  │  1  │  2  │  3  │                   │
│  ├─────┼─────┼─────┼─────┤      ├─────┼─────┼─────┼─────┤                   │
│  │  S  │  P  │  P  │  P  │      │  0  │  1  │  2  │  3  │                   │
│  ├─────┼─────┼─────┼─────┤      ├─────┼─────┼─────┼─────┤                   │
│  │  S  │  S  │  S  │  S  │      │  0  │  0  │  0  │  0  │                   │
│  └─────┴─────┴─────┴─────┘      └─────┴─────┴─────┴─────┘                   │
│                                                                              │
│  S = Solid (distance = 0)                                                   │
│  P = Pore  (distance = min steps to reach solid)                            │
│                                                                              │
│  Biofilm prefers to expand to LOWER distance values (toward solid surface) │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 5. Equilibrium Solver (Newton-Raphson + Anderson)

## 5.1 Why Equilibrium Chemistry?

Some reactions are **much faster** than transport timescales:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    TIMESCALE COMPARISON                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Reaction Type              Timescale        Treatment                       │
│  ─────────────────────────────────────────────────────────                   │
│  H₂CO₃ ⇌ H⁺ + HCO₃⁻       microseconds     EQUILIBRIUM                     │
│  HCO₃⁻ ⇌ H⁺ + CO₃²⁻       microseconds     EQUILIBRIUM                     │
│  Ca²⁺ + CO₃²⁻ ⇌ CaCO₃     seconds-minutes  EQUILIBRIUM                     │
│  Microbial growth          hours-days       KINETICS                         │
│  Diffusion (1 cm)          hours-days       TRANSPORT                        │
│                                                                              │
│  Fast reactions → treat as instantaneous equilibrium                        │
│  Slow reactions → solve kinetically                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Mass Action Law

At equilibrium, species concentrations satisfy the **mass action law**:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         MASS ACTION LAW                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  For reaction:  aA + bB ⇌ cC + dD                                           │
│                                                                              │
│                    [C]^c · [D]^d                                             │
│           K_eq = ─────────────────                                           │
│                    [A]^a · [B]^b                                             │
│                                                                              │
│  In log form (better for numerical stability):                               │
│                                                                              │
│     log[C_i] = logK_i + Σⱼ S_ij · log[Component_j]                          │
│                                                                              │
│  where:                                                                      │
│     S_ij = stoichiometric coefficient                                        │
│     Component_j = primary species (H⁺, Ca²⁺, etc.)                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.3 The PCF Method (Positive Continuous Fraction)

The code uses the **PCF method** from Carrayrou et al. (2002):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PCF METHOD ALGORITHM                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Goal: Find ω = log[component] such that mass balance is satisfied          │
│                                                                              │
│  For each component j:                                                       │
│                                                                              │
│     S_reactive = Σᵢ (μᵢⱼ · Cᵢ)   for μᵢⱼ > 0 (species consuming component)│
│     S_product  = Tⱼ + Σᵢ |μᵢⱼ| · Cᵢ  for μᵢⱼ < 0 (species producing)       │
│                                                                              │
│  where Tⱼ = total concentration of component j                              │
│                                                                              │
│  PCF iteration:                                                              │
│                         1         S_product                                  │
│     ω_new = ω_old + ──────── · log₁₀(─────────────)                         │
│                       μ_min         S_reactive                               │
│                                                                              │
│  Converged when: |ω_new - ω_old| < tolerance                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.4 Anderson Acceleration

To speed up convergence, **Anderson Acceleration** is applied:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   ANDERSON ACCELERATION                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Fixed-point iteration:  x_{k+1} = G(x_k)                                   │
│                                                                              │
│  Anderson Acceleration uses HISTORY to accelerate:                           │
│                                                                              │
│  1. Store last m iterations: x_{k-m}, ..., x_{k} and residuals f_{k-m},...  │
│                                                                              │
│  2. Solve least-squares problem for optimal coefficients γ:                 │
│        minimize ||f_k - Σᵢ γᵢ (f_{k-i} - f_{k-i-1})||²                      │
│                                                                              │
│  3. Compute accelerated update:                                             │
│        x_{k+1} = x_k - Σᵢ γᵢ (x_{k-i} - x_{k-i-1})                         │
│                        + β (f_k - Σᵢ γᵢ (f_{k-i} - f_{k-i-1}))             │
│                                                                              │
│  Parameters:                                                                 │
│     m = andersonDepth (default: 4) - history length                         │
│     β = beta (default: 1.0) - damping factor                                │
│                                                                              │
│  Benefit: Typically 2-10x faster convergence than plain iteration           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 5.5 Code Implementation

File: `complab3d_processors_part4_eqsolver.hh`

```cpp
std::vector<T> solve_equilibrium_anderson(
    const std::vector<T>& initial_species_conc,
    const std::vector<T>& T_total  // Total concentrations
) {
    // Initialize: ω = log10([component])
    std::vector<T> omega(nc);
    for (j = 0; j < nc; ++j) {
        omega[j] = log10(initial_conc[j]);
    }

    // Main iteration loop
    for (iter = 0; iter < maxIterations; ++iter) {

        // Step 1: Calculate PCF residual
        std::vector<T> f_k = pcf_residual(omega, T_total);

        // Step 2: Check convergence
        if (norm(f_k) < tolerance) {
            return calc_species(omega);  // Converged!
        }

        // Step 3: Anderson Acceleration
        if (history.size() >= andersonDepth) {
            // QR decomposition of residual differences
            qr_decomposition(Delta_F, Q, R, condNum);

            // Solve least-squares for γ
            gamma = solve_upper_triangular(R, Q^T * f_k);

            // Accelerated update
            omega_new = omega - Σ γᵢ Δx_i + β (f_k - Σ γᵢ Δf_i);
        } else {
            // Simple fixed-point iteration
            omega_new = omega + f_k;
        }

        omega = omega_new;
    }
}
```

## 5.6 XML Configuration

```xml
<equilibrium>
    <enabled>true</enabled>
    <species_names>H+ HCO3- CO32- Ca2+ CaHCO3+ CaCO3(aq)</species_names>
    <component_names>H+ HCO3- Ca2+</component_names>
    <logK>0.0 -10.33 0.0 1.11 3.22</logK>

    <!-- Stoichiometry matrix: each row = species, each column = component -->
    <stoichiometry>
        1 0 0      <!-- H+ -->
        0 1 0      <!-- HCO3- -->
        -1 1 0     <!-- CO32-: logK + (-1)*log[H+] + 1*log[HCO3-] -->
        0 0 1      <!-- Ca2+ -->
        0 1 1      <!-- CaHCO3+: logK + 1*log[HCO3-] + 1*log[Ca2+] -->
        -1 1 1     <!-- CaCO3(aq) -->
    </stoichiometry>

    <!-- Solver parameters -->
    <max_iterations>200</max_iterations>
    <tolerance>1e-8</tolerance>
    <anderson_depth>4</anderson_depth>
</equilibrium>
```

---

# 6. Data Flow in the Simulation Loop

## 6.1 Complete Simulation Cycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MAIN SIMULATION LOOP (one iteration)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  START: Lattices contain C(t), B(t), velocity u                             │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 1: LBM COLLISION                                                │    │
│  │   • For each substrate lattice: f_out = f_in - (f_in - f_eq)/τ      │    │
│  │   • Computes diffusion and advection implicitly                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│                           v                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 2: KINETICS (if enable_kinetics=true OR enable_abiotic_kinetics)│    │
│  │   • Biotic: run_kinetics → defineRxnKinetics → dC, dB               │    │
│  │   • Abiotic: run_abiotic_kinetics → defineAbioticRxnKinetics → dC   │    │
│  │   • Update: C += dC·dt,  B += dB·dt                                 │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│                           v                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 3: EQUILIBRIUM (if equilibrium.enabled=true)                    │    │
│  │   • run_equilibrium_biotic → solve_equilibrium_anderson             │    │
│  │   • Adjusts all equilibrium species to satisfy mass action          │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│                           v                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 4: CA BIOFILM EXPANSION (if biotic_mode=true AND CA microbes)   │    │
│  │   • Check if B > B_max anywhere                                      │    │
│  │   • pushExcessBiomass3D OR halfPushExcessBiomass3D                  │    │
│  │   • Update geometry if biofilm enters new cells                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│                           v                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │ STEP 5: LBM STREAMING                                                │    │
│  │   • f_i(x+e_i·dt, t+dt) = f_i(x, t)                                 │    │
│  │   • Propagates distributions to neighbors                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                           │                                                  │
│                           v                                                  │
│  END: Lattices contain C(t+dt), B(t+dt)                                     │
│       Increment iteration counter, check convergence                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## 6.2 Lattice Organization

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LATTICE POINTER ORGANIZATION                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  BIOTIC MODE (with kinetics):                                               │
│    kinetics_lattices = [C0, C1, ..., Cn, B0, B1, ..., Bm,                   │
│                         dC0, dC1, ..., dCn, dB0, dB1, ..., dBm, mask]       │
│                                                                              │
│    Where:                                                                    │
│      C0...Cn = substrate concentration lattices                              │
│      B0...Bm = biomass concentration lattices                               │
│      dC, dB  = rate change lattices (temporary storage)                     │
│      mask    = geometry/material number lattice                             │
│                                                                              │
│  ABIOTIC MODE (with abiotic kinetics):                                      │
│    abiotic_lattices = [C0, C1, ..., Cn, dC0, dC1, ..., dCn, mask]          │
│                                                                              │
│  CA EXPANSION:                                                               │
│    ca_lattices = [B0, B1, ..., Bm, copy_B0, ..., copy_Bm,                   │
│                   total_B, mask, distance]                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

# 7. Complete Examples

## 7.1 Example: Aerobic Respiration with Biofilm

**Reaction:** DOC + O₂ → CO₂ + Biomass (Monod kinetics)

### defineKinetics.hh:

```cpp
namespace KineticParams {
    constexpr double mu_max   = 1.0e-4;    // [1/s] max growth rate
    constexpr double Ks_DOC   = 1.0e-4;    // [mol/L] DOC half-saturation
    constexpr double Ks_O2    = 3.0e-5;    // [mol/L] O2 half-saturation
    constexpr double Y        = 0.3;       // [kg/mol] yield
    constexpr double k_decay  = 1.0e-6;    // [1/s] decay rate
}

void defineRxnKinetics(
    std::vector<double> B,
    std::vector<double> C,
    std::vector<double>& subsR,
    std::vector<double>& bioR,
    plb::plint mask
) {
    double biomass = B[0];
    double DOC = C[0];     // Substrate 0 = DOC
    double O2 = C[1];      // Substrate 1 = O2

    // Dual Monod kinetics
    double monod_DOC = DOC / (Ks_DOC + DOC);
    double monod_O2 = O2 / (Ks_O2 + O2);
    double mu = mu_max * monod_DOC * monod_O2;

    // Rates
    double dB_dt = (mu - k_decay) * biomass;
    double dDOC_dt = -mu * biomass / Y;
    double dO2_dt = -mu * biomass / Y * 1.0;  // Stoichiometry: 1 mol O2 per mol DOC
    double dCO2_dt = mu * biomass / Y;

    subsR[0] = dDOC_dt;  // DOC consumption
    subsR[1] = dO2_dt;   // O2 consumption
    subsR[2] = dCO2_dt;  // CO2 production
    bioR[0] = dB_dt;     // Biomass growth
}
```

### XML Configuration:

```xml
<chemistry>
    <number_of_substrates>3</number_of_substrates>

    <substrate0>
        <name_of_substrates>DOC</name_of_substrates>
        <initial_concentration>1.0e-3</initial_concentration>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <left_boundary_condition>1.0e-3</left_boundary_condition>
        <right_boundary_type>Neumann</right_boundary_type>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate0>

    <substrate1>
        <name_of_substrates>O2</name_of_substrates>
        <initial_concentration>2.5e-4</initial_concentration>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <left_boundary_condition>2.5e-4</left_boundary_condition>
        <right_boundary_type>Neumann</right_boundary_type>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate1>

    <substrate2>
        <name_of_substrates>CO2</name_of_substrates>
        <initial_concentration>0.0</initial_concentration>
        <left_boundary_type>Neumann</left_boundary_type>
        <left_boundary_condition>0.0</left_boundary_condition>
        <right_boundary_type>Neumann</right_boundary_type>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate2>
</chemistry>

<microbiology>
    <number_of_microbes>1</number_of_microbes>
    <maximum_biomass_density>100.0</maximum_biomass_density>
    <ca_type>half</ca_type>

    <microbe0>
        <name_of_microbes>Aerobic_Heterotroph</name_of_microbes>
        <solver_type>CA</solver_type>
        <reaction_type>kinetics</reaction_type>
        <initial_densities>50.0</initial_densities>
    </microbe0>
</microbiology>
```

## 7.2 Example: Radioactive Decay (Abiotic)

**Reaction:** ²³⁸U → ²³⁴Th + α (first-order decay)

### defineAbioticKinetics.hh:

```cpp
namespace AbioticParams {
    // Uranium-238 half-life = 4.47 billion years
    // k = ln(2) / t_half = 4.92e-18 [1/s]
    // For demonstration, use faster decay:
    constexpr double k_decay_U238 = 1.0e-6;  // [1/s]
}

void defineAbioticRxnKinetics(
    std::vector<double> C,
    std::vector<double>& subsR,
    plb::plint mask
) {
    // C[0] = U-238 concentration
    // C[1] = Th-234 concentration (daughter product)

    if (C.size() >= 2) {
        double U238 = C[0];
        double Th234 = C[1];

        // First-order decay
        double decay_rate = k_decay_U238 * U238;

        // U-238 decreases, Th-234 increases (1:1 stoichiometry)
        subsR[0] = -decay_rate;  // U-238 consumed
        subsR[1] = +decay_rate;  // Th-234 produced
    }
}
```

### XML Configuration:

```xml
<simulation_mode>
    <biotic_mode>false</biotic_mode>
    <enable_abiotic_kinetics>true</enable_abiotic_kinetics>
</simulation_mode>

<chemistry>
    <number_of_substrates>2</number_of_substrates>

    <substrate0>
        <name_of_substrates>U238</name_of_substrates>
        <initial_concentration>1.0e-6</initial_concentration>
        <left_boundary_type>Dirichlet</left_boundary_type>
        <left_boundary_condition>1.0e-6</left_boundary_condition>
        <right_boundary_type>Neumann</right_boundary_type>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate0>

    <substrate1>
        <name_of_substrates>Th234</name_of_substrates>
        <initial_concentration>0.0</initial_concentration>
        <left_boundary_type>Neumann</left_boundary_type>
        <left_boundary_condition>0.0</left_boundary_condition>
        <right_boundary_type>Neumann</right_boundary_type>
        <right_boundary_condition>0.0</right_boundary_condition>
    </substrate1>
</chemistry>

<microbiology>
    <number_of_microbes>0</number_of_microbes>
</microbiology>
```

---

# Summary

| Feature | Code File | Key Function | XML Option |
|---------|-----------|--------------|------------|
| Biotic kinetics | defineKinetics.hh | defineRxnKinetics() | enable_kinetics |
| Abiotic kinetics | defineAbioticKinetics.hh | defineAbioticRxnKinetics() | enable_abiotic_kinetics |
| CA expansion | complab3d_processors_part1.hh | pushExcessBiomass3D / halfPushExcessBiomass3D | ca_type |
| Equilibrium | complab3d_processors_part4_eqsolver.hh | solve_equilibrium_anderson() | equilibrium.enabled |

For questions or issues, contact the Meile Lab at University of Georgia.
