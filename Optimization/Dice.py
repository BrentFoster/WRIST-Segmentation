import SimpleITK as sitk
import numpy as np

class DiceCalulator(object):
	"""docstring for DICE"""
	def __init__(self):
		super(DiceCalulator, self).__init__()
		# self.arg = arg

	def SetImages(self,GroundTruthImage, SegmentationImage, label=1):
		#Convert images to numpy arrays
		# GroundTruthImage = self.FlipImage(GroundTruthImage) #Flip for now

		self.GroundTruth = np.asarray(sitk.GetArrayFromImage(GroundTruthImage))
		self.Segmentation = np.asarray(sitk.GetArrayFromImage(SegmentationImage))
		#Label refers to the label of the object of interest on the binary image
		self.label = label

	def SetImageFiles(self,GroundTruthFile, SegmentationFile, label=1):
		self.LoadImages(GroundTruthFile, SegmentationFile)
		self.label = label

	def SetLabel(self, label):
		self.label = label

	def LoadImages(self,GroundTruthFile, SegmentationFile, label=1):
		GroundTruth  = sitk.ReadImage(GroundTruthFile)
		Segmentation = sitk.ReadImage(SegmentationFile)
		GroundTruth = self.FlipImage(GroundTruth)
		self.label = label

		#Convert images to numpy arrays
		self.GroundTruth = np.asarray(sitk.GetArrayFromImage(GroundTruth))
		self.Segmentation = np.asarray(sitk.GetArrayFromImage(Segmentation))


	def SaveStats(self, TextFileName):
		print("Save the statistics to a txt file here?")

	def Calculate(self):
		self.AllLabels()
		# try:
		dice = np.sum(self.Segmentation[self.GroundTruth==self.label])*2.0 / (np.sum(self.Segmentation) + np.sum(self.GroundTruth))
		# dice = round(dice * 100,2)
		return dice
		# except:
			# print('No images loaded. Please use SetImages or SetImageFiles first.')
	
	def AllLabels(self):
		self.GroundTruth[self.GroundTruth != 0] = 1
		self.Segmentation[self.Segmentation != 0] = 1
		return self

	def HausdorffDistance(self):
		print("Calculate the HausdorffDistanceImageFilter here")
		sitk.HausdorffDistanceImageFilter()

	def FlipImage(self, image):
		#Flip image(s) (if needed)
		flipFilter = sitk.FlipImageFilter()
		flipFilter.SetFlipAxes((False,True,False))
		image = flipFilter.Execute(image)

		return image

		

