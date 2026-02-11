#!/usr/bin/env python3
"""
Build script for CompLaB Studio
Creates standalone Windows executable using PyInstaller
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"Cleaning {d}...")
            shutil.rmtree(d)
    
    # Clean .spec file
    for f in Path('.').glob('*.spec'):
        f.unlink()


def build_executable():
    """Build the executable using PyInstaller"""
    
    # PyInstaller options
    options = [
        'main.py',
        '--name=CompLaB_Studio',
        '--windowed',  # No console window
        '--onedir',    # Create a directory with all files
        '--icon=icons/complab_icon.ico',
        
        # Include additional data files
        '--add-data=styles;styles',
        '--add-data=icons;icons',
        '--add-data=resources;resources',
        
        # Hidden imports that PyInstaller might miss
        '--hidden-import=PySide6.QtSvg',
        '--hidden-import=PySide6.QtXml',
        
        # Exclude unnecessary modules to reduce size
        '--exclude-module=tkinter',
        '--exclude-module=matplotlib.tests',
        '--exclude-module=numpy.random._examples',
        
        # Optimization
        '--noupx',  # Don't use UPX compression
    ]
    
    # Check if VTK is installed
    try:
        import vtk
        options.append('--hidden-import=vtkmodules')
        options.append('--hidden-import=vtkmodules.all')
    except ImportError:
        print("Warning: VTK not installed. 3D viewer will be limited.")
    
    print("Building executable...")
    print(f"Command: pyinstaller {' '.join(options)}")
    
    result = subprocess.run(['pyinstaller'] + options)
    
    if result.returncode == 0:
        print("\n✅ Build successful!")
        print("Executable located at: dist/CompLaB_Studio/")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)


def create_installer():
    """Create Windows installer using NSIS (if available)"""
    # This would use NSIS or Inno Setup to create an installer
    # For now, just zip the dist folder
    
    import zipfile
    
    dist_dir = Path('dist/CompLaB_Studio')
    if not dist_dir.exists():
        print("Error: dist folder not found. Run build first.")
        return
    
    zip_name = 'CompLaB_Studio_Windows.zip'
    print(f"Creating {zip_name}...")
    
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in dist_dir.rglob('*'):
            arcname = file.relative_to(dist_dir.parent)
            zipf.write(file, arcname)
    
    print(f"✅ Created {zip_name}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Build CompLaB Studio')
    parser.add_argument('--clean', action='store_true', help='Clean build artifacts')
    parser.add_argument('--build', action='store_true', help='Build executable')
    parser.add_argument('--installer', action='store_true', help='Create installer/zip')
    parser.add_argument('--all', action='store_true', help='Clean, build, and create installer')
    
    args = parser.parse_args()
    
    if args.all or (not any([args.clean, args.build, args.installer])):
        args.clean = args.build = args.installer = True
    
    if args.clean:
        clean_build()
    
    if args.build:
        build_executable()
    
    if args.installer:
        create_installer()


if __name__ == '__main__':
    main()
