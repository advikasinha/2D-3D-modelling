"""
Simple Static Structural Analysis of CUBE.STEP
================================================

This example imports your CUBE.STEP file and performs a basic
static structural analysis with stress visualization.

Installation:
pip install ansys-mapdl-core numpy pyvista matplotlib
"""

import os
import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap

print("="*60)
print("CUBE.STEP STATIC STRUCTURAL ANALYSIS")
print("="*60)

# Launch MAPDL
print("\nLaunching ANSYS MAPDL...")
exec_file = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

try:
    mapdl = launch_mapdl(exec_file=exec_file)
    print("✓ MAPDL launched successfully!")
except Exception as e:
    print(f"✗ Error launching MAPDL: {e}")
    print("\nMake sure ANSYS is installed at the specified path.")
    input("Press Enter to exit...")
    exit()

# Clear and prepare
mapdl.clear()
mapdl.prep7()
mapdl.title("CUBE.STEP - Static Structural Analysis")

# Import STEP file
print("\n" + "-"*60)
print("IMPORTING CUBE.STEP")
print("-"*60)

step_file = "./CUBE.STEP"

if not os.path.exists(step_file):
    print(f"✗ ERROR: {step_file} not found!")
    print(f"   Current directory: {os.getcwd()}")
    print("\nMake sure CUBE.STEP is in the same folder as this script.")
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

print(f"File found: {os.path.abspath(step_file)}")
print("Uploading to ANSYS...")

try:
    # Upload file to MAPDL working directory
    mapdl.upload(step_file)
    print("✓ File uploaded")
    
    # Import STEP file
    print("Importing geometry...")
    mapdl.aux15()
    
    # Set import options
    mapdl.ioptn('IGES', 'NO')
    mapdl.ioptn('MERGE', 'YES')
    mapdl.ioptn('SOLID', 'YES')
    mapdl.ioptn('SMALL', 'YES')
    
    # Import using filename only (no path)
    try:
        mapdl.run("~PARAIN,'CUBE.STEP',STEP")
    except:
        try:
            mapdl.run("PARAIN,'CUBE.STEP',STEP")
        except:
            mapdl.igesin('CUBE', 'STEP')
    
    # Switch to preprocessor
    mapdl.prep7()
    
    # Clean up geometry
    print("Cleaning up geometry...")
    mapdl.nummrg('KP')
    
    try:
        mapdl.vglue('ALL')
        mapdl.aglue('ALL')
        mapdl.lglue('ALL')
    except:
        pass
    
    # Check what was imported
    num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
    num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
    num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
    num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
    
    print("\n" + "-"*60)
    print("GEOMETRY SUMMARY")
    print("-"*60)
    print(f"Keypoints: {num_kps}")
    print(f"Lines:     {num_lines}")
    print(f"Areas:     {num_areas}")
    print(f"Volumes:   {num_vols}")
    
    # Try to rebuild volume if needed
    if num_vols == 0 and num_areas > 0:
        print("\nRebuilding volume from areas...")
        try:
            mapdl.allsel()
            mapdl.run('VA,ALL')
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            print(f"✓ Created {num_vols} volume(s)")
        except:
            print("✗ Could not create volume")
    
    if num_vols == 0:
        print("\n✗ ERROR: No 3D volumes found!")
        print("\nThe STEP file imported but couldn't create solid geometry.")
        print("Try exporting from SolidWorks as:")
        print("  - STEP AP214")
        print("  - IGES format")
        print("  - Parasolid (.x_t)")
        mapdl.exit()
        input("Press Enter to exit...")
        exit()
    
    print(f"\n✓ Successfully imported {num_vols} volume(s)!")
    
    if num_vols > 0:
        print("\nVolume details:")
        mapdl.vlist()

except Exception as e:
    print(f"\n✗ ERROR importing geometry: {e}")
    import traceback
    traceback.print_exc()
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Define element type
print("\n" + "-"*60)
print("SETTING UP ANALYSIS")
print("-"*60)

print("Element type: SOLID186 (3D 20-node structural solid)")
mapdl.et(1, 'SOLID186')

# Material properties - Structural Steel
print("Material: Structural Steel")
mapdl.mp('EX', 1, 2e11)      # Young's modulus (Pa)
mapdl.mp('NUXY', 1, 0.3)     # Poisson's ratio
mapdl.mp('DENS', 1, 7850)    # Density (kg/m³)

print("✓ Material properties set")

