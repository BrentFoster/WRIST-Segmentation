# print(__doc__)

# From http://scikit-learn.org/stable/auto_examples/cluster/plot_segmentation_toy.html#example-cluster-plot-segmentation-toy-py
# Authors:  Emmanuelle Gouillart <emmanuelle.gouillart@normalesup.org>
#           Gael Varoquaux <gael.varoquaux@normalesup.org>
# License: BSD 3 clause

import numpy as np
# import matplotlib.pyplot as plt

from sklearn.feature_extraction import image
from sklearn.cluster import spectral_clustering

import SimpleITK as sitk

def plt(npArray):
	print('Upsampling image')
	refImg = sitk.ReadImage(Binary_Filename)
	refImg = shrinkFilter.Execute(refImg)

	img = sitk.Cast(sitk.GetImageFromArray(npArray), sitk.sitkFloat32)
	img = expandFilter.Execute(img)

	# img.CopyInformation(refImg)
	

	sitk.Show(img)
	
	return 0

# Binary_Filename = '/Users/Brent/BoneSegmentation/Clustering/leakage_test_segmentation.nii'
# Binary_Filename = 'test_thumb.nii'
Binary_Filename = 'Volunteer1_GroundTruth.hdr'
ScalingFactor = [4,4,4]

img = sitk.ReadImage(Binary_Filename)
print('Image loaded')

shrinkFilter = sitk.ShrinkImageFilter()
expandFilter = sitk.ExpandImageFilter()

shrinkFilter.SetShrinkFactors(ScalingFactor)
expandFilter.SetExpandFactors(ScalingFactor)

print('Down sampling image')
img = shrinkFilter.Execute(img)

img = sitk.GetArrayFromImage(img)
img[img != 1] = 0

mask = img
mask[mask != 0] = 1

mask = mask.astype(bool)
img = img.astype(int)


print('Creating graph')
# Convert the image into a graph with the value of the gradient on the edges.
graph = image.img_to_graph(img, mask=mask)

# Take a decreasing function of the gradient
graph.data = np.exp(-graph.data / graph.data.std())

# Force the solver to be arpack, since amg is numerically
# unstable on this example
print('Running spectral clustering')
labels = spectral_clustering(graph, n_clusters = 4, eigen_solver='arpack')

label_im = -np.ones(mask.shape)
label_im[mask] = labels




plt(label_im)


print('Done!')
