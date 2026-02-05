# Abiotic Kinetics Test Cases

## Overview

This directory contains **5 complete test cases** for validating the abiotic kinetics functionality in CompLaB3D. Each test includes:

1. **XML configuration file** - Simulation parameters
2. **defineAbioticKinetics_testN.hh** - Kinetics implementation for that test

## Test Summary

| Test | Reaction | Rate Law | Key Validation |
|------|----------|----------|----------------|
| **Test 1** | None (diffusion only) | ∂C/∂t = D∇²C | Linear steady-state profile |
| **Test 2** | A → products | dA/dt = -k·[A] | Exponential decay |
| **Test 3** | A + B → C | r = k·[A]·[B] | Mass balance: A+B+C = const |
| **Test 4** | A ⇌ B | dA/dt = -k_f·[A] + k_r·[B] | Equilibrium: [B]/[A] = K_eq |
| **Test 5** | A → B → C | Bateman equations | Transient peak in B |

---

## How to Run a Test

### Step 1: Copy the kinetics file

```bash
# For Test 2 (First-Order Decay):
cp test_cases/abiotic/defineAbioticKinetics_test2.hh src/defineAbioticKinetics.hh
```

### Step 2: Recompile

```bash
cd src
make clean
make
```

### Step 3: Run the simulation

```bash
./complab3d ../test_cases/abiotic/test2_first_order_decay.xml
```

### Step 4: Check output

```bash
# View VTK files in ParaView
paraview output_abiotic_test2_decay/substrate*.vti
```

---

## Test 1: Pure Diffusion (No Reactions)

### Physics
```
∂C/∂t = D × ∇²C

Boundary Conditions:
  Left:  C = 1.0 mol/L (Dirichlet)
  Right: dC/dx = 0 (Neumann)
```

### Validation
At steady state, concentration profile is LINEAR:
```
C(x) = 1.0 × (1 - x/L)

Check:
  - Left boundary: C = 1.0
  - Middle: C ≈ 0.5
  - Right boundary: C → 0
```

### Files
- `test1_pure_diffusion.xml`
- No kinetics file needed (`enable_abiotic_kinetics=false`)

---

## Test 2: First-Order Decay

### Physics
```
A → products

dA/dt = -k × [A]

k = 1.0e-4 [1/s]
Half-life = ln(2)/k = 6930 seconds
```

### Analytical Solution
```
[A](t) = [A]₀ × exp(-k×t)

At t = 6930 s:  [A] = 0.5 × [A]₀
At t = 13860 s: [A] = 0.25 × [A]₀
```

### Validation
- Exponential decay curve
- No negative concentrations
- Mass lost (products not tracked)

### Files
- `test2_first_order_decay.xml`
- `defineAbioticKinetics_test2.hh`

---

## Test 3: Bimolecular Reaction

### Physics
```
A + B → C

dA/dt = dB/dt = -k × [A] × [B]
dC/dt = +k × [A] × [B]

k = 1.0e-2 [L/mol/s]
```

### Initial Conditions
```
[A]₀ = 1.0 mol/L
[B]₀ = 0.5 mol/L  (limiting reagent)
[C]₀ = 0.0 mol/L
```

### Validation
```
Mass balance (constant):
  [A] + [B] + [C] = 1.5 mol/L

At completion (B exhausted):
  [A] = 0.5 mol/L
  [B] = 0.0 mol/L
  [C] = 0.5 mol/L
```

### Files
- `test3_bimolecular.xml`
- `defineAbioticKinetics_test3.hh`

---

## Test 4: Reversible Reaction

### Physics
```
A ⇌ B

Forward: A → B, k_f = 1.0e-3 [1/s]
Reverse: B → A, k_r = 5.0e-4 [1/s]

dA/dt = -k_f×[A] + k_r×[B]
dB/dt = +k_f×[A] - k_r×[B]
```

### Equilibrium Constant
```
K_eq = k_f / k_r = 2.0

At equilibrium: [B]/[A] = K_eq = 2.0
```

### Initial Conditions
```
[A]₀ = 1.0 mol/L
[B]₀ = 0.0 mol/L
```

### Validation
```
Conservation: [A] + [B] = 1.0 mol/L (constant)

Equilibrium values:
  [A]_eq = 1/(1 + K_eq) = 0.333 mol/L
  [B]_eq = K_eq/(1 + K_eq) = 0.667 mol/L

Check: [B]/[A] approaches 2.0 over time
```

### Files
- `test4_reversible.xml`
- `defineAbioticKinetics_test4.hh`

---

## Test 5: Sequential Decay Chain

### Physics
```
A → B → C  (like radioactive decay series)

A → B:  dA/dt = -k₁×[A],  k₁ = 2.0e-4 [1/s]
B → C:  dB/dt = +k₁×[A] - k₂×[B],  k₂ = 1.0e-4 [1/s]
        dC/dt = +k₂×[B]
```

### Analytical Solution (Bateman Equations)
```
[A](t) = A₀ × exp(-k₁t)

[B](t) = A₀ × k₁/(k₂-k₁) × (exp(-k₁t) - exp(-k₂t))

[C](t) = A₀ × [1 + (k₁×exp(-k₂t) - k₂×exp(-k₁t))/(k₂-k₁)]
```

### Initial Conditions
```
[A]₀ = 1.0 mol/L (only parent)
[B]₀ = 0.0 mol/L
[C]₀ = 0.0 mol/L
```

### Validation
```
Conservation: [A] + [B] + [C] = 1.0 mol/L (constant)

Final state (t → ∞):
  [A] → 0
  [B] → 0
  [C] → 1.0 mol/L

B shows TRANSIENT PEAK:
  - Initially grows (produced from A faster than decays to C)
  - Reaches maximum at t_max = ln(k₁/k₂)/(k₁-k₂) ≈ 6932 s
  - Then decays to zero
```

### Files
- `test5_decay_chain.xml`
- `defineAbioticKinetics_test5.hh`

---

## Validation Checklist

For each test, verify:

| Check | Method |
|-------|--------|
| **Mass balance** | Sum of all species should be constant (except Test 1, 2) |
| **No negative concentrations** | All C[i] ≥ 0 |
| **Correct final state** | Compare with analytical solution |
| **Stability** | No oscillations or NaN values |
| **Convergence** | Steady state or equilibrium reached |

---

## Troubleshooting

### Problem: Simulation crashes

**Solution:** Check that kinetics file matches XML:
```bash
# Verify substrate count in XML matches kinetics code
grep "number_of_substrates" test3_bimolecular.xml
# Should show: 3

# In defineAbioticKinetics_test3.hh, verify:
# if (C.size() >= 3) { ... }
```

### Problem: Mass not conserved

**Solution:** Check rate clamping is not too aggressive:
```cpp
// In kinetics file, try increasing MAX_RATE_FRACTION:
constexpr double MAX_RATE_FRACTION = 0.5;  // Allow more reaction per step
```

### Problem: Reaction too slow

**Solution:** Increase rate constants:
```cpp
// Test 2: faster decay
constexpr double k_decay = 1.0e-3;  // 10x faster
```

---

## Creating New Test Cases

To add a new reaction:

1. **Create XML file** with correct number of substrates
2. **Create kinetics file** implementing your rate law:
```cpp
void defineAbioticRxnKinetics(
    std::vector<double> C,      // Input concentrations
    std::vector<double>& subsR, // Output rates
    plb::plint mask
) {
    // Your rate law here
    // subsR[i] = rate of change for species i
    // Negative = consumption, Positive = production
}
```
3. **Test validation** - ensure mass balance and physical behavior

---

## Contact

Meile Lab, University of Georgia
