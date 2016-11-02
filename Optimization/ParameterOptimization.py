import BoneSegmentation
import SimpleITK as sitk
import timeit
import Dice
import numpy as np

from scipy.optimize import differential_evolution
from scipy.optimize import minimize

import BrentPython


def GetImagePaths():
	# Brent's MacBook image paths
	# MRI_Filenames = ['/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.hdr']

	# Brent's Lab PC image paths
	MRI_Directory = 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Training Dataset\VIBE Images'
	MRI_Filenames = [MRI_Directory + '\Volunteer1_VIBE_Neutral_1.hdr',\
					MRI_Directory + '\Volunteer7_VIBE_Position_1.hdr',\
					MRI_Directory + '\Volunteer9_VIBE_Position_1.hdr',\
					MRI_Directory + '\Volunteer10_VIBE_Position_1.hdr',\
					MRI_Directory + '\Volunteer11_VIBE_Neutral.hdr']

	# Ground truth image paths (manually created using 3D Slicer)
	GT_Directory = 'E:\Google Drive\Research\Projects\Carpal Bone Segmentation\MRI Images\Training Dataset\Segmented Images'
	GT_Filenames = [GT_Directory + '\Volunteer1_Neutral.nii',\
					GT_Directory + '\Volunteer7_VIBE_gt.nii',\
					GT_Directory + '\Volunteer9_VIBE_gt.nii',\
					GT_Directory + '\Volunteer10_VIBE_gt.nii',\
					GT_Directory + '\Volunteer11_VIBE_gt.nii']
	
	GenderList = ['Male', 'Male', 'Male', 'Female', 'Female']


	return MRI_Filenames, GT_Filenames, GenderList

def GetRandomSeeds(GT_Filename, num_seeds, kernelRadius, label):
	''' Use the ground truth image to create random seed locations within bone '''

	# Load the ground truth image
	GroundTruth = sitk.ReadImage(GT_Filename)

	erodeFilter = sitk.BinaryErodeImageFilter()
	erodeFilter.SetKernelRadius(kernelRadius)
	GroundTruth = erodeFilter.Execute(GroundTruth, 0, label, False) 

	# Find all the locations within the ground truth bone with an intensity of 1 (current label)
	ndaGT = sitk.GetArrayFromImage(GroundTruth)
	ndx = np.where(ndaGT == label) 

	seedPoints = []
	for i in range(0, num_seeds):
		try:
			# Choose some random location out of the index fround above (ndx) 
			rand_ndx = np.random.random_integers(len(ndx[0]))
			new_point = np.asarray([ndx[2][rand_ndx],  ndx[1][rand_ndx], ndx[0][rand_ndx]])
			seedPoints.append(new_point)
		except:
			print('Error in creating random seed point. len(ndx[0]) = ' + str(len(ndx[0])))

	return seedPoints

def RemoveLabels(label, img, refImg):
	''' Remove the non-label intensities from the ground truth and make them zero '''
	
	print('label = ' + str(label))
	ndaGT = sitk.GetArrayFromImage(img)
	ndaGT = np.asarray(ndaGT)
	ndaGT[ndaGT != label] = 0
	ndaGT[ndaGT != 0] = 1

	# Convert back to a SimpleITK image type
	img = sitk.Cast(sitk.GetImageFromArray(ndaGT), img.GetPixelID())
	img.CopyInformation(refImg)

	return img

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
 
def ComputeDice(GroundTruth, segmentedImg, seedPoint, elapsed, MRI_Filename, label, parameter):
	''' Compute dice overlap between segmentation and ground truth '''

	DiceCalulator = Dice.DiceCalulator()
	DiceCalulator.SetImages(GroundTruth, segmentedImg)
	dice_value = DiceCalulator.Calculate()
	dice_value = round(dice_value,4)

	print('Dice = ' + str(dice_value) + ' for location ' + str(seedPoint))

	# Save the log data to a text file
	logData = str(dice_value) + ',' + str(parameter) + ',' + str(seedPoint) + ',' + str(elapsed) + ',' + \
	MRI_Filename + ',' + str(label)

	filename = 'ParameterSensitivityLog.txt'
	saveLog(filename, logData)

	return 0

def GetBoneLabel(label):
	BoneList = ['Trapezium', 'Trapezoid', 'Scaphoid', 'Capitate', 'Lunate', 'Hamate', 'Triquetrum', 'Pisiform']
	Current_Bone = BoneList[label-1] # Subtract one sice index starts at 0 and labels start at 1
	return Current_Bone

