# Add the parent folder to search for the python class for import
#$ python Testing/RunSeedTest.py 
# import sys
# import os.path
# sys.path.append(
#     os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


import BoneSegmentation_Slicer as BrentSeg
import SimpleITK as sitk
import timeit
import Dice
import numpy as np


# Brent's MacBook paths
MRI_Filenames = [\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr', \
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr', \
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr', \
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 4/VIBE/Volunteer4_VIBE_we.hdr']

GT_Filenames = [\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer1_GroundTruth.hdr',\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer2_GroundTruth.hdr',\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer3_GroundTruth.hdr',\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer4_GroundTruth.hdr']

def loadSeedPoints(filename):
	readfile = open(filename, "rU")
	readlines = readfile.readlines()
	x = []
	y = []
	z = []
	for i in range(3,len(readlines)):	
		currLine = readlines[i].split(",")
		x.append(currLine[1])
		y.append(currLine[2])
		z.append(currLine[3])
	return {'x':x, 'y':y ,'z':z}
	
def saveLog(filename, logData):
	try:
		#Save computation time in a log file
		text_file = open(filename, "r+")
		text_file.readlines()
		text_file.write("%s\n" % logData)
		text_file.close()
	except:
		print("Failed writing log data to .txt file")
 
def main(MRI_Filename, GT_Filename, label, num_seeds=5, kernelRadius=2):

	DiceList = []

	# Load MRI and ground truth image
	MRI   = sitk.ReadImage(MRI_Filename)
	GroundTruth = sitk.ReadImage(GT_Filename)

	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(kernelRadius)
	GroundTruth = erodeFilter.Execute(GroundTruth, 0, 1, False) 


	MRI = sitk.Cast(MRI, sitk.sitkUInt16)

	# sitk.Show(MRI, 'MRI')
	# sitk.Show(GroundTruth, 'GroundTruth')

	# Choose some random location within the ground truth bone as an 
	# initial seed location

	ndaMRI = sitk.GetArrayFromImage(MRI)
	ndaMRI = np.asarray(ndaMRI)

	ndaGT = sitk.GetArrayFromImage(GroundTruth)
	ndaGT = np.asarray(ndaGT)
	ndaGT[ndaGT != label] = 0
	ndaGT[ndaGT != 0] = 1

	GroundTruth = sitk.Cast(sitk.GetImageFromArray(ndaGT), GroundTruth.GetPixelID())
	GroundTruth.CopyInformation(MRI)

	# sitk.Show(GroundTruth, 'GroundTruth')

	ndx = np.where(ndaGT == 1) 

	''' Use the ground truth image to create random seed locations within bone '''
	seedPoints = []
	for i in range(0, num_seeds):
		rand_ndx = np.random.random_integers(len(ndx[0]))
		

		new_point = np.asarray([ndx[2][rand_ndx],  ndx[1][rand_ndx], ndx[0][rand_ndx]])
		seedPoints.append(new_point)

	print(seedPoints)

	# Show the seed location on the MRI image
	# ndaGT = ndaGT * 0
	# ndaGT[new_point[0], new_point[1], new_point[2]] = 255
	# GroundTruth = sitk.Cast(sitk.GetImageFromArray(ndaGT), GroundTruth.GetPixelID())
	# GroundTruth.CopyInformation(MRI)
	# sitk.Show(GroundTruth)
	# sitk.Show(MRI)
	# return
	# sitk.Show(GroundTruth, 'GroundTruth')
	# sitk.Show(segmentedImg, 'segmentedImg')


	segmentationClass = BrentSeg.BoneSeg()
	DiceCalulator = Dice.DiceCalulator()

	for i in range(0, num_seeds): 
		
		start_time = timeit.default_timer()
		
		# Run segmentation with randomly selected seed
		segmentedImg = segmentationClass.Execute(MRI, [seedPoints[i]], False)

		# Compute dice overlap between segmentation and ground truth
		DiceCalulator.SetImages(GroundTruth, segmentedImg)
		dice_value = DiceCalulator.Calculate()
		# dice_value = round(dice_value,4)
		# print(dice_value)

		print('Dice = ' + str(dice_value))

		DiceList.append(Dice)

		# Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time


		logData = str(dice_value) + ',' + str(seedPoints[i]) + ',' + str(elapsed) + \
		MRI_Filename + ',' + str(label)
		filename = 'SeedSensitivityLog.txt'
		saveLog(filename, logData)

	return 1
	
##STARTS HERE##
if __name__ == '__main__':
	start_time = timeit.default_timer()

	displayColors = True #Change the color of the output text
	if displayColors == True:
		from colorama import init
		from colorama import Fore
		from colorama import Back
		from colorama import Style
		init()

		MRI_Filename = MRI_Filenames[0]
		GT_Filename = GT_Filenames[0]
		label = 2

		print(Style.BRIGHT + Fore.YELLOW + 'Starting seed location test code ')
		main(MRI_Filename, GT_Filename, label)
		
	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	print(Fore.BLUE + "Elapsed Time (secs):" + str(round(elapsed,3)))





# Windows path
# imageFilenames = [\
# 'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer1_VIBE.hdr',
# 'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer2_VIBE.hdr',
# 'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer3_VIBE.hdr',
# 'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer4_VIBE.hdr']
# groundtruthFilenames = [\
# 'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer1_GroundTruth.hdr',
# 'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer2_GroundTruth.hdr',
# 'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer3_GroundTruth.hdr',
# 'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer4_GroundTruth.hdr']
# seedListFiles = [\
# 'SeedList/Volunteer1_SeedList.csv',\
# 'SeedList/Volunteer2_SeedList.csv',\
# 'SeedList/Volunteer3_SeedList.csv',\
# 'SeedList/Volunteer4_SeedList.csv']
