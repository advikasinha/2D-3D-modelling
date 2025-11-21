Option Explicit

Sub CreateModelFromJSON()
    Dim swApp As SldWorks.SldWorks
    Dim swModel As SldWorks.ModelDoc2
    Dim swSketchMgr As SldWorks.SketchManager
    Dim swFeatureMgr As SldWorks.FeatureManager

    ' Connect to SolidWorks
    Set swApp = Application.SldWorks

    ' Create new part
    Set swModel = swApp.NewPart()
    Set swFeatureMgr = swModel.FeatureManager
    Set swSketchMgr = swModel.SketchManager

    ' Draw basic extrusion
    Dim width As Double
    Dim height As Double
    Dim depth As Double
    width = 0.1
    height = 0.1
    depth = 0.1

    ' Select front plane and create sketch
    swModel.Extension.SelectByID2 "Front Plane", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swSketchMgr.InsertSketch True

    ' Draw rectangle (centered at 0.0, 0.0, 0.0)
    swSketchMgr.CreateCenterRectangle 0.0, 0.0, 0.0, 0.05, 0.05, 0.0

    ' Exit sketch
    swModel.InsertSketch2 True

    ' Create extrusion
    swFeatureMgr.FeatureExtrusion2 _
        True, False, False, 0, 0, 0.1, 0.01, _
        False, False, False, False, 0, 0, _
        False, False, False, False, True, True, True, _
        0, 0, False

    ' Select front plane and create sketch
    swModel.Extension.SelectByID2 "Front Plane", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swSketchMgr.InsertSketch True

    swSketchMgr.CreateLine 0.0, 0.0, 0, 0.1, 0.0, 0
    swSketchMgr.CreateLine 0.1, 0.0, 0, 0.1, 0.1, 0
    swSketchMgr.CreateLine 0.1, 0.1, 0, 0.0, 0.1, 0
    swSketchMgr.CreateLine 0.0, 0.1, 0, 0.0, 0.0, 0

    ' Exit sketch
    swModel.InsertSketch2 True

    ' Create extrusion from sketch
    swFeatureMgr.FeatureExtrusion2 _
        True, False, False, 0, 0, 0.1, 0.01, _
        False, False, False, False, 0, 0, _
        False, False, False, False, True, True, True, _
        0, 0, False

    ' Zoom to fit
    swModel.ViewZoomtofit2

    ' Clean up
    Set swSketchMgr = Nothing
    Set swFeatureMgr = Nothing
    Set swModel = Nothing
    Set swApp = Nothing

    MsgBox "Model created successfully!", vbInformation, "Done"
End Sub