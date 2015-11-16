# TESTING SCRIPT FOR THE AUTOMATED BUILDING WITH LINUX VIRTUAL MACHINE
import ConfidenceConnectedClass as BrentSeg
import SimpleITK as sitk
import multiprocessing
import numpy as np

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

def f(x,SeedPoints,MRI_Array,q):
	segmentationClass = BrentSeg.BoneSeg()
	output = segmentationClass.Execute(MRI_Array,[SeedPoints[x]])
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


	###Initial data and paths for Linux testing###
	imageFilename = 'Volunteer5_VIBE.hdr'
	inputLabelFilename = 'Volunteer5_VIBE.hdr'
	SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51],[-57.6651,-153.251,36.09],[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858,-176.277,36.67],[-80.2723,-157.437,36.67],[-88.2267,-165.671,36.67],[-92.6923,-167.764,23.62]]
	MRI_Image = sitk.ReadImage(imageFilename)
	inputLabel_Image = sitk.ReadImage(inputLabelFilename)	
	###

	###Create an empty segmenationLabel array###
	nda = sitk.GetArrayFromImage(MRI_Image)
	nda = np.asarray(nda)
	nda = nda*0
	segmenationArray = nda
	#####

	###Convert the SimpleITK images to arrays###
	MRI_Array = sitk.GetArrayFromImage(MRI_Image)
	inputLabel_Array = sitk.GetArrayFromImage(inputLabel_Image)
	#####

	print('\033[90m' + "Testing single thread routine...")
	try:
		for x in range(2):
			segmentationClass = BrentSeg.BoneSeg()
			output = segmentationClass.Execute(MRI_Image,[SeedPoints[x]])
		print('\033[90m' + "Single Thread test PASSED")
	except:
		print('\033[90m' + "Single Thread test FAILED")


	print('\033[90m' + "Testing multiprocessing routine...")
	try:

		procs = []
		#Store the output image arrays into a 'Queue'
		q = multiprocessing.Queue() 
		for x in range(2):

			p = multiprocessing.Process(target=f, args=(x,SeedPoints,MRI_Array,q,))
			p.start()
			procs.append(p) #List of current processes

		print("Printing q:")
		for i in range(2):
			#Outputs an array (due to multiprocessing 'pickle' constraints)
			segmenationArray = segmenationArray + q.get() 

		# Wait for all worker processes to finish by using .join()
		for p in procs:
			p.join()

		#Convert segmentationArray back into an image
		segmenationLabel = sitk.Cast(sitk.GetImageFromArray(segmenationArray), MRI_Image.GetPixelID())
		segmenationLabel.CopyInformation(MRI_Image)
		print('\033[90m' + "Multiprocessing routine PASSED")
	except:
		print('\033[90m' + "Multiprocessing routine FAILED")