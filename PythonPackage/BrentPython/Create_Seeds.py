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
			rand_ndx = np.random.random_integers(len(ndx[0]))
			new_point = np.asarray([ndx[2][rand_ndx],  ndx[1][rand_ndx], ndx[0][rand_ndx]])
			seedPoints.append(new_point)
		except:
			print('Error in creating random seed point. len(ndx[0]) = ' + str(len(ndx[0])))

	print seedPoints
	return seedPoints

if __name__ == '__main__':
	import sys
	print sys.argv[1]
	Create_Seeds(sys.argv[1])