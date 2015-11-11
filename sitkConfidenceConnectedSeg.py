import SimpleITK as sitk
import numpy as np

def ConfidenceConnectedSeg(image, seedPoints):

	#Save the user defined points in a .txt for automatimating testing (TODO)
	text_file = open("PointList.txt", "r+")
	text_file.readlines()
	text_file.write("%s\n" % seedPoints)
	text_file.close()


	scalingFactor = [2, 2, 1] #X,Y,Z

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

	#Filter to attempt to remove the leakage areas
	connectedComponentFilter = sitk.ScalarConnectedComponentImageFilter()
	connectedComponentFilter.SetFullyConnected(True)
	connectedComponentFilter.SetDistanceThreshold(0.01) #Distance=Intensity difference NOT location

	### END FILTERS ###


	print('\033[90m' + "Scaling image down...")
	image = shrinkFilter.Execute(image)

	print('\033[91m' + "### SEGMENTING ###")
	print("  ")

	# sitkFloat32
	image = sitk.Cast(image,sitk.sitkFloat32)

	#Copy the orignal image for plotting later
	originalImage = sitk.Cast(sitk.RescaleIntensity(image), image.GetPixelID())

	#Create empty image to hold the segmentations
	segmentation = sitk.Image(image.GetSize(), image.GetPixelID())
	segmentation.CopyInformation(image)

	


	###Apply the Anisotropic Filter###
	print('\033[92m' + "Applying the Anisotropic Filter...")
	# image = anisotropicFilter.Execute(image)
	print("  ")


	# sitk.Show(image)


	#Need to round the seedPoints because integers are required for indexing
	seedPoints = np.array(seedPoints).astype(int)
	seedPoints = abs(seedPoints)
	seedPoints = seedPoints/scalingFactor #Scale the points down as well

	for x in range(0, len(seedPoints)):

		tempPoint = [seedPoints[x].tolist()]
		print('\033[94m' + "Current Seed Point: ")
		print(tempPoint)

		#numberOfIterations = 25, multiplier = 2
		segXImg = sitk.ConfidenceConnected(image, tempPoint, numberOfIterations=20, multiplier=2, initialNeighborhoodRadius=2, replaceValue=x+1)

		print('\033[93m' + "Filling Segmentation Holes...")
		#Apply the filters to the binary image
		dilateFilter.SetKernelRadius(1)
		segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)
		segXImg = fillFilter.Execute(segXImg, True, x+1)
		erodeFilter.SetKernelRadius(1)
		segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)

		###TEMP###
		# segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())
		# segXImg.CopyInformation(segmentation)
		# segmentation = segmentation + segXImg
		###TEMP###

		print('\033[95m' + "Running Connected Component...")

		#Try to remove leakage areas by first eroding the binary and
		#get the labels that are still connected to the original seed location

		erodeFilter.SetKernelRadius(1)
		segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)

		connectedXImg = connectedComponentFilter.Execute(segXImg)

		nda = sitk.GetArrayFromImage(connectedXImg)
		nda = np.asarray(nda)

		#In numpy an array is indexed in the opposite order (z,y,x)
		tempPoint = tempPoint[0]
		val = nda[tempPoint[2]][tempPoint[1]][tempPoint[0]]
		#TODO Check this
		nda[nda != val] = 0 #Keep only the label that intersects with the seed point
		nda[nda != 0] = x+1

		segXImg = sitk.GetImageFromArray(nda)
		
		dilateFilter.SetKernelRadius(1)
		segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)

		segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())
		segXImg.CopyInformation(segmentation)

		print('\033[96m' + "Checking volume for potential leakage... "), #Comma keeps printing on the same line
		volume = len(nda[nda == x+1])
		maxVolume = 90000
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


	segmentation = sitk.Cast(segmentation, sitk.sitkUInt16)
	originalImage = sitk.Cast(originalImage, sitk.sitkUInt16)

	try:
		sitk.Show(segmentation)

		overlaidSegImage = sitk.LabelOverlay(originalImage, segmentation)
		# nda = sitk.GetArrayFromImage(overlaidSegImage)
		# nda = nda[:,:,:,0] + nda[:,:,:,1] + nda[:,:,:,2]
		# overlaidSegImage = sitk.GetImageFromArray(nda)

		sitk.Show(overlaidSegImage)
	except:
		print("Can't show the image with ImageJ! (Probably testing through Linux virtual machine)")



	print('\033[90m' + "Scaling image back...")
	segmentation = expandFilter.Execute(segmentation)


	return segmentation

if __name__ == '__main__':
    ### sitkConfidenceConnectedSeg.py executed as script ##

	#Create a list for the seed points
	# seedPoints = [[130, 184, 42], [175.987, 90.123, 31.0], [100, 200, 47]]

	#Test for leakage
	# seedPoints = [[99, 206, 50]]
	# seedPoints = [[141, 290, 119]]

	#Could load the points from a saved text file (PointList.txt)
	seedPoints = [(-373.1014570105204, -615.4203026139975, 110.3448307613415), (-204.98551149614664, -670.5623327427121, 110.3448307613415), (-346.2029057282207, -667.8724776144821, 134.48276249038494), (-266.8521794454362, -698.8058115891268, 134.48276249038494), (-209.02029418849162, -679.976825691517, 141.3793144129688), (-242.64348329136638, -623.4898679986875, 141.3793144129688), (-288.37102047127604, -626.1797231269175, 172.41379806459608)]
	# seedPoints = [(-266.8521794454362, -698.8058115891268, 134.48276249038494)]
	# seedPoints = [(342, 678, 142)]
	# seedPoints = [(-204.98551149614664, -670.5623327427121, 110.3448307613415)]
	#Read in image
	# image = sitk.ReadImage("Volunteer5_VIBE.hdr")

	image = sitk.ReadImage("/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer2_VIBE.hdr")


	#Need to flip the image if loading from the terminal vs. Slicer/Slicelet. Need to fix this

	flipFilter = sitk.FlipImageFilter()
	flipFilter.SetFlipAxes((False,True,False))
	image = flipFilter.Execute(image)

	segmentation = ConfidenceConnectedSeg(image, seedPoints)






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
