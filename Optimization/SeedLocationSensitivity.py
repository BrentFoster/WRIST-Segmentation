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


# Brent's MacBook image paths
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


# Brent's Lab PC image paths
# MRI_Filenames = [\
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr', \
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr', \
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr', \
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 4/VIBE/Volunteer4_VIBE_we.hdr']

# GT_Filenames = [\
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer1_GroundTruth.hdr',\
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer2_GroundTruth.hdr',\
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer3_GroundTruth.hdr',\
# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer4_GroundTruth.hdr']



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
 
def main(MRI_Filename, GT_Filename, label, num_seeds=5, kernelRadius=1):

	DiceList = []

	# Load MRI and cast to 16 bit
	MRI = sitk.ReadImage(MRI_Filename)
	MRI = sitk.Cast(MRI, sitk.sitkUInt16)

	# Load the ground truth image
	GroundTruth = sitk.ReadImage(GT_Filename)

	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(kernelRadius)
	GroundTruth = erodeFilter.Execute(GroundTruth, 0, label, False) 

	# Find all the locations within the ground truth bone with an intensity of 1 (current label)
	ndaGT = sitk.GetArrayFromImage(GroundTruth)
	ndx = np.where(ndaGT == label) 

	# Reload the ground truth image (so there is no erosion)
	GroundTruth = sitk.ReadImage(GT_Filename)
	ndaGT = sitk.GetArrayFromImage(GroundTruth)

	# Remove the non-label intensities from the ground truth and make them zero
	ndaGT = np.asarray(ndaGT)
	ndaGT[ndaGT != label] = 0
	ndaGT[ndaGT != 0] = 1

	# Convert back to a SimpleITK image type
	GroundTruth = sitk.Cast(sitk.GetImageFromArray(ndaGT), GroundTruth.GetPixelID())
	GroundTruth.CopyInformation(MRI)


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

	print(seedPoints)

	segmentationClass = BrentSeg.BoneSeg()
	DiceCalulator = Dice.DiceCalulator()

	for i in range(0, len(seedPoints)): 
		
		start_time = timeit.default_timer()

		# sitk.Show(GroundTruth, 'GroundTruth')
		# sitk.Show(MRI, 'MRI')

		# Run segmentation with a randomly selected seed
		segmentedImg = segmentationClass.Execute(MRI, [seedPoints[i]], True)

		# Compute dice overlap between segmentation and ground truth
		DiceCalulator.SetImages(GroundTruth, segmentedImg)
		dice_value = DiceCalulator.Calculate()
		dice_value = round(dice_value,4)

		print('Dice = ' + str(dice_value) + 'for location ' + str(seedPoints[i]))

		DiceList.append(dice_value)

		# Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time

		# Save the log data to a text file
		logData = str(dice_value) + ',' + str(label) + ',' + str(elapsed) + ',' + \
		str(seedPoints[i]) + ',' + MRI_Filename 

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

		print(Style.BRIGHT + Fore.YELLOW + 'Starting seed location test code ')

	for i in range(0,len(MRI_Filenames)):
		for label in range(1,10):
			print('i = ' + str(i) + ' label = ' + str(label))
			MRI_Filename = MRI_Filenames[i]
			GT_Filename = GT_Filenames[i]

			# num_seeds = 10 corresponds to ~3 hours
			# kernelRadius = 5 seems to be a good amount

			try:
				main(MRI_Filename, GT_Filename, label, num_seeds=30, kernelRadius=5)	
			except:
				print('ERROR IN MAIN!!')


		
	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	print(Fore.BLUE + "Elapsed Time (secs):" + str(round(elapsed,3)))






# seedListFiles = [\
# 'SeedList/Volunteer1_SeedList.csv',\
# 'SeedList/Volunteer2_SeedList.csv',\
# 'SeedList/Volunteer3_SeedList.csv',\
# 'SeedList/Volunteer4_SeedList.csv']


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