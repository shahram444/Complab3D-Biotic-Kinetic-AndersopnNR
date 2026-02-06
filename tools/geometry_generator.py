# -*- coding: utf-8 -*-
"""
================================================================================
 CompLaB3D Geometry Generator v6.0
================================================================================

 DEVELOPED BY:
   Shahram Asgari & Christof Meile
   Department of Marine Sciences
   University of Georgia, Athens, GA, United States

================================================================================

 VERSION 6.0 - IMPROVED MENU WITH THREE GENERATORS

 KEY IMPROVEMENTS:
   - NEW: Step-by-step guided menu system (no confusion!)
   - ABIOTIC DOMAIN GENERATOR: Create porous media without biofilm (5 options)
   - SESSILE BIOFILM GENERATOR: Create biofilm geometries (14 scenarios)
   - IMAGE CONVERTER: Convert image stacks to geometry (same as v5.7)
   - All v5.7 functionality preserved
   - Enhanced user guidance at every step
   - Input validation and default values

 FLOW DIRECTION: X-axis (MATLAB convention)
   - Inlet at x=0
   - Outlet at x=nx-1
   - Walls on Y and Z boundaries

================================================================================
"""

import numpy as np
from PIL import Image
import os
import glob
from datetime import datetime

# =============================================================================
# MATPLOTLIB CONFIGURATION
# =============================================================================

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    from matplotlib.colors import ListedColormap, BoundaryNorm
    from matplotlib.patches import Rectangle
    HAS_MATPLOTLIB = True

    import matplotlib.font_manager as fm
    available = [f.name for f in fm.fontManager.ttflist]
    if 'Arial' in available:
        FONT_NAME = 'Arial'
    elif 'Helvetica' in available:
        FONT_NAME = 'Helvetica'
    else:
        FONT_NAME = 'DejaVu Sans'

except ImportError:
    HAS_MATPLOTLIB = False
    FONT_NAME = 'Arial'

# =============================================================================
# CONSTANTS
# =============================================================================

SINGLE_COL_WIDTH = 3.504
DOUBLE_COL_WIDTH = 7.205
MAX_HEIGHT = 9.724

FONT_AXIS_LABEL = 8
FONT_TICK_LABEL = 7
FONT_LEGEND = 8
FONT_PANEL_LABEL = 11
FONT_TITLE = 9
FONT_SCALEBAR = 8
FONT_MIN = 6

DPI_MIXED = 600

AXIS_LINE_WIDTH = 0.75
TICK_WIDTH = 0.5

# Extended colors for multiple microbes with core/fringe
COLORS = {
    0: '#2b2b2b',    # Solid - dark gray
    1: '#e69f00',    # Interface - orange
    2: '#0072b2',    # Pore - blue
    3: '#009e73',    # Microbe-1 core - green
    4: '#cc79a7',    # Microbe-2 core - pink
    5: '#f0e442',    # Microbe-3 core - yellow
    6: '#66c2a5',    # Microbe-1 fringe - light green
    7: '#e0a0c0',    # Microbe-2 fringe - light pink
    8: '#f5f0a0',    # Microbe-3 fringe - light yellow
}

COLORS_RGB = {
    0: (43, 43, 43),
    1: (230, 159, 0),
    2: (0, 114, 178),
    3: (0, 158, 115),
    4: (204, 121, 167),
    5: (240, 228, 66),
    6: (102, 194, 165),
    7: (224, 160, 192),
    8: (245, 240, 160),
}

NAMES = {
    0: 'Solid',
    1: 'Interface',
    2: 'Pore',
    3: 'Microbe-1 core',
    4: 'Microbe-2 core',
    5: 'Microbe-3 core',
    6: 'Microbe-1 fringe',
    7: 'Microbe-2 fringe',
    8: 'Microbe-3 fringe',
}

# =============================================================================
# MATERIAL CONFIGURATION
# =============================================================================

class MaterialConfig:
    def __init__(self):
        self.solid = 0
        self.interface = 1
        self.pore = 2
        # Each sessile microbe gets two mask IDs: (core, fringe)
        # microbe 0 -> core=3, fringe=6
        # microbe 1 -> core=4, fringe=7
        # microbe 2 -> core=5, fringe=8
        self.microbe_cores = [3, 4, 5]
        self.microbe_fringes = [6, 7, 8]

    def get_microbe_id(self, idx):
        """Return CORE mask for microbe idx (backward compatible)."""
        return self.microbe_cores[idx] if idx < len(self.microbe_cores) else 3 + idx

    def get_microbe_core(self, idx):
        """Return core mask ID for microbe idx."""
        return self.microbe_cores[idx] if idx < len(self.microbe_cores) else 3 + idx

    def get_microbe_fringe(self, idx):
        """Return fringe mask ID for microbe idx."""
        return self.microbe_fringes[idx] if idx < len(self.microbe_fringes) else 6 + idx

    def get_microbe_masks(self, idx):
        """Return (core, fringe) mask pair for microbe idx."""
        return (self.get_microbe_core(idx), self.get_microbe_fringe(idx))

    def get_color(self, mat_id):
        return COLORS.get(mat_id, '#888888')

    def get_color_rgb(self, mat_id):
        return COLORS_RGB.get(mat_id, (136, 136, 136))

    def get_name(self, mat_id):
        return NAMES.get(mat_id, f'Material {mat_id}')

MAT = MaterialConfig()

# =============================================================================
# SESSILE BIOFILM SCENARIOS
# =============================================================================

SESSILE_SCENARIOS = {
    1: {
        'name': 'Bottom Wall Biofilm',
        'description': 'Single biofilm layer on bottom Y wall',
        'num_microbes': 1,
        'location': 'bottom_wall',
    },
    2: {
        'name': 'Top Wall Biofilm',
        'description': 'Single biofilm layer on top Y wall',
        'num_microbes': 1,
        'location': 'top_wall',
    },
    3: {
        'name': 'Both Walls Biofilm',
        'description': 'Biofilm on both top and bottom Y walls',
        'num_microbes': 1,
        'location': 'both_walls',
    },
    4: {
        'name': 'All Walls Biofilm',
        'description': 'Biofilm coating all wall surfaces',
        'num_microbes': 1,
        'location': 'all_walls',
    },
    5: {
        'name': 'Inlet Region Biofilm',
        'description': 'Biofilm concentrated near inlet (x=0)',
        'num_microbes': 1,
        'location': 'inlet',
    },
    6: {
        'name': 'Outlet Region Biofilm',
        'description': 'Biofilm concentrated near outlet (x=nx-1)',
        'num_microbes': 1,
        'location': 'outlet',
    },
    7: {
        'name': 'Center Region Biofilm',
        'description': 'Biofilm in center of domain',
        'num_microbes': 1,
        'location': 'center',
    },
    8: {
        'name': 'Random Patches',
        'description': 'Random biofilm patches on surfaces',
        'num_microbes': 1,
        'location': 'random_patches',
    },
    9: {
        'name': 'Hemispherical Colonies',
        'description': 'Hemispherical biofilm bumps on bottom wall',
        'num_microbes': 1,
        'location': 'hemispheres',
    },
    10: {
        'name': 'Two-Zone SMTZ Style',
        'description': 'Two microbe species in separate zones (inlet/outlet)',
        'num_microbes': 2,
        'location': 'two_zones',
    },
    11: {
        'name': 'Competing Biofilms',
        'description': 'Two microbes competing on same wall',
        'num_microbes': 2,
        'location': 'competing',
    },
    12: {
        'name': 'Layered Biofilm',
        'description': 'Two microbes in layers (one on top of other)',
        'num_microbes': 2,
        'location': 'layered',
    },
    13: {
        'name': 'Three Species Zones',
        'description': 'Three microbes in three zones along X',
        'num_microbes': 3,
        'location': 'three_zones',
    },
    14: {
        'name': 'Grain Surface Coating',
        'description': 'Biofilm coating sphere surfaces in porous medium',
        'num_microbes': 1,
        'location': 'grain_coating',
    },
}

