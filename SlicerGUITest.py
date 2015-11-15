import ConfidenceConnectedClass as BrentSeg
import MultiprocessorHelper
import SimpleITK as sitk
import timeit


imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
MRI_Image = sitk.ReadImage(imageFilename)

#All seeds for Volunteer 1
# SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51],[-57.6651,-153.251,36.09],[-57.386,-170.276,36.09],[-68.4105,-160.647,40.15],[-76.0858, -176.277, 36.67],[-80.2723, -157.437, 36.67],[-88.2267, -165.671, 36.67],[-92.6923, -167.764, 23.62]]
# SeedPoints = [SeedPoints[5]] #Just pick one for now
SeedPoints = [[-36.7324,-142.645,26.51],[-50.1293,-157.158,26.51]]

segmentationClass = BrentSeg.BoneSeg()

multiHelper = MultiprocessorHelper.Multiprocessor(segmentationClass, SeedPoints, MRI_Image)

start_time = timeit.default_timer()
output = multiHelper.Execute()
#Determine how long the algorithm took to run
elapsed = timeit.default_timer() - start_time
print("Elapsed Time (secs):"),
print(elapsed)

sitk.Show(output)
