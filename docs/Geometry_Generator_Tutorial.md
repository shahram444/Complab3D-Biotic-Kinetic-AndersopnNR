# CompLaB3D Geometry Generator v6.0 - Complete Tutorial

## Overview

The Geometry Generator creates 3D porous media geometries for CompLaB3D simulations. It supports:

1. **ABIOTIC domains** - Porous media without biofilm (for abiotic kinetics simulations)
2. **SESSILE BIOFILM geometries** - Porous media with attached biofilm (14 scenarios)
3. **IMAGE CONVERTER** - Convert image stacks (CT scans, microscopy) to geometry files

## Installation & Requirements

```bash
# Required
pip install numpy pillow

# Optional (for visualization)
pip install matplotlib
```

## Running the Generator

```bash
cd tools
python geometry_generator.py
```

This launches an interactive menu:

```
======================================================================
  CompLaB3D GEOMETRY GENERATOR v6.0
  THREE GENERATORS: ABIOTIC | BIOFILM | IMAGE CONVERTER
======================================================================

  1 = ABIOTIC Domain Generator (porous media without biofilm)
  2 = SESSILE BIOFILM Generator (with biofilm)
  3 = IMAGE CONVERTER (convert image stacks to .dat)
  4 = Exit

  Your choice (1-4) [1]:
```

---

## 1. ABIOTIC Domain Generator

Use this for simulations **without microorganisms** (pure transport or abiotic kinetics).

### Step-by-Step Guide

```
STEP 1: Select Medium Type
-----------------------------------
  1 = Rectangular Channel (simple hollow box)
  2 = Parallel Plates (two parallel surfaces)
  3 = Overlapping Spheres (porous media - most realistic)
  4 = Reaction Chamber (fully enclosed)
  5 = Hollow Box (partially open)
```

### Medium Types Explained

| Type | Description | Best For |
|------|-------------|----------|
| **1. Rectangular Channel** | Simple hollow rectangular tube | Basic flow tests, validation |
| **2. Parallel Plates** | Two parallel surfaces with gap | 2D-like flow, Poiseuille flow |
| **3. Overlapping Spheres** | Random spheres create porous media | Realistic porous media, aquifer simulation |
| **4. Reaction Chamber** | Narrow inlet/outlet, wide middle | Batch reactors, mixing zones |
| **5. Hollow Box** | Partially open box | General purpose |

### Parameters

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| **NX** | Flow direction (number of slices) | 50-200 |
| **NY** | Width | 30-100 |
| **NZ** | Height | 30-100 |
| **Porosity** | Fraction of open space | 0.3-0.7 |

### Example: Creating Porous Media

```
Select (1-5) [1]: 3              # Overlapping Spheres
NX (flow direction) [50]: 100
NY [30]: 50
NZ [30]: 50
Target porosity (0.3-0.9) [0.5]: 0.45
Folder name [abiotic_domain]: my_porous_media
```

### Output Files

```
my_porous_media_20240206_143022/
├── input/
│   └── geometry.dat          # Main geometry file for CompLaB3D
├── images/
│   ├── slice_0000.png       # B/W slice images
│   ├── slice_0001.png
│   └── ...
├── geometry_abiotic_Spheres.png   # Visualization
└── geometry_abiotic_Spheres.pdf   # Publication-quality figure
```

---

## 2. SESSILE BIOFILM Generator

Use this for simulations **with microorganisms** attached to surfaces.

### 14 Biofilm Scenarios

#### Single Species (1-9)

| # | Scenario | Description |
|---|----------|-------------|
| 1 | Bottom Wall Biofilm | Biofilm on bottom Y wall |
| 2 | Top Wall Biofilm | Biofilm on top Y wall |
| 3 | Both Walls Biofilm | Biofilm on top and bottom walls |
| 4 | All Walls Coating | Biofilm coating all surfaces |
| 5 | Inlet Region | Biofilm concentrated near inlet (x=0) |
| 6 | Outlet Region | Biofilm concentrated near outlet |
| 7 | Center Region | Biofilm in center of domain |
| 8 | Random Patches | Random biofilm patches |
| 9 | Hemispherical Colonies | Dome-shaped colonies on surface |

#### Two Species (10-12)

