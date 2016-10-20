# Build and install the BrentPython package first!
# cd /Users/Brent/BoneSegmentation/PythonPackage; python setup.py bdist; python setup.py install  ; cd /Users/Brent/BoneSegmentation/CLI; clear; python BoneSegmentation_CLI.py 

# Import modules from the BrentPython Python package 
import BrentPython
from BrentPython import *
from BrentPython import BrentFiltering
from BrentPython import Create_Seeds
from BrentPython import Dice
from BrentPython import SpectralClutering
from BrentPython import MultiprocessorHelper

import SimpleITK as sitk
import timeit



def main():		
	# MRI_Filename = ['/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr']
	
	# MRI_Filename = ['/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii']
	

	MRI_Filename = ['E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii']
	
	# Create objects of the needed classes
	# Set the parameters for the segmentation class object
	segmentationClass = BoneSegmentation.BoneSeg()

	multiHelper = MultiprocessorHelper.Multiprocessor()
	DiceCalulator = Dice.DiceCalulator()

	MRI_Image = sitk.ReadImage(MRI_Filename[0])

	seedPoints = []
	# new_point = np.array([110, 470, 91], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([170, 620, 91], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([120, 534, 91], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([116, 507, 101], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([100, 484, 75], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([143, 610, 85], dtype=int)
	# seedPoints.append(new_point)




	new_point = np.array([250, 630, 118], dtype=int)
	seedPoints.append(new_point)
	new_point = np.array([230, 680, 106], dtype=int)
	seedPoints.append(new_point)
	new_point = np.array([285, 670, 141], dtype=int)
	seedPoints.append(new_point)
	# new_point = np.array([350, 650, 141], dtype=int)
	# seedPoints.append(new_point)

	print('seedPoints' + str(seedPoints))

	Segmentation = multiHelper.Execute(segmentationClass, seedPoints, MRI_Image, parameter=[1,2,3], verbose=True)
	Segmentation.CopyInformation(MRI_Image)

	BrentPython.SaveSegmentation(Segmentation, 'ScreenShots/CLI_Segmentation.nii', verbose=True)	

	# sitk.Show(Segmentation, 'Segmentation')
	
	return 0

def FillHoles(image, verbose=False):
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

def test():

	segmentationOutput = sitk.ReadImage('ScreenShots/CLI_Segmentation.nii')
	

	segmentationOutput = FillHoles(segmentationOutput)


	
	BrentPython.SaveSegmentation(segmentationOutput, 'ScreenShots/filledtest.nii', verbose=True)	




	# # Initilize the needed SimpleITK filter classes
	# erodeFilter = sitk.BinaryErodeImageFilter()
	# erodeFilter.SetKernelRadius(2)

	# dilateFilter = sitk.BinaryDilateImageFilter()
	# dilateFilter.SetKernelRadius(2)


	# segmentationOutput = dilateFilter.Execute(segmentationOutput, 0, 1, False)

	# fillFilter = sitk.VotingBinaryIterativeHoleFillingImageFilter()  
	# fillFilter.SetForegroundValue(255) 
	# fillFilter.SetMaximumNumberOfIterations(5)
	# fillFilter.SetRadius(10)

	# fillFilter.SetMajorityThreshold(0)

	# fillFilter.FullyConnectedOff()

	# print(fillFilter)
	
	# segmentationOutput = fillFilter.Execute(segmentationOutput)
	# segmentationOutput = fillFilter.Execute(segmentationOutput)


	# fillFilter = sitk.BinaryFillholeImageFilter()
	# print(fillFilter)
	# fillFilter.SetForegroundValue(255) 
	# fillFilter.FullyConnectedOn()
	# segmentationOutput = fillFilter.Execute(segmentationOutput)

	# segmentationOutput = sitk.VotingBinaryHoleFilling(image1=segmentationOutput,
 #                                                          radius=[2]*3,
 #                                                          majorityThreshold=1,
 #                                                          backgroundValue=0,
 #                                                          foregroundValue=255)

	# grindPeakFilter = sitk.BinaryGrindPeakImageFilter()
	# segmentationOutput = grindPeakFilter.Execute(sitk.Not(segmentationOutput), True, 255, 0)
 	# segmentationOutput = segmentationOutput>0
 	# segmentationOutput = sitk.LabelToRGB(sitk.ConnectedComponent(segmentationOutput))

	


if __name__ == '__main__':
	start_time = timeit.default_timer()
	
	main()

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	print("Elapsed Time (secs):" + str(round(elapsed,3)))

	print('Done!!')