"""
analysis_config.py - Configuration Registry for All Analysis Types
===================================================================
Defines what inputs each analysis type requires
"""

# This will be populated after analysis modules are imported
ANALYSIS_REGISTRY = {}

def register_analysis(key, config):
    """Register an analysis type with its configuration"""
    ANALYSIS_REGISTRY[key] = config

# ============================================================
# STRUCTURAL ANALYSIS CONFIGURATION
# ============================================================

STRUCTURAL_CONFIG = {
    'name': 'Static Structural Analysis - Force Variation',
    'parameter_name': 'Force',
    'parameter_unit': 'N',
    'param_min_default': 100,
    'param_max_default': 1000,
    'param_steps_default': 10,
    'material_properties': {
        'youngs_modulus': {
            'name': "Young's Modulus",
            'unit': 'Pa',
            'default': 200e9
        },
        'poissons_ratio': {
            'name': "Poisson's Ratio",
            'unit': '-',
            'default': 0.3
        },
        'density': {
            'name': 'Density',
            'unit': 'kg/m³',
            'default': 7850
        }
    }
}

# ============================================================
# THERMAL ANALYSIS CONFIGURATION
# ============================================================

THERMAL_CONFIG = {
    'name': 'Thermal Analysis - Heat Flux Variation',
    'parameter_name': 'Heat Flux',
    'parameter_unit': 'W/m²',
    'param_min_default': 500,
    'param_max_default': 5000,
    'param_steps_default': 10,
    'material_properties': {
        'thermal_conductivity': {
            'name': 'Thermal Conductivity',
            'unit': 'W/m·K',
            'default': 60.5
        },
        'specific_heat': {
            'name': 'Specific Heat',
            'unit': 'J/kg·K',
            'default': 434
        },
        'density': {
            'name': 'Density',
            'unit': 'kg/m³',
            'default': 7850
        }
    }
}