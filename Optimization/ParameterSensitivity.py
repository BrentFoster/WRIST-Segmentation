import BoneSegmentation
import SimpleITK as sitk
import timeit
import Dice
import numpy as np
import BrentPython

def GetImagePaths():
	# Brent's MacBook image paths
	# MRI_Filenames = ['/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Filtered Images/Volunteer1_VIBE_we_filtered.hdr']

	# Brent's Lab PC image paths
	MRI_Directory = '/Users/Brent/Google Drive/Research/Projects/Carpal Bone Segmentation/MRI Images/Radiologist - MRI Carpal Bone Segmentation/Women/'
	MRI_Filenames = [MRI_Directory + 'Healthy_Women_2.nii']
					# MRI_Directory + '/Volunteer7_VIBE_Position_1.hdr',
					# MRI_Directory + '/Volunteer9_VIBE_Position_1.hdr',
					# MRI_Directory + '/Volunteer10_VIBE_Position_1.hdr',
					# MRI_Directory + '/Volunteer11_VIBE_Neutral.hdr']

	# Ground truth image paths (manually created using 3D Slicer)
	GT_Directory = '/Users/Brent/Google Drive/Research/Projects/Carpal Bone Segmentation/MRI Images/Radiologist - MRI Carpal Bone Segmentation/Expert Segmentations/Expert Segmentations in Nii Format/'
	GT_Filenames = [GT_Directory + 'Healthy_Women_2_MB.nii']
					# GT_Directory + '/Volunteer7_VIBE_gt.nii',
					# GT_Directory + '/Volunteer9_VIBE_gt.nii',
					# GT_Directory + '/Volunteer10_VIBE_gt.nii',
					# GT_Directory + '\Volunteer11_VIBE_gt.nii']
	
	GenderList = ['Male']


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

def main(MRI_Filename, GT_Filename, label, parameter, Subject_Gender, num_seeds=1, kernelRadius=1):
	# Load MRI and cast to 16 bit image type
	MRI = sitk.ReadImage(MRI_Filename)
	MRI = sitk.Cast(MRI, sitk.sitkUInt16)

	# Load the ground truth image
	GroundTruth = sitk.ReadImage(GT_Filename)

	# TEST
	# GroundTruth = BrentPython.FlipImageVertical(GroundTruth)
	# END TEST

	# sitk.Show(GroundTruth, 'GroundTruth')
	# sitk.Show(MRI, 'MRI')

	# Use the label number to determine which bone it is from (since the labels are in specified order)
	Current_Bone = GetBoneLabel(label)

	# Use the ground truth image to create random seed locations within bone label 
	seedPoint = GetRandomSeeds(GT_Filename, num_seeds, kernelRadius, label)
	print(seedPoint)
	
	# Initilize the needed python classes
	segmentationClass = BoneSegmentation.BoneSeg()

	start_time = timeit.default_timer()

	for i in parameter:
		# Set the parameters for the segmentation class object
		segmentationClass.SetShapeCurvatureScale(1)
		# segmentationClass.SetShapeMaxRMSError(0.001)
		# segmentationClass.SetShapeMaxIterations(800)
		# segmentationClass.SetShapePropagationScale(4)
		# segmentationClass.SetAnatomicalRelaxation(0.20)
		# segmentationClass.SetAnisotropicIts(5)

		segmentationClass.SetPatientGender(Subject_Gender)
		segmentationClass.SetCurrentBone(Current_Bone)	

		# Use the current parameter to modify the segmentation class
		# segmentationClass.SetShapeMaxRMSError(i)

			
		# Run segmentation with a randomly selected seed
		segmentedImg = segmentationClass.Execute(MRI, seedPoint, True, returnSitkImage=True, convertSeedPhyscialFlag=False)

		# Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time

		# Remove the non-label intensities from the ground truth and make them zero
		GroundTruth = RemoveLabels(label, GroundTruth, MRI)


		ComputeDice(GroundTruth, segmentedImg, seedPoint, elapsed, MRI_Filename, label, i)

		sitk.Show(segmentedImg, 'segmentedImg')

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

		print(Style.BRIGHT + Fore.YELLOW + 'Starting parameter sensitivity test code ')


	i = 0
	label = 4
	# parameter = np.linspace(40, 110, num=10) # Sigmoid threshold level
	# parameter = np.linspace(50, 2500, num=14) # Levelset maximum iterations
	# parameter = np.linspace(0, 0.015, num=15) # Levelset max RMS error

	parameter = np.linspace(5.4, 6.5, num=1) # Levelset shape propagation scale

	[MRI_Filenames, GT_Filenames, GenderList] = GetImagePaths()
	

	MRI_Filename = MRI_Filenames[i]
	GT_Filename = GT_Filenames[i]
	Subject_Gender = GenderList[i]

	# num_seeds = 10 corresponds to ~3 hours
	# kernelRadius = 5 seems to be a good amount
	main(MRI_Filename, GT_Filename, label, parameter, Subject_Gender, num_seeds=1, kernelRadius=2)			

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