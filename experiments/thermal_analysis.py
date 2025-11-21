# """
# 3D Steady-State Thermal Analysis of Finned Heat Sink using ANSYS MAPDL
# ========================================================================

# Problem Description:
# -------------------
# Analysis of an aluminum heat sink with 5 rectangular fins cooling a power
# electronic component (e.g., MOSFET, IGBT). The component dissipates 50W of heat.
# The heat sink is cooled by natural convection in air.

# Geometry:
# - Base plate: 50mm x 50mm x 5mm (aluminum)
# - Fins: 5 fins, each 50mm x 40mm x 2mm, spaced 10mm apart
# - Heat source: 20mm x 20mm area on bottom of base plate (50W power dissipation)

# Boundary Conditions:
# - Heat flux applied at bottom center (component location)
# - Convection on all exposed surfaces (h = 10 W/m²·K for natural convection)
# - Ambient temperature: 25°C

# Installation Instructions:
# --------------------------
# pip install ansys-mapdl-core
# pip install numpy
# pip install pyvista
# pip install matplotlib

# Note: You need ANSYS MAPDL installed on your system.
# """

# import numpy as np
# import pyvista as pv
# from ansys.mapdl.core import launch_mapdl
# from ansys.mapdl.core.plotting import GraphicsBackend
# from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap

# # Launch MAPDL service
# print("="*70)
# print("3D STEADY-STATE THERMAL ANALYSIS OF FINNED HEAT SINK")
# print("="*70)
# print("\nLaunching MAPDL...")

# # Specify ANSYS Student v252 path
# exec_file = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"
# mapdl = launch_mapdl(exec_file=exec_file)

# mapdl.clear()
# mapdl.prep7()
# mapdl.title("3D Heat Sink Thermal Analysis - Natural Convection")

# # ============================================================================
# # DEFINE PARAMETERS (SI units: meters, Watts, Kelvin)
# # ============================================================================
# print("\nDefining analysis parameters...")

# # Geometry parameters (convert mm to m)
# base_length = 0.050      # Base length (m)
# base_width = 0.050       # Base width (m)
# base_thick = 0.005       # Base thickness (m)

# fin_height = 0.040       # Fin height above base (m)
# fin_thick = 0.002        # Fin thickness (m)
# fin_spacing = 0.010      # Spacing between fins (m)
# num_fins = 5             # Number of fins

# # Heat source parameters
# heat_source_size = 0.020 # Heat source size (20mm x 20mm)
# total_power = 50.0       # Total power dissipation (W)

# # Thermal parameters
# ambient_temp = 25.0      # Ambient temperature (°C)
# conv_coeff = 10.0        # Convection coefficient for natural convection (W/m²·K)

# # Material properties - Aluminum 6061
# thermal_cond = 167.0     # Thermal conductivity (W/m·K)
# density = 2700.0         # Density (kg/m³)
# specific_heat = 896.0    # Specific heat (J/kg·K)

# # Mesh control
# element_size = 0.003     # Element size (3mm)

# print(f"\n  Heat Sink Dimensions: {base_length*1000}mm x {base_width*1000}mm")
# print(f"  Number of Fins: {num_fins}")
# print(f"  Power Dissipation: {total_power}W")
# print(f"  Convection Coefficient: {conv_coeff} W/m²·K")
# print(f"  Ambient Temperature: {ambient_temp}°C")

# # ============================================================================
# # DEFINE ELEMENT TYPE AND MATERIAL PROPERTIES
# # ============================================================================
# print("\nSetting up element type and material properties...")

# # Define 3D thermal solid element with midside nodes for better accuracy
# mapdl.et(1, "SOLID87")   # 3D 20-node thermal solid element (tetrahedral)

# # Define material properties for Aluminum
# mapdl.mp("KXX", 1, thermal_cond)   # Thermal conductivity
# mapdl.mp("DENS", 1, density)        # Density
# mapdl.mp("C", 1, specific_heat)     # Specific heat

# # ============================================================================
# # CREATE GEOMETRY
# # ============================================================================
# print("\nCreating heat sink geometry...")

# # Create base plate
# mapdl.block(0, base_length, 0, base_width, 0, base_thick)

# # Create fins - build them separately then add
# fin_start_x = (base_length - (num_fins * fin_thick + (num_fins - 1) * fin_spacing)) / 2

# for i in range(num_fins):
#     x_pos = fin_start_x + i * (fin_thick + fin_spacing)
#     mapdl.block(x_pos, x_pos + fin_thick, 0, base_width, 
#                 base_thick, base_thick + fin_height)

