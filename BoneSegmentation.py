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

        # print("Image Data:")
        image = sitkUtils.PullFromSlicer('Volunteer5_VIBE')
        
        # print(seedPoints)

        

        # import os    
        # Load the sitkConfidenceConnectedSeg.py file
        # full_path = os.path.abspath('sitkConfidenceConnectedSeg.py')

        # image = sitkUtils.PullFromSlicer('Volunteer5_VIBE.hdr')

        #Transform the seed locations to voxel coordinates
        
        # print(image.TransformPhysicalPointToContinuousIndex([-105, -105, 30 ]))

        for i in range(numFids):
            seedPoints[i] = image.TransformPhysicalPointToContinuousIndex(seedPoints[i])




        import sitkConfidenceConnectedSeg
        segmentation = sitkConfidenceConnectedSeg.ConfidenceConnectedSeg(image,seedPoints)
        
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
