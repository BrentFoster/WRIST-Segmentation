from __main__ import vtk, qt, ctk, slicer
import EditorLib

#
# BoneSegmentation
#


class BoneSegmentation:

    def __init__(self, parent):
        import string
        parent.title = "Carpal Bone Segmentation"
        parent.categories = ["Bone Segmentation"]
        parent.contributors = ["Brent Foster (UC Davis)"]
        parent.helpText = string.Template("Use this module to segment the eight carpal bones of the wrist. Input is a seed location defined by the user within each bone of interest. The Confidence Connected ITK Filter is then applied. ").substitute({
            'a': parent.slicerWikiUrl, 'b': slicer.app.majorVersion, 'c': slicer.app.minorVersion})
        parent.acknowledgementText = """
    Supported by NSF and NIH funding. Module implemented by Brent Foster.
    """
        self.parent = parent

#
# qSlicerPythonModuleExampleWidget
#


class BoneSegmentationWidget:

    def __init__(self, parent=None):
        self.parent = parent
        self.logic = None
        self.ImageNode = None

    def setup(self):


        frame = qt.QFrame()
        firstTabLayout = qt.QFormLayout()
        frame.setLayout(firstTabLayout)
        self.parent.layout().addWidget(frame)

        # firstTabLayout = qt.QFormLayout()

        # Markup Selector
        self.markupSelectorLabel = qt.QLabel()
        self.markupSelectorLabel.setText("Markup list: ")
        self.markupSelector = slicer.qMRMLNodeComboBox()
        self.markupSelector.nodeTypes = ("vtkMRMLMarkupsFiducialNode", "")
        # self.markupSelector.nodeTypes = ("vtkMRMLAnnotationFiducialNode", "")
        self.markupSelector.noneEnabled = False
        self.markupSelector.baseName = "Seed List"
        self.markupSelector.selectNodeUponCreation = True
        self.markupSelector.setMRMLScene(slicer.mrmlScene)
        self.markupSelector.setToolTip("Pick the markup list to be filled")
        firstTabLayout.addRow(self.markupSelectorLabel, self.markupSelector)


        #
        # Input Volume Selector
        #

        self.inputVolumeSelectorLabel = qt.QLabel()
        self.inputVolumeSelectorLabel.setText("Input Volume: ")
        self.inputVolumeSelectorLabel.setToolTip(
            "Select the inputVolume volume (background inputVolume scalar volume node) for statistics calculations")
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputSelector.noneEnabled = False
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        firstTabLayout.addRow(
            self.inputVolumeSelectorLabel, self.inputSelector)

        #
        # Input Label Selector
        #

        self.inputLabelSelectorLabel = qt.QLabel()
        self.inputLabelSelectorLabel.setText("Input Label: ")
        self.inputLabelSelectorLabel.setToolTip(
            "Use the 'editor' to create lines to prevent leakage")
        self.inputLabelSelector = slicer.qMRMLNodeComboBox()
        self.inputLabelSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputLabelSelector.noneEnabled = True
        self.inputLabelSelector.selectNodeUponCreation = True
        self.inputLabelSelector.setMRMLScene(slicer.mrmlScene)
        firstTabLayout.addRow(
            self.inputLabelSelectorLabel, self.inputLabelSelector)


        #
        # Apply button
        #
        self.computeButton = qt.QPushButton("Compute")
        self.computeButton.toolTip = "Compute information for the selected markup"
        firstTabLayout.addWidget(self.computeButton)
        self.UpdatecomputeButtonState()
        # connections
        self.computeButton.connect('clicked()', self.onCompute)
        # self.markupSelector.connect(
            # 'currentNodeChanged(vtkMRMLNode*)', self.onMarkupSelect)
        self.inputSelector.connect(
            'currentNodeChanged(vtkMRMLNode*)', self.onInputSelect)

        #
        # Output Volume Label
        #
        self.outputVolumeSelectorLabel = qt.QLabel()
        self.outputVolumeSelectorLabel.setText("Output Volume: ")
        self.outputVolumeSelectorLabel.setToolTip(
            "Select the inputVolume volume (background inputVolume scalar volume node) for statistics calculations")
        self.outputSelector = slicer.qMRMLNodeComboBox()
        self.outputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.outputSelector.noneEnabled = True
        self.outputSelector.selectNodeUponCreation = True
        self.outputSelector.setMRMLScene(slicer.mrmlScene)

        firstTabLayout.addRow(
            self.outputVolumeSelectorLabel, self.outputSelector)
        

        

        #
        # the output volume label
        #
        # self.outputVolumeSelectorFrame = qt.QFrame(self.parent)
        # self.outputVolumeSelectorFrame.setLayout(qt.QHBoxLayout())
        # self.parent.layout().addWidget(self.outputVolumeSelectorFrame)

        # self.outputVolumeSelectorLabel = qt.QLabel(
        #     "Masked Volume: ", self.outputVolumeSelectorFrame)
        # self.outputVolumeSelectorFrame.layout().addWidget(self.outputVolumeSelectorLabel)

        # Apply button
        # self.applyButton = qt.QPushButton("Apply")
        # self.applyButton.toolTip = "Apply the masking."
        # self.applyButton.enabled = False
        # self.parent.layout().addWidget(self.applyButton)

        # # Auto button
        # self.autoApplyButton = qt.QCheckBox("Auto Apply")
        # self.autoApplyButton.toolTip = "Apply the change when either input value changes."
        # self.autoApplyButton.enabled = False
        # self.parent.layout().addWidget(self.autoApplyButton)

        # # Add vertical spacer
        # self.parent.layout().addStretch(1)

        # connections
        # self.applyButton.connect('clicked()', self.onApply)
        # self.autoApplyButton.connect('toggled(bool)', self.onAutoApply)
        # self.inputVolumeSelector.connect(
            # 'currentNodeChanged(vtkMRMLNode*)', self.onInputSelect)
        # self.labelSelector.connect(
            # 'currentNodeChanged(vtkMRMLNode*)', self.onLabelSelect)

    


    def UpdatecomputeButtonState(self):
        # if not self.markupSelector.currentNode():
            # self.computeButton.enabled = False
        # elif self.inputSelector.currentNode():
        if self.inputSelector.currentNode():
            self.computeButton.enabled = True
        else:
            self.computeButton.enabled = False

    def onMarkupSelect(self, node):
        self.UpdatecomputeButtonState()


    def onCompute(self):
        # slicer.app.processEvents()

        #Make list of all the seed point locations
        fidList = getNode("vtkMRMLMarkupsFiducialNode1")
        numFids = fidList.GetNumberOfFiducials()
        seedPoints = []
        for i in range(numFids):
            ras = [0,0,0]
            fidList.GetNthFiducialPosition(i,ras)
            # fidList.GetNthFiducialWorldCoordinates(i,ras)
            
            seedPoints.append(ras)
            print i,": RAS =",ras
        # seedPoints[0] = []
        print(fidList)
        # imageID = getNode("vtkMRMLScalarVolumeNode2") #Get the name of the image
        # print(imageID.GetName())

        imageID = self.inputSelector.currentNode()
        inputLabelID = self.inputLabelSelector.currentNode()

        image = sitkUtils.PullFromSlicer(imageID.GetName())

        inputLabelimage = sitkUtils.PullFromSlicer(inputLabelID.GetName())

        # inputLabelID = getNode(self.inputLabelSelector)
        # inputLabel = sitkUtils.PullFromSlicer(inputLabelID.GetName())
        

        for i in range(numFids):
            seedPoints[i] = image.TransformPhysicalPointToContinuousIndex(seedPoints[i])

        #Use the two classes that are defined at the bottom of this file
        segmentationClass = BoneSeg()
        multiHelper = MultiprocessorHelper.Multiprocessor(segmentationClass, seedPoints, image)
        segmentation = multiHelper.Execute()
         # compositeViewMap = {0:'background',
         #                1:'foreground',
         #                2:'label'}
        sitkUtils.PushToSlicer(segmentation,'Segmentation',2)

    def updateEnableState(self):
        enabled = bool(self.logic.inputVolumeNode) and bool(
            self.logic.labelNode)
        self.applyButton.enabled = enabled
        self.autoApplyButton.enabled = enabled
        if not enabled:
            self.outputVolumeSelectorLabel.text = ""


    def onInputSelect(self, node):
        # self.logic.inputVolumeNode = node
        # self.updateEnableState()
        self.UpdatecomputeButtonState()

        self.ImageNode = node
        print("UPDATING self.ImageNode")
        print(self.ImageNode)
        print(node)
        print("GetScalarVolumeDisplayNode")
        print(self.ImageNode.GetScalarVolumeDisplayNode())


    # def onLabelSelect(self, node):        
        # self.logic.labelNode = node



        # self.updateEnableState()

    def updateLabelText(self):
        if self.logic.outputVolumeNode:
            self.outputVolumeSelectorLabel.text = self.logic.outputVolumeNode.GetName()
        else:
            self.outputVolumeSelectorLabel.text = ""

    def onApply(self):
        """Calculate the mask volume
        """
        if self.logic.apply():
            self.updateLabelText()

    def onAutoApply(self, state):
        """Calculate the mask volume"""
        if state:
            if self.logic.apply():
                self.logic.autoApply()
                self.updateLabelText()
            else:
                self.logic.removeObservers()


