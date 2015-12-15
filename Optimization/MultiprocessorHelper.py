import SimpleITK as sitk
import numpy as np
import multiprocessing
import timeit

def f(MRI_Array, SeedPoint,q, parameter):
	""" Function to be used with the Multiprocessor class (needs to be its own function 
		and not part of the same class to avoid the 'Pickle' type errors. """
	import BoneSegmentation as BrentSeg #This seems to be needed for Windows
	segmentationClass = BrentSeg.BoneSeg()

	# #Change some parameter(s) of the segmentation class for the optimization
	if (len(parameter) > 1): 
		segmentationClass.SetLevelSetLowerThreshold(0)
		segmentationClass.SetLevelSetUpperThreshold(parameter[0])

		#Shape Detection Filter
		segmentationClass.SetShapeCurvatureScale(1)
		segmentationClass.SetShapeMaxRMSError(parameter[2])
		segmentationClass.SetShapeMaxIterations(parameter[1])
		segmentationClass.SetShapePropagationScale(parameter[3])
		segmentationClass.SetScalingFactor(2)

	output = segmentationClass.Execute(MRI_Array,[SeedPoint], False)
	q.put(output)
	q.close()

class Multiprocessor(object):
	"""Helper class for sliptting a segmentation class (such as from SimpleITK) into
	several logical cores in parallel. Requires: SegmentationClass, Seed List, SimpleITK Image"""
	def __init__(self):
		self = self

	def Execute(self, segmentationClass, seedList, MRI_Image, parameter=0, verbose = False):
		self.segmentationClass = segmentationClass
		self.seedList = seedList
		self.MRI_Image = MRI_Image
		self.parameter = parameter
		self.verbose = verbose #Show output to terminal or not

		#Convert to voxel coordinates
		self.RoundSeedPoints() 

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
		num_CPUs = 3
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
		seeds = []
		for i in range(0,len(self.seedList)):
			#Convert from string to float
			tempFloat = [float(self.seedList[i][0]), float(self.seedList[i][1]), float(self.seedList[i][2])]
			
			#Convert from physical units to voxel coordinates
			tempVoxelCoordinates = self.MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
			seeds.append(tempVoxelCoordinates)

		self.seedList = seeds
		return self