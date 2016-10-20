#############################################################################################
#$/path/to/Slicer.exe --no-main-window --python-script /path/to/BoneSegmentation.py 
#For mac
#/Applications/Slicer.app/Contents/MacOS/Slicer --no-main-window --python-script /Applications/Slicer.app/Contents/Extensions-24735/BoneSegmentation/BoneSegmentation.py
#############################################################################################

from __main__ import vtk, qt, ctk, slicer
import EditorLib

import SimpleITK as sitk
import sitkUtils
import numpy as np

import BoneSegmentation


#
# BoneSegmentation
#
class BoneSegmentation_Slicer:

    def __init__(self, parent):
        import string
        parent.title = "Carpal Bone Segmentation"
        parent.categories = ["Brent Modules"]
        parent.contributors = ["Brent Foster (UC Davis)"]
        parent.helpText = string.Template("Use this module to segment the eight carpal bones of the wrist. Input is a seed location defined by the user within each bone of interest. The Confidence Connected ITK Filter is then applied. ").substitute({
            'a': parent.slicerWikiUrl, 'b': slicer.app.majorVersion, 'c': slicer.app.minorVersion})
        parent.acknowledgementText = """
    Supported by NSF and NIH funding. Module implemented by Brent Foster.
    """
        self.parent = parent

