import SimpleITK as sitk
import numpy as np


def apply_AnisotropicFilter(image, anisotropicFilter):
	image = anisotropicFilter.Execute(image)

	return image

def savePointList(seedPoints):
	try:
		#Save the user defined points in a .txt for automatimating testing (TODO)
		text_file = open("PointList.txt", "r+")
		text_file.readlines()
		text_file.write("%s\n" % seedPoints)
		text_file.close()
	except:
		print("Saving to .txt failed...")


def initiateFilters(scalingFactor):

	### LOAD FILTERS ###
	shrinkFilter = sitk.ShrinkImageFilter()
	shrinkFilter.SetShrinkFactors(scalingFactor)

	expandFilter = sitk.ExpandImageFilter()
	expandFilter.SetExpandFactors (scalingFactor)

	###PRE-PROCESSING FILTERS###
	anisotropicFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
	anisotropicFilter.SetNumberOfIterations(5)
	anisotropicFilter.SetTimeStep(0.01)
	anisotropicFilter.SetConductanceParameter(2)

	###POST-PROCESSING FILTERS###
	dilateFilter = sitk.BinaryDilateImageFilter()
	dilateFilter.SetKernelRadius(1)
	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(1)
	fillFilter = sitk.BinaryFillholeImageFilter()
	laplacianFilter = sitk.LaplacianSegmentationLevelSetImageFilter()
	laplacianFilter.SetReverseExpansionDirection (True)

	#Filter to attempt to remove the leakage areas
	connectedComponentFilter = sitk.ScalarConnectedComponentImageFilter()
	connectedComponentFilter.SetFullyConnected(True)
	connectedComponentFilter.SetDistanceThreshold(0.01) #Distance=Intensity difference NOT location
	### END FILTERS ###

	return(shrinkFilter,expandFilter,anisotropicFilter,dilateFilter,erodeFilter,fillFilter,laplacianFilter,connectedComponentFilter)

def ConfidenceConnectedSegmentation(image,seedPoint,x):
	#numberOfIterations = 25, multiplier = 2
	segXImg = sitk.ConfidenceConnected(image, seedPoint, numberOfIterations=2, multiplier=2, initialNeighborhoodRadius=3, replaceValue=x+1)
	return segXImg


def fillHoles(segXImg, dilateFilter, fillFilter, erodeFilter, x):
	#Apply the filters to the binary image
	dilateFilter.SetKernelRadius(1)
	segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)
	segXImg = fillFilter.Execute(segXImg, True, x+1)
	erodeFilter.SetKernelRadius(1)
	segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)	
	return segXImg


def LaplacianLevelSet(segXImg, image, laplacianFilter, x):
	#Additional post-processing (Lapacian Level Set Filter)
	#Binary image needs to have a value of 0 and 1/2*(x+1)
	segXImg = segXImg/(2)
	segXImg = laplacianFilter.Execute(segXImg, image)
	# sitk.Show(segXImg)	

	nda = sitk.GetArrayFromImage(segXImg)
	nda = np.asarray(nda)

	#Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
	nda[nda <= 0.1] = 0
	nda[nda != 0] = x+1

	segXImg = sitk.GetImageFromArray(nda)
	segXImg = sitk.Cast(segXImg, image.GetPixelID())
	segXImg.CopyInformation(image)

	return segXImg


def ConnectedComponent(segXImg, seedPoint, segmentation, connectedComponentFilter, erodeFilter, dilateFilter, x):

	segXImg = sitk.Cast(segXImg, 1) #Can't be a 32 bit float
	segXImg.CopyInformation(segmentation)

	#Try to remove leakage areas by first eroding the binary and
	#get the labels that are still connected to the original seed location

	erodeFilter.SetKernelRadius(3)
	segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)

	connectedXImg = connectedComponentFilter.Execute(segXImg)

	nda = sitk.GetArrayFromImage(connectedXImg)
	nda = np.asarray(nda)

	#In numpy an array is indexed in the opposite order (z,y,x)
	seedPoint = seedPoint[0]
	val = nda[seedPoint[2]][seedPoint[1]][seedPoint[0]]

	#Keep only the label that intersects with the seed point
	nda[nda != val] = 0 
	nda[nda != 0] = x+1

	segXImg = sitk.GetImageFromArray(nda)

	#Undo the earlier erode filter by dilating by same radius
	dilateFilter.SetKernelRadius(3)
	segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)

	segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())
	segXImg.CopyInformation(segmentation)

	return segXImg

def LeakageCheck(segXImg, segmentation, x):

	nda = sitk.GetArrayFromImage(segXImg)
	nda = np.asarray(nda)

	volume = len(nda[nda == x+1])
	maxVolume = 200000
	if volume > maxVolume:
		print('\033[97m' + "Failed check with volume "),
		print(volume)
		print("Skipping this label")
	else:
		print('\033[96m' + "Passed with volume "),
		print(volume)

		#Combine with the previous segmentations
		print('\033[96m' + "Combining Segmentations...")
		segmentation = segmentation + segXImg
		print("  ")

	return segmentation


def segmentationWall(image,inputLabel):
	#This takes a user defined label map and uses the voxels with an intensity of
	#1 to modify the original image to prevent the segmentation from crossing the boundary
	
	imageArray = np.asarray(sitk.GetArrayFromImage(image))
	labelArray = np.asarray(sitk.GetArrayFromImage(inputLabel))

	#Just a very large number to prevent segmentation from crossing the boundary
	imageArray[labelArray == 1] = 2000 

	#Take this array and make a SimpleITK image with it again
	image = sitk.GetImageFromArray(imageArray)

	#This may not be necessary
	image = sitk.Cast(image, inputLabel.GetPixelID())
	image.CopyInformation(inputLabel)

	return image

