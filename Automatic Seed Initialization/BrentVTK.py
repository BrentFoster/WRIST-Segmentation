#! /usr/bin/env python

''' Import all Python module dependencies '''
# Fist try to import vtk and catch if there is an error
try:
	import vtk
except:
	''' Add the needed paths to the vtk Python wrapping and dll's '''
	# print('Adding vtk paths to Python... ')
	import sys 

	using_PC = False
	if using_PC == True:
		# For Brent's PC
		sys.path.append("C:/MyProjects/VTK-bin/bin/Release/")
		sys.path.append("C:/MyProjects/VTK-bin/Wrapping/Python/")
		sys.path.append("C:/MyProjects/VTK-bin/lib/")
		# print sys.path
	else: 
		# For Brent's Mac
		sys.path.append("/Users/Brent/VTK/build/bin/")
		sys.path.append("/Users/Brent/VTK/build/Wrapping/Python/")
		sys.path.append("/Users/Brent/VTK/build/lib/")
		# print sys.path

	# Import vtk again (hopefully will work now)
	import vtk

from vtk.util.numpy_support import vtk_to_numpy
from vtk.util.numpy_support import numpy_to_vtk

import math 
import time

# Numpy is for holding arrays and converting from vtk to itk 
import numpy as np

import SimpleITK as sitk

def VTKToNumpyArray(imgReader):
	header = imgReader.GetNIFTIHeader()
	ImgDim = (header.GetDim(1), header.GetDim(2), header.GetDim(3))

	#Convert from vtk to numpy array
	Img = imgReader.GetOutput().GetPointData().GetScalars()

	npImg = np.asarray(vtk_to_numpy(Img))
	npImg = npImg.reshape(ImgDim, order='F')


	npImg[npImg != 1] = 0

	# vtkArray = numpy_to_vtk(num_array=npImg.ravel(), deep=True, array_type=vtk.VTK_FLOAT)

	return npImg

def load_image(ImgFileName):
	imgReader = vtk.vtkNIFTIImageReader()
	imgReader.SetFileName(ImgFileName)
	imgReader.Update()

	# Need to move the origin to the center of the image
	# to correctly transform the images later (after registration)
	changeFilter = vtk.vtkImageChangeInformation()
	changeFilter.SetInputConnection(imgReader.GetOutputPort())
	changeFilter.CenterImageOn()
	changeFilter.Update()

	# Resize the image (as needed) to be of size 256x256x100
	# This might be good as a user input later on
	# resizeFilter = vtk.vtkImageResize()
	# resizeFilter.SetOutputDimensions(256,256,250)
	# resizeFilter.SetInputConnection(changeFilter.GetOutputPort())
	# resizeFilter.Update()

	return changeFilter

def Initilize_Render():
	# Create the renderer, the render window, and the interactor. The
	# renderer draws into the render window, the interactor enables mouse-
	# and keyboard-based interaction with the scene.
	aRenderer = vtk.vtkRenderer()
	renWin = vtk.vtkRenderWindow()
	renWin.AddRenderer(aRenderer)
	iren = vtk.vtkRenderWindowInteractor()
	iren.SetRenderWindow(renWin)

	# It is convenient to create an initial view of the data. The FocalPoint
	# and Position form a vector direction. Later on (ResetCamera() method)
	# this vector is used to position the camera to look at the data in
	# this direction.
	aCamera = vtk.vtkCamera()
	aCamera.SetViewUp(0, 0, -1)
	aCamera.SetPosition(0, 1, 0)
	aCamera.SetFocalPoint(0, 0, 0)
	aCamera.ComputeViewPlaneNormal()

	return aRenderer, renWin, iren, aCamera

