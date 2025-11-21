"""
analysis_magnetostatic.py - Magnetostatic Analysis Module
==========================================================
Handles current density variation parametric studies with magnetic field
visualization and comprehensive plotting
"""

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
from analysis_config import MAGNETOSTATIC_CONFIG, register_analysis


def setup_visualization_directory():
    """Create output directory for images and animations"""
    output_path = Path.cwd() / "magnetostatic_results"
    output_path.mkdir(exist_ok=True)
    return output_path


def configure_mapdl_graphics(mapdl):
    """Configure MAPDL graphics settings for better visualization"""
    try:
        mapdl.graphics("POWER")
        mapdl.rgb("INDEX", 100, 100, 100, 0)
        mapdl.rgb("INDEX", 80, 80, 80, 13)
        mapdl.rgb("INDEX", 60, 60, 60, 14)
        mapdl.rgb("INDEX", 0, 0, 0, 15)
    except Exception as e:
        print(f"  Warning: Could not configure graphics: {e}")


def export_magnetic_flux_plot(mapdl, result_type, output_path, filename, step_number=None):
    """
    Export magnetic flux density contour plot
    
    Args:
        mapdl: MAPDL instance
        result_type: Type of result ('bx', 'by', 'bz', 'bsum')
        output_path: Path to save images
        filename: Name of the output file
        step_number: Optional step number for animation frames
    
    Returns:
        Path to saved image or None
    """
    try:
        mapdl.post1()
        
        if step_number is not None:
            mapdl.set(1, step_number)
        else:
            mapdl.set("LAST")
        
        configure_mapdl_graphics(mapdl)
        
        # Plot based on result type
        if result_type == 'bx':
            mapdl.plnsol("B", "X")
        elif result_type == 'by':
            mapdl.plnsol("B", "Y")
        elif result_type == 'bz':
            mapdl.plnsol("B", "Z")
        elif result_type == 'bsum':
            mapdl.plnsol("B", "SUM")
        
        # Save plot as PNG
        image_path = output_path / filename
        mapdl.show("PNG")
        mapdl.show("CLOSE")
        mapdl.show("PNG", str(image_path))
        
        if image_path.exists():
            return image_path
        else:
            print(f"  Warning: Image file not created: {image_path}")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not export {result_type} plot: {e}")
        return None


def export_vector_plot(mapdl, output_path, filename):
    """
    Export magnetic flux vector plot
    
    Args:
        mapdl: MAPDL instance
        output_path: Path to save image
        filename: Name of the output file
    
    Returns:
        Path to saved image or None
    """
    try:
        mapdl.post1()
        mapdl.set("LAST")
        
        configure_mapdl_graphics(mapdl)
        
        # Vector plot of magnetic flux
        mapdl.plvect("B", "", "", "VECT", "ELEM")
        
        image_path = output_path / filename
        mapdl.show("PNG")
        mapdl.show("CLOSE")
        mapdl.show("PNG", str(image_path))
        
        if image_path.exists():
            print(f"  ✓ Vector plot saved: {image_path}")
            return image_path
        else:
            print(f"  Warning: Vector plot not created: {image_path}")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not export vector plot: {e}")
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
        
        configure_mapdl_graphics(mapdl)
        
        mapdl.eplot()
        
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
        
        valid_images = [img for img in image_files if Path(img).exists()]
        
        if not valid_images:
            print("  Warning: No valid image files found")
            return None
        
        images = []
        for img_path in valid_images:
            try:
                images.append(Image.open(img_path))
            except Exception as e:
                print(f"  Warning: Could not load image {img_path}: {e}")
        
        if not images:
            return None
        
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


