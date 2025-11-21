"""
analysis_structural.py - Static Structural Analysis Module
===========================================================
Handles force variation parametric studies with comprehensive visualization
"""

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib import image as mpimg
from PIL import Image
from analysis_config import STRUCTURAL_CONFIG, register_analysis

# ============================================================
# VISUALIZATION FUNCTIONS
# ============================================================

def setup_visualization_directory():
    """Create output directory for images and animations"""
    output_path = Path.cwd() / "structural_results"
    output_path.mkdir(exist_ok=True)
    return output_path

def display_image(image_path, title="Result", pyplot_figsize=(16, 9)):
    """Display and save enhanced image with matplotlib"""
    try:
        if not Path(image_path).exists():
            return
            
        plt.figure(figsize=pyplot_figsize)
        img = mpimg.imread(str(image_path))
        plt.imshow(img)
        plt.title(title, fontsize=16, fontweight='bold', pad=20)
        plt.xticks([])
        plt.yticks([])
        plt.axis('off')
        plt.tight_layout()
        
        display_path = str(image_path).replace('.png', '_display.png')
        plt.savefig(display_path, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"    → Display image saved: {Path(display_path).name}")
        
    except Exception as e:
        print(f"  Warning: Could not display image: {e}")

def export_stress_plot(mapdl, output_path, filename, step_number=None):
    """Export von Mises stress contour plot"""
    try:
        mapdl.post1()
        if step_number:
            mapdl.set(1, step_number)
        else:
            mapdl.set("LAST")
        
        mapdl.plnsol("S", "EQV")
        
        image_path = output_path / filename
        mapdl.show("PNG", str(image_path))
        
        return image_path
    except Exception as e:
        print(f"  Warning: Could not export stress plot: {e}")
        return None

def export_displacement_plot(mapdl, output_path, filename, step_number=None):
    """Export displacement magnitude contour plot"""
    try:
        mapdl.post1()
        if step_number:
            mapdl.set(1, step_number)
        else:
            mapdl.set("LAST")
        
        mapdl.plnsol("U", "SUM")
        
        image_path = output_path / filename
        mapdl.show("PNG", str(image_path))
        
        return image_path
    except Exception as e:
        print(f"  Warning: Could not export displacement plot: {e}")
        return None

def export_deformed_shape(mapdl, output_path, filename):
    """Export deformed shape plot"""
    try:
        mapdl.post1()
        mapdl.set("LAST")
        mapdl.pldisp(2)
        
        image_path = output_path / filename
        mapdl.show("PNG", str(image_path))
        
        return image_path
    except Exception as e:
        print(f"  Warning: Could not export deformed shape: {e}")
        return None

def export_stress_components(mapdl, output_path, prefix="stress_component"):
    """Export individual stress component plots (X, Y, Z, XY, YZ, XZ)"""
    components = ['X', 'Y', 'Z', 'XY', 'YZ', 'XZ']
    image_paths = []
    
    try:
        mapdl.post1()
        mapdl.set("LAST")
        
        for comp in components:
            try:
                mapdl.plnsol("S", comp)
                image_path = output_path / f"{prefix}_{comp}.png"
                mapdl.show("PNG", str(image_path))
                image_paths.append(image_path)
                print(f"    → Stress {comp} component saved")
            except:
                continue
                
        return image_paths
    except Exception as e:
        print(f"  Warning: Could not export stress components: {e}")
        return image_paths

def export_displacement_components(mapdl, output_path, prefix="displacement_component"):
    """Export individual displacement component plots (X, Y, Z)"""
    components = ['X', 'Y', 'Z']
    image_paths = []
    
    try:
        mapdl.post1()
        mapdl.set("LAST")
        
        for comp in components:
            try:
                mapdl.plnsol("U", comp)
                image_path = output_path / f"{prefix}_{comp}.png"
                mapdl.show("PNG", str(image_path))
                image_paths.append(image_path)
                print(f"    → Displacement {comp} component saved")
            except:
                continue
                
        return image_paths
    except Exception as e:
        print(f"  Warning: Could not export displacement components: {e}")
        return image_paths

