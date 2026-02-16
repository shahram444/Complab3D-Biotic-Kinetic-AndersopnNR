============================================================
CompLaB3D Geometry File Info
Generated: 2026-02-16 13:10:38
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
  Solid                     (mask=0):      6,000 voxels ( 13.3%)
  Interface (bounce-back)   (mask=1):      5,200 voxels ( 11.6%)
  Pore                      (mask=2):     33,800 voxels ( 75.1%)

SUMMARY:
  Porosity (pore only):      0.7511  (75.1%)
  Biofilm coverage:          0.0%
  Open space (pore+biofilm): 75.1%

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
  Expected lines: 45,000
============================================================