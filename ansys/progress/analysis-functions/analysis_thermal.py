"""
analysis_thermal.py - Thermal Analysis Module
==============================================
Handles heat flux variation parametric studies with visualization
"""

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PIL import Image
from analysis_config import THERMAL_CONFIG, register_analysis


def setup_visualization_directory():
    """Create output directory for images and animations"""
    output_path = Path.cwd() / "thermal_results"
    output_path.mkdir(exist_ok=True)
    return output_path

def export_thermal_contour_plot(mapdl, result_type, output_path, filename, step_number=None):
    """
    Export thermal contour plot from MAPDL
    
    Args:
        mapdl: MAPDL instance
        result_type: Type of result ('temperature', 'heat_flux', etc.)
        output_path: Path to save images
        filename: Name of the output file
        step_number: Optional step number for animation frames
    """
    try:
        # Enter postprocessing
        mapdl.post1()
        
        if step_number is not None:
            mapdl.set(1, step_number)
        else:
            mapdl.set("LAST")
        
        # Configure plot settings
        mapdl.graphics("POWER")
        mapdl.rgb("INDEX", 100, 100, 100, 0)
        mapdl.rgb("INDEX", 80, 80, 80, 13)
        mapdl.rgb("INDEX", 60, 60, 60, 14)
        mapdl.rgb("INDEX", 0, 0, 0, 15)
        
        # Plot based on result type
        if result_type == 'temperature':
            mapdl.plnsol("TEMP")
        elif result_type == 'heat_flux':
            mapdl.plnsol("TF", "SUM")
        elif result_type == 'thermal_gradient':
            mapdl.plnsol("TG", "SUM")
        
        # Save plot
        image_path = output_path / filename
        mapdl.show("PNG")
        mapdl.show("CLOSE")
        mapdl.show("PNG", str(image_path))
        
        return image_path
        
    except Exception as e:
        print(f"  Warning: Could not export {result_type} plot: {e}")
        return None

def create_results_animation(image_files, output_path, animation_name, duration=200):
    """
    Create animated GIF from a series of images
    
    Args:
        image_files: List of image file paths
        output_path: Directory to save animation
        animation_name: Name of output GIF file
        duration: Duration of each frame in milliseconds
    """
    try:
        if not image_files:
            return None
            
        images = [Image.open(img) for img in image_files if Path(img).exists()]
        
        if not images:
            return None
        
        gif_path = output_path / animation_name
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0
        )
        
        print(f"  ✓ Animation saved: {gif_path}")
        return gif_path
        
    except Exception as e:
        print(f"  Warning: Could not create animation: {e}")
        return None

def create_thermal_parametric_plots(df, output_path):
    """
    Create summary plots for thermal parametric study
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    """
    try:
        # Set style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Thermal Parametric Study Results', fontsize=18, fontweight='bold')
        
        # Plot 1: Heat Flux vs Max Temperature
        axes[0, 0].plot(df['heat_flux_w_m2'], df['max_temp_c'], 'o-', linewidth=2, markersize=8, color='#d62728')
        axes[0, 0].set_xlabel('Heat Flux (W/m²)', fontsize=12, fontweight='bold')
        axes[0, 0].set_ylabel('Max Temperature (°C)', fontsize=12, fontweight='bold')
        axes[0, 0].set_title('Heat Flux vs Maximum Temperature', fontsize=14, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Heat Flux vs Temperature Range
        axes[0, 1].plot(df['heat_flux_w_m2'], df['temp_range_c'], 'o-', linewidth=2, markersize=8, color='#ff7f0e')
        axes[0, 1].set_xlabel('Heat Flux (W/m²)', fontsize=12, fontweight='bold')
        axes[0, 1].set_ylabel('Temperature Range (°C)', fontsize=12, fontweight='bold')
        axes[0, 1].set_title('Heat Flux vs Temperature Range', fontsize=14, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Heat Flux vs Average Temperature
        axes[1, 0].plot(df['heat_flux_w_m2'], df['avg_temp_c'], 'o-', linewidth=2, markersize=8, color='#2ca02c')
        axes[1, 0].set_xlabel('Heat Flux (W/m²)', fontsize=12, fontweight='bold')
        axes[1, 0].set_ylabel('Avg Temperature (°C)', fontsize=12, fontweight='bold')
        axes[1, 0].set_title('Heat Flux vs Average Temperature', fontsize=14, fontweight='bold')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Temperature Distribution (Max, Min, Avg)
        axes[1, 1].plot(df['heat_flux_w_m2'], df['max_temp_c'], 'o-', label='Max Temp', linewidth=2, markersize=8)
        axes[1, 1].plot(df['heat_flux_w_m2'], df['min_temp_c'], 's-', label='Min Temp', linewidth=2, markersize=8)
        axes[1, 1].plot(df['heat_flux_w_m2'], df['avg_temp_c'], '^-', label='Avg Temp', linewidth=2, markersize=8)
        axes[1, 1].set_xlabel('Heat Flux (W/m²)', fontsize=12, fontweight='bold')
        axes[1, 1].set_ylabel('Temperature (°C)', fontsize=12, fontweight='bold')
        axes[1, 1].set_title('Temperature Distribution Overview', fontsize=14, fontweight='bold')
        axes[1, 1].legend(fontsize=10)
        axes[1, 1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_path = output_path / 'thermal_parametric_summary.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Summary plots saved: {plot_path}")
        return plot_path
        
    except Exception as e:
        print(f"  Warning: Could not create parametric plots: {e}")
        return None

# ============================================================
# MESH CREATION IN MAPDL
# ============================================================

def create_thermal_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes):
    """Create thermal mesh in MAPDL"""
    mapdl.finish()
    mapdl.clear()
    mapdl.prep7()
    mapdl.units("SI")
    
    # Define thermal element type
    mapdl.et(1, 278)  # SOLID278 - thermal tetrahedral
    
    # Create nodes
    for node_id, coords in zip(node_tags, node_coords):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
    
    # Create elements
    for tet in tet_nodes:
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))

