"""
Parametric FEA Study with Excel Export - FIXED VERSION
=======================================================
Runs multiple analyses with different parameters and exports to Excel

Installation:
pip install pandas openpyxl
"""

import os
import numpy as np
import pandas as pd
import gmsh
from ansys.mapdl.core import launch_mapdl
from datetime import datetime

ANSYS_PATH = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

# ============================================================
# PARAMETRIC STUDY RUNNER
# ============================================================

def import_and_mesh_cad(step_file, mesh_size):
    """Import CAD and create mesh"""
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("model")
    gmsh.model.occ.importShapes(step_file)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
    gmsh.model.mesh.generate(3)
    
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    node_coords = node_coords.reshape(-1, 3) / 1000.0
    
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)
    tet_index = [i for i, et in enumerate(elem_types) if et == 4][0]
    tet_nodes = elem_node_tags[tet_index].reshape(-1, 4)
    
    gmsh.finalize()
    return node_tags, node_coords, tet_nodes

def create_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes):
    """Create mesh in MAPDL - FIXED: Ensure we're in PREP7"""
    mapdl.finish()  # Exit any previous processor
    mapdl.clear()   # Clear database
    mapdl.prep7()   # Enter preprocessor
    mapdl.units("SI")
    
    # CRITICAL: Define element type BEFORE creating elements
    mapdl.et(1, 285)  # SOLID285 - tetrahedral
    
    # Create nodes
    print("  Creating nodes...")
    for node_id, coords in zip(node_tags, node_coords):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
    
    # Create elements
    print("  Creating elements...")
    for tet in tet_nodes:
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))
    
    print("  ✓ Mesh created in MAPDL")

def run_static_structural_analysis(mapdl, node_tags, node_coords, tet_nodes, material_props, force):
    """Run single static structural analysis - FIXED: Recreate mesh each time"""
    
    # SOLUTION 1: Recreate mesh for each analysis
    create_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes)
    
    # Material properties
    mapdl.mp("EX", 1, material_props['youngs_modulus'])
    mapdl.mp("NUXY", 1, material_props['poissons_ratio'])
    mapdl.mp("DENS", 1, material_props['density'])
    
    # Boundary conditions
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "ALL", 0)
    
    mapdl.allsel()
    mapdl.nsel("S", "LOC", "Z", 0.05)
    mapdl.f("ALL", "FZ", -force)
    mapdl.allsel()
    
    # Solve
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype("STATIC")
    mapdl.solve()
    
    # Postprocess
    mapdl.post1()
    mapdl.set("LAST")
    
    stress = mapdl.post_processing.nodal_eqv_stress()
    disp = mapdl.post_processing.nodal_displacement('NORM')
    
    # Find node with maximum stress
    max_stress_idx = np.argmax(stress)
    max_stress_node_id = node_tags[max_stress_idx]
    max_stress_coords = node_coords[max_stress_idx]
    
    # Find node with maximum displacement
    max_disp_idx = np.argmax(disp)
    max_disp_node_id = node_tags[max_disp_idx]
    max_disp_coords = node_coords[max_disp_idx]
    
    return {
        'max_stress_mpa': np.max(stress) / 1e6,
        'max_stress_x_m': max_stress_coords[0],
        'max_stress_y_m': max_stress_coords[1],
        'max_stress_z_m': max_stress_coords[2],
        'max_stress_node': int(max_stress_node_id),
        'max_displacement_mm': np.max(disp) * 1000,
        'max_disp_x_m': max_disp_coords[0],
        'max_disp_y_m': max_disp_coords[1],
        'max_disp_z_m': max_disp_coords[2],
        'max_disp_node': int(max_disp_node_id),
        'avg_stress_mpa': np.mean(stress) / 1e6,
    }

def run_thermal_analysis(mapdl, node_tags, node_coords, tet_nodes, material_props, heat_flux):
    """Run single thermal analysis - FIXED: Recreate mesh each time"""
    
    # Recreate mesh with thermal element
    mapdl.finish()
    mapdl.clear()
    mapdl.prep7()
    mapdl.units("SI")
    
    # Define THERMAL element type
    mapdl.et(1, 278)  # SOLID278 - thermal
    
    # Create nodes
    for node_id, coords in zip(node_tags, node_coords):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
    
    # Create elements
    for tet in tet_nodes:
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))
    
    # Material properties
    mapdl.mp("KXX", 1, material_props['thermal_conductivity'])
    mapdl.mp("DENS", 1, material_props['density'])
    mapdl.mp("C", 1, material_props['specific_heat'])
    
    # Boundary conditions
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "TEMP", 20)
    
    mapdl.allsel()
    mapdl.nsel("S", "LOC", "Z", 0.05)
    mapdl.sf("ALL", "HFLUX", heat_flux)
    mapdl.allsel()
    
    # Solve
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype("STATIC")
    mapdl.solve()
    
    # Postprocess
    mapdl.post1()
    mapdl.set("LAST")
    
    temp = mapdl.post_processing.nodal_temperature()
    
    # Find node with maximum and minimum temperature
    max_temp_idx = np.argmax(temp)
    max_temp_coords = node_coords[max_temp_idx]
    max_temp_node_id = node_tags[max_temp_idx]
    
    min_temp_idx = np.argmin(temp)
    min_temp_coords = node_coords[min_temp_idx]
    min_temp_node_id = node_tags[min_temp_idx]
    
    return {
        'max_temp_c': np.max(temp),
        'max_temp_x_m': max_temp_coords[0],
        'max_temp_y_m': max_temp_coords[1],
        'max_temp_z_m': max_temp_coords[2],
        'max_temp_node': int(max_temp_node_id),
        'min_temp_c': np.min(temp),
        'min_temp_x_m': min_temp_coords[0],
        'min_temp_y_m': min_temp_coords[1],
        'min_temp_z_m': min_temp_coords[2],
        'min_temp_node': int(min_temp_node_id),
        'avg_temp_c': np.mean(temp),
        'temp_range_c': np.max(temp) - np.min(temp),
    }

