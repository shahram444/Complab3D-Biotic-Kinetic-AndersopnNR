# CompLaB3D Test Cases
## Complete XML and defineKinetics Files for Each Scenario

**Version:** 2.0 (Biotic-Kinetic-Anderson-NR)
**Author:** Shahram Asgari

---

# Table of Contents

| Test | Type | Description | Runtime |
|------|------|-------------|---------|
| **TEST 1** | Abiotic | Pure diffusion (no flow) | ~2 min |
| **TEST 2** | Abiotic | Advection-diffusion with flow | ~3 min |
| **TEST 3** | Abiotic | Transport + Equilibrium chemistry | ~5 min |
| **TEST 4** | Biotic | Single biofilm with CA (fraction) | ~10 min |
| **TEST 5** | Biotic | Single biofilm with CA (half) | ~8 min |
| **TEST 6** | Biotic | Planktonic bacteria (LBM) | ~5 min |
| **TEST 7** | Biotic | Biofilm + Equilibrium | ~15 min |
| **TEST 8** | Validation | Diagnostics enabled | ~5 min |

All tests use a small domain (30x20x20) for fast execution while demonstrating correct behavior.

---

# TEST 1: Pure Diffusion (Abiotic, No Flow)

## Scenario Description

A tracer diffuses from the left boundary into an initially empty domain. No flow, no reactions. This tests the basic diffusion solver.

```
PHYSICAL SETUP:
===============

  C=1.0                                               C=0 (Neumann)
    │                                                     │
    │  ┌─────────────────────────────────────────────┐    │
    │  │                                             │    │
    ▼  │    Initially C = 0 everywhere               │    ▼
  ━━━━━│                                             │━━━━━
  Inlet│         Tracer diffuses →                   │Outlet
  ━━━━━│                                             │━━━━━
       │                                             │
       └─────────────────────────────────────────────┘

EQUATION:
─────────
∂C/∂t = D × ∇²C

Where:
  C = tracer concentration [mol/L]
  D = diffusion coefficient = 1.0e-9 m²/s

EXPECTED BEHAVIOR:
──────────────────
• Concentration profile develops smoothly from left to right
• At steady state: linear gradient C(x) = 1.0 × (1 - x/L)
• No negative concentrations
• Mass flux J = -D × dC/dx = constant
```

## XML Configuration: test1_diffusion.xml

```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <src_path>src</src_path>
        <input_path>input</input_path>
        <output_path>output_test1_diffusion</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>false</biotic_mode>
        <enable_kinetics>false</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>30</nx>
            <ny>20</ny>
            <nz>20</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>20</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>0.0</delta_P>      <!-- No flow -->
        <Peclet>0.0</Peclet>        <!-- Pure diffusion -->
        <tau>0.8</tau>
        <track_performance>false</track_performance>
        <iteration>
            <ade_max_iT>5000</ade_max_iT>
            <ade_converge_iT>1e-8</ade_converge_iT>
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
        <read_NS_file>false</read_NS_file>
        <read_ADE_file>false</read_ADE_file>
        <save_VTK_interval>500</save_VTK_interval>
        <save_CHK_interval>5000</save_CHK_interval>
    </IO>
</parameters>
```

## Expected Output

```
SIMULATION MODE: ABIOTIC (no microbes - transport only)
Note: Kinetics disabled (abiotic mode)

Equilibrium chemistry: DISABLED

ITERATION 0  |  Time: 0.00e+00 s
  Tracer: min=0.00e+00 avg=0.00e+00 max=0.00e+00

ITERATION 500  |  Time: 3.75e-01 s
  Tracer: min=0.00e+00 avg=2.45e-01 max=1.00e+00

ITERATION 5000  |  Time: 3.75e+00 s
  Tracer: min=0.00e+00 avg=4.89e-01 max=1.00e+00  <- Near steady-state
```

---

# TEST 2: Advection-Diffusion (Abiotic, With Flow)

## Scenario Description

Tracer is transported by flow AND diffusion. Tests coupling between NS and ADE solvers.

