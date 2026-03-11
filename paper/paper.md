---
title: 'CompLaB3D: A Three-Dimensional Pore-Scale Reactive Transport Solver Coupling Lattice Boltzmann Methods with Biogeochemical Kinetics'
tags:
  - C++
  - Python
  - reactive transport
  - lattice Boltzmann method
  - biofilm
  - pore-scale modeling
  - biogeochemistry
  - equilibrium chemistry
authors:
  - name: Shahram Asgari
    orcid: 0009-0004-3810-2739
    corresponding: true
    affiliation: 1
  - name: Christof Meile
    affiliation: 1
affiliations:
  - name: Department of Marine Sciences, University of Georgia, Athens, GA, United States
    index: 1
date: 11 March 2026
bibliography: paper.bib
---

# Summary

CompLaB3D is an open-source three-dimensional reactive transport solver for
simulating biogeochemical processes in porous media at the pore scale. The
software couples a Lattice Boltzmann Method (LBM) flow solver (D3Q19 for
Navier--Stokes, D3Q7 for advection--diffusion) with Monod-based microbial
kinetics, abiotic chemical reactions, and an equilibrium chemistry solver
accelerated by Anderson mixing. Biofilm growth and morphology are resolved
through a cellular automaton (CA) that dynamically updates the pore geometry,
creating a fully coupled feedback between fluid flow, solute transport, microbial
metabolism, and mineral--fluid interactions. CompLaB3D includes CompLaB Studio, a
cross-platform graphical user interface (GUI) built with PySide6 that provides
project configuration, code generation, simulation management, and
post-processing capabilities without requiring direct XML editing or command-line
interaction.

# Statement of need

Pore-scale reactive transport modeling is essential for understanding how
microscale processes---such as biofilm formation, mineral dissolution, and
nutrient cycling---control macroscopic fluxes in sediments, soils, and
engineered systems [@Steefel:2005; @Meile:2005]. Existing tools typically
address subsets of these coupled processes. Continuum-scale codes like
CrunchFlow [@Steefel:2015] and PFLOTRAN [@Lichtner:2015] operate at scales
above the pore level, while pore-network models [@Raoof:2013] simplify the
geometry. Pore-scale LBM codes such as Palabos [@Latt:2021] provide
high-fidelity flow and transport but lack built-in biogeochemical reaction
frameworks. OpenLB [@Krause:2021] offers a general-purpose LBM platform but
requires users to implement their own reactive transport coupling. Standalone
biofilm models [@Picioreanu:2004] typically do not resolve three-dimensional
pore-scale flow feedback.

CompLaB3D fills this gap by providing an integrated, ready-to-use solver that
couples all three processes---flow, transport, and biogeochemical
reactions---within a single framework. It targets researchers in environmental
science, geomicrobiology, and subsurface engineering who need to investigate how
pore-scale heterogeneity and biofilm dynamics affect bulk transport properties
such as permeability, breakthrough curves, and reaction rates. The GUI
(CompLaB Studio) lowers the barrier to entry for users unfamiliar with LBM
theory, enabling them to set up simulations through a visual interface,
generate the required C++ kinetics headers, and launch MPI-parallel runs
without writing code.

# State of the field

Pore-scale reactive transport has gained significant attention over the past two
decades as experimental imaging (micro-CT, confocal microscopy) has made
three-dimensional pore geometries routinely available [@Blunt:2013]. Several
modeling approaches coexist:

- **Continuum-scale codes** (CrunchFlow, PFLOTRAN, TOUGHREACT [@Xu:2012])
  solve coupled flow--transport--reaction systems on representative elementary
  volumes but cannot resolve individual pores or biofilm morphology.
- **Pore-network models** [@Raoof:2013] approximate the pore space as a graph
  of idealized throats and bodies, offering computational efficiency at the cost
  of geometric fidelity.
- **Direct numerical simulation** with LBM or finite-volume methods on
  voxelized geometries provides the highest spatial resolution. Palabos
  [@Latt:2021] and OpenLB [@Krause:2021] supply the LBM infrastructure but
  leave reaction coupling to the user. Dedicated biofilm--LBM codes exist
  [@Picioreanu:2004; @Tang:2017] but are often limited to two dimensions,
  specific reaction systems, or closed-source implementations.

CompLaB3D contributes to this landscape by coupling a D3Q19/D3Q7 LBM solver
with operator-split biogeochemical kinetics and a Newton--Raphson equilibrium
solver with Anderson acceleration, all in a single open-source package with a
GUI front-end. This combination of three-dimensional pore-scale resolution,
flexible kinetics specification, equilibrium chemistry, and accessibility
through CompLaB Studio distinguishes it from existing tools.

