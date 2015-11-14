import ConfidenceConnectedClass as BrentSeg
import SimpleITK as sitk
import timeit
import multiprocessing



#easy_install -f . pathos

imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
inputLabelFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/Constrained Regions/Volunteer1_VIBE-label.hdr'
SeedPoint = [[-57.6651,	-153.251,	36.09],[-57.6651,	-153.251,	36.09]] #For Volunteer 1
MRI_Image = sitk.ReadImage(imageFilename)
inputLabel_Image = sitk.ReadImage(inputLabelFilename)	



start_time = timeit.default_timer()

def f(x):
	segmentationClass = BrentSeg.BoneSeg(MRI_Image,inputLabel_Image,[SeedPoint[x]])
	segmentationClass.Execute()
	print('Finished with process:'),
	print(x)

if __name__ == '__main__':	
	procs = []
	for x in range(2):
		p = multiprocessing.Process(target=f, args=(x,))
		p.start()

	# Wait for all worker processes to finish
	for p in procs:
	    p.join()
	
	#Determine how long the algorithm took to run
	elapsed = timeit.default_timer() - start_time

	print(type(p))

	print("Elapsed Time (secs):"),
	print(elapsed)


# pool = multiprocessing.Pool(processes = multiprocessing.cpu_count())

# async_results = [pool.apply_async(BrentSeg.BoneSeg,	args = ((MRI_Image,inputLabel_Image,i))) for i in xrange(0,7)]

# pool.close()

# map(multiprocessing.pool.ApplyResult.wait, async_results)

# lst_results = [r.get() for r in async_results]

# print lst_results




# segmentationClass = BrentSeg.BoneSeg(MRI_Image,inputLabel_Image,SeedPoint)
# output = segmentationClass.Execute()


# segmentation  = sitk.Cast(output, MRI_Image.GetPixelID())
# segmentation.CopyInformation(MRI_Image)


# segmentation  = sitk.Cast(segmentation, sitk.sitkUInt16)
# MRI_Image = sitk.Cast(MRI_Image, sitk.sitkUInt16)

# overlaidSegImage = sitk.LabelOverlay(MRI_Image, segmentation)
# sitk.Show(overlaidSegImage)