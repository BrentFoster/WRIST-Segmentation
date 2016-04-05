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
	
	MRI_Filename = ['E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii']
	
	# Create objects of the needed classes
	# Set the parameters for the segmentation class object
	segmentationClass = BoneSegmentation.BoneSeg()

	multiHelper = MultiprocessorHelper.Multiprocessor()
	DiceCalulator = Dice.DiceCalulator()

	MRI_Image = sitk.ReadImage(MRI_Filename[0])

	seedPoints = []
	new_point = np.array([220, 650, 100], dtype=int)
	seedPoints.append(new_point)
	# new_point = np.array([230, 680, 106], dtype=int)
	# seedPoints.append(new_point)
	print('seedPoints' + str(seedPoints))

	Segmentation = multiHelper.Execute(segmentationClass, seedPoints, MRI_Image, parameter=[1,2,3], verbose=True)

	BrentPython.SaveSegmentation(Segmentation, 'ScreenShots\CLI_Segmentation.nii', verbose=True)	

	# sitk.Show(Segmentation, 'Segmentation')
	
	return 0

if __name__ == '__main__':
	start_time = timeit.default_timer()
	
	main()

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	print("Elapsed Time (secs):" + str(round(elapsed,3)))

	print('Done!!')