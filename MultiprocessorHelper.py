import SimpleITK as sitk
import numpy as np
import multiprocessing
import timeit

class Multiprocessor(object):
	"""docstring for ClassName"""
	def __init__(self, segmentationClass, seedList, MRI_Image):
		# super(ClassName, self).__init__()
		self.segmentationClass = segmentationClass
		self.seedList = seedList
		self.MRI_Image = MRI_Image

		#Convert to voxel coordinates
		self.RoundSeedPoints() 
		self.Execute()

	def Execute(self):

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
		num_CPUs = multiprocessing.cpu_count()
		print("Number of CPUs = "),
		print(num_CPUs)

		if (len(self.seedList) <= num_CPUs):
			jobOrder = range(0, len(self.seedList))
			print(jobOrder)
			self.segmentationArray = self.RunMultiprocessing(jobOrder)

		elif (len(self.seedList) > num_CPUs):
			print("Splitting jobs since number of CPUs < number of seed points")
			#Run the multiprocessing several times since there wasn't enough CPU's before
			jobOrder = self.SplitJobs(range(len(self.seedList)), num_CPUs)
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
		maxSize = 4
		q = multiprocessing.Queue(maxSize)
		for x in jobOrder:
			p = multiprocessing.Process(target=self.f, args=(self.MRI_Array, self.seedList[x],q,))
			p.start()
			procs.append(p) #List of current processes

		tempArray = self.segmentationArray
		print("Printing multiprocessing queue:")
		for i in range(len(jobOrder)):
			#Outputs an array (due to multiprocessing 'pickle' constraints)
			tempArray = tempArray + q.get() 
		# Wait for all worker processes to finish by using .join()
		for p in procs:
			p.join()
			p.terminate()

		print('Finished with processes:'),
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

	def f(self, MRI_Array, SeedPoint,q):
		output = self.segmentationClass.Execute(MRI_Array,[SeedPoint])
		q.put(output)

	#Need to convert to voxel coordinates since we pass only the array due to a 'Pickle' error
	#with the multiprocessing library and the ITK image type which means the header information
	#is lost
	def RoundSeedPoints(self):
		seeds = []
		for i in xrange(0,len(self.seedList)): #Select which bone (or all of them) from the csv file
			#Convert from string to float
			tempFloat = [float(self.seedList[i][0]), float(self.seedList[i][1]), float(self.seedList[i][2])]
			#Convert from physical units to voxel coordinates
			tempVoxelCoordinates = self.MRI_Image.TransformPhysicalPointToContinuousIndex(tempFloat)
			seeds.append(tempVoxelCoordinates)
		self.seedList = seeds
		return self

#############################################################################################
	