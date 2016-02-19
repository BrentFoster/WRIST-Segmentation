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


import DICE




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

	for k in [1]:#range(0,len(imageFilenames)):
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


		#Initilize the various Python classes here
		segmentationClass = BrentSeg.BoneSeg()
		multiHelper = MultiprocessorHelper.Multiprocessor()
		dice_testing = DICE.DICE()

		
		outputSegmentation = multiHelper.Execute(segmentationClass, SeedPoints, MRI_Image)
		#Determine how long the algorithm took to run
		elapsed = timeit.default_timer() - start_time
		print("Elapsed Time (secs):"),
		print(elapsed)

		#Save the segmentation
		print("Saving segmentation to "),
		imageWriter = sitk.ImageFileWriter()
		tempFilename = imageFilenames[k]
		tempFilename = tempFilename[0:len(tempFilename)-4] + '_segmentation.hdr'
		print(tempFilename)
		imageWriter.Execute(outputSegmentation, tempFilename, True)
		print("Segmentation saved")
		sitk.Show(outputSegmentation)


# 		#Compute the Dice coefficent and save to a text file
# 		Dice = dice_testing.Execute(\
# '/Users/Brent/Desktop/Segmentations/Volunteer2_GroundTruth.hdr', \
# '/Users/Brent/Desktop/Segmentations/Volunteer2_VIBE_segmentation.hdr')

# 		#Save Dice coefficient to a text file
# 		text_file = open("Dice_Values.txt", "r+")
# 		text_file.readlines()
# 		text_file.write("%s\n" % Dice)
# 		text_file.close()
			


