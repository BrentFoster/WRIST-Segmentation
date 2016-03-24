import SimpleITK as sitk
import timeit
import numpy as np

# Import modules from the BrentPython Python package 
import BrentPython
from BrentPython import *
from BrentPython import BrentFiltering
from BrentPython import Create_Seeds
from BrentPython import Dice

def GetImagePaths():
	# Brent's MacBook image paths
	# MRI_Filenames = [\
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr', \
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr', \
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr', \
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 4/VIBE/Volunteer4_VIBE_we.hdr']

	# GT_Filenames = [\
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer1_GroundTruth.hdr',\
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer2_GroundTruth.hdr',\
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer3_GroundTruth.hdr',\
	# '/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer4_GroundTruth.hdr']


	# Brent's Lab PC image paths
	# Original MRI image paths
	# MRI_Filenames = [\
	# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr', \
	# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr', \
	# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr', \
	# 'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 4/VIBE/Volunteer4_VIBE_we.hdr']

	# Anisotropic and Bias corrected image paths (using 3D Slicer)
	MRI_Filenames = [\
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.nii', \
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer2_VIBE_we_filtered.nii', \
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer3_VIBE_we_filtered.nii', \
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer4_VIBE_we_filtered.nii']

	# Ground truth image paths (manually created using 3D Slicer)
	GT_Filenames = [\
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer1_GroundTruth.hdr',\
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer2_GroundTruth.hdr',\
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer3_GroundTruth.hdr',\
	'E:/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer4_GroundTruth.hdr']

	return MRI_Filenames, GT_Filenames

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
 
def SaveSlice(sitkImg, sliceNum, filename):
	
	ndaImg = sitk.GetArrayFromImage(sitkImg)

	ndaImg = ndaImg[:,:,sliceNum]

	# Convert back to a SimpleITK image type
	sitkSlice = sitk.Cast(sitk.GetImageFromArray(ndaImg), sitkImg.GetPixelID())

	BrentPython.SaveSegmentation(sitkSlice, 'sitkSlice.jpg', verbose = True)

	a

	return 0


def load_GT(GT_Filename, label):

	# Reload the ground truth image (so there is no erosion)
	GroundTruth = sitk.ReadImage(GT_Filename)
	ndaGT = sitk.GetArrayFromImage(GroundTruth)

	# Remove the non-label intensities from the ground truth and make them zero
	ndaGT = np.asarray(ndaGT)
	ndaGT[ndaGT != label] = 0
	ndaGT[ndaGT != 0] = 1

	# Convert back to a SimpleITK image type
	GroundTruth_thresh = sitk.Cast(sitk.GetImageFromArray(ndaGT), GroundTruth.GetPixelID())
	GroundTruth_thresh.CopyInformation(GroundTruth)

	return GroundTruth_thresh

def load_MRI(MRI_Filename, apply_filtering=False):
	MRI = sitk.ReadImage(MRI_Filename)
	MRI = sitk.Cast(MRI, sitk.sitkUInt16)

	if apply_filtering == True:
		# Run a curvature anisotropic diffusion filter 
		# http://www.itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1CurvatureAnisotropicDiffusionImageFilter.html

		biasFilter = BrentFiltering.SitkBias()
		# MRI = biasFilter.Execute(MRI)
		handsegFilter = BrentFiltering.Segment_Hand()
		MRI = handsegFilter.Execute(MRI)

		# DEBUG
		BrentPython.SaveSegmentation(MRI, 'MRI_bias.nii', verbose = True)
		# END DEBUG
		anisotropicFilter = BrentFiltering.AnisotropicFilter()
		MRI = anisotropicFilter.Execute(MRI)

		BrentPython.SaveSegmentation(MRI, 'MRI_diffusion_filtered.nii', verbose = True)

	return MRI

def main(MRI_Filename, GT_Filename, label, num_seeds=5, kernelRadius=1):

	DiceList = []

	# Load MRI and cast to 16 bit
	MRI = load_MRI(MRI_Filename)

	SaveSlice(image=MRI, sliceNum=42, filename='test.jpg')


	# Load the ground truth (manual segmented) image
	GroundTruth = load_GT(GT_Filename, label)

	seedPoints = Create_Seeds.New_Seeds(GT_Filename, num_seeds, label, kernelRadius)

	segmentationClass = BoneSegmentation.BoneSeg()
	segmentationClass.SetScalingFactor(1)
	DiceCalulator = Dice.DiceCalulator()

	for i in range(0, len(seedPoints)): 
		
		start_time = timeit.default_timer()

		# Run segmentation with a randomly selected seed
		segmentedImg = segmentationClass.Execute(MRI, [seedPoints[i]], True)

		# Compute dice overlap between segmentation and ground truth
		DiceCalulator.SetImages(GroundTruth, segmentedImg)
		print(DiceCalulator.Calculate())
		dice_value = round(DiceCalulator.Calculate(), 4)

		print('Dice = ' + str(dice_value) + 'for location ' + str(seedPoints[i]))

		DiceList.append(dice_value)

		# Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time

		# Save the log data to a text file
		logData = str(dice_value) + ',' + str(label) + ',' + str(elapsed) + ',' + \
		str(seedPoints[i]) + ',' + MRI_Filename 

		filename = 'SeedSensitivityLog.txt'
		saveLog(filename, logData)

	return 0
	
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
	
	[MRI_Filenames, GT_Filenames] = GetImagePaths()

	for i in range(0, len(MRI_Filenames)):
		for label in range(1,10):
			print('i = ' + str(i) + ' label = ' + str(label))
			MRI_Filename = MRI_Filenames[i]
			GT_Filename = GT_Filenames[i]

			# num_seeds = 10 corresponds to ~3 hours
			# kernelRadius = 5 seems to be a good amount

			# try:
			
			main(MRI_Filename, GT_Filename, label, num_seeds=30, kernelRadius=5)	
			# except:
				# print('ERROR IN MAIN!!')

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	print(Fore.BLUE + "Elapsed Time (secs):" + str(round(elapsed,3)))




# # DEBUG
# BrentPython.SaveSegmentation(GroundTruth, 'GroundTruth.nii', verbose = True)
# BrentPython.SaveSegmentation(segmentedImg, 'segmentedImg.nii', verbose = True)
# # END DEBUG

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