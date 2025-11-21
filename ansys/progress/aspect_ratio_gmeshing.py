"""
CUBE.STEP Analysis - Direct Gmsh to MAPDL
==========================================

This approach uses Gmsh to create mesh, then directly creates
nodes and elements in MAPDL instead of using CDB files.

Installation:
pip install ansys-mapdl-core gmsh pyvista numpy
"""

import os
import numpy as np
import pyvista as pv
import gmsh
from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap

print("="*60)
print("CUBE.STEP ANALYSIS - DIRECT GMSH→MAPDL")
print("="*60)

# Step 1: Use Gmsh to import STEP and create mesh
print("\n" + "-"*60)
print("STEP 1: GMSH - IMPORTING AND MESHING")
print("-"*60)

step_file = "./CUBE.STEP"

if not os.path.exists(step_file):
    print(f"✗ ERROR: {step_file} not found!")
    input("Press Enter to exit...")
    exit()

print(f"✓ Found: {os.path.abspath(step_file)}")

try:
    # Initialize Gmsh
    print("\nInitializing Gmsh...")
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 1)
    
    # Create model
    gmsh.model.add("cube_model")
    
    # Import STEP file
    print(f"Importing {step_file}...")
    volumes = gmsh.model.occ.importShapes(step_file)
    print(f"✓ Imported {len(volumes)} volume(s)")
    
    # Synchronize
    gmsh.model.occ.synchronize()
    
    # Set mesh size - smaller for better quality
    mesh_size = 8.0  # 8mm elements
    print(f"\nSetting mesh size: {mesh_size} mm")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
    
    # Generate 3D mesh
    print("Generating 3D mesh...")
    gmsh.model.mesh.generate(3)
    
    # Get nodes
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    node_coords = node_coords.reshape(-1, 3)
    
    # Convert from mm to meters
    node_coords = node_coords / 1000.0
    
    print(f"✓ Mesh created: {len(node_tags)} nodes")
    
    # Get tetrahedral elements (element type 4 in Gmsh)
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)  # 3 = volume
    
    # Find tetrahedrons (type 4)
    tet_index = None
    for i, et in enumerate(elem_types):
        if et == 4:  # Linear tetrahedron
            tet_index = i
            break
    
    if tet_index is None:
        print("\n✗ ERROR: No tetrahedral elements found!")
        gmsh.finalize()
        input("Press Enter to exit...")
        exit()
    
    # Get tetrahedral connectivity
    tet_nodes = elem_node_tags[tet_index].reshape(-1, 4)
    
    print(f"✓ Found {len(tet_nodes)} tetrahedral elements")
    
    # Finalize Gmsh
    gmsh.finalize()
    
except Exception as e:
    print(f"\n✗ ERROR in Gmsh: {e}")
    import traceback
    traceback.print_exc()
    gmsh.finalize()
    input("Press Enter to exit...")
    exit()

# Step 2: Launch MAPDL
print("\n" + "-"*60)
print("STEP 2: LAUNCHING ANSYS MAPDL")
print("-"*60)

exec_file = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

try:
    print("Starting MAPDL...")
    mapdl = launch_mapdl(exec_file=exec_file)
    print("✓ MAPDL launched successfully!")
except Exception as e:
    print(f"✗ Error launching MAPDL: {e}")
    input("Press Enter to exit...")
    exit()

# Step 3: Create geometry in MAPDL
print("\n" + "-"*60)
print("STEP 3: CREATING MESH IN MAPDL")
print("-"*60)

