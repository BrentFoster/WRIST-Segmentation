import SimpleITK as sitk
import timeit
import numpy as np

import copy


# Import modules from the BrentPython Python package 
import BrentPython
from BrentPython import *
from BrentPython import BrentFiltering
from BrentPython import Create_Seeds
from BrentPython import Dice
from BrentPython import SpectralClutering

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

	# # Thumb maneuver study (Window paths)
	# MRI_Filenames = [\
	# 'E:\Google Drive\Research\MRI Wrist Images\Thumb Maneuvers\Filtered Images\Volunteer1_VIBE_Neutral_2.hdr', \
	# 'E:\Google Drive\Research\MRI Wrist Images\Thumb Maneuvers\Filtered Images\Volunteer2_VIBE_Neutral.hdr', \
	# 'E:\Google Drive\Research\MRI Wrist Images\Thumb Maneuvers\Filtered Images\Volunteer3_VIBE_Position3.hdr',\
	# 'E:\Google Drive\Research\MRI Wrist Images\Thumb Maneuvers\Filtered Images\Volunteer4_VIBE_Neutral.hdr', \
	# 'E:\Google Drive\Research\MRI Wrist Images\Thumb Maneuvers\Filtered Images\Volunteer5_VIBE_Position3.hdr',\
	# ]
	
	# GT_Filenames = [\
	# 'E:\Google Drive\Research\Projects\Thumb Maneuvers\Segmentations\Volunteer 1\Neutral\Volunteer1_Neutral.nii',\
	# 'E:\Google Drive\Research\Projects\Thumb Maneuvers\Segmentations\Volunteer 2\Neutral\Volunteer2_Neutral.nii',\
	# 'E:\Google Drive\Research\Projects\Thumb Maneuvers\Segmentations\Volunteer 3\Radial Abduction\Volunteer3_Position3.nii',\
	# 'E:\Google Drive\Research\Projects\Thumb Maneuvers\Segmentations\Volunteer 4\Neutral\Volunteer4_Neutral.nii',\
	# 'E:\Google Drive\Research\Projects\Thumb Maneuvers\Segmentations\Volunteer 5\Radial Abduction\Volunteer5_Position3.nii',\
	# ]

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
 
def SaveSlice(MRI, segmentedImg, seedPoint, filename):
	''' Save a screenshot of the slice where the seed is from with the segmentation overlaid '''

	overlaidImg = BrentPython.OverlayImages(sitkImage=MRI, labelImage=segmentedImg, opacity=0.2, backgroundValue=0)

	ndaImg = sitk.GetArrayFromImage(overlaidImg)

	# Select the correct slice number to save 2D image
	ndaImg = ndaImg[seedPoint[2], :, :]

	# Highlight the seed on the 2D image
	ndaImg[seedPoint[1], seedPoint[0]] = 0

	# Convert back to a SimpleITK image type
	sitkSlice = sitk.Cast(sitk.GetImageFromArray(ndaImg), overlaidImg.GetPixelID())

	BrentPython.SaveSegmentation(sitkSlice, filename, verbose = False)	

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

def RunSpectralClustering(sitkImage, seedPoint, refImage):
	ClusterFilter = SpectralClutering()
	ClusterFilter.AddSeedLocation(seedPoint)
	ClusterFilter.SetScaling([2,2,2])

	start_time = timeit.default_timer()
	labelimg = ClusterFilter.Execute(sitkImage)
	labelimg.CopyInformation(sitkImage)

	BrentPython.SaveSegmentation(labelimg, 'ScreenShots\labelimg.nii', verbose = True)	

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	print('elapsed time:'),
	print(elapsed)

	labelimg.CopyInformation(refImage)
	labelimg = sitk.Cast(labelimg, refImage.GetPixelID())

	return labelimg

def output_measures(GroundTruth, segmentedImg, seedPoint, label, MRI_Filename, MRI_num, seed_num):
	''' Create output measures by comparing the segmentation with ground truth '''
	overlapFitler = sitk.LabelOverlapMeasuresImageFilter()
	overlapFitler.Execute(GroundTruth, segmentedImg)
	dice_value = overlapFitler.GetDiceCoefficient()
	dice_value = round(dice_value, 2)
	# print(overlapFitler)

	#print('Dice = ' + str(dice_value) + ' for Volunteer ' + str(MRI_num) + ' and location ' + str(seedPoint))

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	# Save the log data to a text file
	logData = str(dice_value) + ',' + str(label) + ',' + str(elapsed) + ',' + \
	str(seedPoint) + ',' + MRI_Filename 

	filename = 'SeedSensitivityLog.txt'
	saveLog(filename, logData)

	print('Volunteer: ' + str(MRI_num) + ' Label: ' + str(label) + ' Seed Number: ' + str(seed_num) + ' Dice: ' + str(dice_value))


	return dice_value

