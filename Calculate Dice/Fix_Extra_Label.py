import SimpleITK as sitk
import numpy as np

' Remove the thumb (label=1) and subtract one from the other labels '

FileName = '/Users/Brent/Google Drive/Research/Projects/Carpal Bone Segmentation/MRI Images/Radiologist - MRI Carpal Bone Segmentation/Expert Segmentations/Expert Segmentations in Nii Format/Healthy_Women_5_YA.nii'

img = sitk.ReadImage(FileName)

img_np = np.asarray(sitk.GetArrayFromImage(img))

img_np[img_np != 0] = img_np[img_np != 0] - 1

tempImg = sitk.Cast(sitk.GetImageFromArray(img_np), img.GetPixelID())
tempImg.CopyInformation(img)

img = tempImg

imageWriter = sitk.ImageFileWriter()
imageWriter.Execute(img, FileName, False)
