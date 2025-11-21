"""
Modular FEA Analysis Framework
================================
Supports multiple analysis types with user inputs

Usage:
    python modular_fea.py
"""

import os
import numpy as np
import pandas as pd
import gmsh
from ansys.mapdl.core import launch_mapdl
import pyvista as pv
from datetime import datetime

# ============================================================
# CONFIGURATION
# ============================================================

ANSYS_PATH = r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe"

MATERIALS = {
    'steel': {'name': 'Structural Steel', 'ex': 200e9, 'nuxy': 0.3, 'dens': 7850, 'kxx': 60.5, 'c': 434},
    'aluminum': {'name': 'Aluminum Alloy', 'ex': 71e9, 'nuxy': 0.33, 'dens': 2770, 'kxx': 170, 'c': 875},
    'copper': {'name': 'Copper', 'ex': 120e9, 'nuxy': 0.34, 'dens': 8900, 'kxx': 385, 'c': 385},
    'titanium': {'name': 'Titanium Alloy', 'ex': 96e9, 'nuxy': 0.36, 'dens': 4620, 'kxx': 7.2, 'c': 580},
}

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def print_header(title):
    """Print formatted section header"""
    print("\n" + "="*60)
    print(title.center(60))
    print("="*60)

def print_section(title):
    """Print formatted subsection"""
    print("\n" + "-"*60)
    print(title)
    print("-"*60)

# ============================================================
# GEOMETRY & MESHING
# ============================================================

def import_and_mesh_cad(step_file, mesh_size=8.0):
    """Import CAD file and create mesh using Gmsh"""
    print_section("IMPORTING CAD AND MESHING")
    
    if not os.path.exists(step_file):
        raise FileNotFoundError(f"STEP file not found: {step_file}")
    
    print(f"✓ Found: {step_file}")
    
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("model")
    
    print(f"Importing geometry...")
    gmsh.model.occ.importShapes(step_file)
    gmsh.model.occ.synchronize()
    
    print(f"Generating mesh (size: {mesh_size} mm)...")
    gmsh.option.setNumber("Mesh.CharacteristicLengthMin", mesh_size)
    gmsh.option.setNumber("Mesh.CharacteristicLengthMax", mesh_size)
    gmsh.model.mesh.generate(3)
    
    # Get nodes
    node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
    node_coords = node_coords.reshape(-1, 3) / 1000.0  # mm to m
    
    # Get tetrahedrons
    elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)
    tet_index = [i for i, et in enumerate(elem_types) if et == 4][0]
    tet_nodes = elem_node_tags[tet_index].reshape(-1, 4)
    
    print(f"✓ Mesh created: {len(node_tags)} nodes, {len(tet_nodes)} elements")
    
    gmsh.finalize()
    
    return node_tags, node_coords, tet_nodes

def create_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes):
    """Create mesh directly in MAPDL"""
    print_section("CREATING MESH IN MAPDL")
    
    mapdl.clear()
    mapdl.prep7()
    mapdl.units("SI")
    
    # Create nodes
    print(f"Creating {len(node_tags)} nodes...")
    for i, (node_id, coords) in enumerate(zip(node_tags, node_coords)):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
    
    # Create elements (will assign type later)
    print(f"Creating {len(tet_nodes)} elements...")
    for tet in tet_nodes:
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))
    
    print(f"✓ Mesh created in MAPDL")

# ============================================================
# ANALYSIS MODULES
# ============================================================

class AnalysisConfig:
    """Base class for analysis configuration"""
    def __init__(self):
        self.results = {}
    
    def setup_element_type(self, mapdl):
        raise NotImplementedError
    
    def setup_material(self, mapdl, material):
        raise NotImplementedError
    
    def apply_boundary_conditions(self, mapdl, params):
        raise NotImplementedError
    
    def solve(self, mapdl):
        raise NotImplementedError
    
    def postprocess(self, mapdl):
        raise NotImplementedError

