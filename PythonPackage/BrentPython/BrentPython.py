import SimpleITK as sitk
import multiprocessing
import numpy as np
import timeit

#Allowed levels are CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging 
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)

from sklearn.feature_extraction import image
from sklearn.cluster import spectral_clustering


def AddImages(sitkImageOne, sitkImageTwo, MakeBinary=True):
	''' Add two SimpleITK type images together and optionally binarize the resulting image '''

	ndaOne = np.asarray(sitk.GetArrayFromImage(sitkImageOne))
	ndaTwo = np.asarray(sitk.GetArrayFromImage(sitkImageTwo))

	ndaOutput = ndaOne + ndaTwo

	if MakeBinary == True:
		ndaOutput[ndaOutput != 0] = 1

	outputImg = sitk.Cast(sitk.GetImageFromArray(ndaOutput), sitkImageOne.GetPixelID())

	return outputImg



def OverlayImages(sitkImage, labelImage, opacity=0.9, backgroundValue=0):
	''' Apply a colormap to a label image and put it on top of the input image '''	

	# BinaryToLabelFilter = sitk.BinaryImageToLabelMapFilter()
	# labelImage = BinaryToLabelFilter.Execute(labelImage)

	overlayFilter = sitk.LabelOverlayImageFilter() 
	# print(labelImage)

	sitkImage = sitk.Cast(sitkImage, sitk.sitkUInt16)
	labelImage = sitk.Cast(labelImage, sitk.sitkUInt16)
	# labelImage.CopyInformation(sitkImage)

	ndaLabel = sitk.GetArrayFromImage(labelImage)
	ndaLabel = np.asarray(ndaLabel)
	ndaLabel = ndaLabel*700

	ndaImage = sitk.GetArrayFromImage(sitkImage)
	ndaImage = np.asarray(ndaImage)

	ndaOverlay = ndaLabel + ndaImage

	overlaidImg = sitk.Cast(sitk.GetImageFromArray(ndaOverlay), labelImage.GetPixelID())
	overlaidImg.CopyInformation(sitkImage)


	# overlaidImg = sitk.LabelOverlay(sitkImage, labelImage)

	# overlaidImg = overlayFilter.Execute(sitkImage, labelImage, opacity, backgroundValue)

	# overlaidImg = sitk.Cast(overlaidImg, sitk.sitkUInt8)

	# addFilter = sitk.AddImageFilter()

	# overlaidImg = addFilter.Execute(sitkImage, labelImage)

	return overlaidImg

def loadSeedPoints(filename):
	"""
	Function to load fiducial markers (seed points) saved in a .csv file
	exported from 3D Slicer. 
	Inputs: Filename to .csv filename
	Outputs: Dictionary with x, y, and z labels
	"""
	readfile = open(filename, "rU")
	readlines = readfile.readlines()
	x = []
	y = []
	z = []
	for i in range(3,len(readlines)):	
		currLine = readlines[i].split(",")
		x.append(currLine[1])
		y.append(currLine[2])
		z.append(currLine[3])
	return {'x':x, 'y':y ,'z':z}

def FlipImageVertical(image):
	""" Take an SimpleITK type image and flip vertically """
	flipFilter = sitk.FlipImageFilter()
	flipFilter.SetFlipAxes((False,True,False))
	image = flipFilter.Execute(image)
	return image

def FlipImageHorizontal(image):
	""" Take an SimpleITK type image and flip horizontally """
	flipFilter = sitk.FlipImageFilter()
	flipFilter.SetFlipAxes((True,False,False))
	image = flipFilter.Execute(image)
	return image

def FlipImageZ(image):
	""" Take an SimpleITK type image and flip in the Z direction """
	flipFilter = sitk.FlipImageFilter()
	flipFilter.SetFlipAxes((False,False,True))
	image = flipFilter.Execute(image)
	return image

def SaveSegmentation(image, filename, verbose = False):
	""" Take a SimpleITK type image and save to a filename (in analyze format) """
	if verbose == True:
		print("Saving segmentation to "),
		print(filename)
	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(image, filename, False)
	if verbose == True:
		print("Segmentation saved")

def PointsToVoxel(textSeeds, sitkImage):
	""" Take a dictionary of fiducial markers (from loadSeedPoints perhaps) and 
	convert from physical coordinates to the voxel coordinates of a given SimpleITK type image"""
	SeedPoints = []
	for i in range(0,len(textSeeds)): 
		#Convert from string to float
		tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
		#Convert from physical units to voxel coordinates
		tempVoxelCoordinates = sitkImage.TransformPhysicalPointToContinuousIndex(tempFloat)
		SeedPoints.append(tempVoxelCoordinates)
	return SeedPoints

