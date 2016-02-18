#Add the parent folder to search for the python class for import
#$ python Testing/RunSeedTest.py 
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


import BoneSegmentation as BrentSeg
import MultiprocessorHelper
import SimpleITK as sitk
import timeit
import Dice
import numpy

from scipy.optimize import differential_evolution

# Brent's MacBook paths
imageFilenames = [\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 1/VIBE/Volunteer1_VIBE_we.hdr', \
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 2/VIBE/Volunteer2_VIBE_we.hdr', \
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 3/VIBE/Volunteer3_VIBE_we.hdr', \
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/Volunteer 4/VIBE/Volunteer4_VIBE_we.hdr']

seedListFiles = ['SeedList/Volunteer1_SeedList.csv', \
'SeedList/Volunteer2_SeedList.csv', \
'SeedList/Volunteer3_SeedList.csv', \
'SeedList/Volunteer4_SeedList.csv']


groundtruthFilenames = [\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer1_GroundTruth.hdr',\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer2_GroundTruth.hdr',\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer3_GroundTruth.hdr',\
'/Users/Brent/Google Drive/Research/MRI Wrist Images/CMC OA/VIBE Ground Truth/Volunteer4_GroundTruth.hdr']


#Windows path
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
 
def SaveSegmentation(image, filename):
	#Save the segmentation
	print("Saving segmentation to "),
	imageWriter = sitk.ImageFileWriter()
	# tempFilename = imageFilenames[k]
	# tempFilename = tempFilename[0:len(tempFilename)-4] + '_segmentation.hdr'
	imageWriter.Execute(image, filename, True)
	print("Segmentation saved")
	
def runSegmentation(parameter):

	start_time = timeit.default_timer()
	
	global segmentationClass, SeedPoints, GroundTruth, MRI_Image, DiceCalulator
	
	#Load the images and take mean Dice value
	DiceList = []
	for k in range(0,len(imageFilenames)):
		#Load the data
		MRI_Image = sitk.ReadImage(imageFilenames[k])
		GroundTruth = sitk.ReadImage(groundtruthFilenames[k])

		seedsFilename = seedListFiles[k]
		textSeeds = loadSeedPoints(seedsFilename)
		SeedPoints = []
		for i in xrange(0,9): #Select which bone (or all of them) from the csv file
			#Convert from string to float
			tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
			SeedPoints.append(tempFloat)
		
		Segmentation = multiHelper.Execute(segmentationClass, SeedPoints, MRI_Image,parameter, True)

	# sitk.Show(Segmentation)
		# SaveSegmentation(Segmentation, 'E:\Google Drive\Research\Wrist MRI Database\VIBE\segmentation_temp.hdr')
	
		#Calculate Dice coefficient 
		DiceCalulator.SetImages(GroundTruth, Segmentation)
		Dice = DiceCalulator.Calculate()
		Dice = -1*round(Dice,2) #Try rounding it
		DiceList.append(Dice)
		
	#Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	#Save the data to a log file (for plotting later perhaps)
	logData = [parameter[0], parameter[1], parameter[2], DiceList, elapsed]
	
	#Take the mean of the Dice value for all the MRI images
	Dice = numpy.mean(DiceList)
	
	filename = 'OptimizationLog.txt'
	saveLog(filename, logData)
	
	#Print the status updates to the terminal
	print(Style.BRIGHT + Fore.YELLOW + ' Dice = '),
	print(Fore.GREEN + str(round(Dice * 100,4)) + ','), #Round the dice coeffient only for better displaying
	print(Fore.CYAN + 'Threshold = '),
	print(str(round(parameter[0],2))),
	print(Fore.CYAN + 'Iterations = '),
	print(str(round(parameter[1],0))),
	print(Fore.CYAN + 'MaxRMSError = '),
	print(str(round(parameter[2],3))),
	print(Fore.BLUE + "Elapsed Time (secs):"),
	print(str(round(elapsed,2)))	
	
	#Need to return the negative dice coefficient (since optimization minimizes not maximizes)
	return Dice
	
	
##STARTS HERE##
if __name__ == '__main__':
	displayColors = True #Change the color of the output text
	if displayColors == True:
		from colorama import init
		from colorama import Fore
		from colorama import Back
		from colorama import Style
		init()
		

	# for k in range(0,len(imageFilenames)):
		# print("Filename:"),
		# print(imageFilenames[k])
		## Load the data
		# MRI_Image = sitk.ReadImage(imageFilenames[k])

		# seedsFilename = seedListFiles[k]
		# textSeeds = loadSeedPoints(seedsFilename)
		# SeedPoints = []
		# for i in [6]:#xrange(0,9): #Select which bone (or all of them) from the csv file
			## Convert from string to float
			# tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
			# SeedPoints.append(tempFloat)

		# print("seeds:"),
		# print(SeedPoints)

		segmentationClass = BrentSeg.BoneSeg()
		DiceCalulator = Dice.DiceCalulator()
		# GroundTruth = sitk.ReadImage(groundtruthFilenames[k])
		
		multiHelper = MultiprocessorHelper.Multiprocessor()
		
		# runSegmentation([69, 25000, 0.002]) #Sanity check to ensure everything is working

		#TEST
		# curvatureFilter = sitk.MinMaxCurvatureFlowImageFilter()
		# print(curvatureFilter)
		# MRI_Image = sitk.Cast(MRI_Image, sitk.sitkFloat32)
		# MRI_Image = curvatureFilter.Execute(MRI_Image)
		# SaveSegmentation(MRI_Image, 'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer2_VIBE_minmaxfiltered.hdr')
		# print('filtered image saved')
		#TEST
		
		# runSegmentation([69, 2000, 0.0013])
		
		bounds = [(60,150), (0.001, 0.01), (1500,2500), (0.001, 0.01)]
		result = differential_evolution(runSegmentation, bounds, disp=True, popsize=2)
		print(result)

		#Save the segmentation
		# print("Saving segmentation to "),
		# imageWriter = sitk.ImageFileWriter()
		# tempFilename = imageFilenames[k]
		# tempFilename = '/Users/Brent/Desktop/Segmentations/' + tempFilename[len(tempFilename)-19:len(tempFilename)-4] + '_segmentation.hdr'
		# tempFilename =  'E:\Google Drive\Research\Wrist MRI\Segmentations\Volunteer2_TEST.hdr'
		# + tempFilename[len(tempFilename)-19:len(tempFilename)-4] + '_segmentation.hdr'
		
		
		# print(tempFilename)
		# imageWriter.Execute(outputSegmentation, tempFilename, True)
		# print("Segmentation saved")

		try:
			#Save computation time in a log file
			text_file = open("computation_times.txt", "r+")
			text_file.readlines()
			text_file.write("%s\n" % elapsed)
			text_file.close()
		except:
			print("Failed writing computation time to .txt file")



# print('\033[94m' + "Applying preprocessing...")
		#Filter to reduce noise while preserving edges
		#May be better to do the pre-processing only once to speed up computation
		# anisotropicFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
		# anisotropicFilter.SetNumberOfIterations(1)
		# anisotropicFilter.SetTimeStep(0.01)
		# anisotropicFilter.SetConductanceParameter(3)

		# smoothed_MRI_Image = sitk.Cast(MRI_Image, sitk.sitkFloat32)


		# smoothed_MRI_Image = anisotropicFilter.Execute(smoothed_MRI_Image)
		# MRI_Image = sitk.Cast(smoothed_MRI_Image, MRI_Image.GetPixelID())
		# print('\033[94m' + "Preprocessing done")


