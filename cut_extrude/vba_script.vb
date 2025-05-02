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

    ' Select front plane and create sketch
    swModel.Extension.SelectByID2 "Front Plane", "PLANE", 0, 0, 0, False, 0, Nothing, 0
    swSketchMgr.InsertSketch True

    swSketchMgr.CreateLine 0.0, 0.0, 0, 40.0, 0.0, 0
    swSketchMgr.CreateLine 40.0, 0.0, 0, 40.0, 60.0, 0
    swSketchMgr.CreateLine 40.0, 60.0, 0, 0.0, 60.0, 0
    swSketchMgr.CreateLine 0.0, 60.0, 0, 0.0, 0.0, 0
    swSketchMgr.CreateLine 5.0, 15.0, 0, 35.0, 15.0, 0
    swSketchMgr.CreateLine 35.0, 15.0, 0, 35.0, 45.0, 0
    swSketchMgr.CreateLine 35.0, 45.0, 0, 5.0, 45.0, 0
    swSketchMgr.CreateLine 5.0, 45.0, 0, 5.0, 15.0, 0

    ' Exit sketch
    swModel.InsertSketch2 True

    ' Create extrusion from sketch
    swFeatureMgr.FeatureExtrusion2 _
        True, False, False, 0, 0, 100.0, 0.01, _
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