```
PHYSICAL SETUP:
===============

  ΔP > 0 (pressure drop drives flow)
  ────────────────────────────────────────────────────────────▶ Flow

  C=1.0                                               C=0 (Neumann)
    │                                                     │
    │  ┌─────────────────────────────────────────────┐    │
    │  │                                             │    │
    ▼  │    Flow velocity u ─────────────────────▶   │    ▼
  ━━━━━│                                             │━━━━━
       │         Tracer advects + diffuses →         │
  ━━━━━│                                             │━━━━━
       │                                             │
       └─────────────────────────────────────────────┘

EQUATION:
─────────
∂C/∂t + u·∇C = D × ∇²C

Where:
  u = velocity field from NS solver [m/s]
  Pe = u×L/D = Peclet number (advection/diffusion ratio)

For Pe = 1.0:
  Advection and diffusion are equally important

EXPECTED BEHAVIOR:
──────────────────
• Tracer front moves faster than pure diffusion
• Asymmetric concentration profile (steeper at front)
• Steady-state reached faster than pure diffusion
```

## XML Configuration: test2_advection_diffusion.xml

```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <src_path>src</src_path>
        <input_path>input</input_path>
        <output_path>output_test2_advdiff</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>false</biotic_mode>
        <enable_kinetics>false</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>30</nx>
            <ny>20</ny>
            <nz>20</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>20</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>1.0e-3</delta_P>   <!-- Pressure drop for flow -->
        <Peclet>1.0</Peclet>        <!-- Advection = Diffusion -->
        <tau>0.8</tau>
        <track_performance>false</track_performance>
        <iteration>
            <ns_max_iT1>50000</ns_max_iT1>
            <ns_converge_iT1>1e-8</ns_converge_iT1>
            <ade_max_iT>5000</ade_max_iT>
            <ade_converge_iT>1e-8</ade_converge_iT>
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
        <save_VTK_interval>500</save_VTK_interval>
    </IO>
</parameters>
```

---

# TEST 3: Transport + Equilibrium Chemistry (Abiotic)

## Scenario Description

Carbonate system speciation without biology. CO2-rich water enters, equilibrium adjusts pH.

```
CHEMICAL SYSTEM:
================

  Reactions:
  ──────────
  CO₂(aq) + H₂O ⇌ H₂CO₃ ⇌ HCO₃⁻ + H⁺     (K₁ = 10^-6.35)
  HCO₃⁻ ⇌ CO₃²⁻ + H⁺                      (K₂ = 10^-10.33)

  Inlet conditions:
  ─────────────────
  [CO₂] = 1.0e-3 mol/L  (high CO₂)
  [HCO₃⁻] = 1.0e-3 mol/L
  [H⁺] = 1.0e-7 mol/L   (pH 7)

EQUILIBRIUM CONSTRAINT:
───────────────────────
At each point, the solver finds [CO₂], [HCO₃⁻], [CO₃²⁻], [H⁺] that satisfy:

  K₁ = [HCO₃⁻][H⁺] / [CO₂]
  K₂ = [CO₃²⁻][H⁺] / [HCO₃⁻]

EXPECTED BEHAVIOR:
──────────────────
• CO₂ dissociates, releasing H⁺
• pH decreases (more acidic)
• HCO₃⁻ increases, CO₃²⁻ decreases
• Total DIC (CO₂ + HCO₃⁻ + CO₃²⁻) is conserved
```

## XML Configuration: test3_equilibrium.xml

```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_test3_equilibrium</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>false</biotic_mode>
        <enable_kinetics>false</enable_kinetics>
        <enable_validation_diagnostics>true</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>30</nx>
            <ny>20</ny>
            <nz>20</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>20</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>1.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>5000</ade_max_iT>
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
            <left_boundary_condition>1.0e-3</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>

        <substrate1>
            <name_of_substrates>HCO3</name_of_substrates>
            <initial_concentration>1.0e-3</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.2e-9</in_pore>
                <in_biofilm>1.2e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-3</left_boundary_condition>
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
            <name_of_substrates>Hplus</name_of_substrates>
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

    <microbiology>
        <number_of_microbes>0</number_of_microbes>
    </microbiology>

    <equilibrium>
        <enabled>true</enabled>
        <components>HCO3 Hplus</components>
        <stoichiometry>
            <species0>1.0 1.0</species0>   <!-- CO2 = HCO3 + H -->
            <species1>1.0 0.0</species1>   <!-- HCO3 (component) -->
            <species2>1.0 -1.0</species2>  <!-- CO3 = HCO3 - H -->
            <species3>0.0 1.0</species3>   <!-- H+ (component) -->
        </stoichiometry>
        <logK>
            <species0>6.35</species0>      <!-- pKa1 -->
            <species1>0.0</species1>
            <species2>-10.33</species2>    <!-- pKa2 -->
            <species3>0.0</species3>
        </logK>
    </equilibrium>

    <IO>
        <save_VTK_interval>500</save_VTK_interval>
    </IO>
</parameters>
```