def ConfidenceConnectedSeg(image, inputLabel, seedPoints):

	#If inputLabel is not empty, use it to slightly modify the input image to prevent leakage
	image = segmentationWall(image,inputLabel)

	# sitk.Show(image)

	print('\033[92m' + "Saving Seed Points to txt file...")
	savePointList(seedPoints)


	scalingFactor = [2, 2, 1] #X,Y,Z

	print('\033[90m' + "Initiating filters...")
	(shrinkFilter,expandFilter,anisotropicFilter,dilateFilter,erodeFilter,fillFilter,laplacianFilter,connectedComponentFilter) = initiateFilters(scalingFactor)

	print('\033[90m' + "Scaling image down...")
	image = shrinkFilter.Execute(image)

	print('\033[91m' + "### SEGMENTING ###")
	print("  ")

	image = sitk.Cast(image,sitk.sitkFloat32)

	#Copy the orignal image for plotting later
	originalImage = sitk.Cast(sitk.RescaleIntensity(image), image.GetPixelID())

	#Create empty image to hold the segmentations
	segmentation = sitk.Image(image.GetSize(), image.GetPixelID())
	segmentation.CopyInformation(image)


	print('\033[92m' + "Applying the Anisotropic Filter...")
	image = apply_AnisotropicFilter(image, anisotropicFilter)

	#Need to round the seedPoints because integers are required for indexing
	seedPoints = np.array(seedPoints).astype(int)
	seedPoints = abs(seedPoints)
	seedPoints = seedPoints/scalingFactor #Scale the points down as well
	seedPoints = seedPoints.round() #Need to round it again for Python 3.3
	seedPoints = np.array(seedPoints).astype(int) #Just to be safe make it int again

	for x in range(0, len(seedPoints)):

		tempPoint = [seedPoints[x].tolist()]
		print('\033[94m' + "Current Seed Point: ")
		print(tempPoint)

		print('\033[93m' + "Segmenting via confidence connected...")
		segXImg = ConfidenceConnectedSegmentation(image,tempPoint,x)

		print('\033[93m' + "Filling Segmentation Holes...")
		segXImg = fillHoles(segXImg, dilateFilter, fillFilter, erodeFilter,x)

		segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())
		segXImg.CopyInformation(segmentation)
		
		print('\033[95m' + "Running Laplacian Level Set...")
		segXImg = LaplacianLevelSet(segXImg, image, laplacianFilter, x)

		print('\033[95m' + "Running Connected Component...")
		segXImg = ConnectedComponent(segXImg, tempPoint, segmentation, connectedComponentFilter, erodeFilter, dilateFilter, x)

		print('\033[96m' + "Checking volume for potential leakage... "), #Comma keeps printing on the same line
		segmentation = LeakageCheck(segXImg, segmentation, x)
		
	segmentation  = sitk.Cast(segmentation, sitk.sitkUInt16)
	originalImage = sitk.Cast(originalImage, sitk.sitkUInt16)

	try:
		# sitk.Show(segmentation)
		overlaidSegImage = sitk.LabelOverlay(originalImage, segmentation)
		sitk.Show(overlaidSegImage)
	except:
		print("Can't show the image with ImageJ! (Probably testing through Linux virtual machine)")

	print('\033[90m' + "Scaling image back...")
	segmentation = expandFilter.Execute(segmentation)


	return segmentation

if __name__ == '__main__':

    ### sitkConfidenceConnectedSeg.py executed as script starts here##
	##For the remote Linux automated testing##
	seedPoints = [[99, 206, 50]] #TODO Use the .txt file to load points
	# image = sitk.ReadImage("/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer5_VIBE.hdr")
	image = sitk.ReadImage("Volunteer5_VIBE.hdr")
	
	###

	#TODO Fix this: Need to flip the image if loading from the terminal vs. Slicer/Slicelet
	flipFilter = sitk.FlipImageFilter()
	flipFilter.SetFlipAxes((False,True,False))
	image = flipFilter.Execute(image)

	###Create an empty inputLabel image###

	nda = sitk.GetArrayFromImage(image)
	nda = np.asarray(nda)
	nda = nda*0
	inputLabel = sitk.Cast(sitk.GetImageFromArray(nda), image.GetPixelID())
	inputLabel.CopyInformation(image)
	##Done creating empty inputLabel##

	#Run the algorithm
	segmentation = ConfidenceConnectedSeg(image, inputLabel, seedPoints)



######################################################################
	#NOTES#

	# #Print colors#
	# HEADER = '\033[95m'
	# OKBLUE = '\033[94m'
	# OKGREEN = '\033[92m'
	# WARNING = '\033[93m'
	# FAIL = '\033[91m'
	# ENDC = '\033[0m'

	#Posibility to refine the Segmentation
	#http://www.itk.org/Doxygen46/html/classitk_1_1LaplacianSegmentationLevelSetImageFilter.html
	#http://www.itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1LaplacianSegmentationLevelSetImageFilter.html


	# fastMarchingFilter = sitk.FastMarchingUpwindGradientImageFilter()
	# fastMarchingFilter = sitk.FastMarchingBaseImageFilter()
	# fastMarchingFilter.SetTrialPoints (intPoints)
	# fastMarchingFilter.SetStoppingValue(100)
	# fastMarchingFilter.SetTopologyCheck(True)
	# print(fastMarchingFilter)
	# fastMarchingImg = fastMarchingFilter.Execute(image)

	#Run the Slicelet on Brent's MacBook
	#clear; /Applications/Slicer.app/Contents/MacOS/Slicer --no-main-window --python-script /Users/Brent/BoneSegmentation/BoneSegmentation.py

######################################################################