MEDIUM_TYPES = {
    1: {'name': 'Rectangular Channel', 'func': 'channel'},
    2: {'name': 'Parallel Plates', 'func': 'plates'},
    3: {'name': 'Overlapping Spheres', 'func': 'spheres'},
    4: {'name': 'Reaction Chamber', 'func': 'chamber'},
    5: {'name': 'Hollow Box', 'func': 'hollow_box'},
}

# =============================================================================
# MATPLOTLIB SETUP
# =============================================================================

def setup_nature_rcparams():
    if not HAS_MATPLOTLIB:
        return
    plt.rcParams.update({
        'font.family': 'sans-serif', 'font.sans-serif': [FONT_NAME],
        'font.size': FONT_TICK_LABEL, 'figure.dpi': 150, 'figure.facecolor': 'white',
        'axes.linewidth': AXIS_LINE_WIDTH, 'axes.labelsize': FONT_AXIS_LABEL,
        'axes.titlesize': FONT_TITLE, 'axes.titleweight': 'bold',
        'axes.spines.top': False, 'axes.spines.right': False,
        'xtick.labelsize': FONT_TICK_LABEL, 'ytick.labelsize': FONT_TICK_LABEL,
        'legend.fontsize': FONT_LEGEND, 'legend.frameon': False,
        'savefig.facecolor': 'white', 'savefig.bbox': 'tight', 'pdf.fonttype': 42,
    })

# =============================================================================
# GEOMETRY GENERATORS - BASE MEDIUMS
# =============================================================================

def _add_interface(geometry):
    """Add interface (bounce-back) layer between solid and pore."""
    nx, ny, nz = geometry.shape
    result = geometry.copy()
    neighbors = [(1,0,0), (-1,0,0), (0,1,0), (0,-1,0), (0,0,1), (0,0,-1)]
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == MAT.solid:
                    for dx, dy, dz in neighbors:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] >= MAT.pore:
                                result[x, y, z] = MAT.interface
                                break
    return result


def create_rectangular_channel(nx, ny, nz, wall_thickness=2):
    """Rectangular channel. FLOW ALONG X."""
    geometry = np.zeros((nx, ny, nz), dtype=np.uint8)
    w = wall_thickness
    geometry[:, w:ny-w, w:nz-w] = MAT.pore
    geometry = _add_interface(geometry)
    porosity = np.sum(geometry == MAT.pore) / geometry.size
    return geometry, porosity


