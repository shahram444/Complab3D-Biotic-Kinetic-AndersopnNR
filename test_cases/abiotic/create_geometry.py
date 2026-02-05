#!/usr/bin/env python3
"""
Create simple open channel geometry for abiotic kinetics tests.

Geometry tags:
  0 = solid (no dynamics)
  1 = bounce-back (solid boundary)
  2 = pore space (fluid)

Creates an open channel with solid walls at y=0, y=ny-1, z=0, z=nz-1
"""

import os

def create_open_channel(nx, ny, nz, output_file):
    """
    Create open channel geometry.

    nx, ny, nz: domain dimensions
    All interior cells are pore (2), boundaries are bounce-back (1)
    """
    pore_count = 0
    boundary_count = 0

    # Write to file (format: slice by slice in x direction)
    with open(output_file, 'w') as f:
        for ix in range(nx):
            for iy in range(ny):
                for iz in range(nz):
                    # Determine cell type
                    if iy == 0 or iy == ny-1 or iz == 0 or iz == nz-1:
                        cell = 1  # Bounce-back boundary
                        boundary_count += 1
                    else:
                        cell = 2  # Pore space
                        pore_count += 1
                    f.write(f"{cell} ")
                f.write("\n")

    print(f"Created geometry: {output_file}")
    print(f"  Dimensions: {nx} x {ny} x {nz}")
    print(f"  Pore cells: {pore_count}")
    print(f"  Boundary cells: {boundary_count}")

if __name__ == "__main__":
    # Create geometries for test cases
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Small domain for quick tests (matches test XMLs)
    create_open_channel(20, 10, 10, os.path.join(script_dir, "geometry_open.dat"))

    # Slightly larger for diffusion test
    create_open_channel(30, 10, 10, os.path.join(script_dir, "geometry_open_30.dat"))

    print("\nGeometry files created successfully!")
    print("Copy to input/ directory before running tests:")
    print("  cp geometry_open.dat ../../input/")
