import SimpleITK as sitk
import sitkConfidenceConnectedSeg
import csv
import timeit
start_time = timeit.default_timer()

def getSeedPoints(filename):
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


#Load the csv file of the saved seeds locations manually created in Slicer
textSeeds = getSeedPoints('SeedList/SeedList.csv')

#Format the seeds into a long list (may also be good to give the bone labels)
x = (textSeeds['x'][1], textSeeds['x'][1], textSeeds['x'][1])

#Load the image
image = sitk.ReadImage("/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer2_VIBE.hdr")

seeds = []
for i in xrange(1,9): #Select which bone (or all of them) from the csv file
	#Convert from string to float
	tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
	print(tempFloat)

	#Convert from physical units to voxel coordinates
	tempVoxelCoordinates = image.TransformPhysicalPointToContinuousIndex(tempFloat)

	seeds.append(tempVoxelCoordinates)

#Segment using the seeds and the loaded image
# segmentation = sitkConfidenceConnectedSeg.ConfidenceConnectedSeg(image,seeds)

#Determine how long the algorithm took to run
elapsed = timeit.default_timer() - start_time

print "Time Elapsed:", elapsed, "seconds"


