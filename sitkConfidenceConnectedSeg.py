import SimpleITK as sitk
import numpy as np
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, \
    FileTransferSpeed, FormatLabel, Percentage, \
    ProgressBar, ReverseBar, RotatingMarker, \
    SimpleProgress, Timer, AdaptiveETA, AbsoluteETA, AdaptiveTransferSpeed

#Read in image
img = sitk.ReadImage("Volunteer5_VIBE.hdr")
img_T1_255 = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

img = sitk.Cast(img,sitk.sitkFloat32)

#Create empty image to hold the segmentations
segmentation = sitk.Image(img.GetSize(), img.GetPixelID())
segmentation.CopyInformation(img)

#Create empty seed image for the level set filter to use
seedImage = img*0

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
# fastMarchingImg = fastMarchingFilter.Execute(img)

# segPixels = sitk.GetArrayFromImage(fastMarchingImg)
# segPixels[segPixels > 10] = 10
# fastMarchingImg = sitk.GetImageFromArray(segPixels)
# sitk.Show(fastMarchingImg)

######################################################################

intPoints = [[130, 184, 41], [175, 90, 31],[100, 200, 44],[90, 225, 61],[100, 200, 72],[75, 200, 85],[45, 200, 100]]

numPoints = len(intPoints)

pbar = ProgressBar(widgets=[Percentage(), Bar()], max_value=(numPoints+1)*5).start()
for x in range(0, 7):

	pbar.update(x*5+0.0001)
	segXImg = sitk.ConfidenceConnected(img, [intPoints[x]], numberOfIterations=10, 
			multiplier=2,	initialNeighborhoodRadius = 5, replaceValue=x+1)

	pbar.update(x*5+1)
	segXImg = dilateFilter.Execute(segXImg, 0, x+1, False)
	pbar.update(x*5+2)
	segXImg = fillFilter.Execute(segXImg, True, x+1)
	pbar.update(x*5+3)
	segXImg = erodeFilter.Execute(segXImg, 0, x+1, False)
	pbar.update(x*5+4)
	segXImg = sitk.Cast(segXImg, segmentation.GetPixelID())
	pbar.update(x*5+5)
	segmentation = segmentation + segXImg

	
pbar.finish()

segmentation = segmentation*50
segmentation = sitk.Cast(segmentation, sitk.sitkUInt16)

overlaidSegImage = sitk.LabelOverlay(img_T1_255, segmentation)
nda = sitk.GetArrayFromImage(overlaidSegImage)
nda = nda[:,:,:,1]
overlaidSegImage = sitk.GetImageFromArray(nda)

try:
	sitk.Show(overlaidSegImage)	
	sitk.Show(segmentation)
except: 
	print("Can't show the image! (Probably tsting through Linux virtual machine")
















# segPixels = sitk.GetArrayFromImage(segmentation)
# segPixels[segPixels < 0] = 0
# segPixels[segPixels > 0] = 1
# segmentation = sitk.GetImageFromArray(segPixels)

# sitk.Show(segmentation)





# break

#Range intensities from 0 to 100

# LevelSetFilter =  sitk.ThresholdSegmentationLevelSetImageFilter()

# img = sitk.Cast(img,sitk.sitkUInt8)
# print(img.GetPixelID())
# seedImg = sitk.Cast(seedImg, img.GetPixelID())
# LevelSetFilter.SetUpperThreshold(100)
# LevelSetFilter.SetNumberOfIterations(5000)
# LevelSetFilter.SetMaximumRMSError(0.000001)
# seedImage[intPoints[x]] = 1;
# seedImage = sitk.Cast(seedImage, img.GetPixelID())
# seedImage = seedImage/2
# seg = LevelSetFilter.Execute(seedImage, img)
# print(LevelSetFilter)
# LevelSetFilter.Execute(seedImage, img, double 0, double 100, double maximumRMSError, double propagationScaling, double curvatureScaling, uint32_t numberOfIterations, bool reverseExpansionDirection)
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
