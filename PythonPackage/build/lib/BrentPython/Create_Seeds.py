import SimpleITK as sitk
import numpy as np

# Import modules from the BrentPython Python package 
import BrentPython
from BrentPython import *

def New_Seeds(GT_Filename, num_seeds=1, label=1, kernelRadius=2):
	# Load the ground truth image
	GroundTruth_original = sitk.ReadImage(GT_Filename)

	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(kernelRadius)
	GroundTruth = erodeFilter.Execute(GroundTruth_original, 0, label, False) 

	# Find all the locations within the ground truth bone with an intensity of 1 (current label)
	ndaGT = sitk.GetArrayFromImage(GroundTruth)
	ndx = np.where(ndaGT == label) 

	''' Use the ground truth image to create random seed locations within bone '''
	seedPoints = []
	for i in range(0, num_seeds):
		try:
			# Choose some random location out of the index fround above (ndx) 
			rand_ndx  = np.random.random_integers(len(ndx[0]))
			new_point = np.asarray([ndx[2][rand_ndx],  ndx[1][rand_ndx], ndx[0][rand_ndx]])
			seedPoints.append(new_point)
		except:
			print('Error in creating random seed point. len(ndx[0]) = ' + str(len(ndx[0])))

	return seedPoints


def New_Seeds_Group(GT_Filename, num_seeds=1, label=1, kernelRadius=2, buffer_size=10, save_seeds_as_image=False, seed_img_filename='ScreenShots/img_Output.nii'):
	# Load the ground truth image
	GroundTruth_original = sitk.ReadImage(GT_Filename)

	# Erode the binary image slightly to prevent the seeds to be exactly on the boundary 
	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(kernelRadius)
	GroundTruth = erodeFilter.Execute(GroundTruth_original, 0, label, False) 

	''' Split the image into a top and bottom (to get seeds at the top and bottom of some bone) '''
	# Automatically find the center of the bone to split into two halves
	ndx = np.where(sitk.GetArrayFromImage(GroundTruth_original) == label)
	Slice = np.mean(ndx[1])

	print('Slice: ' + str(Slice))

	# Use this slice to split the bone into two halves with a buffer between then
	# to have the seeds to be near the ends of the bone
	ndaGT_top = sitk.GetArrayFromImage(GroundTruth_original)
	ndaGT_top[:,Slice+1-buffer_size:ndaGT_top.shape[1], :] = 0

	ndaGT_bot = sitk.GetArrayFromImage(GroundTruth_original)
	ndaGT_bot[:, 0:Slice+buffer_size, :] = 0

	# BrentPython.SaveSegmentation(sitk.GetImageFromArray(ndaGT_top), 'ScreenShots/ndaGT_top.nii', verbose = True)	
	

	''' Use the ground truth image to create random seed locations within bone '''
	seedPoints = []

	# Top half of image
	# Find all the locations within the ground truth bone with an intensity of 1 (current label)	
	ndx = np.where(ndaGT_top == label) 
	for i in range(0, num_seeds):
		try:
			# Choose some random location out of the index fround above (ndx) 
			rand_ndx  = np.random.random_integers(len(ndx[0]))
			new_point = np.asarray([ndx[2][rand_ndx],  ndx[1][rand_ndx], ndx[0][rand_ndx]])
			seedPoints.append(new_point)
		except:
			print('Error in creating random seed point. len(ndx[0]) = ' + str(len(ndx[0])))

	# Bottom half of image
	ndx = np.where(ndaGT_bot == label) 
	for i in range(0, num_seeds):
		try:
			# Choose some random location out of the index fround above (ndx) 
			rand_ndx  = np.random.random_integers(len(ndx[0]))
			new_point = np.asarray([ndx[2][rand_ndx],  ndx[1][rand_ndx], ndx[0][rand_ndx]])
			seedPoints.append(new_point)
		except:
			print('Error in creating random seed point. len(ndx[0]) = ' + str(len(ndx[0])))

	# Optionally save all the seed locations as an image (for rendering and debugging purposes)
	if save_seeds_as_image == True:

		ndaGT = sitk.GetArrayFromImage(GroundTruth_original)
		ndaGT = ndaGT*0

		for i in range(0, len(seedPoints)):
			tempSeed = seedPoints[i]
			print(tempSeed)
			ndaGT[tempSeed[2], tempSeed[1], tempSeed[0]] = 255

		img_Output = sitk.Cast(sitk.GetImageFromArray(ndaGT), GroundTruth_original.GetPixelID())

		imageWriter = sitk.ImageFileWriter()
		imageWriter.Execute(img_Output, seed_img_filename, True)




	return seedPoints

if __name__ == '__main__':
	import sys
	print sys.argv[1]
	Create_Seeds(sys.argv[1])