# Mesh the model
print("\nMeshing...")
mesh_size = 0.01  # 10mm elements (cube is 50mm based on STEP file)
mapdl.esize(mesh_size)
mapdl.vmesh('ALL')

num_nodes = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
num_elems = int(mapdl.get('_', 'ELEM', 0, 'COUNT'))

print(f"✓ Mesh created: {num_nodes} nodes, {num_elems} elements")

if num_nodes == 0 or num_elems == 0:
    print("\n✗ ERROR: Meshing failed!")
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Apply boundary conditions
print("\n" + "-"*60)
print("BOUNDARY CONDITIONS")
print("-"*60)

# Get available areas
print("\nAvailable areas:")
mapdl.alist()

print("\nApplying constraints...")
# Fix bottom face (area 1 - typically the Z=0 plane)
try:
    mapdl.da(1, 'ALL', 0)
    print("✓ Fixed area 1 (all DOF)")
except:
    print("✗ Could not fix area 1, trying area 2...")
    try:
        mapdl.da(2, 'ALL', 0)
        print("✓ Fixed area 2 (all DOF)")
    except:
        print("✗ Warning: Could not apply constraints automatically")

print("\nApplying loads...")
# Apply pressure on top face (area 6 - typically the Z=max plane)
pressure = -1e6  # -1 MPa (compression)
try:
    mapdl.sfa(6, 1, 'PRES', pressure)
    print(f"✓ Applied {pressure/1e6:.1f} MPa pressure on area 6")
except:
    print("✗ Could not apply load to area 6, trying area 5...")
    try:
        mapdl.sfa(5, 1, 'PRES', pressure)
        print(f"✓ Applied {pressure/1e6:.1f} MPa pressure on area 5")
    except:
        print("✗ Warning: Could not apply load automatically")

# Solve
print("\n" + "-"*60)
print("SOLVING")
print("-"*60)

mapdl.finish()
mapdl.slashsolu()
mapdl.antype('STATIC')

print("Running solution...")
try:
    mapdl.solve()
    print("✓ Solution completed successfully!")
except Exception as e:
    print(f"✗ Solution failed: {e}")
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

mapdl.finish()

# Post-processing
print("\n" + "-"*60)
print("POST-PROCESSING")
print("-"*60)

mapdl.post1()
mapdl.set('LAST')

# Get results
try:
    # Get von Mises stress
    nodal_stress = mapdl.post_processing.nodal_eqv_stress()
    max_stress = np.max(nodal_stress)
    
    print(f"\nMaximum von Mises Stress: {max_stress/1e6:.2f} MPa")
    
    # Get displacement
    nodal_disp = mapdl.post_processing.nodal_displacement('NORM')
    max_disp = np.max(nodal_disp)
    
    print(f"Maximum Displacement: {max_disp*1000:.4f} mm")
    
except Exception as e:
    print(f"✗ Error getting results: {e}")
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Visualization
print("\n" + "-"*60)
print("VISUALIZATION")
print("-"*60)

try:
    print("Preparing 3D visualization...")
    
    # Get mesh grid
    grid = mapdl.mesh.grid
    
    # Create plotter
    plotter = pv.Plotter(window_size=[1400, 900])
    
    # Add mesh with stress scalars
    plotter.add_mesh(
        grid,
        scalars=nodal_stress,
        show_edges=True,
        cmap=PyMAPDL_cmap,
        n_colors=9,
        scalar_bar_args={
            "color": "black",
            "title": "von Mises Stress (Pa)",
            "vertical": True,
            "n_labels": 10,
            "title_font_size": 16,
            "label_font_size": 12,
        },
    )
    
    plotter.set_background(color="white")
    plotter.add_text(
        f"CUBE.STEP - Static Structural Analysis\n"
        f"Max Stress: {max_stress/1e6:.2f} MPa\n"
        f"Max Displacement: {max_disp*1000:.4f} mm",
        position="upper_edge",
        font_size=14,
        color="black",
    )
    
    print("\n✓ Visualization ready!")
    print("\nShowing results...")
    print("Close the window to exit.")
    
    plotter.show()
    
except Exception as e:
    print(f"✗ Visualization error: {e}")
    import traceback
    traceback.print_exc()

# Clean up
print("\n" + "-"*60)
print("CLEANUP")
print("-"*60)

print("Closing ANSYS MAPDL...")
mapdl.exit()

print("\n" + "="*60)
print("ANALYSIS COMPLETE!")
print("="*60)

input("\nPress Enter to exit...")