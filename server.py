import pythoncom
import win32com.client
import threading
import os
import uuid
from flask import Flask, request, jsonify
from queue import Queue
import time
from flask import Flask, request, jsonify, render_template, send_file
import json
import io

app = Flask(__name__)

# Configuration - Adjust these for your environment
TEMP_DIR = "D:\\solidworks_macros"
SOLIDWORKS_VERSION = "29"  # 29 = 2021, 28 = 2020, etc.
STARTUP_TIMEOUT = 30  # seconds
MACRO_TIMEOUT = 60  # seconds

# Ensure temp directory exists
os.makedirs(TEMP_DIR, exist_ok=True)

class SOLIDWORKSController:
    def __init__(self):
        self.sw_app = None
        self.initialized = False
        self.error = None
        self.queue = Queue()
        self.thread = None
        self._start_controller()

    def _start_controller(self):
        """Start the SOLIDWORKS control thread"""
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

        # Wait for initialization to complete
        start_time = time.time()
        while not self.initialized and time.time() - start_time < STARTUP_TIMEOUT:
            time.sleep(0.1)

        if not self.initialized:
            self.error = self.error or "SOLIDWORKS initialization timed out"

    def _run(self):
        """Main thread function for SOLIDWORKS interaction"""
        try:
            pythoncom.CoInitialize()
            
            # Try both version-specific and generic ProgIDs
            prog_ids = [
                f"SldWorks.Application.{SOLIDWORKS_VERSION}",
                "SldWorks.Application"
            ]
            
            for prog_id in prog_ids:
                try:
                    print(f"Attempting to connect using ProgID: {prog_id}")
                    self.sw_app = win32com.client.Dispatch(prog_id)
                    self.sw_app.Visible = True
                    
                    # Verify connection by getting version
                    version = self.sw_app.RevisionNumber
                    print(f"Connected to SOLIDWORKS version: {version}")
                    self.initialized = True
                    break
                except Exception as e:
                    print(f"Failed with {prog_id}: {str(e)}")
                    continue

            if not self.initialized:
                self.error = "Failed to connect using all ProgID options"
                return

            # Process tasks from queue
            while True:
                task = self.queue.get()
                try:
                    task()
                except Exception as e:
                    print(f"Error executing task: {e}")

        except Exception as e:
            self.error = f"SOLIDWORKS thread failed: {str(e)}"
        finally:
            if self.sw_app:
                self.sw_app.ExitApp()
            pythoncom.CoUninitialize()

    def execute_macro(self, vba_code):
        """Execute VBA code in SOLIDWORKS"""
        if not self.initialized:
            raise Exception("SOLIDWORKS not initialized")

        response_queue = Queue()
        
        def task():
            try:
                # Create properly formatted macro file
                swp_content = f"""Attribute VB_Name = "RemoteMacro"
Sub Main()
    On Error Resume Next
    {vba_code}
    If Err.Number <> 0 Then
        MsgBox "Macro error: " & Err.Description
    End If
End Sub
"""
                # Save to temporary file
                macro_path = os.path.join(TEMP_DIR, f"macro_{uuid.uuid4().hex}.swp")
                with open(macro_path, 'w', encoding='utf-8') as f:
                    f.write(swp_content)

                # Execute macro
                result = self.sw_app.RunMacro(
                    macro_path.replace('/', '\\'), 
                    "RemoteMacro", 
                    "Main"
                )
                response_queue.put({"status": "success", "result": result})
            except Exception as e:
                response_queue.put({"status": "error", "message": str(e)})
            finally:
                # Clean up macro file
                try:
                    os.remove(macro_path)
                except:
                    pass

        self.queue.put(task)
        return response_queue.get(timeout=MACRO_TIMEOUT)

# Initialize SOLIDWORKS controller when module loads
print("Initializing SOLIDWORKS controller...")
sw_controller = SOLIDWORKSController()

