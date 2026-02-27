"""Geometry Creator Dialog v6.0 - GUI-based geometry generation.

Three generators in one dialog:
  1. ABIOTIC Domain Generator  (5 medium types, no biofilm)
  2. SESSILE Biofilm Generator (14 scenarios x 5 medium types)
  3. Image Stack Converter     (BMP/PNG/TIF -> .dat)

Generates .dat geometry files + README with full metadata.

Based on CompLaB3D Geometry Generator v6.0
  by Shahram Asgari & Christof Meile
  Department of Marine Sciences, University of Georgia
"""

import os
import glob
import struct
import datetime
import numpy as np
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QFileDialog, QSpinBox,
    QComboBox, QCheckBox, QTabWidget, QWidget, QProgressBar,
    QTextEdit, QDoubleSpinBox, QMessageBox, QDialogButtonBox,
    QScrollArea, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

# ── Constants ──────────────────────────────────────────────────────────

MEDIUM_TYPES = [
    ("Rectangular Channel",    "channel"),
    ("Parallel Plates",        "plates"),
    ("Overlapping Spheres",    "spheres"),
    ("Reaction Chamber",       "chamber"),
    ("Hollow Box",             "hollow_box"),
    ("Gaussian Random Field",  "gaussian"),
    ("Fibrous Medium",         "fibrous"),
]

SESSILE_SCENARIOS = [
    # (id, name, description, num_microbes, location)
    ( 1, "Bottom Wall Biofilm",      "Single biofilm layer on bottom Y wall",           1, "bottom_wall"),
    ( 2, "Top Wall Biofilm",         "Single biofilm layer on top Y wall",              1, "top_wall"),
    ( 3, "Both Walls Biofilm",       "Biofilm on both top and bottom Y walls",          1, "both_walls"),
    ( 4, "All Walls Coating",        "Biofilm coating all wall surfaces",               1, "all_walls"),
    ( 5, "Inlet Region Biofilm",     "Biofilm concentrated near inlet (x=0)",           1, "inlet"),
    ( 6, "Outlet Region Biofilm",    "Biofilm concentrated near outlet (x=nx-1)",       1, "outlet"),
    ( 7, "Center Region Biofilm",    "Biofilm in center of domain",                     1, "center"),
    ( 8, "Random Patches",           "Random biofilm patches on surfaces",              1, "random_patches"),
    ( 9, "Hemispherical Colonies",   "Hemispherical biofilm bumps on bottom wall",      1, "hemispheres"),
    (10, "Two-Zone SMTZ Style",      "Two microbe species in separate zones",           2, "two_zones"),
    (11, "Competing Biofilms",       "Two microbes competing on same wall",             2, "competing"),
    (12, "Layered Biofilm",          "Two microbes in layers (one on top of other)",    2, "layered"),
    (13, "Three Species Zones",      "Three microbes in three zones along X",           3, "three_zones"),
    (14, "Grain Surface Coating",    "Biofilm coating sphere surfaces in porous medium",1, "grain_coating"),
]

# Material IDs matching CompLaB3D convention
SOLID = 0
INTERFACE = 1
PORE = 2
MICROBE_CORES = [3, 4, 5]
MICROBE_FRINGES = [6, 7, 8]

MATERIAL_NAMES = {
    0: "Solid",          1: "Interface (bounce-back)", 2: "Pore",
    3: "Microbe-1 core", 4: "Microbe-2 core",         5: "Microbe-3 core",
    6: "Microbe-1 fringe", 7: "Microbe-2 fringe",     8: "Microbe-3 fringe",
}

# RGB colors for color slice images
COLORS_RGB = {
    0: (43, 43, 43),      # Solid - dark gray
    1: (230, 159, 0),     # Interface - orange
    2: (0, 114, 178),     # Pore - blue
    3: (0, 158, 115),     # Microbe-1 core - green
    4: (204, 121, 167),   # Microbe-2 core - pink
    5: (240, 228, 66),    # Microbe-3 core - yellow
    6: (102, 194, 165),   # Microbe-1 fringe - light green
    7: (224, 160, 192),   # Microbe-2 fringe - light pink
    8: (245, 240, 160),   # Microbe-3 fringe - light yellow
}

# Hex colors for matplotlib figures
COLORS_HEX = {
    0: '#2b2b2b', 1: '#e69f00', 2: '#0072b2', 3: '#009e73',
    4: '#cc79a7', 5: '#f0e442', 6: '#66c2a5', 7: '#e0a0c0', 8: '#f5f0a0',
}


# ── Geometry generation functions ──────────────────────────────────────

def _add_interface(geometry):
    """Add interface (bounce-back) layer between solid and pore."""
    nx, ny, nz = geometry.shape
    result = geometry.copy()
    offsets = np.array([(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)])
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geometry[x, y, z] == SOLID:
                    for dx, dy, dz in offsets:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geometry[x2, y2, z2] >= PORE:
                                result[x, y, z] = INTERFACE
                                break
    return result


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
                            if geometry[x2, y2, z2] == PORE:
                                fringe_mask[x, y, z] = True
                                break
    geometry[fringe_mask] = fringe_id
    return geometry


# ── Base medium generators ─────────────────────────────────────────

def create_channel(nx, ny, nz, **_):
    geom = np.zeros((nx, ny, nz), dtype=np.uint8)
    geom[:, 2:ny-2, 2:nz-2] = PORE
    return _add_interface(geom)


def create_plates(nx, ny, nz, target_porosity=0.5, **_):
    geom = np.zeros((nx, ny, nz), dtype=np.uint8)
    gap = max(4, int(nz * target_porosity))
    wall = (nz - gap) // 2
    geom[:, :, wall:nz-wall] = PORE
    return _add_interface(geom)


def create_spheres(nx, ny, nz, target_porosity=0.5, **_):
    geom = np.full((nx, ny, nz), PORE, dtype=np.uint8)
    current = 1.0
    rng = np.random.default_rng(42)
    for _ in range(500):
        if current <= target_porosity:
            break
        cx, cy, cz = rng.integers(0, nx), rng.integers(0, ny), rng.integers(0, nz)
        r = rng.integers(3, 9)
        xs = np.arange(max(0, cx-r), min(nx, cx+r+1))
        ys = np.arange(max(0, cy-r), min(ny, cy+r+1))
        zs = np.arange(max(0, cz-r), min(nz, cz+r+1))
        xx, yy, zz = np.meshgrid(xs, ys, zs, indexing='ij')
        mask = (xx-cx)**2 + (yy-cy)**2 + (zz-cz)**2 <= r**2
        geom[xx[mask], yy[mask], zz[mask]] = SOLID
        current = np.sum(geom == PORE) / geom.size
    # Keep inlet/outlet open
    geom[0, :, :][geom[0, :, :] == SOLID] = PORE
    geom[-1, :, :][geom[-1, :, :] == SOLID] = PORE
    return _add_interface(geom)