---

# TEST 4: Biofilm with CA (Fraction Method)

## Scenario Description

Biofilm grows by consuming DOC. When cells exceed B_max, excess is distributed equally to all neighbors.

```
REACTION:
─────────
DOC + O₂ → CO₂ + H₂O + Biomass

  Monod kinetics:
                    [DOC]
  μ = μ_max × ────────────
               Ks + [DOC]

  dB/dt = μ × B - k_decay × B    (biomass growth)
  dDOC/dt = -μ × B / Y           (substrate consumption)

PARAMETERS:
───────────
  μ_max = 1.0e-4 /s      Maximum growth rate
  Ks = 1.0e-5 mol/L      Half-saturation
  Y = 0.4                Yield (kg biomass / mol DOC)
  k_decay = 1.0e-7 /s    Decay rate
  B_max = 100 kg/m³      Maximum biomass density

EXPECTED BEHAVIOR:
──────────────────
• Biomass grows where DOC is available
• Growth rate: initially fast (μ ≈ μ_max when DOC >> Ks)
• When B > B_max: CA redistributes to neighbors
• Biofilm expands smoothly with fraction method
• DOC concentration decreases in biofilm region
```

## XML Configuration: test4_biofilm_fraction.xml

```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_test4_biofilm_fraction</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>30</nx>
            <ny>20</ny>
            <nz>20</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>20</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
                <microbe0>3 6</microbe0>
            </material_numbers>
        </domain>
        <delta_P>1.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>10000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>2</number_of_substrates>

        <substrate0>
            <name_of_substrates>DOC</name_of_substrates>
            <initial_concentration>1.0e-2</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>2.0e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-2</left_boundary_condition>
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
            <initial_densities>90.0 90.0</initial_densities>
            <decay_coefficient>1.0e-7</decay_coefficient>
            <viscosity_ratio_in_biofilm>10.0</viscosity_ratio_in_biofilm>
            <half_saturation_constants>1.0e-5 0.0</half_saturation_constants>
            <maximum_uptake_flux>2.0 0.0</maximum_uptake_flux>
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
        <save_VTK_interval>1000</save_VTK_interval>
    </IO>
</parameters>
```

## defineKinetics.hh for Test 4

```cpp
#ifndef DEFINE_KINETICS_HH
#define DEFINE_KINETICS_HH

/*
 * TEST 4: Biofilm with CA (Fraction Method)
 * =========================================
 *
 * Reaction: DOC → Biomass + CO2
 *
 * Kinetics:
 *   dB/dt = mu * B - k_decay * B
 *   dDOC/dt = -mu * B / Y
 *   dCO2/dt = +mu * B / Y  (stoichiometric)
 *
 * where: mu = mu_max * DOC / (Ks + DOC)
 */

namespace KineticParams {
    // Growth parameters
    constexpr double mu_max   = 1.0e-4;    // Max growth rate [1/s]
    constexpr double Ks       = 1.0e-5;    // Half-saturation [mol/L]
    constexpr double Y        = 0.4;       // Yield [kg/mol]
    constexpr double k_decay  = 1.0e-7;    // Decay rate [1/s]

    // Numerical
    constexpr double dt_kinetics = 0.0075; // Timestep [s]
    constexpr double MIN_BIOMASS = 0.1;    // Threshold for kinetics
    constexpr double MIN_SUBSTRATE = 1e-12; // Prevent division by zero
}

// Kinetics calculation function
template<typename T>
void calculateKinetics(
    T DOC,       // Substrate concentration [mol/L]
    T B,         // Biomass concentration [kg/m3]
    T& dDOC,     // Output: substrate change
    T& dB,       // Output: biomass change
    T& dCO2,     // Output: CO2 change
    T dt         // Timestep [s]
) {
    using namespace KineticParams;

    // Skip if no biomass
    if (B < MIN_BIOMASS) {
        dDOC = 0.0;
        dB = 0.0;
        dCO2 = 0.0;
        return;
    }

    // Prevent negative concentrations
    if (DOC < MIN_SUBSTRATE) DOC = MIN_SUBSTRATE;

    // Monod growth rate
    T mu = mu_max * DOC / (Ks + DOC);

    // Net growth (growth - decay)
    T net_growth = (mu - k_decay) * B;

    // Biomass change
    dB = net_growth * dt;

    // Substrate consumption (only for growth, not decay)
    T consumption = mu * B / Y;
    dDOC = -consumption * dt;

    // CO2 production (stoichiometric with consumption)
    dCO2 = consumption * dt;

    // Clamp to prevent negative substrate
    if (DOC + dDOC < 0) {
        dDOC = -DOC * 0.9;  // Leave 10% to prevent instability
        dB = -dDOC * Y;      // Adjust biomass proportionally
        dCO2 = -dDOC;
    }
}

#endif // DEFINE_KINETICS_HH
```

