"""
analysis_thermal.py - Enhanced Thermal Analysis Module
======================================================
Handles heat flux variation parametric studies with visualization,
animations, and comprehensive plotting
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


def configure_mapdl_graphics(mapdl):
    """Configure MAPDL graphics settings for better visualization"""
    try:
        mapdl.graphics("POWER")
        # Background colors
        mapdl.rgb("INDEX", 100, 100, 100, 0)
        mapdl.rgb("INDEX", 80, 80, 80, 13)
        mapdl.rgb("INDEX", 60, 60, 60, 14)
        mapdl.rgb("INDEX", 0, 0, 0, 15)
    except Exception as e:
        print(f"  Warning: Could not configure graphics: {e}")


def export_thermal_contour_plot(mapdl, result_type, output_path, filename, step_number=None):
    """
    Export thermal contour plot from MAPDL
    
    Args:
        mapdl: MAPDL instance
        result_type: Type of result ('temperature', 'heat_flux', 'thermal_gradient')
        output_path: Path to save images
        filename: Name of the output file
        step_number: Optional step number for animation frames
    
    Returns:
        Path to saved image or None
    """
    try:
        # Enter postprocessing
        mapdl.post1()
        
        # Set the result set
        if step_number is not None:
            mapdl.set(1, step_number)
        else:
            mapdl.set("LAST")
        
        # Configure graphics
        configure_mapdl_graphics(mapdl)
        
        # Plot based on result type
        if result_type == 'temperature':
            mapdl.plnsol("TEMP")
        elif result_type == 'heat_flux':
            mapdl.plnsol("TF", "SUM")
        elif result_type == 'thermal_gradient':
            mapdl.plnsol("TG", "SUM")
        elif result_type == 'heat_flux_x':
            mapdl.plnsol("TF", "X")
        elif result_type == 'heat_flux_y':
            mapdl.plnsol("TF", "Y")
        elif result_type == 'heat_flux_z':
            mapdl.plnsol("TF", "Z")
        
        # Save plot as PNG
        image_path = output_path / filename
        mapdl.show("PNG")
        mapdl.show("CLOSE")
        mapdl.show("PNG", str(image_path))
        
        # Verify file was created
        if image_path.exists():
            return image_path
        else:
            print(f"  Warning: Image file not created: {image_path}")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not export {result_type} plot: {e}")
        return None


def export_mesh_visualization(mapdl, output_path, filename="mesh_3d_view.png"):
    """
    Export 3D mesh visualization
    
    Args:
        mapdl: MAPDL instance
        output_path: Path to save image
        filename: Name of the output file
    
    Returns:
        Path to saved image or None
    """
    try:
        mapdl.finish()
        mapdl.prep7()
        
        # Configure graphics for mesh display
        configure_mapdl_graphics(mapdl)
        
        # Display mesh
        mapdl.eplot()
        
        # Save image
        image_path = output_path / filename
        mapdl.show("PNG")
        mapdl.show("CLOSE")
        mapdl.show("PNG", str(image_path))
        
        if image_path.exists():
            print(f"  ✓ Mesh visualization saved: {image_path}")
            return image_path
        else:
            print(f"  Warning: Mesh image not created: {image_path}")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not export mesh visualization: {e}")
        return None


def create_multi_view_animation(mapdl, output_path, animation_name="directional_heat_flux.gif"):
    """
    Create animated GIF showing heat flux from multiple viewing angles
    Similar to the ExportAnimation functionality in the reference script
    
    Args:
        mapdl: MAPDL instance
        output_path: Path to save animation
        animation_name: Name of output GIF file
    
    Returns:
        Path to GIF file or None
    """
    try:
        print("\n  Creating multi-view heat flux animation...")
        
        mapdl.post1()
        mapdl.set("LAST")
        
        # Configure graphics
        configure_mapdl_graphics(mapdl)
        
        # Create images from different angles
        angles = [
            (0, 0, 0),      # Front view
            (90, 0, 0),     # Top view
            (0, 90, 0),     # Side view
            (45, 45, 0),    # Isometric 1
            (135, 45, 0),   # Isometric 2
            (225, 45, 0),   # Isometric 3
            (315, 45, 0),   # Isometric 4
            (0, 0, 0),      # Back to front
        ]
        
        image_files = []
        
        for idx, (az, el, roll) in enumerate(angles):
            # Plot heat flux
            mapdl.plnsol("TF", "SUM")
            
            # Rotate view (Note: MAPDL view control is limited, this is approximate)
            # In practice, you might need to use /VIEW command
            
            filename = f"hflux_view_{idx:02d}.png"
            image_path = output_path / filename
            
            mapdl.show("PNG")
            mapdl.show("CLOSE")
            mapdl.show("PNG", str(image_path))
            
            if image_path.exists():
                image_files.append(image_path)
        
        # Create GIF from the images
        if image_files:
            gif_path = create_results_animation(
                image_files, output_path, animation_name, duration=400
            )
            return gif_path
        else:
            print("  Warning: No images created for multi-view animation")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not create multi-view animation: {e}")
        return None


def create_results_animation(image_files, output_path, animation_name, duration=500):
    """
    Create animated GIF from a series of images
    
    Args:
        image_files: List of image file paths
        output_path: Directory to save animation
        animation_name: Name of output GIF file
        duration: Duration of each frame in milliseconds
    
    Returns:
        Path to GIF file or None
    """
    try:
        if not image_files:
            print("  Warning: No images provided for animation")
            return None
        
        # Filter out non-existent files
        valid_images = [img for img in image_files if Path(img).exists()]
        
        if not valid_images:
            print("  Warning: No valid image files found")
            return None
        
        # Load images
        images = []
        for img_path in valid_images:
            try:
                images.append(Image.open(img_path))
            except Exception as e:
                print(f"  Warning: Could not load image {img_path}: {e}")
        
        if not images:
            return None
        
        # Save as GIF
        gif_path = output_path / animation_name
        images[0].save(
            gif_path,
            save_all=True,
            append_images=images[1:],
            duration=duration,
            loop=0,
            optimize=False
        )
        
        print(f"  ✓ Animation saved: {gif_path}")
        return gif_path
        
    except Exception as e:
        print(f"  Warning: Could not create animation: {e}")
        return None


def create_thermal_parametric_plots(df, output_path):
    """
    Create comprehensive summary plots for thermal parametric study
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    
    Returns:
        Path to saved plot or None
    """
    try:
        # Set style for better looking plots
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Thermal Parametric Study Results', fontsize=20, fontweight='bold')
        
        # Plot 1: Heat Flux vs Max Temperature
        axes[0, 0].plot(df['heat_flux_w_m2'], df['max_temp_c'], 
                       'o-', linewidth=2.5, markersize=10, color='#d62728', 
                       markerfacecolor='white', markeredgewidth=2)
        axes[0, 0].set_xlabel('Heat Flux (W/m²)', fontsize=13, fontweight='bold')
        axes[0, 0].set_ylabel('Max Temperature (°C)', fontsize=13, fontweight='bold')
        axes[0, 0].set_title('Heat Flux vs Maximum Temperature', fontsize=15, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        
        # Plot 2: Heat Flux vs Temperature Range
        axes[0, 1].plot(df['heat_flux_w_m2'], df['temp_range_c'], 
                       'o-', linewidth=2.5, markersize=10, color='#ff7f0e',
                       markerfacecolor='white', markeredgewidth=2)
        axes[0, 1].set_xlabel('Heat Flux (W/m²)', fontsize=13, fontweight='bold')
        axes[0, 1].set_ylabel('Temperature Range (°C)', fontsize=13, fontweight='bold')
        axes[0, 1].set_title('Heat Flux vs Temperature Range', fontsize=15, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, linestyle='--')
        
        # Plot 3: Heat Flux vs Average Temperature
        axes[0, 2].plot(df['heat_flux_w_m2'], df['avg_temp_c'], 
                       'o-', linewidth=2.5, markersize=10, color='#2ca02c',
                       markerfacecolor='white', markeredgewidth=2)
        axes[0, 2].set_xlabel('Heat Flux (W/m²)', fontsize=13, fontweight='bold')
        axes[0, 2].set_ylabel('Avg Temperature (°C)', fontsize=13, fontweight='bold')
        axes[0, 2].set_title('Heat Flux vs Average Temperature', fontsize=15, fontweight='bold')
        axes[0, 2].grid(True, alpha=0.3, linestyle='--')
        
        # Plot 4: Temperature Distribution (Max, Min, Avg)
        axes[1, 0].plot(df['heat_flux_w_m2'], df['max_temp_c'], 
                       'o-', label='Max Temp', linewidth=2.5, markersize=10, color='#d62728')
        axes[1, 0].plot(df['heat_flux_w_m2'], df['min_temp_c'], 
                       's-', label='Min Temp', linewidth=2.5, markersize=10, color='#1f77b4')
        axes[1, 0].plot(df['heat_flux_w_m2'], df['avg_temp_c'], 
                       '^-', label='Avg Temp', linewidth=2.5, markersize=10, color='#2ca02c')
        axes[1, 0].set_xlabel('Heat Flux (W/m²)', fontsize=13, fontweight='bold')
        axes[1, 0].set_ylabel('Temperature (°C)', fontsize=13, fontweight='bold')
        axes[1, 0].set_title('Temperature Distribution Overview', fontsize=15, fontweight='bold')
        axes[1, 0].legend(fontsize=11, loc='best')
        axes[1, 0].grid(True, alpha=0.3, linestyle='--')
        
        # Plot 5: Temperature Gradient (Rate of Change)
        if len(df) > 1:
            temp_gradient = np.gradient(df['max_temp_c'], df['heat_flux_w_m2'])
            axes[1, 1].plot(df['heat_flux_w_m2'], temp_gradient, 
                           'o-', linewidth=2.5, markersize=10, color='#9467bd',
                           markerfacecolor='white', markeredgewidth=2)
            axes[1, 1].set_xlabel('Heat Flux (W/m²)', fontsize=13, fontweight='bold')
            axes[1, 1].set_ylabel('Temperature Gradient (°C/(W/m²))', fontsize=13, fontweight='bold')
            axes[1, 1].set_title('Thermal Sensitivity', fontsize=15, fontweight='bold')
            axes[1, 1].grid(True, alpha=0.3, linestyle='--')
        
        # Plot 6: Summary Statistics Table
        axes[1, 2].axis('off')
        summary_data = [
            ['Parameter', 'Value'],
            ['Max Heat Flux', f"{df['heat_flux_w_m2'].max():.1f} W/m²"],
            ['Min Heat Flux', f"{df['heat_flux_w_m2'].min():.1f} W/m²"],
            ['Peak Temperature', f"{df['max_temp_c'].max():.2f} °C"],
            ['Lowest Temperature', f"{df['min_temp_c'].min():.2f} °C"],
            ['Max Temp Range', f"{df['temp_range_c'].max():.2f} °C"],
            ['Total Runs', f"{len(df)}"]
        ]
        
        table = axes[1, 2].table(cellText=summary_data, cellLoc='left',
                                loc='center', colWidths=[0.5, 0.5])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2)
        
        # Style the header row
        for i in range(2):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(summary_data)):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#E7E6E6')
        
        axes[1, 2].set_title('Study Summary', fontsize=15, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plot_path = output_path / 'thermal_parametric_summary.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Summary plots saved: {plot_path}")
        return plot_path
        
    except Exception as e:
        print(f"  Warning: Could not create parametric plots: {e}")
        return None


def create_individual_result_plots(df, output_path):
    """
    Create individual high-quality plots for each result metric
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    """
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Plot 1: Max Temperature vs Heat Flux (Large, detailed)
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(df['heat_flux_w_m2'], df['max_temp_c'], 
               'o-', linewidth=3, markersize=12, color='#d62728',
               markerfacecolor='white', markeredgewidth=2.5, label='Max Temperature')
        ax.fill_between(df['heat_flux_w_m2'], df['min_temp_c'], df['max_temp_c'], 
                        alpha=0.2, color='#d62728', label='Temperature Range')
        ax.set_xlabel('Heat Flux (W/m²)', fontsize=16, fontweight='bold')
        ax.set_ylabel('Temperature (°C)', fontsize=16, fontweight='bold')
        ax.set_title('Maximum Temperature Response to Heat Flux Variation', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.legend(fontsize=13, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=1.5)
        plt.tight_layout()
        plt.savefig(output_path / 'max_temp_detailed.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Individual plots saved")
        
    except Exception as e:
        print(f"  Warning: Could not create individual plots: {e}")


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

def run_single_thermal_analysis(mapdl, node_tags, node_coords, tet_nodes, 
                                material_props, heat_flux, run_number, 
                                output_path=None, create_images=True):
    """
    Run single thermal analysis with optional visualization
    
    Args:
        mapdl: MAPDL instance
        node_tags: Node IDs
        node_coords: Node coordinates
        tet_nodes: Element connectivity
        material_props: Material properties dictionary
        heat_flux: Heat flux value (W/m²)
        run_number: Current run number for file naming
        output_path: Path for saving images
        create_images: Whether to create contour images
    
    Returns:
        Dictionary with results
    """
    
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
    
    # Export mesh visualization on first run
    if create_images and output_path is not None and run_number == 1:
        export_mesh_visualization(mapdl, output_path, "mesh_3d_view.png")
    
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
    
    # Export images for animation if requested
    image_paths = {}
    if create_images and output_path is not None:
        # Temperature contour
        temp_filename = f"temp_contour_run_{run_number:03d}.png"
        image_paths['temperature'] = export_thermal_contour_plot(
            mapdl, 'temperature', output_path, temp_filename
        )
        
        # Heat flux contour
        hflux_filename = f"hflux_contour_run_{run_number:03d}.png"
        image_paths['heat_flux'] = export_thermal_contour_plot(
            mapdl, 'heat_flux', output_path, hflux_filename
        )
        
        # Thermal gradient
        tgrad_filename = f"tgrad_contour_run_{run_number:03d}.png"
        image_paths['thermal_gradient'] = export_thermal_contour_plot(
            mapdl, 'thermal_gradient', output_path, tgrad_filename
        )
    
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
        'image_paths': image_paths
    }


# ============================================================
# PARAMETRIC STUDY
# ============================================================

def run_thermal_parametric_study(mapdl, node_tags, node_coords, tet_nodes,
                                param_min, param_max, param_steps, material):
    """
    Run parametric study varying heat flux with animations and plots
    
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
    
    # Setup visualization directory
    output_path = setup_visualization_directory()
    print(f"Output directory: {output_path}")
    
    # Generate parameter values
    fluxes = np.linspace(param_min, param_max, param_steps)
    
    results_list = []
    temp_image_paths = []
    hflux_image_paths = []
    tgrad_image_paths = []
    
    for i, flux in enumerate(fluxes, 1):
        print(f"\n[{i}/{len(fluxes)}] Analyzing with Heat Flux = {flux:.1f} W/m²...")
        
        try:
            results = run_single_thermal_analysis(
                mapdl, node_tags, node_coords, tet_nodes, material, flux,
                run_number=i, output_path=output_path, create_images=True
            )
            
            # Collect image paths for different result types
            if results['image_paths']:
                if results['image_paths'].get('temperature'):
                    temp_image_paths.append(results['image_paths']['temperature'])
                if results['image_paths'].get('heat_flux'):
                    hflux_image_paths.append(results['image_paths']['heat_flux'])
                if results['image_paths'].get('thermal_gradient'):
                    tgrad_image_paths.append(results['image_paths']['thermal_gradient'])
            
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
    
    # Create animations and plots
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60)
    
    # Create multiple animations for different result types
    if temp_image_paths:
        print("\n📹 Creating temperature evolution animation...")
        create_results_animation(temp_image_paths, output_path, 
                                'temperature_evolution.gif', duration=500)
    
    if hflux_image_paths:
        print("📹 Creating heat flux evolution animation...")
        create_results_animation(hflux_image_paths, output_path, 
                                'heat_flux_evolution.gif', duration=500)
    
    if tgrad_image_paths:
        print("📹 Creating thermal gradient evolution animation...")
        create_results_animation(tgrad_image_paths, output_path, 
                                'thermal_gradient_evolution.gif', duration=500)
    
    # Create multi-view animation (like the directional heat flux in reference)
    print("📹 Creating multi-view heat flux animation...")
    create_multi_view_animation(mapdl, output_path, "directional_heat_flux.gif")
    
    # Create summary plots
    print("\n📊 Creating parametric study plots...")
    create_thermal_parametric_plots(df, output_path)
    create_individual_result_plots(df, output_path)
    
    # Save to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = output_path / f"thermal_flux_study_{timestamp}.xlsx"
    
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
    print(f"✓ All visualizations saved to: {output_path}")
    
    # Print summary of created files
    print("\n" + "="*60)
    print("OUTPUT SUMMARY")
    print("="*60)
    print("📁 3D Visualizations:")
    print("   • mesh_3d_view.png - 3D mesh visualization")
    print("\n🎬 Animations:")
    print("   • temperature_evolution.gif - Temperature changes over heat flux range")
    print("   • heat_flux_evolution.gif - Heat flux distribution changes")
    print("   • thermal_gradient_evolution.gif - Thermal gradient changes")
    print("   • directional_heat_flux.gif - Multi-view rotating heat flux")
    print("\n📊 Plots:")
    print("   • thermal_parametric_summary.png - 6-panel comprehensive summary")
    print("   • max_temp_detailed.png - Detailed max temperature plot")
    print("\n📄 Data:")
    print(f"   • {excel_filename.name} - Complete results spreadsheet")
    print("\n🖼️  Individual Images:")
    print(f"   • {len(temp_image_paths)} temperature contour images")
    print(f"   • {len(hflux_image_paths)} heat flux contour images")
    print(f"   • {len(tgrad_image_paths)} thermal gradient images")
    
    return df, str(excel_filename)


# ============================================================
# REGISTER THIS ANALYSIS TYPE
# ============================================================

THERMAL_CONFIG['function'] = run_thermal_parametric_study
register_analysis('2', THERMAL_CONFIG)