def create_chamber(nx, ny, nz, **_):
    geom = np.zeros((nx, ny, nz), dtype=np.uint8)
    iw = max(4, min(ny, nz) // 4)
    il = int(nx * 0.2)
    y0, y1 = (ny - iw) // 2, (ny + iw) // 2
    z0, z1 = (nz - iw) // 2, (nz + iw) // 2
    geom[0:il, y0:y1, z0:z1] = PORE
    geom[il:nx-il, 2:ny-2, 2:nz-2] = PORE
    geom[nx-il:nx, y0:y1, z0:z1] = PORE
    return _add_interface(geom)


def create_hollow_box(nx, ny, nz, target_porosity=0.7, **_):
    geom = np.full((nx, ny, nz), SOLID, dtype=np.uint8)
    min_dim = min(ny, nz)
    w = max(1, int(min_dim / 2 * (1 - np.sqrt(target_porosity))))
    geom[:, w:ny-w, w:nz-w] = PORE
    return _add_interface(geom)


def create_gaussian(nx, ny, nz, target_porosity=0.5, feature_size=2, **_):
    """Generate porous medium using Gaussian random field thresholding."""
    try:
        from scipy.ndimage import gaussian_filter, binary_dilation, generate_binary_structure
    except ImportError:
        return create_spheres(nx, ny, nz, target_porosity=target_porosity)
    rng = np.random.default_rng(42)
    noise = rng.random((nx, ny, nz))
    noise = gaussian_filter(noise, sigma=(feature_size, feature_size, feature_size))
    threshold_val = np.percentile(noise, (1 - target_porosity) * 100)
    pore_mask = noise > threshold_val
    solid_mask = ~pore_mask
    struct_elem = generate_binary_structure(3, 1)
    solid_mask = binary_dilation(solid_mask, structure=struct_elem)
    pore_mask = ~solid_mask
    geom = np.where(pore_mask, PORE, SOLID).astype(np.uint8)
    geom[0, :, :][geom[0, :, :] == SOLID] = PORE
    geom[-1, :, :][geom[-1, :, :] == SOLID] = PORE
    return _add_interface(geom)


def create_fibrous(nx, ny, nz, target_porosity=0.5, **_):
    """Generate fibrous porous medium with random cylindrical fibers."""
    rng = np.random.default_rng(42)
    geom = np.full((nx, ny, nz), PORE, dtype=np.uint8)
    thickness = 1 if target_porosity >= 0.6 else 2
    num_fibers = max(100, int(500 * (1 - target_porosity)))
    fiber_length = min(50, max(nx, ny, nz))
    for fib_idx in range(num_fibers):
        x = rng.integers(0, nx)
        y = rng.integers(0, ny)
        z = rng.integers(0, nz)
        direction = rng.integers(0, 3)
        for step in range(fiber_length):
            if direction == 0:
                x = (x + 1) % nx
            elif direction == 1:
                y = (y + 1) % ny
            else:
                z = (z + 1) % nz
            for di in range(-thickness, thickness + 1):
                for dj in range(-thickness, thickness + 1):
                    for dk in range(-thickness, thickness + 1):
                        xi, yj, zk = x + di, y + dj, z + dk
                        if 0 <= xi < nx and 0 <= yj < ny and 0 <= zk < nz:
                            geom[xi, yj, zk] = SOLID
        current_porosity = np.sum(geom == PORE) / geom.size
        if current_porosity <= target_porosity:
            break
    geom[0, :, :][geom[0, :, :] == SOLID] = PORE
    geom[-1, :, :][geom[-1, :, :] == SOLID] = PORE
    return _add_interface(geom)


MEDIUM_FUNCS = {
    "channel": create_channel,
    "plates": create_plates,
    "spheres": create_spheres,
    "chamber": create_chamber,
    "hollow_box": create_hollow_box,
    "gaussian": create_gaussian,
    "fibrous": create_fibrous,
}


# ── Sessile biofilm placement functions ─────────────────────────────

def _place_bottom_wall(geom, mi=0, thickness=3, coverage=1.0):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = ci
                    break
    return _mark_fringe(geom, ci, fi)


def _place_top_wall(geom, mi=0, thickness=3, coverage=1.0):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    for x in range(nx):
        for z in range(nz):
            for y in range(ny-1, -1, -1):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y-t >= 0 and geom[x, y-t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y-t, z] = ci
                    break
    return _mark_fringe(geom, ci, fi)


def _place_both_walls(geom, mi=0, thickness=3, coverage=1.0):
    geom = _place_bottom_wall(geom, mi, thickness, coverage)
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    geom[geom == fi] = ci  # reset fringe for combined pass
    nx, ny, nz = geom.shape
    for x in range(nx):
        for z in range(nz):
            for y in range(ny-1, -1, -1):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y-t >= 0 and geom[x, y-t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y-t, z] = ci
                    break
    return _mark_fringe(geom, ci, fi)


def _place_all_walls(geom, mi=0, thickness=2, coverage=1.0):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geom[x, y, z] == PORE:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geom[x2, y2, z2] == INTERFACE:
                                if np.random.random() < coverage:
                                    geom[x, y, z] = ci
                                break
    for _ in range(thickness - 1):
        new_core = np.zeros_like(geom, dtype=bool)
        for x in range(nx):
            for y in range(ny):
                for z in range(nz):
                    if geom[x, y, z] == PORE:
                        for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                            x2, y2, z2 = x+dx, y+dy, z+dz
                            if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                                if geom[x2, y2, z2] == ci:
                                    if np.random.random() < coverage:
                                        new_core[x, y, z] = True
                                    break
        geom[new_core] = ci
    return _mark_fringe(geom, ci, fi)


def _place_inlet(geom, mi=0, thickness=3, coverage=1.0):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    depth = int(nx * 0.2)
    for x in range(depth):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = ci
                    break
    return _mark_fringe(geom, ci, fi)


def _place_outlet(geom, mi=0, thickness=3, coverage=1.0):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    start = int(nx * 0.8)
    for x in range(start, nx):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = ci
                    break
    return _mark_fringe(geom, ci, fi)


def _place_center(geom, mi=0, thickness=3, coverage=1.0):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    s, e = int(nx * 0.3), int(nx * 0.7)
    for x in range(s, e):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = ci
                    break
    return _mark_fringe(geom, ci, fi)


def _place_random_patches(geom, mi=0, **_):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    surface = []
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geom[x, y, z] == PORE:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geom[x2, y2, z2] == INTERFACE:
                                surface.append((x, y, z))
                                break
    if not surface:
        return geom
    rng = np.random.default_rng(42)
    for _ in range(15):
        cx, cy, cz = surface[rng.integers(len(surface))]
        r = rng.integers(2, 6)
        xs = np.arange(max(0, cx-r), min(nx, cx+r+1))
        ys = np.arange(max(0, cy-r), min(ny, cy+r+1))
        zs = np.arange(max(0, cz-r), min(nz, cz+r+1))
        for xi in xs:
            for yi in ys:
                for zi in zs:
                    if (xi-cx)**2 + (yi-cy)**2 + (zi-cz)**2 <= r**2:
                        if geom[xi, yi, zi] == PORE:
                            geom[xi, yi, zi] = ci
    return _mark_fringe(geom, ci, fi)


def _place_hemispheres(geom, mi=0, **_):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    rng = np.random.default_rng(42)
    for _ in range(20):
        cx = rng.integers(5, max(6, nx-5))
        cz = rng.integers(5, max(6, nz-5))
        r = rng.integers(2, 5)
        cy = None
        for y in range(ny):
            if geom[cx, y, cz] == PORE:
                cy = y
                break
        if cy is None:
            continue
        for x in range(max(0, cx-r), min(nx, cx+r+1)):
            for y in range(cy, min(ny, cy+r+1)):
                for z in range(max(0, cz-r), min(nz, cz+r+1)):
                    if (x-cx)**2 + (y-cy)**2 + (z-cz)**2 <= r**2:
                        if geom[x, y, z] == PORE:
                            geom[x, y, z] = ci
    return _mark_fringe(geom, ci, fi)


def _place_two_zones(geom, thickness=3, coverage=1.0, **_):
    nx, ny, nz = geom.shape
    third = nx // 3
    c1, f1 = MICROBE_CORES[0], MICROBE_FRINGES[0]
    c2, f2 = MICROBE_CORES[1], MICROBE_FRINGES[1]
    for x in range(third):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = c2
                    break
    for x in range(2*third, nx):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = c1
                    break
    for x in range(third, 2*third):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = c1 if np.random.random() < 0.5 else c2
                    break
    geom = _mark_fringe(geom, c1, f1)
    return _mark_fringe(geom, c2, f2)


def _place_competing(geom, thickness=3, coverage=0.8, **_):
    nx, ny, nz = geom.shape
    c1, f1 = MICROBE_CORES[0], MICROBE_FRINGES[0]
    c2, f2 = MICROBE_CORES[1], MICROBE_FRINGES[1]
    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = c1 if (x+z) % 2 == 0 else c2
                    break
    geom = _mark_fringe(geom, c1, f1)
    return _mark_fringe(geom, c2, f2)


def _place_layered(geom, thickness=3, coverage=1.0, **_):
    nx, ny, nz = geom.shape
    c1, f1 = MICROBE_CORES[0], MICROBE_FRINGES[0]
    c2, f2 = MICROBE_CORES[1], MICROBE_FRINGES[1]
    t1 = thickness // 2 + 1
    t2 = thickness // 2 + 1
    for x in range(nx):
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(t1):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = c1
                    for t in range(t1, t1+t2):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = c2
                    break
    geom = _mark_fringe(geom, c1, f1)
    return _mark_fringe(geom, c2, f2)


def _place_three_zones(geom, thickness=3, coverage=1.0, **_):
    nx, ny, nz = geom.shape
    third = nx // 3
    cores = [(MICROBE_CORES[i], MICROBE_FRINGES[i]) for i in range(3)]
    for x in range(nx):
        if x < third:
            ci, fi = cores[0]
        elif x < 2*third:
            ci, fi = cores[1]
        else:
            ci, fi = cores[2]
        for z in range(nz):
            for y in range(ny):
                if geom[x, y, z] == PORE:
                    for t in range(thickness):
                        if y+t < ny and geom[x, y+t, z] == PORE:
                            if np.random.random() < coverage:
                                geom[x, y+t, z] = ci
                    break
    for ci, fi in cores:
        geom = _mark_fringe(geom, ci, fi)
    return geom


def _place_grain_coating(geom, mi=0, coverage=0.7, **_):
    nx, ny, nz = geom.shape
    ci, fi = MICROBE_CORES[mi], MICROBE_FRINGES[mi]
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geom[x, y, z] == PORE:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geom[x2, y2, z2] == INTERFACE:
                                if np.random.random() < coverage:
                                    geom[x, y, z] = ci
                                break
    return _mark_fringe(geom, ci, fi)


def _place_two_zones_grains(geom, thickness=2, coverage=0.7, **_):
    """Two species on grain surfaces, split by X position."""
    nx, ny, nz = geom.shape
    c1, f1 = MICROBE_CORES[0], MICROBE_FRINGES[0]
    c2, f2 = MICROBE_CORES[1], MICROBE_FRINGES[1]
    mid_x = nx // 2
    for x in range(nx):
        for y in range(ny):
            for z in range(nz):
                if geom[x, y, z] == PORE:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geom[x2, y2, z2] == INTERFACE:
                                if np.random.random() < coverage:
                                    geom[x, y, z] = c1 if x < mid_x else c2
                                break
    geom = _mark_fringe(geom, c1, f1)
    return _mark_fringe(geom, c2, f2)


def _place_three_zones_grains(geom, thickness=2, coverage=0.7, **_):
    """Three species on grain surfaces, split by X into thirds."""
    nx, ny, nz = geom.shape
    third = nx // 3
    cores = [(MICROBE_CORES[i], MICROBE_FRINGES[i]) for i in range(3)]
    for x in range(nx):
        ci = cores[0][0] if x < third else (cores[1][0] if x < 2*third else cores[2][0])
        for y in range(ny):
            for z in range(nz):
                if geom[x, y, z] == PORE:
                    for dx, dy, dz in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0),(0,0,1),(0,0,-1)]:
                        x2, y2, z2 = x+dx, y+dy, z+dz
                        if 0 <= x2 < nx and 0 <= y2 < ny and 0 <= z2 < nz:
                            if geom[x2, y2, z2] == INTERFACE:
                                if np.random.random() < coverage:
                                    geom[x, y, z] = ci
                                break
    for ci, fi in cores:
        geom = _mark_fringe(geom, ci, fi)
    return geom


