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

import BoneSegmentation

def GetImagePaths():
	# Brent's MacBook image paths
	# MRI_Filenames = ['/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.hdr']

	# Brent's Lab PC image paths
	# MRI_Directory = 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Training Dataset\VIBE Images'
	# MRI_Filenames = [MRI_Directory + '\Volunteer1_VIBE_Neutral_1.hdr',\
	# 				MRI_Directory + '\Volunteer7_VIBE_Position_1.hdr',\
	# 				MRI_Directory + '\Volunteer9_VIBE_Position_1.hdr',\
	# 				MRI_Directory + '\Volunteer10_VIBE_Position_1.hdr',\
	# 				MRI_Directory + '\Volunteer11_VIBE_Neutral.hdr']

	# Ground truth image paths (manually created using 3D Slicer)
	# GT_Directory = 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Training Dataset\Segmented Images'
	# GT_Filenames = [GT_Directory + '\Volunteer1_Neutral.nii',\
	# 				GT_Directory + '\Volunteer7_VIBE_gt.nii',\
	# 				GT_Directory + '\Volunteer9_VIBE_gt.nii',\
	# 				GT_Directory + '\Volunteer10_VIBE_gt.nii',\
	# 				GT_Directory + '\Volunteer11_VIBE_gt.nii']
	
	# GenderList = ['Male', 'Male', 'Male', 'Female', 'Female']



	GT_Filenames = [
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Men_1_YA.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Men_2_YA.nii',\
	# 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Men_3_YA.nii',\
	# 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Men_4_YA.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Men_5_YA.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Women_1_YA.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Women_2_YA.nii',\
	#'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Women_3_YA.nii',\
	#'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Women_4_YA.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Expert Segmentations\Expert Segmentations in Nii Format\Healthy_Women_5_YA.nii'
	]


	MRI_Filenames= [
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Men\Healthy_Men_1.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Men\Healthy_Men_2.nii',\
	# 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Men\Healthy_Men_3.nii',\
	# 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Men\Healthy_Men_4.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Men\Healthy_Men_5.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Women\Healthy_Women_1.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Women\Healthy_Women_2.nii',\
	#'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Women\Healthy_Women_3.nii',\
	#'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Women\Healthy_Women_4.nii',\
	'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Radiologist - MRI Carpal Bone Segmentation\Women\Healthy_Women_5.nii'
	]

	# GenderList = ['Male', 'Male', 'Male', 'Male', 'Male']#, 'Female', 'Female', 'Female', 'Female', 'Female']
	GenderList = ['Male', 'Male', 'Male', 'Female', 'Female', 'Female']

	return MRI_Filenames, GT_Filenames, GenderList

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

	BrentPython.SaveSegmentation(segmentedImg, filename, verbose = False)	

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

def output_measures(GroundTruth, segmentedImg, seedPoint, label, MRI_Filename, MRI_num, seed_num, elapsed):
	''' Create output measures by comparing the segmentation with ground truth '''
	overlapFitler = sitk.LabelOverlapMeasuresImageFilter()
	overlapFitler.Execute(GroundTruth, segmentedImg)
	dice_value = overlapFitler.GetDiceCoefficient()
	dice_value = round(dice_value, 2)
	# print(overlapFitler)

	#print('Dice = ' + str(dice_value) + ' for Volunteer ' + str(MRI_num) + ' and location ' + str(seedPoint))

	# Determine how long the algorithm took to run
	elapsed = round(elapsed, 3)

	# Save the log data to a text file
	logData = str(dice_value) + ',' + str(label) + ',' + str(elapsed) + ',' + \
	str(seedPoint) + ',' + MRI_Filename 

	filename = 'SeedSensitivityLog.txt'
	saveLog(filename, logData)

	print('Volunteer: ' + str(MRI_num) + ' Label: ' + str(label) + ' Seed Number: ' + str(seed_num) + ' Dice: ' + str(dice_value))


	return dice_value

def GetBoneLabel(label):
	BoneList = ['Trapezium', 'Trapezoid', 'Scaphoid', 'Capitate', 'Lunate', 'Hamate', 'Triquetrum', 'Pisiform']
	Current_Bone = BoneList[label-1] # Subtract one sice index starts at 0 and labels start at 1
	return Current_Bone