---

# TEST 5: Biofilm with CA (Half Method)

## Scenario Description

Same as Test 4, but using the "half" CA method for faster, directional expansion.

```
DIFFERENCE FROM TEST 4:
───────────────────────
• CA_method = half (instead of fraction)
• Excess biomass goes toward open pore space
• Faster stabilization
• More directional expansion pattern

EXPECTED BEHAVIOR:
──────────────────
• Same growth kinetics as Test 4
• When B > B_max:
  - Find neighbor closest to pore space
  - Send HALF of excess to that neighbor
  - Repeat until stable
• Biofilm expands preferentially toward nutrients
• Fewer CA iterations needed
```

## XML Configuration: test5_biofilm_half.xml

Same as Test 4, except:

```xml
<CA_method>half</CA_method>
```

And output path:
```xml
<output_path>output_test5_biofilm_half</output_path>
```

---

# TEST 6: Planktonic Bacteria (LBM Solver)

## Scenario Description

Free-floating bacteria transported by flow. No CA expansion - bacteria are advected.

```
PHYSICAL SETUP:
===============

  Bacteria inlet                                      Outlet
      │                                                  │
      ▼                                                  ▼
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    │  B=10    →    →    →    →    →    →    →    →    │
    │          →    →    →    →    →    →    →    →    │
    │  DOC     →    →    →    →    →    →    →    →    │
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

KEY DIFFERENCES FROM BIOFILM:
─────────────────────────────
• solver_type = LBM (not CA)
• Bacteria advected with flow velocity
• Bacteria can diffuse (like a solute)
• No CA expansion - bacteria move with flow
• Higher decay rate (exposed to environment)

EXPECTED BEHAVIOR:
──────────────────
• Bacteria concentration develops plume
• Growth where DOC is available
• Decay everywhere
• Bacteria transported downstream
```

## XML Configuration: test6_planktonic.xml

```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_test6_planktonic</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>30</nx>
            <ny>20</ny>
            <nz>20</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>20</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
            </material_numbers>
        </domain>
        <delta_P>1.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>5000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>1</number_of_substrates>
        <substrate0>
            <name_of_substrates>DOC</name_of_substrates>
            <initial_concentration>1.0e-2</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>1.0e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-2</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate0>
    </chemistry>

    <microbiology>
        <number_of_microbes>1</number_of_microbes>
        <maximum_biomass_density>100.0</maximum_biomass_density>
        <thrd_biofilm_fraction>0.1</thrd_biofilm_fraction>
        <CA_method>none</CA_method>

        <microbe0>
            <name_of_microbes>Planktonic</name_of_microbes>
            <solver_type>LBM</solver_type>
            <reaction_type>kinetics</reaction_type>
            <initial_densities>0.0 10.0</initial_densities>
            <decay_coefficient>1.0e-6</decay_coefficient>
            <biomass_diffusion_coefficients>
                <in_pore>1.0e-10</in_pore>
                <in_biofilm>1.0e-10</in_biofilm>
            </biomass_diffusion_coefficients>
            <half_saturation_constants>1.0e-5</half_saturation_constants>
            <maximum_uptake_flux>1.0</maximum_uptake_flux>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>10.0</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
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

## defineKinetics_planktonic.hh for Test 6

```cpp
#ifndef DEFINE_KINETICS_PLANKTONIC_HH
#define DEFINE_KINETICS_PLANKTONIC_HH

/*
 * TEST 6: Planktonic Bacteria
 * ===========================
 *
 * Key differences from biofilm:
 * - Higher decay rate (exposed, no EPS protection)
 * - Lower maximum growth rate (less efficient)
 * - Bacteria transported by flow
 */

namespace KineticParams {
    // Growth parameters (lower than biofilm)
    constexpr double mu_max   = 5.0e-5;    // Max growth rate [1/s]
    constexpr double Ks       = 1.0e-5;    // Half-saturation [mol/L]
    constexpr double Y        = 0.35;      // Yield [kg/mol]
    constexpr double k_decay  = 1.0e-6;    // Higher decay [1/s]

