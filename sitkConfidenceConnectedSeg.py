# #Add the location where the Linux virtual machine is installing the SimpleITK module
# import sys
# sys.path.append("/home/shippable/.local/lib/python2.7/site-packages")
# sys.path.append("/home/shippable/.local/lib/python2.7/site-packages/SimpleITK-0.9.1-py2.7-linux-x86_64.egg")
# sys.path.append("/usr/local/lib/python2.7/dist-packages/SimpleITK-0.9.1-py2.7-linux-x86_64.egg")
# print(sys.path)

# import numpy as np
import SimpleITK as sitk
import numpy as np

#Read in image
img = sitk.ReadImage("Volunteer5_VIBE.hdr")
img_T1_255 = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

img = sitk.Cast(img,sitk.sitkFloat32)


#Create empty image to hold the segmentations
segmentation = sitk.Image(img.GetSize(), img.GetPixelID())
segmentation.CopyInformation(img)

#Create empty seed image for the level set filter to use
seedImage = img*0
# print(seedImage)

#Array of the seed points

##POST-PROCESSING FILTERS##
# Create the filters for filling any holes
dilateFilter = sitk.BinaryDilateImageFilter()
dilateFilter.SetKernelRadius(2)
erodeFilter = sitk.BinaryErodeImageFilter()
erodeFilter.SetKernelRadius(2)
fillFilter = sitk.BinaryFillholeImageFilter()

# intPoints = np.array([[150, 150, 87], [170, 100, 87],[100, 200, 97],[90, 225, 114],[100, 200, 125],[75, 200, 138],[45, 200, 153]])
intPoints = [[130, 184, 41], [170, 100, 27],[100, 200, 37],[90, 225, 54],[100, 200, 65],[75, 200, 78],[45, 200, 93]]

for x in range(0, len(intPoints)):
	segmentation = sitk.ConfidenceConnected(img, [intPoints[x]], numberOfIterations=0, 
			multiplier=1,	initialNeighborhoodRadius = 5, replaceValue=x+1)
	# seedImg = segmentation
	#its = 9 multiplier = 1.75

	segmentation = dilateFilter.Execute(segmentation)
	segmentation = fillFilter.Execute(segmentation)
	segmentation = erodeFilter.Execute(segmentation)

	sitk.Show(overlaidSegImage)

	break

	#Range intensities from 0 to 100

	LevelSetFilter =  sitk.ThresholdSegmentationLevelSetImageFilter()

	# img = sitk.Cast(img,sitk.sitkUInt8)
	# print(img.GetPixelID())
	# seedImg = sitk.Cast(seedImg, img.GetPixelID())

	LevelSetFilter.SetUpperThreshold(100)
	LevelSetFilter.SetNumberOfIterations(5000)
	LevelSetFilter.SetMaximumRMSError(0.000001)

	# LevelSetFilter.SetIsoSurfaceValue(1)
	
	# seedImage[intPoints[x]] = 1;

	seedImage = sitk.Cast(seedImage, img.GetPixelID())
	# seedImage = seedImage/2
	seg = LevelSetFilter.Execute(seedImage, img)

	print(LevelSetFilter)


	 # LevelSetFilter.Execute(seedImage, img, double 0, double 100, double maximumRMSError, double propagationScaling, double curvatureScaling, uint32_t numberOfIterations, bool reverseExpansionDirection)

	segmentation = segmentation + seg
	sitk.Show(segmentation)
	break



	temp = sitk.LabelOverlay(img_T1_255, segmentation)

	nda = sitk.GetArrayFromImage(temp)
	nda = nda[:,:,:,1]
	overlaidSegImage = sitk.GetImageFromArray(nda)


# segPixels = sitk.GetArrayFromImage(segmentation)
# segPixels[segPixels < 0] = 0
# segPixels[segPixels > 0] = 1
# segmentation = sitk.GetImageFromArray(segPixels)

# sitk.Show(segmentation)






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
