import sys
# from __main__ import vtk, qt, ctk, slicer

from sklearn.feature_extraction import image
from sklearn.cluster import spectral_clustering
import SimpleITK as sitk
import numpy as np

#Allowed levels are CRITICAL, ERROR, WARNING, INFO, DEBUG, NOTSET
import logging 

def load_image(Binary_Filename, ScalingFactor=[4,4,4]):
	''' Load the input image and downsample (to speed up computation) '''

	logging.info('Loading image')
	img = sitk.ReadImage(Binary_Filename)
	
	logging.info('Down sampling image')
	shrinkFilter = sitk.ShrinkImageFilter()
	shrinkFilter.SetShrinkFactors(ScalingFactor)

	img = shrinkFilter.Execute(img)

	return img


def Spectral_Clustering(sitkImg, label=1, ScalingFactor=[4,4,4]):
 ''' Use spectral clustering on a binary image to remove the leakage areas '''

    logging.info('Converting to numpy array')
    
    npImg = sitk.GetArrayFromImage(sitkImg)

    npImg[npImg != label] = 0
    npImg[npImg != 0] = 1

    mask = npImg
    mask[mask != 0] = 1

    mask = mask.astype(bool)
    npImg = npImg.astype(int)

    logging.info('Creating graph from image')

    # Convert the image into a graph with the value of the gradient on the edges.
    graph = image.img_to_graph(npImg, mask=mask)

    # Take a decreasing function of the gradient
    graph.data = np.exp(-graph.data / graph.data.std())

    logging.info('Running spectral clustering')
    labels = spectral_clustering(graph, n_clusters = 2, eigen_solver='arpack')

    npLabel = -np.ones(mask.shape)
    npLabel[mask] = labels


    # Convert back to SimpleITK image type and upsample back to original size
    expandFilter = sitk.ExpandImageFilter()
    expandFilter.SetExpandFactors(ScalingFactor)

    Labelimg = sitk.Cast(sitk.GetImageFromArray(npLabel), sitkImg.GetPixelID())
    Labelimg = expandFilter.Execute(Labelimg)


    return Labelimg


if __name__ == "__main__":
	logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
	
	print sys.argv

	if len(sys.argv) > 1:
		Binary_Filename = sys.argv[1]
	else:
		Binary_Filename = 'Volunteer1_GroundTruth.hdr'

	ScalingFactor = [9,9,9]



	img = load_image(Binary_Filename, ScalingFactor)
	sc_img = Spectral_Clustering(img, label=1, ScalingFactor=ScalingFactor)

	sitk.Show(sc_img)

	logging.info('Done!')
