# #Add the location where the Linux virtual machine is installing the SimpleITK module
# import sys
# sys.path.append("/home/shippable/.local/lib/python2.7/site-packages")
# sys.path.append("/home/shippable/.local/lib/python2.7/site-packages/SimpleITK-0.9.1-py2.7-linux-x86_64.egg")
# sys.path.append("/usr/local/lib/python2.7/dist-packages/SimpleITK-0.9.1-py2.7-linux-x86_64.egg")
# print(sys.path)

# import numpy as np
import SimpleITK as sitk

#List all the locally installed python modules
import pip
installed_packages = pip.get_installed_distributions()
installed_packages_list = sorted(["%s==%s" % (i.key, i.version)
     for i in installed_packages])
print(installed_packages_list)






#Read in image
img = sitk.ReadImage("Volunteer5_VIBE.hdr")
img_T1_255 = sitk.Cast(sitk.RescaleIntensity(img), sitk.sitkUInt8)

#Create empty image to hold the segmentations
segmentation = sitk.Image(img.GetSize(), sitk.sitkUInt8)
segmentation.CopyInformation(img)

#Array of the seed points
# intPoints = np.array([[150, 150, 87], [170, 100, 87]])
#[intPoints[x,:]]
intPoints = [150, 150, 87]
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
