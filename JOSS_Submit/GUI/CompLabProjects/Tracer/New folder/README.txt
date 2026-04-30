============================================================
CompLaB3D Geometry File Info
Generated: 2026-04-30 06:08:36
============================================================

DIMENSIONS:
  nx = 20  (flow direction, X-axis)
  ny = 20
  nz = 20
  Total voxels = 8,000

FLOW DIRECTION: X-axis
  Inlet:  x = 0
  Outlet: x = 19

MATERIAL COMPOSITION:
  Solid                     (mask=0):      1,600 voxels ( 20.0%)
  Interface (bounce-back)   (mask=1):      1,280 voxels ( 16.0%)
  Pore                      (mask=2):      5,120 voxels ( 64.0%)

SUMMARY:
  Porosity (pore only):      0.6400  (64.0%)
  Biofilm coverage:          0.0%
  Open space (pore+biofilm): 64.0%

GENERATION MODE: Abiotic - channel
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
  Expected lines: 8,000
============================================================