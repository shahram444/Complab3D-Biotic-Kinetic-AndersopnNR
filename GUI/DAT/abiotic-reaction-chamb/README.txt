============================================================
CompLaB3D Geometry File Info
Generated: 2026-02-16 13:12:56
============================================================

DIMENSIONS:
  nx = 50  (flow direction, X-axis)
  ny = 30
  nz = 30
  Total voxels = 45,000

FLOW DIRECTION: X-axis
  Inlet:  x = 0
  Outlet: x = 49

MATERIAL COMPOSITION:
  Solid                     (mask=0):     18,862 voxels ( 41.9%)
  Interface (bounce-back)   (mask=1):      4,878 voxels ( 10.8%)
  Pore                      (mask=2):     21,260 voxels ( 47.2%)

SUMMARY:
  Porosity (pore only):      0.4724  (47.2%)
  Biofilm coverage:          0.0%
  Open space (pore+biofilm): 47.2%

GENERATION MODE: Abiotic - chamber
  Target porosity: 0.50

MASK VALUES:
  0 = Solid (impermeable)
  1 = Interface (bounce-back boundary)
  2 = Pore (open fluid space)
  3 = Microbe-1 core (dense biofilm)
  4 = Microbe-2 core
  5 = Microbe-3 core
  6 = Microbe-1 fringe (active growth zone)
  7 = Microbe-2 fringe
  8 = Microbe-3 fringe

FILE FORMAT:
  Text file, one voxel value per line
  Loop order: x -> z -> y (MATLAB convention)
  Expected lines: 45,000
============================================================