def Smooth_Surface(surface):
	''' Take a vtk surface and run through the smoothing pipeline '''

	boneNormals = vtk.vtkPolyDataNormals()
	boneNormals.SetInputConnection(surface.GetOutputPort())
	boneNormals.Update()

	# # Clean the polydata so that the edges are shared!
	# cleanPolyData = vtk.vtkCleanPolyData()
	# cleanPolyData.SetInputConnection(boneNormals.GetOutputPort())
	# cleanPolyData.Update()

	# We want to preserve topology (not let any cracks form). This may
	# limit the total reduction possible, which we have specified at 80%.
	# deci = vtk.vtkDecimatePro()
	# deci.SetInputConnection(cleanPolyData.GetOutputPort())
	# deci.SetTargetReduction(0.6)
	# deci.PreserveTopologyOn()

	# Apply laplacian smoothing to the surface
	smoothingFilter = vtk.vtkSmoothPolyDataFilter()
	smoothingFilter.SetInputConnection(boneNormals.GetOutputPort())
	smoothingFilter.SetNumberOfIterations(10)
	# smoothingFilter.SetRelaxationFactor(0.06)
	# smoothingFilter.SetFeatureAngle(60.0)
	smoothingFilter.Update()

	# # Generate surface normals to give a better visualization
	# normals = vtk.vtkPolyDataNormals()
	# normals.SetInputConnection(smoothingFilter.GetOutputPort())
	# normals.FlipNormalsOn()
	# normals.AutoOrientNormalsOn()
	# normals.ComputeCellNormalsOn()
	# normals.Update()

	return smoothingFilter

def Extract_Surface(imgReader):
	''' Extract a vtk surface from a vtk image '''

	boneExtractor = vtk.vtkContourFilter()
	boneExtractor.SetInputData(imgReader.GetOutput())
	# Use (1,.5,.5) for a binary image of intensity >= 1
	boneExtractor.GenerateValues(1,.5, .5)

	surface = Smooth_Surface(boneExtractor)

	return surface

class vtkTimerCallback():
	def __init__(self):
		self.timer_count = 0

	def execute(self,obj,event):
		self.actor.RotateX(0.1)
		self.actor.RotateY(-0.1)
		# self.actor.RotateZ(-0.01)
		# print(self.actor.GetPosition())

		# self.actor.SetPosition(5, -2.5, 2);

		# self.actor.SetPosition(0.17*self.timer_count, -0.32*self.timer_count, -0.09*self.timer_count);
		

		iren = obj
		iren.GetRenderWindow().Render()
		self.timer_count += 0.1

		if self.timer_count > 6:
			self.timer_count = 0

def Start_Camera(Neutral_bone, Position_One_bone):

	[aRenderer, renWin, iren, aCamera] = Initilize_Render()

	# Actors are added to the renderer
	aRenderer.AddActor(Neutral_bone)
	aRenderer.AddActor(Position_One_bone)

	# Set bone to semi-transparent.
	Neutral_bone.GetProperty().SetOpacity(1)
	Position_One_bone.GetProperty().SetOpacity(0.6)

	# An initial camera view is created.  The Dolly() method moves
	# the camera towards the FocalPoint, thereby enlarging the image.
	aRenderer.SetActiveCamera(aCamera)
	aRenderer.ResetCamera()
	aCamera.Dolly(1.5)

	# Set a background color for the renderer and set the size of the
	# render window (expressed in pixels).
	aRenderer.SetBackground(1, 1, 1)
	renWin.SetSize(640, 480)

	# Note that when camera movement occurs (as it does in the Dolly()
	# method), the clipping planes often need adjusting. Clipping planes
	# consist of two planes: near and far along the view direction. The
	# near plane clips out objects in front of the plane the far plane
	# clips out objects behind the plane. This way only what is drawn
	# between the planes is actually rendered.
	aRenderer.ResetCameraClippingRange()

	# Interact with the data.
	iren.Initialize()
	renWin.Render()
	iren.Start()

