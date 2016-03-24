import SimpleITK as sitk

#Load Images
# ShapePriorimg = sitk.ReadImage('/Users/Brent/Desktop/ShapePrior.nii')
VIBE  = sitk.ReadImage('/Users/Brent/Desktop/Volunteer1_VIBE.nii')
Segmentationimg  = sitk.ReadImage('/Users/Brent/Desktop/InitialSegmentation.nii')


# sitk.Show(ShapePriorimg)

#Initilize the SimpleITK Filters
GradientMagnitudeFilter = sitk.GradientMagnitudeImageFilter()
shapeDetectionFilter = sitk.ShapeDetectionLevelSetImageFilter()

shapeDetectionFilter.SetMaximumRMSError(0.01)
# shapeDetectionFilter.SetNumberOfIterations(100)
shapeDetectionFilter.SetPropagationScaling(-1)
# shapeDetectionFilter.SetCurvatureScaling(1)

#Signed distance function using the initial levelset segmentation
init_ls = sitk.SignedMaurerDistanceMap(Segmentationimg, insideIsPositive=True, useImageSpacing=True)

gradientImage = GradientMagnitudeFilter.Execute(VIBE)

# sitk.Show(gradientImage)

shapeImage = shapeDetectionFilter.Execute(init_ls, gradientImage)
print(shapeDetectionFilter)

sitk.Show(shapeImage)