def runSegmentation(parameter):

	start_time = timeit.default_timer()
	
	# global segmentationClass, SeedPoints, GroundTruth, MRI_Image, DiceCalulator
	
	# Segmentation = multiHelper.Execute(segmentationClass, SeedPoints, MRI_Image,parameter)

	# Initilize the needed python classes
	segmentationClass = BoneSegmentation.BoneSeg()

	[MRI_Filenames, GT_Filenames, GenderList] = GetImagePaths()

	imageWriter = sitk.ImageFileWriter()

	
	iter = 0
	dice_array = []

	for i in range(2,4): # MRI Filename Number
		for j in range(2,5): # Bone Label Number
			for k in range(1,4): # Seed Number
				try:

					MRI_Filename = MRI_Filenames[i]
					GT_Filename = GT_Filenames[i]
					Subject_Gender = GenderList[i]
					label=j

					# Load MRI and cast to 16 bit image type
					MRI = sitk.ReadImage(MRI_Filename)
					MRI = sitk.Cast(MRI, sitk.sitkUInt16)

					MRI = BrentPython.FlipImageVertical(MRI)

					# Load GroundTruth and cast to 16 bit image type
					GroundTruth = sitk.ReadImage(GT_Filename)
					GroundTruth = sitk.Cast(GroundTruth, sitk.sitkUInt16)

					# Keep only the current label in the GroundTruth image
					GroundTruth = RemoveLabels(label=label, img=GroundTruth, refImg=GroundTruth)

					# Use the ground truth image to create random seed locations within bone label 
					seedPoint = GetRandomSeeds(GT_Filename, num_seeds=1, kernelRadius=1, label=label)
					print(seedPoint)

					# Use the label number to determine which bone it is from (since the labels are in specified order)
					Current_Bone = GetBoneLabel(label)

					# Set the currently being optimized parameters for the segmentation class object	
					# bounds = [(400,1000), (0,0.30), (3,5), (0.001, 0.01)]			
					segmentationClass.SetShapeMaxIterations(parameter[0])
					segmentationClass.SetAnatomicalRelaxation(parameter[1])
					segmentationClass.SetShapePropagationScale(parameter[2])
					segmentationClass.SetShapeMaxRMSError(parameter[3])			

					segmentationClass.SetShapeCurvatureScale(1)
					segmentationClass.SetPatientGender(Subject_Gender)
					segmentationClass.SetCurrentBone(Current_Bone)	
				
					# Run segmentation with a randomly selected seed
					segmentedImg = segmentationClass.Execute(MRI, seedPoint, verbose=False, returnSitkImage=True, convertSeedPhyscialFlag=False)

					# # Save the segmented image (for debugging purposes)				
					# imageWriter.Execute(segmentedImg, 'segmentedImg_Parameter_Optimization.nii', False)
					# imageWriter.Execute(GroundTruth, 'GT_Optimization.nii', False)
					# imageWriter.Execute(MRI, 'MRI_Parameter_Optimization.nii', False)

					print('Current_Bone is ' + Current_Bone)
					print('Current Gender is ' + Subject_Gender)

					# Determine how long the algorithm took to run
					elapsed = timeit.default_timer() - start_time

					#Calculate Dice coefficient 
					DiceCalulator = Dice.DiceCalulator()
					DiceCalulator.SetImages(GroundTruth, segmentedImg)
					temp_dice = DiceCalulator.Calculate()
					temp_dice = -1*round(temp_dice,2) #Try rounding it
					dice_array.append(temp_dice)
					iter = iter + 1

					print(dice_array)

					#Determine how long the algorithm took to run
					elapsed = timeit.default_timer() - start_time

					mean_dice = np.average(dice_array)
					#Save the data to a log file (for plotting later perhaps)
					logData = [mean_dice, parameter[0], parameter[1], parameter[2], parameter[3], elapsed]
					filename = 'OptimizationLog.txt'
					saveLog(filename, logData)

					#Print the status updates to the terminal
					print(Style.BRIGHT + Fore.YELLOW + ' Dice = '),
					print(Fore.GREEN + str(round(mean_dice * 100,4)) + ','), #Round the dice coeffient only for better displaying
					print(Fore.CYAN + 'Iterations = '),
					print(str(round(parameter[0],0))),
					print(Fore.CYAN + 'Relaxation = '),
					print(str(round(parameter[1],2))),
					print(Fore.CYAN + 'Propagation Scale = '),
					print(str(round(parameter[2],2))),
					print(Fore.CYAN + 'MaxRMSError = '),
					print(str(round(parameter[3],3))),					
					print(Fore.BLUE + "Elapsed Time (secs):"),
					print(str(round(elapsed,2)))	

				except:
					print('SEGMENTATION FAILED. Skipping this one...')

	#Need to return the negative dice coefficient (since optimization minimizes not maximizes)
	return mean_dice

if __name__ == '__main__':
	
	start_time = timeit.default_timer()

	displayColors = True #Change the color of the output text
	if displayColors == True:
		from colorama import init
		from colorama import Fore
		from colorama import Back
		from colorama import Style
		init()

		print(Style.BRIGHT + Fore.YELLOW + 'Starting parameter sensitivity test code ')

	# num_seeds = 10 corresponds to ~3 hours
	# kernelRadius = 5 seems to be a good amount

	# Run optimization
	minimizer_kwargs = {"method": "Nelder-Mead"}
	bounds = [(400,700), (0.05,0.30), (3.8, 4.2), (0.001, 0.006)]
	print("Starting")
	result = differential_evolution(runSegmentation, bounds, disp=True, popsize=2)

	# Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	print(Fore.BLUE + "Elapsed Time (secs):" + str(round(elapsed,3)))
