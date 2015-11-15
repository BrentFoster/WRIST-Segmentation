import ConfidenceConnectedClass as BrentSeg
import SimpleITK as sitk
import timeit
import multiprocessing
import numpy as np

#TODO: Do pre-processing beforehand since it doesn't make sense to redo the anisotropic filter
#for each bone

#Timing Test: 4 bones
#Multiprocessing: 72.9 seconds
#Single Thread: 121.8 seconds

#Timing Test: 8 bones
#Multiprocessing:207.4 seconds  
#Single Thread: 379.91 seconds 

#Paths for Brent's MacBook
seedsFilename = 'SeedList/Volunteer1SeedList.csv'
imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
inputLabelFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/Constrained Regions/Volunteer1_VIBE-label.hdr'

#Paths for Brent's PC
# imageFilename = 'E:\Google Drive\Research\Wrist MRI\VIBE\Volunteer1_VIBE.hdr'
# inputLabelFilename = 'E:\Google Drive\Research\Wrist MRI\Constrained Regions\Volunteer1_VIBE-label.hdr'


# MRI_Image = sitk.ReadImage(imageFilename)
# inputLabel_Image = sitk.ReadImage(inputLabelFilename)	

# ###Create an empty segmenationLabel array###
# nda = sitk.GetArrayFromImage(MRI_Image)
# nda = np.asarray(nda)
# nda = nda*0
# segmenationArray = nda
# ##Done creating empty inputLabel##


#Seed points for Volunteer 1 VIBE image
# SeedPoints = [[-57.6651,	-153.251,	36.09],[-76.0858,-176.277,36.67],[-80.2723,-157.437,36.67],[-88.2267,-165.671,36.67]] 
#All seeds for Volunteer 1
# SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51],[-57.6651,-153.251,36.09],[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858, -176.277, 36.67],[-80.2723, -157.437, 36.67],[-88.2267, -165.671, 36.67],[-92.6923, -167.764, 23.62]]
#Trapezium for Volunteer 1
# SeedPoints = [[-50.1293,-157.158,26.51],[-68.4105,-160.647,40.15]]
#4 seesd for Volunteer 1
# SeedPoints = [[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858, -176.277, 36.67],[-80.2723, -157.437, 36.67]]



def RoundSeedPoints(seedPoints, MRI_Image):
	seeds = []
	for i in xrange(0,len(SeedPoints)): #Select which bone (or all of them) from the csv file
		#Convert from string to float
		tempFloat = [float(seedPoints[i][0]), float(seedPoints[i][1]), float(seedPoints[i][2])]
		#Convert from physical units to voxel coordinates
		tempVoxelCoordinates = MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
		seeds.append(tempVoxelCoordinates)
	return seeds

# #Single core! time = 57.6 seconds
# start_time = timeit.default_timer()
# for x in range(8):
# 	segmentationClass = BrentSeg.BoneSeg(MRI_Image,inputLabel_Image,[SeedPoints[x]])
# 	output = segmentationClass.Execute()
# elapsed = timeit.default_timer() - start_time
# print("Elapsed Time (secs):"),
# print(elapsed)

def loadSeedPoints(filename):
	readfile = open(filename, "rU")
	readlines = readfile.readlines()
	x = list()
	y = []
	z = []
	label = []
	image = []
	for line in readlines:
		currLine = line.split(",")
		x.append(currLine[0])
		y.append(currLine[1])
		z.append(currLine[2])
		label.append(currLine[3])
		image.append(currLine[4])
	return {'x':x, 'y':y ,'z':z , 'label':label, 'image':image}

#Multiprocessing time = 33 seconds
start_time = timeit.default_timer()
def f(SeedPoint,MRI_Array,q):
	segmentationClass = BrentSeg.BoneSeg(MRI_Array,[SeedPoint])
	output = segmentationClass.Execute()
	q.put(output)

def RunMultiprocessing(WorkerNumbers,segmenationArray):
	procs = []
	q = multiprocessing.Queue()
	for x in WorkerNumbers:
		p = multiprocessing.Process(target=f, args=(SeedPoints[x],MRI_Array,q,))
		p.start()
		procs.append(p) #List of current processes

	print("Printing multiprocessing queue:")
	for i in range(len(WorkerNumbers)):
		#Outputs an array (due to multiprocessing 'pickle' constraints)
		segmenationArray = segmenationArray + q.get() 
	# Wait for all worker processes to finish by using .join()
	for p in procs:
		p.join()
		p.terminate()

	print('Finished with processes:'),
	print(WorkerNumbers)
	return segmenationArray