# ============================================================
# PARAMETRIC STUDY CONFIGURATIONS
# ============================================================

def parametric_study_force_variation():
    """
    Example: Vary force from 100N to 1000N
    Study how stress and displacement change with load
    """
    print("="*60)
    print("PARAMETRIC STUDY: FORCE VARIATION")
    print("="*60)
    
    # Get user inputs
    step_file = input("\nEnter STEP file path: ").strip().strip('"')
    mesh_size = float(input("Mesh size (mm) [8.0]: ") or 8.0)
    
    print("\nForce range:")
    force_min = float(input("  Minimum force (N) [100]: ") or 100)
    force_max = float(input("  Maximum force (N) [1000]: ") or 1000)
    force_steps = int(input("  Number of steps [10]: ") or 10)
    
    # Material properties
    print("\nMaterial properties (SI units):")
    material = {
        'youngs_modulus': float(input("  Young's Modulus (Pa) [200e9]: ") or 200e9),
        'poissons_ratio': float(input("  Poisson's Ratio [0.3]: ") or 0.3),
        'density': float(input("  Density (kg/m³) [7850]: ") or 7850),
    }
    
    # Generate force range
    forces = np.linspace(force_min, force_max, force_steps)
    
    # Create mesh once (reuse mesh data for all analyses)
    print("\n" + "-"*60)
    print("Creating mesh...")
    node_tags, node_coords, tet_nodes = import_and_mesh_cad(step_file, mesh_size)
    print(f"✓ Mesh: {len(node_tags)} nodes, {len(tet_nodes)} elements")
    
    # Launch MAPDL once
    print("\n" + "-"*60)
    print("Launching ANSYS MAPDL...")
    mapdl = launch_mapdl(exec_file=ANSYS_PATH)
    print("✓ MAPDL launched")
    
    # Run parametric study
    results_list = []
    
    print("\n" + "="*60)
    print("RUNNING PARAMETRIC ANALYSES")
    print("="*60)
    
    for i, force in enumerate(forces, 1):
        print(f"\n[{i}/{len(forces)}] Analyzing with Force = {force:.1f} N...")
        
        try:
            # FIXED: Pass mesh data to analysis function
            results = run_static_structural_analysis(
                mapdl, node_tags, node_coords, tet_nodes, material, force
            )
            
            # Store results
            row = {
                'run_number': i,
                'force_n': force,
                'max_stress_mpa': results['max_stress_mpa'],
                'max_stress_x_m': results['max_stress_x_m'],
                'max_stress_y_m': results['max_stress_y_m'],
                'max_stress_z_m': results['max_stress_z_m'],
                'max_stress_node': results['max_stress_node'],
                'max_displacement_mm': results['max_displacement_mm'],
                'max_disp_x_m': results['max_disp_x_m'],
                'max_disp_y_m': results['max_disp_y_m'],
                'max_disp_z_m': results['max_disp_z_m'],
                'max_disp_node': results['max_disp_node'],
                'avg_stress_mpa': results['avg_stress_mpa'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            results_list.append(row)
            
            print(f"  ✓ Max Stress: {results['max_stress_mpa']:.2f} MPa at ({results['max_stress_x_m']:.4f}, {results['max_stress_y_m']:.4f}, {results['max_stress_z_m']:.4f}) m")
            print(f"  ✓ Max Displacement: {results['max_displacement_mm']:.4f} mm at ({results['max_disp_x_m']:.4f}, {results['max_disp_y_m']:.4f}, {results['max_disp_z_m']:.4f}) m")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results_list.append({
                'run_number': i,
                'force_n': force,
                'max_stress_mpa': None,
                'max_displacement_mm': None,
                'avg_stress_mpa': None,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
    
    mapdl.exit()
    
    # Create DataFrame
    df = pd.DataFrame(results_list)
    
    # Save to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f"parametric_study_force_{timestamp}.xlsx"
    
    print("\n" + "="*60)
    print("SAVING RESULTS TO EXCEL")
    print("="*60)
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Results sheet
        df.to_excel(writer, sheet_name='Results', index=False)
        
        # Summary statistics
        summary = pd.DataFrame({
            'Parameter': ['Force (N)'],
            'Min': [force_min],
            'Max': [force_max],
            'Steps': [force_steps],
            'Total Runs': [len(results_list)],
            'Successful': [df['max_stress_mpa'].notna().sum()],
            'Failed': [df['max_stress_mpa'].isna().sum()],
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Material properties
        mat_df = pd.DataFrame([{
            'Property': 'Young\'s Modulus (Pa)',
            'Value': material['youngs_modulus'],
        }, {
            'Property': 'Poisson\'s Ratio',
            'Value': material['poissons_ratio'],
        }, {
            'Property': 'Density (kg/m³)',
            'Value': material['density'],
        }])
        mat_df.to_excel(writer, sheet_name='Material', index=False)
    
    print(f"✓ Results saved to: {excel_filename}")
    
    # Display summary
    print("\n" + "-"*60)
    print("RESULTS SUMMARY")
    print("-"*60)
    print(df[['force_n', 'max_stress_mpa', 'max_stress_x_m', 'max_stress_y_m', 'max_stress_z_m', 'max_displacement_mm']].to_string(index=False))
    
    return df, excel_filename

def parametric_study_thermal_flux():
    """
    Example: Vary heat flux from 500 to 5000 W/m²
    Study thermal response
    """
    print("="*60)
    print("PARAMETRIC STUDY: HEAT FLUX VARIATION")
    print("="*60)
    
    # Get user inputs
    step_file = input("\nEnter STEP file path: ").strip().strip('"')
    mesh_size = float(input("Mesh size (mm) [8.0]: ") or 8.0)
    
    print("\nHeat flux range:")
    flux_min = float(input("  Minimum flux (W/m²) [500]: ") or 500)
    flux_max = float(input("  Maximum flux (W/m²) [5000]: ") or 5000)
    flux_steps = int(input("  Number of steps [10]: ") or 10)
    
    # Material properties
    material = {
        'thermal_conductivity': float(input("\nThermal conductivity (W/m·K) [60.5]: ") or 60.5),
        'specific_heat': float(input("Specific heat (J/kg·K) [434]: ") or 434),
        'density': float(input("Density (kg/m³) [7850]: ") or 7850),
    }
    
    # Generate flux range
    fluxes = np.linspace(flux_min, flux_max, flux_steps)
    
    # Setup
    node_tags, node_coords, tet_nodes = import_and_mesh_cad(step_file, mesh_size)
    mapdl = launch_mapdl(exec_file=ANSYS_PATH)
    
    # Run analyses
    results_list = []
    
    print("\n" + "="*60)
    print("RUNNING PARAMETRIC ANALYSES")
    print("="*60)
    
    for i, flux in enumerate(fluxes, 1):
        print(f"\n[{i}/{len(fluxes)}] Analyzing with Heat Flux = {flux:.1f} W/m²...")
        
        try:
            results = run_thermal_analysis(mapdl, node_tags, node_coords, tet_nodes, material, flux)
            
            row = {
                'run_number': i,
                'heat_flux_w_m2': flux,
                'max_temp_c': results['max_temp_c'],
                'max_temp_x_m': results['max_temp_x_m'],
                'max_temp_y_m': results['max_temp_y_m'],
                'max_temp_z_m': results['max_temp_z_m'],
                'max_temp_node': results['max_temp_node'],
                'min_temp_c': results['min_temp_c'],
                'min_temp_x_m': results['min_temp_x_m'],
                'min_temp_y_m': results['min_temp_y_m'],
                'min_temp_z_m': results['min_temp_z_m'],
                'min_temp_node': results['min_temp_node'],
                'avg_temp_c': results['avg_temp_c'],
                'temp_range_c': results['temp_range_c'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            results_list.append(row)
            
            print(f"  ✓ Max Temp: {results['max_temp_c']:.2f}°C at ({results['max_temp_x_m']:.4f}, {results['max_temp_y_m']:.4f}, {results['max_temp_z_m']:.4f}) m")
            print(f"  ✓ Temp Range: {results['temp_range_c']:.2f}°C")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    mapdl.exit()
    
    # Save results
    df = pd.DataFrame(results_list)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f"parametric_study_thermal_{timestamp}.xlsx"
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Results', index=False)
    
    print(f"\n✓ Results saved to: {excel_filename}")
    print("\n" + df.to_string(index=False))
    
    return df, excel_filename

# ============================================================
# MAIN MENU
# ============================================================

def main_menu():
    """Main menu for parametric studies"""
    print("="*60)
    print("PARAMETRIC FEA STUDY TOOL")
    print("="*60)
    print("\nSelect study type:")
    print("1. Force Variation (Static Structural)")
    print("2. Heat Flux Variation (Thermal)")
    print("3. Custom Multi-Parameter Study")
    print("0. Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == '1':
        parametric_study_force_variation()
    elif choice == '2':
        parametric_study_thermal_flux()
    elif choice == '3':
        print("\nCustom study - coming soon!")
    elif choice == '0':
        return
    else:
        print("Invalid choice")

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")