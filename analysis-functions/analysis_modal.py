"""
analysis_modal.py - Modal Analysis Module
==========================================
Handles natural frequency extraction with mode shape visualization
and comprehensive plotting
"""

import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from PIL import Image
from analysis_config import MODAL_CONFIG, register_analysis


def setup_visualization_directory():
    """Create output directory for images and animations"""
    output_path = Path.cwd() / "modal_results"
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


def export_mode_shape_plot(mapdl, result, mode_number, output_path, filename):
    """
    Export mode shape visualization
    
    Args:
        mapdl: MAPDL instance
        result: Result object
        mode_number: Mode number to plot (1-indexed)
        output_path: Path to save images
        filename: Name of the output file
    
    Returns:
        Path to saved image or None
    """
    try:
        # Get maximum displacement for normalization
        disp = result.nodal_displacement(mode_number - 1)[1]
        max_disp = np.abs(disp).max()
        
        if max_disp > 0:
            normalize_factor = 1.0 / max_disp
        else:
            normalize_factor = 1.0
        
        # Plot the mode shape
        image_path = output_path / filename
        
        result.plot_nodal_displacement(
            mode_number,
            show_displacement=True,
            displacement_factor=normalize_factor,
            n_colors=10,
            screenshot=str(image_path),
            off_screen=True
        )
        
        if image_path.exists():
            return image_path
        else:
            print(f"  Warning: Mode shape image not created: {image_path}")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not export mode shape for mode {mode_number}: {e}")
        return None


def create_mode_animation(result, mode_number, output_path, filename, normalize_factor=1.0):
    """
    Create animated GIF of mode shape
    
    Args:
        result: Result object
        mode_number: Mode number to animate (1-indexed)
        output_path: Path to save animation
        filename: Name of output GIF file
        normalize_factor: Displacement normalization factor
    
    Returns:
        Path to GIF file or None
    """
    try:
        gif_path = output_path / filename
        
        result.animate_nodal_displacement(
            mode_number,
            loop=False,
            add_text=False,
            n_frames=50,
            displacement_factor=normalize_factor,
            show_axes=False,
            background="w",
            movie_filename=str(gif_path),
            off_screen=True
        )
        
        if gif_path.exists():
            print(f"  ✓ Animation created: {filename}")
            return gif_path
        else:
            print(f"  Warning: Animation not created: {filename}")
            return None
        
    except Exception as e:
        print(f"  Warning: Could not create animation for mode {mode_number}: {e}")
        return None


