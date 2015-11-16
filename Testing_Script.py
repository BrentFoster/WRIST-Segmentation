import numpy as np
import SimpleITK as sitk
import sitkConfidenceConnectedSeg
import csv
import timeit
start_time = timeit.default_timer()

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


def loadData(imageFilename, inputLabelFilename, seedsFilename):
	#Load the csv file of the saved seeds locations manually created in Slicer
	textSeeds = loadSeedPoints(seedsFilename)

	#Format the seeds into a long list (may also be good to give the bone labels)
	x = (textSeeds['x'][1], textSeeds['x'][1], textSeeds['x'][1])
	#Load the image
	image = sitk.ReadImage(imageFilename)

	seeds = []
	for i in xrange(1,9): #Select which bone (or all of them) from the csv file
		#Convert from string to float
		tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
		#Convert from physical units to voxel coordinates
		tempVoxelCoordinates = image.TransformPhysicalPointToContinuousIndex(tempFloat)
		seeds.append(tempVoxelCoordinates)

	#Check to see if there's a filename for the inputlabel or not
	if (len(inputLabelFilename) > 1):
		inputLabel = sitk.ReadImage(inputLabelFilename)	
	else:
		###Create an empty inputLabel image###
		nda = sitk.GetArrayFromImage(image)
		nda = np.asarray(nda)
		nda = nda*0
		inputLabel = sitk.Cast(sitk.GetImageFromArray(nda), image.GetPixelID())
		inputLabel.CopyInformation(image)
		##Done creating empty inputLabel##

	#Finished so return the loaded testing data
	return(image, inputLabel, seeds)


##STARTS HERE##
if __name__ == '__main__':

	seedsFilename = 'SeedList/Volunteer1SeedList.csv'
	imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
	inputLabelFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/Constrained Regions/Volunteer1_VIBE-label.hdr'

	(image, inputLabel, seeds) = loadData(imageFilename, inputLabelFilename, seedsFilename)

	#Run the algorithm using the seeds and the loaded image
	segmentation = sitkConfidenceConnectedSeg.ConfidenceConnectedSeg(image, inputLabel, seeds)

	#Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	print "Time Elapsed:", elapsed, "seconds"