def EstimateSigmoid(image):
	''' Estimate the upper threshold of the sigmoid based on the 
	mean and std of the image intensities '''
	ndaImg = sitk.GetArrayFromImage(image)

	# [ndaImg > 25]
	std = np.std(ndaImg) # 30 25
	mean = np.mean(ndaImg)

	# Using a linear model (fitted in Matlab and manually selected sigmoid threshold values)

	#UpperThreshold = 0.899*(std+mean) - 41.3

	UpperThreshold = 0.002575*(std+mean)*(std+mean) - 0.028942*(std+mean) + 36.791614

	print('Mean: ' + str(round(mean,2)))
	print('STD: ' + str(round(std,2)))
	print('UpperThreshold: ' + str(round(UpperThreshold,2)))
	print(' ')

	return UpperThreshold

def main(MRI_Filename, GT_Filename, label, num_seeds=5, kernelRadius=1, MRI_num=1):

	# Load MRI and cast to 16 bit
	MRI = load_MRI(MRI_Filename)

	#MRI = BrentPython.FlipImageVertical(MRI)

	# Load the ground truth (manual segmented) image
	GroundTruth = load_GT(GT_Filename, label)

	# Create a random seed
	seedPoints = Create_Seeds.New_Seeds(GT_Filename, num_seeds, label, kernelRadius)
	# seedPoints = []
	# new_point = np.array([355, 633, 147], dtype=int)
	# seedPoints.append(newq_point)

	# Set the parameters for the segmentation class object
	segmentationClass = BoneSegmentation.BoneSeg()
	segmentationClass.SetScalingFactor(1)
	segmentationClass.SetLevelSetUpperThreshold(80)
	segmentationClass.SetShapeMaxRMSError(0.002) #0.004
	segmentationClass.SetShapeMaxIterations(600)
	segmentationClass.SetShapePropagationScale(4) #2, 4
	segmentationClass.SetShapeCurvatureScale(1)


	# Estimate the threshold level by image intensity statistics
	UpperThreshold = EstimateSigmoid(MRI)
	segmentationClass.SetLevelSetUpperThreshold(UpperThreshold)

	for i in range(0, len(seedPoints)): 
		
		start_time = timeit.default_timer()

		# Run segmentation with a randomly selected seed
		segmentedImg = segmentationClass.Execute(MRI, [seedPoints[i]], True)
		segmentedImg.CopyInformation(GroundTruth)
		segmentedImg = sitk.Cast(segmentedImg, GroundTruth.GetPixelID())

		dice_value = output_measures(GroundTruth, segmentedImg, seedPoints[i], label, MRI_Filename, MRI_num,i)
		
		# Save a screenshot to understand any errors
		slice_filename =  'ScreenShots\Volunteer_' + str(MRI_num) + '_label_' + str(label) + '_slice_' + str(seedPoints[i][2]) + '_dice_' + str(dice_value) + '.nii'
		SaveSlice(MRI=MRI, segmentedImg=segmentedImg,  seedPoint=seedPoints[i], filename=slice_filename)

		# if dice_value < 0.5:
		# 	''' Run the spectral clustering on the segmentation to remove leakage '''
		# 	segmentedImg = RunSpectralClustering(segmentedImg, copy.copy(seedPoints[i]), GroundTruth)
		# 	segmentedImg.CopyInformation(GroundTruth)
		# 	segmentedImg = sitk.Cast(segmentedImg, GroundTruth.GetPixelID())

		# 	dice_value = output_measures(GroundTruth, segmentedImg, seedPoints[i], label, MRI_Filename)

		# 	slice_filename =  'ScreenShots\Volunteer_' + str(MRI_num) + '_label_' + str(label) + '_slice_' + str(seedPoints[i][2]) + '_dice_' + str(dice_value) + '_SC.nii'
		# 	SaveSlice(MRI=MRI, segmentedImg=segmentedImg,  seedPoint=seedPoints[i], filename=slice_filename)

	return 0
	
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

	for i in [2]:#range(0, len(MRI_Filenames)):
		for label in [1]:#range(1,10):
			#print('i = ' + str(i) + ' label = ' + str(label))
			MRI_Filename = MRI_Filenames[i]
			GT_Filename = GT_Filenames[i]

			try:			
				main(MRI_Filename, GT_Filename, label, num_seeds=1, kernelRadius=3, MRI_num=i+1)	
			except:
				print('ERROR IN MAIN!!')

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	print(Fore.BLUE + "Elapsed Time (secs):" + str(round(elapsed,3)))

def old_garbage():
	'Old code that is potentially useful for later'
	# num_seeds = 10 corresponds to ~3 hours
	# kernelRadius = 5 seems to be a good amount

	# segmentedImg = sitk.Cast(segmentedImg, GroundTruth.GetPixelID())

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