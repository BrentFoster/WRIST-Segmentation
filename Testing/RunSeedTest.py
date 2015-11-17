#Add the parent folder to search for the python class for import
#$ python Testing/RunSeedTest.py 
import sys
import os.path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))


import ConfidenceConnectedClass as BrentSeg
import MultiprocessorHelper
import SimpleITK as sitk
import timeit



imageFilenames = ['/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer2_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer3_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer4_VIBE.hdr', \
'/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer5_VIBE.hdr']

seedListFiles = ['SeedList/Volunteer1_SeedList.csv', \
'SeedList/Volunteer2_SeedList.csv', \
'SeedList/Volunteer3_SeedList.csv', \
'SeedList/Volunteer4_SeedList.csv', \
'SeedList/Volunteer5_SeedList.csv']


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

##STARTS HERE##
if __name__ == '__main__':

	for k in [1]:#range(3,len(imageFilenames)):
		print("Filename:"),
		print(imageFilenames[k])
		#Load the data
		MRI_Image = sitk.ReadImage(imageFilenames[k])

		seedsFilename = seedListFiles[k]
		textSeeds = loadSeedPoints(seedsFilename)
		SeedPoints = []
		for i in xrange(0,9): #Select which bone (or all of them) from the csv file
			#Convert from string to float
			tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
			SeedPoints.append(tempFloat)

		print("seeds:"),
		print(SeedPoints)

		segmentationClass = BrentSeg.BoneSeg()
		multiHelper = MultiprocessorHelper.Multiprocessor()

		start_time = timeit.default_timer()
	
		outputSegmentation = multiHelper.Execute(segmentationClass, SeedPoints, MRI_Image)
		#Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time
		print("Elapsed Time (secs):"),
		print(elapsed)

		#Save computation time in a log file
		text_file = open("Testing/computation_times.txt", "r+")
		text_file.readlines()
		text_file.write("%s\n" % elapsed)
		text_file.close()

		#Save the segmentation
		print("Saving segmentation to "),
		imageWriter = sitk.ImageFileWriter()
		tempFilename = imageFilenames[k]
		tempFilename = '/Users/Brent/Desktop/Segmentations/' + tempFilename[len(tempFilename)-19:len(tempFilename)-4] + '_segmentation.hdr'
		print(tempFilename)
		imageWriter.Execute(outputSegmentation, tempFilename, True)
		print("Segmentation saved")




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


