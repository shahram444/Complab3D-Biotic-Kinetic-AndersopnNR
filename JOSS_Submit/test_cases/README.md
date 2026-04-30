# CompLaB3D Test Cases

Eight simulation configurations that exercise every major capability of the
solver. Each case is run **manually** — you copy the right files into a working
directory and launch the solver yourself. This gives you full control over
which geometry you use, how many MPI processes you start, and what output
you inspect.

---

## Contents

```
test_cases/
  flow_only/
    CompLaB.xml               ← Navier-Stokes only, no transport
  abiotic/
    test1_pure_diffusion.xml  ← diffusion with no reactions
    test2_first_order_decay.xml  + defineAbioticKinetics_test2.hh
    test3_bimolecular.xml        + defineAbioticKinetics_test3.hh
    test4_reversible.xml         + defineAbioticKinetics_test4.hh
    test5_decay_chain.xml        + defineAbioticKinetics_test5.hh
    CompLaB_equilibrium.xml   ← abiotic transport + carbonate equilibrium
    input/geometry.dat        ← 50×30×30 geometry (create once, used by all)
  biotic/
    CompLaB.xml               ← heterotrophic biofilm growth (Monod kinetics)
    defineKinetics.hh         ← kinetics header compiled into the solver
```

---

## Before You Start

### 1 — Build the solver

You need the compiled `complab` binary with Palabos and MPI.  
See the main `README.md` §4 (local build) or §5 (HPC cluster build).

### 2 — one rule

> **The solver always reads a file named `CompLaB.xml` from the directory
> where you run it.** The filename is hardcoded in `src/complab_functions.hh`.
> Command-line arguments for the config file are ignored.

This means for every case:

```
cp <test_xml_file> ./CompLaB.xml      ← always this exact name
mpirun -np <N> /path/to/complab       ← no xml argument needed
```

### 3 — Create the geometry file (do this once)

All test cases use a 50 × 30 × 30 domain with `geometry.dat` in an `input/`
subdirectory. The geometry file is a plain ASCII list of integers — one per
line — where `2` = pore and `0` = solid.

If you already have a `50 × 30 × 30` geometry file from your research, copy it:

```bash
mkdir -p test_cases/abiotic/input
cp /your/geometry.dat test_cases/abiotic/input/geometry.dat
```

The biotic case uses the same geometry — just copy:

```bash
mkdir -p test_cases/biotic/input
cp test_cases/abiotic/input/geometry.dat test_cases/biotic/input/geometry.dat
```

---

## Case 0 — Flow Only

**What it runs:** Navier-Stokes flow solver only. No advection-diffusion, no
chemistry. Output is the velocity and pressure VTK file.

**When to use:** Compute permeability, validate velocity field in your geometry,
or pre-converge flow before adding transport.

**How it works:** `ade_max_iT = 0` tells the solver to exit after NS converges
(checked at `complab.cpp` line 401).

**Files needed:**

```
flow_only/CompLaB.xml  →  copy as CompLaB.xml in your working dir
input/geometry.dat
```

**Steps:**

```bash
mkdir -p my_runs/flow_only && cd my_runs/flow_only
cp ../../test_cases/flow_only/CompLaB.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat
mpirun -np 4 ../../complab 2>&1 | tee run.log
```



**Output files:** `output_flow_only/nsLattice*.vtk` — open in ParaView to
visualize velocity streamlines and verify Poiseuille-type flow profile.

---

## Case 1 — Pure Diffusion

**What it runs:** One tracer species diffusing from a Dirichlet inlet
(C = 1.0 mol/L) to a Neumann outlet. No reactions, no flow (Pe = 0).

**Validates:** The ADE transport solver in isolation. At steady state the
concentration profile must be exactly linear: C(x) = 1 − x/L.

**No recompilation needed** — kinetics are disabled in the XML.

**Files needed:**

```
abiotic/test1_pure_diffusion.xml  →  copy as CompLaB.xml
abiotic/input/geometry.dat
```