def create_magnetostatic_parametric_plots(df, output_path):
    """
    Create comprehensive summary plots for magnetostatic parametric study
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    
    Returns:
        Path to saved plot or None
    """
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        
        fig, axes = plt.subplots(2, 3, figsize=(20, 12))
        fig.suptitle('Magnetostatic Parametric Study Results', 
                     fontsize=20, fontweight='bold')
        
        # Plot 1: Current Density vs Max B-Field
        axes[0, 0].plot(df['current_density_a_m2'], df['max_b_field_t'], 
                       'o-', linewidth=2.5, markersize=10, color='#d62728', 
                       markerfacecolor='white', markeredgewidth=2)
        axes[0, 0].set_xlabel('Current Density (A/m²)', fontsize=13, fontweight='bold')
        axes[0, 0].set_ylabel('Max B-Field (T)', fontsize=13, fontweight='bold')
        axes[0, 0].set_title('Current Density vs Maximum Magnetic Flux Density', 
                            fontsize=15, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        axes[0, 0].ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        
        # Plot 2: Current Density vs Average B-Field
        axes[0, 1].plot(df['current_density_a_m2'], df['avg_b_field_t'], 
                       'o-', linewidth=2.5, markersize=10, color='#2ca02c',
                       markerfacecolor='white', markeredgewidth=2)
        axes[0, 1].set_xlabel('Current Density (A/m²)', fontsize=13, fontweight='bold')
        axes[0, 1].set_ylabel('Avg B-Field (T)', fontsize=13, fontweight='bold')
        axes[0, 1].set_title('Current Density vs Average Magnetic Flux Density', 
                            fontsize=15, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, linestyle='--')
        axes[0, 1].ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        
        # Plot 3: B-Field Components Comparison
        axes[0, 2].plot(df['current_density_a_m2'], df['max_bx_t'], 
                       'o-', label='Bx', linewidth=2.5, markersize=8, color='#1f77b4')
        axes[0, 2].plot(df['current_density_a_m2'], df['max_by_t'], 
                       's-', label='By', linewidth=2.5, markersize=8, color='#ff7f0e')
        axes[0, 2].plot(df['current_density_a_m2'], df['max_bz_t'], 
                       '^-', label='Bz', linewidth=2.5, markersize=8, color='#2ca02c')
        axes[0, 2].set_xlabel('Current Density (A/m²)', fontsize=13, fontweight='bold')
        axes[0, 2].set_ylabel('B-Field Component (T)', fontsize=13, fontweight='bold')
        axes[0, 2].set_title('Magnetic Flux Density Components', fontsize=15, fontweight='bold')
        axes[0, 2].legend(fontsize=11, loc='best')
        axes[0, 2].grid(True, alpha=0.3, linestyle='--')
        axes[0, 2].ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        
        # Plot 4: B-Field Distribution (Max, Min, Avg)
        axes[1, 0].plot(df['current_density_a_m2'], df['max_b_field_t'], 
                       'o-', label='Max B', linewidth=2.5, markersize=10, color='#d62728')
        axes[1, 0].plot(df['current_density_a_m2'], df['min_b_field_t'], 
                       's-', label='Min B', linewidth=2.5, markersize=10, color='#1f77b4')
        axes[1, 0].plot(df['current_density_a_m2'], df['avg_b_field_t'], 
                       '^-', label='Avg B', linewidth=2.5, markersize=10, color='#2ca02c')
        axes[1, 0].set_xlabel('Current Density (A/m²)', fontsize=13, fontweight='bold')
        axes[1, 0].set_ylabel('B-Field (T)', fontsize=13, fontweight='bold')
        axes[1, 0].set_title('Magnetic Flux Density Distribution', fontsize=15, fontweight='bold')
        axes[1, 0].legend(fontsize=11, loc='best')
        axes[1, 0].grid(True, alpha=0.3, linestyle='--')
        axes[1, 0].ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        
        # Plot 5: Linearity Check
        if len(df) > 1:
            # Linear fit
            z = np.polyfit(df['current_density_a_m2'], df['max_b_field_t'], 1)
            p = np.poly1d(z)
            
            axes[1, 1].plot(df['current_density_a_m2'], df['max_b_field_t'], 
                           'o', markersize=10, label='Actual', color='#d62728')
            axes[1, 1].plot(df['current_density_a_m2'], p(df['current_density_a_m2']), 
                           '--', linewidth=2, label=f'Linear Fit', color='#1f77b4')
            axes[1, 1].set_xlabel('Current Density (A/m²)', fontsize=13, fontweight='bold')
            axes[1, 1].set_ylabel('Max B-Field (T)', fontsize=13, fontweight='bold')
            axes[1, 1].set_title('Linearity Analysis', fontsize=15, fontweight='bold')
            axes[1, 1].legend(fontsize=11, loc='best')
            axes[1, 1].grid(True, alpha=0.3, linestyle='--')
            axes[1, 1].ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        
        # Plot 6: Summary Statistics Table
        axes[1, 2].axis('off')
        summary_data = [
            ['Parameter', 'Value'],
            ['Max Current Density', f"{df['current_density_a_m2'].max():.2e} A/m²"],
            ['Min Current Density', f"{df['current_density_a_m2'].min():.2e} A/m²"],
            ['Peak B-Field', f"{df['max_b_field_t'].max():.4f} T"],
            ['Min B-Field', f"{df['min_b_field_t'].min():.4f} T"],
            ['Max Bx', f"{df['max_bx_t'].max():.4f} T"],
            ['Max By', f"{df['max_by_t'].max():.4f} T"],
            ['Max Bz', f"{df['max_bz_t'].max():.4f} T"],
            ['Total Runs', f"{len(df)}"]
        ]
        
        table = axes[1, 2].table(cellText=summary_data, cellLoc='left',
                                loc='center', colWidths=[0.5, 0.5])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        for i in range(2):
            table[(0, i)].set_facecolor('#4472C4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        for i in range(1, len(summary_data)):
            for j in range(2):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#E7E6E6')
        
        axes[1, 2].set_title('Study Summary', fontsize=15, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plot_path = output_path / 'magnetostatic_parametric_summary.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Summary plots saved: {plot_path}")
        return plot_path
        
    except Exception as e:
        print(f"  Warning: Could not create parametric plots: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_individual_result_plots(df, output_path):
    """
    Create individual high-quality plots
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    """
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Detailed B-Field plot
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(df['current_density_a_m2'], df['max_b_field_t'], 
               'o-', linewidth=3, markersize=12, color='#d62728',
               markerfacecolor='white', markeredgewidth=2.5, label='Max B-Field')
        ax.fill_between(df['current_density_a_m2'], df['min_b_field_t'], 
                        df['max_b_field_t'], alpha=0.2, color='#d62728', 
                        label='B-Field Range')
        ax.set_xlabel('Current Density (A/m²)', fontsize=16, fontweight='bold')
        ax.set_ylabel('Magnetic Flux Density (T)', fontsize=16, fontweight='bold')
        ax.set_title('Magnetic Flux Density Response to Current Density Variation', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.legend(fontsize=13, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=1.5)
        ax.ticklabel_format(style='scientific', axis='x', scilimits=(0,0))
        plt.tight_layout()
        plt.savefig(output_path / 'max_bfield_detailed.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Individual plots saved")
        
    except Exception as e:
        print(f"  Warning: Could not create individual plots: {e}")


# ============================================================
# MESH CREATION IN MAPDL
# ============================================================

def create_magnetostatic_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes):
    """Create electromagnetic mesh in MAPDL"""
    mapdl.finish()
    mapdl.clear()
    mapdl.prep7()
    mapdl.units("SI")
    
    # Define electromagnetic element type
    mapdl.et(1, 236)  # SOLID236 - 3D magnetic solid
    
    # Create nodes
    for node_id, coords in zip(node_tags, node_coords):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
    
    # Create elements
    for tet in tet_nodes:
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))


# ============================================================
# SINGLE ANALYSIS RUN
# ============================================================

def run_single_magnetostatic_analysis(mapdl, node_tags, node_coords, tet_nodes, 
                                      material_props, current_density, run_number, 
                                      output_path=None, create_images=True):
    """
    Run single magnetostatic analysis
    
    Args:
        mapdl: MAPDL instance
        node_tags: Node IDs
        node_coords: Node coordinates
        tet_nodes: Element connectivity
        material_props: Material properties dictionary
        current_density: Current density value (A/m²)
        run_number: Current run number for file naming
        output_path: Path for saving images
        create_images: Whether to create contour images
    
    Returns:
        Dictionary with results
    """
    
    # Recreate mesh with electromagnetic elements
    create_magnetostatic_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes)
    
    # Material properties
    mapdl.mp("MURX", 1, material_props['relative_permeability'])
    
    # Apply current density to all elements (coil region)
    mapdl.esel("ALL")
    mapdl.bfe("ALL", "JS", 1, "", "", current_density)
    
    # Boundary conditions - Magnetic vector potential = 0 at boundaries
    mapdl.allsel()
    mapdl.nsel("EXT")  # Select exterior nodes
    mapdl.d("ALL", "AZ", 0)
    mapdl.d("ALL", "AX", 0)
    mapdl.d("ALL", "AY", 0)
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
    
    # Get magnetic flux density components
    bx = mapdl.post_processing.nodal_values("B", "X")
    by = mapdl.post_processing.nodal_values("B", "Y")
    bz = mapdl.post_processing.nodal_values("B", "Z")
    b_mag = np.sqrt(bx**2 + by**2 + bz**2)
    
    # Find maximum B-field location
    max_b_idx = np.argmax(b_mag)
    max_b_coords = node_coords[max_b_idx]
    max_b_node_id = node_tags[max_b_idx]
    
    # Find minimum B-field location
    min_b_idx = np.argmin(b_mag)
    min_b_coords = node_coords[min_b_idx]
    min_b_node_id = node_tags[min_b_idx]
    
    # Export images for animation if requested
    image_paths = {}
    if create_images and output_path is not None:
        # B-field magnitude contour
        bsum_filename = f"bfield_contour_run_{run_number:03d}.png"
        image_paths['bsum'] = export_magnetic_flux_plot(
            mapdl, 'bsum', output_path, bsum_filename
        )
        
        # Bx component
        bx_filename = f"bx_contour_run_{run_number:03d}.png"
        image_paths['bx'] = export_magnetic_flux_plot(
            mapdl, 'bx', output_path, bx_filename
        )
        
        # By component
        by_filename = f"by_contour_run_{run_number:03d}.png"
        image_paths['by'] = export_magnetic_flux_plot(
            mapdl, 'by', output_path, by_filename
        )
        
        # Bz component
        bz_filename = f"bz_contour_run_{run_number:03d}.png"
        image_paths['bz'] = export_magnetic_flux_plot(
            mapdl, 'bz', output_path, bz_filename
        )
        
        # Vector plot on first and last run
        if run_number == 1:
            vector_filename = f"bfield_vector_run_{run_number:03d}.png"
            image_paths['vector'] = export_vector_plot(
                mapdl, output_path, vector_filename
            )
    
    return {
        'max_b_field_t': np.max(b_mag),
        'max_b_x_m': max_b_coords[0],
        'max_b_y_m': max_b_coords[1],
        'max_b_z_m': max_b_coords[2],
        'max_b_node': int(max_b_node_id),
        'min_b_field_t': np.min(b_mag),
        'min_b_x_m': min_b_coords[0],
        'min_b_y_m': min_b_coords[1],
        'min_b_z_m': min_b_coords[2],
        'min_b_node': int(min_b_node_id),
        'avg_b_field_t': np.mean(b_mag),
        'max_bx_t': np.max(np.abs(bx)),
        'max_by_t': np.max(np.abs(by)),
        'max_bz_t': np.max(np.abs(bz)),
        'image_paths': image_paths
    }


# ============================================================
# PARAMETRIC STUDY
# ============================================================

def run_magnetostatic_parametric_study(mapdl, node_tags, node_coords, tet_nodes,
                                      param_min, param_max, param_steps, material):
    """
    Run parametric study varying current density
    
    Args:
        mapdl: MAPDL instance
        node_tags: Node IDs from mesh
        node_coords: Node coordinates from mesh
        tet_nodes: Element connectivity from mesh
        param_min: Minimum current density value (A/m²)
        param_max: Maximum current density value (A/m²)
        param_steps: Number of steps
        material: Dictionary of material properties
    
    Returns:
        df: DataFrame with results
        excel_filename: Name of Excel file created
    """
    
    print("\n" + "="*60)
    print("RUNNING MAGNETOSTATIC PARAMETRIC STUDY")
    print("="*60)
    print(f"Current Density range: {param_min:.2e} - {param_max:.2e} A/m²")
    print(f"Number of steps: {param_steps}")
    
    # Setup visualization directory
    output_path = setup_visualization_directory()
    print(f"Output directory: {output_path}")
    
    # Generate parameter values
    current_densities = np.linspace(param_min, param_max, param_steps)
    
    results_list = []
    bsum_image_paths = []
    bx_image_paths = []
    by_image_paths = []
    bz_image_paths = []
    
    for i, j_current in enumerate(current_densities, 1):
        print(f"\n[{i}/{len(current_densities)}] Analyzing with Current Density = {j_current:.2e} A/m²...")
        
        try:
            results = run_single_magnetostatic_analysis(
                mapdl, node_tags, node_coords, tet_nodes, material, j_current,
                run_number=i, output_path=output_path, create_images=True
            )
            
            # Collect image paths
            if results['image_paths']:
                if results['image_paths'].get('bsum'):
                    bsum_image_paths.append(results['image_paths']['bsum'])
                if results['image_paths'].get('bx'):
                    bx_image_paths.append(results['image_paths']['bx'])
                if results['image_paths'].get('by'):
                    by_image_paths.append(results['image_paths']['by'])
                if results['image_paths'].get('bz'):
                    bz_image_paths.append(results['image_paths']['bz'])
            
            row = {
                'run_number': i,
                'current_density_a_m2': j_current,
                'max_b_field_t': results['max_b_field_t'],
                'max_b_x_m': results['max_b_x_m'],
                'max_b_y_m': results['max_b_y_m'],
                'max_b_z_m': results['max_b_z_m'],
                'max_b_node': results['max_b_node'],
                'min_b_field_t': results['min_b_field_t'],
                'min_b_x_m': results['min_b_x_m'],
                'min_b_y_m': results['min_b_y_m'],
                'min_b_z_m': results['min_b_z_m'],
                'min_b_node': results['min_b_node'],
                'avg_b_field_t': results['avg_b_field_t'],
                'max_bx_t': results['max_bx_t'],
                'max_by_t': results['max_by_t'],
                'max_bz_t': results['max_bz_t'],
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            results_list.append(row)
            
            print(f"  ✓ Max B-Field: {results['max_b_field_t']:.4f} T")
            print(f"  ✓ Avg B-Field: {results['avg_b_field_t']:.4f} T")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results_list.append({
                'run_number': i,
                'current_density_a_m2': j_current,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
    
        # ============================================================
    # CREATE DATAFRAME
    # ============================================================
    df = pd.DataFrame(results_list)

    print("\n" + "=" * 60)
    print("CREATING COMPREHENSIVE VISUALIZATIONS")
    print("=" * 60)

    # ====== Only plot if valid results exist ======
    if not df.empty and 'max_b_field_t' in df.columns and df['max_b_field_t'].notna().sum() > 0:
        create_magnetostatic_parametric_plots(df, output_path)
        create_individual_result_plots(df, output_path)
    else:
        print("  ⚠ No valid B-field results available for visualization")

    # ============================================================
    # CREATE ANIMATIONS
    # ============================================================
    print("\nCreating B-field animations...")

    if bsum_image_paths:
        create_results_animation(
            bsum_image_paths, output_path, "bfield_magnitude_evolution.gif", duration=300
        )

    if bx_image_paths:
        create_results_animation(
            bx_image_paths, output_path, "bfield_bx_evolution.gif", duration=300
        )

    if by_image_paths:
        create_results_animation(
            by_image_paths, output_path, "bfield_by_evolution.gif", duration=300
        )

    if bz_image_paths:
        create_results_animation(
            bz_image_paths, output_path, "bfield_bz_evolution.gif", duration=300
        )

    # ============================================================
    # SAVE TO EXCEL
    # ============================================================
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = output_path / f"magnetostatic_current_density_study_{timestamp}.xlsx"

    print("\n" + "=" * 60)
    print("SAVING RESULTS TO EXCEL")
    print("=" * 60)

    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:

        # -------- Raw Results --------
        df.to_excel(writer, sheet_name="Results", index=False)

        # -------- Summary sheet --------
        summary_df = pd.DataFrame({
            "Parameter": ["Current Density (A/m²)"],
            "Min": [param_min],
            "Max": [param_max],
            "Steps": [param_steps],
            "Total Runs": [len(results_list)],
            "Successful": [df['max_b_field_t'].notna().sum()],
            "Failed": [df['max_b_field_t'].isna().sum()],
        })
        summary_df.to_excel(writer, sheet_name="Summary", index=False)

        # -------- Material sheet --------
        mat_df = pd.DataFrame([
            {"Property": "Relative Permeability μ_r", "Value": material["relative_permeability"]},
        ])
        mat_df.to_excel(writer, sheet_name="Material", index=False)

        # -------- Statistics sheet --------
        if df['max_b_field_t'].notna().sum() > 0:
            stats_df = pd.DataFrame({
                "Metric": [
                    "Max B-field Magnitude (T)",
                    "Average B-field Magnitude (T)",
                    "Max Bx Component (T)",
                    "Max By Component (T)",
                    "Max Bz Component (T)"
                ],
                "Min": [
                    df['max_b_field_t'].min(),
                    df['avg_b_field_t'].min(),
                    df['max_bx_t'].min(),
                    df['max_by_t'].min(),
                    df['max_bz_t'].min(),
                ],
                "Max": [
                    df['max_b_field_t'].max(),
                    df['avg_b_field_t'].max(),
                    df['max_bx_t'].max(),
                    df['max_by_t'].max(),
                    df['max_bz_t'].max(),
                ],
                "Mean": [
                    df['max_b_field_t'].mean(),
                    df['avg_b_field_t'].mean(),
                    df['max_bx_t'].mean(),
                    df['max_by_t'].mean(),
                    df['max_bz_t'].mean(),
                ],
                "Std Dev": [
                    df['max_b_field_t'].std(),
                    df['avg_b_field_t'].std(),
                    df['max_bx_t'].std(),
                    df['max_by_t'].std(),
                    df['max_bz_t'].std(),
                ]
            })
            stats_df.to_excel(writer, sheet_name="Statistics", index=False)

    print(f"✓ Excel results written: {excel_filename.name}")
    print(f"✓ Visualizations saved in: {output_path}")

    # ============================================================
    # OUTPUT SUMMARY
    # ============================================================
    print("\n" + "=" * 60)
    print("OUTPUT SUMMARY")
    print("=" * 60)
    print("📊 Comprehensive Analysis Plot: magnetostatic_parametric_summary.png")
    print("📈 Detailed Plot: max_bfield_detailed.png")
    print("🎬 Animation – |B|: bfield_magnitude_evolution.gif")
    print("🎬 Animation – Bx: bfield_bx_evolution.gif")
    print("🎬 Animation – By: bfield_by_evolution.gif")
    print("🎬 Animation – Bz: bfield_bz_evolution.gif")
    print("📐 Mesh View: mesh_3d_view.png")
    print(f"📑 Excel Report: {excel_filename.name}")
    print("=" * 60)

    return df, str(excel_filename)
