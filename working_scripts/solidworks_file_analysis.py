"""
ANSYS MAPDL Analysis with CAD Import - FIXED VERSION
====================================================

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
import time
import shutil
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
    print("4. Magnetostatic Analysis")
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
    if ext not in ['.step', '.stp', '.iges', '.igs', '.sat']:
        print(f"✗ ERROR: Unsupported file format: {ext}")
        print("   Supported formats: .step, .iges, .sat")
        return None
    
    print(f"✓ File found: {os.path.basename(file_path)}")
    return file_path


def create_cube_geometry(mapdl):
    """Create a simple cube geometry in MAPDL"""
    print("\n" + "-"*60)
    print("CREATING TEST CUBE GEOMETRY")
    print("-"*60)
    
    try:
        size_input = input("Enter cube size in meters (e.g., 0.1 for 10cm) [default: 0.1]: ").strip()
        size = float(size_input) if size_input else 0.1
    except ValueError:
        print("Invalid input, using default size of 0.1m")
        size = 0.1
    
    print(f"\nCreating {size}m x {size}m x {size}m cube...")
    
    mapdl.prep7()
    
    # Create cube using BLOCK command
    mapdl.block(0, size, 0, size, 0, size)
    
    # Check geometry - ensure we get proper integer values
    try:
        num_vols = int(float(mapdl.get('NUM_VOLS', 'VOLU', 0, 'COUNT')))
        num_areas = int(float(mapdl.get('NUM_AREAS', 'AREA', 0, 'COUNT')))
    except:
        # Fallback method
        mapdl.vlist()
        output = mapdl.get('_', 'VOLU', 0, 'COUNT')
        num_vols = 1 if output else 0
        num_areas = 6 if num_vols > 0 else 0
    
    print("\n" + "-"*60)
    print("GEOMETRY CREATION SUMMARY")
    print("-"*60)
    print(f"Volumes created: {num_vols}")
    print(f"Areas created: {num_areas}")
    
    if num_vols > 0:
        print("\nVolume list:")
        mapdl.vlist()
    
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
    
    choice = input("\nEnter choice (1-5) [default: 1]: ").strip() or '1'
    
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
        try:
            return {
                'name': 'Custom Material',
                'ex': float(input("Young's Modulus (Pa): ")),
                'nuxy': float(input("Poisson's Ratio: ")),
                'dens': float(input("Density (kg/m³): ")),
                'kxx': float(input("Thermal Conductivity (W/m·K): ")),
                'c': float(input("Specific Heat (J/kg·K): ")),
                'murx': float(input("Relative Permeability (for magnetic): "))
            }
        except ValueError:
            print("Invalid input. Using Structural Steel as default.")
            return materials['1']
    else:
        print("Invalid choice. Using Structural Steel as default.")
        return materials['1']


def import_cad_geometry(mapdl, file_path):
    """Import CAD geometry into MAPDL"""
    print(f"\nImporting CAD file...")
    print(f"File: {os.path.basename(file_path)}")
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        # Switch to AUX15 for import
        mapdl.aux15()
        
        if ext in ['.step', '.stp']:
            print("Format: STEP")
            print("Configuring import options...")
            
            # Set import options
            mapdl.run('IOPTN,IGES,NO')
            mapdl.run('IOPTN,MERGE,YES')
            mapdl.run('IOPTN,SOLID,YES')
            mapdl.run('IOPTN,SMALL,YES')
            mapdl.run('IOPTN,GTOLER,DEFA')
            
            print(f"Reading STEP file: {file_path}")
            
            # Convert path to use forward slashes (ANSYS prefers this)
            file_path_normalized = file_path.replace('\\', '/')
            
            # Try multiple import methods
            import_success = False
            
            # Method 1: Use PARAIN with proper quoting
            try:
                print("Attempting import method 1: PARAIN with quotes...")
                # Remove extension for PARAIN command
                base_name = os.path.splitext(file_path_normalized)[0]
                mapdl.run(f'PARAIN,{base_name},,STEP', mute=False)
                import_success = True
                print("✓ Import successful!")
            except Exception as e1:
                print(f"Method 1 failed: {str(e1)[:100]}")
                
                # Method 2: Copy file to temp directory with simple name
                try:
                    print("Attempting import method 2: Simple path...")
                    import shutil
                    temp_dir = os.path.join(os.getcwd(), 'temp_cad')
                    os.makedirs(temp_dir, exist_ok=True)
                    simple_path = os.path.join(temp_dir, 'import.step')
                    shutil.copy2(file_path, simple_path)
                    
                    simple_normalized = simple_path.replace('\\', '/')
                    base_name = os.path.splitext(simple_normalized)[0]
                    mapdl.run(f'PARAIN,{base_name},,STEP', mute=False)
                    import_success = True
                    print("✓ Import successful!")
                except Exception as e2:
                    print(f"Method 2 failed: {str(e2)[:100]}")
                    
                    # Method 3: Use cd to change to file directory
                    try:
                        print("Attempting import method 3: Change directory...")
                        file_dir = os.path.dirname(file_path)
                        file_name = os.path.basename(file_path)
                        base_name = os.path.splitext(file_name)[0]
                        
                        # Change working directory in MAPDL
                        mapdl.run(f'/CWD,{file_dir.replace(chr(92), "/")}')
                        mapdl.run(f'PARAIN,{base_name},,STEP', mute=False)
                        import_success = True
                        print("✓ Import successful!")
                    except Exception as e3:
                        print(f"Method 3 failed: {str(e3)[:100]}")
                        print("\n✗ All import methods failed!")
                        print("\nTroubleshooting tips:")
                        print("1. Try saving your STEP file with a simpler filename (e.g., 'part.step')")
                        print("2. Move the file to a path without spaces (e.g., C:\\temp\\part.step)")
                        print("3. Ensure the STEP file is valid (try opening in a CAD viewer)")
                        print("4. Try exporting as STEP AP203 or AP214 from your CAD software")
                        raise Exception("Could not import STEP file using any method")
                    
        elif ext in ['.iges', '.igs']:
            print("Format: IGES")
            mapdl.run('IOPTN,MERGE,YES')
            mapdl.run('IOPTN,SOLID,YES')
            mapdl.run('IOPTN,SMALL,YES')
            
            file_path_no_ext = os.path.splitext(file_path)[0]
            mapdl.run(f'IGESIN,"{file_path_no_ext}"', mute=False)
            
        elif ext == '.sat':
            print("Format: SAT (ACIS)")
            mapdl.run(f'SATIN,"{file_path}"', mute=False)
        
        # Switch to PREP7 to work with geometry
        print("Switching to preprocessor...")
        mapdl.prep7()
        
        # Give ANSYS a moment to process the import
        import time
        time.sleep(1)
        
        # Clean up geometry
        print("Cleaning up imported geometry...")
        mapdl.allsel()
        mapdl.nummrg('KP')  # Merge coincident keypoints
        mapdl.nummrg('LINE')  # Merge coincident lines
        mapdl.numcmp('ALL')  # Compress numbering
        
        # Check if geometry was imported
        try:
            num_vols = int(float(mapdl.get('_', 'VOLU', 0, 'COUNT')))
            num_areas = int(float(mapdl.get('_', 'AREA', 0, 'COUNT')))
            num_lines = int(float(mapdl.get('_', 'LINE', 0, 'COUNT')))
            num_kps = int(float(mapdl.get('_', 'KP', 0, 'COUNT')))
        except:
            # Fallback - check if entities exist
            mapdl.vlist()
            num_vols = 1  # Assume at least some geometry if we got here
            num_areas = 0
            num_lines = 0
            num_kps = 0
        
        print("\n" + "-"*60)
        print("GEOMETRY IMPORT SUMMARY")
        print("-"*60)
        print(f"Keypoints: {num_kps}")
        print(f"Lines: {num_lines}")
        print(f"Areas: {num_areas}")
        print(f"Volumes: {num_vols}")
        
        if num_vols == 0 and num_areas == 0:
            print("\n✗ ERROR: No geometry was imported!")
            print("\nTroubleshooting:")
            print("1. Check if the STEP file is valid (open in CAD viewer)")
            print("2. Try exporting from SolidWorks as 'STEP AP214'")
            print("3. Simplify the geometry (remove fillets, chamfers)")
            print("4. Save in a different format (IGES, Parasolid)")
            return False
        
        # Display geometry details
        if num_vols > 0:
            print("\n✓ 3D solid volumes found!")
            print("\nVolume list:")
            mapdl.vlist()
        elif num_areas > 0:
            print("\n✓ 2D surfaces found (no solid volumes)")
            print("\nArea list:")
            mapdl.alist()
        
        print("\n✓ Geometry imported successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR importing geometry: {e}")
        traceback.print_exc()
        return False


def check_geometry(mapdl):
    """Check what geometry entities exist"""
    try:
        num_vols = int(float(mapdl.get('_', 'VOLU', 0, 'COUNT')))
    except:
        num_vols = 0
    
    try:
        num_areas = int(float(mapdl.get('_', 'AREA', 0, 'COUNT')))
    except:
        num_areas = 0
    
    return num_vols, num_areas


def mesh_geometry(mapdl, esize):
    """Mesh the geometry (volumes or areas)"""
    num_vols, num_areas = check_geometry(mapdl)
    
    print(f"\nMeshing geometry (Volumes: {num_vols}, Areas: {num_areas})...")
    
    mapdl.esize(esize)
    
    if num_vols > 0:
        print("Meshing volumes...")
        mapdl.allsel()
        mapdl.vmesh('ALL')
    elif num_areas > 0:
        print("Meshing areas (2D)...")
        mapdl.allsel()
        mapdl.amesh('ALL')
    else:
        print("✗ No geometry to mesh!")
        return False
    
    # Check mesh
    try:
        num_nodes = int(float(mapdl.get('_', 'NODE', 0, 'COUNT')))
        num_elems = int(float(mapdl.get('_', 'ELEM', 0, 'COUNT')))
    except:
        num_nodes = 0
        num_elems = 0
    
    print(f"Mesh generated: {num_nodes} nodes, {num_elems} elements")
    
    if num_nodes == 0 or num_elems == 0:
        print("\n✗ ERROR: Meshing failed!")
        print("Try a larger element size or check geometry.")
        return False
    
    return True


def static_structural_analysis(mapdl, material):
    """Perform static structural analysis"""
    print("\n" + "="*60)
    print("STATIC STRUCTURAL ANALYSIS")
    print("="*60)
    
    # Check geometry type
    num_vols, num_areas = check_geometry(mapdl)
    
    # Set element type based on geometry
    if num_vols > 0:
        mapdl.et(1, 'SOLID186')  # 3D structural element
        print("Element type: SOLID186 (3D)")
    else:
        mapdl.et(1, 'PLANE182')  # 2D structural element
        mapdl.keyopt(1, 3, 3)  # Plane stress with thickness
        print("Element type: PLANE182 (2D)")
    
    # Material properties
    mapdl.mp('EX', 1, material['ex'])
    mapdl.mp('NUXY', 1, material['nuxy'])
    mapdl.mp('DENS', 1, material['dens'])
    
    # Mesh
    try:
        esize_input = input("\nEnter element size (meters, e.g., 0.005) [default: 0.01]: ").strip()
        esize = float(esize_input) if esize_input else 0.01
    except ValueError:
        esize = 0.01
    
    if not mesh_geometry(mapdl, esize):
        return None, None
    
    # Get available areas for boundary conditions
    print("\n" + "-"*60)
    print("AVAILABLE AREAS FOR BOUNDARY CONDITIONS:")
    print("-"*60)
    mapdl.allsel()
    mapdl.alist()
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    print("Fix one face (all DOF = 0)")
    
    try:
        area_num = int(input("Enter area number to fix (from list above): "))
        mapdl.allsel()
        mapdl.da(area_num, 'ALL', 0)
        print(f"✓ Fixed area {area_num}")
    except Exception as e:
        print(f"✗ ERROR: Could not fix area {area_num}: {e}")
        return None, None
    
    # Apply force
    print("\nApply force on a face")
    try:
        force_area = int(input("Enter area number for force: "))
        force_val = float(input("Enter force magnitude (N, negative for compression): "))
        
        mapdl.allsel()
        mapdl.sfa(force_area, 1, 'PRES', force_val)
        print(f"✓ Applied pressure on area {force_area}")
    except Exception as e:
        print(f"✗ ERROR: Could not apply force to area {force_area}: {e}")
        return None, None
    
    # Solve
    print("\nSolving...")
    mapdl.allsel()
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
    
    # Check geometry type
    num_vols, num_areas = check_geometry(mapdl)
    
    # Set element type
    if num_vols > 0:
        mapdl.et(1, 'SOLID186')
    else:
        mapdl.et(1, 'PLANE182')
        mapdl.keyopt(1, 3, 3)
    
    # Material properties
    mapdl.mp('EX', 1, material['ex'])
    mapdl.mp('NUXY', 1, material['nuxy'])
    mapdl.mp('DENS', 1, material['dens'])
    
    # Mesh
    try:
        esize = float(input("\nEnter element size (meters, e.g., 0.005) [default: 0.01]: ") or "0.01")
    except ValueError:
        esize = 0.01
    
    if not mesh_geometry(mapdl, esize):
        return None, None
    
    # List areas
    print("\n" + "-"*60)
    print("AVAILABLE AREAS:")
    print("-"*60)
    mapdl.allsel()
    mapdl.alist()
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    try:
        area_num = int(input("Enter area number to fix: "))
        mapdl.allsel()
        mapdl.da(area_num, 'ALL', 0)
        print(f"✓ Fixed area {area_num}")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return None, None
    
    # Modal solve
    try:
        num_modes = int(input("\nNumber of modes to extract (e.g., 10) [default: 6]: ") or "6")
    except ValueError:
        num_modes = 6
    
    mapdl.allsel()
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
    
    return 'disp', 'Displacement (m) - Mode 1'


def thermal_analysis(mapdl, material):
    """Perform steady-state thermal analysis"""
    print("\n" + "="*60)
    print("THERMAL ANALYSIS")
    print("="*60)
    
    # Check geometry
    num_vols, num_areas = check_geometry(mapdl)
    
    # Set element type
    if num_vols > 0:
        mapdl.et(1, 'SOLID90')
    else:
        mapdl.et(1, 'PLANE77')
    
    # Material properties
    mapdl.mp('KXX', 1, material['kxx'])
    mapdl.mp('DENS', 1, material['dens'])
    mapdl.mp('C', 1, material['c'])
    
    # Mesh
    try:
        esize = float(input("\nEnter element size (meters, e.g., 0.005) [default: 0.01]: ") or "0.01")
    except ValueError:
        esize = 0.01
    
    if not mesh_geometry(mapdl, esize):
        return None, None
    
    # List areas
    mapdl.allsel()
    mapdl.alist()
    
    # Boundary conditions
    print("\nApplying boundary conditions...")
    try:
        temp_area = int(input("Enter area number for fixed temperature: "))
        temp_val = float(input("Enter temperature value (°C): "))
        mapdl.allsel()
        mapdl.da(temp_area, 'TEMP', temp_val)
        print(f"✓ Fixed temperature on area {temp_area}")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return None, None
    
    # Apply heat flux
    try:
        flux_area = int(input("Enter area number for heat flux: "))
        flux_val = float(input("Enter heat flux value (W/m²): "))
        mapdl.allsel()
        mapdl.sfa(flux_area, 1, 'HFLUX', flux_val)
        print(f"✓ Applied heat flux on area {flux_area}")
    except Exception as e:
        print(f"✗ ERROR: {e}")
        return None, None
    
    # Solve
    mapdl.allsel()
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
    
    # Check geometry
    num_vols, num_areas = check_geometry(mapdl)
    
    # Set element type
    if num_vols > 0:
        mapdl.et(1, 'SOLID236')
    else:
        mapdl.et(1, 'PLANE233')
    
    # Material properties
    mapdl.mp('MURX', 1, material['murx'])
    
    # Mesh
    try:
        esize = float(input("\nEnter element size (meters, e.g., 0.005) [default: 0.01]: ") or "0.01")
    except ValueError:
        esize = 0.01
    
    if not mesh_geometry(mapdl, esize):
        return None, None
    
    # List volumes/areas
    mapdl.allsel()
    if num_vols > 0:
        mapdl.vlist()
        print("\nApply current density to a volume")
        try:
            vol_num = int(input("Enter volume number for current: "))
            current_dens = float(input("Enter current density (A/m²): "))
            mapdl.allsel()
            mapdl.bfv(vol_num, 'JS', 1, current_dens)
            print(f"✓ Applied current density to volume {vol_num}")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            return None, None
    else:
        mapdl.alist()
        print("\nApply current density to an area")
        try:
            area_num = int(input("Enter area number for current: "))
            current_dens = float(input("Enter current density (A/m²): "))
            mapdl.allsel()
            mapdl.bfa(area_num, 1, 'JS', 1, current_dens)
            print(f"✓ Applied current density to area {area_num}")
        except Exception as e:
            print(f"✗ ERROR: {e}")
            return None, None
    
    # Solve
    mapdl.allsel()
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
            try:
                scalars = mapdl.post_processing.nodal_values('b', 'sum')
            except:
                scalars = mapdl.post_processing.nodal_values('b', 'x')
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
        mapdl = launch_mapdl(exec_file=exec_file)
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
            choice = input("\nEnter your choice (0-4): ").strip()
            
            if choice == '0':
                print("\nExiting...")
                break
            
            if choice not in ['1', '2', '3', '4']:
                print("Invalid choice. Please try again.")
                continue
            
            # Clear and start fresh
            mapdl.clear()
            mapdl.prep7()
            
            # Get CAD file or create cube
            file_path = get_file_path()
            if not file_path:
                continue
            
            # Handle cube creation vs CAD import
            geometry_created = False
            
            if file_path == 'CREATE_CUBE':
                # Create cube directly
                geometry_created = create_cube_geometry(mapdl)
            else:
                # Import CAD geometry
                geometry_created = import_cad_geometry(mapdl, file_path)
            
            if not geometry_created:
                print("\nGeometry creation/import failed.")
                input("\nPress Enter to continue...")
                continue
            
            # Get material properties
            material = get_material_properties()
            
            # Perform selected analysis
            try:
                if choice == '1':
                    result_type, title = static_structural_analysis(mapdl, material)
                elif choice == '2':
                    result_type, title = modal_analysis(mapdl, material)
                elif choice == '3':
                    result_type, title = thermal_analysis(mapdl, material)
                elif choice == '4':
                    result_type, title = magnetostatic_analysis(mapdl, material)
                
                if result_type and title:
                    # Visualize results
                    visualize_results(mapdl, result_type, title)
                    print("\n✓ Analysis completed successfully!")
                else:
                    print("\n✗ Analysis failed - check errors above")
                
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