def main(MRI_Filename, GT_Filename, label, Subject_Gender, num_seeds=5, kernelRadius=1, MRI_num=1):

	# Load MRI and cast to 16 bit
	MRI = load_MRI(MRI_Filename)

	# MRI = BrentPython.FlipImageVertical(MRI)

	# Load the ground truth (manual segmented) image
	GroundTruth = load_GT(GT_Filename, label)
	# Create a random seed
	seedPoints = Create_Seeds.New_Seeds(GT_Filename, num_seeds, label, kernelRadius)

	# Use the label number to determine which bone it is from (since the labels are in specified order)
	Current_Bone = GetBoneLabel(label)

	# DEBUG
	print(MRI_Filename)
	print(GT_Filename)
	print(label)
	print(Current_Bone)
	print(seedPoints)
	# DEBUG END

	# Set the parameters for the segmentation class object
	segmentationClass = BoneSegmentation.BoneSeg()
	segmentationClass.SetShapeCurvatureScale(1)
	segmentationClass.SetShapeMaxRMSError(0.003)
	segmentationClass.SetShapeMaxIterations(300)
	segmentationClass.SetShapePropagationScale(4)
	segmentationClass.SetAnatomicalRelaxation(0.10)
	segmentationClass.SetAnisotropicIts(2)

	segmentationClass.SetPatientGender(Subject_Gender)
	segmentationClass.SetCurrentBone(Current_Bone)	

	for i in range(0, len(seedPoints)):

		print('Iteration: ' + str(i)) 
	
		start_time = timeit.default_timer()

		# Run segmentation with a randomly selected seed
		segmentedImg = segmentationClass.Execute(MRI, [seedPoints[i]], verbose=False, returnSitkImage=True, convertSeedPhyscialFlag=False)
		
		BrentPython.SaveSegmentation(segmentedImg, 'SegImg.nii', verbose=True)
		
		segmentedImg.CopyInformation(GroundTruth)
		segmentedImg = sitk.Cast(segmentedImg, GroundTruth.GetPixelID())

		# Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time

		dice_value = output_measures(GroundTruth, segmentedImg, seedPoints[i], label, MRI_Filename, MRI_num, i, elapsed)
		
		# Save a screenshot to understand any errors
		slice_filename = 'ScreenShots\Volunteer_' + str(MRI_num) + '_label_' + str(label) + '_slice_' + str(seedPoints[i][2]) + '_dice_' + str(dice_value) + '.nii'
		SaveSlice(MRI=MRI, segmentedImg=segmentedImg,  seedPoint=seedPoints[i], filename=slice_filename)

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
	
	[MRI_Filenames, GT_Filenames, GenderList] = GetImagePaths()


	for i in range(0, len(MRI_Filenames)):
		for label in range(1,9):

			print('i = ' + str(i) + ' label = ' + str(label))
			MRI_Filename = MRI_Filenames[i]
			GT_Filename = GT_Filenames[i]
			Subject_Gender = GenderList[i]

			try:			
				main(MRI_Filename, GT_Filename, label, Subject_Gender, num_seeds=30, kernelRadius=4, MRI_num=i+1)	
			except:
				print('ERROR IN MAIN!!')

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	print(Fore.BLUE + "Elapsed Time (secs):" + str(round(elapsed,3)))

def old_garbage():
	'Old code that is potentially (or not) useful for later'

	# def RunSpectralClustering(sitkImage, seedPoint, refImage):
	# 	ClusterFilter = SpectralClutering()
	# 	ClusterFilter.AddSeedLocation(seedPoint)
	# 	ClusterFilter.SetScaling([2,2,2])

	# 	start_time = timeit.default_timer()
	# 	labelimg = ClusterFilter.Execute(sitkImage)
	# 	labelimg.CopyInformation(sitkImage)

	# 	BrentPython.SaveSegmentation(labelimg, 'ScreenShots\labelimg.nii', verbose = True)	

	# 	# Determine how long the algorithm took to run
	# 	elapsed = timeit.default_timer() - start_time

	# 	print('elapsed time:'),
	# 	print(elapsed)

	# 	labelimg.CopyInformation(refImage)
	# 	labelimg = sitk.Cast(labelimg, refImage.GetPixelID())

	# 	return labelimg


	# seedPoints = []
	# new_point = np.array([305, 679, 148], dtype=int)
	# seedPoints.append(new_point)

	# if dice_value < 0.5:
	# 	''' Run the spectral clustering on the segmentation to remove leakage '''
	# 	segmentedImg = RunSpectralClustering(segmentedImg, copy.copy(seedPoints[i]), GroundTruth)
	# 	segmentedImg.CopyInformation(GroundTruth)
	# 	segmentedImg = sitk.Cast(segmentedImg, GroundTruth.GetPixelID())

	# 	dice_value = output_measures(GroundTruth, segmentedImg, seedPoints[i], label, MRI_Filename)

	# 	slice_filename =  'ScreenShots\Volunteer_' + str(MRI_num) + '_label_' + str(label) + '_slice_' + str(seedPoints[i][2]) + '_dice_' + str(dice_value) + '_SC.nii'
	# 	SaveSlice(MRI=MRI, segmentedImg=segmentedImg,  seedPoint=seedPoints[i], filename=slice_filename)



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