class BoneSegmentation_SlicerWidget:
    def __init__(self, parent=None):
        self.parent = parent
        self.logic = None
        self.ImageNode = None

    def setup(self):
        frame = qt.QFrame()
        frameLayout = qt.QFormLayout()
        frame.setLayout(frameLayout)
        self.parent.layout().addWidget(frame)

        #
        # Input Volume Selector
        #
        self.inputVolumeSelectorLabel = qt.QLabel()
        self.inputVolumeSelectorLabel.setText("Input Volume: ")
        self.inputVolumeSelectorLabel.setToolTip(
            "Select the input volume to be segmented")
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputSelector.noneEnabled = False
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        frameLayout.addRow(
            self.inputVolumeSelectorLabel, self.inputSelector)
        self.inputSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputSelect)


        #
        # Output Volume Selector
        #
        self.outputVolumeSelectorLabel = qt.QLabel()
        self.outputVolumeSelectorLabel.setText("Output Volume: ")
        self.outputVolumeSelectorLabel.setToolTip(
            "Select the output volume to save to")
        self.outputSelector = slicer.qMRMLNodeComboBox()
        # self.outputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.outputSelector.nodeTypes = ["vtkMRMLLabelMapVolumeNode"]
        self.outputSelector.noneEnabled = False
        self.outputSelector.selectNodeUponCreation = True
        self.outputSelector.setMRMLScene(slicer.mrmlScene)
        frameLayout.addRow(
            self.outputVolumeSelectorLabel, self.outputSelector)
        # self.outputSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputSelect)







        #
        # Markup Selector
        #
        self.markupSelectorLabel = qt.QLabel()
        self.markupSelectorLabel.setText("Markup list: ")
        self.markupSelector = slicer.qMRMLNodeComboBox()
        self.markupSelector.nodeTypes = ("vtkMRMLMarkupsFiducialNode", "")
        self.markupSelector.noneEnabled = False
        self.markupSelector.baseName = "Seed List"
        self.markupSelector.selectNodeUponCreation = True
        self.markupSelector.setMRMLScene(slicer.mrmlScene)
        self.markupSelector.setToolTip("Pick the markup list of fiducial markers to use as initial points for the segmentation. (One marker for each object of interest)")
        frameLayout.addRow(self.markupSelectorLabel, self.markupSelector)
        self.markupSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onMarkupSelect)

        #
        # Level set threshold range slider
        #
        self.label = qt.QLabel()
        self.label.setText("Level Set Threshold Range: ")
        self.label.setToolTip(
            "Select the threshold range that the level set will slow down when near the max/min")
        self.thresholdInputSlider = ctk.ctkRangeWidget()
        self.thresholdInputSlider.minimum = 0
        self.thresholdInputSlider.maximum = 150
        self.thresholdInputSlider.minimumValue = 0
        self.thresholdInputSlider.maximumValue = 60
        self.thresholdInputSlider.connect('valuesChanged(double,double)', self.onthresholdInputSliderRelease)
        frameLayout.addRow(self.label, self.thresholdInputSlider)
        #Set default value
        self.LevelSetThresholds = (self.thresholdInputSlider.minimumValue, self.thresholdInputSlider.maximumValue)

        # #
        # # Level set maximum iterations slider
        # #
        # self.label = qt.QLabel()
        # self.label.setText("Level Set Maximum Iterations: ")
        # self.label.setToolTip(
        #     "Select the maximum number of iterations for the level set convergence")
        # self.MaxItsInputSlider = ctk.ctkSliderWidget()
        # self.MaxItsInputSlider.minimum = 1
        # self.MaxItsInputSlider.maximum = 2500
        # self.MaxItsInputSlider.value = 2000
        # self.MaxItsInputSlider.connect('valueChanged(double)', self.onMaxItsInputSliderChange)
        # frameLayout.addRow(self.label, self.MaxItsInputSlider)
        # #Set default value
        # self.MaxIts = self.MaxItsInputSlider.value
 
        # #
        # # Level set maximum RMS error slider
        # #        
        # self.label = qt.QLabel()
        # self.label.setText("Level Set Maximum RMS Error: ")
        # self.label.setToolTip(
        #     "Select the maximum root mean square error to determine convergence of the segmentation")
        # self.MaxRMSErrorInputSlider = ctk.ctkSliderWidget()
        # self.MaxRMSErrorInputSlider.minimum = 0.001
        # self.MaxRMSErrorInputSlider.maximum = 0.15
        # self.MaxRMSErrorInputSlider.value = 0.008
        # self.MaxRMSErrorInputSlider.singleStep = 0.001
        # self.MaxRMSErrorInputSlider.tickInterval = 0.001
        # self.MaxRMSErrorInputSlider.decimals = 3
        # self.MaxRMSErrorInputSlider.connect('valueChanged(double)', self.onMaxRMSErrorInputSliderChange)
        # frameLayout.addRow(self.label, self.MaxRMSErrorInputSlider)
        # #Set default value
        # self.MaxRMSError = self.MaxRMSErrorInputSlider.value


        #
        # Shape Detection Level set maximum Iterations
        #        
        self.label = qt.QLabel()
        self.label.setText("Shape Detection Level Set Maximum Iterations: ")
        self.label.setToolTip(
            "Select the maximum number of iterations for the shape detection level set convergence")
        self.ShapeMaxItsInputSlider = ctk.ctkSliderWidget()
        self.ShapeMaxItsInputSlider.minimum = 0
        self.ShapeMaxItsInputSlider.maximum = 2500
        self.ShapeMaxItsInputSlider.value = 1000
        self.ShapeMaxItsInputSlider.connect('valueChanged(double)', self.onShapeMaxItsInputSliderChange)
        frameLayout.addRow(self.label, self.ShapeMaxItsInputSlider)
        #Set default value
        self.ShapeMaxIts = self.ShapeMaxItsInputSlider.value


        #
        # Shape Detection Level set maximum RMS error slider
        #        
        self.label = qt.QLabel()
        self.label.setText("Shape Detection Level Set Maximum RMS Error: ")
        self.label.setToolTip(
            "Select the maximum root mean square error to determine convergence of the shape detection level set filter")
        self.ShapeMaxRMSErrorInputSlider = ctk.ctkSliderWidget()
        self.ShapeMaxRMSErrorInputSlider.minimum = 0.001
        self.ShapeMaxRMSErrorInputSlider.maximum = 0.15
        self.ShapeMaxRMSErrorInputSlider.value = 0.003
        self.ShapeMaxRMSErrorInputSlider.singleStep = 0.001
        self.ShapeMaxRMSErrorInputSlider.tickInterval = 0.001
        self.ShapeMaxRMSErrorInputSlider.decimals = 3
        self.ShapeMaxRMSErrorInputSlider.connect('valueChanged(double)', self.onShapeMaxRMSErrorInputSliderChange)
        frameLayout.addRow(self.label, self.ShapeMaxRMSErrorInputSlider)
        #Set default value
        self.ShapeMaxRMSError = self.ShapeMaxRMSErrorInputSlider.value




        #
        # Shape Detection Level set curvatuve scale
        #        
        self.label = qt.QLabel()
        self.label.setText("Shape Detection Level Set Curvature Scale: ")
        self.label.setToolTip(
            "Select the shape curvature scale (higher number causes more smoothing)")
        self.ShapeCurvatureScaleInputSlider = ctk.ctkSliderWidget()
        self.ShapeCurvatureScaleInputSlider.minimum = 0
        self.ShapeCurvatureScaleInputSlider.maximum = 3
        self.ShapeCurvatureScaleInputSlider.value = 1
        self.ShapeCurvatureScaleInputSlider.singleStep = 0.01
        self.ShapeCurvatureScaleInputSlider.tickInterval = 0.01
        self.ShapeCurvatureScaleInputSlider.decimals = 1
        self.ShapeCurvatureScaleInputSlider.connect('valueChanged(double)', self.onShapeCurvatureScaleInputSliderChange)
        frameLayout.addRow(self.label, self.ShapeCurvatureScaleInputSlider)
        #Set default value
        self.ShapeCurvatureScale = self.ShapeCurvatureScaleInputSlider.value


        #
        # Shape Detection Level set propagation scale
        #        
        self.label = qt.QLabel()
        self.label.setText("Shape Detection Level Set Propagation Scale: ")
        self.label.setToolTip(
            "Select the shape curvature scale (higher number causes more smoothing)")
        self.ShapePropagationScaleInputSlider = ctk.ctkSliderWidget()
        self.ShapePropagationScaleInputSlider.minimum = 0
        self.ShapePropagationScaleInputSlider.maximum = 5
        self.ShapePropagationScaleInputSlider.value = 4
        self.ShapePropagationScaleInputSlider.singleStep = 0.2
        self.ShapePropagationScaleInputSlider.tickInterval = 0.2
        self.ShapePropagationScaleInputSlider.decimals = 1
        self.ShapePropagationScaleInputSlider.connect('valueChanged(double)', self.onShapePropagationScaleInputSliderChange)
        frameLayout.addRow(self.label, self.ShapePropagationScaleInputSlider)
        #Set default value
        self.ShapePropagationScale = self.ShapePropagationScaleInputSlider.value

        #
        # Image Downsample Scale
        # 
        self.label = qt.QLabel()
        self.label.setText("Image Downsampling: ")
        self.label.setToolTip(
            "Select the amount of downsampling (larger downsampling will compute faster, but the accuracy may be slightly reduced)")
        self.NumScalingSlider = ctk.ctkSliderWidget()
        self.NumScalingSlider.minimum = 1
        self.NumScalingSlider.maximum = 5
        self.NumScalingSlider.value = 2
        self.NumScalingSlider.connect('valueChanged(double)', self.onNumScalingSliderChange)
        frameLayout.addRow(self.label, self.NumScalingSlider)
        #Set default value
        self.NumScaling = self.NumScalingSlider.value

       
        #
        # Compute button
        #
        self.computeButton = qt.QPushButton("Compute")
        self.computeButton.toolTip = "Compute the segmentation"
        frameLayout.addWidget(self.computeButton)
        self.UpdatecomputeButtonState()
        self.computeButton.connect('clicked()', self.onCompute)

    def onNumScalingSliderChange(self, newValue):
        self.NumScaling = newValue

    def onShapePropagationScaleInputSliderChange(self, newValue):
        self.ShapePropagationScale = newValue

    def onShapeCurvatureScaleInputSliderChange(self, newValue):
        self.ShapeCurvatureScale = newValue

    def onShapeMaxItsInputSliderChange(self, newValue):
        self.ShapeMaxIts = newValue

    def onShapeMaxRMSErrorInputSliderChange(self, newValue):
        self.ShapeMaxRMSError = newValue

    def onMaxRMSErrorInputSliderChange(self, newValue):
        self.MaxRMSError = newValue

    def onMaxItsInputSliderChange(self, newValue):
        self.MaxIts = newValue

    def onthresholdInputSliderRelease(self, newLowerThreshold, newUpperThreshold):
        self.LevelSetThresholds = (newLowerThreshold, newUpperThreshold)

    def onNumCPUChange(self, newValue):
        self.NumCPUs = newValue

    def UpdatecomputeButtonState(self):
        #Enable the 'Compute' button only if there is a selection to the input volume and markup list
        if not self.markupSelector.currentNode():
            self.computeButton.enabled = False
        elif self.inputSelector.currentNode():
            self.computeButton.enabled = True
        else:
            self.computeButton.enabled = False

    def onInputSelect(self, node):
        #Test to see if the Compute button should be enabled/disabled
        self.UpdatecomputeButtonState()
        # self.ImageNode = node

    def onMarkupSelect(self, node):
        #Test to see if the Compute button should be enabled/disabled
        self.UpdatecomputeButtonState()

    def onCompute(self):
        slicer.app.processEvents()



        # TEST TEST TEST 
        # Find the input image in Slicer and convert to a SimpleITK image type
        # imageID = self.inputSelector.currentNode()
        # image = sitkUtils.PullFromSlicer(imageID.GetName())

        import subprocess
        import numpy as np
        import json
        x = np.random.rand(2,2)

        from subprocess import Popen, PIPE