# ============================================================
# SINGLE ANALYSIS RUN
# ============================================================

def run_single_thermal_analysis(mapdl, node_tags, node_coords, tet_nodes, material_props, heat_flux):
    """Run single thermal analysis"""
    
    # Recreate mesh with thermal elements
    create_thermal_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes)
    
    # Material properties
    mapdl.mp("KXX", 1, material_props['thermal_conductivity'])
    mapdl.mp("DENS", 1, material_props['density'])
    mapdl.mp("C", 1, material_props['specific_heat'])
    
    # Boundary conditions - Fixed temperature at Z=0
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "TEMP", 20)
    
    # Apply heat flux at Z=0.05
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
    
    # Find maximum temperature location
    max_temp_idx = np.argmax(temp)
    max_temp_coords = node_coords[max_temp_idx]
    max_temp_node_id = node_tags[max_temp_idx]
    
    # Find minimum temperature location
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
# PARAMETRIC STUDY
# ============================================================

def run_thermal_parametric_study(mapdl, node_tags, node_coords, tet_nodes,
                                param_min, param_max, param_steps, material):
    """
    Run parametric study varying heat flux
    
    Args:
        mapdl: MAPDL instance
        node_tags: Node IDs from mesh
        node_coords: Node coordinates from mesh
        tet_nodes: Element connectivity from mesh
        param_min: Minimum heat flux value (W/m²)
        param_max: Maximum heat flux value (W/m²)
        param_steps: Number of steps
        material: Dictionary of material properties
    
    Returns:
        df: DataFrame with results
        excel_filename: Name of Excel file created
    """
    
    print("\n" + "="*60)
    print("RUNNING THERMAL PARAMETRIC STUDY")
    print("="*60)
    print(f"Heat Flux range: {param_min} - {param_max} W/m²")
    print(f"Number of steps: {param_steps}")
    
    # Generate parameter values
    fluxes = np.linspace(param_min, param_max, param_steps)
    
    results_list = []
    
    for i, flux in enumerate(fluxes, 1):
        print(f"\n[{i}/{len(fluxes)}] Analyzing with Heat Flux = {flux:.1f} W/m²...")
        
        try:
            results = run_single_thermal_analysis(
                mapdl, node_tags, node_coords, tet_nodes, material, flux
            )
            
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
            
            print(f"  ✓ Max Temp: {results['max_temp_c']:.2f}°C")
            print(f"  ✓ Temp Range: {results['temp_range_c']:.2f}°C")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results_list.append({
                'run_number': i,
                'heat_flux_w_m2': flux,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
    
    # Create DataFrame
    df = pd.DataFrame(results_list)
    
    # Save to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = f"thermal_flux_study_{timestamp}.xlsx"
    
    print("\n" + "="*60)
    print("SAVING RESULTS TO EXCEL")
    print("="*60)
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Results sheet
        df.to_excel(writer, sheet_name='Results', index=False)
        
        # Summary statistics
        summary = pd.DataFrame({
            'Parameter': ['Heat Flux (W/m²)'],
            'Min': [param_min],
            'Max': [param_max],
            'Steps': [param_steps],
            'Total Runs': [len(results_list)],
            'Successful': [df['max_temp_c'].notna().sum()],
            'Failed': [df['max_temp_c'].isna().sum()],
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Material properties
        mat_df = pd.DataFrame([
            {'Property': 'Thermal Conductivity (W/m·K)', 'Value': material['thermal_conductivity']},
            {'Property': 'Specific Heat (J/kg·K)', 'Value': material['specific_heat']},
            {'Property': 'Density (kg/m³)', 'Value': material['density']},
        ])
        mat_df.to_excel(writer, sheet_name='Material', index=False)
    
    print(f"✓ Results saved to: {excel_filename}")
    
    return df, excel_filename

# ============================================================
# REGISTER THIS ANALYSIS TYPE
# ============================================================

THERMAL_CONFIG['function'] = run_thermal_parametric_study
register_analysis('2', THERMAL_CONFIG)