def export_principal_stresses(mapdl, output_path, prefix="principal_stress"):
    """Export principal stress plots (S1, S2, S3)"""
    principals = ['1', '2', '3']
    image_paths = []
    
    try:
        mapdl.post1()
        mapdl.set("LAST")
        
        for principal in principals:
            try:
                mapdl.plnsol("S", principal)
                image_path = output_path / f"{prefix}_S{principal}.png"
                mapdl.show("PNG", str(image_path))
                image_paths.append(image_path)
                print(f"    → Principal Stress S{principal} saved")
            except:
                continue
                
        return image_paths
    except Exception as e:
        print(f"  Warning: Could not export principal stresses: {e}")
        return image_paths

def create_results_animation(image_files, output_path, animation_name, duration=200):
    """Create animated GIF from image series"""
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
        
        print(f"  ✓ Animation created: {animation_name}")
        return gif_path
        
    except Exception as e:
        print(f"  Warning: Could not create animation: {e}")
        return None

def create_comprehensive_parametric_plots(df, output_path):
    """Create comprehensive summary plots for parametric study"""
    try:
        plt.style.use('seaborn-v0_8-whitegrid')
        
        # Create main figure with 6 subplots
        fig = plt.figure(figsize=(20, 15))
        fig.suptitle('Comprehensive Structural Parametric Study Results', 
                     fontsize=20, fontweight='bold', y=0.995)
        
        # Create grid spec for better layout
        gs = fig.add_gridspec(3, 3, hspace=0.3, wspace=0.3)
        
        # Plot 1: Force vs Max Stress
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.plot(df['force_n'], df['max_stress_mpa'], 'o-', linewidth=2.5, 
                markersize=10, color='#d62728', markeredgecolor='black', markeredgewidth=0.5)
        ax1.set_xlabel('Applied Force (N)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Maximum Stress (MPa)', fontsize=12, fontweight='bold')
        ax1.set_title('Force vs Maximum von Mises Stress', fontsize=13, fontweight='bold', pad=10)
        ax1.grid(True, alpha=0.4, linestyle='--')
        ax1.tick_params(labelsize=10)
        
        # Plot 2: Force vs Max Displacement
        ax2 = fig.add_subplot(gs[0, 1])
        ax2.plot(df['force_n'], df['max_displacement_mm'], 'o-', linewidth=2.5,
                markersize=10, color='#2ca02c', markeredgecolor='black', markeredgewidth=0.5)
        ax2.set_xlabel('Applied Force (N)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Maximum Displacement (mm)', fontsize=12, fontweight='bold')
        ax2.set_title('Force vs Maximum Displacement', fontsize=13, fontweight='bold', pad=10)
        ax2.grid(True, alpha=0.4, linestyle='--')
        ax2.tick_params(labelsize=10)
        
        # Plot 3: Force vs Average Stress
        ax3 = fig.add_subplot(gs[0, 2])
        ax3.plot(df['force_n'], df['avg_stress_mpa'], 'o-', linewidth=2.5,
                markersize=10, color='#ff7f0e', markeredgecolor='black', markeredgewidth=0.5)
        ax3.set_xlabel('Applied Force (N)', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Average Stress (MPa)', fontsize=12, fontweight='bold')
        ax3.set_title('Force vs Average Stress', fontsize=13, fontweight='bold', pad=10)
        ax3.grid(True, alpha=0.4, linestyle='--')
        ax3.tick_params(labelsize=10)
        
        # Plot 4: Stress Distribution (Max vs Avg)
        ax4 = fig.add_subplot(gs[1, 0])
        scatter = ax4.scatter(df['max_stress_mpa'], df['avg_stress_mpa'], 
                            s=150, alpha=0.7, c=df['force_n'], cmap='plasma',
                            edgecolors='black', linewidth=0.5)
        ax4.set_xlabel('Maximum Stress (MPa)', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Average Stress (MPa)', fontsize=12, fontweight='bold')
        ax4.set_title('Stress Distribution Correlation', fontsize=13, fontweight='bold', pad=10)
        ax4.grid(True, alpha=0.4, linestyle='--')
        cbar = plt.colorbar(scatter, ax=ax4)
        cbar.set_label('Force (N)', fontsize=11, fontweight='bold')
        ax4.tick_params(labelsize=10)
        
        # Plot 5: Stress and Displacement on Same Plot (dual axis)
        ax5 = fig.add_subplot(gs[1, 1])
        ax5_twin = ax5.twinx()
        
        line1 = ax5.plot(df['force_n'], df['max_stress_mpa'], 'o-', linewidth=2.5,
                        markersize=10, color='#d62728', label='Max Stress', 
                        markeredgecolor='black', markeredgewidth=0.5)
        line2 = ax5_twin.plot(df['force_n'], df['max_displacement_mm'], 's-', linewidth=2.5,
                             markersize=10, color='#2ca02c', label='Max Displacement',
                             markeredgecolor='black', markeredgewidth=0.5)
        
        ax5.set_xlabel('Applied Force (N)', fontsize=12, fontweight='bold')
        ax5.set_ylabel('Maximum Stress (MPa)', fontsize=12, fontweight='bold', color='#d62728')
        ax5_twin.set_ylabel('Maximum Displacement (mm)', fontsize=12, fontweight='bold', color='#2ca02c')
        ax5.set_title('Combined Response Plot', fontsize=13, fontweight='bold', pad=10)
        ax5.tick_params(axis='y', labelcolor='#d62728', labelsize=10)
        ax5_twin.tick_params(axis='y', labelcolor='#2ca02c', labelsize=10)
        ax5.tick_params(axis='x', labelsize=10)
        ax5.grid(True, alpha=0.4, linestyle='--')
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax5.legend(lines, labels, loc='upper left', fontsize=10)
        
        # Plot 6: Stress Location Heatmap (3D projection)
        ax6 = fig.add_subplot(gs[1, 2], projection='3d')
        scatter3d = ax6.scatter(df['max_stress_x_m']*1000, df['max_stress_y_m']*1000, 
                               df['max_stress_z_m']*1000,
                               c=df['max_stress_mpa'], cmap='hot', s=150, 
                               edgecolors='black', linewidth=0.5, alpha=0.8)
        ax6.set_xlabel('X (mm)', fontsize=11, fontweight='bold')
        ax6.set_ylabel('Y (mm)', fontsize=11, fontweight='bold')
        ax6.set_zlabel('Z (mm)', fontsize=11, fontweight='bold')
        ax6.set_title('Max Stress Locations', fontsize=13, fontweight='bold', pad=10)
        cbar = plt.colorbar(scatter3d, ax=ax6, shrink=0.6)
        cbar.set_label('Stress (MPa)', fontsize=10, fontweight='bold')
        
        # Plot 7: Displacement Location Heatmap (3D projection)
        ax7 = fig.add_subplot(gs[2, 0], projection='3d')
        scatter3d_disp = ax7.scatter(df['max_disp_x_m']*1000, df['max_disp_y_m']*1000,
                                    df['max_disp_z_m']*1000,
                                    c=df['max_displacement_mm'], cmap='viridis', s=150,
                                    edgecolors='black', linewidth=0.5, alpha=0.8)
        ax7.set_xlabel('X (mm)', fontsize=11, fontweight='bold')
        ax7.set_ylabel('Y (mm)', fontsize=11, fontweight='bold')
        ax7.set_zlabel('Z (mm)', fontsize=11, fontweight='bold')
        ax7.set_title('Max Displacement Locations', fontsize=13, fontweight='bold', pad=10)
        cbar = plt.colorbar(scatter3d_disp, ax=ax7, shrink=0.6)
        cbar.set_label('Disp. (mm)', fontsize=10, fontweight='bold')
        
        # Plot 8: Summary Statistics Table
        ax8 = fig.add_subplot(gs[2, 1:])
        ax8.axis('tight')
        ax8.axis('off')
        
        summary_data = [
            ['Parameter', 'Minimum', 'Maximum', 'Average', 'Std Dev'],
            ['Force (N)', f'{df["force_n"].min():.2f}', f'{df["force_n"].max():.2f}', 
             f'{df["force_n"].mean():.2f}', f'{df["force_n"].std():.2f}'],
            ['Max Stress (MPa)', f'{df["max_stress_mpa"].min():.2f}', f'{df["max_stress_mpa"].max():.2f}',
             f'{df["max_stress_mpa"].mean():.2f}', f'{df["max_stress_mpa"].std():.2f}'],
            ['Avg Stress (MPa)', f'{df["avg_stress_mpa"].min():.2f}', f'{df["avg_stress_mpa"].max():.2f}',
             f'{df["avg_stress_mpa"].mean():.2f}', f'{df["avg_stress_mpa"].std():.2f}'],
            ['Max Disp. (mm)', f'{df["max_displacement_mm"].min():.4f}', f'{df["max_displacement_mm"].max():.4f}',
             f'{df["max_displacement_mm"].mean():.4f}', f'{df["max_displacement_mm"].std():.4f}'],
        ]
        
        table = ax8.table(cellText=summary_data, cellLoc='center', loc='center',
                         colWidths=[0.2, 0.2, 0.2, 0.2, 0.2])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1, 2.5)
        
        # Style header row
        for i in range(5):
            table[(0, i)].set_facecolor('#4CAF50')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Alternate row colors
        for i in range(1, len(summary_data)):
            for j in range(5):
                if i % 2 == 0:
                    table[(i, j)].set_facecolor('#f0f0f0')
        
        ax8.set_title('Summary Statistics', fontsize=13, fontweight='bold', pad=20)
        
        plt.savefig(output_path / 'comprehensive_parametric_analysis.png', 
                   dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  ✓ Comprehensive analysis plots saved")
        
        # Create individual comparison plots
        create_individual_comparison_plots(df, output_path)
        
    except Exception as e:
        print(f"  Warning: Could not create comprehensive plots: {e}")
        import traceback
        traceback.print_exc()

def create_individual_comparison_plots(df, output_path):
    """Create individual detailed comparison plots"""
    try:
        # Linearity Check Plot
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.plot(df['force_n'], df['max_stress_mpa'], 'o-', linewidth=2, markersize=10, label='Actual')
        
        # Linear fit
        z = np.polyfit(df['force_n'], df['max_stress_mpa'], 1)
        p = np.poly1d(z)
        ax.plot(df['force_n'], p(df['force_n']), '--', linewidth=2, label=f'Linear Fit (y={z[0]:.4f}x+{z[1]:.4f})')
        
        ax.set_xlabel('Applied Force (N)', fontsize=13, fontweight='bold')
        ax.set_ylabel('Maximum Stress (MPa)', fontsize=13, fontweight='bold')
        ax.set_title('Linearity Check: Force vs Stress Response', fontsize=15, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.4)
        
        plt.savefig(output_path / 'linearity_check.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Linearity check plot saved")
        
    except Exception as e:
        print(f"  Warning: Could not create comparison plots: {e}")

# ============================================================
# MESH CREATION IN MAPDL
# ============================================================

def create_structural_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes):
    """Create structural mesh in MAPDL"""
    mapdl.finish()
    mapdl.clear()
    mapdl.prep7()
    mapdl.units("SI")
    
    # Define structural element type
    mapdl.et(1, 285)  # SOLID285 - tetrahedral
    
    # Create nodes
    for node_id, coords in zip(node_tags, node_coords):
        mapdl.n(int(node_id), coords[0], coords[1], coords[2])
    
    # Create elements
    for tet in tet_nodes:
        mapdl.e(int(tet[0]), int(tet[1]), int(tet[2]), int(tet[3]))

# ============================================================
# SINGLE ANALYSIS RUN
# ============================================================

def run_single_structural_analysis(mapdl, node_tags, node_coords, tet_nodes, material_props, force):
    """Run single static structural analysis"""
    
    # Recreate mesh for each analysis
    create_structural_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes)
    
    # Material properties
    mapdl.mp("EX", 1, material_props['youngs_modulus'])
    mapdl.mp("NUXY", 1, material_props['poissons_ratio'])
    mapdl.mp("DENS", 1, material_props['density'])
    
    # Boundary conditions - Fixed at Z=0
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "ALL", 0)
    
    # Apply force at Z=0.05
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
    
    # Find maximum stress location
    max_stress_idx = np.argmax(stress)
    max_stress_node_id = node_tags[max_stress_idx]
    max_stress_coords = node_coords[max_stress_idx]
    
    # Find maximum displacement location
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

