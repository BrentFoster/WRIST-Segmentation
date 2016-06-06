import SimpleITK as sitk

import BrentPython
from BrentPython import *


Segmentation = sitk.ReadImage('E:\Google Drive\Research\MRI Wrist Images\MRI and Ground Truth Images\Volunteer1_GroundTruth.hdr')



BinaryToLabelFilter = sitk.BinaryImageToLabelMapFilter()
# BinaryToLabelFilter.SetInputForegroundValue(5)
LabelMapToLabelImageFilter = sitk.LabelMapToLabelImageFilter()

Segmentation = BinaryToLabelFilter.Execute(Segmentation)
Segmentation = LabelMapToLabelImage.Execute(Segmentation)

print(Segmentation)

BrentPython.SaveSegmentation(Segmentation, 'test_segmentation.nii', verbose = False)

print('Done!!')

