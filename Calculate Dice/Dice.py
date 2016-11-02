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

		self.GroundTruth_sitk = GroundTruthImage
		self.Segmentation_sitk =SegmentationImage

		self.GroundTruth_np = np.asarray(sitk.GetArrayFromImage(GroundTruthImage))
		self.Segmentation_np = np.asarray(sitk.GetArrayFromImage(SegmentationImage))
		#Label refers to the label of the object of interest on the binary image
		self.label = label


	def SetImageFiles(self,GroundTruthFile, SegmentationFile, label=1):
		self.LoadImages(GroundTruthFile, SegmentationFile)
		self.label = label

	def SetLabel(self, label):
		self.label = label

	def LoadImages(self,GroundTruthFile, SegmentationFile, label=0):
		GroundTruth = sitk.ReadImage(GroundTruthFile)
		Segmentation = sitk.ReadImage(SegmentationFile)
		GroundTruth = self.FlipImage(GroundTruth)
		self.label = label

		#Convert images to numpy arrays
		self.GroundTruth_np = np.asarray(sitk.GetArrayFromImage(GroundTruth))
		self.Segmentation_np = np.asarray(sitk.GetArrayFromImage(Segmentation))


	def SaveStats(self, TextFileName):
		print("Save the statistics to a txt file here?")

	def Calculate(self):
		# Remove the extra labels from the segmentation image
		self.AllLabels()

		# try:
		dice = np.sum(self.Segmentation_np[self.GroundTruth_np==self.label])*2.0 / (np.sum(self.Segmentation_np) + np.sum(self.GroundTruth_np))
		# dice = round(dice * 100,2)
		return dice
		# except:
			# print('No images loaded. Please use SetImages or SetImageFiles first.')
	
	def AllLabels(self):
		if self.label == 0:
			self.GroundTruth_np[self.GroundTruth_np != self.label] = 1
			self.Segmentation_np[self.Segmentation_np != self.label] = 1
		else:
			self.GroundTruth_np[self.GroundTruth_np != self.label] = 0
			self.Segmentation_np[self.Segmentation_np != self.label] = 0

		return self

	def HausdorffDistance(self):
		print("Calculating Hausdorff Distance...")
		# Remove the extra labels from the segmentation image
		self.AllLabels()

		# Need to convert to SimpleITK image type for the SimpleITK Hausdorff Distance Fitler 
		GroundTruth_Label = sitk.Cast(sitk.GetImageFromArray(self.GroundTruth_np), self.GroundTruth_sitk.GetPixelID())
		GroundTruth_Label.CopyInformation(self.GroundTruth_sitk)

		Segmentation_Label = sitk.Cast(sitk.GetImageFromArray(self.Segmentation_np), self.Segmentation_sitk.GetPixelID())
		Segmentation_Label.CopyInformation(self.Segmentation_sitk)


		HausdorffFilter = sitk.HausdorffDistanceImageFilter()
		HausdorffFilter.Execute(GroundTruth_Label, Segmentation_Label)
		
		Hausdorff_Distance = HausdorffFilter.GetHausdorffDistance()
		AverageHausdorffDistance = HausdorffFilter.GetAverageHausdorffDistance()


		return Hausdorff_Distance, AverageHausdorffDistance


	def FlipImage(self, image):
		#Flip image(s) (if needed)
		flipFilter = sitk.FlipImageFilter()
		flipFilter.SetFlipAxes((False,True,False))
		image = flipFilter.Execute(image)

		return image

		

