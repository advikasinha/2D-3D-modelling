"""
CUBE.STEP Analysis Using Gmsh + PyMAPDL
========================================

This approach uses Gmsh to import and mesh the STEP file, then converts
it to ANSYS format. This is MUCH more reliable than ANSYS native import!

Installation:
pip install ansys-mapdl-core
pip install ansys-mapdl-reader
pip install gmsh
pip install pyvista
pip install meshio
pip install numpy
"""

import os
import numpy as np
import pyvista as pv
import gmsh
from ansys.mapdl.reader import save_as_archive
from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap

print("="*60)
print("CUBE.STEP ANALYSIS USING GMSH")
print("="*60)

# Step 1: Use Gmsh to import STEP and create mesh
print("\n" + "-"*60)
print("STEP 1: GMSH - IMPORTING AND MESHING STEP FILE")
print("-"*60)

step_file = "./CUBE.STEP"

if not os.path.exists(step_file):
    print(f"✗ ERROR: {step_file} not found!")
    print(f"   Current directory: {os.getcwd()}")
    print("\nMake sure CUBE.STEP is in the same folder as this script.")
    input("Press Enter to exit...")
    exit()

print(f"✓ Found: {os.path.abspath(step_file)}")

try:
    # Initialize Gmsh
    print("\nInitializing Gmsh...")
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    
    # Create new model
    gmsh.model.add("cube_model")
    
    # Import STEP file
    print(f"Importing {step_file}...")
    volumes = gmsh.model.occ.importShapes(step_file)
    print(f"✓ Imported {len(volumes)} volume(s)")
    
    # Synchronize CAD representation with mesh
    gmsh.model.occ.synchronize()
    
    # Set mesh size
    mesh_size = 5.0  # 5mm elements (cube is 50mm)
    print(f"\nSetting mesh size: {mesh_size} mm")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
    
    # Generate 3D mesh
    print("Generating 3D mesh...")
    gmsh.model.mesh.generate(3)
    
    # Save as MSH file
    msh_file = "cube_from_gmsh.msh"
    print(f"Saving mesh to {msh_file}...")
    gmsh.write(msh_file)
    
    # Get mesh statistics
    num_nodes = len(gmsh.model.mesh.getNodes()[0])
    num_elements = len(gmsh.model.mesh.getElements()[1][0])
    
    print(f"\n✓ Gmsh mesh created successfully!")
    print(f"   Nodes: {num_nodes}")
    print(f"   Elements: {num_elements}")
    
    # Finalize Gmsh
    gmsh.finalize()
    
except Exception as e:
    print(f"\n✗ ERROR in Gmsh: {e}")
    import traceback
    traceback.print_exc()
    gmsh.finalize()
    input("Press Enter to exit...")
    exit()

# Step 2: Convert MSH to ANSYS CDB format
print("\n" + "-"*60)
print("STEP 2: CONVERTING MSH TO ANSYS CDB FORMAT")
print("-"*60)

try:
    print("Reading Gmsh mesh...")
    mesh = pv.read_meshio(msh_file)
    
    print(f"Original mesh: {mesh.n_points} points, {mesh.n_cells} cells")
    
    # CRITICAL: Filter to keep only tetrahedral volume elements
    # Gmsh creates both surface triangles and volume tetrahedrons
    # We only want the tetrahedrons for ANSYS
    
    print("\nFiltering mesh - keeping only tetrahedral volume elements...")
    
    # Extract only tetrahedral cells (cell type 10 in VTK)
    # Cell types: 5=triangle, 10=tetrahedron, 12=hexahedron
    cell_types = mesh.celltypes
    unique_types = np.unique(cell_types)
    
    print(f"Cell types found: {unique_types}")
    print("  Type 5 = Triangle (surface)")
    print("  Type 10 = Tetrahedron (volume)")
    
    # Extract only tetrahedrons
    tet_mask = cell_types == 10
    
    if not np.any(tet_mask):
        print("\n✗ ERROR: No tetrahedral elements found in mesh!")
        print("The mesh only contains surface elements.")
        input("Press Enter to exit...")
        exit()
    
    # Create new mesh with only tetrahedrons
    tet_cells = []
    cell_offset = 0
    
    for i, cell_type in enumerate(cell_types):
        if cell_type == 10:  # Tetrahedron
            tet_cells.append(i)
    
    print(f"\nFound {len(tet_cells)} tetrahedral elements out of {mesh.n_cells} total")
    
    # Extract tetrahedral submesh
    mesh_tets = mesh.extract_cells(tet_cells)
    
    print(f"✓ Filtered mesh: {mesh_tets.n_points} points, {mesh_tets.n_cells} tetrahedral cells")
    
    # Convert from mm to meters (STEP file is in mm)
    print("Converting units: mm → m")
    mesh_tets.points /= 1000.0
    
    # Save as ANSYS archive (CDB) format
    cdb_file = "cube_archive.cdb"
    print(f"Saving as ANSYS archive: {cdb_file}...")
    save_as_archive(cdb_file, mesh_tets)
    
    print(f"✓ CDB file created successfully!")
    
