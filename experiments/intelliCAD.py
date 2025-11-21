"""
IntelliCAD-FEA: AI-Assisted Automated Multi-Physics Analysis System
===================================================================

Installation:
pip install ansys-mapdl-core numpy pyvista matplotlib google-generativeai pillow reportlab

Requirements:
- ANSYS MAPDL installed
- Gemini API key (get from https://makersuite.google.com/app/apikey)
"""

import os
import sys
import time
import shutil
import traceback
import base64
import json
from datetime import datetime
from io import BytesIO

import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
from PIL import Image

from ansys.mapdl.core import launch_mapdl
from ansys.mapdl.core.plotting.theme import PyMAPDL_cmap

import google.generativeai as genai

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT


# ============================================================================
# INDUSTRY TEMPLATES
# ============================================================================

INDUSTRY_TEMPLATES = {
    'automotive': {
        'name': 'Automotive Components',
        'description': 'Brackets, mounts, suspension parts',
        'analyses': [
            {
                'type': 'static',
                'name': 'Static Structural Analysis',
                'element_type': 'SOLID186',
                'load_factor': 2.0,
                'material_props': ['EX', 'NUXY', 'DENS'],
                'results': ['stress', 'displacement'],
                'pass_criteria': 'stress < yield_strength / 2.5'
            },
            {
                'type': 'modal',
                'name': 'Vibration Analysis',
                'element_type': 'SOLID186',
                'num_modes': 10,
                'material_props': ['EX', 'NUXY', 'DENS'],
                'results': ['frequencies', 'mode_shapes'],
                'pass_criteria': 'first_frequency > 50 Hz'
            }
        ],
        'materials': {
            'Steel-AISI1020': {'ex': 2.0e11, 'nuxy': 0.29, 'dens': 7850, 'yield': 3.5e8},
            'Aluminum-6061': {'ex': 6.9e10, 'nuxy': 0.33, 'dens': 2700, 'yield': 2.76e8},
            'Steel-AISI4140': {'ex': 2.05e11, 'nuxy': 0.29, 'dens': 7850, 'yield': 4.15e8}
        }
    },
    
    'electronics': {
        'name': 'Electronics & Thermal Management',
        'description': 'Heat sinks, enclosures, PCB mounts',
        'analyses': [
            {
                'type': 'thermal',
                'name': 'Heat Dissipation Analysis',
                'element_type': 'SOLID90',
                'material_props': ['KXX', 'DENS', 'C'],
                'results': ['temperature'],
                'pass_criteria': 'max_temperature < 85°C'
            },
            {
                'type': 'thermal_structural',
                'name': 'Thermal Stress Analysis',
                'element_type': 'SOLID186',
                'material_props': ['EX', 'NUXY', 'DENS', 'ALPX', 'KXX'],
                'results': ['thermal_stress', 'displacement'],
                'pass_criteria': 'thermal_stress < yield_strength / 3'
            }
        ],
        'materials': {
            'Aluminum-6061': {'ex': 6.9e10, 'nuxy': 0.33, 'dens': 2700, 'yield': 2.76e8, 
                             'kxx': 167, 'c': 896, 'alpx': 23.6e-6},
            'Copper': {'ex': 1.2e11, 'nuxy': 0.34, 'dens': 8900, 'yield': 2.0e8,
                      'kxx': 385, 'c': 385, 'alpx': 17e-6},
            'Aluminum-7075': {'ex': 7.2e10, 'nuxy': 0.33, 'dens': 2810, 'yield': 5.03e8,
                            'kxx': 130, 'c': 960, 'alpx': 23.2e-6}
        }
    },
    
    'aerospace': {
        'name': 'Aerospace Structures',
        'description': 'Lightweight high-strength components',
        'analyses': [
            {
                'type': 'static',
                'name': 'Ultimate Load Analysis',
                'element_type': 'SOLID186',
                'load_factor': 1.5,
                'material_props': ['EX', 'NUXY', 'DENS'],
                'results': ['stress', 'displacement'],
                'pass_criteria': 'stress < ultimate_strength / 1.5'
            },
            {
                'type': 'modal',
                'name': 'Flutter Analysis',
                'element_type': 'SOLID186',
                'num_modes': 15,
                'material_props': ['EX', 'NUXY', 'DENS'],
                'results': ['frequencies', 'mode_shapes'],
                'pass_criteria': 'first_frequency > 100 Hz'
            }
        ],
        'materials': {
            'Aluminum-7075': {'ex': 7.2e10, 'nuxy': 0.33, 'dens': 2810, 'yield': 5.03e8, 'ultimate': 5.72e8},
            'Titanium-Ti6Al4V': {'ex': 1.14e11, 'nuxy': 0.34, 'dens': 4430, 'yield': 8.8e8, 'ultimate': 9.5e8},
            'Aluminum-2024': {'ex': 7.3e10, 'nuxy': 0.33, 'dens': 2780, 'yield': 3.24e8, 'ultimate': 4.69e8}
        }
    },
    
    'general': {
        'name': 'General Mechanical',
        'description': 'Standard mechanical components',
        'analyses': [
            {
                'type': 'static',
                'name': 'Static Structural Analysis',
                'element_type': 'SOLID186',
                'load_factor': 1.5,
                'material_props': ['EX', 'NUXY', 'DENS'],
                'results': ['stress', 'displacement'],
                'pass_criteria': 'stress < yield_strength / 2'
            },
            {
                'type': 'modal',
                'name': 'Natural Frequency Analysis',
                'element_type': 'SOLID186',
                'num_modes': 6,
                'material_props': ['EX', 'NUXY', 'DENS'],
                'results': ['frequencies', 'mode_shapes'],
                'pass_criteria': 'informational'
            }
        ],
        'materials': {
            'Steel-Structural': {'ex': 2.0e11, 'nuxy': 0.3, 'dens': 7850, 'yield': 2.5e8},
            'Aluminum-6061': {'ex': 6.9e10, 'nuxy': 0.33, 'dens': 2700, 'yield': 2.76e8},
            'Stainless-Steel-316': {'ex': 1.93e11, 'nuxy': 0.31, 'dens': 8000, 'yield': 2.9e8}
        }
    }
}


