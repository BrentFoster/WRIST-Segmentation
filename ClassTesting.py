import ConfidenceConnectedClass as BrentSeg
import SimpleITK as sitk
import timeit
import multiprocessing
import numpy as np

#Timing Test: 4 bones
#Multiprocessing: 72.9 seconds
#Single Thread: 121.8 seconds

#Timing Test: 8 bones
#Multiprocessing: 267.4 seconds  207.4
#Single Thread: 379.91 seconds 


#easy_install -f . pathos
seedsFilename = 'SeedList/Volunteer1SeedList.csv'
imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
inputLabelFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/Constrained Regions/Volunteer1_VIBE-label.hdr'
# SeedPoint = [[-57.6651,	-153.251,	36.09],[-57.6651,	-153.251,	36.09]] #For Volunteer 1
SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51],[-57.6651,-153.251,36.09],[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858,-176.277,36.67],[-80.2723,-157.437,36.67],[-88.2267,-165.671,36.67],[-92.6923,-167.764,23.62]]

MRI_Image = sitk.ReadImage(imageFilename)
inputLabel_Image = sitk.ReadImage(inputLabelFilename)	

###Create an empty segmenationLabel array###
nda = sitk.GetArrayFromImage(MRI_Image)
nda = np.asarray(nda)
nda = nda*0
segmenationArray = nda
##Done creating empty inputLabel##

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
def f(x,SeedPoints,q):
	segmentationClass = BrentSeg.BoneSeg(MRI_Image,inputLabel_Image,[SeedPoints[x]])
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
	for x in range(8):
		p = multiprocessing.Process(target=f, args=(x,SeedPoints,q,))
		p.start()
		procs.append(p) #List of current processes

	print("Printing q:")
	for i in range(8):
		#Outputs an array (due to multiprocessing 'pickle' constraints)
		segmenationArray = segmenationArray + q.get() 

	# Wait for all worker processes to finish by using .join()
	for p in procs:
		p.join()

	#Convert segmentationArray back into an image
	segmenationLabel = sitk.Cast(sitk.GetImageFromArray(segmenationArray), MRI_Image.GetPixelID())
	segmenationLabel.CopyInformation(MRI_Image)

	sitk.Show(segmenationLabel)

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