except Exception as e:
    print(f"\n✗ ERROR converting mesh: {e}")
    import traceback
    traceback.print_exc()
    input("Press Enter to exit...")
    exit()

# Step 3: Launch MAPDL and import CDB
print("\n" + "-"*60)
print("STEP 3: LAUNCHING ANSYS MAPDL")
print("-"*60)

exec_file = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

try:
    print("Starting MAPDL...")
    mapdl = launch_mapdl(exec_file=exec_file)
    print("✓ MAPDL launched successfully!")
except Exception as e:
    print(f"✗ Error launching MAPDL: {e}")
    print("\nMake sure ANSYS is installed at the specified path.")
    input("Press Enter to exit...")
    exit()

# Import CDB database
print("\n" + "-"*60)
print("STEP 4: IMPORTING MESH INTO MAPDL")
print("-"*60)

try:
    print(f"Reading CDB file: {cdb_file}...")
    mapdl.cdread("db", cdb_file)
    mapdl.save()
    
    print("✓ Mesh imported into MAPDL")
    
    # Enter preprocessor
    mapdl.prep7()
    
    # Verify mesh
    print("\nVerifying mesh...")
    mapdl.shpp("SUMM")
    
    # Get mesh info
    num_nodes = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
    num_elems = int(mapdl.get('_', 'ELEM', 0, 'COUNT'))
    
    print(f"✓ Mesh verified: {num_nodes} nodes, {num_elems} elements")
    
except Exception as e:
    print(f"\n✗ ERROR importing CDB: {e}")
    import traceback
    traceback.print_exc()
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 5: Setup material properties and analysis
print("\n" + "-"*60)
print("STEP 5: SETTING UP ANALYSIS")
print("-"*60)

try:
    # Set units
    mapdl.units("SI")
    
    # Material properties - Structural Steel
    print("Material: Structural Steel")
    mapdl.mp("EX", 1, 200e9)      # Young's modulus (Pa)
    mapdl.mp("DENS", 1, 7850)     # Density (kg/m³)
    mapdl.mp("NUXY", 1, 0.3)      # Poisson's ratio
    
    # Check what element types exist
    print("\nAnalyzing imported elements...")
    mapdl.allsel()
    
    total_elems = int(mapdl.get('_', 'ELEM', 0, 'COUNT'))
    print(f"Total elements imported: {total_elems}")
    
    if total_elems == 0:
        print("\n✗ ERROR: No elements in CDB file!")
        raise Exception("CDB import failed")
    
    # CRITICAL: Gmsh creates 4-node linear tetrahedrons
    # SOLID187 requires 10-node quadratic tets (will crash!)
    # SOLID285 supports both 4-node and 10-node tets
    
    print("Setting element type: SOLID285 (tetrahedral, linear compatible)...")
    mapdl.et(1, 285)
    
    # Assign element type and material to all elements
    print("Assigning properties to all elements...")
    mapdl.emodif("ALL", "TYPE", 1)
    mapdl.emodif("ALL", "MAT", 1)
    
    print(f"✓ Material properties assigned to {total_elems} elements")
    
except Exception as e:
    print(f"\n✗ ERROR setting up analysis: {e}")
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 6: Apply boundary conditions
print("\n" + "-"*60)
print("STEP 6: APPLYING BOUNDARY CONDITIONS")
print("-"*60)