# Software design

CompLaB3D follows an **operator-splitting** architecture that decomposes each
timestep into sequential sub-problems (\autoref{fig:architecture}):

1. **Transport** (LBM): D3Q19 lattice Boltzmann solves the incompressible
   Navier--Stokes equations for the velocity field; D3Q7 lattice Boltzmann
   solves the advection--diffusion equation for each dissolved species.
2. **Kinetics**: Monod saturation kinetics compute microbial growth, substrate
   consumption, and metabolic product generation. Abiotic reactions (first-order
   decay, bimolecular, reversible) are handled in a separate operator.
3. **Equilibrium**: A Newton--Raphson solver with QR-factored Jacobian and
   Anderson acceleration (depth $m$) solves the mass-action system
   $\mathbf{K} = \prod c_i^{\nu_{ij}}$ for aqueous speciation.
4. **Biofilm expansion**: A cellular automaton redistributes excess biomass to
   neighboring pore voxels, updating the solid--fluid boundary and triggering
   flow-field recalculation.

The solver is implemented in C++ (approximately 5,800 lines) using the Palabos
library [@Latt:2021] for LBM lattice management and MPI parallelism. Kinetics
are defined in swappable `.hh` header files, allowing users to modify reaction
systems without recompiling the core solver. The equilibrium solver uses a
Partial Component Formulation (PCF) that reduces the nonlinear system dimension
from the number of species to the number of components.

![CompLaB3D operator-splitting architecture. Each timestep cycles through
transport (LBM collision and streaming), biotic and abiotic kinetics, equilibrium
chemistry, and biofilm expansion. The cellular automaton updates the pore
geometry, which feeds back into the flow
solver.\label{fig:architecture}](architecture.png){ width=80% }

**CompLaB Studio** is the Python GUI (PySide6, approximately 8,000 lines) that
provides:

- Visual project configuration for all nine simulation modes (flow-only through
  coupled biotic--abiotic with equilibrium).
- Automatic C++ kinetics header generation with cross-validation against the
  project configuration to prevent array-index mismatches.
- MPI-aware simulation launching with real-time progress parsing and convergence
  monitoring.
- Post-processing views for VTI output files.

## Testing

CompLaB3D includes a comprehensive test suite:

- **130 C++ unit tests** (GoogleTest/CTest) covering LBM stability checks,
  abiotic and biotic kinetics, planktonic kinetics, the equilibrium solver
  (convergence, mass conservation, QR decomposition), D3Q7 population encoding,
  finite-difference Laplacian, Darcy flow, and biofilm expansion logic.
- **275+ Python tests** (pytest) covering the GUI panels, XML/JSON
  serialization round-trips, kinetics code generation and cross-validation,
  simulation runner lifecycle, and end-to-end pipeline tests for all nine
  simulation templates.
- **5 analytical validation cases** comparing solver output against closed-form
  solutions for pure diffusion, first-order decay, bimolecular reaction,
  reversible equilibrium, and sequential decay chains (Bateman equations).
- **Continuous integration** via GitHub Actions runs both C++ and Python test
  suites on every push.

# Research impact statement

CompLaB3D was developed to support research on biogeochemical cycling in marine
and freshwater sediments at the Meile Lab, University of Georgia. The solver
enables investigation of how pore-scale biofilm growth alters permeability and
solute transport in natural and engineered porous media. The modular kinetics
system allows researchers to define arbitrary reaction networks---from simple
first-order decay to multi-substrate Monod systems coupled with equilibrium
speciation---making the software applicable across environmental science,
geomicrobiology, bioremediation, and subsurface carbon storage research.

The inclusion of CompLaB Studio as a GUI front-end extends the potential user
base to experimentalists and students who may not have experience with LBM
theory or C++ programming but need to interpret pore-scale imaging data in the
context of reactive transport.

# AI usage disclosure

Generative AI tools (Claude, Anthropic) were used to assist with: documentation
writing, test scaffolding and generation, GUI code structure, and copy-editing.
All AI-assisted outputs were reviewed, edited, and validated by the human
authors, who made all core design decisions regarding the solver architecture,
numerical methods, and scientific formulation.

# Acknowledgements

We acknowledge the Palabos development team for providing the open-source LBM
framework upon which CompLaB3D is built. This work was supported by the
University of Georgia Department of Marine Sciences.

# References