# ============================================================
# PARAMETRIC STUDY
# ============================================================

def run_structural_parametric_study(mapdl, node_tags, node_coords, tet_nodes, 
                                   param_min, param_max, param_steps, material):
    """Run parametric study varying force with comprehensive visualization"""
    
    print("\n" + "="*60)
    print("RUNNING STRUCTURAL PARAMETRIC STUDY")
    print("WITH COMPREHENSIVE VISUALIZATION")
    print("="*60)
    print(f"Force range: {param_min} - {param_max} N")
    print(f"Number of steps: {param_steps}")
    
    # Setup visualization directory
    output_path = setup_visualization_directory()
    print(f"Results directory: {output_path}")
    
    # Generate parameter values
    forces = np.linspace(param_min, param_max, param_steps)
    
    results_list = []
    stress_images = []
    displacement_images = []
    
    # Track first and last step for detailed visualization
    first_step = True
    last_step_index = len(forces)
    
    for i, force in enumerate(forces, 1):
        print(f"\n[{i}/{len(forces)}] Analyzing Force = {force:.1f} N...")
        
        try:
            results = run_single_structural_analysis(
                mapdl, node_tags, node_coords, tet_nodes, material, force
            )
            
            # Export contour plots for animation
            print("  Exporting contour plots...")
            
            stress_img = export_stress_plot(mapdl, output_path, 
                                           f'stress_step_{i:03d}.png', step_number=i)
            if stress_img:
                stress_images.append(stress_img)
                
            disp_img = export_displacement_plot(mapdl, output_path,
                                               f'displacement_step_{i:03d}.png', step_number=i)
            if disp_img:
                displacement_images.append(disp_img)
            
            # Export detailed visualizations for first and last steps
            if first_step or i == last_step_index:
                step_label = "first" if first_step else "last"
                print(f"  Exporting detailed {step_label} step visualizations...")
                
                # Stress components
                export_stress_components(mapdl, output_path, f"stress_components_{step_label}")
                
                # Displacement components
                export_displacement_components(mapdl, output_path, f"displacement_components_{step_label}")
                
                # Principal stresses
                export_principal_stresses(mapdl, output_path, f"principal_stress_{step_label}")
                
                # Deformed shape
                export_deformed_shape(mapdl, output_path, f"deformed_shape_{step_label}.png")
                
                first_step = False
            
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
            
            print(f"  ✓ Max Stress: {results['max_stress_mpa']:.2f} MPa at node {results['max_stress_node']}")
            print(f"  ✓ Max Displacement: {results['max_displacement_mm']:.4f} mm at node {results['max_disp_node']}")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            results_list.append({
                'run_number': i,
                'force_n': force,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
    
    # Create DataFrame
    df = pd.DataFrame(results_list)
    
    # Generate comprehensive visualizations
    print("\n" + "="*60)
    print("CREATING COMPREHENSIVE VISUALIZATIONS")
    print("="*60)
    
    # Only create plots if we have valid results
    if not df.empty and 'max_stress_mpa' in df.columns and df['max_stress_mpa'].notna().sum() > 0:
        # Create comprehensive parametric analysis plots
        create_comprehensive_parametric_plots(df, output_path)
    else:
        print("  ⚠ No valid results to visualize")
    
    # Create animations
    if stress_images:
        print("\nCreating stress evolution animation...")
        create_results_animation(stress_images, output_path, 'stress_evolution.gif', duration=300)
    
    if displacement_images:
        print("Creating displacement evolution animation...")
        create_results_animation(displacement_images, output_path, 'displacement_evolution.gif', duration=300)
    
    # Save to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = output_path / f"structural_force_study_{timestamp}.xlsx"
    
    print("\n" + "="*60)
    print("SAVING RESULTS TO EXCEL")
    print("="*60)
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Results sheet
        df.to_excel(writer, sheet_name='Results', index=False)
        
        # Summary statistics
        summary = pd.DataFrame({
            'Parameter': ['Force (N)'],
            'Min': [param_min],
            'Max': [param_max],
            'Steps': [param_steps],
            'Total Runs': [len(results_list)],
            'Successful': [df['max_stress_mpa'].notna().sum()],
            'Failed': [df['max_stress_mpa'].isna().sum()],
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Material properties
        mat_df = pd.DataFrame([
            {'Property': 'Young\'s Modulus (Pa)', 'Value': material['youngs_modulus']},
            {'Property': 'Poisson\'s Ratio', 'Value': material['poissons_ratio']},
            {'Property': 'Density (kg/m³)', 'Value': material['density']},
        ])
        mat_df.to_excel(writer, sheet_name='Material', index=False)
        
        # Detailed Results with Statistics
        if 'max_stress_mpa' in df.columns and df['max_stress_mpa'].notna().sum() > 0:
            stats_df = pd.DataFrame({
                'Metric': ['Maximum Stress (MPa)', 'Average Stress (MPa)', 'Maximum Displacement (mm)'],
                'Min': [df['max_stress_mpa'].min(), df['avg_stress_mpa'].min(), df['max_displacement_mm'].min()],
                'Max': [df['max_stress_mpa'].max(), df['avg_stress_mpa'].max(), df['max_displacement_mm'].max()],
                'Mean': [df['max_stress_mpa'].mean(), df['avg_stress_mpa'].mean(), df['max_displacement_mm'].mean()],
                'Std Dev': [df['max_stress_mpa'].std(), df['avg_stress_mpa'].std(), df['max_displacement_mm'].std()],
            })
            stats_df.to_excel(writer, sheet_name='Statistics', index=False)
    
    print(f"✓ Excel results: {excel_filename.name}")
    print(f"✓ All visualizations: {output_path}")
    
    # Print summary of outputs
    print("\n" + "="*60)
    print("OUTPUT SUMMARY")
    print("="*60)
    print(f"📊 Comprehensive Analysis Plot: comprehensive_parametric_analysis.png")
    print(f"📈 Linearity Check: linearity_check.png")
    print(f"🎬 Stress Animation: stress_evolution.gif")
    print(f"🎬 Displacement Animation: displacement_evolution.gif")
    print(f"📐 Stress Components (First/Last): stress_components_*.png")
    print(f"📐 Displacement Components (First/Last): displacement_components_*.png")
    print(f"📐 Principal Stresses (First/Last): principal_stress_*.png")
    print(f"🔧 Deformed Shapes (First/Last): deformed_shape_*.png")
    print(f"📑 Excel Report: {excel_filename.name}")
    print("="*60)
    
    return df, str(excel_filename)

# ============================================================
# REGISTER THIS ANALYSIS TYPE
# ============================================================

STRUCTURAL_CONFIG['function'] = run_structural_parametric_study
register_analysis('1', STRUCTURAL_CONFIG)