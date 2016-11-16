import SimpleITK as sitk

class SitkBias(object):
	"""docstring for AnisotropicFilter"""
	def __init__(self):
		super(SitkBias, self).__init__()

	def Execute(self, sitkImg):

        #Bias field correction
        BiasFilter = sitk.N4BiasFieldCorrectionImageFilter()
        sitkImg = BiasFilter.Execute(sitkImg)

		return sitkImg