| # | Scenario | Description |
|---|----------|-------------|
| 10 | Two-Zone SMTZ | Two species in separate zones (sulfate-methane transition zone style) |
| 11 | Competing Biofilms | Checkerboard pattern of two species |
| 12 | Layered Biofilm | One species on top of another |

#### Three Species (13)

| # | Scenario | Description |
|---|----------|-------------|
| 13 | Three Species Zones | Three species in three zones along flow |

#### Porous Media (14)

| # | Scenario | Description |
|---|----------|-------------|
| 14 | Grain Surface Coating | Biofilm coating grain surfaces |

### Biofilm Parameters

| Parameter | Description | Typical Values |
|-----------|-------------|----------------|
| **Thickness** | Biofilm thickness in voxels | 2-5 |
| **Coverage** | Fraction of surface covered | 0.5-1.0 |

### Example: Two-Zone SMTZ Biofilm

```
Select scenario (1-14) [1]: 10      # Two-Zone SMTZ
Select medium (1-5) [1]: 1          # Rectangular Channel
NX (flow direction) [50]: 100
NY [30]: 40
NZ [30]: 40
Target porosity (0.3-0.9) [0.5]: 0.6
Biofilm thickness (voxels) [3]: 3
Biofilm coverage (0.0-1.0) [1.0]: 0.9
Output folder name [sessile_biofilm]: smtz_simulation
```

### Mask Values in Output

| Mask | Material | Description |
|------|----------|-------------|
| 0 | Solid | Impermeable grain/wall |
| 1 | Interface | Bounce-back boundary (solid-fluid interface) |
| 2 | Pore | Open fluid space |
| 3 | Microbe-1 Core | Dense biofilm (species 1) |
| 4 | Microbe-2 Core | Dense biofilm (species 2) |
| 5 | Microbe-3 Core | Dense biofilm (species 3) |
| 6 | Microbe-1 Fringe | Active growth zone (species 1) |
| 7 | Microbe-2 Fringe | Active growth zone (species 2) |
| 8 | Microbe-3 Fringe | Active growth zone (species 3) |

### Core vs Fringe

- **Core**: Interior biofilm cells (dense, lower activity)
- **Fringe**: Biofilm cells adjacent to pore space (active growth zone)

The fringe is automatically marked as cells adjacent to open pore space.

---

## 3. IMAGE CONVERTER

Convert microscopy images or CT scan slices to CompLaB3D geometry.

### Supported Formats

- PNG, BMP, TIFF, JPG

### Image Requirements

1. All images must be the same size
2. Images are interpreted as YZ slices along X (flow direction)
3. **BLACK** (pixel < 128) = PORE space
4. **WHITE** (pixel >= 128) = SOLID

### Example Usage

```
Image folder path: /path/to/ct_slices
Output name [converted]: my_rock_sample
```

### Preparing Images

If your images have different convention (white = pore):

```python
# Invert images using Python
from PIL import Image
import os

for f in os.listdir('input_folder'):
    img = Image.open(f'input_folder/{f}')
    inverted = Image.eval(img, lambda x: 255 - x)
    inverted.save(f'output_folder/{f}')
```

---

## Using Generated Geometry in CompLaB3D

### 1. Copy geometry file to simulation folder

```bash
cp my_geometry/input/geometry.dat /path/to/simulation/input/
```

### 2. Update XML configuration

```xml
<geometry>
    <file>input/geometry.dat</file>
    <nx>100</nx>
    <ny>50</ny>
    <nz>50</nz>
</geometry>
```

### 3. Ensure dimensions match

The NX, NY, NZ in XML **must match** the generated geometry dimensions.

---

## Flow Direction Convention

```
        Z
        ^
        |
        |
        +-------> Y
       /
      /
     v
    X (FLOW DIRECTION)

    Inlet:  x = 0
    Outlet: x = nx-1
```

- Flow is along the **X-axis**
- **Inlet** at x = 0 (first slice)
- **Outlet** at x = nx-1 (last slice)
- Walls on Y and Z boundaries

---

## Programmatic Usage

You can also use the generator as a Python library:

```python
from geometry_generator import (
    create_overlapping_spheres,
    create_rectangular_channel,
    place_biofilm_bottom_wall,
    save_dat,
    save_slice_images
)

# Create porous medium
geometry, porosity = create_overlapping_spheres(
    nx=100, ny=50, nz=50,
    target_porosity=0.45
)

# Add biofilm
geometry = place_biofilm_bottom_wall(
    geometry,
    microbe_idx=0,
    thickness=3,
    coverage=0.9
)

# Save
save_dat(geometry, 'geometry.dat')
save_slice_images(geometry, 'images/')
```

