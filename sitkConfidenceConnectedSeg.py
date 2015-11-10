import SimpleITK as sitk
import numpy as np

def ConfidenceConnectedSeg(image, seedPoints):

	print('\033[91m' + "### SEGMENTING ###")
	print("  ")
	
	# sitkFloat32
	image = sitk.Cast(image,sitk.sitkFloat32)

	#Copy the orignal image for plotting later
	originalImage = sitk.Cast(sitk.RescaleIntensity(image), image.GetPixelID())

	#Create empty image to hold the segmentations
	segmentation = sitk.Image(image.GetSize(), image.GetPixelID())
	segmentation.CopyInformation(image)

	###PRE-PROCESSING FILTERS###
	anisotropicFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
	anisotropicFilter.SetNumberOfIterations(10)
	anisotropicFilter.SetTimeStep(0.01)
	anisotropicFilter.SetConductanceParameter(3)

	###POST-PROCESSING FILTERS###
	dilateFilter = sitk.BinaryDilateImageFilter()
	dilateFilter.SetKernelRadius(1)
	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(1)
	fillFilter = sitk.BinaryFillholeImageFilter()
	



	###Apply the Anisotropic Filter###
	print('\033[92m' + "Applying the Anisotropic Filter...")
	image = anisotropicFilter.Execute(image)
	print("  ")


	#Need to round the seedPoints because integers are required for indexing
	seedPoints = np.array(seedPoints).astype(int)
	seedPoints = abs(seedPoints)

	for x in range(0, len(seedPoints)):

		tempPoint = [seedPoints[x].tolist()]
		print('\033[94m' + "Current Seed Point: ")
		print(tempPoint)

		segXImg = sitk.ConfidenceConnected(image, tempPoint, numberOfIterations=10, multiplier=2,	initialNeighborhoodRadius = 5, replaceValue=x+1)


		print('\033[93m' + "Filling Segmentation Holes...")
		#Apply the filters to the binary image
		segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)
		segXImg = fillFilter.Execute(segXImg, True, x+1)
		segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)
		

		segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())

		#Combine with the previous segmentations
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

	return segmentation

if __name__ == '__main__':
    ### sitkConfidenceConnectedSeg.py executed as script ##

	#Create a list for the seed points
	seedPoints = [[130, 184, 42], [175.987, 90.123, 31.0], [100, 200, 47]]
	# seedPoints = [[130.1238, 184.98213, 41.123], [175.987, 90.123, 31.0]]
	
	#Read in image
	image = sitk.ReadImage("Volunteer5_VIBE.hdr")

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

	# clear; ./Slicer --no-main-window --python-script /Users/Brent/BoneSegmentation/SlicerModule/BoneSegmentation/BoneSegmentation.py 
	# /Applications/Slicer.app/Contents/MacOS/Slicer --no-main-window --python-script /Users/Brent/BoneSegmentation/SlicerModule/BoneSegmentation/BoneSegmentation.py 

######################################################################