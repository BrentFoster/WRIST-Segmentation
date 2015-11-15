import ConfidenceConnectedClass as BrentSeg
import SimpleITK as sitk
import timeit
import multiprocessing
import numpy as np

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


MRI_Image = sitk.ReadImage(imageFilename)
inputLabel_Image = sitk.ReadImage(inputLabelFilename)	

###Create an empty segmenationLabel array###
nda = sitk.GetArrayFromImage(MRI_Image)
nda = np.asarray(nda)
nda = nda*0
segmenationArray = nda
##Done creating empty inputLabel##


#Seed points for Volunteer 1 VIBE image
SeedPoints = [[-57.6651,	-153.251,	36.09],[-76.0858,-176.277,36.67],[-80.2723,-157.437,36.67],[-88.2267,-165.671,36.67]] 

def RoundSeedPoints(seedPoints):
	seeds = []
	for i in xrange(0,len(SeedPoints)): #Select which bone (or all of them) from the csv file
		#Convert from string to float
		tempFloat = [float(seedPoints[i][0]), float(seedPoints[i][1]), float(seedPoints[i][2])]
		#Convert from physical units to voxel coordinates
		tempVoxelCoordinates = MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
		seeds.append(tempVoxelCoordinates)
	return seeds

#Need to convert pixels to voxel coordinates because I only pass the image array
#for the multiprocessing so the header information isn't there

SeedPoints = RoundSeedPoints(SeedPoints) 

##Convert the SimpleITK images to arrays##
MRI_Array = sitk.GetArrayFromImage(MRI_Image)
inputLabel_Array = sitk.GetArrayFromImage(inputLabel_Image)
#####

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
def f(x,SeedPoints,MRI_Array,inputLabel_Array,q):
	segmentationClass = BrentSeg.BoneSeg(MRI_Array,inputLabel_Array,[SeedPoints[x]])
	output = segmentationClass.Execute()
	print('Finished with process:'),
	print(x)
	q.put(output)

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

	procs = []
	#Store the output image arrays into a 'Queue'
	q = multiprocessing.Queue() 
	for x in range(1):

		p = multiprocessing.Process(target=f, args=(x,SeedPoints,MRI_Array,inputLabel_Array,q,))
		p.start()
		procs.append(p) #List of current processes

	print("Printing multiprocessing queue:")
	for i in range(1):
		#Outputs an array (due to multiprocessing 'pickle' constraints)
		segmenationArray = segmenationArray + q.get() 

	# Wait for all worker processes to finish by using .join()
	for p in procs:
		p.join()

	#Convert segmentationArray back into an image
	segmenationLabel = sitk.Cast(sitk.GetImageFromArray(segmenationArray), MRI_Image.GetPixelID())
	segmenationLabel.CopyInformation(MRI_Image)

	# Convert binary to a label map (seperate value per connected object)
	# sitk.BinaryImageToLabelMapFilter 
	# http://www.itk.org/SimpleITKDoxygen/html/classitk_1_1simple_1_1BinaryImageToLabelMapFilter.html

	try:
		sitk.Show(segmenationLabel)
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