import SimpleITK as sitk
import BoneSegmentation
import numpy as np

import MultiprocessorHelper
import timeit
import BrentPython

def SaveSegmentation(image, filename, verbose = False):
	""" Take a SimpleITK type image and save to a filename (in analyze format) """
	if verbose == True:
		print("Saving segmentation to "),
		print(filename)
	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(image, filename, True)
	if verbose == True:
		print("Segmentation saved")

def AddImages(image_one, image_two):
	image_one.CopyInformation(image_two)

	addFilter = sitk.AddImageFilter()
	combined_img = addFilter.Execute(image_one, image_two)

	return combined_img

def RunSegmentation(input_image, seedPoint, CurrBoneName):

	# seedPoint = np.array(seedPoint).astype(int)

	start_time = timeit.default_timer()

	' Run the Segmentation '
	multiHelper = MultiprocessorHelper.Multiprocessor()
	seg_img = multiHelper.Execute(seedPoint, input_image, verbose=True)

	elapsed = timeit.default_timer() - start_time
	print("Elapsed Time (secs):"),
	print(str(round(elapsed,2)))	

	overlaidImg = BrentPython.OverlayImages(input_image, seg_img, opacity=0.9, backgroundValue=0)

	return overlaidImg

if __name__ == "__main__":
	start_time = timeit.default_timer()

	' Load the MRI image to be segmented'
	input_image = sitk.ReadImage('/Users/Brent/Google Drive/Research/MRI Wrist Images/MRI Ground Truth Brent/Volunteer4_VIBE_we.nii')

	# sitk.Show(input_image, 'input_image')
	
	# TEST
	# bias_corrected_image = sitk.ReadImage('/Users/Brent/Google Drive/Research/MRI Wrist Images/MRI Ground Truth Brent/Volunteer4_VIBE_we_Bias_Corrected.nii')
	# bias_field_image     = sitk.ReadImage('/Users/Brent/Google Drive/Research/MRI Wrist Images/MRI Ground Truth Brent/Volunteer4_VIBE_we_Bias_Field.nii')
	# sitk.Show(input_image, 'Original Image')
	# sitk.Show(bias_corrected_image, 'bias_corrected_image')
	# sitk.Show(bias_field_image, 'bias_field_image')

	# END TEST

	' Define the seed points '
	seedPoints = []
	CurrBoneName = []

	for i in range(0,8):
		new_point = np.array([220, 565, 127], dtype=int)
		seedPoints.append(new_point)
		CurrBoneName.append('Hamate')

		# new_point = np.array([200, 670, 100], dtype=int)
		# seedPoints.append(new_point)
		# CurrBoneName.append('Pisiform')
		
		# new_point = np.array([290, 630, 160], dtype=int)
		# seedPoints.append(new_point)
		# CurrBoneName.append('Capitate')

	print('Number of Points: ' + str(len(seedPoints)))

	' Run the Segmentation '	
	# Create a output image of all zeros to hold the segmentation results
	outputImg_nda = sitk.GetArrayFromImage(input_image)
	outputImg_nda = np.asarray(outputImg_nda)
	outputImg_nda = outputImg_nda*0

	outputImg = sitk.Cast(sitk.GetImageFromArray(outputImg_nda), sitk.sitkUInt16)
	outputImg.CopyInformation(input_image)


	# for i in range(0,len(seedPoints)):
	outputImg_temp = RunSegmentation(input_image, seedPoints, CurrBoneName[i])

		# Double check the pixel types
		# outputImg_temp = sitk.Cast(outputImg_temp, outputImg.GetPixelID())
		# outputImg = AddImages(outputImg, outputImg_temp)


	' Show the final output image '
	sitk.Show(outputImg)


	# elapsed = timeit.default_timer() - start_time
	# print("Elapsed Time (secs):"),
	# print(str(round(elapsed,2)))	

	print('Done!!')

