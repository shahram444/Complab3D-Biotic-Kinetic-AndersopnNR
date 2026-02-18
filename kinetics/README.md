# Kinetics Template Pairs

Each folder contains a matched pair of `defineKinetics.hh` + `defineAbioticKinetics.hh`.
**Both files must always be present** because the C++ solver `#include`s both unconditionally.

## How to use

1. Choose a scenario folder below
2. Copy **both** `.hh` files to the **repository root** (next to `CompLaB.xml`)
3. Recompile: `cd build && cmake .. && make -j$(nproc)`
4. Run: `./complab` (or use the GUI Run button)

## Available scenarios

| Folder | Substrates | Microbes | Description |
|--------|-----------|----------|-------------|
| `01_flow_only` | 0 | 0 | Navier-Stokes flow only (both files are no-op stubs) |
| `02_single_tracer` | 1 | 0 | Transport of a passive tracer (no reactions) |
| `03_abiotic_first_order` | 1 | 0 | First-order decay: dA/dt = -k*A |
| `04_abiotic_bimolecular` | 3 | 0 | Second-order: A + B -> C |
| `05_biofilm_single_substrate` | 1 | 1 (CA) | Monod biofilm consuming DOC |
| `06_planktonic_single_substrate` | 1 | 1 (LBM) | Monod planktonic consuming DOC |

## Matching GUI templates

Each folder matches a GUI template by the same name. When you select a template
in **File > New Project**, the GUI auto-generates the matching `.hh` code.
These on-disk copies serve as reference and for manual workflows.
