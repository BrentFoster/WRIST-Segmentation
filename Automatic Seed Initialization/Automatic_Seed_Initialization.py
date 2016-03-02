#For creating debug file and printing warning to the terminal
#Allows the user to decide what level to print
#Allowed levels are CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging 
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
logging.debug('Starting automatic seed initialization...')


import SimpleITK as sitk
import numpy as np

''' Load images '''
MRI_Filename = '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr'
# MRI_Filename = '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr'
MRI = sitk.ReadImage(MRI_Filename)
MRI = sitk.Cast(MRI, sitk.sitkUInt16) # Cast to 16 bit image 

''' Roughly segment the hand boundary (use automatic thresholding in SimpleITK)
	Could either hard code the thresholds based on VIBE or use a ITK method '''

# Initialize various ITK filters
otsuFilter = sitk.OtsuMultipleThresholdsImageFilter()
otsuFilter.SetNumberOfHistogramBins(256)

kernelRadius = [2,2,2]
medianFilter = sitk.BinaryMedianImageFilter()
medianFilter.SetRadius(kernelRadius)

kernelRadius = [5,5,5]
dilateFilter = sitk.BinaryDilateImageFilter()
dilateFilter.SetBackgroundValue(0)
dilateFilter.SetForegroundValue(1)
dilateFilter.SetKernelRadius(kernelRadius)

fillFilter = sitk.BinaryFillholeImageFilter()
fillFilter.SetForegroundValue(1)
fillFilter.FullyConnectedOn()

run_pipeline = False
if run_pipeline == True:
	# Run pipeline
	logging.debug('Running Otsu thresholding')
	segHand = otsuFilter.Execute(MRI)
	logging.debug('Running median filter')
	segHand = medianFilter.Execute(segHand)
	logging.debug('Running median filter')
	segHand = medianFilter.Execute(segHand)
	logging.debug('Running median filter')
	segHand = medianFilter.Execute(segHand)
	logging.debug('Running dilation filter')
	segHand = dilateFilter.Execute(segHand)
	logging.debug('Running dilation filter')
	segHand = dilateFilter.Execute(segHand)
	logging.debug('Running binary fill filter')
	segHand = fillFilter.Execute(segHand)

	# sitk.Show(segHand)



	# Save this image using ITK
	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(segHand, 'segHand_volunteer_3.nii', True)

import BrentVTK
movingFilename = 'segHand_volunteer_3_carpals.nii'
fixedFilename  = 'HandModel_volunteer_2_carpals.nii'
labels = (1,0)


BrentVTK.main(movingFilename, fixedFilename, labels, show_rendering=True, calculateDice=False)


# Overlap with model for goodness of fit evaluation
transformedImg = sitk.ReadImage('vtk_Transformed_Img.nii')
transformedImg = sitk.Cast(transformedImg, sitk.sitkUInt16) 

hand_model_img = sitk.ReadImage('HandModel_volunteer_2_carpals.nii')
hand_model_img = sitk.Cast(hand_model_img, sitk.sitkUInt16) 




ndaTransformImg = np.asarray(sitk.GetArrayFromImage(transformedImg))
nda_hand_model_img = np.asarray(sitk.GetArrayFromImage(hand_model_img))


ndaTransformImg = ndaTransformImg + nda_hand_model_img

overlapImg = sitk.GetImageFromArray(ndaTransformImg)
overlapImg.CopyInformation(MRI)

sitk.Show(overlapImg)



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