def SplitJobs(arr, size):
     arrs = []
     while len(arr) > size:
         pice = arr[:size]
         arrs.append(pice)
         arr   = arr[size:]
     arrs.append(arr)
     return arrs

if __name__ == '__main__':	

	# ###################LOAD SEED POINTS FROM CSV###################
	# #Load the csv file of the saved seeds locations manually created in Slicer
	# textSeeds = loadSeedPoints(seedsFilename)
	# SeedPoints = []
	# for i in xrange(1,9): #Select which bone (or all of them) from the csv file
	# 	#Convert from string to float
	# 	tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
	# 	#Convert from physical units to voxel coordinates
	# 	tempVoxelCoordinates = MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
	# 	SeedPoints.append(tempVoxelCoordinates)
	# ############################################################

	MRI_Image = sitk.ReadImage(imageFilename)
	inputLabel_Image = sitk.ReadImage(inputLabelFilename)	

	#Need to convert pixels to voxel coordinates because I only pass the image array
	#for the multiprocessing so the header information isn't there

	#All seeds for Volunteer 1
	SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51],[-57.6651,-153.251,36.09],[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858, -176.277, 36.67],[-80.2723, -157.437, 36.67],[-88.2267, -165.671, 36.67],[-92.6923, -167.764, 23.62]]
	
	SeedPoints = [SeedPoints[5]]
	print(SeedPoints)
	SeedPoints = RoundSeedPoints(SeedPoints, MRI_Image) 

	##Convert the SimpleITK images to arrays##
	MRI_Array = sitk.GetArrayFromImage(MRI_Image)
	#####

	###Create an empty segmenationLabel array###
	nda = sitk.GetArrayFromImage(MRI_Image)
	nda = np.asarray(nda)
	nda = nda*0
	segmenationArray = nda
	##Done creating empty inputLabel##

	#Check the number of cpu's in the computer and if the seed list is greater than 
	#the number of cpu's then run the parallel computing twice
	#TODO: Use a 'pool' of works for this may be more efficient

	num_CPUs = multiprocessing.cpu_count()
	print("Number of CPUs = "),
	print(num_CPUs)
	if (len(SeedPoints) <= num_CPUs):
		jobOrder = range(0, len(SeedPoints))
		segmenationArray = RunMultiprocessing(jobOrder, segmenationArray)

	elif (len(SeedPoints) > num_CPUs):
		print("Splitting jobs since number of CPUs < number of seed points")
		#Run the multiprocessing several times since there wasn't enough CPU's before
		jobOrder = SplitJobs(range(len(SeedPoints)), num_CPUs)
		for x in range(len(jobOrder)):
			segmenationArray = segmenationArray + RunMultiprocessing(jobOrder[x], segmenationArray)

	#Convert segmentationArray back into an image
	segmenationLabel = sitk.Cast(sitk.GetImageFromArray(segmenationArray), MRI_Image.GetPixelID())
	segmenationLabel.CopyInformation(MRI_Image)

	# Convert binary to a label map (seperate value per connected object)
	# sitk.BinaryImageToLabelMapFilter 
	# http://www.itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1BinaryImageToLabelMapFilter.html

	try:
		# sitk.Show(segmenationLabel)

		segmenationLabel  = sitk.Cast(segmenationLabel, sitk.sitkUInt16)
		MRI_Image = sitk.Cast(MRI_Image, sitk.sitkUInt16)

		overlaidSegImage = sitk.LabelOverlay(MRI_Image, segmenationLabel)
		sitk.Show(overlaidSegImage)
	except:
		print("Failed opening image in ITK (perhaps testing on Linux server)")

	#Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time
	print("Elapsed Time (secs):"),
	print(elapsed)


# segmentation  = sitk.Cast(output, MRI_Image.GetPixelID())
# segmentation.CopyInformation(MRI_Image)

# segmentation  = sitk.Cast(segmentation, sitk.sitkUInt16)
# MRI_Image = sitk.Cast(MRI_Image, sitk.sitkUInt16)

# overlaidSegImage = sitk.LabelOverlay(MRI_Image, segmentation)
# sitk.Show(overlaidSegImage)