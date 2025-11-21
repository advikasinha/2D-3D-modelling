import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap
import os

# --- Configuration ---
MODEL_DB_FILE = "solenoid_model.db" # File to save the geometry and mesh
RESULTS_VTM_FILE = "solenoid_analysis_results.vtm"
EXEC_FILE = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

# Set parameters for geometry design
N_TURNS = 650
I_CURRENT = 1.0
# Dimensions in cm
TA, TB, TC, TD = 0.75, 0.75, 0.50, 0.75
WC, HC = 1, 2
GAP, SPACE = 0.25, 0.25
SMART_SIZE = 4

# Calculated geometry parameters
WS = WC + 2 * SPACE
HS = HC + 0.75
W_TOTAL = TA + WS + TC
HB = TB + HS
H_TOTAL = HB + GAP + TD
ACOIL = WC * HC
JDENS_CM2 = N_TURNS * I_CURRENT / ACOIL
JDENS_M2 = JDENS_CM2 / 0.01**2


def create_and_save_model(mapdl, db_filename):
    """
    Creates the geometry, defines materials, meshes the model, scales it,
    and saves the database file for later analysis.
    """
    print("\n--- STAGE 1: CREATING AND SAVING MODEL ---")
    mapdl.clear()
    mapdl.prep7()
    mapdl.title("2-D Solenoid Actuator Geometry and Mesh")

    # 1. Element and Material Definition
    mapdl.et(1, "PLANE233"); mapdl.keyopt(1, 3, 1); mapdl.keyopt(1, 7, 1)
    mapdl.mp("MURX", 1, 1); mapdl.mp("MURX", 2, 1000)
    mapdl.mp("MURX", 3, 1); mapdl.mp("MURX", 4, 2000)
    print("✅ Materials and Element Type (PLANE233, Axisymmetric) defined.")

    # 2. Create Geometry
    mapdl.rectng(0, W_TOTAL, 0, TB)
    mapdl.rectng(0, W_TOTAL, TB, HB)
    mapdl.rectng(TA, TA + WS, 0, H_TOTAL)
    mapdl.rectng(TA + SPACE, TA + SPACE + WC, TB + SPACE, TB + SPACE + HC)
    mapdl.aovlap("ALL")
    mapdl.rectng(0, W_TOTAL, 0, HB + GAP)
    mapdl.rectng(0, W_TOTAL, 0, H_TOTAL)
    mapdl.aovlap("ALL")
    mapdl.numcmp("AREA")
    print(f"✅ Geometry created. Total Areas: {mapdl.inquire('NUMA')}")

    # 3. Assign Attributes and Mesh
    mapdl.asel("S", "AREA", "", 2); mapdl.aatt(3, 1, 1, 0) # Coil (MAT 3)
    mapdl.asel("S", "AREA", "", 1); mapdl.asel("A", "AREA", "", 12, 13); mapdl.aatt(4, 1, 1) # Armature (MAT 4)
    mapdl.asel("S", "AREA", "", 3, 5); mapdl.asel("A", "AREA", "", 7, 8); mapdl.aatt(2, 1, 1, 0) # Backiron (MAT 2)
    mapdl.allsel("ALL")
    mapdl.smrtsize(SMART_SIZE)
    mapdl.amesh("ALL")
    print(f"✅ Mesh created. Total Elements: {mapdl.mesh.n_elem:,}.")

    # 4. Scale Model to Meters (Must be done before saving if analysis is in SI)
    print("📏 Scaling Model (cm -> m)...")
    
    # --- FIX APPLIED HERE ---
    # Correctly getting the maximum X coordinate before scaling
    mapdl.allsel("ALL") # Ensure all nodes are selected before inquiry
    # Use item1='LOC', it1z='X', item2='MAX' to match *GET, Par, NODE, 0, LOC, X, MAX
    max_x_before_scale = mapdl.get("max_x_bef", "NODE", 0, "LOC", "X", "MAX")
    mapdl.arscale(na1="all", rx=0.01, ry=0.01, rz=1, imove=1)

    # Correctly getting the maximum X coordinate after scaling
    max_x_after_scale = mapdl.get("max_x_aft", "NODE", 0, "LOC", "X", "MAX")
    # ------------------------
    
    print(f"✅ Model scaled from cm to meters (1/100).")
    # 5. Save Model Database
    mapdl.save(db_filename, "db")

    # 5. Save Model Database
    mapdl.save(db_filename, "db")
    print(f"\n💾 Model saved to **{db_filename}**.")
    mapdl.finish()


