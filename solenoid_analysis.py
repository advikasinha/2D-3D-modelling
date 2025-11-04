"""
1. Exampel analysis of a pre-made model using pymapdl itself. 


2D Magnetostatic Solenoid Analysis using ANSYS MAPDL
=====================================================

Installation Instructions:
--------------------------
Run these commands in your terminal before executing this script:

pip install ansys-mapdl-core
pip install numpy
pip install pyvista
pip install matplotlib

Note: You need ANSYS MAPDL installed on your system.
"""

import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting import GraphicsBackend
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap

# Launch MAPDL service
print("Launching MAPDL...")

# Specify ANSYS Student v252 path
exec_file = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"
mapdl = launch_mapdl(exec_file=exec_file)

mapdl.clear()
mapdl.prep7()
mapdl.title("2-D Solenoid Actuator Static Analysis")

# Set up the FE model
print("\nSetting up FE model...")
mapdl.et(1, "PLANE233")  # Define PLANE233 as element type
mapdl.keyopt(1, 3, 1)  # Use axisymmetric analysis option
mapdl.keyopt(1, 7, 1)  # Condense forces at the corner nodes

# Set material properties (SI units)
mapdl.mp("MURX", 1, 1)  # Air permeability
mapdl.mp("MURX", 2, 1000)  # Backiron permeability
mapdl.mp("MURX", 3, 1)  # Coil permeability
mapdl.mp("MURX", 4, 2000)  # Armature permeability

# Set parameters for geometry design
n_turns = 650  # Number of coil turns
i_current = 1.0  # Current per turn
ta = 0.75  # Model dimensions (centimeters)
tb = 0.75
tc = 0.50
td = 0.75
wc = 1
hc = 2
gap = 0.25
space = 0.25
ws = wc + 2 * space
hs = hc + 0.75
w = ta + ws + tc
hb = tb + hs
h = hb + gap + td
acoil = wc * hc  # Cross-section area of coil (cm**2)
jdens = n_turns * i_current / acoil  # Current density (A/cm**2)

smart_size = 4  # Smart Size Level for Meshing

# Create geometry
print("Creating geometry...")
mapdl.rectng(0, w, 0, tb)
mapdl.rectng(0, w, tb, hb)
mapdl.rectng(ta, ta + ws, 0, h)
mapdl.rectng(ta + space, ta + space + wc, tb + space, tb + space + hc)
mapdl.aovlap("ALL")
mapdl.rectng(0, w, 0, hb + gap)
mapdl.rectng(0, w, 0, h)
mapdl.aovlap("ALL")
mapdl.numcmp("AREA")

# Mesh the model
print("Meshing the model...")
mapdl.asel("S", "AREA", "", 2)  # Assign attributes to coil
mapdl.aatt(3, 1, 1, 0)

mapdl.asel("S", "AREA", "", 1)  # Assign attributes to armature
mapdl.asel("A", "AREA", "", 12, 13)
mapdl.aatt(4, 1, 1)

mapdl.asel("S", "AREA", "", 3, 5)  # Assign attributes to backiron
mapdl.asel("A", "AREA", "", 7, 8)
mapdl.aatt(2, 1, 1, 0)

mapdl.pnum("MAT", 1)
mapdl.allsel("ALL")

mapdl.smrtsize(smart_size)
mapdl.amesh("ALL")

# Scale mesh to meters
print("Scaling model to meters...")
mapdl.esel("S", "MAT", "", 4)
mapdl.cm("ARM", "ELEM")
mapdl.allsel("ALL")
mapdl.arscale(na1="all", rx=0.01, ry=0.01, rz=1, imove=1)
mapdl.finish()

# Apply loads and boundary conditions
print("Applying loads and boundary conditions...")
mapdl.slashsolu()

mapdl.esel("S", "MAT", "", 3)  # Select coil elements
mapdl.bfe("ALL", "JS", 1, "", "", jdens / 0.01**2)  # Apply current density

mapdl.esel("ALL")
mapdl.nsel("EXT")  # Select exterior nodes
mapdl.d("ALL", "AZ", 0)  # Set potentials to zero

# Solve the model
print("Solving the model...")
mapdl.allsel("ALL")
mapdl.solve()
mapdl.finish()

# Postprocessing
print("\nPostprocessing results...")
mapdl.post1()
mapdl.file("file", "rmg")
mapdl.set("last")

# Print nodal values
print("\nSample nodal B-field X values:")
nodal_bx = mapdl.post_processing.nodal_values("b", "x")
print(nodal_bx[:10])  # Print first 10 values

# Obtain grid and scalar data for plotting
print("\nPreparing visualization data...")
elem_mats = mapdl.mesh.material_type
unique_mats = np.unique(elem_mats)

grids = []
scalars = []
for mat in unique_mats:
    mapdl.esel("s", "mat", "", mat)
    mapdl.nsle()
    grids.append(mapdl.mesh.grid)
    scalars.append(mapdl.post_processing.nodal_values("b", "x"))
mapdl.allsel()

# Create visualization
print("\nCreating visualization...")
plotter = pv.Plotter(window_size=[1200, 800])

for i, grid in enumerate(grids):
    plotter.add_mesh(
        grid,
        scalars=scalars[i],
        show_edges=True,
        cmap=PyMAPDL_cmap,
        n_colors=9,
        scalar_bar_args={
            "color": "black",
            "title": "B Flux X (Tesla)",
            "vertical": False,
            "n_labels": 10,
            "title_font_size": 16,
            "label_font_size": 12,
        },
    )

plotter.set_background(color="white")
plotter.camera_position = "xy"
plotter.add_text(
    "2D Magnetostatic Solenoid Analysis\nX-Direction Magnetic Flux",
    position="upper_edge",
    font_size=14,
    color="black",
)

print("\nDisplaying results...")
print("Close the visualization window to exit.")
plotter.show()

# Exit MAPDL
print("\nExiting MAPDL...")
mapdl.exit()
print("Analysis complete!")