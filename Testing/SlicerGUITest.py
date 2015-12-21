import ConfidenceConnectedClass as BrentSeg
import MultiprocessorHelper
import SimpleITK as sitk
import timeit




imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
MRI_Image = sitk.ReadImage(imageFilename)

#All seeds for Volunteer 1
# SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51],[-57.6651,-153.251,36.09],[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858, -176.277, 36.67],[-80.2723, -157.437, 36.67],[-88.2267, -165.671, 36.67],[-92.6923, -167.764, 23.62]]
# SeedPoints = [SeedPoints[5]] #Just pick one for now
# SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51]]

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


#Load the seed list
seedsFilename = 'SeedList/Volunteer1_SeedList.csv'
textSeeds = loadSeedPoints(seedsFilename)
SeedPoints = []
for i in xrange(0,9): #Select which bone (or all of them) from the csv file
	#Convert from string to float
	tempFloat = [float(textSeeds['x'][i]), float(textSeeds['y'][i]), float(textSeeds['z'][i])]
	SeedPoints.append(tempFloat)

print("seeds:"),
print(SeedPoints)

segmentationClass = BrentSeg.BoneSeg()

multiHelper = MultiprocessorHelper.Multiprocessor(segmentationClass, SeedPoints, MRI_Image)

start_time = timeit.default_timer()
outputSegmentation = multiHelper.Execute()
#Determine how long the algorithm took to run
elapsed = timeit.default_timer() - start_time
print("Elapsed Time (secs):"),
print(elapsed)

#Save the segmentation
imageWriter = sitk.ImageFileWriter()
imageWriter.Execute(outputSegmentation, "Volunteer1_segmentation.hdr", True)


#Show the resulting segmentation labels

MRI_Image = sitk.Cast(MRI_Image, sitk.sitkUInt16)
outputSegmentation  = sitk.Cast(outputSegmentation, sitk.sitkUInt16)

overlaidSegImage = sitk.LabelOverlay(MRI_Image, outputSegmentation)
sitk.Show(overlaidSegImage)




# import subprocess
# import os

# args = ['MultiprocessorHelper.py','13', '123', '123']
# # proc = subprocess.Popen(['python', 'MultiprocessorHelper.py'],  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
# # print(proc.communicate('13', '123', '123'))


# print(subprocess.Popen(['python', 'MultiprocessorHelper.py']))



# # proc = subprocess.check_call(args, shell=True)
# # print(proc)



# # subprocess.call("python MultiprocessorHelper.py -l '%s'" % "BoneSegmentation", shell=True)


# # print(subprocess.check_call)

# # program_name = "python MultiprocessorHelper.py" 

# # arguments = ["-l", "-a"] 

# # command = [program_name]
# # command.extend(arguments) 
# # output = subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0] 
# # print(output)