# ============================================================================
# GEMINI AI INTEGRATION
# ============================================================================

class GeminiAssistant:
    """AI assistant for part classification and analysis guidance"""
    
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def encode_image(self, image_path):
        """Encode image to base64 for API"""
        with open(image_path, 'rb') as f:
            return base64.b64encode(f.read()).decode()
    
    def classify_part(self, image_paths):
        """Classify part and suggest industry/analysis type"""
        
        # Load images
        images = [Image.open(path) for path in image_paths]
        
        prompt = """
        Analyze these images of a CAD part from multiple angles. Provide:
        
        1. PART TYPE: What kind of component is this? (bracket, heat sink, housing, shaft, etc.)
        2. INDUSTRY: Which industry most likely uses this? Choose ONE:
           - automotive (vehicles, brackets, mounts)
           - electronics (heat sinks, enclosures, thermal)
           - aerospace (lightweight structures, high-performance)
           - general (standard mechanical parts)
        3. KEY FEATURES: List important geometric features (holes, ribs, flat surfaces, etc.)
        4. FUNCTION GUESS: What do you think this part does?
        5. LOAD BEARING: Does it look like it carries mechanical loads or is it thermal management?
        
        Format your response as JSON:
        {
            "part_type": "...",
            "industry": "automotive|electronics|aerospace|general",
            "confidence": 0.0-1.0,
            "key_features": ["feature1", "feature2"],
            "function": "...",
            "load_type": "mechanical|thermal|both"
        }
        """
        
        try:
            response = self.model.generate_content([prompt] + images)
            # Extract JSON from response
            text = response.text
            # Try to find JSON in the response
            if '{' in text and '}' in text:
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_str = text[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                # Fallback parsing
                return {
                    'part_type': 'unknown',
                    'industry': 'general',
                    'confidence': 0.5,
                    'key_features': ['Not detected'],
                    'function': text[:200],
                    'load_type': 'mechanical'
                }
        except Exception as e:
            print(f"Gemini classification error: {e}")
            return {
                'part_type': 'unknown',
                'industry': 'general',
                'confidence': 0.0,
                'key_features': ['Error'],
                'function': 'Classification failed',
                'load_type': 'mechanical'
            }
    
    def suggest_boundary_conditions(self, image_paths, area_list):
        """Suggest which faces to fix and load based on geometry"""
        
        images = [Image.open(path) for path in image_paths]
        
        prompt = f"""
        This is a mechanical part with numbered areas/faces. Available area numbers: {area_list}
        
        Analyze the geometry and suggest:
        1. Which area(s) should be FIXED (constrained)?
           - Look for: mounting holes, bolt holes, flat mounting surfaces
           - These typically have small circular features or flat bases
        
        2. Which area(s) should have LOADS applied?
           - Look for: large flat surfaces away from mounting points
           - Surfaces that appear to be contact or application points
        
        3. Explain your reasoning for each suggestion
        
        Format as JSON:
        {{
            "fixed_areas": [area_numbers],
            "fixed_reasoning": "why these areas...",
            "loaded_areas": [area_numbers],
            "loaded_reasoning": "why these areas...",
            "confidence": 0.0-1.0
        }}
        """
        
        try:
            response = self.model.generate_content([prompt] + images)
            text = response.text
            
            if '{' in text and '}' in text:
                json_start = text.find('{')
                json_end = text.rfind('}') + 1
                json_str = text[json_start:json_end]
                result = json.loads(json_str)
                return result
            else:
                return {
                    'fixed_areas': [area_list[0] if area_list else 1],
                    'fixed_reasoning': 'Default first area',
                    'loaded_areas': [area_list[-1] if area_list else 2],
                    'loaded_reasoning': 'Default last area',
                    'confidence': 0.3
                }
        except Exception as e:
            print(f"Gemini BC suggestion error: {e}")
            return {
                'fixed_areas': [1],
                'fixed_reasoning': 'Error - using default',
                'loaded_areas': [2],
                'loaded_reasoning': 'Error - using default',
                'confidence': 0.0
            }
    
    def analyze_results(self, results_data, max_stress, max_displacement, material_yield):
        """Provide engineering interpretation of results"""
        
        safety_factor = material_yield / max_stress if max_stress > 0 else float('inf')
        
        prompt = f"""
        FEA Analysis Results:
        - Maximum von Mises Stress: {max_stress/1e6:.2f} MPa
        - Material Yield Strength: {material_yield/1e6:.2f} MPa
        - Safety Factor: {safety_factor:.2f}
        - Maximum Displacement: {max_displacement*1000:.3f} mm
        
        Provide a brief engineering assessment:
        1. Is the design SAFE or UNSAFE?
        2. Key concerns or observations
        3. Design recommendations (if any)
        
        Keep it concise (3-4 sentences).
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            if safety_factor > 2.0:
                return f"Design appears SAFE with safety factor of {safety_factor:.2f}. Stress levels are acceptable."
            else:
                return f"WARNING: Low safety factor of {safety_factor:.2f}. Consider design modifications."


# ============================================================================
# MAPDL AUTOMATION
# ============================================================================

class IntelliCADFEA:
    """Main automation class"""
    
    def __init__(self, ansys_path=None, gemini_key=None):
        self.mapdl = None
        self.gemini = GeminiAssistant(gemini_key) if gemini_key else None
        self.ansys_path = ansys_path or self.find_ansys()
        self.results = {}
        self.screenshots = []
        
    def find_ansys(self):
        """Find ANSYS installation"""
        possible_paths = [
            r"C:\Program Files\ANSYS Inc\ANSYS Student\v252\ansys\bin\winx64\ANSYS252.exe",
            r"C:\Program Files\ANSYS Inc\v252\ansys\bin\winx64\ANSYS252.exe",
            r"C:\Program Files\ANSYS Inc\ANSYS Student\v251\ansys\bin\winx64\ANSYS251.exe",
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def launch_mapdl(self):
        """Launch MAPDL session"""
        print("\n" + "="*60)
        print("LAUNCHING ANSYS MAPDL...")
        print("="*60)
        
        if not self.ansys_path:
            raise Exception("ANSYS executable not found!")
        
        print(f"Using: {self.ansys_path}")
        print("Please wait 30-60 seconds...")
        
        self.mapdl = launch_mapdl(exec_file=self.ansys_path)
        print("✓ ANSYS MAPDL launched successfully!\n")
    
    def import_step_file(self, step_file):
        """Import STEP file with multiple fallback methods"""
        print("\n" + "="*60)
        print("IMPORTING STEP FILE")
        print("="*60)
        print(f"File: {os.path.basename(step_file)}\n")
        
        self.mapdl.clear()
        self.mapdl.prep7()
        
        # Try import
        try:
            self.mapdl.aux15()
            
            # Normalize path
            file_path_normalized = step_file.replace('\\', '/')
            base_name = os.path.splitext(file_path_normalized)[0]
            
            # Set import options
            self.mapdl.run('IOPTN,IGES,NO')
            self.mapdl.run('IOPTN,MERGE,YES')
            self.mapdl.run('IOPTN,SOLID,YES')
            self.mapdl.run('IOPTN,SMALL,YES')
            
            # Try import
            print("Importing geometry...")
            self.mapdl.run(f'PARAIN,{base_name},,STEP', mute=False)
            
            self.mapdl.prep7()
            time.sleep(1)
            
            # Clean geometry
            self.mapdl.allsel()
            self.mapdl.nummrg('KP')
            self.mapdl.nummrg('LINE')
            self.mapdl.numcmp('ALL')
            
            # Check import
            num_vols = int(float(self.mapdl.get('_', 'VOLU', 0, 'COUNT')))
            num_areas = int(float(self.mapdl.get('_', 'AREA', 0, 'COUNT')))
            
            print(f"\n✓ Import successful!")
            print(f"  Volumes: {num_vols}")
            print(f"  Areas: {num_areas}")
            
            if num_vols == 0 and num_areas == 0:
                raise Exception("No geometry imported")
            
            return True
            
        except Exception as e:
            print(f"\n✗ Import failed: {e}")
            return False
    
    def capture_views(self, output_dir='temp_views'):
        """Capture multiple views of the model for AI analysis"""
        print("\nCapturing model views for AI analysis...")
        
        os.makedirs(output_dir, exist_ok=True)
        self.screenshots = []
        
        views = [
            ('iso', 'isometric'),
            ('front', 'front'),
            ('top', 'top'),
            ('right', 'right')
        ]
        
        for i, (view_name, view_type) in enumerate(views):
            try:
                img_path = os.path.join(output_dir, f'view_{i}_{view_name}.png')
                
                # Use PyVista to capture view
                grid = self.mapdl.mesh.grid if hasattr(self.mapdl, 'mesh') else None
                
                if grid:
                    plotter = pv.Plotter(off_screen=True, window_size=[800, 600])
                    plotter.add_mesh(grid, show_edges=True, color='lightblue')
                    plotter.camera_position = view_type
                    plotter.screenshot(img_path)
                    plotter.close()
                    
                    self.screenshots.append(img_path)
                    print(f"  ✓ Captured {view_name} view")
                
            except Exception as e:
                print(f"  ✗ Failed to capture {view_name}: {e}")
        
        return self.screenshots
    
    def get_area_list(self):
        """Get list of available area numbers"""
        try:
            self.mapdl.allsel()
            # Get area list
            output = self.mapdl.alist()
            # Parse area numbers from output
            # This is a simplified version
            num_areas = int(float(self.mapdl.get('_', 'AREA', 0, 'COUNT')))
            return list(range(1, num_areas + 1))
        except:
            return [1, 2, 3, 4, 5, 6]  # Default guess for cube
    
    def run_analysis_template(self, template_name, material_name, fixed_area, loaded_area, load_value):
        """Run all analyses in the template"""
        print("\n" + "="*60)
        print(f"RUNNING {template_name.upper()} ANALYSIS TEMPLATE")
        print("="*60)
        
        template = INDUSTRY_TEMPLATES[template_name]
        material = template['materials'][material_name]
        
        self.results = {
            'template': template_name,
            'material': material_name,
            'analyses': []
        }
        
        for analysis_config in template['analyses']:
            print(f"\n>>> Running: {analysis_config['name']}")
            
            result = self.run_single_analysis(
                analysis_config,
                material,
                fixed_area,
                loaded_area,
                load_value
            )
            
            self.results['analyses'].append(result)
        
        return self.results
    
    def run_single_analysis(self, config, material, fixed_area, loaded_area, load_value):
        """Run a single analysis"""
        
        analysis_type = config['type']
        
        try:
            # Setup
            self.mapdl.prep7()
            self.mapdl.et(1, config['element_type'])
            
            # Material properties
            if 'EX' in config['material_props']:
                self.mapdl.mp('EX', 1, material['ex'])
            if 'NUXY' in config['material_props']:
                self.mapdl.mp('NUXY', 1, material['nuxy'])
            if 'DENS' in config['material_props']:
                self.mapdl.mp('DENS', 1, material['dens'])
            if 'KXX' in config['material_props']:
                self.mapdl.mp('KXX', 1, material.get('kxx', 50))
            if 'C' in config['material_props']:
                self.mapdl.mp('C', 1, material.get('c', 500))
            if 'ALPX' in config['material_props']:
                self.mapdl.mp('ALPX', 1, material.get('alpx', 12e-6))
            
            # Mesh
            self.mapdl.esize(0.01)
            self.mapdl.allsel()
            self.mapdl.vmesh('ALL')
            
            # Boundary conditions
            self.mapdl.allsel()
            
            if analysis_type == 'static':
                self.mapdl.da(fixed_area, 'ALL', 0)
                self.mapdl.sfa(loaded_area, 1, 'PRES', load_value * config.get('load_factor', 1.0))
                
                self.mapdl.finish()
                self.mapdl.slashsolu()
                self.mapdl.antype('STATIC')
                self.mapdl.solve()
                self.mapdl.finish()
                
                # Post-process
                self.mapdl.post1()
                self.mapdl.set('LAST')
                
                max_stress = np.max(self.mapdl.post_processing.nodal_eqv_stress())
                max_disp = np.max(self.mapdl.post_processing.nodal_displacement('NORM'))
                
                return {
                    'type': 'static',
                    'name': config['name'],
                    'max_stress': max_stress,
                    'max_displacement': max_disp,
                    'status': 'completed'
                }
            
            elif analysis_type == 'modal':
                self.mapdl.da(fixed_area, 'ALL', 0)
                
                self.mapdl.finish()
                self.mapdl.slashsolu()
                self.mapdl.antype('MODAL')
                self.mapdl.modopt('LANB', config.get('num_modes', 6))
                self.mapdl.solve()
                self.mapdl.finish()
                
                # Get frequencies
                self.mapdl.post1()
                frequencies = []
                for i in range(1, config.get('num_modes', 6) + 1):
                    self.mapdl.set(1, i)
                    freq = self.mapdl.get('_', 'MODE', '', 'FREQ')
                    frequencies.append(freq)
                
                self.mapdl.set(1, 1)  # Set to first mode for visualization
                
                return {
                    'type': 'modal',
                    'name': config['name'],
                    'frequencies': frequencies,
                    'status': 'completed'
                }
            
            elif analysis_type == 'thermal':
                self.mapdl.da(fixed_area, 'TEMP', 25)  # Ambient temp
                self.mapdl.sfa(loaded_area, 1, 'HFLUX', load_value)  # Heat flux
                
                self.mapdl.finish()
                self.mapdl.slashsolu()
                self.mapdl.antype('STATIC')
                self.mapdl.solve()
                self.mapdl.finish()
                
                self.mapdl.post1()
                self.mapdl.set('LAST')
                
                max_temp = np.max(self.mapdl.post_processing.nodal_temperature())
                
                return {
                    'type': 'thermal',
                    'name': config['name'],
                    'max_temperature': max_temp,
                    'status': 'completed'
                }
        
        except Exception as e:
            print(f"✗ Analysis failed: {e}")
            return {
                'type': analysis_type,
                'name': config['name'],
                'status': 'failed',
                'error': str(e)
            }
    
    def generate_report(self, classification, bc_suggestions, ai_assessment):
        """Generate PDF report"""
        print("\n" + "="*60)
        print("GENERATING REPORT")
        print("="*60)
        
        filename = f"FEA_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        doc = SimpleDocTemplate(filename, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='darkblue',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        story.append(Paragraph("IntelliCAD-FEA Analysis Report", title_style))
        story.append(Spacer(1, 0.2*inch))
        
        # AI Classification
        story.append(Paragraph("AI Part Classification", styles['Heading2']))
        story.append(Paragraph(f"<b>Part Type:</b> {classification.get('part_type', 'Unknown')}", styles['Normal']))
        story.append(Paragraph(f"<b>Industry:</b> {classification.get('industry', 'general')}", styles['Normal']))
        story.append(Paragraph(f"<b>Confidence:</b> {classification.get('confidence', 0)*100:.0f}%", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Analysis Results
        story.append(Paragraph("Analysis Results", styles['Heading2']))
        
        for analysis in self.results.get('analyses', []):
            story.append(Paragraph(f"<b>{analysis['name']}</b>", styles['Heading3']))
            
            if analysis['type'] == 'static':
                story.append(Paragraph(
                    f"Maximum Stress: {analysis['max_stress']/1e6:.2f} MPa", 
                    styles['Normal']
                ))
                story.append(Paragraph(
                    f"Maximum Displacement: {analysis['max_displacement']*1000:.3f} mm", 
                    styles['Normal']
                ))
            elif analysis['type'] == 'modal':
                freq_text = ", ".join([f"{f:.2f} Hz" for f in analysis['frequencies'][:5]])
                story.append(Paragraph(
                    f"Natural Frequencies (first 5): {freq_text}", 
                    styles['Normal']
                ))
            elif analysis['type'] == 'thermal':
                story.append(Paragraph(
                    f"Maximum Temperature: {analysis['max_temperature']:.2f} °C", 
                    styles['Normal']
                ))
            
            story.append(Spacer(1, 0.2*inch))
        
        # AI Assessment
        story.append(Paragraph("Engineering Assessment (AI-Generated)", styles['Heading2']))
        story.append(Paragraph(ai_assessment, styles['Normal']))
        
        # Build PDF
        doc.build(story)
        print(f"\n✓ Report saved: {filename}")
        
        return filename


# ============================================================================
# MAIN PROGRAM
# ============================================================================

def main():
    print("\n" + "="*60)
    print("IntelliCAD-FEA: AI-Assisted Analysis System")
    print("="*60)
    
    # Get Gemini API key
    gemini_key = input("\nEnter Gemini API key (or press Enter to skip AI features): ").strip()
    if not gemini_key:
        print("⚠ Running without AI features")
        gemini_key = None
    
    # Initialize system
    system = IntelliCADFEA(gemini_key=gemini_key)
    
    try:
        # Launch MAPDL
        system.launch_mapdl()
        
        # Get STEP file
        step_file = input("\nEnter path to STEP file: ").strip().strip('"')
        if not os.path.exists(step_file):
            print("✗ File not found!")
            return
        
        # Import geometry
        if not system.import_step_file(step_file):
            print("✗ Failed to import geometry")
            return
        
        # Capture views for AI
        classification = None
        if system.gemini:
            screenshots = system.capture_views()
            if screenshots:
                print("\nAnalyzing with AI...")
                classification = system.gemini.classify_part(screenshots)
                
                print("\n" + "-"*60)
                print("AI CLASSIFICATION")
                print("-"*60)
                print(f"Part Type: {classification['part_type']}")
                print(f"Industry: {classification['industry']}")
                print(f"Confidence: {classification['confidence']*100:.0f}%")
                print(f"Function: {classification['function']}")
                print("-"*60)
        
        # Select industry template
        print("\nAvailable Industry Templates:")
        for i, (key, template) in enumerate(INDUSTRY_TEMPLATES.items(), 1):
            marker = " (AI Suggested)" if classification and classification['industry'] == key else ""
            print(f"{i}. {template['name']}{marker}")
        
        if classification:
            default_choice = list(INDUSTRY_TEMPLATES.keys()).index(classification['industry']) + 1
            choice = input(f"\nSelect template [default: {default_choice}]: ").strip() or str(default_choice)
        else:
            choice = input("\nSelect template: ").strip()
        
        template_keys = list(INDUSTRY_TEMPLATES.keys())
        selected_template = template_keys[int(choice) - 1]
        template = INDUSTRY_TEMPLATES[selected_template]
        
        print(f"\n✓ Selected: {template['name']}")
        
        # Select material
        print("\nAvailable Materials:")
        materials = list(template['materials'].keys())
        for i, mat in enumerate(materials, 1):
            print(f"{i}. {mat}")
        
        mat_choice = input(f"\nSelect material [default: 1]: ").strip() or "1"
        selected_material = materials[int(mat_choice) - 1]
        
        # Get area list
        area_list = system.get_area_list()
        print(f"\nAvailable areas: {area_list}")
        
        # AI boundary condition suggestions
        bc_suggestions = None
        if system.gemini and screenshots:
            print("\nGetting AI suggestions for boundary conditions...")
            bc_suggestions = system.gemini.suggest_boundary_conditions(screenshots, area_list)
            
            print("\n" + "-"*60)
            print("AI BOUNDARY CONDITION SUGGESTIONS")
            print("-"*60)
            print(f"Suggested Fixed Area: {bc_suggestions['fixed_areas']}")
            print(f"Reasoning: {bc_suggestions['fixed_reasoning']}")
            print(f"\nSuggested Load Area: {bc_suggestions['loaded_areas']}")
            print(f"Reasoning: {bc_suggestions['loaded_reasoning']}")
            print(f"Confidence: {bc_suggestions['confidence']*100:.0f}%")
            print("-"*60)
            
            fixed_default = bc_suggestions['fixed_areas'][0]
            loaded_default = bc_suggestions['loaded_areas'][0]
        else:
            fixed_default = area_list[0]
            loaded_default = area_list[-1]
        
        # Get boundary conditions
        fixed_area = int(input(f"\nEnter fixed area [default: {fixed_default}]: ") or str(fixed_default))
        loaded_area = int(input(f"Enter loaded area [default: {loaded_default}]: ") or str(loaded_default))
        load_value = float(input("Enter load value (N or W): "))
        
        # Run analyses
        results = system.run_analysis_template(
            selected_template,
            selected_material,
            fixed_area,
            loaded_area,
            load_value
        )
        
        print("\n" + "="*60)
        print("ANALYSIS COMPLETE")
        print("="*60)
        
        # AI assessment
        ai_assessment = ""
        if system.gemini and results['analyses']:
            static_result = next((r for r in results['analyses'] if r['type'] == 'static'), None)
            if static_result and static_result['status'] == 'completed':
                material_props = template['materials'][selected_material]
                ai_assessment = system.gemini.analyze_results(
                    static_result,
                    static_result['max_stress'],
                    static_result['max_displacement'],
                    material_props['yield']
                )
                
                print("\n" + "-"*60)
                print("AI ENGINEERING ASSESSMENT")
                print("-"*60)
                print(ai_assessment)
                print("-"*60)
        
        # Generate report
        generate = input("\nGenerate PDF report? (y/n) [default: y]: ").strip().lower() or 'y'
        if generate == 'y':
            system.generate_report(
                classification or {},
                bc_suggestions or {},
                ai_assessment
            )
        
        print("\n✓ All tasks completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        traceback.print_exc()
    finally:
        if system.mapdl:
            print("\nClosing ANSYS...")
            try:
                system.mapdl.exit()
            except:
                pass
        
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()