def Start_Animation(actor1, actor2):

	''' Run a visualization of a simple animation '''

	# Setup a renderer, render window, and interactor
	renderer = vtk.vtkRenderer()
	renderWindow = vtk.vtkRenderWindow()
	renderWindow.SetWindowName("Test")

	renderWindow.AddRenderer(renderer);
	renderWindowInteractor = vtk.vtkRenderWindowInteractor()
	renderWindowInteractor.SetRenderWindow(renderWindow)

	#Add the actor to the scene
	renderer.AddActor(actor1)
	renderer.AddActor(actor2)

	actor1.SetPosition(5, -2.5, 2)
	print('Actor1 position:', actor1.GetPosition())
	print('Actor2 position:', actor2.GetPosition())



	renderer.SetBackground(1,1,1) # Background color white

	#Render and interact
	renderWindow.Render()

	# Initialize must be called prior to creating timer events.
	renderWindowInteractor.Initialize()

	# Sign up to receive TimerEvent
	cb = vtkTimerCallback()
	cb.actor = actor2
	renderWindowInteractor.AddObserver('TimerEvent', cb.execute)
	timerId = renderWindowInteractor.CreateRepeatingTimer(100);

	#start the interaction and timer
	renderWindowInteractor.Start()

	return 0

def ShrinkImage(sitkImg, ScalingFactor=[3,3,3]):
	
	shrinkFilter = sitk.ShrinkImageFilter()
	shrinkFilter.SetShrinkFactors(ScalingFactor)
	sitkImg = shrinkFilter.Execute(sitkImg)

	return sitkImg

def Extract_Label(FileName, label):

	sitkImg  = sitk.ReadImage(FileName)

	sitkImg = ShrinkImage(sitkImg)

	# Convert to numpy array
	ndaImg = np.asarray(sitk.GetArrayFromImage(sitkImg))

	# Use logical indexing to remove unwanted label(s)
	if type(label) == int:
		# Create case for integer since int type doesn't have length 
		label_length = 1
	else:
		label_length = len(label)

	if label_length > 1:
		#Some number larger than maximum label
		maxLabel = ndaImg.max() + 1

		# Below is not elegant and hurts my eyes, but it works
		ndaNewImg = ndaImg.copy()

		for i in label:
			ndaNewImg[ndaImg == i] = maxLabel 

		ndaNewImg[ndaNewImg != maxLabel] = 0

		for i in label:
			#Put the label values back in
			ndaNewImg[ndaImg == i] = i

		ndaImg = ndaNewImg

	else:
		#There's only one label of interest
		ndaImg[ndaImg != label] = 0

	# Convert from arrays back into SimpleITK image
	sitkExtractedImg = sitk.GetImageFromArray(ndaImg)

	# Copy parameters (such as origin and spacing)
	sitkExtractedImg.CopyInformation(sitkImg)

	# Temporarily save this image using ITK
	imageWriter = sitk.ImageFileWriter()
	imageWriter.Execute(sitkExtractedImg, 'temp.nii', True)

	# Now load the temp image using vtk
	imgReader = load_image('temp.nii')

	return imgReader

def CopyMatrix4x4(matrix):
    """
    Copies the elements of a vtkMatrix4x4 into a numpy array.
    
    :@type matrix: vtk.vtkMatrix4x4
    :@param matrix: The matrix to be copied into an array.
    :@rtype: numpy.ndarray
    """
    m = np.ones((4,4))
    for i in range(4):
        for j in range(4):
            m[i,j] = matrix.GetElement(i,j)
    return m

def StoreAsMatrix4x4(marray):
    """
    Copies the elements of a numpy array into a vtkMatrix4x4.
    
    :@type: numpy.ndarray
    :@param matrix: The array to be copied into a matrix.
    :@rtype matrix: vtk.vtkMatrix4x4
    """
    m = vtk.Matrix4x4()
    for i in range(4):
        for j in range(4):
            m.SetElement(i, j, marray[i,j])
    return m