def load_and_analyze_model(mapdl, db_filename, jdens_m2):
    """
    Loads the saved model, applies loads, solves, and post-processes results.
    Includes diagnostic checks and saves results to VTM.
    """
    print("\n--- STAGE 2: LOADING AND ANALYZING MODEL ---")
    if not os.path.exists(db_filename):
        print(f"❌ ERROR: Model file '{db_filename}' not found. Run create_and_save_model first.")
        return

    mapdl.resume(db_filename)
    print(f"✅ Model loaded from **{db_filename}**.")

    # 1. Apply Loads and Boundary Conditions (in SOLUTION module)
    mapdl.slashsolu()

    # Load Application Check
    mapdl.esel("S", "MAT", "", 3)  # Select coil elements (MAT 3)
    mapdl.bfe("ALL", "JS", 1, "", "", jdens_m2)
    n_coil_elements = mapdl.inquire("NUME")
    print(f"✅ Current Load Applied (J_S): **{jdens_m2:.2e} A/m²** to {n_coil_elements:,} Coil elements.")

    # Boundary Condition Check (AZ=0 on exterior nodes)
    mapdl.allsel("ALL"); mapdl.nsel("EXT")
    mapdl.d("ALL", "AZ", 0)
    n_ext_nodes = mapdl.inquire("NUMN")
    print(f"✅ Boundary Condition: AZ=0 set on **{n_ext_nodes:,}** Exterior Nodes.")

    # 2. Solve the Model
    print("\n🔬 Solving Model...")
    mapdl.allsel("ALL")
    solve_output = mapdl.solve()
    mapdl.finish()

    # Diagnostic Check: Solution Status
    if "SOLUTION IS DONE" in solve_output:
        print("✨ Solution Status: **SUCCESSFUL.**")
    else:
        print("❌ Solution Status: **FAILED.** Check the MAPDL solve log.")
        return

    # 3. Postprocessing and Diagnostics
    print("\n🔬 POSTPROCESSING & RESULTS SUMMARY...")
    mapdl.post1()
    mapdl.file(mapdl.jobname, "rmg")
    mapdl.set("last")

    # Results extraction and statistics
    nodal_bx = mapdl.post_processing.nodal_values("b", "x")
    max_bx = np.max(np.abs(nodal_bx))
    
    print(f"🔬 Nodal B-field X (BX) Statistics:")
    print(f"   - Max Absolute BX (Tesla): **{max_bx:.4f}**")
    if max_bx > 5.0:
        print("   ⚠️ **Warning:** High B-field suggests potential saturation in ferromagnetic parts.")

    # Prepare visualization data (Grid and Scalars by material)
    elem_mats = mapdl.mesh.material_type
    unique_mats = np.unique(elem_mats)
    grids, scalars = [], []
    for mat in unique_mats:
        mapdl.esel("s", "mat", "", mat); mapdl.nsle()
        grids.append(mapdl.mesh.grid)
        scalars.append(mapdl.post_processing.nodal_values("b", "x"))
    mapdl.allsel()
    print(f"✅ Retrieved {len(grids)} mesh blocks for visualization.")

    # 4. Save Results to VTM
    multi_block_data = pv.MultiBlock(grids)
    multi_block_data.save(RESULTS_VTM_FILE)
    print(f"💾 Results (Mesh + Bx Field) saved to **{RESULTS_VTM_FILE}**.")

    # 5. Visualization
    print("\nCreating and displaying visualization (Close the window to proceed)...")
    plotter = pv.Plotter(window_size=[1200, 800])
    for i, grid in enumerate(grids):
        plotter.add_mesh(grid, scalars=scalars[i], show_edges=True, cmap=PyMAPDL_cmap, n_colors=9,
                         scalar_bar_args={"color": "black", "title": "B Flux X (Tesla)", "vertical": False})
    plotter.set_background(color="white"); plotter.camera_position = "xy"
    plotter.add_text("2D Solenoid Analysis: X-Direction Magnetic Flux", position="upper_edge", font_size=14, color="black")
    plotter.show()


# --- Main Execution Block ---
if __name__ == "__main__":
    print(f"Launching MAPDL with executable: {EXEC_FILE}...")
    try:
        mapdl = launch_mapdl(exec_file=EXEC_FILE)
    except Exception as e:
        print(f"❌ ERROR: Could not launch MAPDL. Details: {e}")
        exit()

    # Step A: Create and Save the Model
    create_and_save_model(mapdl, MODEL_DB_FILE)

    # Step B: Load the Model, Analyze, and Save Results
    load_and_analyze_model(mapdl, MODEL_DB_FILE, JDENS_M2)

    # Clean up
    print("\nExiting MAPDL...")
    mapdl.exit()
    print("Analysis complete!")