def create_frequency_plots(df, output_path):
    """
    Create comprehensive frequency analysis plots
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    
    Returns:
        Path to saved plot or None
    """
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Modal Analysis Results - Natural Frequencies', 
                     fontsize=20, fontweight='bold')
        
        # Get all unique mode numbers and frequencies
        all_modes = []
        all_freqs = []
        
        for _, row in df.iterrows():
            for i in range(1, 21):  # Max 20 modes
                mode_col = f'mode_{i}_freq_hz'
                if mode_col in df.columns and pd.notna(row[mode_col]):
                    all_modes.append(i)
                    all_freqs.append(row[mode_col])
        
        if not all_modes:
            print("  Warning: No frequency data to plot")
            return None
        
        # Plot 1: Mode Number vs Frequency
        axes[0, 0].plot(all_modes, all_freqs, 'o-', linewidth=2.5, 
                       markersize=10, color='#1f77b4', 
                       markerfacecolor='white', markeredgewidth=2)
        axes[0, 0].set_xlabel('Mode Number', fontsize=13, fontweight='bold')
        axes[0, 0].set_ylabel('Frequency (Hz)', fontsize=13, fontweight='bold')
        axes[0, 0].set_title('Natural Frequencies by Mode', fontsize=15, fontweight='bold')
        axes[0, 0].grid(True, alpha=0.3, linestyle='--')
        
        # Plot 2: Frequency Distribution
        axes[0, 1].hist(all_freqs, bins=20, color='#ff7f0e', alpha=0.7, edgecolor='black')
        axes[0, 1].set_xlabel('Frequency (Hz)', fontsize=13, fontweight='bold')
        axes[0, 1].set_ylabel('Count', fontsize=13, fontweight='bold')
        axes[0, 1].set_title('Frequency Distribution', fontsize=15, fontweight='bold')
        axes[0, 1].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Plot 3: Frequency Spacing (difference between consecutive modes)
        if len(all_freqs) > 1:
            freq_spacing = np.diff(sorted(all_freqs))
            mode_pairs = [f"{i}-{i+1}" for i in range(1, len(freq_spacing)+1)]
            
            axes[1, 0].bar(range(len(freq_spacing)), freq_spacing, 
                          color='#2ca02c', alpha=0.7, edgecolor='black')
            axes[1, 0].set_xlabel('Mode Pair', fontsize=13, fontweight='bold')
            axes[1, 0].set_ylabel('Frequency Spacing (Hz)', fontsize=13, fontweight='bold')
            axes[1, 0].set_title('Frequency Spacing Between Consecutive Modes', 
                                fontsize=15, fontweight='bold')
            axes[1, 0].grid(True, alpha=0.3, linestyle='--', axis='y')
        
        # Plot 4: Summary Statistics Table
        axes[1, 1].axis('off')
        summary_data = [
            ['Statistic', 'Value'],
            ['Total Modes Analyzed', f"{len(all_modes)}"],
            ['Minimum Frequency', f"{min(all_freqs):.2f} Hz"],
            ['Maximum Frequency', f"{max(all_freqs):.2f} Hz"],
            ['Mean Frequency', f"{np.mean(all_freqs):.2f} Hz"],
            ['Frequency Range', f"{max(all_freqs) - min(all_freqs):.2f} Hz"],
            ['First Mode (Fundamental)', f"{min(all_freqs):.2f} Hz"],
        ]
        
        table = axes[1, 1].table(cellText=summary_data, cellLoc='left',
                                loc='center', colWidths=[0.6, 0.4])
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
        
        axes[1, 1].set_title('Summary Statistics', fontsize=15, fontweight='bold', pad=20)
        
        plt.tight_layout()
        plot_path = output_path / 'modal_analysis_summary.png'
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Summary plots saved: {plot_path}")
        return plot_path
        
    except Exception as e:
        print(f"  Warning: Could not create frequency plots: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_individual_frequency_plot(df, output_path):
    """
    Create detailed individual frequency plot
    
    Args:
        df: DataFrame with results
        output_path: Directory to save plots
    """
    try:
        plt.style.use('seaborn-v0_8-darkgrid')
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Collect all frequencies
        all_modes = []
        all_freqs = []
        
        for _, row in df.iterrows():
            for i in range(1, 21):
                mode_col = f'mode_{i}_freq_hz'
                if mode_col in df.columns and pd.notna(row[mode_col]):
                    all_modes.append(i)
                    all_freqs.append(row[mode_col])
        
        if not all_modes:
            return
        
        ax.plot(all_modes, all_freqs, 'o-', linewidth=3, markersize=12, 
               color='#d62728', markerfacecolor='white', markeredgewidth=2.5,
               label='Natural Frequencies')
        
        # Add horizontal lines at key frequencies
        ax.axhline(y=min(all_freqs), color='green', linestyle='--', 
                  alpha=0.5, label=f'Fundamental: {min(all_freqs):.2f} Hz')
        
        ax.set_xlabel('Mode Number', fontsize=16, fontweight='bold')
        ax.set_ylabel('Natural Frequency (Hz)', fontsize=16, fontweight='bold')
        ax.set_title('Complete Modal Frequency Spectrum', 
                    fontsize=18, fontweight='bold', pad=20)
        ax.legend(fontsize=13, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--', linewidth=1.5)
        
        plt.tight_layout()
        plt.savefig(output_path / 'frequency_spectrum_detailed.png', 
                   dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"  ✓ Detailed frequency plot saved")
        
    except Exception as e:
        print(f"  Warning: Could not create detailed plot: {e}")


# ============================================================
# MESH CREATION IN MAPDL
# ============================================================

def create_modal_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes):
    """Create structural mesh in MAPDL for modal analysis"""
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

def run_single_modal_analysis(mapdl, node_tags, node_coords, tet_nodes, 
                              material_props, num_modes, run_number, 
                              output_path=None, create_images=True):
    """
    Run single modal analysis
    
    Args:
        mapdl: MAPDL instance
        node_tags: Node IDs
        node_coords: Node coordinates
        tet_nodes: Element connectivity
        material_props: Material properties dictionary
        num_modes: Number of modes to extract
        run_number: Current run number for file naming
        output_path: Path for saving images
        create_images: Whether to create mode shape images
    
    Returns:
        Dictionary with results
    """
    
    # Recreate mesh
    create_modal_mesh_in_mapdl(mapdl, node_tags, node_coords, tet_nodes)
    
    # Material properties
    mapdl.mp("EX", 1, material_props['youngs_modulus'])
    mapdl.mp("PRXY", 1, material_props['poissons_ratio'])
    mapdl.mp("DENS", 1, material_props['density'])
        
    # Boundary conditions - Fixed at Z=0
    mapdl.nsel("S", "LOC", "Z", 0)
    mapdl.d("ALL", "ALL", 0)
    mapdl.allsel()

    # Solve modal analysis
    mapdl.finish()
    mapdl.slashsolu()
    mapdl.antype("MODAL")
    mapdl.modopt("LANB", num_modes, 0, 200)
    mapdl.mxpand(num_modes, "", "", "YES")  # Expand mode shapes
    mapdl.solve()
    mapdl.finish()

    # Wait for solution to complete and check status
    print(f"    Checking solution status...")
    mapdl.post1()

    # Try to access result file - with error handling
    try:
        result = mapdl.result
        # Verify result file has data
        output = mapdl.set("LIST")
        print(f"    Solution completed successfully")
    except Exception as e:
        print(f"    Warning: Could not access result file: {e}")
        result = None
        
    # Extract frequencies using POST1
    frequencies = []
    for i in range(num_modes):
        try:
            mapdl.set(1, i+1)
            # Use POST1 command to get frequency
            freq = mapdl.post_processing.frequency
            if freq is not None and freq > 0:
                frequencies.append(freq)
            else:
                # Alternative method
                mapdl.run("*GET, freq_val, ACTIVE, 0, SET, FREQ")
                freq = mapdl.parameters['freq_val']
                frequencies.append(freq if freq > 0 else None)
        except Exception as e:
            print(f"    Warning: Could not extract frequency for mode {i+1}: {e}")
            frequencies.append(None)
        
    # Create visualizations for first few modes if requested
    mode_images = {}
    mode_animations = {}

    if create_images and output_path is not None:
        try:
            # Check if result file has displacement data
            test_disp = result.nodal_displacement(0)
            has_displacements = True
        except:
            has_displacements = False
            print(f"    Note: Result file doesn't contain displacement data for visualization")
        
        if has_displacements:
            # Create images and animations for first 5 modes or all if less than 5
            modes_to_visualize = min(5, num_modes)
            
            for mode_num in range(1, modes_to_visualize + 1):
                if mode_num > len(frequencies) or frequencies[mode_num-1] is None:
                    continue
                    
                print(f"    Creating visualization for mode {mode_num}...")
                
                # Get normalization factor
                try:
                    disp = result.nodal_displacement(mode_num - 1)[1]
                    max_disp = np.abs(disp).max()
                    normalize_factor = 1.0 / max_disp if max_disp > 0 else 1.0
                except:
                    normalize_factor = 1.0
                
                # Create mode shape image
                img_filename = f"run_{run_number:03d}_mode_{mode_num}_shape.png"
                img_path = export_mode_shape_plot(mapdl, result, mode_num, 
                                                output_path, img_filename)
                if img_path:
                    mode_images[mode_num] = img_path
                
                # Create animation
                anim_filename = f"run_{run_number:03d}_mode_{mode_num}_animation.gif"
                anim_path = create_mode_animation(result, mode_num, output_path, 
                                                anim_filename, normalize_factor)
                if anim_path:
                    mode_animations[mode_num] = anim_path
    
    # Build results dictionary
    results = {
        'num_modes': num_modes,
        'frequencies': frequencies,
        'mode_images': mode_images,
        'mode_animations': mode_animations
    }
    
    # Add individual mode frequencies to results
    for i, freq in enumerate(frequencies, 1):
        results[f'mode_{i}_freq_hz'] = freq
    
    return results


# ============================================================
# PARAMETRIC STUDY
# ============================================================

def run_modal_parametric_study(mapdl, node_tags, node_coords, tet_nodes,
                               param_min, param_max, param_steps, material):
    """
    Run parametric study varying number of modes extracted
    
    Args:
        mapdl: MAPDL instance
        node_tags: Node IDs from mesh
        node_coords: Node coordinates from mesh
        tet_nodes: Element connectivity from mesh
        param_min: Minimum number of modes
        param_max: Maximum number of modes
        param_steps: Number of steps
        material: Dictionary of material properties
    
    Returns:
        df: DataFrame with results
        excel_filename: Name of Excel file created
    """
    
    print("\n" + "="*60)
    print("RUNNING MODAL PARAMETRIC STUDY")
    print("="*60)
    print(f"Number of modes range: {param_min} - {param_max}")
    print(f"Number of steps: {param_steps}")
    
    # Setup visualization directory
    output_path = setup_visualization_directory()
    print(f"Output directory: {output_path}")
    
    # Generate parameter values (number of modes)
    mode_counts = np.linspace(param_min, param_max, param_steps, dtype=int)
    
    results_list = []
    
    for i, num_modes in enumerate(mode_counts, 1):
        print(f"\n[{i}/{len(mode_counts)}] Extracting {num_modes} modes...")
        
        try:
            results = run_single_modal_analysis(
                mapdl, node_tags, node_coords, tet_nodes, material, 
                int(num_modes), run_number=i, output_path=output_path, 
                create_images=True
            )
            
            # Build row for DataFrame
            row = {
                'run_number': i,
                'num_modes_requested': int(num_modes),
                'num_modes_found': len([f for f in results['frequencies'] if f is not None]),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            
            # Add individual mode frequencies
            for mode_num, freq in enumerate(results['frequencies'], 1):
                row[f'mode_{mode_num}_freq_hz'] = freq
            
            results_list.append(row)
            
            print(f"  ✓ Successfully extracted {row['num_modes_found']} modes")
            valid_freqs = [f for f in results['frequencies'] if f is not None]
            if valid_freqs:
                print(f"  ✓ Fundamental frequency: {valid_freqs[0]:.2f} Hz")
                if len(valid_freqs) > 1:
                    print(f"  ✓ Highest frequency: {valid_freqs[-1]:.2f} Hz")
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()
            results_list.append({
                'run_number': i,
                'num_modes_requested': int(num_modes),
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            })
    
    # Create DataFrame
    df = pd.DataFrame(results_list)
    
    # Create plots
    print("\n" + "="*60)
    print("CREATING VISUALIZATIONS")
    print("="*60)
    
    create_frequency_plots(df, output_path)
    create_individual_frequency_plot(df, output_path)
    
    # Save to Excel
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    excel_filename = output_path / f"modal_analysis_{timestamp}.xlsx"
    
    print("\n" + "="*60)
    print("SAVING RESULTS TO EXCEL")
    print("="*60)
    
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        # Results sheet
        df.to_excel(writer, sheet_name='Results', index=False)
        
        # Summary statistics
        summary = pd.DataFrame({
            'Parameter': ['Number of Modes'],
            'Min': [param_min],
            'Max': [param_max],
            'Steps': [param_steps],
            'Total Runs': [len(results_list)],
            'Successful': [df['num_modes_found'].notna().sum()],
            'Failed': [df['num_modes_found'].isna().sum()],
        })
        summary.to_excel(writer, sheet_name='Summary', index=False)
        
        # Material properties
        mat_df = pd.DataFrame([
            {'Property': "Young's Modulus (Pa)", 'Value': material['youngs_modulus']},
            {'Property': "Poisson's Ratio", 'Value': material['poissons_ratio']},
            {'Property': 'Density (kg/m³)', 'Value': material['density']},
        ])
        mat_df.to_excel(writer, sheet_name='Material', index=False)
        
        # Frequency summary - collect all unique frequencies
        all_frequencies = []
        for _, row in df.iterrows():
            for col in df.columns:
                if col.startswith('mode_') and col.endswith('_freq_hz'):
                    if pd.notna(row[col]):
                        mode_num = int(col.split('_')[1])
                        all_frequencies.append({
                            'Mode Number': mode_num,
                            'Frequency (Hz)': row[col],
                            'Run Number': row['run_number']
                        })
        
        if all_frequencies:
            freq_df = pd.DataFrame(all_frequencies)
            freq_df = freq_df.sort_values(['Mode Number', 'Frequency (Hz)'])
            freq_df.to_excel(writer, sheet_name='All Frequencies', index=False)
    
    print(f"✓ Results saved to: {excel_filename}")
    print(f"✓ All visualizations saved to: {output_path}")
    
    # Print summary of created files
    print("\n" + "="*60)
    print("OUTPUT SUMMARY")
    print("="*60)
    print("📊 Plots:")
    print("   • modal_analysis_summary.png - 4-panel comprehensive summary")
    print("   • frequency_spectrum_detailed.png - Detailed frequency spectrum")
    print("\n🎬 Mode Shape Visualizations:")
    print("   • Mode shape images for first 5 modes of each run")
    print("   • Mode shape animations (GIF) for first 5 modes of each run")
    print("\n📄 Data:")
    print(f"   • {excel_filename.name} - Complete results spreadsheet")
    print("   • All natural frequencies organized by mode number")
    print("="*60)
    
    return df, str(excel_filename)


# ============================================================
# REGISTER THIS ANALYSIS TYPE
# ============================================================

MODAL_CONFIG['function'] = run_modal_parametric_study
register_analysis('3', MODAL_CONFIG)