def create_hollow_box(nx, ny, nz, target_porosity=0.70):
    """Hollow box. FLOW ALONG X."""
    geometry = np.full((nx, ny, nz), MAT.solid, dtype=np.uint8)
    min_dim = min(ny, nz)
    w = int(min_dim / 2 * (1 - np.sqrt(target_porosity)))
    w = max(1, min(w, min_dim // 3))
    geometry[:, w:ny-w, w:nz-w] = MAT.pore
    geometry = _add_interface(geometry)
    porosity = np.sum(geometry == MAT.pore) / geometry.size
    return geometry, porosity


def create_parallel_plates(nx, ny, nz, target_porosity=0.50):
    """Parallel plates with walls on Z. FLOW ALONG X."""
    geometry = np.zeros((nx, ny, nz), dtype=np.uint8)
    gap = int(nz * target_porosity)
    gap = max(4, min(gap, nz - 4))
    wall = (nz - gap) // 2
    geometry[:, :, wall:nz-wall] = MAT.pore
    geometry = _add_interface(geometry)
    porosity = np.sum(geometry == MAT.pore) / geometry.size
    return geometry, porosity


def create_overlapping_spheres(nx, ny, nz, target_porosity=0.50, min_radius=3, max_radius=8, max_iterations=500):
    """Random overlapping spheres. FLOW ALONG X."""
    geometry = np.ones((nx, ny, nz), dtype=np.uint8) * MAT.pore
    current_porosity = 1.0
    iteration = 0
    print(f"    Creating spheres (target: {target_porosity:.1%})...")

    while current_porosity > target_porosity and iteration < max_iterations:
        cx, cy, cz = np.random.randint(0, nx), np.random.randint(0, ny), np.random.randint(0, nz)
        r = np.random.randint(min_radius, max_radius + 1)

        for x in range(max(0, cx-r), min(nx, cx+r+1)):
            for y in range(max(0, cy-r), min(ny, cy+r+1)):
                for z in range(max(0, cz-r), min(nz, cz+r+1)):
                    if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 <= r**2:
                        geometry[x, y, z] = MAT.solid

        current_porosity = np.sum(geometry == MAT.pore) / geometry.size
        iteration += 1
        if iteration % 50 == 0:
            print(f"      Iter {iteration}: phi = {current_porosity:.1%}")

    # Ensure inlet/outlet open
    geometry[0, :, :][geometry[0, :, :] == MAT.solid] = MAT.pore
    geometry[-1, :, :][geometry[-1, :, :] == MAT.solid] = MAT.pore

    geometry = _add_interface(geometry)
    print(f"    Final: phi = {np.sum(geometry == MAT.pore) / geometry.size:.1%}")
    porosity = np.sum(geometry == MAT.pore) / geometry.size
    return geometry, porosity


def create_reaction_chamber(nx, ny, nz, inlet_width=None, chamber_fraction=0.6):
    """Reaction chamber along X."""
    geometry = np.zeros((nx, ny, nz), dtype=np.uint8)

    if inlet_width is None:
        inlet_width = max(4, min(ny, nz) // 4)

    inlet_length = int(nx * (1 - chamber_fraction) / 2)
    chamber_start, chamber_end = inlet_length, nx - inlet_length

    y_start, y_end = (ny - inlet_width) // 2, (ny + inlet_width) // 2
    z_start, z_end = (nz - inlet_width) // 2, (nz + inlet_width) // 2

    geometry[0:chamber_start, y_start:y_end, z_start:z_end] = MAT.pore
    wall = 2
    geometry[chamber_start:chamber_end, wall:ny-wall, wall:nz-wall] = MAT.pore
    geometry[chamber_end:nx, y_start:y_end, z_start:z_end] = MAT.pore

    geometry = _add_interface(geometry)
    porosity = np.sum(geometry == MAT.pore) / geometry.size
    return geometry, porosity


# =============================================================================
# SESSILE BIOFILM PLACEMENT FUNCTIONS
# =============================================================================

def _mark_fringe(geometry, core_id, fringe_id):
    """Convert core voxels adjacent to pore into fringe."""
    nx, ny, nz = geometry.shape
    fringe_mask = np.zeros_like(geometry, dtype=bool)

    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == core_id:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] == MAT.pore:
                                fringe_mask[x, y, z] = True
                                break

    geometry[fringe_mask] = fringe_id
    return geometry


def place_biofilm_bottom_wall(geometry, microbe_idx=0, thickness=3, coverage=1.0):
    """Place biofilm on bottom Y wall."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    # Find the wall interface
    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    # Found first pore from bottom, place biofilm above interface
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core_id
                    break

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_top_wall(geometry, microbe_idx=0, thickness=3, coverage=1.0):
    """Place biofilm on top Y wall."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    for x in range(nx):
        for z in range(nz):
            for y in range(ny-1, -1, -1):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y - t >= 0 and geometry[x, y - t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y - t, z] = core_id
                    break

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_both_walls(geometry, microbe_idx=0, thickness=3, coverage=1.0):
    """Place biofilm on both top and bottom Y walls."""
    geometry = place_biofilm_bottom_wall(geometry, microbe_idx, thickness, coverage)
    # Reset fringe for combined marking
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)
    geometry[geometry == fringe_id] = core_id

    nx, ny, nz = geometry.shape
    for x in range(nx):
        for z in range(nz):
            for y in range(ny-1, -1, -1):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y - t >= 0 and geometry[x, y - t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y - t, z] = core_id
                    break

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_all_walls(geometry, microbe_idx=0, thickness=2, coverage=1.0):
    """Place biofilm coating all wall surfaces."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    # Find pore voxels adjacent to interface and mark as biofilm
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == MAT.pore:
                    is_surface = False
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] == MAT.interface:
                                is_surface = True
                                break
                    if is_surface and np.random.random() < coverage:
                        geometry[x, y, z] = core_id

    # Expand thickness
    for _ in range(thickness - 1):
        new_core = np.zeros_like(geometry, dtype=bool)
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    if geometry[x, y, z] == MAT.pore:
                        for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                            x2, y2, z2 = x+dx, y+dy, z+dz
                            if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                                if geometry[x2, y2, z2] == core_id:
                                    if np.random.random() < coverage:
                                        new_core[x, y, z] = True
                                    break
        geometry[new_core] = core_id

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_inlet(geometry, microbe_idx=0, thickness=3, depth_fraction=0.2, coverage=1.0):
    """Place biofilm near inlet region (low X)."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)
    depth = int(nx * depth_fraction)

    for x in range(depth):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core_id
                    break

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_outlet(geometry, microbe_idx=0, thickness=3, depth_fraction=0.2, coverage=1.0):
    """Place biofilm near outlet region (high X)."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)
    start = int(nx * (1 - depth_fraction))

    for x in range(start, nx):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core_id
                    break

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_center(geometry, microbe_idx=0, thickness=3, center_fraction=0.4, coverage=1.0):
    """Place biofilm in center region of domain."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    start = int(nx * (0.5 - center_fraction / 2))
    end = int(nx * (0.5 + center_fraction / 2))

    for x in range(start, end):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core_id
                    break

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_random_patches(geometry, microbe_idx=0, num_patches=15, min_radius=2, max_radius=5):
    """Place random biofilm patches on surfaces."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    # Find surface pore voxels
    surface_voxels = []
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == MAT.pore:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] == MAT.interface:
                                surface_voxels.append((x, y, z))
                                break

    if not surface_voxels:
        return geometry

    # Place patches
    for _ in range(num_patches):
        cx, cy, cz = surface_voxels[np.random.randint(len(surface_voxels))]
        r = np.random.randint(min_radius, max_radius + 1)

        for x in range(max(0, cx-r), min(nx, cx+r+1)):
            for y in range(max(0, cy-r), min(ny, cy+r+1)):
                for z in range(max(0, cz-r), min(nz, cz+r+1)):
                    if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 <= r**2:
                        if geometry[x, y, z] == MAT.pore:
                            geometry[x, y, z] = core_id

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_hemispheres(geometry, microbe_idx=0, num_bumps=20, min_radius=2, max_radius=4):
    """Place hemispherical biofilm colonies on bottom wall."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    # Find bottom pore surface
    for _ in range(num_bumps):
        cx = np.random.randint(5, nx - 5)
        cz = np.random.randint(5, nz - 5)
        r = np.random.randint(min_radius, max_radius + 1)

        # Find y position of pore surface at this x,z
        cy = None
        for y in range(ny):
            if geometry[cx, y, cz] == MAT.pore:
                cy = y
                break

        if cy is None:
            continue

        # Place hemisphere
        for x in range(max(0, cx-r), min(nx, cx+r+1)):
            for y in range(cy, min(ny, cy+r+1)):
                for z in range(max(0, cz-r), min(nz, cz+r+1)):
                    if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 <= r**2:
                        if geometry[x, y, z] == MAT.pore:
                            geometry[x, y, z] = core_id

    return _mark_fringe(geometry, core_id, fringe_id)


def place_biofilm_two_zones(geometry, thickness=3, coverage=1.0):
    """Two microbe species in separate zones (SMTZ style)."""
    nx, ny, nz = geometry.shape
    third = nx // 3

    core1, fringe1 = MAT.get_microbe_masks(0)
    core2, fringe2 = MAT.get_microbe_masks(1)

    # Microbe-2 near inlet
    for x in range(third):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core2
                    break

    # Microbe-1 near outlet
    for x in range(2 * third, nx):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core1
                    break

    # Mixed in middle
    for x in range(third, 2 * third):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core1 if np.random.random() < 0.5 else core2
                    break

    geometry = _mark_fringe(geometry, core1, fringe1)
    geometry = _mark_fringe(geometry, core2, fringe2)
    return geometry


def place_biofilm_competing(geometry, thickness=3, coverage=0.8):
    """Two microbes competing on same wall (checkerboard pattern)."""
    nx, ny, nz = geometry.shape
    core1, fringe1 = MAT.get_microbe_masks(0)
    core2, fringe2 = MAT.get_microbe_masks(1)

    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                # Checkerboard allocation
                                if (x + z) % 2 == 0:
                                    geometry[x, y + t, z] = core1
                                else:
                                    geometry[x, y + t, z] = core2
                    break

    geometry = _mark_fringe(geometry, core1, fringe1)
    geometry = _mark_fringe(geometry, core2, fringe2)
    return geometry


def place_biofilm_layered(geometry, layer1_thickness=2, layer2_thickness=2, coverage=1.0):
    """Two microbes in layers (one on top of other)."""
    nx, ny, nz = geometry.shape
    core1, fringe1 = MAT.get_microbe_masks(0)  # Inner layer (on wall)
    core2, fringe2 = MAT.get_microbe_masks(1)  # Outer layer (on top)

    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    # Inner layer - microbe 1
                    for t in range(layer1_thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core1
                    # Outer layer - microbe 2
                    for t in range(layer1_thickness, layer1_thickness + layer2_thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                geometry[x, y + t, z] = core2
                    break

    geometry = _mark_fringe(geometry, core1, fringe1)
    geometry = _mark_fringe(geometry, core2, fringe2)
    return geometry


def place_biofilm_three_zones(geometry, thickness=3, coverage=1.0):
    """Three microbes in three zones along X."""
    nx, ny, nz = geometry.shape
    third = nx // 3

    core1, fringe1 = MAT.get_microbe_masks(0)
    core2, fringe2 = MAT.get_microbe_masks(1)
    core3, fringe3 = MAT.get_microbe_masks(2)

    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geometry[x, y, z] == MAT.pore:
                    for t in range(thickness):
                        if y + t < ny and geometry[x, y + t, z] == MAT.pore:
                            if np.random.random() < coverage:
                                if x < third:
                                    geometry[x, y + t, z] = core1
                                elif x < 2 * third:
                                    geometry[x, y + t, z] = core2
                                else:
                                    geometry[x, y + t, z] = core3
                    break

    geometry = _mark_fringe(geometry, core1, fringe1)
    geometry = _mark_fringe(geometry, core2, fringe2)
    geometry = _mark_fringe(geometry, core3, fringe3)
    return geometry


def place_biofilm_grain_coating(geometry, microbe_idx=0, thickness=1, coverage=0.7):
    """Coat grain surfaces in porous medium with biofilm."""
    nx, ny, nz = geometry.shape
    core_id, fringe_id = MAT.get_microbe_masks(microbe_idx)

    # Find pore voxels adjacent to interface (grain surfaces)
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == MAT.pore:
                    is_surface = False
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] == MAT.interface:
                                is_surface = True
                                break
                    if is_surface and np.random.random() < coverage:
                        geometry[x, y, z] = core_id

    return _mark_fringe(geometry, core_id, fringe_id)


# =============================================================================
# FILE I/O
# =============================================================================

def save_dat(geometry, filepath):
    """Save geometry in CompLaB3D .dat format."""
    nx, ny, nz = geometry.shape
    with open(filepath, 'w') as f:
        for x in range(nx):
            for z in range(nz):
                for y in range(ny):
                    f.write(f"{geometry[x, y, z]}\n")
    return nx * ny * nz


def save_slice_images(geometry, folder, prefix="slice"):
    """Save YZ slice images along flow direction (X)."""
    nx, ny, nz = geometry.shape
    os.makedirs(folder, exist_ok=True)

    for x in range(nx):
        img_array = np.zeros((nz, ny), dtype=np.uint8)
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] >= MAT.pore:
                    img_array[z, y] = 0    # BLACK = pore/biofilm
                else:
                    img_array[z, y] = 255  # WHITE = solid

        img = Image.fromarray(img_array, mode='L')
        img.save(os.path.join(folder, f'{prefix}_{x:04d}.png'))

    return nx


def save_color_slice_images(geometry, folder, prefix="color_slice"):
    """Save colored YZ slice images showing all material types."""
    nx, ny, nz = geometry.shape
    os.makedirs(folder, exist_ok=True)

    for x in range(nx):
        img_array = np.zeros((nz, ny, 3), dtype=np.uint8)
        for y in range(ny):
            for z in range(nz):
                mat_id = geometry[x, y, z]
                img_array[z, y] = COLORS_RGB.get(mat_id, (128, 128, 128))

        img = Image.fromarray(img_array, mode='RGB')
        img.save(os.path.join(folder, f'{prefix}_{x:04d}.png'))

    return nx


def save_readme(output_dir, geometry, info, scenario_num=None):
    """Save README with geometry information."""
    nx, ny, nz = geometry.shape

    # Count materials
    counts = {}
    for mat_id in range(9):
        count = np.sum(geometry == mat_id)
        if count > 0:
            counts[mat_id] = count

    total = geometry.size

    readme = f"""================================================================================
CompLaB3D Geometry - Sessile Biofilm
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
================================================================================

DIMENSIONS:
  nx = {nx} (flow direction, # images)
  ny = {ny}
  nz = {nz}
  Total voxels: {total:,}

FLOW DIRECTION: X-axis
  Inlet: x=0
  Outlet: x={nx-1}

MATERIAL COMPOSITION:
"""

    for mat_id, count in sorted(counts.items()):
        pct = count / total * 100
        readme += f"  {MAT.get_name(mat_id):20s} (mask={mat_id}): {count:8,} voxels ({pct:5.1f}%)\n"

    # Calculate porosity (pore only, not biofilm)
    pore_count = counts.get(MAT.pore, 0)
    porosity = pore_count / total

    # Calculate biofilm coverage
    biofilm_count = sum(counts.get(i, 0) for i in [3,4,5,6,7,8])
    biofilm_pct = biofilm_count / total * 100

    readme += f"""
SUMMARY:
  Porosity (pore only): {porosity:.1%}
  Biofilm coverage: {biofilm_pct:.1f}%
  Open space (pore + biofilm): {(pore_count + biofilm_count) / total:.1%}

"""

    if scenario_num:
        scenario = SESSILE_SCENARIOS.get(scenario_num, {})
        readme += f"""SCENARIO: {scenario_num} - {scenario.get('name', 'Unknown')}
  {scenario.get('description', '')}
  Number of microbe species: {scenario.get('num_microbes', 1)}

"""

    readme += f"""CONFIGURATION INFO:
  {info}

FILES:
  input/geometry.dat - Geometry file for CompLaB3D
  images/slice_*.png - B/W slice images (YZ planes)
  images/color_slice_*.png - Colored slice images

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

================================================================================
"""

    with open(os.path.join(output_dir, "README.txt"), 'w') as f:
        f.write(readme)


# =============================================================================
# VISUALIZATION
# =============================================================================

def create_geometry_figure(geometry, filepath_base, title="Geometry"):
    """Create publication-quality geometry visualization."""
    if not HAS_MATPLOTLIB:
        print("    Matplotlib not available, skipping figure generation")
        return

    setup_nature_rcparams()
    nx, ny, nz = geometry.shape

    # Create figure with 3 views
    fig, axes = plt.subplots(1, 3, figsize=(DOUBLE_COL_WIDTH, 3))

    # Custom colormap
    unique_vals = np.unique(geometry)
    colors_list = [COLORS.get(v, '#888888') for v in unique_vals]
    cmap = ListedColormap(colors_list)
    bounds = list(unique_vals) + [unique_vals[-1] + 1]
    norm = BoundaryNorm(bounds, cmap.N)

    # XY slice (mid-Z)
    mid_z = nz // 2
    ax = axes[0]
    im = ax.imshow(geometry[:, :, mid_z].T, origin='lower', cmap=cmap, norm=norm, aspect='equal')
    ax.set_xlabel('X (flow)')
    ax.set_ylabel('Y')
    ax.set_title(f'XY plane (z={mid_z})')

    # XZ slice (mid-Y)
    mid_y = ny // 2
    ax = axes[1]
    ax.imshow(geometry[:, mid_y, :].T, origin='lower', cmap=cmap, norm=norm, aspect='equal')
    ax.set_xlabel('X (flow)')
    ax.set_ylabel('Z')
    ax.set_title(f'XZ plane (y={mid_y})')

    # YZ slice (mid-X)
    mid_x = nx // 2
    ax = axes[2]
    ax.imshow(geometry[mid_x, :, :].T, origin='lower', cmap=cmap, norm=norm, aspect='equal')
    ax.set_xlabel('Y')
    ax.set_ylabel('Z')
    ax.set_title(f'YZ plane (x={mid_x})')

    # Legend
    patches = [mpatches.Patch(color=COLORS.get(v, '#888888'), label=MAT.get_name(v))
               for v in unique_vals]
    fig.legend(handles=patches, loc='center right', bbox_to_anchor=(1.15, 0.5))

    plt.suptitle(title, fontsize=FONT_TITLE, fontweight='bold')
    plt.tight_layout()

    # Save
    for ext in ['png', 'pdf']:
        plt.savefig(f"{filepath_base}.{ext}", dpi=DPI_MIXED, bbox_inches='tight')
    plt.close()

    print(f"    Saved {filepath_base}.png/pdf")


# =============================================================================
# MAIN SESSILE GEOMETRY GENERATOR
# =============================================================================

def generate_sessile_geometry(scenario_num, medium_type, nx, ny, nz, output_dir,
                               target_porosity=0.5, biofilm_thickness=3,
                               biofilm_coverage=1.0, core_fringe_ratio=0.7,
                               generate_figures=True):
    """
    Generate sessile biofilm geometry.

    Parameters:
    -----------
    scenario_num : int
        Biofilm scenario (1-14)
    medium_type : int
        Medium type (1-5)
    nx, ny, nz : int
        Domain dimensions
    output_dir : str
        Output directory
    target_porosity : float
        Target porosity for porous media (0-1)
    biofilm_thickness : int
        Biofilm thickness in voxels
    biofilm_coverage : float
        Coverage fraction (0-1)
    core_fringe_ratio : float
        Not used directly, but controls core/fringe via thickness
    generate_figures : bool
        Whether to generate visualization figures
    """

    scenario = SESSILE_SCENARIOS.get(scenario_num, SESSILE_SCENARIOS[1])
    medium = MEDIUM_TYPES.get(medium_type, MEDIUM_TYPES[1])

    print(f"\n{'='*60}")
    print(f"  SESSILE BIOFILM GEOMETRY GENERATOR")
    print(f"{'='*60}")
    print(f"  Scenario: {scenario_num} - {scenario['name']}")
    print(f"  Medium: {medium['name']}")
    print(f"  Dimensions: {nx} x {ny} x {nz}")
    print(f"  Target porosity: {target_porosity:.1%}")
    print(f"  Biofilm thickness: {biofilm_thickness}")
    print(f"  Biofilm coverage: {biofilm_coverage:.1%}")
    print(f"{'='*60}\n")

    # Create base medium
    print("  Creating base medium...")
    if medium['func'] == 'channel':
        geometry, phi = create_rectangular_channel(nx, ny, nz)
    elif medium['func'] == 'plates':
        geometry, phi = create_parallel_plates(nx, ny, nz, target_porosity)
    elif medium['func'] == 'spheres':
        geometry, phi = create_overlapping_spheres(nx, ny, nz, target_porosity)
    elif medium['func'] == 'chamber':
        geometry, phi = create_reaction_chamber(nx, ny, nz)
    elif medium['func'] == 'hollow_box':
        geometry, phi = create_hollow_box(nx, ny, nz, target_porosity)
    else:
        geometry, phi = create_rectangular_channel(nx, ny, nz)

    print(f"    Base porosity: {phi:.1%}")

    # Place biofilm according to scenario
    print(f"  Placing biofilm ({scenario['name']})...")

    location = scenario['location']

    if location == 'bottom_wall':
        geometry = place_biofilm_bottom_wall(geometry, 0, biofilm_thickness, biofilm_coverage)
    elif location == 'top_wall':
        geometry = place_biofilm_top_wall(geometry, 0, biofilm_thickness, biofilm_coverage)
    elif location == 'both_walls':
        geometry = place_biofilm_both_walls(geometry, 0, biofilm_thickness, biofilm_coverage)
    elif location == 'all_walls':
        geometry = place_biofilm_all_walls(geometry, 0, biofilm_thickness, biofilm_coverage)
    elif location == 'inlet':
        geometry = place_biofilm_inlet(geometry, 0, biofilm_thickness, 0.2, biofilm_coverage)
    elif location == 'outlet':
        geometry = place_biofilm_outlet(geometry, 0, biofilm_thickness, 0.2, biofilm_coverage)
    elif location == 'center':
        geometry = place_biofilm_center(geometry, 0, biofilm_thickness, 0.4, biofilm_coverage)
    elif location == 'random_patches':
        geometry = place_biofilm_random_patches(geometry, 0, 15, 2, 5)
    elif location == 'hemispheres':
        geometry = place_biofilm_hemispheres(geometry, 0, 20, 2, 4)
    elif location == 'two_zones':
        geometry = place_biofilm_two_zones(geometry, biofilm_thickness, biofilm_coverage)
    elif location == 'competing':
        geometry = place_biofilm_competing(geometry, biofilm_thickness, biofilm_coverage)
    elif location == 'layered':
        geometry = place_biofilm_layered(geometry, biofilm_thickness // 2 + 1, biofilm_thickness // 2 + 1, biofilm_coverage)
    elif location == 'three_zones':
        geometry = place_biofilm_three_zones(geometry, biofilm_thickness, biofilm_coverage)
    elif location == 'grain_coating':
        geometry = place_biofilm_grain_coating(geometry, 0, 1, biofilm_coverage)

    # Calculate final statistics
    pore_count = np.sum(geometry == MAT.pore)
    final_porosity = pore_count / geometry.size

    biofilm_count = sum(np.sum(geometry == i) for i in [3,4,5,6,7,8])
    core_count = sum(np.sum(geometry == i) for i in [3,4,5])
    fringe_count = sum(np.sum(geometry == i) for i in [6,7,8])

    print(f"\n  STATISTICS:")
    print(f"    Final porosity: {final_porosity:.1%}")
    print(f"    Total biofilm: {biofilm_count:,} voxels ({biofilm_count/geometry.size:.1%})")
    if biofilm_count > 0:
        print(f"    Core: {core_count:,} ({core_count/biofilm_count:.1%} of biofilm)")
        print(f"    Fringe: {fringe_count:,} ({fringe_count/biofilm_count:.1%} of biofilm)")

    # Save files
    print(f"\n  Saving files...")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "input"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "output"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

    n_voxels = save_dat(geometry, os.path.join(output_dir, "input", "geometry.dat"))
    print(f"    geometry.dat ({n_voxels:,} voxels)")

    n_slices = save_slice_images(geometry, os.path.join(output_dir, "images"))
    print(f"    {n_slices} B/W slice images")

    n_color = save_color_slice_images(geometry, os.path.join(output_dir, "images"))
    print(f"    {n_color} color slice images")

    info = {
        'scenario': scenario_num,
        'scenario_name': scenario['name'],
        'medium': medium['name'],
        'num_microbes': scenario['num_microbes'],
        'biofilm_thickness': biofilm_thickness,
        'biofilm_coverage': biofilm_coverage,
    }
    save_readme(output_dir, geometry, info, scenario_num)
    print(f"    README.txt")

    if generate_figures and HAS_MATPLOTLIB:
        fig_path = os.path.join(output_dir, f"geometry_S{scenario_num:02d}")
        create_geometry_figure(geometry, fig_path,
                               f"Scenario {scenario_num}: {scenario['name']}")

    print(f"\n  Output: {output_dir}")
    print(f"{'='*60}\n")

    return geometry, output_dir


# =============================================================================
# INTERACTIVE MENU
# =============================================================================

def print_sessile_scenarios():
    """Print all available sessile scenarios."""
    print("\n  ╔══════════════════════════════════════════════════════════════╗")
    print("  ║           SESSILE BIOFILM SCENARIOS                          ║")
    print("  ╠══════════════════════════════════════════════════════════════╣")
    print("  ║                                                              ║")
    print("  ║  SINGLE SPECIES:                                             ║")
    print("  ║   1 = Bottom Wall Biofilm                                    ║")
    print("  ║   2 = Top Wall Biofilm                                       ║")
    print("  ║   3 = Both Walls Biofilm                                     ║")
    print("  ║   4 = All Walls Coating                                      ║")
    print("  ║   5 = Inlet Region                                           ║")
    print("  ║   6 = Outlet Region                                          ║")
    print("  ║   7 = Center Region                                          ║")
    print("  ║   8 = Random Patches                                         ║")
    print("  ║   9 = Hemispherical Colonies                                 ║")
    print("  ║                                                              ║")
    print("  ║  TWO SPECIES:                                                ║")
    print("  ║  10 = Two-Zone SMTZ Style                                    ║")
    print("  ║  11 = Competing Biofilms (checkerboard)                      ║")
    print("  ║  12 = Layered Biofilm (one on top of other)                  ║")
    print("  ║                                                              ║")
    print("  ║  THREE SPECIES:                                              ║")
    print("  ║  13 = Three Species Zones                                    ║")
    print("  ║                                                              ║")
    print("  ║  POROUS MEDIA:                                               ║")
    print("  ║  14 = Grain Surface Coating                                  ║")
    print("  ║                                                              ║")
    print("  ╚══════════════════════════════════════════════════════════════╝\n")


def print_medium_types():
    """Print all available medium types."""
    print("\n  ╔════════════════════════════════════════╗")
    print("  ║         MEDIUM TYPES                   ║")
    print("  ╠════════════════════════════════════════╣")
    print("  ║  1 = Rectangular Channel               ║")
    print("  ║  2 = Parallel Plates                   ║")
    print("  ║  3 = Overlapping Spheres (porous)      ║")
    print("  ║  4 = Reaction Chamber                  ║")
    print("  ║  5 = Hollow Box                        ║")
    print("  ╚════════════════════════════════════════╝\n")


def sessile_menu():
    """Interactive menu for sessile biofilm geometry generation."""
    print("\n" + "="*60)
    print("  CompLaB3D SESSILE BIOFILM GEOMETRY GENERATOR v6.0")
    print("="*60)

    print_sessile_scenarios()

    scenario = int(input("  Select scenario (1-14) [1]: ").strip() or "1")
    if scenario < 1 or scenario > 14:
        scenario = 1

    print_medium_types()

    # For grain coating, force spheres medium
    if scenario == 14:
        print("  (Grain coating requires spheres medium)")
        medium = 3
    else:
        medium = int(input("  Select medium (1-5) [1]: ").strip() or "1")

    print("\n  DIMENSIONS:")
    nx = int(input("    NX (flow direction) [50]: ").strip() or "50")
    ny = int(input("    NY [30]: ").strip() or "30")
    nz = int(input("    NZ [30]: ").strip() or "30")

    print("\n  POROSITY & BIOFILM:")
    target_porosity = float(input("    Target porosity (0.3-0.9) [0.5]: ").strip() or "0.5")
    biofilm_thickness = int(input("    Biofilm thickness (voxels) [3]: ").strip() or "3")
    coverage = float(input("    Biofilm coverage (0.0-1.0) [1.0]: ").strip() or "1.0")

    name = input("\n  Output folder name [sessile_biofilm]: ").strip() or "sessile_biofilm"
    output_dir = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_sessile_geometry(
        scenario_num=scenario,
        medium_type=medium,
        nx=nx, ny=ny, nz=nz,
        output_dir=output_dir,
        target_porosity=target_porosity,
        biofilm_thickness=biofilm_thickness,
        biofilm_coverage=coverage,
        generate_figures=HAS_MATPLOTLIB,
    )


def get_positive_int(prompt, default):
    """Get positive integer with validation."""
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                return default
            val = int(val)
            if val > 0:
                return val
            print("  Please enter a positive number")
        except ValueError:
            print("  Invalid input. Please enter a number")

def get_float_range(prompt, default, min_val, max_val):
    """Get float within range."""
    while True:
        try:
            val = input(prompt).strip()
            if not val:
                return default
            val = float(val)
            if min_val <= val <= max_val:
                return val
            print(f"  Enter value between {min_val}-{max_val}")
        except ValueError:
            print("  Invalid input")

def abiotic_generator_menu():
    """Step-by-step ABIOTIC domain generator (no biofilm)."""
    print("\n" + "="*70)
    print("  ABIOTIC DOMAIN GENERATOR - Step-by-Step")
    print("="*70)

    print("\n  STEP 1: Select Medium Type")
    print("  " + "-" * 35)
    print("    1 = Rectangular Channel (simple hollow box)")
    print("    2 = Parallel Plates (two parallel surfaces)")
    print("    3 = Overlapping Spheres (porous media - most realistic)")
    print("    4 = Reaction Chamber (fully enclosed)")
    print("    5 = Hollow Box (partially open)")

    medium = int(input("\n    Select (1-5) [1]: ").strip() or "1")
    if medium < 1 or medium > 5:
        medium = 1

    print("\n  STEP 2: Domain Dimensions")
    print("  " + "-" * 35)
    nx = get_positive_int("    NX (flow direction) [50]: ", 50)
    ny = get_positive_int("    NY [30]: ", 30)
    nz = get_positive_int("    NZ [30]: ", 30)

    print("\n  STEP 3: Porosity")
    print("  " + "-" * 35)
    print("    0.3 = tight packing | 0.5 = moderate | 0.7 = loose")
    porosity = get_float_range("    Target porosity (0.3-0.9) [0.5]: ", 0.5, 0.3, 0.9)

    print("\n  STEP 4: Output Folder Name")
    print("  " + "-" * 35)
    name = input("    Folder name [abiotic_domain]: ").strip() or "abiotic_domain"
    output_dir = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    print("\n  STEP 5: Generate")
    print("  " + "-" * 35)
    print(f"    Medium: {['Channel', 'Plates', 'Spheres', 'Chamber', 'Box'][medium-1]}")
    print(f"    Dimensions: {nx} x {ny} x {nz}")
    print(f"    Porosity: {porosity:.1%}")
    print(f"    Output: {output_dir}")

    confirm = input("\n    Proceed? (y/n) [y]: ").strip().lower() or "y"
    if confirm != 'y':
        print("  Cancelled.")
        return

    # Generate
    print(f"\n  Generating {['channel', 'plates', 'spheres', 'chamber', 'box'][medium-1]}...")

    if medium == 1:
        geometry, phi = create_rectangular_channel(nx, ny, nz)
    elif medium == 2:
        geometry, phi = create_parallel_plates(nx, ny, nz, porosity)
    elif medium == 3:
        geometry, phi = create_overlapping_spheres(nx, ny, nz, porosity)
    elif medium == 4:
        geometry, phi = create_reaction_chamber(nx, ny, nz)
    else:
        geometry, phi = create_hollow_box(nx, ny, nz, porosity)

    # Save
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, "input"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

    save_dat(geometry, os.path.join(output_dir, "input", "geometry.dat"))
    save_slice_images(geometry, os.path.join(output_dir, "images"))

    # Create publication-quality figure
    med_name = ['Channel', 'Plates', 'Spheres', 'Chamber', 'Box'][medium-1]
    fig_path = os.path.join(output_dir, f"geometry_abiotic_{med_name}")
    create_geometry_figure(geometry, fig_path, f"Abiotic: {med_name} (porosity={porosity:.1%})")

    print(f"  Output: {output_dir}")
    print(f"    - geometry.dat")
    print(f"    - B/W slice images")
    print(f"    - Publication-quality figure (PNG + PDF)")
    print(f"  Ready for CompLaB3D!\n")

def image_converter_menu():
    """Convert image stack to geometry with optional biofilm."""
    print("\n" + "="*70)
    print("  IMAGE STACK CONVERTER")
    print("="*70)

    # Step 1: Image folder
    print("\n  STEP 1: Select Image Folder")
    print("  " + "-" * 35)
    folder = input("    Image folder path: ").strip()
    if not os.path.exists(folder):
        print(f"    Folder not found: {folder}")
        return

    # Step 2: Add biofilm?
    print("\n  STEP 2: Add Biofilm?")
    print("  " + "-" * 35)
    print("    Do you want to add biofilm to the converted geometry?")
    print("")
    print("    0 = No biofilm (abiotic domain only)")
    print("    1 = Single species biofilm")
    print("    2 = Two species biofilm")
    print("    3 = Three species biofilm")

    add_biofilm = input("\n    Select (0-3) [0]: ").strip() or "0"
    add_biofilm = int(add_biofilm) if add_biofilm.isdigit() else 0

    biofilm_thickness = 2
    biofilm_coverage = 0.7
    biofilm_location = 1  # Default: all surfaces

    if add_biofilm > 0:
        # Step 3: Biofilm Location
        print("\n  STEP 3: Biofilm Location/Distribution")
        print("  " + "-" * 35)
        print("    Where should biofilm be placed?")
        print("")
        print("    1 = All grain surfaces (uniform coating)")
        print("    2 = Inlet region only (first 20% of X)")
        print("    3 = Outlet region only (last 20% of X)")
        print("    4 = Center region only (middle 40% of X)")
        print("    5 = Random patches on surfaces")
        if add_biofilm >= 2:
            print("    6 = Zoned by X (species separated along flow)")

        max_loc = 6 if add_biofilm >= 2 else 5
        biofilm_location = input(f"\n    Select (1-{max_loc}) [1]: ").strip() or "1"
        biofilm_location = int(biofilm_location) if biofilm_location.isdigit() else 1

        # Step 4: Biofilm Parameters
        print("\n  STEP 4: Biofilm Parameters")
        print("  " + "-" * 35)
        biofilm_thickness = get_positive_int("    Biofilm thickness (voxels) [2]: ", 2)
        biofilm_coverage = get_float_range("    Coverage fraction (0.1-1.0) [0.7]: ", 0.7, 0.1, 1.0)

    # Step 5: Output name
    print("\n  STEP 5: Output")
    print("  " + "-" * 35)
    name = input("    Output folder name [converted]: ").strip() or "converted"
    output_dir = f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Location names for display
    location_names = {
        1: "All surfaces",
        2: "Inlet region",
        3: "Outlet region",
        4: "Center region",
        5: "Random patches",
        6: "Zoned by X"
    }

    # Summary
    print("\n  SUMMARY:")
    print(f"    Input: {folder}")
    print(f"    Biofilm: {['None', '1 species', '2 species', '3 species'][add_biofilm]}")
    if add_biofilm > 0:
        print(f"    Location: {location_names.get(biofilm_location, 'Unknown')}")
        print(f"    Thickness: {biofilm_thickness} voxels")
        print(f"    Coverage: {biofilm_coverage:.0%}")
    print(f"    Output: {output_dir}")

    confirm = input("\n    Proceed? (y/n) [y]: ").strip().lower() or "y"
    if confirm != 'y':
        print("    Cancelled.")
        return

    print(f"\n  Converting images from: {folder}")

    try:
        geometry = load_image_stack(folder)
        nx, ny, nz = geometry.shape
        print(f"    Loaded geometry: {nx} x {ny} x {nz}")

        # Add biofilm if requested
        if add_biofilm >= 1:
            print(f"    Adding biofilm (species: {add_biofilm}, location: {location_names.get(biofilm_location)})...")

            if add_biofilm == 1:
                # Single species - use location
                if biofilm_location == 1:
                    geometry = place_biofilm_grain_coating(geometry, 0, biofilm_thickness, biofilm_coverage)
                elif biofilm_location == 2:
                    geometry = place_biofilm_inlet(geometry, 0, biofilm_thickness, 0.2, biofilm_coverage)
                elif biofilm_location == 3:
                    geometry = place_biofilm_outlet(geometry, 0, biofilm_thickness, 0.2, biofilm_coverage)
                elif biofilm_location == 4:
                    geometry = place_biofilm_center(geometry, 0, biofilm_thickness, 0.4, biofilm_coverage)
                elif biofilm_location == 5:
                    geometry = place_biofilm_random_patches(geometry, 0, 20, 2, 5)

            elif add_biofilm == 2:
                # Two species
                if biofilm_location == 6:
                    geometry = place_biofilm_two_zones_on_grains(geometry, biofilm_thickness, biofilm_coverage)
                else:
                    # Both species in same location pattern
                    geometry = place_biofilm_competing(geometry, biofilm_thickness, biofilm_coverage)

            elif add_biofilm == 3:
                # Three species
                if biofilm_location == 6:
                    geometry = place_biofilm_three_zones_on_grains(geometry, biofilm_thickness, biofilm_coverage)
                else:
                    geometry = place_biofilm_three_zones(geometry, biofilm_thickness, biofilm_coverage)

        # Save files
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "input"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)

        save_dat(geometry, os.path.join(output_dir, "input", "geometry.dat"))
        save_slice_images(geometry, os.path.join(output_dir, "images"))
        save_color_slice_images(geometry, os.path.join(output_dir, "images"))

        # Statistics
        pore_count = np.sum(geometry == MAT.pore)
        biofilm_count = sum(np.sum(geometry == i) for i in [3,4,5,6,7,8])

        print(f"\n  Conversion complete!")
        print(f"    Dimensions: {geometry.shape}")
        print(f"    Porosity: {pore_count/geometry.size:.1%}")
        if biofilm_count > 0:
            print(f"    Biofilm: {biofilm_count:,} voxels ({biofilm_count/geometry.size:.1%})")
        print(f"    Output: {output_dir}/")
        print(f"      - input/geometry.dat")
        print(f"      - images/slice_*.png (B/W)")
        print(f"      - images/color_slice_*.png (colored)\n")

        # Generate figure
        if HAS_MATPLOTLIB:
            fig_path = os.path.join(output_dir, "geometry_converted")
            title = "Converted from Images"
            if add_biofilm > 0:
                title += f" + {add_biofilm} species biofilm"
            create_geometry_figure(geometry, fig_path, title)

    except Exception as e:
        print(f"  Error: {e}\n")


def place_biofilm_two_zones_on_grains(geometry, thickness=2, coverage=0.7):
    """Place two species biofilm on grain surfaces, split by X position."""
    nx, ny, nz = geometry.shape
    core1, fringe1 = MAT.get_microbe_masks(0)
    core2, fringe2 = MAT.get_microbe_masks(1)
    mid_x = nx // 2

    # Find pore voxels adjacent to interface (grain surfaces)
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == MAT.pore:
                    is_surface = False
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] == MAT.interface:
                                is_surface = True
                                break
                    if is_surface and np.random.random() < coverage:
                        if x < mid_x:
                            geometry[x, y, z] = core1
                        else:
                            geometry[x, y, z] = core2

    geometry = _mark_fringe(geometry, core1, fringe1)
    geometry = _mark_fringe(geometry, core2, fringe2)
    return geometry