    // Numerical
    constexpr double dt_kinetics = 0.0075;
    constexpr double MIN_BIOMASS = 0.01;   // Lower threshold
    constexpr double MIN_SUBSTRATE = 1e-12;
}

#endif
```

---

# TEST 7: Biofilm + Equilibrium Chemistry

## Scenario Description

Biofilm respiration produces CO2, which affects carbonate equilibrium and pH.

```
COUPLED SYSTEM:
===============

  KINETIC REACTION (slow - tracked explicitly):
  ─────────────────────────────────────────────
  DOC + O₂ → CO₂ + H₂O + Biomass

  EQUILIBRIUM REACTIONS (fast - solved at each step):
  ───────────────────────────────────────────────────
  CO₂ + H₂O ⇌ H₂CO₃ ⇌ HCO₃⁻ + H⁺     (K₁ = 10^-6.35)
  HCO₃⁻ ⇌ CO₃²⁻ + H⁺                  (K₂ = 10^-10.33)

COUPLING:
─────────
  1. Kinetics: DOC consumed → CO₂ produced
  2. Equilibrium: CO₂ enters carbonate system
  3. Result: pH decreases in biofilm region

EXPECTED BEHAVIOR:
──────────────────
• Biomass grows, consumes DOC
• CO₂ concentration increases in biofilm
• pH drops (H⁺ increases) near biofilm
• Equilibrium adjusts carbonate speciation
• Spatial gradients in all species
```

## XML Configuration: test7_biofilm_equilibrium.xml

```xml
<?xml version="1.0" ?>
<parameters>
    <path>
        <output_path>output_test7_biofilm_eq</output_path>
    </path>

    <simulation_mode>
        <biotic_mode>true</biotic_mode>
        <enable_kinetics>true</enable_kinetics>
        <enable_validation_diagnostics>false</enable_validation_diagnostics>
    </simulation_mode>

    <LB_numerics>
        <domain>
            <nx>30</nx>
            <ny>20</ny>
            <nz>20</nz>
            <dx>1.0</dx>
            <unit>um</unit>
            <characteristic_length>20</characteristic_length>
            <filename>geometry.dat</filename>
            <material_numbers>
                <pore>2</pore>
                <solid>0</solid>
                <bounce_back>1</bounce_back>
                <microbe0>3 6</microbe0>
            </material_numbers>
        </domain>
        <delta_P>1.0e-3</delta_P>
        <Peclet>1.0</Peclet>
        <tau>0.8</tau>
        <iteration>
            <ade_max_iT>15000</ade_max_iT>
        </iteration>
    </LB_numerics>

    <chemistry>
        <number_of_substrates>5</number_of_substrates>

        <substrate0>
            <name_of_substrates>DOC</name_of_substrates>
            <initial_concentration>1.0e-2</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.0e-9</in_pore>
                <in_biofilm>2.0e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-2</left_boundary_condition>
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

        <substrate2>
            <name_of_substrates>HCO3</name_of_substrates>
            <initial_concentration>2.0e-3</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>1.2e-9</in_pore>
                <in_biofilm>2.4e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>2.0e-3</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate2>

        <substrate3>
            <name_of_substrates>CO3</name_of_substrates>
            <initial_concentration>1.0e-5</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>0.9e-9</in_pore>
                <in_biofilm>1.8e-10</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-5</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate3>

        <substrate4>
            <name_of_substrates>Hplus</name_of_substrates>
            <initial_concentration>1.0e-7</initial_concentration>
            <substrate_diffusion_coefficients>
                <in_pore>9.3e-9</in_pore>
                <in_biofilm>1.9e-9</in_biofilm>
            </substrate_diffusion_coefficients>
            <left_boundary_type>Dirichlet</left_boundary_type>
            <right_boundary_type>Neumann</right_boundary_type>
            <left_boundary_condition>1.0e-7</left_boundary_condition>
            <right_boundary_condition>0.0</right_boundary_condition>
        </substrate4>
    </chemistry>

    <microbiology>
        <number_of_microbes>1</number_of_microbes>
        <maximum_biomass_density>100.0</maximum_biomass_density>
        <thrd_biofilm_fraction>0.1</thrd_biofilm_fraction>
        <CA_method>half</CA_method>

        <microbe0>
            <name_of_microbes>Heterotroph</name_of_microbes>
            <solver_type>CA</solver_type>
            <reaction_type>kinetics</reaction_type>
            <initial_densities>90.0 90.0</initial_densities>
            <decay_coefficient>1.0e-7</decay_coefficient>
            <viscosity_ratio_in_biofilm>10.0</viscosity_ratio_in_biofilm>
            <half_saturation_constants>1.0e-5 0.0 0.0 0.0 0.0</half_saturation_constants>
            <maximum_uptake_flux>2.0 0.0 0.0 0.0 0.0</maximum_uptake_flux>
        </microbe0>
    </microbiology>

    <equilibrium>
        <enabled>true</enabled>
        <components>HCO3 Hplus</components>
        <stoichiometry>
            <species0>0.0 0.0</species0>   <!-- DOC: not in equilibrium -->
            <species1>1.0 1.0</species1>   <!-- CO2 = HCO3 + H -->
            <species2>1.0 0.0</species2>   <!-- HCO3 (component) -->
            <species3>1.0 -1.0</species3>  <!-- CO3 = HCO3 - H -->
            <species4>0.0 1.0</species4>   <!-- H+ (component) -->
        </stoichiometry>
        <logK>
            <species0>0.0</species0>
            <species1>6.35</species1>
            <species2>0.0</species2>
            <species3>-10.33</species3>
            <species4>0.0</species4>
        </logK>
    </equilibrium>

    <IO>
        <save_VTK_interval>1500</save_VTK_interval>
    </IO>