class BoneSegmentationLogic:
    """Implement the logic to calculate the mask volume
  """

    def __init__(self):
        self.inputVolumeNode = None
        self.labelNode = None
        self.outputVolumeNode = None
        self.observerTags = {}
        self.lastMaskLabel = None

    def removeObservers(self):
        if self.observerTags != {}:
            for n in self.observerTags.keys():
                n.RemoveObserver(self.observerTags[n])
        self.observerTags = {}

    def apply(self):
        if not (self.inputVolumeNode and self.labelNode):
            return False
        if not self.outputVolumeNode:
            volumesLogic = slicer.modules.volumes.logic()
            outputName = self.inputVolumeNode.GetName() + "-masked"
            self.outputVolumeNode = volumesLogic.CloneVolume(
                slicer.mrmlScene, self.inputVolumeNode, outputName)
        self.performMasking()
        return True

    def autoApply(self):
        self.removeObservers()
        parameterNode = EditorLib.EditUtil.EditUtil().getParameterNode()
        self.observerTags[parameterNode] = parameterNode.AddObserver(
            vtk.vtkCommand.ModifiedEvent, self.conditionalPerformMasking)
        nodes = (self.inputVolumeNode, self.labelNode)
        for n in nodes:
            self.observerTags[n] = n.AddObserver(
                n.ImageDataModifiedEvent, self.performMasking)

    def conditionalPerformMasking(self, object=None, event=None):
        """Since we cannot observe for just the label value
    changing on the parameter node, we check the label value
    or else we would be re-masking for every small edit
    parameter change.
    """
        label = EditorLib.EditUtil.EditUtil().getLabel()
        if label != self.lastMaskLabel:
            self.performMasking()

    def performMasking(self, object=None, event=None):
        import numpy
        label = EditorLib.EditUtil.EditUtil().getLabel()
        a = slicer.util.array(self.inputVolumeNode.GetID())
        la = slicer.util.array(self.labelNode.GetID())
        ma = slicer.util.array(self.outputVolumeNode.GetID())
        mask = numpy.ndarray.copy(la)
        # TODO: can there be one vector operation that sets
        # everything to 0 or 1?
        mask[mask == label] = 1
        mask[mask != 1] = 0
        ma[:] = a * mask
        self.outputVolumeNode.GetImageData().Modified()
        self.lastMaskLabel = label


