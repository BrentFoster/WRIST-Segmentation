
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
class Flip_Image_Slicer:

    def __init__(self, parent):
        import string
        parent.title = "Flip Image"
        parent.categories = ["Brent Modules"]
        parent.contributors = ["Brent Foster (UC Davis)"]
        parent.helpText = string.Template("Use this module to segment the eight carpal bones of the wrist. Input is a seed location defined by the user within each bone of interest. The Confidence Connected ITK Filter is then applied. ").substitute({
            'a': parent.slicerWikiUrl, 'b': slicer.app.majorVersion, 'c': slicer.app.minorVersion})
        parent.acknowledgementText = """
    Supported by NSF and NIH funding. Module implemented by Brent Foster.
    """
        self.parent = parent

class Flip_Image_SlicerWidget:
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
        self.inputVolumeSelectorLabel.setToolTip("Select the input volume to be flipped")
        self.inputSelector = slicer.qMRMLNodeComboBox()
        self.inputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        self.inputSelector.noneEnabled = False
        self.inputSelector.selectNodeUponCreation = True
        self.inputSelector.setMRMLScene(slicer.mrmlScene)
        frameLayout.addRow(
        self.inputVolumeSelectorLabel, self.inputSelector)
        self.inputSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onInputSelect)

        # Compute button
        #
        self.computeButton = qt.QPushButton("Flip Image")
        self.computeButton.toolTip = "Flip the image vertically"
        frameLayout.addWidget(self.computeButton)
        self.UpdatecomputeButtonState()
        self.computeButton.connect('clicked()', self.onCompute)




        # #
        # # Output Volume Label
        # #
        # self.outputVolumeSelectorLabel = qt.QLabel()
        # self.outputVolumeSelectorLabel.setText("Output Volume: ")
        # self.outputVolumeSelectorLabel.setToolTip("Select the output volume to save the segmentation to")
        # self.outputSelector = slicer.qMRMLNodeComboBox()
        # self.outputSelector.nodeTypes = ("vtkMRMLScalarVolumeNode", "")
        # self.outputSelector.noneEnabled = True
        # self.outputSelector.selectNodeUponCreation = True
        # self.outputSelector.setMRMLScene(slicer.mrmlScene)
        # frameLayout.addRow(self.outputVolumeSelectorLabel, self.outputSelector)
  
    def UpdatecomputeButtonState(self):
        #Enable the 'Compute' button only if there is a selection to the input volume and markup list
        if self.inputSelector.currentNode():
            self.computeButton.enabled = True
        else:
            self.computeButton.enabled = False

    def onInputSelect(self, node):
        #Test to see if the Compute button should be enabled/disabled
        self.UpdatecomputeButtonState()
        # self.ImageNode = node

    def onCompute(self):
        slicer.app.processEvents()

        #Find the input image in Slicer and convert to a SimpleITK image type
        imageID = self.inputSelector.currentNode()
        image = sitkUtils.PullFromSlicer(imageID.GetName())

        npI = np.asarray(sitk.GetArrayFromImage(image), dtype='float64')

        npI = np.fliplr(npI)

        FlippedImage = sitk.Cast(sitk.GetImageFromArray(npI), image.GetPixelID())
        FlippedImage.CopyInformation(image)

        # Output options in Slicer = {0:'background', 1:'foreground', 2:'label'}
        sitkUtils.PushToSlicer(FlippedImage,imageID.GetName(),0, overwrite=True)

if __name__ == "__main__":
    # TODO: need a way to access and parse command line arguments
    # TODO: ideally command line args should handle --xml

    import sys
    print(sys.argv)

    slicelet = BoneSegmentationSlicelet()