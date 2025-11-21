from flask import Flask, request, jsonify
import cv2
import numpy as np
import pytesseract
from flask_cors import CORS, cross_origin
import re
import json
import tempfile
import os
from werkzeug.utils import secure_filename
from typing import Dict, List, Tuple, Any, Optional

app = Flask(__name__)

# Configure pytesseract path (adjust based on your system)
# For Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# For Linux: pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

class DimensionExtractor:
    """
    Extract dimensions from cropped engineering drawing views and
    establish relationships between dimensions across views.
    """
    
    def __init__(self):
        """Initialize the extractor."""
        self.views = {}
        self.dimensions = {}
        self.matched_dimensions = {}
        
    def upload_views(self, files: Dict[str, Any]):
        """Process uploaded view images from Flask request."""
        if not files:
            raise ValueError("No files were uploaded")
        
        for view_type in ['top', 'front', 'side']:
            file_key = f'{view_type}_view'
            if file_key not in files:
                continue
                
            file = files[file_key]
            if file.filename == '':
                continue
                
            # Read image file
            filename = secure_filename(file.filename)
            file_bytes = file.read()
            image = cv2.imdecode(np.frombuffer(file_bytes, np.uint8), cv2.IMREAD_COLOR)
            
            # Store view
            self.views[f'{view_type.upper()}_VIEW'] = {
                'image': image,
                'filename': filename
            }
            
        return self.views
    
    def preprocess_image(self, image):
        """Preprocess image for better text detection."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Increase contrast
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Apply binary threshold
        _, binary = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        
        return gray, binary
    
    def extract_dimensions_from_view(self, view_type: str) -> Dict[str, float]:
        """
        Extract dimensions from a single view using OCR and dimension line detection.
        """
        if view_type not in self.views:
            print(f"View {view_type} not found")
            return {}
        
        view_image = self.views[view_type]['image']
        gray, binary = self.preprocess_image(view_image)
        
        # Extract text using OCR
        extracted_dimensions = {}
        
        # First try on the normal image with low threshold
        text_normal = pytesseract.image_to_string(gray)
        dimensions_normal = self._parse_dimensions_from_text(text_normal)
        
        # Try also on the binary image
        text_binary = pytesseract.image_to_string(binary)
        dimensions_binary = self._parse_dimensions_from_text(text_binary)
        
        # Try with different preprocessing
        # Resize for better OCR
        resized = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        text_resized = pytesseract.image_to_string(resized)
        dimensions_resized = self._parse_dimensions_from_text(text_resized)
        
        # Combine results from different methods
        all_dimensions = {**dimensions_normal, **dimensions_binary, **dimensions_resized}
        
        # If dimensions were found through OCR
        if all_dimensions:
            # Map dimensions to appropriate names based on view type
            if view_type == 'TOP_VIEW':
                if len(all_dimensions) >= 2:
                    # Try to determine which is width and which is depth
                    dim_keys = list(all_dimensions.keys())
                    extracted_dimensions['width'] = all_dimensions[dim_keys[0]]
                    extracted_dimensions['depth'] = all_dimensions[dim_keys[1]]
                    
                    # If there are more dimensions, add them as extras
                    for i, key in enumerate(dim_keys[2:], start=1):
                        extracted_dimensions[f'extra_{i}'] = all_dimensions[key]
                else:
                    # Just copy over whatever was found
                    extracted_dimensions = all_dimensions
            
            elif view_type == 'FRONT_VIEW':
                if len(all_dimensions) >= 2:
                    dim_keys = list(all_dimensions.keys())
                    extracted_dimensions['width'] = all_dimensions[dim_keys[0]]
                    extracted_dimensions['height'] = all_dimensions[dim_keys[1]]
                    
                    for i, key in enumerate(dim_keys[2:], start=1):
                        extracted_dimensions[f'extra_{i}'] = all_dimensions[key]
                else:
                    extracted_dimensions = all_dimensions
            
            elif view_type == 'SIDE_VIEW':
                if len(all_dimensions) >= 2:
                    dim_keys = list(all_dimensions.keys())
                    extracted_dimensions['depth'] = all_dimensions[dim_keys[0]]
                    extracted_dimensions['height'] = all_dimensions[dim_keys[1]]
                    
                    for i, key in enumerate(dim_keys[2:], start=1):
                        extracted_dimensions[f'extra_{i}'] = all_dimensions[key]
                else:
                    extracted_dimensions = all_dimensions
        
        # Find dimension lines to associate with values
        dimension_lines = self._detect_dimension_lines(binary)
        
        # Store the results
        self.dimensions[view_type] = {
            'extracted': extracted_dimensions,
            'dimension_lines': dimension_lines
        }
        
        return extracted_dimensions
    
    def _parse_dimensions_from_text(self, text: str) -> Dict[str, float]:
        """
        Parse dimension values from OCR text.
        """
        # Pattern to match common dimension formats (e.g., "100 mm", "100mm", "100")
        dimension_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(?:mm|cm|m)?', re.IGNORECASE)
        matches = dimension_pattern.findall(text)
        
        # Convert to float and map to positions
        dimensions = {}
        for i, match in enumerate(matches):
            if match:
                try:
                    value = float(match)
                    # Use dimension index as key initially
                    dimensions[f'dim_{i+1}'] = value
                except ValueError:
                    pass
        
        return dimensions
    
    def _detect_dimension_lines(self, binary_image):
        """
        Detect dimension lines in the binary image.
        """
        # Find lines using Hough transform
        lines = cv2.HoughLinesP(
            binary_image, 
            rho=1, 
            theta=np.pi/180, 
            threshold=50, 
            minLineLength=20, 
            maxLineGap=10
        )
        
        dimension_lines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                
                # Calculate line angle to separate horizontal and vertical lines
                angle = np.abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
                
                # Classify as horizontal, vertical, or diagonal
                if angle < 10 or angle > 170:  # Horizontal lines
                    line_type = 'horizontal'
                elif 80 < angle < 100:  # Vertical lines
                    line_type = 'vertical'
                else:
                    line_type = 'diagonal'
                
                dimension_lines.append({
                    'coords': (x1, y1, x2, y2),
                    'type': line_type,
                    'length': np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                })
        
        return dimension_lines
    
    def extract_all_dimensions(self):
        """Extract dimensions from all views."""
        for view_type in self.views:
            self.extract_dimensions_from_view(view_type)
        
        return self.dimensions
    
    def match_dimensions_across_views(self):
        """
        Match dimensions across different views based on standard engineering drawing
        relationships.
        """
        if not self.dimensions:
            print("No dimensions extracted yet")
            return {}
        
        matched = {
            'width': None,
            'height': None,
            'depth': None
        }
        
        # Extract standard dimensions from each view if available
        top_dims = self.dimensions.get('TOP_VIEW', {}).get('extracted', {})
        front_dims = self.dimensions.get('FRONT_VIEW', {}).get('extracted', {})
        side_dims = self.dimensions.get('SIDE_VIEW', {}).get('extracted', {})
        
        # Match width (should be consistent in TOP and FRONT views)
        if 'width' in top_dims and 'width' in front_dims:
            # Check if they're close (within 5%)
            top_width = top_dims['width']
            front_width = front_dims['width']
            
            if self._are_values_close(top_width, front_width):
                matched['width'] = (top_width + front_width) / 2  # Average them
            else:
                # If they differ significantly, prioritize one (e.g., top view)
                matched['width'] = top_width
                print(f"Warning: Width mismatch between TOP ({top_width}) and FRONT ({front_width}) views")
        elif 'width' in top_dims:
            matched['width'] = top_dims['width']
        elif 'width' in front_dims:
            matched['width'] = front_dims['width']
        
        # Match height (should be consistent in FRONT and SIDE views)
        if 'height' in front_dims and 'height' in side_dims:
            front_height = front_dims['height']
            side_height = side_dims['height']
            
            if self._are_values_close(front_height, side_height):
                matched['height'] = (front_height + side_height) / 2
            else:
                matched['height'] = front_height
                print(f"Warning: Height mismatch between FRONT ({front_height}) and SIDE ({side_height}) views")
        elif 'height' in front_dims:
            matched['height'] = front_dims['height']
        elif 'height' in side_dims:
            matched['height'] = side_dims['height']
        
        # Match depth (should be consistent in TOP and SIDE views)
        if 'depth' in top_dims and 'depth' in side_dims:
            top_depth = top_dims['depth']
            side_depth = side_dims['depth']
            
            if self._are_values_close(top_depth, side_depth):
                matched['depth'] = (top_depth + side_depth) / 2
            else:
                matched['depth'] = top_depth
                print(f"Warning: Depth mismatch between TOP ({top_depth}) and SIDE ({side_depth}) views")
        elif 'depth' in top_dims:
            matched['depth'] = top_dims['depth']
        elif 'depth' in side_dims:
            matched['depth'] = side_dims['depth']
        
        # Add any additional dimensions that might be important
        additional_dims = {}
        
        for view_type, view_dims in self.dimensions.items():
            for dim_name, value in view_dims.get('extracted', {}).items():
                if dim_name.startswith('extra_'):
                    additional_dims[f"{view_type}_{dim_name}"] = value
        
        matched['additional'] = additional_dims
        
        # Store the results
        self.matched_dimensions = matched
        
        return matched
    
    def _are_values_close(self, val1, val2, tolerance=0.05):
        """Check if two values are close within a tolerance."""
        if val1 == 0 or val2 == 0:
            return val1 == val2
        
        return abs(val1 - val2) / max(abs(val1), abs(val2)) <= tolerance
    
    def create_operations_structure(self):
        """
        Create a structure with the exact format requested.
        """
        # Use matched dimensions if available, otherwise use default values
        width = 100.0
        height = 100.0
        depth = 100.0
        
        if self.matched_dimensions:
            # Only use matched dimensions if they exist, otherwise keep defaults
            if self.matched_dimensions.get('width') is not None:
                width = self.matched_dimensions['width']
            if self.matched_dimensions.get('height') is not None:
                height = self.matched_dimensions['height']
            if self.matched_dimensions.get('depth') is not None:
                depth = self.matched_dimensions['depth']
        
        # Create the exact structure requested
        structure = {
            "root": {
                "type": "object3D",
                "operations": [
                    {
                        "type": "extrude",
                        "dimensions": {
                            "width": float(width),
                            "height": float(height),
                            "depth": float(depth)
                        },
                        "position": {"x": 0, "y": 0, "z": 0}
                    }
                ]
            }
        }
        
        return structure

@app.route('/extract-dimensions', methods=['POST'])
@cross_origin()
def extract_dimensions():
    """
    API endpoint to extract dimensions from uploaded engineering drawing views.
    Expected files in request:
    - top_view: Image file for top view
    - front_view: Image file for front view
    - side_view: Image file for side view
    """
    if 'top_view' not in request.files or 'front_view' not in request.files or 'side_view' not in request.files:
        return jsonify({"error": "Missing one or more required view images (top_view, front_view, side_view)"}), 400
    
    try:
        # Initialize the extractor
        extractor = DimensionExtractor()
        
        # Process uploaded files
        extractor.upload_views(request.files)
        
        # Extract dimensions from all views
        extractor.extract_all_dimensions()
        
        # Match dimensions across views
        matched = extractor.match_dimensions_across_views()
        
        # Create the operations structure
        result = extractor.create_operations_structure()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    



if __name__ == '__main__':
    app.run(debug=True, port=5001)