# # Boolean add all volumes to create single part
# mapdl.vglue("ALL")
# mapdl.numcmp("VOLU")  # Compress volume numbering
# mapdl.vsel("ALL")
# mapdl.vatt(1, 1, 1)  # Assign material 1, element type 1
# mapdl.allsel()

# # ============================================================================
# # MESH THE MODEL
# # ============================================================================
# print("Meshing the model...")

# mapdl.allsel()
# mapdl.mshape(1, "3D")      # Tetrahedral shape
# mapdl.mshkey(0)            # Free meshing
# mapdl.smrtsize(6)          # Smart size for automatic meshing

# # Mesh all volumes
# mapdl.esize(element_size)
# mapdl.vmesh("ALL")

# num_nodes = mapdl.mesh.n_node
# num_elements = mapdl.mesh.n_elem
# print(f"  Nodes created: {num_nodes}")
# print(f"  Elements created: {num_elements}")

# mapdl.finish()
# # ============================================================================
# # APPLY LOADS AND BOUNDARY CONDITIONS (FINAL, VERIFIED STRUCTURE)
# # ============================================================================
# print("\nApplying boundary conditions...")

# mapdl.slashsolu()

# # 1. APPLY HEAT FLUX (Nodal/Element Load)
# x_center = base_length / 2
# y_center = base_width / 2
# heat_source_half = heat_source_size / 2

# mapdl.nsel("S", "LOC", "Z", 0)  # Bottom surface
# mapdl.nsel("R", "LOC", "X", x_center - heat_source_half, x_center + heat_source_half)
# mapdl.nsel("R", "LOC", "Y", y_center - heat_source_half, y_center + heat_source_half)

# # Calculate heat flux (W/m²)
# heat_source_area = heat_source_size * heat_source_size
# heat_flux = total_power / heat_source_area
# print(f"  Applied heat flux: {heat_flux:.2f} W/m²")
# print(f"  Heat source area: {heat_source_area*1e6:.1f} mm²")


# # 2. APPLY CONVECTION (Area Load)
# # print(" Applying convection to all exterior areas...")

# # # Make sure we’re in the solution environment
# # mapdl.allsel()
# # mapdl.asel("S", "EXT")       # Select all exterior areas
# # mapdl.nsel("ALL")            # Ensure no node selection interferes
# # mapdl.esel("ALL")            # Ensure no element selection interferes

# # # Double-check: list the number of selected areas
# # n_areas = mapdl.get("NAREAS", "AREA", 0, "COUNT")
# # print(f"  Found {n_areas} exterior areas for convection.")

# # if n_areas > 0:
# #     # Apply convection load on all selected exterior areas
# #     mapdl.run(f"SFALL, ALL, CONV, {conv_coeff}, {ambient_temp}")
# #     print(" Convection applied successfully to all exterior surfaces.")
# # else:
# #     print("⚠ No exterior areas found for SFALL — check geometry before applying convection.")
# # ==============================================================
# # APPLY CONVECTION TO ALL EXTERIOR SURFACES -- PART 2 THAT WORKS WOWOWOWOWOWOWO GRPC ERROR 
# # ==============================================================
# print("Applying convection to all exterior surfaces...")

# # Step 1: Select all elements (no need to try selecting by area)
# mapdl.allsel()
# mapdl.asel("S", "EXT")  # all exterior areas

# # Step 2: Apply convection to all exterior element faces
# # h = conv_coeff, T∞ = ambient_temp
# cmd = f"SFE, ALL, 1, CONV, {conv_coeff}, , {ambient_temp}"
# print(f"  Running command: {cmd}")
# mapdl.run(cmd)

# # Optional verification: list first few convection surfaces
# print("  Listing first few convection surfaces:")
# sfelist_output = mapdl.run("SFELIST, 1")
# print(sfelist_output)

# print("Convection applied successfully to exterior element faces.")

# # ==============================================================
# # SOLVE THE MODEL
# # ==============================================================
# print("\nSolving the thermal model...")
# print("  (This may take a moment...)")

# mapdl.allsel()  # ensure all elements/nodes are selected
# mapdl.solve()
# mapdl.finish()

# print("Solution completed successfully!")


# # ============================================================================
# # POST-PROCESSING
# # ============================================================================
# print("\n" + "="*70)
# print("POST-PROCESSING RESULTS")
# print("="*70)

# mapdl.post1()
# mapdl.set("LAST")

