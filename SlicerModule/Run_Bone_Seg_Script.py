
import SimpleITK as sitk
import BoneSegmentation
import numpy as np

import MultiprocessorHelper

import timeit

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
	addFilter = sitk.AddImageFilter()
	combined_img = addFilter.Execute(image_one, image_two)

	return combined_img

def RunSegmentation(input_image, seedPoint, searchWindow):

	seedPoint = np.array(seedPoint).astype(int)

	# im_size = np.asarray(input_image.GetSize())

	# ' Crop the input_image around the initial seed point to speed up computation '
	# cropFilter = sitk.CropImageFilter()
	# addFilter = sitk.AddImageFilter()

	# cropFilter.SetLowerBoundaryCropSize(seedPoint - searchWindow)
	# cropFilter.SetUpperBoundaryCropSize(im_size - seedPoint - searchWindow)

	# print(im_size - seedPoint - searchWindow)
	# asdf


	# cropNdxOne = seedPoint - searchWindow
	# cropNdxTwo = seedPoint + searchWindow
	
	# cropped_img = cropFilter.Execute(input_image)

	# # The seed point is now in the middle of the search window
	# seedPoint = np.asarray(searchWindow)

	' Run the Segmentation '
	segmentationClass = BoneSegmentation.BoneSeg()
	segmentationClass.SetSearchWindowSize(searchWindow)

	# seg_img = segmentationClass.Execute(cropped_img, [seedPoint], verbose=False, returnSitkImage=True, convertSeedPhyscial=False)
	seg_img = segmentationClass.Execute(input_image, [seedPoint], verbose=False, 
										returnSitkImage=True, convertSeedPhyscialFlag=False)


	return seg_img

	# ' Indexing to put the segmentation of the cropped image back into the original MRI '
	# input_image_nda = sitk.GetArrayFromImage(input_image)
	# input_image_nda = np.asarray(input_image_nda)

	# seg_img_nda = sitk.GetArrayFromImage(seg_img)
	# seg_img_nda = np.asarray(seg_img_nda)

	# cropped_img_nda = sitk.GetArrayFromImage(cropped_img)
	# cropped_img_nda = np.asarray(cropped_img_nda)

	# cropped_img_nda[seg_img_nda == 1] = cropped_img_nda[seg_img_nda == 1] + 500;
	# seg_img_nda = cropped_img_nda;

	# input_image_nda[cropNdxOne[2]:cropNdxTwo[2],
	# 				cropNdxOne[1]:cropNdxTwo[1],
	# 				cropNdxOne[0]:cropNdxTwo[0]] = seg_img_nda


	# ' Return the final image '
	# outputImg = sitk.Cast(sitk.GetImageFromArray(input_image_nda), sitk.sitkUInt16)
	# outputImg.CopyInformation(input_image)

	# return outputImg

if __name__ == "__main__":
	start_time = timeit.default_timer()

	' Load the MRI image to be segmented'
	input_image = sitk.ReadImage('/Users/Brent/Google Drive/Research/MRI Wrist Images/MRI Ground Truth Brent/VOlunteer2_VIBE_we.nii')

	' Define the seed points '
	seedPoints = []

	for i in range(0,1):
		new_point = np.array([200, 670, 100], dtype=int)
		seedPoints.append(new_point)

	# new_point = np.array([370, 600, 120], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([350, 660, 120], dtype=int)
	# seedPoints.append(new_point)
	# new_point = np.array([210, 670, 140], dtype=int)
	# seedPoints.append(new_point)
	# print('seedPoints' + str(seedPoints))


	' Define other variables '
	searchWindow = 200;
	# Create objects of the needed classes
	# Set the parameters for the segmentation class object
	# segmentationClass = BoneSegmentation.BoneSeg()
	multiHelper = MultiprocessorHelper.Multiprocessor()

	' Run the Segmentation '
	# outputImg = multiHelper.Execute(seedPoints, input_image, searchWindow=searchWindow, parameter=[1,2,3], verbose=True)
	# outputImg.CopyInformation(input_image)
	
	# Create a zero output image to hold the segmentations
	outputImg_nda = sitk.GetArrayFromImage(input_image)
	outputImg_nda = np.asarray(outputImg_nda)
	outputImg_nda = outputImg_nda*0

	outputImg = sitk.Cast(sitk.GetImageFromArray(outputImg_nda), sitk.sitkUInt16)
	outputImg.CopyInformation(input_image)

	for i in range(0,len(seedPoints)):
		outputImg_temp = RunSegmentation(input_image, seedPoints[i], searchWindow)
		outputImg = AddImages(outputImg, outputImg_temp)


	' Show the final output image '
	sitk.Show(outputImg)


	# for i in range(0, len(seedPoint)):
	# 	print(seedPoint[i])
	# seedPoint = np.zeros(shape=(3,3))
	# seedPoint[0] = np.array([200, 670, 100]).astype(int);
	# seedPoint[1] = np.array([200, 670, 80]).astype(int);



	elapsed = timeit.default_timer() - start_time
	print("Elapsed Time (secs):"),
	print(str(round(elapsed,2)))	

	print('Done!!')