def place_biofilm_three_zones_on_grains(geometry, thickness=2, coverage=0.7):
    """Place three species biofilm on grain surfaces, split by X position."""
    nx, ny, nz = geometry.shape
    core1, fringe1 = MAT.get_microbe_masks(0)
    core2, fringe2 = MAT.get_microbe_masks(1)
    core3, fringe3 = MAT.get_microbe_masks(2)
    third = nx // 3

    # Find pore voxels adjacent to interface (grain surfaces)
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == MAT.pore:
                    is_surface = False
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] == MAT.interface:
                                is_surface = True
                                break
                    if is_surface and np.random.random() < coverage:
                        if x < third:
                            geometry[x, y, z] = core1
                        elif x < 2 * third:
                            geometry[x, y, z] = core2
                        else:
                            geometry[x, y, z] = core3

    geometry = _mark_fringe(geometry, core1, fringe1)
    geometry = _mark_fringe(geometry, core2, fringe2)
    geometry = _mark_fringe(geometry, core3, fringe3)
    return geometry

def interactive_menu():
    """Main menu - Choose between three generators."""
    while True:
        print("\n" + "="*70)
        print("  CompLaB3D GEOMETRY GENERATOR v6.0")
        print("  THREE GENERATORS: ABIOTIC | BIOFILM | IMAGE CONVERTER")
        print("="*70)

        print("\n  1 = ABIOTIC Domain Generator (porous media without biofilm)")
        print("  2 = SESSILE BIOFILM Generator (with biofilm)")
        print("  3 = IMAGE CONVERTER (convert image stacks to .dat)")
        print("  4 = Exit")

        choice = input("\n  Your choice (1-4) [1]: ").strip() or "1"

        if choice == '1':
            abiotic_generator_menu()
        elif choice == '2':
            sessile_menu()
        elif choice == '3':
            image_converter_menu()
        elif choice == '4':
            print("\n  Thank you for using CompLaB3D Geometry Generator v6.0!")
            break
        else:
            print("  Invalid choice")


def load_image_stack(folder):
    """Load image stack."""
    extensions = ['*.bmp', '*.png', '*.tif', '*.tiff', '*.jpg', '*.jpeg']
    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(folder, ext)))
        files.extend(glob.glob(os.path.join(folder, ext.upper())))
    files = sorted(files)

    if not files:
        raise ValueError(f"No image files found in {folder}")

    print(f"    Found {len(files)} images (= nx)")

    first_img = np.array(Image.open(files[0]).convert('L'))
    img_h, img_w = first_img.shape
    nx = len(files)
    ny = img_w
    nz = img_h

    geometry = np.zeros((nx, ny, nz), dtype=np.uint8)

    for x, filepath in enumerate(files):
        img = np.array(Image.open(filepath).convert('L'))
        for y in range(ny):
            for z in range(nz):
                if img[z, y] < 128:
                    geometry[x, y, z] = MAT.pore
                else:
                    geometry[x, y, z] = MAT.solid

    geometry = _add_interface(geometry)
    return geometry


if __name__ == "__main__":
    interactive_menu()