class Slicelet(object):
    """A slicer slicelet is a module widget that comes up in stand alone mode
  implemented as a python class.
  This class provides common wrapper functionality used by all slicer modlets.
  """
    # TODO: put this in a SliceletLib
    # TODO: parse command line arge

    def __init__(self, widgetClass=None):
        self.parent = qt.QFrame()
        self.parent.setLayout(qt.QVBoxLayout())

        # TODO: should have way to pop up python interactor
        self.buttons = qt.QFrame()
        self.buttons.setLayout(qt.QHBoxLayout())
        self.addDataButton = qt.QPushButton("Add Data")
        self.buttons.layout().addWidget(self.addDataButton)
        self.addDataButton.connect(
            "clicked()", slicer.app.ioManager().openAddDataDialog)
        self.saveDataButton = qt.QPushButton("Save Data")
        self.buttons.layout().addWidget(self.saveDataButton)
        self.saveDataButton.connect(
            "clicked()", slicer.app.ioManager().openSaveDataDialog)



        self.parent.layout().addWidget(self.buttons)

        #Add a second column of buttons
        self.buttonsColTwo = qt.QFrame()
        self.buttonsColTwo.setLayout(qt.QHBoxLayout())
        self.parent.layout().addWidget(self.buttonsColTwo)
        #
        # Add fiducial marker button
        #
        self.addMarkerButton = qt.QPushButton("Add Marker")
        self.addMarkerButton.toolTip = "Compute information for the selected markup"
        self.buttonsColTwo.layout().addWidget(self.addMarkerButton)
        self.addMarkerButton.connect(
            'clicked()', self.enableOrDisableFiducialeButton)

        #
        # Delete fiducial marker button
        #
        self.deleteMarkerButton = qt.QPushButton("Delete Markers")
        self.deleteMarkerButton.toolTip = "Remove all the current fiducial markers."
        self.buttonsColTwo.layout().addWidget(self.deleteMarkerButton)
        self.addMarkerButton.connect(
            'clicked()', self.deleteFiducialsButton)




        self.printMarkersButton = qt.QPushButton("Print Markers")
        self.printMarkersButton.toolTip = "Compute information for the selected markup"
        self.buttonsColTwo.layout().addWidget(self.printMarkersButton)
        self.printMarkersButton.connect(
            'clicked()', self.printMarkers)



        #
        # Add A 2D View of the Input Image
        #

        # layoutManager = slicer.qMRMLLayoutWidget()
        # layoutManager.setMRMLScene(slicer.mrmlScene)
        
        # self.viewSlice = qt.QFrame()
        # self.viewSlice.setLayout()
        layoutManager = slicer.qMRMLLayoutWidget()
        layoutManager.setMRMLScene(slicer.mrmlScene)
        layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutOneUpRedSliceView)
        self.parent.layout().addWidget(layoutManager)



        if widgetClass:
            self.widget = widgetClass(self.parent)
            self.widget.setup()
        self.parent.show()