def saveMeasurement(measurement, Filename):
    try:
        #Save the user defined points in a .txt for automatimating testing (TODO)
        text_file = open(Filename, "r+")
        text_file.readlines()
        text_file.write("%s\n" % measurement)
        text_file.close()
    except:
        print("Saving to .txt failed...")
    return

def IterativeClosestPoint(source, target, transformImgFilename, labels):

	icp = vtk.vtkIterativeClosestPointTransform()
	icp.SetSource(source.GetOutput())
	icp.SetTarget(target.GetOutput())
	# icp.GetLandmarkTransform().SetModeToAffine()
	icp.GetLandmarkTransform().SetModeToSimilarity()
	# icp.GetLandmarkTransform().SetModeToRigidBody()
	# icp.DebugOn()
	icp.SetMaximumNumberOfIterations(500)  # 500
	icp.SetMaximumNumberOfLandmarks(400)   # 200
	# icp.SetMaximumMeanDistance(0.001) # Small number to use all iterations
	icp.StartByMatchingCentroidsOn()
	icp.SetMeanDistanceModeToAbsoluteValue()

	icp.Modified()
	icp.Update()

	print(icp)

	# Apply the resulting transform to the data
	imgReader = load_image(transformImgFilename)

	icpTransformFilter = vtk.vtkTransformPolyDataFilter()
	icpTransformFilter.SetInputConnection(source.GetOutputPort())
	icpTransformFilter.SetTransform(icp)
	icpTransformFilter.Update()


	# Apply the resulting transform to the input image
	resamplingFilter = vtk.vtkImageReslice()
	resamplingFilter.SetResliceTransform(icp)
	resamplingFilter.SetInputData(imgReader.GetOutput())
	resamplingFilter.Update()

	imgWriter = vtk.vtkNIFTIImageWriter()
	imgWriter.SetFileName(transformImgFilename[0:len(transformImgFilename)-4] + '_transformed.nii')
	imgWriter.SetInputConnection(resamplingFilter.GetOutputPort())
	imgWriter.Update()


	# # Export the registered surface to a stl file 
	# filename = 'Test_vtk_output.stl'
	# if labels == 1:
	# 	labels = '_MC'
	# elif labels == 2:
	# 	labels = '_Trapezium'

	# OutputFilename = 'Output_Images/' + ImgFileName_Two[0:len(ImgFileName_Two)-4]+ str(labels) + '_registered_model.stl'
	# stlWriter = vtk.vtkSTLWriter()
	# stlWriter.SetFileName(OutputFilename)
	# stlWriter.SetInputData(icpTransformFilter.GetOutput())
	# stlWriter.Write()

	# Update the source object with the transformed object
	transformedSource = icpTransformFilter.GetOutput()

	return transformedSource

