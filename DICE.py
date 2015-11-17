import SimpleITK as sitk
import numpy as np

class DICE(object):
	"""docstring for DICE"""
	def __init__(self):
		super(DICE, self).__init__()
		# self.arg = arg

	def Execute(self, GroundTruthFile, SegmentationFile):
		print('\033[94m' + "Loading Images...")
		self.LoadImages(GroundTruthFile, SegmentationFile)

		dice = self.AllLabels()
		print("Dice: "),
		print(dice)
		

	def LoadImages(self,GroundTruthFile, SegmentationFile):
		GroundTruth = sitk.ReadImage(GroundTruthFile)
		Segmentation = sitk.ReadImage(SegmentationFile)
		GroundTruth = self.FlipImage(GroundTruth)

		#Convert images to numpy arrays
		self.GroundTruth = np.asarray(sitk.GetArrayFromImage(GroundTruth))
		self.Segmentation = np.asarray(sitk.GetArrayFromImage(Segmentation))


	def SaveStats(self):
		print("Save the statistics to a txt file here?")

	def DiceCalculate(self):
		dice = np.sum(self.Segmentation[self.GroundTruth==self.label])*2.0 / (np.sum(self.Segmentation) + np.sum(self.GroundTruth))
		dice = round(dice * 100,2)
		return dice

	def AllLabels(self):
		self.GroundTruth[self.GroundTruth != 4] = 0
		self.GroundTruth[self.GroundTruth != 0] = 1
		self.Segmentation[self.Segmentation != 0] = 1
		self.label = 1
		AllLabelDice = self.DiceCalculate()
		return AllLabelDice

	def HausdorffDistance(self):
		print("Calculate the HausdorffDistanceImageFilter here")
		sitk.HausdorffDistanceImageFilter()

	def FlipImage(self, image):
		#Flip image(s) (if needed)
		flipFilter = sitk.FlipImageFilter()
		flipFilter.SetFlipAxes((False,True,False))
		image = flipFilter.Execute(image)

		return image

		