@app.route('/execute-vba', methods=['POST'])
def execute_vba():
    if not sw_controller.initialized:
        return jsonify({
            "status": "error",
            "message": "SOLIDWORKS not available",
            "detail": sw_controller.error
        }), 500

    try:
        vba_code = request.json.get('vba_code')
        if not vba_code:
            return jsonify({"status": "error", "message": "No VBA code provided"}), 400
        
        result = sw_controller.execute_macro(vba_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    
def generate_vba_from_json(data):
    """
    Generates SolidWorks VBA script from JSON input
    Args:
        data (dict): Parsed JSON data containing shape definitions
    Returns:
        str: Generated VBA script
    """
    vba_script = """Option Explicit

Sub CreateShape()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2
    Dim swSketchMgr As SldWorks.SketchManager
    
    ' Connect to SolidWorks
    On Error Resume Next
    Set swApp = Application.SldWorks
    On Error GoTo 0
    If swApp Is Nothing Then
        MsgBox "SolidWorks is not running", vbExclamation, "Error"
        Exit Sub
    End If
    
    ' Create new part
    Set swModel = swApp.NewPart()
    If swModel Is Nothing Then
        MsgBox "Failed to create new part", vbExclamation, "Error"
        Exit Sub
    End If
    
    ' Set units to millimeters (converted to meters in API calls)
    swModel.SetUnits 0, 0, 6, False  ' swMM = 0, swUnitsDecimal = 0
    
    ' Initialize sketch manager
    Set swSketchMgr = swModel.SketchManager
"""
    
    operations = data.get("root", {}).get("operations", [])
    
    for op in operations:
        op_type = op.get("type", "").lower()
        
        if op_type == "extrude":
            dims = op.get("dimensions", {})
            width = dims.get("width", 100.0) / 1000  # mm to m
            height = dims.get("height", 100.0) / 1000
            depth = dims.get("depth", 100.0) / 1000
            pos = op.get("position", {"x": 0, "y": 0, "z": 0})
            
            vba_script += f"""
    ' Create extrusion sketch
    swModel.ClearSelection2 True
    swModel.SketchManager.InsertSketch True
    
    ' Draw center rectangle (Width: {width*1000}mm, Height: {height*1000}mm)
    swSketchMgr.CreateCenterRectangle {pos.get('x', 0)/1000}, {pos.get('y', 0)/1000}, 0, {width/2}, {height/2}, 0
    
    ' Exit sketch
    swModel.InsertSketch2 True
    
    ' Extrude to {depth*1000}mm depth
    swModel.FeatureManager.FeatureExtrusion2 _
        True, False, False, 0, 0, {depth}, 0.01, _
        False, False, False, False, 0, 0, _
        False, False, False, False, True, True, True, _
        0, 0, False
"""
        
        elif op_type == "sketch":
            contour = op.get("contour", [])
            extrude_depth = op.get("extrude", {}).get("depth", 0) / 1000
            
            vba_script += """
    ' Create sketch
    swModel.ClearSelection2 True
    swModel.SketchManager.InsertSketch True
"""
            
            for segment in contour:
                seg_type = segment.get("type", "").lower()
                start = segment.get("start", {"x": 0, "y": 0})
                end = segment.get("end", {"x": 0, "y": 0})
                
                if seg_type == "line":
                    vba_script += f"""
    ' Draw line from ({start.get('x', 0)}mm,{start.get('y', 0)}mm) to ({end.get('x', 0)}mm,{end.get('y', 0)}mm)
    swSketchMgr.CreateLine {start.get('x', 0)/1000}, {start.get('y', 0)/1000}, 0, {end.get('x', 0)/1000}, {end.get('y', 0)/1000}, 0
"""
            
            if extrude_depth > 0:
                vba_script += f"""
    ' Exit sketch
    swModel.InsertSketch2 True
    
    ' Extrude sketch to {extrude_depth*1000}mm
    swModel.FeatureManager.FeatureExtrusion2 _
        True, False, False, 0, 0, {extrude_depth}, 0.01, _
        False, False, False, False, 0, 0, _
        False, False, False, False, True, True, True, _
        0, 0, False
"""
    
    vba_script += """
    ' Zoom to fit
    swModel.ViewZoomtofit2
    
    ' Clean up
    Set swSketchMgr = Nothing
    Set swModel = Nothing
    Set swApp = Nothing
    
    MsgBox "Shape created successfully!", vbInformation, "Done"
End Sub
"""
    return vba_script

@app.route('/generate-vba', methods=['POST'])
def generate_vba():
    """
    Endpoint that accepts JSON and returns VBA script
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        vba_script = generate_vba_from_json(data)
        return jsonify({
            "status": "success",
            "vba_script": vba_script
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    



@app.route('/convert', methods=['POST'])
def convert_json_to_vba():
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        # Convert the JSON to VBA code
        vba_code = generate_vba_from_json(data)
        
        # Return the VBA code
        return jsonify({"vba_code": vba_code})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/convert-clean', methods=['POST'])
def convert_json_to_vba_clean():
    """Endpoint that returns VBA code without newline escape sequences"""
    try:
        # Get the JSON data from the request
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Get operation mode (optional parameter to select which operations to process)
        params = request.args
        operation_mode = params.get('mode', 'all')  # Default to 'all'
        
        # Convert the JSON to VBA code
        vba_code = generate_vba_from_json(data, operation_mode)
        
        # Return the raw VBA code without JSON wrapping
        return vba_code, 200, {'Content-Type': 'text/plain'}
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def generate_vba_from_json(data, operation_mode='all'):
    """
    Generate SolidWorks VBA code from the provided JSON data.
    operation_mode can be 'all', 'extrude_only', or 'sketch_only'
    """
    vba_code = []
    
    # Start with the standard headers and sub declaration
    vba_code.append("Option Explicit")
    vba_code.append("")
    vba_code.append("Sub CreateModelFromJSON()")
    vba_code.append("    Dim swApp As SldWorks.SldWorks")
    vba_code.append("    Dim swModel As SldWorks.ModelDoc2")
    vba_code.append("    Dim swSketchMgr As SldWorks.SketchManager")
    vba_code.append("    Dim swFeatureMgr As SldWorks.FeatureManager")
    vba_code.append("")
    vba_code.append("    ' Connect to SolidWorks")
    vba_code.append("    Set swApp = Application.SldWorks")
    vba_code.append("")
    vba_code.append("    ' Create new part")
    vba_code.append("    Set swModel = swApp.NewPart()")
    vba_code.append("    Set swFeatureMgr = swModel.FeatureManager")
    vba_code.append("    Set swSketchMgr = swModel.SketchManager")
    vba_code.append("")
    
    # Process the root object
    if "root" in data and "operations" in data["root"]:
        operations = data["root"]["operations"]
        
        # Filter operations based on operation_mode
        if operation_mode == 'extrude_only':
            operations = [op for op in operations if op["type"] == "extrude"]
        elif operation_mode == 'sketch_only':
            operations = [op for op in operations if op["type"] == "sketch"]
        # For 'all', keep all operations (default)
        
        # Process the filtered operations
        for operation in operations:
            vba_code.extend(process_operation(operation))
    
    # Add closing code
    vba_code.append("    ' Zoom to fit")
    vba_code.append("    swModel.ViewZoomtofit2")
    vba_code.append("")
    vba_code.append("    ' Clean up")
    vba_code.append("    Set swSketchMgr = Nothing")
    vba_code.append("    Set swFeatureMgr = Nothing")
    vba_code.append("    Set swModel = Nothing")
    vba_code.append("    Set swApp = Nothing")
    vba_code.append("")
    vba_code.append("    MsgBox \"Model created successfully!\", vbInformation, \"Done\"")
    vba_code.append("End Sub")
    
    # Join with CRLF line endings for proper VBA format
    return '\r\n'.join(vba_code)

def process_operation(operation):
    """
    Process a single operation from the JSON and generate the corresponding VBA code.
    """
    vba_lines = []
    
    if operation["type"] == "extrude":
        dimensions = operation["dimensions"]
        position = operation["position"]
        
        width = dimensions.get("width", 100.0) / 1000.0  # Convert to meters
        height = dimensions.get("height", 100.0) / 1000.0
        depth = dimensions.get("depth", 100.0) / 1000.0
        
        x = position.get("x", 0) / 1000.0
        y = position.get("y", 0) / 1000.0
        z = position.get("z", 0) / 1000.0
        
        vba_lines.append("    ' Draw basic extrusion")
        vba_lines.append("    Dim width As Double")
        vba_lines.append("    Dim height As Double")
        vba_lines.append("    Dim depth As Double")
        vba_lines.append(f"    width = {width}")
        vba_lines.append(f"    height = {height}")
        vba_lines.append(f"    depth = {depth}")
        vba_lines.append("")
        vba_lines.append("    ' Select front plane and create sketch")
        vba_lines.append("    swModel.Extension.SelectByID2 \"Front Plane\", \"PLANE\", 0, 0, 0, False, 0, Nothing, 0")
        vba_lines.append("    swSketchMgr.InsertSketch True")
        vba_lines.append("")
        
        # Calculate corner positions (centered)
        half_width = width / 2
        half_height = height / 2
        vba_lines.append(f"    ' Draw rectangle (centered at {x}, {y}, {z})")
        vba_lines.append(f"    swSketchMgr.CreateCenterRectangle {x}, {y}, {z}, {x + half_width}, {y + half_height}, {z}")
        vba_lines.append("")
        vba_lines.append("    ' Exit sketch")
        vba_lines.append("    swModel.InsertSketch2 True")
        vba_lines.append("")
        vba_lines.append("    ' Create extrusion")
        vba_lines.append("    swFeatureMgr.FeatureExtrusion2 _")
        vba_lines.append(f"        True, False, False, 0, 0, {depth}, 0.01, _")
        vba_lines.append("        False, False, False, False, 0, 0, _")
        vba_lines.append("        False, False, False, False, True, True, True, _")
        vba_lines.append("        0, 0, False")
        vba_lines.append("")
    
    elif operation["type"] == "sketch":
        vba_lines.append("    ' Select front plane and create sketch")
        vba_lines.append("    swModel.Extension.SelectByID2 \"Front Plane\", \"PLANE\", 0, 0, 0, False, 0, Nothing, 0")
        vba_lines.append("    swSketchMgr.InsertSketch True")
        vba_lines.append("")
        
        # Process sketch contour
        if "contour" in operation:
            prev_end = None
            
            for segment in operation["contour"]:
                if segment["type"] == "line":
                    start = segment["start"]
                    end = segment["end"]
                    
                    # Convert to meters
                    start_x = start["x"] / 1000.0
                    start_y = start["y"] / 1000.0
                    end_x = end["x"] / 1000.0
                    end_y = end["y"] / 1000.0
                    
                    vba_lines.append(f"    swSketchMgr.CreateLine {start_x}, {start_y}, 0, {end_x}, {end_y}, 0")
                    prev_end = end
            
            vba_lines.append("")
            vba_lines.append("    ' Exit sketch")
            vba_lines.append("    swModel.InsertSketch2 True")
            
            # Handle extrusion of the sketch if specified
            if "extrude" in operation:
                depth = operation["extrude"].get("depth", 100.0) / 1000.0  # Convert to meters
                
                vba_lines.append("")
                vba_lines.append("    ' Create extrusion from sketch")
                vba_lines.append("    swFeatureMgr.FeatureExtrusion2 _")
                vba_lines.append(f"        True, False, False, 0, 0, {depth}, 0.01, _")
                vba_lines.append("        False, False, False, False, 0, 0, _")
                vba_lines.append("        False, False, False, False, True, True, True, _")
                vba_lines.append("        0, 0, False")
                vba_lines.append("")
    
    return vba_lines

if __name__ == '__main__':
    if not sw_controller.initialized:
        print(f"Failed to initialize SOLIDWORKS: {sw_controller.error}")
    else:
        print("SOLIDWORKS controller ready")
    
    app.run(host='0.0.0.0', port=5000, debug=True)