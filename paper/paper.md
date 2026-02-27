---
title: "CompLaB3D: A 3D Pore-Scale Biogeochemical Reactive Transport Simulator"
tags:
  - Python
  - C++
  - lattice Boltzmann method
  - reactive transport
  - biofilm
  - pore-scale modelling
  - biogeochemistry
authors:
  - name: Shahram Asgari
    orcid: 0000-0000-0000-0000
    affiliation: 1
affiliations:
  - name: University of Georgia, USA
    index: 1
date: 1 January 2025
bibliography: paper.bib
---

# Summary

CompLaB3D is an open-source, MPI-parallel 3D pore-scale reactive transport
simulator that couples Lattice Boltzmann Method (LBM) flow and
advection-diffusion with biotic kinetics, abiotic chemical reactions,
cellular-automata biofilm growth, and equilibrium chemistry. It is designed
for researchers studying subsurface biogeochemical processes at the pore
scale, such as bioremediation, mineral dissolution, and microbially induced
calcite precipitation.

The software consists of two integrated components: (1) a C++ solver built
on the Palabos LBM library [@latt2021palabos] that performs Navier-Stokes
flow, multi-species advection-diffusion, Monod biotic kinetics, first-order
abiotic reactions, cellular-automata biofilm expansion, and Newton-Raphson
equilibrium solving with Anderson acceleration; and (2) CompLaB Studio, a
Python GUI built with PySide6 that provides scenario configuration, XML
generation, 3D geometry viewing, solver management, and result visualisation.

# Statement of Need

Pore-scale reactive transport modelling is essential for understanding how
fluid flow, solute transport, microbial activity, and chemical reactions
interact within complex 3D pore geometries. Existing tools in this space
either focus solely on flow and transport without biofilm dynamics, require
commercial licences, or lack an accessible graphical interface for
configuring multi-physics scenarios.

CompLaB3D addresses these gaps by:

- Coupling LBM transport with Monod biotic kinetics and cellular-automata
  biofilm growth in a single, unified framework.
- Providing an operator-splitting architecture that cleanly separates
  transport, kinetics, and equilibrium steps, making it straightforward to
  add new reaction models.
- Offering nine ready-to-use scenario templates ranging from simple
  flow-only simulations to fully coupled biotic-abiotic systems.
- Including CompLaB Studio, a GUI that lowers the barrier to entry for
  researchers who are not comfortable editing XML configuration files and
  C++ kinetics headers by hand.

The target audience includes environmental engineers, hydrogeologists,
microbiologists, and computational scientists working on subsurface reactive
transport problems.

# Architecture

CompLaB3D uses an **operator-splitting** approach. Each simulation timestep
is divided into three sequential stages:

1. **Transport (LBM ADE):** Advection-diffusion of dissolved substrates and
   planktonic biomass is solved using the Lattice Boltzmann
   advection-diffusion equation on a D3Q7 lattice.
2. **Kinetics:** Biotic reactions follow the Monod model
   ($\mu = \mu_{\max} \cdot C / (K_s + C)$) with substrate consumption
   scaled by a yield coefficient. Abiotic reactions support first-order
   decay. Biomass growth, decay, and substrate uptake are computed at every
   lattice node.
3. **Equilibrium:** Aqueous speciation (e.g., carbonate equilibrium) is
   solved via Newton-Raphson iteration with Anderson acceleration
   [@anderson1965iterative] for robust convergence.

Biofilm is modelled as a discrete solid phase on the lattice. A
cellular-automata algorithm handles biomass spreading into neighbouring
pore nodes when local biomass exceeds a threshold, and detachment when
shear stress exceeds a critical value. Flow fields are updated dynamically
as the pore geometry evolves.

The solver reads an XML configuration file that specifies domain geometry,
fluid properties, substrate parameters, microbial kinetics, and output
settings. Kinetics are defined in pluggable C++ header files (`.hh`),
allowing users to implement custom reaction models without modifying the
core solver.

# CompLaB Studio

CompLaB Studio is a cross-platform GUI written in Python with PySide6
(Qt 6). It provides:

- A **template selector** with nine pre-configured scenarios.
- **Substrate and microbe editors** with input validation and
  cross-referencing.
- **XML generation and parsing** for the solver configuration file.
- **Kinetics code generation** producing ready-to-compile `.hh` header
  files.
- A **3D geometry viewer** (VTK) for inspecting pore structures.
- A **solver panel** for launching MPI runs and monitoring progress.
- A **geometry generator** for creating synthetic pore structures.

The GUI has a comprehensive test suite of 93 automated tests covering
template generation, XML building and parsing, kinetics code generation,
cross-validation logic, and end-to-end pipeline flows.

# Acknowledgements

The author acknowledges the Palabos development team for the open-source
LBM library on which the flow solver is built.

# References
