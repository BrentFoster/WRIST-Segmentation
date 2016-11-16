# Script to be launched with: python -m scoop TEST.py

import SimpleITK as sitk
import timeit
import numpy as np

from scoop import futures

data = [[i for i in range(x, x + 1000)] for x in range(0, 60, 1)]



def mySum(inIndex):
	"""The worker will only receive an index from network."""

	MRI_Filename = 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii'

	image = sitk.ReadImage(MRI_Filename)
	ndaImage = sitk.GetArrayFromImage(image)
	print(ndaImage)
	return ndaImage[inIndex]

if __name__ == '__main__':
    results = list(futures.map(mySum, range(len(data))))

# from scoop import futures, shared

# def myParallelFunc(inValue):
# 	# myValue = shared.getConst('myValue')

# 	MRI_Filename = 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii'

# 	image = sitk.ReadImage(MRI_Filename)
# 	ndaImage = sitk.GetArrayFromImage(image)
# 	print('inValue' + inValue)

# 	return myValue


# if __name__ == '__main__':
# 	MRI_Filename = 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii'

# 	image = sitk.ReadImage(MRI_Filename)
# 	ndaImage = sitk.GetArrayFromImage(image)


# 	shared.setConst(myValue=ndaImage)
# 	print('Starting parallel!')
# 	futures.map(myParallelFunc, range(8))
# 	print('Done!')