try:
    # Select nodes on bottom face (Z ≈ 0)
    print("Fixing bottom face (Z = 0)...")
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "ALL", 0)
    
    num_fixed = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
    print(f"✓ Fixed {num_fixed} nodes at Z=0")
    
    # Select nodes on top face (Z ≈ 0.05m = 50mm)
    print("\nApplying load on top face (Z = 0.05m)...")
    mapdl.allsel()
    mapdl.nsel("S", "LOC", "Z", 0.05)
    
    # Apply force in -Z direction
    force_per_node = -100  # -100 N per node (compression)
    mapdl.f("ALL", "FZ", force_per_node)
    
    num_loaded = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
    total_force = num_loaded * force_per_node
    print(f"✓ Applied force to {num_loaded} nodes")
    print(f"   Total force: {total_force:.1f} N")
    
    # Reselect all
    mapdl.allsel()
    
except Exception as e:
    print(f"\n✗ ERROR applying BC: {e}")
    import traceback
    traceback.print_exc()
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 7: Solve
print("\n" + "-"*60)
print("STEP 7: SOLVING")
print("-"*60)

try:
    mapdl.finish()
    mapdl.slashsolu()
    
    # Static analysis
    print("Analysis type: Static Structural")
    mapdl.antype("STATIC")
    
    # Output controls
    mapdl.outres("all", "all")
    
    # Solve
    print("Running solution...")
    mapdl.solve()
    
    print("✓ Solution completed successfully!")
    
    mapdl.finish()
    
except Exception as e:
    print(f"\n✗ Solution failed: {e}")
    import traceback
    traceback.print_exc()
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 8: Post-processing
print("\n" + "-"*60)
print("STEP 8: POST-PROCESSING")
print("-"*60)

try:
    mapdl.post1()
    mapdl.set("LAST")
    
    # Get von Mises stress
    print("Calculating von Mises stress...")
    nodal_stress = mapdl.post_processing.nodal_eqv_stress()
    max_stress = np.max(nodal_stress)
    min_stress = np.min(nodal_stress)
    
    print(f"✓ Stress Results:")
    print(f"   Max von Mises: {max_stress/1e6:.2f} MPa")
    print(f"   Min von Mises: {min_stress/1e6:.2f} MPa")
    
    # Get displacement
    print("\nCalculating displacement...")
    nodal_disp = mapdl.post_processing.nodal_displacement('NORM')
    max_disp = np.max(nodal_disp)
    
    print(f"✓ Displacement Results:")
    print(f"   Max displacement: {max_disp*1000:.4f} mm")
    
except Exception as e:
    print(f"\n✗ Error in post-processing: {e}")
    import traceback
    traceback.print_exc()
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 9: Visualization
print("\n" + "-"*60)
print("STEP 9: VISUALIZATION")
print("-"*60)

try:
    print("Creating 3D visualization...")
    
    # Get mesh grid
    grid = mapdl.mesh.grid
    
    # Create plotter
    plotter = pv.Plotter(window_size=[1400, 900])
    
    # Add deformed mesh with stress
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
        f"CUBE.STEP - Static Analysis (Gmsh Method)\n"
        f"Max Stress: {max_stress/1e6:.2f} MPa\n"
        f"Max Displacement: {max_disp*1000:.4f} mm\n"
        f"Elements: {num_elems}",
        position="upper_edge",
        font_size=14,
        color="black",
    )
    
    print("\n✓ Visualization ready!")
    print("\nShowing results (close window to exit)...")
    
    plotter.show()
    
except Exception as e:
    print(f"\n✗ Visualization error: {e}")
    import traceback
    traceback.print_exc()

# Step 10: Cleanup
print("\n" + "-"*60)
print("STEP 10: CLEANUP")
print("-"*60)

print("Closing MAPDL...")
mapdl.exit()

print("\n" + "="*60)
print("ANALYSIS COMPLETE!")
print("="*60)
print("\nGenerated files:")
print(f"  - {msh_file} (Gmsh mesh)")
print(f"  - {cdb_file} (ANSYS archive)")

input("\nPress Enter to exit...")