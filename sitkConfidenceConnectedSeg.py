import SimpleITK as sitk
import numpy as np

#Read in image
img = sitk.ReadImage("Volunteer5_VIBE.hdr")
img_T1_255 = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

#Create empty image to hold the segmentations
segmentation = sitk.Image(img.GetSize(), sitk.sitkUInt8)
segmentation.CopyInformation(img)

#Array of the seed points
intPoints = np.array([[150, 150, 87], [170, 100, 87]])
#[intPoints[x,:]]
for x in range(0, len(intPoints)):
	seg = sitk.ConfidenceConnected(img, [[150,150,87]], numberOfIterations=0, multiplier=1,
	initialNeighborhoodRadius = 1, replaceValue=x+1)
	segmentation = segmentation + seg

# sitk.Show(sitk.LabelOverlay(img_T1_255, segmentation))


##POST-PROCESSING FILTERS##
#Create the filters for filling any holes
# dilateFilter = sitk.BinaryDilateImageFilter()
# dilateFilter.SetKernelRadius(1)
# erodeFilter = sitk.BinaryErodeImageFilter()
# erodeFilter.SetKernelRadius(1)
# fillFilter = sitk.BinaryFillholeImageFilter()


#segTwo = dilateFilter.Execute(segTwo, 0, 5, False)
#segTwo = fillFilter.Execute(segTwo, True, 5)
#segTwo = erodeFilter.Execute(segTwo, 0, 5, False)
