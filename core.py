"""
core.py - Main FEA Analysis Controller
=======================================
Handles meshing, user interaction, and delegates to specific analysis modules
"""

import os
import numpy as np
import gmsh
from ansys.mapdl.core import launch_mapdl
from datetime import datetime

# Import analysis modules from analysis-functions directory
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'analysis-functions'))

from analysis_structural import run_structural_parametric_study
from analysis_thermal import run_thermal_parametric_study
from analysis_modal import run_modal_parametric_study
from analysis_magnetostatic import run_magnetostatic_parametric_study
from analysis_config import ANALYSIS_REGISTRY

ANSYS_PATH = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

# ============================================================
# MESHING FUNCTIONS
# ============================================================

def import_and_mesh_cad(step_file, mesh_size):
    """Import CAD and create mesh using Gmsh"""
    print(f"\nCreating mesh with size {mesh_size} mm...")
    
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("model")
    gmsh.model.occ.importShapes(step_file)
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
    gmsh.model.mesh.generate(3)
    
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    node_coords = node_coords.reshape(-1, 3) / 1000.0  # Convert to meters
    
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)
    tet_index = [i for i, et in enumerate(elem_types) if et == 4][0]
    tet_nodes = elem_node_tags[tet_index].reshape(-1, 4)
    
    gmsh.finalize()
    
    print(f"✓ Mesh created: {len(node_tags)} nodes, {len(tet_nodes)} elements")
    return node_tags, node_coords, tet_nodes

# ============================================================
# USER INPUT COLLECTION
# ============================================================

def get_common_inputs():
    """Get inputs common to all analyses"""
    print("\n" + "="*60)
    print("COMMON INPUTS")
    print("="*60)
    
    step_file = input("\nEnter STEP file path: ").strip().strip('"')
    mesh_size = float(input("Mesh size (mm) [8.0]: ") or 8.0)
    
    return {
        'step_file': step_file,
        'mesh_size': mesh_size
    }

def get_analysis_specific_inputs(analysis_type):
    """Get inputs specific to the selected analysis type"""
    if analysis_type not in ANALYSIS_REGISTRY:
        raise ValueError(f"Unknown analysis type: {analysis_type}")
    
    config = ANALYSIS_REGISTRY[analysis_type]
    inputs = {}
    
    print("\n" + "="*60)
    print(f"{config['name'].upper()} - SPECIFIC INPUTS")
    print("="*60)
    
    # Get parametric study parameters
    print(f"\n{config['parameter_name']} range:")
    inputs['param_min'] = float(input(f"  Minimum {config['parameter_name']} ({config['parameter_unit']}) [{config['param_min_default']}]: ") 
                                or config['param_min_default'])
    inputs['param_max'] = float(input(f"  Maximum {config['parameter_name']} ({config['parameter_unit']}) [{config['param_max_default']}]: ") 
                                or config['param_max_default'])
    inputs['param_steps'] = int(input(f"  Number of steps [{config['param_steps_default']}]: ") 
                              or config['param_steps_default'])
    
    # Get material properties
    print(f"\nMaterial properties:")
    material = {}
    for prop_key, prop_config in config['material_properties'].items():
        value = input(f"  {prop_config['name']} ({prop_config['unit']}) [{prop_config['default']}]: ")
        material[prop_key] = float(value) if value else prop_config['default']
    
    inputs['material'] = material
    
    return inputs

# ============================================================
# MAIN WORKFLOW
# ============================================================

def run_parametric_study():
    """Main workflow: mesh -> select analysis -> run study"""
    
    # Step 1: Get common inputs and create mesh
    common_inputs = get_common_inputs()
    node_tags, node_coords, tet_nodes = import_and_mesh_cad(
        common_inputs['step_file'], 
        common_inputs['mesh_size']
    )
    
    # Step 2: Select analysis type
    print("\n" + "="*60)
    print("SELECT ANALYSIS TYPE")
    print("="*60)
    
    for key, config in ANALYSIS_REGISTRY.items():
        print(f"{key}. {config['name']}")
    
    analysis_choice = input("\nEnter choice: ").strip()
    
    if analysis_choice not in ANALYSIS_REGISTRY:
        print("Invalid choice!")
        return
    
    # Step 3: Get analysis-specific inputs
    analysis_inputs = get_analysis_specific_inputs(analysis_choice)
    
    # Step 4: Launch MAPDL
    print("\n" + "="*60)
    print("LAUNCHING ANSYS MAPDL")
    print("="*60)
    mapdl = launch_mapdl(exec_file=ANSYS_PATH)
    print("✓ MAPDL launched")
    
    # Step 5: Run the selected analysis
    analysis_function = ANALYSIS_REGISTRY[analysis_choice]['function']
    
    try:
        df, excel_filename = analysis_function(
            mapdl=mapdl,
            node_tags=node_tags,
            node_coords=node_coords,
            tet_nodes=tet_nodes,
            param_min=analysis_inputs['param_min'],
            param_max=analysis_inputs['param_max'],
            param_steps=analysis_inputs['param_steps'],
            material=analysis_inputs['material']
        )
        
        print("\n" + "="*60)
        print("STUDY COMPLETED SUCCESSFULLY")
        print("="*60)
        print(f"Results saved to: {excel_filename}")
        
    except Exception as e:
        print(f"\n✗ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
    finally:
        mapdl.exit()
        print("\n✓ MAPDL closed")

# ============================================================
# MAIN ENTRY POINT
# ============================================================

def main():
    """Main entry point"""
    print("="*60)
    print("PARAMETRIC FEA STUDY TOOL")
    print("="*60)
    
    try:
        run_parametric_study()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()