# import sys
# sys.path.insert(0, 'C:\Users\Brent\GitRepositories\BoneSegmentation\SlicerModule')
# import joblib_test
# reload(joblib_test)
# joblib_test.main(5)

        import os
        print(os.path.dirname(os.path.abspath(__file__)))
        print(os.getcwd())


        fullCmd ="python " + "C:\Users\Brent\GitRepositories\BoneSegmentation\SlicerModule\joblib_test.py " + json.dumps(x.tolist())
        proc = Popen(fullCmd, stdout=PIPE, shell=False)

        output = proc.communicate()[0]
        print('output')
        print(output)
        # print(subprocess.check_output(
        #     fullCmd, 
        #     shell = True, 
        #     stdin = subprocess.PIPE, 
        #     # stdout = subprocess.PIPE, 
        #     # stderr = subprocess.STDOUT,
        #     bufsize = 0
        # ))


        print('done!')






        # "python joblib_test.py json.dumps(x.tolist())"


        return 0

        # END TEST TEST TEST 











        # TODO: Consider adding a QProgressBar() if not too difficult
        # Make a list of all the seed point locations
        fidList = self.markupSelector.currentNode()
        numFids = fidList.GetNumberOfFiducials()
        seedPoints = []
        # Create a list of the fiducial markers from the 'Markup List' input
        for i in range(numFids):
            ras = [0,0,0]
            fidList.GetNthFiducialPosition(i,ras)
            seedPoints.append(ras)
        print(fidList)

        # Find the input image in Slicer and convert to a SimpleITK image type
        imageID = self.inputSelector.currentNode()
        image = sitkUtils.PullFromSlicer(imageID.GetName())

        # Slicer has the fiducial markers in physical coordinate space, but need to have the points in voxel space
        # Convert using a SimpleITk function   
        for i in range(numFids):
            seedPoints[i] = image.TransformPhysicalPointToContinuousIndex(seedPoints[i])

        # Initilize the two classes that are defined at the bottom of this file
        segmentationClass = BoneSegmentation.BoneSeg()
        multiHelper = Multiprocessor()
        #Parameters = [LevelSet Thresholds, LevelSet Iterations, Level Set Error, Shape Level Set Curvature, Shape Level Set Max Error, Shape Level Set Max Its, Shape LS Propagation Scale]
        # parameters = [self.LevelSetThresholds, self.MaxIts, self.MaxRMSError,self.ShapeCurvatureScale, self.ShapeMaxRMSError, self.ShapeMaxIts, self.ShapePropagationScale] #From the sliders above
        parameters = [self.LevelSetThresholds, self.ShapeCurvatureScale, self.ShapeMaxRMSError, self.ShapeMaxIts, self.ShapePropagationScale, self.NumScaling] #From the sliders above
       
        NumCPUs = 1
        # Segmentation = multiHelper.Execute(segmentationClass, seedPoints, image, parameters, NumCPUs, True)
        Segmentation = slicer.cli.run(multiHelper.Execute(segmentationClass, seedPoints, image, parameters, NumCPUs, True), None, parameters)

        print(Segmentation)

        # Segmentation = sitk.Cast(Segmentation, sitk.sitkLabelUInt8)



        # BinaryToLabelFilter = sitk.BinaryImageToLabelMapFilter()
        # BinaryToLabelFilter.SetInputForegroundValue(1)
        # LabelMapToLabelImageFilter = sitk.LabelMapToLabelImageFilter()

        # Segmentation = BinaryToLabelFilter.Execute(Segmentation)
        # Segmentation = LabelMapToLabelImageFilter.Execute(Segmentation)


        # print('done with LabelMapToLabelImageFilter')
        # print(Segmentation)

        # imageWriter = sitk.ImageFileWriter()
        # imageWriter.Execute(Segmentation, 'C:\Users\Brent\GitRepositories\BoneSegmentation\SlicerModule\segImg.nii', True)

        # Output options in Slicer = {0:'background', 1:'foreground', 2:'label'}
        imageID = self.outputSelector.currentNode()
        # sitkUtils.PushLabel(Segmentation, imageID.GetName(), overwrite=True)     
        sitkUtils.PushToSlicer(Segmentation, 'Segmentation', 1, overwrite=True) 

        # Find the output image in Slicer to save the segmentation to
        # imageID = self.outputSelector.currentNode()
        # image = sitkUtils.PushToSlicer(Segmentation, imageID.GetName(), 1, overwrite=True)



