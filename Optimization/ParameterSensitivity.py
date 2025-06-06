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
	MRI_Directory_Men   = 'E:/Google Drive/Research/Projects/Carpal Bone Segmentation/MRI Images/Radiologist - MRI Carpal Bone Segmentation/Men/'
	MRI_Directory_Women = 'E:/Google Drive/Research/Projects/Carpal Bone Segmentation/MRI Images/Radiologist - MRI Carpal Bone Segmentation/Women/'
	MRI_Filenames = [MRI_Directory_Women + 'Healthy_Women_1.nii',
					MRI_Directory_Women  + 'Healthy_Women_2.hdr',
					MRI_Directory_Women  + 'Healthy_Women_4.hdr',
					MRI_Directory_Women  + 'Healthy_Women_5.hdr',
					MRI_Directory_Men + 'Healthy_Men_1.nii',
					MRI_Directory_Men + 'Healthy_Men_2.nii',
					MRI_Directory_Men + 'Healthy_Men_4.nii',
					MRI_Directory_Men + 'Healthy_Men_5.nii']

	# Ground truth image paths (manually created using 3D Slicer)
	GT_Directory = 'E:/Google Drive/Research/Projects/Carpal Bone Segmentation/MRI Images/Radiologist - MRI Carpal Bone Segmentation/Expert Segmentations/Expert Segmentations in Nii Format/'
	GT_Filenames = [GT_Directory + 'Healthy_Women_1_MB.nii',
					GT_Directory + 'Healthy_Women_2_MB.nii',
					GT_Directory + 'Healthy_Women_4_MB.nii',
					GT_Directory + 'Healthy_Women_5_MB.nii',
					GT_Directory + 'Healthy_Men_1_MB.nii',
					GT_Directory + 'Healthy_Men_2_MB.nii',
					GT_Directory + 'Healthy_Men_4_MB.nii',
					GT_Directory + 'Healthy_Men_5_MB.nii']
	
	GenderList = ['Female', 'Female', 'Female', 'Female', 'Male', 'Male', 'Male', 'Male']


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

def RemoveLabels(label, img):
	''' Remove the non-label intensities from the ground truth and make them zero '''
	
	# Keep a copy of the original image to get the pixel type later on
	refImg = img

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
 
def ComputeDice(GroundTruth, segmentedImg, label):
	''' Compute dice overlap between segmentation and ground truth '''

	# Remove the non-label intensities from the ground truth and make them zero
	GroundTruth = RemoveLabels(label, GroundTruth)

	DiceCalulator = Dice.DiceCalulator()
	DiceCalulator.SetImages(GroundTruth, segmentedImg)
	dice_value = DiceCalulator.Calculate()
	dice_value = round(dice_value,4)

	print('Dice = ' + str(dice_value) + ' for label ' + str(label))

	return dice_value

def GetBoneLabel(label):
	BoneList = ['Trapezium', 'Trapezoid', 'Scaphoid', 'Capitate', 'Lunate', 'Hamate', 'Triquetrum', 'Pisiform']
	Current_Bone = BoneList[label-1] # Subtract one sice index starts at 0 and labels start at 1
	return Current_Bone

def main(MRI_Filenames, GT_Filenames, GenderList, parameter, num_seeds=1, kernelRadius=1, parameter_name=''):

	filename = 'ParameterSensitivityLog.txt'
	saveLog(filename, ' ')
	saveLog(filename, 'New experiment....')
	saveLog(filename, ' ')

	# Initilize the needed python classes
	segmentationClass = BoneSegmentation.BoneSeg()

	start_time = timeit.default_timer()

	dice_array = []

	for temp_parameter in parameter:

		for i in range(0,1):#len(MRI_Filenames)): # Image Filename Number
			start_time = timeit.default_timer()

			# Load MRI and cast to 16 bit image type
			MRI = sitk.ReadImage(MRI_Filenames[i])
			MRI = sitk.Cast(MRI, sitk.sitkUInt16)

			# Load the ground truth image
			GroundTruth = sitk.ReadImage(GT_Filenames[i])

			# Define the gender of the volunteer
			Subject_Gender = GenderList[i]

			for label in range(3,7): # Bone Label Number

				# Use the label number to determine which bone it is from (since the labels are in specified order)
				Current_Bone = GetBoneLabel(label)

				for k in range(0,1): # Seed Number
					# Use the ground truth image to create random seed locations within bone label 
					seedPoint = GetRandomSeeds(GT_Filenames[i], num_seeds, kernelRadius, label)

				
					# Set the parameters for the segmentation class object
					segmentationClass.SetShapeCurvatureScale(temp_parameter)
					# segmentationClass.SetShapeMaxRMSError(0.001)
					# segmentationClass.SetShapeMaxIterations(temp_parameter)
					# segmentationClass.SetShapePropagationScale(temp_parameter)
					# segmentationClass.SetAnatomicalRelaxation(temp_parameter)
					# segmentationClass.SetAnisotropicIts(5)

					segmentationClass.SetPatientGender(Subject_Gender)
					segmentationClass.SetCurrentBone(Current_Bone)	

					# Use the current parameter to modify the segmentation class
					# segmentationClass.SetShapeMaxRMSError()

					print('temp_parameter = ' + str(temp_parameter))

					try:
						# Run segmentation with a randomly selected seed
						segmentedImg = segmentationClass.Execute(MRI, seedPoint, verbose=False, returnSitkImage=True, convertSeedPhyscialFlag=False,
																LeakageCheckFlag=False)

						# Determine how long the algorithm took to run
						elapsed = timeit.default_timer() - start_time

						temp_dice = ComputeDice(GroundTruth, segmentedImg, label)

						dice_array.append(temp_dice)
					except:
						print('Failed to segment!')


					# sitk.Show(segmentedImg, 'segmentedImg')

					# Save the log data to a text file
					#mean_dice = np.average(dice_array)
					logData = str(round(temp_dice,4)) + ', ' + parameter_name + ', ' + str(temp_parameter) + ', ' + str(elapsed) + ',' + 'MRI_Num' + str(i) +',' + ' Label: ' + ', ' + str(label)

					filename = 'ParameterSensitivityLog.txt'
					saveLog(filename, logData)

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


	# parameter = np.linspace(40, 110, num=40) # Sigmoid threshold level
	# parameter = np.linspace(50, 2000, num=40) # Levelset maximum iterations
	# parameter = np.linspace(0.001, 0.025, num=20) # Levelset max RMS error
	# parameter = np.linspace(0, 1, num=20) # Anatomical Relaxation
	# parameter = np.linspace(1, 5, num=20) # Propagation Scale
	parameter = np.linspace(0, 3, num=20) # Curvature Scale


	# parameter = np.asarray([5.2105,    5.4210,    5.6315,    5.8420,    6.0525])

	print('parameter values are: ' + str(parameter))


	
	

	parameter_name = 'ShapeCurvatureScale'

	# parameter = np.linspace(5.4, 6.5, num=1) # Levelset shape propagation scale

	[MRI_Filenames, GT_Filenames, GenderList] = GetImagePaths()

	# num_seeds = 10 corresponds to ~3 hours
	# kernelRadius = 5 seems to be a good amount
	main(MRI_Filenames, GT_Filenames, GenderList, parameter, num_seeds=1, kernelRadius=2, parameter_name=parameter_name)			

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
# TEST
# GroundTruth = BrentPython.FlipImageVertical(GroundTruth)
# END TEST