# # Get temperature results
# temperatures = mapdl.post_processing.nodal_temperature()

# # Calculate key thermal metrics
# max_temp = np.max(temperatures)
# min_temp = np.min(temperatures)
# avg_temp = np.mean(temperatures)

# print(f"\nTemperature Distribution:")
# print(f"  Maximum Temperature: {max_temp:.2f}°C")
# print(f"  Minimum Temperature: {min_temp:.2f}°C")
# print(f"  Average Temperature: {avg_temp:.2f}°C")
# print(f"  Temperature Rise (ΔT): {max_temp - ambient_temp:.2f}°C")

# # Calculate thermal resistance
# thermal_resistance = (max_temp - ambient_temp) / total_power
# print(f"\nThermal Performance:")
# print(f"  Thermal Resistance: {thermal_resistance:.4f} K/W")
# print(f"  Thermal Resistance: {thermal_resistance*1000:.2f} K/kW")

# # Get heat flux on heat source area
# mapdl.nsel("S", "LOC", "Z", 0)
# mapdl.nsel("R", "LOC", "X", x_center - heat_source_half, x_center + heat_source_half)
# mapdl.nsel("R", "LOC", "Y", y_center - heat_source_half, y_center + heat_source_half)
# source_temps = mapdl.post_processing.nodal_temperature()
# max_source_temp = np.max(source_temps)
# print(f"  Maximum Component Temperature: {max_source_temp:.2f}°C")

# # ============================================================================
# # VISUALIZATION
# # ============================================================================
# print("\nPreparing visualization...")

# mapdl.allsel()
# grid = mapdl.mesh.grid
# temps_kelvin = mapdl.post_processing.nodal_temperature()

# # Create multiple views
# print("\nCreating visualization windows...")

# # Main temperature distribution view
# plotter = pv.Plotter(shape=(1, 2), window_size=[1600, 700])

# # Left plot - Full temperature distribution
# plotter.subplot(0, 0)
# plotter.add_mesh(
#     grid,
#     scalars=temps_kelvin,
#     show_edges=False,
#     cmap="jet",
#     n_colors=256,
#     scalar_bar_args={
#         "color": "black",
#         "title": "Temperature (°C)",
#         "vertical": True,
#         "n_labels": 8,
#         "title_font_size": 14,
#         "label_font_size": 11,
#         "position_x": 0.05,
#         "position_y": 0.3,
#     },
# )
# plotter.add_text(
#     f"Heat Sink Temperature Distribution\nMax: {max_temp:.1f}°C | Thermal Resistance: {thermal_resistance:.4f} K/W",
#     position="upper_edge",
#     font_size=12,
#     color="black",
# )
# plotter.set_background("white")
# plotter.camera_position = "iso"
# plotter.add_axes()

# # Right plot - Top view showing fin temperatures
# plotter.subplot(0, 1)
# plotter.add_mesh(
#     grid,
#     scalars=temps_kelvin,
#     show_edges=True,
#     cmap="jet",
#     n_colors=256,
#     scalar_bar_args={
#         "color": "black",
#         "title": "Temperature (°C)",
#         "vertical": True,
#         "n_labels": 8,
#         "title_font_size": 14,
#         "label_font_size": 11,
#         "position_x": 0.05,
#         "position_y": 0.3,
#     },
# )
# plotter.add_text(
#     f"Top View - Fin Temperature Variation\nAmbient: {ambient_temp}°C | Power: {total_power}W",
#     position="upper_edge",
#     font_size=12,
#     color="black",
# )
# plotter.set_background("white")
# plotter.camera_position = "xy"
# plotter.camera.zoom(1.3)

# print("\nDisplaying results...")
# print("Close the visualization window to exit.\n")
# plotter.show()

# # ============================================================================
# # GENERATE SUMMARY REPORT
# # ============================================================================
# print("\n" + "="*70)
# print("THERMAL ANALYSIS SUMMARY REPORT")
# print("="*70)
# print(f"\nGeometry Configuration:")
# print(f"  Base Dimensions: {base_length*1000:.1f} x {base_width*1000:.1f} x {base_thick*1000:.1f} mm")
# print(f"  Fin Dimensions: {fin_thick*1000:.1f} x {base_width*1000:.1f} x {fin_height*1000:.1f} mm")
# print(f"  Number of Fins: {num_fins}")
# print(f"  Fin Spacing: {fin_spacing*1000:.1f} mm")