def R_euler_zyz(matrix, alpha, beta, gamma):
    """Function for calculating the z-y-z Euler angle convention rotation matrix.

    From: http://svn.gna.org/svn/relax/tags/1.3.4/maths_fns/rotation_matrix.py
    Unit vectors
    ============

    The unit mux vector is::

                | -sin(alpha) * sin(gamma) + cos(alpha) * cos(beta) * cos(gamma) |
        mux  =  | -sin(alpha) * cos(gamma) - cos(alpha) * cos(beta) * sin(gamma) |.
                |                    cos(alpha) * sin(beta)                      |

    The unit muy vector is::

                | cos(alpha) * sin(gamma) + sin(alpha) * cos(beta) * cos(gamma) |
        muy  =  | cos(alpha) * cos(gamma) - sin(alpha) * cos(beta) * sin(gamma) |.
                |                   sin(alpha) * sin(beta)                      |

    The unit muz vector is::

                | -sin(beta) * cos(gamma) |
        muz  =  |  sin(beta) * sin(gamma) |.
                |        cos(beta)        |

    Rotation matrix
    ===============

    The rotation matrix is defined as the vector of unit vectors::

        R = [mux, muy, muz].


    @param matrix:  The 3x3 rotation matrix to update.
    @type matrix:   3x3 numpy array
    @param alpha:   The alpha Euler angle in rad.
    @type alpha:    float
    @param beta:    The beta Euler angle in rad.
    @type beta:     float
    @param gamma:   The gamma Euler angle in rad.
    @type gamma:    float
    """

    # Trig.
    sin_a = math.sin(alpha)
    sin_b = math.sin(beta)
    sin_g = math.sin(gamma)

    cos_a = math.cos(alpha)
    cos_b = math.cos(beta)
    cos_g = math.cos(gamma)

    # The unit mux vector component of the rotation matrix.
    matrix[0,0] = -sin_a * sin_g + cos_a * cos_b * cos_g
    matrix[1,0] = -sin_a * cos_g - cos_a * cos_b * sin_g
    matrix[2,0] =  cos_a * sin_b

    # The unit muy vector component of the rotation matrix.
    matrix[0,1] = cos_a * sin_g + sin_a * cos_b * cos_g
    matrix[1,1] = cos_a * cos_g - sin_a * cos_b * sin_g
    matrix[2,1] = sin_a * sin_b

    # The unit muz vector component of the rotation matrix.
    matrix[0,2] = -sin_b * cos_g
    matrix[1,2] =  sin_b * sin_g
    matrix[2,2] =  cos_b

    return matrix