**Steps:**

```bash
mkdir -p my_runs/test1 && cd my_runs/test1
cp ../../test_cases/abiotic/test1_pure_diffusion.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

**Expected output directory:** `output_abiotic_test1_diffusion/`  
**VTK files:** `Tracer_0000000.vti`, `Tracer_0001000.vti`, … `Tracer_0005000.vti`



**In ParaView:** color the domain by `Tracer` — you should see a smooth
gradient from 1.0 at the left face to near 0 at the right face.

---

## Case 2 — First-Order Decay

**Reaction:** A → products, rate = k·[A], k = 10⁻⁴ /s

**Analytical solution:**

```
[A](t) = [A]₀ × exp(−k × t)      [A]₀ = 1.0 mol/L
Half-life t½ = ln(2)/k ≈ 6 931 s
```

**Requires recompilation** — `defineAbioticKinetics_test2.hh` implements this
specific rate law. The solver binary has the kinetics compiled in.

**Steps:**

```bash
# Step 1 — copy the kinetics header and recompile
cd /path/to/JOSS_Submit
cp test_cases/abiotic/defineAbioticKinetics_test2.hh defineAbioticKinetics.hh
cd build && make -j4 && cd ..

# Step 2 — set up working directory
mkdir -p my_runs/test2 && cd my_runs/test2
cp ../../test_cases/abiotic/test2_first_order_decay.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat

# Step 3 — run
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

**Output directory:** `output_abiotic_test2_decay/`

**What to check:**

- Concentration in `FINAL CONCENTRATIONS` block is between 0 and 1.0
- Value decreases relative to initial 1.0 (exponential decay)
- No NaN, no negative values
- After 3 000 iterations at dt ≈ 0.0075 s (t ≈ 22.5 s):
  `[A] ≈ 1.0 × exp(−1e-4 × 22.5) ≈ 0.9978`

---

## Case 3 — Bimolecular Reaction

**Reaction:** A + B → C, rate = k·[A]·[B], k = 10⁻² L/mol/s

**Initial:** [A]₀ = 1.0, [B]₀ = 0.5, [C]₀ = 0.0 mol/L

**Mass balance (always true):**

```
[A] + [C] = 1.0     [B] + [C] = 0.5     [A] + [B] + [C] = 1.5 mol/L
```

B is the limiting reagent — at completion: [A]→0.5, [B]→0, [C]→0.5.

**Requires recompilation** — copy `defineAbioticKinetics_test3.hh`.

**Steps:**

```bash
# Step 1 — recompile with test3 kinetics
cd /path/to/JOSS_Submit
cp test_cases/abiotic/defineAbioticKinetics_test3.hh defineAbioticKinetics.hh
cd build && make -j4 && cd ..

# Step 2 — working directory
mkdir -p my_runs/test3 && cd my_runs/test3
cp ../../test_cases/abiotic/test3_bimolecular.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat

# Step 3 — run
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

**Output directory:** `output_abiotic_test3_bimolecular/`



---

## Case 4 — Reversible Reaction

**Reaction:** A ⇌ B, forward k_f = 10⁻³/s, reverse k_r = 5×10⁻⁴/s

**Equilibrium constant:** K_eq = k_f / k_r = 2.0

**Equilibrium concentrations** (starting from [A]₀=1, [B]₀=0):

```
[A]_eq = 1/(1 + K_eq) = 0.333 mol/L
[B]_eq = K_eq/(1 + K_eq) = 0.667 mol/L
[A] + [B] = 1.0 mol/L  (conserved)
```

**Requires recompilation** — copy `defineAbioticKinetics_test4.hh`.

**Steps:**

```bash
cd /path/to/JOSS_Submit
cp test_cases/abiotic/defineAbioticKinetics_test4.hh defineAbioticKinetics.hh
cd build && make -j4 && cd ..

mkdir -p my_runs/test4 && cd my_runs/test4
cp ../../test_cases/abiotic/test4_reversible.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

