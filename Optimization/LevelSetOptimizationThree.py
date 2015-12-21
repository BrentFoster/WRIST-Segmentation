import SimpleITK as sitk
import numpy as np
import multiprocessing
import timeit

def f(MRI_Array, SeedPoint,q, parameter):
	""" Function to be used with the Multiprocessor class (needs to be its own function 
		and not part of the same class to avoid the 'Pickle' type errors. """
	import BoneSegmentation as BrentSeg #This seems to be needed for Windows
	segmentationClass = BrentSeg.BoneSeg()

	#Change some parameter(s) of the segmentation class for the optimization
	if (len(parameter) > 1): 
		#Set the threshold and then compute/save the Dice coefficient
		segmentationClass.SetLevelSetUpperThreshold(parameter[0])
		segmentationClass.SetLevelSetIts(parameter[1])
		segmentationClass.SetLevelSetError(parameter[2])

	output = segmentationClass.Execute(MRI_Array,[SeedPoint], False)
	q.put(output)
	q.close()

class Multiprocessor(object):
	"""Helper class for sliptting a segmentation class (such as from SimpleITK) into
	several logical cores in parallel. Requires: SegmentationClass, Seed List, SimpleITK Image"""
	def __init__(self):
		# super(ClassName, self).__init__()
		self = self

	def Execute(self, segmentationClass, seedList, MRI_Image, parameter=0, verbose = False):
		self.segmentationClass = segmentationClass
		self.seedList = seedList
		self.MRI_Image = MRI_Image
		self.parameter = parameter
		self.verbose = verbose #Show output to terminal or not

		#Convert to voxel coordinates
		self.RoundSeedPoints() 
		
		# print(self.seedList)

		###Create an empty segmenationLabel array###
		nda = sitk.GetArrayFromImage(self.MRI_Image)
		nda = np.asarray(nda)
		nda = nda*0		
		self.segmentationArray = nda
		############################################
		##Convert the SimpleITK images to arrays##
		self.MRI_Array = sitk.GetArrayFromImage(self.MRI_Image)
		#####

		#Check the number of cpu's in the computer and if the seed list is greater than 
		#the number of cpu's then run the parallel computing twice
		#TODO: Use a 'pool' of works for this may be more efficient
		num_CPUs = multiprocessing.cpu_count() #Might be better to subtract 1 since OS needs one
		# num_CPUs = 1
		if self.verbose == True:
			print('\033[94m' + "Number of CPUs = "),
			print(num_CPUs)

		if (len(self.seedList) <= num_CPUs):
			jobOrder = range(0, len(self.seedList))
			if self.verbose == True:
				print(jobOrder)
			self.segmentationArray = self.RunMultiprocessing(jobOrder)

		elif (len(self.seedList) > num_CPUs):
			if self.verbose == True:
				print('\033[93m' + "Splitting jobs since number of CPUs < number of seed points")
			#Run the multiprocessing several times since there wasn't enough CPU's before
			jobOrder = self.SplitJobs(range(len(self.seedList)), num_CPUs)
			if self.verbose == True:
				print(jobOrder)
			for x in range(len(jobOrder)):
				self.segmentationArray = self.segmentationArray + (x+1)*self.RunMultiprocessing(jobOrder[x])

		#Convert segmentationArray back into an image
		segmentationOutput = sitk.Cast(sitk.GetImageFromArray(self.segmentationArray), self.MRI_Image.GetPixelID())
		segmentationOutput.CopyInformation(self.MRI_Image)

		return segmentationOutput

	###Split the Seed List using the multiprocessing library and then execute the pipeline###
	#Helper functions for the multiprocessing
	def RunMultiprocessing(self,jobOrder):
		procs = []
		q = multiprocessing.Queue()
		for x in jobOrder:
			p = multiprocessing.Process(target=f, args=(self.MRI_Array, self.seedList[x],q, self.parameter,))
			p.start()
			procs.append(p) #List of current processes

		tempArray = self.segmentationArray
		if self.verbose == True:
			print('\033[96m' + "Printing multiprocessing queue:")
		for i in range(len(jobOrder)):
			#Outputs an array (due to multiprocessing 'pickle' constraints)
			tempArray = tempArray + q.get() 
		# Wait for all worker processes to finish by using .join()
		for p in procs:
			p.join()
			p.terminate() #Unix

		if self.verbose == True:
			print('\033[96m' + 'Finished with processes:'),
			print(jobOrder)
		return tempArray

	def SplitJobs(self, jobs, size):
	     output = []
	     while len(jobs) > size:
	         pice = jobs[:size]
	         output.append(pice)
	         jobs   = jobs[size:]
	     output.append(jobs)
	     return output

	#Need to convert to voxel coordinates since we pass only the array due to a 'Pickle' error
	#with the multiprocessing library and the ITK image type which means the header information
	#is lost
	def RoundSeedPoints(self):
		#TEMP
		# print("Saving segmentation to "),
		# imageWriter = sitk.ImageFileWriter()
		# tempFilename = 'E:\Google Drive\Research\Wrist MRI\VIBE\Volunteer2_VIBE_temp_MRI.hdr'
		# imageWriter.Execute(self.MRI_Image, tempFilename, True)
		# print("Segmentation saved")
		#TEMP
		
		
		seeds = []
		for i in range(0,len(self.seedList)): #Select which bone (or all of them) from the csv file
			#Convert from string to float
			# tempFloat = [float(self.seedList[i][0])/(-0.24), float(self.seedList[i][1])/(-0.24), float(self.seedList[i][2])/(0.29)]
			tempFloat = [float(self.seedList[i][0]), float(self.seedList[i][1]), float(self.seedList[i][2])]
			
			#Convert from physical units to voxel coordinates
			tempVoxelCoordinates = self.MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
			seeds.append(tempVoxelCoordinates)

		self.seedList = seeds
		return self

#############################################################################################


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

# imageFilenames = ['/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr', \
# '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer2_VIBE.hdr', \
# '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer3_VIBE.hdr', \
# '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer4_VIBE.hdr', \
# '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer5_VIBE.hdr']

# seedListFiles = ['SeedList/Volunteer1_SeedList.csv', \
# 'SeedList/Volunteer2_SeedList.csv', \
# 'SeedList/Volunteer3_SeedList.csv', \
# 'SeedList/Volunteer4_SeedList.csv', \
# 'SeedList/Volunteer5_SeedList.csv']

#Windows path
imageFilenames = [\
'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer1_VIBE.hdr',
'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer2_VIBE.hdr',
'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer3_VIBE.hdr',
'E:\Google Drive\Research\Wrist MRI Database\VIBE\Volunteer4_VIBE.hdr']
groundtruthFilenames = [\
'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer1_GroundTruth.hdr',
'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer2_GroundTruth.hdr',
'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer3_GroundTruth.hdr',
'E:\Google Drive\Research\Wrist MRI Database\Ground Truth\Volunteer4_GroundTruth.hdr']
seedListFiles = [\
'SeedList/Volunteer1_SeedList.csv',\
'SeedList/Volunteer2_SeedList.csv',\
'SeedList/Volunteer3_SeedList.csv',\
'SeedList/Volunteer4_SeedList.csv']


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
		
		Segmentation = multiHelper.Execute(segmentationClass, SeedPoints, MRI_Image,parameter, False)

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
		
		multiHelper = Multiprocessor()
		
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
		
		bounds = [(60,150), (1500,2500), (0.001, 0.01)]
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