def Output_Surface_To_Image(transformedSource):
	''' Convert the smoothed surface to an image and save it '''
	
	import math

	circle = transformedSource

	# print(transformedSource)
	# print(' ')

	# Copied from example on 
	# http://www.vtk.org/Wiki/VTK/Examples/Python/PolyData/PolyDataContourToImageData

	# prepare the binary image's voxel grid
	whiteImage = vtk.vtkImageData()
	bounds = [0]*6
	circle.GetBounds(bounds)
	spacing = [0]*3 # desired volume spacing
	spacing[0] = 1
	spacing[1] = 1
	spacing[2] = 1
	whiteImage.SetSpacing(spacing)
	 
	# compute dimensions
	dim = [0]*3
	for i in range(3):
	    dim[i] = int(math.ceil((bounds[i * 2 + 1] - bounds[i * 2]) / spacing[i])) + 1
	    if (dim[i] < 1):
	        dim[i] = 1
	
	# dim = [256,256,120]
	# print(dim)
	whiteImage.SetDimensions(dim)
	whiteImage.SetExtent(0, dim[0] - 1, 0, dim[1] - 1, 0, dim[2] - 1)
	origin = [0]*3
	# NOTE: I am not sure whether or not we had to add some offset!
	origin[0] = bounds[0]# + spacing[0] / 2
	origin[1] = bounds[2]# + spacing[1] / 2
	origin[2] = bounds[4]# + spacing[2] / 2

	# origin = (0,0,0)
	whiteImage.SetOrigin(origin)
	whiteImage.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
	 
	# fill the image with foreground voxels:
	inval = 255
	outval = 0
	count = whiteImage.GetNumberOfPoints()
	#for (vtkIdType i = 0 i < count ++i)
	for i in range(count):
	    whiteImage.GetPointData().GetScalars().SetTuple1(i, inval)
	 
	 
	# sweep polygonal data (this is the important thing with contours!)
	extruder = vtk.vtkLinearExtrusionFilter()
	extruder.SetInputData(circle)
	 
	extruder.SetScaleFactor(1.)
	extruder.SetExtrusionTypeToNormalExtrusion()
	extruder.SetVector(0, 0, 1)
	extruder.Update()
	 
	# polygonal data -> image stencil:
	pol2stenc = vtk.vtkPolyDataToImageStencil()
	pol2stenc.SetTolerance(0) # important if extruder.SetVector(0, 0, 1) !!!
	pol2stenc.SetInputConnection(extruder.GetOutputPort())
	pol2stenc.SetOutputOrigin(origin)
	pol2stenc.SetOutputSpacing(spacing)
	pol2stenc.SetOutputWholeExtent(whiteImage.GetExtent())
	pol2stenc.Update()
	 
	# cut the corresponding white image and set the background:
	imgstenc = vtk.vtkImageStencil()
	imgstenc.SetInputData(whiteImage)
	imgstenc.SetStencilConnection(pol2stenc.GetOutputPort())
	 
	imgstenc.ReverseStencilOff()
	imgstenc.SetBackgroundValue(outval)
	imgstenc.Update()
	 
	imageWriter = vtk.vtkNIFTIImageWriter()
	imageWriter.SetFileName('Output_Images/test_Smoothed_Surface.nii')
	imageWriter.SetInputConnection(imgstenc.GetOutputPort())
	imageWriter.Update()




	# reader2 = vtk.vtkPNGReader()
	# reader2.SetDataSpacing(0.8, 0.8, 1.5)
	# reader2.SetDataOrigin(0.0, 0.0, 0.0)
	# reader2.SetFileName("" + str(VTK_DATA_ROOT) + "/Data/fullhead15.png")

	# reader2 = vtk.vtkNIFTIImageReader()
	# reader2.SetFileName('Test_Surface_Smooted.nii')
	# reader2.SetDataSpacing(0.47, 0.47, 0.5)
	# reader2.SetDataOrigin(0.0, 0.0, 0.0)
	# reader2.SetDataExtent(0,256,0,256,0,120)

	# plane = vtk.vtkPlane()
	# plane.SetOrigin(0, 0, 0)
	# plane.SetNormal(0, 0, 1)

	# cutter = vtk.vtkCutter()
	# cutter.SetInputData(transformedSource)
	# cutter.SetCutFunction(plane)

	# stripper2 = vtk.vtkStripper()
	# stripper2.SetInputConnection(cutter.GetOutputPort())

	# dataToStencil2 = vtk.vtkPolyDataToImageStencil()
	# dataToStencil2.SetInputConnection(stripper2.GetOutputPort())
	# dataToStencil2.SetOutputSpacing(0.8, 0.8, 1.5)
	# dataToStencil2.SetOutputOrigin(0.0, 0.0, 0.0)
	# dataToStencil2.SetOutputWholeExtent(0, 256, 0, 256, 0, 120)

	# stencil2 = vtk.vtkImageStencil()
	# stencil2.SetInputConnection(reader2.GetOutputPort())
	# stencil2.SetStencilConnection(dataToStencil2.GetOutputPort())
	# stencil2.SetBackgroundValue(500)

	# imageAppend = vtk.vtkImageAppend()
	# # imageAppend.SetInputConnection(stencil.GetOutputPort())
	# imageAppend.SetInputConnection(stencil2.GetOutputPort())

	# imageAppend.Update()
	# reader2.Update()
	# print(stencil2)





	# Initilize a blank image
	# vtk.vtkImageData

	# QuantizePolyFilter = vtk.vtkQuantizePolyDataPoints()
	# QuantizePolyFilter.SetInputData(transformedSource)
	# QuantizePolyFilter.Update()

	# print(QuantizePolyFilter.GetOutput())


	# imgReader = vtk.vtkNIFTIImageReader()
	# imgReader.SetFileName('Volunteer5_Neutral_MC_registered.nii')
	# imgReader.Update()

	# pol2stenc = vtk.vtkPolyDataToImageStencil()
	# pol2stenc.SetInputData(transformedSource)
	# pol2stenc.SetOutputOrigin(0,0,0)
	# pol2stenc.SetOutputSpacing(0.47,0.47,0.5)
	# pol2stenc.SetOutputWholeExtent(0, 256, 0, 256, 0, 120)
	# pol2stenc.Update()
	# print(pol2stenc)
	# print(pol2stenc.GetOutput())
	# pol2stenc.SetBackgroundValue(0)
	# print(pol2stenc.GetOutput())

	# print(pol2stenc.GetOutput())

	# StencilData = vtk.vtkImageStencilData()
	# StencilData.SetExtent(0, 256, 0, 256, 0, 120)
	# StencilData.SetOrigin(0,0,0)
	# StencilData.SetSpacing(0.47,0.47,0.5)
	# StencilData.Add(pol2stenc.GetOutput())
	# StencilData.SetInputConnection(imgReader.GetOutputPort())
	# StencilData.Update()

	# imageStencil = vtk.vtkImageStencil()
	# imageStencil.SetStencilData(StencilData)
	# imageStencil.SetInput(imgReader.GetOutput())
	# imageStencil.Update()

	# print(imageStencil)

	# # Save the newly created image using the image stencil data type
	# imgWriter = vtk.vtkNIFTIImageWriter()
	# imgWriter.SetFileName('testSurface.nii')
	# imgWriter.SetInputData(imageStencil.GetOutput())
	# imgWriter.Update()



	# #choose an input point data array to copy
	# ivals = transformedSource.GetPointData().GetScalars()
	# numPts = transformedSource.GetNumberOfPoints()

	# ca = vtk.vtkFloatArray()
	# ca.SetName(ivals.GetName())
	# ca.SetNumberOfComponents(1)
	# ca.SetNumberOfTuples(numPts)

	# #create the output dataset with one cell per point
	# imgWriter = vtk.vtkNIFTIImageWriter()
	# imgWriter.SetFileName('testSurface.nii')
	# imgWriter.SetInputData(stencil.GetOutput())
	# imgWriter.Update()

	# # imgWriter.SetDimensions(numPts+1,2,2)
	# imgWriter.SetDataOrigin(0,0,0)
	# imgWriter.SetDataSpacing(.1,.1,.1)

	# #add the new array to the output
	# imgWriter.GetCellData().AddArray(ca)

	# #copy the values over element by element
	# for i in range(0, numPts):
	# 	ca.SetValue(i, ivals.GetValue(i))

	# print(ca)




	return 0

