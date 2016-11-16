# For creating debug file and printing warning to the terminal
# Allows the user to decide what level to print
# Allowed levels are CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging 
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.debug('Starting automatic seed initialization...')

import SimpleITK as sitk
import numpy as np
import BrentVTK

def SaveSegmentation(image, filename, verbose = False):
	""" Take a SimpleITK type image and save to a filename (in analyze format) """
	if verbose == True:
		print("Saving segmentation to "),
		print(filename)
	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(image, filename, True)
	if verbose == True:
		print("Segmentation saved")

def Segment_Hand(MRI, outputFilename):
	''' Roughly segment the hand boundary (use automatic thresholding in SimpleITK)
		Could either hard code the thresholds based on VIBE or use a ITK method '''

	# Initialize various ITK filters
	otsuFilter = sitk.OtsuMultipleThresholdsImageFilter()
	# otsuFilter = sitk.OtsuThresholdImageFilter()
	otsuFilter.SetNumberOfHistogramBins(256)
	# otsuFilter = sitk.BinaryThresholdImageFilter()
	# otsuFilter.SetUpperThreshold(100)
	
	kernelRadius = [2,2,2]
	binary_medianFilter = sitk.BinaryMedianImageFilter()
	binary_medianFilter.SetRadius(kernelRadius)

	medianFilter = sitk.MedianImageFilter()
	medianFilter.SetRadius(kernelRadius)

	dilateFilter = sitk.BinaryDilateImageFilter()
	dilateFilter.SetBackgroundValue(0)
	dilateFilter.SetForegroundValue(1)
	dilateFilter.SetKernelRadius(kernelRadius)

	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetBackgroundValue(0)
	erodeFilter.SetForegroundValue(1)
	erodeFilter.SetKernelRadius(kernelRadius*2)

	fillFilter = sitk.BinaryFillholeImageFilter()
	fillFilter.SetForegroundValue(0)
	fillFilter.FullyConnectedOff()

	# Run pipeline
	logging.debug('Running median filter on MRI')
	MRI = medianFilter.Execute(MRI)

	MRI = sitk.Cast(MRI, sitk.sitkUInt8) # Cast to 8 bit image

	logging.debug('Running Otsu thresholding')
	segHand = otsuFilter.Execute(MRI)
	print(otsuFilter)

	logging.debug('Running dilation filter')
	segHand = dilateFilter.Execute(segHand)

	logging.debug('Running binary fill filter')
	segHand = fillFilter.Execute(segHand)

	logging.debug('Running dilation filter')
	segHand = dilateFilter.Execute(segHand)

	logging.debug('Running binary fill filter')
	segHand = fillFilter.Execute(segHand)

	logging.debug('Running erode filter')
	segHand = erodeFilter.Execute(segHand)

	logging.debug('Running binary fill filter')
	segHand = fillFilter.Execute(segHand)
	
	# Save this image using ITK
	SaveSegmentation(segHand, outputFilename, verbose = True)

	return segHand

def Load_Image(MRI_Filename):
	''' Load images '''
	# MRI_Filename = '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr'
	MRI = sitk.ReadImage(MRI_Filename)
	MRI = sitk.Cast(MRI, sitk.sitkUInt16) # Cast to 16 bit image 

	return MRI

def Post_processing(Filename_one, Filename_two):
	''' Overlap with model for goodness of fit evaluation '''
	transformedImg = sitk.ReadImage(Filename_one)
	transformedImg = sitk.Cast(transformedImg, sitk.sitkUInt16) 

	hand_model_img = sitk.ReadImage(Filename_two)
	hand_model_img = sitk.Cast(hand_model_img, sitk.sitkUInt16) 

	ndaTransformImg = np.asarray(sitk.GetArrayFromImage(transformedImg))
	nda_hand_model_img = np.asarray(sitk.GetArrayFromImage(hand_model_img))


	ndaTransformImg = ndaTransformImg + nda_hand_model_img

	overlapImg = sitk.GetImageFromArray(ndaTransformImg)
	overlapImg.CopyInformation(MRI)

	sitk.Show(overlapImg)

def Apply_Transform(movingImg, fixedImg, transformField):
	''' Apply the transformation to the moving image segmentation image '''

	warpingFilter = sitk.WarpImageFilter() 
	warpingFilter.SetEdgePaddingValue(0) 
	warpingFilter.SetInterpolator(sitk.sitkNearestNeighbor) # try sitkGaussian sitkLabelGaussian sitkNearestNeighbor
	warpingFilter.SetOutputParameteresFromImage(movingImg) 
	warpedMovingImg = warpingFilter.Execute(movingImg, transformField)

	warpedMovingImg.CopyInformation(fixedImg)
	warpedMovingImg = sitk.Cast(warpedMovingImg, fixedImg.GetPixelID())

	return warpedMovingImg