if __name__ == "__main__":
    # TODO: need a way to access and parse command line arguments
    # TODO: ideally command line args should handle --xml

    import sys
    print(sys.argv)

    slicelet = BoneSegmentationSlicelet()

#############################################################################################
###MULTIPROCESSOR HELPER CLASS###
#############################################################################################

class Multiprocessor(object):
    """Helper class for seperating a segmentation class (such as from SimpleITK) into
    several logical cores in parallel. Requires: SegmentationClass, Seed List, SimpleITK Image"""
    def __init__(self):
        self = self

    def Execute(self, segmentationClass, seedList, MRI_Image, parameters, numCPUS, verbose = False):
        self.segmentationClass = segmentationClass
        self.seedList = seedList
        self.MRI_Image = MRI_Image
        self.parameters = parameters
        self.numCPUS = numCPUS
        self.verbose = verbose #Print output text to terminal or not

        #Convert to voxel coordinates
        self.RoundSeedPoints() 

        #Create an empty segmentationLabel image
        nda = sitk.GetArrayFromImage(self.MRI_Image)
        nda = np.asarray(nda)
        nda = nda*0
        segmentationLabel = sitk.Cast(sitk.GetImageFromArray(nda), self.MRI_Image.GetPixelID())
        segmentationLabel.CopyInformation(self.MRI_Image)
      

        for x in range(len(seedList)):
            tempOutput = self.RunSegmentation(seedList[x])
            tempOutput = sitk.Cast(tempOutput, self.MRI_Image.GetPixelID())
            tempOutput.CopyInformation(self.MRI_Image)

            segmentationLabel = segmentationLabel + tempOutput

        # Convert segmentationArray back into an image
        # segmentationLabel = sitk.Cast(sitk.GetImageFromArray(self.segmentationArray), self.MRI_Image.GetPixelID())
        # segmentationLabel.CopyInformation(self.MRI_Image)
        # segmentationLabel = self.segmentationArray

        return segmentationLabel

    def RunSegmentation(self, SeedPoint):
        """ Function to be used with the Multiprocessor class (needs to be its own function 
            and not part of the same class to avoid the 'Pickle' type errors. """
        segmentationClass = BoneSegmentation.BoneSeg()

        # Change some parameters(s) of the segmentation class for the optimization
        #Parameters = [LevelSet Thresholds, LevelSet Iterations, Level Set Error, Shape Level Set Curvature, Shape Level Set Max Error, Shape Level Set Max Its]
        print(self.parameters)
        segmentationClass.SetLevelSetLowerThreshold(self.parameters[0][0])
        segmentationClass.SetLevelSetUpperThreshold(self.parameters[0][1])

        #Shape Detection Filter
        segmentationClass.SetShapeCurvatureScale(self.parameters[1])
        segmentationClass.SetShapeMaxRMSError(self.parameters[2])
        segmentationClass.SetShapeMaxIterations(self.parameters[3])
        segmentationClass.SetShapePropagationScale(self.parameters[4])
        segmentationClass.SetScalingFactor(self.parameters[5])


        segmentation = segmentationClass.Execute(self.MRI_Image,[SeedPoint])

        return segmentation

    def RoundSeedPoints(self):           
        seeds = []
        for i in range(0,len(self.seedList)): #Select which bone (or all of them) from the csv file
            #Convert from string to float
            # tempFloat = [float(self.seedList[i][0])/(-0.24), float(self.seedList[i][1])/(-0.24), float(self.seedList[i][2])/(0.29)]
            tempFloat = [float(self.seedList[i][0]), float(self.seedList[i][1]), float(self.seedList[i][2])]
            
            #Convert from physical units to voxel coordinates
            tempVoxelCoordinates = self.MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
            seeds.append(tempVoxelCoordinates)

        self.seedList = seeds
        return self