def Start_Actor(obj, color):

	boneStripper = vtk.vtkStripper()

	try:
		boneStripper.SetInputConnection(obj.GetOutputPort())
	except:
		boneStripper.SetInputData(obj)

	boneMapper = vtk.vtkPolyDataMapper()
	boneMapper.SetInputConnection(boneStripper.GetOutputPort())
	boneMapper.ScalarVisibilityOff()
	obj = vtk.vtkActor()
	obj.SetMapper(boneMapper)
	# obj.GetProperty().SetDiffuseColor(1, .49, .25)
	obj.GetProperty().SetDiffuseColor(color)
	obj.GetProperty().SetSpecular(.3)
	obj.GetProperty().SetSpecularPower(20)


	return obj

def Rotate_Surface(obj, RotateAngle):

	# Apply the resulting transform to the data
	transform = vtk.vtkTransform()
	transform.RotateWXYZ(RotateAngle,0,1,0)

	transformFilter=vtk.vtkTransformPolyDataFilter()
	transformFilter.SetTransform(transform)
	transformFilter.SetInputConnection(obj.GetOutputPort())
	transformFilter.Update()

	obj = transformFilter

	return obj

def Brent_VTK_Dice(surface_A_Input, surface_B_Input):
	''' Calculate the dice coefficient of two vtk surfaces '''
	''' dice = 2*intersection_volumes/(Volume_A + Volume_B) '''

	# Check to make sure the surfaces are triangle (needed for estimating volume)
	surface_A = vtk.vtkTriangleFilter()
	try:
		surface_A.SetInputData(surface_A_Input)
	except:
		surface_A.SetInputData(surface_A_Input.GetOutput())

	surface_B = vtk.vtkTriangleFilter()
	try:
		surface_B.SetInputData(surface_B_Input)
	except:
		surface_B.SetInputData(surface_B_Input.GetOutput())

	# Use the vtk boolean filter to get the intersected volume
	booleanOperation = vtk.vtkBooleanOperationPolyDataFilter()
	# booleanOperation.SetOperationToIntersection()
	booleanOperation.SetOperationToUnion()
	# booleanOperation.SetOperationToDifference()

	booleanOperation.ReorientDifferenceCellsOn()

	booleanOperation.SetInputConnection(0, surface_A.GetOutputPort())
	booleanOperation.SetInputConnection(1, surface_B.GetOutputPort())
	booleanOperation.Update()

	# Use the vtk massFilter to calculate the surface volumes 
	massFilter = vtk.vtkMassProperties()

	# Get the intersection volume
	massFilter.SetInputConnection(booleanOperation.GetOutputPort())
	massFilter.Update()
	intersection_volume = massFilter.GetVolume()

	# Get the volume of surface A
	massFilter.SetInputConnection(surface_A.GetOutputPort())
	massFilter.Update()
	Volume_A = massFilter.GetVolume()

	# Get the volume of surface B
	massFilter.SetInputConnection(surface_B.GetOutputPort())
	massFilter.Update()
	Volume_B = massFilter.GetVolume()

	# Plug in the resulting volumes to calculate the dice overlap coefficient
	dice = 2*intersection_volume/(Volume_A + Volume_B)

	print('intersection_volume '),
	print(intersection_volume)

	print('Volume_A '),
	print(Volume_A)

	print('Volume_B '),
	print(Volume_B)

	print("Dice = "),
	print(dice)

	surface = Smooth_Surface(booleanOperation)

	return dice, surface

