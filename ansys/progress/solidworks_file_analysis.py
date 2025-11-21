"""
ANSYS MAPDL Analysis with CAD Import
=====================================

Installation Instructions:
--------------------------
pip install ansys-mapdl-core
pip install numpy
pip install pyvista
pip install matplotlib

Note: Ensure ANSYS MAPDL is installed on your system.
"""

import os
import sys
import traceback
import numpy as np
import pyvista as pv
from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting import GraphicsBackend
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap


def display_menu():
    """Display analysis type menu"""
    print("\n" + "="*60)
    print("ANSYS MAPDL ANALYSIS TOOL")
    print("="*60)
    print("\nSelect Analysis Type:")
    print("1. Static Structural Analysis")
    print("2. Modal Analysis (Natural Frequencies)")
    print("3. Thermal Analysis (Steady-State)")
    print("4. Thermal-Structural Analysis")
    print("5. Magnetostatic Analysis")
    print("6. Harmonic Response Analysis")
    print("0. Exit")
    print("="*60)


def get_file_path():
    """Get CAD file path from user"""
    print("\n" + "-"*60)
    print("CAD FILE IMPORT")
    print("-"*60)
    print("\nSupported formats: .step, .stp, .iges, .igs, .sat")
    print("(For SolidWorks .sldprt files, export to STEP format first)")
    print("\nOr type 'cube' to create a simple test cube")
    
    file_path = input("\nEnter the full path to your CAD file (or 'cube'): ").strip().strip('"')
    
    # Check if user wants to create a cube
    if file_path.lower() == 'cube':
        return 'CREATE_CUBE'
    
    # Handle relative paths
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)
    
    print(f"\nChecking file: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"✗ ERROR: File not found!")
        print(f"   Searched at: {file_path}")
        print("\nTip: Use full path or relative path like:")
        print("     ../solidworks-parts/CUBE.step")
        print("     Or type 'cube' to create a test geometry")
        return None
    
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.sldprt', '.step', '.stp', '.iges', '.igs', '.sat']:
        print(f"✗ ERROR: Unsupported file format: {ext}")
        print("   Supported formats: .sldprt, .step, .iges, .sat")
        return None
    
    print(f"✓ File found: {os.path.basename(file_path)}")
    return file_path


def create_cube_geometry(mapdl):
    """Create a simple cube geometry in MAPDL"""
    print("\n" + "-"*60)
    print("CREATING TEST CUBE GEOMETRY")
    print("-"*60)
    
    size = float(input("Enter cube size in meters (e.g., 0.1 for 10cm): ") or "0.1")
    
    print(f"\nCreating {size}m x {size}m x {size}m cube...")
    
    mapdl.prep7()
    
    # Create cube using BLOCK command
    mapdl.block(0, size, 0, size, 0, size)
    
    # Check geometry
    num_vols = mapdl.get('_', 'VOLU', 0, 'COUNT')
    num_areas = mapdl.get('_', 'AREA', 0, 'COUNT')
    
    print("\n" + "-"*60)
    print("GEOMETRY CREATION SUMMARY")
    print("-"*60)
    print(f"Volumes created: {int(num_vols)}")
    print(f"Areas created: {int(num_areas)}")
    
    if num_areas > 0:
        print("\nArea list:")
        mapdl.alist()
    
    print("\n✓ Cube geometry created successfully!")
    
    return True


def get_material_properties():
    """Get material properties from user"""
    print("\n" + "-"*60)
    print("MATERIAL PROPERTIES")
    print("-"*60)
    print("Select material preset:")
    print("1. Structural Steel")
    print("2. Aluminum Alloy")
    print("3. Titanium Alloy")
    print("4. Copper")
    print("5. Custom Material")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    materials = {
        '1': {'name': 'Structural Steel', 'ex': 2e11, 'nuxy': 0.3, 'dens': 7850, 'kxx': 60.5, 'c': 434, 'murx': 1},
        '2': {'name': 'Aluminum Alloy', 'ex': 7.1e10, 'nuxy': 0.33, 'dens': 2770, 'kxx': 170, 'c': 875, 'murx': 1},
        '3': {'name': 'Titanium Alloy', 'ex': 9.6e10, 'nuxy': 0.36, 'dens': 4620, 'kxx': 7.2, 'c': 580, 'murx': 1},
        '4': {'name': 'Copper', 'ex': 1.2e11, 'nuxy': 0.34, 'dens': 8900, 'kxx': 385, 'c': 385, 'murx': 1},
    }
    
    if choice in materials:
        mat = materials[choice]
        print(f"\nSelected: {mat['name']}")
        return mat
    elif choice == '5':
        print("\nEnter custom material properties:")
        return {
            'name': 'Custom Material',
            'ex': float(input("Young's Modulus (Pa): ")),
            'nuxy': float(input("Poisson's Ratio: ")),
            'dens': float(input("Density (kg/m³): ")),
            'kxx': float(input("Thermal Conductivity (W/m·K): ")),
            'c': float(input("Specific Heat (J/kg·K): ")),
            'murx': float(input("Relative Permeability (for magnetic): "))
        }
    else:
        print("Invalid choice. Using Structural Steel as default.")
        return materials['1']


import os
import traceback
# Make sure to import traceback at the top of your file if it's not already there

def import_cad_geometry(mapdl, file_path):
    """Import CAD geometry into MAPDL with geometry repair"""
    print(f"\nImporting CAD file...")
    print(f"File: {os.path.basename(file_path)}")
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.step', '.stp']:
            print("Format: STEP")
            
            # Upload file to MAPDL working directory
            print("Uploading file to ANSYS working directory...")
            mapdl.upload(file_path)
            
            # Get just the filename
            filename_only = os.path.basename(file_path)
            
            # **********************************
            #  NEW FIXED IMPORT LOGIC
            # **********************************
            
            import_success = False
            
            # --- ATTEMPT 1: PARAIN (PREP7 Command) ---
            print("... trying PARAIN command (Method 1)...")
            try:
                mapdl.prep7() # Ensure we are in PREP7
                mapdl.run(f"PARAIN,'{filename_only}',STEP")
                num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                if num_vols > 0:
                    import_success = True
                    print(f"   ✓ PARAIN successful! Volumes found: {num_vols}")
                else:
                    print("   - PARAIN ran but found no volumes.")
            except Exception as e1:
                print(f"   - PARAIN failed: {e1}")

            # --- ATTEMPT 2: ~PARAIN (PREP7 Command) ---
            if not import_success:
                print("... trying ~PARAIN command (Method 2)...")
                try:
                    mapdl.clear() # Clear the failed attempt
                    mapdl.prep7()
                    mapdl.upload(file_path) # Re-upload
                    mapdl.run(f"~PARAIN,'{filename_only}',STEP")
                    num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                    if num_vols > 0:
                        import_success = True
                        print(f"   ✓ ~PARAIN successful! Volumes found: {num_vols}")
                    else:
                        print("   - ~PARAIN ran but found no volumes.")
                except Exception as e2:
                    print(f"   - ~PARAIN failed: {e2}")

            # --- ATTEMPT 3: IGESIN (AUX15 Command) ---
            if not import_success:
                print("... trying IGESIN command (Method 3)...")
                try:
                    mapdl.clear() # Clear the failed attempt
                    mapdl.prep7()
                    mapdl.upload(file_path) # Re-upload
                    
                    # Get base and extension separately
                    file_base = os.path.splitext(filename_only)[0]
                    file_ext_only = os.path.splitext(filename_only)[1].replace('.', '').upper()

                    mapdl.aux15() # Switch to AUX15
                    print("   - Setting AUX15 options...")
                    mapdl.ioptn('IGES', 'NO')
                    mapdl.ioptn('MERGE', 'YES')
                    mapdl.ioptn('SOLID', 'YES')
                    mapdl.ioptn('SMALL', 'YES')
                    mapdl.ioptn('GTOLER', 'DEFA')
                    
                    print(f"   - Running IGESIN, '{file_base}', '{file_ext_only}'")
                    mapdl.igesin(file_base, file_ext_only) # Use correct args
                    
                    mapdl.prep7() # SWITCH BACK!
                    
                    num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                    if num_vols > 0:
                        import_success = True
                        print(f"   ✓ IGESIN successful! Volumes found: {num_vols}")
                    else:
                        print("   - IGESIN ran but found no volumes.")
                except Exception as e3:
                    print(f"   - IGESIN failed: {e3}")
            
            if not import_success:
                print("\n✗ ERROR: All STEP import methods failed.")
                return False
                
            # **********************************
            #  END OF NEW LOGIC
            # **********************************

            # CRITICAL: Check and repair geometry
            print("\nChecking imported geometry...")
            
            # Clean up geometry
            print("\n--- Initial Geometry Check ---")
            mapdl.nummrg('KP')  # Merge coincident keypoints
            
            # Glue overlapping entities
            try:
                mapdl.vglue('ALL')  # Glue volumes
                mapdl.aglue('ALL')  # Glue areas
                mapdl.lglue('ALL')  # Glue lines
            except:
                pass  # Ignore if nothing to glue
            
            # Get counts
            num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
            num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            
            print(f"Keypoints: {num_kps}")
            print(f"Lines: {num_lines}")
            print(f"Areas: {num_areas}")
            print(f"Volumes: {num_vols}")
            
            # If we have keypoints but no volumes, try to rebuild
            if num_kps > 0 and num_vols == 0:
                print("\n⚠ Geometry needs reconstruction...")
                
                # Try to create areas from lines if needed
                if num_areas == 0 and num_lines > 0:
                    print("Attempting to create areas from lines...")
                    try:
                        mapdl.allsel()
                        mapdl.run('AL,ALL')  # Create area from all lines
                        num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
                        print(f"Areas created: {num_areas}")
                    except Exception as e:
                         print(f"Could not create areas: {e}")
                
                # Try to create volume from areas
                if num_areas > 0 and num_vols == 0:
                    print("Attempting to create volume from areas...")
                    try:
                        # Select all areas
                        mapdl.allsel()
                        # Try to create volume
                        mapdl.run('VA,ALL')  # Create volume from all areas
                        num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                        print(f"Volumes created: {num_vols}")
                    except Exception as e:
                        print(f"Could not create volume: {e}")
                        
                        # Alternative: Try gluing areas together first
                        try:
                            print("Trying to glue areas...")
                            mapdl.allsel()
                            mapdl.aglue('ALL')
                            mapdl.run('VA,ALL')
                            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                            print(f"Volumes created: {num_vols}")
                        except:
                            pass
            
            # Final check
            num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
            num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            
            print("\n" + "-"*60)
            print("FINAL GEOMETRY SUMMARY")
            print("-"*60)
            print(f"Keypoints: {num_kps}")
            print(f"Lines: {num_lines}")
            print(f"Areas: {num_areas}")
            print(f"Volumes: {num_vols}")
            
            if num_vols == 0 and num_areas == 0:
                print("\n✗ ERROR: No usable geometry!")
                print("\nThe STEP file imported but couldn't be converted to ANSYS geometry.")
                print("\nTROUBLESHOOTING OPTIONS:")
                print("1. Use 'cube' option to create geometry directly in ANSYS")
                print("2. Export from SolidWorks as IGES format instead")
                print("3. Simplify the geometry (remove small features)")
                print("4. Try Parasolid (.x_t) format if available")
                return False
            
            # Display geometry details
            if num_vols > 0:
                print("\n✓ 3D solid volumes found!")
                print("\nVolume list:")
                mapdl.vlist()
            elif num_areas > 0:
                print("\n✓ 2D surfaces found!")
                print("(Can mesh as shell elements)")
                print("\nArea list:")
                mapdl.alist()
            
            print("\n✓ Geometry ready for meshing!")
            return True
            
        elif ext in ['.iges', '.igs']:
            print("Format: IGES")
            
            # Upload file to MAPDL working directory
            print("Uploading file to ANSYS working directory...")
            mapdl.upload(file_path)
            
            # Get just the filename (no path, WITH extension)
            filename_only = os.path.basename(file_path)
            
            print(f"Importing '{filename_only}' from ANSYS directory...")
            
            mapdl.aux15()
            mapdl.ioptn('MERGE', 'YES')
            mapdl.ioptn('SOLID', 'YES')
            mapdl.ioptn('SMALL', 'YES')
            
            # Pass the full filename to the Python wrapper
            mapdl.igesin(filename_only)
            
            mapdl.prep7()
            
            # Apply same geometry checks
            print("\nCleaning up geometry...")
            mapdl.nummrg('KP')  # Only merge keypoints
            
            try:
                mapdl.vglue('ALL')
                mapdl.aglue('ALL')
                mapdl.lglue('ALL')
            except:
                pass
            
            num_kps = int(mapdl.get('_', 'KP', 0, 'COUNT'))
            num_lines = int(mapdl.get('_', 'LINE', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            
            print("\n" + "-"*60)
            print("GEOMETRY IMPORT SUMMARY")
            print("-"*60)
            print(f"Keypoints: {num_kps}")
            print(f"Lines: {num_lines}")
            print(f"Areas: {num_areas}")
            print(f"Volumes: {num_vols}")
            
            # Try to rebuild if needed
            if num_kps > 0 and num_vols == 0: # Check if we have *anything* but a volume
                
                # Try to create areas from lines if needed
                if num_areas == 0 and num_lines > 0:
                    print("\nAttempting to create areas from lines...")
                    try:
                        mapdl.allsel()
                        mapdl.run('AL,ALL')  # Create area from all lines
                        num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))
                        print(f"Areas created: {num_areas}")
                    except Exception as e:
                        print(f"Could not create areas: {e}") # This is where your wireframe cube fails
                
                # Try to create volume from areas
                if num_areas > 0 and num_vols == 0:
                    print("\nAttempting to create volume from areas...")
                    try:
                        mapdl.allsel()
                        mapdl.run('VA,ALL') # Create volume from all areas
                        num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
                        print(f"Volumes created: {num_vols}")
                    except Exception as e:
                        print(f"Could not create volume: {e}")

            
            # Final check on new numbers
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            num_areas = int(mapdl.get('_', 'AREA', 0, 'COUNT'))

            if num_vols > 0 or num_areas > 0:
                print(f"\n✓ Imported successfully!")
                if num_vols > 0:
                    print(f"Final Volumes: {num_vols}")
                    mapdl.vlist()
                elif num_areas > 0:
                    print(f"Final Areas: {num_areas} (Can mesh as shell)")
                    mapdl.alist()
                return True
            
            print("\n✗ ERROR: No solid volumes or surfaces found.")
            print("   The file may be a wireframe, or the geometry is invalid.")
            print("   Re-export from CAD as a 'Solid' model (STEP is recommended).")
            return False
            
        elif ext == '.sat':
            print("Format: SAT (ACIS)")
            mapdl.satin(file_path)
            mapdl.prep7()
            
            num_vols = int(mapdl.get('_', 'VOLU', 0, 'COUNT'))
            if num_vols > 0:
                print(f"\n✓ Imported successfully! Volumes: {num_vols}")
                return True
            else:
                print("\n✗ ERROR: No volumes found in SAT file.")
                return False
            
        elif ext == '.sldprt':
            print("\n" + "!"*60)
            print("! SolidWorks File Detected")
            print("!"*60)
            print("\nSolidWorks .sldprt files cannot be directly imported.")
            print("\nPlease export to STEP or IGES format first.")
            print("!"*60)
            return False
        
        else:
            print(f"\n✗ ERROR: Unsupported file format: {ext}")
            return False
        
    except Exception as e:
        print(f"\n✗ ERROR importing geometry: {e}")
        print("\nFull error:")
        traceback.print_exc()
        return False
        
def static_structural_analysis(mapdl, material):
    """Perform static structural analysis"""
    print("\n" + "="*60)
    print("STATIC STRUCTURAL ANALYSIS")
    print("="*60)
    
    # Set element type
    mapdl.et(1, 'SOLID186')
    
    # Material properties
    mapdl.mp('EX', 1, material['ex'])
    mapdl.mp('NUXY', 1, material['nuxy'])
    mapdl.mp('DENS', 1, material['dens'])
    
    # Mesh
    esize = float(input("\nEnter element size (meters, e.g., 0.005): "))
    mapdl.esize(esize)
    
    print("\nGenerating mesh...")
    mapdl.vmesh('ALL')
    
    # Check mesh
    num_nodes = mapdl.get('_', 'NODE', 0, 'COUNT')
    num_elems = mapdl.get('_', 'ELEM', 0, 'COUNT')
    
    print(f"Mesh generated: {int(num_nodes)} nodes, {int(num_elems)} elements")
    
    if num_nodes == 0 or num_elems == 0:
        print("\n✗ ERROR: Meshing failed!")
        print("Try a larger element size or check geometry.")
        return None, None
    
    # Get available areas for boundary conditions
    print("\n" + "-"*60)
    print("AVAILABLE AREAS FOR BOUNDARY CONDITIONS:")
    print("-"*60)
    mapdl.alist()
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    print("Fix one face (all DOF = 0)")
    area_num = int(input("Enter area number to fix (from list above): "))
    
    try:
        mapdl.da(area_num, 'ALL', 0)
        print(f"✓ Fixed area {area_num}")
    except:
        print(f"✗ ERROR: Could not fix area {area_num}")
        return None, None
    
    # Apply force
    print("\nApply force on a face")
    force_area = int(input("Enter area number for force: "))
    force_val = float(input("Enter force value (N): "))
    
    try:
        mapdl.sfa(force_area, 1, 'PRES', force_val)
        print(f"✓ Applied force on area {force_area}")
    except:
        print(f"✗ ERROR: Could not apply force to area {force_area}")
        return None, None
    
    # Solve
    print("\nSolving...")
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype('STATIC')
    mapdl.solve()
    mapdl.finish()
    
    # Post-process
    mapdl.post1()
    mapdl.set('LAST')
    
    print("✓ Solution complete!")
    
    return 'stress', 'von Mises Stress (Pa)'


def modal_analysis(mapdl, material):
    """Perform modal analysis"""
    print("\n" + "="*60)
    print("MODAL ANALYSIS")
    print("="*60)
    
    # Set element type
    mapdl.et(1, 'SOLID186')
    
    # Material properties
    mapdl.mp('EX', 1, material['ex'])
    mapdl.mp('NUXY', 1, material['nuxy'])
    mapdl.mp('DENS', 1, material['dens'])
    
    # Mesh
    esize = float(input("\nEnter element size (meters, e.g., 0.005): "))
    mapdl.esize(esize)
    mapdl.vmesh('ALL')
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    area_num = int(input("Enter area number to fix: "))
    mapdl.da(area_num, 'ALL', 0)
    
    # Modal solve
    num_modes = int(input("\nNumber of modes to extract (e.g., 10): "))
    
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype('MODAL')
    mapdl.modopt('LANB', num_modes)
    mapdl.solve()
    mapdl.finish()
    
    # Post-process
    mapdl.post1()
    
    print("\n" + "-"*60)
    print("NATURAL FREQUENCIES")
    print("-"*60)
    for i in range(1, num_modes + 1):
        mapdl.set(1, i)
        freq = mapdl.get('_', 'MODE', '', 'FREQ')
        print(f"Mode {i}: {freq:.2f} Hz")
    
    mapdl.set(1, 1)  # Show first mode
    
    return 'disp', 'Displacement (m)'


def thermal_analysis(mapdl, material):
    """Perform steady-state thermal analysis"""
    print("\n" + "="*60)
    print("THERMAL ANALYSIS")
    print("="*60)
    
    # Set element type
    mapdl.et(1, 'SOLID90')
    
    # Material properties
    mapdl.mp('KXX', 1, material['kxx'])
    mapdl.mp('DENS', 1, material['dens'])
    mapdl.mp('C', 1, material['c'])
    
    # Mesh
    esize = float(input("\nEnter element size (meters, e.g., 0.005): "))
    mapdl.esize(esize)
    mapdl.vmesh('ALL')
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    print("Fix temperature on one face")
    temp_area = int(input("Enter area number for fixed temperature: "))
    temp_val = float(input("Enter temperature value (°C): "))
    mapdl.da(temp_area, 'TEMP', temp_val)
    
    # Apply heat flux
    print("\nApply heat flux on a face")
    flux_area = int(input("Enter area number for heat flux: "))
    flux_val = float(input("Enter heat flux value (W/m²): "))
    mapdl.sfa(flux_area, 1, 'HFLUX', flux_val)
    
    # Solve
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype('STATIC')
    mapdl.solve()
    mapdl.finish()
    
    # Post-process
    mapdl.post1()
    mapdl.set('LAST')
    
    return 'temp', 'Temperature (°C)'


def magnetostatic_analysis(mapdl, material):
    """Perform magnetostatic analysis"""
    print("\n" + "="*60)
    print("MAGNETOSTATIC ANALYSIS")
    print("="*60)
    
    # Set element type
    mapdl.et(1, 'SOLID236')
    
    # Material properties
    mapdl.mp('MURX', 1, material['murx'])
    
    # Mesh
    esize = float(input("\nEnter element size (meters, e.g., 0.005): "))
    mapdl.esize(esize)
    mapdl.vmesh('ALL')
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    print("Apply current density")
    vol_num = int(input("Enter volume number for current: "))
    current_dens = float(input("Enter current density (A/m²): "))
    mapdl.bfv(vol_num, 'JS', 1, current_dens)
    
    # Solve
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype('STATIC')
    mapdl.solve()
    mapdl.finish()
    
    # Post-process
    mapdl.post1()
    mapdl.set('LAST')
    
    return 'b', 'Magnetic Flux Density (T)'


def visualize_results(mapdl, result_type, title):
    """Visualize analysis results"""
    print("\nPreparing visualization...")
    
    try:
        # Get mesh grid
        grid = mapdl.mesh.grid
        
        # Get result values based on type
        if result_type == 'stress':
            scalars = mapdl.post_processing.nodal_eqv_stress()
        elif result_type == 'disp':
            scalars = mapdl.post_processing.nodal_displacement('NORM')
        elif result_type == 'temp':
            scalars = mapdl.post_processing.nodal_temperature()
        elif result_type == 'b':
            scalars = mapdl.post_processing.nodal_values('b', 'sum')
        else:
            scalars = mapdl.post_processing.nodal_displacement('NORM')
        
        # Create plot
        plotter = pv.Plotter(window_size=[1400, 900])
        
        plotter.add_mesh(
            grid,
            scalars=scalars,
            show_edges=True,
            cmap=PyMAPDL_cmap,
            n_colors=9,
            scalar_bar_args={
                "color": "black",
                "title": title,
                "vertical": True,
                "n_labels": 10,
                "title_font_size": 16,
                "label_font_size": 12,
            },
        )
        
        plotter.set_background(color="white")
        plotter.add_text(
            f"ANSYS MAPDL Analysis\n{title}",
            position="upper_edge",
            font_size=14,
            color="black",
        )
        
        print("\nDisplaying results...")
        print("Close the visualization window to continue.")
        plotter.show()
        
    except Exception as e:
        print(f"ERROR during visualization: {e}")
        traceback.print_exc()


def find_ansys_executable():
    """Try to find ANSYS executable automatically"""
    possible_paths = [
        r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe",
        r"C:\Program Files\ANSYS Inc\v252\ansys\bin\winx64\ANSYS252.exe",
        r"C:\Program Files\ANSYS Inc\ANSYS Student\v251\ansys\bin\winx64\ANSYS251.exe",
        r"C:\Program Files\ANSYS Inc\v251\ansys\bin\winx64\ANSYS251.exe",
        r"C:\Program Files\ANSYS Inc\ANSYS Student\v242\ansys\bin\winx64\ANSYS242.exe",
        r"C:\Program Files\ANSYS Inc\v242\ansys\bin\winx64\ANSYS242.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def main():
    """Main function"""
    
    print("\n" + "="*60)
    print("ANSYS MAPDL ANALYSIS TOOL - STARTING...")
    print("="*60)
    
    # Find ANSYS executable
    print("\nSearching for ANSYS installation...")
    exec_file = find_ansys_executable()
    
    if exec_file:
        print(f"✓ Found ANSYS at: {exec_file}")
    else:
        print("✗ Could not find ANSYS automatically.")
        exec_file = input("Enter full path to ANSYS executable: ").strip().strip('"')
        if not os.path.exists(exec_file):
            print("ERROR: ANSYS executable not found!")
            input("\nPress Enter to exit...")
            return
    
    # Launch MAPDL
    print("\nLaunching ANSYS MAPDL...")
    print("Please wait, this may take 30-60 seconds...")
    
    try:
        # Create a simple, clean working directory
        ansys_work_dir = r"C:\ANSYS_TEMP"
        if not os.path.exists(ansys_work_dir):
            os.makedirs(ansys_work_dir)
        print(f"✓ Setting ANSYS working directory to: {ansys_work_dir}")
        
        mapdl = launch_mapdl(exec_file=exec_file, run_location=ansys_work_dir)
        print("\n✓ ANSYS MAPDL launched successfully!")
    except Exception as e:
        print(f"\n✗ ERROR launching MAPDL: {e}")
        print("\nFull error details:")
        traceback.print_exc()
        print("\nTroubleshooting:")
        print("1. Ensure ANSYS is properly installed")
        print("2. Check if ANSYS license is available")
        print("3. Try closing any running ANSYS instances")
        print("4. Run PowerShell as Administrator")
        input("\nPress Enter to exit...")
        return
    
    try:
        while True:
            display_menu()
            choice = input("\nEnter your choice (0-6): ").strip()
            
            if choice == '0':
                print("\nExiting...")
                break
            
            if choice not in ['1', '2', '3', '4', '5', '6']:
                print("Invalid choice. Please try again.")
                continue
            
            # Clear and start fresh
            mapdl.clear()
            mapdl.prep7()
            
            # --- MODIFIED LOGIC HERE ---
            # Get CAD file path or 'cube' command
            file_path = get_file_path()
            if not file_path:
                continue
            
            # Handle geometry creation
            geometry_success = False
            if file_path == 'CREATE_CUBE':
                print("\nAttempting to create built-in cube...")
                if create_cube_geometry(mapdl):
                    geometry_success = True
                else:
                    print("\n✗ ERROR: Failed to create test cube.")
            else:
                # It's a file path, try to import it
                if import_cad_geometry(mapdl, file_path):
                    geometry_success = True
            
            # If geometry failed, loop back to main menu
            if not geometry_success:
                print("\n✗ ERROR: Geometry import or creation failed.")
                print("Please check your file or try the 'cube' option.")
                input("\nPress Enter to continue...")
                continue
            # --- END OF MODIFIED LOGIC ---

            # Get material properties
            material = get_material_properties()
            
            # Perform selected analysis
            try:
                result_type = None
                title = None
                
                if choice == '1':
                    result_type, title = static_structural_analysis(mapdl, material)
                elif choice == '2':
                    result_type, title = modal_analysis(mapdl, material)
                elif choice == '3':
                    result_type, title = thermal_analysis(mapdl, material)
                elif choice == '4':
                    print("\nThermal-Structural analysis combines thermal and structural.")
                    print("Run thermal analysis first, then apply thermal loads to structural.")
                    input("\nPress Enter to continue...")
                    continue
                elif choice == '5':
                    result_type, title = magnetostatic_analysis(mapdl, material)
                elif choice == '6':
                    print("\nHarmonic analysis coming soon!")
                    input("\nPress Enter to continue...")
                    continue
                
                # Visualize results
                if result_type and title:
                    visualize_results(mapdl, result_type, title)
                    print("\n✓ Analysis completed successfully!")
                else:
                    print("\nAnalysis did not produce results to visualize.")
                
            except Exception as e:
                print(f"\nERROR during analysis: {e}")
                print("\nFull error details:")
                traceback.print_exc()
                print("Please check your inputs and try again.")
            
            input("\nPress Enter to return to main menu...")
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
    finally:
        # Exit MAPDL
        print("\nClosing ANSYS MAPDL...")
        try:
            mapdl.exit()
            print("Done!")
        except:
            pass
        
        input("\nPress Enter to exit...")

if __name__ == "__main__":

    try:

        main()

    except Exception as e:

        print(f"\nFATAL ERROR: {e}")

        traceback.print_exc()

        input("\nPress Enter to exit...")

    finally:

        # Ensure window stays open

        pass