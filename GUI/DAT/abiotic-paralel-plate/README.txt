============================================================
CompLaB3D Geometry File Info
Generated: 2026-02-16 13:11:55
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
  Solid                     (mask=0):     18,000 voxels ( 40.0%)
  Interface (bounce-back)   (mask=1):      3,000 voxels (  6.7%)
  Pore                      (mask=2):     24,000 voxels ( 53.3%)

SUMMARY:
  Porosity (pore only):      0.5333  (53.3%)
  Biofilm coverage:          0.0%
  Open space (pore+biofilm): 53.3%

GENERATION MODE: Abiotic - plates
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