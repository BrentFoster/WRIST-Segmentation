import SimpleITK as sitk
import numpy as np


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


def New_Seeds_Group(GT_Filename, Slice=550, num_seeds=1, label=1, kernelRadius=2, buffer_size=50):
	# Load the ground truth image
	GroundTruth_original = sitk.ReadImage(GT_Filename)

	# erodeFilter = sitk.BinaryErodeImageFilter()
	# erodeFilter.SetKernelRadius(kernelRadius)
	# GroundTruth = erodeFilter.Execute(GroundTruth_original, 0, label, False) 

	''' Split the image into a top and bottom (to get seeds at the top and bottom of some bone) '''
	# ndaGT = sitk.GetArrayFromImage(GroundTruth)
	

	ndaGT_top = sitk.GetArrayFromImage(GroundTruth_original)
	ndaGT_top[:,Slice+1-buffer_size:ndaGT_top.shape[1], :] = 0

	ndaGT_bot = sitk.GetArrayFromImage(GroundTruth_original)
	ndaGT_bot[:, 0:Slice+buffer_size, :] = 0

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





	ndaGT = sitk.GetArrayFromImage(GroundTruth_original)
	ndaGT = ndaGT*0

	for i in range(0, len(seedPoints)):
		tempSeed = seedPoints[i]
		print(tempSeed)
		ndaGT[tempSeed[2], tempSeed[1], tempSeed[0]] = 255

	img_Output = sitk.Cast(sitk.GetImageFromArray(ndaGT), GroundTruth_original.GetPixelID())

	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(img_Output, 'ScreenShots/img_Output.nii', True)




	return seedPoints

if __name__ == '__main__':
	import sys
	print sys.argv[1]
	Create_Seeds(sys.argv[1])