def Demons_Registration(movingImg, fixedImg):
	''' Deformable registration after ICP registration of the hand surfaces '''

	logging.info('Non-rigid registration using Demons')
	
	# demonsReg = sitk.FastSymmetricForcesDemonsRegistrationFilter()
	demonsReg = sitk.DemonsRegistrationFilter()
	demonsReg.SetNumberOfIterations(10) 
	demonsReg.SetSmoothDisplacementField(True)
	# demonsReg.SetSmoothUpdateField(True)
	transformField = demonsReg.Execute(fixedImg, movingImg)
	transformField.CopyInformation(fixedImg)

	logging.info('GetElapsedIterations')
	logging.info(demonsReg.GetElapsedIterations())
	logging.info('GetRMSChange')
	logging.info(demonsReg.GetRMSChange())

	return transformField

if __name__ == "__main__":

	# Should try different images. The ICP isn't good between these two
	# Moving_MRI_Filename = '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr'
	# Fixed_MRI_Filename  = '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr'
	
	# Brent's Lab PC image paths
	Moving_MRI_Filename = 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr'
	Fixed_MRI_Filename  = 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr'

	outputHandFilename  = 'segHand.nii'
	labels = (1,0)

	# movingFilename = 'segHand_volunteer_3_carpals.nii'
	# fixedFilename  = 'HandModel_volunteer_2_carpals.nii'
	# transformImgFilename = MRI_Filename
	
	# Moving_MRI = Load_Image(Moving_MRI_Filename)
	# Moving_segHand = Segment_Hand(Moving_MRI, 'Moving_segHand.nii')
	# SaveSegmentation(Moving_segHand, 'Moving_segHand.nii', verbose = True)

	# Fixed_MRI = Load_Image(Fixed_MRI_Filename)
	# Fixed_segHand = Segment_Hand(Fixed_MRI, 'Fixed_segHand.nii')

	BrentVTK.main('Fixed_segHand.nii', 'Moving_segHand.nii', 'E:\Google Drive\Research\MRI Wrist Images\CMC OA\VIBE Ground Truth\Volunteer1_GroundTruth.hdr', labels, show_rendering=True, calculateDice=False)

	# Load the ICP transformed MRI image
	movingImg = Load_Image('movingMRItransformed.nii')
	fixedImg  = Load_Image('fixed_vol_3.nii')

	# transformField  = Demons_Registration(movingImg, fixedImg)

	# transformedImg	= Apply_Transform(movingImg, fixedImg, transformField)

	# sitk.Show(transformedImg)

	# Post_processing('vtk_Transformed_Img.nii', 'HandModel_volunteer_2_carpals.nii')





# segHand = sitk.ReadImage('binary_hand_volunteer_1.nii')

# ndaMRI  = np.asarray(sitk.GetArrayFromImage(MRI))
# ndaHand = np.asarray(sitk.GetArrayFromImage(segHand))

# ndaSegMRI = ndaMRI * ndaHand

# segMRI = sitk.GetImageFromArray(ndaSegMRI)
# segMRI.CopyInformation(MRI)

# otsuFilter.SetNumberOfHistogramBins(128)

# logging.debug('Running Otsu thresholding')
# segMRI = otsuFilter.Execute(segMRI)

# sitk.Show(segMRI)


# medianFilter.SetRadius([1,1,1])
# logging.debug('Running median filter')
# segMRI = medianFilter.Execute(segMRI)
# segMRI = medianFilter.Execute(segMRI)

# logging.debug('Running dilation filter')
# dilateFilter.SetKernelRadius([2,2,2])
# segMRI = dilateFilter.Execute(segMRI)

# logging.debug('Running binary fill filter')
# segMRI = fillFilter.Execute(segMRI)

# logging.debug('Done!')
# sitk.Show(segMRI)

# Use ICP to register the hand surface to the hand model


# Apply the resulting transformation to a set of points in the hand model
# One point for each bone

# Could also do some logic to test whether the seed location is the correct intensity
# Similar to Mansoor TMI paper for the lung segmentation seed location

# Run the carpal bone segmentation code

# Check for leakage (similar to Mansoor TMI paper) 

# If leakage is detected, apply spectral clustering to remove leakage areas

# Do everything in parallel to lower computation time (up to 8x faster)