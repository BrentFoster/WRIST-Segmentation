# clear; ./Slicer --no-main-window --python-script /Users/Brent/BoneSegmentation/SlicerModule/BoneSegmentation/BoneSegmentation.py 


# /Applications/Slicer.app/Contents/MacOS/Slicer --no-main-window --python-script /Users/Brent/BoneSegmentation/SlicerModule/BoneSegmentation/BoneSegmentation.py 


import SimpleITK as sitk
import numpy as np


# Import additional Python modules? (Important to keep SimpleITK version the same 
# as the local copy)
# import sys 
# sys.path.insert(0,"/Library/Python/2.7/site-packages") 


# print(sitk.__version__)

# import progressbar
# from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
# 	FileTransferSpeed, FormatLabel, Percentage, \
# 	ProgressBar, ReverseBar, RotatingMarker, \
# 	SimpleProgress, Timer, AdaptiveETA, AbsoluteETA, AdaptiveTransferSpeed


# 0.9.0.dev381
# import pkg_resources
# print(pkg_resources.get_distribution("SimpleITK").version)

# print(help('modules'))

# import pip #needed to use the pip functions
# for i in pip.get_installed_distributions(local_only=True):
#     print(i)






def ConfidenceConnectedSeg(image, seedPoints):

	print("### SEGMENTING ###")
	# print(seedPoints)
	
	image = sitk.Cast(image,sitk.sitkUInt16)

	try:
		img_T1_255 = sitk.Cast(sitk.RescaleIntensity(image), sitk.sitkUInt8)
		#Create empty image to hold the segmentations
		segmentation = sitk.Image(image.GetSize(), image.GetPixelID())
		segmentation.CopyInformation(image)
	except: 
		print("Casting of img_T1_255 failed...")


	#Create empty segmentation image
	segmentation = image*0

	#Create empty seed image for the level set filter to use
	seedImage = image*0

	##POST-PROCESSING FILTERS##
	# Create the filters for filling any holes
	dilateFilter = sitk.BinaryDilateImageFilter()
	dilateFilter.SetKernelRadius(1)
	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(1)
	fillFilter = sitk.BinaryFillholeImageFilter()


	######################################################################

	# intPoints = [[130, 184, 41], [175, 90, 31],[100, 200, 44],[90, 225, 61],[100, 200, 72],[75, 200, 85],[45, 200, 100]]

	# fastMarchingFilter = sitk.FastMarchingUpwindGradientImageFilter()
	# fastMarchingFilter = sitk.FastMarchingBaseImageFilter()
	# fastMarchingFilter.SetTrialPoints (intPoints)
	# fastMarchingFilter.SetStoppingValue(100)
	# fastMarchingFilter.SetTopologyCheck(True)
	# print(fastMarchingFilter)
	# fastMarchingImg = fastMarchingFilter.Execute(image)

	# segPixels = sitk.GetArrayFromImage(fastMarchingImg)
	# segPixels[segPixels > 10] = 10
	# fastMarchingImg = sitk.GetImageFromArray(segPixels)
	# sitk.Show(fastMarchingImg)

	######################################################################

	# seedPoints = [[130, 184, 41], [175, 90, 31],[100, 200, 44],[90, 225, 61],[100, 200, 72],[75, 200, 85],[45, 200, 100]]

	#Need to round the seedPoints because integers are required for indexing


	# seedPoints = [[130.123, 184.987213, 41.12307], [175.123, 90.0993123, 31],[100, 200, 44],[90, 225, 61],[100, 200, 72],[75, 200, 85],[45, 200, 100]]




	seedPoints = np.array(seedPoints).astype(int)

	seedPoints = abs(seedPoints)


	numPoints = len(seedPoints)
	# roundedSeedPoints = [[0, 1, 2]]*numPoints
	# roundedSeedPoints = np.array(roundedSeedPoints)
	# # roundedSeedPoints = seedPoints
	# for j in range(0,3):
	# 	for i in range(0,numPoints):
	# 		roundedSeedPoints[i][j] = int(seedPoints[i][j])	

	# print(roundedSeedPoints)
	# print(type(roundedSeedPoints))

	# seedPoints = np.array(roundedSeedPoints)
	# seedPoints


	# print(seedPoints)
	# print(type(seedPoints))


	# pbar = ProgressBar(widgets=[Percentage(), Bar()], max_value=(numPoints+1)*5).start()


	print("Final Seed Points:")
	print(seedPoints)
	for x in range(0, numPoints):

		# pbar.update(x*5+0.0001)
		# tempPoint = [(seedPoints[x])]

		# tempPoint = [[130, 184, 41]]
		# print(tempPoint)

		tempPoint = [seedPoints[x].tolist()]
		# tempPoint = [tuple(seedPoints[x])]
		# print(tempPoint)
		# print(type(tempPoint))

		# tempPoint = [[(-83, -71, 0)]]


		segXImg = sitk.ConfidenceConnected(image, tempPoint, numberOfIterations=10, multiplier=1.7,	initialNeighborhoodRadius = 5, replaceValue=x+1)

		# pbar.update(x*5+1)
		segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)
		# pbar.update(x*5+2)
		segXImg = fillFilter.Execute(segXImg, True, x+1)
		# pbar.update(x*5+3)
		segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)
		# pbar.update(x*5+4)
		segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())
		# pbar.update(x*5+5)
		segmentation = segmentation + segXImg

		
	# pbar.finish()

	# segmentation = segmentation*100`
	segmentation = sitk.Cast(segmentation, sitk.sitkUInt16)

	try:

		overlaidSegImage = sitk.LabelOverlay(img_T1_255, segmentation)
		nda = sitk.GetArrayFromImage(overlaidSegImage)
		nda = nda[:,:,:,1]
		overlaidSegImage = sitk.GetImageFromArray(nda)

		# sitk.Show(overlaidSegImage)	
		# sitk.Show(segmentation)
	except: 
		print("Can't show the image with ImageJ! (Probably testing through Linux virtual machine)")

	return segmentation

	# segPixels = sitk.GetArrayFromImage(segmentation)
	# segPixels[segPixels < 0] = 0
	# segPixels[segPixels > 0] = 1
	# segmentation = sitk.GetImageFromArray(segPixels)

	# sitk.Show(segmentation)





	# break

	#Range intensities from 0 to 100

	# LevelSetFilter =  sitk.ThresholdSegmentationLevelSetImageFilter()

	# image = sitk.Cast(image,sitk.sitkUInt8)
	# print(image.GetPixelID())
	# seedImg = sitk.Cast(seedImg, image.GetPixelID())
	# LevelSetFilter.SetUpperThreshold(100)
	# LevelSetFilter.SetNumberOfIterations(5000)
	# LevelSetFilter.SetMaximumRMSError(0.000001)
	# seedImage[intPoints[x]] = 1;
	# seedImage = sitk.Cast(seedImage, image.GetPixelID())
	# seedImage = seedImage/2
	# seg = LevelSetFilter.Execute(seedImage, image)
	# print(LevelSetFilter)
	# LevelSetFilter.Execute(seedImage, image, double 0, double 100, double maximumRMSError, double propagationScaling, double curvatureScaling, uint32_t numberOfIterations, bool reverseExpansionDirection)
	# segmentation = segmentation + seg
	# sitk.Show(segmentation)
	# break



	# segmentation = sitk.Cast(segmentation, img_T1_255.GetPixelID())
	# sitk.Show(sitk.LabelOverlay(img_T1_255, segmentation))


	#Refine the Segmentation
	#http://www.itk.org/Doxygen46/html/classitk_1_1LaplacianSegmentationLevelSetImageFilter.html

	#GetNumberOfComponentsPerPixel from Image class

	##POST-PROCESSING FILTERS##
	#Create the filters for filling any holes
	# dilateFilter = sitk.BinaryDilateImageFilter()
	# dilateFilter.SetKernelRadius(1)
	# erodeFilter = sitk.BinaryErodeImageFilter()
	# erodeFilter.SetKernelRadius(1)
	# fillFilter = sitk.BinaryFillholeImageFilter()


	#segTwo = dilateFilter.Execute(segTwo, 0, 5, False)
	#segTwo = fillFilter.Execute(segTwo, True, 5)
	#segTwo = erodeFilter.Execute(segTwo, 0, 5, False)

if __name__ == '__main__':
    # sitkConfidenceConnectedSeg.py executed as script
	#Create a list for the seed points
	# seedPoints = [[130.1238, 184.98213, 41.123], [175.987, 90.123, 31.0],[100, 200, 44],[90, 225, 61],[100, 200, 72],[75, 200, 85],[45, 200, 100]]
	seedPoints = [[130.1238, 184.98213, 41.123], [175.987, 90.123, 31.0]]
	#Read in image
	image = sitk.ReadImage("Volunteer5_VIBE.hdr")

	segmentation = ConfidenceConnectedSeg(image, seedPoints)

