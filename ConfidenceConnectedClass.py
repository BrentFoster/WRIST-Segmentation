import SimpleITK as sitk
import numpy as np

class BoneSeg(object):
	"""Class of BoneSegmentation. REQUIRED: BoneSeg(MRI_Image,inputLabelImage,SeedPoint)"""
	def __init__(self, image, inputLabel, seedPoint):
		self.image = image
		self.inputLabel = inputLabel
		self.seedPoint = seedPoint

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
		self.SetMaxVolume(200000) #Pixel counts (TODO change to mm^3)	
		self.SetBinaryMorphologicalRadius(1)	
		self.SetLaplacianExpansionDirection(True) #Laplacian Level Set
		self.SetConnectedComponentFullyConnected(True)	
		self.SetConnectedComponentDistance(0.01) 
		self.SeedListFilename = "PointList.txt"


	def SetImage(self, image):
		self.image = image
	
	def SetInputLabel(self, inputLabel):
		self.inputLabel = inputLabel

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

	def SetConnectedComponentFullyConnected(self, fullyConnected):
		self.connectedComponentFilter.SetFullyConnected(fullyConnected)	

	def SetConnectedComponentDistance(self, distanceThreshold):
		#Distance = Intensity difference NOT location distance
		self.connectedComponentFilter.SetDistanceThreshold(distanceThreshold) 

	###Main algorithm execution here###
	def Execute(self):
		#Convert images to float 32 first	
		self.inputLabelImage = sitk.Cast(self.inputLabel, sitk.sitkFloat32)
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

		print('\033[93m' + "Segmenting via confidence connected...")
		self.ConfidenceConnectedSegmentation()

		print('\033[93m' + "Filling Segmentation Holes...")
		self.HoleFilling()

		print('\033[95m' + "Running Laplacian Level Set...")
		self.LaplacianLevelSet()

		print('\033[95m' + "Running Connected Component...")
		self.ConnectedComponent()

		print('\033[96m' + "Checking volume for potential leakage... "), #Comma keeps printing on the same line
		self.LeakageCheck()

		print('\033[90m' + "Scaling image back...")
		self.scaleUpImage()

		print('\033[96m' + "Finished with seed point "),
		print(self.seedPoint)

		return self.segImg

	###Main algorithm end###

	def RoundSeedPoint(self):

		tempseedPoint = np.array(self.seedPoint).astype(int) #Just to be safe make it int again
		tempseedPoint = tempseedPoint[0]
		#Convert from physical to image domain
		tempFloat = [float(tempseedPoint[0]), float(tempseedPoint[1]), float(tempseedPoint[2])]
		#Convert from physical units to voxel coordinates
		tempVoxelCoordinates = self.image.TransformPhysicalPointToContinuousIndex(tempFloat)
		self.seedPoint = tempVoxelCoordinates

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
		self.image = self.expandFilter.Execute(self.segImg)
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

	def ConfidenceConnectedSegmentation(self):
		#numberOfIterations = 25, multiplier = 2
		self.segImg = sitk.ConfidenceConnected(self.image, self.seedPoint, numberOfIterations=self.ConfidenceConnectedIts,
		 multiplier=self.ConfidenceConnectedMultiplier, initialNeighborhoodRadius=self.ConfidenceConnectedRadius, replaceValue=1)
		return self

	def HoleFilling(self):
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

		nda = sitk.GetArrayFromImage(self.segImg)
		nda = np.asarray(nda)

		#Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
		nda[nda <= 0.1] = 0
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

		connectedXImg = self.connectedComponentFilter.Execute(self.segImg)

		nda = sitk.GetArrayFromImage(connectedXImg)
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


	def segmentationWall(self):
		#This takes a user defined label map and uses the voxels with an intensity of
		#1 to modify the original image to prevent the segmentation from crossing the boundary
		
		imageArray = np.asarray(sitk.GetArrayFromImage(self.image))
		labelArray = np.asarray(sitk.GetArrayFromImage(self.inputLabel))

		#Just a very large number to prevent segmentation from crossing the boundary
		imageArray[labelArray == 1] = 2000 

		#Take this array and make a SimpleITK image with it again
		self.image = sitk.GetImageFromArray(imageArray)

		#This may not be necessary
		self.image = sitk.Cast(self.image, inputLabel.GetPixelID())
		self.image.CopyInformation(self.inputLabel)

		return self