BIOFILM_FUNCS = {
    "bottom_wall": _place_bottom_wall,
    "top_wall": _place_top_wall,
    "both_walls": _place_both_walls,
    "all_walls": _place_all_walls,
    "inlet": _place_inlet,
    "outlet": _place_outlet,
    "center": _place_center,
    "random_patches": _place_random_patches,
    "hemispheres": _place_hemispheres,
    "two_zones": _place_two_zones,
    "competing": _place_competing,
    "layered": _place_layered,
    "three_zones": _place_three_zones,
    "grain_coating": _place_grain_coating,
}


# ── File I/O ──────────────────────────────────────────────────────────

def save_dat(geometry, filepath):
    """Save geometry in CompLaB3D text .dat format (one integer per line).

    The C++ solver reads geometry via Palabos ``>>`` operator which expects
    whitespace-separated integers in text format.  Loop order is x→y→z
    (z varies fastest) to match the Palabos natural iteration order.

    All nx*ny*nz values are written; the solver reads (nx-2) interior
    x-slices and mirrors the first/last to the boundaries.
    """
    nx, ny, nz = geometry.shape
    os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
    import numpy as np
    # Flatten in x→y→z order (Palabos natural order)
    flat = geometry.reshape(-1)  # numpy default: C-order = x→y→z
    np.savetxt(filepath, flat, fmt="%d")
    return nx * ny * nz


def build_readme(geometry, mode_name, extra_info=""):
    """Build a README string with geometry statistics."""
    nx, ny, nz = geometry.shape
    total = geometry.size
    lines = []
    lines.append("=" * 60)
    lines.append("CompLaB3D Geometry File Info")
    lines.append(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"DIMENSIONS:")
    lines.append(f"  nx = {nx}  (flow direction, X-axis)")
    lines.append(f"  ny = {ny}")
    lines.append(f"  nz = {nz}")
    lines.append(f"  Total voxels = {total:,}")
    lines.append("")
    lines.append("FLOW DIRECTION: X-axis")
    lines.append(f"  Inlet:  x = 0")
    lines.append(f"  Outlet: x = {nx-1}")
    lines.append("")
    lines.append("MATERIAL COMPOSITION:")

    for mat_id in range(9):
        count = int(np.sum(geometry == mat_id))
        if count > 0:
            pct = 100.0 * count / total
            name = MATERIAL_NAMES.get(mat_id, f"Material {mat_id}")
            lines.append(f"  {name:25s} (mask={mat_id}): {count:>10,} voxels ({pct:5.1f}%)")

    pore_count = int(np.sum(geometry == PORE))
    porosity = pore_count / total
    bio_count = sum(int(np.sum(geometry == i)) for i in [3,4,5,6,7,8])
    bio_pct = 100.0 * bio_count / total

    lines.append("")
    lines.append("SUMMARY:")
    lines.append(f"  Porosity (pore only):      {porosity:.4f}  ({100*porosity:.1f}%)")
    lines.append(f"  Biofilm coverage:          {bio_pct:.1f}%")
    lines.append(f"  Open space (pore+biofilm): {100*(pore_count+bio_count)/total:.1f}%")
    lines.append("")
    lines.append(f"GENERATION MODE: {mode_name}")
    if extra_info:
        lines.append(f"  {extra_info}")
    lines.append("")
    lines.append("MASK VALUES:")
    lines.append("  0 = Solid (impermeable)")
    lines.append("  1 = Interface (bounce-back boundary)")
    lines.append("  2 = Pore (open fluid space)")
    lines.append("  3 = Microbe-1 core (dense biofilm)")
    lines.append("  4 = Microbe-2 core")
    lines.append("  5 = Microbe-3 core")
    lines.append("  6 = Microbe-1 fringe (active growth zone)")
    lines.append("  7 = Microbe-2 fringe")
    lines.append("  8 = Microbe-3 fringe")
    lines.append("")
    lines.append("FILE FORMAT:")
    lines.append("  Text file, one voxel value per line")
    lines.append("  Loop order: x -> z -> y (MATLAB convention)")
    lines.append(f"  Expected lines: {total:,}")
    lines.append("=" * 60)
    return "\n".join(lines)


def save_slice_images(geometry, folder, prefix="slice"):
    """Save B/W YZ slice images along flow direction (X)."""
    try:
        from PIL import Image as PILImage
    except ImportError:
        return 0
    nx, ny, nz = geometry.shape
    os.makedirs(folder, exist_ok=True)
    for x in range(nx):
        img_array = np.zeros((nz, ny), dtype=np.uint8)
        for y in range(ny):
            for z in range(nz):
                img_array[z, y] = 0 if geometry[x, y, z] >= PORE else 255
        img = PILImage.fromarray(img_array, mode='L')
        img.save(os.path.join(folder, f'{prefix}_{x:04d}.png'))
    return nx


def save_color_slice_images(geometry, folder, prefix="color_slice"):
    """Save colored YZ slice images showing all material types."""
    try:
        from PIL import Image as PILImage
    except ImportError:
        return 0
    nx, ny, nz = geometry.shape
    os.makedirs(folder, exist_ok=True)
    for x in range(nx):
        img_array = np.zeros((nz, ny, 3), dtype=np.uint8)
        for y in range(ny):
            for z in range(nz):
                mat_id = geometry[x, y, z]
                img_array[z, y] = COLORS_RGB.get(mat_id, (128, 128, 128))
        img = PILImage.fromarray(img_array, mode='RGB')
        img.save(os.path.join(folder, f'{prefix}_{x:04d}.png'))
    return nx


def save_2d_slice_stacks(geometry, folder, prefix="slice"):
    """Save 2D Z-slices (XY planes) as BMP stacks for 2D simulations.

    Saves all slices and separately saves only connected slices
    (verified pore connectivity from left to right).
    """
    try:
        from PIL import Image as PILImage
        from scipy.ndimage import label as ndimage_label
    except ImportError:
        return 0, 0
    nx, ny, nz = geometry.shape
    all_dir = os.path.join(folder, "2D_slices")
    conn_dir = os.path.join(folder, "2D_slices_connected")
    os.makedirs(all_dir, exist_ok=True)
    os.makedirs(conn_dir, exist_ok=True)
    connected_count = 0
    for z in range(nz):
        slice_z = geometry[:, :, z].T
        bw = np.where(slice_z >= PORE, np.uint8(255), np.uint8(0))
        fname = f"{prefix}_S{z+1:04d}.bmp"
        img = PILImage.fromarray(bw, mode='L')
        img.save(os.path.join(all_dir, fname))
        pore_field = (slice_z >= PORE).astype(np.int32)
        labeled, _ = ndimage_label(pore_field)
        left_labels = set(np.unique(labeled[:, 0])) - {0}
        right_labels = set(np.unique(labeled[:, -1])) - {0}
        if left_labels & right_labels:
            img.save(os.path.join(conn_dir, fname))
            connected_count += 1
    return nz, connected_count


