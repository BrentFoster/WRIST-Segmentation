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
import multiprocessing
import timeit


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
        self.thresholdInputSlider.maximum = 250
        self.thresholdInputSlider.minimumValue = 0
        self.thresholdInputSlider.maximumValue = 90
        self.thresholdInputSlider.connect('valuesChanged(double,double)', self.onthresholdInputSliderRelease)
        frameLayout.addRow(self.label, self.thresholdInputSlider)
        #Set default value
        self.LevelSetThresholds = (self.thresholdInputSlider.minimumValue, self.thresholdInputSlider.maximumValue)

        #
        # Level set maximum iterations slider
        #
        self.label = qt.QLabel()
        self.label.setText("Level Set Maximum Iterations: ")
        self.label.setToolTip(
            "Select the maximum number of iterations for the level set convergence")
        self.MaxItsInputSlider = ctk.ctkSliderWidget()
        self.MaxItsInputSlider.minimum = 1
        self.MaxItsInputSlider.maximum = 2500
        self.MaxItsInputSlider.value = 2000
        self.MaxItsInputSlider.connect('valueChanged(double)', self.onMaxItsInputSliderChange)
        frameLayout.addRow(self.label, self.MaxItsInputSlider)
        #Set default value
        self.MaxIts = self.MaxItsInputSlider.value
 
        #
        # Level set maximum RMS error slider
        #        
        self.label = qt.QLabel()
        self.label.setText("Level Set Maximum RMS Error: ")
        self.label.setToolTip(
            "Select the maximum root mean square error to determine convergence of the segmentation")
        self.MaxRMSErrorInputSlider = ctk.ctkSliderWidget()
        self.MaxRMSErrorInputSlider.minimum = 0.001
        self.MaxRMSErrorInputSlider.maximum = 0.15
        self.MaxRMSErrorInputSlider.value = 0.008
        self.MaxRMSErrorInputSlider.singleStep = 0.001
        self.MaxRMSErrorInputSlider.tickInterval = 0.001
        self.MaxRMSErrorInputSlider.decimals = 3
        self.MaxRMSErrorInputSlider.connect('valueChanged(double)', self.onMaxRMSErrorInputSliderChange)
        frameLayout.addRow(self.label, self.MaxRMSErrorInputSlider)
        #Set default value
        self.MaxRMSError = self.MaxRMSErrorInputSlider.value


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
        self.ShapeMaxRMSErrorInputSlider.value = 0.008
        self.ShapeMaxRMSErrorInputSlider.singleStep = 0.001
        self.ShapeMaxRMSErrorInputSlider.tickInterval = 0.001
        self.ShapeMaxRMSErrorInputSlider.decimals = 3
        self.ShapeMaxRMSErrorInputSlider.connect('valueChanged(double)', self.onShapeMaxRMSErrorInputSliderChange)
        frameLayout.addRow(self.label, self.ShapeMaxRMSErrorInputSlider)
        #Set default value
        self.ShapeMaxRMSError = self.MaxRMSErrorInputSlider.value




        #
        # Shape Detection Level set curvatuve scale
        #        
        self.label = qt.QLabel()
        self.label.setText("Shape Detection Level Set Curvature Scale: ")
        self.label.setToolTip(
            "Select the shape curvature scale (higher number causes more smoothing)")
        self.ShapeCurvatureScaleInputSlider = ctk.ctkSliderWidget()
        self.ShapeCurvatureScaleInputSlider.minimum = 0
        self.ShapeCurvatureScaleInputSlider.maximum = 5
        self.ShapeCurvatureScaleInputSlider.value = 1
        self.ShapeCurvatureScaleInputSlider.singleStep = 0.2
        self.ShapeCurvatureScaleInputSlider.tickInterval = 0.2
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
        self.ShapePropagationScaleInputSlider.value = 1
        self.ShapePropagationScaleInputSlider.singleStep = 0.2
        self.ShapePropagationScaleInputSlider.tickInterval = 0.2
        self.ShapePropagationScaleInputSlider.decimals = 1
        self.ShapePropagationScaleInputSlider.connect('valueChanged(double)', self.onShapePropagationScaleInputSliderChange)
        frameLayout.addRow(self.label, self.ShapePropagationScaleInputSlider)
        #Set default value
        self.ShapePropagationScale = self.ShapePropagationScaleInputSlider.value

        #
        # Maximum number of CPUs slider
        # 
        self.label = qt.QLabel()
        self.label.setText("Number of CPUs To Use: ")
        self.label.setToolTip(
            "Select the maximum number of logical cores to use for parallel processing to speed up computation. Note: More RAM is needed for higher cores used")
        self.NumCPUInputSlider = ctk.ctkSliderWidget()
        num_CPUs = multiprocessing.cpu_count()
        self.NumCPUInputSlider.minimum = 1
        self.NumCPUInputSlider.maximum = num_CPUs
        self.NumCPUInputSlider.value = num_CPUs
        self.NumCPUInputSlider.connect('valueChanged(double)', self.onNumCPUChange)
        frameLayout.addRow(self.label, self.NumCPUInputSlider)
        #Set default value
        self.NumCPUs = self.NumCPUInputSlider.value
        
        #
        # Compute button
        #
        self.computeButton = qt.QPushButton("Compute")
        self.computeButton.toolTip = "Compute the segmentation"
        frameLayout.addWidget(self.computeButton)
        self.UpdatecomputeButtonState()
        self.computeButton.connect('clicked()', self.onCompute)

        # #
        # # Output Volume Label
        # #
        # self.outputVolumeSelectorLabel = qt.QLabel()
        # self.outputVolumeSelectorLabel.setText("Output Volume: ")
        # self.outputVolumeSelectorLabel.setToolTip(
        #     "Select the output volume to save the segmentation to")
        # self.outputSelector = slicer.qMRMLNodeComboBox()
        # self.outputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        # self.outputSelector.noneEnabled = True
        # self.outputSelector.selectNodeUponCreation = True
        # self.outputSelector.setMRMLScene(slicer.mrmlScene)
        # frameLayout.addRow(self.outputVolumeSelectorLabel, self.outputSelector)
        
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
        # TODO: Consider adding a QProgressBar() if not too difficult
        #Make a list of all the seed point locations
        fidList = self.markupSelector.currentNode()
        numFids = fidList.GetNumberOfFiducials()
        seedPoints = []
        #Create a list of the fiducial markers from the 'Markup List' input
        for i in range(numFids):
            ras = [0,0,0]
            fidList.GetNthFiducialPosition(i,ras)
            seedPoints.append(ras)
        print(fidList)

        #Find the input image in Slicer and convert to a SimpleITK image type
        imageID = self.inputSelector.currentNode()
        image = sitkUtils.PullFromSlicer(imageID.GetName())

        #Slicer has the fiducial markers in physical coordinate space, but need to have the points in voxel space
        #Convert using a SimpleITk function   
        for i in range(numFids):
            seedPoints[i] = image.TransformPhysicalPointToContinuousIndex(seedPoints[i])

        #Initilize the two classes that are defined at the bottom of this file
        segmentationClass = BoneSeg()
        multiHelper = Multiprocessor()
        #Parameters = [LevelSet Thresholds, LevelSet Iterations, Level Set Error, Shape Level Set Curvature, Shape Level Set Max Error, Shape Level Set Max Its, Shape LS Propagation Scale]
        parameters = [self.LevelSetThresholds, self.MaxIts, self.MaxRMSError,self.ShapeCurvatureScale, self.ShapeMaxRMSError, self.ShapeMaxIts, self.ShapePropagationScale] #From the sliders above
        NumCPUs = self.NumCPUs
        Segmentation = multiHelper.Execute(segmentationClass, seedPoints, image, parameters, NumCPUs, True)
        print(Segmentation)

        # Output options in Slicer = {0:'background', 1:'foreground', 2:'label'}
        sitkUtils.PushLabel(Segmentation,'Segmentation',overwrite=True)      

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
    """Helper class for sliptting a segmentation class (such as from SimpleITK) into
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



        #Convert segmentationArray back into an image
        # segmentationLabel = sitk.Cast(sitk.GetImageFromArray(self.segmentationArray), self.MRI_Image.GetPixelID())
        # segmentationLabel.CopyInformation(self.MRI_Image)
        # segmentationLabel = self.segmentationArray

        return segmentationLabel

    def RunSegmentation(self, SeedPoint):
        """ Function to be used with the Multiprocessor class (needs to be its own function 
            and not part of the same class to avoid the 'Pickle' type errors. """
        segmentationClass = BoneSeg()

        # Change some parameters(s) of the segmentation class for the optimization
        #Parameters = [LevelSet Thresholds, LevelSet Iterations, Level Set Error, Shape Level Set Curvature, Shape Level Set Max Error, Shape Level Set Max Its]
        print(self.parameters)
        segmentationClass.SetLevelSetLowerThreshold(self.parameters[0][0])
        segmentationClass.SetLevelSetUpperThreshold(self.parameters[0][1])
        segmentationClass.SetLevelSetIts(self.parameters[1])
        segmentationClass.SetLevelSetError(self.parameters[2])


        #Shape Detection Filter
        segmentationClass.SetShapeCurvatureScale(self.parameters[3])
        segmentationClass.SetShapeMaxRMSError(self.parameters[4])
        segmentationClass.SetShapeMaxIterations(self.parameters[5])
        segmentationClass.SetShapePropagationScale(self.parameters[6])



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

#############################################################################################
###SEGMENTATION CLASS###
#############################################################################################
class BoneSeg(object):
    """Class of BoneSegmentation. REQUIRED: BoneSeg(MRI_Image,SeedPoint)"""
    def __init__(self):
        self.ScalingFactor = []
        self.AnisotropicIts = []
        self.AnisotropicTimeStep = []
        self.AnisotropicConductance = []
        self.ConfidenceConnectedIts = []
        self.ConfidenceConnectedMultiplier = []
        self.ConfidenceConnectedRadius = []
        self.BinaryMorphologicalRadius = []
        self.MaxVolume = []
        self.SeedListFilename = [] 

        ##Initilize the ITK filters##
        #Filters to down/up sample the image for faster computation
        self.shrinkFilter = sitk.ShrinkImageFilter()
        self.expandFilter = sitk.ExpandImageFilter()
        #Filter to reduce noise while preserving edgdes
        self.anisotropicFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
        #Post-processing filters for fillinging holes and to attempt to remove any leakage areas
        self.dilateFilter = sitk.BinaryDilateImageFilter()
        self.erodeFilter = sitk.BinaryErodeImageFilter()
        self.fillFilter = sitk.BinaryFillholeImageFilter()  
        self.connectedComponentFilter = sitk.ScalarConnectedComponentImageFilter()
        self.laplacianFilter = sitk.LaplacianSegmentationLevelSetImageFilter()
        self.thresholdLevelSet = sitk.ThresholdSegmentationLevelSetImageFilter()

        #Initilize the SimpleITK Filters
        self.GradientMagnitudeFilter = sitk.GradientMagnitudeImageFilter()
        self.shapeDetectionFilter = sitk.ShapeDetectionLevelSetImageFilter()

        #Set the deafult values 
        self.SetDefaultValues()

    def SetDefaultValues(self):
        #Set the default values of all the parameters here
        self.SetScalingFactor([2,2,1]) #X,Y,Z

        # self.SetAnisotropicIts(5)
        # self.SetAnisotropicTimeStep(0.01)
        # self.SetAnisotropicConductance(2)
        # self.SetConfidenceConnectedIts(0)
        # self.SetConfidenceConnectedMultiplier(0.5)
        # self.SetConfidenceConnectedRadius(2)
        # self.SetLaplacianExpansionDirection(True) #Laplacian Level Set
        # self.SetLaplacianError(0.001)
        # self.SetConnectedComponentFullyConnected(True)    
        # self.SetConnectedComponentDistance(0.01) 
        
        self.SeedListFilename = "PointList.txt"
        self.SetMaxVolume(300000) #Pixel counts (TODO change to mm^3)   
        self.SetBinaryMorphologicalRadius(2)
        self.SetLevelSetLowerThreshold(0)
        self.SetLevelSetUpperThreshold(75)
        self.SetLevelSetIts(2500)
        self.SetLevelSetReverseDirection(True)
        self.SetLevelSetError(0.03)
        self.SetLevelSetPropagation(1)
        self.SetLevelSetCurvature(1)

        #Shape Detection Filter
        self.SetShapeMaxRMSError(0.01)
        self.SetShapeMaxIterations(500)
        self.SetShapePropagationScale(-1)
        self.SetShapeCurvatureScale(1)


    def SetShapeMaxIterations(self, MaxIts):
        self.shapeDetectionFilter.SetNumberOfIterations(int(MaxIts))

    def SetShapePropagationScale(self, propagationScale):
        self.shapeDetectionFilter.SetPropagationScaling(propagationScale)

    def SetShapeCurvatureScale(self, curvatureScale):
        self.shapeDetectionFilter.SetCurvatureScaling(curvatureScale)

    def SetShapeMaxRMSError(self, MaxRMSError):
        self.shapeDetectionFilter.SetMaximumRMSError(MaxRMSError)

    def SetLevelSetCurvature(self, curvatureScale):
        self.thresholdLevelSet.SetCurvatureScaling(curvatureScale)
        
    def SetLevelSetPropagation(self, propagationScale):
        self.thresholdLevelSet.SetPropagationScaling(propagationScale)
        
    def SetLevelSetLowerThreshold(self, lowerThreshold):
        self.thresholdLevelSet.SetLowerThreshold(int(lowerThreshold))   
        
    def SetLevelSetUpperThreshold(self, upperThreshold):
        self.thresholdLevelSet.SetUpperThreshold(int(upperThreshold))   
        
    def SetLevelSetIts(self,iterations):
        self.thresholdLevelSet.SetNumberOfIterations(int(iterations))
        
    def SetLevelSetReverseDirection(self, direction):
        self.thresholdLevelSet.SetReverseExpansionDirection(direction)
        
    def SetLevelSetError(self,MaxError):        
        self.thresholdLevelSet.SetMaximumRMSError(MaxError)

    def SetImage(self, image):
        self.image = image

    def SefSeedPoint(self, SeedPoint):
        self.SeedPoint = SeedPoint

    def SetScalingFactor(self, ScalingFactor):
        self.ScalingFactor = ScalingFactor
        self.shrinkFilter.SetShrinkFactors(ScalingFactor)
        self.expandFilter.SetExpandFactors(ScalingFactor)

    def SetAnisotropicIts(self, AnisotropicIts):
        self.anisotropicFilter.SetNumberOfIterations(AnisotropicIts)
    
    def SetAnisotropicTimeStep(self, AnisotropicTimeStep):
        self.anisotropicFilter.SetTimeStep(AnisotropicTimeStep)
    
    def SetAnisotropicConductance(self, AnisotropicConductance):
        self.anisotropicFilter.SetConductanceParameter(AnisotropicConductance)

    def SetConfidenceConnectedIts(self, ConfidenceConnectedIts):
        self.ConfidenceConnectedIts = ConfidenceConnectedIts

    def SetConfidenceConnectedMultiplier(self, ConfidenceConnectedMultiplier):
        self.ConfidenceConnectedMultiplier = ConfidenceConnectedMultiplier

    def SetConfidenceConnectedRadius(self, ConfidenceConnectedRadius):
        self.ConfidenceConnectedRadius = ConfidenceConnectedRadius

    def SetBinaryMorphologicalRadius(self, kernelRadius):
        self.erodeFilter.SetKernelRadius(kernelRadius)
        self.dilateFilter.SetKernelRadius(kernelRadius) 

    def SetMaxVolume(self, MaxVolume):
        self.MaxVolume = MaxVolume  

    def SetLaplacianExpansionDirection(self, expansionDirection):       
        self.laplacianFilter.SetReverseExpansionDirection(expansionDirection)

    def SetLaplacianError(self, RMSError):
        self.laplacianFilter.SetMaximumRMSError(RMSError)

    def SetConnectedComponentFullyConnected(self, fullyConnected):
        self.connectedComponentFilter.SetFullyConnected(fullyConnected) 

    def SetConnectedComponentDistance(self, distanceThreshold):
        #Distance = Intensity difference NOT location distance
        self.connectedComponentFilter.SetDistanceThreshold(distanceThreshold) 

#############################################################################################
###Main algorithm execution here###
#############################################################################################
    def Execute(self, image, seedPoint, verbose = False):

        self.verbose = verbose #Optional argument to output text to terminal

        self.image = image
        self.seedPoint = seedPoint

        # self.image = self.FlipImage(self.image) #Flip the MRI

        #Convert images to float 32 first
        self.image = sitk.Cast(self.image, sitk.sitkFloat32)

        if self.verbose == True:
            print('\033[94m' + "Current Seed Point: "),
            print(self.seedPoint)
            print('\033[94m' + "Rounding and converting to voxel domain: "), 
        self.RoundSeedPoint()

        if self.verbose == True:
            print(self.seedPoint)
            print('\033[90m' + "Scaling image down...")
        self.scaleDownImage()

        # print('\033[92m' + "Applying the Anisotropic Filter...")
        # self.apply_AnisotropicFilter()

        if self.verbose == True:
            print("Threshold level set segmentation...")
        self.ThresholdLevelSet() 

        # print('\033[93m' + "Segmenting via confidence connected...")
        # self.ConfidenceConnectedSegmentation()

        # print('\033[95m' + "Running Laplacian Level Set...")
        # self.LaplacianLevelSet()

        # print('\033[95m' + "Finding connected regions...")
        # self.ConnectedComponent()

        # if self.verbose == True:
            # print('\033[96m' + "Checking volume for potential leakage... "), #Comma keeps printing on the same line
        # self.LeakageCheck()

        # print('\033[90m' + "Simple threshold operation...")
        # self.ThresholdImage()
        if (self.shapeDetectionFilter.GetNumberOfIterations > 0):
            self.ShapeDetection()


        if self.verbose == True:
            print('\033[93m' + "Filling Segmentation Holes...")
        self.HoleFilling()

        if self.verbose == True:
            print('\033[90m' + "Scaling image back...")
        self.scaleUpImage()

        print('\033[90m' + "Eroding image slightly...")
        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)


        if self.verbose == True:
            print('\033[96m' + "Finished with seed point "),
            print(self.seedPoint)
        
        return  self.segImg 

#############################################################################################
#############################################################################################

    def FlipImage(self,image):
        #Flip image(s) (if needed)
        flipFilter = sitk.FlipImageFilter()
        flipFilter.SetFlipAxes((False,True,False))
        image = flipFilter.Execute(self.image)
        return image

    def ThresholdImage(self):
        self.segImg.CopyInformation(self.image)
        thresholdFilter = sitk.BinaryThresholdImageFilter()
        thresholdFilter.SetLowerThreshold(1)
        thresholdFilter.SetUpperThreshold(100)
        tempImg = self.segImg * self.image
        self.segImg = thresholdFilter.Execute(tempImg)
        # sitk.Show(self.segImg)
        return self

    def RoundSeedPoint(self):
        tempseedPoint = np.array(self.seedPoint).astype(int) #Just to be safe make it int again
        tempseedPoint = tempseedPoint[0]
        #Convert from physical to image domain
        tempFloat = [float(tempseedPoint[0]), float(tempseedPoint[1]), float(tempseedPoint[2])]
        #Convert from physical units to voxel coordinates
        # tempVoxelCoordinates = self.image.TransformPhysicalPointToContinuousIndex(tempFloat)
        # self.seedPoint = tempVoxelCoordinates
        self.seedPoint = tempFloat

        #Need to round the seedPoints because integers are required for indexing
        ScalingFactor = np.array(self.ScalingFactor)
        tempseedPoint = np.array(self.seedPoint).astype(int)
        tempseedPoint = abs(tempseedPoint)
        tempseedPoint = tempseedPoint/ScalingFactor #Scale the points down as well
        tempseedPoint = tempseedPoint.round() #Need to round it again for Python 3.3

        self.seedPoint = [tempseedPoint]

        return self
    
    def scaleDownImage(self):
        self.image = self.shrinkFilter.Execute(self.image)
        return self

    def scaleUpImage(self):
        self.segImg = self.expandFilter.Execute(self.segImg)
        return self

    #Function definitions are below
    def apply_AnisotropicFilter(self):
        self.image = self.anisotropicFilter.Execute(self.image)
        return self

    def savePointList(self):
        try:
            #Save the user defined points in a .txt for automatimating testing (TODO)
            text_file = open(self.SeedListFilename, "r+")
            text_file.readlines()
            text_file.write("%s\n" % self.seedPoint)
            text_file.close()
        except:
            print("Saving to .txt failed...")
        return

    def HoleFilling(self):
        self.segImg  = sitk.Cast(self.segImg, sitk.sitkUInt16)
        #Apply the filters to the binary image
        self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
        self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)
        self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
        # self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)  
        return self

    def ShapeDetection(self):
        print('Shape Detection Level Set...')

        self.segImg = sitk.Cast(self.segImg, sitk.sitkUInt16)

        #Signed distance function using the initial levelset segmentation
        init_ls = sitk.SignedMaurerDistanceMap(self.segImg, insideIsPositive=True, useImageSpacing=True)

        gradientImage = self.GradientMagnitudeFilter.Execute(self.image)

        shapeBinary = self.shapeDetectionFilter.Execute(init_ls, gradientImage)

        npshapeBinary = np.asarray(sitk.GetArrayFromImage(shapeBinary), dtype='float64')

        npshapeBinary[npshapeBinary > 0.2] = 1 #Make into a binary again
        # npshapeBinary[npshapeBinary < 0] = 0 #Make into a binary again

        npshapeBinary[npshapeBinary != 1] = 0

        self.segImg = sitk.Cast(sitk.GetImageFromArray(npshapeBinary), self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        print(self.shapeDetectionFilter)

    def LaplacianLevelSet(self):
        #Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID()) #Can't be a 32 bit float
        self.segImg.CopyInformation(self.image)

        #Additional post-processing (Lapacian Level Set Filter)
        #Binary image needs to have a value of 0 and 1/2*(x+1)
        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        #Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda == 1] = 0.5

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)


        self.segImg = self.laplacianFilter.Execute(self.segImg, self.image)
        if self.verbose == True:
            print(self.laplacianFilter)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        #Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda <= 0.3] = 0
        nda[nda != 0] = 1

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self


    def ConnectedComponent(self):

        self.segImg = sitk.Cast(self.segImg, 1) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        #Try to remove leakage areas by first eroding the binary and
        #get the labels that are still connected to the original seed location

        self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)

        self.segImg = self.connectedComponentFilter.Execute(self.segImg)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        #In numpy an array is indexed in the opposite order (z,y,x)
        tempseedPoint = self.seedPoint[0]
        val = nda[tempseedPoint[2]][tempseedPoint[1]][tempseedPoint[0]]

        #Keep only the label that intersects with the seed point
        nda[nda != val] = 0 
        nda[nda != 0] = 1

        self.segImg = sitk.GetImageFromArray(nda)

        #Undo the earlier erode filter by dilating by same radius
        self.dilateFilter.SetKernelRadius(3)
        self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)

        # self.segImg = sitk.Cast(self.segImg, segmentation.GetPixelID())
        # self.segImg.CopyInformation(segmentation)

        return self

    def LeakageCheck(self):

        #Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)
        # self.segImg = sitk.Cast(self.segImg, segmentation.GetPixelID()) #Can't be a 32 bit float
        # self.segImg.CopyInformation(segmentation)

        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)

        volume = len(nda[nda == 1])
        if volume > self.MaxVolume:
            if self.verbose == True:
                print('\033[97m' + "Failed check with volume "),
                print(volume)
                print("Skipping this label")
            #Clearing the label is the same as ignoring it since they're added together later
            nda = nda*0 
            self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), self.segImg.GetPixelID())
            
        else:
            if self.verbose == True:
                print('\033[96m' + "Passed with volume "),
                print(volume)

        return self

    def ThresholdLevelSet(self):

        ###Create the seed image###
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        seedPoint = self.seedPoint[0]
        if self.verbose == True:
            print(seedPoint)
        #In numpy an array is indexed in the opposite order (z,y,x)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

        seg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        seg.CopyInformation(self.image)

        seg = sitk.BinaryDilate(seg, 3)

        init_ls = sitk.SignedMaurerDistanceMap(seg, insideIsPositive=True, useImageSpacing=True)

        threshOutput = self.thresholdLevelSet.Execute(init_ls, self.image)
        if self.verbose == True:
            print(self.thresholdLevelSet)


        nda = sitk.GetArrayFromImage(threshOutput)
        nda = np.asarray(nda)

        #Fix the intensities of the output of the level set; 0 = 1 and ~! 1 is 0 then 1 == x+1
        nda[nda > 0] = 1
        nda[nda < 0] = 0

        self.segImg = sitk.GetImageFromArray(nda)
        self.segImg = sitk.Cast(self.segImg, self.image.GetPixelID())
        self.segImg.CopyInformation(self.image)

        return self
#############################################################################################

























    # def updateEnableState(self):
    #     enabled = bool(self.logic.inputVolumeNode) and bool(
    #         self.logic.labelNode)
    #     self.applyButton.enabled = enabled
    #     self.autoApplyButton.enabled = enabled
    #     if not enabled:
    #         self.outputVolumeSelectorLabel.text = ""

    # def updateLabelText(self):
    #     if self.logic.outputVolumeNode:
    #         self.outputVolumeSelectorLabel.text = self.logic.outputVolumeNode.GetName()
    #     else:
    #         self.outputVolumeSelectorLabel.text = ""

    # def onApply(self):
    #     """Calculate the mask volume
    #     """
    #     if self.logic.apply():
    #         self.updateLabelText()

    # def onAutoApply(self, state):
    #     """Calculate the mask volume"""
    #     if state:
    #         if self.logic.apply():
    #             self.logic.autoApply()
    #             self.updateLabelText()
    #         else:
    #             self.logic.removeObservers()

# class Slicelet(object):
#     """A slicer slicelet is a module widget that comes up in stand alone mode
#   implemented as a python class.
#   This class provides common wrapper functionality used by all slicer modlets.
#   """
#     # TODO: put this in a SliceletLib
#     # TODO: parse command line arge

#     def __init__(self, widgetClass=None):
#         self.parent = qt.QFrame()
#         self.parent.setLayout(qt.QVBoxLayout())

#         # TODO: should have way to pop up python interactor
#         self.buttons = qt.QFrame()
#         self.buttons.setLayout(qt.QHBoxLayout())
#         self.addDataButton = qt.QPushButton("Add Data")
#         self.buttons.layout().addWidget(self.addDataButton)
#         self.addDataButton.connect(
#             "clicked()", slicer.app.ioManager().openAddDataDialog)
#         self.saveDataButton = qt.QPushButton("Save Data")
#         self.buttons.layout().addWidget(self.saveDataButton)
#         self.saveDataButton.connect(
#             "clicked()", slicer.app.ioManager().openSaveDataDialog)






#         self.parent.layout().addWidget(self.buttons)

#         #Add a second column of buttons
#         self.buttonsColTwo = qt.QFrame()
#         self.buttonsColTwo.setLayout(qt.QHBoxLayout())
#         self.parent.layout().addWidget(self.buttonsColTwo)
#         #
#         # Add fiducial marker button
#         #
#         self.addMarkerButton = qt.QPushButton("Add Marker")
#         self.addMarkerButton.toolTip = "Compute information for the selected markup"
#         self.buttonsColTwo.layout().addWidget(self.addMarkerButton)
#         self.addMarkerButton.connect(
#             'clicked()', self.enableOrDisableFiducialeButton)

#         #
#         # Delete fiducial marker button
#         #
#         self.deleteMarkerButton = qt.QPushButton("Delete Markers")
#         self.deleteMarkerButton.toolTip = "Remove all the current fiducial markers."
#         self.buttonsColTwo.layout().addWidget(self.deleteMarkerButton)
#         self.addMarkerButton.connect(
#             'clicked()', self.deleteFiducialsButton)




#         self.printMarkersButton = qt.QPushButton("Print Markers")
#         self.printMarkersButton.toolTip = "Compute information for the selected markup"
#         self.buttonsColTwo.layout().addWidget(self.printMarkersButton)
#         self.printMarkersButton.connect(
#             'clicked()', self.printMarkers)



#         #
#         # Add A 2D View of the Input Image
#         #

#         # layoutManager = slicer.qMRMLLayoutWidget()
#         # layoutManager.setMRMLScene(slicer.mrmlScene)
        
#         # self.viewSlice = qt.QFrame()
#         # self.viewSlice.setLayout()
#         layoutManager = slicer.qMRMLLayoutWidget()
#         layoutManager.setMRMLScene(slicer.mrmlScene)
#         layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
#         self.parent.layout().addWidget(layoutManager)



#         if widgetClass:
#             self.widget = widgetClass(self.parent)
#             self.widget.setup()
#         self.parent.show()


# class BoneSegmentationSlicelet(Slicelet):
#     """ Creates the interface when module is run as a stand alone gui app.
#   """

#     def __init__(self):
#         super(BoneSegmentationSlicelet, self).__init__(BoneSegmentationWidget)

#     def enableOrDisableFiducialeButton(self):
#         placeModePersistence = 1
#         # slicer.modules.markups.logic().AddFiducial(1.0, -2.0, 3.3)
#         slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
#         #Change the seed points color
#         slicer.modules.markups.logic().SetDefaultMarkupsDisplayNodeSelectedColor(0, 255, 0)


#     def deleteFiducialsButton(self):
#         fidList = getNode("vtkMRMLMarkupsFiducialNode1")
#         fidList.RemoveAllMarkups()
#         placeModePersistence = 0
#         slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
#         print("Removed all markeup points")


#     def printMarkers(self):

#         fidList = getNode("vtkMRMLMarkupsFiducialNode1")

#         numFids = fidList.GetNumberOfFiducials()
#         for i in range(numFids):
#             ras = [0,0,0]

#             fidList.GetNthFiducialPosition(i,ras)
#             print i,": RAS =",ras
#             ras = [0,0,0,0]
#             fidList.GetNthFiducialWorldCoordinates(i,ras)
#             print i,": RAS =",ras       