try:
    mapdl.clear()
    mapdl.prep7()
    mapdl.title("CUBE.STEP - Direct Gmsh Import")
    
    # Set units
    mapdl.units("SI")
    
    # Define element type
    print("Defining element type: SOLID285...")
    mapdl.et(1, 285)  # SOLID285 - 4-node tetrahedral
    
    # Material properties
    print("Setting material properties (Structural Steel)...")
    mapdl.mp("EX", 1, 200e9)    # Young's modulus (Pa)
    mapdl.mp("DENS", 1, 7850)   # Density (kg/m³)
    mapdl.mp("NUXY", 1, 0.3)    # Poisson's ratio
    
    # Create nodes
    print(f"\nCreating {len(node_tags)} nodes...")
    
    # Create nodes in batches for speed
    for i, (node_id, coords) in enumerate(zip(node_tags, node_coords)):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
        
        if (i + 1) % 200 == 0:
            print(f"  Created {i+1}/{len(node_tags)} nodes...", end='\r')
    
    print(f"✓ Created {len(node_tags)} nodes           ")
    
    # Create elements
    print(f"\nCreating {len(tet_nodes)} tetrahedral elements...")
    
    for i, tet in enumerate(tet_nodes):
        # ANSYS E command: E, I, J, K, L
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))
        
        if (i + 1) % 500 == 0:
            print(f"  Created {i+1}/{len(tet_nodes)} elements...", end='\r')
    
    print(f"✓ Created {len(tet_nodes)} elements           ")
    
    # Verify mesh
    num_nodes = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
    num_elems = int(mapdl.get('_', 'ELEM', 0, 'COUNT'))
    
    print(f"\n✓ Mesh verified: {num_nodes} nodes, {num_elems} elements")
    
except Exception as e:
    print(f"\n✗ ERROR creating mesh: {e}")
    import traceback
    traceback.print_exc()
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 4: Apply boundary conditions
print("\n" + "-"*60)
print("STEP 4: BOUNDARY CONDITIONS")
print("-"*60)

try:
    # Fix bottom face (Z ≈ 0)
    print("Fixing bottom face (Z = 0)...")
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "ALL", 0)
    
    num_fixed = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
    print(f"✓ Fixed {num_fixed} nodes at Z=0")
    
    # Apply load on top face (Z ≈ 0.05m)
    print("\nApplying load on top face (Z = 0.05m)...")
    mapdl.allsel()
    mapdl.nsel("S", "LOC", "Z", 0.05)
    
    force_per_node = -100  # -100 N per node
    mapdl.f("ALL", "FZ", force_per_node)
    
    num_loaded = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
    total_force = num_loaded * force_per_node
    print(f"✓ Applied force to {num_loaded} nodes")
    print(f"   Total force: {total_force:.1f} N")
    
    mapdl.allsel()
    
except Exception as e:
    print(f"\n✗ ERROR applying BC: {e}")
    mapdl.exit()
    input("Press Enter to exit...")
    exit()

# Step 5: Solve
print("\n" + "-"*60)
print("STEP 5: SOLVING")
print("-"*60)

try:
    mapdl.finish()
    mapdl.slashsolu()
    
    print("Analysis type: Static Structural")
    mapdl.antype("STATIC")
    mapdl.outres("all", "all")
    
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

# Step 6: Post-processing
print("\n" + "-"*60)
print("STEP 6: POST-PROCESSING")
print("-"*60)

try:
    mapdl.post1()
    mapdl.set("LAST")
    
    # Get results
    print("Calculating von Mises stress...")
    nodal_stress = mapdl.post_processing.nodal_eqv_stress()
    max_stress = np.max(nodal_stress)
    min_stress = np.min(nodal_stress)
    
    print(f"✓ Stress Results:")
    print(f"   Max von Mises: {max_stress/1e6:.2f} MPa")
    print(f"   Min von Mises: {min_stress/1e6:.2f} MPa")
    
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

# Step 7: Visualization
print("\n" + "-"*60)
print("STEP 7: VISUALIZATION")
print("-"*60)

try:
    print("Creating 3D visualization...")
    
    # Get mesh grid
    grid = mapdl.mesh.grid
    
    # Create plotter
    plotter = pv.Plotter(window_size=[1400, 900])
    
    # Add mesh with stress
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
        f"CUBE.STEP - Static Analysis\n"
        f"Max Stress: {max_stress/1e6:.2f} MPa\n"
        f"Max Displacement: {max_disp*1000:.4f} mm\n"
        f"Elements: {num_elems}",
        position="upper_edge",
        font_size=14,
        color="black",
    )
    
    print("\n✓ Visualization ready!")
    print("Showing results (close window to exit)...")
    
    plotter.show()
    
except Exception as e:
    print(f"\n✗ Visualization error: {e}")
    import traceback
    traceback.print_exc()

# Cleanup
print("\n" + "-"*60)
print("CLEANUP")
print("-"*60)

print("Closing MAPDL...")
mapdl.exit()

print("\n" + "="*60)
print("ANALYSIS COMPLETE!")
print("="*60)

input("\nPress Enter to exit...")