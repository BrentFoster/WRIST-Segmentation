import SimpleITK as sitk
import numpy as np


def CreateSeedImage(image, seedPoint):
	###Create the seed image###
	nda = sitk.GetArrayFromImage(image)
	nda = np.asarray(nda)
	nda = nda*0

	#In numpy an array is indexed in the opposite order (z,y,x)
	nda[seedPoint[2]][seedPoint[1]][seedPoint[0]] = 1

	seg = sitk.Cast(sitk.GetImageFromArray(nda), sitk.sitkUInt16)
	seg.CopyInformation(image)

	seg = sitk.BinaryDilate(seg, 3)
	return seg

def Preprocessing(image):
	''' Pre-processing '''
	sigFilter = sitk.SigmoidImageFilter()
	sigFilter.SetAlpha(0)
	sigFilter.SetBeta(80)
	sigFilter.SetOutputMinimum(0)
	sigFilter.SetOutputMaximum(1)

	medianFilter = sitk.BinaryMedianImageFilter()
	# medianFilter.SetRadius([2,2,2])

	image = sigFilter.Execute(image)
	image = medianFilter.Execute(image)
	# sitk.Show(image, 'image')

	#Want 0 for the background and 1 for the objects
	nda = sitk.GetArrayFromImage(image)
	nda = np.asarray(nda)

	#Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
	nda[nda  == 1] = -1
	nda[nda == 0] = 1
	nda[nda != 1] = 0


	processedImage = sitk.Cast(sitk.GetImageFromArray(nda), image.GetPixelID())
	processedImage.CopyInformation(image)

	# sitk.Show(processedImage)


	return processedImage

def Segmentation(processedImage, seedPoint):
	''' Segmentation '''

	#Initilize the SimpleITK Filter
	shapeDetectionFilter = sitk.ShapeDetectionLevelSetImageFilter()
	shapeDetectionFilter.SetMaximumRMSError(0.005)
	# shapeDetectionFilter.SetNumberOfIterations(500)
	shapeDetectionFilter.SetPropagationScaling(-2)
	# shapeDetectionFilter.SetCurvatureScaling(1)

	iniSeg = CreateSeedImage(processedImage, seedPoint)

	#Signed distance function using the initial levelset segmentation
	# init_ls = sitk.SignedMaurerDistanceMap(iniSeg, insideIsPositive=False, useImageSpacing=True)

	# distanceMapFilter = sitk.DanielssonDistanceMapImageFilter()
	# distanceMapFilter.SetInsideValue(0)
	# distanceMapFilter.SetOutsideValue(1)

	# iniSeg = distanceMapFilter.Execute(iniSeg)
	init_ls = sitk.SignedMaurerDistanceMap(iniSeg, insideIsPositive=True, useImageSpacing=True)

	init_ls  = sitk.Cast(init_ls, sitk.sitkFloat32)
	processedImage  = sitk.Cast(processedImage, sitk.sitkFloat32)

	segImage = shapeDetectionFilter.Execute(init_ls, processedImage)
	print(shapeDetectionFilter)

	return segImage

def scaleDownImage(image, ScalingFactor):
	shrinkFilter = sitk.ShrinkImageFilter()
	shrinkFilter.SetShrinkFactors(ScalingFactor)
	image = shrinkFilter.Execute(image)
	return image

def VisualizeResult(image,segImage):
	segImage  = sitk.Cast(segImage, sitk.sitkUInt16)
	image = sitk.Cast(image, sitk.sitkUInt16)

	overlaidSegImage = sitk.LabelOverlay(image, segImage)
	sitk.Show(overlaidSegImage)

def Execute():
	#Load Image
	ScalingFactor = 3
	image  = sitk.ReadImage('/Users/Brent/Desktop/Volunteer1_VIBE.hdr')
	image  = scaleDownImage(image, [ScalingFactor,ScalingFactor,ScalingFactor])
	processedImage  = Preprocessing(image)
	segImage = Segmentation(processedImage,[210/ScalingFactor, 120/ScalingFactor, 100/ScalingFactor])

	VisualizeResult(image,segImage)

Execute()







	# GradientMagnitudeFilter = sitk.GradientMagnitudeImageFilter()
	# gradientImage = GradientMagnitudeFilter.Execute(image)
	# gradientImage  = sitk.Cast(gradientImage, sitk.sitkUInt16)
	# image  = sitk.Cast(image, sitk.sitkUInt16)


	# nda = sitk.GetArrayFromImage(gradientImage)
	# nda = np.asarray(nda)

	# #Fix the intensities of the output of the laplcian; 0 = 1 and ~! 1 is 0 then 1 == x+1
	# nda[nda  > 0] = 1
	# nda[nda != 1] = 0

	# gradientImage = sitk.Cast(sitk.GetImageFromArray(nda), gradientImage.GetPixelID())
	# gradientImage.CopyInformation(image)