def main(ImgFileName_One, ImgFileName_Two, transformImgFilename, labels, show_rendering=False, calculateDice=False):

	print('extracting fixed image')
	imgReaderFixed = Extract_Label(ImgFileName_One, labels)
	print('smoothing fixed image')
	Neutral_bone = Extract_Surface(imgReaderFixed)

	print('extracting moving image')
	imgReaderMoving = Extract_Label(ImgFileName_Two, labels)
	print('smoothing moving image')
	Position_One_bone = Extract_Surface(imgReaderMoving)
	
	# Neutral_bone = Rotate_Surface(Neutral_bone, RotateAngle=1)
	# Position_One_bone = Rotate_Surface(Position_One_bone, RotateAngle=10)

	print('Running ICP registration')
	Neutral_bone = IterativeClosestPoint(
		Neutral_bone, 
		Position_One_bone, 
		transformImgFilename,
		labels)

	if calculateDice == True:
		try:
			# Calculate the dice coefficient of the two surfaces
			[dice, dice_surface] = Brent_VTK_Dice(Position_One_bone, Neutral_bone)
			if dice > 1:
				dice = 'Error during dice'
			saveMeasurement(' ', 'Dice_Overlaps.txt')
			saveMeasurement(ImgFileName_One + ', ' + ImgFileName_Two + 
				', ' + str(labels) + ', Dice = ' + str(dice), 'Dice_Overlaps.txt')
		except:
			print('Error during dice')

	print('Showing rendering... ')
	if show_rendering == True:
		color = (0.8,0.4,0.7)
		Neutral_Actor = Start_Actor(Neutral_bone, color)

		color = (0.6, 0.6, 0.4)
		Position_One_Actor = Start_Actor(Position_One_bone, color)

		Start_Camera(Neutral_Actor, Position_One_Actor)
		# Start_Animation(Neutral_Actor, Position_One_Actor)

	# return npMatrix
	return 0

if __name__ == "__main__":
	ImgFileName_One = 'segHand_volunteer_1.nii'
	ImgFileName_Two = 'HandModel_volunteer_2.nii'
	transformImgFilename = ImgFileName_Two

	labels = (1,0)

	npMatrix = main(ImgFileName_One, ImgFileName_Two, transformImgFilename, labels, show_rendering=True, calculateDice=False)