class StaticStructuralAnalysis(AnalysisConfig):
    """Static structural analysis"""
    
    def get_user_inputs(self):
        """Get user inputs for structural analysis"""
        print_section("STATIC STRUCTURAL - USER INPUTS")
        
        params = {}
        params['force'] = float(input("Enter force magnitude (N): "))
        params['force_direction'] = input("Force direction (x/y/z) [z]: ").lower() or 'z'
        
        return params
    
    def setup_element_type(self, mapdl):
        mapdl.et(1, 285)  # SOLID285
    
    def setup_material(self, mapdl, material):
        mapdl.mp("EX", 1, material['ex'])
        mapdl.mp("NUXY", 1, material['nuxy'])
        mapdl.mp("DENS", 1, material['dens'])
    
    def apply_boundary_conditions(self, mapdl, params):
        print_section("APPLYING BOUNDARY CONDITIONS")
        
        # Fix bottom
        mapdl.nsel("S", "LOC", "Z", 0)
        mapdl.d("ALL", "ALL", 0)
        num_fixed = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
        print(f"✓ Fixed {num_fixed} nodes at Z=0")
        
        # Apply force
        mapdl.allsel()
        mapdl.nsel("S", "LOC", "Z", 0.05)
        
        force_component = f"F{params['force_direction'].upper()}"
        force_value = -params['force'] if params['force_direction'] == 'z' else params['force']
        
        mapdl.f("ALL", force_component, force_value)
        num_loaded = int(mapdl.get('_', 'NODE', 0, 'COUNT'))
        print(f"✓ Applied {force_value:.1f} N to {num_loaded} nodes")
        
        mapdl.allsel()
    
    def solve(self, mapdl):
        print_section("SOLVING")
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        print("✓ Solution complete")
    
    def postprocess(self, mapdl):
        print_section("POST-PROCESSING")
        mapdl.post1()
        mapdl.set("LAST")
        
        stress = mapdl.post_processing.nodal_eqv_stress()
        disp = mapdl.post_processing.nodal_displacement('NORM')
        
        self.results = {
            'max_stress_pa': np.max(stress),
            'max_stress_mpa': np.max(stress) / 1e6,
            'max_displacement_m': np.max(disp),
            'max_displacement_mm': np.max(disp) * 1000,
        }
        
        print(f"Max von Mises Stress: {self.results['max_stress_mpa']:.2f} MPa")
        print(f"Max Displacement: {self.results['max_displacement_mm']:.4f} mm")
        
        return stress

class ThermalAnalysis(AnalysisConfig):
    """Steady-state thermal analysis"""
    
    def get_user_inputs(self):
        print_section("THERMAL ANALYSIS - USER INPUTS")
        
        params = {}
        params['temp_fixed'] = float(input("Fixed temperature (°C) [20]: ") or 20)
        params['heat_flux'] = float(input("Heat flux (W/m²) [1000]: ") or 1000)
        
        return params
    
    def setup_element_type(self, mapdl):
        mapdl.et(1, 278)  # SOLID278 - thermal solid
    
    def setup_material(self, mapdl, material):
        mapdl.mp("KXX", 1, material['kxx'])
        mapdl.mp("DENS", 1, material['dens'])
        mapdl.mp("C", 1, material['c'])
    
    def apply_boundary_conditions(self, mapdl, params):
        print_section("APPLYING BOUNDARY CONDITIONS")
        
        # Fix temperature at bottom
        mapdl.nsel("S", "LOC", "Z", 0)
        mapdl.d("ALL", "TEMP", params['temp_fixed'])
        print(f"✓ Fixed temperature: {params['temp_fixed']}°C")
        
        # Apply heat flux at top
        mapdl.allsel()
        mapdl.nsel("S", "LOC", "Z", 0.05)
        mapdl.sf("ALL", "HFLUX", params['heat_flux'])
        print(f"✓ Applied heat flux: {params['heat_flux']} W/m²")
        
        mapdl.allsel()
    
    def solve(self, mapdl):
        print_section("SOLVING")
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("STATIC")
        mapdl.solve()
        print("✓ Solution complete")
    
    def postprocess(self, mapdl):
        print_section("POST-PROCESSING")
        mapdl.post1()
        mapdl.set("LAST")
        
        temp = mapdl.post_processing.nodal_temperature()
        
        self.results = {
            'max_temp_c': np.max(temp),
            'min_temp_c': np.min(temp),
            'avg_temp_c': np.mean(temp),
            'temp_range_c': np.max(temp) - np.min(temp),
        }
        
        print(f"Max Temperature: {self.results['max_temp_c']:.2f}°C")
        print(f"Min Temperature: {self.results['min_temp_c']:.2f}°C")
        print(f"Temperature Range: {self.results['temp_range_c']:.2f}°C")
        
        return temp