def FillHoles(image, verbose=False):
	''' Fill the holes of a binary SimpleITK image type. Uses the scipy package 
	since the SimpleITK binary fill does not work well '''
	
	from scipy import ndimage

	image  = sitk.Cast(image, sitk.sitkUInt16)
	npImage = np.asarray(sitk.GetArrayFromImage(image), dtype=int)
	
	for i in range(0, npImage.shape[0]):
		npImage[i,:,:] = ndimage.binary_fill_holes(npImage[i,:,:]).astype(int)

		if verbose == True:
			progress = round(np.divide(float(i), float(npImage.shape[0])), 2)*100
			print(str(progress) + '%')

	img_Output = sitk.Cast(sitk.GetImageFromArray(npImage), image.GetPixelID())
	img_Output.CopyInformation(image)

	return img_Output



class AlgorithmTime(object):
	"""Simple class for determining the time a section of code took to execute."""
	def __init__(self, verbose = False):
		super(AlgorithmTime, self).__init__()
		self.verbose = verbose
	def start(self):
		self.start_time = timeit.default_timer()
	def end(self):
		#Determine how long the algorithm took to run
		# try:
		self.elapsed = timeit.default_timer() - self.start_time
		if (self.verbose == True):
			print("Elapsed Time (secs):"),
			print(str(round(self.elapsed,2)))	
		return self.elapsed
		# except:
			# print('Failed to calculate time. Did you remember to use start() first?')

class DiceCalulator(object):
	"""DiceCalulator salculates the Dice overlap coefficient of two images.
	Inputs: Filename to Image1, Filename to Image2 
	or Image1 and Image2 as numpy arrays.
	Output: Dice coefficient"""

	def __init__(self):
		super(DiceCalulator, self).__init__()

	def SetNumpyImages(self,GroundTruthImage, SegmentationImage):
		""" Takes two numpy arrays as inputs"""
		self.GroundTruth = GroundTruthImage
		self.Segmentation = SegmentationImage

	def SetSITKImages(self,GroundTruthImage, SegmentationImage):
		""" Takes two SimpleITK images as inputs"""
		#Convert images to numpy arrays
		self.GroundTruth = np.asarray(sitk.GetArrayFromImage(GroundTruthImage))
		self.Segmentation = np.asarray(sitk.GetArrayFromImage(SegmentationImage))

	def LoadImages(self,GroundTruthFile, SegmentationFile):
		GroundTruth = sitk.ReadImage(GroundTruthFile)
		Segmentation = sitk.ReadImage(SegmentationFile)

		#Convert images to numpy arrays
		self.GroundTruth = np.asarray(sitk.GetArrayFromImage(GroundTruth))
		self.Segmentation = np.asarray(sitk.GetArrayFromImage(Segmentation))


	def SaveStats(self, LogFileName):
		"""Save the Dice coefficient to the end of a txt file here"""
		try:
			#Save computation time in a log file
			text_file = open(LogFileName, "r+")
			text_file.readlines()
			text_file.write("%s\n" % self.dice)
			text_file.close()
		except:
			print("Failed writing log data to .txt file")


	def DiceCalculate(self, label = 0, numRound = 2):
		""" Calculate the Dice coefficient giving the two defined images.
		Optional values are the label (intensity on the binary image) for comparison else
		the computation will use all non-zero values; decimal places to round to (default of 2)"""
		if (label == 0):

			""" Convert all non-zero intensity to a value of one for global comparison """
			self.GroundTruth[self.GroundTruth != 0] = 1
			self.Segmentation[self.Segmentation != 0] = 1

			dice = np.sum(self.Segmentation[self.GroundTruth==1])*2.0 / (np.sum(self.Segmentation) + np.sum(self.GroundTruth))
			self.dice = round(dice,numRound)

		else:
			""" Use the user defined label to compute the Dice coefficient"""
			dice = np.sum(self.Segmentation[self.GroundTruth==label])*2.0 / (np.sum(self.Segmentation) + np.sum(self.GroundTruth))
			self.dice = round(dice,numRound)
		return self.dice


	def HausdorffDistance(self, returnHD = True, returnMeanHD = False):
		"""Calculate the Hausdorff distance from the two previously given images. 
		Options to return the Hausdorff distance and/or the average Hausdorff distance."""
		
		#Need to convert from numpy arrays to SimpleITK images 
		GroundTruth = sitk.Cast(sitk.GetImageFromArray(self.GroundTruth), sitk.sitkUInt16)
		Segmentation = sitk.Cast(sitk.GetImageFromArray(self.Segmentation), sitk.sitkUInt16)

		HausdorffFilter = sitk.HausdorffDistanceImageFilter()
		HausdorffFilter.Execute(GroundTruth, Segmentation)
		
		if (returnHD == True & returnMeanHD == False):
			return HausdorffFilter.GetHausdorffDistance()

		elif (returnHD == False & returnMeanHD == True):
			return HausdorffFilter.GetAverageHausdorffDistance()

		elif (returnHD == True & returnMeanHD == True):
			return (HausdorffFilter.GetHausdorffDistance(), \
				HausdorffFilter.GetAverageHausdorffDistance())

	def ConvertToOneZeros(self):
		""" Convert the two images to zeros and ones """
		self.GroundTruth[self.GroundTruth != 0] = 1
		self.Segmentation[self.Segmentation != 0] = 1

