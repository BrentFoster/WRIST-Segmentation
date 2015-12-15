#Load the Python Packages
import SimpleITK as sitk
import timeit
from scipy.optimize import differential_evolution
from scipy.optimize import minimize

import numpy as np

#Self created python files (package created using the setup.py file)
# import BrentPython.Dice as Dice
# import BrentPython.BoneSegmentation as BrentSeg
# import BrentPython.MultiprocessorHelper as MultiprocessorHelper

import BoneSegmentation as BrentSeg
import MultiprocessorHelper
import SimpleITK as sitk
import Dice
import timeit

groundtruthFilenames = [\
'/Users/Brent/Google Drive/Research/Wrist MRI/Ground Truth/Volunteer1_GroundTruth.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/Ground Truth/Volunteer2_GroundTruth.hdr']

imageFilenames = [\
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer2_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer3_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer4_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer5_VIBE.hdr']

seedListFiles = [\
'SeedList/Volunteer1_SeedList.csv', \
'SeedList/Volunteer2_SeedList.csv', \
'SeedList/Volunteer3_SeedList.csv', \
'SeedList/Volunteer4_SeedList.csv', \
'SeedList/Volunteer5_SeedList.csv']

# Windows path
groundtruthFilenames = [\
'E:\Google Drive\Research\MRI Wrist Images\CMC OA\VIBE Ground Truth\Volunteer2_GroundTruth.hdr']
imageFilenames = [\
'E:\Google Drive\Research\MRI Wrist Images\CMC OA\Volunteer 2\Vibe\Volunteer2_VIBE_we.hdr']
seedListFiles = ['SeedList/Volunteer2_SeedList.csv']

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
	textSeeds = {'x':x, 'y':y ,'z':z}

	SeedPoints = []
	for i in range(1,9):#range(0,9): #Select which bone (or all of them) from the csv file
		#Convert from string to float
		tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
		SeedPoints.append(tempFloat)
	return SeedPoints

def SaveSegmentation(image, filename):
	#Save the segmentation
	print("Saving segmentation to "),
	imageWriter = sitk.ImageFileWriter()
	tempFilename = imageFilenames[k]
	tempFilename = tempFilename[0:len(tempFilename)-4] + '_segmentation.hdr'
	imageWriter.Execute(image, tempFilename, True)
	print(tempFilename)
	print("Segmentation saved")

def saveLog(filename, logData):
	try:
		#Save computation time in a log file
		text_file = open(filename, "r+")
		text_file.readlines()
		text_file.write("%s\n" % logData)
		text_file.close()
	except:
		print("Failed writing log data to .txt file")

def runSegmentation(parameter):

	start_time = timeit.default_timer()
	
	global segmentationClass, SeedPoints, GroundTruth, MRI_Image, DiceCalulator
	
	Segmentation = multiHelper.Execute(segmentationClass, SeedPoints, MRI_Image,parameter)

	# sitk.Show(Segmentation)


	#SaveSegmentation(Segmentation, 'E:\Google Drive\Research\Wrist MRI\VIBE\Volunteer2_VIBE_temp.hdr')
	
	#Calculate Dice coefficient 
	DiceCalulator.SetImages(GroundTruth, Segmentation)
	Dice = DiceCalulator.Calculate()
	Dice = -1*round(Dice,2) #Try rounding it
		
	#Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	
	#Save the data to a log file (for plotting later perhaps)
	logData = [parameter[0], parameter[1], parameter[2], Dice, elapsed]
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
		
	for k in [0]:#range(0,len(imageFilenames)):
		print("Filename:"),
		print(imageFilenames[k])

		global segmentationClass, SeedPoints, MRI_Image, DiceCalulator

		#Load Data
		MRI_Image = sitk.ReadImage(imageFilenames[k])
		GroundTruth = sitk.ReadImage(groundtruthFilenames[k])

		#TEMP##########################
		nda = sitk.GetArrayFromImage(GroundTruth)
		nda = np.asarray(nda)

		nda[nda < 2] = 0 #Remove the thumb for now
		nda[nda != 0] = 1

		GroundTruth = sitk.Cast(sitk.GetImageFromArray(nda), MRI_Image.GetPixelID())
		GroundTruth.CopyInformation(MRI_Image)
		#TEMP##########################

		SeedPoints = loadSeedPoints(seedListFiles[k])

		#Create opbjects of the needed classes
		segmentationClass = BrentSeg.BoneSeg()
		multiHelper = MultiprocessorHelper.Multiprocessor()
		DiceCalulator = Dice.DiceCalulator()
		
		
		
		#Run optimization

		
		minimizer_kwargs = {"method": "Nelder-Mead"}
		bounds = [(35,80), (400,1000), (0.001, 0.01), (1,4)]
		print("Starting")
		result = differential_evolution(runSegmentation, bounds, disp=True, popsize=2)
		#result = differential_evolution(runSegmentation, bounds, disp= True)

		# runSegmentation([101, 640, 0.009])
		
		#x0 = np.array([60, 1000, 0.003, 3])
		#res = minimize(runSegmentation, x0, method='Nelder-Mead', \
		#	options={'xtol': 1e-8, 'disp': True})

		print(result)

		print("Finished!")