def create_geometry_figure(geometry, filepath_base, title="Geometry"):
    """Create publication-quality geometry visualization (PNG + PDF)."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from matplotlib.colors import ListedColormap, BoundaryNorm
    except ImportError:
        return

    nx, ny, nz = geometry.shape
    fig, axes = plt.subplots(1, 3, figsize=(10, 3.5))

    unique_vals = np.unique(geometry)
    colors_list = [COLORS_HEX.get(v, '#888888') for v in unique_vals]
    cmap = ListedColormap(colors_list)
    bounds = list(unique_vals) + [unique_vals[-1] + 1]
    norm = BoundaryNorm(bounds, cmap.N)

    mid_z = nz // 2
    axes[0].imshow(geometry[:, :, mid_z].T, origin='lower',
                   cmap=cmap, norm=norm, aspect='equal')
    axes[0].set_xlabel('X (flow)')
    axes[0].set_ylabel('Y')
    axes[0].set_title(f'XY plane (z={mid_z})')

    mid_y = ny // 2
    axes[1].imshow(geometry[:, mid_y, :].T, origin='lower',
                   cmap=cmap, norm=norm, aspect='equal')
    axes[1].set_xlabel('X (flow)')
    axes[1].set_ylabel('Z')
    axes[1].set_title(f'XZ plane (y={mid_y})')

    mid_x = nx // 2
    axes[2].imshow(geometry[mid_x, :, :].T, origin='lower',
                   cmap=cmap, norm=norm, aspect='equal')
    axes[2].set_xlabel('Y')
    axes[2].set_ylabel('Z')
    axes[2].set_title(f'YZ plane (x={mid_x})')

    patches = [mpatches.Patch(color=COLORS_HEX.get(v, '#888888'),
               label=MATERIAL_NAMES.get(v, f'Mat {v}'))
               for v in unique_vals]
    fig.legend(handles=patches, loc='upper center',
               bbox_to_anchor=(0.5, 0.02),
               ncol=min(len(patches), 5), fontsize=7,
               framealpha=0.9)

    plt.suptitle(title, fontsize=9, fontweight='bold')
    plt.tight_layout(rect=[0, 0.12, 1, 0.95])

    for ext in ['png', 'pdf']:
        plt.savefig(f"{filepath_base}.{ext}", dpi=600, bbox_inches='tight')
    plt.close()


# ── Worker Thread ──────────────────────────────────────────────────────

class GeometryWorker(QThread):
    """Background worker for geometry generation."""

    progress = Signal(int, str)
    finished = Signal(bool, str, str, str)  # success, message, output_path, readme

    def __init__(self, params):
        super().__init__()
        self.params = params

    def run(self):
        try:
            p = self.params
            generator = p["generator"]  # "abiotic", "sessile", "image"
            output_dir = p["output_dir"]

            if generator == "abiotic":
                self._run_abiotic(p, output_dir)
            elif generator == "sessile":
                self._run_sessile(p, output_dir)
            elif generator == "image":
                self._run_image(p, output_dir)
            else:
                self.finished.emit(False, f"Unknown generator: {generator}", "", "")

        except Exception as e:
            import traceback
            self.finished.emit(False, f"Error: {e}\n{traceback.format_exc()}", "", "")

    def _save_outputs(self, geom, output_dir, readme, label="geometry"):
        """Save all requested output files into the directory structure."""
        p = self.params
        input_dir = os.path.join(output_dir, "input")
        images_dir = os.path.join(output_dir, "images")
        os.makedirs(input_dir, exist_ok=True)

        # Always save geometry.dat and README
        dat_path = os.path.join(input_dir, "geometry.dat")
        n = save_dat(geom, dat_path)

        readme_path = os.path.join(output_dir, "README.txt")
        with open(readme_path, "w") as f:
            f.write(readme)

        files_created = [dat_path, readme_path]

        # Optional: B/W slice images
        if p.get("save_bw_slices", False):
            self.progress.emit(82, "Saving B/W slice images...")
            ns = save_slice_images(geom, images_dir, "slice")
            files_created.append(f"{images_dir}/slice_*.png ({ns} files)")

        # Optional: Color slice images
        if p.get("save_color_slices", False):
            self.progress.emit(88, "Saving color slice images...")
            ns = save_color_slice_images(geom, images_dir, "color_slice")
            files_created.append(f"{images_dir}/color_slice_*.png ({ns} files)")

        # Optional: Publication figure
        if p.get("save_pub_figure", False):
            self.progress.emit(90, "Creating publication figure...")
            fig_base = os.path.join(output_dir, label)
            create_geometry_figure(geom, fig_base, title=label)
            files_created.append(f"{fig_base}.png")
            files_created.append(f"{fig_base}.pdf")

        # Optional: 2D slice stacks (BMP)
        if p.get("save_2d_stacks", False):
            self.progress.emit(95, "Saving 2D slice stacks (BMP)...")
            stacks_dir = os.path.join(output_dir, "stacks")
            n_total, n_conn = save_2d_slice_stacks(geom, stacks_dir, label)
            files_created.append(f"{stacks_dir}/2D_slices/ ({n_total} BMP files)")
            files_created.append(f"{stacks_dir}/2D_slices_connected/ ({n_conn} connected)")

        return dat_path, n, files_created

    def _run_abiotic(self, p, output_dir):
        nx, ny, nz = p["nx"], p["ny"], p["nz"]
        medium = p["medium_func"]
        porosity = p["target_porosity"]
        feature_size = p.get("feature_size", 2)

        self.progress.emit(10, f"Creating {medium} medium {nx}x{ny}x{nz}...")
        func = MEDIUM_FUNCS[medium]
        geom = func(nx, ny, nz, target_porosity=porosity, feature_size=feature_size)

        self.progress.emit(70, "Saving outputs...")
        readme = build_readme(geom, f"Abiotic - {medium}", f"Target porosity: {porosity:.2f}")
        dat_path, n, files = self._save_outputs(
            geom, output_dir, readme, f"abiotic_{medium}")

        self.progress.emit(100, "Done!")
        self.finished.emit(True,
            f"Geometry saved: {dat_path}\n"
            f"Dimensions: {nx} x {ny} x {nz} = {n:,} voxels\n"
            f"Files created: {len(files)}",
            dat_path, readme)

    def _run_sessile(self, p, output_dir):
        nx, ny, nz = p["nx"], p["ny"], p["nz"]
        medium = p["medium_func"]
        porosity = p["target_porosity"]
        feature_size = p.get("feature_size", 2)
        scenario_idx = p["scenario_idx"]
        thickness = p["biofilm_thickness"]
        coverage = p["biofilm_coverage"]

        scenario = SESSILE_SCENARIOS[scenario_idx]
        sid, sname, sdesc, n_microbes, location = scenario

        self.progress.emit(10, f"Creating {medium} medium {nx}x{ny}x{nz}...")
        func = MEDIUM_FUNCS[medium]
        geom = func(nx, ny, nz, target_porosity=porosity, feature_size=feature_size)

        self.progress.emit(40, f"Placing biofilm: {sname}...")
        bio_func = BIOFILM_FUNCS[location]
        if n_microbes == 1:
            geom = bio_func(geom, mi=0, thickness=thickness, coverage=coverage)
        else:
            geom = bio_func(geom, thickness=thickness, coverage=coverage)

        self.progress.emit(70, "Saving outputs...")
        extra = (f"Scenario {sid}: {sname}\n"
                 f"  {sdesc}\n"
                 f"  Species: {n_microbes}, Thickness: {thickness}, Coverage: {coverage:.0%}")
        readme = build_readme(geom, f"Sessile Biofilm - {medium}", extra)
        dat_path, n, files = self._save_outputs(
            geom, output_dir, readme, f"geometry_S{sid:02d}")

        self.progress.emit(100, "Done!")
        self.finished.emit(True,
            f"Geometry saved: {dat_path}\n"
            f"Dimensions: {nx} x {ny} x {nz} = {n:,} voxels\n"
            f"Scenario: {sid} - {sname}\n"
            f"Files created: {len(files)}",
            dat_path, readme)

    def _run_image(self, p, output_dir):
        folder = p["image_folder"]
        bio_species = p.get("biofilm_species", 0)
        bio_location = p.get("biofilm_location", 1)
        bio_thickness = p.get("biofilm_thickness", 2)
        bio_coverage = p.get("biofilm_coverage", 0.7)

        self.progress.emit(5, "Scanning image folder...")
        extensions = ['*.bmp', '*.png', '*.tif', '*.tiff', '*.jpg', '*.jpeg']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(folder, ext)))
            files.extend(glob.glob(os.path.join(folder, ext.upper())))
        files = sorted(set(files))

        if not files:
            self.finished.emit(False, f"No image files found in {folder}", "", "")
            return

        try:
            from PIL import Image
        except ImportError:
            self.finished.emit(False,
                "Pillow not installed. Run: pip install Pillow", "", "")
            return

        self.progress.emit(10, f"Found {len(files)} images...")
        first_img = np.array(Image.open(files[0]).convert('L'))
        img_h, img_w = first_img.shape
        n_slices = len(files)
        nx, ny, nz = n_slices, img_w, img_h

        geom = np.zeros((nx, ny, nz), dtype=np.uint8)
        for x, filepath in enumerate(files):
            img = np.array(Image.open(filepath).convert('L'))
            for y in range(min(ny, img.shape[1])):
                for z in range(min(nz, img.shape[0])):
                    geom[x, y, z] = PORE if img[z, y] == 0 else SOLID
            if (x + 1) % max(1, n_slices // 10) == 0:
                pct = 10 + int(40 * (x + 1) / n_slices)
                self.progress.emit(pct, f"Processed {x+1}/{n_slices} slices...")

        self.progress.emit(55, "Adding interface layer...")
        geom = _add_interface(geom)

        # Add biofilm if requested
        bio_label = ""
        if bio_species >= 1:
            self.progress.emit(60, f"Adding {bio_species}-species biofilm...")
            loc_names = {1: "All surfaces", 2: "Inlet region", 3: "Outlet region",
                         4: "Center region", 5: "Random patches", 6: "Zoned by X"}
            bio_label = f" + {bio_species} species biofilm ({loc_names.get(bio_location, '')})"

            if bio_species == 1:
                if bio_location == 1:
                    geom = _place_grain_coating(geom, mi=0, coverage=bio_coverage)
                elif bio_location == 2:
                    geom = _place_inlet(geom, mi=0, thickness=bio_thickness, coverage=bio_coverage)
                elif bio_location == 3:
                    geom = _place_outlet(geom, mi=0, thickness=bio_thickness, coverage=bio_coverage)
                elif bio_location == 4:
                    geom = _place_center(geom, mi=0, thickness=bio_thickness, coverage=bio_coverage)
                elif bio_location == 5:
                    geom = _place_random_patches(geom, mi=0)
                else:
                    geom = _place_grain_coating(geom, mi=0, coverage=bio_coverage)
            elif bio_species == 2:
                if bio_location == 6:
                    geom = _place_two_zones_grains(geom, thickness=bio_thickness, coverage=bio_coverage)
                else:
                    geom = _place_competing(geom, thickness=bio_thickness, coverage=bio_coverage)
            elif bio_species == 3:
                if bio_location == 6:
                    geom = _place_three_zones_grains(geom, thickness=bio_thickness, coverage=bio_coverage)
                else:
                    geom = _place_three_zones(geom, thickness=bio_thickness, coverage=bio_coverage)

        self.progress.emit(70, "Saving outputs...")
        readme = build_readme(geom, f"Image Stack Import from {folder}{bio_label}")
        dat_path, n, out_files = self._save_outputs(
            geom, output_dir, readme, "image_geometry")

        self.progress.emit(100, "Done!")
        self.finished.emit(True,
            f"Converted {n_slices} images -> {dat_path}\n"
            f"Dimensions: {nx} x {ny} x {nz} = {n:,} voxels\n"
            f"Files created: {len(out_files)}",
            dat_path, readme)


# ── Dialog ─────────────────────────────────────────────────────────────

class GeometryCreatorDialog(QDialog):
    """CompLaB3D Geometry Generator v6.0 - Mini GUI.

    Three generators: Abiotic | Sessile Biofilm | Image Converter
    """

    def __init__(self, project=None, config=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("CompLaB3D Geometry Generator v6.0")
        self.setMinimumSize(780, 720)
        self._project = project
        self._config = config
        self._worker = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Header
        heading = QLabel("CompLaB3D Geometry Generator v6.0")
        heading.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(heading)

        credit = QLabel(
            "S. Asgari & C. Meile  |  Dept. Marine Sciences, Univ. of Georgia")
        credit.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(credit)

        # Main tabs: three generators
        self._main_tabs = QTabWidget()

        # ── Tab 1: Abiotic ─────────────────────────────────────
        self._main_tabs.addTab(self._build_abiotic_tab(), "Abiotic Domain")

        # ── Tab 2: Sessile Biofilm ─────────────────────────────
        self._main_tabs.addTab(self._build_sessile_tab(), "Sessile Biofilm")

        # ── Tab 3: Image Converter ─────────────────────────────
        self._main_tabs.addTab(self._build_image_tab(), "Image Converter")

        # ── Tab 4: Help ───────────────────────────────────────
        self._main_tabs.addTab(self._build_help_tab(), "Help")

        layout.addWidget(self._main_tabs)

        # ── Shared output/progress section ─────────────────────
        out_group = QGroupBox("Output")
        out_layout = QVBoxLayout()

        # Output directory path
        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Output folder:"))
        self._output_edit = QLineEdit("geometry_output")
        self._output_edit.setToolTip(
            "Output directory. Structure:\n"
            "  folder/input/geometry.dat\n"
            "  folder/images/slice_*.png (B/W)\n"
            "  folder/images/color_slice_*.png\n"
            "  folder/README.txt\n"
            "  folder/geometry_figure.png/pdf")
        path_row.addWidget(self._output_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_output)
        path_row.addWidget(browse_btn)
        out_layout.addLayout(path_row)

        # Output options
        opts_row = QHBoxLayout()
        self._opt_bw_slices = QCheckBox("B/W slice images")
        self._opt_bw_slices.setChecked(True)
        self._opt_bw_slices.setToolTip("Save black/white YZ slice images (one per X position)")
        opts_row.addWidget(self._opt_bw_slices)

        self._opt_color_slices = QCheckBox("Color slice images")
        self._opt_color_slices.setChecked(True)
        self._opt_color_slices.setToolTip("Save colored YZ slice images showing all material types")
        opts_row.addWidget(self._opt_color_slices)

        self._opt_pub_figure = QCheckBox("Publication figure")
        self._opt_pub_figure.setChecked(True)
        self._opt_pub_figure.setToolTip("Save publication-quality XY/XZ/YZ cross-section figure (PNG + PDF)")
        opts_row.addWidget(self._opt_pub_figure)

        self._opt_2d_stacks = QCheckBox("2D slice stacks (BMP)")
        self._opt_2d_stacks.setChecked(False)
        self._opt_2d_stacks.setToolTip(
            "Save 2D Z-slices as BMP image stacks for 2D simulations.\n"
            "Creates: 2D_slices/ (all) + 2D_slices_connected/ (flow-connected only)\n"
            "WHITE=Pore, BLACK=Solid")
        opts_row.addWidget(self._opt_2d_stacks)

        opts_row.addStretch()
        out_layout.addLayout(opts_row)

        # Generate button
        gen_row = QHBoxLayout()
        self._gen_btn = QPushButton("Generate Geometry")
        self._gen_btn.setStyleSheet(
            "QPushButton { background: #0078d4; color: white; "
            "padding: 8px 24px; font-weight: bold; font-size: 12px; }")
        self._gen_btn.clicked.connect(self._generate)
        gen_row.addWidget(self._gen_btn)
        gen_row.addStretch()
        out_layout.addLayout(gen_row)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setVisible(False)
        out_layout.addWidget(self._progress)
        self._status_lbl = QLabel("")
        out_layout.addWidget(self._status_lbl)

        out_group.setLayout(out_layout)
        layout.addWidget(out_group)

        # ── README / Results display ───────────────────────────
        readme_group = QGroupBox("Geometry Info / README")
        readme_layout = QVBoxLayout()
        self._readme_text = QTextEdit()
        self._readme_text.setReadOnly(True)
        self._readme_text.setFont(QFont("Consolas", 9))
        self._readme_text.setMaximumHeight(200)
        self._readme_text.setStyleSheet(
            "QTextEdit { background: #1e1e1e; color: #d4d4d4;"
            " border: 1px solid #3c3c3c; }")
        readme_layout.addWidget(self._readme_text)
        readme_group.setLayout(readme_layout)
        layout.addWidget(readme_group)

        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        # Pre-fill from project
        if self._project:
            try:
                self._abio_nx.setValue(self._project.domain.nx)
                self._abio_ny.setValue(self._project.domain.ny)
                self._abio_nz.setValue(self._project.domain.nz)
                self._bio_nx.setValue(self._project.domain.nx)
                self._bio_ny.setValue(self._project.domain.ny)
                self._bio_nz.setValue(self._project.domain.nz)
            except Exception:
                pass

    # ── Tab builders ───────────────────────────────────────────

    def _build_abiotic_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        w = QWidget()
        lay = QVBoxLayout(w)

        lay.addWidget(self._make_info(
            "Create porous media domains without biofilm.\n"
            "5 medium types available. Flow direction: X-axis."))

        # Medium type
        med_group = QGroupBox("Medium Type")
        med_form = QFormLayout()
        self._abio_medium = QComboBox()
        for name, _ in MEDIUM_TYPES:
            self._abio_medium.addItem(name)
        self._abio_medium.setToolTip(
            "Channel: simple rectangular duct\n"
            "Plates: two parallel plates (Z-walls)\n"
            "Spheres: overlapping random spheres (most realistic porous medium)\n"
            "Chamber: wide reaction chamber with narrow inlet/outlet\n"
            "Box: hollow box with configurable porosity")
        med_form.addRow("Medium:", self._abio_medium)
        med_group.setLayout(med_form)
        lay.addWidget(med_group)

        # Dimensions
        dim_group = QGroupBox("Domain Dimensions")
        dim_form = QFormLayout()
        self._abio_nx = QSpinBox(); self._abio_nx.setRange(3, 1000); self._abio_nx.setValue(50)
        self._abio_ny = QSpinBox(); self._abio_ny.setRange(3, 1000); self._abio_ny.setValue(30)
        self._abio_nz = QSpinBox(); self._abio_nz.setRange(3, 1000); self._abio_nz.setValue(30)
        dim_form.addRow("nx (flow direction):", self._abio_nx)
        dim_form.addRow("ny:", self._abio_ny)
        dim_form.addRow("nz:", self._abio_nz)
        dim_group.setLayout(dim_form)
        lay.addWidget(dim_group)

        # Porosity
        por_group = QGroupBox("Porosity")
        por_form = QFormLayout()
        self._abio_porosity = QDoubleSpinBox()
        self._abio_porosity.setRange(0.1, 0.95)
        self._abio_porosity.setDecimals(2)
        self._abio_porosity.setValue(0.50)
        self._abio_porosity.setSingleStep(0.05)
        self._abio_porosity.setToolTip(
            "Target porosity for porous media.\n"
            "0.3 = tight packing, 0.5 = moderate, 0.7 = loose")
        por_form.addRow("Target porosity:", self._abio_porosity)
        por_group.setLayout(por_form)
        lay.addWidget(por_group)

        # Gaussian-specific parameters (shown only for Gaussian medium)
        self._abio_gaussian_group = QGroupBox("Gaussian Parameters")
        gau_form = QFormLayout()
        self._abio_feature_size = QSpinBox()
        self._abio_feature_size.setRange(1, 20)
        self._abio_feature_size.setValue(2)
        self._abio_feature_size.setToolTip(
            "Controls grain/pore feature size.\n"
            "Larger values = bigger pores and grains.\n"
            "Typical range: 1-5")
        gau_form.addRow("Feature size:", self._abio_feature_size)
        self._abio_gaussian_group.setLayout(gau_form)
        self._abio_gaussian_group.setVisible(False)
        lay.addWidget(self._abio_gaussian_group)

        # Connect medium selector to show/hide Gaussian params
        self._abio_medium.currentIndexChanged.connect(self._on_abio_medium_changed)

        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_sessile_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        w = QWidget()
        lay = QVBoxLayout(w)

        lay.addWidget(self._make_info(
            "Create biofilm geometries with 14 placement scenarios.\n"
            "Each microbe species gets a core + fringe layer."))

        # Scenario selection
        sc_group = QGroupBox("Biofilm Scenario")
        sc_form = QFormLayout()
        self._bio_scenario = QComboBox()
        for sid, name, desc, n_mic, loc in SESSILE_SCENARIOS:
            species_tag = f"[{n_mic} species]" if n_mic > 1 else ""
            self._bio_scenario.addItem(f"{sid}. {name} {species_tag}")
        self._bio_scenario.currentIndexChanged.connect(self._on_scenario_changed)
        sc_form.addRow("Scenario:", self._bio_scenario)

        self._bio_scenario_desc = QLabel(SESSILE_SCENARIOS[0][2])
        self._bio_scenario_desc.setWordWrap(True)
        self._bio_scenario_desc.setStyleSheet("color: #888; padding: 4px;")
        sc_form.addRow("", self._bio_scenario_desc)

        sc_group.setLayout(sc_form)
        lay.addWidget(sc_group)

        # Medium type
        med_group = QGroupBox("Base Medium")
        med_form = QFormLayout()
        self._bio_medium = QComboBox()
        for name, _ in MEDIUM_TYPES:
            self._bio_medium.addItem(name)
        med_form.addRow("Medium:", self._bio_medium)
        med_group.setLayout(med_form)
        lay.addWidget(med_group)

        # Dimensions
        dim_group = QGroupBox("Domain Dimensions")
        dim_form = QFormLayout()
        self._bio_nx = QSpinBox(); self._bio_nx.setRange(3, 1000); self._bio_nx.setValue(50)
        self._bio_ny = QSpinBox(); self._bio_ny.setRange(3, 1000); self._bio_ny.setValue(30)
        self._bio_nz = QSpinBox(); self._bio_nz.setRange(3, 1000); self._bio_nz.setValue(30)
        dim_form.addRow("nx (flow direction):", self._bio_nx)
        dim_form.addRow("ny:", self._bio_ny)
        dim_form.addRow("nz:", self._bio_nz)
        dim_group.setLayout(dim_form)
        lay.addWidget(dim_group)

        # Biofilm parameters
        bf_group = QGroupBox("Biofilm Parameters")
        bf_form = QFormLayout()

        self._bio_porosity = QDoubleSpinBox()
        self._bio_porosity.setRange(0.1, 0.95)
        self._bio_porosity.setDecimals(2)
        self._bio_porosity.setValue(0.50)
        self._bio_porosity.setSingleStep(0.05)
        bf_form.addRow("Target porosity:", self._bio_porosity)

        self._bio_thickness = QSpinBox()
        self._bio_thickness.setRange(1, 20)
        self._bio_thickness.setValue(3)
        self._bio_thickness.setToolTip("Biofilm thickness in voxels")
        bf_form.addRow("Biofilm thickness:", self._bio_thickness)

        self._bio_coverage = QDoubleSpinBox()
        self._bio_coverage.setRange(0.0, 1.0)
        self._bio_coverage.setDecimals(2)
        self._bio_coverage.setValue(1.0)
        self._bio_coverage.setSingleStep(0.1)
        self._bio_coverage.setToolTip("Biofilm surface coverage fraction (0-1)")
        bf_form.addRow("Coverage:", self._bio_coverage)

        bf_group.setLayout(bf_form)
        lay.addWidget(bf_group)

        # Material number info for biofilm (core + fringe IDs)
        mat_group = QGroupBox("Biofilm Material Numbers")
        mat_lay = QVBoxLayout()
        self._bio_material_info = QLabel()
        self._bio_material_info.setWordWrap(True)
        self._bio_material_info.setStyleSheet(
            "color: #8ac; padding: 6px; font-family: Consolas, monospace; font-size: 11px;")
        self._bio_material_info.setText(
            "Microbe 1:  core = 3,  fringe = 6")
        mat_lay.addWidget(self._bio_material_info)
        mat_group.setLayout(mat_lay)
        lay.addWidget(mat_group)

        # Gaussian-specific parameters (shown only for Gaussian medium)
        self._bio_gaussian_group = QGroupBox("Gaussian Parameters")
        gau_form = QFormLayout()
        self._bio_feature_size = QSpinBox()
        self._bio_feature_size.setRange(1, 20)
        self._bio_feature_size.setValue(2)
        self._bio_feature_size.setToolTip(
            "Controls grain/pore feature size for Gaussian medium.\n"
            "Larger values = bigger pores and grains.")
        gau_form.addRow("Feature size:", self._bio_feature_size)
        self._bio_gaussian_group.setLayout(gau_form)
        self._bio_gaussian_group.setVisible(False)
        lay.addWidget(self._bio_gaussian_group)

        # Connect medium selector to show/hide Gaussian params
        self._bio_medium.currentIndexChanged.connect(self._on_bio_medium_changed)

        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_image_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        w = QWidget()
        lay = QVBoxLayout(w)

        lay.addWidget(self._make_info(
            "Convert image stacks (BMP, PNG, TIF, JPG) to CompLaB3D .dat geometry.\n"
            "Each image becomes one X-slice. Dark pixels = pore, light = solid."))

        # Image folder
        folder_group = QGroupBox("Image Stack")
        folder_form = QFormLayout()

        folder_row = QHBoxLayout()
        self._img_folder = QLineEdit()
        self._img_folder.setPlaceholderText("Folder containing image slices...")
        folder_row.addWidget(self._img_folder)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_img_folder)
        folder_row.addWidget(browse_btn)
        folder_form.addRow("Image folder:", folder_row)

        folder_group.setLayout(folder_form)
        lay.addWidget(folder_group)

        # Biofilm options for converted images
        bio_group = QGroupBox("Add Biofilm (optional)")
        bio_form = QFormLayout()

        self._img_biofilm_species = QComboBox()
        self._img_biofilm_species.addItems([
            "0 - No biofilm (abiotic only)",
            "1 - Single species",
            "2 - Two species",
            "3 - Three species",
        ])
        self._img_biofilm_species.currentIndexChanged.connect(
            self._on_img_biofilm_changed)
        bio_form.addRow("Biofilm species:", self._img_biofilm_species)

        self._img_bio_location = QComboBox()
        self._img_bio_location.addItems([
            "1 - All grain surfaces",
            "2 - Inlet region (first 20% of X)",
            "3 - Outlet region (last 20% of X)",
            "4 - Center region (middle 40% of X)",
            "5 - Random patches",
            "6 - Zoned by X (species separated)",
        ])
        self._img_bio_location.setEnabled(False)
        bio_form.addRow("Location:", self._img_bio_location)

        self._img_bio_thickness = QSpinBox()
        self._img_bio_thickness.setRange(1, 20)
        self._img_bio_thickness.setValue(2)
        self._img_bio_thickness.setEnabled(False)
        bio_form.addRow("Thickness:", self._img_bio_thickness)

        self._img_bio_coverage = QDoubleSpinBox()
        self._img_bio_coverage.setRange(0.1, 1.0)
        self._img_bio_coverage.setDecimals(2)
        self._img_bio_coverage.setValue(0.70)
        self._img_bio_coverage.setSingleStep(0.1)
        self._img_bio_coverage.setEnabled(False)
        bio_form.addRow("Coverage:", self._img_bio_coverage)

        # Material number info
        self._img_material_info = QLabel("")
        self._img_material_info.setWordWrap(True)
        self._img_material_info.setStyleSheet(
            "color: #8ac; padding: 4px; font-family: Consolas, monospace; font-size: 11px;")
        self._img_material_info.setVisible(False)
        bio_form.addRow("Material IDs:", self._img_material_info)

        bio_group.setLayout(bio_form)
        lay.addWidget(bio_group)

        lay.addStretch()
        scroll.setWidget(w)
        return scroll

    def _build_help_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        w = QWidget()
        lay = QVBoxLayout(w)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setFont(QFont("Segoe UI", 10))
        help_text.setStyleSheet(
            "QTextEdit { background: #1e1e1e; color: #d4d4d4; border: none; }")
        help_text.setHtml(
            "<h2 style='color:#4fc3f7;'>CompLaB3D Geometry Generator - Help</h2>"
            "<p>This tool creates geometry files (<code>.dat</code>) for CompLaB3D simulations. "
            "Three generator modes are available, plus this help page.</p>"

            "<hr><h3 style='color:#81c784;'>Material ID System</h3>"
            "<table cellpadding='4' style='border-collapse:collapse; color:#d4d4d4;'>"
            "<tr style='background:#333;'><th>ID</th><th>Material</th><th>Description</th></tr>"
            "<tr><td><b>0</b></td><td>Solid</td><td>Impermeable solid phase</td></tr>"
            "<tr><td><b>1</b></td><td>Interface</td><td>Bounce-back boundary between solid and fluid</td></tr>"
            "<tr><td><b>2</b></td><td>Pore</td><td>Open fluid space</td></tr>"
            "<tr><td><b>3</b></td><td>Microbe-1 core</td><td>Dense biofilm for species 1</td></tr>"
            "<tr><td><b>4</b></td><td>Microbe-2 core</td><td>Dense biofilm for species 2</td></tr>"
            "<tr><td><b>5</b></td><td>Microbe-3 core</td><td>Dense biofilm for species 3</td></tr>"
            "<tr><td><b>6</b></td><td>Microbe-1 fringe</td><td>Active growth zone for species 1</td></tr>"
            "<tr><td><b>7</b></td><td>Microbe-2 fringe</td><td>Active growth zone for species 2</td></tr>"
            "<tr><td><b>8</b></td><td>Microbe-3 fringe</td><td>Active growth zone for species 3</td></tr>"
            "</table>"
            "<p><i>Core</i> = interior of biofilm colony. <i>Fringe</i> = outermost layer adjacent to pore space (active growth zone).</p>"

            "<hr><h3 style='color:#81c784;'>Medium Types (7 available)</h3>"
            "<p>All medium types are available in both <b>Abiotic</b> and <b>Sessile Biofilm</b> tabs.</p>"
            "<ol>"
            "<li><b>Rectangular Channel</b> - Simple rectangular duct with solid walls. Good for basic flow tests.</li>"
            "<li><b>Parallel Plates</b> - Two parallel plates along Z-axis. Porosity controls gap width.</li>"
            "<li><b>Overlapping Spheres</b> - Random sphere packing. Most realistic porous medium. "
            "Porosity controls number of spheres placed.</li>"
            "<li><b>Reaction Chamber</b> - Wide central chamber with narrow inlet/outlet channels. "
            "Good for studying reactions in confined spaces.</li>"
            "<li><b>Hollow Box</b> - Box with solid walls and hollow interior. Porosity controls wall thickness.</li>"
            "<li><b>Gaussian Random Field</b> - Porous medium generated by "
            "thresholding a Gaussian-filtered random noise field. <b>Feature size</b> controls grain/pore "
            "dimensions (1=fine, 5=coarse). Requires <code>scipy</code>.</li>"
            "<li><b>Fibrous Medium</b> - Random cylindrical fibers in 3D. Simulates fibrous materials like "
            "filter media or biofilm support structures. Fiber thickness auto-adjusts from porosity.</li>"
            "</ol>"

            "<hr><h3 style='color:#81c784;'>Abiotic Domain Tab</h3>"
            "<p>Creates porous media <b>without biofilm</b>. Choose a medium type, set domain "
            "dimensions (nx, ny, nz), and target porosity. Flow direction is always X-axis "
            "(inlet at x=0, outlet at x=nx-1).</p>"

            "<hr><h3 style='color:#81c784;'>Sessile Biofilm Tab</h3>"
            "<p>Creates a base porous medium then places biofilm in one of <b>14 spatial scenarios</b>:</p>"
            "<table cellpadding='3' style='border-collapse:collapse; color:#d4d4d4;'>"
            "<tr style='background:#333;'><th>#</th><th>Scenario</th><th>Species</th><th>Description</th></tr>"
            "<tr><td>1</td><td>Bottom Wall</td><td>1</td><td>Biofilm on bottom Y wall</td></tr>"
            "<tr><td>2</td><td>Top Wall</td><td>1</td><td>Biofilm on top Y wall</td></tr>"
            "<tr><td>3</td><td>Both Walls</td><td>1</td><td>Biofilm on top and bottom Y walls</td></tr>"
            "<tr><td>4</td><td>All Walls</td><td>1</td><td>Biofilm coating all 6 wall surfaces</td></tr>"
            "<tr><td>5</td><td>Inlet Region</td><td>1</td><td>Biofilm near inlet (first 20% of X)</td></tr>"
            "<tr><td>6</td><td>Outlet Region</td><td>1</td><td>Biofilm near outlet (last 20% of X)</td></tr>"
            "<tr><td>7</td><td>Center Region</td><td>1</td><td>Biofilm in center (30-70% of X)</td></tr>"
            "<tr><td>8</td><td>Random Patches</td><td>1</td><td>Random spherical biofilm bumps on surfaces</td></tr>"
            "<tr><td>9</td><td>Hemispheres</td><td>1</td><td>Hemispherical colonies on bottom wall</td></tr>"
            "<tr><td>10</td><td>Two-Zone SMTZ</td><td>2</td><td>Two species in separate zones (left/right)</td></tr>"
            "<tr><td>11</td><td>Competing</td><td>2</td><td>Two species on same wall (checkerboard)</td></tr>"
            "<tr><td>12</td><td>Layered</td><td>2</td><td>Two species in vertical layers</td></tr>"
            "<tr><td>13</td><td>Three Zones</td><td>3</td><td>Three species along X in thirds</td></tr>"
            "<tr><td>14</td><td>Grain Coating</td><td>1</td><td>Biofilm on all grain surfaces (spheres medium)</td></tr>"
            "</table>"
            "<p><b>Parameters:</b> Thickness = biofilm thickness in voxels (1-20). "
            "Coverage = fraction of surface covered (0.0-1.0).</p>"
            "<p><b>Material IDs</b> are shown in the 'Biofilm Material Numbers' box and update "
            "based on the selected scenario's species count.</p>"

            "<hr><h3 style='color:#81c784;'>Image Stack Converter Tab</h3>"
            "<p>Converts image stacks (BMP, PNG, TIF, JPG) to CompLaB3D <code>.dat</code> format.</p>"
            "<ul>"
            "<li>Each image = one X-slice (flow direction)</li>"
            "<li><b>Black pixels</b> (0) = Pore (fluid)</li>"
            "<li><b>White pixels</b> (255) = Solid</li>"
            "<li>Optional: add 1-3 species of biofilm to converted geometry</li>"
            "<li>Biofilm material IDs shown when species &gt; 0</li>"
            "</ul>"

            "<hr><h3 style='color:#81c784;'>Output Options</h3>"
            "<ul>"
            "<li><b>B/W slice images</b> - Black/white YZ cross-sections (one PNG per X position)</li>"
            "<li><b>Color slice images</b> - Color-coded YZ cross-sections showing all material types</li>"
            "<li><b>Publication figure</b> - Three-panel XY/XZ/YZ figure (PNG + PDF, 600 DPI)</li>"
            "<li><b>2D Slice Stacks (BMP)</b> - Z-slices as BMP images for 2D simulations. "
            "Creates two folders:<br>"
            "&nbsp;&nbsp;<code>2D_slices/</code> - all Z-slices<br>"
            "&nbsp;&nbsp;<code>2D_slices_connected/</code> - only slices with verified left-to-right "
            "pore connectivity (use these for 2D simulations!)</li>"
            "</ul>"
            "<p>All outputs go into the specified output folder with this structure:</p>"
            "<pre style='color:#b0bec5;'>"
            "output_folder/\n"
            "  input/geometry.dat      (main geometry file)\n"
            "  README.txt              (metadata and statistics)\n"
            "  images/slice_*.png      (B/W slices)\n"
            "  images/color_slice_*.png (color slices)\n"
            "  geometry_figure.png/pdf (publication figure)\n"
            "  stacks/2D_slices/       (BMP stacks - all)\n"
            "  stacks/2D_slices_connected/ (BMP stacks - connected)\n"
            "</pre>"

            "<hr><h3 style='color:#81c784;'>File Format</h3>"
            "<p>The <code>.dat</code> file is a text file with one integer per line. "
            "Total lines = nx * ny * nz. Loop order: x &rarr; y &rarr; z. "
            "The C++ solver reads this via the Palabos <code>&gt;&gt;</code> operator.</p>"

            "<hr><h3 style='color:#81c784;'>Tips</h3>"
            "<ul>"
            "<li>For 2D simulations, use <b>2D Slice Stacks</b> with the <code>_connected</code> folder</li>"
            "<li>For Gaussian medium, feature_size=2 gives realistic pore structure</li>"
            "<li>Grain Coating scenario (14) automatically selects Overlapping Spheres medium</li>"
            "<li>All 7 medium types work in both Abiotic and Sessile Biofilm modes</li>"
            "<li>Porosity range: 0.1 (very tight) to 0.95 (very open)</li>"
            "<li>The generated geometry.dat can be loaded directly in the Domain panel</li>"
            "</ul>"
        )
        lay.addWidget(help_text)
        scroll.setWidget(w)
        return scroll

    def _on_abio_medium_changed(self, idx):
        """Show/hide Gaussian parameters in abiotic tab."""
        if idx < len(MEDIUM_TYPES):
            medium_key = MEDIUM_TYPES[idx][1]
            self._abio_gaussian_group.setVisible(medium_key == "gaussian")

    def _on_bio_medium_changed(self, idx):
        """Show/hide Gaussian parameters in sessile tab."""
        if idx < len(MEDIUM_TYPES):
            medium_key = MEDIUM_TYPES[idx][1]
            self._bio_gaussian_group.setVisible(medium_key == "gaussian")

    def _on_img_biofilm_changed(self, idx):
        enabled = idx > 0
        self._img_bio_location.setEnabled(enabled)
        self._img_bio_thickness.setEnabled(enabled)
        self._img_bio_coverage.setEnabled(enabled)
        self._img_material_info.setVisible(enabled)
        # Update material number display
        if idx > 0:
            lines = []
            for i in range(idx):
                lines.append(
                    f"Microbe {i+1}:  core = {MICROBE_CORES[i]},  fringe = {MICROBE_FRINGES[i]}")
            self._img_material_info.setText("\n".join(lines))
        # Zone option only for 2+ species
        if idx < 2:
            if self._img_bio_location.currentIndex() == 5:
                self._img_bio_location.setCurrentIndex(0)

    # ── Helpers ─────────────────────────────────────────────────

    @staticmethod
    def _make_info(text):
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        lbl.setStyleSheet("color: #aaa; padding: 4px;")
        return lbl

    def _on_scenario_changed(self, idx):
        if 0 <= idx < len(SESSILE_SCENARIOS):
            scenario = SESSILE_SCENARIOS[idx]
            n_species = scenario[3]
            self._bio_scenario_desc.setText(
                f"{scenario[2]}\n({n_species} microbe species)")
            # Update material number display
            lines = []
            for i in range(n_species):
                lines.append(
                    f"Microbe {i+1}:  core = {MICROBE_CORES[i]},  fringe = {MICROBE_FRINGES[i]}")
            self._bio_material_info.setText("\n".join(lines))
            # Force spheres medium for grain coating
            if scenario[4] == "grain_coating":
                self._bio_medium.setCurrentIndex(2)

    def _browse_output(self):
        path = QFileDialog.getExistingDirectory(
            self, "Select Output Folder")
        if path:
            self._output_edit.setText(path)

    def _browse_img_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Image Folder")
        if path:
            self._img_folder.setText(path)

    # ── Generate ───────────────────────────────────────────────

    def _generate(self):
        output_dir = self._output_edit.text().strip()
        if not output_dir:
            QMessageBox.warning(self, "Error", "Specify an output folder.")
            return

        tab_idx = self._main_tabs.currentIndex()

        # Common output options
        output_opts = {
            "save_bw_slices": self._opt_bw_slices.isChecked(),
            "save_color_slices": self._opt_color_slices.isChecked(),
            "save_pub_figure": self._opt_pub_figure.isChecked(),
            "save_2d_stacks": self._opt_2d_stacks.isChecked(),
        }

        if tab_idx == 0:  # Abiotic
            medium_func = MEDIUM_TYPES[self._abio_medium.currentIndex()][1]
            params = {
                "generator": "abiotic",
                "medium_func": medium_func,
                "nx": self._abio_nx.value(),
                "ny": self._abio_ny.value(),
                "nz": self._abio_nz.value(),
                "target_porosity": self._abio_porosity.value(),
                "feature_size": self._abio_feature_size.value(),
                "output_dir": output_dir,
                **output_opts,
            }

        elif tab_idx == 1:  # Sessile Biofilm
            scenario_idx = self._bio_scenario.currentIndex()
            medium_func = MEDIUM_TYPES[self._bio_medium.currentIndex()][1]
            params = {
                "generator": "sessile",
                "scenario_idx": scenario_idx,
                "medium_func": medium_func,
                "nx": self._bio_nx.value(),
                "ny": self._bio_ny.value(),
                "nz": self._bio_nz.value(),
                "target_porosity": self._bio_porosity.value(),
                "feature_size": self._bio_feature_size.value(),
                "biofilm_thickness": self._bio_thickness.value(),
                "biofilm_coverage": self._bio_coverage.value(),
                "output_dir": output_dir,
                **output_opts,
            }

        elif tab_idx == 2:  # Image Converter
            folder = self._img_folder.text().strip()
            if not folder or not os.path.isdir(folder):
                QMessageBox.warning(self, "Error", "Select a valid image folder.")
                return
            params = {
                "generator": "image",
                "image_folder": folder,
                "biofilm_species": self._img_biofilm_species.currentIndex(),
                "biofilm_location": self._img_bio_location.currentIndex() + 1,
                "biofilm_thickness": self._img_bio_thickness.value(),
                "biofilm_coverage": self._img_bio_coverage.value(),
                "nx": 0, "ny": 0, "nz": 0,  # determined by images
                "output_dir": output_dir,
                **output_opts,
            }
        else:
            return

        self._gen_btn.setEnabled(False)
        self._progress.setVisible(True)
        self._progress.setValue(0)
        self._status_lbl.setText("Generating...")
        self._status_lbl.setStyleSheet("")
        self._readme_text.clear()

        self._worker = GeometryWorker(params)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_progress(self, pct, msg):
        self._progress.setValue(pct)
        self._status_lbl.setText(msg)

    def _on_finished(self, success, message, output_path, readme):
        self._gen_btn.setEnabled(True)
        self._progress.setValue(100 if success else 0)

        if success:
            self._status_lbl.setText("Generation complete!")
            self._status_lbl.setStyleSheet("color: #5ca060; font-weight: bold;")
            self._readme_text.setPlainText(readme if readme else message)
        else:
            self._status_lbl.setText(f"Failed: {message}")
            self._status_lbl.setStyleSheet("color: #c75050;")
            self._readme_text.setPlainText(f"ERROR:\n{message}")