class Multiprocessor(object):
	"""Helper class for sliptting a segmentation class (such as from SimpleITK) into
	several logical cores in parallel. Requires: SegmentationClass, Seed List, SimpleITK Image"""
	def __init__(self):
		# super(ClassName, self).__init__()
		self = self

	def Execute(self, segmentationClass, seedList, MRI_Image, parameter=0, verbose = False):
		self.segmentationClass = segmentationClass
		self.seedList = seedList
		self.MRI_Image = MRI_Image
		self.parameter = parameter
		self.verbose = verbose #Show output to terminal or not

		try:
			#Convert to voxel coordinates
			self.RoundSeedPoints() 
		except:
			pass #The list of seeds was already converted to voxel coordinates

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
		num_CPUs = multiprocessing.cpu_count() #Might be better to subtract 1 since OS needs one
		# num_CPUs = 1
		if self.verbose == True:
			print('\033[94m' + "Number of CPUs = "),
			print(num_CPUs)

		if (len(self.seedList) <= num_CPUs):
			jobOrder = range(0, len(self.seedList))
			if self.verbose == True:
				print(jobOrder)
			self.segmentationArray = self.RunMultiprocessing(jobOrder)

		elif (len(self.seedList) > num_CPUs):
			if self.verbose == True:
				print('\033[93m' + "Splitting jobs since number of CPUs < number of seed points")
			#Run the multiprocessing several times since there wasn't enough CPU's before
			jobOrder = self.SplitJobs(range(len(self.seedList)), num_CPUs)
			if self.verbose == True:
				print(jobOrder)
			for x in range(len(jobOrder)):
				self.segmentationArray = self.segmentationArray + (x+1)*self.RunMultiprocessing(jobOrder[x])

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
			p = multiprocessing.Process(target=f, args=(self.MRI_Array, self.seedList[x],q, self.parameter,))
			p.start()
			procs.append(p) #List of current processes

		tempArray = self.segmentationArray
		if self.verbose == True:
			print('\033[96m' + "Printing multiprocessing queue:")
		for i in range(len(jobOrder)):
			#Outputs an array (due to multiprocessing 'pickle' constraints)
			tempArray = tempArray + q.get() 
		# Wait for all worker processes to finish by using .join()
		for p in procs:
			p.join()
			p.terminate() #Unix

		if self.verbose == True:
			print('\033[96m' + 'Finished with processes:'),
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

	#Need to convert to voxel coordinates since we pass only the array due to a 'Pickle' error
	#with the multiprocessing library and the ITK image type which means the header information
	#is lost
	def RoundSeedPoints(self):
		seeds = []
		for i in range(0,len(self.seedList)): #Select which bone (or all of them) from the csv file
			#Convert from string to float
			tempFloat = [float(self.seedList['x'][0]), float(self.seedList['y'][1]), float(self.seedList['z'][2])]
			#Convert from physical units to voxel coordinates
			tempVoxelCoordinates = self.MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
			seeds.append(tempVoxelCoordinates)
		self.seedList = seeds
		return self

def f(MRI_Array, SeedPoint,q, parameter):
	""" Function to be used with the Multiprocessor class (needs to be its own function 
		and not part of the same class to avoid the 'Pickle' type errors. """
	# import BoneSegmentation as BrentSeg #This seems to be needed for Windows
	# segmentationClass = BrentSeg.BoneSeg()
	segmentationClass = BoneSeg()

	#Change some parameter(s) of the segmentation class for the optimization
	if (parameter != 0): 
		#Set the threshold and then compute/save the Dice coefficient
		segmentationClass.SetLevelSetUpperThreshold(parameter[0])
		segmentationClass.SetLevelSetIts(parameter[1])
		segmentationClass.SetLevelSetError(parameter[2])

	output = segmentationClass.Execute(MRI_Array,[SeedPoint])
	q.put(output)
	q.close()