**Output directory:** `output_abiotic_test4_reversible/`

---

## Case 5 — Sequential Decay Chain (Bateman Equations)

**Reaction:** A → B → C, k₁ = 2×10⁻⁴/s, k₂ = 10⁻⁴/s

**Initial:** [A]₀ = 1.0, [B]₀ = [C]₀ = 0 mol/L

**Analytical solution (Bateman):**

```
[A](t) = A₀ × exp(−k₁t)
[B](t) = A₀ × k₁/(k₂−k₁) × (exp(−k₁t) − exp(−k₂t))
[C](t) = A₀ − [A](t) − [B](t)

[A] + [B] + [C] = 1.0 mol/L at all times
At large t → [C] = 1.0, [A] = [B] = 0
```

B shows a transient peak before decaying — this is the most distinguishing feature
to look for in ParaView.

**Requires recompilation** — copy `defineAbioticKinetics_test5.hh`.

**Steps:**

```bash
cd /path/to/JOSS_Submit
cp test_cases/abiotic/defineAbioticKinetics_test5.hh defineAbioticKinetics.hh
cd build && make -j4 && cd ..

mkdir -p my_runs/test5 && cd my_runs/test5
cp ../../test_cases/abiotic/test5_decay_chain.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

**Output directory:** `output_abiotic_test5_chain/`

## Case 6 — Abiotic + Equilibrium Chemistry (Carbonate System)

**What it runs:** Advection-diffusion transport of three carbonate species, with
the PCF + Anderson Acceleration equilibrium solver enforcing carbonate speciation
at every time step. No kinetics, no microbes.

**Species:**

- CO2 (equilibrium)
- HCO3⁻ master component — carried by transport
- H⁺ master component — carried by transport (pH)

**Equilibrium relationship:**

```
log[CO2] = +6.35 + log[HCO3⁻] + log[H⁺]     (pKa1 = 6.35)
```

At inlet conditions (HCO3⁻ = 2×10⁻³, H⁺ = 10⁻⁷ = pH 7):

```
[CO2]_eq = 10^6.35 × 2×10⁻³ × 10⁻⁷ ≈ 4.5×10⁻³ mol/L
```

**No recompilation needed** — equilibrium is handled entirely at runtime by
the solver's built-in PCF+AA solver.

**Files needed:**

```
abiotic/CompLaB_equilibrium.xml  →  copy as CompLaB.xml
abiotic/input/geometry.dat
```

**Steps:**

```bash
mkdir -p my_runs/abiotic_eq && cd my_runs/abiotic_eq
cp ../../test_cases/abiotic/CompLaB_equilibrium.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

---

## Case 7 — Biotic: Heterotrophic Biofilm Growth

**What it runs:** Full biotic simulation — Navier-Stokes flow, advection-diffusion
transport of 5 species, and Monod kinetics for heterotrophic biofilm growth.
No equilibrium chemistry.

**Species:**

- DOC (dissolved organic carbon) — electron donor consumed by microbes
- CO2, HCO3⁻, CO3²⁻, H⁺ — transported but not reacting (no abiotic kinetics,
  no equilibrium — pure transport)

**Kinetics (from `biotic/defineKinetics.hh`, compiled into your binary):**

```
µ = µ_max × [DOC] / (Ks + [DOC])     µ_max = 1.0/s,  Ks = 10⁻⁵ mol/L
dB/dt = (µ − k_decay) × B            k_decay = 10⁻⁹/s
dDOC/dt = −µ × B / Y                 Y = 0.4
```

**Initial conditions:**

- DOC = 0.1 mol/L (Dirichlet inlet)
- Biomass = 99 kg/m³ in biofilm voxels (material 3 and 6)
- Maximum biomass = 100 kg/m³

> **Important:** The biotic case uses `defineKinetics.hh`, not
> `defineAbioticKinetics.hh`. Check that your compiled binary uses the
> `biotic/defineKinetics.hh` provided here. Copy it to the repo root before
> building:
> 
> ```bash
> cp test_cases/biotic/defineKinetics.hh defineKinetics.hh
> cd build && make -j4 && cd ..
> ```