class BoneSegmentationSlicelet(Slicelet):
    """ Creates the interface when module is run as a stand alone gui app.
  """

    def __init__(self):
        super(BoneSegmentationSlicelet, self).__init__(BoneSegmentationWidget)

    def enableOrDisableFiducialeButton(self):
        placeModePersistence = 1
        # slicer.modules.markups.logic().AddFiducial(1.0, -2.0, 3.3)
        slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
        #Change the seed points color
        slicer.modules.markups.logic().SetDefaultMarkupsDisplayNodeSelectedColor(0, 255, 0)


    def deleteFiducialsButton(self):
        fidList = getNode("vtkMRMLMarkupsFiducialNode1")
        fidList.RemoveAllMarkups()
        placeModePersistence = 0
        slicer.modules.markups.logic().StartPlaceMode(placeModePersistence)
        print("Removed all markeup points")


    def printMarkers(self):

        fidList = getNode("vtkMRMLMarkupsFiducialNode1")

        numFids = fidList.GetNumberOfFiducials()
        for i in range(numFids):
            ras = [0,0,0]

            fidList.GetNthFiducialPosition(i,ras)
            print i,": RAS =",ras
            ras = [0,0,0,0]
            fidList.GetNthFiducialWorldCoordinates(i,ras)
            print i,": RAS =",ras
        



            # the world position is the RAS position with any transform matrices applied
            # world = [0,0,0,0]
            # fidList.GetNthFiducialWorldCoordinates(0,world)
            # print i,": RAS =",ras,", world =",world
        # get the first list of annotations
        # listNodeID = "vtkMRMLMarkupsFiducialNode1"
        # annotationHierarchyNode = slicer.mrmlScene.GetNodeByID(listNodeID)
        # get the first in the list
        # listIndex = 0
        # annotation = annotationHierarchyNode.GetNthChildNode(listIndex).GetAssociatedNode()
        # coords = [0,0,0]
        # vtkMRMLAnnotationFiducialNode
        # fidList.GetFiducialCoordinates(coords)
        # print coords

        

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
    """docstring for ClassName"""
    def __init__(self, segmentationClass, seedList, MRI_Image):
        # super(ClassName, self).__init__()
        # self.arg = arg
        self.segmentationClass = segmentationClass
        self.seedList = seedList
        self.MRI_Image = MRI_Image

        #Convert to voxel coordinates
        self.RoundSeedPoints() 

    def Execute(self):

        ###Create an empty segmenationLabel array###
        nda = sitk.GetArrayFromImage(self.MRI_Image)
        nda = np.asarray(nda)
        nda = nda*0
        self.segmentationArray = nda
        ############################################
        ##Convert the SimpleITK images to arrays##
        self.MRI_Array = sitk.GetArrayFromImage(self.MRI_Image)
        #####

        #Check the number of cpu's in the computer and if the seed list is greater than 
        #the number of cpu's then run the parallel computing twice
        #TODO: Use a 'pool' of works for this may be more efficient
        num_CPUs = multiprocessing.cpu_count()
        print("Number of CPUs = "),
        print(num_CPUs)

        if (len(self.seedList) <= num_CPUs):
            jobOrder = range(0, len(self.seedList))
            print(jobOrder)
            self.segmentationArray = self.RunMultiprocessing(jobOrder)

        elif (len(self.seedList) > num_CPUs):
            print("Splitting jobs since number of CPUs < number of seed points")
            #Run the multiprocessing several times since there wasn't enough CPU's before
            jobOrder = self.SplitJobs(range(len(self.seedList)), num_CPUs)
            print(jobOrder)
            for x in range(len(jobOrder)):
                self.segmentationArray = self.segmentationArray + self.RunMultiprocessing(jobOrder[x])

        #Convert segmentationArray back into an image
        segmentationOutput = sitk.Cast(sitk.GetImageFromArray(self.segmentationArray), self.MRI_Image.GetPixelID())
        segmentationOutput.CopyInformation(self.MRI_Image)

        return segmentationOutput

    ###Split the Seed List using the multiprocessing library and then execute the pipeline###
    #Helper functions for the multiprocessing
    def RunMultiprocessing(self,jobOrder):
        procs = []
        q = multiprocessing.Queue()
        for x in jobOrder:
            p = multiprocessing.Process(target=self.f, args=(self.MRI_Array, self.seedList[x],q,))
            p.start()
            procs.append(p) #List of current processes

        tempArray = self.segmentationArray
        print("Printing multiprocessing queue:")
        for i in range(len(jobOrder)):
            #Outputs an array (due to multiprocessing 'pickle' constraints)
            tempArray = tempArray + q.get() 
        # Wait for all worker processes to finish by using .join()
        for p in procs:
            p.join()
            p.terminate()

        print('Finished with processes:'),
        print(jobOrder)
        return tempArray

    def SplitJobs(self, jobs, size):
         output = []
         while len(jobs) > size:
             pice = jobs[:size]
             output.append(pice)
             jobs   = jobs[size:]
         output.append(jobs)
         return output

    def f(self, MRI_Array, SeedPoint,q):
        output = self.segmentationClass.Execute(MRI_Array,[SeedPoint])
        q.put(output)

    #Need to convert to voxel coordinates since we pass only the array due to a 'Pickle' error
    #with the multiprocessing library and the ITK image type which means the header information
    #is lost
    def RoundSeedPoints(self):
        seeds = []
        for i in xrange(0,len(self.seedList)): #Select which bone (or all of them) from the csv file
            #Convert from string to float
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

        #Set the deafult values 
        self.SetDefaultValues()

    def SetDefaultValues(self):
        #Set the default values of all the parameters here
        self.SetScalingFactor([2,2,1]) #X,Y,Z
        self.SetAnisotropicIts(5)
        self.SetAnisotropicTimeStep(0.01)
        self.SetAnisotropicConductance(2)
        self.SetConfidenceConnectedIts(0)
        self.SetConfidenceConnectedMultiplier(0.5)
        self.SetConfidenceConnectedRadius(2)
        self.SetMaxVolume(400000) #Pixel counts (TODO change to mm^3)   
        self.SetBinaryMorphologicalRadius(1)    
        self.SetLaplacianExpansionDirection(True) #Laplacian Level Set
        self.SetLaplacianError(0.002)
        self.SetConnectedComponentFullyConnected(True)  
        self.SetConnectedComponentDistance(0.01) 
        self.SeedListFilename = "PointList.txt"

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
    def Execute(self, image, seedPoint):

        self.image = image
        self.seedPoint = seedPoint

        #Convert from the arrays back into ITK images (due to multiprocessing)
        self.image = sitk.Cast(sitk.GetImageFromArray(self.image), sitk.sitkFloat32)

        #Convert images to float 32 first
        self.image = sitk.Cast(self.image, sitk.sitkFloat32)

        print('\033[94m' + "Current Seed Point: "),
        print(self.seedPoint)

        print('\033[94m' + "Rounding and converting to voxel domain: "), 
        self.RoundSeedPoint()
        print(self.seedPoint)

        print('\033[90m' + "Scaling image down...")
        self.scaleDownImage()

        print('\033[92m' + "Applying the Anisotropic Filter...")
        # self.apply_AnisotropicFilter()

        print("Testing the threshold level set segmentation...")
        self.ThresholdLevelSet() 

        print('\033[93m' + "Segmenting via confidence connected...")
        # self.ConfidenceConnectedSegmentation()

        print('\033[93m' + "Filling Segmentation Holes...")
        self.HoleFilling()

        print('\033[95m' + "Running Laplacian Level Set...")
        # self.LaplacianLevelSet()

        print('\033[95m' + "Finding connected regions...")
        self.ConnectedComponent()

        print('\033[96m' + "Checking volume for potential leakage... "), #Comma keeps printing on the same line
        self.LeakageCheck()

        print('\033[90m' + "Scaling image back...")
        self.scaleUpImage()

        print('\033[96m' + "Finished with seed point "),
        print(self.seedPoint)

        #Return an array instead of a sitk.Image due to contraints on the multiprocessing library
        nda = sitk.GetArrayFromImage(self.segImg)
        nda = np.asarray(nda)
        return  nda 

