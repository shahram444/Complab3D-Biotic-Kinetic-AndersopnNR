============================================================
CompLaB3D Geometry File Info
Generated: 2026-02-13 15:25:30
============================================================

DIMENSIONS:
  nx = 50  (flow direction, X-axis)
  ny = 30
  nz = 28
  Total voxels = 42,000

FLOW DIRECTION: X-axis
  Inlet:  x = 0
  Outlet: x = 49

MATERIAL COMPOSITION:
  Solid                     (mask=0):      5,800 voxels ( 13.8%)
  Interface (bounce-back)   (mask=1):      5,000 voxels ( 11.9%)
  Pore                      (mask=2):     27,600 voxels ( 65.7%)
  Microbe-1 core            (mask=3):      1,239 voxels (  3.0%)
  Microbe-2 core            (mask=4):      1,161 voxels (  2.8%)
  Microbe-1 fringe          (mask=6):        623 voxels (  1.5%)
  Microbe-2 fringe          (mask=7):        577 voxels (  1.4%)

SUMMARY:
  Porosity (pore only):      0.6571  (65.7%)
  Biofilm coverage:          8.6%
  Open space (pore+biofilm): 74.3%

GENERATION MODE: Sessile Biofilm - channel
  Scenario 10: Two-Zone SMTZ Style
  Two microbe species in separate zones
  Species: 2, Thickness: 3, Coverage: 100%

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
  Expected lines: 42,000
============================================================