**Steps:**

```bash
mkdir -p my_runs/biotic && cd my_runs/biotic
cp ../../test_cases/biotic/CompLaB.xml ./CompLaB.xml
mkdir -p input
cp ../../test_cases/abiotic/input/geometry.dat ./input/geometry.dat
mpirun -np 4 ../../complab 2>&1 | tee run.log
```

**Expected output directory:** `output/` (the biotic XML uses `output_path=output`)



---

## Kinetics Recompilation Reference

Tests 2–5 each require a different kinetics header compiled into the solver.
The pattern is always the same:

```bash
# From the JOSS_Submit directory:
cp test_cases/abiotic/defineAbioticKinetics_testN.hh defineAbioticKinetics.hh
cd build
make -j4
cd ..
```

Then run the test from its working directory as shown above.

**Never mix headers** — running test 3 with the test 2 header compiled in
gives wrong rates and wrong concentrations. Always recompile before switching.

| Case    | Kinetics file                    | Rate law                     |
| ------- | -------------------------------- | ---------------------------- |
| Test 1  | none (kinetics off)              | pure diffusion               |
| Test 2  | `defineAbioticKinetics_test2.hh` | dA/dt = −k·A                 |
| Test 3  | `defineAbioticKinetics_test3.hh` | dA/dB/dC = ±k·A·B            |
| Test 4  | `defineAbioticKinetics_test4.hh` | dA/dt = −kf·A + kr·B         |
| Test 5  | `defineAbioticKinetics_test5.hh` | dA/dt=−k1·A, dB/dt=k1·A−k2·B |
| Eq case | none (equilibrium, runtime only) | PCF+AA carbonate             |
| Biotic  | `defineKinetics.hh`              | Monod growth                 |

---

## Troubleshooting

**Solver crashes immediately with exit code 255**

Usually means it cannot find the geometry file. Check:

```
ERROR: could not open input/geometry.dat
```

Fix: make sure `input/geometry.dat` exists **in the directory where you run
the solver**, not in the test_cases folder.

**Solver prints the wrong simulation mode**

Example: you see `BIOTIC mode: ENABLED` but you expected abiotic.

This means the solver read a different `CompLaB.xml` — either there was already
a `CompLaB.xml` in that directory from a previous run, or you forgot to copy
the test XML. The solver ignores any filename you pass on the command line.
Fix:

```bash
ls CompLaB.xml    # confirm it is in your current directory
head -5 CompLaB.xml   # confirm it is the right test file
```

**NaN detected in final concentrations**

Most common causes:

- `tau` value at or below 0.5 in the XML (check `<tau>`)
- Reaction rate too large — `rate × dt > concentration` causes the
  concentration to go negative and then diverge
- For the equilibrium case: initial concentrations are chemically inconsistent
  with the logK values — try running with `enable_validation_diagnostics=true`
  to see per-iteration equilibrium convergence

**Build fails when copying kinetics header**

Read the compiler error — it points to the exact line in the `.hh` file. The
most common issue is a missing semicolon or wrong variable name after editing.

**Solver exits after NS with no ADE output**

This is expected for the flow-only case (`ade_max_iT = 0`). For other cases,
check that `<ade_max_iT>` is greater than zero in your `CompLaB.xml`.

**MPI: "more processors than permitted" on a login node**

Login nodes on HPC clusters (e.g. GACRC Sapelo2) block multi-process MPI.
Use `mpirun -np 1` for a quick check, or submit a batch job:

```bash
mpirun -np 1 ./complab 2>&1 | tee run.log
```

**Parallel ParaView — VTK files appear incomplete**

Palabos writes one VTK per MPI rank, named `Tracer_0001000.vti.p0`,
`.p1`, etc. Open the `*.pvti` master file in ParaView, not the individual
rank files.
