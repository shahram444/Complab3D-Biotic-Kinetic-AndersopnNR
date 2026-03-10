---
title: "CompLaB3D: A 3D Pore-Scale Biogeochemical Reactive Transport Simulator with an Integrated GUI"
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
    corresponding: true
affiliations:
  - name: Department of Marine Sciences, University of Georgia, Athens, GA, USA
    index: 1
date: 10 March 2026
bibliography: paper.bib
---

# Summary

CompLaB3D is an open-source, MPI-parallel, three-dimensional pore-scale
reactive transport simulator that couples Lattice Boltzmann Method (LBM)
flow and advection-diffusion with biotic kinetics, abiotic chemical
reactions, cellular-automata biofilm growth, and equilibrium chemistry
solving. It targets researchers studying subsurface biogeochemical
processes at the pore scale, including bioremediation, mineral
dissolution, and microbially induced calcite precipitation.

The software comprises two integrated components. First, a C++ solver
built on the Palabos LBM library [@latt2021palabos] performs
Navier-Stokes flow, multi-species advection-diffusion on a D3Q7 lattice,
Monod biotic kinetics [@monod1949growth], first-order abiotic reactions,
cellular-automata biofilm expansion and detachment
[@rittmann2001biofilms], and Newton-Raphson equilibrium solving with
Anderson acceleration [@anderson1965iterative]. Second, CompLaB Studio
is a cross-platform Python GUI built with PySide6 that provides scenario
configuration through nine ready-to-use templates, XML generation,
kinetics code generation, 3D geometry viewing via VTK, solver
management, and result visualisation.

# Statement of Need

Pore-scale reactive transport modelling is essential for understanding
how fluid flow, solute transport, microbial activity, and chemical
reactions interact within complex three-dimensional pore geometries
[@steefel2015reactive]. Existing tools in this space either focus solely
on flow and transport without biofilm dynamics
[@kang2006lattice; @molins2012investigation], require commercial
licences, or lack an accessible graphical interface for configuring
multi-physics scenarios. OpenLB [@krause2021openlb] and Palabos
[@latt2021palabos] provide excellent LBM frameworks but do not include
integrated biogeochemical reaction modules or user-facing GUIs.

CompLaB3D addresses these gaps by:

- Coupling LBM transport with Monod biotic kinetics and
  cellular-automata biofilm growth in a single, unified framework.
- Providing an operator-splitting architecture that cleanly separates
  transport, kinetics, and equilibrium steps, making it straightforward
  to add new reaction models.
- Offering nine ready-to-use scenario templates ranging from simple
  flow-only simulations to fully coupled biotic-abiotic systems.
- Including CompLaB Studio, a GUI that lowers the barrier to entry for
  researchers who are not comfortable editing XML configuration files
  and C++ kinetics headers by hand.

The target audience includes environmental engineers, hydrogeologists,
microbiologists, and computational scientists working on subsurface
reactive transport problems.

# Architecture

CompLaB3D uses an operator-splitting approach (\autoref{fig:architecture}).
Each simulation timestep is divided into sequential stages:

1. **Transport (LBM ADE):** Advection-diffusion of dissolved substrates
   and planktonic biomass is solved using the Lattice Boltzmann
   advection-diffusion equation on a D3Q7 lattice [@succi2001lattice].
2. **Kinetics:** Biotic reactions follow the Monod model
   ($\mu = \mu_{\max} \cdot C / (K_s + C)$) with substrate consumption
   scaled by a yield coefficient. Abiotic reactions support first-order
   decay. Biomass growth, decay, and substrate uptake are computed at
   every lattice node.
3. **Equilibrium:** Aqueous speciation (e.g., carbonate equilibrium) is
   solved via Newton-Raphson iteration with Anderson acceleration
   [@anderson1965iterative] for robust convergence.
4. **Biofilm update:** A cellular-automata algorithm handles biomass
   spreading into neighbouring pore nodes when local biomass exceeds a
   threshold, and detachment when shear stress exceeds a critical value.
   Flow fields are updated dynamically as the pore geometry evolves.

![CompLaB3D architecture showing the GUI layer, the C++ solver with its
operator-splitting stages (transport, kinetics, equilibrium, biofilm
update), and VTI output for visualisation.\label{fig:architecture}](architecture.png){width=95%}

The solver reads an XML configuration file specifying domain geometry,
fluid properties, substrate parameters, microbial kinetics, and output
settings. Kinetics are defined in pluggable C++ header files (`.hh`),
allowing users to implement custom reaction models without modifying the
core solver.

# CompLaB Studio

CompLaB Studio is a cross-platform GUI written in Python with PySide6
(Qt 6). It provides a template selector with nine pre-configured
scenarios, substrate and microbe editors with input validation and
cross-referencing, XML generation and parsing for the solver
configuration file, kinetics code generation producing ready-to-compile
`.hh` header files, a 3D geometry viewer (VTK) for inspecting pore
structures, a solver panel for launching MPI runs and monitoring
progress, and a geometry generator for creating synthetic pore
structures.

The GUI ships with a comprehensive test suite of 275 automated tests
covering template generation, XML building and parsing, kinetics code
generation, cross-validation logic, and end-to-end pipeline flows.

# Acknowledgements

The author acknowledges the Palabos development team for the open-source
LBM library on which the flow solver is built, and Dr. Christof Meile
at the University of Georgia for guidance on the biogeochemical
modelling framework.

# References