# print(f"\nOperating Conditions:")
# print(f"  Heat Dissipation: {total_power} W")
# print(f"  Convection Coefficient: {conv_coeff} W/m²·K (Natural Convection)")
# print(f"  Ambient Temperature: {ambient_temp}°C")

# print(f"\nThermal Results:")
# print(f"  Maximum Temperature: {max_temp:.2f}°C")
# print(f"  Component Temperature: {max_source_temp:.2f}°C")
# print(f"  Temperature Rise: {max_temp - ambient_temp:.2f}°C")
# print(f"  Thermal Resistance: {thermal_resistance:.4f} K/W ({thermal_resistance*1000:.2f} K/kW)")

# print(f"\nMesh Statistics:")
# print(f"  Total Nodes: {num_nodes:,}")
# print(f"  Total Elements: {num_elements:,}")
# print(f"  Element Size: {element_size*1000:.1f} mm")

# print(f"\nDesign Assessment:")
# if max_temp < 85:
#     print(f"  ✓ PASS - Temperature within safe limits for most electronics (<85°C)")
# elif max_temp < 100:
#     print(f"  ⚠ CAUTION - Temperature approaching high limits (85-100°C)")
# else:
#     print(f"  ✗ FAIL - Temperature exceeds safe operating limits (>100°C)")

# print("\n" + "="*70)

# # Exit MAPDL
# print("\nExiting MAPDL...")
# mapdl.exit()
# print("Analysis complete!")
# print("="*70)

"""
3D Steady-State Thermal Analysis of Finned Heat Sink using ANSYS MAPDL
========================================================================

Problem Description:
-------------------
Analysis of an aluminum heat sink with 5 rectangular fins cooling a power
electronic component (e.g., MOSFET, IGBT). The component dissipates 50W of heat.
The heat sink is cooled by natural convection in air.

Geometry:
- Base plate: 50mm x 50mm x 5mm (aluminum)
- Fins: 5 fins, each 50mm x 40mm x 2mm, spaced 10mm apart
- Heat source: 20mm x 20mm area on bottom of base plate (50W power dissipation)

Boundary Conditions:
- Heat flux applied at bottom center (component location)
- Convection on all exposed surfaces (h = 10 W/m²·K for natural convection)
- Ambient temperature: 25°C

Installation Instructions:
--------------------------
pip install ansys-mapdl-core
pip install numpy
pip install pyvista
pip install matplotlib

Note: You need ANSYS MAPDL installed on your system.
"""

import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl

# Launch MAPDL service
print("="*70)
print("3D STEADY-STATE THERMAL ANALYSIS OF FINNED HEAT SINK")
print("="*70)
print("\nLaunching MAPDL...")

# Specify ANSYS Student v252 path
exec_file = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"
mapdl = launch_mapdl(exec_file=exec_file)

mapdl.clear()
mapdl.prep7()
mapdl.title("3D Heat Sink Thermal Analysis - Natural Convection")

# ============================================================================
# DEFINE PARAMETERS (SI units: meters, Watts, Kelvin)
# ============================================================================
print("\nDefining analysis parameters...")

# Geometry parameters (convert mm to m)
base_length = 0.050      # Base length (m)
base_width = 0.050       # Base width (m)
base_thick = 0.005       # Base thickness (m)

fin_height = 0.040       # Fin height above base (m)
fin_thick = 0.002        # Fin thickness (m)
fin_spacing = 0.010      # Spacing between fins (m)
num_fins = 5             # Number of fins

# Heat source parameters
heat_source_size = 0.020 # Heat source size (20mm x 20mm)
total_power = 50.0       # Total power dissipation (W)

# Thermal parameters
ambient_temp = 25.0      # Ambient temperature (°C)
conv_coeff = 10.0        # Convection coefficient for natural convection (W/m²·K)

# Material properties - Aluminum 6061
thermal_cond = 167.0     # Thermal conductivity (W/m·K)
density = 2700.0         # Density (kg/m³)
specific_heat = 896.0    # Specific heat (J/kg·K)

# Mesh control
element_size = 0.003     # Element size (3mm)

print(f"\n  Heat Sink Dimensions: {base_length*1000}mm x {base_width*1000}mm")
print(f"  Number of Fins: {num_fins}")
print(f"  Power Dissipation: {total_power}W")
print(f"  Convection Coefficient: {conv_coeff} W/m²·K")
print(f"  Ambient Temperature: {ambient_temp}°C")

# ============================================================================
# DEFINE ELEMENT TYPE AND MATERIAL PROPERTIES
# ============================================================================
print("\nSetting up element type and material properties...")

