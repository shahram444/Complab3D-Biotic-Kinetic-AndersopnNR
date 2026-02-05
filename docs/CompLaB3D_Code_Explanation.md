# CompLaB3D Code Explanation
## Understanding the Biogeochemical Reactive Transport Simulator

**Version:** 2.0 (Biotic-Kinetic-Anderson-NR)
**Author:** Shahram Asgari
**Advisor:** Dr. Christof Meile
**Institution:** University of Georgia

---

# Table of Contents

1. [Overview: What Does CompLaB3D Do?](#1-overview)
2. [Biotic vs Abiotic Modes](#2-biotic-vs-abiotic-modes)
3. [The Kinetics System](#3-the-kinetics-system)
4. [Cellular Automata (CA) for Biofilm](#4-cellular-automata-ca-for-biofilm)
5. [Equilibrium Chemistry Solver](#5-equilibrium-chemistry-solver)
6. [Code Flow: Step by Step](#6-code-flow-step-by-step)
7. [Data Structures and Lattices](#7-data-structures-and-lattices)

---

# 1. Overview: What Does CompLaB3D Do?

CompLaB3D simulates how chemicals move and react in porous materials (like soil, sediments, or rock) when microorganisms are present. The code solves several coupled physical and biological processes:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                        WHAT CompLaB3D SIMULATES                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   1. FLUID FLOW                                                               ║
║      Water moves through pore spaces between solid grains                     ║
║      Solved using: Lattice Boltzmann Method (LBM) with D3Q19 stencil         ║
║      Equation: Navier-Stokes (incompressible)                                 ║
║                                                                               ║
║   2. SOLUTE TRANSPORT                                                         ║
║      Dissolved chemicals are carried by flow (advection) and spread          ║
║      by random motion (diffusion)                                             ║
║      Solved using: LBM with D3Q7 stencil                                      ║
║      Equation: Advection-Diffusion                                            ║
║                                                                               ║
║   3. MICROBIAL KINETICS                                                       ║
║      Bacteria consume substrates and grow                                     ║
║      Solved using: Monod kinetics (source/sink terms)                         ║
║      Equation: Monod growth model                                             ║
║                                                                               ║
║   4. BIOFILM EXPANSION                                                        ║
║      When bacteria grow too dense, they spread to neighbors                   ║
║      Solved using: Cellular Automata (CA)                                     ║
║      Rule: Redistribute excess biomass                                        ║
║                                                                               ║
║   5. EQUILIBRIUM CHEMISTRY                                                    ║
║      Fast chemical reactions reach equilibrium instantly                      ║
║      Solved using: Newton-Raphson with Anderson Acceleration                  ║
║      Equation: Mass action law                                                ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## Why Use Lattice Boltzmann?

Traditional methods solve differential equations on a grid. LBM instead simulates particle distributions moving on a lattice:

```
TRADITIONAL METHOD (Finite Difference):
  Solve: ∂C/∂t = D∇²C - u·∇C
  Discretize derivatives directly on grid points

LATTICE BOLTZMANN METHOD:
  Track particle distribution functions f_i(x,t)
  Particles stream along lattice links and collide at nodes
  Macroscopic quantities emerge from distributions:
    Concentration: C = Σf_i
    Flux: J = Σf_i * c_i

ADVANTAGES OF LBM:
  ✓ Complex geometries handled naturally
  ✓ Parallelizes efficiently
  ✓ No need to track moving boundaries
  ✓ Stable for high Peclet numbers
```

---

# 2. Biotic vs Abiotic Modes

The code supports two fundamental simulation modes controlled by the `<biotic_mode>` XML option.

## 2.1 What is Abiotic Mode?

**Abiotic** means "without life." In abiotic mode:
- No microorganisms are simulated
- No biomass growth or decay
- Only physical transport (advection + diffusion)
- Optionally: equilibrium chemistry

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           ABIOTIC MODE                                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   WHAT RUNS:                         WHAT IS SKIPPED:                         ║
║   ────────────                       ────────────────                         ║
║   ✓ Navier-Stokes flow               ✗ Kinetics calculations                  ║
║   ✓ Advection-diffusion transport    ✗ Biomass lattices                       ║
║   ✓ Equilibrium chemistry (optional) ✗ CA expansion                           ║
║                                      ✗ Microbe XML parsing                    ║
║                                                                               ║
║   USE CASES:                                                                  ║
║   ──────────                                                                  ║
║   • Testing transport without biology                                         ║
║   • Pure geochemistry simulations                                             ║
║   • Debugging flow field                                                      ║
║   • Studying conservative tracers                                             ║
║   • Validating against analytical solutions                                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

**Code location:** `src/complab_functions.hh`, lines 636-686

When `biotic_mode=false`:
1. `num_of_microbes` is set to 0
2. Microbiology XML section is skipped
3. Kinetics is automatically disabled
4. No biomass lattices are created

## 2.2 What is Biotic Mode?

**Biotic** means "with life." In biotic mode:
- Microorganisms are simulated
- Bacteria consume substrates and grow
- Biofilm can expand via Cellular Automata
- Full reactive transport

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           BIOTIC MODE                                         ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   FULL SIMULATION WITH:                                                       ║
║   ─────────────────────                                                       ║
║   ✓ Navier-Stokes flow                                                        ║
║   ✓ Advection-diffusion transport                                             ║
║   ✓ Monod kinetics (substrate consumption, biomass growth)                    ║
║   ✓ Cellular Automata biofilm expansion                                       ║
║   ✓ Flow field updates when biofilm grows                                     ║
║   ✓ Equilibrium chemistry (optional)                                          ║
║                                                                               ║
║   MICROBE TYPES SUPPORTED:                                                    ║
║   ────────────────────────                                                    ║
║   • Sessile (attached biofilm) - uses CA solver                               ║
║   • Planktonic (free-floating) - uses LBM transport                           ║
║   • Multiple species simultaneously                                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 2.3 The enable_kinetics Option

Even in biotic mode, you can disable kinetics:

```
biotic_mode = true, enable_kinetics = true
  → Full simulation: transport + kinetics + CA + equilibrium

biotic_mode = true, enable_kinetics = false
  → Biomass exists but doesn't grow
  → Useful for: testing equilibrium with static biofilm

biotic_mode = false
  → enable_kinetics is forced to false
  → Pure transport (no biology at all)
```

**Code location:** `src/complab.cpp`, line 792-797

```cpp
// Kinetics (only if enable_kinetics is true)
if (enable_kinetics && kns_count > 0) {
    applyProcessingFunctional(new run_kinetics<T,RXNDES>(...), ...);
}
```

---

# 3. The Kinetics System

## 3.1 What is Monod Kinetics?

Monod kinetics describes how microorganisms grow based on substrate availability. It's the microbial equivalent of Michaelis-Menten enzyme kinetics.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                         MONOD KINETICS                                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   THE MONOD EQUATION:                                                         ║
║   ───────────────────                                                         ║
║                         S                                                     ║
║       μ = μ_max × ─────────                                                   ║
║                    K_s + S                                                    ║
║                                                                               ║
║   WHERE:                                                                      ║
║       μ      = specific growth rate [1/s]                                     ║
║       μ_max  = maximum growth rate when S >> K_s [1/s]                        ║
║       S      = substrate concentration [mol/L]                                ║
║       K_s    = half-saturation constant [mol/L]                               ║
║                (concentration where μ = μ_max/2)                              ║
║                                                                               ║
║   GRAPHICALLY:                                                                ║
║                                                                               ║
║   μ ▲                                                                         ║
║     │                    _______________  μ_max                               ║
║     │                 __/                                                     ║
║     │              __/                                                        ║
║     │           __/                                                           ║
║ μ/2 │........./.......                                                        ║
║     │        /│                                                               ║
║     │      _/ │                                                               ║
║     │    _/   │                                                               ║
║     │___/     │                                                               ║
║     └─────────┼────────────────────────▶ S                                    ║
║               K_s                                                             ║
║                                                                               ║
║   INTERPRETATION:                                                             ║
║   • At low S (S << K_s): Growth is limited by substrate (first-order)         ║
║   • At high S (S >> K_s): Growth is at maximum rate (zero-order)              ║
║   • K_s represents the "affinity" - lower K_s = better at low concentrations  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 3.2 Complete Kinetics Equations

The full kinetics system couples substrate consumption with biomass growth:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    COUPLED KINETICS EQUATIONS                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   BIOMASS GROWTH:                                                             ║
║   ───────────────                                                             ║
║       dB              S                                                       ║
║       ── = μ_max × ─────── × B  -  k_decay × B                                ║
║       dt           K_s + S                                                    ║
║            \_________  _________/     \______  ______/                        ║
║                      \/                      \/                               ║
║                   Growth                   Decay                              ║
║                                                                               ║
║   WHERE:                                                                      ║
║       B        = biomass concentration [kg/m³]                                ║
║       k_decay  = first-order decay rate [1/s]                                 ║
║                                                                               ║
║                                                                               ║
║   SUBSTRATE CONSUMPTION:                                                      ║
║   ──────────────────────                                                      ║
║       dS        1           S                                                 ║
║       ── = - ───── × μ_max × ─────── × B                                      ║
║       dt       Y          K_s + S                                             ║
║                                                                               ║
║   WHERE:                                                                      ║
║       Y = yield coefficient [kg biomass / mol substrate]                      ║
║           (how much biomass is produced per substrate consumed)               ║
║                                                                               ║
║                                                                               ║
║   RELATIONSHIP:                                                               ║
║   ─────────────                                                               ║
║       dS        1    dB                                                       ║
║       ── = - ───── × ── + decay contribution                                  ║
║       dt       Y     dt                                                       ║
║                                                                               ║
║   This ensures mass balance: substrate consumed = biomass produced / Y        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 3.3 Multiple Substrates (Dual Monod)

When growth depends on multiple substrates (e.g., carbon AND oxygen):

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    DUAL MONOD KINETICS                                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   For growth requiring TWO substrates (e.g., DOC and O2):                     ║
║                                                                               ║
║       dB              S_DOC              S_O2                                 ║
║       ── = μ_max × ──────────── × ──────────── × B  -  k_decay × B            ║
║       dt           K_DOC + S_DOC   K_O2 + S_O2                                ║
║                                                                               ║
║   MULTIPLICATIVE TERMS:                                                       ║
║   • Both substrates must be present for growth                                ║
║   • Either being zero stops growth completely                                 ║
║   • Each substrate has its own K_s value                                      ║
║                                                                               ║
║   EXAMPLE - Aerobic heterotrophy:                                             ║
║   ───────────────────────────────                                             ║
║       DOC + O2 → CO2 + H2O + Biomass                                          ║
║                                                                               ║
║       Substrate 0: DOC (dissolved organic carbon)                             ║
║       Substrate 1: O2 (dissolved oxygen)                                      ║
║                                                                               ║
║       Growth limited by BOTH - whichever is lower relative to its K_s         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 3.4 How Kinetics is Implemented in Code

**File:** `defineKinetics.hh` (or `defineKinetics_planktonic.hh`)

```cpp
// STEP 1: Get current concentrations
T DOC = lattices[0]->get(iX,iY,iZ).computeDensity();  // Substrate
T B   = lattices[N]->get(iX,iY,iZ).computeDensity();  // Biomass

// STEP 2: Calculate Monod term
T monod = DOC / (Ks + DOC);

// STEP 3: Calculate growth rate
T mu = mu_max * monod;

// STEP 4: Calculate change in biomass
T dB = (mu - k_decay) * B * dt;

// STEP 5: Calculate change in substrate
T dS = -dB / Y;

// STEP 6: Store changes for later application
dC_lattice->get(iX,iY,iZ).setDensity(dS);
dB_lattice->get(iX,iY,iZ).setDensity(dB);
```

**Main loop location:** `src/complab.cpp`, lines 790-803

---

# 4. Cellular Automata (CA) for Biofilm

## 4.1 Why Do We Need CA?

When bacteria grow, biomass increases. But there's a physical limit to how much biomass can fit in a single voxel. CA handles this by redistributing excess biomass to neighbors.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    THE BIOFILM EXPANSION PROBLEM                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   SITUATION:                                                                  ║
║   ──────────                                                                  ║
║   A voxel has biomass B. After kinetics: B_new = B + dB                       ║
║                                                                               ║
║   PROBLEM:                                                                    ║
║   ────────                                                                    ║
║   What if B_new > B_max (maximum biomass density)?                            ║
║                                                                               ║
║   EXAMPLE:                                                                    ║
║   ────────                                                                    ║
║   B_max = 100 kg/m³                                                           ║
║   Current B = 98 kg/m³                                                        ║
║   Growth dB = 5 kg/m³                                                         ║
║   B_new = 103 kg/m³  ← EXCEEDS LIMIT!                                         ║
║                                                                               ║
║   SOLUTION: Cellular Automata                                                 ║
║   ──────────────────────────                                                  ║
║   1. Keep B_max in the cell (100 kg/m³)                                       ║
║   2. Redistribute excess (3 kg/m³) to neighbors                               ║
║   3. If neighbors also overflow, continue redistributing                      ║
║                                                                               ║
║   PHYSICAL MEANING:                                                           ║
║   ─────────────────                                                           ║
║   Biofilm "pushes" outward as it grows, colonizing new pore space             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 4.2 CA Method: FRACTION

The `fraction` method distributes excess equally to all 6 face neighbors (in 3D):

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    CA METHOD: FRACTION                                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ALGORITHM:                                                                  ║
║   ──────────                                                                  ║
║   1. Excess = B - B_max                                                       ║
║   2. Each of 6 neighbors receives: Excess / 6                                 ║
║   3. Cell is set to B_max                                                     ║
║                                                                               ║
║   VISUALIZATION (2D slice, 4 neighbors shown):                                ║
║   ────────────────────────────────────────────                                ║
║                                                                               ║
║   BEFORE:                           AFTER:                                    ║
║   ┌─────┬─────┬─────┐              ┌─────┬─────┬─────┐                        ║
║   │     │  50 │     │              │     │  52 │     │                        ║
║   │     │     │     │              │     │ +2  │     │                        ║
║   ├─────┼─────┼─────┤              ├─────┼─────┼─────┤                        ║
║   │  40 │ 108 │  30 │    ───►      │  42 │ 100 │  32 │                        ║
║   │     │ >MAX│     │              │ +2  │ MAX │ +2  │                        ║
║   ├─────┼─────┼─────┤              ├─────┼─────┼─────┤                        ║
║   │     │  60 │     │              │     │  62 │     │                        ║
║   │     │     │     │              │     │ +2  │     │                        ║
║   └─────┴─────┴─────┘              └─────┴─────┴─────┘                        ║
║                                                                               ║
║   Excess = 108 - 100 = 8 kg/m³                                                ║
║   Each of 4 neighbors gets: 8/4 = 2 kg/m³                                     ║
║   (In 3D with 6 neighbors: 8/6 = 1.33 kg/m³ each)                             ║
║                                                                               ║
║   CHARACTERISTICS:                                                            ║
║   ────────────────                                                            ║
║   ✓ Symmetric distribution - no preferred direction                           ║
║   ✓ Produces smooth, rounded biofilm shapes                                   ║
║   ✗ May require many iterations if excess is large                            ║
║   ✗ Can spread biomass to areas far from nutrients                            ║
║                                                                               ║
║   BEST FOR:                                                                   ║
║   ─────────                                                                   ║
║   • Studying detailed biofilm morphology                                      ║
║   • When smooth expansion is desired                                          ║
║   • Academic/research simulations                                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 4.3 CA Method: HALF

The `half` method is directionally biased - it sends biomass toward open pore space:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    CA METHOD: HALF                                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ALGORITHM:                                                                  ║
║   ──────────                                                                  ║
║   1. Excess = B - B_max                                                       ║
║   2. Find neighbor with SHORTEST DISTANCE to open pore                        ║
║   3. Send HALF of excess to that neighbor                                     ║
║   4. Cell keeps: B_max + Excess/2                                             ║
║   5. Repeat until stable                                                      ║
║                                                                               ║
║   VISUALIZATION (with distance field):                                        ║
║   ─────────────────────────────────────                                       ║
║                                                                               ║
║   Distance to pore (lower = closer to open space):                            ║
║   ┌─────┬─────┬─────┐                                                         ║
║   │ d=3 │ d=2 │ d=1 │  ← Closer to pore                                       ║
║   ├─────┼─────┼─────┤                                                         ║
║   │ d=4 │ 108 │ d=2 │  ← Center cell overflows                                ║
║   ├─────┼─────┼─────┤                                                         ║
║   │ d=5 │ d=4 │ d=3 │  ← Farther from pore                                    ║
║   └─────┴─────┴─────┘                                                         ║
║                                                                               ║
║   RESULT:                                                                     ║
║   ┌─────┬─────┬─────┐                                                         ║
║   │     │     │ +4  │  ← Neighbor with d=1 receives half                      ║
║   ├─────┼─────┼─────┤                                                         ║
║   │     │ 104 │     │  ← Still >B_max, will redistribute again                ║
║   ├─────┼─────┼─────┤                                                         ║
║   │     │     │     │                                                         ║
║   └─────┴─────┴─────┘                                                         ║
║                                                                               ║
║   CHARACTERISTICS:                                                            ║
║   ────────────────                                                            ║
║   ✓ Biofilm grows TOWARD nutrients (biologically realistic)                   ║
║   ✓ Faster stabilization (fewer iterations)                                   ║
║   ✓ Efficient for large simulations                                           ║
║   ✗ Can create directional bias artifacts                                     ║
║   ✗ Less smooth biofilm boundaries                                            ║
║                                                                               ║
║   BEST FOR:                                                                   ║
║   ─────────                                                                   ║
║   • Production simulations                                                    ║
║   • When computation time matters                                             ║
║   • Biologically realistic expansion patterns                                 ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 4.4 CA Implementation in Code

**File:** `src/complab3d_processors.hh`

The CA runs after kinetics updates biomass:

```cpp
// STEP 1: Update mask and check for overflow
applyProcessingFunctional(new updateLocalMaskNtotalLattices3D<T,RXNDES>(...), ...);

// STEP 2: Check global maximum
T globalBmax = computeMax(*computeDensity(totalbFilmLattice));

// STEP 3: Redistribute if overflow exists
while (globalBmax - max_bMassRho > thrd) {

    if (halfflag == 0) {
        // FRACTION method: equal distribution to all neighbors
        applyProcessingFunctional(new pushExcessBiomass3D<T,RXNDES>(...), ...);
    }
    else {
        // HALF method: directional toward pore
        applyProcessingFunctional(new halfPushExcessBiomass3D<T,RXNDES>(...), ...);
    }

    // Neighbors collect pushed biomass
    applyProcessingFunctional(new pullExcessBiomass3D<T,RXNDES>(...), ...);

    // Check if still overflowing
    globalBmax = computeMax(*computeDensity(totalbFilmLattice));
}
```

**Code location:** `src/complab.cpp`, lines 878-899

---

# 5. Equilibrium Chemistry Solver

## 5.1 What is Equilibrium Chemistry?

Some chemical reactions are very fast compared to transport. Instead of tracking them kinetically (which would require tiny timesteps), we assume they reach equilibrium instantly.

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    EQUILIBRIUM vs KINETIC REACTIONS                           ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   KINETIC REACTIONS (slow - tracked explicitly):                              ║
║   ──────────────────────────────────────────────                              ║
║   • Microbial metabolism: DOC → CO2 + Biomass                                 ║
║   • Mineral dissolution: Cite Cite → Ca²⁺ + CO₃²⁻ (slow)                      ║
║   • Timescale: seconds to days                                                ║
║                                                                               ║
║   EQUILIBRIUM REACTIONS (fast - assumed instantaneous):                       ║
║   ─────────────────────────────────────────────────────                       ║
║   • Acid-base: H₂CO₃ ⇌ HCO₃⁻ + H⁺                                             ║
║   • Complexation: Ca²⁺ + CO₃²⁻ ⇌ CaCO₃(aq)                                    ║
║   • Timescale: microseconds to milliseconds                                   ║
║                                                                               ║
║   WHY TREAT THEM DIFFERENTLY?                                                 ║
║   ────────────────────────────                                                ║
║   If we tracked acid-base kinetically with dt = 0.01 s:                       ║
║      Reaction half-life ≈ 10⁻⁶ s                                              ║
║      Ratio = 0.01 / 10⁻⁶ = 10,000                                             ║
║      The reaction would "overshoot" by 10,000×!                               ║
║                                                                               ║
║   SOLUTION: Assume equilibrium is reached at each timestep                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 5.2 Mass Action Law

Equilibrium is described by the mass action law:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    MASS ACTION LAW                                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   For reaction:  aA + bB ⇌ cC + dD                                            ║
║                                                                               ║
║                   [C]^c × [D]^d                                               ║
║       K = ─────────────────────                                               ║
║                   [A]^a × [B]^b                                               ║
║                                                                               ║
║   WHERE:                                                                      ║
║       K = equilibrium constant (temperature-dependent)                        ║
║       [X] = concentration of species X                                        ║
║       a,b,c,d = stoichiometric coefficients                                   ║
║                                                                               ║
║   EXAMPLE - Carbonic acid first dissociation:                                 ║
║   ──────────────────────────────────────────────                              ║
║       H₂CO₃ ⇌ HCO₃⁻ + H⁺                                                      ║
║                                                                               ║
║              [HCO₃⁻] × [H⁺]                                                   ║
║       K₁ = ─────────────────  = 10^(-6.35) at 25°C                            ║
║                [H₂CO₃]                                                        ║
║                                                                               ║
║       pKa₁ = 6.35                                                             ║
║                                                                               ║
║   This means:                                                                 ║
║   • At pH 6.35: [HCO₃⁻] = [H₂CO₃]                                             ║
║   • At pH < 6.35: H₂CO₃ dominates                                             ║
║   • At pH > 6.35: HCO₃⁻ dominates                                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 5.3 The Carbonate System

The carbonate system is a common application of equilibrium chemistry:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    THE CARBONATE SYSTEM                                       ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   CO₂ dissolves in water and forms carbonic acid, which dissociates:          ║
║                                                                               ║
║       CO₂(aq) + H₂O ⇌ H₂CO₃ ⇌ HCO₃⁻ + H⁺ ⇌ CO₃²⁻ + 2H⁺                       ║
║                                                                               ║
║   TWO EQUILIBRIA:                                                             ║
║   ───────────────                                                             ║
║                                                                               ║
║   Reaction 1: H₂CO₃ ⇌ HCO₃⁻ + H⁺                                              ║
║       K₁ = 10^(-6.35)    (pKa₁ = 6.35)                                        ║
║                                                                               ║
║   Reaction 2: HCO₃⁻ ⇌ CO₃²⁻ + H⁺                                              ║
║       K₂ = 10^(-10.33)   (pKa₂ = 10.33)                                       ║
║                                                                               ║
║   SPECIATION DIAGRAM:                                                         ║
║   ───────────────────                                                         ║
║                                                                               ║
║   Fraction ▲                                                                  ║
║      1.0   │     H₂CO₃          HCO₃⁻           CO₃²⁻                         ║
║            │    ──────╲       ╱──────╲       ╱──────                          ║
║            │           ╲     ╱        ╲     ╱                                 ║
║      0.5   │            ╲   ╱          ╲   ╱                                  ║
║            │             ╲ ╱            ╲ ╱                                   ║
║            │              ╳              ╳                                    ║
║            │             ╱ ╲            ╱ ╲                                   ║
║      0.0   │────────────╱───╲──────────╱───╲────────                          ║
║            └────────────┼────┼─────────┼────┼────────▶ pH                     ║
║                         4   6.35       8   10.33   12                         ║
║                             pKa₁           pKa₂                               ║
║                                                                               ║
║   CONNECTION TO BIOLOGY:                                                      ║
║   ──────────────────────                                                      ║
║   When microbes respire: DOC + O₂ → CO₂                                       ║
║   CO₂ enters the carbonate system, lowering pH                                ║
║   This affects mineral solubility, metal speciation, etc.                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 5.4 Newton-Raphson Method

Finding equilibrium concentrations requires solving nonlinear equations. We use Newton-Raphson iteration:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    NEWTON-RAPHSON METHOD                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   PROBLEM:                                                                    ║
║   ────────                                                                    ║
║   Given total concentrations (T_HCO3, T_H), find species concentrations       ║
║   that satisfy both equilibrium AND mass balance.                             ║
║                                                                               ║
║   EQUATIONS TO SOLVE:                                                         ║
║   ───────────────────                                                         ║
║   Mass balance for HCO₃ component:                                            ║
║       [H₂CO₃] + [HCO₃⁻] + [CO₃²⁻] = T_HCO3                                    ║
║                                                                               ║
║   Mass balance for H component:                                               ║
║       [H⁺] + [H₂CO₃] - [CO₃²⁻] = T_H                                          ║
║                                                                               ║
║   Equilibrium constraints:                                                    ║
║       [HCO₃⁻][H⁺]/[H₂CO₃] = K₁                                                ║
║       [CO₃²⁻][H⁺]/[HCO₃⁻] = K₂                                                ║
║                                                                               ║
║   NEWTON-RAPHSON ITERATION:                                                   ║
║   ─────────────────────────                                                   ║
║   Start with guess: C₀ = [component concentrations]                           ║
║                                                                               ║
║   Repeat:                                                                     ║
║       1. Calculate residual: R = mass balance error                           ║
║       2. Calculate Jacobian: J = ∂R/∂C                                        ║
║       3. Solve: J × ΔC = -R                                                   ║
║       4. Update: C_{n+1} = C_n + ΔC                                           ║
║   Until: ||R|| < tolerance                                                    ║
║                                                                               ║
║   CONVERGENCE:                                                                ║
║   ────────────                                                                ║
║   Newton-Raphson converges QUADRATICALLY near the solution:                   ║
║       Error_{n+1} ≈ (Error_n)²                                                ║
║                                                                               ║
║   If error = 10⁻³, next iteration: 10⁻⁶, then 10⁻¹², etc.                     ║
║   Very fast when close to solution!                                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 5.5 Anderson Acceleration

Newton-Raphson can be slow or oscillate. Anderson acceleration improves convergence:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    ANDERSON ACCELERATION                                      ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   THE PROBLEM WITH PURE NEWTON-RAPHSON:                                       ║
║   ─────────────────────────────────────                                       ║
║   • Can oscillate near the solution                                           ║
║   • May converge slowly for stiff systems                                     ║
║   • Sensitive to initial guess                                                ║
║                                                                               ║
║   STANDARD ITERATION:                                                         ║
║       C_{n+1} = G(C_n)        where G is the Newton update                    ║
║                                                                               ║
║   ANDERSON ACCELERATION:                                                      ║
║       Instead of using only the previous iterate, use a weighted              ║
║       combination of the last m iterates:                                     ║
║                                                                               ║
║       C_{n+1} = Σ(α_i × G(C_{n-i}))                                           ║
║                                                                               ║
║       where α_i are chosen to minimize the residual                           ║
║                                                                               ║
║   COMPARISON:                                                                 ║
║   ───────────                                                                 ║
║                                                                               ║
║   Iteration     Pure NR         Anderson (m=4)                                ║
║   ─────────     ────────        ──────────────                                ║
║       1         1.0e-02         1.0e-02                                       ║
║       2         5.0e-03         2.0e-03                                       ║
║       3         2.5e-03         3.0e-04                                       ║
║       4         1.2e-03         2.0e-05                                       ║
║       5         6.0e-04         1.0e-07                                       ║
║       ...       ...             CONVERGED                                     ║
║      15         1.0e-07                                                       ║
║                 CONVERGED                                                     ║
║                                                                               ║
║   PARAMETERS:                                                                 ║
║   ───────────                                                                 ║
║   • m = Anderson depth (how many previous iterates to use)                    ║
║   • Typical value: m = 4                                                      ║
║   • m = 0 gives pure Newton-Raphson                                           ║
║   • Larger m uses more memory but may converge faster                         ║
║                                                                               ║
║   WHY IT WORKS:                                                               ║
║   ─────────────                                                               ║
║   Anderson acceleration extrapolates based on the trajectory of               ║
║   previous iterations, effectively "predicting" where the solution is.        ║
║   It's like using momentum in optimization.                                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 5.6 Equilibrium in Code

**Code location:** `src/complab.cpp`, lines 805-811

```cpp
// Equilibrium chemistry (runs regardless of enable_kinetics)
if (useEquilibrium) {
    applyProcessingFunctional(
        new run_equilibrium_biotic<T, RXNDES>(nx, num_of_substrates,
                                               eqSolver, no_dynamics, bounce_back),
        vec_substr_lattices[0].getBoundingBox(),
        ptr_eq_lattices
    );
}
```

---

# 6. Code Flow: Step by Step

## 6.1 Main Simulation Phases

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    COMPLAB3D EXECUTION FLOW                                   ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   PHASE 1: INITIALIZATION                                                     ║
║   ───────────────────────                                                     ║
║   • Read XML configuration file                                               ║
║   • Parse simulation_mode (biotic/abiotic, kinetics, diagnostics)             ║
║   • Set up domain parameters (nx, ny, nz, dx)                                 ║
║   • Parse chemistry and microbiology sections                                 ║
║   File: complab_functions.hh, function: initialize_complab()                  ║
║                                                                               ║
║   PHASE 2: GEOMETRY SETUP                                                     ║
║   ──────────────────────                                                      ║
║   • Read geometry file (material numbers)                                     ║
║   • Identify pore, solid, biofilm cells                                       ║
║   • Calculate distance field for CA                                           ║
║   File: complab.cpp, lines 200-350                                            ║
║                                                                               ║
║   PHASE 3: NAVIER-STOKES FLOW                                                 ║
║   ───────────────────────────                                                 ║
║   • Create NS lattice (D3Q19)                                                 ║
║   • Set boundary conditions (pressure inlet/outlet)                           ║
║   • Iterate until steady-state flow                                           ║
║   • Calculate permeability, adjust pressure for target Pe                     ║
║   File: complab.cpp, lines 350-400                                            ║
║                                                                               ║
║   PHASE 4: TRANSPORT SETUP                                                    ║
║   ────────────────────────                                                    ║
║   • Create substrate lattices (D3Q7)                                          ║
║   • Create biomass lattices (if biotic mode)                                  ║
║   • Set diffusion coefficients and boundary conditions                        ║
║   • Couple velocity field to transport lattices                               ║
║   File: complab.cpp, lines 400-650                                            ║
║                                                                               ║
║   PHASE 5: MAIN SIMULATION LOOP                                               ║
║   ─────────────────────────────                                               ║
║   See detailed breakdown in Section 6.2                                       ║
║   File: complab.cpp, lines 683-950                                            ║
║                                                                               ║
║   PHASE 6: OUTPUT AND CLEANUP                                                 ║
║   ───────────────────────────                                                 ║
║   • Write final VTI files                                                     ║
║   • Save checkpoints                                                          ║
║   • Print summary statistics                                                  ║
║   File: complab.cpp, lines 950-1000                                           ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 6.2 Main Loop Detail

Each iteration of the main loop:

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    MAIN LOOP (ONE ITERATION)                                  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   for (iT = 0; iT < max_iterations; ++iT) {                                   ║
║                                                                               ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 1: OUTPUT (every N iterations)                                     │ ║
║   │ • Write VTI files for visualization                                     │ ║
║   │ • Print diagnostics if enabled                                          │ ║
║   │ • Save checkpoints if interval reached                                  │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 2: LBM COLLISION                                                   │ ║
║   │ • All substrate lattices collide                                        │ ║
║   │ • Planktonic biomass lattices collide (if LBM solver)                   │ ║
║   │ • Updates particle distributions locally                                │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 3: KINETICS (if enable_kinetics = true)                            │ ║
║   │ • Calculate Monod growth rates                                          │ ║
║   │ • Compute dS (substrate change) and dB (biomass change)                 │ ║
║   │ • Store changes in delta lattices                                       │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 4: UPDATE CONCENTRATIONS                                           │ ║
║   │ • Apply dS to substrate lattices                                        │ ║
║   │ • Apply dB to biomass lattices                                          │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 5: EQUILIBRIUM CHEMISTRY (if useEquilibrium = true)                │ ║
║   │ • Solve mass action equations                                           │ ║
║   │ • Adjust species concentrations                                         │ ║
║   │ • Newton-Raphson with Anderson acceleration                             │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 6: VALIDATION DIAGNOSTICS (if enabled)                             │ ║
║   │ • Print per-iteration data for debugging                                │ ║
║   │ • Show concentrations, changes, mass balances                           │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 7: CELLULAR AUTOMATA (if ca_count > 0)                             │ ║
║   │ • Check if any cell exceeds B_max                                       │ ║
║   │ • Redistribute excess biomass (fraction or half method)                 │ ║
║   │ • Update mask lattice (biofilm vs pore)                                 │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 8: FLOW UPDATE (if biofilm expanded)                               │ ║
║   │ • Update NS lattice dynamics for new biofilm cells                      │ ║
║   │ • Re-converge flow field                                                │ ║
║   │ • Update transport lattice couplings                                    │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                              ↓                                                ║
║   ┌─────────────────────────────────────────────────────────────────────────┐ ║
║   │ STEP 9: LBM STREAMING                                                   │ ║
║   │ • All substrate lattices stream                                         │ ║
║   │ • Planktonic biomass lattices stream                                    │ ║
║   │ • Particles move to neighboring nodes                                   │ ║
║   └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                               ║
║   }  // end main loop                                                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# 7. Data Structures and Lattices

## 7.1 Lattice Types

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    LATTICE TYPES IN COMPLAB3D                                 ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   NAVIER-STOKES LATTICE (D3Q19):                                              ║
║   ──────────────────────────────                                              ║
║   • Variable: nsLattice                                                       ║
║   • Type: MultiBlockLattice3D<T,NSDES>                                        ║
║   • 19 velocity directions in 3D                                              ║
║   • Stores: velocity field, pressure                                          ║
║   • Updated: only when biofilm expands                                        ║
║                                                                               ║
║   SUBSTRATE LATTICES (D3Q7):                                                  ║
║   ──────────────────────────                                                  ║
║   • Variable: vec_substr_lattices[i]                                          ║
║   • Type: MultiBlockLattice3D<T,RXNDES>                                       ║
║   • 7 velocity directions (simpler, faster)                                   ║
║   • One lattice per substrate species                                         ║
║   • Stores: concentration field                                               ║
║                                                                               ║
║   BIOMASS LATTICES (D3Q7):                                                    ║
║   ────────────────────────                                                    ║
║   • Biofilm: vec_bFilm_lattices[i]                                            ║
║   • Planktonic: vec_bFree_lattices[i]                                         ║
║   • Type: MultiBlockLattice3D<T,RXNDES>                                       ║
║   • One lattice per microbe species                                           ║
║                                                                               ║
║   DELTA LATTICES (for kinetics):                                              ║
║   ──────────────────────────────                                              ║
║   • dC[i] - substrate change per iteration                                    ║
║   • dBf[i] - biofilm biomass change                                           ║
║   • dBp[i] - planktonic biomass change                                        ║
║                                                                               ║
║   AUXILIARY LATTICES:                                                         ║
║   ───────────────────                                                         ║
║   • maskLattice - identifies cell type (pore, biofilm, solid)                 ║
║   • ageLattice - age of biofilm cells (for CA)                                ║
║   • distLattice - distance to nearest pore (for CA half method)               ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

## 7.2 Memory Layout

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    POINTER VECTORS                                            ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   ptr_kns_lattices (for kinetics processor):                                  ║
║   ──────────────────────────────────────────                                  ║
║   Index 0 to N-1:     Substrate lattices                                      ║
║   Index N to N+M-1:   Biomass lattices                                        ║
║   Index N+M to 2N-1:  dC (substrate delta) lattices                           ║
║   Index 2N to 2N+M-1: dB (biomass delta) lattices                             ║
║   Last:               Mask lattice                                            ║
║                                                                               ║
║   ptr_ca_lattices (for CA processor):                                         ║
║   ────────────────────────────────────                                        ║
║   Index 0 to M-1:     Biofilm lattices                                        ║
║   Index M to 2M-1:    Copy lattices (for redistribution)                      ║
║   Then:               totalbFilmLattice                                       ║
║   Then:               maskLattice                                             ║
║   Last:               ageLattice                                              ║
║                                                                               ║
║   ptr_eq_lattices (for equilibrium processor):                                ║
║   ─────────────────────────────────────────────                               ║
║   Index 0 to N-1:     Substrate lattices                                      ║
║   Last:               Mask lattice                                            ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
```

---

# Summary

This document explained the core concepts behind CompLaB3D:

1. **Biotic/Abiotic modes** - Controls whether microbes are simulated
2. **Kinetics** - Monod model for microbial growth and substrate consumption
3. **Cellular Automata** - Biofilm expansion when cells get too dense
4. **Equilibrium Chemistry** - Fast reactions solved with Newton-Raphson + Anderson

For practical examples with XML files and test cases, see the companion document:
**CompLaB3D_Test_Cases.md**

---

**End of Code Explanation Document**
