import ConfidenceConnectedClass as BrentSeg
import SimpleITK as sitk

imageFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/VIBE/Volunteer1_VIBE.hdr'
inputLabelFilename = '/Users/Brent/Google Drive/Research/Wrist MRI/Constrained Regions/Volunteer1_VIBE-label.hdr'



MRI_Image = sitk.ReadImage(imageFilename)
inputLabel_Image = sitk.ReadImage(inputLabelFilename)	

SeedPoint = [[-57.6651,	-153.251,	36.09]] #For Volunteer 1

segmentationClass = BrentSeg.BoneSeg(MRI_Image,inputLabel_Image,SeedPoint)
output = segmentationClass.Execute()


segmentation  = sitk.Cast(output, MRI_Image.GetPixelID())
segmentation.CopyInformation(MRI_Image)

print(MRI_Image.GetSize())
print(segmentation.GetSize())

overlaidSegImage = sitk.LabelOverlay(MRI_Image, output)
sitk.Show(overlaidSegImage)