# Define 3D thermal solid element (8-node brick)
mapdl.et(1, "SOLID70")

# Define material properties for Aluminum
mapdl.mp("KXX", 1, thermal_cond)   # Thermal conductivity
mapdl.mp("DENS", 1, density)        # Density
mapdl.mp("C", 1, specific_heat)     # Specific heat

# ============================================================================
# CREATE GEOMETRY
# ============================================================================
print("\nCreating heat sink geometry...")

# Create base plate
mapdl.block(0, base_length, 0, base_width, 0, base_thick)

# Create fins
fin_start_x = (base_length - (num_fins * fin_thick + (num_fins - 1) * fin_spacing)) / 2

for i in range(num_fins):
    x_pos = fin_start_x + i * (fin_thick + fin_spacing)
    mapdl.block(x_pos, x_pos + fin_thick, 0, base_width, 
                base_thick, base_thick + fin_height)

# Boolean add all volumes
mapdl.vglue("ALL")

# ============================================================================
# MESH THE MODEL
# ============================================================================
print("Meshing the model...")

mapdl.allsel()
mapdl.lesize("ALL", element_size)  # Set line element size
mapdl.mshape(0, "3D")              # Tetrahedral mesh shape
mapdl.mshkey(1)                    # Mapped meshing where possible
mapdl.vmesh("ALL")

num_nodes = mapdl.mesh.n_node
num_elements = mapdl.mesh.n_elem
print(f"  Nodes created: {num_nodes}")
print(f"  Elements created: {num_elements}")

mapdl.finish()

# ============================================================================
# APPLY LOADS AND BOUNDARY CONDITIONS
# ============================================================================
print("\nApplying boundary conditions...")

mapdl.slashsolu()

# Select nodes on bottom surface for heat flux application
x_center = base_length / 2
y_center = base_width / 2
heat_source_half = heat_source_size / 2

mapdl.nsel("S", "LOC", "Z", 0)  # Bottom surface
mapdl.nsel("R", "LOC", "X", x_center - heat_source_half, x_center + heat_source_half)
mapdl.nsel("R", "LOC", "Y", y_center - heat_source_half, y_center + heat_source_half)

# Calculate and apply heat flux
heat_source_area = heat_source_size * heat_source_size
heat_flux = total_power / heat_source_area
print(f"  Applied heat flux: {heat_flux:.2f} W/m²")
print(f"  Heat source area: {heat_source_area*1e6:.1f} mm²")

mapdl.sf("ALL", "HFLUX", heat_flux)

# Apply convection on all exterior surfaces
print("  Applying convection to exterior surfaces...")
mapdl.allsel()
mapdl.nsel("EXT")
mapdl.esln("S", 1)

# Apply convection on element faces
for face_num in range(1, 7):
    try:
        mapdl.sfe("ALL", face_num, "CONV", "", conv_coeff, ambient_temp)
    except:
        pass

print("  Convection applied successfully")

# ============================================================================
# SOLVE THE MODEL
# ============================================================================
print("\nSolving the thermal model...")
print("  (This may take a moment...)")

mapdl.allsel()
mapdl.solve()
mapdl.finish()

print("  Solution completed successfully!")

# ============================================================================
# POST-PROCESSING
# ============================================================================
print("\n" + "="*70)
print("POST-PROCESSING RESULTS")
print("="*70)

mapdl.post1()
mapdl.set("LAST")

# Get temperature results
temperatures = mapdl.post_processing.nodal_temperature()

# Calculate key thermal metrics
max_temp = np.max(temperatures)
min_temp = np.min(temperatures)
avg_temp = np.mean(temperatures)

print(f"\nTemperature Distribution:")
print(f"  Maximum Temperature: {max_temp:.2f}°C")
print(f"  Minimum Temperature: {min_temp:.2f}°C")
print(f"  Average Temperature: {avg_temp:.2f}°C")
print(f"  Temperature Rise (ΔT): {max_temp - ambient_temp:.2f}°C")

# Calculate thermal resistance
thermal_resistance = (max_temp - ambient_temp) / total_power
print(f"\nThermal Performance:")
print(f"  Thermal Resistance: {thermal_resistance:.4f} K/W")
print(f"  Thermal Resistance: {thermal_resistance*1000:.2f} K/kW")