### Available Functions

#### Medium Creators

```python
# Simple channel
geometry, phi = create_rectangular_channel(nx, ny, nz, wall_thickness=2)

# Parallel plates
geometry, phi = create_parallel_plates(nx, ny, nz, target_porosity=0.5)

# Porous media (random spheres)
geometry, phi = create_overlapping_spheres(nx, ny, nz, target_porosity=0.5)

# Reaction chamber
geometry, phi = create_reaction_chamber(nx, ny, nz)

# Hollow box
geometry, phi = create_hollow_box(nx, ny, nz, target_porosity=0.7)
```

#### Biofilm Placement

```python
# Single species
place_biofilm_bottom_wall(geometry, microbe_idx=0, thickness=3, coverage=1.0)
place_biofilm_top_wall(geometry, microbe_idx=0, thickness=3, coverage=1.0)
place_biofilm_both_walls(geometry, microbe_idx=0, thickness=3, coverage=1.0)
place_biofilm_all_walls(geometry, microbe_idx=0, thickness=2, coverage=1.0)
place_biofilm_inlet(geometry, microbe_idx=0, thickness=3, depth_fraction=0.2)
place_biofilm_outlet(geometry, microbe_idx=0, thickness=3, depth_fraction=0.2)
place_biofilm_center(geometry, microbe_idx=0, thickness=3, center_fraction=0.4)
place_biofilm_random_patches(geometry, microbe_idx=0, num_patches=15)
place_biofilm_hemispheres(geometry, microbe_idx=0, num_bumps=20)

# Multiple species
place_biofilm_two_zones(geometry, thickness=3, coverage=1.0)
place_biofilm_competing(geometry, thickness=3, coverage=0.8)
place_biofilm_layered(geometry, layer1_thickness=2, layer2_thickness=2)
place_biofilm_three_zones(geometry, thickness=3, coverage=1.0)
place_biofilm_grain_coating(geometry, microbe_idx=0, thickness=1, coverage=0.7)
```

---

## Visualization

The generator creates publication-quality figures (PNG + PDF) showing:

1. **XY plane** (mid-Z slice) - Top view
2. **XZ plane** (mid-Y slice) - Side view
3. **YZ plane** (mid-X slice) - Cross-section

Colors:
- Dark gray: Solid
- Orange: Interface (bounce-back)
- Blue: Pore
- Green: Microbe-1 core
- Light green: Microbe-1 fringe
- Pink: Microbe-2 core
- Light pink: Microbe-2 fringe
- Yellow: Microbe-3 core
- Light yellow: Microbe-3 fringe

---

## Tips & Best Practices

### 1. Choosing Domain Size

- Start small (50x30x30) for testing
- Production runs: 100x50x50 or larger
- Memory scales as nx * ny * nz

### 2. Porosity Selection

| Application | Recommended Porosity |
|-------------|---------------------|
| Tight sandstone | 0.15-0.25 |
| Typical aquifer | 0.25-0.40 |
| Loose sand | 0.35-0.50 |
| Biofilm reactor | 0.50-0.70 |

### 3. Biofilm Thickness

- 1-2 voxels: Thin coating
- 3-4 voxels: Moderate biofilm
- 5+ voxels: Thick biofilm (may block flow)

### 4. Ensuring Flow Connectivity

The generator automatically ensures inlet (x=0) and outlet (x=nx-1) are open for flow.

---

## Troubleshooting

### "No pore space created"

- Increase target porosity
- Reduce number of spheres (for overlapping spheres method)

### "Biofilm blocks all flow"

- Reduce biofilm thickness
- Reduce coverage
- Use larger domain

### "Dimensions don't match XML"

- Check nx, ny, nz in geometry README.txt
- Update XML to match exactly

---

## File Format: geometry.dat

The .dat file format is simple text:

```
0
0
1
2
2
2
...
```

One value per line, ordered as:
- Loop X (outer)
  - Loop Z (middle)
    - Loop Y (inner)

Total lines = nx * ny * nz

---

## Authors

Shahram Asgari & Christof Meile
Department of Marine Sciences
University of Georgia, Athens, GA, United States