class ModalAnalysis(AnalysisConfig):
    """Modal analysis for natural frequencies"""
    
    def get_user_inputs(self):
        print_section("MODAL ANALYSIS - USER INPUTS")
        
        params = {}
        params['num_modes'] = int(input("Number of modes to extract [10]: ") or 10)
        
        return params
    
    def setup_element_type(self, mapdl):
        mapdl.et(1, 285)  # SOLID285
    
    def setup_material(self, mapdl, material):
        mapdl.mp("EX", 1, material['ex'])
        mapdl.mp("NUXY", 1, material['nuxy'])
        mapdl.mp("DENS", 1, material['dens'])
    
    def apply_boundary_conditions(self, mapdl, params):
        print_section("APPLYING BOUNDARY CONDITIONS")
        
        # Fix bottom face
        mapdl.nsel("S", "LOC", "Z", 0)
        mapdl.d("ALL", "ALL", 0)
        print(f"✓ Fixed base for modal analysis")
        
        mapdl.allsel()
    
    def solve(self, mapdl):
        print_section("SOLVING")
        mapdl.finish()
        mapdl.slashsolu()
        mapdl.antype("MODAL")
        mapdl.modopt("LANB", self.params['num_modes'])
        mapdl.solve()
        print("✓ Solution complete")
    
    def postprocess(self, mapdl):
        print_section("POST-PROCESSING")
        mapdl.post1()
        
        frequencies = []
        for i in range(1, self.params['num_modes'] + 1):
            mapdl.set(1, i)
            freq = mapdl.get('_', 'MODE', '', 'FREQ')
            frequencies.append(freq)
            print(f"Mode {i}: {freq:.2f} Hz")
        
        self.results = {
            'frequencies_hz': frequencies,
            'fundamental_freq_hz': frequencies[0],
        }
        
        mapdl.set(1, 1)  # Set to first mode for visualization
        disp = mapdl.post_processing.nodal_displacement('NORM')
        
        return disp

# ============================================================
# MAIN WORKFLOW
# ============================================================

def select_analysis_type():
    """User selects analysis type"""
    print_header("SELECT ANALYSIS TYPE")
    print("1. Static Structural")
    print("2. Thermal (Steady-State)")
    print("3. Modal (Natural Frequencies)")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    analyses = {
        '1': StaticStructuralAnalysis(),
        '2': ThermalAnalysis(),
        '3': ModalAnalysis(),
    }
    
    return analyses.get(choice)

def select_material():
    """User selects material"""
    print_section("SELECT MATERIAL")
    for i, (key, mat) in enumerate(MATERIALS.items(), 1):
        print(f"{i}. {mat['name']}")
    
    choice = int(input("\nEnter choice: "))
    material_key = list(MATERIALS.keys())[choice - 1]
    
    return MATERIALS[material_key]

def run_single_analysis():
    """Run a single analysis"""
    print_header("FEA ANALYSIS TOOL")
    
    # Get inputs
    step_file = input("Enter STEP file path: ").strip().strip('"')
    mesh_size = float(input("Mesh size (mm) [8.0]: ") or 8.0)
    
    analysis = select_analysis_type()
    if not analysis:
        print("Invalid analysis type")
        return None
    
    material = select_material()
    params = analysis.get_user_inputs()
    
    # Store params for modal analysis
    if hasattr(analysis, 'params'):
        analysis.params = params
    
    # Import and mesh
    node_tags, node_coords, tet_nodes = import_and_mesh_cad(step_file, mesh_size)
    
    # Launch MAPDL
    print_section("LAUNCHING ANSYS")
    mapdl = launch_mapdl(exec_file=ANSYS_PATH)
    print("✓ MAPDL launched")
    
    try:
        # Create mesh
        create_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes)
        
        # Setup
        print_section("SETTING UP ANALYSIS")
        analysis.setup_element_type(mapdl)
        analysis.setup_material(mapdl, material)
        print(f"✓ Material: {material['name']}")
        
        # Boundary conditions & solve
        analysis.apply_boundary_conditions(mapdl, params)
        analysis.solve(mapdl)
        
        # Postprocess
        scalars = analysis.postprocess(mapdl)
        
        # Visualization
        print_section("VISUALIZATION")
        grid = mapdl.mesh.grid
        plotter = pv.Plotter(window_size=[1400, 900])
        plotter.add_mesh(grid, scalars=scalars, show_edges=True)
        plotter.show()
        
        return analysis.results, mapdl
        
    finally:
        mapdl.exit()

if __name__ == "__main__":
    try:
        results, mapdl = run_single_analysis()
        print("\n✓ Analysis complete!")
        print("\nResults:", results)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")