# Get max temperature at heat source
mapdl.nsel("S", "LOC", "Z", 0)
mapdl.nsel("R", "LOC", "X", x_center - heat_source_half, x_center + heat_source_half)
mapdl.nsel("R", "LOC", "Y", y_center - heat_source_half, y_center + heat_source_half)
source_temps = mapdl.post_processing.nodal_temperature()
max_source_temp = np.max(source_temps)
print(f"  Maximum Component Temperature: {max_source_temp:.2f}°C")

# ============================================================================
# VISUALIZATION
# ============================================================================
print("\nPreparing visualization...")

mapdl.allsel()
grid = mapdl.mesh.grid
temps_kelvin = mapdl.post_processing.nodal_temperature()

# Create visualization
print("\nCreating visualization windows...")

plotter = pv.Plotter(shape=(1, 2), window_size=[1600, 700])

# Left plot - Isometric view
plotter.subplot(0, 0)
plotter.add_mesh(
    grid,
    scalars=temps_kelvin,
    show_edges=False,
    cmap="jet",
    n_colors=256,
    scalar_bar_args={
        "color": "black",
        "title": "Temperature (°C)",
        "vertical": True,
        "n_labels": 8,
        "title_font_size": 14,
        "label_font_size": 11,
        "position_x": 0.05,
        "position_y": 0.3,
    },
)
plotter.add_text(
    f"Heat Sink Temperature Distribution\nMax: {max_temp:.1f}°C | Thermal Resistance: {thermal_resistance:.4f} K/W",
    position="upper_edge",
    font_size=12,
    color="black",
)
plotter.set_background("white")
plotter.camera_position = "iso"
plotter.add_axes()

# Right plot - Top view
plotter.subplot(0, 1)
plotter.add_mesh(
    grid,
    scalars=temps_kelvin,
    show_edges=True,
    cmap="jet",
    n_colors=256,
    scalar_bar_args={
        "color": "black",
        "title": "Temperature (°C)",
        "vertical": True,
        "n_labels": 8,
        "title_font_size": 14,
        "label_font_size": 11,
        "position_x": 0.05,
        "position_y": 0.3,
    },
)
plotter.add_text(
    f"Top View - Fin Temperature Variation\nAmbient: {ambient_temp}°C | Power: {total_power}W",
    position="upper_edge",
    font_size=12,
    color="black",
)
plotter.set_background("white")
plotter.camera_position = "xy"
plotter.camera.zoom(1.3)

print("\nDisplaying results...")
print("Close the visualization window to exit.\n")
plotter.show()

# ============================================================================
# GENERATE SUMMARY REPORT
# ============================================================================
print("\n" + "="*70)
print("THERMAL ANALYSIS SUMMARY REPORT")
print("="*70)
print(f"\nGeometry Configuration:")
print(f"  Base Dimensions: {base_length*1000:.1f} x {base_width*1000:.1f} x {base_thick*1000:.1f} mm")
print(f"  Fin Dimensions: {fin_thick*1000:.1f} x {base_width*1000:.1f} x {fin_height*1000:.1f} mm")
print(f"  Number of Fins: {num_fins}")
print(f"  Fin Spacing: {fin_spacing*1000:.1f} mm")

print(f"\nOperating Conditions:")
print(f"  Heat Dissipation: {total_power} W")
print(f"  Convection Coefficient: {conv_coeff} W/m²·K (Natural Convection)")
print(f"  Ambient Temperature: {ambient_temp}°C")

print(f"\nThermal Results:")
print(f"  Maximum Temperature: {max_temp:.2f}°C")
print(f"  Component Temperature: {max_source_temp:.2f}°C")
print(f"  Temperature Rise: {max_temp - ambient_temp:.2f}°C")
print(f"  Thermal Resistance: {thermal_resistance:.4f} K/W ({thermal_resistance*1000:.2f} K/kW)")

print(f"\nMesh Statistics:")
print(f"  Total Nodes: {num_nodes:,}")
print(f"  Total Elements: {num_elements:,}")
print(f"  Element Size: {element_size*1000:.1f} mm")

print(f"\nDesign Assessment:")
if max_temp < 85:
    print(f"  ✓ PASS - Temperature within safe limits for most electronics (<85°C)")
elif max_temp < 100:
    print(f"  ⚠ CAUTION - Temperature approaching high limits (85-100°C)")
else:
    print(f"  ✗ FAIL - Temperature exceeds safe operating limits (>100°C)")

print("\n" + "="*70)

# Exit MAPDL
print("\nExiting MAPDL...")
mapdl.exit()
print("Analysis complete!")
print("="*70)