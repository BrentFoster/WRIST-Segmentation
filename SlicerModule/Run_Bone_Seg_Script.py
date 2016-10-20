
import SimpleITK as sitk
import BoneSegmentation
import numpy as np

def SaveSegmentation(image, filename, verbose = False):
	""" Take a SimpleITK type image and save to a filename (in analyze format) """
	if verbose == True:
		print("Saving segmentation to "),
		print(filename)
	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(image, filename, True)
	if verbose == True:
		print("Segmentation saved")


def RunSegmentation(input_image, seedPoint, searchWindow):
	seedPoint = np.array(seedPoint).astype(int)

	im_size = np.asarray(input_image.GetSize())

	' Crop the input_image around the initial seed point to speed up computation '
	cropFilter = sitk.CropImageFilter()
	addFilter = sitk.AddImageFilter()

	cropFilter.SetLowerBoundaryCropSize(seedPoint - searchWindow)
	cropFilter.SetUpperBoundaryCropSize(im_size - seedPoint - searchWindow)

	cropNdxOne = seedPoint - searchWindow
	cropNdxTwo = seedPoint + searchWindow
	
	cropped_img = cropFilter.Execute(input_image)

	# The seed point is now in the middle of the search window
	seedPoint = np.asarray(searchWindow)

	' Run the Segmentation '
	segmentationClass = BoneSegmentation.BoneSeg()
	seg_img = segmentationClass.Execute(cropped_img, [seedPoint], verbose=False, returnSitkImage=True, convertSeedPhyscial=False)

	' Indexing to put the segmentation of the cropped image back into the original MRI '
	input_image_nda = sitk.GetArrayFromImage(input_image)
	input_image_nda = np.asarray(input_image_nda)

	seg_img_nda = sitk.GetArrayFromImage(seg_img)
	seg_img_nda = np.asarray(seg_img_nda)

	cropped_img_nda = sitk.GetArrayFromImage(cropped_img)
	cropped_img_nda = np.asarray(cropped_img_nda)

	cropped_img_nda[seg_img_nda == 1] = cropped_img_nda[seg_img_nda == 1] + 500;
	seg_img_nda = cropped_img_nda;

	input_image_nda[cropNdxOne[2]:cropNdxTwo[2],
					cropNdxOne[1]:cropNdxTwo[1],
					cropNdxOne[0]:cropNdxTwo[0]] = seg_img_nda


	' Return the final image '
	outputImg = sitk.Cast(sitk.GetImageFromArray(input_image_nda), sitk.sitkUInt16)
	outputImg.CopyInformation(input_image)

	return outputImg



if __name__ == "__main__":

	' Load the MRI image to be segmented'
	input_image = sitk.ReadImage('/Users/Brent/Google Drive/Research/MRI Wrist Images/MRI Ground Truth Brent/VOlunteer2_VIBE_we.nii')

	' Define the seed points '
	seedPoint = [200, 670, 100];

	' Define the size of the search window '
	searchWindow = [50,50,40];

	' Run the Segmentation '
	outputImg = RunSegmentation(input_image, seedPoint, searchWindow)

	outputImg = RunSegmentation(outputImg, [290,630,150], searchWindow)

	outputImg = RunSegmentation(outputImg, [210,670,140], searchWindow)

	' Show the final output image '
	sitk.Show(outputImg)



	# for i in range(0, len(seedPoint)):
	# 	print(seedPoint[i])
	# seedPoint = np.zeros(shape=(3,3))
	# seedPoint[0] = np.array([200, 670, 100]).astype(int);
	# seedPoint[1] = np.array([200, 670, 80]).astype(int);




print('Done!!')