</parameters>
```

---

# TEST 8: Validation Diagnostics

## Scenario Description

Run any biotic simulation with diagnostics enabled to verify correct behavior.

```
PURPOSE:
────────
• Verify kinetics is calculating correctly
• Check mass balance
• Debug unexpected behavior
• Confirm equilibrium solver is working

WHAT TO CHECK:
──────────────
1. dC (substrate change) should be negative where biomass exists
2. dB (biomass change) should be positive when DOC available
3. Mass balance: |dDOC × Y| ≈ |dB| (within 5%)
4. No NaN or Inf values
5. Equilibrium shows different min/max if enabled
```

## XML Configuration

Add to any biotic test:

```xml
<simulation_mode>
    <biotic_mode>true</biotic_mode>
    <enable_kinetics>true</enable_kinetics>
    <enable_validation_diagnostics>true</enable_validation_diagnostics>
</simulation_mode>
```

## Expected Diagnostic Output

```
┌─────────────────────────────────────────────────────────────────────────┐
│ VALIDATION DIAGNOSTICS - Iteration 100                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ Time: 7.5000e-01 s                                                      │
├─────────────────────────────────────────────────────────────────────────┤
│ STEP 6.1 [COLLISION]: LBM collision completed                           │
│ STEP 6.2 [KINETICS]: ACTIVE - 1 reaction(s)                             │
│   DOC @center: C=9.87e-03, dC=-2.34e-06                                 │
│   Biomass @center: B=9.05e+01, dB=9.36e-06                              │
│ STEP 6.3 [EQUILIBRIUM]: ACTIVE                                          │
│   CO2: min=1.00e-05, max=1.15e-05                                       │
│   Hplus: min=1.00e-07, max=1.25e-07                                     │
├─────────────────────────────────────────────────────────────────────────┤
│ MASS BALANCE CHECK:                                                      │
│   DOC total: 3.45e+02                                                    │
│   Total biomass: 1.08e+04                                                │
└─────────────────────────────────────────────────────────────────────────┘

Interpretation:
───────────────
• dC=-2.34e-06 < 0: DOC being consumed ✓
• dB=9.36e-06 > 0: Biomass growing ✓
• |dC × Y| = 2.34e-06 × 0.4 = 9.36e-06 ≈ dB ✓ (mass balance OK)
• CO2 max > min: Equilibrium is adjusting values ✓
• H+ max > min: pH gradient exists ✓
```

---

# Quick Reference: Which Test for Which Purpose

| I want to test... | Run this test |
|-------------------|---------------|
| Basic LBM diffusion | TEST 1 |
| Flow coupling | TEST 2 |
| Equilibrium solver | TEST 3 |
| Biofilm growth | TEST 4 or 5 |
| CA fraction method | TEST 4 |
| CA half method | TEST 5 |
| Planktonic transport | TEST 6 |
| Full coupled system | TEST 7 |
| Debug/verify code | TEST 8 |

---

**End of Test Cases Document**
