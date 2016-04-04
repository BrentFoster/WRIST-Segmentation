import SimpleITK as sitk

class AnisotropicFilter(object):
	"""docstring for AnisotropicFilter"""
	def __init__(self):
		super(AnisotropicFilter, self).__init__()

	def Execute(self, sitkImg):

		# Pixel type has to be float for the diffusion filter
		MRI = sitk.Cast(sitkImg, sitk.sitkFloat32)

		diffusionFilter = sitk.CurvatureAnisotropicDiffusionImageFilter()
		# diffusionFilter = sitk.GradientAnisotropicDiffusionImageFilter()
		diffusionFilter.SetTimeStep(0.01)
		diffusionFilter.SetNumberOfIterations(5)
		# diffusionFilter.SetConductanceParameter(6)
		# diffusionFilter.SetConductanceScalingUpdateInterval(5)

		print(diffusionFilter)
		filteredImg = diffusionFilter.Execute(MRI)

		# Cast the image back to the original pixel type
		filteredImg = sitk.Cast(filteredImg, MRI.GetPixelID())

		return filteredImg

class SitkBias(object):
	"""docstring for AnisotropicFilter"""
	def __init__(self):
		super(SitkBias, self).__init__()

	def Execute(self, sitkImg):

		# Pixel type has to be float for the diffusion filter
		MRI = sitk.Cast(sitkImg, sitk.sitkFloat32)

		# Need to create a mask image for the bias correction step
		thresholdFilter = sitk.BinaryThresholdImageFilter()
		thresholdFilter.SetLowerThreshold(1)
		# thresholdFilter.SetUpperThreshold(20)

		# maskImg = thresholdFilter.Execute(sitkImg)	

		otsuFilter = sitk.OtsuMultipleThresholdsImageFilter()
		maskImg = otsuFilter.Execute(MRI)


		# #Bias field correction
		# BiasFilter = sitk.N4BiasFieldCorrectionImageFilter()
		# filteredImg = BiasFilter.Execute(MRI, maskImg)

		# # Cast the image back to the original pixel type
		# filteredImg = sitk.Cast(filteredImg, MRI.GetPixelID())

		return maskImg


class Segment_Hand(object):
	"""docstring for AnisotropicFilter"""
	def __init__(self):
		super(Segment_Hand, self).__init__()

	def Execute(self, MRI):
		''' Roughly segment the hand boundary (use automatic thresholding in SimpleITK)
			Could either hard code the thresholds based on VIBE or use a ITK method '''

		# Initialize various ITK filters
		otsuFilter = sitk.OtsuMultipleThresholdsImageFilter()
		# otsuFilter = sitk.OtsuThresholdImageFilter()
		otsuFilter.SetNumberOfHistogramBins(256)
		# otsuFilter = sitk.BinaryThresholdImageFilter()
		# otsuFilter.SetUpperThreshold(100)
		
		kernelRadius = [2,2,2]
		binary_medianFilter = sitk.BinaryMedianImageFilter()
		binary_medianFilter.SetRadius(kernelRadius)

		medianFilter = sitk.MedianImageFilter()
		medianFilter.SetRadius(kernelRadius)

		dilateFilter = sitk.BinaryDilateImageFilter()
		dilateFilter.SetBackgroundValue(0)
		dilateFilter.SetForegroundValue(1)
		dilateFilter.SetKernelRadius(kernelRadius)

		erodeFilter = sitk.BinaryErodeImageFilter()
		erodeFilter.SetBackgroundValue(0)
		erodeFilter.SetForegroundValue(1)
		erodeFilter.SetKernelRadius(kernelRadius*2)

		fillFilter = sitk.BinaryFillholeImageFilter()
		fillFilter.SetForegroundValue(0)
		fillFilter.FullyConnectedOff()

		# Run pipeline
		print('Running median filter on MRI')
		MRI = medianFilter.Execute(MRI)

		MRI = sitk.Cast(MRI, sitk.sitkUInt8) # Cast to 8 bit image

		print('Running Otsu thresholding')
		segHand = otsuFilter.Execute(MRI)
		print(otsuFilter)

		print('Running dilation filter')
		segHand = dilateFilter.Execute(segHand)

		print('Running binary fill filter')
		segHand = fillFilter.Execute(segHand)

		print('Running dilation filter')
		segHand = dilateFilter.Execute(segHand)

		print('Running binary fill filter')
		segHand = fillFilter.Execute(segHand)

		print('Running erode filter')
		segHand = erodeFilter.Execute(segHand)

		print('Running binary fill filter')
		segHand = fillFilter.Execute(segHand)

		return segHand