class BoneSeg(object):
	"""Class of BoneSegmentation for segmenting the bones of the wrist from MRI. 
	REQUIRED: SimpleITK type MRI_Image and an array of SeedPoints"""
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
		#Set the deafult values 
		self.SetDefaultValues()

	def SetDefaultValues(self):
		#Set the default values of all the parameters here
		self.SetScalingFactor([1,1,1]) #X,Y,Z

		# self.SetAnisotropicIts(5)
		# self.SetAnisotropicTimeStep(0.01)
		# self.SetAnisotropicConductance(2)
		# self.SetConfidenceConnectedIts(0)
		# self.SetConfidenceConnectedMultiplier(0.5)
		# self.SetConfidenceConnectedRadius(2)
		# self.SetLaplacianExpansionDirection(True) #Laplacian Level Set
		# self.SetLaplacianError(0.01)
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

	def Execute(self, image, seedPoint, verbose = False):

		self.verbose = verbose #Optional argument to output text to terminal

		self.image = image
		self.seedPoint = seedPoint
		try:
			#Convert from the arrays back into ITK images (due to multiprocessing)
			self.image = sitk.Cast(sitk.GetImageFromArray(self.image), sitk.sitkFloat32)
			self.image = self.FlipImage(self.image) #Flip the MRI
		except:
			self.image = image
			self.image = self.FlipImage(self.image) #Flip the MRI

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

		if self.verbose == True:
			print('\033[93m' + "Filling Segmentation Holes...")
		self.HoleFilling()

		if self.verbose == True:
			print('\033[90m' + "Scaling image back...")
		self.scaleUpImage()

		# print('\033[90m' + "Eroding image slightly...")
		# self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)


		#Return an array instead of a sitk.Image due to contraints on the multiprocessing library
		nda = sitk.GetArrayFromImage(self.segImg)
		nda = np.asarray(nda, dtype=np.int32)
		
		if self.verbose == True:
			print('\033[96m' + "Finished with seed point "),
			print(self.seedPoint)
		
		return  nda 

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
		self.dilateFilter.SetKernelRadius(3)
		
		self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
		self.segImg = self.dilateFilter.Execute(self.segImg, 0, 1, False)
		self.segImg = self.fillFilter.Execute(self.segImg, True, 1)
		# self.segImg = self.erodeFilter.Execute(self.segImg, 0, 1, False)	
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

		##Check the image type of self.segImg and image are the same (for Python 3.3 and 3.4)

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

		#Create the seed image
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

class SpectralClutering(object):
	''' Use spectral clustering on a binary image to remove the leakage areas '''

	def __init__(self):
		super(SpectralClutering, self).__init__()

		# Set some default values
		self.n_clusters = 2
		self.ScalingFactor = [4, 4, 4]

	def AddSeedLocation(self, seedPoint):
		''' Seed location to choose which cluter to keep '''
		self.seedPoint = seedPoint

	def SetScaling(self, ScalingFactor):
		self.ScalingFactor = ScalingFactor

	def SetNumClusters(self, n_clusters):
		self.n_clusters = n_clusters

	def Execute(self, sitkImg):
		''' Run the spectral clustering method '''
		logging.info('Down sampling image')
		shrinkFilter = sitk.ShrinkImageFilter()
		shrinkFilter.SetShrinkFactors(self.ScalingFactor)

		sitkImg = shrinkFilter.Execute(sitkImg)

		logging.info('Converting to numpy array')

		npImg = sitk.GetArrayFromImage(sitkImg)

		mask = npImg
		mask[mask != 0] = 1

		mask = mask.astype(bool)
		npImg = npImg.astype(int)

		logging.info('Creating graph from image')

		# Convert the image into a graph with the value of the gradient on the edges.
		graph = image.img_to_graph(npImg, mask=mask)

		# Take a decreasing function of the gradient
		graph.data = np.exp(-graph.data / graph.data.std())

		logging.info('Running spectral clustering')
		labels = spectral_clustering(graph, self.n_clusters, eigen_solver='arpack')

		logging.info('Spectral clustering post-processing')

		npLabel = -np.ones(mask.shape)
		npLabel[mask] = labels

		# Keep only the label that intersects with the seed point location
		for i in range(0, len(self.seedPoint)):
			self.seedPoint[i] = round(self.seedPoint[i]/self.ScalingFactor[0],0)

		cluster_index = npLabel[self.seedPoint[2], self.seedPoint[1], self.seedPoint[0]]
		
		tempLabel = npLabel*0
		tempLabel[npLabel == cluster_index] = 1
		npLabel = tempLabel


		# Convert back to SimpleITK image type and upsample back to original size
		expandFilter = sitk.ExpandImageFilter()
		expandFilter.SetExpandFactors(self.ScalingFactor)

		sitkImg = sitk.Cast(sitk.GetImageFromArray(npLabel), sitkImg.GetPixelID())
		sitkImg = expandFilter.Execute(sitkImg)

		return sitkImg