#############################################################################################
#############################################################################################


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
        self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)
        self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
        self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)    
        return self

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
            print('\033[97m' + "Failed check with volume "),
            print(volume)
            #Clearing the label is the same as ignoring it since they're added together later
            nda = nda*0 
            self.segImg = sitk.Cast(sitk.GetImageFromArray(nda), self.segImg.GetPixelID())
            print("Skipping this label")
        else:
            print('\033[96m' + "Passed with volume "),
            print(volume)

        return self

    def ThresholdLevelSet(self):

        ###Create the seed image###
        nda = sitk.GetArrayFromImage(self.image)
        nda = np.asarray(nda)
        nda = nda*0

        seedPoint = self.seedPoint[0]
        print(seedPoint)
        nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1
        #In numpy an array is indexed in the opposite order (z,y,x)
        # nda[47][100][50] = 1

        seg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
        seg.CopyInformation(self.image)

        seg = sitk.BinaryDilate(seg, 3)

        # seg = sitk.Cast(seg, sitk.sitkFloat32)

        init_ls = sitk.SignedMaurerDistanceMap(seg, insideIsPositive=True, useImageSpacing=True)

        thresholdLevelSet = sitk.ThresholdSegmentationLevelSetImageFilter()
        
        thresholdLevelSet.SetLowerThreshold(0)
        thresholdLevelSet.SetUpperThreshold(60)
        thresholdLevelSet.SetNumberOfIterations(1000)
        thresholdLevelSet.SetReverseExpansionDirection(True)
        thresholdLevelSet.SetMaximumRMSError(0.005)
        # thresholdLevelSet.SetPropagationScaling(1)
        # thresholdLevelSet.SetCurvatureScaling(1)

        threshOutput = thresholdLevelSet.Execute(init_ls, self.image)
        print(thresholdLevelSet)


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










