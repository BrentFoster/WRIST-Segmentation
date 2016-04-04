from __main__ import vtk, qt, ctk, slicer
import EditorLib

import SimpleITK as sitk
import sitkUtils
import numpy as np
import timeit

from sklearn.feature_extraction import image
from sklearn.cluster import spectral_clustering

#Allowed levels are CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging 

class Spectral_Clustering_Slicer:

    def __init__(self, parent):
        import string
        parent.title = "Spectral Clustering"
        parent.categories = ["Brent Modules"]
        parent.contributors = ["Brent Foster (UC Davis)"]
        parent.helpText = string.Template("Use this module to segment the eight carpal bones of the wrist. Input is a seed location defined by the user within each bone of interest. The Confidence Connected ITK Filter is then applied. ").substitute({
            'a': parent.slicerWikiUrl, 'b': slicer.app.majorVersion, 'c': slicer.app.minorVersion})
        parent.acknowledgementText = """
    Supported by NSF and NIH funding. Module implemented by Brent Foster.
    """
        self.parent = parent

class Spectral_Clustering_SlicerWidget:
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

        #
        # Image Downsample Scale
        # 
        self.label = qt.QLabel()
        self.label.setText("Image Downsampling: ")
        self.label.setToolTip(
            "Select the amount of downsampling (larger downsampling will compute faster, but the accuracy may be slightly reduced)")
        self.NumScalingSlider = ctk.ctkSliderWidget()
        self.NumScalingSlider.minimum = 1
        self.NumScalingSlider.maximum = 9
        self.NumScalingSlider.value = 4
        self.NumScalingSlider.connect('valueChanged(double)', self.onNumScalingSliderChange)
        frameLayout.addRow(self.label, self.NumScalingSlider)
        #Set default value
        self.NumScaling = self.NumScalingSlider.value


        #
        # Label Selection
        # 
        self.label = qt.QLabel()
        self.label.setText("Label to use: ")
        self.label.setToolTip(
            "Select which label to apply the spectral clustering to")
        self.LabelNumSlider = ctk.ctkSliderWidget()
        self.LabelNumSlider.minimum = 1
        self.LabelNumSlider.maximum = 10
        self.LabelNumSlider.value   = 1
        self.LabelNumSlider.connect('valueChanged(double)', self.onLabelNumSliderChange)
        frameLayout.addRow(self.label, self.LabelNumSlider)
        #Set default value
        self.LabelNum = self.LabelNumSlider.value



        #
        # Beta Selection
        # 
        self.label = qt.QLabel()
        self.label.setText("Beta: ")
        self.label.setToolTip(
            "Select the level of beta (for the distance mapping during graph creation)")
        self.BetaSlider = ctk.ctkSliderWidget()
        self.BetaSlider.minimum = 1
        self.BetaSlider.maximum = 10
        self.BetaSlider.value   = 1
        self.BetaSlider.connect('valueChanged(double)', self.onBetaSliderChange)
        frameLayout.addRow(self.label, self.BetaSlider)
        #Set default value
        self.Beta = self.BetaSlider.value



        # Compute button
        #
        self.computeButton = qt.QPushButton("Run Spectral Clustering")
        self.computeButton.toolTip = "Run spectral clustering on the input image to remove leakage areas."
        frameLayout.addWidget(self.computeButton)
        self.UpdatecomputeButtonState()
        self.computeButton.connect('clicked()', self.Spectral_Clustering)

    def onBetaSliderChange(self, newValue):
        self.Beta = newValue

    def onLabelNumSliderChange(self, newValue):
        self.LabelNum = newValue

    def onNumScalingSliderChange(self, newValue):
        self.NumScaling = newValue

    def UpdatecomputeButtonState(self):
        #Enable the 'Compute' button only if there is a selection to the input volume and markup list
        if self.inputSelector.currentNode():
            self.computeButton.enabled = True
        else:
            self.computeButton.enabled = False

    def onInputSelect(self, node):
        # Check to see if the compute button should be enabled/disabled now
        self.UpdatecomputeButtonState()


    def Spectral_Clustering(self):
        ''' Use spectral clustering on a binary image to remove the leakage areas '''
        logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

        label = self.LabelNum
        ScalingFactor = np.asarray([int(self.NumScaling), int(self.NumScaling), int(self.NumScaling)])

        slicer.app.processEvents()

        #Find the input image in Slicer and convert to a SimpleITK image type
        logging.info('Getting image from Slicer')
        imageID = self.inputSelector.currentNode()
        slicerImg = sitkUtils.PullFromSlicer(imageID.GetName())


        logging.info('Down sampling image')
        shrinkFilter = sitk.ShrinkImageFilter()
        shrinkFilter.SetShrinkFactors(ScalingFactor)

        slicerImgDS = shrinkFilter.Execute(slicerImg)


        logging.info('Converting to numpy array')
        npImg = np.asarray(sitk.GetArrayFromImage(slicerImgDS), dtype='float64')

        npImg[npImg != label] = 0
        npImg[npImg != 0] = 1

        mask = npImg
        mask[mask != 0] = 1

        mask = mask.astype(bool)
        npImg = npImg.astype(int)


        logging.info('Creating graph from image')

        # Convert the image into a graph with the value of the gradient on the edges.
        graph = image.img_to_graph(npImg, mask=mask)

        # Take a decreasing function of the gradient: an exponential
        # The smaller beta is, the more independent the segmentation is of the
        # actual image. For beta=1, the segmentation is close to a voronoi
        eps = 1e-6
        graph.data = np.exp(-self.Beta * graph.data / graph.data.std()) + eps

        logging.info('Running spectral clustering')
        labels = spectral_clustering(graph, n_clusters = 2, eigen_solver='arpack', n_init=30,  assign_labels='discretize')

        npLabel = -np.ones(mask.shape)
        npLabel[mask] = labels

        npLabel = npLabel + 1 # To have backgroun = 1 (instead of -1) for better automatic viewing in Slicer

        # Convert back to SimpleITK image type and upsample back to original size
        expandFilter = sitk.ExpandImageFilter()
        expandFilter.SetExpandFactors(ScalingFactor)

        Labelimg = sitk.Cast(sitk.GetImageFromArray(npLabel), slicerImg.GetPixelID())
        Labelimg = expandFilter.Execute(Labelimg)

        Labelimg.CopyInformation(slicerImg)

        # Output options in Slicer = {0:'background', 1:'foreground', 2:'label'}
        sitkUtils.PushToSlicer(Labelimg, imageID.GetName(),1, overwrite=False)

        logging.info('Done with spectral clustering')




if __name__ == "__main__":
    # TODO: need a way to access and parse command line arguments
    # TODO: ideally command line args should handle --xml

    import sys
    print(sys.argv)

    slicelet = BoneSegmentationSlicelet()